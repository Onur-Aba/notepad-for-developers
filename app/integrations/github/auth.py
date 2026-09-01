from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta, timezone

from app.services.credential_store import CredentialStore, StoredCredentials

from .config import GitHubConfig
from .errors import (
    GitHubAccessDenied,
    GitHubAuthenticationError,
    GitHubAuthorizationPending,
    GitHubConfigurationError,
    GitHubDeviceFlowExpired,
    GitHubSlowDown,
)
from .http import HttpTransport
from .models import DeviceCode, TokenBundle


class GitHubAuthService:
    def __init__(self, credential_store: CredentialStore, config: GitHubConfig | None = None,
                 transport: HttpTransport | None = None) -> None:
        self.credential_store = credential_store
        self.config = config or GitHubConfig.from_environment()
        self.transport = transport or HttpTransport()

    def _ensure_configured(self) -> None:
        if not self.config.client_id:
            raise GitHubConfigurationError(
                "GitHub integration is not configured. Set DEVNEST_GITHUB_CLIENT_ID to the public GitHub App Client ID."
            )

    def request_device_code(self) -> DeviceCode:
        self._ensure_configured()
        response = self.transport.request(
            "POST", f"{self.config.web_base_url}/login/device/code",
            headers={"Accept": "application/json", "User-Agent": self.config.user_agent},
            form={"client_id": self.config.client_id},
        )
        if response.status < 200 or response.status >= 300 or not isinstance(response.data, dict):
            raise GitHubAuthenticationError("GitHub Device Flow could not be started.")
        data = response.data
        try:
            return DeviceCode(
                device_code=str(data["device_code"]), user_code=str(data["user_code"]),
                verification_uri=str(data.get("verification_uri") or data.get("verification_uri_complete") or "https://github.com/login/device"),
                expires_in=int(data.get("expires_in", 900)), interval=max(1, int(data.get("interval", 5))),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise GitHubAuthenticationError("GitHub returned an invalid Device Flow response.") from exc

    def poll_device_authorization_once(self, device_code: str) -> TokenBundle:
        self._ensure_configured()
        response = self.transport.request(
            "POST", f"{self.config.web_base_url}/login/oauth/access_token",
            headers={"Accept": "application/json", "User-Agent": self.config.user_agent},
            form={
                "client_id": self.config.client_id,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
        )
        data = response.data if isinstance(response.data, dict) else {}
        error = str(data.get("error") or "")
        if error == "authorization_pending":
            raise GitHubAuthorizationPending("Waiting for GitHub authorization.")
        if error == "slow_down":
            raise GitHubSlowDown("GitHub requested slower Device Flow polling.")
        if error in {"expired_token", "expired_device_code"}:
            raise GitHubDeviceFlowExpired("The GitHub device code expired. Start the connection again.")
        if error == "access_denied":
            raise GitHubAccessDenied("GitHub authorization was cancelled or denied.")
        if error:
            raise GitHubAuthenticationError(str(data.get("error_description") or error))
        token = str(data.get("access_token") or "")
        if not token:
            raise GitHubAuthenticationError("GitHub did not return a user access token.")
        return TokenBundle(
            access_token=token, token_type=str(data.get("token_type") or "bearer"),
            expires_in=int(data["expires_in"]) if data.get("expires_in") is not None else None,
            refresh_token=str(data["refresh_token"]) if data.get("refresh_token") else None,
            refresh_token_expires_in=int(data["refresh_token_expires_in"]) if data.get("refresh_token_expires_in") is not None else None,
        )

    def poll_until_authorized(self, device: DeviceCode, cancel_event: threading.Event | None = None) -> TokenBundle:
        deadline = time.monotonic() + device.expires_in
        interval = device.interval
        while time.monotonic() < deadline:
            if cancel_event and cancel_event.is_set():
                raise GitHubAccessDenied("GitHub connection was cancelled.")
            try:
                bundle = self.poll_device_authorization_once(device.device_code)
                self.store_token_bundle(bundle)
                return bundle
            except GitHubAuthorizationPending:
                time.sleep(interval)
            except GitHubSlowDown:
                interval += 5
                time.sleep(interval)
        raise GitHubDeviceFlowExpired("The GitHub device code expired. Start the connection again.")

    def store_token_bundle(self, bundle: TokenBundle) -> None:
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(seconds=bundle.expires_in)).isoformat(timespec="seconds") if bundle.expires_in else None
        refresh_expires_at = (
            now + timedelta(seconds=bundle.refresh_token_expires_in)
        ).isoformat(timespec="seconds") if bundle.refresh_token_expires_in else None
        self.credential_store.set(StoredCredentials(
            access_token=bundle.access_token, refresh_token=bundle.refresh_token,
            expires_at=expires_at, refresh_expires_at=refresh_expires_at,
        ))

    def refresh(self, refresh_token: str) -> TokenBundle:
        self._ensure_configured()
        response = self.transport.request(
            "POST", f"{self.config.web_base_url}/login/oauth/access_token",
            headers={"Accept": "application/json", "User-Agent": self.config.user_agent},
            form={"client_id": self.config.client_id, "grant_type": "refresh_token", "refresh_token": refresh_token},
        )
        data = response.data if isinstance(response.data, dict) else {}
        if data.get("error"):
            raise GitHubAuthenticationError("GitHub token refresh failed. Reconnect GitHub.")
        access_token = str(data.get("access_token") or "")
        if not access_token:
            raise GitHubAuthenticationError("GitHub token refresh did not return an access token.")
        bundle = TokenBundle(
            access_token=access_token, token_type=str(data.get("token_type") or "bearer"),
            expires_in=int(data["expires_in"]) if data.get("expires_in") is not None else None,
            refresh_token=str(data["refresh_token"]) if data.get("refresh_token") else refresh_token,
            refresh_token_expires_in=int(data["refresh_token_expires_in"]) if data.get("refresh_token_expires_in") is not None else None,
        )
        self.store_token_bundle(bundle)
        return bundle

    def get_valid_access_token(self) -> str:
        stored = self.credential_store.get()
        if not stored.access_token:
            raise GitHubAuthenticationError("GitHub is not connected.")
        if not stored.expires_at:
            return stored.access_token
        try:
            expires = datetime.fromisoformat(stored.expires_at)
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
        except ValueError:
            expires = datetime.now(timezone.utc)
        if expires > datetime.now(timezone.utc) + timedelta(minutes=2):
            return stored.access_token
        if stored.refresh_token:
            return self.refresh(stored.refresh_token).access_token
        raise GitHubAuthenticationError("GitHub authorization expired. Reconnect GitHub.")

    def disconnect(self) -> None:
        self.credential_store.delete()

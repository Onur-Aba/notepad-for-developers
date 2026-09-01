from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

from app.constants import VERSION

GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_WEB_BASE_URL = "https://github.com"
GITHUB_API_VERSION = "2026-03-10"


class SettingsLike(Protocol):
    def value(self, key: str, default: object = None) -> object: ...
    def set_value(self, key: str, value: object) -> None: ...
    def sync(self) -> None: ...


@dataclass(frozen=True, slots=True)
class GitHubConfig:
    client_id: str = ""
    app_slug: str = ""
    api_base_url: str = GITHUB_API_BASE_URL
    web_base_url: str = GITHUB_WEB_BASE_URL
    api_version: str = GITHUB_API_VERSION

    @classmethod
    def from_environment(cls) -> "GitHubConfig":
        return cls(
            client_id=os.environ.get("DEVNEST_GITHUB_CLIENT_ID", "").strip(),
            app_slug=os.environ.get("DEVNEST_GITHUB_APP_SLUG", "").strip(),
        )

    @classmethod
    def from_environment_and_settings(cls, settings: SettingsLike) -> "GitHubConfig":
        """Load public GitHub App identifiers and persist them locally.

        The GitHub App Client ID and app slug are public identifiers, not secrets.
        Environment variables win when present. Once seen, they are copied to
        QSettings so a packaged EXE launched by double-click keeps working even
        when the original PowerShell session is gone.
        """
        env_client_id = os.environ.get("DEVNEST_GITHUB_CLIENT_ID", "").strip()
        env_app_slug = os.environ.get("DEVNEST_GITHUB_APP_SLUG", "").strip()
        stored_client_id = str(settings.value("github/app_client_id", "") or "").strip()
        stored_app_slug = str(settings.value("github/app_slug", "") or "").strip()

        client_id = env_client_id or stored_client_id
        app_slug = env_app_slug or stored_app_slug

        changed = False
        if env_client_id and env_client_id != stored_client_id:
            settings.set_value("github/app_client_id", env_client_id)
            changed = True
        if env_app_slug and env_app_slug != stored_app_slug:
            settings.set_value("github/app_slug", env_app_slug)
            changed = True
        if changed:
            settings.sync()

        return cls(client_id=client_id, app_slug=app_slug)

    @property
    def user_agent(self) -> str:
        return f"DevNest/{VERSION}"

    @property
    def configured(self) -> bool:
        return bool(self.client_id)

    @property
    def install_url(self) -> str | None:
        return f"{self.web_base_url}/apps/{self.app_slug}/installations/new" if self.app_slug else None

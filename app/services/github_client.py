from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.secret_store import clear_github_credentials, load_github_credentials, save_github_credentials


API_VERSION = "2026-03-10"


class GitHubError(RuntimeError):
    pass


class GitHubAuthorizationPending(GitHubError):
    pass


class GitHubSlowDown(GitHubError):
    pass


@dataclass(slots=True)
class DeviceCode:
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int


class GitHubClient:
    def __init__(self, client_id: str, *, timeout: int = 20) -> None:
        self.client_id = client_id.strip()
        self.timeout = timeout

    @staticmethod
    def _expiry_iso(seconds: object) -> str | None:
        try: value = int(seconds)
        except (TypeError, ValueError): return None
        return (datetime.now(timezone.utc) + timedelta(seconds=max(0, value - 60))).isoformat(timespec="seconds")

    @staticmethod
    def _is_expired(value: object) -> bool:
        if not value: return False
        try: return datetime.fromisoformat(str(value)) <= datetime.now(timezone.utc)
        except ValueError: return True

    def _request(self, url: str, *, method: str = "GET", token: str | None = None,
                 data: dict[str, object] | None = None, form: bool = False) -> Any:
        body = None
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "DevNest-Desktop/2"}
        if url.startswith("https://github.com/login/"):
            headers["Accept"] = "application/json"
        if "api.github.com" in url:
            headers["X-GitHub-Api-Version"] = API_VERSION
        if token: headers["Authorization"] = f"Bearer {token}"
        if data is not None:
            if form:
                body = urllib.parse.urlencode({k: str(v) for k, v in data.items() if v is not None}).encode("utf-8")
                headers["Content-Type"] = "application/x-www-form-urlencoded"
            else:
                body = json.dumps(data).encode("utf-8"); headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try: message = json.loads(raw.decode("utf-8")).get("message", exc.reason)
            except Exception: message = exc.reason
            raise GitHubError(f"GitHub HTTP {exc.code}: {message}") from exc
        except urllib.error.URLError as exc:
            raise GitHubError(f"Could not reach GitHub: {exc.reason}") from exc
        if not raw: return {}
        try: return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc: raise GitHubError("GitHub returned an invalid response.") from exc

    def start_device_flow(self) -> DeviceCode:
        if not self.client_id: raise GitHubError("GitHub App Client ID is not configured.")
        data = self._request("https://github.com/login/device/code", method="POST", data={"client_id": self.client_id}, form=True)
        return DeviceCode(str(data["device_code"]), str(data["user_code"]), str(data["verification_uri"]), int(data["expires_in"]), int(data.get("interval", 5)))

    def poll_device_flow(self, device_code: str) -> dict[str, object]:
        data = self._request("https://github.com/login/oauth/access_token", method="POST", data={
            "client_id": self.client_id, "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }, form=True)
        error = data.get("error") if isinstance(data, dict) else None
        if error == "authorization_pending": raise GitHubAuthorizationPending("Authorization pending")
        if error == "slow_down": raise GitHubSlowDown("GitHub requested slower polling")
        if error: raise GitHubError(str(data.get("error_description") or error))
        credentials = {
            "access_token": data.get("access_token"), "access_expires_at": self._expiry_iso(data.get("expires_in")),
            "refresh_token": data.get("refresh_token"), "refresh_expires_at": self._expiry_iso(data.get("refresh_token_expires_in")),
            "token_type": data.get("token_type", "bearer"), "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        save_github_credentials(credentials)
        return credentials

    def credentials(self) -> dict[str, object] | None:
        return load_github_credentials()

    def access_token(self) -> str | None:
        creds = load_github_credentials()
        if not creds or not creds.get("access_token"): return None
        if not self._is_expired(creds.get("access_expires_at")):
            return str(creds["access_token"])
        refresh = creds.get("refresh_token")
        if not refresh or self._is_expired(creds.get("refresh_expires_at")):
            clear_github_credentials(); return None
        data = self._request("https://github.com/login/oauth/access_token", method="POST", data={
            "client_id": self.client_id, "grant_type": "refresh_token", "refresh_token": refresh,
        }, form=True)
        if data.get("error"):
            clear_github_credentials(); raise GitHubError(str(data.get("error_description") or data["error"]))
        updated = {
            "access_token": data.get("access_token"), "access_expires_at": self._expiry_iso(data.get("expires_in")),
            "refresh_token": data.get("refresh_token", refresh), "refresh_expires_at": self._expiry_iso(data.get("refresh_token_expires_in")),
            "token_type": data.get("token_type", "bearer"), "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        save_github_credentials(updated)
        return str(updated["access_token"])

    def disconnect(self) -> None:
        clear_github_credentials()

    def authenticated_user(self) -> dict[str, object]:
        token = self.access_token()
        if not token: raise GitHubError("GitHub is not connected.")
        return self._request("https://api.github.com/user", token=token)

    def list_repositories(self, limit: int = 200) -> list[dict[str, object]]:
        """Return repositories from installations of this GitHub App only.

        A GitHub App user token is intentionally narrower than a general OAuth
        token. Enumerating installations first mirrors GitHub's permission model
        and means the picker only shows repositories on which DevNest is actually
        installed.
        """
        token = self.access_token()
        if not token: raise GitHubError("GitHub is not connected.")
        installations_data = self._request("https://api.github.com/user/installations?per_page=100", token=token)
        installations = installations_data.get("installations", []) if isinstance(installations_data, dict) else []
        result: list[dict[str, object]] = []
        seen: set[int] = set()
        for installation in installations:
            if not isinstance(installation, dict) or not installation.get("id"):
                continue
            installation_id = int(installation["id"])
            page = 1
            while len(result) < limit:
                data = self._request(
                    f"https://api.github.com/user/installations/{installation_id}/repositories?per_page=100&page={page}",
                    token=token,
                )
                repos = data.get("repositories", []) if isinstance(data, dict) else []
                if not isinstance(repos, list): break
                for repo in repos:
                    if not isinstance(repo, dict): continue
                    repo_id = int(repo.get("id", 0) or 0)
                    if repo_id and repo_id in seen: continue
                    if repo_id: seen.add(repo_id)
                    copy = dict(repo); copy["_devnest_installation_id"] = installation_id
                    result.append(copy)
                    if len(result) >= limit: break
                if len(repos) < 100 or len(result) >= limit: break
                page += 1
        result.sort(key=lambda item: str(item.get("full_name", "")).casefold())
        return result[:limit]

    def repository(self, owner: str, repo: str) -> dict[str, object]:
        return self._request(f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}", token=self.access_token())

    def branch_head(self, owner: str, repo: str, branch: str | None = None) -> tuple[str, str]:
        info = self.repository(owner, repo)
        branch_name = branch or str(info.get("default_branch") or "main")
        data = self._request(f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/commits/{urllib.parse.quote(branch_name, safe='')}", token=self.access_token())
        return str(data["sha"]), branch_name

    def compare_commits(self, owner: str, repo: str, base: str, head: str) -> tuple[list[str], int]:
        data = self._request(f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/compare/{urllib.parse.quote(base, safe='')}...{urllib.parse.quote(head, safe='')}", token=self.access_token())
        files = [str(item.get("filename")) for item in data.get("files", []) if isinstance(item, dict) and item.get("filename")]
        return files, int(data.get("total_commits", len(data.get("commits", []))))


    def list_commits(self, owner: str, repo: str, limit: int = 50) -> list[dict[str, object]]:
        data = self._request(f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/commits?per_page={max(1,min(limit,100))}", token=self.access_token())
        return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []

    def list_pull_requests(self, owner: str, repo: str, state: str = "all", limit: int = 50) -> list[dict[str, object]]:
        data = self._request(f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/pulls?state={state}&per_page={max(1,min(limit,100))}&sort=updated&direction=desc", token=self.access_token())
        return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []

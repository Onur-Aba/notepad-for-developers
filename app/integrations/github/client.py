from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from app.models import CommitInfo, GitHubInstallation, PullRequestInfo
from app.database import utc_now_iso

from .config import GitHubConfig
from .errors import (
    GitHubAuthenticationError,
    GitHubNetworkError,
    GitHubNotFoundError,
    GitHubPermissionError,
    GitHubRateLimitError,
    GitHubTemporaryError,
    GitHubValidationError,
)
from .http import HttpResponse, HttpTransport


class GitHubClient:
    """Read-only GitHub REST client for repository data.

    All repository endpoints implemented here are GET-only. Authentication token
    exchange lives in auth.py and is the intentional POST exception.
    """

    def __init__(self, access_token: str, config: GitHubConfig | None = None,
                 transport: HttpTransport | None = None) -> None:
        if not access_token:
            raise GitHubAuthenticationError("GitHub access token is missing.")
        self._access_token = access_token
        self.config = config or GitHubConfig.from_environment()
        self.transport = transport or HttpTransport()

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._access_token}",
            "User-Agent": self.config.user_agent,
            "X-GitHub-Api-Version": self.config.api_version,
        }

    def _get(self, path: str, query: dict[str, object] | None = None) -> HttpResponse:
        response = self.transport.request("GET", f"{self.config.api_base_url}{path}", headers=self._headers(), query=query)
        self._raise_for_response(response)
        return response

    @staticmethod
    def _raise_for_response(response: HttpResponse) -> None:
        if 200 <= response.status < 300:
            return
        data = response.data if isinstance(response.data, dict) else {}
        message = str(data.get("message") or f"GitHub returned HTTP {response.status}.")
        if response.status == 401:
            raise GitHubAuthenticationError("GitHub authorization is no longer valid. Reconnect GitHub.")
        if response.status in {403, 429}:
            remaining = response.headers.get("x-ratelimit-remaining")
            if response.status == 429 or remaining == "0" or "rate limit" in message.lower():
                raise GitHubRateLimitError("GitHub rate limit reached. Local DevNest features remain available.", response.headers.get("x-ratelimit-reset"))
            raise GitHubPermissionError(message)
        if response.status == 404:
            raise GitHubNotFoundError("GitHub resource is unavailable or is not authorized for DevNest.")
        if response.status == 422:
            raise GitHubValidationError(message)
        if response.status >= 500:
            raise GitHubTemporaryError("GitHub is temporarily unavailable.")
        raise GitHubNetworkError(message)

    def _paginate(self, path: str, *, list_key: str | None = None,
                  query: dict[str, object] | None = None, max_pages: int = 20) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        page = 1
        while page <= max_pages:
            params = {**(query or {}), "per_page": 100, "page": page}
            response = self._get(path, params)
            data = response.data
            raw_items = data.get(list_key, []) if list_key and isinstance(data, dict) else data
            if not isinstance(raw_items, list):
                return items
            items.extend(item for item in raw_items if isinstance(item, dict))
            link_header = response.headers.get("link", "")
            if not raw_items or 'rel="next"' not in link_header:
                break
            page += 1
        return items

    def get_authenticated_user(self) -> dict[str, Any]:
        data = self._get("/user").data
        return data if isinstance(data, dict) else {}

    def list_user_installations(self) -> list[GitHubInstallation]:
        items = self._paginate("/user/installations", list_key="installations")
        now = utc_now_iso()
        result: list[GitHubInstallation] = []
        for raw in items:
            account = raw.get("account") or {}
            result.append(GitHubInstallation(
                id=int(raw.get("id", 0)),
                account_login=str(account.get("login") or account.get("name") or "Unknown"),
                account_type=str(account.get("type") or "Unknown"),
                account_avatar_url=account.get("avatar_url"),
                target_type=raw.get("target_type"),
                last_synced_at=now,
            ))
        return result

    def list_installation_repositories(self, installation_id: int) -> list[dict[str, Any]]:
        return self._paginate(f"/user/installations/{installation_id}/repositories", list_key="repositories")

    def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        data = self._get(f"/repos/{owner}/{repo}").data
        return data if isinstance(data, dict) else {}

    def list_branches(self, owner: str, repo: str) -> list[dict[str, Any]]:
        return self._paginate(f"/repos/{owner}/{repo}/branches")

    def get_branch(self, owner: str, repo: str, branch: str) -> dict[str, Any]:
        data = self._get(f"/repos/{owner}/{repo}/branches/{branch}").data
        return data if isinstance(data, dict) else {}

    def list_commits(self, owner: str, repo: str, branch: str | None = None, path: str | None = None,
                     max_pages: int = 5) -> list[CommitInfo]:
        raw = self._paginate(f"/repos/{owner}/{repo}/commits", query={"sha": branch, "path": path}, max_pages=max_pages)
        return [CommitInfo(
            sha=str(c.get("sha", "")),
            message=str(c.get("commit", {}).get("message", "")).splitlines()[0],
            author=(c.get("author") or {}).get("login") or c.get("commit", {}).get("author", {}).get("name"),
            authored_at=c.get("commit", {}).get("author", {}).get("date"),
            html_url=c.get("html_url"),
        ) for c in raw]

    def get_commit(self, owner: str, repo: str, sha: str) -> dict[str, Any]:
        data = self._get(f"/repos/{owner}/{repo}/commits/{sha}").data
        return data if isinstance(data, dict) else {}

    def compare_commits(self, owner: str, repo: str, base: str, head: str) -> dict[str, Any]:
        data = self._get(f"/repos/{owner}/{repo}/compare/{base}...{head}").data
        return data if isinstance(data, dict) else {}

    def list_pull_requests(self, owner: str, repo: str, state: str = "all", max_pages: int = 5) -> list[PullRequestInfo]:
        raw = self._paginate(f"/repos/{owner}/{repo}/pulls", query={"state": state, "sort": "updated", "direction": "desc"}, max_pages=max_pages)
        return [PullRequestInfo(
            number=int(p.get("number", 0)), title=str(p.get("title", "")), state=str(p.get("state", "")),
            html_url=str(p.get("html_url", "")), merged_at=p.get("merged_at"), updated_at=p.get("updated_at"),
        ) for p in raw]

    def get_pull_request(self, owner: str, repo: str, number: int) -> dict[str, Any]:
        data = self._get(f"/repos/{owner}/{repo}/pulls/{number}").data
        return data if isinstance(data, dict) else {}

    def list_pull_request_files(self, owner: str, repo: str, number: int) -> list[dict[str, Any]]:
        return self._paginate(f"/repos/{owner}/{repo}/pulls/{number}/files")

    def get_contents(self, owner: str, repo: str, path: str = "", ref: str | None = None) -> list[dict[str, Any]] | dict[str, Any]:
        clean_path = path.strip("/")
        endpoint = f"/repos/{owner}/{repo}/contents" + (f"/{clean_path}" if clean_path else "")
        data = self._get(endpoint, {"ref": ref} if ref else None).data
        if isinstance(data, (list, dict)):
            return data
        return []

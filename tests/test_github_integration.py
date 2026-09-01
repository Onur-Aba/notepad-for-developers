from __future__ import annotations

import pytest

from app.integrations.github.auth import GitHubAuthService
from app.integrations.github.client import GitHubClient
from app.integrations.github.config import GitHubConfig
from app.integrations.github.errors import GitHubAuthorizationPending, GitHubRateLimitError, GitHubSlowDown
from app.integrations.github.http import HttpResponse
from app.services.credential_store import InMemoryCredentialStore


class FakeTransport:
    def __init__(self, responses: list[HttpResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, str, dict]] = []

    def request(self, method: str, url: str, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)


def config() -> GitHubConfig:
    return GitHubConfig(client_id="Iv1.public-client-id", app_slug="devnest-test")


def test_device_code_and_token_parsing() -> None:
    transport = FakeTransport([
        HttpResponse(200, {}, {"device_code": "dev", "user_code": "DNV-42XX", "verification_uri": "https://github.com/login/device", "expires_in": 900, "interval": 5}),
        HttpResponse(200, {}, {"access_token": "ghu_test", "expires_in": 28800, "refresh_token": "ghr_test", "refresh_token_expires_in": 15897600, "token_type": "bearer"}),
    ])
    auth = GitHubAuthService(InMemoryCredentialStore(), config(), transport)  # type: ignore[arg-type]
    device = auth.request_device_code()
    token = auth.poll_device_authorization_once(device.device_code)
    assert device.user_code == "DNV-42XX"
    assert token.access_token == "ghu_test"
    assert transport.calls[0][0] == "POST"
    assert transport.calls[1][2]["form"]["grant_type"] == "urn:ietf:params:oauth:grant-type:device_code"


def test_device_pending_and_slow_down() -> None:
    pending = GitHubAuthService(InMemoryCredentialStore(), config(), FakeTransport([HttpResponse(200, {}, {"error": "authorization_pending"})]))  # type: ignore[arg-type]
    with pytest.raises(GitHubAuthorizationPending):
        pending.poll_device_authorization_once("dev")
    slow = GitHubAuthService(InMemoryCredentialStore(), config(), FakeTransport([HttpResponse(200, {}, {"error": "slow_down"})]))  # type: ignore[arg-type]
    with pytest.raises(GitHubSlowDown):
        slow.poll_device_authorization_once("dev")


def test_client_installation_repo_pagination_and_read_only_methods() -> None:
    transport = FakeTransport([
        HttpResponse(200, {"link": '<next>; rel="next"'}, {"installations": [{"id": 1, "account": {"login": "me", "type": "User"}}]}),
        HttpResponse(200, {}, {"installations": [{"id": 2, "account": {"login": "Acme", "type": "Organization"}}]}),
        HttpResponse(200, {}, {"repositories": [{"id": 10, "name": "private", "private": True}]}),
    ])
    client = GitHubClient("ghu_test", config(), transport)  # type: ignore[arg-type]
    installations = client.list_user_installations()
    repositories = client.list_installation_repositories(1)
    assert [i.id for i in installations] == [1, 2]
    assert repositories[0]["private"] is True
    assert all(call[0] == "GET" for call in transport.calls)
    assert transport.calls[0][2]["headers"]["X-GitHub-Api-Version"] == "2026-03-10"


def test_rate_limit_maps_to_specific_error() -> None:
    transport = FakeTransport([HttpResponse(403, {"x-ratelimit-remaining": "0"}, {"message": "API rate limit exceeded"})])
    client = GitHubClient("ghu_test", config(), transport)  # type: ignore[arg-type]
    with pytest.raises(GitHubRateLimitError):
        client.get_authenticated_user()


def test_public_github_app_config_is_remembered_from_environment(monkeypatch) -> None:
    class FakeSettings:
        def __init__(self) -> None:
            self.values: dict[str, object] = {}
            self.synced = False

        def value(self, key: str, default: object = None) -> object:
            return self.values.get(key, default)

        def set_value(self, key: str, value: object) -> None:
            self.values[key] = value

        def sync(self) -> None:
            self.synced = True

    settings = FakeSettings()
    monkeypatch.setenv("DEVNEST_GITHUB_CLIENT_ID", "Iv1.remember-me")
    monkeypatch.setenv("DEVNEST_GITHUB_APP_SLUG", "devnest-local")
    cfg = GitHubConfig.from_environment_and_settings(settings)
    assert cfg.client_id == "Iv1.remember-me"
    assert cfg.app_slug == "devnest-local"
    assert settings.values["github/app_client_id"] == "Iv1.remember-me"
    assert settings.values["github/app_slug"] == "devnest-local"
    assert settings.synced is True

    monkeypatch.delenv("DEVNEST_GITHUB_CLIENT_ID")
    monkeypatch.delenv("DEVNEST_GITHUB_APP_SLUG")
    restored = GitHubConfig.from_environment_and_settings(settings)
    assert restored.client_id == "Iv1.remember-me"
    assert restored.app_slug == "devnest-local"

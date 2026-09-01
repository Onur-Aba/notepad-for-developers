from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from app.services.local_git_service import LocalGitService, parse_github_remote, path_matches


pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="Git executable unavailable")


def _git(path: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=path, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def test_remote_parsing_formats() -> None:
    expected = "acme/payment-api"
    assert parse_github_remote("https://github.com/acme/payment-api.git") == expected
    assert parse_github_remote("https://github.com/acme/payment-api") == expected
    assert parse_github_remote("git@github.com:acme/payment-api.git") == expected
    assert parse_github_remote("ssh://git@github.com/acme/payment-api.git") == expected
    assert parse_github_remote("https://gitlab.com/acme/payment-api.git") is None


def test_path_matching_boundaries() -> None:
    assert path_matches("directory", "backend/auth/", "backend/auth/session.py")
    assert path_matches("directory", "backend/auth/", "backend/auth/nested/foo.py")
    assert not path_matches("directory", "backend/auth/", "backend/authentication/foo.py")
    assert not path_matches("directory", "backend/auth/", "frontend/auth/foo.py")
    assert path_matches("file", "backend/auth/session.py", "backend/auth/session.py")
    assert not path_matches("file", "backend/auth/session.py", "backend/auth/session_test.py")


def test_local_git_discovery_and_comparison(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.email", "devnest@example.invalid")
    _git(tmp_path, "config", "user.name", "DevNest Test")
    (tmp_path / "backend" / "auth").mkdir(parents=True)
    (tmp_path / "backend" / "auth" / "session.py").write_text("v1\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "initial")
    base = _git(tmp_path, "rev-parse", "HEAD")
    _git(tmp_path, "remote", "add", "origin", "git@github.com:acme/payment-api.git")

    service = LocalGitService()
    info = service.discover_repository(tmp_path)
    assert info.branch == "main"
    assert info.head_sha == base
    assert service.github_full_name_from_remotes(info.remotes) == ("origin", "acme/payment-api")

    (tmp_path / "backend" / "auth" / "session.py").write_text("v2\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("readme\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "auth update")
    head = _git(tmp_path, "rev-parse", "HEAD")
    changed = service.get_changed_files(tmp_path, base, head)
    assert {f.path for f in changed} == {"backend/auth/session.py", "README.md"}
    assert service.get_commit_count(tmp_path, base, head) == 1
    assert service.get_commits(tmp_path, base, head)[0].message == "auth update"
    assert service.is_commit_available(tmp_path, base)

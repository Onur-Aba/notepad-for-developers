from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.skip(
    reason="Legacy schema-5 service API tests; replaced by v6 migration/local-git/change-detection/GitHub integration tests."
)

from app.database import Database
from app.services.local_git import inspect_repository, parse_github_remote
from app.services.repository_scanner import RepositoryScanner, resource_is_affected


def _git(path: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _init_repo(path: Path) -> None:
    path.mkdir()
    _git(path, "init")
    _git(path, "config", "user.email", "devnest@example.test")
    _git(path, "config", "user.name", "DevNest Test")
    _git(path, "remote", "add", "origin", "git@github.com:acme/backend.git")


def test_v1_database_migrates_without_losing_notes(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.db"
    con = sqlite3.connect(db_path)
    con.executescript(
        """
        CREATE TABLE notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content_html TEXT NOT NULL DEFAULT '',
            content_plain TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_deleted INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE diagrams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            note_id INTEGER NOT NULL UNIQUE,
            data_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        INSERT INTO notes(title, content_html, content_plain, created_at, updated_at, is_deleted)
        VALUES ('Legacy', '<p>kept</p>', 'kept', '2026-01-01', '2026-01-01', 0);
        PRAGMA user_version = 1;
        """
    )
    con.commit(); con.close()

    db = Database(db_path)
    try:
        note = db.get_note(1)
        assert note is not None
        assert note.title == "Legacy"
        assert note.uuid
        assert note.project_id is not None
        assert db.connection.execute("PRAGMA user_version").fetchone()[0] == Database.SCHEMA_VERSION
        assert (tmp_path / "legacy.pre-v2.backup.db").exists()
    finally:
        db.close()


def test_parse_github_remote_supports_ssh_and_https() -> None:
    assert parse_github_remote("git@github.com:acme/backend.git") == ("acme", "backend")
    assert parse_github_remote("https://github.com/acme/backend.git") == ("acme", "backend")
    assert parse_github_remote("https://gitlab.com/acme/backend.git") == (None, None)


def test_resource_scope_matching(tmp_path: Path) -> None:
    db = Database(tmp_path / "links.db")
    try:
        project = db.create_project("API")
        note = db.create_note(project_id=project.id)
        repo = db.add_repository(project.id, local_path=str(tmp_path / "repo"))
        directory = db.add_resource_link(note.id, repo.id, "directory", "src/auth", baseline_sha="a")
        file_link = db.add_resource_link(note.id, repo.id, "file", "src/db.py", baseline_sha="a")
        assert resource_is_affected(directory, ["src/auth/session.py"])
        assert not resource_is_affected(directory, ["src/other.py"])
        assert resource_is_affected(file_link, ["src/db.py"])
        assert not resource_is_affected(file_link, ["src/db.py.old"])
    finally:
        db.close()


def test_local_repository_scan_marks_link_needs_review(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    _init_repo(repo_path)
    (repo_path / "src").mkdir()
    (repo_path / "src" / "auth.py").write_text("VERSION = 1\n", encoding="utf-8")
    (repo_path / "README.md").write_text("hello\n", encoding="utf-8")
    _git(repo_path, "add", ".")
    _git(repo_path, "commit", "-m", "initial")
    info = inspect_repository(repo_path)

    db = Database(tmp_path / "devnest.db")
    try:
        project = db.create_project("Backend")
        note = db.create_note("Auth decision", project_id=project.id, note_kind="decision")
        repo = db.add_repository(
            project.id, local_path=str(info.root), github_owner=info.github_owner,
            github_repo=info.github_repo, default_branch=info.branch,
        )
        db.update_repository(repo.id, last_seen_sha=info.head_sha)
        link = db.add_resource_link(note.id, repo.id, "file", "src/auth.py", baseline_sha=info.head_sha)

        # An unrelated commit must not mark this link.
        (repo_path / "README.md").write_text("changed\n", encoding="utf-8")
        _git(repo_path, "add", "."); _git(repo_path, "commit", "-m", "docs")
        result = RepositoryScanner(db).scan_repository(repo.id)
        assert result.error is None
        assert not db.get_resource_link(link.id).needs_review  # type: ignore[union-attr]

        # A commit touching the linked file must mark it Needs Review from the original baseline.
        (repo_path / "src" / "auth.py").write_text("VERSION = 2\n", encoding="utf-8")
        _git(repo_path, "add", "."); _git(repo_path, "commit", "-m", "change auth")
        result = RepositoryScanner(db).scan_repository(repo.id)
        updated = db.get_resource_link(link.id)
        assert result.error is None
        assert updated is not None and updated.needs_review
        assert updated.change_count >= 2  # baseline spans both commits

        head = _git(repo_path, "rev-parse", "HEAD")
        db.mark_note_reviewed(note.id, repo.id, head)
        reviewed = db.get_resource_link(link.id)
        assert reviewed is not None and not reviewed.needs_review
        assert reviewed.baseline_sha == head
    finally:
        db.close()


def test_github_repository_listing_is_limited_to_app_installations(monkeypatch) -> None:
    from app.services.github_client import GitHubClient

    client = GitHubClient("Iv1.test")
    monkeypatch.setattr(client, "access_token", lambda: "token")

    def fake_request(url: str, **_kwargs):
        if url.startswith("https://api.github.com/user/installations?"):
            return {"installations": [{"id": 10}, {"id": 20}]}
        if "/user/installations/10/repositories" in url:
            return {"repositories": [{"id": 1, "full_name": "acme/backend"}]}
        if "/user/installations/20/repositories" in url:
            return {"repositories": [{"id": 2, "full_name": "me/frontend"}]}
        raise AssertionError(url)

    monkeypatch.setattr(client, "_request", fake_request)
    repos = client.list_repositories()
    assert [repo["full_name"] for repo in repos] == ["acme/backend", "me/frontend"]
    assert repos[0]["_devnest_installation_id"] == 10
    assert repos[1]["_devnest_installation_id"] == 20

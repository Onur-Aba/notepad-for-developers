from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.database import Database


def _create_v1_database(path: Path) -> None:
    connection = sqlite3.connect(path)
    with connection:
        connection.executescript(
            """
            CREATE TABLE notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content_html TEXT NOT NULL DEFAULT '',
                content_plain TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_deleted INTEGER NOT NULL DEFAULT 0 CHECK (is_deleted IN (0, 1))
            );
            CREATE TABLE diagrams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER NOT NULL UNIQUE,
                data_json TEXT NOT NULL DEFAULT '{"items":[],"edges":[],"paths":[]}',
                updated_at TEXT NOT NULL,
                FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE
            );
            CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            PRAGMA user_version = 1;
            """
        )
        connection.execute(
            "INSERT INTO notes(title,content_html,content_plain,created_at,updated_at,is_deleted) VALUES (?,?,?,?,?,0)",
            ("Legacy", "<p><b>Hello</b></p>", "Hello", "2025-01-01T00:00:00+00:00", "2025-01-02T00:00:00+00:00"),
        )
        connection.execute(
            "INSERT INTO notes(title,content_html,content_plain,created_at,updated_at,is_deleted) VALUES (?,?,?,?,?,1)",
            ("Deleted", "<p>Trash</p>", "Trash", "2025-01-03T00:00:00+00:00", "2025-01-04T00:00:00+00:00"),
        )
        diagram = {"version": 5, "items": [{"type": "shape", "shape": "square", "id": "stable", "x": 1, "y": 2, "text": "Legacy", "width": 90, "height": 90}], "edges": [], "paths": [], "connectors": []}
        connection.execute(
            "INSERT INTO diagrams(note_id,data_json,updated_at) VALUES (1,?,?)",
            (json.dumps(diagram), "2025-01-02T00:00:00+00:00"),
        )
    connection.close()


def test_legacy_v1_migration_preserves_all_data(tmp_path: Path) -> None:
    path = tmp_path / "legacy.db"
    _create_v1_database(path)
    db = Database(path)
    assert db.connection.execute("PRAGMA user_version").fetchone()[0] == Database.SCHEMA_VERSION
    note = db.get_note(1)
    assert note is not None
    assert note.content_html == "<p><b>Hello</b></p>"
    assert note.content_plain == "Hello"
    assert note.created_at == "2025-01-01T00:00:00+00:00"
    assert note.project_id is not None
    deleted = db.get_note(2, include_deleted=True)
    assert deleted is not None and deleted.is_deleted
    assert db.get_diagram(1)["items"][0]["id"] == "stable"
    assert db.get_project(note.project_id).name == "Personal Workspace"
    assert list(tmp_path.glob("legacy.db.backup-*-v1"))


def test_domain_crud_indexes_and_token_absence(tmp_path: Path) -> None:
    db = Database(tmp_path / "devnest.db")
    project = db.create_project("Payment API", "Payments")
    repo = db.upsert_repository(name="payment-api", owner="acme", full_name="acme/payment-api", default_branch="main")
    db.link_repository_to_project(project.id, repo.id, "main")
    note = db.create_note("Auth", project_id=project.id)
    link = db.add_resource_link(project.id, "note", note.id, repo.id, "directory", "backend/auth/")
    baseline = db.upsert_review_baseline("note", note.id, repo.id, "a" * 40, "main")
    decision = db.create_decision(project.id, "Use PostgreSQL", "accepted")
    assert decision.decision_key == "DEC-001"
    assert db.get_resource_link(link.id).target_value == "backend/auth/"
    assert baseline.baseline_sha == "a" * 40
    assert {"projects", "repositories", "resource_links", "review_baselines", "repository_changes", "github_accounts"} <= db.table_names()
    assert {"idx_notes_project_id", "idx_resource_links_repository", "idx_repository_changes_lookup"} <= db.index_names()
    schema_text = "\n".join(str(r[0]) for r in db.connection.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL"))
    assert "access_token" not in schema_text
    assert "refresh_token" not in schema_text


def test_resource_unlink_cleans_orphan_baseline_without_deleting_note(tmp_path: Path) -> None:
    db = Database(tmp_path / "devnest.db")
    project_id = db.default_project_id()
    note = db.create_note("A", project_id=project_id)
    repo = db.upsert_repository(name="local", local_git_root=str(tmp_path), github_access_state="local_only")
    db.link_repository_to_project(project_id, repo.id)
    link = db.add_resource_link(project_id, "note", note.id, repo.id, "file", "a.py")
    db.upsert_review_baseline("note", note.id, repo.id, "b" * 40, "main")
    db.remove_resource_link(link.id)
    assert db.get_note(note.id) is not None
    assert db.get_review_baseline("note", note.id, repo.id) is None


def test_repositories_are_sorted_by_most_recent_github_push(tmp_path: Path) -> None:
    db = Database(tmp_path / "devnest.db")
    old = db.upsert_repository(
        name="old", full_name="acme/old", github_repo_id=1,
        last_pushed_at="2026-01-01T10:00:00Z",
    )
    newest = db.upsert_repository(
        name="newest", full_name="acme/newest", github_repo_id=2,
        last_pushed_at="2026-08-31T18:00:00Z",
    )
    middle = db.upsert_repository(
        name="middle", full_name="acme/middle", github_repo_id=3,
        last_pushed_at="2026-04-15T12:00:00Z",
    )
    no_push = db.upsert_repository(name="unknown", full_name="acme/unknown", github_repo_id=4)

    assert [repo.id for repo in db.list_repositories()] == [newest.id, middle.id, old.id, no_push.id]


def test_deleting_decision_cleans_links_and_does_not_reuse_key(tmp_path: Path) -> None:
    db = Database(tmp_path / "devnest.db")
    project_id = db.default_project_id()
    repo = db.upsert_repository(name="repo", local_git_root=str(tmp_path), github_access_state="local_only")
    db.link_repository_to_project(project_id, repo.id)
    first = db.create_decision(project_id, "First")
    second = db.create_decision(project_id, "Second")
    link = db.add_resource_link(project_id, "decision", second.id, repo.id, "file", "a.py")
    db.upsert_review_baseline("decision", second.id, repo.id, "a" * 40, "main")

    db.delete_decision(second.id)

    assert db.get_decision(second.id) is None
    assert db.get_resource_link(link.id) is None
    assert db.get_review_baseline("decision", second.id, repo.id) is None
    replacement = db.create_decision(project_id, "Third")
    assert first.decision_key == "DEC-001"
    assert replacement.decision_key == "DEC-003"

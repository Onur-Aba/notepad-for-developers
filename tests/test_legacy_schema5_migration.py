from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.database import Database


def _create_legacy_v5_database(path: Path) -> None:
    con = sqlite3.connect(path)
    with con:
        con.executescript(
            """
            CREATE TABLE notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content_html TEXT NOT NULL DEFAULT '',
                content_plain TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_deleted INTEGER NOT NULL DEFAULT 0 CHECK (is_deleted IN (0, 1)),
                uuid TEXT,
                project_id INTEGER REFERENCES projects(id),
                note_kind TEXT NOT NULL DEFAULT 'note'
            );
            CREATE TABLE diagrams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER NOT NULL UNIQUE,
                data_json TEXT NOT NULL DEFAULT '{"items":[],"edges":[],"paths":[]}',
                updated_at TEXT NOT NULL,
                FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE
            );
            CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE repositories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                uuid TEXT NOT NULL UNIQUE,
                provider TEXT NOT NULL DEFAULT 'git',
                local_path TEXT,
                github_owner TEXT,
                github_repo TEXT,
                default_branch TEXT,
                last_seen_sha TEXT,
                last_scanned_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                github_installation_id INTEGER,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                UNIQUE(project_id, local_path),
                UNIQUE(project_id, github_owner, github_repo)
            );
            CREATE TABLE resource_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER NOT NULL,
                repository_id INTEGER NOT NULL,
                resource_type TEXT NOT NULL CHECK(resource_type IN ('repository','directory','file')),
                resource_value TEXT NOT NULL DEFAULT '',
                display_label TEXT NOT NULL DEFAULT '',
                diagram_item_id TEXT,
                baseline_sha TEXT,
                last_checked_sha TEXT,
                needs_review INTEGER NOT NULL DEFAULT 0 CHECK(needs_review IN (0,1)),
                change_count INTEGER NOT NULL DEFAULT 0,
                last_changed_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE,
                FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
            );
            CREATE TABLE external_refs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER NOT NULL,
                repository_id INTEGER NOT NULL,
                ref_type TEXT NOT NULL CHECK(ref_type IN ('pull_request','commit','branch')),
                ref_value TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                url TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE,
                FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE,
                UNIQUE(note_id, repository_id, ref_type, ref_value)
            );
            CREATE TABLE repository_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repository_id INTEGER NOT NULL,
                from_sha TEXT,
                to_sha TEXT NOT NULL,
                changed_files_json TEXT NOT NULL DEFAULT '[]',
                commit_count INTEGER NOT NULL DEFAULT 0,
                detected_at TEXT NOT NULL,
                FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
            );
            CREATE TABLE review_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER NOT NULL,
                repository_id INTEGER NOT NULL,
                reviewed_sha TEXT NOT NULL,
                reviewed_at TEXT NOT NULL,
                FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE,
                FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
            );
            PRAGMA user_version = 5;
            """
        )
        con.execute(
            "INSERT INTO projects(id,uuid,name,created_at,updated_at) VALUES (1,'p1','Legacy Project','2026-01-01','2026-01-02')"
        )
        con.execute(
            """INSERT INTO notes(id,title,content_html,content_plain,created_at,updated_at,is_deleted,uuid,project_id,note_kind)
               VALUES (1,'Legacy note','<p>Hello</p>','Hello','2026-01-01','2026-01-02',0,'n1',1,'note')"""
        )
        con.execute(
            """INSERT INTO notes(id,title,content_html,content_plain,created_at,updated_at,is_deleted,uuid,project_id,note_kind)
               VALUES (2,'Use SQLite','<p>Decision</p>','Decision','2026-01-03','2026-01-04',0,'n2',1,'decision')"""
        )
        con.execute(
            "INSERT INTO diagrams(note_id,data_json,updated_at) VALUES (1,?,?)",
            (json.dumps({"items":[{"id":"node-1","type":"shape"}],"edges":[],"paths":[]}), "2026-01-02"),
        )
        con.execute(
            """INSERT INTO repositories(id,project_id,uuid,provider,local_path,github_owner,github_repo,default_branch,last_seen_sha,last_scanned_at,created_at,updated_at,github_installation_id)
               VALUES (1,1,'r1','git','C:\\code\\legacy','acme','legacy','main','headsha','2026-01-05','2026-01-01','2026-01-05',123)"""
        )
        con.execute(
            """INSERT INTO resource_links(id,note_id,repository_id,resource_type,resource_value,display_label,diagram_item_id,
               baseline_sha,last_checked_sha,needs_review,change_count,last_changed_at,created_at,updated_at)
               VALUES (1,1,1,'directory','backend/auth','Auth dir',NULL,'basesha','headsha',1,2,'2026-01-05','2026-01-02','2026-01-05')"""
        )
        con.execute(
            """INSERT INTO resource_links(id,note_id,repository_id,resource_type,resource_value,display_label,diagram_item_id,
               baseline_sha,last_checked_sha,needs_review,change_count,last_changed_at,created_at,updated_at)
               VALUES (2,1,1,'file','backend/auth/session.py','Session','node-1','basesha','headsha',1,1,'2026-01-05','2026-01-02','2026-01-05')"""
        )
        con.execute(
            "INSERT INTO external_refs(note_id,repository_id,ref_type,ref_value,title,url,created_at) VALUES (2,1,'commit','abc123','Implementation','https://github.com/acme/legacy/commit/abc123','2026-01-06')"
        )
        con.execute(
            "INSERT INTO external_refs(note_id,repository_id,ref_type,ref_value,title,url,created_at) VALUES (2,1,'pull_request','#42','PR 42','https://github.com/acme/legacy/pull/42','2026-01-06')"
        )
        con.execute(
            "INSERT INTO repository_changes(repository_id,from_sha,to_sha,changed_files_json,commit_count,detected_at) VALUES (1,'basesha','headsha',?,2,'2026-01-05')",
            (json.dumps(["backend/auth/session.py", "backend/auth/token.py"]),),
        )
        con.execute(
            "INSERT INTO review_events(note_id,repository_id,reviewed_sha,reviewed_at) VALUES (1,1,'basesha','2026-01-02')"
        )
    con.close()


def test_legacy_schema5_is_converted_to_normalized_schema6(tmp_path: Path) -> None:
    path = tmp_path / "legacy5.db"
    _create_legacy_v5_database(path)

    db = Database(path)
    assert db.connection.execute("PRAGMA user_version").fetchone()[0] == 6

    # The exact crash from the report is fixed: description now exists and is readable.
    project = db.get_project(1)
    assert project is not None
    assert project.name == "Legacy Project"
    assert project.description == ""

    # Notes and diagrams remain intact.
    note = db.get_note(1)
    assert note is not None and note.content_html == "<p>Hello</p>"
    assert db.get_diagram(1)["items"][0]["id"] == "node-1"

    # Old repository ownership is normalized into the junction model.
    repo = db.get_repository(1)
    assert repo is not None
    assert repo.full_name == "acme/legacy"
    assert repo.local_git_root == r"C:\code\legacy"
    assert db.list_repositories(1)[0].id == 1

    # Old note-kind decisions are promoted without changing their note content.
    decisions = db.list_decisions(1)
    assert len(decisions) == 1
    assert decisions[0].title == "Use SQLite"
    assert decisions[0].decision_key == "DEC-001"

    # Old resource links and baselines survive in the new generic model.
    note_links = db.list_resource_links("note", 1)
    assert any(link.target_type == "directory" and link.target_value == "backend/auth" for link in note_links)
    diagram_links = db.list_resource_links("diagram_item", "node-1", 1)
    assert len(diagram_links) == 1
    baseline = db.get_review_baseline("note", 1, 1)
    assert baseline is not None and baseline.baseline_sha == "basesha"

    # Commit / PR refs tied to old decisions are retained.
    decision_links = db.list_resource_links("decision", decisions[0].id)
    assert {link.target_type for link in decision_links} >= {"commit", "pull_request"}
    assert db.connection.execute("SELECT COUNT(*) FROM decision_commits").fetchone()[0] == 1
    assert db.connection.execute("SELECT COUNT(*) FROM decision_pull_requests").fetchone()[0] == 1

    # Old changed-file cache is converted into the structured v6 form.
    change = db.get_repository_change(1, "basesha", "headsha", "local_git")
    assert change is not None
    assert {item.path for item in change.changed_files} == {"backend/auth/session.py", "backend/auth/token.py"}

    # Migration backup exists and foreign keys are clean.
    assert list(tmp_path.glob("legacy5.db.backup-*-v5"))
    assert db.connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_normalized_schema4_can_advance_through_bridge_versions(tmp_path: Path) -> None:
    path = tmp_path / "normalized.db"
    db = Database(path)
    assert db.connection.execute("PRAGMA user_version").fetchone()[0] == 6
    project = db.create_project("After migration", "works")
    assert db.get_project(project.id).description == "works"

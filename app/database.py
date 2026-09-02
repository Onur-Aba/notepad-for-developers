from __future__ import annotations

import json
import logging
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from app.constants import DEFAULT_NOTE_TITLE
from app.models import (
    ChangedFile,
    CommitInfo,
    Decision,
    GitHubAccount,
    GitHubInstallation,
    Note,
    NoteSummary,
    Project,
    ProjectRepository,
    ProjectSummary,
    PullRequestInfo,
    Repository,
    RepositoryChange,
    ResourceLink,
    ReviewBaseline,
)

logger = logging.getLogger(__name__)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class DatabaseError(RuntimeError):
    pass


class Database:
    """SQLite persistence with sequential, backward-compatible migrations.

    Version 1 is the original DevNest notes/diagrams/settings schema. Newer
    versions only add data structures or columns; legacy note/diagram payloads
    are never rewritten.
    """

    SCHEMA_VERSION = 8

    def __init__(self, path: Path | str | None = None) -> None:
        if path is None:
            from app.paths import database_path

            self.path = database_path()
        else:
            self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.connection = sqlite3.connect(self.path, timeout=5.0)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.connection.execute("PRAGMA journal_mode = WAL")
            self.connection.execute("PRAGMA synchronous = NORMAL")
            self._migrate()
        except DatabaseError:
            raise
        except sqlite3.Error as exc:
            raise DatabaseError(f"Database could not be opened: {exc}") from exc

    # ------------------------------------------------------------------
    # Migration
    # ------------------------------------------------------------------
    def _migrate(self) -> None:
        try:
            version = int(self.connection.execute("PRAGMA user_version").fetchone()[0])
            if version > self.SCHEMA_VERSION:
                raise DatabaseError(
                    f"Database schema {version} is newer than supported schema {self.SCHEMA_VERSION}."
                )
            if 0 < version < self.SCHEMA_VERSION:
                self._backup_before_migration(version)
            while version < self.SCHEMA_VERSION:
                target = version + 1
                logger.info("Migrating DevNest database schema v%s -> v%s", version, target)
                migration = getattr(self, f"_migrate_to_v{target}")
                migration()
                version = target
        except DatabaseError:
            raise
        except sqlite3.Error as exc:
            raise DatabaseError(f"Database migration failed: {exc}") from exc

    def _backup_before_migration(self, version: int) -> None:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = self.path.with_name(f"{self.path.name}.backup-{stamp}-v{version}")
        suffix = 1
        while backup_path.exists():
            backup_path = self.path.with_name(f"{self.path.name}.backup-{stamp}-v{version}-{suffix}")
            suffix += 1
        try:
            destination = sqlite3.connect(backup_path)
            try:
                self.connection.backup(destination)
            finally:
                destination.close()
            logger.info("Created pre-migration database backup: %s", backup_path)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Database backup before migration failed: {exc}") from exc

    def _migrate_to_v1(self) -> None:
        with self.connection:
            self.connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content_html TEXT NOT NULL DEFAULT '',
                    content_plain TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_deleted INTEGER NOT NULL DEFAULT 0 CHECK (is_deleted IN (0, 1))
                );

                CREATE INDEX IF NOT EXISTS idx_notes_deleted_updated
                    ON notes(is_deleted, updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_notes_title
                    ON notes(title COLLATE NOCASE);

                CREATE TABLE IF NOT EXISTS diagrams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_id INTEGER NOT NULL UNIQUE,
                    data_json TEXT NOT NULL DEFAULT '{"items":[],"edges":[],"paths":[]}',
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                PRAGMA user_version = 1;
                """
            )

    def _migrate_to_v2(self) -> None:
        now = utc_now_iso()
        with self.connection:
            self.connection.executescript(
                """
                CREATE TABLE projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    archived_at TEXT
                );

                CREATE TABLE repositories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    github_repo_id INTEGER UNIQUE,
                    github_node_id TEXT,
                    owner TEXT,
                    name TEXT NOT NULL,
                    full_name TEXT UNIQUE,
                    html_url TEXT,
                    clone_url TEXT,
                    default_branch TEXT,
                    is_private INTEGER NOT NULL DEFAULT 0 CHECK (is_private IN (0, 1)),
                    installation_id INTEGER,
                    local_path TEXT,
                    local_git_root TEXT,
                    remote_name TEXT,
                    language TEXT,
                    description TEXT,
                    last_pushed_at TEXT,
                    last_seen_sha TEXT,
                    last_checked_at TEXT,
                    last_successful_check_at TEXT,
                    last_check_source TEXT,
                    github_access_state TEXT NOT NULL DEFAULT 'unknown',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE project_repositories (
                    project_id INTEGER NOT NULL,
                    repository_id INTEGER NOT NULL,
                    monitored_branch TEXT,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(project_id, repository_id),
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
                );

                CREATE INDEX idx_projects_archived_updated
                    ON projects(archived_at, updated_at DESC);
                CREATE INDEX idx_repositories_github_repo_id
                    ON repositories(github_repo_id);
                CREATE INDEX idx_repositories_full_name
                    ON repositories(full_name COLLATE NOCASE);
                CREATE INDEX idx_project_repositories_project
                    ON project_repositories(project_id);
                """
            )
            project_id = self.connection.execute(
                "INSERT INTO projects(name, description, created_at, updated_at) VALUES (?, ?, ?, ?)",
                ("Personal Workspace", "Migrated and local DevNest knowledge.", now, now),
            ).lastrowid
            columns = {str(row[1]) for row in self.connection.execute("PRAGMA table_info(notes)").fetchall()}
            if "project_id" not in columns:
                self.connection.execute("ALTER TABLE notes ADD COLUMN project_id INTEGER REFERENCES projects(id)")
            self.connection.execute("UPDATE notes SET project_id = ? WHERE project_id IS NULL", (project_id,))
            self.connection.execute("CREATE INDEX IF NOT EXISTS idx_notes_project_id ON notes(project_id)")
            self.connection.execute("PRAGMA user_version = 2")

    def _migrate_to_v3(self) -> None:
        with self.connection:
            self.connection.executescript(
                """
                CREATE TABLE decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    note_id INTEGER NOT NULL UNIQUE,
                    decision_key TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'proposed',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(project_id, decision_key),
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE RESTRICT,
                    FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE
                );

                CREATE TABLE resource_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    resource_parent_id TEXT NOT NULL DEFAULT '',
                    repository_id INTEGER NOT NULL,
                    target_type TEXT NOT NULL,
                    target_value TEXT NOT NULL DEFAULT '',
                    github_node_id TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    UNIQUE(resource_type, resource_id, resource_parent_id, repository_id, target_type, target_value),
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
                );

                CREATE TABLE review_baselines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    resource_parent_id TEXT NOT NULL DEFAULT '',
                    repository_id INTEGER NOT NULL,
                    baseline_sha TEXT NOT NULL,
                    branch TEXT,
                    reviewed_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(resource_type, resource_id, resource_parent_id, repository_id),
                    FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
                );

                CREATE INDEX idx_decisions_project_id ON decisions(project_id);
                CREATE INDEX idx_resource_links_resource
                    ON resource_links(resource_type, resource_id, resource_parent_id);
                CREATE INDEX idx_resource_links_repository
                    ON resource_links(repository_id, target_type, target_value);
                CREATE INDEX idx_review_baselines_resource
                    ON review_baselines(resource_type, resource_id, resource_parent_id, repository_id);

                PRAGMA user_version = 3;
                """
            )

    def _migrate_to_v4(self) -> None:
        with self.connection:
            self.connection.executescript(
                """
                CREATE TABLE github_accounts (
                    github_user_id INTEGER PRIMARY KEY,
                    login TEXT NOT NULL,
                    avatar_url TEXT,
                    connected_at TEXT NOT NULL,
                    last_validated_at TEXT
                );

                CREATE TABLE github_installations (
                    id INTEGER PRIMARY KEY,
                    account_login TEXT NOT NULL,
                    account_type TEXT NOT NULL,
                    account_avatar_url TEXT,
                    target_type TEXT,
                    last_synced_at TEXT NOT NULL
                );

                CREATE TABLE repository_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repository_id INTEGER NOT NULL,
                    from_sha TEXT NOT NULL,
                    to_sha TEXT NOT NULL,
                    source TEXT NOT NULL,
                    commit_count INTEGER NOT NULL DEFAULT 0,
                    changed_files_json TEXT NOT NULL DEFAULT '[]',
                    commits_json TEXT NOT NULL DEFAULT '[]',
                    pull_requests_json TEXT NOT NULL DEFAULT '[]',
                    detected_at TEXT NOT NULL,
                    UNIQUE(repository_id, from_sha, to_sha, source),
                    FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
                );

                CREATE TABLE decision_commits (
                    decision_id INTEGER NOT NULL,
                    repository_id INTEGER NOT NULL,
                    commit_sha TEXT NOT NULL,
                    github_url TEXT,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(decision_id, repository_id, commit_sha),
                    FOREIGN KEY(decision_id) REFERENCES decisions(id) ON DELETE CASCADE,
                    FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
                );

                CREATE TABLE decision_pull_requests (
                    decision_id INTEGER NOT NULL,
                    repository_id INTEGER NOT NULL,
                    pull_number INTEGER NOT NULL,
                    github_node_id TEXT,
                    title TEXT,
                    state TEXT,
                    url TEXT,
                    updated_at TEXT,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(decision_id, repository_id, pull_number),
                    FOREIGN KEY(decision_id) REFERENCES decisions(id) ON DELETE CASCADE,
                    FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
                );

                CREATE TABLE activity_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    event_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    detail TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE INDEX idx_repository_changes_lookup
                    ON repository_changes(repository_id, from_sha, to_sha, source);
                CREATE INDEX idx_activity_project_created
                    ON activity_events(project_id, created_at DESC);

                PRAGMA user_version = 4;
                """
            )

    def _migrate_to_v5(self) -> None:
        """Compatibility marker.

        DevNest 2.0 initially used schema 4 for the normalized project/repository
        model, while an earlier DevNest branch had already shipped a different
        schema numbered 5.  Version 5 is therefore reserved as a bridge.  The
        actual compatibility conversion happens in v6 after inspecting the
        table shapes instead of trusting the number alone.
        """
        with self.connection:
            self.connection.execute("PRAGMA user_version = 5")

    def _migrate_to_v6(self) -> None:
        if self._is_legacy_v5_schema():
            self._migrate_legacy_v5_to_v6()
            return
        # A database produced by the normalized v1-v4 migrations (or by the
        # short-lived schema-5 compatibility build) already has the v6 table
        # shapes.  Only the schema marker needs to advance.
        with self.connection:
            self.connection.execute("PRAGMA user_version = 6")

    def _migrate_to_v7(self) -> None:
        """Add reversible project-level Trash without destroying workspace data.

        A project in Trash keeps its repository mappings, resource links, review
        baselines, decisions and diagrams intact. Notes are hidden using the
        existing is_deleted flag, while two marker columns remember whether a
        note was already in Trash before the project was removed.
        """
        with self.connection:
            project_columns = {str(row[1]) for row in self.connection.execute("PRAGMA table_info(projects)").fetchall()}
            if "trashed_at" not in project_columns:
                self.connection.execute("ALTER TABLE projects ADD COLUMN trashed_at TEXT")
            note_columns = {str(row[1]) for row in self.connection.execute("PRAGMA table_info(notes)").fetchall()}
            if "trashed_with_project_id" not in note_columns:
                self.connection.execute("ALTER TABLE notes ADD COLUMN trashed_with_project_id INTEGER")
            if "project_trash_was_deleted" not in note_columns:
                self.connection.execute("ALTER TABLE notes ADD COLUMN project_trash_was_deleted INTEGER NOT NULL DEFAULT 0")
            self.connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_projects_trash ON projects(trashed_at, archived_at, updated_at DESC)"
            )
            self.connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_notes_project_trash ON notes(trashed_with_project_id, is_deleted, updated_at DESC)"
            )
            self.connection.execute("PRAGMA user_version = 7")

    def _migrate_to_v8(self) -> None:
        """Persistent timelines, tags, favorites, recent work, notifications and backlinks."""
        with self.connection:
            activity_columns = {str(row[1]) for row in self.connection.execute("PRAGMA table_info(activity_events)").fetchall()}
            for column, definition in (
                ("repository_id", "INTEGER"),
                ("resource_type", "TEXT"),
                ("resource_id", "TEXT"),
                ("metadata_json", "TEXT NOT NULL DEFAULT '{}'"),
            ):
                if column not in activity_columns:
                    self.connection.execute(f"ALTER TABLE activity_events ADD COLUMN {column} {definition}")

            self.connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS decision_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    detail TEXT NOT NULL DEFAULT '',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(decision_id) REFERENCES decisions(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS review_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    resource_parent_id TEXT NOT NULL DEFAULT '',
                    repository_id INTEGER NOT NULL,
                    baseline_sha TEXT NOT NULL,
                    branch TEXT,
                    reviewed_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS resource_tags (
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    tag_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(resource_type, resource_id, tag_id),
                    FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS favorites (
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    project_id INTEGER,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(resource_type, resource_id),
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS recent_items (
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    project_id INTEGER,
                    title TEXT NOT NULL,
                    detail TEXT NOT NULL DEFAULT '',
                    opened_at TEXT NOT NULL,
                    PRIMARY KEY(resource_type, resource_id),
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    event_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    detail TEXT NOT NULL DEFAULT '',
                    notification_key TEXT UNIQUE,
                    is_read INTEGER NOT NULL DEFAULT 0 CHECK (is_read IN (0, 1)),
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_activity_project_repo_created
                    ON activity_events(project_id, repository_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_activity_resource_created
                    ON activity_events(resource_type, resource_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_decision_history_created
                    ON decision_history(decision_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_review_history_resource
                    ON review_history(resource_type, resource_id, resource_parent_id, reviewed_at DESC);
                CREATE INDEX IF NOT EXISTS idx_resource_tags_resource
                    ON resource_tags(resource_type, resource_id);
                CREATE INDEX IF NOT EXISTS idx_recent_project_opened
                    ON recent_items(project_id, opened_at DESC);
                CREATE INDEX IF NOT EXISTS idx_notifications_unread
                    ON notifications(is_read, created_at DESC);

                PRAGMA user_version = 8;
                """
            )

            # Seed the new review-history table from the current baselines so an
            # upgraded workspace immediately has a useful first historical point.
            self.connection.execute(
                """INSERT INTO review_history(project_id,resource_type,resource_id,resource_parent_id,repository_id,baseline_sha,branch,reviewed_at)
                   SELECT rl.project_id, rb.resource_type, rb.resource_id, rb.resource_parent_id, rb.repository_id,
                          rb.baseline_sha, rb.branch, rb.reviewed_at
                   FROM review_baselines rb
                   JOIN resource_links rl ON rl.resource_type=rb.resource_type AND rl.resource_id=rb.resource_id
                        AND rl.resource_parent_id=rb.resource_parent_id AND rl.repository_id=rb.repository_id
                   WHERE NOT EXISTS (
                       SELECT 1 FROM review_history h WHERE h.resource_type=rb.resource_type AND h.resource_id=rb.resource_id
                         AND h.resource_parent_id=rb.resource_parent_id AND h.repository_id=rb.repository_id
                         AND h.baseline_sha=rb.baseline_sha AND h.reviewed_at=rb.reviewed_at
                   )
                   GROUP BY rb.id"""
            )

    def _is_legacy_v5_schema(self) -> bool:
        """Detect the *shape* of the older schema-5 database.

        The old schema used projects.uuid and repositories.project_id /
        github_owner / github_repo.  The newer normalized model instead uses a
        project_repositories junction and owner/full_name repository metadata.
        Looking at columns makes this safe even when a previous build changed
        PRAGMA user_version without changing the tables.
        """
        def columns(table: str) -> set[str]:
            exists = self.connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()
            if not exists:
                return set()
            return {str(row[1]) for row in self.connection.execute(f"PRAGMA table_info({table})").fetchall()}

        project_columns = columns("projects")
        repository_columns = columns("repositories")
        resource_columns = columns("resource_links")
        return bool(
            ("uuid" in project_columns and "description" not in project_columns)
            or ({"project_id", "github_owner", "github_repo"} <= repository_columns
                and "full_name" not in repository_columns)
            or ({"note_id", "resource_value", "baseline_sha"} <= resource_columns
                and "resource_id" not in resource_columns)
        )

    def _migrate_legacy_v5_to_v6(self) -> None:
        """Convert the older, incompatible schema 5 into the normalized model.

        This migration is intentionally data-preserving: project/note ids stay
        stable, repository ids are retained where possible, old note-based
        decisions become first-class decisions, resource baselines are moved to
        review_baselines, and old commit/PR/branch references become generic
        resource links.  Legacy review history is retained in a compatibility
        table because v6 does not otherwise expose historical review events.
        """
        def table_exists(name: str) -> bool:
            return self.connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
            ).fetchone() is not None

        def rows(name: str) -> list[dict[str, object]]:
            if not table_exists(name):
                return []
            return [dict(row) for row in self.connection.execute(f"SELECT * FROM {name}").fetchall()]

        legacy_projects = rows("projects")
        legacy_repositories = rows("repositories")
        legacy_links = rows("resource_links")
        legacy_changes = rows("repository_changes")
        legacy_external_refs = rows("external_refs")
        legacy_review_events = rows("review_events")

        note_columns = {
            str(row[1]) for row in self.connection.execute("PRAGMA table_info(notes)").fetchall()
        }
        select_note_columns = "id, title, created_at, updated_at, project_id"
        if "note_kind" in note_columns:
            select_note_columns += ", note_kind"
        legacy_notes = [
            dict(row) for row in self.connection.execute(
                f"SELECT {select_note_columns} FROM notes ORDER BY id"
            ).fetchall()
        ]

        now = utc_now_iso()
        # PRAGMA foreign_keys cannot be toggled while a transaction is active.
        self.connection.commit()
        self.connection.execute("PRAGMA foreign_keys = OFF")
        try:
            with self.connection:
                # Remove only the incompatible schema-5 domain tables. Notes,
                # diagrams and settings are deliberately left untouched.
                self.connection.executescript(
                    """
                    DROP TABLE IF EXISTS external_refs;
                    DROP TABLE IF EXISTS review_events;
                    DROP TABLE IF EXISTS resource_links;
                    DROP TABLE IF EXISTS repository_changes;
                    DROP TABLE IF EXISTS project_repositories;
                    DROP TABLE IF EXISTS repositories;
                    DROP TABLE IF EXISTS decisions;
                    DROP TABLE IF EXISTS review_baselines;
                    DROP TABLE IF EXISTS decision_commits;
                    DROP TABLE IF EXISTS decision_pull_requests;
                    DROP TABLE IF EXISTS github_accounts;
                    DROP TABLE IF EXISTS github_installations;
                    DROP TABLE IF EXISTS activity_events;
                    DROP TABLE IF EXISTS projects;

                    CREATE TABLE projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT NOT NULL DEFAULT '',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        archived_at TEXT
                    );

                    CREATE TABLE repositories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        github_repo_id INTEGER UNIQUE,
                        github_node_id TEXT,
                        owner TEXT,
                        name TEXT NOT NULL,
                        full_name TEXT UNIQUE,
                        html_url TEXT,
                        clone_url TEXT,
                        default_branch TEXT,
                        is_private INTEGER NOT NULL DEFAULT 0 CHECK (is_private IN (0, 1)),
                        installation_id INTEGER,
                        local_path TEXT,
                        local_git_root TEXT,
                        remote_name TEXT,
                        language TEXT,
                        description TEXT,
                        last_pushed_at TEXT,
                        last_seen_sha TEXT,
                        last_checked_at TEXT,
                        last_successful_check_at TEXT,
                        last_check_source TEXT,
                        github_access_state TEXT NOT NULL DEFAULT 'unknown',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );

                    CREATE TABLE project_repositories (
                        project_id INTEGER NOT NULL,
                        repository_id INTEGER NOT NULL,
                        monitored_branch TEXT,
                        created_at TEXT NOT NULL,
                        PRIMARY KEY(project_id, repository_id),
                        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                        FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
                    );

                    CREATE TABLE decisions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER NOT NULL,
                        note_id INTEGER NOT NULL UNIQUE,
                        decision_key TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'proposed',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        UNIQUE(project_id, decision_key),
                        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE RESTRICT,
                        FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE
                    );

                    CREATE TABLE resource_links (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER NOT NULL,
                        resource_type TEXT NOT NULL,
                        resource_id TEXT NOT NULL,
                        resource_parent_id TEXT NOT NULL DEFAULT '',
                        repository_id INTEGER NOT NULL,
                        target_type TEXT NOT NULL,
                        target_value TEXT NOT NULL DEFAULT '',
                        github_node_id TEXT,
                        metadata_json TEXT NOT NULL DEFAULT '{}',
                        created_at TEXT NOT NULL,
                        UNIQUE(resource_type, resource_id, resource_parent_id, repository_id, target_type, target_value),
                        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                        FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
                    );

                    CREATE TABLE review_baselines (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        resource_type TEXT NOT NULL,
                        resource_id TEXT NOT NULL,
                        resource_parent_id TEXT NOT NULL DEFAULT '',
                        repository_id INTEGER NOT NULL,
                        baseline_sha TEXT NOT NULL,
                        branch TEXT,
                        reviewed_at TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        UNIQUE(resource_type, resource_id, resource_parent_id, repository_id),
                        FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
                    );

                    CREATE TABLE github_accounts (
                        github_user_id INTEGER PRIMARY KEY,
                        login TEXT NOT NULL,
                        avatar_url TEXT,
                        connected_at TEXT NOT NULL,
                        last_validated_at TEXT
                    );

                    CREATE TABLE github_installations (
                        id INTEGER PRIMARY KEY,
                        account_login TEXT NOT NULL,
                        account_type TEXT NOT NULL,
                        account_avatar_url TEXT,
                        target_type TEXT,
                        last_synced_at TEXT NOT NULL
                    );

                    CREATE TABLE repository_changes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        repository_id INTEGER NOT NULL,
                        from_sha TEXT NOT NULL,
                        to_sha TEXT NOT NULL,
                        source TEXT NOT NULL,
                        commit_count INTEGER NOT NULL DEFAULT 0,
                        changed_files_json TEXT NOT NULL DEFAULT '[]',
                        commits_json TEXT NOT NULL DEFAULT '[]',
                        pull_requests_json TEXT NOT NULL DEFAULT '[]',
                        detected_at TEXT NOT NULL,
                        UNIQUE(repository_id, from_sha, to_sha, source),
                        FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
                    );

                    CREATE TABLE decision_commits (
                        decision_id INTEGER NOT NULL,
                        repository_id INTEGER NOT NULL,
                        commit_sha TEXT NOT NULL,
                        github_url TEXT,
                        created_at TEXT NOT NULL,
                        PRIMARY KEY(decision_id, repository_id, commit_sha),
                        FOREIGN KEY(decision_id) REFERENCES decisions(id) ON DELETE CASCADE,
                        FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
                    );

                    CREATE TABLE decision_pull_requests (
                        decision_id INTEGER NOT NULL,
                        repository_id INTEGER NOT NULL,
                        pull_number INTEGER NOT NULL,
                        github_node_id TEXT,
                        title TEXT,
                        state TEXT,
                        url TEXT,
                        updated_at TEXT,
                        created_at TEXT NOT NULL,
                        PRIMARY KEY(decision_id, repository_id, pull_number),
                        FOREIGN KEY(decision_id) REFERENCES decisions(id) ON DELETE CASCADE,
                        FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
                    );

                    CREATE TABLE activity_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER,
                        event_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        detail TEXT NOT NULL DEFAULT '',
                        created_at TEXT NOT NULL,
                        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                    );

                    CREATE TABLE legacy_review_events (
                        id INTEGER PRIMARY KEY,
                        note_id INTEGER NOT NULL,
                        repository_id INTEGER NOT NULL,
                        reviewed_sha TEXT NOT NULL,
                        reviewed_at TEXT NOT NULL
                    );
                    """
                )

                # Projects keep their original integer ids, so every existing
                # notes.project_id reference remains valid.
                for project in legacy_projects:
                    self.connection.execute(
                        "INSERT INTO projects(id,name,description,created_at,updated_at,archived_at) VALUES (?,?,?,?,?,NULL)",
                        (
                            int(project["id"]), str(project.get("name") or "Untitled Project"), "",
                            str(project.get("created_at") or now), str(project.get("updated_at") or now),
                        ),
                    )
                if not legacy_projects:
                    cursor = self.connection.execute(
                        "INSERT INTO projects(name,description,created_at,updated_at) VALUES (?,?,?,?)",
                        ("Personal Workspace", "", now, now),
                    )
                    default_project_id = int(cursor.lastrowid)
                else:
                    default_project_id = min(int(project["id"]) for project in legacy_projects)

                valid_project_ids = {
                    int(row["id"]) for row in self.connection.execute("SELECT id FROM projects").fetchall()
                }
                self.connection.execute(
                    "UPDATE notes SET project_id=? WHERE project_id IS NULL", (default_project_id,)
                )
                for note in legacy_notes:
                    project_id = note.get("project_id")
                    if project_id is not None and int(project_id) not in valid_project_ids:
                        self.connection.execute(
                            "UPDATE notes SET project_id=? WHERE id=?", (default_project_id, int(note["id"]))
                        )

                # Repositories in schema 5 belonged directly to one project.
                # The normalized model stores the repository once and maps it
                # through project_repositories. Duplicate GitHub full names are
                # therefore safely folded into one repository record.
                repository_id_map: dict[int, int] = {}
                repository_by_key: dict[str, int] = {}
                repository_branch: dict[int, str | None] = {}
                repository_project: dict[int, int] = {}
                for repository in sorted(legacy_repositories, key=lambda item: int(item["id"])):
                    old_id = int(repository["id"])
                    project_id = int(repository.get("project_id") or default_project_id)
                    if project_id not in valid_project_ids:
                        project_id = default_project_id
                    owner = str(repository.get("github_owner") or "").strip() or None
                    github_name = str(repository.get("github_repo") or "").strip() or None
                    full_name = f"{owner}/{github_name}" if owner and github_name else None
                    local_path = str(repository.get("local_path") or "").strip() or None
                    path_name = ""
                    if local_path:
                        path_name = local_path.replace("\\", "/").rstrip("/").split("/")[-1]
                    name = github_name or path_name or f"Repository {old_id}"
                    dedupe_key = f"github:{full_name.lower()}" if full_name else f"legacy:{old_id}"
                    existing_id = repository_by_key.get(dedupe_key)
                    if existing_id is None:
                        new_id = old_id
                        installation_id = repository.get("github_installation_id")
                        last_scanned = str(repository.get("last_scanned_at") or "").strip() or None
                        self.connection.execute(
                            """INSERT INTO repositories(
                               id,github_repo_id,github_node_id,owner,name,full_name,html_url,clone_url,
                               default_branch,is_private,installation_id,local_path,local_git_root,remote_name,
                               language,description,last_pushed_at,last_seen_sha,last_checked_at,
                               last_successful_check_at,last_check_source,github_access_state,created_at,updated_at
                               ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (
                                new_id, None, None, owner, name, full_name,
                                f"https://github.com/{full_name}" if full_name else None,
                                f"https://github.com/{full_name}.git" if full_name else None,
                                repository.get("default_branch"), 0,
                                int(installation_id) if installation_id is not None else None,
                                local_path, local_path, "origin" if full_name else None,
                                None, None, None, repository.get("last_seen_sha"), last_scanned, last_scanned,
                                "legacy_v5" if last_scanned else None,
                                "available" if full_name else ("local_only" if local_path else "unknown"),
                                str(repository.get("created_at") or now), str(repository.get("updated_at") or now),
                            ),
                        )
                        repository_by_key[dedupe_key] = new_id
                    else:
                        new_id = existing_id
                        # Keep a local clone path if the canonical row did not
                        # already have one.
                        if local_path:
                            self.connection.execute(
                                """UPDATE repositories SET
                                   local_path=COALESCE(local_path,?),local_git_root=COALESCE(local_git_root,?),
                                   updated_at=? WHERE id=?""",
                                (local_path, local_path, str(repository.get("updated_at") or now), new_id),
                            )
                    repository_id_map[old_id] = new_id
                    repository_branch[old_id] = (
                        str(repository.get("default_branch")) if repository.get("default_branch") else None
                    )
                    repository_project[old_id] = project_id
                    self.connection.execute(
                        """INSERT OR IGNORE INTO project_repositories(project_id,repository_id,monitored_branch,created_at)
                           VALUES (?,?,?,?)""",
                        (project_id, new_id, repository_branch[old_id], str(repository.get("created_at") or now)),
                    )

                # Older decisions were notes tagged with note_kind='decision'.
                # Convert them to the new metadata table while leaving the note
                # content itself byte-for-byte untouched.
                decision_by_note: dict[int, int] = {}
                decision_sequence: dict[int, int] = {}
                for note in legacy_notes:
                    if str(note.get("note_kind") or "note") != "decision":
                        continue
                    note_id = int(note["id"])
                    project_id = int(note.get("project_id") or default_project_id)
                    if project_id not in valid_project_ids:
                        project_id = default_project_id
                    number = decision_sequence.get(project_id, 0) + 1
                    decision_sequence[project_id] = number
                    cursor = self.connection.execute(
                        """INSERT INTO decisions(project_id,note_id,decision_key,status,created_at,updated_at)
                           VALUES (?,?,?,?,?,?)""",
                        (
                            project_id, note_id, f"DEC-{number:03d}", "proposed",
                            str(note.get("created_at") or now), str(note.get("updated_at") or now),
                        ),
                    )
                    decision_by_note[note_id] = int(cursor.lastrowid)

                note_project = {
                    int(row["id"]): int(row["project_id"]) if row["project_id"] is not None else default_project_id
                    for row in self.connection.execute("SELECT id,project_id FROM notes").fetchall()
                }

                latest_review: dict[tuple[int, int, str], str] = {}
                for event in legacy_review_events:
                    old_repo_id = int(event["repository_id"])
                    new_repo_id = repository_id_map.get(old_repo_id)
                    if new_repo_id is None:
                        continue
                    reviewed_sha = str(event.get("reviewed_sha") or "")
                    key = (int(event["note_id"]), new_repo_id, reviewed_sha)
                    reviewed_at = str(event.get("reviewed_at") or now)
                    if reviewed_at > latest_review.get(key, ""):
                        latest_review[key] = reviewed_at
                    self.connection.execute(
                        "INSERT OR REPLACE INTO legacy_review_events(id,note_id,repository_id,reviewed_sha,reviewed_at) VALUES (?,?,?,?,?)",
                        (int(event["id"]), int(event["note_id"]), new_repo_id, reviewed_sha, reviewed_at),
                    )

                def resource_identity(note_id: int, diagram_item_id: object | None = None) -> tuple[str, str, str]:
                    diagram_id = str(diagram_item_id or "").strip()
                    if diagram_id:
                        return "diagram_item", diagram_id, str(note_id)
                    if note_id in decision_by_note:
                        return "decision", str(decision_by_note[note_id]), ""
                    return "note", str(note_id), ""

                for link in legacy_links:
                    old_repo_id = int(link["repository_id"])
                    repository_id = repository_id_map.get(old_repo_id)
                    note_id = int(link["note_id"])
                    if repository_id is None or note_id not in note_project:
                        continue
                    resource_type, resource_id, resource_parent_id = resource_identity(
                        note_id, link.get("diagram_item_id")
                    )
                    target_type = str(link.get("resource_type") or "repository")
                    target_value = str(link.get("resource_value") or "").replace("\\", "/").strip("/")
                    if target_type == "repository":
                        target_value = ""
                    metadata = {
                        "display_label": str(link.get("display_label") or ""),
                        "migrated_from_schema": 5,
                        "legacy_last_checked_sha": link.get("last_checked_sha"),
                        "legacy_needs_review": bool(link.get("needs_review")),
                        "legacy_change_count": int(link.get("change_count") or 0),
                        "legacy_last_changed_at": link.get("last_changed_at"),
                    }
                    self.connection.execute(
                        """INSERT OR IGNORE INTO resource_links(
                           project_id,resource_type,resource_id,resource_parent_id,repository_id,
                           target_type,target_value,github_node_id,metadata_json,created_at
                           ) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        (
                            note_project[note_id], resource_type, resource_id, resource_parent_id,
                            repository_id, target_type, target_value, None,
                            json.dumps(metadata, ensure_ascii=False, separators=(",", ":")),
                            str(link.get("created_at") or now),
                        ),
                    )
                    baseline_sha = str(link.get("baseline_sha") or "").strip()
                    if baseline_sha:
                        reviewed_at = latest_review.get(
                            (note_id, repository_id, baseline_sha), str(link.get("updated_at") or now)
                        )
                        branch = repository_branch.get(old_repo_id)
                        self.connection.execute(
                            """INSERT INTO review_baselines(
                               resource_type,resource_id,resource_parent_id,repository_id,baseline_sha,branch,
                               reviewed_at,created_at,updated_at
                               ) VALUES (?,?,?,?,?,?,?,?,?)
                               ON CONFLICT(resource_type,resource_id,resource_parent_id,repository_id) DO UPDATE SET
                               baseline_sha=excluded.baseline_sha,branch=excluded.branch,
                               reviewed_at=excluded.reviewed_at,updated_at=excluded.updated_at""",
                            (
                                resource_type, resource_id, resource_parent_id, repository_id,
                                baseline_sha, branch, reviewed_at,
                                str(link.get("created_at") or reviewed_at), str(link.get("updated_at") or reviewed_at),
                            ),
                        )

                # Commit/PR/branch references were stored separately in schema 5.
                # Move them into the generic resource link model and enrich
                # first-class decisions when possible.
                for external in legacy_external_refs:
                    old_repo_id = int(external["repository_id"])
                    repository_id = repository_id_map.get(old_repo_id)
                    note_id = int(external["note_id"])
                    if repository_id is None or note_id not in note_project:
                        continue
                    resource_type, resource_id, resource_parent_id = resource_identity(note_id)
                    target_type = str(external.get("ref_type") or "")
                    if target_type not in {"pull_request", "commit", "branch"}:
                        continue
                    target_value = str(external.get("ref_value") or "").strip()
                    metadata = {
                        "title": str(external.get("title") or ""),
                        "url": external.get("url"),
                        "migrated_from_schema": 5,
                    }
                    self.connection.execute(
                        """INSERT OR IGNORE INTO resource_links(
                           project_id,resource_type,resource_id,resource_parent_id,repository_id,
                           target_type,target_value,github_node_id,metadata_json,created_at
                           ) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        (
                            note_project[note_id], resource_type, resource_id, resource_parent_id,
                            repository_id, target_type, target_value, None,
                            json.dumps(metadata, ensure_ascii=False, separators=(",", ":")),
                            str(external.get("created_at") or now),
                        ),
                    )
                    decision_id = decision_by_note.get(note_id)
                    if decision_id is None:
                        continue
                    if target_type == "commit" and target_value:
                        self.connection.execute(
                            """INSERT OR IGNORE INTO decision_commits(
                               decision_id,repository_id,commit_sha,github_url,created_at
                               ) VALUES (?,?,?,?,?)""",
                            (
                                decision_id, repository_id, target_value,
                                external.get("url"), str(external.get("created_at") or now),
                            ),
                        )
                    elif target_type == "pull_request":
                        number_text = target_value.lstrip("#")
                        if number_text.isdigit():
                            self.connection.execute(
                                """INSERT OR IGNORE INTO decision_pull_requests(
                                   decision_id,repository_id,pull_number,github_node_id,title,state,url,updated_at,created_at
                                   ) VALUES (?,?,?,?,?,?,?,?,?)""",
                                (
                                    decision_id, repository_id, int(number_text), None,
                                    str(external.get("title") or ""), None, external.get("url"), None,
                                    str(external.get("created_at") or now),
                                ),
                            )

                # Old cache entries stored file paths as strings. Convert them to
                # the structured ChangedFile JSON consumed by v6.
                for change in legacy_changes:
                    old_repo_id = int(change["repository_id"])
                    repository_id = repository_id_map.get(old_repo_id)
                    if repository_id is None:
                        continue
                    try:
                        raw_files = json.loads(str(change.get("changed_files_json") or "[]"))
                    except json.JSONDecodeError:
                        raw_files = []
                    converted_files: list[dict[str, object]] = []
                    if isinstance(raw_files, list):
                        for item in raw_files:
                            if isinstance(item, str):
                                converted_files.append({"status": "M", "path": item, "previous_path": None})
                            elif isinstance(item, dict):
                                path = item.get("path") or item.get("filename") or ""
                                converted_files.append({
                                    "status": str(item.get("status") or "M"),
                                    "path": str(path),
                                    "previous_path": item.get("previous_path") or item.get("previous_filename"),
                                })
                    from_sha = str(change.get("from_sha") or "")
                    to_sha = str(change.get("to_sha") or "")
                    if not to_sha:
                        continue
                    old_repository = next(
                        (item for item in legacy_repositories if int(item["id"]) == old_repo_id), None
                    )
                    source = "local_git" if old_repository and old_repository.get("local_path") else "github_api"
                    self.connection.execute(
                        """INSERT INTO repository_changes(
                           repository_id,from_sha,to_sha,source,commit_count,changed_files_json,
                           commits_json,pull_requests_json,detected_at
                           ) VALUES (?,?,?,?,?,?,?,?,?)
                           ON CONFLICT(repository_id,from_sha,to_sha,source) DO UPDATE SET
                           commit_count=excluded.commit_count,changed_files_json=excluded.changed_files_json,
                           detected_at=excluded.detected_at""",
                        (
                            repository_id, from_sha, to_sha, source, int(change.get("commit_count") or 0),
                            json.dumps(converted_files, ensure_ascii=False, separators=(",", ":")),
                            "[]", "[]", str(change.get("detected_at") or now),
                        ),
                    )

                self.connection.executescript(
                    """
                    CREATE INDEX IF NOT EXISTS idx_projects_archived_updated
                        ON projects(archived_at, updated_at DESC);
                    CREATE INDEX IF NOT EXISTS idx_repositories_github_repo_id
                        ON repositories(github_repo_id);
                    CREATE INDEX IF NOT EXISTS idx_repositories_full_name
                        ON repositories(full_name COLLATE NOCASE);
                    CREATE INDEX IF NOT EXISTS idx_project_repositories_project
                        ON project_repositories(project_id);
                    CREATE INDEX IF NOT EXISTS idx_notes_project_id ON notes(project_id);
                    CREATE INDEX IF NOT EXISTS idx_decisions_project_id ON decisions(project_id);
                    CREATE INDEX IF NOT EXISTS idx_resource_links_resource
                        ON resource_links(resource_type, resource_id, resource_parent_id);
                    CREATE INDEX IF NOT EXISTS idx_resource_links_repository
                        ON resource_links(repository_id, target_type, target_value);
                    CREATE INDEX IF NOT EXISTS idx_review_baselines_resource
                        ON review_baselines(resource_type, resource_id, resource_parent_id, repository_id);
                    CREATE INDEX IF NOT EXISTS idx_repository_changes_lookup
                        ON repository_changes(repository_id, from_sha, to_sha, source);
                    CREATE INDEX IF NOT EXISTS idx_activity_project_created
                        ON activity_events(project_id, created_at DESC);
                    PRAGMA user_version = 6;
                    """
                )
        finally:
            self.connection.execute("PRAGMA foreign_keys = ON")

        violations = self.connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            detail = "; ".join(str(tuple(row)) for row in violations[:5])
            raise DatabaseError(f"Legacy schema-5 migration produced foreign-key violations: {detail}")

    # ------------------------------------------------------------------
    # Row mapping
    # ------------------------------------------------------------------
    @staticmethod
    def _note_from_row(row: sqlite3.Row) -> Note:
        return Note(
            id=int(row["id"]),
            title=str(row["title"]),
            content_html=str(row["content_html"]),
            content_plain=str(row["content_plain"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            is_deleted=bool(row["is_deleted"]),
            project_id=int(row["project_id"]) if row["project_id"] is not None else None,
        )

    @staticmethod
    def _project_from_row(row: sqlite3.Row) -> Project:
        return Project(
            id=int(row["id"]), name=str(row["name"]), description=str(row["description"] or ""),
            created_at=str(row["created_at"]), updated_at=str(row["updated_at"]),
            archived_at=str(row["archived_at"]) if row["archived_at"] else None,
            trashed_at=str(row["trashed_at"]) if "trashed_at" in row.keys() and row["trashed_at"] else None,
        )

    @staticmethod
    def _repository_from_row(row: sqlite3.Row) -> Repository:
        return Repository(
            id=int(row["id"]),
            github_repo_id=int(row["github_repo_id"]) if row["github_repo_id"] is not None else None,
            github_node_id=str(row["github_node_id"]) if row["github_node_id"] else None,
            owner=str(row["owner"]) if row["owner"] else None,
            name=str(row["name"]),
            full_name=str(row["full_name"]) if row["full_name"] else None,
            html_url=str(row["html_url"]) if row["html_url"] else None,
            clone_url=str(row["clone_url"]) if row["clone_url"] else None,
            default_branch=str(row["default_branch"]) if row["default_branch"] else None,
            is_private=bool(row["is_private"]),
            installation_id=int(row["installation_id"]) if row["installation_id"] is not None else None,
            local_path=str(row["local_path"]) if row["local_path"] else None,
            local_git_root=str(row["local_git_root"]) if row["local_git_root"] else None,
            remote_name=str(row["remote_name"]) if row["remote_name"] else None,
            language=str(row["language"]) if row["language"] else None,
            description=str(row["description"]) if row["description"] else None,
            last_pushed_at=str(row["last_pushed_at"]) if row["last_pushed_at"] else None,
            last_seen_sha=str(row["last_seen_sha"]) if row["last_seen_sha"] else None,
            last_checked_at=str(row["last_checked_at"]) if row["last_checked_at"] else None,
            last_successful_check_at=str(row["last_successful_check_at"]) if row["last_successful_check_at"] else None,
            last_check_source=str(row["last_check_source"]) if row["last_check_source"] else None,
            github_access_state=str(row["github_access_state"] or "unknown"),
            created_at=str(row["created_at"]), updated_at=str(row["updated_at"]),
        )

    @staticmethod
    def _resource_link_from_row(row: sqlite3.Row) -> ResourceLink:
        try:
            metadata = json.loads(str(row["metadata_json"] or "{}"))
            if not isinstance(metadata, dict):
                metadata = {}
        except json.JSONDecodeError:
            metadata = {}
        return ResourceLink(
            id=int(row["id"]), project_id=int(row["project_id"]),
            resource_type=str(row["resource_type"]), resource_id=str(row["resource_id"]),
            resource_parent_id=str(row["resource_parent_id"] or ""), repository_id=int(row["repository_id"]),
            target_type=str(row["target_type"]), target_value=str(row["target_value"] or ""),
            github_node_id=str(row["github_node_id"]) if row["github_node_id"] else None,
            metadata=metadata, created_at=str(row["created_at"]),
        )

    @staticmethod
    def _baseline_from_row(row: sqlite3.Row) -> ReviewBaseline:
        return ReviewBaseline(
            id=int(row["id"]), resource_type=str(row["resource_type"]), resource_id=str(row["resource_id"]),
            resource_parent_id=str(row["resource_parent_id"] or ""), repository_id=int(row["repository_id"]),
            baseline_sha=str(row["baseline_sha"]), branch=str(row["branch"]) if row["branch"] else None,
            reviewed_at=str(row["reviewed_at"]), created_at=str(row["created_at"]), updated_at=str(row["updated_at"]),
        )

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------
    def default_project_id(self) -> int:
        row = self.connection.execute(
            "SELECT id FROM projects WHERE archived_at IS NULL AND trashed_at IS NULL ORDER BY id LIMIT 1"
        ).fetchone()
        if row:
            return int(row["id"])
        return self.create_project("Personal Workspace", "Local DevNest knowledge.").id

    def create_project(self, name: str, description: str = "") -> Project:
        safe_name = name.strip()
        if not safe_name:
            raise DatabaseError("Project name cannot be empty.")
        now = utc_now_iso()
        try:
            with self.connection:
                cursor = self.connection.execute(
                    "INSERT INTO projects(name, description, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (safe_name, description.strip(), now, now),
                )
                self.connection.execute(
                    "INSERT INTO activity_events(project_id, event_type, title, detail, created_at) VALUES (?, 'project_created', ?, '', ?)",
                    (cursor.lastrowid, safe_name, now),
                )
            return self.get_project(int(cursor.lastrowid))  # type: ignore[return-value]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not create project: {exc}") from exc

    def get_project(self, project_id: int, include_trashed: bool = False) -> Project | None:
        sql = "SELECT * FROM projects WHERE id = ?"
        if not include_trashed:
            sql += " AND trashed_at IS NULL"
        row = self.connection.execute(sql, (project_id,)).fetchone()
        return self._project_from_row(row) if row else None

    def list_projects(self, include_archived: bool = False, include_trashed: bool = False) -> list[Project]:
        where: list[str] = []
        if not include_archived:
            where.append("archived_at IS NULL")
        if not include_trashed:
            where.append("trashed_at IS NULL")
        clause = f"WHERE {' AND '.join(where)}" if where else ""
        rows = self.connection.execute(
            f"SELECT * FROM projects {clause} ORDER BY updated_at DESC, name COLLATE NOCASE"
        ).fetchall()
        return [self._project_from_row(row) for row in rows]

    def list_trashed_projects(self) -> list[Project]:
        rows = self.connection.execute(
            "SELECT * FROM projects WHERE trashed_at IS NOT NULL ORDER BY trashed_at DESC, name COLLATE NOCASE"
        ).fetchall()
        return [self._project_from_row(row) for row in rows]

    def list_project_summaries(self) -> list[ProjectSummary]:
        rows = self.connection.execute(
            """
            SELECT p.*,
                   (SELECT COUNT(*) FROM project_repositories pr WHERE pr.project_id=p.id) repository_count,
                   (SELECT COUNT(*) FROM notes n WHERE n.project_id=p.id AND n.is_deleted=0) note_count,
                   (SELECT COUNT(*) FROM decisions d JOIN notes dn ON dn.id=d.note_id
                        WHERE d.project_id=p.id AND dn.is_deleted=0) decision_count,
                   (SELECT COUNT(*) FROM diagrams dg JOIN notes n2 ON n2.id=dg.note_id
                        WHERE n2.project_id=p.id AND n2.is_deleted=0) diagram_count,
                   (SELECT MAX(created_at) FROM activity_events a WHERE a.project_id=p.id) last_activity
            FROM projects p WHERE p.archived_at IS NULL AND p.trashed_at IS NULL
            ORDER BY EXISTS(SELECT 1 FROM favorites f WHERE f.resource_type='project' AND f.resource_id=CAST(p.id AS TEXT)) DESC,
                     p.updated_at DESC
            """
        ).fetchall()
        return [
            ProjectSummary(
                id=int(row["id"]), name=str(row["name"]), description=str(row["description"] or ""),
                created_at=str(row["created_at"]), updated_at=str(row["updated_at"]), archived_at=None, trashed_at=None,
                repository_count=int(row["repository_count"] or 0), note_count=int(row["note_count"] or 0),
                decision_count=int(row["decision_count"] or 0), diagram_count=int(row["diagram_count"] or 0),
                needs_review_count=0, last_activity=str(row["last_activity"]) if row["last_activity"] else None,
            ) for row in rows
        ]

    def update_project(self, project_id: int, name: str, description: str) -> None:
        safe_name = name.strip()
        if not safe_name:
            raise DatabaseError("Project name cannot be empty.")
        project = self.get_project(project_id)
        now = utc_now_iso()
        with self.connection:
            self.connection.execute(
                "UPDATE projects SET name=?, description=?, updated_at=? WHERE id=?",
                (safe_name, description.strip(), now, project_id),
            )
            if project and (project.name != safe_name or project.description != description.strip()):
                self.connection.execute(
                    "INSERT INTO activity_events(project_id,event_type,title,detail,created_at,resource_type,resource_id,metadata_json) VALUES (?, 'project_updated', ?, ?, ?, 'project', ?, '{}')",
                    (project_id, safe_name, description.strip(), now, str(project_id)),
                )

    def archive_project(self, project_id: int) -> None:
        with self.connection:
            self.connection.execute(
                "UPDATE projects SET archived_at=?, updated_at=? WHERE id=?",
                (utc_now_iso(), utc_now_iso(), project_id),
            )

    def trash_project(self, project_id: int) -> None:
        """Move an entire project into Trash as one reversible bundle."""
        project = self.get_project(project_id)
        if project is None:
            raise DatabaseError("Project not found.")
        now = utc_now_iso()
        try:
            with self.connection:
                # Remember each note's previous Trash state so restoring the project
                # does not resurrect notes that the user had deleted earlier.
                self.connection.execute(
                    """UPDATE notes
                       SET project_trash_was_deleted=is_deleted, is_deleted=1,
                           trashed_with_project_id=?, updated_at=?
                       WHERE project_id=?""",
                    (project_id, now, project_id),
                )
                self.connection.execute(
                    "UPDATE projects SET trashed_at=?, updated_at=? WHERE id=?",
                    (now, now, project_id),
                )
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not move project to Trash: {exc}") from exc

    def restore_project(self, project_id: int) -> None:
        row = self.connection.execute(
            "SELECT id FROM projects WHERE id=? AND trashed_at IS NOT NULL", (project_id,)
        ).fetchone()
        if row is None:
            raise DatabaseError("Project is not in Trash.")
        now = utc_now_iso()
        try:
            with self.connection:
                self.connection.execute(
                    """UPDATE notes
                       SET is_deleted=project_trash_was_deleted, trashed_with_project_id=NULL,
                           project_trash_was_deleted=0, updated_at=?
                       WHERE project_id=? AND trashed_with_project_id=?""",
                    (now, project_id, project_id),
                )
                self.connection.execute(
                    "UPDATE projects SET trashed_at=NULL, archived_at=NULL, updated_at=? WHERE id=?",
                    (now, project_id),
                )
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not restore project: {exc}") from exc

    def project_trash_contents(self, project_id: int) -> dict[str, object]:
        project = self.get_project(project_id, include_trashed=True)
        if project is None:
            raise DatabaseError("Project not found.")
        decision_rows = self.connection.execute(
            """SELECT d.id,d.decision_key,n.title FROM decisions d
               JOIN notes n ON n.id=d.note_id WHERE d.project_id=? ORDER BY d.decision_key""",
            (project_id,),
        ).fetchall()
        decision_note_ids = {int(row["id"]) for row in self.connection.execute(
            "SELECT note_id AS id FROM decisions WHERE project_id=?", (project_id,)
        ).fetchall()}
        note_rows = self.connection.execute(
            "SELECT id,title FROM notes WHERE project_id=? ORDER BY title COLLATE NOCASE", (project_id,)
        ).fetchall()
        normal_notes = [str(row["title"]) for row in note_rows if int(row["id"]) not in decision_note_ids]
        diagram_rows = self.connection.execute(
            """SELECT n.title FROM diagrams dg JOIN notes n ON n.id=dg.note_id
               WHERE n.project_id=? ORDER BY n.title COLLATE NOCASE""", (project_id,)
        ).fetchall()
        repo_rows = self.connection.execute(
            """SELECT COALESCE(r.full_name,r.name) AS label FROM repositories r
               JOIN project_repositories pr ON pr.repository_id=r.id
               WHERE pr.project_id=? ORDER BY label COLLATE NOCASE""", (project_id,)
        ).fetchall()
        link_count = int(self.connection.execute(
            "SELECT COUNT(*) FROM resource_links WHERE project_id=?", (project_id,)
        ).fetchone()[0])
        baseline_count = int(self.connection.execute(
            """SELECT COUNT(*) FROM review_baselines rb WHERE EXISTS (
                   SELECT 1 FROM resource_links rl WHERE rl.project_id=?
                   AND rl.resource_type=rb.resource_type AND rl.resource_id=rb.resource_id
                   AND rl.resource_parent_id=rb.resource_parent_id AND rl.repository_id=rb.repository_id
               )""", (project_id,)
        ).fetchone()[0])
        return {
            "project": project,
            "notes": normal_notes,
            "decisions": [f"{row['decision_key']} · {row['title']}" for row in decision_rows],
            "diagrams": [str(row["title"]) for row in diagram_rows],
            "repositories": [str(row["label"]) for row in repo_rows],
            "resource_links": link_count,
            "review_baselines": baseline_count,
        }

    def permanently_delete_project(self, project_id: int) -> None:
        row = self.connection.execute(
            "SELECT id FROM projects WHERE id=? AND trashed_at IS NOT NULL", (project_id,)
        ).fetchone()
        if row is None:
            raise DatabaseError("Project must be in Trash before permanent deletion.")
        try:
            with self.connection:
                note_ids = [str(row["id"]) for row in self.connection.execute(
                    "SELECT id FROM notes WHERE project_id=?", (project_id,)
                ).fetchall()]
                decision_ids = [str(row["id"]) for row in self.connection.execute(
                    "SELECT id FROM decisions WHERE project_id=?", (project_id,)
                ).fetchall()]
                for note_id in note_ids:
                    self.connection.execute(
                        "DELETE FROM review_baselines WHERE resource_type='note' AND resource_id=?", (note_id,)
                    )
                    self.connection.execute(
                        "DELETE FROM review_baselines WHERE resource_type='diagram_item' AND resource_parent_id=?", (note_id,)
                    )
                for decision_id in decision_ids:
                    self.connection.execute(
                        "DELETE FROM review_baselines WHERE resource_type='decision' AND resource_id=?", (decision_id,)
                    )
                self.connection.execute("DELETE FROM resource_links WHERE project_id=?", (project_id,))
                self.connection.execute("DELETE FROM decisions WHERE project_id=?", (project_id,))
                self.connection.execute("DELETE FROM notes WHERE project_id=?", (project_id,))
                self.connection.execute("DELETE FROM projects WHERE id=?", (project_id,))
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not permanently delete project: {exc}") from exc

    def touch_project(self, project_id: int) -> None:
        self.connection.execute("UPDATE projects SET updated_at=? WHERE id=?", (utc_now_iso(), project_id))

    # ------------------------------------------------------------------
    # Notes and diagrams (backward-compatible surface)
    # ------------------------------------------------------------------
    def create_note(
        self,
        title: str = DEFAULT_NOTE_TITLE,
        content_html: str = "",
        content_plain: str = "",
        project_id: int | None = None,
    ) -> Note:
        now = utc_now_iso()
        safe_title = title.strip() or DEFAULT_NOTE_TITLE
        project_id = project_id or self.default_project_id()
        try:
            with self.connection:
                cursor = self.connection.execute(
                    """
                    INSERT INTO notes(title, content_html, content_plain, created_at, updated_at, is_deleted, project_id)
                    VALUES (?, ?, ?, ?, ?, 0, ?)
                    """,
                    (safe_title, content_html, content_plain, now, now, project_id),
                )
                self.connection.execute("UPDATE projects SET updated_at=? WHERE id=?", (now, project_id))
                self.connection.execute(
                    """INSERT INTO activity_events(project_id,event_type,title,detail,created_at,resource_type,resource_id,metadata_json)
                       VALUES (?, 'note_created', ?, '', ?, 'note', ?, '{}')""",
                    (project_id, safe_title, now, str(cursor.lastrowid)),
                )
            note = self.get_note(int(cursor.lastrowid))
            if note is None:
                raise DatabaseError("Created note could not be reloaded.")
            return note
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not create note: {exc}") from exc

    def get_note(self, note_id: int, include_deleted: bool = False) -> Note | None:
        sql = "SELECT * FROM notes WHERE id = ?"
        if not include_deleted:
            sql += " AND is_deleted = 0"
        row = self.connection.execute(sql, (note_id,)).fetchone()
        return self._note_from_row(row) if row else None

    def update_note(self, note_id: int, title: str, content_html: str, content_plain: str) -> None:
        now = utc_now_iso()
        safe_title = title.strip() or DEFAULT_NOTE_TITLE
        before = self.get_note(note_id)
        if before is None:
            raise DatabaseError("The note no longer exists or is in Trash.")
        changed_title = before.title != safe_title
        changed_content = before.content_html != content_html or before.content_plain != content_plain
        if not changed_title and not changed_content:
            return
        try:
            with self.connection:
                cursor = self.connection.execute(
                    """UPDATE notes SET title=?, content_html=?, content_plain=?, updated_at=?
                       WHERE id=? AND is_deleted=0""",
                    (safe_title, content_html, content_plain, now, note_id),
                )
                if cursor.rowcount == 0:
                    raise DatabaseError("The note no longer exists or is in Trash.")
                project_id = before.project_id
                if project_id:
                    self.connection.execute("UPDATE projects SET updated_at=? WHERE id=?", (now, project_id))
                    detail_bits = []
                    if changed_title:
                        detail_bits.append(f"{before.title} → {safe_title}")
                    if changed_content:
                        detail_bits.append("content updated")
                    self.connection.execute(
                        """INSERT INTO activity_events(project_id,event_type,title,detail,created_at,resource_type,resource_id,metadata_json)
                           VALUES (?, 'note_updated', ?, ?, ?, 'note', ?, '{}')""",
                        (project_id, safe_title, " · ".join(detail_bits), now, str(note_id)),
                    )
        except DatabaseError:
            raise
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not save note: {exc}") from exc

    def rename_note(self, note_id: int, title: str) -> None:
        note = self.get_note(note_id)
        if note is None:
            raise DatabaseError("Note not found.")
        self.update_note(note_id, title, note.content_html, note.content_plain)

    def duplicate_note(self, note_id: int) -> Note:
        source = self.get_note(note_id)
        if source is None:
            raise DatabaseError("Note not found.")
        copy = self.create_note(
            title=f"{source.title} Copy", content_html=source.content_html,
            content_plain=source.content_plain, project_id=source.project_id,
        )
        diagram = self.get_diagram(note_id)
        if diagram and any(diagram.get(key) for key in ("items", "paths", "connectors", "edges")):
            self.save_diagram(copy.id, diagram)
        return copy

    def list_notes(self, search: str = "", sort: str = "updated", project_id: int | None = None) -> list[NoteSummary]:
        where = ["is_deleted = 0", "id NOT IN (SELECT note_id FROM decisions)"]
        params: list[object] = []
        if project_id is not None:
            where.append("project_id = ?")
            params.append(project_id)
        term = search.strip()
        if term:
            where.append("""(title LIKE ? COLLATE NOCASE OR content_plain LIKE ? COLLATE NOCASE OR EXISTS(
                SELECT 1 FROM resource_tags rt JOIN tags t ON t.id=rt.tag_id
                WHERE rt.resource_type='note' AND rt.resource_id=CAST(notes.id AS TEXT)
                  AND t.name LIKE ? COLLATE NOCASE))""")
            like = f"%{term}%"
            params.extend([like, like, like])
        favorite_order = "EXISTS(SELECT 1 FROM favorites f WHERE f.resource_type='note' AND f.resource_id=CAST(notes.id AS TEXT)) DESC, "
        order_by = favorite_order + ("updated_at DESC" if sort == "updated" else "title COLLATE NOCASE ASC, updated_at DESC")
        rows = self.connection.execute(
            f"""
            SELECT id, title,
                   substr(replace(replace(content_plain, char(10), ' '), char(13), ' '), 1, 140) AS preview,
                   created_at, updated_at, is_deleted, project_id
            FROM notes WHERE {' AND '.join(where)} ORDER BY {order_by}
            """, params,
        ).fetchall()
        return [NoteSummary(
            id=int(row["id"]), title=str(row["title"]), preview=str(row["preview"] or ""),
            created_at=str(row["created_at"]), updated_at=str(row["updated_at"]),
            is_deleted=bool(row["is_deleted"]), project_id=int(row["project_id"]) if row["project_id"] else None,
        ) for row in rows]

    def list_trash(self) -> list[NoteSummary]:
        rows = self.connection.execute(
            """
            SELECT id, title,
                   substr(replace(replace(content_plain, char(10), ' '), char(13), ' '), 1, 140) AS preview,
                   created_at, updated_at, is_deleted, project_id
            FROM notes WHERE is_deleted = 1 AND trashed_with_project_id IS NULL ORDER BY updated_at DESC
            """
        ).fetchall()
        return [NoteSummary(
            id=int(row["id"]), title=str(row["title"]), preview=str(row["preview"] or ""),
            created_at=str(row["created_at"]), updated_at=str(row["updated_at"]), is_deleted=True,
            project_id=int(row["project_id"]) if row["project_id"] else None,
        ) for row in rows]

    def soft_delete_note(self, note_id: int) -> None:
        try:
            with self.connection:
                self.connection.execute("UPDATE notes SET is_deleted=1, updated_at=? WHERE id=?", (utc_now_iso(), note_id))
                # A deleted note must not linger in Dashboard > Continue working.
                self.connection.execute(
                    "DELETE FROM recent_items WHERE resource_type='note' AND resource_id=?",
                    (str(note_id),),
                )
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not move note to Trash: {exc}") from exc

    def restore_note(self, note_id: int) -> None:
        try:
            with self.connection:
                self.connection.execute("UPDATE notes SET is_deleted=0, updated_at=? WHERE id=?", (utc_now_iso(), note_id))
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not restore note: {exc}") from exc

    def permanently_delete_note(self, note_id: int) -> None:
        try:
            with self.connection:
                # Polymorphic resource rows cannot use a direct FK to notes.
                self.connection.execute("DELETE FROM resource_links WHERE resource_type='note' AND resource_id=?", (str(note_id),))
                self.connection.execute("DELETE FROM review_baselines WHERE resource_type='note' AND resource_id=?", (str(note_id),))
                self.connection.execute("DELETE FROM notes WHERE id=? AND is_deleted=1", (note_id,))
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not permanently delete note: {exc}") from exc

    def empty_trash(self) -> int:
        try:
            rows = self.connection.execute("SELECT id FROM notes WHERE is_deleted=1 AND trashed_with_project_id IS NULL").fetchall()
            with self.connection:
                for row in rows:
                    nid = str(row["id"])
                    self.connection.execute("DELETE FROM resource_links WHERE resource_type='note' AND resource_id=?", (nid,))
                    self.connection.execute("DELETE FROM review_baselines WHERE resource_type='note' AND resource_id=?", (nid,))
                cursor = self.connection.execute("DELETE FROM notes WHERE is_deleted=1 AND trashed_with_project_id IS NULL")
            return int(cursor.rowcount)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not empty Trash: {exc}") from exc

    def save_diagram(self, note_id: int, data: dict[str, object] | str) -> None:
        data_json = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        now = utc_now_iso()
        previous = self.connection.execute("SELECT data_json FROM diagrams WHERE note_id=?", (note_id,)).fetchone()
        changed = previous is None or str(previous["data_json"]) != data_json
        try:
            with self.connection:
                self.connection.execute(
                    """
                    INSERT INTO diagrams(note_id, data_json, updated_at) VALUES (?, ?, ?)
                    ON CONFLICT(note_id) DO UPDATE SET data_json=excluded.data_json, updated_at=excluded.updated_at
                    """, (note_id, data_json, now),
                )
                if changed:
                    note = self.connection.execute("SELECT project_id,title FROM notes WHERE id=?", (note_id,)).fetchone()
                    if note:
                        self.connection.execute(
                            "INSERT INTO activity_events(project_id,event_type,title,detail,created_at,resource_type,resource_id,metadata_json) VALUES (?, 'architecture_updated', ?, '', ?, 'architecture', ?, '{}')",
                            (int(note["project_id"]), str(note["title"]), now, str(note_id)),
                        )
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not save diagram: {exc}") from exc

    def get_diagram(self, note_id: int) -> dict[str, object]:
        row = self.connection.execute("SELECT data_json FROM diagrams WHERE note_id=?", (note_id,)).fetchone()
        if not row:
            return {"items": [], "edges": [], "paths": []}
        try:
            data = json.loads(str(row["data_json"]))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        return {"items": [], "edges": [], "paths": []}

    def delete_diagram(self, note_id: int) -> None:
        """Remove only the architecture diagram attached to a note.

        The note text remains intact. Diagram-node resource links/baselines are
        relational metadata and are removed with the diagram.
        """
        try:
            with self.connection:
                self.connection.execute(
                    "DELETE FROM review_baselines WHERE resource_type='diagram_item' AND resource_parent_id=?",
                    (str(note_id),),
                )
                self.connection.execute(
                    "DELETE FROM resource_links WHERE resource_type='diagram_item' AND resource_parent_id=?",
                    (str(note_id),),
                )
                self.connection.execute("DELETE FROM diagrams WHERE note_id=?", (note_id,))
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not delete diagram: {exc}") from exc

    def list_diagram_notes(self, project_id: int | None = None) -> list[NoteSummary]:
        params: list[object] = []
        where = ["n.is_deleted=0"]
        if project_id is not None:
            where.append("n.project_id=?")
            params.append(project_id)
        rows = self.connection.execute(
            f"""SELECT n.id,n.title,n.content_plain,n.created_at,n.updated_at,n.is_deleted,n.project_id
                FROM diagrams d JOIN notes n ON n.id=d.note_id
                WHERE {' AND '.join(where)} ORDER BY n.updated_at DESC""", params,
        ).fetchall()
        return [NoteSummary(
            id=int(r["id"]), title=str(r["title"]), preview=str(r["content_plain"] or "")[:140],
            created_at=str(r["created_at"]), updated_at=str(r["updated_at"]), is_deleted=False,
            project_id=int(r["project_id"]) if r["project_id"] else None,
        ) for r in rows]

    # ------------------------------------------------------------------
    # Decisions
    # ------------------------------------------------------------------
    def _next_decision_key(self, project_id: int) -> str:
        # Decision keys are permanent human references. A deleted DEC-014 must never
        # cause a later decision to reuse DEC-014, so include creation history too.
        rows = self.connection.execute("SELECT decision_key FROM decisions WHERE project_id=?", (project_id,)).fetchall()
        keys = [str(row["decision_key"]) for row in rows]
        try:
            history = self.connection.execute(
                "SELECT title FROM activity_events WHERE project_id=? AND event_type='decision_created'", (project_id,)
            ).fetchall()
            keys.extend(str(row["title"]) for row in history)
        except sqlite3.Error:
            pass
        numbers: list[int] = []
        for key in keys:
            if key.startswith("DEC-") and key[4:].isdigit():
                numbers.append(int(key[4:]))
        return f"DEC-{(max(numbers, default=0) + 1):03d}"

    def create_decision(self, project_id: int, title: str = "Untitled Decision", status: str = "proposed") -> Decision:
        safe_title = title.strip() or "Untitled Decision"
        now = utc_now_iso()
        key = self._next_decision_key(project_id)
        try:
            with self.connection:
                note_cursor = self.connection.execute(
                    "INSERT INTO notes(title, content_html, content_plain, created_at, updated_at, is_deleted, project_id) VALUES (?, '', '', ?, ?, 0, ?)",
                    (safe_title, now, now, project_id),
                )
                decision_cursor = self.connection.execute(
                    "INSERT INTO decisions(project_id,note_id,decision_key,status,created_at,updated_at) VALUES (?,?,?,?,?,?)",
                    (project_id, note_cursor.lastrowid, key, status, now, now),
                )
                self.connection.execute("UPDATE projects SET updated_at=? WHERE id=?", (now, project_id))
                self.connection.execute(
                    """INSERT INTO activity_events(project_id,event_type,title,detail,created_at,resource_type,resource_id,metadata_json)
                       VALUES (?, 'decision_created', ?, ?, ?, 'decision', ?, '{}')""",
                    (project_id, key, safe_title, now, str(decision_cursor.lastrowid)),
                )
                self.connection.execute(
                    "INSERT INTO decision_history(decision_id,event_type,title,detail,metadata_json,created_at) VALUES (?, 'created', ?, ?, '{}', ?)",
                    (decision_cursor.lastrowid, key, safe_title, now),
                )
            return self.get_decision(int(decision_cursor.lastrowid))  # type: ignore[return-value]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not create decision: {exc}") from exc

    def get_decision(self, decision_id: int) -> Decision | None:
        row = self.connection.execute(
            """SELECT d.*, n.title,n.content_html,n.content_plain
               FROM decisions d JOIN notes n ON n.id=d.note_id WHERE d.id=? AND n.is_deleted=0""", (decision_id,),
        ).fetchone()
        if not row:
            return None
        return Decision(
            id=int(row["id"]), project_id=int(row["project_id"]), note_id=int(row["note_id"]),
            decision_key=str(row["decision_key"]), status=str(row["status"]), title=str(row["title"]),
            content_html=str(row["content_html"]), content_plain=str(row["content_plain"]),
            created_at=str(row["created_at"]), updated_at=str(row["updated_at"]),
        )

    def list_decisions(self, project_id: int | None = None, search: str = "") -> list[Decision]:
        where = ["n.is_deleted=0"]
        params: list[object] = []
        if project_id is not None:
            where.append("d.project_id=?")
            params.append(project_id)
        if search.strip():
            where.append("""(d.decision_key LIKE ? OR n.title LIKE ? COLLATE NOCASE OR n.content_plain LIKE ? COLLATE NOCASE OR EXISTS(
                SELECT 1 FROM resource_tags rt JOIN tags t ON t.id=rt.tag_id
                WHERE rt.resource_type='decision' AND rt.resource_id=CAST(d.id AS TEXT)
                  AND t.name LIKE ? COLLATE NOCASE))""")
            like = f"%{search.strip()}%"
            params.extend([like, like, like, like])
        rows = self.connection.execute(
            f"""SELECT d.*,n.title,n.content_html,n.content_plain FROM decisions d JOIN notes n ON n.id=d.note_id
                WHERE {' AND '.join(where)} ORDER BY EXISTS(SELECT 1 FROM favorites f WHERE f.resource_type='decision' AND f.resource_id=CAST(d.id AS TEXT)) DESC, d.updated_at DESC""", params,
        ).fetchall()
        return [Decision(
            id=int(r["id"]), project_id=int(r["project_id"]), note_id=int(r["note_id"]),
            decision_key=str(r["decision_key"]), status=str(r["status"]), title=str(r["title"]),
            content_html=str(r["content_html"]), content_plain=str(r["content_plain"]),
            created_at=str(r["created_at"]), updated_at=str(r["updated_at"]),
        ) for r in rows]

    def update_decision(self, decision_id: int, title: str, content_html: str, content_plain: str, status: str) -> None:
        decision = self.get_decision(decision_id)
        if decision is None:
            raise DatabaseError("Decision not found.")
        safe_title = title.strip() or "Untitled Decision"
        changed_title = decision.title != safe_title
        changed_status = decision.status != status
        changed_content = decision.content_html != content_html or decision.content_plain != content_plain
        if not (changed_title or changed_status or changed_content):
            return
        now = utc_now_iso()
        with self.connection:
            self.connection.execute(
                "UPDATE notes SET title=?,content_html=?,content_plain=?,updated_at=? WHERE id=?",
                (safe_title, content_html, content_plain, now, decision.note_id),
            )
            self.connection.execute("UPDATE decisions SET status=?,updated_at=? WHERE id=?", (status, now, decision_id))
            self.connection.execute("UPDATE projects SET updated_at=? WHERE id=?", (now, decision.project_id))
            events: list[tuple[str, str, str, dict[str, object]]] = []
            if changed_title:
                events.append(("title_changed", "Title changed", f"{decision.title} → {safe_title}", {"old": decision.title, "new": safe_title}))
            if changed_status:
                events.append(("status_changed", "Status changed", f"{decision.status} → {status}", {"old": decision.status, "new": status}))
            if changed_content:
                events.append(("content_updated", "Decision text updated", "", {}))
            for event_type, event_title, detail, metadata in events:
                payload = json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))
                self.connection.execute(
                    "INSERT INTO decision_history(decision_id,event_type,title,detail,metadata_json,created_at) VALUES (?,?,?,?,?,?)",
                    (decision_id, event_type, event_title, detail, payload, now),
                )
                self.connection.execute(
                    """INSERT INTO activity_events(project_id,event_type,title,detail,created_at,resource_type,resource_id,metadata_json)
                       VALUES (?,?,?,?,?,'decision',?,?)""",
                    (decision.project_id, f"decision_{event_type}", f"{decision.decision_key} · {event_title}", detail, now, str(decision_id), payload),
                )

    def delete_decision(self, decision_id: int) -> None:
        decision = self.get_decision(decision_id)
        if decision is None:
            raise DatabaseError("Decision not found.")
        now = utc_now_iso()
        try:
            with self.connection:
                # Polymorphic links/baselines cannot use a direct FK to decisions.
                self.connection.execute(
                    "DELETE FROM review_baselines WHERE resource_type='decision' AND resource_id=?",
                    (str(decision_id),),
                )
                self.connection.execute(
                    "DELETE FROM resource_links WHERE resource_type='decision' AND resource_id=?",
                    (str(decision_id),),
                )
                # decision_commits / decision_pull_requests cascade from decisions.
                self.connection.execute("DELETE FROM decisions WHERE id=?", (decision_id,))
                self.connection.execute("DELETE FROM notes WHERE id=?", (decision.note_id,))
                self.connection.execute(
                    "DELETE FROM recent_items WHERE resource_type='decision' AND resource_id=?",
                    (str(decision_id),),
                )
                self.connection.execute("UPDATE projects SET updated_at=? WHERE id=?", (now, decision.project_id))
                self.connection.execute(
                    "INSERT INTO activity_events(project_id,event_type,title,detail,created_at) VALUES (?, 'decision_deleted', ?, ?, ?)",
                    (decision.project_id, decision.decision_key, decision.title, now),
                )
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not delete decision: {exc}") from exc

    # ------------------------------------------------------------------
    # Repositories / project mappings
    # ------------------------------------------------------------------
    def upsert_repository(self, *, name: str, github_repo_id: int | None = None, github_node_id: str | None = None,
                          owner: str | None = None, full_name: str | None = None, html_url: str | None = None,
                          clone_url: str | None = None, default_branch: str | None = None, is_private: bool = False,
                          installation_id: int | None = None, local_path: str | None = None,
                          local_git_root: str | None = None, remote_name: str | None = None,
                          language: str | None = None, description: str | None = None,
                          last_pushed_at: str | None = None, github_access_state: str = "available") -> Repository:
        now = utc_now_iso()
        existing: sqlite3.Row | None = None
        if github_repo_id is not None:
            existing = self.connection.execute("SELECT * FROM repositories WHERE github_repo_id=?", (github_repo_id,)).fetchone()
        if existing is None and full_name:
            existing = self.connection.execute("SELECT * FROM repositories WHERE full_name=? COLLATE NOCASE", (full_name,)).fetchone()
        if existing is None and local_git_root:
            existing = self.connection.execute("SELECT * FROM repositories WHERE local_git_root=?", (local_git_root,)).fetchone()
        try:
            with self.connection:
                if existing:
                    rid = int(existing["id"])
                    values = {
                        "github_repo_id": github_repo_id if github_repo_id is not None else existing["github_repo_id"],
                        "github_node_id": github_node_id or existing["github_node_id"], "owner": owner or existing["owner"],
                        "name": name or existing["name"], "full_name": full_name or existing["full_name"],
                        "html_url": html_url or existing["html_url"], "clone_url": clone_url or existing["clone_url"],
                        "default_branch": default_branch or existing["default_branch"],
                        "is_private": int(is_private if github_repo_id is not None else bool(existing["is_private"])),
                        "installation_id": installation_id if installation_id is not None else existing["installation_id"],
                        "local_path": local_path or existing["local_path"], "local_git_root": local_git_root or existing["local_git_root"],
                        "remote_name": remote_name or existing["remote_name"], "language": language or existing["language"],
                        "description": description if description is not None else existing["description"],
                        "last_pushed_at": last_pushed_at or existing["last_pushed_at"],
                        "github_access_state": github_access_state or existing["github_access_state"],
                    }
                    self.connection.execute(
                        """UPDATE repositories SET github_repo_id=:github_repo_id,github_node_id=:github_node_id,owner=:owner,
                           name=:name,full_name=:full_name,html_url=:html_url,clone_url=:clone_url,default_branch=:default_branch,
                           is_private=:is_private,installation_id=:installation_id,local_path=:local_path,local_git_root=:local_git_root,
                           remote_name=:remote_name,language=:language,description=:description,last_pushed_at=:last_pushed_at,
                           github_access_state=:github_access_state,updated_at=:updated_at WHERE id=:id""",
                        {**values, "updated_at": now, "id": rid},
                    )
                else:
                    cursor = self.connection.execute(
                        """INSERT INTO repositories(github_repo_id,github_node_id,owner,name,full_name,html_url,clone_url,
                           default_branch,is_private,installation_id,local_path,local_git_root,remote_name,language,description,
                           last_pushed_at,github_access_state,created_at,updated_at)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (github_repo_id, github_node_id, owner, name, full_name, html_url, clone_url, default_branch,
                         int(is_private), installation_id, local_path, local_git_root, remote_name, language, description,
                         last_pushed_at, github_access_state, now, now),
                    )
                    rid = int(cursor.lastrowid)
            return self.get_repository(rid)  # type: ignore[return-value]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not save repository: {exc}") from exc

    def get_repository(self, repository_id: int) -> Repository | None:
        row = self.connection.execute("SELECT * FROM repositories WHERE id=?", (repository_id,)).fetchone()
        return self._repository_from_row(row) if row else None

    def get_repository_by_full_name(self, full_name: str) -> Repository | None:
        row = self.connection.execute("SELECT * FROM repositories WHERE full_name=? COLLATE NOCASE", (full_name,)).fetchone()
        return self._repository_from_row(row) if row else None

    def list_repositories(self, project_id: int | None = None) -> list[Repository]:
        if project_id is None:
            rows = self.connection.execute("SELECT * FROM repositories ORDER BY EXISTS(SELECT 1 FROM favorites f WHERE f.resource_type='repository' AND f.resource_id=CAST(repositories.id AS TEXT)) DESC, CASE WHEN last_pushed_at IS NULL OR last_pushed_at = '' THEN 1 ELSE 0 END, last_pushed_at DESC, updated_at DESC, COALESCE(full_name,name) COLLATE NOCASE").fetchall()
        else:
            rows = self.connection.execute(
                """SELECT r.* FROM repositories r JOIN project_repositories pr ON pr.repository_id=r.id
                   WHERE pr.project_id=? ORDER BY EXISTS(SELECT 1 FROM favorites f WHERE f.resource_type='repository' AND f.resource_id=CAST(r.id AS TEXT)) DESC, CASE WHEN r.last_pushed_at IS NULL OR r.last_pushed_at = '' THEN 1 ELSE 0 END, r.last_pushed_at DESC, r.updated_at DESC, COALESCE(r.full_name,r.name) COLLATE NOCASE""", (project_id,),
            ).fetchall()
        return [self._repository_from_row(r) for r in rows]

    def link_repository_to_project(self, project_id: int, repository_id: int, monitored_branch: str | None = None) -> None:
        now = utc_now_iso()
        existed = self.connection.execute(
            "SELECT 1 FROM project_repositories WHERE project_id=? AND repository_id=?", (project_id, repository_id)
        ).fetchone() is not None
        repo = self.get_repository(repository_id)
        with self.connection:
            self.connection.execute(
                """INSERT INTO project_repositories(project_id,repository_id,monitored_branch,created_at)
                   VALUES (?,?,?,?) ON CONFLICT(project_id,repository_id) DO UPDATE SET monitored_branch=excluded.monitored_branch""",
                (project_id, repository_id, monitored_branch, now),
            )
            self.connection.execute("UPDATE projects SET updated_at=? WHERE id=?", (now, project_id))
            if not existed:
                label = (repo.full_name or repo.name) if repo else f"Repository #{repository_id}"
                self.connection.execute(
                    """INSERT INTO activity_events(project_id,event_type,title,detail,created_at,repository_id,metadata_json)
                       VALUES (?, 'repository_linked', ?, ?, ?, ?, '{}')""",
                    (project_id, label, monitored_branch or "", now, repository_id),
                )

    def unlink_repository_from_project(self, project_id: int, repository_id: int) -> None:
        repo = self.get_repository(repository_id)
        now = utc_now_iso()
        with self.connection:
            self.connection.execute("DELETE FROM project_repositories WHERE project_id=? AND repository_id=?", (project_id, repository_id))
            self.connection.execute("DELETE FROM resource_links WHERE project_id=? AND repository_id=?", (project_id, repository_id))
            label = (repo.full_name or repo.name) if repo else f"Repository #{repository_id}"
            self.connection.execute(
                """INSERT INTO activity_events(project_id,event_type,title,detail,created_at,repository_id,metadata_json)
                   VALUES (?, 'repository_unlinked', ?, '', ?, ?, '{}')""",
                (project_id, label, now, repository_id),
            )

    def project_repository(self, project_id: int, repository_id: int) -> ProjectRepository | None:
        row = self.connection.execute(
            "SELECT * FROM project_repositories WHERE project_id=? AND repository_id=?", (project_id, repository_id),
        ).fetchone()
        return ProjectRepository(int(row["project_id"]), int(row["repository_id"]), row["monitored_branch"], str(row["created_at"])) if row else None

    def list_projects_for_repository(self, repository_id: int) -> list[Project]:
        rows = self.connection.execute(
            """SELECT p.* FROM projects p
               JOIN project_repositories pr ON pr.project_id=p.id
               WHERE pr.repository_id=? AND p.archived_at IS NULL AND p.trashed_at IS NULL
               ORDER BY p.updated_at DESC, p.name COLLATE NOCASE""",
            (repository_id,),
        ).fetchall()
        return [self._project_from_row(row) for row in rows]

    def update_repository_sync(self, repository_id: int, head_sha: str | None, source: str,
                               success: bool = True, branch: str | None = None) -> None:
        now = utc_now_iso()
        with self.connection:
            self.connection.execute(
                """UPDATE repositories SET last_seen_sha=COALESCE(?,last_seen_sha), last_checked_at=?,
                   last_successful_check_at=CASE WHEN ? THEN ? ELSE last_successful_check_at END,
                   last_check_source=?, default_branch=COALESCE(?,default_branch), updated_at=? WHERE id=?""",
                (head_sha, now, int(success), now, source, branch, now, repository_id),
            )

    def set_repository_github_access_state(self, repository_id: int, state: str) -> None:
        repo = self.get_repository(repository_id)
        previous = repo.github_access_state if repo else None
        now = utc_now_iso()
        with self.connection:
            self.connection.execute("UPDATE repositories SET github_access_state=?,updated_at=? WHERE id=?", (state, now, repository_id))
        if previous != state and state not in {"available", "unknown"}:
            label = (repo.full_name or repo.name) if repo else f"Repository #{repository_id}"
            for project in self.list_projects_for_repository(repository_id):
                self.add_activity(project.id, "repository_access_changed", label, state, repository_id=repository_id)
                self.add_notification(project.id, "repository_access_lost", "Repository access lost", f"{label}: {state}", f"repo-access:{project.id}:{repository_id}:{state}")

    # ------------------------------------------------------------------
    # Resource links and baselines
    # ------------------------------------------------------------------
    def add_resource_link(self, project_id: int, resource_type: str, resource_id: str | int,
                          repository_id: int, target_type: str, target_value: str = "",
                          resource_parent_id: str | int | None = None, github_node_id: str | None = None,
                          metadata: dict[str, object] | None = None) -> ResourceLink:
        now = utc_now_iso()
        parent = "" if resource_parent_id is None else str(resource_parent_id)
        rid = str(resource_id)
        target = target_value.strip().replace("\\", "/")
        payload = json.dumps(metadata or {}, ensure_ascii=False, separators=(",", ":"))
        repo = self.get_repository(repository_id)
        try:
            with self.connection:
                cursor = self.connection.execute(
                    """INSERT INTO resource_links(project_id,resource_type,resource_id,resource_parent_id,repository_id,
                       target_type,target_value,github_node_id,metadata_json,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (project_id, resource_type, rid, parent, repository_id, target_type, target, github_node_id, payload, now),
                )
                repo_label = (repo.full_name or repo.name) if repo else f"Repository #{repository_id}"
                detail = f"{repo_label} · {target_type}: {target or '/'}"
                self.connection.execute(
                    """INSERT INTO activity_events(project_id,event_type,title,detail,created_at,repository_id,resource_type,resource_id,metadata_json)
                       VALUES (?, 'code_linked', ?, ?, ?, ?, ?, ?, ?)""",
                    (project_id, "Code linked", detail, now, repository_id, resource_type, rid, payload),
                )
                if resource_type == "decision":
                    self.connection.execute(
                        """INSERT INTO decision_history(decision_id,event_type,title,detail,metadata_json,created_at)
                           VALUES (?, 'code_linked', 'Code linked', ?, ?, ?)""",
                        (int(resource_id), detail, payload, now),
                    )
            return self.get_resource_link(int(cursor.lastrowid))  # type: ignore[return-value]
        except sqlite3.IntegrityError as exc:
            raise DatabaseError("This resource is already linked to the selected repository target.") from exc
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not link resource: {exc}") from exc

    def get_resource_link(self, link_id: int) -> ResourceLink | None:
        row = self.connection.execute("SELECT * FROM resource_links WHERE id=?", (link_id,)).fetchone()
        return self._resource_link_from_row(row) if row else None

    def list_resource_links(self, resource_type: str | None = None, resource_id: str | int | None = None,
                            resource_parent_id: str | int | None = None, project_id: int | None = None,
                            repository_id: int | None = None) -> list[ResourceLink]:
        where: list[str] = []
        params: list[object] = []
        for column, value in (("resource_type", resource_type), ("resource_id", resource_id),
                              ("resource_parent_id", resource_parent_id), ("project_id", project_id),
                              ("repository_id", repository_id)):
            if value is not None:
                where.append(f"{column}=?")
                params.append(str(value) if column in {"resource_id", "resource_parent_id"} else value)
        sql = "SELECT * FROM resource_links"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY created_at"
        return [self._resource_link_from_row(r) for r in self.connection.execute(sql, params).fetchall()]

    def remove_resource_link(self, link_id: int) -> None:
        row = self.connection.execute("SELECT * FROM resource_links WHERE id=?", (link_id,)).fetchone()
        if not row:
            return
        repo = self.get_repository(int(row["repository_id"]))
        now = utc_now_iso()
        with self.connection:
            self.connection.execute("DELETE FROM resource_links WHERE id=?", (link_id,))
            remaining = self.connection.execute(
                """SELECT 1 FROM resource_links WHERE resource_type=? AND resource_id=? AND resource_parent_id=? AND repository_id=? LIMIT 1""",
                (row["resource_type"], row["resource_id"], row["resource_parent_id"], row["repository_id"]),
            ).fetchone()
            if not remaining:
                self.connection.execute(
                    "DELETE FROM review_baselines WHERE resource_type=? AND resource_id=? AND resource_parent_id=? AND repository_id=?",
                    (row["resource_type"], row["resource_id"], row["resource_parent_id"], row["repository_id"]),
                )
            repo_label = (repo.full_name or repo.name) if repo else f"Repository #{row['repository_id']}"
            detail = f"{repo_label} · {row['target_type']}: {row['target_value'] or '/'}"
            self.connection.execute(
                """INSERT INTO activity_events(project_id,event_type,title,detail,created_at,repository_id,resource_type,resource_id,metadata_json)
                   VALUES (?, 'code_unlinked', 'Code unlinked', ?, ?, ?, ?, ?, '{}')""",
                (int(row["project_id"]), detail, now, int(row["repository_id"]), str(row["resource_type"]), str(row["resource_id"])),
            )
            if str(row["resource_type"]) == "decision":
                self.connection.execute(
                    "INSERT INTO decision_history(decision_id,event_type,title,detail,metadata_json,created_at) VALUES (?, 'code_unlinked', 'Code unlinked', ?, '{}', ?)",
                    (int(row["resource_id"]), detail, now),
                )

    def delete_resource_context(self, resource_type: str, resource_id: str | int,
                                resource_parent_id: str | int | None = None) -> None:
        """Remove DevNest-only links/baselines for a deleted knowledge sub-resource.

        This never deletes a note, repository, source file, commit, or GitHub object.
        It exists mainly for stable diagram item IDs whose lifecycle is stored inside
        the legacy diagram JSON rather than represented by a relational FK.
        """
        parent = "" if resource_parent_id is None else str(resource_parent_id)
        rid = str(resource_id)
        with self.connection:
            self.connection.execute(
                "DELETE FROM review_baselines WHERE resource_type=? AND resource_id=? AND resource_parent_id=?",
                (resource_type, rid, parent),
            )
            self.connection.execute(
                "DELETE FROM resource_links WHERE resource_type=? AND resource_id=? AND resource_parent_id=?",
                (resource_type, rid, parent),
            )

    def upsert_review_baseline(self, resource_type: str, resource_id: str | int, repository_id: int,
                               baseline_sha: str, branch: str | None, resource_parent_id: str | int | None = None) -> ReviewBaseline:
        now = utc_now_iso()
        parent = "" if resource_parent_id is None else str(resource_parent_id)
        rid = str(resource_id)
        link_row = self.connection.execute(
            """SELECT project_id FROM resource_links WHERE resource_type=? AND resource_id=? AND resource_parent_id=? AND repository_id=?
               ORDER BY id LIMIT 1""", (resource_type, rid, parent, repository_id)
        ).fetchone()
        project_id = int(link_row["project_id"]) if link_row else None
        repo = self.get_repository(repository_id)
        with self.connection:
            self.connection.execute(
                """INSERT INTO review_baselines(resource_type,resource_id,resource_parent_id,repository_id,baseline_sha,branch,
                   reviewed_at,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(resource_type,resource_id,resource_parent_id,repository_id) DO UPDATE SET
                   baseline_sha=excluded.baseline_sha,branch=excluded.branch,reviewed_at=excluded.reviewed_at,updated_at=excluded.updated_at""",
                (resource_type, rid, parent, repository_id, baseline_sha, branch, now, now, now),
            )
            if project_id is not None:
                self.connection.execute(
                    """INSERT INTO review_history(project_id,resource_type,resource_id,resource_parent_id,repository_id,baseline_sha,branch,reviewed_at)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (project_id, resource_type, rid, parent, repository_id, baseline_sha, branch, now),
                )
                repo_label = (repo.full_name or repo.name) if repo else f"Repository #{repository_id}"
                detail = f"{repo_label} @ {baseline_sha[:8]}"
                self.connection.execute(
                    """INSERT INTO activity_events(project_id,event_type,title,detail,created_at,repository_id,resource_type,resource_id,metadata_json)
                       VALUES (?, 'marked_reviewed', 'Marked as Reviewed', ?, ?, ?, ?, ?, ?)""",
                    (project_id, detail, now, repository_id, resource_type, rid,
                     json.dumps({"sha": baseline_sha, "branch": branch}, separators=(",", ":"))),
                )
                if resource_type == "decision":
                    self.connection.execute(
                        """INSERT INTO decision_history(decision_id,event_type,title,detail,metadata_json,created_at)
                           VALUES (?, 'reviewed', 'Reviewed', ?, ?, ?)""",
                        (int(resource_id), detail, json.dumps({"sha": baseline_sha, "branch": branch}, separators=(",", ":")), now),
                    )
        baseline = self.get_review_baseline(resource_type, rid, repository_id, parent)
        if baseline is None:
            raise DatabaseError("Review baseline could not be saved.")
        return baseline

    def get_review_baseline(self, resource_type: str, resource_id: str | int, repository_id: int,
                            resource_parent_id: str | int | None = None) -> ReviewBaseline | None:
        parent = "" if resource_parent_id is None else str(resource_parent_id)
        row = self.connection.execute(
            """SELECT * FROM review_baselines WHERE resource_type=? AND resource_id=? AND resource_parent_id=? AND repository_id=?""",
            (resource_type, str(resource_id), parent, repository_id),
        ).fetchone()
        return self._baseline_from_row(row) if row else None

    def list_review_baselines(self, project_id: int | None = None) -> list[ReviewBaseline]:
        if project_id is None:
            rows = self.connection.execute("SELECT * FROM review_baselines").fetchall()
        else:
            rows = self.connection.execute(
                """SELECT b.* FROM review_baselines b JOIN resource_links l
                   ON l.resource_type=b.resource_type AND l.resource_id=b.resource_id AND l.resource_parent_id=b.resource_parent_id
                   AND l.repository_id=b.repository_id WHERE l.project_id=? GROUP BY b.id""", (project_id,),
            ).fetchall()
        return [self._baseline_from_row(r) for r in rows]

    # ------------------------------------------------------------------
    # Repository comparison cache
    # ------------------------------------------------------------------
    def save_repository_change(self, repository_id: int, from_sha: str, to_sha: str, source: str,
                               commit_count: int, changed_files: Sequence[ChangedFile], commits: Sequence[CommitInfo] = (),
                               pull_requests: Sequence[PullRequestInfo] = ()) -> RepositoryChange:
        now = utc_now_iso()
        files_json = json.dumps([{"status": f.status, "path": f.path, "previous_path": f.previous_path} for f in changed_files])
        commits_json = json.dumps([{"sha": c.sha, "message": c.message, "author": c.author,
                                    "authored_at": c.authored_at, "html_url": c.html_url} for c in commits])
        prs_json = json.dumps([{"number": p.number, "title": p.title, "state": p.state, "html_url": p.html_url,
                                "merged_at": p.merged_at, "updated_at": p.updated_at} for p in pull_requests])
        existed = self.connection.execute(
            "SELECT 1 FROM repository_changes WHERE repository_id=? AND from_sha=? AND to_sha=? AND source=?",
            (repository_id, from_sha, to_sha, source),
        ).fetchone() is not None
        with self.connection:
            self.connection.execute(
                """INSERT INTO repository_changes(repository_id,from_sha,to_sha,source,commit_count,changed_files_json,
                   commits_json,pull_requests_json,detected_at) VALUES (?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(repository_id,from_sha,to_sha,source) DO UPDATE SET commit_count=excluded.commit_count,
                   changed_files_json=excluded.changed_files_json,commits_json=excluded.commits_json,
                   pull_requests_json=excluded.pull_requests_json,detected_at=excluded.detected_at""",
                (repository_id, from_sha, to_sha, source, commit_count, files_json, commits_json, prs_json, now),
            )
        if not existed and from_sha != to_sha:
            repo = self.get_repository(repository_id)
            repo_label = (repo.full_name or repo.name) if repo else f"Repository #{repository_id}"
            for project in self.list_projects_for_repository(repository_id):
                detail = f"{commit_count} commit(s) · {from_sha[:8]} → {to_sha[:8]}"
                self.add_activity(project.id, "commits_detected", repo_label, detail, repository_id=repository_id,
                                  metadata={"from_sha": from_sha, "to_sha": to_sha, "commit_count": commit_count})
                self.add_notification(project.id, "commits_detected", "New commits detected",
                                      f"{repo_label}: {commit_count} new commit(s)",
                                      f"commits:{project.id}:{repository_id}:{to_sha}")
        return self.get_repository_change(repository_id, from_sha, to_sha, source)  # type: ignore[return-value]

    def get_repository_change(self, repository_id: int, from_sha: str, to_sha: str, source: str | None = None) -> RepositoryChange | None:
        params: list[object] = [repository_id, from_sha, to_sha]
        sql = "SELECT * FROM repository_changes WHERE repository_id=? AND from_sha=? AND to_sha=?"
        if source:
            sql += " AND source=?"
            params.append(source)
        sql += " ORDER BY detected_at DESC LIMIT 1"
        row = self.connection.execute(sql, params).fetchone()
        if not row:
            return None
        def loads_list(key: str) -> list[dict[str, object]]:
            try:
                value = json.loads(str(row[key] or "[]"))
                return value if isinstance(value, list) else []
            except json.JSONDecodeError:
                return []
        files = [ChangedFile(str(x.get("status", "M")), str(x.get("path", "")),
                             str(x["previous_path"]) if x.get("previous_path") else None) for x in loads_list("changed_files_json")]
        commits = [CommitInfo(str(x.get("sha", "")), str(x.get("message", "")),
                              str(x["author"]) if x.get("author") else None,
                              str(x["authored_at"]) if x.get("authored_at") else None,
                              str(x["html_url"]) if x.get("html_url") else None) for x in loads_list("commits_json")]
        prs = [PullRequestInfo(int(x.get("number", 0)), str(x.get("title", "")), str(x.get("state", "")),
                               str(x.get("html_url", "")), str(x["merged_at"]) if x.get("merged_at") else None,
                               str(x["updated_at"]) if x.get("updated_at") else None) for x in loads_list("pull_requests_json")]
        return RepositoryChange(int(row["id"]), int(row["repository_id"]), str(row["from_sha"]), str(row["to_sha"]),
                                str(row["source"]), int(row["commit_count"]), files, commits, prs, str(row["detected_at"]))

    # ------------------------------------------------------------------
    # GitHub metadata cache (never tokens)
    # ------------------------------------------------------------------
    def save_github_account(self, github_user_id: int, login: str, avatar_url: str | None) -> GitHubAccount:
        now = utc_now_iso()
        with self.connection:
            self.connection.execute(
                """INSERT INTO github_accounts(github_user_id,login,avatar_url,connected_at,last_validated_at)
                   VALUES (?,?,?,?,?) ON CONFLICT(github_user_id) DO UPDATE SET login=excluded.login,avatar_url=excluded.avatar_url,
                   last_validated_at=excluded.last_validated_at""", (github_user_id, login, avatar_url, now, now),
            )
        return GitHubAccount(github_user_id, login, avatar_url, now, now)

    def get_github_account(self) -> GitHubAccount | None:
        row = self.connection.execute("SELECT * FROM github_accounts ORDER BY connected_at DESC LIMIT 1").fetchone()
        return GitHubAccount(int(row["github_user_id"]), str(row["login"]), row["avatar_url"], str(row["connected_at"]), row["last_validated_at"]) if row else None

    def touch_github_account_validation(self, github_user_id: int) -> None:
        with self.connection:
            self.connection.execute("UPDATE github_accounts SET last_validated_at=? WHERE github_user_id=?", (utc_now_iso(), github_user_id))

    def save_github_installations(self, installations: Iterable[GitHubInstallation]) -> None:
        # This table is a cache of the installations visible to the current user
        # access token. Replace it as a set so removed GitHub App installations
        # do not remain visible forever. Repository/link data is intentionally
        # preserved elsewhere.
        items = list(installations)
        with self.connection:
            self.connection.execute("DELETE FROM github_installations")
            for item in items:
                self.connection.execute(
                    """INSERT INTO github_installations(id,account_login,account_type,account_avatar_url,target_type,last_synced_at)
                       VALUES (?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET account_login=excluded.account_login,
                       account_type=excluded.account_type,account_avatar_url=excluded.account_avatar_url,
                       target_type=excluded.target_type,last_synced_at=excluded.last_synced_at""",
                    (item.id, item.account_login, item.account_type, item.account_avatar_url, item.target_type, item.last_synced_at),
                )

    def list_github_installations(self) -> list[GitHubInstallation]:
        return [GitHubInstallation(int(r["id"]), str(r["account_login"]), str(r["account_type"]), r["account_avatar_url"],
                                   r["target_type"], str(r["last_synced_at"]))
                for r in self.connection.execute("SELECT * FROM github_installations ORDER BY account_type,account_login COLLATE NOCASE").fetchall()]

    def disconnect_github_metadata(self) -> None:
        # Intentionally preserves projects, repository mappings, links, baselines and cached repository metadata.
        with self.connection:
            self.connection.execute("DELETE FROM github_accounts")
            self.connection.execute("DELETE FROM github_installations")

    # ------------------------------------------------------------------
    # Search/activity/settings
    # ------------------------------------------------------------------
    def global_search(self, query: str, limit: int = 80) -> list[tuple[str, int, str, str]]:
        """Search user-visible workspace data, code paths and cached commit messages.

        The historical four-column return shape is intentionally retained for
        compatibility with older callers/tests. Code-resource results use the
        resource-link id as the integer identifier; repository and commit hits
        use the repository id so the UI can open the repository/code detail.
        """
        term = query.strip()
        if not term:
            return []
        like = f"%{term}%"
        results: list[tuple[str, int, str, str]] = []

        def room() -> int:
            return max(0, limit - len(results))

        for row in self.connection.execute(
            """SELECT p.id,p.name,p.description FROM projects p
               WHERE p.archived_at IS NULL AND p.trashed_at IS NULL
                 AND (p.name LIKE ? COLLATE NOCASE OR p.description LIKE ? COLLATE NOCASE)
               ORDER BY EXISTS(SELECT 1 FROM favorites f WHERE f.resource_type='project' AND f.resource_id=CAST(p.id AS TEXT)) DESC,
                        p.updated_at DESC LIMIT ?""",
            (like, like, room()),
        ).fetchall():
            results.append(("project", int(row["id"]), str(row["name"]), str(row["description"] or "")))

        if room():
            for row in self.connection.execute(
                """SELECT n.id,n.title,n.content_plain FROM notes n
                   WHERE n.is_deleted=0 AND n.id NOT IN (SELECT note_id FROM decisions)
                     AND (n.title LIKE ? COLLATE NOCASE OR n.content_plain LIKE ? COLLATE NOCASE OR EXISTS(
                         SELECT 1 FROM resource_tags rt JOIN tags t ON t.id=rt.tag_id
                         WHERE rt.resource_type='note' AND rt.resource_id=CAST(n.id AS TEXT) AND t.name LIKE ? COLLATE NOCASE))
                   ORDER BY EXISTS(SELECT 1 FROM favorites f WHERE f.resource_type='note' AND f.resource_id=CAST(n.id AS TEXT)) DESC,
                            n.updated_at DESC LIMIT ?""",
                (like, like, like, room()),
            ).fetchall():
                results.append(("note", int(row["id"]), str(row["title"]), str(row["content_plain"] or "")[:220]))

        if room():
            for row in self.connection.execute(
                """SELECT d.id,d.decision_key,n.title,n.content_plain FROM decisions d JOIN notes n ON n.id=d.note_id
                   WHERE n.is_deleted=0 AND (d.decision_key LIKE ? COLLATE NOCASE OR n.title LIKE ? COLLATE NOCASE OR n.content_plain LIKE ? COLLATE NOCASE OR EXISTS(
                       SELECT 1 FROM resource_tags rt JOIN tags t ON t.id=rt.tag_id
                       WHERE rt.resource_type='decision' AND rt.resource_id=CAST(d.id AS TEXT) AND t.name LIKE ? COLLATE NOCASE))
                   ORDER BY EXISTS(SELECT 1 FROM favorites f WHERE f.resource_type='decision' AND f.resource_id=CAST(d.id AS TEXT)) DESC,
                            d.updated_at DESC LIMIT ?""",
                (like, like, like, like, room()),
            ).fetchall():
                results.append(("decision", int(row["id"]), f"{row['decision_key']} · {row['title']}", str(row["content_plain"] or "")[:220]))

        if room():
            for row in self.connection.execute(
                """SELECT r.id,COALESCE(r.full_name,r.name) label,r.description,r.local_git_root
                   FROM repositories r
                   WHERE COALESCE(r.full_name,r.name) LIKE ? COLLATE NOCASE
                      OR COALESCE(r.description,'') LIKE ? COLLATE NOCASE
                      OR COALESCE(r.local_git_root,'') LIKE ? COLLATE NOCASE
                   ORDER BY EXISTS(SELECT 1 FROM favorites f WHERE f.resource_type='repository' AND f.resource_id=CAST(r.id AS TEXT)) DESC,
                            r.updated_at DESC LIMIT ?""",
                (like, like, like, room()),
            ).fetchall():
                detail = str(row["description"] or row["local_git_root"] or "")
                results.append(("repository", int(row["id"]), str(row["label"]), detail[:220]))

        if room():
            for row in self.connection.execute(
                """SELECT rl.id,rl.repository_id,rl.target_type,rl.target_value,COALESCE(r.full_name,r.name) repo_name
                   FROM resource_links rl JOIN repositories r ON r.id=rl.repository_id
                   WHERE rl.target_value LIKE ? COLLATE NOCASE
                   ORDER BY rl.created_at DESC LIMIT ?""",
                (like, room()),
            ).fetchall():
                target = str(row["target_value"] or "/")
                results.append(("code", int(row["id"]), target, f"{row['repo_name']} · {row['target_type']}"))

        if room():
            # Commit messages are cached as JSON. LIKE is sufficient here and
            # avoids making JSON1 a hard SQLite build requirement.
            for row in self.connection.execute(
                """SELECT rc.repository_id,rc.commits_json,COALESCE(r.full_name,r.name) repo_name
                   FROM repository_changes rc JOIN repositories r ON r.id=rc.repository_id
                   WHERE rc.commits_json LIKE ? COLLATE NOCASE
                   ORDER BY rc.detected_at DESC LIMIT ?""",
                (like, room()),
            ).fetchall():
                try:
                    commits = json.loads(str(row["commits_json"] or "[]"))
                except json.JSONDecodeError:
                    commits = []
                for commit in commits if isinstance(commits, list) else []:
                    message = str(commit.get("message") or "") if isinstance(commit, dict) else ""
                    if term.casefold() not in message.casefold():
                        continue
                    sha = str(commit.get("sha") or "") if isinstance(commit, dict) else ""
                    results.append(("commit", int(row["repository_id"]), f"{sha[:8]} · {message}", str(row["repo_name"])))
                    if not room():
                        break

        return results[:limit]

    def add_activity(self, project_id: int | None, event_type: str, title: str, detail: str = "",
                     *, repository_id: int | None = None, resource_type: str | None = None,
                     resource_id: str | int | None = None, metadata: dict[str, object] | None = None) -> None:
        with self.connection:
            self.connection.execute(
                """INSERT INTO activity_events(project_id,event_type,title,detail,created_at,repository_id,resource_type,resource_id,metadata_json)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (project_id, event_type, title, detail, utc_now_iso(), repository_id, resource_type,
                 None if resource_id is None else str(resource_id),
                 json.dumps(metadata or {}, ensure_ascii=False, separators=(",", ":"))),
            )

    def list_activity(self, project_id: int | None = None, limit: int = 100,
                      repository_id: int | None = None, days: int | None = None) -> list[sqlite3.Row]:
        where: list[str] = []
        params: list[object] = []
        if project_id is not None:
            where.append("project_id=?")
            params.append(project_id)
        if repository_id is not None:
            where.append("repository_id=?")
            params.append(repository_id)
        if days is not None and days > 0:
            where.append("datetime(created_at) >= datetime('now', ?)")
            params.append(f"-{int(days)} days")
        sql = "SELECT * FROM activity_events"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(limit)
        return self.connection.execute(sql, params).fetchall()

    def add_decision_history(self, decision_id: int, event_type: str, title: str, detail: str = "",
                             metadata: dict[str, object] | None = None) -> None:
        with self.connection:
            self.connection.execute(
                "INSERT INTO decision_history(decision_id,event_type,title,detail,metadata_json,created_at) VALUES (?,?,?,?,?,?)",
                (decision_id, event_type, title, detail,
                 json.dumps(metadata or {}, ensure_ascii=False, separators=(",", ":")), utc_now_iso()),
            )

    def add_decision_history_once(self, decision_id: int, event_type: str, title: str, detail: str = "",
                                  *, unique_key: str, metadata: dict[str, object] | None = None) -> bool:
        rows = self.connection.execute(
            "SELECT metadata_json FROM decision_history WHERE decision_id=? AND event_type=? ORDER BY id DESC LIMIT 100",
            (decision_id, event_type),
        ).fetchall()
        for row in rows:
            try:
                existing = json.loads(str(row["metadata_json"] or "{}"))
            except json.JSONDecodeError:
                existing = {}
            if str(existing.get("unique_key") or "") == unique_key:
                return False
        payload = dict(metadata or {})
        payload["unique_key"] = unique_key
        self.add_decision_history(decision_id, event_type, title, detail, payload)
        return True

    def list_decision_history(self, decision_id: int, limit: int = 200) -> list[sqlite3.Row]:
        return self.connection.execute(
            "SELECT * FROM decision_history WHERE decision_id=? ORDER BY created_at DESC,id DESC LIMIT ?",
            (decision_id, limit),
        ).fetchall()

    def list_review_history(self, resource_type: str, resource_id: str | int,
                            resource_parent_id: str | int | None = None, limit: int = 100) -> list[sqlite3.Row]:
        parent = "" if resource_parent_id is None else str(resource_parent_id)
        return self.connection.execute(
            """SELECT h.*,COALESCE(r.full_name,r.name) repository_name FROM review_history h
               JOIN repositories r ON r.id=h.repository_id
               WHERE h.resource_type=? AND h.resource_id=? AND h.resource_parent_id=?
               ORDER BY h.reviewed_at DESC,h.id DESC LIMIT ?""",
            (resource_type, str(resource_id), parent, limit),
        ).fetchall()

    @staticmethod
    def _normalize_tag_names(names: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        clean: list[str] = []
        for raw in names:
            name = str(raw).strip().lstrip("#")
            if not name or len(name) > 48:
                continue
            key = name.casefold()
            if key in seen:
                continue
            seen.add(key)
            clean.append(name)
        return clean

    def set_tags(self, resource_type: str, resource_id: str | int, tags: Iterable[str]) -> list[str]:
        names = self._normalize_tag_names(tags)
        rid = str(resource_id)
        now = utc_now_iso()
        with self.connection:
            self.connection.execute("DELETE FROM resource_tags WHERE resource_type=? AND resource_id=?", (resource_type, rid))
            for name in names:
                self.connection.execute("INSERT OR IGNORE INTO tags(name,created_at) VALUES (?,?)", (name, now))
                tag_row = self.connection.execute("SELECT id FROM tags WHERE name=? COLLATE NOCASE", (name,)).fetchone()
                if tag_row:
                    self.connection.execute(
                        "INSERT OR IGNORE INTO resource_tags(resource_type,resource_id,tag_id,created_at) VALUES (?,?,?,?)",
                        (resource_type, rid, int(tag_row["id"]), now),
                    )
        return self.get_tags(resource_type, rid)

    def get_tags(self, resource_type: str, resource_id: str | int) -> list[str]:
        return [str(r["name"]) for r in self.connection.execute(
            """SELECT t.name FROM tags t JOIN resource_tags rt ON rt.tag_id=t.id
               WHERE rt.resource_type=? AND rt.resource_id=? ORDER BY t.name COLLATE NOCASE""",
            (resource_type, str(resource_id)),
        ).fetchall()]

    def list_tags(self) -> list[str]:
        return [str(r["name"]) for r in self.connection.execute("SELECT name FROM tags ORDER BY name COLLATE NOCASE").fetchall()]

    def set_favorite(self, resource_type: str, resource_id: str | int, favorite: bool,
                     project_id: int | None = None) -> None:
        rid = str(resource_id)
        with self.connection:
            if favorite:
                self.connection.execute(
                    "INSERT OR REPLACE INTO favorites(resource_type,resource_id,project_id,created_at) VALUES (?,?,?,?)",
                    (resource_type, rid, project_id, utc_now_iso()),
                )
            else:
                self.connection.execute("DELETE FROM favorites WHERE resource_type=? AND resource_id=?", (resource_type, rid))

    def is_favorite(self, resource_type: str, resource_id: str | int) -> bool:
        return self.connection.execute(
            "SELECT 1 FROM favorites WHERE resource_type=? AND resource_id=?", (resource_type, str(resource_id))
        ).fetchone() is not None

    def touch_recent(self, resource_type: str, resource_id: str | int, title: str,
                     project_id: int | None = None, detail: str = "") -> None:
        with self.connection:
            self.connection.execute(
                """INSERT INTO recent_items(resource_type,resource_id,project_id,title,detail,opened_at) VALUES (?,?,?,?,?,?)
                   ON CONFLICT(resource_type,resource_id) DO UPDATE SET project_id=excluded.project_id,title=excluded.title,
                       detail=excluded.detail,opened_at=excluded.opened_at""",
                (resource_type, str(resource_id), project_id, title, detail, utc_now_iso()),
            )

    def list_recent(self, project_id: int | None = None, limit: int = 12) -> list[sqlite3.Row]:
        """Return recent work only for projects that still exist and are active.

        ``recent_items`` deliberately has no cascading foreign key because it is
        session/history metadata. A project can therefore remain referenced after
        being moved to Trash or permanently deleted. Filtering through ``projects``
        here keeps Dashboard/Continue Working from resurrecting deleted projects.
        """
        params: list[object] = []
        if project_id is None:
            # Preserve any intentionally project-less recent entries for callers
            # that request the global history, while still filtering stale project
            # references. Dashboard normally uses the project-scoped branch below.
            where = [
                "(ri.project_id IS NULL OR (p.id IS NOT NULL AND p.trashed_at IS NULL AND p.archived_at IS NULL))"
            ]
        else:
            where = [
                "p.id IS NOT NULL", "p.trashed_at IS NULL", "p.archived_at IS NULL", "ri.project_id=?"
            ]
            params.append(project_id)
        params.append(limit)
        return self.connection.execute(
            f"""SELECT ri.* FROM recent_items ri
                LEFT JOIN projects p ON p.id=ri.project_id
                WHERE {' AND '.join(where)}
                ORDER BY ri.opened_at DESC LIMIT ?""",
            params,
        ).fetchall()

    def add_notification(self, project_id: int | None, event_type: str, title: str, detail: str = "",
                         notification_key: str | None = None) -> None:
        with self.connection:
            self.connection.execute(
                """INSERT OR IGNORE INTO notifications(project_id,event_type,title,detail,notification_key,is_read,created_at)
                   VALUES (?,?,?,?,?,0,?)""",
                (project_id, event_type, title, detail, notification_key, utc_now_iso()),
            )

    def list_notifications(self, unread_only: bool = False, limit: int = 100) -> list[sqlite3.Row]:
        sql = "SELECT * FROM notifications"
        params: list[object] = []
        if unread_only:
            sql += " WHERE is_read=0"
        sql += " ORDER BY created_at DESC,id DESC LIMIT ?"
        params.append(limit)
        return self.connection.execute(sql, params).fetchall()

    def unread_notification_count(self) -> int:
        return int(self.connection.execute("SELECT COUNT(*) FROM notifications WHERE is_read=0").fetchone()[0])

    def mark_notifications_read(self) -> None:
        with self.connection:
            self.connection.execute("UPDATE notifications SET is_read=1 WHERE is_read=0")

    def backlinks_for_path(self, repository_id: int, path: str) -> list[sqlite3.Row]:
        """Return knowledge resources whose link scope contains *path*."""
        normalized = path.replace("\\", "/").strip("/")
        rows = self.connection.execute(
            """SELECT rl.*,COALESCE(r.full_name,r.name) repository_name FROM resource_links rl
               JOIN repositories r ON r.id=rl.repository_id WHERE rl.repository_id=?
               ORDER BY rl.created_at DESC""", (repository_id,)
        ).fetchall()
        matches: list[sqlite3.Row] = []
        for row in rows:
            target_type = str(row["target_type"])
            target = str(row["target_value"] or "").replace("\\", "/").strip("/")
            if target_type == "repository":
                matches.append(row)
            elif target_type == "file" and target == normalized:
                matches.append(row)
            elif target_type == "directory" and (not target or normalized == target or normalized.startswith(target + "/")):
                matches.append(row)
        return matches

    def describe_resource(self, resource_type: str, resource_id: str, resource_parent_id: str = "") -> tuple[str, str]:
        if resource_type == "note":
            try:
                note = self.get_note(int(resource_id))
            except ValueError:
                note = None
            return (note.title if note else f"Note #{resource_id}", "note")
        if resource_type == "decision":
            try:
                decision = self.get_decision(int(resource_id))
            except ValueError:
                decision = None
            return ((f"{decision.decision_key} · {decision.title}" if decision else f"Decision #{resource_id}"), "decision")
        if resource_type == "diagram_item":
            try:
                note = self.get_note(int(resource_parent_id))
            except ValueError:
                note = None
            return ((note.title if note else "Architecture") + f" · node {resource_id[:8]}", "architecture")
        return (f"{resource_type} #{resource_id}", resource_type)

    def resource_links_for_path(self, repository_id: int, path: str) -> list[tuple[sqlite3.Row, str, str]]:
        result: list[tuple[sqlite3.Row, str, str]] = []
        for row in self.backlinks_for_path(repository_id, path):
            title, kind = self.describe_resource(str(row["resource_type"]), str(row["resource_id"]), str(row["resource_parent_id"] or ""))
            result.append((row, title, kind))
        return result

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        row = self.connection.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return str(row["value"]) if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self.connection:
            self.connection.execute(
                "INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value)
            )

    def table_names(self) -> set[str]:
        return {str(r[0]) for r in self.connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

    def index_names(self) -> set[str]:
        return {str(r[0]) for r in self.connection.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()}

    def optimize(self) -> None:
        try:
            self.connection.execute("VACUUM")
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not optimize database: {exc}") from exc

    def close(self) -> None:
        try:
            self.connection.close()
        except sqlite3.Error:
            pass

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

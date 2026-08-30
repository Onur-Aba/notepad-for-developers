from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from app.constants import DEFAULT_NOTE_TITLE
from app.models import Note, NoteSummary


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class DatabaseError(RuntimeError):
    pass


class Database:
    SCHEMA_VERSION = 1

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
        except sqlite3.Error as exc:
            raise DatabaseError(f"Database could not be opened: {exc}") from exc

    def _migrate(self) -> None:
        try:
            version = int(self.connection.execute("PRAGMA user_version").fetchone()[0])
            if version > self.SCHEMA_VERSION:
                raise DatabaseError(
                    f"Database schema {version} is newer than supported schema {self.SCHEMA_VERSION}."
                )
            if version < 1:
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
        except sqlite3.Error as exc:
            raise DatabaseError(f"Database migration failed: {exc}") from exc

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
        )

    def create_note(
        self,
        title: str = DEFAULT_NOTE_TITLE,
        content_html: str = "",
        content_plain: str = "",
    ) -> Note:
        now = utc_now_iso()
        safe_title = title.strip() or DEFAULT_NOTE_TITLE
        try:
            with self.connection:
                cursor = self.connection.execute(
                    """
                    INSERT INTO notes(title, content_html, content_plain, created_at, updated_at, is_deleted)
                    VALUES (?, ?, ?, ?, ?, 0)
                    """,
                    (safe_title, content_html, content_plain, now, now),
                )
            note_id = int(cursor.lastrowid)
            note = self.get_note(note_id)
            if note is None:
                raise DatabaseError("Created note could not be reloaded.")
            return note
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not create note: {exc}") from exc

    def get_note(self, note_id: int, include_deleted: bool = False) -> Note | None:
        sql = "SELECT * FROM notes WHERE id = ?"
        params: tuple[object, ...] = (note_id,)
        if not include_deleted:
            sql += " AND is_deleted = 0"
        row = self.connection.execute(sql, params).fetchone()
        return self._note_from_row(row) if row else None

    def update_note(self, note_id: int, title: str, content_html: str, content_plain: str) -> None:
        now = utc_now_iso()
        safe_title = title.strip() or DEFAULT_NOTE_TITLE
        try:
            with self.connection:
                cursor = self.connection.execute(
                    """
                    UPDATE notes
                    SET title = ?, content_html = ?, content_plain = ?, updated_at = ?
                    WHERE id = ? AND is_deleted = 0
                    """,
                    (safe_title, content_html, content_plain, now, note_id),
                )
            if cursor.rowcount == 0:
                raise DatabaseError("The note no longer exists or is in Trash.")
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
            title=f"{source.title} Copy",
            content_html=source.content_html,
            content_plain=source.content_plain,
        )
        diagram = self.get_diagram(note_id)
        if diagram:
            self.save_diagram(copy.id, diagram)
        return copy

    def list_notes(self, search: str = "", sort: str = "updated") -> list[NoteSummary]:
        where = ["is_deleted = 0"]
        params: list[object] = []
        term = search.strip()
        if term:
            where.append("(title LIKE ? COLLATE NOCASE OR content_plain LIKE ? COLLATE NOCASE)")
            like = f"%{term}%"
            params.extend([like, like])
        order_by = "updated_at DESC" if sort == "updated" else "title COLLATE NOCASE ASC, updated_at DESC"
        rows = self.connection.execute(
            f"""
            SELECT id, title,
                   substr(replace(replace(content_plain, char(10), ' '), char(13), ' '), 1, 140) AS preview,
                   created_at, updated_at, is_deleted
            FROM notes
            WHERE {' AND '.join(where)}
            ORDER BY {order_by}
            """,
            params,
        ).fetchall()
        return [
            NoteSummary(
                id=int(row["id"]),
                title=str(row["title"]),
                preview=str(row["preview"] or ""),
                created_at=str(row["created_at"]),
                updated_at=str(row["updated_at"]),
                is_deleted=bool(row["is_deleted"]),
            )
            for row in rows
        ]

    def list_trash(self) -> list[NoteSummary]:
        rows = self.connection.execute(
            """
            SELECT id, title,
                   substr(replace(replace(content_plain, char(10), ' '), char(13), ' '), 1, 140) AS preview,
                   created_at, updated_at, is_deleted
            FROM notes WHERE is_deleted = 1 ORDER BY updated_at DESC
            """
        ).fetchall()
        return [
            NoteSummary(
                id=int(row["id"]),
                title=str(row["title"]),
                preview=str(row["preview"] or ""),
                created_at=str(row["created_at"]),
                updated_at=str(row["updated_at"]),
                is_deleted=True,
            )
            for row in rows
        ]

    def soft_delete_note(self, note_id: int) -> None:
        try:
            with self.connection:
                self.connection.execute(
                    "UPDATE notes SET is_deleted = 1, updated_at = ? WHERE id = ?",
                    (utc_now_iso(), note_id),
                )
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not move note to Trash: {exc}") from exc

    def restore_note(self, note_id: int) -> None:
        try:
            with self.connection:
                self.connection.execute(
                    "UPDATE notes SET is_deleted = 0, updated_at = ? WHERE id = ?",
                    (utc_now_iso(), note_id),
                )
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not restore note: {exc}") from exc

    def permanently_delete_note(self, note_id: int) -> None:
        try:
            with self.connection:
                self.connection.execute("DELETE FROM notes WHERE id = ? AND is_deleted = 1", (note_id,))
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not permanently delete note: {exc}") from exc

    def empty_trash(self) -> int:
        try:
            with self.connection:
                cursor = self.connection.execute("DELETE FROM notes WHERE is_deleted = 1")
            return int(cursor.rowcount)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not empty Trash: {exc}") from exc

    def save_diagram(self, note_id: int, data: dict[str, object] | str) -> None:
        data_json = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        now = utc_now_iso()
        try:
            with self.connection:
                self.connection.execute(
                    """
                    INSERT INTO diagrams(note_id, data_json, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(note_id) DO UPDATE SET
                        data_json = excluded.data_json,
                        updated_at = excluded.updated_at
                    """,
                    (note_id, data_json, now),
                )
        except sqlite3.Error as exc:
            raise DatabaseError(f"Could not save diagram: {exc}") from exc

    def get_diagram(self, note_id: int) -> dict[str, object]:
        row = self.connection.execute("SELECT data_json FROM diagrams WHERE note_id = ?", (note_id,)).fetchone()
        if not row:
            return {"items": [], "edges": [], "paths": []}
        try:
            data = json.loads(str(row["data_json"]))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        return {"items": [], "edges": [], "paths": []}

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        row = self.connection.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return str(row["value"]) if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self.connection:
            self.connection.execute(
                "INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

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

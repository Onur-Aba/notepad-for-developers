# DevNest 1.2.4 — Full Source

This file contains the complete text-source snapshot for DevNest 1.2.4. Binary icon files are included in the ZIP but intentionally not embedded here.

## `.gitignore`

````gitignore
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
build/
dist/
*.log
````

## `app/__init__.py`

````python
from app.constants import VERSION

__all__ = ["VERSION"]
````

## `app/constants.py`

````python
from __future__ import annotations

APP_NAME = "DevNest"
ORGANIZATION_NAME = "DevNest"
ORGANIZATION_DOMAIN = "devnest.local"
VERSION = "1.2.4"
DEFAULT_NOTE_TITLE = "Untitled Note"
DEFAULT_AUTOSAVE_DELAY_MS = 750
MIN_AUTOSAVE_DELAY_MS = 300
MAX_AUTOSAVE_DELAY_MS = 5000
TAB_SPACES = 4

SHORTCUTS: dict[str, str] = {
    "New Note": "Ctrl+N",
    "Find in Note": "Ctrl+F",
    "Undo": "Ctrl+Z",
    "Redo": "Ctrl+Y",
    "Bold": "Ctrl+B",
    "Italic": "Ctrl+I",
    "Underline": "Ctrl+U",
    "Checkbox": "Ctrl+Shift+X",
    "Export TXT": "Ctrl+E",
    "Toggle Sidebar": "Ctrl+Shift+B",
    "Editor Tab": "Ctrl+1",
    "Diagram Tab": "Ctrl+2",
    "Duplicate Selected Diagram Item": "Ctrl+D",
    "Delete Selected Diagram Item": "Delete",
}
````

## `app/database.py`

````python
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
````

## `app/dialogs/__init__.py`

````python

````

## `app/dialogs/preferences.py`

````python
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QVBoxLayout,
)

from app.constants import MAX_AUTOSAVE_DELAY_MS, MIN_AUTOSAVE_DELAY_MS
from app.settings import AppPreferences
from app.themes.theme_manager import THEME_OPTIONS


class PreferencesDialog(QDialog):
    def __init__(self, prefs: AppPreferences, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setMinimumWidth(420)
        root = QVBoxLayout(self)

        general = QGroupBox("General")
        general_form = QFormLayout(general)
        self.autosave = QCheckBox("Enable autosave")
        self.autosave.setChecked(prefs.autosave_enabled)
        self.autosave_delay = QSpinBox()
        self.autosave_delay.setRange(MIN_AUTOSAVE_DELAY_MS, MAX_AUTOSAVE_DELAY_MS)
        self.autosave_delay.setSingleStep(100)
        self.autosave_delay.setSuffix(" ms")
        self.autosave_delay.setValue(prefs.autosave_delay_ms)
        self.start_last = QCheckBox("Start with last opened note")
        self.start_last.setChecked(prefs.start_with_last_note)
        general_form.addRow(self.autosave)
        general_form.addRow("Autosave delay:", self.autosave_delay)
        general_form.addRow(self.start_last)

        editor = QGroupBox("Editor")
        editor_form = QFormLayout(editor)
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 36)
        self.font_size.setValue(prefs.editor_font_size)
        self.tab_width = QSpinBox()
        self.tab_width.setRange(2, 8)
        self.tab_width.setValue(prefs.tab_width)
        self.auto_checkbox = QCheckBox("Auto Checkbox by default")
        self.auto_checkbox.setChecked(prefs.auto_checkbox_default)
        self.blank_line_after_enter = QCheckBox("Leave one blank line after Enter")
        self.blank_line_after_enter.setChecked(prefs.blank_line_after_enter)
        self.blank_line_after_enter.setToolTip("Pressing Enter advances by two lines, leaving one empty line in between.")
        self.word_wrap = QCheckBox("Word wrap")
        self.word_wrap.setChecked(prefs.word_wrap)
        editor_form.addRow("Font size:", self.font_size)
        editor_form.addRow("Tab width (spaces):", self.tab_width)
        editor_form.addRow(self.auto_checkbox)
        editor_form.addRow(self.blank_line_after_enter)
        editor_form.addRow(self.word_wrap)

        appearance = QGroupBox("Appearance")
        appearance_form = QFormLayout(appearance)
        self.theme = QComboBox()
        for label, value in THEME_OPTIONS:
            self.theme.addItem(label, value)
        index = self.theme.findData(prefs.theme)
        self.theme.setCurrentIndex(max(0, index))
        appearance_form.addRow("Theme:", self.theme)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root.addWidget(general)
        root.addWidget(editor)
        root.addWidget(appearance)
        root.addWidget(buttons)

    def preferences(self) -> AppPreferences:
        return AppPreferences(
            theme=str(self.theme.currentData()),
            autosave_enabled=self.autosave.isChecked(),
            autosave_delay_ms=self.autosave_delay.value(),
            start_with_last_note=self.start_last.isChecked(),
            editor_font_size=self.font_size.value(),
            tab_width=self.tab_width.value(),
            auto_checkbox_default=self.auto_checkbox.isChecked(),
            blank_line_after_enter=self.blank_line_after_enter.isChecked(),
            word_wrap=self.word_wrap.isChecked(),
        )
````

## `app/dialogs/shortcuts.py`

````python
from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QTableWidget, QTableWidgetItem, QVBoxLayout

from app.constants import SHORTCUTS


class ShortcutsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.resize(480, 430)
        root = QVBoxLayout(self)
        table = QTableWidget(len(SHORTCUTS), 2)
        table.setHorizontalHeaderLabels(["Action", "Shortcut"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, (name, shortcut) in enumerate(SHORTCUTS.items()):
            table.setItem(row, 0, QTableWidgetItem(name))
            table.setItem(row, 1, QTableWidgetItem(shortcut))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.clicked.connect(lambda _button: self.accept())
        root.addWidget(table)
        root.addWidget(buttons)
````

## `app/dialogs/trash.py`

````python
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.database import Database, DatabaseError


class TrashDialog(QDialog):
    def __init__(self, database: Database, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.changed = False
        self.setWindowTitle("Trash")
        self.resize(720, 420)
        root = QVBoxLayout(self)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Title", "Deleted / updated", "Preview"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        row = QHBoxLayout()
        restore = QPushButton("Restore")
        permanent = QPushButton("Permanently Delete")
        empty = QPushButton("Empty Trash")
        optimize = QPushButton("Optimize Database")
        close = QPushButton("Close")
        restore.clicked.connect(self.restore_selected)
        permanent.clicked.connect(self.permanently_delete_selected)
        empty.clicked.connect(self.empty_trash)
        optimize.clicked.connect(self.optimize_database)
        close.clicked.connect(self.accept)
        row.addWidget(restore)
        row.addWidget(permanent)
        row.addStretch(1)
        row.addWidget(empty)
        row.addWidget(optimize)
        row.addWidget(close)

        root.addWidget(self.table, 1)
        root.addLayout(row)
        self.refresh()

    def refresh(self) -> None:
        notes = self.database.list_trash()
        self.table.setRowCount(len(notes))
        for r, note in enumerate(notes):
            title = QTableWidgetItem(note.title)
            title.setData(Qt.ItemDataRole.UserRole, note.id)
            try:
                stamp = datetime.fromisoformat(note.updated_at).astimezone().strftime("%Y-%m-%d %H:%M")
            except ValueError:
                stamp = note.updated_at
            self.table.setItem(r, 0, title)
            self.table.setItem(r, 1, QTableWidgetItem(stamp))
            self.table.setItem(r, 2, QTableWidgetItem(note.preview))
        self.table.resizeColumnsToContents()

    def _selected_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return int(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def restore_selected(self) -> None:
        note_id = self._selected_id()
        if note_id is None:
            QMessageBox.information(self, "Trash", "Select a note first.")
            return
        try:
            self.database.restore_note(note_id)
            self.changed = True
            self.refresh()
        except DatabaseError as exc:
            QMessageBox.critical(self, "Restore Failed", str(exc))

    def permanently_delete_selected(self) -> None:
        note_id = self._selected_id()
        if note_id is None:
            QMessageBox.information(self, "Trash", "Select a note first.")
            return
        answer = QMessageBox.warning(
            self,
            "Permanently Delete",
            "This permanently deletes the note and its diagram data. This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.database.permanently_delete_note(note_id)
            self.changed = True
            self.refresh()
        except DatabaseError as exc:
            QMessageBox.critical(self, "Delete Failed", str(exc))

    def empty_trash(self) -> None:
        if not self.database.list_trash():
            QMessageBox.information(self, "Trash", "Trash is already empty.")
            return
        answer = QMessageBox.warning(
            self,
            "Empty Trash",
            "Permanently delete every note in Trash and its linked diagram data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            count = self.database.empty_trash()
            self.changed = True
            self.refresh()
            QMessageBox.information(self, "Trash", f"Permanently deleted {count} note(s).")
        except DatabaseError as exc:
            QMessageBox.critical(self, "Empty Trash Failed", str(exc))

    def optimize_database(self) -> None:
        answer = QMessageBox.question(
            self,
            "Optimize Database",
            "Run SQLite VACUUM now? This can reduce the database file size after permanent deletions.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.database.optimize()
            QMessageBox.information(self, "Optimize Database", "Database optimization completed.")
        except DatabaseError as exc:
            QMessageBox.critical(self, "Optimize Failed", str(exc))
````

## `app/main_window.py`

````python
from __future__ import annotations

import logging
import re
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QActionGroup, QCloseEvent, QDragEnterEvent, QDropEvent, QFontDatabase, QKeySequence, QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.constants import APP_NAME, DEFAULT_NOTE_TITLE, SHORTCUTS, VERSION
from app.database import Database, DatabaseError
from app.dialogs.preferences import PreferencesDialog
from app.dialogs.shortcuts import ShortcutsDialog
from app.dialogs.trash import TrashDialog
from app.models import Note
from app.paths import database_path
from app.services.txt_codec import (
    export_internal_plain_text,
    import_text_to_html,
    parse_text,
    parsed_to_internal_text,
    read_utf8_text,
    write_utf8_text,
)
from app.settings import AppPreferences, SettingsManager
from app.themes.theme_manager import THEME_OPTIONS, ThemeManager
from app.widgets.diagram_view import DiagramView
from app.widgets.note_editor import NoteEditor
from app.widgets.sidebar import Sidebar

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(
        self,
        database: Database,
        settings: SettingsManager,
        theme_manager: ThemeManager,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.database = database
        self.settings = settings
        self.theme_manager = theme_manager
        self.preferences = self.settings.preferences()
        self.current_note_id: int | None = None
        self._loading_note = False
        self._dirty = False
        self._diagram_dirty = False
        self._search_term = ""
        self._sort_mode = "updated"

        self.setWindowTitle(f"{APP_NAME} — Developer Notes & Planning")
        self.setMinimumSize(840, 560)
        self.resize(1220, 760)
        self.setAcceptDrops(True)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.timeout.connect(self.save_current_note)
        self.diagram_timer = QTimer(self)
        self.diagram_timer.setSingleShot(True)
        self.diagram_timer.timeout.connect(self.save_current_diagram)

        self._build_ui()
        self._create_actions()
        self._build_toolbar()
        self._build_menus()
        self._connect_signals()
        self._restore_window_state()
        self._apply_preferences(self.preferences, persist=False)
        self._load_initial_note()

    def _build_ui(self) -> None:
        self.sidebar = Sidebar()
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText(DEFAULT_NOTE_TITLE)
        self.title_edit.setStyleSheet("font-size: 18px; font-weight: 650; padding: 8px;")

        self.editor = NoteEditor()
        self.editor.setAcceptDrops(False)
        self.diagram = DiagramView()
        self.tabs = QTabWidget()
        self.tabs.addTab(self.editor, "Editor")
        self.tabs.addTab(self.diagram, "Diagram")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 6)
        content_layout.setSpacing(6)
        content_layout.addWidget(self.title_edit)
        content_layout.addWidget(self.tabs, 1)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(content)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([280, 940])

        self.workspace_bar = QWidget()
        self.workspace_bar.setObjectName("workspaceBar")
        self.workspace_layout = QHBoxLayout(self.workspace_bar)
        self.workspace_layout.setContentsMargins(8, 5, 8, 5)
        self.workspace_layout.setSpacing(6)

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self.workspace_bar)
        central_layout.addWidget(self.splitter, 1)
        self.setCentralWidget(central)

        self.save_label = QLabel("Saved")
        self.stats_label = QLabel("Words: 0  •  Lines: 1  •  Ln 1, Col 1")
        self.statusBar().addWidget(self.save_label)
        self.statusBar().addPermanentWidget(self.stats_label)

    def _create_actions(self) -> None:
        self.new_action = QAction("New Note", self)
        self.new_action.setShortcut(SHORTCUTS["New Note"])
        self.new_action.setToolTip("Create a new note")
        self.new_action.triggered.connect(self.new_note)

        self.delete_action = QAction("Delete", self)
        self.delete_action.setToolTip("Move the current note to Trash")
        self.delete_action.triggered.connect(lambda: self.delete_note(self.current_note_id) if self.current_note_id else None)

        self.import_action = QAction("Import TXT", self)
        self.import_action.triggered.connect(self.import_txt)

        self.export_action = QAction("Export TXT", self)
        self.export_action.setShortcut(SHORTCUTS["Export TXT"])
        self.export_action.triggered.connect(lambda: self.export_note(self.current_note_id) if self.current_note_id else None)

        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.close)

        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.triggered.connect(self.editor.undo)
        self.redo_action = QAction("Redo", self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.triggered.connect(self.editor.redo)
        self.cut_action = QAction("Cut", self)
        self.cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        self.cut_action.triggered.connect(self.editor.cut)
        self.copy_action = QAction("Copy", self)
        self.copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        self.copy_action.triggered.connect(self.editor.copy)
        self.paste_action = QAction("Paste", self)
        self.paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        self.paste_action.triggered.connect(self.editor.paste)
        self.select_all_action = QAction("Select All", self)
        self.select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        self.select_all_action.triggered.connect(self.editor.selectAll)
        self.find_action = QAction("Find", self)
        self.find_action.setShortcut(SHORTCUTS["Find in Note"])
        self.find_action.triggered.connect(self.find_in_note)

        self.checkbox_action = QAction("Checkbox", self)
        self.checkbox_action.setShortcut(SHORTCUTS["Checkbox"])
        self.checkbox_action.triggered.connect(self.editor.insert_checkbox)
        self.auto_checkbox_action = QAction("Auto Checkbox", self)
        self.auto_checkbox_action.setCheckable(True)
        self.auto_checkbox_action.toggled.connect(self._set_auto_checkbox)
        self.blank_line_enter_action = QAction("Blank Line After Enter", self)
        self.blank_line_enter_action.setCheckable(True)
        self.blank_line_enter_action.setToolTip("Leave one empty line whenever Enter is pressed")
        self.blank_line_enter_action.toggled.connect(self._set_blank_line_after_enter)

        self.bold_action = QAction("Bold", self)
        self.bold_action.setShortcut(QKeySequence.StandardKey.Bold)
        self.bold_action.triggered.connect(self.editor.toggle_bold)
        self.italic_action = QAction("Italic", self)
        self.italic_action.setShortcut(QKeySequence.StandardKey.Italic)
        self.italic_action.triggered.connect(self.editor.toggle_italic)
        self.underline_action = QAction("Underline", self)
        self.underline_action.setShortcut(QKeySequence.StandardKey.Underline)
        self.underline_action.triggered.connect(self.editor.toggle_underline)
        self.strike_action = QAction("Strikethrough", self)
        self.strike_action.triggered.connect(self.editor.toggle_strikethrough)
        self.bullet_action = QAction("Bullet List", self)
        self.bullet_action.triggered.connect(self.editor.make_bullet_list)
        self.numbered_action = QAction("Numbered List", self)
        self.numbered_action.triggered.connect(self.editor.make_numbered_list)

        self.toggle_sidebar_action = QAction("Toggle Sidebar", self)
        self.toggle_sidebar_action.setShortcut(SHORTCUTS["Toggle Sidebar"])
        self.toggle_sidebar_action.triggered.connect(self._toggle_sidebar)
        self.editor_tab_action = QAction("Editor", self)
        self.editor_tab_action.setShortcut(SHORTCUTS["Editor Tab"])
        self.editor_tab_action.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        self.diagram_tab_action = QAction("Diagram", self)
        self.diagram_tab_action.setShortcut(SHORTCUTS["Diagram Tab"])
        self.diagram_tab_action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))

        self.preferences_action = QAction("Preferences…", self)
        self.preferences_action.triggered.connect(self.open_preferences)
        self.trash_action = QAction("Trash…", self)
        self.trash_action.triggered.connect(self.open_trash)
        self.shortcuts_action = QAction("Keyboard Shortcuts", self)
        self.shortcuts_action.triggered.connect(lambda: ShortcutsDialog(self).exec())
        self.about_action = QAction("About DevNest", self)
        self.about_action.triggered.connect(self.show_about)

    def _build_toolbar(self) -> None:
        # Two compact rows avoid Qt's overflow "..." extension button even on
        # smaller windows. Workspace navigation is a permanent bar below them.
        notes_toolbar = QToolBar("Notes & Format", self)
        notes_toolbar.setMovable(False)
        notes_toolbar.setFloatable(False)
        notes_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.addToolBar(notes_toolbar)
        for action in [self.new_action, self.delete_action, self.import_action, self.export_action]:
            notes_toolbar.addAction(action)
        notes_toolbar.addSeparator()
        notes_toolbar.addAction(self.checkbox_action)
        notes_toolbar.addAction(self.auto_checkbox_action)
        notes_toolbar.addSeparator()
        for action in [self.bold_action, self.italic_action, self.strike_action, self.bullet_action]:
            notes_toolbar.addAction(action)

        self.addToolBarBreak()
        text_toolbar = QToolBar("Text", self)
        text_toolbar.setMovable(False)
        text_toolbar.setFloatable(False)
        text_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.addToolBar(text_toolbar)

        self.font_combo = QComboBox()
        self.font_combo.setMinimumWidth(138)
        self.font_combo.setMaximumWidth(190)
        self.font_combo.setToolTip("Font family for selected text or new text")
        self._populate_font_combo()
        self.font_combo.currentIndexChanged.connect(self._apply_font_family_from_toolbar)
        text_toolbar.addWidget(self.font_combo)

        self.font_size_label = QLabel("12 pt")
        self.font_size_label.setMinimumWidth(36)
        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setRange(8, 36)
        self.font_size_slider.setSingleStep(1)
        self.font_size_slider.setPageStep(2)
        self.font_size_slider.setValue(12)
        self.font_size_slider.setFixedWidth(92)
        self.font_size_slider.setToolTip("Text size: 8–36 pt")
        self.font_size_slider.valueChanged.connect(self._apply_font_size_from_toolbar)
        text_toolbar.addWidget(self.font_size_label)
        text_toolbar.addWidget(self.font_size_slider)

        self.font_weight_label = QLabel("W 400")
        self.font_weight_label.setMinimumWidth(42)
        self.font_weight_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_weight_slider.setRange(100, 900)
        self.font_weight_slider.setSingleStep(100)
        self.font_weight_slider.setPageStep(100)
        self.font_weight_slider.setValue(400)
        self.font_weight_slider.setFixedWidth(92)
        self.font_weight_slider.setToolTip("Font weight: 100 thin – 900 black")
        self.font_weight_slider.valueChanged.connect(self._apply_font_weight_from_toolbar)
        text_toolbar.addWidget(self.font_weight_label)
        text_toolbar.addWidget(self.font_weight_slider)
        text_toolbar.addSeparator()
        text_toolbar.addAction(self.undo_action)
        text_toolbar.addAction(self.redo_action)

        # Always-visible workspace controls. They are not QToolBar overflow items,
        # so Qt never moves Editor / Diagram / Theme behind a three-dot button.
        self.editor_workspace_button = QPushButton("Editor")
        self.editor_workspace_button.setObjectName("workspaceButton")
        self.editor_workspace_button.setCheckable(True)
        self.editor_workspace_button.clicked.connect(lambda: self.tabs.setCurrentIndex(0))
        self.diagram_workspace_button = QPushButton("Diagram")
        self.diagram_workspace_button.setObjectName("workspaceButton")
        self.diagram_workspace_button.setCheckable(True)
        self.diagram_workspace_button.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        self.workspace_layout.addWidget(self.editor_workspace_button)
        self.workspace_layout.addWidget(self.diagram_workspace_button)
        self.workspace_layout.addStretch(1)
        theme_label = QLabel("Theme:")
        self.workspace_layout.addWidget(theme_label)
        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("themePresetCombo")
        self.theme_combo.setToolTip("Choose a DevNest color theme")
        for label, value in THEME_OPTIONS:
            self.theme_combo.addItem(label, value)
        self.theme_combo.currentIndexChanged.connect(self._theme_combo_changed)
        self.workspace_layout.addWidget(self.theme_combo)
        self._sync_workspace_buttons(self.tabs.currentIndex())

        # Defensive: if the platform style creates an extension button anyway,
        # keep it hidden. Both toolbars are deliberately short enough to fit.
        for toolbar in (notes_toolbar, text_toolbar):
            extension = toolbar.findChild(QToolButton, "qt_toolbar_ext_button")
            if extension is not None:
                extension.hide()

    def _populate_font_combo(self) -> None:
        available = {family.casefold(): family for family in QFontDatabase.families()}
        system_mono = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont).family()
        system_ui = QApplication.font().family()
        choices = [
            ("System Mono", system_mono),
            ("System UI", system_ui),
            ("Cascadia Code", "Cascadia Code"),
            ("Cascadia Mono", "Cascadia Mono"),
            ("Consolas", "Consolas"),
            ("JetBrains Mono", "JetBrains Mono"),
            ("Fira Code", "Fira Code"),
            ("Courier New", "Courier New"),
            ("Segoe UI", "Segoe UI"),
            ("Arial", "Arial"),
        ]
        used: set[str] = set()
        for label, requested in choices:
            family = available.get(requested.casefold())
            if family is None and requested in {system_mono, system_ui}:
                family = requested
            if not family or family.casefold() in used:
                continue
            used.add(family.casefold())
            self.font_combo.addItem(label, family)
        if self.font_combo.count() == 0:
            self.font_combo.addItem(system_mono, system_mono)

    def _apply_font_family_from_toolbar(self, _index: int) -> None:
        family = self.font_combo.currentData()
        if family:
            self.editor.apply_font_family(str(family))
            self.editor.setFocus()

    def _apply_font_size_from_toolbar(self, value: int) -> None:
        self.font_size_label.setText(f"{value} pt")
        self.editor.apply_font_point_size(value)
        self.editor.setFocus()

    def _apply_font_weight_from_toolbar(self, value: int) -> None:
        snapped = max(100, min(900, int(round(value / 100.0) * 100)))
        if snapped != value:
            self.font_weight_slider.blockSignals(True)
            self.font_weight_slider.setValue(snapped)
            self.font_weight_slider.blockSignals(False)
        self.font_weight_label.setText(f"W {snapped}")
        self.editor.apply_font_weight(snapped)
        self.editor.setFocus()

    def _sync_font_controls(self, fmt) -> None:
        size = int(round(fmt.fontPointSize())) if fmt.fontPointSize() > 0 else self.editor.base_font_size
        size = max(self.font_size_slider.minimum(), min(self.font_size_slider.maximum(), size))
        self.font_size_slider.blockSignals(True)
        self.font_size_slider.setValue(size)
        self.font_size_slider.blockSignals(False)
        self.font_size_label.setText(f"{size} pt")

        weight = int(fmt.fontWeight())
        weight = max(100, min(900, int(round(weight / 100.0) * 100)))
        self.font_weight_slider.blockSignals(True)
        self.font_weight_slider.setValue(weight)
        self.font_weight_slider.blockSignals(False)
        self.font_weight_label.setText(f"W {weight}")

        families = fmt.font().families()
        family = families[0] if families else fmt.font().family()
        index = self.font_combo.findData(family)
        if index >= 0:
            self.font_combo.blockSignals(True)
            self.font_combo.setCurrentIndex(index)
            self.font_combo.blockSignals(False)

    def _build_menus(self) -> None:
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.import_action)
        file_menu.addAction(self.export_action)
        file_menu.addSeparator()
        file_menu.addAction(self.trash_action)
        file_menu.addAction(self.preferences_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        edit_menu = menu.addMenu("Edit")
        for action in [self.undo_action, self.redo_action]:
            edit_menu.addAction(action)
        edit_menu.addSeparator()
        for action in [self.cut_action, self.copy_action, self.paste_action, self.select_all_action]:
            edit_menu.addAction(action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.find_action)

        view_menu = menu.addMenu("View")
        view_menu.addAction(self.toggle_sidebar_action)
        view_menu.addSeparator()
        view_menu.addAction(self.editor_tab_action)
        view_menu.addAction(self.diagram_tab_action)
        theme_menu = view_menu.addMenu("Theme")
        self.theme_group = QActionGroup(self)
        self.theme_group.setExclusive(True)
        self.theme_actions: dict[str, QAction] = {}
        for label, value in THEME_OPTIONS:
            action = QAction(label, self, checkable=True)
            action.setData(value)
            action.triggered.connect(lambda _checked=False, t=value: self.set_theme(t))
            self.theme_group.addAction(action)
            theme_menu.addAction(action)
            self.theme_actions[value] = action

        format_menu = menu.addMenu("Format")
        for action in [
            self.checkbox_action,
            self.auto_checkbox_action,
            self.blank_line_enter_action,
            self.bold_action,
            self.italic_action,
            self.underline_action,
            self.strike_action,
            self.bullet_action,
            self.numbered_action,
        ]:
            format_menu.addAction(action)
        help_menu = menu.addMenu("Help")
        help_menu.addAction(self.shortcuts_action)
        help_menu.addAction(self.about_action)

    def _connect_signals(self) -> None:
        self.sidebar.noteSelected.connect(self.open_note)
        self.sidebar.newNoteRequested.connect(self.new_note)
        self.sidebar.trashRequested.connect(self.open_trash)
        self.sidebar.renameRequested.connect(self.rename_note)
        self.sidebar.duplicateRequested.connect(self.duplicate_note)
        self.sidebar.deleteRequested.connect(self.delete_note)
        self.sidebar.exportRequested.connect(self.export_note)
        self.sidebar.searchChanged.connect(self._on_search_changed)
        self.sidebar.sortChanged.connect(self._on_sort_changed)

        self.title_edit.textChanged.connect(self._mark_content_dirty)
        self.editor.textChanged.connect(self._on_editor_changed)
        self.editor.cursorPositionChanged.connect(self._update_stats)
        self.editor.currentCharFormatChanged.connect(self._sync_font_controls)
        self.editor.taskStateChanged.connect(self._mark_content_dirty)
        self.diagram.diagramChanged.connect(self._on_diagram_changed)
        self.tabs.currentChanged.connect(self._sync_workspace_buttons)
        color_scheme_changed = getattr(QApplication.styleHints(), "colorSchemeChanged", None)
        if color_scheme_changed is not None:
            color_scheme_changed.connect(self._on_system_color_scheme_changed)

    def _load_initial_note(self) -> None:
        notes = self.database.list_notes(sort=self._sort_mode)
        if not notes:
            note = self.database.create_note()
            notes = self.database.list_notes(sort=self._sort_mode)
            target = note.id
        else:
            last_id = self.settings.last_note_id() if self.preferences.start_with_last_note else None
            ids = {note.id for note in notes}
            target = last_id if last_id in ids else notes[0].id
        self.sidebar.set_notes(notes, target)
        self.open_note(target)

    def refresh_sidebar(self, selected_id: int | None = None) -> None:
        notes = self.database.list_notes(self._search_term, self._sort_mode)
        self.sidebar.set_notes(notes, selected_id if selected_id is not None else self.current_note_id)

    def open_note(self, note_id: int) -> None:
        if note_id == self.current_note_id and not self._loading_note:
            return
        self.flush_pending_saves()
        note = self.database.get_note(note_id)
        if note is None:
            self.refresh_sidebar()
            return
        self._loading_note = True
        try:
            self.current_note_id = note.id
            self.title_edit.setText(note.title)
            self.editor.setHtml(note.content_html) if note.content_html else self.editor.clear()
            self.diagram.load_data(self.database.get_diagram(note.id))
            self.settings.set_last_note_id(note.id)
            self._dirty = False
            self._diagram_dirty = False
            self.save_label.setText("Saved")
            self._update_stats()
        finally:
            self._loading_note = False

    def new_note(self) -> None:
        self.flush_pending_saves()
        try:
            note = self.database.create_note()
            self._search_term = ""
            self.sidebar.search.clear()
            self.refresh_sidebar(note.id)
            self.open_note(note.id)
            self.title_edit.setFocus()
            self.title_edit.selectAll()
        except DatabaseError as exc:
            self._show_database_error(exc)

    def rename_note(self, note_id: int) -> None:
        note = self.database.get_note(note_id)
        if note is None:
            return
        title, ok = QInputDialog.getText(self, "Rename Note", "Title:", text=note.title)
        if not ok:
            return
        try:
            if note_id == self.current_note_id:
                self.title_edit.setText(title.strip() or DEFAULT_NOTE_TITLE)
                self.save_current_note()
            else:
                self.database.rename_note(note_id, title)
            self.refresh_sidebar(note_id)
        except DatabaseError as exc:
            self._show_database_error(exc)

    def duplicate_note(self, note_id: int) -> None:
        self.flush_pending_saves()
        try:
            duplicate = self.database.duplicate_note(note_id)
            self.refresh_sidebar(duplicate.id)
            self.open_note(duplicate.id)
        except DatabaseError as exc:
            self._show_database_error(exc)

    def delete_note(self, note_id: int | None) -> None:
        if note_id is None:
            return
        note = self.database.get_note(note_id)
        if note is None:
            return
        answer = QMessageBox.question(
            self,
            "Move to Trash",
            f'Move "{note.title}" to Trash? You can restore it later.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        if note_id == self.current_note_id:
            self.flush_pending_saves()
        try:
            self.database.soft_delete_note(note_id)
            if note_id == self.current_note_id:
                self.current_note_id = None
            notes = self.database.list_notes(self._search_term, self._sort_mode)
            if not notes:
                created = self.database.create_note()
                notes = self.database.list_notes(self._search_term, self._sort_mode)
                target = created.id
            else:
                target = notes[0].id
            self.sidebar.set_notes(notes, target)
            self.open_note(target)
        except DatabaseError as exc:
            self._show_database_error(exc)

    def open_trash(self) -> None:
        self.flush_pending_saves()
        dialog = TrashDialog(self.database, self)
        dialog.exec()
        if dialog.changed:
            self.refresh_sidebar(self.current_note_id)

    def save_current_note(self) -> None:
        self.autosave_timer.stop()
        if self._loading_note or not self._dirty or self.current_note_id is None:
            return
        try:
            title = self.title_edit.text().strip() or DEFAULT_NOTE_TITLE
            if self.title_edit.text() != title:
                self.title_edit.blockSignals(True)
                self.title_edit.setText(title)
                self.title_edit.blockSignals(False)
            self.database.update_note(
                self.current_note_id,
                title,
                self.editor.document().toHtml(),
                self.editor.toPlainText(),
            )
            self._dirty = False
            self.save_label.setText("Saved")
            self.refresh_sidebar(self.current_note_id)
        except DatabaseError as exc:
            self.save_label.setText("Save failed")
            logger.exception("Autosave failed")
            QMessageBox.critical(self, "Save Failed", str(exc))

    def save_current_diagram(self) -> None:
        self.diagram_timer.stop()
        if self._loading_note or not self._diagram_dirty or self.current_note_id is None:
            return
        try:
            self.database.save_diagram(self.current_note_id, self.diagram.to_data())
            self._diagram_dirty = False
        except DatabaseError as exc:
            logger.exception("Diagram save failed")
            QMessageBox.critical(self, "Diagram Save Failed", str(exc))

    def flush_pending_saves(self) -> None:
        self.save_current_note()
        self.save_current_diagram()
        self.settings.sync()

    def _mark_content_dirty(self) -> None:
        if self._loading_note:
            return
        self._dirty = True
        self.save_label.setText("Saving…" if self.preferences.autosave_enabled else "Modified")
        if self.preferences.autosave_enabled:
            self.autosave_timer.start(self.preferences.autosave_delay_ms)

    def _on_editor_changed(self) -> None:
        self._mark_content_dirty()
        self._update_stats()

    def _on_diagram_changed(self) -> None:
        if self._loading_note:
            return
        self._diagram_dirty = True
        self.diagram_timer.start(max(500, self.preferences.autosave_delay_ms))

    def _on_search_changed(self, text: str) -> None:
        self._search_term = text
        self.refresh_sidebar(self.current_note_id)

    def _on_sort_changed(self, mode: str) -> None:
        self._sort_mode = mode
        self.refresh_sidebar(self.current_note_id)

    def _update_stats(self) -> None:
        text = self.editor.toPlainText()
        words = len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))
        lines = max(1, self.editor.document().blockCount())
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.positionInBlock() + 1
        self.stats_label.setText(f"Words: {words}  •  Lines: {lines}  •  Ln {line}, Col {col}")

    def find_in_note(self) -> None:
        term, ok = QInputDialog.getText(self, "Find", "Find text:")
        if not ok or not term:
            return
        if self.editor.find(term):
            return
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.editor.setTextCursor(cursor)
        if not self.editor.find(term):
            QMessageBox.information(self, "Find", f'"{term}" was not found.')

    def import_txt(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Import TXT", "", "Text Files (*.txt);;All Files (*)")
        if filename:
            self._import_path(Path(filename))

    def _import_path(self, path: Path) -> None:
        if path.suffix.lower() != ".txt":
            QMessageBox.warning(self, "Import", "DevNest imports .txt files only.")
            return
        try:
            text = read_utf8_text(path)
            parsed = parse_text(text)
            html = import_text_to_html(text)
            plain = parsed_to_internal_text(parsed)
            note = self.database.create_note(path.stem or DEFAULT_NOTE_TITLE, html, plain)
            self._search_term = ""
            self.sidebar.search.clear()
            self.refresh_sidebar(note.id)
            self.open_note(note.id)
        except (OSError, UnicodeError, DatabaseError) as exc:
            logger.exception("TXT import failed for %s", path)
            QMessageBox.critical(self, "Import Failed", f"Could not import the file.\n\n{exc}")

    def export_note(self, note_id: int | None) -> None:
        if note_id is None:
            return
        if note_id == self.current_note_id:
            self.flush_pending_saves()
        note = self.database.get_note(note_id)
        if note is None:
            return
        default_name = self._safe_filename(note.title) + ".txt"
        filename, _ = QFileDialog.getSaveFileName(self, "Export Note as TXT", default_name, "Text Files (*.txt)")
        if not filename:
            return
        path = Path(filename)
        if path.suffix.lower() != ".txt":
            path = path.with_suffix(".txt")
        if path.exists():
            answer = QMessageBox.question(
                self,
                "Overwrite File",
                f'"{path.name}" already exists. Overwrite it?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        try:
            if note_id == self.current_note_id:
                plain = self.editor.toPlainText()
            else:
                doc = QTextDocument()
                doc.setHtml(note.content_html)
                plain = doc.toPlainText()
            write_utf8_text(path, export_internal_plain_text(plain))
            self.statusBar().showMessage(f"Exported {path.name}", 3000)
        except OSError as exc:
            logger.exception("TXT export failed for %s", path)
            QMessageBox.critical(self, "Export Failed", f"Could not write the file.\n\n{exc}")

    @staticmethod
    def _safe_filename(title: str) -> str:
        cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title).strip(" .")
        return cleaned[:100] or "Untitled Note"

    def open_preferences(self) -> None:
        dialog = PreferencesDialog(self.preferences, self)
        if dialog.exec():
            self.preferences = dialog.preferences()
            self.settings.save_preferences(self.preferences)
            self._apply_preferences(self.preferences, persist=False)

    def _apply_preferences(self, prefs: AppPreferences, persist: bool = False) -> None:
        self.editor.set_editor_font_size(prefs.editor_font_size)
        if hasattr(self, "font_size_slider"):
            self.font_size_slider.blockSignals(True)
            self.font_size_slider.setValue(prefs.editor_font_size)
            self.font_size_slider.blockSignals(False)
            self.font_size_label.setText(f"{prefs.editor_font_size} pt")
        self.editor.set_tab_width(prefs.tab_width)
        self.editor.setLineWrapMode(
            QTextEdit.LineWrapMode.WidgetWidth if prefs.word_wrap else QTextEdit.LineWrapMode.NoWrap
        )
        auto_enabled = prefs.auto_checkbox_default
        self.auto_checkbox_action.blockSignals(True)
        self.auto_checkbox_action.setChecked(auto_enabled)
        self.auto_checkbox_action.blockSignals(False)
        self.editor.set_auto_checkbox(auto_enabled)
        self.blank_line_enter_action.blockSignals(True)
        self.blank_line_enter_action.setChecked(prefs.blank_line_after_enter)
        self.blank_line_enter_action.blockSignals(False)
        self.editor.set_blank_line_after_enter(prefs.blank_line_after_enter)
        self.set_theme(prefs.theme, persist=persist)

    def _set_auto_checkbox(self, enabled: bool) -> None:
        self.editor.set_auto_checkbox(enabled)
        self.preferences.auto_checkbox_default = enabled
        self.settings.set_value("editor/auto_checkbox_default", enabled)

    def _set_blank_line_after_enter(self, enabled: bool) -> None:
        self.editor.set_blank_line_after_enter(enabled)
        self.preferences.blank_line_after_enter = enabled
        self.settings.set_value("editor/blank_line_after_enter", enabled)

    def set_theme(self, theme: str, persist: bool = True) -> None:
        self.theme_manager.apply(theme)
        resolved_theme = self.theme_manager.current_theme
        self.diagram.set_theme(self.theme_manager.current_spec.diagram_palette())
        self.preferences.theme = resolved_theme
        for name, action in getattr(self, "theme_actions", {}).items():
            action.setChecked(name == resolved_theme)
        if hasattr(self, "theme_combo"):
            index = self.theme_combo.findData(resolved_theme)
            if index >= 0 and index != self.theme_combo.currentIndex():
                self.theme_combo.blockSignals(True)
                self.theme_combo.setCurrentIndex(index)
                self.theme_combo.blockSignals(False)
        if persist:
            self.settings.set_value("appearance/theme", resolved_theme)
            self.settings.sync()

    def _theme_combo_changed(self, _index: int) -> None:
        theme = self.theme_combo.currentData()
        if theme:
            self.set_theme(str(theme))

    def _sync_workspace_buttons(self, index: int) -> None:
        if hasattr(self, "editor_workspace_button"):
            self.editor_workspace_button.setChecked(index == 0)
            self.diagram_workspace_button.setChecked(index == 1)

    def _on_system_color_scheme_changed(self, _scheme) -> None:
        if self.preferences.theme == "system":
            self.set_theme("system", persist=False)

    def _toggle_sidebar(self) -> None:
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<b>{APP_NAME} {VERSION}</b><br><br>"
            "Offline developer notes, tasks, planning, and lightweight diagrams.<br><br>"
            "No account, telemetry, or cloud connection is required.<br><br>"
            f"Database: {database_path()}",
        )

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        if any(Path(url.toLocalFile()).suffix.lower() == ".txt" for url in urls):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        accepted = False
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() == ".txt":
                self._import_path(path)
                accepted = True
        if accepted:
            event.acceptProposedAction()
        else:
            event.ignore()

    def _restore_window_state(self) -> None:
        geometry = self.settings.value("window/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        splitter_state = self.settings.value("window/splitter")
        if splitter_state is not None:
            self.splitter.restoreState(splitter_state)
        tab_index = self.settings.value("window/tab_index", 0)
        try:
            self.tabs.setCurrentIndex(int(tab_index))
        except (TypeError, ValueError):
            pass

    def closeEvent(self, event: QCloseEvent) -> None:
        self.flush_pending_saves()
        self.settings.set_value("window/geometry", self.saveGeometry())
        self.settings.set_value("window/splitter", self.splitter.saveState())
        self.settings.set_value("window/tab_index", self.tabs.currentIndex())
        self.settings.set_last_note_id(self.current_note_id)
        self.settings.sync()
        self.database.close()
        event.accept()

    def _show_database_error(self, exc: DatabaseError) -> None:
        logger.exception("Database operation failed")
        QMessageBox.critical(self, "Database Error", str(exc))
````

## `app/models.py`

````python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Note:
    id: int
    title: str
    content_html: str
    content_plain: str
    created_at: str
    updated_at: str
    is_deleted: bool


@dataclass(slots=True)
class NoteSummary:
    id: int
    title: str
    preview: str
    created_at: str
    updated_at: str
    is_deleted: bool
````

## `app/paths.py`

````python
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths


def app_data_dir() -> Path:
    path = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    return app_data_dir() / "devnest.db"


def log_dir() -> Path:
    path = app_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / relative
````

## `app/services/__init__.py`

````python

````

## `app/services/logging_setup.py`

````python
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.paths import log_dir


def configure_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(logging.INFO)
    handler = RotatingFileHandler(
        log_dir() / "devnest.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    root.addHandler(handler)
````

## `app/services/txt_codec.py`

````python
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path

TASK_RE = re.compile(
    r"^(?P<indent>[\t ]*)(?P<marker>\[\s\]|\[[xX]\]|☐|☑|✓)(?:[\t ]*)(?P<text>.*)$"
)
INTERNAL_TASK_RE = re.compile(r"^(?P<indent>[\t ]*)(?P<marker>☐|☑)(?:[\t ]?)(?P<text>.*)$")


@dataclass(frozen=True, slots=True)
class ParsedLine:
    text: str
    is_task: bool
    checked: bool = False
    indent: str = ""


def parse_line(line: str) -> ParsedLine:
    match = TASK_RE.match(line)
    if not match:
        return ParsedLine(text=line, is_task=False)
    marker = match.group("marker")
    return ParsedLine(
        text=match.group("text"),
        is_task=True,
        checked=marker.lower() == "[x]" or marker in {"☑", "✓"},
        indent=match.group("indent"),
    )


def parse_text(text: str) -> list[ParsedLine]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return [parse_line(line) for line in normalized.split("\n")]


def _indent_html(indent: str) -> str:
    return html.escape(indent.expandtabs(4))


def parsed_to_html(lines: list[ParsedLine]) -> str:
    blocks: list[str] = ["<!DOCTYPE html><html><head><meta charset=\"utf-8\"></head><body>"]
    for line in lines:
        if line.is_task:
            marker = "☑" if line.checked else "☐"
            task_text = html.escape(line.text)
            if line.checked:
                task_text = f'<span style="text-decoration: line-through;">{task_text}</span>'
            blocks.append(
                f'<p style="margin:0; white-space:pre-wrap;">{_indent_html(line.indent)}{marker} {task_text}</p>'
            )
        else:
            escaped = html.escape(line.text).replace("\t", "    ")
            blocks.append(f'<p style="margin:0; white-space:pre-wrap;">{escaped if escaped else "<br>"}</p>')
    blocks.append("</body></html>")
    return "".join(blocks)



def parsed_to_internal_text(lines: list[ParsedLine]) -> str:
    output: list[str] = []
    for line in lines:
        if line.is_task:
            marker = "☑" if line.checked else "☐"
            suffix = f" {line.text}" if line.text else ""
            output.append(f"{line.indent.expandtabs(4)}{marker}{suffix}")
        else:
            output.append(line.text)
    return "\n".join(output)


def import_text_to_html(text: str) -> str:
    return parsed_to_html(parse_text(text))


def export_internal_plain_text(text: str) -> str:
    output: list[str] = []
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    for line in normalized.split("\n"):
        match = INTERNAL_TASK_RE.match(line)
        if not match:
            output.append(line)
            continue
        prefix = "[x]" if match.group("marker") == "☑" else "[ ]"
        text_part = match.group("text")
        output.append(f"{match.group('indent')}{prefix}{(' ' + text_part) if text_part else ''}")
    return "\n".join(output)


def read_utf8_text(path: Path) -> str:
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise UnicodeError("The file is not valid UTF-8/UTF-8-SIG text.") from exc


def write_utf8_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")
````

## `app/settings.py`

````python
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSettings

from app.constants import DEFAULT_AUTOSAVE_DELAY_MS


@dataclass(slots=True)
class AppPreferences:
    theme: str = "system"
    autosave_enabled: bool = True
    autosave_delay_ms: int = DEFAULT_AUTOSAVE_DELAY_MS
    start_with_last_note: bool = True
    editor_font_size: int = 12
    tab_width: int = 4
    auto_checkbox_default: bool = True
    blank_line_after_enter: bool = False
    word_wrap: bool = True


class SettingsManager:
    def __init__(self, settings: QSettings | None = None) -> None:
        self.qsettings = settings or QSettings()

    def preferences(self) -> AppPreferences:
        return AppPreferences(
            theme=str(self.qsettings.value("appearance/theme", "system")),
            autosave_enabled=self._bool("general/autosave_enabled", True),
            autosave_delay_ms=int(self.qsettings.value("general/autosave_delay_ms", DEFAULT_AUTOSAVE_DELAY_MS)),
            start_with_last_note=self._bool("general/start_with_last_note", True),
            editor_font_size=int(self.qsettings.value("editor/font_size", 12)),
            tab_width=int(self.qsettings.value("editor/tab_width", 4)),
            auto_checkbox_default=self._bool("editor/auto_checkbox_default", True),
            blank_line_after_enter=self._bool("editor/blank_line_after_enter", False),
            word_wrap=self._bool("editor/word_wrap", True),
        )

    def save_preferences(self, prefs: AppPreferences) -> None:
        self.qsettings.setValue("appearance/theme", prefs.theme)
        self.qsettings.setValue("general/autosave_enabled", prefs.autosave_enabled)
        self.qsettings.setValue("general/autosave_delay_ms", prefs.autosave_delay_ms)
        self.qsettings.setValue("general/start_with_last_note", prefs.start_with_last_note)
        self.qsettings.setValue("editor/font_size", prefs.editor_font_size)
        self.qsettings.setValue("editor/tab_width", prefs.tab_width)
        self.qsettings.setValue("editor/auto_checkbox_default", prefs.auto_checkbox_default)
        self.qsettings.setValue("editor/blank_line_after_enter", prefs.blank_line_after_enter)
        self.qsettings.setValue("editor/word_wrap", prefs.word_wrap)
        self.qsettings.sync()

    def last_note_id(self) -> int | None:
        value = self.qsettings.value("session/last_note_id", None)
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def set_last_note_id(self, note_id: int | None) -> None:
        if note_id is None:
            self.qsettings.remove("session/last_note_id")
        else:
            self.qsettings.setValue("session/last_note_id", note_id)

    def value(self, key: str, default: object = None) -> object:
        return self.qsettings.value(key, default)

    def set_value(self, key: str, value: object) -> None:
        self.qsettings.setValue(key, value)

    def sync(self) -> None:
        self.qsettings.sync()

    def _bool(self, key: str, default: bool) -> bool:
        value = self.qsettings.value(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)
````

## `app/themes/__init__.py`

````python

````

## `app/themes/theme_manager.py`

````python
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication


@dataclass(frozen=True, slots=True)
class ThemeSpec:
    key: str
    label: str
    dark: bool
    window: str
    surface: str
    surface_alt: str
    editor: str
    text: str
    muted: str
    border: str
    hover: str
    selected: str
    accent: str
    diagram_bg: str
    diagram_grid_minor: str
    diagram_grid_major: str
    diagram_stroke: str
    diagram_fill: str
    diagram_text: str

    def diagram_palette(self) -> dict[str, str]:
        return {
            "background": self.diagram_bg,
            "grid_minor": self.diagram_grid_minor,
            "grid_major": self.diagram_grid_major,
            "stroke": self.diagram_stroke,
            "fill": self.diagram_fill,
            "text": self.diagram_text,
            "connector": self.diagram_stroke,
        }


THEME_SPECS: dict[str, ThemeSpec] = {
    "dark_matte": ThemeSpec(
        key="dark_matte",
        label="Matte Black",
        dark=True,
        window="#121212",
        surface="#171717",
        surface_alt="#1d1d1d",
        editor="#151515",
        text="#e7e7e7",
        muted="#a7a7a7",
        border="#303030",
        hover="#252525",
        selected="#303030",
        accent="#8b9bb4",
        diagram_bg="#151515",
        diagram_grid_minor="#1d1d1d",
        diagram_grid_major="#292929",
        diagram_stroke="#c4c7cc",
        diagram_fill="#1b1b1b",
        diagram_text="#f0f0f0",
    ),
    "dark_slate": ThemeSpec(
        key="dark_slate",
        label="Midnight Slate",
        dark=True,
        window="#151922",
        surface="#1b202b",
        surface_alt="#222938",
        editor="#181d27",
        text="#e7ecf3",
        muted="#9aa6b6",
        border="#313b4c",
        hover="#283142",
        selected="#33415a",
        accent="#5f86c9",
        diagram_bg="#171c26",
        diagram_grid_minor="#202735",
        diagram_grid_major="#2d384b",
        diagram_stroke="#c1cad8",
        diagram_fill="#202735",
        diagram_text="#eef3f8",
    ),
    "dark_graphite": ThemeSpec(
        key="dark_graphite",
        label="Graphite",
        dark=True,
        window="#202124",
        surface="#25262a",
        surface_alt="#2b2d31",
        editor="#232428",
        text="#e8eaed",
        muted="#a9adb5",
        border="#3a3d43",
        hover="#32343a",
        selected="#3d424b",
        accent="#929aa8",
        diagram_bg="#222327",
        diagram_grid_minor="#292b30",
        diagram_grid_major="#383b42",
        diagram_stroke="#d0d3d8",
        diagram_fill="#292b30",
        diagram_text="#f1f3f4",
    ),
    "light_clean": ThemeSpec(
        key="light_clean",
        label="Clean Light",
        dark=False,
        window="#f7f7f8",
        surface="#ffffff",
        surface_alt="#f0f1f4",
        editor="#ffffff",
        text="#202124",
        muted="#69707c",
        border="#d7d9df",
        hover="#eceef2",
        selected="#dfe7ff",
        accent="#60769f",
        diagram_bg="#f7f8fa",
        diagram_grid_minor="#edf0f3",
        diagram_grid_major="#dde1e6",
        diagram_stroke="#596273",
        diagram_fill="#ffffff",
        diagram_text="#202124",
    ),
    "light_soft": ThemeSpec(
        key="light_soft",
        label="Soft Gray",
        dark=False,
        window="#eceff1",
        surface="#f7f8f9",
        surface_alt="#e6e9ec",
        editor="#f9fafb",
        text="#25282c",
        muted="#687078",
        border="#cfd4d8",
        hover="#e1e5e8",
        selected="#d7e2eb",
        accent="#687f91",
        diagram_bg="#f1f3f4",
        diagram_grid_minor="#e5e8ea",
        diagram_grid_major="#d3d8dc",
        diagram_stroke="#5f6972",
        diagram_fill="#fbfcfc",
        diagram_text="#25282c",
    ),
    "light_warm": ThemeSpec(
        key="light_warm",
        label="Warm Paper",
        dark=False,
        window="#f3efe7",
        surface="#fbf8f1",
        surface_alt="#eee8dc",
        editor="#fffdf8",
        text="#332f2a",
        muted="#766e64",
        border="#d8d0c2",
        hover="#eee7db",
        selected="#e6dccb",
        accent="#8a7255",
        diagram_bg="#faf6ee",
        diagram_grid_minor="#eee8dc",
        diagram_grid_major="#ddd3c4",
        diagram_stroke="#6f655a",
        diagram_fill="#fffdf8",
        diagram_text="#332f2a",
    ),
    "light_cool": ThemeSpec(
        key="light_cool",
        label="Cool Mist",
        dark=False,
        window="#edf4f7",
        surface="#f8fbfc",
        surface_alt="#e4eef2",
        editor="#fbfdfe",
        text="#24313a",
        muted="#647681",
        border="#cad9df",
        hover="#e1edf2",
        selected="#d3e6ef",
        accent="#5e8194",
        diagram_bg="#f3f8fa",
        diagram_grid_minor="#e5eff3",
        diagram_grid_major="#cfdee5",
        diagram_stroke="#58707c",
        diagram_fill="#fbfdfe",
        diagram_text="#24313a",
    ),
}

THEME_OPTIONS: tuple[tuple[str, str], ...] = (
    ("System", "system"),
    ("Matte Black", "dark_matte"),
    ("Midnight Slate", "dark_slate"),
    ("Graphite", "dark_graphite"),
    ("Clean Light", "light_clean"),
    ("Soft Gray", "light_soft"),
    ("Warm Paper", "light_warm"),
    ("Cool Mist", "light_cool"),
)


def _qss(spec: ThemeSpec) -> str:
    return f"""
QWidget {{ color: {spec.text}; }}
QMainWindow, QDialog {{ background: {spec.window}; }}
QMenuBar {{ background: {spec.surface}; color: {spec.text}; }}
QMenuBar::item {{ background: transparent; padding: 5px 8px; }}
QMenuBar::item:selected {{ background: {spec.hover}; }}
QToolBar {{ background: {spec.surface}; border-bottom: 1px solid {spec.border}; spacing: 4px; padding: 4px; }}
QToolButton {{ border: 0; border-radius: 5px; padding: 5px 7px; background: transparent; color: {spec.text}; }}
QToolButton:hover {{ background: {spec.hover}; }}
QToolButton:checked {{ background: {spec.selected}; }}
QToolBar QToolButton#qt_toolbar_ext_button {{ width: 0px; height: 0px; padding: 0; margin: 0; border: 0; }}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QListWidget, QTableWidget {{
    background: {spec.editor}; color: {spec.text}; border: 1px solid {spec.border}; border-radius: 6px; padding: 5px;
    selection-background-color: {spec.selected}; selection-color: {spec.text};
}}
QComboBox QAbstractItemView {{ background: {spec.surface}; color: {spec.text}; border: 1px solid {spec.border}; selection-background-color: {spec.selected}; }}
QListWidget {{ background: {spec.surface}; }}
QListWidget::item {{ border-radius: 6px; padding: 3px; margin: 2px 0; }}
QListWidget::item:selected {{ background: {spec.selected}; color: {spec.text}; }}
QPushButton {{ background: {spec.surface}; color: {spec.text}; border: 1px solid {spec.border}; border-radius: 6px; padding: 6px 10px; }}
QPushButton:hover {{ background: {spec.hover}; }}
QPushButton:pressed, QPushButton:checked {{ background: {spec.selected}; }}
QMenu {{ background: {spec.surface}; color: {spec.text}; border: 1px solid {spec.border}; padding: 4px; }}
QMenu::item {{ padding: 6px 28px 6px 10px; border-radius: 4px; }}
QMenu::item:selected {{ background: {spec.selected}; }}
QStatusBar {{ background: {spec.surface}; border-top: 1px solid {spec.border}; }}
QTabWidget::pane {{ border: 1px solid {spec.border}; background: {spec.editor}; }}
QTabBar::tab {{ background: {spec.surface_alt}; color: {spec.muted}; padding: 7px 14px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }}
QTabBar::tab:selected {{ background: {spec.editor}; color: {spec.text}; }}
QScrollBar:vertical {{ background: transparent; width: 12px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {spec.border}; min-height: 24px; border-radius: 6px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QSplitter::handle {{ background: {spec.border}; width: 1px; }}
QToolTip {{ background: {spec.surface_alt}; color: {spec.text}; border: 1px solid {spec.border}; padding: 4px; }}
QSlider::groove:horizontal {{ height: 4px; background: {spec.border}; border-radius: 2px; }}
QSlider::handle:horizontal {{ width: 14px; margin: -5px 0; background: {spec.text}; border: 1px solid {spec.muted}; border-radius: 7px; }}
QSlider::sub-page:horizontal {{ background: {spec.accent}; border-radius: 2px; }}
QLabel#diagramHint {{ color: {spec.muted}; }}
QWidget#workspaceBar {{ background: {spec.surface}; border-bottom: 1px solid {spec.border}; }}
QPushButton#workspaceButton {{ min-width: 78px; padding: 6px 12px; border: 0; border-radius: 5px; }}
QPushButton#workspaceButton:checked {{ background: {spec.selected}; }}
QComboBox#themePresetCombo {{ min-width: 142px; background: {spec.surface_alt}; }}
"""


class ThemeManager:
    def __init__(self, app: QApplication) -> None:
        self.app = app
        self.current_theme = "system"
        self.current_spec = THEME_SPECS["light_clean"]
        self.is_dark = False

    def apply(self, theme: str) -> bool:
        normalized = theme.lower().strip()
        valid = {value for _, value in THEME_OPTIONS}
        if normalized not in valid:
            # Backward compatibility with DevNest 1.0/1.1 settings.
            if normalized == "dark":
                normalized = "dark_slate"
            elif normalized == "light":
                normalized = "light_clean"
            else:
                normalized = "system"
        self.current_theme = normalized
        resolved = self._resolve_system_theme() if normalized == "system" else normalized
        self.current_spec = THEME_SPECS[resolved]
        self.is_dark = self.current_spec.dark
        self.app.setStyleSheet(_qss(self.current_spec))
        return self.is_dark

    def _resolve_system_theme(self) -> str:
        return "dark_matte" if self._system_is_dark() else "light_clean"

    def _system_is_dark(self) -> bool:
        hints = self.app.styleHints()
        color_scheme = getattr(hints, "colorScheme", None)
        if callable(color_scheme):
            try:
                scheme = color_scheme()
                dark = getattr(Qt.ColorScheme, "Dark", None)
                light = getattr(Qt.ColorScheme, "Light", None)
                if dark is not None and scheme == dark:
                    return True
                if light is not None and scheme == light:
                    return False
            except Exception:
                pass
        palette: QPalette = self.app.palette()
        return palette.color(QPalette.ColorRole.Window).lightness() < 128
````

## `app/utils/__init__.py`

````python

````

## `app/widgets/__init__.py`

````python

````

## `app/widgets/diagram_view.py`

````python
from __future__ import annotations

import math
import uuid
from typing import Callable

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPolygonF, QWheelEvent
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
    QGraphicsTextItem,
    QGraphicsView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


# Shape defaults are used for legacy data and programmatic creation. New shapes are
# created by click-dragging their desired bounds, so these values are only fallbacks.
SHAPE_SIZES: dict[str, tuple[float, float]] = {
    "square": (92.0, 92.0),
    "rect": (160.0, 82.0),
    "rounded": (160.0, 82.0),
    "ellipse": (150.0, 90.0),
    "diamond": (150.0, 100.0),
}

SHAPE_LABELS: dict[str, str] = {
    "square": "Square",
    "rect": "Rectangle",
    "rounded": "Rounded",
    "ellipse": "Ellipse",
    "diamond": "Diamond",
}

MIN_SHAPE_WIDTH = 36.0
MIN_SHAPE_HEIGHT = 28.0
HANDLE_SIZE = 10.0
MIN_CREATE_DRAG = 6.0


DEFAULT_DIAGRAM_PALETTE: dict[str, str] = {
    "background": "#f7f8fa",
    "grid_minor": "#edf0f3",
    "grid_major": "#dde1e6",
    "stroke": "#596273",
    "fill": "#ffffff",
    "text": "#202124",
    "connector": "#596273",
}


def _pen(color: str, width: float = 2.0) -> QPen:
    return QPen(QColor(color), width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)


def _make_shape_path(shape_type: str, width: float, height: float) -> QPainterPath:
    rect = QRectF(0.0, 0.0, max(1.0, width), max(1.0, height))
    path = QPainterPath()
    if shape_type == "ellipse":
        path.addEllipse(rect)
    elif shape_type == "diamond":
        polygon = QPolygonF(
            [
                QPointF(width / 2.0, 0.0),
                QPointF(width, height / 2.0),
                QPointF(width / 2.0, height),
                QPointF(0.0, height / 2.0),
            ]
        )
        path.addPolygon(polygon)
        path.closeSubpath()
    elif shape_type == "rounded":
        radius = min(18.0, max(6.0, min(width, height) * 0.18))
        path.addRoundedRect(rect, radius, radius)
    else:
        path.addRect(rect)
    return path


def _path_points(path: QPainterPath) -> list[list[float]]:
    return [[path.elementAt(i).x, path.elementAt(i).y] for i in range(path.elementCount())]


def _translated_path(path: QPainterPath, offset: QPointF) -> QPainterPath:
    points = _path_points(path)
    if not points:
        return QPainterPath()
    translated = QPainterPath(QPointF(points[0][0] + offset.x(), points[0][1] + offset.y()))
    for x, y in points[1:]:
        translated.lineTo(x + offset.x(), y + offset.y())
    return translated


def _path_from_points(points: object) -> QPainterPath | None:
    if not isinstance(points, list) or not points:
        return None
    first = points[0]
    if not isinstance(first, list) or len(first) < 2:
        return None
    try:
        path = QPainterPath(QPointF(float(first[0]), float(first[1])))
        for point in points[1:]:
            if isinstance(point, list) and len(point) >= 2:
                path.lineTo(float(point[0]), float(point[1]))
        return path
    except (TypeError, ValueError):
        return None


class DiagramResizeHandle(QGraphicsRectItem):
    """Small drag handle used to resize a DiagramShape after creation."""

    _CURSORS = {
        "nw": Qt.CursorShape.SizeFDiagCursor,
        "se": Qt.CursorShape.SizeFDiagCursor,
        "ne": Qt.CursorShape.SizeBDiagCursor,
        "sw": Qt.CursorShape.SizeBDiagCursor,
        "n": Qt.CursorShape.SizeVerCursor,
        "s": Qt.CursorShape.SizeVerCursor,
        "e": Qt.CursorShape.SizeHorCursor,
        "w": Qt.CursorShape.SizeHorCursor,
    }

    def __init__(self, owner: "DiagramShape", role: str) -> None:
        half = HANDLE_SIZE / 2.0
        super().__init__(-half, -half, HANDLE_SIZE, HANDLE_SIZE, owner)
        self.owner = owner
        self.role = role
        self.setZValue(30.0)
        self.setCursor(self._CURSORS[role])
        self.setBrush(QBrush(QColor("#ffffff")))
        self.setPen(_pen("#4f8cff", 1.4))
        self.setVisible(False)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setBrush(QBrush(QColor(palette["fill"])))
        self.setPen(_pen(palette["connector"], 1.4))

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        event.accept()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.owner.resize_from_handle(self.role, event.scenePos())
        event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.owner.finish_resize()
        event.accept()


class DiagramShape(QGraphicsPathItem):
    def __init__(
        self,
        item_id: str,
        shape_type: str,
        text: str,
        on_changed: Callable[[], None],
        width: float | None = None,
        height: float | None = None,
    ) -> None:
        super().__init__()
        self.item_id = item_id
        self.shape_type = shape_type if shape_type in SHAPE_SIZES else "rect"
        self._on_changed = on_changed
        default_width, default_height = SHAPE_SIZES[self.shape_type]
        self._width = max(MIN_SHAPE_WIDTH, float(width if width is not None else default_width))
        self._height = max(MIN_SHAPE_HEIGHT, float(height if height is not None else default_height))
        self.setPath(_make_shape_path(self.shape_type, self._width, self._height))
        self.label = QGraphicsTextItem(text, self)
        self.label.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.label.setTextWidth(max(28.0, self._width - 20.0))
        self._position_label()
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setPen(_pen("#747b88", 1.6))
        self.setBrush(QBrush(QColor("#ffffff")))
        self._handles = {role: DiagramResizeHandle(self, role) for role in ("nw", "n", "ne", "e", "se", "s", "sw", "w")}
        self._position_handles()

    @property
    def width(self) -> float:
        return self._width

    @property
    def height(self) -> float:
        return self._height

    def _position_label(self) -> None:
        self.label.setTextWidth(max(28.0, self._width - 20.0))
        label_height = self.label.boundingRect().height()
        self.label.setPos(10.0, max(4.0, (self._height - label_height) / 2.0))

    def _position_handles(self) -> None:
        x_mid = self._width / 2.0
        y_mid = self._height / 2.0
        positions = {
            "nw": QPointF(0.0, 0.0),
            "n": QPointF(x_mid, 0.0),
            "ne": QPointF(self._width, 0.0),
            "e": QPointF(self._width, y_mid),
            "se": QPointF(self._width, self._height),
            "s": QPointF(x_mid, self._height),
            "sw": QPointF(0.0, self._height),
            "w": QPointF(0.0, y_mid),
        }
        for role, handle in self._handles.items():
            handle.setPos(positions[role])

    def set_size(self, width: float, height: float, *, notify: bool = True) -> None:
        self._width = max(MIN_SHAPE_WIDTH, float(width))
        self._height = max(MIN_SHAPE_HEIGHT, float(height))
        self.setPath(_make_shape_path(self.shape_type, self._width, self._height))
        self._position_label()
        self._position_handles()
        if notify:
            self._on_changed()

    def resize_from_handle(self, role: str, scene_pos: QPointF) -> None:
        left = self.x()
        top = self.y()
        right = left + self._width
        bottom = top + self._height

        if "w" in role:
            left = min(scene_pos.x(), right - MIN_SHAPE_WIDTH)
        if "e" in role:
            right = max(scene_pos.x(), left + MIN_SHAPE_WIDTH)
        if "n" in role:
            top = min(scene_pos.y(), bottom - MIN_SHAPE_HEIGHT)
        if "s" in role:
            bottom = max(scene_pos.y(), top + MIN_SHAPE_HEIGHT)

        self.setPos(left, top)
        self.set_size(right - left, bottom - top, notify=False)
        self._on_changed()

    def finish_resize(self) -> None:
        self._on_changed()

    @property
    def text(self) -> str:
        return self.label.toPlainText()

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setBrush(QBrush(QColor(palette["fill"])))
        self.setPen(_pen(palette["stroke"], 1.6))
        self.label.setDefaultTextColor(QColor(palette["text"]))
        for handle in self._handles.values():
            handle.set_theme(palette)

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._on_changed()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            selected = bool(value)
            for handle in self._handles.values():
                handle.setVisible(selected)
        return result

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        text, ok = QInputDialog.getText(None, "Edit Shape", "Text:", text=self.text)
        if ok:
            self.label.setPlainText(text or SHAPE_LABELS.get(self.shape_type, "Shape"))
            self._position_label()
            self._on_changed()
        event.accept()


class DiagramText(QGraphicsTextItem):
    def __init__(self, item_id: str, text: str, on_changed: Callable[[], None]) -> None:
        super().__init__(text)
        self.item_id = item_id
        self._on_changed = on_changed
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setDefaultTextColor(QColor(palette["text"]))

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._on_changed()
        return result

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        text, ok = QInputDialog.getMultiLineText(None, "Edit Text", "Text:", self.toPlainText())
        if ok:
            self.setPlainText(text)
            self._on_changed()
        event.accept()


class DiagramEdge(QGraphicsPathItem):
    """Legacy node-to-node edge kept for old DevNest diagrams."""

    def __init__(self, source_id: str, target_id: str) -> None:
        super().__init__()
        self.source_id = source_id
        self.target_id = target_id
        self._start = QPointF()
        self._end = QPointF()
        self.setZValue(-10)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setPen(_pen("#596273", 2.6))

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setPen(_pen(palette["connector"], 2.6))

    def set_endpoints(self, start: QPointF, end: QPointF) -> None:
        self._start = start
        self._end = end
        path = QPainterPath(start)
        path.lineTo(end)
        self.setPath(path)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)
        _paint_arrow_head(painter, self.path(), self.pen())


class DiagramFreehand(QGraphicsPathItem):
    """A freehand drawing that can also act as a connection endpoint."""

    def __init__(
        self,
        item_id: str,
        path: QPainterPath | None,
        on_changed: Callable[[], None],
    ) -> None:
        super().__init__(path or QPainterPath())
        self.item_id = item_id
        self._on_changed = on_changed
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setPen(_pen(palette["stroke"], 2.2))

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._on_changed()
        return result


DiagramEndpoint = DiagramShape | DiagramText | DiagramFreehand


class DiagramConnector(QGraphicsPathItem):
    """A hand-drawn arrow whose route can optionally stay attached to shapes."""

    def __init__(
        self,
        path: QPainterPath | None = None,
        source_id: str | None = None,
        target_id: str | None = None,
    ) -> None:
        super().__init__(path or QPainterPath())
        self.source_id = source_id
        self.target_id = target_id
        self.setZValue(-6)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setPen(_pen("#596273", 2.6))

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setPen(_pen(palette["connector"], 2.6))

    def paint(self, painter: QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)
        _paint_arrow_head(painter, self.path(), self.pen())


def _paint_arrow_head(painter: QPainter, path: QPainterPath, pen: QPen) -> None:
    count = path.elementCount()
    if count < 2:
        return
    end_element = path.elementAt(count - 1)
    end = QPointF(end_element.x, end_element.y)
    previous: QPointF | None = None
    for index in range(count - 2, -1, -1):
        element = path.elementAt(index)
        candidate = QPointF(element.x, element.y)
        if QLineF(candidate, end).length() >= 2.0:
            previous = candidate
            break
    if previous is None:
        return
    line = QLineF(previous, end)
    angle = math.atan2(-line.dy(), line.dx())
    arrow_size = 16.0
    left = end - QPointF(
        math.sin(angle + math.pi / 3.0) * arrow_size,
        math.cos(angle + math.pi / 3.0) * arrow_size,
    )
    right = end - QPointF(
        math.sin(angle + math.pi - math.pi / 3.0) * arrow_size,
        math.cos(angle + math.pi - math.pi / 3.0) * arrow_size,
    )
    painter.setBrush(pen.color())
    painter.setPen(pen)
    painter.drawPolygon(QPolygonF([end, left, right]))


class DiagramScene(QGraphicsScene):
    diagramChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.mode = "select"
        self.current_path: DiagramFreehand | None = None  # legacy only
        self.current_connector: DiagramConnector | None = None
        self._last_draw_point: QPointF | None = None
        self._shape_preview: QGraphicsPathItem | None = None
        self._shape_start: QPointF | None = None
        self._shape_type: str | None = None
        self.palette = dict(DEFAULT_DIAGRAM_PALETTE)
        self.path_pen = _pen(self.palette["stroke"])
        self.loading = False
        self.setSceneRect(-2500, -2500, 5000, 5000)

    def set_mode(self, mode: str) -> None:
        self._cancel_shape_preview()
        if self.current_connector is not None and self.current_connector.scene() is self:
            self.removeItem(self.current_connector)
        self.mode = mode
        self.current_path = None
        self.current_connector = None
        self._last_draw_point = None

    def _notify_changed(self) -> None:
        self.update_connections()
        if not self.loading:
            self.diagramChanged.emit()

    @staticmethod
    def _new_id() -> str:
        return uuid.uuid4().hex

    def add_shape(
        self,
        shape_type: str,
        pos: QPointF,
        text: str | None = None,
        item_id: str | None = None,
        width: float | None = None,
        height: float | None = None,
        notify: bool = True,
    ) -> DiagramShape:
        label = text if text is not None else SHAPE_LABELS.get(shape_type, "Shape")
        shape = DiagramShape(
            item_id or self._new_id(),
            shape_type,
            label,
            self._notify_changed,
            width=width,
            height=height,
        )
        shape.set_theme(self.palette)
        self.addItem(shape)
        shape.setPos(pos)
        if notify:
            self._notify_changed()
        return shape

    @staticmethod
    def _drag_rect(start: QPointF, end: QPointF) -> QRectF:
        return QRectF(start, end).normalized()

    def _begin_shape_preview(self, shape_type: str, pos: QPointF) -> None:
        self._cancel_shape_preview()
        self._shape_start = pos
        self._shape_type = shape_type if shape_type in SHAPE_SIZES else "square"
        preview = QGraphicsPathItem()
        preview.setZValue(50.0)
        pen = _pen(self.palette["connector"], 1.6)
        pen.setStyle(Qt.PenStyle.DashLine)
        preview.setPen(pen)
        fill = QColor(self.palette["fill"])
        fill.setAlpha(72)
        preview.setBrush(QBrush(fill))
        preview.setPath(_make_shape_path(self._shape_type, 1.0, 1.0))
        preview.setPos(pos)
        self.addItem(preview)
        self._shape_preview = preview

    def _update_shape_preview(self, pos: QPointF) -> None:
        if self._shape_preview is None or self._shape_start is None or self._shape_type is None:
            return
        rect = self._drag_rect(self._shape_start, pos)
        self._shape_preview.setPos(rect.topLeft())
        self._shape_preview.setPath(
            _make_shape_path(self._shape_type, max(1.0, rect.width()), max(1.0, rect.height()))
        )

    def _finish_shape_preview(self, pos: QPointF) -> DiagramShape | None:
        if self._shape_preview is None or self._shape_start is None or self._shape_type is None:
            self._cancel_shape_preview()
            return None
        rect = self._drag_rect(self._shape_start, pos)
        shape_type = self._shape_type
        self._cancel_shape_preview()
        if rect.width() < MIN_CREATE_DRAG or rect.height() < MIN_CREATE_DRAG:
            return None
        width = max(MIN_SHAPE_WIDTH, rect.width())
        height = max(MIN_SHAPE_HEIGHT, rect.height())
        shape = self.add_shape(
            shape_type,
            rect.topLeft(),
            width=width,
            height=height,
            notify=False,
        )
        self.clearSelection()
        shape.setSelected(True)
        self._notify_changed()
        return shape

    def _cancel_shape_preview(self) -> None:
        if self._shape_preview is not None and self._shape_preview.scene() is self:
            self.removeItem(self._shape_preview)
        self._shape_preview = None
        self._shape_start = None
        self._shape_type = None

    def add_text(self, pos: QPointF, text: str = "Text", item_id: str | None = None) -> DiagramText:
        item = DiagramText(item_id or self._new_id(), text, self._notify_changed)
        item.set_theme(self.palette)
        self.addItem(item)
        item.setPos(pos)
        self._notify_changed()
        return item

    def add_edge(self, source: DiagramEndpoint, target: DiagramEndpoint) -> DiagramEdge:
        if source.item_id == target.item_id:
            raise ValueError("A diagram item cannot connect to itself")
        edge = DiagramEdge(source.item_id, target.item_id)
        edge.set_theme(self.palette)
        self.addItem(edge)
        self.update_edges()
        self._notify_changed()
        return edge

    def add_freehand_path(
        self,
        path: QPainterPath,
        item_id: str | None = None,
        notify: bool = True,
    ) -> DiagramFreehand:
        item = DiagramFreehand(item_id or self._new_id(), path, self._notify_changed)
        item.set_theme(self.palette)
        self.addItem(item)
        if notify:
            self._notify_changed()
        return item

    def add_connector_path(
        self,
        path: QPainterPath,
        notify: bool = True,
        source_id: str | None = None,
        target_id: str | None = None,
    ) -> DiagramConnector:
        if not source_id or not target_id or source_id == target_id:
            raise ValueError("A connector must link two different diagram items")
        nodes = self._nodes_by_id()
        if source_id not in nodes or target_id not in nodes:
            raise ValueError("Connector endpoints must exist in the scene")
        connector = DiagramConnector(path, source_id=source_id, target_id=target_id)
        connector.set_theme(self.palette)
        self.addItem(connector)
        if notify:
            self._notify_changed()
        return connector

    def update_connections(self) -> None:
        self.update_edges()
        self.update_drawn_connectors()

    def update_edges(self) -> None:
        nodes = self._nodes_by_id()
        for item in self.items():
            if not isinstance(item, DiagramEdge):
                continue
            source = nodes.get(item.source_id)
            target = nodes.get(item.target_id)
            if source is None or target is None:
                continue
            source_center = source.sceneBoundingRect().center()
            target_center = target.sceneBoundingRect().center()
            start = self._connection_point(source, target_center)
            end = self._connection_point(target, source_center)
            item.set_endpoints(start, end)

    def update_drawn_connectors(self) -> None:
        nodes = self._nodes_by_id()
        for item in self.items():
            if not isinstance(item, DiagramConnector):
                continue
            points = _path_points(item.path())
            if len(points) < 2:
                continue
            if item.source_id and item.source_id in nodes:
                toward = QPointF(points[1][0], points[1][1])
                start = self._connection_point(nodes[item.source_id], toward)
                points[0] = [start.x(), start.y()]
            if item.target_id and item.target_id in nodes:
                toward = QPointF(points[-2][0], points[-2][1])
                end = self._connection_point(nodes[item.target_id], toward)
                points[-1] = [end.x(), end.y()]
            rebuilt = _path_from_points(points)
            if rebuilt is not None:
                item.setPath(rebuilt)

    @staticmethod
    def _scene_path(item: DiagramFreehand) -> QPainterPath:
        points = _path_points(item.path())
        if not points:
            return QPainterPath()
        first = item.mapToScene(QPointF(points[0][0], points[0][1]))
        scene_path = QPainterPath(first)
        for x, y in points[1:]:
            scene_point = item.mapToScene(QPointF(x, y))
            scene_path.lineTo(scene_point)
        return scene_path

    def _connection_point(self, item: DiagramEndpoint, toward: QPointF) -> QPointF:
        if isinstance(item, DiagramFreehand):
            # Freehand objects have no artificial center anchor. Attach the
            # connector to the actual drawn contour point nearest to the drag.
            scene_path = self._scene_path(item)
            points = _path_points(scene_path)
            if not points:
                return item.sceneBoundingRect().center()
            best = min(
                (QPointF(x, y) for x, y in points),
                key=lambda point: QLineF(point, toward).length(),
            )
            return best
        return self._boundary_point(item, toward)

    def _boundary_point(self, item: DiagramEndpoint, toward: QPointF) -> QPointF:
        rect = item.sceneBoundingRect()
        center = rect.center()
        dx = toward.x() - center.x()
        dy = toward.y() - center.y()
        if abs(dx) < 1e-6 and abs(dy) < 1e-6:
            return center
        half_w = max(1.0, rect.width() / 2.0)
        half_h = max(1.0, rect.height() / 2.0)
        shape_type = item.shape_type if isinstance(item, DiagramShape) else "rect"
        if shape_type == "ellipse":
            scale = 1.0 / math.sqrt((dx / half_w) ** 2 + (dy / half_h) ** 2)
        elif shape_type == "diamond":
            scale = 1.0 / (abs(dx) / half_w + abs(dy) / half_h)
        else:
            scale = min(half_w / max(abs(dx), 1e-6), half_h / max(abs(dy), 1e-6))
        return QPointF(center.x() + dx * scale, center.y() + dy * scale)

    def _nodes_by_id(self) -> dict[str, DiagramEndpoint]:
        result: dict[str, DiagramEndpoint] = {}
        for item in self.items():
            if isinstance(item, (DiagramShape, DiagramText, DiagramFreehand)):
                result[item.item_id] = item
        return result

    def _endpoint_at(self, pos: QPointF) -> DiagramEndpoint | None:
        # First prefer the exact Qt hit-test, including child text labels.
        for item in self.items(pos):
            current = item
            while current is not None:
                if isinstance(current, (DiagramShape, DiagramText, DiagramFreehand)):
                    return current
                current = current.parentItem()

        # A hand-drawn box/circle often has an empty interior. Treat the interior
        # of its bounding box as a practical hit area so connecting does not
        # require pixel-perfect clicking on the pen stroke. Smallest match wins.
        candidates: list[DiagramFreehand] = []
        for item in self.items():
            if isinstance(item, DiagramFreehand) and item.sceneBoundingRect().adjusted(-8, -8, 8, 8).contains(pos):
                candidates.append(item)
        if candidates:
            return min(candidates, key=lambda item: item.sceneBoundingRect().width() * item.sceneBoundingRect().height())
        return None

    @staticmethod
    def _append_sample(item: QGraphicsPathItem, pos: QPointF, previous: QPointF | None) -> QPointF:
        if previous is not None and QLineF(previous, pos).length() < 1.5:
            return previous
        path = item.path()
        path.lineTo(pos)
        item.setPath(path)
        return pos

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        pos = event.scenePos()
        if event.button() == Qt.MouseButton.LeftButton:
            if self.mode.startswith("shape:"):
                self._begin_shape_preview(self.mode.split(":", 1)[1], pos)
                event.accept()
                return
            if self.mode == "text":
                text, ok = QInputDialog.getText(None, "Text", "Text:")
                if ok:
                    self.add_text(pos, text or "Text")
                event.accept()
                return
            if self.mode == "connect":
                source = self._endpoint_at(pos)
                if source is None:
                    self.current_connector = None
                    self._last_draw_point = None
                    event.accept()
                    return
                start = self._connection_point(source, pos)
                path = QPainterPath(start)
                self.current_connector = DiagramConnector(path, source_id=source.item_id)
                self.current_connector.set_theme(self.palette)
                self.addItem(self.current_connector)
                self._last_draw_point = start
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.mode.startswith("shape:") and self._shape_preview is not None:
            self._update_shape_preview(event.scenePos())
            event.accept()
            return
        if self.mode == "connect" and self.current_connector is not None:
            self._last_draw_point = self._append_sample(
                self.current_connector, event.scenePos(), self._last_draw_point
            )
            points = _path_points(self.current_connector.path())
            nodes = self._nodes_by_id()
            source = nodes.get(self.current_connector.source_id or "")
            if source is not None and len(points) >= 2:
                toward = QPointF(points[1][0], points[1][1])
                start = self._connection_point(source, toward)
                points[0] = [start.x(), start.y()]
                rebuilt = _path_from_points(points)
                if rebuilt is not None:
                    self.current_connector.setPath(rebuilt)
            event.accept()
            return
        super().mouseMoveEvent(event)
        self.update_connections()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.mode.startswith("shape:"):
            self._finish_shape_preview(event.scenePos())
            event.accept()
            return

        if event.button() == Qt.MouseButton.LeftButton and self.mode == "connect":
            item = self.current_connector
            if item is not None:
                self._append_sample(item, event.scenePos(), self._last_draw_point)
                keep_item = item.path().elementCount() >= 2
                target = self._endpoint_at(event.scenePos())
                valid_target = (
                    target is not None
                    and item.source_id is not None
                    and target.item_id != item.source_id
                )
                if not valid_target:
                    keep_item = False
                else:
                    item.target_id = target.item_id
                    points = _path_points(item.path())
                    if len(points) >= 2:
                        end = self._connection_point(target, QPointF(points[-2][0], points[-2][1]))
                        points[-1] = [end.x(), end.y()]
                        rebuilt = _path_from_points(points)
                        if rebuilt is not None:
                            item.setPath(rebuilt)
                if not keep_item and item.scene() is self:
                    self.removeItem(item)
                self.current_connector = None
                self._last_draw_point = None
                if keep_item:
                    self._notify_changed()
            event.accept()
            return

        super().mouseReleaseEvent(event)
        self._notify_changed()

    def delete_selected(self) -> None:
        selected = list(self.selectedItems())
        if not selected:
            return
        node_ids = {item.item_id for item in selected if isinstance(item, (DiagramShape, DiagramText, DiagramFreehand))}
        for item in list(self.items()):
            if isinstance(item, (DiagramEdge, DiagramConnector)) and (
                item.source_id in node_ids or item.target_id in node_ids
            ):
                self.removeItem(item)
        for item in selected:
            if item.scene() is self:
                self.removeItem(item)
        self._notify_changed()

    def duplicate_selected(self) -> None:
        selected = list(self.selectedItems())
        if not selected:
            return
        self.clearSelection()
        created = False
        offset = QPointF(24.0, 24.0)
        for item in selected:
            if isinstance(item, DiagramShape):
                copy = self.add_shape(item.shape_type, item.pos() + offset, item.text, width=item.width, height=item.height)
                copy.setSelected(True)
                created = True
            elif isinstance(item, DiagramText):
                copy = self.add_text(item.pos() + offset, item.toPlainText())
                copy.setSelected(True)
                created = True
            elif isinstance(item, DiagramFreehand):
                scene_path = self._scene_path(item)
                path = _translated_path(scene_path, offset)
                copy = self.add_freehand_path(path, notify=False)
                copy.setSelected(True)
                created = True
            elif isinstance(item, DiagramConnector):
                path = _translated_path(item.path(), offset)
                copy = self.add_connector_path(
                    path, notify=False, source_id=item.source_id, target_id=item.target_id
                )
                copy.setSelected(True)
                created = True
        if created:
            self._notify_changed()

    def set_theme(self, palette: dict[str, str] | bool) -> None:
        if isinstance(palette, bool):
            # Compatibility with older caller code/tests.
            palette = {
                **DEFAULT_DIAGRAM_PALETTE,
                **(
                    {
                        "background": "#151515",
                        "grid_minor": "#1d1d1d",
                        "grid_major": "#292929",
                        "stroke": "#c4c7cc",
                        "fill": "#1b1b1b",
                        "text": "#f0f0f0",
                        "connector": "#c4c7cc",
                    }
                    if palette
                    else {}
                ),
            }
        self.palette = {**DEFAULT_DIAGRAM_PALETTE, **palette}
        self.setBackgroundBrush(QBrush(QColor(self.palette["background"])))
        self.path_pen = _pen(self.palette["stroke"])
        for item in self.items():
            if isinstance(item, (DiagramShape, DiagramText, DiagramEdge, DiagramFreehand, DiagramConnector)):
                item.set_theme(self.palette)

    def to_data(self) -> dict[str, object]:
        nodes: list[dict[str, object]] = []
        edges: list[dict[str, object]] = []
        paths: list[dict[str, object]] = []
        connectors: list[dict[str, object]] = []
        for item in self.items():
            if isinstance(item, DiagramShape):
                nodes.append(
                    {
                        "type": "shape",
                        "shape": item.shape_type,
                        "id": item.item_id,
                        "x": item.x(),
                        "y": item.y(),
                        "text": item.text,
                        "width": item.width,
                        "height": item.height,
                    }
                )
            elif isinstance(item, DiagramText):
                nodes.append(
                    {
                        "type": "text",
                        "id": item.item_id,
                        "x": item.x(),
                        "y": item.y(),
                        "text": item.toPlainText(),
                    }
                )
            elif isinstance(item, DiagramEdge):
                edges.append({"source": item.source_id, "target": item.target_id})
            elif isinstance(item, DiagramConnector):
                points = _path_points(item.path())
                if (
                    points
                    and item.source_id
                    and item.target_id
                    and item.source_id != item.target_id
                ):
                    connectors.append(
                        {
                            "points": points,
                            "source": item.source_id,
                            "target": item.target_id,
                        }
                    )
            elif isinstance(item, DiagramFreehand):
                points = _path_points(self._scene_path(item))
                if points:
                    paths.append({"id": item.item_id, "points": points})
        return {"version": 5, "items": nodes, "edges": edges, "paths": paths, "connectors": connectors}

    def load_data(self, data: dict[str, object]) -> None:
        self.loading = True
        try:
            self.current_path = None
            self.current_connector = None
            self._last_draw_point = None
            self._shape_preview = None
            self._shape_start = None
            self._shape_type = None
            self.clear()
            id_map: dict[str, DiagramEndpoint] = {}
            for raw in data.get("items", []) if isinstance(data, dict) else []:
                if not isinstance(raw, dict):
                    continue
                item_id = str(raw.get("id", self._new_id()))
                try:
                    pos = QPointF(float(raw.get("x", 0.0)), float(raw.get("y", 0.0)))
                except (TypeError, ValueError):
                    pos = QPointF()
                text = str(raw.get("text", "Shape"))
                item_type = str(raw.get("type", "node"))
                if item_type == "text":
                    item = self.add_text(pos, text, item_id)
                else:
                    # Version 1 stored rectangle nodes as type="node" without a shape field.
                    shape_type = str(raw.get("shape", "rect"))
                    try:
                        width = float(raw["width"]) if "width" in raw else None
                        height = float(raw["height"]) if "height" in raw else None
                    except (TypeError, ValueError):
                        width = None
                        height = None
                    item = self.add_shape(
                        shape_type, pos, text, item_id, width=width, height=height, notify=False
                    )
                id_map[item_id] = item

            for raw in data.get("edges", []) if isinstance(data, dict) else []:
                if not isinstance(raw, dict):
                    continue
                source = id_map.get(str(raw.get("source", "")))
                target = id_map.get(str(raw.get("target", "")))
                if source is not None and target is not None and source is not target:
                    self.add_edge(source, target)

            for raw in data.get("paths", []) if isinstance(data, dict) else []:
                if not isinstance(raw, dict):
                    continue
                path = _path_from_points(raw.get("points", []))
                if path is None:
                    continue
                item_id = str(raw.get("id", self._new_id()))
                path_item = self.add_freehand_path(path, item_id=item_id, notify=False)
                id_map[item_id] = path_item

            for raw in data.get("connectors", []) if isinstance(data, dict) else []:
                if not isinstance(raw, dict):
                    continue
                path = _path_from_points(raw.get("points", []))
                if path is not None:
                    source_id = str(raw.get("source")) if raw.get("source") else None
                    target_id = str(raw.get("target")) if raw.get("target") else None
                    # Version 4+ only accepts connectors that are anchored at both ends.
                    # Legacy floating connectors are intentionally ignored instead of
                    # reintroducing arrows that point to empty canvas space.
                    if (
                        source_id in id_map
                        and target_id in id_map
                        and source_id != target_id
                    ):
                        self.add_connector_path(
                            path, notify=False, source_id=source_id, target_id=target_id
                        )

            self.update_connections()
            self.set_theme(self.palette)
        finally:
            self.loading = False


class DiagramCanvas(QGraphicsView):
    def __init__(self, scene: DiagramScene, parent=None) -> None:
        super().__init__(scene, parent)
        self.palette = dict(DEFAULT_DIAGRAM_PALETTE)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self._middle_panning = False
        self._middle_pan_pos = QPointF()


    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._middle_panning = True
            self._middle_pan_pos = event.position()
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._middle_panning:
            current = event.position()
            delta = current - self._middle_pan_pos
            self._middle_pan_pos = current
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton and self._middle_panning:
            self._middle_panning = False
            self.viewport().unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def set_mode(self, mode: str) -> None:
        if mode == "pan":
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
        elif mode == "select":
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.viewport().setCursor(Qt.CursorShape.CrossCursor)

    def set_theme(self, palette: dict[str, str] | bool) -> None:
        if isinstance(palette, bool):
            self.palette = dict(DEFAULT_DIAGRAM_PALETTE)
            if palette:
                self.palette.update(
                    {
                        "background": "#151515",
                        "grid_minor": "#1d1d1d",
                        "grid_major": "#292929",
                    }
                )
        else:
            self.palette = {**DEFAULT_DIAGRAM_PALETTE, **palette}
        self.viewport().update()

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        painter.fillRect(rect, QColor(self.palette["background"]))
        minor = 25
        major = 100
        left = int(math.floor(rect.left() / minor) * minor)
        top = int(math.floor(rect.top() / minor) * minor)
        minor_pen = QPen(QColor(self.palette["grid_minor"]), 1.0)
        major_pen = QPen(QColor(self.palette["grid_major"]), 1.0)
        x = left
        while x < rect.right():
            painter.setPen(major_pen if x % major == 0 else minor_pen)
            painter.drawLine(QLineF(float(x), rect.top(), float(x), rect.bottom()))
            x += minor
        y = top
        while y < rect.bottom():
            painter.setPen(major_pen if y % major == 0 else minor_pen)
            painter.drawLine(QLineF(rect.left(), float(y), rect.right(), float(y)))
            y += minor

    def wheelEvent(self, event: QWheelEvent) -> None:
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)
        event.accept()

    def keyPressEvent(self, event) -> None:
        scene = self.scene()
        if isinstance(scene, DiagramScene):
            if event.key() == Qt.Key.Key_Delete:
                scene.delete_selected()
                event.accept()
                return
            if event.key() == Qt.Key.Key_D and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                scene.duplicate_selected()
                event.accept()
                return
        super().keyPressEvent(event)

    def fit_all(self) -> None:
        scene = self.scene()
        if scene is None:
            return
        bounds = scene.itemsBoundingRect()
        if bounds.isNull() or bounds.isEmpty():
            self.resetTransform()
            return
        self.fitInView(bounds.adjusted(-60, -60, 60, 60), Qt.AspectRatioMode.KeepAspectRatio)


class DiagramView(QWidget):
    diagramChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        bar = QHBoxLayout()
        bar.setContentsMargins(6, 4, 6, 0)
        self.scene = DiagramScene(self)
        self.scene.diagramChanged.connect(self.diagramChanged)
        self.canvas = DiagramCanvas(self.scene)
        self._mode_buttons: dict[str, QPushButton] = {}

        tools = [
            ("Select", "select", "Select/move items; selected shapes show resize handles"),
            ("Pan", "pan", "Pan the canvas (middle mouse drag works in every tool)"),
            ("Square", "shape:square", "Press and drag to draw a box at exactly the size you want; stretch it into a rectangle if needed"),
            ("Round", "shape:rounded", "Press and drag to draw a rounded box at the size you want"),
            ("Ellipse", "shape:ellipse", "Press and drag to draw an ellipse at the size you want"),
            ("Diamond", "shape:diamond", "Press and drag to draw a decision diamond at the size you want"),
            ("Text", "text", "Add standalone text"),
            ("Connect", "connect", "Start on one existing item and drag any route to another item; the arrow points to the target"),
        ]
        for label, mode, tooltip in tools:
            button = QPushButton(label)
            button.setCheckable(True)
            button.setToolTip(tooltip)
            button.clicked.connect(lambda _checked=False, m=mode: self.set_mode(m))
            bar.addWidget(button)
            self._mode_buttons[mode] = button

        bar.addStretch(1)
        duplicate = QPushButton("Duplicate")
        duplicate.setToolTip("Duplicate selected diagram items (Ctrl+D)")
        duplicate.clicked.connect(self.scene.duplicate_selected)
        fit = QPushButton("Fit")
        fit.setToolTip("Fit all diagram items in view")
        fit.clicked.connect(self.canvas.fit_all)
        zoom_out = QPushButton("−")
        zoom_out.setToolTip("Zoom out")
        zoom_out.clicked.connect(lambda: self.canvas.scale(0.85, 0.85))
        zoom_in = QPushButton("+")
        zoom_in.setToolTip("Zoom in")
        zoom_in.clicked.connect(lambda: self.canvas.scale(1.15, 1.15))
        delete = QPushButton("Delete")
        delete.setToolTip("Delete selected diagram items (Delete)")
        delete.clicked.connect(self.scene.delete_selected)
        for button in (duplicate, fit, zoom_out, zoom_in, delete):
            bar.addWidget(button)

        hint = QLabel(
            "Square/Round/Ellipse/Diamond: basılı tutup sürükleyerek istediğin boyutta çiz. Select: seçili şeklin 8 tutamacından yeniden boyutlandır. Connect: bir öğeden diğerine rota çiz. Orta mouse: canvas taşı."
        )
        hint.setObjectName("diagramHint")
        hint.setContentsMargins(8, 0, 8, 2)

        root.addLayout(bar)
        root.addWidget(hint)
        root.addWidget(self.canvas, 1)
        self.set_mode("shape:square")

    def set_mode(self, mode: str) -> None:
        self.scene.set_mode(mode)
        self.canvas.set_mode(mode)
        for button_mode, button in self._mode_buttons.items():
            button.setChecked(button_mode == mode)

    def set_theme(self, palette: dict[str, str] | bool) -> None:
        self.scene.set_theme(palette)
        self.canvas.set_theme(palette)

    def load_data(self, data: dict[str, object]) -> None:
        self.scene.load_data(data)
        self.canvas.resetTransform()

    def to_data(self) -> dict[str, object]:
        return self.scene.to_data()

    def delete_selected(self) -> None:
        self.scene.delete_selected()
````

## `app/widgets/note_editor.py`

````python
from __future__ import annotations

import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QFontDatabase, QKeyEvent, QMouseEvent, QTextBlock, QTextCharFormat, QTextCursor, QTextListFormat
from PySide6.QtWidgets import QMenu, QTextEdit

from app.constants import TAB_SPACES

TASK_LINE_RE = re.compile(r"^(?P<indent>[ ]*)(?P<marker>☐|☑)(?: (?P<text>.*))?$")


class NoteEditor(QTextEdit):
    taskStateChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.auto_checkbox_enabled = True
        self.blank_line_after_enter = False
        self.tab_spaces = TAB_SPACES
        self.base_font_size = 12
        self.setAcceptRichText(True)
        self.setUndoRedoEnabled(True)
        self.setPlaceholderText("Write notes, tasks, bugs, ideas, or plans…")
        self.setTabChangesFocus(False)
        self.setMouseTracking(True)
        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(self.base_font_size)
        self.setFont(font)

    def set_editor_font_size(self, size: int) -> None:
        self.base_font_size = max(8, min(32, size))
        font = self.font()
        font.setPointSize(self.base_font_size)
        self.setFont(font)

    def apply_font_family(self, family: str) -> None:
        if not family:
            return
        fmt = QTextCharFormat()
        fmt.setFontFamilies([family])
        self._merge_font_format(fmt)

    def apply_font_point_size(self, size: int) -> None:
        size = max(8, min(48, int(size)))
        fmt = QTextCharFormat()
        fmt.setFontPointSize(float(size))
        self._merge_font_format(fmt)

    def apply_font_weight(self, weight: int) -> None:
        weight = max(100, min(900, int(round(weight / 100.0) * 100)))
        fmt = QTextCharFormat()
        fmt.setFontWeight(weight)
        self._merge_font_format(fmt)

    def set_tab_width(self, spaces: int) -> None:
        self.tab_spaces = max(2, min(8, spaces))
        metrics = self.fontMetrics()
        self.setTabStopDistance(metrics.horizontalAdvance(" ") * self.tab_spaces)

    def set_auto_checkbox(self, enabled: bool) -> None:
        self.auto_checkbox_enabled = enabled

    def set_blank_line_after_enter(self, enabled: bool) -> None:
        self.blank_line_after_enter = enabled

    def insert_checkbox(self) -> None:
        cursor = self.textCursor()
        block = cursor.block()
        match = TASK_LINE_RE.match(block.text())
        if match:
            self.toggle_checkbox(block)
            return
        block_pos = block.position()
        leading = len(block.text()) - len(block.text().lstrip(" "))
        cursor.setPosition(block_pos + leading)
        cursor.insertText("☐ ")
        self.setTextCursor(cursor)
        self._apply_task_style(cursor.block(), checked=False)
        self.taskStateChanged.emit()

    def toggle_checkbox_at_cursor(self) -> bool:
        block = self.textCursor().block()
        if not TASK_LINE_RE.match(block.text()):
            return False
        self.toggle_checkbox(block)
        return True

    def toggle_checkbox(self, block: QTextBlock) -> None:
        match = TASK_LINE_RE.match(block.text())
        if not match:
            return
        marker_pos = block.position() + len(match.group("indent"))
        cursor = QTextCursor(self.document())
        cursor.setPosition(marker_pos)
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
        checked = match.group("marker") == "☐"
        cursor.insertText("☑" if checked else "☐")
        updated_block = self.document().findBlock(marker_pos)
        self._apply_task_style(updated_block, checked=checked)
        self.taskStateChanged.emit()

    def _apply_task_style(self, block: QTextBlock, checked: bool) -> None:
        match = TASK_LINE_RE.match(block.text())
        if not match:
            return
        indent_len = len(match.group("indent"))
        marker_pos = block.position() + indent_len
        text_start = marker_pos + 1
        if block.text()[indent_len + 1 :].startswith(" "):
            text_start += 1

        marker_cursor = QTextCursor(self.document())
        marker_cursor.setPosition(marker_pos)
        marker_cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
        marker_fmt = QTextCharFormat()
        marker_fmt.setFontStrikeOut(False)
        marker_cursor.mergeCharFormat(marker_fmt)

        if text_start < block.position() + len(block.text()):
            text_cursor = QTextCursor(self.document())
            text_cursor.setPosition(text_start)
            text_cursor.setPosition(block.position() + len(block.text()), QTextCursor.MoveMode.KeepAnchor)
            text_fmt = QTextCharFormat()
            text_fmt.setFontStrikeOut(checked)
            text_cursor.mergeCharFormat(text_fmt)

    def toggle_bold(self) -> None:
        fmt = QTextCharFormat()
        current = self.textCursor().charFormat().fontWeight()
        fmt.setFontWeight(QFont.Weight.Normal if current >= QFont.Weight.Bold else QFont.Weight.Bold)
        self._merge_font_format(fmt)

    def toggle_italic(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self.textCursor().charFormat().fontItalic())
        self._merge_format(fmt)

    def toggle_underline(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not self.textCursor().charFormat().fontUnderline())
        self._merge_format(fmt)

    def toggle_strikethrough(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontStrikeOut(not self.textCursor().charFormat().fontStrikeOut())
        self._merge_format(fmt)

    def _merge_format(self, fmt: QTextCharFormat) -> None:
        cursor = self.textCursor()
        cursor.mergeCharFormat(fmt)
        self.mergeCurrentCharFormat(fmt)

    def _merge_font_format(self, fmt: QTextCharFormat) -> None:
        """Apply font properties without leaving task/list markers behind.

        Checkbox markers are ordinary document characters, while Qt bullet and
        numbered-list markers are block decorations.  When the cursor is on a
        decorated line we therefore update both the text fragments and the
        block character format used to paint the list marker.
        """
        visible_cursor = self.textCursor()
        start = visible_cursor.selectionStart()
        end = visible_cursor.selectionEnd()

        if visible_cursor.hasSelection():
            visible_cursor.mergeCharFormat(fmt)
            self._format_decorated_markers(start, end, fmt)
            self.setTextCursor(visible_cursor)
            self.mergeCurrentCharFormat(fmt)
            return

        block = visible_cursor.block()
        is_task = bool(TASK_LINE_RE.match(block.text()))
        is_list_item = block.textList() is not None
        if is_task or is_list_item:
            line_cursor = QTextCursor(self.document())
            line_cursor.setPosition(block.position())
            line_cursor.setPosition(block.position() + len(block.text()), QTextCursor.MoveMode.KeepAnchor)
            if line_cursor.hasSelection():
                line_cursor.mergeCharFormat(fmt)
            if is_list_item:
                block_cursor = QTextCursor(block)
                block_cursor.mergeBlockCharFormat(fmt)
            self.setTextCursor(visible_cursor)
            self.mergeCurrentCharFormat(fmt)
            return

        visible_cursor.mergeCharFormat(fmt)
        self.setTextCursor(visible_cursor)
        self.mergeCurrentCharFormat(fmt)

    def _format_decorated_markers(self, start: int, end: int, fmt: QTextCharFormat) -> None:
        document = self.document()
        block = document.findBlock(start)
        if end > start and document.findBlock(end).position() == end:
            last_position = max(start, end - 1)
        else:
            last_position = end
        last_block = document.findBlock(last_position)

        while block.isValid():
            task_match = TASK_LINE_RE.match(block.text())
            if task_match:
                marker_position = block.position() + len(task_match.group("indent"))
                marker_cursor = QTextCursor(document)
                marker_cursor.setPosition(marker_position)
                marker_cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
                marker_cursor.mergeCharFormat(fmt)
            if block.textList() is not None:
                block_cursor = QTextCursor(block)
                block_cursor.mergeBlockCharFormat(fmt)
            if block == last_block:
                break
            block = block.next()

    def set_heading(self, level: int) -> None:
        sizes = {0: self.base_font_size, 1: self.base_font_size + 10, 2: self.base_font_size + 6, 3: self.base_font_size + 3}
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        fmt = QTextCharFormat()
        fmt.setFontPointSize(sizes.get(level, self.base_font_size))
        fmt.setFontWeight(QFont.Weight.Bold if level else QFont.Weight.Normal)
        cursor.mergeCharFormat(fmt)

    def make_bullet_list(self) -> None:
        self._make_list(QTextListFormat.Style.ListDisc)

    def make_numbered_list(self) -> None:
        self._make_list(QTextListFormat.Style.ListDecimal)

    def _make_list(self, style: QTextListFormat.Style) -> None:
        cursor = self.textCursor()
        list_format = QTextListFormat()
        list_format.setStyle(style)
        current_list = cursor.currentList()
        if current_list is not None:
            list_format.setIndent(current_list.format().indent())
        else:
            list_format.setIndent(1)
        cursor.createList(list_format)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        modifiers = event.modifiers()

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.auto_checkbox_enabled and self._handle_task_enter():
                return
            if self.blank_line_after_enter:
                self._handle_spaced_enter(event)
                return

        if key == Qt.Key.Key_Tab and not (modifiers & Qt.KeyboardModifier.ControlModifier):
            if self._handle_task_indent(outdent=bool(modifiers & Qt.KeyboardModifier.ShiftModifier)):
                return

        if key == Qt.Key.Key_Backtab:
            if self._handle_task_indent(outdent=True):
                return

        super().keyPressEvent(event)

    def _handle_task_enter(self) -> bool:
        cursor = self.textCursor()
        if cursor.hasSelection():
            return False
        block = cursor.block()
        match = TASK_LINE_RE.match(block.text())
        if not match:
            return False

        text = (match.group("text") or "").strip()
        indent = match.group("indent")
        if not text:
            marker_start = block.position() + len(indent)
            remove_cursor = QTextCursor(self.document())
            remove_cursor.setPosition(marker_start)
            remove_cursor.setPosition(block.position() + len(block.text()), QTextCursor.MoveMode.KeepAnchor)
            remove_cursor.removeSelectedText()
            remove_cursor.setPosition(marker_start)
            self.setTextCursor(remove_cursor)
            return True

        checked = match.group("marker") == "☑"
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
        cursor.insertBlock()
        if self.blank_line_after_enter:
            cursor.insertBlock()
        cursor.insertText(f"{indent}☐ ")
        self.setTextCursor(cursor)
        self._apply_task_style(block, checked=checked)
        self._apply_task_style(cursor.block(), checked=False)
        reset_fmt = QTextCharFormat()
        reset_fmt.setFontStrikeOut(False)
        self.mergeCurrentCharFormat(reset_fmt)
        return True

    def _handle_spaced_enter(self, event: QKeyEvent) -> None:
        """Handle Enter as two native Enter presses, leaving one blank line."""
        super().keyPressEvent(event)
        cursor = self.textCursor()
        cursor.insertBlock()
        self.setTextCursor(cursor)

    def _handle_task_indent(self, outdent: bool) -> bool:
        cursor = self.textCursor()
        block = cursor.block()
        match = TASK_LINE_RE.match(block.text())
        if not match:
            return False
        block_start = block.position()
        old_pos = cursor.position()
        leading = match.group("indent")
        edit = QTextCursor(self.document())
        if outdent:
            remove_count = min(self.tab_spaces, len(leading))
            if remove_count == 0:
                return True
            edit.setPosition(block_start)
            edit.setPosition(block_start + remove_count, QTextCursor.MoveMode.KeepAnchor)
            edit.removeSelectedText()
            cursor.setPosition(max(block_start, old_pos - remove_count))
        else:
            edit.setPosition(block_start)
            edit.insertText(" " * self.tab_spaces)
            cursor.setPosition(old_pos + self.tab_spaces)
        self.setTextCursor(cursor)
        return True

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            cursor = self.cursorForPosition(event.position().toPoint())
            block = cursor.block()
            match = TASK_LINE_RE.match(block.text())
            if match:
                marker_index = len(match.group("indent"))
                relative = cursor.position() - block.position()
                if relative in {marker_index, marker_index + 1}:
                    self.toggle_checkbox(block)
                    event.accept()
                    return
        super().mousePressEvent(event)

    def contextMenuEvent(self, event) -> None:
        menu: QMenu = self.createStandardContextMenu()
        menu.addSeparator()
        add_checkbox = menu.addAction("Add / Toggle Checkbox")
        add_checkbox.triggered.connect(self.insert_checkbox)
        toggle_checked = menu.addAction("Toggle Checked")
        toggle_checked.setEnabled(bool(TASK_LINE_RE.match(self.textCursor().block().text())))
        toggle_checked.triggered.connect(self.toggle_checkbox_at_cursor)
        strike = menu.addAction("Strikethrough")
        strike.triggered.connect(self.toggle_strikethrough)
        menu.exec(event.globalPos())
````

## `app/widgets/sidebar.py`

````python
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models import NoteSummary


class NoteCard(QWidget):
    def __init__(self, note: NoteSummary, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(7, 5, 7, 5)
        layout.setSpacing(2)
        title = QLabel(note.title)
        title.setStyleSheet("font-weight: 600;")
        preview = QLabel(note.preview or "No content")
        preview.setWordWrap(False)
        preview.setStyleSheet("font-size: 11px;")
        date = QLabel(self._format_date(note.updated_at))
        date.setStyleSheet("font-size: 10px;")
        layout.addWidget(title)
        layout.addWidget(preview)
        layout.addWidget(date)

    @staticmethod
    def _format_date(value: str) -> str:
        try:
            dt = datetime.fromisoformat(value)
            return dt.astimezone().strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return value


class Sidebar(QWidget):
    noteSelected = Signal(int)
    newNoteRequested = Signal()
    trashRequested = Signal()
    renameRequested = Signal(int)
    duplicateRequested = Signal(int)
    deleteRequested = Signal(int)
    exportRequested = Signal(int)
    searchChanged = Signal(str)
    sortChanged = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(210)
        self.setMaximumWidth(520)
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(7)

        top = QHBoxLayout()
        label = QLabel("Notes")
        label.setStyleSheet("font-size: 15px; font-weight: 700;")
        new_button = QPushButton("+")
        new_button.setToolTip("New Note (Ctrl+N)")
        new_button.setFixedWidth(34)
        new_button.clicked.connect(self.newNoteRequested)
        top.addWidget(label)
        top.addStretch(1)
        top.addWidget(new_button)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search notes…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.searchChanged)

        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Recently edited", "updated")
        self.sort_combo.addItem("Alphabetical", "title")
        self.sort_combo.currentIndexChanged.connect(
            lambda _index: self.sortChanged.emit(str(self.sort_combo.currentData()))
        )

        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._show_context_menu)
        self.list.currentItemChanged.connect(self._on_current_changed)

        trash = QPushButton("Trash")
        trash.setToolTip("Restore or permanently delete notes")
        trash.clicked.connect(self.trashRequested)

        root.addLayout(top)
        root.addWidget(self.search)
        root.addWidget(self.sort_combo)
        root.addWidget(self.list, 1)
        root.addWidget(trash)

    def set_notes(self, notes: list[NoteSummary], selected_id: int | None = None) -> None:
        self.list.blockSignals(True)
        self.list.clear()
        selected_item: QListWidgetItem | None = None
        for note in notes:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, note.id)
            card = NoteCard(note)
            item.setSizeHint(card.sizeHint())
            self.list.addItem(item)
            self.list.setItemWidget(item, card)
            if note.id == selected_id:
                selected_item = item
        if selected_item is not None:
            self.list.setCurrentItem(selected_item)
        self.list.blockSignals(False)

    def select_note(self, note_id: int) -> None:
        for index in range(self.list.count()):
            item = self.list.item(index)
            if int(item.data(Qt.ItemDataRole.UserRole)) == note_id:
                self.list.setCurrentItem(item)
                self.list.scrollToItem(item)
                return

    def _on_current_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is not None:
            self.noteSelected.emit(int(current.data(Qt.ItemDataRole.UserRole)))

    def _show_context_menu(self, pos) -> None:
        item = self.list.itemAt(pos)
        if item is None:
            return
        note_id = int(item.data(Qt.ItemDataRole.UserRole))
        menu = QMenu(self)
        rename = menu.addAction("Rename")
        duplicate = menu.addAction("Duplicate")
        export = menu.addAction("Export TXT")
        menu.addSeparator()
        delete = menu.addAction("Delete to Trash")
        chosen = menu.exec(self.list.mapToGlobal(pos))
        if chosen == rename:
            self.renameRequested.emit(note_id)
        elif chosen == duplicate:
            self.duplicateRequested.emit(note_id)
        elif chosen == export:
            self.exportRequested.emit(note_id)
        elif chosen == delete:
            self.deleteRequested.emit(note_id)
````

## `build.ps1`

````powershell
param(
    [switch]$SkipInstall,
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

function Fail([string]$Message) {
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

try {
    $VersionText = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
} catch {
    Fail "Python was not found. Install 64-bit Python 3.12 or newer and reopen PowerShell."
}

$Parts = $VersionText.Trim().Split('.')
if ([int]$Parts[0] -lt 3 -or ([int]$Parts[0] -eq 3 -and [int]$Parts[1] -lt 12)) {
    Fail "Python 3.12+ is required. Found $VersionText."
}

$Architecture = python -c "import platform; print(platform.architecture()[0])"
if ($Architecture.Trim() -ne "64bit") {
    Write-Host "WARNING: You are not building with 64-bit Python. For normal Windows 10/11 distribution, 64-bit Python is recommended." -ForegroundColor Yellow
}

if (-not $SkipInstall) {
    Write-Host "Installing/updating project dependencies..."
    python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { Fail "pip upgrade failed." }
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { Fail "Dependency installation failed." }
}

python -c "import PySide6, PyInstaller; print('PySide6', PySide6.__version__, '| PyInstaller', PyInstaller.__version__)"
if ($LASTEXITCODE -ne 0) { Fail "PySide6 or PyInstaller is unavailable in the active Python environment." }

Write-Host "Running tests..."
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest -q
if ($LASTEXITCODE -ne 0) { Fail "Tests failed. Build stopped to avoid packaging a broken release." }
Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue

foreach ($Folder in @("build", "dist")) {
    if (Test-Path $Folder) {
        Write-Host "Removing old $Folder folder..."
        Remove-Item -Recurse -Force $Folder
    }
}

if ($OneFile) {
    Write-Host "Building single-file DevNest.exe with PyInstaller..."
    python -m PyInstaller --noconfirm --clean DevNest.spec -- --onefile
    if ($LASTEXITCODE -ne 0) { Fail "PyInstaller one-file build failed. Review the output above." }
    $Exe = Join-Path $ProjectRoot "dist\DevNest.exe"
} else {
    Write-Host "Building DevNest onedir package with PyInstaller..."
    python -m PyInstaller --noconfirm --clean DevNest.spec
    if ($LASTEXITCODE -ne 0) { Fail "PyInstaller onedir build failed. Review the output above." }
    $Exe = Join-Path $ProjectRoot "dist\DevNest\DevNest.exe"
}

if (-not (Test-Path $Exe)) {
    Fail "Build completed without the expected executable: $Exe"
}

Write-Host ""
Write-Host "Build successful." -ForegroundColor Green
Write-Host "Executable: $Exe"
if ($OneFile) {
    Write-Host "You can distribute dist\DevNest.exe as a single file."
} else {
    Write-Host "For maximum reliability, distribute the ENTIRE dist\DevNest folder."
}
Write-Host "User notes remain in Windows AppData, not beside the executable."
````

## `DevNest.spec`

````python
# -*- mode: python ; coding: utf-8 -*-
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--onefile", action="store_true")
options, _unknown = parser.parse_known_args()

project_root = Path(SPECPATH)

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[(str(project_root / "resources"), "resources")],
    hiddenimports=["PySide6.QtSvg"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

common = dict(
    name="DevNest",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "resources" / "devnest.ico"),
)

if options.onefile:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        upx_exclude=[],
        runtime_tmpdir=None,
        **common,
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        **common,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="DevNest",
    )
````

## `main.py`

````python
from __future__ import annotations

import logging
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from app.constants import APP_NAME, ORGANIZATION_DOMAIN, ORGANIZATION_NAME, VERSION
from app.database import Database, DatabaseError
from app.main_window import MainWindow
from app.paths import resource_path
from app.services.logging_setup import configure_logging
from app.settings import SettingsManager
from app.themes.theme_manager import ThemeManager


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(VERSION)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setOrganizationDomain(ORGANIZATION_DOMAIN)
    app.setDesktopFileName("devnest")

    icon_path = resource_path("resources/devnest.svg")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    configure_logging()
    logger = logging.getLogger(__name__)

    try:
        database = Database()
    except DatabaseError as exc:
        logger.exception("Application startup failed")
        QMessageBox.critical(None, "DevNest — Database Error", str(exc))
        return 1

    settings = SettingsManager()
    theme_manager = ThemeManager(app)
    window = MainWindow(database, settings, theme_manager)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
````

## `pytest.ini`

````ini
[pytest]
pythonpath = .
testpaths = tests
````

## `README.md`

````markdown
<p align="center">
  <img src="resources/devnest.svg" alt="DevNest" width="96" height="96">
</p>

<h1 align="center">DevNest</h1>

<p align="center">
  <strong>Notes, tasks and lightweight diagrams for developers.</strong><br>
  Native desktop app for Windows · Offline-first · No account · No telemetry
</p>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-1.2.4-2f81f7?style=flat-square">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="PySide6" src="https://img.shields.io/badge/PySide6-Qt%206-41CD52?style=flat-square&logo=qt&logoColor=white">
  <img alt="Platform" src="https://img.shields.io/badge/Windows-10%20%2F%2011-0078D4?style=flat-square&logo=windows11&logoColor=white">
  <img alt="Offline" src="https://img.shields.io/badge/offline-ready-555?style=flat-square">
</p>

<p align="center">
  <a href="https://github.com/Onur-Aba/notepad-for-developers/releases/latest/download/DevNest.exe">
    <strong>⬇ Download DevNest.exe</strong>
  </a>
  &nbsp;·&nbsp;
  <a href="https://github.com/Onur-Aba/notepad-for-developers/releases/latest">Latest Release</a>
  &nbsp;·&nbsp;
  <a href="#turkce">Türkçe</a>
  &nbsp;·&nbsp;
  <a href="#english">English</a>
</p>

> **Windows users:** If you only want to use the application, you do not need to install the source code. Download `DevNest.exe` using the **Download DevNest.exe** button above and run it directly.
>
> **Windows kullanıcıları:** Sadece programı kullanmak istiyorsanız kaynak kodu kurmanıza gerek yok. Yukarıdaki **Download DevNest.exe** bağlantısından `DevNest.exe` dosyasını indirip doğrudan çalıştırabilirsiniz.

---

<a id="turkce"></a>

# 🇹🇷 Türkçe

## DevNest nedir?

DevNest; notlarını, yapılacak işlerini, teknik fikirlerini ve küçük yazılım diyagramlarını tek yerde tutmak isteyen geliştiriciler için hazırlanmış native bir masaüstü uygulamasıdır.

Tarayıcı açmaz, hesap istemez ve notlarınızı herhangi bir sunucuya göndermez. Veriler yerel SQLite veritabanında saklanır; arayüz PySide6 / Qt ile çalışır.

### Öne çıkan özellikler

| Alan | Özellikler |
|---|---|
| **Notlar** | Hızlı not oluşturma, arama, yeniden adlandırma, çoğaltma, sıralama |
| **Editör** | Bold, italic, underline, strikethrough, listeler, font / boyut / kalınlık kontrolleri; checkbox ve liste marker'ları da font ayarlarını takip eder |
| **Todo** | Tıklanabilir `☐ / ☑` görevler, otomatik üstü çizme, Auto Checkbox, nested task desteği, isteğe bağlı Enter sonrası boş satır |
| **TXT** | `[ ]`, `[x]`, `[X]`, `☐`, `☑`, `✓` algılama; UTF-8 import/export |
| **Diagram** | Sürükleyerek boyutlandırılan şekiller, text, yönlü connector, zoom, pan, resize |
| **Temalar** | Matte Black, Midnight Slate, Graphite, Clean Light, Soft Gray, Warm Paper, Cool Mist, System |
| **Veri güvenliği** | Autosave, Trash, Restore, kalıcı silme, SQLite `VACUUM` |
| **Gizlilik** | Offline çalışma, login yok, telemetry yok, zorunlu cloud servisi yok |

## Hızlı indirme

Kaynak kodla uğraşmadan yalnızca uygulamayı kullanmak istiyorsanız hazır Windows executable dosyasını indirebilirsiniz:

<p align="center">
  <a href="https://github.com/Onur-Aba/notepad-for-developers/releases/latest/download/DevNest.exe">
    <strong>⬇ DevNest.exe indir</strong>
  </a>
</p>

Bu bağlantı repository içindeki büyük binary dosya önizleme sayfasına değil, GitHub Releases üzerindeki en güncel `DevNest.exe` dosyasına gider.

> PyInstaller build'i gerekli Python runtime ve Qt bileşenlerini paketler. Hedef Windows bilgisayarda ayrıca Python veya PySide6 kurulu olması gerekmez.

## Checkbox kullanımı

Bir satırı görev haline getirmek için toolbar'daki checkbox düğmesini veya <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>X</kbd> kullanabilirsiniz.

```text
☐ API endpointlerini hazırla
☐ Database bağlantısını oluştur
☑ Login ekranını tamamla
```

İşaretlenen görevlerin metni otomatik olarak üstü çizili hale gelir. İşaret kaldırıldığında strikethrough da kaldırılır.

**Auto Checkbox** açıkken dolu bir görev satırında <kbd>Enter</kbd> yeni bir checkbox satırı oluşturur. Boş checkbox satırında tekrar <kbd>Enter</kbd> normal metne döner. <kbd>Tab</kbd> / <kbd>Shift</kbd> + <kbd>Tab</kbd> ile görev seviyesini değiştirebilirsiniz.

## TXT içe / dışa aktarma

DevNest aşağıdaki biçimlerin tamamını tanır:

```text
[ ] Backend
[x] Database
[X] Authentication
☐ Frontend
☑ Login
✓ Deploy
```

Dışa aktarılan checklist'ler taşınabilir bir biçimde yazılır:

```text
[ ] Backend
    [ ] API
    [x] Database
```

TXT formatı bold / italic gibi rich-text özelliklerini taşımaz. Bu biçimler uygulamanın SQLite veritabanındaki native not içeriğinde korunur.

## Diagram kullanımı

Diagram alanı her not için ayrı saklanır.

- **Square** — sol mouse tuşuna basılı tutup sürükleyerek istediğiniz genişlik ve yükseklikte kutu oluşturur.
- **Round** — yuvarlatılmış dikdörtgen oluşturur.
- **Ellipse** — elips / oval oluşturur.
- **Diamond** — karar / akış diyagramı şekli oluşturur.
- **Text** — bağımsız metin öğesi ekler.
- **Connect** — bir nesnenin üzerinde başlayıp başka bir nesnenin üzerinde biten yönlü bağlantı çizer.
- **Select** — nesneleri taşır; seçilen shape'in kenar ve köşe tutamaçlarıyla boyutunu değiştirir.
- **Orta mouse tuşu + sürükleme** — aktif araçtan bağımsız olarak canvas üzerinde gezinir.
- **Mouse wheel** — zoom yapar.

Connector yalnızca geçerli bir nesneden başlayıp başka bir geçerli nesnede bitebilir. Boş canvas'a bırakılan bağlantı kaydedilmez. Ok başı bağlantının yönünü gösterir.

## Temalar

DevNest farklı çalışma ortamlarına uygun tema seçenekleri sunar.

### Dark

- Matte Black
- Midnight Slate
- Graphite

### Light

- Clean Light
- Soft Gray
- Warm Paper
- Cool Mist

### System

İşletim sisteminin renk tercihine göre görünüm uygular.

Seçilen tema QSettings ile kaydedilir ve uygulama tekrar açıldığında geri yüklenir.

## Klavye kısayolları

| İşlem | Kısayol |
|---|---|
| Yeni not | <kbd>Ctrl</kbd> + <kbd>N</kbd> |
| Not içinde bul | <kbd>Ctrl</kbd> + <kbd>F</kbd> |
| Geri al | <kbd>Ctrl</kbd> + <kbd>Z</kbd> |
| Yinele | <kbd>Ctrl</kbd> + <kbd>Y</kbd> |
| Bold | <kbd>Ctrl</kbd> + <kbd>B</kbd> |
| Italic | <kbd>Ctrl</kbd> + <kbd>I</kbd> |
| Underline | <kbd>Ctrl</kbd> + <kbd>U</kbd> |
| Checkbox | <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>X</kbd> |
| TXT export | <kbd>Ctrl</kbd> + <kbd>E</kbd> |
| Sidebar aç / kapat | <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>B</kbd> |
| Editor | <kbd>Ctrl</kbd> + <kbd>1</kbd> |
| Diagram | <kbd>Ctrl</kbd> + <kbd>2</kbd> |
| Diagram öğesini çoğalt | <kbd>Ctrl</kbd> + <kbd>D</kbd> |
| Seçili diagram öğesini sil | <kbd>Delete</kbd> |

## Kaynak koddan çalıştırma

### Gereksinimler

- Windows 10 / 11
- Python 3.12+
- PowerShell

Repository'yi indirdikten sonra proje klasöründe PowerShell açın.

```powershell
python --version
```

Virtual environment oluşturun:

```powershell
python -m venv .venv
```

Aktifleştirin:

```powershell
.\.venv\Scripts\Activate.ps1
```

PowerShell izin vermezse yalnızca mevcut terminal oturumu için:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

Bağımlılıkları kurun:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Testleri çalıştırın:

```powershell
python -m pytest -q
```

Uygulamayı başlatın:

```powershell
python main.py
```

## Windows EXE oluşturma

Projede hazır `build.ps1` ve `DevNest.spec` bulunur.

### Klasörlü build

Geliştirme ve ilk dağıtım testi için:

```powershell
.\build.ps1
```

Çıktı:

```text
dist\DevNest\DevNest.exe
```

Bu build tipinde `dist\DevNest` klasörünün tamamını dağıtmanız gerekir.

### Tek dosya EXE

Tek `DevNest.exe` üretmek için:

```powershell
.\build.ps1 -OneFile
```

Çıktı:

```text
dist\DevNest.exe
```

GitHub Releases'a yüklenecek dosya bu tek dosyalık build olabilir.

## GitHub Release yayınlama

Yeni bir sürüm yayınlarken:

1. GitHub repository sayfasında **Releases** bölümünü açın.
2. **Draft a new release** seçin.
3. Örneğin `v1.2.4` şeklinde bir tag oluşturun.
4. Release başlığını örneğin `DevNest 1.2.4` yapın.
5. `dist\DevNest.exe` dosyasını release asset olarak yükleyin.
6. Release'i yayınlayın.

README'deki indirme bağlantısı:

```text
https://github.com/Onur-Aba/notepad-for-developers/releases/latest/download/DevNest.exe
```

olduğu için sonraki sürümlerde README bağlantısını değiştirmeniz gerekmez. Release asset adı `DevNest.exe` olarak kaldığı sürece buton en güncel release dosyasını indirir.

## Veriler nerede saklanıyor?

DevNest kullanıcı verisini executable'ın yanına yazmak zorunda değildir. SQLite veritabanı Qt'nin application-data konumunda tutulur.

Kesin veritabanı yolunu **Help → About DevNest** ekranında görebilirsiniz.

Loglar aynı application-data alanındaki `logs` klasöründe tutulur.

### Yedekleme

Yedek almadan önce DevNest'i kapatın ve `devnest.db` dosyasını güvenli bir konuma kopyalayın.

### Windows SmartScreen

İmzalanmamış yeni executable dosyalarında Windows SmartScreen uyarısı görülebilir. Uygulamayı geniş çapta dağıtacaksanız `DevNest.exe` dosyasını bir code-signing sertifikasıyla imzalamak daha profesyonel bir dağıtım sağlar.

---

<a id="english"></a>

# 🇬🇧 English

## What is DevNest?

DevNest is a native desktop workspace for developers who want notes, checklists, technical ideas and lightweight software diagrams in one place.

It does not require a browser, an account or a network connection. Notes stay on your machine in a local SQLite database, while the interface is built with PySide6 / Qt.

### Highlights

| Area | Features |
|---|---|
| **Notes** | Fast note creation, search, rename, duplicate and sorting |
| **Editor** | Bold, italic, underline, strikethrough, lists, font / size / weight controls; checkbox and list markers follow font formatting |
| **Tasks** | Clickable `☐ / ☑` items, automatic strikethrough, Auto Checkbox and nested tasks |
| **TXT** | `[ ]`, `[x]`, `[X]`, `☐`, `☑`, `✓` detection with UTF-8 import/export |
| **Diagrams** | Drag-to-size shapes, text, directional connectors, zoom, pan and resize |
| **Themes** | Matte Black, Midnight Slate, Graphite, Clean Light, Soft Gray, Warm Paper, Cool Mist and System |
| **Data safety** | Autosave, Trash, Restore, permanent delete and SQLite `VACUUM` |
| **Privacy** | Offline operation, no login, no telemetry and no mandatory cloud service |

## Quick download

If you only want to use DevNest and do not need the source code, download the ready-to-run Windows executable:

<p align="center">
  <a href="https://github.com/Onur-Aba/notepad-for-developers/releases/latest/download/DevNest.exe">
    <strong>⬇ Download DevNest.exe</strong>
  </a>
</p>

This link goes directly to the latest `DevNest.exe` asset published under GitHub Releases instead of opening GitHub's large binary file preview page.

> The PyInstaller build bundles the required Python runtime and Qt components. Python and PySide6 do not need to be installed separately on the target Windows machine.

## Checklists

Use the checkbox toolbar action or <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>X</kbd> to turn a line into a task.

```text
☐ Prepare API endpoints
☐ Create database connection
☑ Finish login screen
```

Completed tasks are struck through automatically. Unchecking a task removes the strikethrough.

With **Auto Checkbox** enabled, pressing <kbd>Enter</kbd> after a non-empty task creates another task with the same indentation. Pressing <kbd>Enter</kbd> on an empty task exits checklist mode. Use <kbd>Tab</kbd> and <kbd>Shift</kbd> + <kbd>Tab</kbd> for nesting.

## TXT import / export

DevNest recognizes all of the following forms:

```text
[ ] Backend
[x] Database
[X] Authentication
☐ Frontend
☑ Login
✓ Deploy
```

Portable TXT export uses:

```text
[ ] Backend
    [ ] API
    [x] Database
```

TXT cannot retain rich formatting such as bold or italic. DevNest keeps the native rich-text version in SQLite so formatting remains intact inside the application.

## Diagrams

Each note has its own diagram workspace.

- **Square** — press and drag to create a box at the exact width and height you want.
- **Round** — create a rounded rectangle.
- **Ellipse** — create an ellipse / oval.
- **Diamond** — create a decision / flowchart shape.
- **Text** — add a standalone text element.
- **Connect** — draw a directional connection from one existing object to another.
- **Select** — move objects and resize selected shapes using edge and corner handles.
- **Middle mouse button + drag** — pan the canvas regardless of the active tool.
- **Mouse wheel** — zoom.

A connector must start on a valid object and end on a different valid object. Connections released onto empty canvas are discarded. The arrowhead marks the target direction.

## Themes

DevNest includes several appearance presets for different environments.

### Dark

- Matte Black
- Midnight Slate
- Graphite

### Light

- Clean Light
- Soft Gray
- Warm Paper
- Cool Mist

### System

Follows the operating system color preference.

The selected theme is stored with QSettings and restored on the next launch.

## Keyboard shortcuts

| Action | Shortcut |
|---|---|
| New note | <kbd>Ctrl</kbd> + <kbd>N</kbd> |
| Find in note | <kbd>Ctrl</kbd> + <kbd>F</kbd> |
| Undo | <kbd>Ctrl</kbd> + <kbd>Z</kbd> |
| Redo | <kbd>Ctrl</kbd> + <kbd>Y</kbd> |
| Bold | <kbd>Ctrl</kbd> + <kbd>B</kbd> |
| Italic | <kbd>Ctrl</kbd> + <kbd>I</kbd> |
| Underline | <kbd>Ctrl</kbd> + <kbd>U</kbd> |
| Checkbox | <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>X</kbd> |
| Export TXT | <kbd>Ctrl</kbd> + <kbd>E</kbd> |
| Toggle sidebar | <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>B</kbd> |
| Editor | <kbd>Ctrl</kbd> + <kbd>1</kbd> |
| Diagram | <kbd>Ctrl</kbd> + <kbd>2</kbd> |
| Duplicate diagram item | <kbd>Ctrl</kbd> + <kbd>D</kbd> |
| Delete selected diagram item | <kbd>Delete</kbd> |

## Run from source

### Requirements

- Windows 10 / 11
- Python 3.12+
- PowerShell

Open PowerShell in the project directory and verify Python:

```powershell
python --version
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script activation for the current session:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run the test suite:

```powershell
python -m pytest -q
```

Start DevNest:

```powershell
python main.py
```

## Build a Windows executable

The repository includes `build.ps1` and `DevNest.spec`.

### Folder build

Recommended for development and initial distribution testing:

```powershell
.\build.ps1
```

Output:

```text
dist\DevNest\DevNest.exe
```

Distribute the complete `dist\DevNest` directory when using this mode.

### Single-file EXE

To create one standalone executable:

```powershell
.\build.ps1 -OneFile
```

Output:

```text
dist\DevNest.exe
```

This single-file build can be uploaded as the GitHub Release asset.

## Publishing a GitHub Release

When publishing a new version:

1. Open **Releases** in the GitHub repository.
2. Select **Draft a new release**.
3. Create a tag such as `v1.2.4`.
4. Use a release title such as `DevNest 1.2.4`.
5. Upload `dist\DevNest.exe` as a release asset.
6. Publish the release.

The README download button points to:

```text
https://github.com/Onur-Aba/notepad-for-developers/releases/latest/download/DevNest.exe
```

As long as the release asset remains named `DevNest.exe`, the README button automatically downloads the executable from the latest published release. You do not need to update the README link for every version.

## Where is the data stored?

DevNest does not require user data to be stored next to the executable. The SQLite database is stored under Qt's application-data location for the current Windows user.

The exact database path is shown under **Help → About DevNest**.

Log files are stored in the `logs` directory inside the same application-data area.

### Backup

Close DevNest before creating a backup, then copy `devnest.db` to a safe location.

### Windows SmartScreen

Windows SmartScreen may warn about a newly distributed unsigned executable. If DevNest is distributed publicly, signing `DevNest.exe` with a code-signing certificate provides a more professional Windows distribution experience.

---

## Technology

```text
Python 3.12+
PySide6 / Qt 6
SQLite
QSettings
PyInstaller
```

DevNest is designed to work locally without a web server, browser frontend, mandatory cloud account or telemetry.

<p align="center">
  <sub>DevNest 1.2.4 · Native desktop workspace for everyday development notes and planning.</sub>
</p>
````

## `requirements.txt`

````text
PySide6==6.11.2
PyInstaller==6.22.2
pytest>=8.3,<10
````

## `resources/devnest.svg`

````xml
<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <rect x="16" y="16" width="224" height="224" rx="48" fill="#273043"/>
  <path d="M68 76h120v22H68zm0 42h88v22H68zm0 42h120v22H68z" fill="#F3F5F7"/>
  <path d="M174 112l18 18-18 18" fill="none" stroke="#7AA2F7" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
````

## `tests/test_database.py`

````python
from __future__ import annotations

from pathlib import Path

from app.database import Database


def test_database_crud_and_search(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.db")
    try:
        note = db.create_note("API Plan", "<p>Hello</p>", "Hello endpoint")
        loaded = db.get_note(note.id)
        assert loaded is not None
        assert loaded.title == "API Plan"

        db.update_note(note.id, "API Plan v2", "<p>Updated</p>", "Database Redis")
        loaded = db.get_note(note.id)
        assert loaded is not None
        assert loaded.title == "API Plan v2"
        assert loaded.content_plain == "Database Redis"
        assert [item.id for item in db.list_notes("redis")] == [note.id]
    finally:
        db.close()


def test_soft_delete_restore_and_permanent_delete_cascade(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.db")
    try:
        note = db.create_note("Disposable")
        db.save_diagram(note.id, {"items": [{"id": "n1"}], "edges": [], "paths": []})

        db.soft_delete_note(note.id)
        assert db.get_note(note.id) is None
        assert db.get_note(note.id, include_deleted=True) is not None
        assert [item.id for item in db.list_trash()] == [note.id]

        db.restore_note(note.id)
        assert db.get_note(note.id) is not None
        assert db.get_diagram(note.id)["items"] == [{"id": "n1"}]

        db.soft_delete_note(note.id)
        db.permanently_delete_note(note.id)
        assert db.get_note(note.id, include_deleted=True) is None
        count = db.connection.execute("SELECT COUNT(*) FROM diagrams WHERE note_id = ?", (note.id,)).fetchone()[0]
        assert count == 0
    finally:
        db.close()


def test_duplicate_copies_diagram(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.db")
    try:
        note = db.create_note("Original", "<p>Body</p>", "Body")
        diagram = {"items": [{"type": "node", "id": "a", "x": 1, "y": 2, "text": "API"}], "edges": [], "paths": []}
        db.save_diagram(note.id, diagram)
        copy = db.duplicate_note(note.id)
        assert copy.title == "Original Copy"
        assert copy.content_html == note.content_html
        assert db.get_diagram(copy.id) == diagram
    finally:
        db.close()


def test_empty_trash_returns_deleted_count(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.db")
    try:
        a = db.create_note("A")
        b = db.create_note("B")
        db.soft_delete_note(a.id)
        db.soft_delete_note(b.id)
        assert db.empty_trash() == 2
        assert db.list_trash() == []
    finally:
        db.close()
````

## `tests/test_diagram.py`

````python
from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6.QtWidgets")

from PySide6.QtCore import QPointF
from PySide6.QtGui import QPainterPath
from PySide6.QtWidgets import QApplication

from app.widgets.diagram_view import DiagramConnector, DiagramFreehand, DiagramScene, DiagramShape, DiagramView


@pytest.fixture(scope="module")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_shape_types_connections_and_round_trip(app: QApplication) -> None:
    scene = DiagramScene()
    first = scene.add_shape("square", QPointF(10, 20), "Frontend")
    second = scene.add_shape("diamond", QPointF(260, 30), "API?")
    third = scene.add_shape("ellipse", QPointF(500, 20), "Database")
    scene.add_edge(first, second)
    scene.add_edge(second, third)

    data = scene.to_data()
    shapes = [item for item in data["items"] if item["type"] == "shape"]
    assert {item["shape"] for item in shapes} == {"square", "diamond", "ellipse"}
    assert len(data["edges"]) == 2

    restored = DiagramScene()
    restored.load_data(data)
    restored_data = restored.to_data()
    assert len(restored_data["items"]) == 3
    assert len(restored_data["edges"]) == 2


def test_old_rectangle_node_data_is_backward_compatible(app: QApplication) -> None:
    scene = DiagramScene()
    scene.load_data(
        {
            "items": [{"type": "node", "id": "old", "x": 1, "y": 2, "text": "Legacy"}],
            "edges": [],
            "paths": [],
        }
    )
    shapes = [item for item in scene.items() if isinstance(item, DiagramShape)]
    assert len(shapes) == 1
    assert shapes[0].shape_type == "rect"
    assert shapes[0].text == "Legacy"


def _freehand_box(x: float, y: float, size: float = 80.0) -> QPainterPath:
    path = QPainterPath(QPointF(x, y))
    path.lineTo(x + size, y)
    path.lineTo(x + size, y + size)
    path.lineTo(x, y + size)
    path.lineTo(x, y)
    return path


def test_freehand_objects_are_connectable_and_round_trip(app: QApplication) -> None:
    scene = DiagramScene()
    first = scene.add_freehand_path(_freehand_box(10, 10))
    second = scene.add_freehand_path(_freehand_box(260, 40))

    route = QPainterPath(QPointF(90, 50))
    route.lineTo(140, 20)
    route.lineTo(210, 100)
    route.lineTo(260, 80)
    scene.add_connector_path(route, source_id=first.item_id, target_id=second.item_id)

    data = scene.to_data()
    assert data["version"] == 5
    assert len(data["paths"]) == 2
    assert all("id" in path for path in data["paths"])
    assert len(data["connectors"]) == 1
    assert data["connectors"][0]["source"] == first.item_id
    assert data["connectors"][0]["target"] == second.item_id

    restored = DiagramScene()
    restored.load_data(data)
    freehands = [item for item in restored.items() if isinstance(item, DiagramFreehand)]
    connectors = [item for item in restored.items() if isinstance(item, DiagramConnector)]
    assert len(freehands) == 2
    assert len(connectors) == 1
    assert connectors[0].source_id != connectors[0].target_id
    assert connectors[0].path().elementCount() == 4


def test_floating_connector_is_rejected(app: QApplication) -> None:
    scene = DiagramScene()
    path = QPainterPath(QPointF(10, 10))
    path.lineTo(100, 100)
    with pytest.raises(ValueError):
        scene.add_connector_path(path)


def test_freehand_connection_point_uses_drawn_contour_not_center(app: QApplication) -> None:
    scene = DiagramScene()
    freehand = scene.add_freehand_path(_freehand_box(0, 0, 100))
    point = scene._connection_point(freehand, QPointF(180, 50))
    assert point.x() == pytest.approx(100.0)
    assert point != freehand.sceneBoundingRect().center()


def test_square_is_drag_creation_tool_and_freehand_draw_is_removed(app: QApplication) -> None:
    view = DiagramView()
    assert "shape:square" in view._mode_buttons
    assert "shape:rect" not in view._mode_buttons
    assert "draw" not in view._mode_buttons
    assert "connect" in view._mode_buttons
    assert view.scene.mode == "shape:square"


def test_shape_size_persists_and_can_be_changed(app: QApplication) -> None:
    scene = DiagramScene()
    shape = scene.add_shape("ellipse", QPointF(20, 30), "Service", width=240, height=110)
    assert shape.width == pytest.approx(240.0)
    assert shape.height == pytest.approx(110.0)

    shape.set_size(310, 150)
    data = scene.to_data()
    assert data["version"] == 5
    raw = next(item for item in data["items"] if item["id"] == shape.item_id)
    assert raw["width"] == pytest.approx(310.0)
    assert raw["height"] == pytest.approx(150.0)

    restored = DiagramScene()
    restored.load_data(data)
    restored_shape = next(item for item in restored.items() if isinstance(item, DiagramShape))
    assert restored_shape.width == pytest.approx(310.0)
    assert restored_shape.height == pytest.approx(150.0)


def test_shape_preview_requires_drag_and_uses_dragged_size(app: QApplication) -> None:
    scene = DiagramScene()
    scene._begin_shape_preview("square", QPointF(10, 10))
    assert scene._finish_shape_preview(QPointF(12, 12)) is None
    assert not any(isinstance(item, DiagramShape) for item in scene.items())

    scene._begin_shape_preview("square", QPointF(20, 30))
    created = scene._finish_shape_preview(QPointF(260, 145))
    assert created is not None
    assert created.width == pytest.approx(240.0)
    assert created.height == pytest.approx(115.0)


def test_resize_from_handle_changes_shape_bounds(app: QApplication) -> None:
    scene = DiagramScene()
    shape = scene.add_shape("rounded", QPointF(100, 100), width=160, height=80)
    shape.resize_from_handle("se", QPointF(340, 250))
    assert shape.width == pytest.approx(240.0)
    assert shape.height == pytest.approx(150.0)
````

## `tests/test_editor.py`

````python
from __future__ import annotations

import pytest

pytest.importorskip("PySide6.QtWidgets")
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication

from app.services.txt_codec import import_text_to_html
from app.widgets.note_editor import NoteEditor


@pytest.fixture(scope="module")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _character_strike_out(editor: NoteEditor, position: int) -> bool:
    """Return the format of the character that starts at *position*.

    QTextCursor.charFormat() at a bare boundary position describes the cursor's
    insertion format and can reflect the character immediately before it.
    Selecting the character makes the assertion deterministic across Qt builds.
    """
    cursor = QTextCursor(editor.document())
    cursor.setPosition(position)
    cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
    return cursor.charFormat().fontStrikeOut()


def test_checkbox_toggle_applies_and_removes_strike(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("☐ API'yi hazırla")
    block = editor.document().firstBlock()
    editor.toggle_checkbox(block)
    assert editor.toPlainText().startswith("☑")

    checked_block = editor.document().firstBlock()
    first_task_char = checked_block.position() + 2
    last_task_char = checked_block.position() + len(checked_block.text()) - 1
    assert _character_strike_out(editor, first_task_char) is True
    assert _character_strike_out(editor, last_task_char) is True

    editor.toggle_checkbox(checked_block)
    assert editor.toPlainText().startswith("☐")
    unchecked_block = editor.document().firstBlock()
    first_task_char = unchecked_block.position() + 2
    last_task_char = unchecked_block.position() + len(unchecked_block.text()) - 1
    assert _character_strike_out(editor, first_task_char) is False
    assert _character_strike_out(editor, last_task_char) is False


def test_imported_checkbox_html_stays_recognizable(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setHtml(import_text_to_html("    [x] Database\n[ ] API"))
    assert editor.toPlainText().splitlines() == ["    ☑ Database", "☐ API"]


def test_auto_checkbox_enter_continues_task(app: QApplication) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor = NoteEditor()
    editor.set_auto_checkbox(True)
    editor.setPlainText("☐ Backend")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText() == "☐ Backend\n☐ "


def test_empty_auto_checkbox_enter_exits_task_mode(app: QApplication) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor = NoteEditor()
    editor.set_auto_checkbox(True)
    editor.setPlainText("☐ ")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText() == ""


def test_font_controls_apply_rich_text_formatting(app: QApplication) -> None:
    from PySide6.QtGui import QFont

    editor = NoteEditor()
    editor.setPlainText("format me")
    cursor = editor.textCursor()
    cursor.select(QTextCursor.SelectionType.Document)
    editor.setTextCursor(cursor)
    family = editor.font().family()
    editor.apply_font_family(family)
    editor.apply_font_point_size(18)
    editor.apply_font_weight(800)

    fmt = editor.textCursor().charFormat()
    assert round(fmt.fontPointSize()) == 18
    assert int(fmt.fontWeight()) == int(QFont.Weight.ExtraBold)
    assert family in fmt.font().families() or fmt.font().family() == family



def _character_format(editor: NoteEditor, position: int):
    cursor = QTextCursor(editor.document())
    cursor.setPosition(position)
    cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
    return cursor.charFormat()


def test_font_controls_apply_to_checkbox_marker_and_whole_task_line(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("☐ API endpoint")
    cursor = editor.textCursor()
    cursor.setPosition(len("☐ API"))
    editor.setTextCursor(cursor)

    editor.apply_font_point_size(20)
    editor.apply_font_weight(700)

    block = editor.document().firstBlock()
    marker_fmt = _character_format(editor, block.position())
    text_fmt = _character_format(editor, block.position() + 2)
    assert round(marker_fmt.fontPointSize()) == 20
    assert round(text_fmt.fontPointSize()) == 20
    assert int(marker_fmt.fontWeight()) == 700
    assert int(text_fmt.fontWeight()) == 700


def test_font_controls_apply_to_bullet_list_marker_block_format(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("Bullet item")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.Start)
    editor.setTextCursor(cursor)
    editor.make_bullet_list()
    editor.apply_font_point_size(19)
    editor.apply_font_weight(700)

    block = editor.document().firstBlock()
    assert block.textList() is not None
    assert round(block.charFormat().fontPointSize()) == 19
    assert int(block.charFormat().fontWeight()) == 700
    text_fmt = _character_format(editor, block.position())
    assert round(text_fmt.fontPointSize()) == 19
    assert int(text_fmt.fontWeight()) == 700


def test_blank_line_after_enter_setting(app: QApplication) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor = NoteEditor()
    editor.set_auto_checkbox(False)
    editor.set_blank_line_after_enter(True)
    editor.setPlainText("First line")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText() == "First line\n\n"


def test_blank_line_after_enter_with_auto_checkbox(app: QApplication) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor = NoteEditor()
    editor.set_auto_checkbox(True)
    editor.set_blank_line_after_enter(True)
    editor.setPlainText("☐ Backend")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText() == "☐ Backend\n\n☐ "
````

## `tests/test_settings.py`

````python
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6.QtCore")
from PySide6.QtCore import QSettings

from app.settings import AppPreferences, SettingsManager


def test_settings_round_trip(tmp_path: Path) -> None:
    qsettings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    manager = SettingsManager(qsettings)
    expected = AppPreferences(
        theme="dark",
        autosave_enabled=False,
        autosave_delay_ms=1200,
        start_with_last_note=False,
        editor_font_size=14,
        tab_width=2,
        auto_checkbox_default=False,
        blank_line_after_enter=True,
        word_wrap=False,
    )
    manager.save_preferences(expected)
    assert manager.preferences() == expected


def test_last_note_id_and_boolean_string_parsing(tmp_path: Path) -> None:
    qsettings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    qsettings.setValue("general/autosave_enabled", "false")
    manager = SettingsManager(qsettings)
    assert manager.preferences().autosave_enabled is False
    assert manager.last_note_id() is None
    manager.set_last_note_id(42)
    assert manager.last_note_id() == 42
    manager.set_last_note_id(None)
    assert manager.last_note_id() is None
````

## `tests/test_themes.py`

````python
from __future__ import annotations

import pytest

pytest.importorskip("PySide6.QtWidgets")

from app.themes.theme_manager import THEME_OPTIONS, THEME_SPECS


def test_theme_presets_include_multiple_dark_and_light_modes() -> None:
    values = {value for _label, value in THEME_OPTIONS}
    assert {"dark_matte", "dark_slate", "dark_graphite"} <= values
    assert {"light_clean", "light_soft", "light_warm", "light_cool"} <= values
    assert sum(1 for spec in THEME_SPECS.values() if spec.dark) >= 3
    assert sum(1 for spec in THEME_SPECS.values() if not spec.dark) >= 4
````

## `tests/test_txt_codec.py`

````python
from __future__ import annotations

from app.services.txt_codec import (
    export_internal_plain_text,
    import_text_to_html,
    parse_line,
    parse_text,
    parsed_to_internal_text,
)


def test_detects_supported_checkbox_markers() -> None:
    samples = {
        "[ ] Task": False,
        "[x] Task": True,
        "[X] Task": True,
        "☐ Task": False,
        "☑ Task": True,
        "✓ Task": True,
    }
    for source, expected_checked in samples.items():
        line = parse_line(source)
        assert line.is_task is True
        assert line.checked is expected_checked
        assert line.text == "Task"


def test_normal_text_is_not_a_task() -> None:
    line = parse_line("Bug: token refresh fails")
    assert line.is_task is False
    assert line.text == "Bug: token refresh fails"


def test_nested_indentation_is_preserved() -> None:
    lines = parse_text("[ ] Backend\n    [ ] API\n\t[x] Database")
    assert lines[0].indent == ""
    assert lines[1].indent == "    "
    assert lines[2].indent == "\t"
    internal = parsed_to_internal_text(lines)
    assert internal == "☐ Backend\n    ☐ API\n    ☑ Database"


def test_unicode_checkbox_html_marks_checked_task_as_struck() -> None:
    rendered = import_text_to_html("☐ Frontend\n☑ Login\n✓ Deploy")
    assert "☐" in rendered
    assert rendered.count("☑") == 2
    assert rendered.count("line-through") == 2


def test_export_converts_internal_checkbox_state() -> None:
    source = "☐ Login ekranı\n☑ Database bağlantısı\n    ☐ API"
    assert export_internal_plain_text(source) == "[ ] Login ekranı\n[x] Database bağlantısı\n    [ ] API"


def test_txt_round_trip_preserves_task_states_and_indentation() -> None:
    original = "[ ] Backend\n    [x] Database\nNormal açıklama\n\t[X] JWT"
    internal = parsed_to_internal_text(parse_text(original))
    exported = export_internal_plain_text(internal)
    reparsed = parse_text(exported)
    assert [(x.is_task, x.checked, x.text) for x in reparsed] == [
        (True, False, "Backend"),
        (True, True, "Database"),
        (False, False, "Normal açıklama"),
        (True, True, "JWT"),
    ]
    assert reparsed[1].indent == "    "
    assert reparsed[3].indent == "    "
````

## `tests/test_version.py`

````python
from app.constants import VERSION


def test_version_is_single_source() -> None:
    assert VERSION == "1.2.4"
````


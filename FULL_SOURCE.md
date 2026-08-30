# DevNest 1.2.0 — Full Source
This file contains the complete text-source snapshot for DevNest 1.2.0. Binary icon files are included in the ZIP but intentionally not embedded here.

## `.gitignore`

```text
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
build/
dist/
*.log

```

## `DevNest.spec`

```python
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

```

## `README.md`

```markdown
# DevNest 1.2.0

DevNest is a native, offline-first desktop workspace for developers. It combines rich notes, click-to-complete checklists, lightweight task planning, TXT portability, Trash/restore, and per-note diagrams in one PySide6 application.

## Technology

- Python 3.12+
- PySide6 / Qt 6
- SQLite
- QSettings
- PyInstaller
- No browser UI, web server, cloud account, telemetry, or runtime internet dependency

## Main Features

- Notes sidebar with title, preview, last-edited time, search, and sorting
- Rich text editor with bold, italic, underline, strikethrough, bullets, numbered lists, undo/redo, clipboard actions, and find
- Clickable task lines using `☐` and `☑`
- Checked task text is automatically struck through; unchecking removes the strike
- Auto Checkbox mode with Enter continuation and empty-task exit behavior
- Tab / Shift+Tab task indentation
- TXT import for `[ ]`, `[x]`, `[X]`, `☐`, `☑`, and `✓`
- TXT export using portable `[ ]` and `[x]` syntax
- UTF-8 and UTF-8-SIG import support
- Drag-and-drop TXT import
- Debounced autosave
- Trash, restore, permanent delete, empty Trash, and SQLite `VACUUM`
- Font-family selector using fonts actually installed on the computer
- 8–36 pt text-size slider and 100–900 font-weight slider for selected text/new typing
- Per-note diagrams using QGraphicsScene/QGraphicsView
- Freehand drawing, hand-drawn routed connectors with arrowheads, rounded box, ellipse, diamond, standalone text, duplicate, fit-to-view, zoom, selection, deletion, and pan
- Square/rectangle creation tools are removed, while old square/rectangle diagram data remains backward-compatible
- Theme presets: Matte Black, Midnight Slate, Graphite, Clean Light, Soft Gray, Warm Paper, Cool Mist, plus System mode
- Window geometry, splitter position, active tab, theme, settings, and last note restored with QSettings
- Rotating log files in the application data directory

## Project Structure

```text
devnest/
├─ main.py
├─ DevNest.spec
├─ build.ps1
├─ requirements.txt
├─ pytest.ini
├─ README.md
├─ resources/
│  ├─ devnest.svg
│  └─ devnest.ico
├─ app/
│  ├─ __init__.py
│  ├─ constants.py
│  ├─ database.py
│  ├─ main_window.py
│  ├─ models.py
│  ├─ paths.py
│  ├─ settings.py
│  ├─ dialogs/
│  │  ├─ __init__.py
│  │  ├─ preferences.py
│  │  ├─ shortcuts.py
│  │  └─ trash.py
│  ├─ services/
│  │  ├─ __init__.py
│  │  ├─ logging_setup.py
│  │  └─ txt_codec.py
│  ├─ themes/
│  │  ├─ __init__.py
│  │  └─ theme_manager.py
│  ├─ utils/
│  │  └─ __init__.py
│  └─ widgets/
│     ├─ __init__.py
│     ├─ diagram_view.py
│     ├─ note_editor.py
│     └─ sidebar.py
└─ tests/
   ├─ test_database.py
   ├─ test_diagram.py
   ├─ test_editor.py
   ├─ test_settings.py
   ├─ test_themes.py
   ├─ test_txt_codec.py
   └─ test_version.py
```

## Windows Installation

Install Python 3.12 or newer from python.org. During installation, enable the option that adds Python to PATH if you intend to use the `python` command directly.

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

If PowerShell blocks activation for the current session:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the application:

```powershell
python main.py
```

Run tests:

```powershell
python -m pytest -q
```

## Keyboard Shortcuts

| Action | Shortcut |
|---|---|
| New Note | Ctrl+N |
| Find in Note | Ctrl+F |
| Undo | Ctrl+Z |
| Redo | Ctrl+Y |
| Bold | Ctrl+B |
| Italic | Ctrl+I |
| Underline | Ctrl+U |
| Checkbox | Ctrl+Shift+X |
| Export TXT | Ctrl+E |
| Toggle Sidebar | Ctrl+Shift+B |
| Editor Tab | Ctrl+1 |
| Diagram Tab | Ctrl+2 |
| Duplicate selected diagram item | Ctrl+D |
| Delete selected diagram item | Delete |

## Checkbox Behavior

Click the checkbox glyph in the editor or use `Ctrl+Shift+X` on a line.

```text
☐ API'yi hazırla
```

After checking:

```text
☑ API'yi hazırla
```

The task text receives strikethrough formatting immediately. Unchecking removes it.

With Auto Checkbox enabled, pressing Enter after a non-empty task creates another unchecked task with the same indentation. Pressing Enter on an empty task removes the task marker and returns to a normal line. Tab adds task indentation; Shift+Tab removes it.

## TXT Import

Use **File > Import TXT**, the toolbar Import button, or drag a `.txt` file onto the main window.

Recognized task markers:

```text
[ ] Task
[x] Task
[X] Task
☐ Task
☑ Task
✓ Task
```

Checked tasks are imported as `☑` with strikethrough. Leading indentation is retained as spaces so nested checklists remain usable.

## TXT Export

Use **File > Export TXT** or `Ctrl+E`.

DevNest exports internal checkboxes as:

```text
[ ] Unchecked task
[x] Checked task
    [ ] Nested task
```

TXT cannot preserve rich text such as bold or italic. DevNest's SQLite storage keeps the native QTextDocument HTML separately, so rich formatting remains available inside the application.

## Text Font Controls

The old `Body / H1 / H2 / H3` toolbar selector has been replaced with direct typography controls:

- **Font selector:** shows several developer-friendly/system fonts only when they are actually installed. It always includes the current system monospace and UI fonts. Common Windows choices such as Cascadia Code, Cascadia Mono, Consolas, Courier New and Segoe UI appear when available.
- **Size slider:** 8–36 pt.
- **Weight slider:** OpenType/Qt weights from 100 (thin) through 900 (black).

Select text and change a control to format that selection. With no selection, the chosen format becomes the typing format for text entered next. The resulting rich-text formatting is stored in the note HTML in SQLite.

## Diagrams

Each note owns a separate diagram. Open the **Diagram** workspace button/tab or press `Ctrl+2`. The diagram canvas follows the selected application theme and uses a subtle grid.

Tools:

- **Select:** select and move normal diagram shapes/text
- **Pan:** drag the canvas
- **Draw:** default diagram tool; press and drag to draw any line or custom shape directly by hand
- **Connect:** press and drag from the start point to the end point; every sampled turn in the route is preserved and an arrowhead is drawn where you release
- **Round:** add a rounded process box
- **Ellipse:** add an ellipse
- **Diamond:** add a decision/diamond shape
- **Text:** add standalone text
- **Duplicate:** duplicate selected diagram content (`Ctrl+D`)
- **Fit:** fit all diagram objects in the viewport
- **+ / −:** zoom
- **Delete:** remove selected items

The old **Square** and **Rect** creation buttons were intentionally removed in 1.2.0. You can draw arbitrary boxes/shapes with **Draw** instead. Existing notes created by older DevNest versions that already contain square or rectangle nodes still load correctly.

**Connect is no longer a two-click straight-line tool.** Hold the left mouse button and draw the route you want. A connector can be angled, zig-zagged, or loosely curved because its actual path points are persisted. If the drag begins/ends on a built-in diagram shape, DevNest also records that attachment and keeps the connector endpoint on the shape boundary when the shape is moved.

Double-click a built-in shape or text item to edit its label. Shapes, text, freehand paths, routed connectors, arrow directions and connector attachment IDs are stored with the note in SQLite diagram JSON.

## Trash and Database Optimization

Normal Delete moves a note to Trash by setting `is_deleted = 1`. It does not immediately remove the SQLite row.

Open **File > Trash** to:

- Restore a note
- Permanently delete a selected note
- Empty Trash
- Optimize Database

Permanent deletion removes the note row. Linked diagram data is deleted by SQLite foreign-key cascade. SQLite may keep the database file size unchanged after deletion because freed pages are reused later. **Optimize Database** executes `VACUUM` to rebuild the database and return unused space to the filesystem where possible.

## Settings

Open **File > Preferences**.

General:

- Autosave enabled/disabled
- Autosave delay
- Start with last opened note

Editor:

- Font size
- Tab width
- Auto Checkbox default
- Word wrap

Appearance:

- System
- Matte Black
- Midnight Slate
- Graphite
- Clean Light
- Soft Gray
- Warm Paper
- Cool Mist

The **Editor / Diagram / Theme** workspace strip is always visible below the toolbars. It is part of the main layout rather than a toolbar overflow menu, so those controls are not hidden behind Qt's three-dot extension button.

QSettings stores these preferences outside the executable.

## Data Location

The database is stored using Qt's `QStandardPaths.AppDataLocation`, not beside the executable. On Windows this resolves under the current user's application-data area. The exact active database path is displayed in **Help > About DevNest**.

The database filename is:

```text
devnest.db
```

Logs are stored under the same application-data directory in:

```text
logs\devnest.log
```

## Backup

For a reliable backup:

1. Close DevNest so pending autosaves are flushed and SQLite is cleanly closed.
2. Open **Help > About DevNest** and note the database path.
3. Copy `devnest.db` to a backup location.

If you back up while the application is running, SQLite WAL files can be relevant. Closing first is the simplest safe approach.

## Building a Windows EXE with PyInstaller

The checked-in `DevNest.spec` supports both **onedir** and **onefile** builds. For maximum reliability with Qt, start with onedir; for easiest sharing, the same spec can also produce one standalone EXE. Build on a 64-bit Windows machine with 64-bit Python when targeting normal Windows 10/11 PCs.

With the virtual environment active:

```powershell
.\build.ps1
```

The script:

- checks for Python 3.12+ and reports the Python architecture
- installs/updates dependencies unless `-SkipInstall` is supplied
- verifies PySide6 and PyInstaller imports
- runs the full test suite in Qt offscreen mode and stops if tests fail
- removes old `build` and `dist` folders
- runs PyInstaller with `DevNest.spec`
- verifies the expected EXE exists

To skip dependency installation after the environment is already prepared:

```powershell
.\build.ps1 -SkipInstall
```

The resulting executable is:

```text
dist\DevNest\DevNest.exe
```

For the onedir build, distribute the **entire** `dist\DevNest` folder, not only the EXE.

### What `--windowed` means

`--windowed` (or `console=False` in the spec) prevents a separate console window from opening for the GUI application on Windows.

### `--onedir` versus `--onefile`

`--onedir` creates one folder containing the EXE and required Qt/Python files. It normally starts faster and is easier to inspect and troubleshoot.

`--onefile` creates one distributable EXE. At launch, PyInstaller extracts bundled files to a temporary location, so startup can be slower and antivirus products may inspect it more aggressively.

For DevNest, **onedir is the safest package to test first**. Distribute the whole `dist\DevNest` directory, usually as a ZIP. Target computers do not need Python installed.

### Onefile build

To produce one standalone EXE using the same checked-in spec:

```powershell
.\build.ps1 -OneFile
```

If dependencies are already installed:

```powershell
.\build.ps1 -OneFile -SkipInstall
```

The onefile output is:

```text
dist\DevNest.exe
```

Onefile is easier to send to someone, but it extracts its bundled runtime to a temporary directory at startup and therefore commonly starts slower than onedir.

### `build` and `dist`

- `build\` contains PyInstaller's temporary analysis and intermediate files.
- `dist\` contains the distributable application.

The `build\` directory is not needed by end users.

### Running on a PC without Python

Yes. A correctly built PyInstaller bundle contains the Python interpreter and the Python/Qt modules needed by DevNest. The target computer does not need a separate Python installation.

Build the Windows application on Windows. PyInstaller is not a cross-compiler for producing a normal Windows EXE from Linux or macOS.

### SmartScreen warnings

A newly built unsigned EXE may show Microsoft Defender SmartScreen warnings because it has little or no reputation and no trusted publisher signature. This does not automatically mean the application is malicious.

For public distribution, obtain a code-signing certificate and sign the executable. Code signing identifies the publisher and helps Windows establish trust/reputation. EV or organization-validated signing options have different cost and reputation characteristics.

### Confirming AppData storage

Run the built EXE, open **Help > About DevNest**, and inspect the displayed database path. It should point to the user's application-data area rather than `dist\DevNest`. Create a note, close the application, reopen it, and verify that the note remains available.

## Troubleshooting

### PowerShell will not activate the virtual environment

Use a process-local policy change:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

### `python` is not recognized

Reinstall Python with PATH enabled, or use the Windows Python launcher if available:

```powershell
py -3.12 --version
```

Then create the environment with:

```powershell
py -3.12 -m venv .venv
```

### PySide6 import error

Confirm the virtual environment is active, then reinstall requirements:

```powershell
python -m pip install -r requirements.txt
```

### Build fails after dependency changes

Clean and rebuild:

```powershell
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
python -m PyInstaller --noconfirm --clean DevNest.spec
```

### TXT import fails

DevNest expects UTF-8 or UTF-8-SIG. Convert older ANSI/Windows-codepage files to UTF-8 in a text editor before importing.

### Database problem

Check `logs\devnest.log` under the DevNest application-data directory. Before manually changing database files, close DevNest and make a backup copy.

## Version

The application version is defined once in `app/constants.py` as `VERSION = "1.2.0"`. The window metadata and About dialog read from this value.

```

## `app/__init__.py`

```python
from app.constants import VERSION

__all__ = ["VERSION"]

```

## `app/constants.py`

```python
from __future__ import annotations

APP_NAME = "DevNest"
ORGANIZATION_NAME = "DevNest"
ORGANIZATION_DOMAIN = "devnest.local"
VERSION = "1.2.0"
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

```

## `app/database.py`

```python
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

```

## `app/dialogs/__init__.py`

```python

```

## `app/dialogs/preferences.py`

```python
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
        self.word_wrap = QCheckBox("Word wrap")
        self.word_wrap.setChecked(prefs.word_wrap)
        editor_form.addRow("Font size:", self.font_size)
        editor_form.addRow("Tab width (spaces):", self.tab_width)
        editor_form.addRow(self.auto_checkbox)
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
            word_wrap=self.word_wrap.isChecked(),
        )

```

## `app/dialogs/shortcuts.py`

```python
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

```

## `app/dialogs/trash.py`

```python
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

```

## `app/main_window.py`

```python
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
        self.set_theme(prefs.theme, persist=persist)

    def _set_auto_checkbox(self, enabled: bool) -> None:
        self.editor.set_auto_checkbox(enabled)
        self.preferences.auto_checkbox_default = enabled
        self.settings.set_value("editor/auto_checkbox_default", enabled)

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


```

## `app/models.py`

```python
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

```

## `app/paths.py`

```python
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

```

## `app/services/__init__.py`

```python

```

## `app/services/logging_setup.py`

```python
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

```

## `app/services/txt_codec.py`

```python
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

```

## `app/settings.py`

```python
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

```

## `app/themes/__init__.py`

```python

```

## `app/themes/theme_manager.py`

```python
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

```

## `app/utils/__init__.py`

```python

```

## `app/widgets/__init__.py`

```python

```

## `app/widgets/diagram_view.py`

```python
from __future__ import annotations

import math
import uuid
from typing import Callable

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPolygonF, QWheelEvent
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
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


# Square/rectangle remain supported internally so diagrams created with DevNest 1.1
# keep loading, but they are intentionally not offered as creation tools anymore.
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


class DiagramShape(QGraphicsPathItem):
    def __init__(
        self,
        item_id: str,
        shape_type: str,
        text: str,
        on_changed: Callable[[], None],
    ) -> None:
        super().__init__()
        self.item_id = item_id
        self.shape_type = shape_type if shape_type in SHAPE_SIZES else "rect"
        self._on_changed = on_changed
        self._width, self._height = SHAPE_SIZES[self.shape_type]
        self.setPath(self._make_path())
        self.label = QGraphicsTextItem(text, self)
        self.label.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.label.setTextWidth(max(52.0, self._width - 20.0))
        self._position_label()
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setPen(_pen("#747b88", 1.6))
        self.setBrush(QBrush(QColor("#ffffff")))

    def _make_path(self) -> QPainterPath:
        rect = QRectF(0.0, 0.0, self._width, self._height)
        path = QPainterPath()
        if self.shape_type == "ellipse":
            path.addEllipse(rect)
        elif self.shape_type == "diamond":
            polygon = QPolygonF(
                [
                    QPointF(self._width / 2.0, 0.0),
                    QPointF(self._width, self._height / 2.0),
                    QPointF(self._width / 2.0, self._height),
                    QPointF(0.0, self._height / 2.0),
                ]
            )
            path.addPolygon(polygon)
            path.closeSubpath()
        elif self.shape_type == "rounded":
            path.addRoundedRect(rect, 14.0, 14.0)
        else:
            path.addRect(rect)
        return path

    def _position_label(self) -> None:
        label_height = self.label.boundingRect().height()
        self.label.setPos(10.0, max(6.0, (self._height - label_height) / 2.0))

    @property
    def text(self) -> str:
        return self.label.toPlainText()

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setBrush(QBrush(QColor(palette["fill"])))
        self.setPen(_pen(palette["stroke"], 1.6))
        self.label.setDefaultTextColor(QColor(palette["text"]))

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._on_changed()
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


DiagramEndpoint = DiagramShape | DiagramText


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
        self.setPen(_pen("#596273"))

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setPen(_pen(palette["connector"]))

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
    def set_theme(self, palette: dict[str, str]) -> None:
        self.setPen(_pen(palette["stroke"]))


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
        self.setPen(_pen("#596273"))

    def set_theme(self, palette: dict[str, str]) -> None:
        self.setPen(_pen(palette["connector"]))

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
    arrow_size = 11.0
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
        self.current_path: DiagramFreehand | None = None
        self.current_connector: DiagramConnector | None = None
        self._last_draw_point: QPointF | None = None
        self.palette = dict(DEFAULT_DIAGRAM_PALETTE)
        self.path_pen = _pen(self.palette["stroke"])
        self.loading = False
        self.setSceneRect(-2500, -2500, 5000, 5000)

    def set_mode(self, mode: str) -> None:
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
    ) -> DiagramShape:
        label = text if text is not None else SHAPE_LABELS.get(shape_type, "Shape")
        shape = DiagramShape(item_id or self._new_id(), shape_type, label, self._notify_changed)
        shape.set_theme(self.palette)
        self.addItem(shape)
        shape.setPos(pos)
        self._notify_changed()
        return shape

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

    def add_connector_path(
        self,
        path: QPainterPath,
        notify: bool = True,
        source_id: str | None = None,
        target_id: str | None = None,
    ) -> DiagramConnector:
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
            start = self._boundary_point(source, target_center)
            end = self._boundary_point(target, source_center)
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
                start = self._boundary_point(nodes[item.source_id], toward)
                points[0] = [start.x(), start.y()]
            if item.target_id and item.target_id in nodes:
                toward = QPointF(points[-2][0], points[-2][1])
                end = self._boundary_point(nodes[item.target_id], toward)
                points[-1] = [end.x(), end.y()]
            rebuilt = _path_from_points(points)
            if rebuilt is not None:
                item.setPath(rebuilt)

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
            if isinstance(item, (DiagramShape, DiagramText)):
                result[item.item_id] = item
        return result

    def _node_at(self, pos: QPointF) -> DiagramEndpoint | None:
        for item in self.items(pos):
            current = item
            while current is not None:
                if isinstance(current, (DiagramShape, DiagramText)):
                    return current
                current = current.parentItem()
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
                shape_type = self.mode.split(":", 1)[1]
                width, height = SHAPE_SIZES.get(shape_type, SHAPE_SIZES["rect"])
                self.add_shape(shape_type, pos - QPointF(width / 2.0, height / 2.0))
                event.accept()
                return
            if self.mode == "text":
                text, ok = QInputDialog.getText(None, "Text", "Text:")
                if ok:
                    self.add_text(pos, text or "Text")
                event.accept()
                return
            if self.mode == "draw":
                path = QPainterPath(pos)
                self.current_path = DiagramFreehand(path)
                self.current_path.setPen(self.path_pen)
                self.current_path.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                self.addItem(self.current_path)
                self._last_draw_point = pos
                event.accept()
                return
            if self.mode == "connect":
                path = QPainterPath(pos)
                source = self._node_at(pos)
                self.current_connector = DiagramConnector(
                    path,
                    source_id=source.item_id if source is not None else None,
                )
                self.current_connector.set_theme(self.palette)
                self.addItem(self.current_connector)
                self._last_draw_point = pos
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.mode == "draw" and self.current_path is not None:
            self._last_draw_point = self._append_sample(self.current_path, event.scenePos(), self._last_draw_point)
            event.accept()
            return
        if self.mode == "connect" and self.current_connector is not None:
            self._last_draw_point = self._append_sample(self.current_connector, event.scenePos(), self._last_draw_point)
            event.accept()
            return
        super().mouseMoveEvent(event)
        self.update_edges()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.mode in {"draw", "connect"}:
            item: QGraphicsPathItem | None = self.current_path if self.mode == "draw" else self.current_connector
            if item is not None:
                self._append_sample(item, event.scenePos(), self._last_draw_point)
                if isinstance(item, DiagramConnector):
                    target = self._node_at(event.scenePos())
                    item.target_id = target.item_id if target is not None else None
                    if item.source_id == item.target_id:
                        item.target_id = None
                if item.path().elementCount() < 2:
                    self.removeItem(item)
                self.current_path = None
                self.current_connector = None
                self._last_draw_point = None
                self._notify_changed()
            event.accept()
            return
        super().mouseReleaseEvent(event)
        self._notify_changed()

    def delete_selected(self) -> None:
        selected = list(self.selectedItems())
        if not selected:
            return
        node_ids = {item.item_id for item in selected if isinstance(item, (DiagramShape, DiagramText))}
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
                copy = self.add_shape(item.shape_type, item.pos() + offset, item.text)
                copy.setSelected(True)
                created = True
            elif isinstance(item, DiagramText):
                copy = self.add_text(item.pos() + offset, item.toPlainText())
                copy.setSelected(True)
                created = True
            elif isinstance(item, DiagramFreehand):
                path = _translated_path(item.path(), offset)
                copy = DiagramFreehand(path)
                copy.setPen(self.path_pen)
                copy.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                self.addItem(copy)
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
                if points:
                    connector_data: dict[str, object] = {"points": points}
                    if item.source_id:
                        connector_data["source"] = item.source_id
                    if item.target_id:
                        connector_data["target"] = item.target_id
                    connectors.append(connector_data)
            elif isinstance(item, DiagramFreehand):
                points = _path_points(item.path())
                if points:
                    paths.append({"points": points})
        return {"version": 3, "items": nodes, "edges": edges, "paths": paths, "connectors": connectors}

    def load_data(self, data: dict[str, object]) -> None:
        self.loading = True
        try:
            self.current_path = None
            self.current_connector = None
            self._last_draw_point = None
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
                    item = self.add_shape(shape_type, pos, text, item_id)
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
                path_item = DiagramFreehand(path)
                path_item.set_theme(self.palette)
                path_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                self.addItem(path_item)

            for raw in data.get("connectors", []) if isinstance(data, dict) else []:
                if not isinstance(raw, dict):
                    continue
                path = _path_from_points(raw.get("points", []))
                if path is not None:
                    source_id = str(raw.get("source")) if raw.get("source") else None
                    target_id = str(raw.get("target")) if raw.get("target") else None
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

    def set_mode(self, mode: str) -> None:
        if mode == "pan":
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        elif mode == "select":
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)

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
            ("Select", "select", "Select and move diagram items"),
            ("Pan", "pan", "Pan the canvas"),
            ("Draw", "draw", "Draw any shape or line freely by hand"),
            ("Connect", "connect", "Press and drag to draw an arrow; the route is kept exactly as drawn"),
            ("Round", "shape:rounded", "Add a rounded process box"),
            ("Ellipse", "shape:ellipse", "Add an ellipse"),
            ("Diamond", "shape:diamond", "Add a diamond / decision shape"),
            ("Text", "text", "Add standalone text"),
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
            "Draw: el ile serbest çiz. Connect: basılı tutup istediğin rotayı çiz; ok eğimi ve kıvrımı çizdiğin gibi saklanır."
        )
        hint.setObjectName("diagramHint")
        hint.setContentsMargins(8, 0, 8, 2)

        root.addLayout(bar)
        root.addWidget(hint)
        root.addWidget(self.canvas, 1)
        self.set_mode("draw")

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

```

## `app/widgets/note_editor.py`

```python
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
        self._merge_format(fmt)

    def apply_font_point_size(self, size: int) -> None:
        size = max(8, min(48, int(size)))
        fmt = QTextCharFormat()
        fmt.setFontPointSize(float(size))
        self._merge_format(fmt)

    def apply_font_weight(self, weight: int) -> None:
        weight = max(100, min(900, int(round(weight / 100.0) * 100)))
        fmt = QTextCharFormat()
        fmt.setFontWeight(weight)
        self._merge_format(fmt)

    def set_tab_width(self, spaces: int) -> None:
        self.tab_spaces = max(2, min(8, spaces))
        metrics = self.fontMetrics()
        self.setTabStopDistance(metrics.horizontalAdvance(" ") * self.tab_spaces)

    def set_auto_checkbox(self, enabled: bool) -> None:
        self.auto_checkbox_enabled = enabled

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
        self._merge_format(fmt)

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

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.auto_checkbox_enabled:
            if self._handle_task_enter():
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
        cursor.insertText(f"{indent}☐ ")
        self.setTextCursor(cursor)
        self._apply_task_style(block, checked=checked)
        self._apply_task_style(cursor.block(), checked=False)
        reset_fmt = QTextCharFormat()
        reset_fmt.setFontStrikeOut(False)
        self.mergeCurrentCharFormat(reset_fmt)
        return True

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

```

## `app/widgets/sidebar.py`

```python
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

```

## `build.ps1`

```powershell
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

```

## `main.py`

```python
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

```

## `pytest.ini`

```ini
[pytest]
pythonpath = .
testpaths = tests

```

## `requirements.txt`

```text
PySide6==6.11.2
PyInstaller==6.22.2
pytest>=8.3,<10

```

## `resources/devnest.svg`

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <rect x="16" y="16" width="224" height="224" rx="48" fill="#273043"/>
  <path d="M68 76h120v22H68zm0 42h88v22H68zm0 42h120v22H68z" fill="#F3F5F7"/>
  <path d="M174 112l18 18-18 18" fill="none" stroke="#7AA2F7" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>
</svg>

```

## `tests/test_database.py`

```python
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

```

## `tests/test_diagram.py`

```python
from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6.QtWidgets")

from PySide6.QtCore import QPointF
from PySide6.QtGui import QPainterPath
from PySide6.QtWidgets import QApplication

from app.widgets.diagram_view import DiagramConnector, DiagramScene, DiagramShape, DiagramView


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


def test_hand_drawn_connector_round_trip(app: QApplication) -> None:
    scene = DiagramScene()
    path = QPainterPath(QPointF(10, 10))
    path.lineTo(80, 40)
    path.lineTo(120, 15)
    path.lineTo(190, 80)
    scene.add_connector_path(path)

    data = scene.to_data()
    assert data["version"] == 3
    assert len(data["connectors"]) == 1
    assert len(data["connectors"][0]["points"]) == 4

    restored = DiagramScene()
    restored.load_data(data)
    connectors = [item for item in restored.items() if isinstance(item, DiagramConnector)]
    assert len(connectors) == 1
    assert connectors[0].path().elementCount() == 4


def test_square_and_rectangle_are_not_creation_buttons(app: QApplication) -> None:
    view = DiagramView()
    assert "shape:square" not in view._mode_buttons
    assert "shape:rect" not in view._mode_buttons
    assert "draw" in view._mode_buttons
    assert "connect" in view._mode_buttons

```

## `tests/test_editor.py`

```python
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


def test_checkbox_toggle_applies_and_removes_strike(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("☐ API'yi hazırla")
    block = editor.document().firstBlock()
    editor.toggle_checkbox(block)
    assert editor.toPlainText().startswith("☑")

    cursor = QTextCursor(editor.document())
    cursor.setPosition(block.position() + 2)
    assert cursor.charFormat().fontStrikeOut() is True

    editor.toggle_checkbox(editor.document().firstBlock())
    assert editor.toPlainText().startswith("☐")
    cursor.setPosition(editor.document().firstBlock().position() + 2)
    assert cursor.charFormat().fontStrikeOut() is False


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

```

## `tests/test_settings.py`

```python
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

```

## `tests/test_themes.py`

```python
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

```

## `tests/test_txt_codec.py`

```python
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

```

## `tests/test_version.py`

```python
from app.constants import VERSION


def test_version_is_single_source() -> None:
    assert VERSION == "1.2.0"

```

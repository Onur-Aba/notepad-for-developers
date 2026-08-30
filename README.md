# DevNest 1.2.2

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
- Drag-to-size Square/box, rounded box, ellipse and diamond tools; selected shapes expose eight resize handles for later adjustment
- Hand-routed directional connectors with clear arrowheads, standalone text, duplicate, fit-to-view, zoom, selection, deletion, and middle-mouse pan
- Legacy freehand and old rectangle diagram data remain backward-compatible even though freehand Draw is no longer a creation tool
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

- **Select:** select and move diagram items. A selected built-in shape shows **8 resize handles** (corners + edges); drag a handle to resize it after creation.
- **Pan:** drag the canvas. In every tool, you can also hold the **middle mouse button / scroll wheel** and drag to pan without changing tools.
- **Square:** press the left mouse button and drag the exact bounds you want. A square drag produces a square; stretching wider/taller produces a rectangular box. A simple click does **not** create a fixed-size object.
- **Round:** press and drag to create a rounded rectangle at your chosen width and height.
- **Ellipse:** press and drag to create an ellipse at your chosen width and height.
- **Diamond:** press and drag to create a decision diamond at your chosen width and height.
- **Text:** add standalone text.
- **Connect:** begin on one existing diagram object, keep the left mouse button held, route the connection however you want, and release on a different object. The filled arrowhead marks the target direction. Starts/ends in empty canvas are rejected.
- **Duplicate:** duplicate selected diagram content (`Ctrl+D`).
- **Fit:** fit all diagram objects in the viewport.
- **+/−:** zoom. The mouse wheel also zooms.
- **Delete:** delete the current selection.

Shape creation deliberately uses a **preview-first** model. Pressing the mouse only starts a temporary dashed preview; the real connectable shape is created after you drag and release. This means a half-created shape never becomes a connector endpoint and no temporary center/anchor marker is introduced while sizing it.

All new built-in shape dimensions are stored in the diagram JSON (`width`/`height`), so sizes survive autosave/restart. Existing diagrams from older DevNest versions still load: old rectangle/square nodes keep their fallback sizes and old freehand paths remain visible/connectable, but the old freehand **Draw** creation tool is no longer shown.

Connections remain anchored to the boundary of resized shapes. Resizing or moving a shape updates attached connector endpoints, while the hand-routed middle section of the connector remains preserved.


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

The application version is defined once in `app/constants.py` as `VERSION = "1.2.2"`. The window metadata and About dialog read from this value.

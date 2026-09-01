from __future__ import annotations

APP_NAME = "DevNest"
ORGANIZATION_NAME = "DevNest"
ORGANIZATION_DOMAIN = "devnest.local"
VERSION = "2.0.0"
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

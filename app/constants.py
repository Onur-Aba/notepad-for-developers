from __future__ import annotations

APP_NAME = "DevNest"
ORGANIZATION_NAME = "DevNest"
ORGANIZATION_DOMAIN = "devnest.local"
VERSION = "2.0.0"
DEFAULT_NOTE_TITLE = "Untitled Note"
DEFAULT_AUTOSAVE_DELAY_MS = 1800
MIN_AUTOSAVE_DELAY_MS = 1000
MAX_AUTOSAVE_DELAY_MS = 10000
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


COMMAND_SHORTCUTS: dict[str, tuple[str, str]] = {
    "command_palette": ("Command Palette", "Ctrl+K"),
    "create_decision": ("Create Decision", "Ctrl+Shift+D"),
    "open_projects": ("Open Project", "Ctrl+Shift+P"),
    "search_notes": ("Search Notes", "Ctrl+Alt+F"),
    "review_inbox": ("Review Inbox", "Ctrl+Shift+R"),
    "switch_theme": ("Switch Theme", "Ctrl+Alt+T"),
    "open_repository": ("Open Repository", "Ctrl+Shift+O"),
}

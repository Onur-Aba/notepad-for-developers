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
    check_repositories_on_startup: bool = True
    github_poll_interval_minutes: int = 15


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
            check_repositories_on_startup=self._bool("github/check_on_startup", True),
            github_poll_interval_minutes=int(self.qsettings.value("github/poll_interval_minutes", 15)),
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
        self.qsettings.setValue("github/check_on_startup", prefs.check_repositories_on_startup)
        self.qsettings.setValue("github/poll_interval_minutes", prefs.github_poll_interval_minutes)
        self.qsettings.sync()


    def command_shortcut(self, command_id: str, default: str) -> str:
        value = self.qsettings.value(f"shortcuts/{command_id}", default)
        return str(value or default)

    def set_command_shortcut(self, command_id: str, sequence: str) -> None:
        self.qsettings.setValue(f"shortcuts/{command_id}", sequence)
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

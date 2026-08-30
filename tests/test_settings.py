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

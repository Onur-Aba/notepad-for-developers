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

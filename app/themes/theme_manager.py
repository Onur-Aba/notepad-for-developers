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

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
    find_match_bg: str
    find_match_fg: str
    find_current_bg: str
    find_current_fg: str
    find_marker: str
    find_current_marker: str
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
        find_match_bg="#59491f",
        find_match_fg="#f4ead2",
        find_current_bg="#b67d20",
        find_current_fg="#111111",
        find_marker="#c89b3c",
        find_current_marker="#f2c45d",
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
        find_match_bg="#294a62",
        find_match_fg="#edf6ff",
        find_current_bg="#4d86b5",
        find_current_fg="#ffffff",
        find_marker="#5e93bd",
        find_current_marker="#91c8f0",
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
        find_match_bg="#51492d",
        find_match_fg="#f1ead2",
        find_current_bg="#8c7836",
        find_current_fg="#ffffff",
        find_marker="#a68c3e",
        find_current_marker="#d6b95d",
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
        find_match_bg="#fff1a8",
        find_match_fg="#2c2a20",
        find_current_bg="#f4c34d",
        find_current_fg="#1f1b10",
        find_marker="#d9a72d",
        find_current_marker="#b47a00",
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
        find_match_bg="#dceaf3",
        find_match_fg="#26333d",
        find_current_bg="#92c4df",
        find_current_fg="#182630",
        find_marker="#72a8c4",
        find_current_marker="#3e86aa",
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
        find_match_bg="#f1dfb5",
        find_match_fg="#3b3020",
        find_current_bg="#d7ac61",
        find_current_fg="#2a1e10",
        find_marker="#b78b48",
        find_current_marker="#8e6227",
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
        find_match_bg="#d1e9f0",
        find_match_fg="#24343c",
        find_current_bg="#8bc2d2",
        find_current_fg="#16303b",
        find_marker="#6aa9bc",
        find_current_marker="#3f8499",
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
QWidget#editorFindBar {{
    background: {spec.surface};
    border: 1px solid {spec.border};
    border-radius: 8px;
}}
QLineEdit#editorFindInput {{
    background: {spec.editor};
    color: {spec.text};
    border: 1px solid {spec.border};
    border-radius: 5px;
    padding: 5px 7px;
}}
QLabel#editorFindCount {{ color: {spec.muted}; }}
QCheckBox#editorFindDirection {{ spacing: 4px; color: {spec.text}; }}
QCheckBox#editorFindDirection::indicator {{
    width: 12px; height: 12px;
    border: 1px solid {spec.muted};
    border-radius: 2px;
    background: {spec.editor};
}}
QCheckBox#editorFindDirection::indicator:checked {{
    background: {spec.accent};
    border-color: {spec.accent};
}}
QPushButton#editorFindButton {{ padding: 5px 9px; background: {spec.surface_alt}; }}
QPushButton#editorFindClose {{
    padding: 3px;
    border: 0;
    background: transparent;
    font-size: 17px;
    font-weight: 600;
}}
QPushButton#editorFindClose:hover {{ background: {spec.hover}; }}

/* DevNest 2.0 product shell */
QWidget#globalNavigation {{
    background: {spec.surface};
    border-right: 1px solid {spec.border};
}}
QLabel#productBrand {{ font-size: 21px; font-weight: 750; }}
QLabel#productTagline {{ color: {spec.muted}; font-size: 11px; line-height: 1.3; }}
QLabel#navSectionLabel {{ color: {spec.muted}; font-size: 10px; font-weight: 700; padding: 5px 8px 3px 8px; }}
QPushButton#navButton {{
    border: 0;
    border-radius: 8px;
    padding: 9px 10px;
    text-align: left;
    font-size: 13px;
    background: transparent;
}}
QPushButton#navButton:hover {{ background: {spec.hover}; }}
QPushButton#navButton:checked {{ background: {spec.selected}; font-weight: 650; }}
QLabel#navFooter {{ color: {spec.muted}; font-size: 10px; padding: 8px; }}
QWidget#productTopBar {{
    background: {spec.surface};
    border-bottom: 1px solid {spec.border};
}}
QLabel#topBarLabel {{ color: {spec.muted}; font-size: 11px; font-weight: 650; }}
QComboBox#projectSelector {{ min-height: 29px; font-weight: 600; }}
QComboBox#languageQuickSelect {{ min-height: 29px; }}
QLabel#connectivityIndicator {{ color: {spec.muted}; padding: 5px 8px; border: 1px solid {spec.border}; border-radius: 7px; }}
QLabel#pageTitle {{ font-size: 27px; font-weight: 760; }}
QLabel#pageSubtitle {{ color: {spec.muted}; font-size: 12px; }}
QLabel#sectionTitle {{ font-size: 15px; font-weight: 700; }}
QLabel#secondaryPanelTitle {{ font-size: 14px; font-weight: 700; }}
QLabel#cardTitle {{ font-size: 14px; font-weight: 700; }}
QLabel#cardLabel, QLabel#fieldLabel, QLabel#contextCaption {{ color: {spec.muted}; font-size: 10px; font-weight: 700; }}
QLabel#metricValue {{ font-size: 28px; font-weight: 760; }}
QLabel#mutedText, QLabel#projectMeta, QLabel#sortNotice {{ color: {spec.muted}; }}
QLabel#sortNotice {{ font-size: 10px; }}
QLabel#helperTitle {{ font-weight: 700; }}
QLabel#contextValue {{ font-size: 12px; font-weight: 650; }}
QLabel#decisionKey {{ font-size: 12px; font-weight: 750; padding: 5px 8px; border: 1px solid {spec.border}; border-radius: 6px; }}
QLabel#emptyState, QLabel#emptyInlineState {{
    color: {spec.muted};
    padding: 26px;
    border: 1px dashed {spec.border};
    border-radius: 10px;
}}
QLabel#emptyInlineState {{ padding: 10px; }}
QFrame#metricCard, QFrame#projectCard, QFrame#repositoryCard, QFrame#reviewCard, QFrame#dashboardPanel,
QFrame#secondaryPanel, QFrame#editorPanel, QWidget#inspectorPanel {{
    background: {spec.surface};
    border: 1px solid {spec.border};
    border-radius: 10px;
}}
QFrame#helperBanner, QLabel#helperBanner {{
    background: {spec.surface_alt};
    border: 1px solid {spec.border};
    border-radius: 9px;
    padding: 10px 12px;
}}
QFrame#attentionPanel {{
    background: {spec.surface};
    border: 1px solid {spec.border};
    border-radius: 10px;
}}
QFrame#attentionPanel[attention="true"] {{ border: 1px solid {spec.accent}; }}
QFrame#contextBar, QFrame#resourceSummary {{
    background: {spec.surface_alt};
    border: 1px solid {spec.border};
    border-radius: 8px;
}}
QPushButton#primaryButton {{
    background: {spec.accent};
    color: #ffffff;
    border: 1px solid {spec.accent};
    font-weight: 650;
    padding: 7px 12px;
}}
QPushButton#primaryButton:hover {{ background: {spec.selected}; color: {spec.text}; border-color: {spec.accent}; }}
QPushButton#secondaryTabButton {{ border: 0; background: {spec.surface_alt}; padding: 7px 11px; }}
QPushButton#secondaryTabButton:hover {{ background: {spec.hover}; }}
QPushButton#iconActionButton {{ font-size: 18px; font-weight: 700; padding: 3px; }}
QLabel#smallPill {{
    color: {spec.muted};
    background: {spec.surface_alt};
    border: 1px solid {spec.border};
    border-radius: 9px;
    padding: 2px 7px;
    font-size: 10px;
}}
QWidget#noteSidebar {{ background: {spec.surface}; border-right: 1px solid {spec.border}; }}
QListWidget#noteList, QListWidget#decisionList {{ background: transparent; border: 0; }}
QListWidget#noteList::item, QListWidget#decisionList::item {{
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 7px;
    margin: 2px 0;
}}
QListWidget#noteList::item:hover, QListWidget#decisionList::item:hover {{ background: {spec.hover}; }}
QListWidget#noteList::item:selected, QListWidget#decisionList::item:selected {{ background: {spec.selected}; border-color: {spec.border}; }}
QLabel#noteCardTitle {{ font-weight: 650; }}
QLabel#noteCardPreview {{ color: {spec.muted}; font-size: 11px; }}
QLabel#noteCardDate {{ color: {spec.muted}; font-size: 9px; }}
QLineEdit#documentTitle {{ font-size: 17px; font-weight: 650; padding: 8px 10px; }}
QLabel#statusBadge {{ border-radius: 8px; padding: 3px 7px; font-size: 10px; font-weight: 650; }}
QLabel#statusBadge[reviewStatus="current"] {{ background: {spec.surface_alt}; }}
QLabel#statusBadge[reviewStatus="needs_review"] {{ border: 1px solid {spec.accent}; background: {spec.selected}; }}
QLabel#statusBadge[reviewStatus="not_reviewed"] {{ color: {spec.muted}; background: {spec.surface_alt}; }}
QLabel#statusBadge[reviewStatus="cannot_compare"] {{ border: 1px solid {spec.border}; background: {spec.surface_alt}; }}
QToolTip {{
    background: {spec.surface_alt};
    color: {spec.text};
    border: 1px solid {spec.border};
    padding: 9px 11px;
    font-size: 11px;
}}
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

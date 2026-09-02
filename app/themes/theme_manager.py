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

UI_MODE_OPTIONS: tuple[tuple[str, str], ...] = (
    ("Classic", "classic"),
    ("Modern", "modern"),
)


def _mix_hex(foreground: str, background: str, amount: float) -> str:
    """Blend foreground into background by amount (0..1)."""
    amount = max(0.0, min(1.0, float(amount)))
    fg = foreground.lstrip("#")
    bg = background.lstrip("#")
    if len(fg) != 6 or len(bg) != 6:
        return foreground
    out = []
    for index in (0, 2, 4):
        f = int(fg[index:index + 2], 16)
        b = int(bg[index:index + 2], 16)
        out.append(round(b + (f - b) * amount))
    return "#" + "".join(f"{value:02x}" for value in out)


def _relative_luminance(hex_color: str) -> float:
    value = hex_color.lstrip("#")
    if len(value) != 6:
        return 0.0
    channels = []
    for index in (0, 2, 4):
        channel = int(value[index:index + 2], 16) / 255.0
        channels.append(channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast_text(background: str) -> str:
    luminance = _relative_luminance(background)
    white_ratio = 1.05 / (luminance + 0.05)
    black_ratio = (luminance + 0.05) / 0.05
    return "#ffffff" if white_ratio >= black_ratio else "#111318"


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
QLabel#activityDetailText, QLabel#repositoryDetailText {{ color: {spec.text}; font-size: 11px; }}
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
QLabel#noteCardTitle {{ color: {spec.text}; font-size: 12px; font-weight: 650; }}
QLabel#noteCardPreview {{ color: {spec.text}; font-size: 11px; }}
QLabel#noteCardDate {{ color: {spec.muted}; font-size: 10px; }}
QLineEdit#documentTitle {{
    font-size: 17px; font-weight: 650; min-height: 26px;
    padding: 6px 10px 8px 10px;
}}
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

/* Accessible settings / dialogs / destructive actions */
QGroupBox#settingsCard {{
    background: {spec.surface};
    border: 1px solid {spec.border};
    border-radius: 12px;
    margin-top: 14px;
    font-weight: 700;
}}
QGroupBox#settingsCard::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 7px;
    color: {spec.text};
    background: {spec.window};
}}
QLabel#settingLabel {{ font-weight: 650; }}
QLabel#settingHelp {{ color: {spec.muted}; line-height: 1.35; }}
QFrame#settingsDialogHeader {{
    background: {spec.surface};
    border-bottom: 1px solid {spec.border};
}}
QFrame#settingsDialogSidebar {{
    background: {spec.surface};
    border-right: 1px solid {spec.border};
}}
QPushButton#settingsCategoryButton {{
    border: 0;
    border-radius: 8px;
    padding: 10px 11px;
    text-align: left;
    background: transparent;
}}
QPushButton#settingsCategoryButton:hover {{ background: {spec.hover}; }}
QPushButton#settingsCategoryButton:checked {{ background: {spec.selected}; font-weight: 700; }}
QLineEdit#settingsSearchInput {{
    background: {spec.editor};
    border: 1px solid {spec.border};
    border-radius: 9px;
    padding: 8px 11px;
    font-size: 13px;
}}
QLabel#dialogTitle {{ font-size: 22px; font-weight: 760; }}
QFrame#dialogCard, QFrame#trashProjectCard {{
    background: {spec.surface};
    border: 1px solid {spec.border};
    border-radius: 11px;
}}
QFrame#trashBundleDetails, QFrame#historyCommitDetails {{
    background: {spec.surface_alt};
    border: 1px solid {spec.border};
    border-radius: 9px;
}}
QFrame#dangerPanel {{
    background: {spec.surface_alt};
    border: 1px solid #c94f4f;
    border-radius: 10px;
}}
QLabel#confirmationProjectName {{
    font-size: 17px; font-weight: 750; padding: 10px 12px;
    background: {spec.surface_alt}; border: 1px solid {spec.border}; border-radius: 8px;
}}
QLabel#bundleSectionTitle {{ font-weight: 700; margin-top: 4px; }}
QLabel#bundleItem {{ color: {spec.text}; padding-left: 4px; }}
QPushButton#dangerButton {{
    background: #b42318; color: #ffffff; border: 1px solid #b42318;
    border-radius: 7px; padding: 7px 12px; font-weight: 700;
}}
QPushButton#dangerButton:hover {{ background: #d92d20; border-color: #d92d20; }}
QPushButton#dangerButton:disabled {{ background: {spec.surface_alt}; color: {spec.muted}; border-color: {spec.border}; }}
QPushButton#disclosureButton {{
    min-width: 32px; max-width: 32px; min-height: 32px; max-height: 32px;
    padding: 0; font-size: 18px; font-weight: 700; background: {spec.surface_alt};
}}
QPushButton#navTrashButton {{
    border: 1px solid {spec.border}; border-radius: 8px; padding: 9px 10px;
    text-align: left; background: {spec.surface_alt};
}}
QPushButton#navTrashButton:hover {{ background: {spec.hover}; }}
QPushButton#connectivityIndicator {{ color: {spec.text}; padding: 6px 9px; }}
QDialog#projectWizard, QDialog#projectDeleteDialog, QDialog#trashDialog {{ background: {spec.window}; }}
QDialog#projectWizard QStackedWidget, QDialog#projectWizard QWidget#dialogPage {{ background: {spec.window}; }}
QRadioButton {{ spacing: 8px; min-height: 26px; }}
QCheckBox {{ spacing: 8px; }}
"""


def _modern_qss(spec: ThemeSpec) -> str:
    """Modern DevNest shell built on the same semantic color ThemeSpec.

    The classic QSS remains the compatibility baseline. Modern mode layers a
    denser, token-like developer-tool visual system on top, so every existing
    color theme keeps working without duplicating page logic.
    """
    accent_soft = _mix_hex(spec.accent, spec.surface, 0.18 if not spec.dark else 0.24)
    accent_soft_hover = _mix_hex(spec.accent, spec.surface, 0.28 if not spec.dark else 0.34)
    elevated = _mix_hex(spec.text, spec.surface, 0.025 if spec.dark else 0.012)
    input_bg = _mix_hex(spec.text, spec.editor, 0.018 if spec.dark else 0.008)
    focus = spec.accent
    primary_fg = _contrast_text(spec.accent)
    danger_bg = "#b42318" if not spec.dark else "#d0443e"
    danger_fg = _contrast_text(danger_bg)
    return _qss(spec) + f"""

/* DevNest Modern UI mode -------------------------------------------------- */
QWidget {{
    font-family: "Segoe UI Variable Text", "Segoe UI", sans-serif;
}}
QMainWindow, QDialog {{ background: {spec.window}; }}
QWidget#globalNavigation {{
    background: {spec.surface};
    border-right: 1px solid {spec.border};
}}
QLabel#productBrand {{ font-size: 22px; font-weight: 800; letter-spacing: -0.2px; }}
QLabel#productTagline {{ color: {spec.muted}; font-size: 11px; padding-right: 4px; }}
QLabel#navSectionLabel {{
    color: {spec.muted}; font-size: 9px; font-weight: 800; letter-spacing: 0.7px;
    padding: 8px 10px 4px 10px;
}}
QPushButton#navButton {{
    min-height: 24px;
    border: 1px solid transparent;
    border-radius: 9px;
    padding: 8px 11px;
    text-align: left;
    font-size: 12px;
    font-weight: 560;
    background: transparent;
}}
QPushButton#navButton:hover {{ background: {spec.hover}; border-color: {spec.border}; }}
QPushButton#navButton:checked {{
    color: {spec.text};
    background: {accent_soft};
    border-color: {accent_soft_hover};
    font-weight: 720;
}}
QPushButton#navButton:focus {{ border: 2px solid {focus}; padding: 7px 10px; }}
QPushButton#navTrashButton {{
    min-height: 34px; border-radius: 10px; padding: 7px 11px;
    background: transparent; border: 1px solid {spec.border}; text-align: left;
}}
QPushButton#navTrashButton:hover {{ background: {spec.hover}; }}
QLabel#navFooter {{ color: {spec.muted}; font-size: 9px; line-height: 1.35; padding: 7px 4px 2px 4px; }}

QWidget#productTopBar {{
    min-height: 48px;
    background: {spec.surface};
    border-bottom: 1px solid {spec.border};
}}
QLabel#topBarLabel {{ color: {spec.muted}; font-size: 10px; font-weight: 700; }}
QComboBox#projectSelector, QComboBox#languageQuickSelect {{
    min-height: 32px; border-radius: 9px; background: {input_bg};
}}
QPushButton#uiModeQuickButton {{
    min-height: 32px; padding: 5px 10px; border-radius: 9px;
    background: {accent_soft}; border: 1px solid {accent_soft_hover}; font-weight: 700;
}}
QPushButton#uiModeQuickButton:hover {{ background: {accent_soft_hover}; }}
QPushButton#connectivityIndicator {{ min-height: 32px; border-radius: 9px; padding: 5px 10px; }}

QToolBar {{
    background: {spec.surface}; border: 0; border-bottom: 1px solid {spec.border};
    spacing: 3px; padding: 5px 8px;
}}
QToolButton {{
    min-height: 26px; border: 1px solid transparent; border-radius: 8px;
    padding: 5px 8px; background: transparent;
}}
QToolButton:hover {{ background: {spec.hover}; border-color: {spec.border}; }}
QToolButton:checked {{ background: {accent_soft}; border-color: {accent_soft_hover}; }}
QToolButton:focus {{ border: 2px solid {focus}; padding: 4px 7px; }}

QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QListWidget, QTableWidget {{
    background: {input_bg}; color: {spec.text};
    border: 1px solid {spec.border}; border-radius: 9px; padding: 7px 9px;
    selection-background-color: {accent_soft_hover}; selection-color: {spec.text};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus,
QListWidget:focus, QTableWidget:focus {{ border: 2px solid {focus}; padding: 6px 8px; }}
QComboBox QAbstractItemView {{
    background: {spec.surface}; color: {spec.text}; border: 1px solid {spec.border};
    border-radius: 10px; padding: 5px; selection-background-color: {accent_soft};
}}
QListWidget::item {{ border-radius: 8px; padding: 6px 7px; margin: 2px 0; }}
QListWidget::item:hover {{ background: {spec.hover}; }}
QListWidget::item:selected {{ background: {accent_soft}; color: {spec.text}; }}

QPushButton {{
    min-height: 30px; background: {elevated}; color: {spec.text};
    border: 1px solid {spec.border}; border-radius: 9px; padding: 6px 11px;
    font-weight: 580;
}}
QPushButton:hover {{ background: {spec.hover}; border-color: {accent_soft_hover}; }}
QPushButton:pressed, QPushButton:checked {{ background: {accent_soft}; }}
QPushButton:focus {{ border: 2px solid {focus}; padding: 5px 10px; }}
QPushButton:disabled {{ color: {spec.muted}; background: {spec.surface_alt}; border-color: {spec.border}; }}
QPushButton#primaryButton {{
    min-height: 32px; background: {spec.accent}; color: {primary_fg};
    border: 1px solid {spec.accent}; border-radius: 9px; padding: 7px 13px; font-weight: 760;
}}
QPushButton#primaryButton:hover {{
    background: {accent_soft_hover}; color: {spec.text}; border-color: {spec.accent};
}}
QPushButton#dangerButton {{
    min-height: 32px; background: {danger_bg}; color: {danger_fg};
    border: 1px solid {danger_bg}; border-radius: 9px; padding: 7px 13px; font-weight: 760;
}}

QLabel#pageTitle {{ font-size: 26px; font-weight: 800; letter-spacing: -0.35px; }}
QLabel#pageSubtitle {{ color: {spec.muted}; font-size: 12px; line-height: 1.45; }}
QLabel#sectionTitle {{ font-size: 14px; font-weight: 760; }}
QLabel#cardTitle {{ font-size: 13px; font-weight: 720; }}
QLabel#cardLabel, QLabel#fieldLabel, QLabel#contextCaption {{
    color: {spec.muted}; font-size: 9px; font-weight: 800; letter-spacing: 0.35px;
}}
QLabel#metricValue {{ font-size: 29px; font-weight: 820; letter-spacing: -0.5px; }}

QFrame#metricCard, QFrame#projectCard, QFrame#repositoryCard, QFrame#reviewCard,
QFrame#dashboardPanel, QFrame#secondaryPanel, QFrame#editorPanel, QWidget#inspectorPanel,
QFrame#dialogCard, QFrame#trashProjectCard {{
    background: {spec.surface}; border: 1px solid {spec.border}; border-radius: 14px;
}}
QFrame#helperBanner, QLabel#helperBanner, QFrame#contextBar, QFrame#resourceSummary {{
    background: {spec.surface_alt}; border: 1px solid {spec.border}; border-radius: 11px;
}}
QLabel#emptyState, QLabel#emptyInlineState {{
    color: {spec.muted}; padding: 28px; border: 1px dashed {accent_soft_hover}; border-radius: 13px;
    background: {spec.surface};
}}

QWidget#noteSidebar {{ background: {spec.surface}; border-right: 1px solid {spec.border}; }}
QListWidget#noteList::item, QListWidget#decisionList::item {{
    border: 1px solid transparent; border-radius: 10px; padding: 8px; margin: 2px 0;
}}
QListWidget#noteList::item:hover, QListWidget#decisionList::item:hover {{ background: {spec.hover}; border-color: {spec.border}; }}
QListWidget#noteList::item:selected, QListWidget#decisionList::item:selected {{ background: {accent_soft}; border-color: {accent_soft_hover}; }}
QLineEdit#documentTitle {{
    font-size: 19px; font-weight: 760; min-height: 30px; border-radius: 10px;
    padding: 8px 11px 9px 11px;
}}

QGroupBox#settingsCard {{
    background: {spec.surface}; border: 1px solid {spec.border}; border-radius: 14px;
    margin-top: 16px; font-weight: 760;
}}
QGroupBox#settingsCard::title {{
    subcontrol-origin: margin; subcontrol-position: top left; left: 14px; padding: 0 7px;
    color: {spec.text}; background: {spec.window};
}}
QFrame#uiModeSwitch {{
    background: {spec.surface_alt}; border: 1px solid {spec.border}; border-radius: 10px;
}}
QPushButton#uiModeSegment {{
    min-height: 30px; border: 0; border-radius: 8px; padding: 5px 14px;
    background: transparent; color: {spec.muted}; font-weight: 680;
}}
QPushButton#uiModeSegment:hover {{ color: {spec.text}; background: {spec.hover}; }}
QPushButton#uiModeSegment:checked {{ color: {spec.text}; background: {accent_soft}; }}
QPushButton#settingsCategoryButton {{ min-height: 32px; border-radius: 9px; padding: 8px 11px; }}
QPushButton#settingsCategoryButton:checked {{ background: {accent_soft}; border: 1px solid {accent_soft_hover}; }}
QLineEdit#settingsSearchInput {{ min-height: 38px; border-radius: 11px; padding: 8px 12px; }}

QMenu {{ background: {spec.surface}; color: {spec.text}; border: 1px solid {spec.border}; border-radius: 9px; padding: 5px; }}
QMenu::item {{ padding: 7px 30px 7px 10px; border-radius: 7px; }}
QMenu::item:selected {{ background: {accent_soft}; }}
QTabWidget::pane {{ border: 1px solid {spec.border}; border-radius: 10px; background: {spec.editor}; top: -1px; }}
QTabBar::tab {{
    background: transparent; color: {spec.muted}; padding: 8px 14px; margin-right: 3px;
    border: 0; border-bottom: 2px solid transparent;
}}
QTabBar::tab:selected {{ color: {spec.text}; background: transparent; border-bottom: 2px solid {spec.accent}; }}
QTabBar::tab:hover {{ color: {spec.text}; background: {spec.hover}; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {spec.border}; min-height: 30px; border-radius: 5px; }}
QScrollBar::handle:vertical:hover {{ background: {spec.muted}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {spec.border}; min-width: 30px; border-radius: 5px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QToolTip {{
    background: {spec.surface_alt}; color: {spec.text}; border: 1px solid {spec.border};
    border-radius: 8px; padding: 7px 9px; font-size: 11px;
}}
QStatusBar {{ background: {spec.surface}; border-top: 1px solid {spec.border}; min-height: 22px; }}
"""


class ThemeManager:
    def __init__(self, app: QApplication) -> None:
        self.app = app
        self.current_theme = "system"
        self.current_mode = "classic"
        self.current_spec = THEME_SPECS["light_clean"]
        self.is_dark = False

    def apply(self, theme: str, ui_mode: str | None = None) -> bool:
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
        if ui_mode is not None:
            requested_mode = str(ui_mode).lower().strip()
            valid_modes = {value for _, value in UI_MODE_OPTIONS}
            self.current_mode = requested_mode if requested_mode in valid_modes else "classic"
        self.current_theme = normalized
        resolved = self._resolve_system_theme() if normalized == "system" else normalized
        self.current_spec = THEME_SPECS[resolved]
        self.is_dark = self.current_spec.dark
        self.app.setProperty("devnestUiMode", self.current_mode)
        stylesheet = _modern_qss(self.current_spec) if self.current_mode == "modern" else _qss(self.current_spec)
        self.app.setStyleSheet(stylesheet)
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

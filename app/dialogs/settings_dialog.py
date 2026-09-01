from __future__ import annotations

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from app.i18n import I18n
from app.pages.settings_page import SettingsPage
from app.settings import SettingsManager


class SettingsDialog(QDialog):
    """Modal, searchable settings window with quick category navigation."""

    preferencesChanged = Signal()
    preferencesRequested = Signal()
    githubRequested = Signal()

    CATEGORY_KEYS = (
        "language",
        "saving",
        "editor",
        "appearance",
        "github",
        "advanced",
        "privacy",
    )

    def __init__(self, settings: SettingsManager, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.i18n = i18n
        self.setObjectName("settingsDialog")
        self.setModal(True)
        self.resize(1220, 800)
        self.setMinimumSize(980, 650)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        header.setObjectName("settingsDialogHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(24, 18, 24, 16)
        header_layout.setSpacing(10)

        self.title = QLabel()
        self.title.setObjectName("dialogTitle")
        self.search = QLineEdit()
        self.search.setObjectName("settingsSearchInput")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumHeight(42)
        self.search.textChanged.connect(self._search_changed)
        header_layout.addWidget(self.title)
        header_layout.addWidget(self.search)
        root.addWidget(header)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        root.addLayout(body, 1)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("settingsDialogSidebar")
        self.sidebar.setMinimumWidth(220)
        self.sidebar.setMaximumWidth(270)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(14, 18, 14, 16)
        side_layout.setSpacing(6)

        self.category_hint = QLabel()
        self.category_hint.setObjectName("navSectionLabel")
        side_layout.addWidget(self.category_hint)

        self.category_buttons: dict[str, QPushButton] = {}
        for key in self.CATEGORY_KEYS:
            button = QPushButton()
            button.setObjectName("settingsCategoryButton")
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.clicked.connect(lambda _checked=False, section=key: self._go_to_section(section))
            side_layout.addWidget(button)
            self.category_buttons[key] = button

        side_layout.addStretch(1)
        self.instant_note = QLabel()
        self.instant_note.setObjectName("navFooter")
        self.instant_note.setWordWrap(True)
        side_layout.addWidget(self.instant_note)

        self.close_button = QPushButton()
        self.close_button.setMinimumHeight(38)
        self.close_button.clicked.connect(self.accept)
        side_layout.addWidget(self.close_button)
        body.addWidget(self.sidebar)

        self.page = SettingsPage(settings, i18n)
        # The dialog header already carries the title/search; avoid repeating a
        # second large page heading inside the scrollable settings content.
        self.page.title.hide()
        self.page.subtitle.hide()
        self.page.preferencesChanged.connect(self.preferencesChanged)
        self.page.preferencesRequested.connect(self.preferencesRequested)
        self.page.githubRequested.connect(self.githubRequested)
        body.addWidget(self.page, 1)

        self.i18n.languageChanged.connect(lambda _language: self.retranslate_ui())
        self.retranslate_ui()
        self.category_buttons["language"].setChecked(True)
        QTimer.singleShot(0, lambda: self.search.setFocus(Qt.FocusReason.OtherFocusReason))

    def retranslate_ui(self) -> None:
        tr = self.i18n.language == "tr"
        self.setWindowTitle("Ayarlar — DevNest" if tr else "Settings — DevNest")
        self.title.setText("Ayarlar" if tr else "Settings")
        self.search.setPlaceholderText(
            "Ayarlarda ara… Örn: tema, otomatik kayıt, GitHub"
            if tr else
            "Search settings… e.g. theme, autosave, GitHub"
        )
        self.category_hint.setText("KATEGORİLER" if tr else "CATEGORIES")
        labels = {
            "language": "Dil" if tr else "Language",
            "saving": "Kayıt ve açılış" if tr else "Saving & startup",
            "editor": "Not editörü" if tr else "Note editor",
            "appearance": "Görünüm" if tr else "Appearance",
            "github": "GitHub kontrolü" if tr else "GitHub checking",
            "advanced": "Gelişmiş tercihler" if tr else "Advanced preferences",
            "privacy": "Gizlilik" if tr else "Privacy",
        }
        for key, button in self.category_buttons.items():
            button.setText(labels[key])
            button.setToolTip(
                (f"{labels[key]} ayarlarına doğrudan git." if tr else f"Jump directly to {labels[key]} settings.")
            )
        self.instant_note.setText(
            "Değişiklikler Kaydet düğmesi beklemeden anında uygulanır."
            if tr else
            "Changes apply immediately; there is no Save step."
        )
        self.close_button.setText("Kapat" if tr else "Close")
        # Re-run the active search after labels change language.
        self.page.filter_settings(self.search.text())

    def _go_to_section(self, section: str) -> None:
        # Category navigation should always reveal the full settings list first.
        if self.search.text():
            self.search.blockSignals(True)
            self.search.clear()
            self.search.blockSignals(False)
            self.page.filter_settings("")
        QTimer.singleShot(0, lambda: self.page.scroll_to_section(section))

    def _search_changed(self, text: str) -> None:
        first = self.page.filter_settings(text)
        if first and first in self.category_buttons:
            self.category_buttons[first].setChecked(True)

    def sync_from_preferences(self) -> None:
        self.page.sync_from_preferences(self.settings.preferences())

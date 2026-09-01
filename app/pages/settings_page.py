from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QGroupBox, QLabel, QPushButton, QVBoxLayout, QWidget

from app.i18n import I18n, LANGUAGE_OPTIONS
from app.settings import SettingsManager


class SettingsPage(QWidget):
    preferencesRequested = Signal()
    githubRequested = Signal()

    def __init__(self, settings: SettingsManager, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.i18n = i18n
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 28, 30, 24)
        root.setSpacing(12)
        self.title = QLabel()
        self.title.setObjectName("pageTitle")
        self.subtitle = QLabel()
        self.subtitle.setWordWrap(True)
        self.subtitle.setObjectName("pageSubtitle")
        root.addWidget(self.title)
        root.addWidget(self.subtitle)

        self.language_group = QGroupBox()
        language_form = QFormLayout(self.language_group)
        self.language_combo = QComboBox()
        for label, value in LANGUAGE_OPTIONS:
            self.language_combo.addItem(label, value)
        index = self.language_combo.findData(self.i18n.language)
        self.language_combo.setCurrentIndex(max(0, index))
        self.language_combo.currentIndexChanged.connect(self._language_selected)
        self.language_help = QLabel()
        self.language_help.setWordWrap(True)
        self.language_help.setObjectName("mutedText")
        self.language_label = QLabel()
        language_form.addRow(self.language_label, self.language_combo)
        language_form.addRow(self.language_help)

        self.general = QGroupBox()
        general_layout = QVBoxLayout(self.general)
        self.general_help = QLabel()
        self.general_help.setWordWrap(True)
        self.prefs_button = QPushButton()
        self.prefs_button.clicked.connect(self.preferencesRequested)
        general_layout.addWidget(self.general_help)
        general_layout.addWidget(self.prefs_button)

        self.github = QGroupBox()
        github_form = QFormLayout(self.github)
        self.startup = QCheckBox()
        self.startup.setChecked(self._bool("github/check_on_startup", True))
        self.startup.toggled.connect(lambda value: self.settings.set_value("github/check_on_startup", value))
        self.interval = QComboBox()
        self._rebuild_interval()
        current = int(self.settings.value("github/poll_interval_minutes", 15))
        index = self.interval.findData(current)
        self.interval.setCurrentIndex(max(0, index))
        self.interval.currentIndexChanged.connect(lambda _i: self.settings.set_value("github/poll_interval_minutes", int(self.interval.currentData())))
        self.github_button = QPushButton()
        self.github_button.clicked.connect(self.githubRequested)
        self.interval_label = QLabel()
        github_form.addRow(self.startup)
        github_form.addRow(self.interval_label, self.interval)
        github_form.addRow(self.github_button)

        self.privacy = QGroupBox()
        privacy_layout = QVBoxLayout(self.privacy)
        self.privacy_text = QLabel()
        self.privacy_text.setWordWrap(True)
        privacy_layout.addWidget(self.privacy_text)

        root.addWidget(self.language_group)
        root.addWidget(self.general)
        root.addWidget(self.github)
        root.addWidget(self.privacy)
        root.addStretch(1)
        self.i18n.languageChanged.connect(lambda _language: self.retranslate_ui())
        self.retranslate_ui()

    def _language_selected(self, _index: int) -> None:
        value = self.language_combo.currentData()
        if value:
            self.i18n.set_language(str(value))

    def _rebuild_interval(self) -> None:
        current = self.interval.currentData() if self.interval.count() else None
        self.interval.blockSignals(True)
        self.interval.clear()
        for minutes in (5, 15, 30, 60):
            self.interval.addItem(self.i18n.t("settings.minutes", minutes=minutes), minutes)
        index = self.interval.findData(current)
        if index >= 0:
            self.interval.setCurrentIndex(index)
        self.interval.blockSignals(False)

    def retranslate_ui(self) -> None:
        self.title.setText(self.i18n.t("settings.title"))
        self.subtitle.setText(self.i18n.t("settings.subtitle"))
        self.language_group.setTitle(self.i18n.t("settings.language_group"))
        self.language_label.setText(self.i18n.t("settings.language"))
        self.language_help.setText(self.i18n.t("settings.language_help"))
        self.general.setTitle(self.i18n.t("settings.general"))
        self.general_help.setText(self.i18n.t("settings.preferences_help"))
        self.prefs_button.setText(self.i18n.t("settings.preferences"))
        self.github.setTitle(self.i18n.t("settings.github"))
        self.startup.setText(self.i18n.t("settings.startup"))
        self.interval_label.setText(self.i18n.t("settings.interval"))
        self.github_button.setText(self.i18n.t("settings.open_github"))
        self.privacy.setTitle(self.i18n.t("settings.privacy"))
        self.privacy_text.setText(self.i18n.t("settings.privacy_text"))
        self.language_combo.setToolTip(self.i18n.t("top.language_tip"))
        self.prefs_button.setToolTip(
            "Tema, otomatik kayıt ve not editörü gibi daha ayrıntılı seçenekleri açar."
            if self.i18n.language == "tr" else
            "Open detailed options such as theme, autosave and note-editor behavior."
        )
        self.startup.setToolTip(
            "Açıksa DevNest başladığında bağlı depolarda yeni değişiklik var mı diye arka planda kontrol eder."
            if self.i18n.language == "tr" else
            "When enabled, DevNest checks connected repositories for new changes in the background after startup."
        )
        self.interval.setToolTip(
            "DevNest açıkken GitHub depolarının ne sıklıkla yeniden kontrol edileceğini seçer."
            if self.i18n.language == "tr" else
            "Choose how often DevNest re-checks GitHub repositories while the app is open."
        )
        self.github_button.setToolTip(self.i18n.t("tip.nav.github"))
        self._rebuild_interval()
        index = self.language_combo.findData(self.i18n.language)
        if index >= 0 and index != self.language_combo.currentIndex():
            self.language_combo.blockSignals(True)
            self.language_combo.setCurrentIndex(index)
            self.language_combo.blockSignals(False)

    def _bool(self, key: str, default: bool) -> bool:
        value = self.settings.value(key, default)
        if isinstance(value, str):
            return value.lower() in {"1", "true", "yes", "on"}
        return bool(value)

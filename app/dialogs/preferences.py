from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QVBoxLayout,
)

from app.constants import MAX_AUTOSAVE_DELAY_MS, MIN_AUTOSAVE_DELAY_MS
from app.i18n import I18n
from app.settings import AppPreferences
from app.themes.theme_manager import THEME_OPTIONS, UI_MODE_OPTIONS
from app.widgets.no_wheel_spinbox import NoWheelSpinBox


class PreferencesDialog(QDialog):
    def __init__(self, prefs: AppPreferences, i18n: I18n | None = None, parent=None) -> None:
        super().__init__(parent)
        self.i18n = i18n
        tr = bool(i18n and i18n.language == "tr")
        self.setWindowTitle("Tercihler" if tr else "Preferences")
        self.setMinimumWidth(450)
        root = QVBoxLayout(self)

        general = QGroupBox("Genel" if tr else "General")
        general_form = QFormLayout(general)
        self.autosave = QCheckBox("Otomatik kaydı aç" if tr else "Enable autosave")
        self.autosave.setChecked(prefs.autosave_enabled)
        self.autosave.setToolTip(
            "Not yazarken değişiklikleri siz Kaydet demeden otomatik kaydeder."
            if tr else "Save note changes automatically while you type, without needing a Save button."
        )
        self.autosave_delay = NoWheelSpinBox()
        self.autosave_delay.setRange(MIN_AUTOSAVE_DELAY_MS, MAX_AUTOSAVE_DELAY_MS)
        self.autosave_delay.setSingleStep(100)
        self.autosave_delay.setSuffix(" ms")
        self.autosave_delay.setValue(prefs.autosave_delay_ms)
        self.start_last = QCheckBox("Son açılan notla başla" if tr else "Start with last opened note")
        self.start_last.setChecked(prefs.start_with_last_note)
        general_form.addRow(self.autosave)
        general_form.addRow("Otomatik kayıt bekleme:" if tr else "Autosave delay:", self.autosave_delay)
        general_form.addRow(self.start_last)

        editor = QGroupBox("Editör" if tr else "Editor")
        editor_form = QFormLayout(editor)
        self.font_size = NoWheelSpinBox()
        self.font_size.setRange(8, 36)
        self.font_size.setValue(prefs.editor_font_size)
        self.tab_width = NoWheelSpinBox()
        self.tab_width.setRange(2, 8)
        self.tab_width.setValue(prefs.tab_width)
        self.auto_checkbox = QCheckBox("Onay kutusunu varsayılan olarak otomatik sürdür" if tr else "Auto Checkbox by default")
        self.auto_checkbox.setChecked(prefs.auto_checkbox_default)
        self.blank_line_after_enter = QCheckBox("Çift Enter" if tr else "Double Enter")
        self.blank_line_after_enter.setChecked(prefs.blank_line_after_enter)
        self.blank_line_after_enter.setToolTip(
            "Açıksa Enter'a bir kez basınca arada bir boş satır bırakır."
            if tr else "When enabled, one Enter leaves an extra blank line between paragraphs."
        )
        self.word_wrap = QCheckBox("Uzun satırları pencereye sığdır" if tr else "Word wrap")
        self.word_wrap.setChecked(prefs.word_wrap)
        editor_form.addRow("Yazı boyutu:" if tr else "Font size:", self.font_size)
        editor_form.addRow("Tab genişliği (boşluk):" if tr else "Tab width (spaces):", self.tab_width)
        editor_form.addRow(self.auto_checkbox)
        editor_form.addRow(self.blank_line_after_enter)
        editor_form.addRow(self.word_wrap)

        appearance = QGroupBox("Görünüm" if tr else "Appearance")
        appearance_form = QFormLayout(appearance)
        self.theme = QComboBox()
        for label, value in THEME_OPTIONS:
            translated = {
                "System": "Sistem",
                "Matte Black": "Mat Siyah",
                "Midnight Slate": "Gece Mavisi",
                "Graphite": "Grafit",
                "Clean Light": "Temiz Açık",
                "Soft Gray": "Yumuşak Gri",
                "Warm Paper": "Sıcak Kağıt",
                "Cool Mist": "Soğuk Sis",
            }.get(label, label) if tr else label
            self.theme.addItem(translated, value)
        index = self.theme.findData(prefs.theme)
        self.theme.setCurrentIndex(max(0, index))
        appearance_form.addRow("Renk teması:" if tr else "Color theme:", self.theme)
        self.ui_mode = QComboBox()
        for label, value in UI_MODE_OPTIONS:
            self.ui_mode.addItem(("Klasik" if value == "classic" else "Modern") if tr else label, value)
        mode_index = self.ui_mode.findData(prefs.ui_mode)
        self.ui_mode.setCurrentIndex(max(0, mode_index))
        self.ui_mode.setToolTip(
            "Klasik ve modern arayüz stilleri arasında geçiş yapar. Seçtiğiniz renk teması korunur."
            if tr else "Switch between Classic and Modern interface styles. Your selected color theme is preserved."
        )
        appearance_form.addRow("Arayüz stili:" if tr else "Interface style:", self.ui_mode)

        github = QGroupBox("GitHub")
        github_form = QFormLayout(github)
        self.github_startup = QCheckBox("Uygulama açılırken depoları kontrol et" if tr else "Check repositories on startup")
        self.github_startup.setChecked(prefs.check_repositories_on_startup)
        self.github_interval = NoWheelSpinBox()
        self.github_interval.setRange(5, 120)
        self.github_interval.setSuffix(" dk" if tr else " min")
        self.github_interval.setValue(prefs.github_poll_interval_minutes)
        github_form.addRow(self.github_startup)
        github_form.addRow("Kontrol sıklığı:" if tr else "Polling interval:", self.github_interval)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        if tr:
            buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Uygula")
            buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("İptal")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root.addWidget(general)
        root.addWidget(editor)
        root.addWidget(appearance)
        root.addWidget(github)
        root.addWidget(buttons)

    def preferences(self) -> AppPreferences:
        return AppPreferences(
            theme=str(self.theme.currentData()),
            ui_mode=str(self.ui_mode.currentData() or "classic"),
            autosave_enabled=self.autosave.isChecked(),
            autosave_delay_ms=self.autosave_delay.value(),
            start_with_last_note=self.start_last.isChecked(),
            editor_font_size=self.font_size.value(),
            tab_width=self.tab_width.value(),
            auto_checkbox_default=self.auto_checkbox.isChecked(),
            blank_line_after_enter=self.blank_line_after_enter.isChecked(),
            word_wrap=self.word_wrap.isChecked(),
            check_repositories_on_startup=self.github_startup.isChecked(),
            github_poll_interval_minutes=self.github_interval.value(),
        )

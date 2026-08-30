from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QVBoxLayout,
)

from app.constants import MAX_AUTOSAVE_DELAY_MS, MIN_AUTOSAVE_DELAY_MS
from app.settings import AppPreferences
from app.themes.theme_manager import THEME_OPTIONS


class PreferencesDialog(QDialog):
    def __init__(self, prefs: AppPreferences, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setMinimumWidth(420)
        root = QVBoxLayout(self)

        general = QGroupBox("General")
        general_form = QFormLayout(general)
        self.autosave = QCheckBox("Enable autosave")
        self.autosave.setChecked(prefs.autosave_enabled)
        self.autosave_delay = QSpinBox()
        self.autosave_delay.setRange(MIN_AUTOSAVE_DELAY_MS, MAX_AUTOSAVE_DELAY_MS)
        self.autosave_delay.setSingleStep(100)
        self.autosave_delay.setSuffix(" ms")
        self.autosave_delay.setValue(prefs.autosave_delay_ms)
        self.start_last = QCheckBox("Start with last opened note")
        self.start_last.setChecked(prefs.start_with_last_note)
        general_form.addRow(self.autosave)
        general_form.addRow("Autosave delay:", self.autosave_delay)
        general_form.addRow(self.start_last)

        editor = QGroupBox("Editor")
        editor_form = QFormLayout(editor)
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 36)
        self.font_size.setValue(prefs.editor_font_size)
        self.tab_width = QSpinBox()
        self.tab_width.setRange(2, 8)
        self.tab_width.setValue(prefs.tab_width)
        self.auto_checkbox = QCheckBox("Auto Checkbox by default")
        self.auto_checkbox.setChecked(prefs.auto_checkbox_default)
        self.blank_line_after_enter = QCheckBox("Leave one blank line after Enter")
        self.blank_line_after_enter.setChecked(prefs.blank_line_after_enter)
        self.blank_line_after_enter.setToolTip("Pressing Enter advances by two lines, leaving one empty line in between.")
        self.word_wrap = QCheckBox("Word wrap")
        self.word_wrap.setChecked(prefs.word_wrap)
        editor_form.addRow("Font size:", self.font_size)
        editor_form.addRow("Tab width (spaces):", self.tab_width)
        editor_form.addRow(self.auto_checkbox)
        editor_form.addRow(self.blank_line_after_enter)
        editor_form.addRow(self.word_wrap)

        appearance = QGroupBox("Appearance")
        appearance_form = QFormLayout(appearance)
        self.theme = QComboBox()
        for label, value in THEME_OPTIONS:
            self.theme.addItem(label, value)
        index = self.theme.findData(prefs.theme)
        self.theme.setCurrentIndex(max(0, index))
        appearance_form.addRow("Theme:", self.theme)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root.addWidget(general)
        root.addWidget(editor)
        root.addWidget(appearance)
        root.addWidget(buttons)

    def preferences(self) -> AppPreferences:
        return AppPreferences(
            theme=str(self.theme.currentData()),
            autosave_enabled=self.autosave.isChecked(),
            autosave_delay_ms=self.autosave_delay.value(),
            start_with_last_note=self.start_last.isChecked(),
            editor_font_size=self.font_size.value(),
            tab_width=self.tab_width.value(),
            auto_checkbox_default=self.auto_checkbox.isChecked(),
            blank_line_after_enter=self.blank_line_after_enter.isChecked(),
            word_wrap=self.word_wrap.isChecked(),
        )

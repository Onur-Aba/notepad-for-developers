from __future__ import annotations

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QKeySequenceEdit,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.constants import COMMAND_SHORTCUTS, MAX_AUTOSAVE_DELAY_MS, MIN_AUTOSAVE_DELAY_MS
from app.i18n import I18n, LANGUAGE_OPTIONS
from app.settings import AppPreferences, SettingsManager
from app.widgets.no_wheel_spinbox import NoWheelSpinBox
from app.themes.theme_manager import THEME_OPTIONS


class SettingsPage(QWidget):
    preferencesRequested = Signal()
    githubRequested = Signal()
    preferencesChanged = Signal()
    backupRequested = Signal()
    exportProjectRequested = Signal()
    importProjectRequested = Signal()
    diagnosticsRequested = Signal()
    shortcutsChanged = Signal()

    def __init__(self, settings: SettingsManager, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.i18n = i18n
        self._loading = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        outer.addWidget(self.scroll, 1)

        viewport = QWidget()
        self.scroll.setWidget(viewport)
        center = QHBoxLayout(viewport)
        center.setContentsMargins(24, 24, 24, 32)
        center.addStretch(1)

        self.content = QWidget()
        self.content.setObjectName("settingsContent")
        self.content.setMaximumWidth(980)
        self.content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        root = QVBoxLayout(self.content)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(18)
        center.addWidget(self.content, 1)
        center.addStretch(1)

        self.title = QLabel()
        self.title.setObjectName("pageTitle")
        self.subtitle = QLabel()
        self.subtitle.setWordWrap(True)
        self.subtitle.setObjectName("pageSubtitle")
        root.addWidget(self.title)
        root.addWidget(self.subtitle)

        self.language_group = self._group()
        language_form = self._form(self.language_group)
        self.language_combo = self._combo()
        for label, value in LANGUAGE_OPTIONS:
            self.language_combo.addItem(label, value)
        self.language_combo.currentIndexChanged.connect(self._language_selected)
        self.language_help = QLabel()
        self.language_help.setWordWrap(True)
        self.language_help.setObjectName("settingHelp")
        self.language_label = QLabel()
        self.language_label.setObjectName("settingLabel")
        language_form.addRow(self.language_label, self.language_combo)
        language_form.addRow(self.language_help)

        self.general = self._group()
        general_form = self._form(self.general)
        self.autosave = self._check()
        self.autosave_delay = self._spin()
        self.autosave_delay.setRange(MIN_AUTOSAVE_DELAY_MS, MAX_AUTOSAVE_DELAY_MS)
        self.autosave_delay.setSingleStep(100)
        self.autosave_delay.setSuffix(" ms")
        self.start_last = self._check()
        self.autosave_delay_label = self._label()
        general_form.addRow(self.autosave)
        general_form.addRow(self.autosave_delay_label, self.autosave_delay)
        general_form.addRow(self.start_last)

        self.editor_group = self._group()
        editor_form = self._form(self.editor_group)
        self.font_size = self._spin()
        self.font_size.setRange(8, 36)
        self.tab_width = self._spin()
        self.tab_width.setRange(2, 8)
        self.auto_checkbox = self._check()
        self.blank_line_after_enter = self._check()
        self.word_wrap = self._check()
        self.font_size_label = self._label()
        self.tab_width_label = self._label()
        editor_form.addRow(self.font_size_label, self.font_size)
        editor_form.addRow(self.tab_width_label, self.tab_width)
        editor_form.addRow(self.auto_checkbox)
        editor_form.addRow(self.blank_line_after_enter)
        editor_form.addRow(self.word_wrap)

        self.appearance_group = self._group()
        appearance_form = self._form(self.appearance_group)
        self.theme_combo = self._combo()
        self.theme_label = self._label()
        appearance_form.addRow(self.theme_label, self.theme_combo)

        self.shortcuts_group = self._group()
        shortcuts_form = self._form(self.shortcuts_group)
        self.shortcut_edits: dict[str, QKeySequenceEdit] = {}
        self.shortcut_labels: dict[str, QLabel] = {}
        for command_id, (label, default_shortcut) in COMMAND_SHORTCUTS.items():
            caption = QLabel(label)
            caption.setObjectName("settingLabel")
            edit = QKeySequenceEdit(QKeySequence(self.settings.command_shortcut(command_id, default_shortcut)))
            edit.setMinimumHeight(38)
            edit.editingFinished.connect(lambda cid=command_id, e=edit, default=default_shortcut: self._shortcut_changed(cid, e, default))
            shortcuts_form.addRow(caption, edit)
            self.shortcut_labels[command_id] = caption
            self.shortcut_edits[command_id] = edit

        self.workspace_group = self._group()
        workspace_layout = QVBoxLayout(self.workspace_group)
        workspace_layout.setContentsMargins(18, 24, 18, 18)
        workspace_layout.setSpacing(10)
        self.workspace_help = QLabel(); self.workspace_help.setWordWrap(True); self.workspace_help.setObjectName("settingHelp")
        workspace_layout.addWidget(self.workspace_help)
        data_row = QHBoxLayout()
        self.backup_button = QPushButton(); self.backup_button.clicked.connect(self.backupRequested)
        self.export_project_button = QPushButton(); self.export_project_button.clicked.connect(self.exportProjectRequested)
        self.import_project_button = QPushButton(); self.import_project_button.clicked.connect(self.importProjectRequested)
        self.diagnostics_button = QPushButton(); self.diagnostics_button.clicked.connect(self.diagnosticsRequested)
        for button in (self.backup_button, self.export_project_button, self.import_project_button, self.diagnostics_button):
            button.setMinimumHeight(38); data_row.addWidget(button)
        workspace_layout.addLayout(data_row)

        self.github = self._group()
        github_form = self._form(self.github)
        self.startup = self._check()
        self.interval = self._combo()
        self.interval_label = self._label()
        self.github_button = QPushButton()
        self.github_button.setMinimumHeight(38)
        self.github_button.clicked.connect(self.githubRequested)
        github_form.addRow(self.startup)
        github_form.addRow(self.interval_label, self.interval)
        github_form.addRow(self.github_button)

        self.more_group = self._group()
        more_layout = QVBoxLayout(self.more_group)
        more_layout.setContentsMargins(18, 22, 18, 18)
        more_layout.setSpacing(12)
        self.general_help = QLabel()
        self.general_help.setWordWrap(True)
        self.general_help.setObjectName("settingHelp")
        self.prefs_button = QPushButton()
        self.prefs_button.setMinimumHeight(38)
        self.prefs_button.clicked.connect(self.preferencesRequested)
        more_layout.addWidget(self.general_help)
        more_layout.addWidget(self.prefs_button, 0, Qt.AlignmentFlag.AlignLeft)

        self.privacy = self._group()
        privacy_layout = QVBoxLayout(self.privacy)
        privacy_layout.setContentsMargins(18, 22, 18, 18)
        self.privacy_text = QLabel()
        self.privacy_text.setWordWrap(True)
        self.privacy_text.setObjectName("settingHelp")
        privacy_layout.addWidget(self.privacy_text)

        for section in (
            self.language_group,
            self.general,
            self.editor_group,
            self.appearance_group,
            self.shortcuts_group,
            self.workspace_group,
            self.github,
            self.more_group,
            self.privacy,
        ):
            root.addWidget(section)
        root.addStretch(1)

        self.sections = {
            "language": self.language_group,
            "saving": self.general,
            "editor": self.editor_group,
            "appearance": self.appearance_group,
            "shortcuts": self.shortcuts_group,
            "workspace": self.workspace_group,
            "github": self.github,
            "advanced": self.more_group,
            "privacy": self.privacy,
        }

        for control in (
            self.autosave,
            self.autosave_delay,
            self.start_last,
            self.font_size,
            self.tab_width,
            self.auto_checkbox,
            self.blank_line_after_enter,
            self.word_wrap,
            self.theme_combo,
            self.startup,
            self.interval,
        ):
            if isinstance(control, QCheckBox):
                control.toggled.connect(self._save_immediate)
            elif isinstance(control, NoWheelSpinBox):
                control.valueChanged.connect(self._save_immediate)
            else:
                control.currentIndexChanged.connect(self._save_immediate)

        self.i18n.languageChanged.connect(lambda _language: self.retranslate_ui())
        self.retranslate_ui()
        self.sync_from_preferences(self.settings.preferences())

    @staticmethod
    def _group() -> QGroupBox:
        group = QGroupBox()
        group.setObjectName("settingsCard")
        return group

    @staticmethod
    def _form(group: QGroupBox) -> QFormLayout:
        form = QFormLayout(group)
        form.setContentsMargins(18, 24, 18, 18)
        form.setHorizontalSpacing(24)
        form.setVerticalSpacing(14)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        return form

    @staticmethod
    def _label() -> QLabel:
        label = QLabel()
        label.setObjectName("settingLabel")
        label.setWordWrap(True)
        return label

    @staticmethod
    def _combo() -> QComboBox:
        combo = QComboBox()
        combo.setMinimumHeight(38)
        combo.setMinimumWidth(260)
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return combo

    @staticmethod
    def _spin() -> NoWheelSpinBox:
        spin = NoWheelSpinBox()
        spin.setMinimumHeight(38)
        spin.setMinimumWidth(170)
        return spin

    @staticmethod
    def _check() -> QCheckBox:
        check = QCheckBox()
        check.setMinimumHeight(30)
        return check

    def _language_selected(self, _index: int) -> None:
        if self._loading:
            return
        value = self.language_combo.currentData()
        if value:
            self.i18n.set_language(str(value))

    def _rebuild_interval(self) -> None:
        current = self.interval.currentData() if self.interval.count() else self.settings.preferences().github_poll_interval_minutes
        self.interval.blockSignals(True)
        self.interval.clear()
        for minutes in (5, 15, 30, 60, 120):
            self.interval.addItem(self.i18n.t("settings.minutes", minutes=minutes), minutes)
        index = self.interval.findData(current)
        self.interval.setCurrentIndex(max(0, index))
        self.interval.blockSignals(False)

    def _rebuild_themes(self) -> None:
        current = self.theme_combo.currentData() if self.theme_combo.count() else self.settings.preferences().theme
        tr = self.i18n.language == "tr"
        translated = {
            "System": "Sistem",
            "Matte Black": "Mat Siyah",
            "Midnight Slate": "Gece Mavisi",
            "Graphite": "Grafit",
            "Clean Light": "Temiz Açık",
            "Soft Gray": "Yumuşak Gri",
            "Warm Paper": "Sıcak Kağıt",
            "Cool Mist": "Soğuk Sis",
        }
        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()
        for label, value in THEME_OPTIONS:
            self.theme_combo.addItem(translated.get(label, label) if tr else label, value)
        index = self.theme_combo.findData(current)
        self.theme_combo.setCurrentIndex(max(0, index))
        self.theme_combo.blockSignals(False)

    def retranslate_ui(self) -> None:
        tr = self.i18n.language == "tr"
        self.title.setText(self.i18n.t("settings.title"))
        self.subtitle.setText(
            "Ayarları rahatça değiştirebilmeniz için bu sayfa bilerek dar bir içerik sütununda ve kaydırılabilir tasarlandı. Değişiklikler anında kaydedilir."
            if tr else
            "This page intentionally uses a comfortable, scrollable content column so controls stay easy to read and click. Changes are saved immediately."
        )
        self.language_group.setTitle(self.i18n.t("settings.language_group"))
        self.language_label.setText(self.i18n.t("settings.language"))
        self.language_help.setText(self.i18n.t("settings.language_help"))

        self.general.setTitle("Kayıt ve açılış" if tr else "Saving and startup")
        self.autosave.setText("Notları otomatik kaydet" if tr else "Autosave notes")
        self.autosave_delay_label.setText("Yazmayı bıraktıktan sonra bekleme süresi" if tr else "Delay after you stop typing")
        self.start_last.setText("Açılışta son kullandığım notu aç" if tr else "Open my last note at startup")

        self.editor_group.setTitle("Not editörü" if tr else "Note editor")
        self.font_size_label.setText("Varsayılan yazı boyutu" if tr else "Default font size")
        self.tab_width_label.setText("Tab tuşunun boşluk sayısı" if tr else "Tab width in spaces")
        self.auto_checkbox.setText("Onay kutusu yazarken yenisini otomatik oluştur" if tr else "Continue checkboxes automatically")
        self.blank_line_after_enter.setText("Enter'dan sonra ekstra boş satır bırak" if tr else "Leave an extra blank line after Enter")
        self.word_wrap.setText("Uzun satırları pencereye sığdır" if tr else "Wrap long lines to the window")

        self.appearance_group.setTitle("Görünüm" if tr else "Appearance")
        self.theme_label.setText("Tema" if tr else "Theme")
        self._rebuild_themes()

        self.shortcuts_group.setTitle("Klavye kısayolları / Komut Paleti" if tr else "Keyboard shortcuts / Command Palette")
        command_tr = {"command_palette":"Komut Paleti", "create_decision":"Karar Oluştur", "open_projects":"Proje Aç", "search_notes":"Notlarda Ara", "review_inbox":"İnceleme Kutusu", "switch_theme":"Tema Değiştir", "open_repository":"Repository Aç"}
        for command_id, (label, _default) in COMMAND_SHORTCUTS.items():
            self.shortcut_labels[command_id].setText(command_tr.get(command_id, label) if tr else label)
        self.workspace_group.setTitle("Workspace verileri" if tr else "Workspace data")
        self.workspace_help.setText("SQLite backup alın, projeyi seçilebilir içeriklerle dışa/içe aktarın veya repository erişimini tanılayın." if tr else "Create SQLite backups, export/import selectable project content, or diagnose repository access.")
        self.backup_button.setText("Backup Yöneticisi" if tr else "Backup Manager")
        self.export_project_button.setText("Projeyi Dışa Aktar" if tr else "Export Project")
        self.import_project_button.setText("Projeyi İçe Aktar" if tr else "Import Project")
        self.diagnostics_button.setText("Repo Tanılama" if tr else "Repo Diagnostics")

        self.github.setTitle(self.i18n.t("settings.github"))
        self.startup.setText(self.i18n.t("settings.startup"))
        self.interval_label.setText(self.i18n.t("settings.interval"))
        self.github_button.setText(self.i18n.t("settings.open_github"))
        self._rebuild_interval()

        self.more_group.setTitle("Gelişmiş tercihler" if tr else "Advanced preferences")
        self.general_help.setText(
            "Eski Tercihler penceresini kaldırmadım. Burada olmayan daha ayrıntılı seçeneklere ihtiyaç duyarsanız aynı pencereyi açabilirsiniz."
            if tr else
            "The existing Preferences dialog is still available. Open it if you need the more detailed options that are not shown on this page."
        )
        self.prefs_button.setText(self.i18n.t("settings.preferences"))

        self.privacy.setTitle(self.i18n.t("settings.privacy"))
        self.privacy_text.setText(self.i18n.t("settings.privacy_text"))

        self.language_combo.setToolTip(self.i18n.t("top.language_tip"))
        self.theme_combo.setToolTip(
            "Uygulamanın renklerini anında değiştirir; notlarınızı veya kodunuzu değiştirmez."
            if tr else
            "Change the app colors instantly; this does not change your notes or code."
        )
        self.prefs_button.setToolTip(
            "Aynı tercihlerin ayrıntılı, ayrı pencere görünümünü açar."
            if tr else
            "Open the detailed separate Preferences window."
        )
        self.startup.setToolTip(
            "Açıksa DevNest başladığında bağlı depolarda yeni değişiklik var mı diye arka planda kontrol eder."
            if tr else
            "When enabled, DevNest checks connected repositories for changes in the background after startup."
        )
        self.interval.setToolTip(
            "DevNest açıkken GitHub depolarının ne sıklıkla yeniden kontrol edileceğini seçer."
            if tr else
            "Choose how often DevNest re-checks GitHub repositories while the app is open."
        )
        self.github_button.setToolTip(self.i18n.t("tip.nav.github"))

        index = self.language_combo.findData(self.i18n.language)
        if index >= 0 and index != self.language_combo.currentIndex():
            self.language_combo.blockSignals(True)
            self.language_combo.setCurrentIndex(index)
            self.language_combo.blockSignals(False)

    @staticmethod
    def _search_normalize(value: str) -> str:
        # Turkish dotted/dotless I should behave naturally in the settings search.
        return value.replace("İ", "i").replace("I", "ı").casefold().strip()

    def _section_search_text(self, section: QWidget) -> str:
        parts: list[str] = []
        if isinstance(section, QGroupBox):
            parts.append(section.title())
        for widget in section.findChildren(QWidget):
            if isinstance(widget, QLabel):
                parts.append(widget.text())
            elif isinstance(widget, QCheckBox):
                parts.append(widget.text())
            elif isinstance(widget, QPushButton):
                parts.append(widget.text())
            elif isinstance(widget, QComboBox):
                parts.extend(widget.itemText(i) for i in range(widget.count()))
            tooltip = widget.toolTip()
            if tooltip:
                parts.append(tooltip)
        return self._search_normalize(" ".join(parts))

    def filter_settings(self, query: str) -> str | None:
        """Filter setting cards live and return the first matching section key."""
        normalized = self._search_normalize(query)
        first: str | None = None
        for key, section in self.sections.items():
            matches = not normalized or normalized in self._section_search_text(section)
            section.setVisible(matches)
            if matches and first is None:
                first = key
        if first is not None:
            QTimer.singleShot(0, lambda key=first: self.scroll_to_section(key))
        return first

    def scroll_to_section(self, key: str) -> None:
        section = self.sections.get(key)
        if section is None or not section.isVisible():
            return
        self.scroll.ensureWidgetVisible(section, 0, 18)

    def sync_from_preferences(self, prefs: AppPreferences) -> None:
        self._loading = True
        try:
            self.autosave.setChecked(prefs.autosave_enabled)
            self.autosave_delay.setValue(prefs.autosave_delay_ms)
            self.start_last.setChecked(prefs.start_with_last_note)
            self.font_size.setValue(prefs.editor_font_size)
            self.tab_width.setValue(prefs.tab_width)
            self.auto_checkbox.setChecked(prefs.auto_checkbox_default)
            self.blank_line_after_enter.setChecked(prefs.blank_line_after_enter)
            self.word_wrap.setChecked(prefs.word_wrap)
            theme_index = self.theme_combo.findData(prefs.theme)
            if theme_index >= 0:
                self.theme_combo.setCurrentIndex(theme_index)
            self.startup.setChecked(prefs.check_repositories_on_startup)
            interval_index = self.interval.findData(prefs.github_poll_interval_minutes)
            if interval_index < 0:
                interval_index = self.interval.findData(15)
            self.interval.setCurrentIndex(max(0, interval_index))
        finally:
            self._loading = False

    def current_preferences(self) -> AppPreferences:
        return AppPreferences(
            theme=str(self.theme_combo.currentData() or "system"),
            autosave_enabled=self.autosave.isChecked(),
            autosave_delay_ms=self.autosave_delay.value(),
            start_with_last_note=self.start_last.isChecked(),
            editor_font_size=self.font_size.value(),
            tab_width=self.tab_width.value(),
            auto_checkbox_default=self.auto_checkbox.isChecked(),
            blank_line_after_enter=self.blank_line_after_enter.isChecked(),
            word_wrap=self.word_wrap.isChecked(),
            check_repositories_on_startup=self.startup.isChecked(),
            github_poll_interval_minutes=int(self.interval.currentData() or 15),
        )

    def _shortcut_changed(self, command_id: str, edit: QKeySequenceEdit, default: str) -> None:
        sequence = edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText)
        self.settings.set_command_shortcut(command_id, sequence or default)
        self.shortcutsChanged.emit()

    def _save_immediate(self, *_args) -> None:
        if self._loading:
            return
        self.settings.save_preferences(self.current_preferences())
        self.preferencesChanged.emit()

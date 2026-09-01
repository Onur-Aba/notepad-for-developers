from __future__ import annotations

import logging
import re
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QActionGroup, QCloseEvent, QDragEnterEvent, QDropEvent, QFontDatabase, QKeySequence, QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.constants import APP_NAME, DEFAULT_NOTE_TITLE, SHORTCUTS, VERSION
from app.i18n import I18n, LANGUAGE_OPTIONS
from app.database import Database, DatabaseError
from app.dialogs.preferences import PreferencesDialog
from app.dialogs.shortcuts import ShortcutsDialog
from app.dialogs.trash import TrashDialog
from app.models import Note, ResourceType, ReviewStatus, ReviewSummary
from app.integrations.github.browser import BrowserLauncher
from app.integrations.github.client import GitHubClient
from app.integrations.github.config import GitHubConfig
from app.pages.architecture_page import ArchitecturePage
from app.pages.dashboard_page import DashboardPage
from app.pages.decisions_page import DecisionsPage
from app.pages.github_page import GitHubPage
from app.pages.project_detail_page import ProjectDetailPage
from app.pages.projects_page import ProjectsPage
from app.pages.review_inbox_page import ReviewInboxPage
from app.pages.settings_page import SettingsPage
from app.services.async_tasks import AsyncTaskRunner
from app.services.change_detection_service import ChangeDetectionService
from app.services.credential_store import create_default_credential_store
from app.services.local_git_service import LocalGitService
from app.services.project_service import ProjectService
from app.services.repository_service import RepositoryService
from app.services.resource_link_service import ResourceLinkService
from app.services.review_service import ReviewService
from app.paths import database_path
from app.services.txt_codec import (
    export_internal_plain_text,
    import_text_to_html,
    parse_text,
    parsed_to_internal_text,
    read_utf8_text,
    write_utf8_text,
)
from app.settings import AppPreferences, SettingsManager
from app.themes.theme_manager import THEME_OPTIONS, ThemeManager
from app.widgets.diagram_view import DiagramView
from app.widgets.note_editor import NoteEditor
from app.widgets.sidebar import Sidebar
from app.widgets.global_search_dialog import GlobalSearchDialog
from app.widgets.navigation_sidebar import NavigationSidebar
from app.widgets.resource_chip import ResourceChip
from app.widgets.resource_link_dialog import ResourceLinkDialog
from app.widgets.review_details_dialog import ReviewDetailsDialog
from app.widgets.status_badge import StatusBadge

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(
        self,
        database: Database,
        settings: SettingsManager,
        theme_manager: ThemeManager,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.database = database
        self.settings = settings
        self.theme_manager = theme_manager
        self.i18n = I18n(self.settings, self)
        self.preferences = self.settings.preferences()
        self.current_note_id: int | None = None
        self._loading_note = False
        self._dirty = False
        self._diagram_dirty = False
        self._search_term = ""
        self._sort_mode = "updated"
        self.local_git = LocalGitService()
        self.project_service = ProjectService(self.database)
        self.repository_service = RepositoryService(self.database, self.local_git)
        self.resource_link_service = ResourceLinkService(self.database)
        self.review_service = ReviewService(self.database)
        self.credential_store = create_default_credential_store()
        self.github_config = GitHubConfig.from_environment_and_settings(self.settings)
        self.browser_launcher = BrowserLauncher()
        self.task_runner = AsyncTaskRunner()
        saved_project = self.settings.value("session/last_project_id", None)
        try:
            saved_project_id = int(saved_project) if saved_project is not None else None
        except (TypeError, ValueError):
            saved_project_id = None
        self.current_project_id = saved_project_id if saved_project_id and self.database.get_project(saved_project_id) else self.database.default_project_id()
        self._review_summaries: list[ReviewSummary] = []
        self._review_refresh_in_progress = False

        self.setWindowTitle(f"{APP_NAME} — Local-first Developer Workspace")
        self.setMinimumSize(1040, 680)
        self.resize(1440, 900)
        self.setAcceptDrops(True)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.timeout.connect(self.save_current_note)
        self.diagram_timer = QTimer(self)
        self.diagram_timer.setSingleShot(True)
        self.diagram_timer.timeout.connect(self.save_current_diagram)

        self._build_ui()
        self._create_actions()
        self._build_toolbar()
        self._build_menus()
        self._connect_signals()
        self._retranslate_shell()
        self._restore_window_state()
        self._apply_preferences(self.preferences, persist=False)
        self._load_initial_note()

        self.repository_poll_timer = QTimer(self)
        self.repository_poll_timer.timeout.connect(self.refresh_review_inbox)
        self._configure_repository_polling()
        saved_page = str(self.settings.value("session/last_page", "dashboard") or "dashboard")
        self._navigate(saved_page if saved_page in self.pages else "dashboard")
        QTimer.singleShot(0, self._startup_refresh)

    def _build_ui(self) -> None:
        # Existing note/editor/diagram workspace is preserved as the Notes page.
        self.sidebar = Sidebar(self.i18n)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText(DEFAULT_NOTE_TITLE)
        self.title_edit.setObjectName("documentTitle")

        self.editor = NoteEditor()
        self.editor.setAcceptDrops(False)
        self.diagram = DiagramView()
        self.tabs = QTabWidget()
        self.tabs.addTab(self.editor, "Editor")
        self.tabs.addTab(self.diagram, "Diagram")

        self.note_resource_bar = QWidget()
        self.note_resource_bar.setObjectName("resourceBar")
        resource_layout = QVBoxLayout(self.note_resource_bar)
        resource_layout.setContentsMargins(8, 6, 8, 6)
        resource_layout.setSpacing(4)
        resource_top = QHBoxLayout()
        self.note_linked_label = QLabel()
        self.note_linked_label.setObjectName("cardLabel")
        self.note_status_badge = StatusBadge()
        self.note_link_button = QPushButton("Link Resource")
        self.note_view_changes_button = QPushButton("View Changes")
        self.note_mark_reviewed_button = QPushButton("Mark as Reviewed")
        resource_top.addWidget(self.note_linked_label)
        resource_top.addStretch(1)
        resource_top.addWidget(self.note_status_badge)
        resource_top.addWidget(self.note_link_button)
        resource_top.addWidget(self.note_view_changes_button)
        resource_top.addWidget(self.note_mark_reviewed_button)
        self.note_chips_widget = QWidget()
        self.note_chips_layout = QHBoxLayout(self.note_chips_widget)
        self.note_chips_layout.setContentsMargins(0, 0, 0, 0)
        self.note_chips_layout.setSpacing(5)
        resource_layout.addLayout(resource_top)
        resource_layout.addWidget(self.note_chips_widget)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 6)
        content_layout.setSpacing(6)
        content_layout.addWidget(self.title_edit)
        content_layout.addWidget(self.note_resource_bar)
        content_layout.addWidget(self.tabs, 1)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(content)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([280, 940])

        self.workspace_bar = QWidget()
        self.workspace_bar.setObjectName("workspaceBar")
        self.workspace_layout = QHBoxLayout(self.workspace_bar)
        self.workspace_layout.setContentsMargins(8, 5, 8, 5)
        self.workspace_layout.setSpacing(6)

        self.notes_page = QWidget()
        notes_layout = QVBoxLayout(self.notes_page)
        notes_layout.setContentsMargins(0, 0, 0, 0)
        notes_layout.setSpacing(0)
        notes_layout.addWidget(self.workspace_bar)
        notes_layout.addWidget(self.splitter, 1)

        # Product-level pages and services.
        self.dashboard_page = DashboardPage(self.database, self.i18n)
        self.projects_page = ProjectsPage(self.database, self.project_service, self.repository_service, self.i18n)
        self.project_detail_page = ProjectDetailPage(self.database, self.i18n)
        self.decisions_page = DecisionsPage(self.database, self.i18n)
        self.architecture_page = ArchitecturePage(self.database, self.i18n)
        self.review_page = ReviewInboxPage(self.i18n)
        self.github_page = GitHubPage(
            self.database, self.credential_store, self.github_config, self.browser_launcher, self.i18n
        )
        self.github_page.set_current_project(self.current_project_id)
        self.settings_page = SettingsPage(self.settings, self.i18n)

        self.page_stack = QStackedWidget()
        self.pages = {
            "dashboard": self.dashboard_page,
            "projects": self.projects_page,
            "project_detail": self.project_detail_page,
            "notes": self.notes_page,
            "decisions": self.decisions_page,
            "architecture": self.architecture_page,
            "review": self.review_page,
            "github": self.github_page,
            "settings": self.settings_page,
        }
        for page in self.pages.values():
            self.page_stack.addWidget(page)

        self.global_navigation = NavigationSidebar(self.i18n)

        self.top_bar = QWidget()
        self.top_bar.setObjectName("productTopBar")
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(14, 8, 14, 8)
        self.project_selector = QComboBox()
        self.project_selector.setObjectName("projectSelector")
        self.project_selector.setMinimumWidth(220)
        self.global_search = QLineEdit()
        self.global_search.setPlaceholderText("Search projects, notes, decisions…")
        self.global_search.setClearButtonEnabled(True)
        self.github_indicator = QLabel("GitHub Disconnected")
        self.github_indicator.setObjectName("connectivityIndicator")
        self.project_selector_label = QLabel()
        self.project_selector_label.setObjectName("topBarLabel")
        self.language_combo = QComboBox()
        self.language_combo.setObjectName("languageQuickSelect")
        self.language_combo.setFixedWidth(100)
        for label, value in LANGUAGE_OPTIONS:
            self.language_combo.addItem(label, value)
        language_index = self.language_combo.findData(self.i18n.language)
        self.language_combo.setCurrentIndex(max(0, language_index))
        self.language_combo.currentIndexChanged.connect(self._language_quick_selected)
        top_layout.addWidget(self.project_selector_label)
        top_layout.addWidget(self.project_selector)
        top_layout.addStretch(1)
        top_layout.addWidget(self.global_search, 2)
        top_layout.addWidget(self.language_combo)
        top_layout.addWidget(self.github_indicator)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(self.top_bar)
        right_layout.addWidget(self.page_stack, 1)

        central = QWidget()
        central_layout = QHBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self.global_navigation)
        central_layout.addWidget(right, 1)
        self.setCentralWidget(central)

        self.save_label = QLabel()
        self.repository_status_label = QLabel()
        self.stats_label = QLabel("Words: 0  •  Lines: 1  •  Ln 1, Col 1")
        self.statusBar().addWidget(self.save_label)
        self.statusBar().addPermanentWidget(self.repository_status_label)
        self.statusBar().addPermanentWidget(self.stats_label)

        self._refresh_project_selector()
        self.decisions_page.set_project(self.current_project_id)
        self.architecture_page.set_project(self.current_project_id)
        self.project_detail_page.set_project(self.current_project_id)
        self._navigate("dashboard")

    def _create_actions(self) -> None:
        self.new_action = QAction("New Note", self)
        self.new_action.setShortcut(SHORTCUTS["New Note"])
        self.new_action.setToolTip("Create a new note")
        self.new_action.triggered.connect(self.new_note)

        self.delete_action = QAction("Delete", self)
        self.delete_action.setToolTip("Move the current note to Trash")
        self.delete_action.triggered.connect(lambda: self.delete_note(self.current_note_id) if self.current_note_id else None)

        self.import_action = QAction("Import TXT", self)
        self.import_action.triggered.connect(self.import_txt)

        self.export_action = QAction("Export TXT", self)
        self.export_action.setShortcut(SHORTCUTS["Export TXT"])
        self.export_action.triggered.connect(lambda: self.export_note(self.current_note_id) if self.current_note_id else None)

        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.close)

        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.triggered.connect(self.editor.undo)
        self.redo_action = QAction("Redo", self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.triggered.connect(self.editor.redo)
        self.cut_action = QAction("Cut", self)
        self.cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        self.cut_action.triggered.connect(self.editor.cut)
        self.copy_action = QAction("Copy", self)
        self.copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        self.copy_action.triggered.connect(self.editor.copy)
        self.paste_action = QAction("Paste", self)
        self.paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        self.paste_action.triggered.connect(self.editor.paste)
        self.select_all_action = QAction("Select All", self)
        self.select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        self.select_all_action.triggered.connect(self.editor.selectAll)
        self.find_action = QAction("Find", self)
        self.find_action.setShortcut(SHORTCUTS["Find in Note"])
        self.find_action.triggered.connect(self.find_in_note)

        self.checkbox_action = QAction("Checkbox", self)
        self.checkbox_action.setShortcut(SHORTCUTS["Checkbox"])
        self.checkbox_action.triggered.connect(self.editor.insert_checkbox)
        self.auto_checkbox_action = QAction("Auto Checkbox", self)
        self.auto_checkbox_action.setCheckable(True)
        self.auto_checkbox_action.toggled.connect(self._set_auto_checkbox)
        self.blank_line_enter_action = QAction("Double Enter", self)
        self.blank_line_enter_action.setCheckable(True)
        self.blank_line_enter_action.setToolTip("When active, one Enter moves the cursor down by two lines")
        self.blank_line_enter_action.toggled.connect(self._set_blank_line_after_enter)

        self.bold_action = QAction("Bold", self)
        self.bold_action.setShortcut(QKeySequence.StandardKey.Bold)
        self.bold_action.triggered.connect(self.editor.toggle_bold)
        self.italic_action = QAction("Italic", self)
        self.italic_action.setShortcut(QKeySequence.StandardKey.Italic)
        self.italic_action.triggered.connect(self.editor.toggle_italic)
        self.underline_action = QAction("Underline", self)
        self.underline_action.setShortcut(QKeySequence.StandardKey.Underline)
        self.underline_action.triggered.connect(self.editor.toggle_underline)
        self.strike_action = QAction("Strikethrough", self)
        self.strike_action.triggered.connect(self.editor.toggle_strikethrough)
        self.bullet_action = QAction("Bullet List", self)
        self.bullet_action.triggered.connect(self.editor.make_bullet_list)
        self.numbered_action = QAction("List Mode", self)
        self.numbered_action.setCheckable(True)
        self.numbered_action.setToolTip("Write 1., 2., 3. ... as real text and continue numbering with Enter")
        self.numbered_action.toggled.connect(self._set_numbered_list_mode)

        self.toggle_sidebar_action = QAction("Toggle Sidebar", self)
        self.toggle_sidebar_action.setShortcut(SHORTCUTS["Toggle Sidebar"])
        self.toggle_sidebar_action.triggered.connect(self._toggle_sidebar)
        self.editor_tab_action = QAction("Editor", self)
        self.editor_tab_action.setShortcut(SHORTCUTS["Editor Tab"])
        self.editor_tab_action.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        self.diagram_tab_action = QAction("Diagram", self)
        self.diagram_tab_action.setShortcut(SHORTCUTS["Diagram Tab"])
        self.diagram_tab_action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))

        self.preferences_action = QAction("Preferences…", self)
        self.preferences_action.triggered.connect(self.open_preferences)
        self.trash_action = QAction("Trash…", self)
        self.trash_action.triggered.connect(self.open_trash)
        self.shortcuts_action = QAction("Keyboard Shortcuts", self)
        self.shortcuts_action.triggered.connect(lambda: ShortcutsDialog(self).exec())
        self.about_action = QAction("About DevNest", self)
        self.about_action.triggered.connect(self.show_about)

    def _build_toolbar(self) -> None:
        # Two compact rows avoid Qt's overflow "..." extension button even on
        # smaller windows. Workspace navigation is a permanent bar below them.
        self.notes_toolbar = QToolBar("Notes & Format", self)
        notes_toolbar = self.notes_toolbar
        notes_toolbar.setMovable(False)
        notes_toolbar.setFloatable(False)
        notes_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.addToolBar(notes_toolbar)
        for action in [self.new_action, self.delete_action, self.import_action, self.export_action]:
            notes_toolbar.addAction(action)
        notes_toolbar.addSeparator()
        notes_toolbar.addAction(self.checkbox_action)
        notes_toolbar.addAction(self.auto_checkbox_action)
        notes_toolbar.addAction(self.numbered_action)
        notes_toolbar.addAction(self.blank_line_enter_action)
        notes_toolbar.addSeparator()
        for action in [self.bold_action, self.italic_action, self.strike_action, self.bullet_action]:
            notes_toolbar.addAction(action)

        self.addToolBarBreak()
        self.text_toolbar = QToolBar("Text", self)
        text_toolbar = self.text_toolbar
        text_toolbar.setMovable(False)
        text_toolbar.setFloatable(False)
        text_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.addToolBar(text_toolbar)

        self.font_combo = QComboBox()
        self.font_combo.setMinimumWidth(138)
        self.font_combo.setMaximumWidth(190)
        self.font_combo.setToolTip("Font family for selected text or new text")
        self._populate_font_combo()
        self.font_combo.currentIndexChanged.connect(self._apply_font_family_from_toolbar)
        text_toolbar.addWidget(self.font_combo)

        self.font_size_label = QLabel("12 pt")
        self.font_size_label.setMinimumWidth(36)
        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setRange(8, 36)
        self.font_size_slider.setSingleStep(1)
        self.font_size_slider.setPageStep(2)
        self.font_size_slider.setValue(12)
        self.font_size_slider.setFixedWidth(92)
        self.font_size_slider.setToolTip("Text size: 8–36 pt")
        self.font_size_slider.valueChanged.connect(self._apply_font_size_from_toolbar)
        text_toolbar.addWidget(self.font_size_label)
        text_toolbar.addWidget(self.font_size_slider)

        self.font_weight_label = QLabel("W 400")
        self.font_weight_label.setMinimumWidth(42)
        self.font_weight_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_weight_slider.setRange(100, 900)
        self.font_weight_slider.setSingleStep(100)
        self.font_weight_slider.setPageStep(100)
        self.font_weight_slider.setValue(400)
        self.font_weight_slider.setFixedWidth(92)
        self.font_weight_slider.setToolTip("Font weight: 100 thin – 900 black")
        self.font_weight_slider.valueChanged.connect(self._apply_font_weight_from_toolbar)
        text_toolbar.addWidget(self.font_weight_label)
        text_toolbar.addWidget(self.font_weight_slider)
        text_toolbar.addSeparator()
        text_toolbar.addAction(self.undo_action)
        text_toolbar.addAction(self.redo_action)

        # Always-visible workspace controls. They are not QToolBar overflow items,
        # so Qt never moves Editor / Diagram / Theme behind a three-dot button.
        self.editor_workspace_button = QPushButton("Editor")
        self.editor_workspace_button.setObjectName("workspaceButton")
        self.editor_workspace_button.setCheckable(True)
        self.editor_workspace_button.clicked.connect(lambda: self.tabs.setCurrentIndex(0))
        self.diagram_workspace_button = QPushButton("Diagram")
        self.diagram_workspace_button.setObjectName("workspaceButton")
        self.diagram_workspace_button.setCheckable(True)
        self.diagram_workspace_button.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        self.workspace_layout.addWidget(self.editor_workspace_button)
        self.workspace_layout.addWidget(self.diagram_workspace_button)
        self.workspace_layout.addStretch(1)
        self.theme_label = QLabel()
        self.workspace_layout.addWidget(self.theme_label)
        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("themePresetCombo")
        self.theme_combo.setToolTip("Choose a DevNest color theme")
        for label, value in THEME_OPTIONS:
            self.theme_combo.addItem(label, value)
        self.theme_combo.currentIndexChanged.connect(self._theme_combo_changed)
        self.workspace_layout.addWidget(self.theme_combo)
        self._sync_workspace_buttons(self.tabs.currentIndex())

        # Defensive: if the platform style creates an extension button anyway,
        # keep it hidden. Both toolbars are deliberately short enough to fit.
        for toolbar in (notes_toolbar, text_toolbar):
            extension = toolbar.findChild(QToolButton, "qt_toolbar_ext_button")
            if extension is not None:
                extension.hide()

    def _populate_font_combo(self) -> None:
        available = {family.casefold(): family for family in QFontDatabase.families()}
        system_mono = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont).family()
        system_ui = QApplication.font().family()
        choices = [
            ("System Mono", system_mono),
            ("System UI", system_ui),
            ("Cascadia Code", "Cascadia Code"),
            ("Cascadia Mono", "Cascadia Mono"),
            ("Consolas", "Consolas"),
            ("JetBrains Mono", "JetBrains Mono"),
            ("Fira Code", "Fira Code"),
            ("Courier New", "Courier New"),
            ("Segoe UI", "Segoe UI"),
            ("Arial", "Arial"),
        ]
        used: set[str] = set()
        for label, requested in choices:
            family = available.get(requested.casefold())
            if family is None and requested in {system_mono, system_ui}:
                family = requested
            if not family or family.casefold() in used:
                continue
            used.add(family.casefold())
            self.font_combo.addItem(label, family)
        if self.font_combo.count() == 0:
            self.font_combo.addItem(system_mono, system_mono)

    def _apply_font_family_from_toolbar(self, _index: int) -> None:
        family = self.font_combo.currentData()
        if family:
            self.editor.apply_font_family(str(family))
            self.editor.setFocus()

    def _apply_font_size_from_toolbar(self, value: int) -> None:
        self.font_size_label.setText(f"{value} pt")
        self.editor.apply_font_point_size(value)
        self.editor.setFocus()

    def _apply_font_weight_from_toolbar(self, value: int) -> None:
        snapped = max(100, min(900, int(round(value / 100.0) * 100)))
        if snapped != value:
            self.font_weight_slider.blockSignals(True)
            self.font_weight_slider.setValue(snapped)
            self.font_weight_slider.blockSignals(False)
        self.font_weight_label.setText(f"W {snapped}")
        self.editor.apply_font_weight(snapped)
        self.editor.setFocus()

    def _sync_font_controls(self, fmt) -> None:
        size = int(round(fmt.fontPointSize())) if fmt.fontPointSize() > 0 else self.editor.base_font_size
        size = max(self.font_size_slider.minimum(), min(self.font_size_slider.maximum(), size))
        self.font_size_slider.blockSignals(True)
        self.font_size_slider.setValue(size)
        self.font_size_slider.blockSignals(False)
        self.font_size_label.setText(f"{size} pt")

        weight = int(fmt.fontWeight())
        weight = max(100, min(900, int(round(weight / 100.0) * 100)))
        self.font_weight_slider.blockSignals(True)
        self.font_weight_slider.setValue(weight)
        self.font_weight_slider.blockSignals(False)
        self.font_weight_label.setText(f"W {weight}")

        families = fmt.font().families()
        family = families[0] if families else fmt.font().family()
        index = self.font_combo.findData(family)
        if index >= 0:
            self.font_combo.blockSignals(True)
            self.font_combo.setCurrentIndex(index)
            self.font_combo.blockSignals(False)

    def _build_menus(self) -> None:
        menu = self.menuBar()
        self.file_menu = menu.addMenu("File")
        file_menu = self.file_menu
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.import_action)
        file_menu.addAction(self.export_action)
        file_menu.addSeparator()
        file_menu.addAction(self.trash_action)
        file_menu.addAction(self.preferences_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        self.edit_menu = menu.addMenu("Edit")
        edit_menu = self.edit_menu
        for action in [self.undo_action, self.redo_action]:
            edit_menu.addAction(action)
        edit_menu.addSeparator()
        for action in [self.cut_action, self.copy_action, self.paste_action, self.select_all_action]:
            edit_menu.addAction(action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.find_action)

        self.view_menu = menu.addMenu("View")
        view_menu = self.view_menu
        view_menu.addAction(self.toggle_sidebar_action)
        view_menu.addSeparator()
        view_menu.addAction(self.editor_tab_action)
        view_menu.addAction(self.diagram_tab_action)
        self.theme_menu = view_menu.addMenu("Theme")
        theme_menu = self.theme_menu
        self.theme_group = QActionGroup(self)
        self.theme_group.setExclusive(True)
        self.theme_actions: dict[str, QAction] = {}
        for label, value in THEME_OPTIONS:
            action = QAction(label, self, checkable=True)
            action.setData(value)
            action.triggered.connect(lambda _checked=False, t=value: self.set_theme(t))
            self.theme_group.addAction(action)
            theme_menu.addAction(action)
            self.theme_actions[value] = action

        self.format_menu = menu.addMenu("Format")
        format_menu = self.format_menu
        for action in [
            self.checkbox_action,
            self.auto_checkbox_action,
            self.blank_line_enter_action,
            self.bold_action,
            self.italic_action,
            self.underline_action,
            self.strike_action,
            self.bullet_action,
            self.numbered_action,
        ]:
            format_menu.addAction(action)
        self.help_menu = menu.addMenu("Help")
        help_menu = self.help_menu
        help_menu.addAction(self.shortcuts_action)
        help_menu.addAction(self.about_action)

    def _connect_signals(self) -> None:
        self.sidebar.noteSelected.connect(self.open_note)
        self.sidebar.newNoteRequested.connect(self.new_note)
        self.sidebar.trashRequested.connect(self.open_trash)
        self.sidebar.renameRequested.connect(self.rename_note)
        self.sidebar.duplicateRequested.connect(self.duplicate_note)
        self.sidebar.deleteRequested.connect(self.delete_note)
        self.sidebar.exportRequested.connect(self.export_note)
        self.sidebar.searchChanged.connect(self._on_search_changed)
        self.sidebar.sortChanged.connect(self._on_sort_changed)

        self.title_edit.textChanged.connect(self._mark_content_dirty)
        self.editor.textChanged.connect(self._on_editor_changed)
        self.editor.cursorPositionChanged.connect(self._update_stats)
        self.editor.currentCharFormatChanged.connect(self._sync_font_controls)
        self.editor.taskStateChanged.connect(self._mark_content_dirty)
        self.editor.numberedListModeChanged.connect(self._sync_numbered_list_action)
        self.diagram.diagramChanged.connect(self._on_diagram_changed)
        self.diagram.itemsDeleted.connect(lambda ids: self._diagram_items_deleted(self.current_note_id, ids))
        self.tabs.currentChanged.connect(self._sync_workspace_buttons)

        self.global_navigation.pageSelected.connect(self._navigate)
        self.project_selector.currentIndexChanged.connect(self._project_selected)
        self.global_search.returnPressed.connect(self._open_global_search)
        self.note_link_button.clicked.connect(lambda: self._link_resource("note", self.current_note_id))
        self.note_view_changes_button.clicked.connect(lambda: self._view_resource_changes("note", self.current_note_id))
        self.note_mark_reviewed_button.clicked.connect(lambda: self._mark_resource_reviewed("note", self.current_note_id))

        self.dashboard_page.reviewRequested.connect(lambda: self._navigate("review"))
        self.dashboard_page.projectRequested.connect(self._open_project_detail)
        self.projects_page.projectOpened.connect(self._open_project_detail)
        self.projects_page.projectsChanged.connect(self._projects_changed)
        self.projects_page.localRepositoryRequested.connect(self._add_local_repository_async)
        self.project_detail_page.backRequested.connect(lambda: self._navigate("projects"))
        self.project_detail_page.sectionRequested.connect(self._project_section_requested)
        self.project_detail_page.refreshRepositoryRequested.connect(self._refresh_repository_async)

        self.decisions_page.linkResourceRequested.connect(lambda did: self._link_resource("decision", did or None))
        self.decisions_page.viewChangesRequested.connect(lambda did: self._view_resource_changes("decision", did or None))
        self.decisions_page.markReviewedRequested.connect(lambda did: self._mark_resource_reviewed("decision", did or None))
        self.decisions_page.list.currentItemChanged.connect(lambda _current, _previous: QTimer.singleShot(0, self._refresh_decision_status))
        self.architecture_page.diagram.itemsDeleted.connect(lambda ids: self._diagram_items_deleted(self.architecture_page.note_id, ids))
        self.architecture_page.linkNodeRequested.connect(lambda note_id, node_id: self._link_resource("diagram_item", node_id, note_id))
        self.architecture_page.viewChangesRequested.connect(lambda note_id, node_id: self._view_resource_changes("diagram_item", node_id, note_id))
        self.architecture_page.markReviewedRequested.connect(lambda note_id, node_id: self._mark_resource_reviewed("diagram_item", node_id, note_id))

        self.review_page.refreshRequested.connect(self.refresh_review_inbox)
        self.review_page.viewRequested.connect(self._show_review_details)
        self.review_page.markReviewedRequested.connect(self._mark_summary_reviewed)
        self.github_page.connectionStateChanged.connect(self._github_state_changed)
        self.github_page.repositoriesChanged.connect(self._github_repositories_changed)
        self.github_page.linkRepositoryRequested.connect(self._link_github_repository_to_current_project)
        self.settings_page.preferencesRequested.connect(self.open_preferences)
        self.settings_page.githubRequested.connect(lambda: self._navigate("github"))
        self.i18n.languageChanged.connect(self._language_changed)

        color_scheme_changed = getattr(QApplication.styleHints(), "colorSchemeChanged", None)
        if color_scheme_changed is not None:
            color_scheme_changed.connect(self._on_system_color_scheme_changed)

    def _language_quick_selected(self, _index: int) -> None:
        value = self.language_combo.currentData()
        if value:
            self.i18n.set_language(str(value))

    def _language_changed(self, language: str) -> None:
        index = self.language_combo.findData(language)
        if index >= 0 and self.language_combo.currentIndex() != index:
            self.language_combo.blockSignals(True)
            self.language_combo.setCurrentIndex(index)
            self.language_combo.blockSignals(False)
        self._retranslate_shell()
        # Re-render project-scoped information so dynamic labels also switch language.
        self.project_detail_page.set_project(self.current_project_id)
        self.decisions_page.refresh(self.decisions_page.current_decision_id)
        self.refresh_note_resources()

    def _retranslate_shell(self) -> None:
        tr = self.i18n.language == "tr"
        self.setWindowTitle("DevNest — Yerel Geliştirici Çalışma Alanı" if tr else f"{APP_NAME} — Local-first Developer Workspace")
        self.project_selector_label.setText(self.i18n.t("top.project"))
        self.project_selector_label.setToolTip(self.i18n.t("top.project_tip"))
        self.project_selector.setToolTip(self.i18n.t("top.project_tip"))
        self.global_search.setPlaceholderText(self.i18n.t("top.search"))
        self.global_search.setToolTip(self.i18n.t("top.search_tip"))
        self.language_combo.setToolTip(self.i18n.t("top.language_tip"))
        self.note_linked_label.setText(self.i18n.t("notes.linked_resources"))
        self.note_link_button.setText(self.i18n.t("notes.link"))
        self.note_view_changes_button.setText(self.i18n.t("notes.view_changes"))
        self.note_mark_reviewed_button.setText(self.i18n.t("notes.mark_reviewed"))
        self.note_link_button.setToolTip(self.i18n.t("tip.notes.link"))
        self.note_view_changes_button.setToolTip(self.i18n.t("tip.notes.changes"))
        self.note_mark_reviewed_button.setToolTip(self.i18n.t("tip.notes.review"))
        self.tabs.setTabText(0, self.i18n.t("notes.editor"))
        self.tabs.setTabText(1, self.i18n.t("notes.diagram"))
        self.editor_workspace_button.setText(self.i18n.t("notes.editor"))
        self.diagram_workspace_button.setText(self.i18n.t("notes.diagram"))
        self.theme_label.setText("Tema:" if tr else "Theme:")
        if not self._dirty:
            self.save_label.setText(self.i18n.t("status.saved"))
        self.repository_status_label.setText(self.i18n.t("status.local_first"))
        # Legacy note editor actions remain feature-compatible, but their visible labels follow the chosen language.
        labels = {
            self.new_action: ("Yeni Not", "New Note"), self.delete_action: ("Sil", "Delete"),
            self.import_action: ("TXT İçe Aktar", "Import TXT"), self.export_action: ("TXT Dışa Aktar", "Export TXT"),
            self.exit_action: ("Çıkış", "Exit"), self.undo_action: ("Geri Al", "Undo"), self.redo_action: ("Yinele", "Redo"),
            self.cut_action: ("Kes", "Cut"), self.copy_action: ("Kopyala", "Copy"), self.paste_action: ("Yapıştır", "Paste"),
            self.select_all_action: ("Tümünü Seç", "Select All"), self.find_action: ("Bul", "Find"),
            self.checkbox_action: ("Onay Kutusu", "Checkbox"), self.auto_checkbox_action: ("Otomatik Onay Kutusu", "Auto Checkbox"),
            self.blank_line_enter_action: ("Çift Enter", "Double Enter"), self.bold_action: ("Kalın", "Bold"),
            self.italic_action: ("İtalik", "Italic"), self.underline_action: ("Altı Çizili", "Underline"),
            self.strike_action: ("Üstü Çizili", "Strikethrough"), self.bullet_action: ("Madde Listesi", "Bullet List"),
            self.numbered_action: ("Numaralı Liste", "List Mode"), self.toggle_sidebar_action: ("Not Panelini Aç/Kapat", "Toggle Sidebar"),
            self.editor_tab_action: ("Yazı", "Editor"), self.diagram_tab_action: ("Diyagram", "Diagram"),
            self.preferences_action: ("Tercihler…", "Preferences…"), self.trash_action: ("Çöp Kutusu…", "Trash…"),
            self.shortcuts_action: ("Klavye Kısayolları", "Keyboard Shortcuts"), self.about_action: ("DevNest Hakkında", "About DevNest"),
        }
        for action, (tr_text, en_text) in labels.items():
            action.setText(tr_text if tr else en_text)
        detailed_tips = {
            self.new_action: ("Aktif projede yeni, boş bir not oluşturur. Yazdıklarınız otomatik kaydedilir.", "Create a new blank note inside the current project. What you type is saved automatically."),
            self.delete_action: ("Açık notu çöp kutusuna taşır. Hemen kalıcı olarak silmez; isterseniz daha sonra geri yükleyebilirsiniz.", "Move the open note to Trash. It is not permanently deleted, so you can restore it later."),
            self.import_action: ("Bilgisayarınızdaki bir TXT dosyasını yeni nota dönüştürür. Kaynak TXT dosyanız değiştirilmez.", "Turn a TXT file from your computer into a DevNest note. The original TXT file is not changed."),
            self.export_action: ("Açık notun okunabilir metin kopyasını TXT dosyası olarak dışarı verir.", "Save a readable plain-text copy of the open note as a TXT file."),
            self.checkbox_action: ("Yazdığınız satıra işaretlenebilir bir görev kutusu ekler.", "Insert a checkable task box on the current line."),
            self.auto_checkbox_action: ("Açıksa bir onay kutulu satırdan sonra Enter'a bastığınızda yeni satırda da otomatik kutu oluşturur.", "When enabled, pressing Enter after a checkbox line automatically creates another checkbox on the next line."),
            self.numbered_action: ("1., 2., 3. şeklindeki numaralı satırları Enter ile otomatik sürdürür.", "Continue numbered lines such as 1., 2., 3. automatically when you press Enter."),
            self.blank_line_enter_action: ("Açıksa Enter'a bir kez basınca iki satır aşağı iner ve arada boş satır bırakır.", "When enabled, one Enter moves down two lines and leaves a blank line between paragraphs."),
            self.toggle_sidebar_action: ("Not listesini gizler veya yeniden gösterir. Notlarınız silinmez.", "Hide or show the note list. This never deletes any notes."),
        }
        for action, (tr_tip, en_tip) in detailed_tips.items():
            action.setToolTip(f"<div style='width:360px'>{tr_tip if tr else en_tip}</div>")
        self.editor_workspace_button.setToolTip("Notun yazı editörünü gösterir." if tr else "Show the note's text editor.")
        self.diagram_workspace_button.setToolTip("Bu nota ait diyagramı gösterir." if tr else "Show the diagram that belongs to this note.")
        self.theme_combo.setToolTip("Uygulamanın renk görünümünü değiştirir; verilerinizi etkilemez." if tr else "Change DevNest's color appearance. This does not affect your data.")
        if hasattr(self, "file_menu"):
            self.file_menu.setTitle("Dosya" if tr else "File")
            self.edit_menu.setTitle("Düzen" if tr else "Edit")
            self.view_menu.setTitle("Görünüm" if tr else "View")
            self.theme_menu.setTitle("Tema" if tr else "Theme")
            self.format_menu.setTitle("Biçim" if tr else "Format")
            self.help_menu.setTitle("Yardım" if tr else "Help")

    def _load_initial_note(self) -> None:
        notes = self.database.list_notes(sort=self._sort_mode, project_id=self.current_project_id)
        if not notes:
            note = self.database.create_note(project_id=self.current_project_id)
            notes = self.database.list_notes(sort=self._sort_mode, project_id=self.current_project_id)
            target = note.id
        else:
            last_id = self.settings.last_note_id() if self.preferences.start_with_last_note else None
            ids = {note.id for note in notes}
            target = last_id if last_id in ids else notes[0].id
        self.sidebar.set_notes(notes, target)
        self.open_note(target)

    def refresh_sidebar(self, selected_id: int | None = None) -> None:
        notes = self.database.list_notes(self._search_term, self._sort_mode, project_id=self.current_project_id)
        self.sidebar.set_notes(notes, selected_id if selected_id is not None else self.current_note_id)

    def open_note(self, note_id: int) -> None:
        if note_id == self.current_note_id and not self._loading_note:
            self._navigate("notes")
            return
        self.flush_pending_saves()
        note = self.database.get_note(note_id)
        if note is None:
            self.refresh_sidebar()
            return
        if note.project_id and note.project_id != self.current_project_id:
            self._set_current_project(note.project_id, reload_note=False)
        self._loading_note = True
        try:
            self.current_note_id = note.id
            self.title_edit.setText(note.title)
            self.editor.setHtml(note.content_html) if note.content_html else self.editor.clear()
            self.diagram.load_data(self.database.get_diagram(note.id))
            self._apply_note_diagram_statuses()
            self.settings.set_last_note_id(note.id)
            self._dirty = False
            self._diagram_dirty = False
            self.save_label.setText(self.i18n.t("status.saved"))
            self._update_stats()
            self.refresh_note_resources()
        finally:
            self._loading_note = False

    def new_note(self) -> None:
        self.flush_pending_saves()
        try:
            note = self.database.create_note(project_id=self.current_project_id)
            self._search_term = ""
            self.sidebar.search.clear()
            self.refresh_sidebar(note.id)
            self.open_note(note.id)
            self.title_edit.setFocus()
            self.title_edit.selectAll()
        except DatabaseError as exc:
            self._show_database_error(exc)

    def rename_note(self, note_id: int) -> None:
        note = self.database.get_note(note_id)
        if note is None:
            return
        title, ok = QInputDialog.getText(self, "Rename Note", "Title:", text=note.title)
        if not ok:
            return
        try:
            if note_id == self.current_note_id:
                self.title_edit.setText(title.strip() or DEFAULT_NOTE_TITLE)
                self.save_current_note()
            else:
                self.database.rename_note(note_id, title)
            self.refresh_sidebar(note_id)
        except DatabaseError as exc:
            self._show_database_error(exc)

    def duplicate_note(self, note_id: int) -> None:
        self.flush_pending_saves()
        try:
            duplicate = self.database.duplicate_note(note_id)
            self.refresh_sidebar(duplicate.id)
            self.open_note(duplicate.id)
        except DatabaseError as exc:
            self._show_database_error(exc)

    def delete_note(self, note_id: int | None) -> None:
        if note_id is None:
            return
        note = self.database.get_note(note_id)
        if note is None:
            return
        answer = QMessageBox.question(
            self,
            "Move to Trash",
            f'Move "{note.title}" to Trash? You can restore it later.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        if note_id == self.current_note_id:
            self.flush_pending_saves()
        try:
            self.database.soft_delete_note(note_id)
            if note_id == self.current_note_id:
                self.current_note_id = None
            notes = self.database.list_notes(self._search_term, self._sort_mode, project_id=self.current_project_id)
            if not notes:
                created = self.database.create_note(project_id=self.current_project_id)
                notes = self.database.list_notes(self._search_term, self._sort_mode, project_id=self.current_project_id)
                target = created.id
            else:
                target = notes[0].id
            self.sidebar.set_notes(notes, target)
            self.open_note(target)
        except DatabaseError as exc:
            self._show_database_error(exc)

    def open_trash(self) -> None:
        self.flush_pending_saves()
        dialog = TrashDialog(self.database, self)
        dialog.exec()
        if dialog.changed:
            self.refresh_sidebar(self.current_note_id)

    def save_current_note(self) -> None:
        self.autosave_timer.stop()
        if self._loading_note or not self._dirty or self.current_note_id is None:
            return
        try:
            title = self.title_edit.text().strip() or DEFAULT_NOTE_TITLE
            if self.title_edit.text() != title:
                self.title_edit.blockSignals(True)
                self.title_edit.setText(title)
                self.title_edit.blockSignals(False)
            self.database.update_note(
                self.current_note_id,
                title,
                self.editor.document().toHtml(),
                self.editor.toPlainText(),
            )
            self._dirty = False
            self.save_label.setText(self.i18n.t("status.saved"))
            self.refresh_sidebar(self.current_note_id)
        except DatabaseError as exc:
            self.save_label.setText("Save failed")
            logger.exception("Autosave failed")
            QMessageBox.critical(self, "Save Failed", str(exc))

    def save_current_diagram(self) -> None:
        self.diagram_timer.stop()
        if self._loading_note or not self._diagram_dirty or self.current_note_id is None:
            return
        try:
            self.database.save_diagram(self.current_note_id, self.diagram.to_data())
            self._diagram_dirty = False
        except DatabaseError as exc:
            logger.exception("Diagram save failed")
            QMessageBox.critical(self, "Diagram Save Failed", str(exc))

    def flush_pending_saves(self) -> None:
        self.save_current_note()
        self.save_current_diagram()
        self.settings.sync()

    def _mark_content_dirty(self) -> None:
        if self._loading_note:
            return
        self._dirty = True
        self.save_label.setText("Saving…" if self.preferences.autosave_enabled else "Modified")
        if self.preferences.autosave_enabled:
            self.autosave_timer.start(self.preferences.autosave_delay_ms)

    def _on_editor_changed(self) -> None:
        self._mark_content_dirty()
        self._update_stats()

    def _on_diagram_changed(self) -> None:
        if self._loading_note:
            return
        self._diagram_dirty = True
        self.diagram_timer.start(max(500, self.preferences.autosave_delay_ms))

    def _on_search_changed(self, text: str) -> None:
        self._search_term = text
        self.refresh_sidebar(self.current_note_id)

    def _on_sort_changed(self, mode: str) -> None:
        self._sort_mode = mode
        self.refresh_sidebar(self.current_note_id)

    def _update_stats(self) -> None:
        text = self.editor.toPlainText()
        words = len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))
        lines = max(1, self.editor.document().blockCount())
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.positionInBlock() + 1
        if self.i18n.language == "tr":
            self.stats_label.setText(f"Kelime: {words}  •  Satır: {lines}  •  Sat {line}, Süt {col}")
        else:
            self.stats_label.setText(f"Words: {words}  •  Lines: {lines}  •  Ln {line}, Col {col}")

    def find_in_note(self) -> None:
        self.tabs.setCurrentIndex(0)
        self.editor.show_find_bar()

    def import_txt(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Import TXT", "", "Text Files (*.txt);;All Files (*)")
        if filename:
            self._import_path(Path(filename))

    def _import_path(self, path: Path) -> None:
        if path.suffix.lower() != ".txt":
            QMessageBox.warning(self, "Import", "DevNest imports .txt files only.")
            return
        try:
            text = read_utf8_text(path)
            parsed = parse_text(text)
            html = import_text_to_html(text)
            plain = parsed_to_internal_text(parsed)
            note = self.database.create_note(path.stem or DEFAULT_NOTE_TITLE, html, plain, project_id=self.current_project_id)
            self._search_term = ""
            self.sidebar.search.clear()
            self.refresh_sidebar(note.id)
            self.open_note(note.id)
        except (OSError, UnicodeError, DatabaseError) as exc:
            logger.exception("TXT import failed for %s", path)
            QMessageBox.critical(self, "Import Failed", f"Could not import the file.\n\n{exc}")

    def export_note(self, note_id: int | None) -> None:
        if note_id is None:
            return
        if note_id == self.current_note_id:
            self.flush_pending_saves()
        note = self.database.get_note(note_id)
        if note is None:
            return
        default_name = self._safe_filename(note.title) + ".txt"
        filename, _ = QFileDialog.getSaveFileName(self, "Export Note as TXT", default_name, "Text Files (*.txt)")
        if not filename:
            return
        path = Path(filename)
        if path.suffix.lower() != ".txt":
            path = path.with_suffix(".txt")
        if path.exists():
            answer = QMessageBox.question(
                self,
                "Overwrite File",
                f'"{path.name}" already exists. Overwrite it?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        try:
            if note_id == self.current_note_id:
                plain = self.editor.toPlainText()
            else:
                doc = QTextDocument()
                doc.setHtml(note.content_html)
                plain = doc.toPlainText()
            write_utf8_text(path, export_internal_plain_text(plain))
            self.statusBar().showMessage(f"Exported {path.name}", 3000)
        except OSError as exc:
            logger.exception("TXT export failed for %s", path)
            QMessageBox.critical(self, "Export Failed", f"Could not write the file.\n\n{exc}")

    @staticmethod
    def _safe_filename(title: str) -> str:
        cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title).strip(" .")
        return cleaned[:100] or "Untitled Note"

    def open_preferences(self) -> None:
        dialog = PreferencesDialog(self.preferences, self.i18n, self)
        if dialog.exec():
            self.preferences = dialog.preferences()
            self.settings.save_preferences(self.preferences)
            self._apply_preferences(self.preferences, persist=False)
            self.settings_page.startup.setChecked(self.preferences.check_repositories_on_startup)
            interval_index = self.settings_page.interval.findData(self.preferences.github_poll_interval_minutes)
            if interval_index >= 0:
                self.settings_page.interval.setCurrentIndex(interval_index)
            self._configure_repository_polling()

    def _apply_preferences(self, prefs: AppPreferences, persist: bool = False) -> None:
        self.editor.set_editor_font_size(prefs.editor_font_size)
        if hasattr(self, "font_size_slider"):
            self.font_size_slider.blockSignals(True)
            self.font_size_slider.setValue(prefs.editor_font_size)
            self.font_size_slider.blockSignals(False)
            self.font_size_label.setText(f"{prefs.editor_font_size} pt")
        self.editor.set_tab_width(prefs.tab_width)
        self.editor.setLineWrapMode(
            QTextEdit.LineWrapMode.WidgetWidth if prefs.word_wrap else QTextEdit.LineWrapMode.NoWrap
        )
        auto_enabled = prefs.auto_checkbox_default
        self.auto_checkbox_action.blockSignals(True)
        self.auto_checkbox_action.setChecked(auto_enabled)
        self.auto_checkbox_action.blockSignals(False)
        self.editor.set_auto_checkbox(auto_enabled)
        self.blank_line_enter_action.blockSignals(True)
        self.blank_line_enter_action.setChecked(prefs.blank_line_after_enter)
        self.blank_line_enter_action.blockSignals(False)
        self.editor.set_blank_line_after_enter(prefs.blank_line_after_enter)
        self.set_theme(prefs.theme, persist=persist)

    def _set_auto_checkbox(self, enabled: bool) -> None:
        self.editor.set_auto_checkbox(enabled)
        self.preferences.auto_checkbox_default = enabled
        self.settings.set_value("editor/auto_checkbox_default", enabled)

    def _set_blank_line_after_enter(self, enabled: bool) -> None:
        self.editor.set_blank_line_after_enter(enabled)
        self.preferences.blank_line_after_enter = enabled
        self.settings.set_value("editor/blank_line_after_enter", enabled)

    def _set_numbered_list_mode(self, enabled: bool) -> None:
        self.editor.set_numbered_list_mode(enabled)
        self.editor.setFocus()

    def _sync_numbered_list_action(self, enabled: bool) -> None:
        self.numbered_action.blockSignals(True)
        self.numbered_action.setChecked(enabled)
        self.numbered_action.blockSignals(False)

    def set_theme(self, theme: str, persist: bool = True) -> None:
        self.theme_manager.apply(theme)
        resolved_theme = self.theme_manager.current_theme
        spec = self.theme_manager.current_spec
        self.diagram.set_theme(spec.diagram_palette())
        if hasattr(self, "architecture_page"):
            self.architecture_page.diagram.set_theme(spec.diagram_palette())
        self.editor.set_search_theme(
            match_background=spec.find_match_bg,
            match_foreground=spec.find_match_fg,
            current_background=spec.find_current_bg,
            current_foreground=spec.find_current_fg,
            marker=spec.find_marker,
            current_marker=spec.find_current_marker,
        )
        self.preferences.theme = resolved_theme
        for name, action in getattr(self, "theme_actions", {}).items():
            action.setChecked(name == resolved_theme)
        if hasattr(self, "theme_combo"):
            index = self.theme_combo.findData(resolved_theme)
            if index >= 0 and index != self.theme_combo.currentIndex():
                self.theme_combo.blockSignals(True)
                self.theme_combo.setCurrentIndex(index)
                self.theme_combo.blockSignals(False)
        if persist:
            self.settings.set_value("appearance/theme", resolved_theme)
            self.settings.sync()

    def _theme_combo_changed(self, _index: int) -> None:
        theme = self.theme_combo.currentData()
        if theme:
            self.set_theme(str(theme))

    def _sync_workspace_buttons(self, index: int) -> None:
        if hasattr(self, "editor_workspace_button"):
            self.editor_workspace_button.setChecked(index == 0)
            self.diagram_workspace_button.setChecked(index == 1)

    def _on_system_color_scheme_changed(self, _scheme) -> None:
        if self.preferences.theme == "system":
            self.set_theme("system", persist=False)

    def _toggle_sidebar(self) -> None:
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def _refresh_project_selector(self) -> None:
        projects = self.database.list_projects()
        self.project_selector.blockSignals(True)
        self.project_selector.clear()
        target_index = -1
        for index, project in enumerate(projects):
            self.project_selector.addItem(project.name, project.id)
            if project.id == self.current_project_id:
                target_index = index
        if target_index >= 0:
            self.project_selector.setCurrentIndex(target_index)
        self.project_selector.blockSignals(False)

    def _projects_changed(self) -> None:
        if self.database.get_project(self.current_project_id) is None:
            self.current_project_id = self.database.default_project_id()
        self._refresh_project_selector()
        self.dashboard_page.refresh()

    def _project_selected(self, _index: int) -> None:
        value = self.project_selector.currentData()
        if value is not None:
            self._set_current_project(int(value))

    def _set_current_project(self, project_id: int, reload_note: bool = True) -> None:
        if self.database.get_project(project_id) is None:
            return
        if project_id == self.current_project_id and not reload_note:
            return
        self.flush_pending_saves()
        self.decisions_page.save_current()
        self.architecture_page.save()
        self.current_project_id = project_id
        self.settings.set_value("session/last_project_id", project_id)
        self._refresh_project_selector()
        self.decisions_page.set_project(project_id)
        self.architecture_page.set_project(project_id)
        self.project_detail_page.set_project(project_id)
        self.github_page.set_current_project(project_id)
        self._search_term = ""
        self.sidebar.search.blockSignals(True)
        self.sidebar.search.clear()
        self.sidebar.search.blockSignals(False)
        if reload_note:
            notes = self.database.list_notes(sort=self._sort_mode, project_id=project_id)
            if not notes:
                note = self.database.create_note(project_id=project_id)
                notes = self.database.list_notes(sort=self._sort_mode, project_id=project_id)
                target = note.id
            else:
                target = notes[0].id
            self.current_note_id = None
            self.sidebar.set_notes(notes, target)
            self.open_note(target)
        else:
            self.refresh_sidebar(self.current_note_id)
        self.dashboard_page.refresh()

    def _navigate(self, key: str) -> None:
        page = self.pages.get(key)
        if page is None:
            return
        if key != "notes":
            self.flush_pending_saves()
        if key != "decisions":
            self.decisions_page.save_current()
        if key != "architecture":
            self.architecture_page.save()
        self.page_stack.setCurrentWidget(page)
        self.settings.set_value("session/last_page", key)
        nav_key = "projects" if key == "project_detail" else key
        self.global_navigation.set_current(nav_key)
        notes_visible = key == "notes"
        if hasattr(self, "notes_toolbar"):
            self.notes_toolbar.setVisible(notes_visible)
            self.text_toolbar.setVisible(notes_visible)
        self.stats_label.setVisible(notes_visible)
        self.save_label.setVisible(notes_visible)
        if key == "dashboard":
            needs = sum(1 for s in self._review_summaries if s.status == ReviewStatus.NEEDS_REVIEW)
            current = sum(1 for s in self._review_summaries if s.status == ReviewStatus.CURRENT)
            self.dashboard_page.refresh(needs, current)
        elif key == "projects":
            self.projects_page.refresh()
        elif key == "project_detail":
            self.project_detail_page.set_project(self.current_project_id)
        elif key == "notes":
            self.refresh_note_resources()
        elif key == "decisions":
            self.decisions_page.refresh(self.decisions_page.current_decision_id)
            QTimer.singleShot(0, self._refresh_decision_status)
        elif key == "architecture":
            self.architecture_page.refresh()
            self.architecture_page.set_review_summaries(self._review_summaries)
        elif key == "review":
            self.refresh_review_inbox()
        elif key == "github":
            self.github_page.update_connection_state()
            self.github_page.render_cached()

    def _open_project_detail(self, project_id: int) -> None:
        self._set_current_project(project_id)
        self.project_detail_page.set_project(project_id)
        self._navigate("project_detail")

    def _project_section_requested(self, section: str) -> None:
        if section in {"notes", "decisions", "architecture", "review"}:
            self._navigate(section)
        elif section == "overview":
            self._navigate("project_detail")
        else:
            # Repository overview is part of Project Detail in this release.
            self._navigate("project_detail")

    def _open_global_search(self) -> None:
        query = self.global_search.text().strip()
        if not query:
            return
        dialog = GlobalSearchDialog(self.database, query, self.i18n, self)
        dialog.resultActivated.connect(self._activate_search_result)
        dialog.exec()

    def _activate_search_result(self, kind: str, item_id: int) -> None:
        if kind == "project":
            self._open_project_detail(item_id)
        elif kind == "note":
            note = self.database.get_note(item_id)
            if note and note.project_id:
                self._set_current_project(note.project_id, reload_note=False)
            self.open_note(item_id)
            self.refresh_sidebar(item_id)
            self.sidebar.select_note(item_id)
            self._navigate("notes")
        elif kind == "decision":
            decision = self.database.get_decision(item_id)
            if decision:
                self._set_current_project(decision.project_id, reload_note=False)
                self._navigate("decisions")
                self.decisions_page.refresh(item_id)
                self.decisions_page.open_decision(item_id)

    def _add_local_repository_async(self, project_id: int, path: str) -> None:
        self.statusBar().showMessage("Checking local Git repository…")
        self.task_runner.submit(
            lambda: self.repository_service.inspect_local_repository(path),
            lambda info: self._local_repository_ready(project_id, path, info),
            lambda exc: QMessageBox.warning(self, "Local Repository", str(exc)),
            lambda: self.statusBar().clearMessage(),
        )

    def _local_repository_ready(self, project_id: int, path: str, info) -> None:
        try:
            repo = self.repository_service.persist_local_repository(project_id, path, info)
        except Exception as exc:
            QMessageBox.warning(self, "Local Repository", str(exc))
            return
        self.project_detail_page.set_project(project_id)
        self.projects_page.refresh()
        self.dashboard_page.refresh()
        self.repository_status_label.setText(f"Repository: {(info.branch or 'detached')} @ {info.head_sha[:8]}")
        self.statusBar().showMessage(f"Linked local repository: {repo.full_name or repo.name}", 3500)
        self.refresh_review_inbox()

    def _refresh_repository_async(self, repository_id: int) -> None:
        repository = self.database.get_repository(repository_id)
        if repository is None:
            return
        self.statusBar().showMessage("Checking repository…")

        def work():
            if repository.local_git_root or repository.local_path:
                root = repository.local_git_root or repository.local_path
                head = self.local_git.get_head_sha(root)
                branch = self.local_git.get_current_branch(root)
                return head, branch, "local_git"
            if repository.full_name:
                token = self.github_page.auth.get_valid_access_token()
                client = GitHubClient(token, self.github_config)
                owner, name = repository.full_name.split("/", 1)
                branch = repository.default_branch or "main"
                data = client.get_branch(owner, name, branch)
                head = str((data.get("commit") or {}).get("sha") or "")
                if not head:
                    raise RuntimeError("GitHub did not return a branch HEAD.")
                return head, branch, "github_api"
            raise RuntimeError("No local or GitHub repository source is available.")

        self.task_runner.submit(
            work,
            lambda result: self._repository_refresh_ready(repository_id, result),
            lambda exc: self._repository_refresh_failed(repository_id, exc),
            lambda: self.statusBar().clearMessage(),
        )

    def _repository_refresh_ready(self, repository_id: int, result) -> None:
        head, branch, source = result
        self.database.update_repository_sync(repository_id, head, source, branch=branch)
        self.repository_status_label.setText(f"Repository: {branch or 'detached'} @ {head[:8]}")
        self.project_detail_page.set_project(self.current_project_id)
        self.statusBar().showMessage("Repository state refreshed.", 2500)
        self.refresh_review_inbox()

    def _repository_refresh_failed(self, repository_id: int, exc: Exception) -> None:
        self.database.update_repository_sync(repository_id, None, "local_git", success=False)
        self.statusBar().showMessage(str(exc), 5000)

    def _github_state_changed(self, state: str) -> None:
        if self.i18n.language == "tr":
            labels = {
                "connected": "GitHub Bağlı · Sadece okuma",
                "offline": "GitHub Çevrimdışı",
                "reconnect": "GitHub Yeniden Bağlanmalı",
                "disconnected": "GitHub Bağlı Değil",
            }
        else:
            labels = {
                "connected": "GitHub Connected · Read-only",
                "offline": "GitHub Offline",
                "reconnect": "GitHub Reconnect Required",
                "disconnected": "GitHub Disconnected",
            }
        self.github_indicator.setText(labels.get(state, "GitHub"))
        self.github_indicator.setToolTip(
            "GitHub bağlantı durumunu gösterir. Bu bağlantı yalnızca okuma içindir; DevNest kod gönderemez."
            if self.i18n.language == "tr" else
            "Shows the GitHub connection state. This connection is read-only; DevNest cannot push code."
        )

    def _link_github_repository_to_current_project(self, repository_id: int) -> None:
        repository = self.database.get_repository(repository_id)
        if repository is None:
            return
        self.database.link_repository_to_project(
            self.current_project_id, repository.id, repository.default_branch
        )
        self.project_detail_page.set_project(self.current_project_id)
        self.projects_page.refresh()
        self.dashboard_page.refresh()
        self.github_page.render_cached()
        message = (
            f"{repository.full_name or repository.name} aktif projeye eklendi."
            if self.i18n.language == "tr" else
            f"Linked {repository.full_name or repository.name} to the current project."
        )
        self.statusBar().showMessage(message, 3000)

    def _github_repositories_changed(self) -> None:
        self._refresh_project_selector()
        self.projects_page.refresh()
        self.project_detail_page.set_project(self.current_project_id)
        if self.preferences.check_repositories_on_startup:
            self.refresh_review_inbox()

    def refresh_note_resources(self) -> None:
        while self.note_chips_layout.count():
            item = self.note_chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if self.current_note_id is None:
            self.note_status_badge.set_status(ReviewStatus.NOT_REVIEWED)
            return
        links = self.database.list_resource_links("note", self.current_note_id)
        for link in links:
            chip = ResourceChip(link, self.i18n)
            chip.unlinkRequested.connect(self._unlink_resource)
            self.note_chips_layout.addWidget(chip)
        self.note_chips_layout.addStretch(1)
        status = self._aggregate_cached_status("note", str(self.current_note_id), "") if links else ReviewStatus.NOT_REVIEWED
        self.note_status_badge.set_status(status)
        self.note_view_changes_button.setEnabled(bool(links))
        self.note_mark_reviewed_button.setEnabled(bool(links))

    def _aggregate_cached_status(self, resource_type: str, resource_id: str, parent_id: str) -> ReviewStatus:
        matches = [s for s in self._review_summaries if s.resource_link.resource_type == resource_type
                   and s.resource_link.resource_id == resource_id
                   and s.resource_link.resource_parent_id == parent_id]
        if not matches:
            links = self.database.list_resource_links(resource_type, resource_id, parent_id)
            if not links:
                return ReviewStatus.NOT_REVIEWED
            if any(self.database.get_review_baseline(resource_type, resource_id, l.repository_id, parent_id) is None for l in links):
                return ReviewStatus.NOT_REVIEWED
            return ReviewStatus.CANNOT_COMPARE
        priorities = [ReviewStatus.NEEDS_REVIEW, ReviewStatus.CANNOT_COMPARE, ReviewStatus.NOT_REVIEWED, ReviewStatus.CURRENT]
        for status in priorities:
            if any(s.status == status for s in matches):
                return status
        return ReviewStatus.NOT_REVIEWED

    def _refresh_decision_status(self) -> None:
        decision_id = self.decisions_page.current_decision_id
        if decision_id is None:
            self.decisions_page.review_badge.set_status(ReviewStatus.NOT_REVIEWED)
            return
        links = self.database.list_resource_links("decision", decision_id)
        status = self._aggregate_cached_status("decision", str(decision_id), "") if links else ReviewStatus.NOT_REVIEWED
        self.decisions_page.review_badge.set_status(status)

    def _apply_note_diagram_statuses(self) -> None:
        if self.current_note_id is None:
            self.diagram.set_review_statuses({})
            return
        parent = str(self.current_note_id)
        grouped: dict[str, list[ReviewSummary]] = {}
        for summary in self._review_summaries:
            if summary.resource_link.resource_type == "diagram_item" and summary.resource_link.resource_parent_id == parent:
                grouped.setdefault(summary.resource_link.resource_id, []).append(summary)
        mapping: dict[str, str] = {}
        for item_id, values in grouped.items():
            for status in (ReviewStatus.NEEDS_REVIEW, ReviewStatus.CANNOT_COMPARE, ReviewStatus.NOT_REVIEWED, ReviewStatus.CURRENT):
                if any(summary.status == status for summary in values):
                    mapping[item_id] = status.value
                    break
        self.diagram.set_review_statuses(mapping)

    def _diagram_items_deleted(self, note_id: int | None, item_ids: list[str]) -> None:
        if note_id is None:
            return
        for item_id in item_ids:
            self.database.delete_resource_context("diagram_item", item_id, note_id)
        self.refresh_review_inbox()

    def _unlink_resource(self, link_id: int) -> None:
        self.database.remove_resource_link(link_id)
        self.refresh_note_resources()
        self.decisions_page.refresh_resources()
        self.architecture_page._selection_changed()
        self.refresh_review_inbox()

    def _load_github_contents(self, repository, path: str):
        if not repository.full_name:
            raise RuntimeError("This repository is not available through GitHub.")
        token = self.github_page.auth.get_valid_access_token()
        client = GitHubClient(token, self.github_config)
        owner, name = repository.full_name.split("/", 1)
        return client.get_contents(owner, name, path, repository.default_branch)

    def _link_resource(self, resource_type: str, resource_id, resource_parent_id=None) -> None:
        if resource_id in (None, 0, ""):
            return
        dialog = ResourceLinkDialog(
            self.database, self.current_project_id, self._load_github_contents, self.i18n, self
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        repository_id, target_type, target_value = dialog.selection()
        try:
            self.database.add_resource_link(
                self.current_project_id, resource_type, resource_id, repository_id, target_type, target_value,
                resource_parent_id=resource_parent_id,
            )
        except DatabaseError as exc:
            QMessageBox.warning(self, "Link Resource", str(exc))
            return
        if resource_type == "note":
            self.refresh_note_resources()
        elif resource_type == "decision":
            self.decisions_page.refresh_resources()
        else:
            self.architecture_page._selection_changed()
        answer = QMessageBox.question(
            self, "Resource Linked",
            "Use the repository's current commit as the human review baseline?\n\n"
            "Choose No to leave this knowledge as Not Reviewed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._mark_resource_reviewed(resource_type, resource_id, resource_parent_id)
        else:
            self.refresh_review_inbox()

    def _compute_review_summaries_worker(self, resource_type: str | None = None,
                                         resource_id: str | int | None = None,
                                         resource_parent_id: str | int | None = None) -> list[ReviewSummary]:
        worker_db = Database(self.database.path)
        try:
            github_client = None
            try:
                token = self.github_page.auth.get_valid_access_token()
                github_client = GitHubClient(token, self.github_config)
            except Exception:
                github_client = None
            detector = ChangeDetectionService(worker_db, LocalGitService(), github_client)
            links = worker_db.list_resource_links(resource_type, resource_id, resource_parent_id)
            monitorable = {"repository", "directory", "file", "branch"}
            return [detector.evaluate(link) for link in links if link.target_type in monitorable]
        finally:
            worker_db.close()

    def _configure_repository_polling(self) -> None:
        if not hasattr(self, "repository_poll_timer"):
            return
        minutes = max(5, min(240, int(self.preferences.github_poll_interval_minutes)))
        self.repository_poll_timer.setInterval(minutes * 60 * 1000)
        self.repository_poll_timer.start()

    def _startup_refresh(self) -> None:
        # Local cached content is already rendered before this runs. Network and Git
        # history checks happen asynchronously after the event loop starts.
        self.github_page.update_connection_state()
        if self.preferences.check_repositories_on_startup:
            self.github_page.refresh_if_connected()
            self.refresh_review_inbox()

    def refresh_review_inbox(self) -> None:
        if self._review_refresh_in_progress:
            return
        self._review_refresh_in_progress = True
        self.review_page.subtitle.setText("Checking repository state… Local cached UI remains available.")
        self.task_runner.submit(
            self._compute_review_summaries_worker,
            self._review_refresh_ready,
            self._review_refresh_failed,
            lambda: setattr(self, "_review_refresh_in_progress", False),
        )

    def _review_refresh_ready(self, summaries: list[ReviewSummary]) -> None:
        self._review_summaries = summaries
        self.review_page.set_summaries(summaries)
        needs = sum(1 for s in summaries if s.status == ReviewStatus.NEEDS_REVIEW)
        current = sum(1 for s in summaries if s.status == ReviewStatus.CURRENT)
        self.dashboard_page.refresh(needs, current)
        self.refresh_note_resources()
        self._refresh_decision_status()
        self.architecture_page.set_review_summaries(summaries)
        self._apply_note_diagram_statuses()
        self.statusBar().showMessage(f"Repository review check complete · {needs} items need review.", 3000)

    def _review_refresh_failed(self, exc: Exception) -> None:
        self.review_page.subtitle.setText(f"Repository check unavailable: {exc}. Local features remain available.")

    def _view_resource_changes(self, resource_type: str, resource_id, resource_parent_id=None) -> None:
        if resource_id in (None, 0, ""):
            return
        self.statusBar().showMessage("Loading changes since review…")
        self.task_runner.submit(
            lambda: self._compute_review_summaries_worker(resource_type, resource_id, resource_parent_id),
            self._show_resource_summaries,
            lambda exc: QMessageBox.warning(self, "View Changes", str(exc)),
            lambda: self.statusBar().clearMessage(),
        )

    def _show_resource_summaries(self, summaries: list[ReviewSummary]) -> None:
        if not summaries:
            QMessageBox.information(self, "View Changes", "This knowledge has no monitorable repository links yet.")
            return
        preferred = next((s for s in summaries if s.status == ReviewStatus.NEEDS_REVIEW), summaries[0])
        if preferred.status == ReviewStatus.NOT_REVIEWED:
            QMessageBox.information(self, "Not Reviewed", "Create a review baseline before comparing changes.")
            return
        if preferred.status == ReviewStatus.CANNOT_COMPARE and not preferred.changed_files:
            QMessageBox.warning(self, "Cannot Compare", preferred.message or "Repository history cannot currently be compared.")
            return
        self._show_review_details(preferred)

    def _show_review_details(self, summary: ReviewSummary) -> None:
        ReviewDetailsDialog(summary, self.i18n, self).exec()

    def _mark_resource_reviewed(self, resource_type: str, resource_id, resource_parent_id=None) -> None:
        if resource_id in (None, 0, ""):
            return
        links = self.database.list_resource_links(resource_type, resource_id, resource_parent_id)
        if not links:
            QMessageBox.information(self, "Mark as Reviewed", "Link this knowledge to a repository first.")
            return
        self.statusBar().showMessage("Resolving current repository HEAD…")
        self.task_runner.submit(
            lambda: self._resolve_current_heads_worker(links),
            lambda resolved: self._confirm_mark_reviewed(links, resolved),
            lambda exc: QMessageBox.warning(self, "Cannot Compare", str(exc)),
            lambda: self.statusBar().clearMessage(),
        )

    def _resolve_current_heads_worker(self, links) -> dict[int, tuple[str, str | None]]:
        resolved: dict[int, tuple[str, str | None]] = {}
        github_client = None
        worker_db = Database(self.database.path)
        try:
            for link in links:
                if link.repository_id in resolved:
                    continue
                repository = worker_db.get_repository(link.repository_id)
                if repository is None:
                    continue
                if repository.local_git_root or repository.local_path:
                    root = repository.local_git_root or repository.local_path
                    resolved[repository.id] = (self.local_git.get_head_sha(root), self.local_git.get_current_branch(root))
                    continue
                if repository.full_name:
                    if github_client is None:
                        token = self.github_page.auth.get_valid_access_token()
                        github_client = GitHubClient(token, self.github_config)
                    owner, name = repository.full_name.split("/", 1)
                    mapping = worker_db.project_repository(link.project_id, repository.id)
                    branch = (mapping.monitored_branch if mapping else None) or repository.default_branch or "main"
                    data = github_client.get_branch(owner, name, branch)
                    sha = str((data.get("commit") or {}).get("sha") or "")
                    if sha:
                        resolved[repository.id] = (sha, branch)
        finally:
            worker_db.close()
        if not resolved:
            raise RuntimeError("No current repository commit is available. Local Git may be missing, or GitHub may require reconnection.")
        return resolved

    def _confirm_mark_reviewed(self, links, resolved: dict[int, tuple[str, str | None]]) -> None:
        lines = [f"{(self.database.get_repository(rid).full_name or self.database.get_repository(rid).name)} @ {sha[:8]}"
                 for rid, (sha, _branch) in resolved.items() if self.database.get_repository(rid)]
        answer = QMessageBox.question(
            self, "Mark as Reviewed",
            "Mark this knowledge as reviewed at the current repository commit?\n\n" + "\n".join(lines),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        for link in links:
            current = resolved.get(link.repository_id)
            if current:
                sha, branch = current
                self.review_service.mark_reviewed(link, sha, branch)
        self.statusBar().showMessage("✓ Review baseline updated.", 2500)
        self.refresh_review_inbox()

    def _mark_summary_reviewed(self, summary: ReviewSummary) -> None:
        if not summary.current_sha:
            self._mark_resource_reviewed(
                summary.resource_link.resource_type,
                summary.resource_link.resource_id,
                summary.resource_link.resource_parent_id,
            )
            return
        answer = QMessageBox.question(
            self, "Mark as Reviewed",
            f"Mark this knowledge as reviewed at {summary.current_sha[:10]}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.review_service.mark_reviewed(summary.resource_link, summary.current_sha, summary.branch)
            self.refresh_review_inbox()

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<b>{APP_NAME} {VERSION}</b><br><br>"
            "A GitHub-connected, local-first developer knowledge workspace.<br><br>"
            "Projects, notes, engineering decisions, architecture maps and review baselines stay local. "
            "GitHub integration is optional and read-only.<br><br>"
            "No DevNest account, telemetry, cloud database or AI service is required.<br><br>"
            f"Database: {database_path()}",
        )

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        if any(Path(url.toLocalFile()).suffix.lower() == ".txt" for url in urls):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        accepted = False
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() == ".txt":
                self._import_path(path)
                accepted = True
        if accepted:
            event.acceptProposedAction()
        else:
            event.ignore()

    def _restore_window_state(self) -> None:
        geometry = self.settings.value("window/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        splitter_state = self.settings.value("window/splitter")
        if splitter_state is not None:
            self.splitter.restoreState(splitter_state)
        tab_index = self.settings.value("window/tab_index", 0)
        try:
            self.tabs.setCurrentIndex(int(tab_index))
        except (TypeError, ValueError):
            pass

    def closeEvent(self, event: QCloseEvent) -> None:
        self.flush_pending_saves()
        self.decisions_page.save_current()
        self.architecture_page.save()
        if self.github_page.cancel_event is not None:
            self.github_page.cancel_event.set()
        if hasattr(self, "repository_poll_timer"):
            self.repository_poll_timer.stop()
        self.settings.set_value("window/geometry", self.saveGeometry())
        self.settings.set_value("window/splitter", self.splitter.saveState())
        self.settings.set_value("window/tab_index", self.tabs.currentIndex())
        self.settings.set_value("session/last_project_id", self.current_project_id)
        self.settings.set_last_note_id(self.current_note_id)
        self.settings.sync()
        self.database.close()
        event.accept()

    def _show_database_error(self, exc: DatabaseError) -> None:
        logger.exception("Database operation failed")
        QMessageBox.critical(self, "Database Error", str(exc))


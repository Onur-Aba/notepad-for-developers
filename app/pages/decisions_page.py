from __future__ import annotations

from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QLineEdit,
)

from app.database import Database, DatabaseError
from app.i18n import I18n
from app.models import DecisionStatus
from app.widgets.note_editor import NoteEditor
from app.widgets.status_badge import StatusBadge


class DecisionsPage(QWidget):
    linkResourceRequested = Signal(int)
    viewChangesRequested = Signal(int)
    markReviewedRequested = Signal(int)

    def __init__(self, database: Database, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.i18n = i18n
        self.project_id: int | None = None
        self.current_decision_id: int | None = None
        self._loading = False
        self._dirty = False
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.save_current)

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 26, 30, 24)
        root.setSpacing(12)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        self.page_title = QLabel()
        self.page_title.setObjectName("pageTitle")
        self.page_subtitle = QLabel()
        self.page_subtitle.setWordWrap(True)
        self.page_subtitle.setObjectName("pageSubtitle")
        titles.addWidget(self.page_title)
        titles.addWidget(self.page_subtitle)
        self.new_button = QPushButton()
        self.new_button.setObjectName("primaryButton")
        self.new_button.clicked.connect(self.new_decision)
        header.addLayout(titles, 1)
        header.addWidget(self.new_button)
        root.addLayout(header)

        self.guide = QFrame()
        self.guide.setObjectName("helperBanner")
        guide_layout = QVBoxLayout(self.guide)
        guide_layout.setContentsMargins(14, 10, 14, 10)
        guide_layout.setSpacing(2)
        self.guide_title = QLabel()
        self.guide_title.setObjectName("helperTitle")
        self.guide_text = QLabel()
        self.guide_text.setWordWrap(True)
        self.guide_text.setObjectName("mutedText")
        guide_layout.addWidget(self.guide_title)
        guide_layout.addWidget(self.guide_text)
        root.addWidget(self.guide)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        left = QFrame()
        left.setObjectName("secondaryPanel")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(9)
        self.list_heading = QLabel()
        self.list_heading.setObjectName("secondaryPanelTitle")
        self.search = QLineEdit()
        self.search.textChanged.connect(self._filters_changed)
        self.repo_filter_label = QLabel()
        self.repo_filter_label.setObjectName("fieldLabel")
        self.repo_filter = QComboBox()
        self.repo_filter.currentIndexChanged.connect(self._filters_changed)
        self.repo_filter.setToolTip(self.i18n.t("tip.decision.repo_filter"))
        self.list = QListWidget()
        self.list.setObjectName("decisionList")
        self.list.setSpacing(2)
        self.list.currentItemChanged.connect(self._selection_changed)
        left_layout.addWidget(self.list_heading)
        left_layout.addWidget(self.search)
        left_layout.addWidget(self.repo_filter_label)
        left_layout.addWidget(self.repo_filter)
        left_layout.addWidget(self.list, 1)

        editor_wrap = QFrame()
        editor_wrap.setObjectName("editorPanel")
        editor_layout = QVBoxLayout(editor_wrap)
        editor_layout.setContentsMargins(18, 16, 18, 16)
        editor_layout.setSpacing(10)

        self.context_bar = QFrame()
        self.context_bar.setObjectName("contextBar")
        context_layout = QHBoxLayout(self.context_bar)
        context_layout.setContentsMargins(12, 8, 12, 8)
        context_left = QVBoxLayout()
        self.project_caption = QLabel()
        self.project_caption.setObjectName("contextCaption")
        self.project_value = QLabel("—")
        self.project_value.setObjectName("contextValue")
        context_left.addWidget(self.project_caption)
        context_left.addWidget(self.project_value)
        context_right = QVBoxLayout()
        self.repo_caption = QLabel()
        self.repo_caption.setObjectName("contextCaption")
        self.repo_value = QLabel("—")
        self.repo_value.setObjectName("contextValue")
        self.repo_value.setWordWrap(True)
        context_right.addWidget(self.repo_caption)
        context_right.addWidget(self.repo_value)
        context_layout.addLayout(context_left, 1)
        context_layout.addLayout(context_right, 2)
        editor_layout.addWidget(self.context_bar)

        top = QHBoxLayout()
        self.key_label = QLabel("DEC-—")
        self.key_label.setObjectName("decisionKey")
        self.status_combo = QComboBox()
        self.review_badge = StatusBadge()
        top.addWidget(self.key_label)
        top.addWidget(self.status_combo)
        top.addStretch(1)
        top.addWidget(self.review_badge)
        editor_layout.addLayout(top)

        self.title_edit = QLineEdit()
        self.title_edit.setObjectName("documentTitle")
        editor_layout.addWidget(self.title_edit)

        self.resources_box = QFrame()
        self.resources_box.setObjectName("resourceSummary")
        resources_layout = QVBoxLayout(self.resources_box)
        resources_layout.setContentsMargins(12, 9, 12, 9)
        self.resources_heading = QLabel()
        self.resources_heading.setObjectName("fieldLabel")
        self.resources_label = QLabel()
        self.resources_label.setObjectName("mutedText")
        self.resources_label.setWordWrap(True)
        resources_layout.addWidget(self.resources_heading)
        resources_layout.addWidget(self.resources_label)
        editor_layout.addWidget(self.resources_box)

        actions = QHBoxLayout()
        self.link_button = QPushButton()
        self.link_button.setObjectName("primaryButton")
        self.link_button.clicked.connect(lambda: self.linkResourceRequested.emit(self.current_decision_id or 0))
        self.changes_button = QPushButton()
        self.changes_button.clicked.connect(lambda: self.viewChangesRequested.emit(self.current_decision_id or 0))
        self.review_button = QPushButton()
        self.review_button.clicked.connect(lambda: self.markReviewedRequested.emit(self.current_decision_id or 0))
        actions.addWidget(self.link_button)
        actions.addWidget(self.changes_button)
        actions.addWidget(self.review_button)
        actions.addStretch(1)
        editor_layout.addLayout(actions)

        self.empty_help = QLabel()
        self.empty_help.setObjectName("emptyInlineState")
        self.empty_help.setWordWrap(True)
        editor_layout.addWidget(self.empty_help)

        self.editor = NoteEditor()
        editor_layout.addWidget(self.editor, 1)

        splitter.addWidget(left)
        splitter.addWidget(editor_wrap)
        splitter.setSizes([360, 900])
        root.addWidget(splitter, 1)

        self.title_edit.textChanged.connect(self._mark_dirty)
        self.editor.textChanged.connect(self._mark_dirty)
        self.status_combo.currentIndexChanged.connect(self._mark_dirty)
        self.i18n.languageChanged.connect(lambda _language: self.retranslate_ui())
        self._set_editor_enabled(False)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        self.page_title.setText(self.i18n.t("decision.title"))
        self.page_subtitle.setText(self.i18n.t("decision.subtitle"))
        self.new_button.setText(self.i18n.t("decision.new"))
        self.new_button.setToolTip(self.i18n.t("tip.decision.new"))
        self.guide_title.setText(self.i18n.t("decision.guide_title"))
        self.guide_text.setText(self.i18n.t("decision.guide"))
        self.search.setPlaceholderText(self.i18n.t("decision.search"))
        self.repo_filter_label.setText(self.i18n.t("decision.filter_repo"))
        self.repo_filter.setToolTip(self.i18n.t("tip.decision.repo_filter"))
        self.project_caption.setText(self.i18n.t("decision.current_project"))
        self.repo_caption.setText(self.i18n.t("decision.connected_repos"))
        self.title_edit.setPlaceholderText(self.i18n.t("decision.title_placeholder"))
        self.resources_heading.setText(self.i18n.t("decision.resources"))
        self.link_button.setText(self.i18n.t("decision.link"))
        self.changes_button.setText(self.i18n.t("decision.changes"))
        self.review_button.setText(self.i18n.t("decision.review"))
        self.link_button.setToolTip(self.i18n.t("tip.decision.link"))
        self.changes_button.setToolTip(self.i18n.t("tip.decision.changes"))
        self.review_button.setToolTip(self.i18n.t("tip.decision.review"))
        self.empty_help.setText(
            f"{self.i18n.t('decision.empty_title')}\n{self.i18n.t('decision.empty_text')}"
            if self.current_decision_id is None else ""
        )
        self._rebuild_status_combo()
        self._refresh_repo_filter()
        self.refresh(self.current_decision_id)

    def _rebuild_status_combo(self) -> None:
        current = self.status_combo.currentData()
        self._loading = True
        self.status_combo.blockSignals(True)
        self.status_combo.clear()
        for status in DecisionStatus:
            self.status_combo.addItem(self.i18n.t(f"decision.status.{status.value}"), status.value)
        index = self.status_combo.findData(current)
        self.status_combo.setCurrentIndex(max(0, index))
        self.status_combo.blockSignals(False)
        self._loading = False

    def _filters_changed(self, *_args) -> None:
        self.save_current()
        self.refresh()

    def _refresh_repo_filter(self) -> None:
        current = self.repo_filter.currentData()
        self.repo_filter.blockSignals(True)
        self.repo_filter.clear()
        self.repo_filter.addItem(self.i18n.t("decision.all_repos"), None)
        self.repo_filter.addItem(self.i18n.t("decision.unlinked"), -1)
        if self.project_id is not None:
            for repo in self.database.list_repositories(self.project_id):
                self.repo_filter.addItem(repo.full_name or repo.name, repo.id)
        index = self.repo_filter.findData(current)
        self.repo_filter.setCurrentIndex(max(0, index))
        self.repo_filter.blockSignals(False)

    def set_project(self, project_id: int) -> None:
        if self.project_id == project_id:
            self._update_project_context()
            return
        self.save_current()
        self.project_id = project_id
        self.current_decision_id = None
        self._refresh_repo_filter()
        self._update_project_context()
        self.refresh()

    def _update_project_context(self) -> None:
        project = self.database.get_project(self.project_id) if self.project_id is not None else None
        name = project.name if project else "—"
        self.project_value.setText(name)
        self.list_heading.setText(name)

    def _decision_repository_ids(self, decision_id: int) -> set[int]:
        return {link.repository_id for link in self.database.list_resource_links("decision", decision_id)}

    def refresh(self, select_id: int | None = None) -> None:
        if self.project_id is None:
            return
        decisions = self.database.list_decisions(self.project_id, self.search.text())
        repo_filter = self.repo_filter.currentData() if self.repo_filter.count() else None
        if repo_filter is not None:
            filtered = []
            for decision in decisions:
                repo_ids = self._decision_repository_ids(decision.id)
                if int(repo_filter) == -1 and not repo_ids:
                    filtered.append(decision)
                elif int(repo_filter) >= 0 and int(repo_filter) in repo_ids:
                    filtered.append(decision)
            decisions = filtered
        current = select_id or self.current_decision_id
        self.list.blockSignals(True)
        self.list.clear()
        target = None
        for decision in decisions:
            repo_names = []
            for rid in self._decision_repository_ids(decision.id):
                repo = self.database.get_repository(rid)
                if repo:
                    repo_names.append(repo.full_name or repo.name)
            repo_line = ", ".join(sorted(repo_names, key=str.casefold)) if repo_names else self.i18n.t("decision.unlinked")
            status_text = self.i18n.t(f"decision.status.{decision.status}")
            item = QListWidgetItem(f"{decision.decision_key}  ·  {status_text}\n{decision.title}\n{repo_line}")
            item.setData(Qt.ItemDataRole.UserRole, decision.id)
            item.setToolTip(
                ("Bu kararı açar. Alt satırda kararın bağlı olduğu depo gösterilir." if self.i18n.language == "tr"
                 else "Open this decision. The last line shows which repository the decision is connected to.")
            )
            item.setSizeHint(item.sizeHint().expandedTo(item.sizeHint()))
            self.list.addItem(item)
            if decision.id == current:
                target = item
        self.list.blockSignals(False)
        if target:
            self.list.setCurrentItem(target)
        elif self.list.count():
            self.list.setCurrentRow(0)
        elif not decisions:
            self._clear_editor()

    def new_decision(self) -> None:
        if self.project_id is None:
            return
        self.save_current()
        try:
            decision = self.database.create_decision(self.project_id)
        except DatabaseError as exc:
            QMessageBox.critical(self, "Create Decision Failed", str(exc))
            return
        self.current_decision_id = decision.id
        self.refresh(decision.id)
        self.title_edit.setFocus()
        self.title_edit.selectAll()

    def _selection_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        decision_id = int(current.data(Qt.ItemDataRole.UserRole))
        if decision_id != self.current_decision_id:
            self.save_current()
            self.open_decision(decision_id)

    def open_decision(self, decision_id: int) -> None:
        decision = self.database.get_decision(decision_id)
        if not decision:
            return
        self._loading = True
        try:
            self.current_decision_id = decision.id
            self.key_label.setText(decision.decision_key)
            self.title_edit.setText(decision.title)
            self.editor.setHtml(decision.content_html) if decision.content_html else self.editor.clear()
            index = self.status_combo.findData(decision.status)
            self.status_combo.setCurrentIndex(max(0, index))
            self._dirty = False
            self._set_editor_enabled(True)
            self.empty_help.clear()
            self.refresh_resources()
        finally:
            self._loading = False

    def _mark_dirty(self) -> None:
        if self._loading or self.current_decision_id is None:
            return
        self._dirty = True
        self.timer.start(750)

    def save_current(self) -> None:
        self.timer.stop()
        if self._loading or not self._dirty or self.current_decision_id is None:
            return
        try:
            self.database.update_decision(
                self.current_decision_id,
                self.title_edit.text(),
                self.editor.document().toHtml(),
                self.editor.toPlainText(),
                str(self.status_combo.currentData()),
            )
            self._dirty = False
            self.refresh(self.current_decision_id)
        except DatabaseError as exc:
            QMessageBox.critical(self, "Save Decision Failed", str(exc))

    def refresh_resources(self) -> None:
        if self.current_decision_id is None:
            self.resources_label.setText(self.i18n.t("decision.no_resources"))
            self.repo_value.setText(self.i18n.t("decision.no_repo"))
            return
        links = self.database.list_resource_links("decision", self.current_decision_id)
        if not links:
            self.resources_label.setText(self.i18n.t("decision.no_resources"))
            self.repo_value.setText(self.i18n.t("decision.no_repo"))
            return
        lines: list[str] = []
        repos: list[str] = []
        for link in links:
            repo = self.database.get_repository(link.repository_id)
            repo_name = (repo.full_name or repo.name) if repo else f"Repository #{link.repository_id}"
            if repo_name not in repos:
                repos.append(repo_name)
            target = link.target_value or ("Entire repository" if self.i18n.language == "en" else "Tüm depo")
            type_label = {
                "repository": self.i18n.t("resources.repo"),
                "directory": self.i18n.t("resources.directory"),
                "file": self.i18n.t("resources.file"),
                "branch": self.i18n.t("resources.branch"),
                "commit": self.i18n.t("resources.commit"),
                "pull_request": self.i18n.t("resources.pr"),
            }.get(link.target_type, link.target_type)
            lines.append(f"{repo_name}  →  {type_label}: {target}")
        self.repo_value.setText(" · ".join(repos))
        self.resources_label.setText("\n".join(lines))

    def _clear_editor(self) -> None:
        self._loading = True
        self.current_decision_id = None
        self.key_label.setText("DEC-—")
        self.title_edit.clear()
        self.editor.clear()
        self.resources_label.setText(self.i18n.t("decision.no_resources"))
        self.repo_value.setText(self.i18n.t("decision.no_repo"))
        self.empty_help.setText(f"{self.i18n.t('decision.empty_title')}\n{self.i18n.t('decision.empty_text')}")
        self._set_editor_enabled(False)
        self._loading = False

    def _set_editor_enabled(self, enabled: bool) -> None:
        for widget in (self.title_edit, self.editor, self.status_combo, self.link_button, self.changes_button, self.review_button):
            widget.setEnabled(enabled)

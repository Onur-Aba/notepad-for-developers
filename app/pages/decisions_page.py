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
    QMenu,
    QInputDialog,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QLineEdit,
)

from app.database import Database, DatabaseError
from app.i18n import I18n
from app.models import DecisionStatus, ReviewStatus
from app.widgets.note_editor import NoteEditor
from app.widgets.status_badge import StatusBadge
from app.widgets.tags_editor import TagsEditor
from app.widgets.resource_history_dialog import ResourceHistoryDialog


class DecisionsPage(QWidget):
    linkResourceRequested = Signal(int)
    viewChangesRequested = Signal(int)
    markReviewedRequested = Signal(int)
    decisionsChanged = Signal()

    def __init__(self, database: Database, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.i18n = i18n
        self.project_id: int | None = None
        self.current_decision_id: int | None = None
        self.review_statuses: dict[int, ReviewStatus] = {}
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
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._show_context_menu)
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

        self.decision_heading = QLabel()
        self.decision_heading.setObjectName("pageTitle")
        self.decision_heading.setWordWrap(True)
        editor_layout.addWidget(self.decision_heading)

        top = QHBoxLayout()
        self.key_label = QLabel("ID: DEC-—")
        self.key_label.setObjectName("decisionKey")
        self.status_combo = QComboBox()
        self.review_badge = StatusBadge()
        top.addWidget(self.key_label)
        top.addWidget(self.status_combo)
        top.addStretch(1)
        top.addWidget(self.review_badge)
        editor_layout.addLayout(top)

        title_row = QHBoxLayout()
        self.title_edit = QLineEdit()
        self.title_edit.setObjectName("documentTitle")
        self.title_edit.setMinimumHeight(42)
        self.favorite_button = QPushButton("☆")
        self.favorite_button.setFixedWidth(44)
        self.favorite_button.clicked.connect(self._toggle_favorite)
        self.history_button = QPushButton()
        self.history_button.clicked.connect(self._open_history)
        title_row.addWidget(self.title_edit, 1)
        title_row.addWidget(self.favorite_button)
        title_row.addWidget(self.history_button)
        editor_layout.addLayout(title_row)
        self.tags_editor = TagsEditor(self.i18n)
        self.tags_editor.tagsChanged.connect(self._tags_changed)
        editor_layout.addWidget(self.tags_editor)

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

        self.tracking_box = QFrame()
        self.tracking_box.setObjectName("helperBanner")
        tracking_layout = QVBoxLayout(self.tracking_box)
        tracking_layout.setContentsMargins(12, 9, 12, 9)
        tracking_layout.setSpacing(3)
        self.tracking_title = QLabel()
        self.tracking_title.setObjectName("helperTitle")
        self.tracking_text = QLabel()
        self.tracking_text.setWordWrap(True)
        self.tracking_text.setObjectName("mutedText")
        tracking_layout.addWidget(self.tracking_title)
        tracking_layout.addWidget(self.tracking_text)
        editor_layout.addWidget(self.tracking_box)

        actions = QHBoxLayout()
        self.link_button = QPushButton()
        self.link_button.setObjectName("primaryButton")
        self.link_button.clicked.connect(lambda: self.linkResourceRequested.emit(self.current_decision_id or 0))
        self.changes_button = QPushButton()
        self.changes_button.clicked.connect(lambda: self.viewChangesRequested.emit(self.current_decision_id or 0))
        self.review_button = QPushButton()
        self.review_button.clicked.connect(lambda: self.markReviewedRequested.emit(self.current_decision_id or 0))
        self.delete_button = QPushButton()
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.clicked.connect(self.delete_current_decision)
        actions.addWidget(self.link_button)
        actions.addWidget(self.changes_button)
        actions.addWidget(self.review_button)
        actions.addWidget(self.delete_button)
        actions.addStretch(1)
        editor_layout.addLayout(actions)

        self.empty_help = QLabel()
        self.empty_help.setObjectName("emptyInlineState")
        self.empty_help.setWordWrap(True)
        self.empty_help.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_help.setMinimumHeight(220)
        editor_layout.addWidget(self.empty_help, 1)

        self.editor = NoteEditor()
        editor_layout.addWidget(self.editor, 1)

        # Keep a single source of truth for the right-side editing UI.  When
        # no decision is selected we hide every editor control and show only
        # the friendly empty state.  This is intentionally visibility-based
        # (not merely disabled) so the user is never presented with a form
        # that looks editable before a decision has been chosen.
        self._editor_widgets = (
            self.context_bar,
            self.decision_heading,
            self.key_label,
            self.status_combo,
            self.review_badge,
            self.title_edit,
            self.favorite_button,
            self.history_button,
            self.tags_editor,
            self.resources_box,
            self.tracking_box,
            self.link_button,
            self.changes_button,
            self.review_button,
            self.delete_button,
            self.editor,
        )

        splitter.addWidget(left)
        splitter.addWidget(editor_wrap)
        splitter.setSizes([360, 900])
        root.addWidget(splitter, 1)

        self.title_edit.textChanged.connect(self._title_changed)
        self.editor.textChanged.connect(self._mark_dirty)
        self.status_combo.currentIndexChanged.connect(self._mark_dirty)
        self.i18n.languageChanged.connect(lambda _language: self.retranslate_ui())
        self._set_editor_enabled(False)
        self.retranslate_ui()
        self.set_review_status(ReviewStatus.NOT_REVIEWED, has_links=False)

    def retranslate_ui(self) -> None:
        self.editor.retranslate_ui()
        self.page_title.setText(self.i18n.t("decision.title"))
        self.page_subtitle.setText(self.i18n.t("decision.subtitle"))
        self.new_button.setText(self.i18n.t("decision.new"))
        self.new_button.setToolTip(self.i18n.t("tip.decision.new"))
        self.guide_title.setText(self.i18n.t("decision.guide_title"))
        self.guide_text.setText(
            "Karar, kodun NE yaptığını yazdığınız yer değildir; o kodu NEDEN öyle yaptığınızı kaydettiğiniz yerdir. "
            "Örnek: ‘SQLite kullandık çünkü uygulama yerel çalışmalı ve sunucu gerektirmemeli.’ Sonra bu kararı ilgili dosya/klasöre bağlayın. "
            "‘Takibi başlat’ dediğiniz andaki commit başlangıç olur. Bundan sonra bağlı kod değişirse DevNest bu kararı İncelenecekler'e taşır."
            if self.i18n.language == "tr" else
            "A decision is not where you describe WHAT the code does; it records WHY the code was built that way. "
            "Example: ‘We use SQLite because the app must work locally without a server.’ Then connect the decision to the relevant file/folder. "
            "When you start tracking, the current commit becomes the reference point. If linked code changes later, DevNest moves this decision to Needs Review."
        )
        self.search.setPlaceholderText(self.i18n.t("decision.search"))
        self.repo_filter_label.setText(self.i18n.t("decision.filter_repo"))
        self.repo_filter.setToolTip(self.i18n.t("tip.decision.repo_filter"))
        self.project_caption.setText(self.i18n.t("decision.current_project"))
        self.repo_caption.setText(self.i18n.t("decision.connected_repos"))
        self.title_edit.setPlaceholderText(self.i18n.t("decision.title_placeholder"))
        self.editor.setPlaceholderText(
            (
                "Buraya kararın nedenini yazın. Örnek:\n\n"
                "Sorun: Hangi problemi çözüyorduk?\n"
                "Karar: Ne yapmayı seçtik?\n"
                "Neden: Neden bu seçeneği tercih ettik?\n"
                "Sonuç: Bunun bize getirdiği avantaj/dezavantaj ne?"
            )
            if self.i18n.language == "tr" else
            (
                "Write the reasoning here. Example:\n\n"
                "Problem: What problem were we solving?\n"
                "Decision: What did we choose?\n"
                "Why: Why did we choose it?\n"
                "Consequences: What are the benefits/trade-offs?"
            )
        )
        self.status_combo.setToolTip(
            "Bu alan kararın yaşam durumudur (önerildi, kabul edildi vb.). Kodun değişip değişmediğini sağdaki takip durumu gösterir."
            if self.i18n.language == "tr" else
            "This is the decision lifecycle (proposed, accepted, etc.). The tracking state on the right tells you whether linked code changed."
        )
        self.resources_heading.setText(self.i18n.t("decision.resources"))
        self.link_button.setText(self.i18n.t("decision.link"))
        self.changes_button.setText(self.i18n.t("decision.changes"))
        self.review_button.setText(self.i18n.t("decision.review"))
        self.favorite_button.setToolTip("Bu kararı favorilere ekle/çıkar." if self.i18n.language == "tr" else "Add/remove this decision from favorites.")
        self.history_button.setText("Geçmiş" if self.i18n.language == "tr" else "History")
        self.history_button.setToolTip("Karar değişikliklerini ve review commit geçmişini gösterir." if self.i18n.language == "tr" else "Show decision changes and reviewed commit history.")
        self.delete_button.setText("Kararı sil" if self.i18n.language == "tr" else "Delete decision")
        self.delete_button.setToolTip(
            "Bu kararı ve yalnızca DevNest içindeki bağlantılarını siler. GitHub deposuna veya kaynak koda dokunmaz."
            if self.i18n.language == "tr" else
            "Delete this decision and its DevNest-only links. This never deletes or changes source code on GitHub."
        )
        self.key_label.setToolTip(
            "Bu değişmeyen teknik kimliktir. Kararın görünen başlığı üstte yazdığınız isimdir."
            if self.i18n.language == "tr" else
            "This is the stable technical ID. The visible decision heading is the name you entered above."
        )
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
            review_status = self.review_statuses.get(decision.id)
            tr = self.i18n.language == "tr"
            tracking_text = {
                ReviewStatus.CURRENT: "Takip: ✓ Güncel" if tr else "Tracking: ✓ Current",
                ReviewStatus.NEEDS_REVIEW: "Takip: ⚠ Yeniden kontrol et" if tr else "Tracking: ⚠ Needs review",
                ReviewStatus.NOT_REVIEWED: "Takip: Başlatılmadı" if tr else "Tracking: Not started",
                ReviewStatus.CANNOT_COMPARE: "Takip: Şu an karşılaştırılamıyor" if tr else "Tracking: Cannot compare",
            }.get(review_status, "Takip: Başlatılmadı" if tr else "Tracking: Not started")
            repo_prefix = "Depo: " if tr else "Repository: "
            id_prefix = "Kimlik" if tr else "ID"
            favorite_prefix = "★ " if self.database.is_favorite("decision", decision.id) else ""
            tags = self.database.get_tags("decision", decision.id)
            tags_line = ("\n#" + "  #".join(tags)) if tags else ""
            item = QListWidgetItem(f"{favorite_prefix}{decision.title}\n{id_prefix}: {decision.decision_key} · {status_text}\n{repo_prefix}{repo_line}\n{tracking_text}{tags_line}")
            item.setData(Qt.ItemDataRole.UserRole, decision.id)
            item.setToolTip(
                ("Kararı açar. İlk satır kararın gerçek başlığıdır; DEC-xxx yalnızca değişmeyen kimliğidir. Sağ tıklayarak adını düzenleyebilir veya silebilirsiniz." if self.i18n.language == "tr"
                 else "Open the decision. The first line is its real title; DEC-xxx is only its stable ID. Right-click to rename or delete it.")
            )
            item.setSizeHint(item.sizeHint().expandedTo(item.sizeHint()))
            self.list.addItem(item)
            if decision.id == current:
                target = item
        self.list.blockSignals(False)
        if target:
            # Select without firing a second selection handler; then load the
            # decision explicitly.  This keeps list selection and editor state
            # synchronized even after a refresh/rebuild of the QListWidget.
            self.list.blockSignals(True)
            self.list.setCurrentItem(target)
            self.list.blockSignals(False)
            self.open_decision(int(target.data(Qt.ItemDataRole.UserRole)))
        else:
            # Do not silently choose the first decision.  With no explicit
            # selection the right side must remain an empty state until the
            # user chooses a decision from the list.
            self.list.clearSelection()
            self.list.setCurrentItem(None)
            self._clear_editor()

    def new_decision(self) -> None:
        if self.project_id is None:
            return
        self.save_current()
        try:
            decision = self.database.create_decision(
                self.project_id,
                "Yeni Karar" if self.i18n.language == "tr" else "Untitled Decision",
            )
        except DatabaseError as exc:
            QMessageBox.critical(self, "Karar Oluşturulamadı" if self.i18n.language == "tr" else "Create Decision Failed", str(exc))
            return
        self.current_decision_id = decision.id
        self.refresh(decision.id)
        self.title_edit.setFocus()
        self.title_edit.selectAll()

    def _selection_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None:
            self._clear_editor()
            return
        decision_id = int(current.data(Qt.ItemDataRole.UserRole))
        if decision_id != self.current_decision_id:
            self.save_current(refresh_after=False)
        # Always load the clicked decision.  In particular, a freshly created
        # decision already has current_decision_id set before the list item is
        # selected; the old equality guard therefore skipped the actual load.
        self.open_decision(decision_id)

    def open_decision(self, decision_id: int) -> None:
        decision = self.database.get_decision(decision_id)
        if not decision:
            return
        self._loading = True
        try:
            self.current_decision_id = decision.id
            self.key_label.setText(("Kimlik: " if self.i18n.language == "tr" else "ID: ") + decision.decision_key)
            self.decision_heading.setText(decision.title)
            self.title_edit.setText(decision.title)
            self.editor.setHtml(decision.content_html) if decision.content_html else self.editor.clear()
            index = self.status_combo.findData(decision.status)
            self.status_combo.setCurrentIndex(max(0, index))
            self._dirty = False
            self._set_editor_enabled(True)
            self.empty_help.clear()
            self.tags_editor.set_tags(self.database.get_tags("decision", decision.id))
            self.favorite_button.setText("★" if self.database.is_favorite("decision", decision.id) else "☆")
            self.database.touch_recent("decision", decision.id, f"{decision.decision_key} · {decision.title}", decision.project_id)
            self.refresh_resources()
        finally:
            self._loading = False

    def _title_changed(self) -> None:
        if not self._loading:
            title = self.title_edit.text().strip()
            self.decision_heading.setText(title or ("Başlıksız karar" if self.i18n.language == "tr" else "Untitled decision"))
        self._mark_dirty()

    def _show_context_menu(self, pos) -> None:
        item = self.list.itemAt(pos)
        if item is None:
            return
        decision_id = int(item.data(Qt.ItemDataRole.UserRole))
        decision = self.database.get_decision(decision_id)
        if decision is None:
            return
        tr = self.i18n.language == "tr"
        menu = QMenu(self)
        open_action = menu.addAction("Aç ve düzenle" if tr else "Open and edit")
        rename_action = menu.addAction("Başlığı değiştir…" if tr else "Rename title…")
        menu.addSeparator()
        delete_action = menu.addAction("Kararı sil…" if tr else "Delete decision…")
        chosen = menu.exec(self.list.mapToGlobal(pos))
        if chosen == open_action:
            self.list.setCurrentItem(item)
            self.open_decision(decision_id)
            self.title_edit.setFocus()
        elif chosen == rename_action:
            title, ok = QInputDialog.getText(
                self, "Karar başlığını değiştir" if tr else "Rename decision",
                "Yeni başlık:" if tr else "New title:", text=decision.title,
            )
            if ok and title.strip():
                self.database.update_decision(decision.id, title.strip(), decision.content_html, decision.content_plain, decision.status)
                self.refresh(decision.id)
                self.open_decision(decision.id)
                self.decisionsChanged.emit()
        elif chosen == delete_action:
            self.delete_decision(decision_id)

    def delete_current_decision(self) -> None:
        if self.current_decision_id is not None:
            self.delete_decision(self.current_decision_id)

    def delete_decision(self, decision_id: int) -> None:
        decision = self.database.get_decision(decision_id)
        if decision is None:
            return
        tr = self.i18n.language == "tr"
        answer = QMessageBox.question(
            self, "Kararı sil" if tr else "Delete decision",
            (
                f'“{decision.title}” kararı silinsin mi?\n\n{decision.decision_key} kimliği tekrar kullanılmaz. '
                "DevNest içindeki kod bağlantıları ve inceleme başlangıç noktaları da kaldırılır. Kaynak kod veya GitHub deposu değişmez."
                if tr else
                f'Delete “{decision.title}”?\n\nThe {decision.decision_key} ID will not be reused. '
                "DevNest-only code links and review baselines for this decision are also removed. Source code and GitHub are not changed."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.save_current()
            self.database.delete_decision(decision_id)
        except DatabaseError as exc:
            QMessageBox.critical(self, "Karar Silinemedi" if tr else "Delete Decision Failed", str(exc))
            return
        if self.current_decision_id == decision_id:
            self.current_decision_id = None
        self.refresh()
        self.decisionsChanged.emit()

    def _tags_changed(self, tags: list[str]) -> None:
        if self.current_decision_id is None or self._loading:
            return
        self.database.set_tags("decision", self.current_decision_id, tags)
        self.refresh(self.current_decision_id)
        self.decisionsChanged.emit()

    def _toggle_favorite(self) -> None:
        if self.current_decision_id is None:
            return
        favorite = not self.database.is_favorite("decision", self.current_decision_id)
        self.database.set_favorite("decision", self.current_decision_id, favorite, self.project_id)
        self.favorite_button.setText("★" if favorite else "☆")
        self.refresh(self.current_decision_id)
        self.decisionsChanged.emit()

    def _open_history(self) -> None:
        if self.current_decision_id is not None:
            ResourceHistoryDialog(self.database, "decision", self.current_decision_id, None, self.i18n, self).exec()

    def _mark_dirty(self) -> None:
        if self._loading or self.current_decision_id is None:
            return
        self._dirty = True
        self.timer.start(750)

    def save_current(self, refresh_after: bool = True) -> None:
        self.timer.stop()
        if self._loading or not self._dirty or self.current_decision_id is None:
            return
        try:
            decision_id = self.current_decision_id
            self.database.update_decision(
                decision_id,
                self.title_edit.text(),
                self.editor.document().toHtml(),
                self.editor.toPlainText(),
                str(self.status_combo.currentData()),
            )
            self._dirty = False
            if refresh_after:
                self.refresh(decision_id)
        except DatabaseError as exc:
            QMessageBox.critical(self, "Karar Kaydedilemedi" if self.i18n.language == "tr" else "Save Decision Failed", str(exc))

    def refresh_resources(self) -> None:
        if self.current_decision_id is None:
            self.resources_label.setText(self.i18n.t("decision.no_resources"))
            self.repo_value.setText(self.i18n.t("decision.no_repo"))
            self.set_review_status(ReviewStatus.NOT_REVIEWED, has_links=False)
            return
        links = self.database.list_resource_links("decision", self.current_decision_id)
        if not links:
            self.resources_label.setText(self.i18n.t("decision.no_resources"))
            self.repo_value.setText(self.i18n.t("decision.no_repo"))
            self.set_review_status(ReviewStatus.NOT_REVIEWED, has_links=False)
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
        self.key_label.setText(("Kimlik: " if self.i18n.language == "tr" else "ID: ") + "DEC-—")
        self.decision_heading.setText("Karar seçilmedi" if self.i18n.language == "tr" else "No decision selected")
        self.title_edit.clear()
        self.editor.clear()
        self.resources_label.setText(self.i18n.t("decision.no_resources"))
        self.tags_editor.set_tags([])
        self.favorite_button.setText("☆")
        self.repo_value.setText(self.i18n.t("decision.no_repo"))
        self.empty_help.setText(f"{self.i18n.t('decision.empty_title')}\n{self.i18n.t('decision.empty_text')}")
        self._set_editor_enabled(False)
        self._loading = False

    def set_review_summaries(self, summaries) -> None:
        priorities = {
            ReviewStatus.NEEDS_REVIEW: 4,
            ReviewStatus.CANNOT_COMPARE: 3,
            ReviewStatus.NOT_REVIEWED: 2,
            ReviewStatus.CURRENT: 1,
        }
        mapping: dict[int, ReviewStatus] = {}
        for summary in summaries:
            link = summary.resource_link
            if link.resource_type != "decision":
                continue
            try:
                decision_id = int(link.resource_id)
            except (TypeError, ValueError):
                continue
            current = mapping.get(decision_id)
            if current is None or priorities.get(summary.status, 0) > priorities.get(current, 0):
                mapping[decision_id] = summary.status
        self.review_statuses = mapping
        if self.project_id is not None:
            self.refresh(self.current_decision_id)

    def set_review_status(self, status: ReviewStatus, has_links: bool = True) -> None:
        """Explain tracking state in plain language and make the next action obvious."""
        tr = self.i18n.language == "tr"
        self.review_badge.set_status(status)
        if not has_links:
            self.tracking_title.setText("Takip henüz başlamadı" if tr else "Tracking has not started yet")
            self.tracking_text.setText(
                "Önce ‘Kod bağla’ düğmesine basıp bu kararın hangi depo, klasör veya dosyayla ilgili olduğunu seçin. Kod bağlanmadan DevNest hangi değişikliği izleyeceğini bilemez."
                if tr else
                "First choose ‘Connect code’ and select which repository, folder or file this decision belongs to. Until code is connected, DevNest does not know what changes to watch."
            )
            self.review_button.setText("2. Takibi başlat" if tr else "2. Start tracking")
            return
        if status == ReviewStatus.NOT_REVIEWED:
            self.tracking_title.setText("Kod bağlı, fakat başlangıç noktası seçilmedi" if tr else "Code is connected, but no starting point exists")
            self.tracking_text.setText(
                "Şimdi ‘Takibi başlat’ düğmesine basın. DevNest deponun şu anki commit'ini başlangıç kabul eder. BUNDAN SONRA bağlı kodda yapılan commitler bu kararı otomatik olarak İncelenecekler'e taşır."
                if tr else
                "Choose ‘Start tracking’ now. DevNest saves the repository's current commit as the starting point. AFTER THAT, later commits that touch the linked code automatically move this decision to Needs Review."
            )
            self.review_button.setText("2. Takibi başlat" if tr else "2. Start tracking")
        elif status == ReviewStatus.CURRENT:
            self.tracking_title.setText("✓ Takip aktif — şu anda yeniden inceleme gerekmiyor" if tr else "✓ Tracking is active — nothing needs re-checking right now")
            self.tracking_text.setText(
                "Bu kararın bağlı olduğu kod izleniyor. Yeni bir commit bağlı dosya/klasörü değiştirirse durum otomatik olarak ‘İncelenecek’ olur; sayfa değiştirmeniz gerekmez."
                if tr else
                "The code connected to this decision is being watched. If a new commit changes the linked file/folder, the state automatically becomes Needs Review; you do not need to change pages."
            )
            self.review_button.setText("Kontrol noktasını şimdi güncelle" if tr else "Update check point now")
        elif status == ReviewStatus.NEEDS_REVIEW:
            self.tracking_title.setText("⚠ Bağlı kod değişti — bu kararı yeniden kontrol edin" if tr else "⚠ Linked code changed — re-check this decision")
            self.tracking_text.setText(
                "Önce ‘Neyin değiştiğini gör’ düğmesine basın. Kod değişikliği bu kararın gerekçesini etkilediyse metni güncelleyin. Hâlâ doğruysa ‘Bunu kontrol ettim’ diyerek yeni commit'i başlangıç noktası yapın."
                if tr else
                "First choose ‘See what changed’. If the code change affects the reasoning, update the decision text. If it is still correct, choose ‘I checked this’ to make the new commit the reference point."
            )
            self.review_button.setText("3. Bunu kontrol ettim" if tr else "3. I checked this")
        else:
            self.tracking_title.setText("! Şu anda kodla karşılaştırılamıyor" if tr else "! Code cannot be compared right now")
            self.tracking_text.setText(
                "Bağlı depo veya eski commit şu anda okunamıyor. Yerel Git yolunu ve GitHub bağlantısını kontrol edin; karar metniniz kaybolmaz."
                if tr else
                "The connected repository or old commit cannot currently be read. Check the local Git path and GitHub connection; your decision text remains safe."
            )
            self.review_button.setText("Tekrar kontrol et" if tr else "Check again")

    def _set_editor_enabled(self, enabled: bool) -> None:
        for widget in (self.title_edit, self.editor, self.status_combo, self.link_button, self.changes_button, self.review_button, self.delete_button):
            widget.setEnabled(enabled)
        for widget in self._editor_widgets:
            widget.setVisible(enabled)
        self.empty_help.setVisible(not enabled)

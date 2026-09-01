from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.database import Database
from app.i18n import I18n
from app.models import ChangedFile, CommitHistoryEntry, ReviewStatus, ReviewSummary
from app.widgets.status_badge import StatusBadge


class ReviewInboxPage(QWidget):
    refreshRequested = Signal()
    historyRequested = Signal()
    historyDetailsRequested = Signal(int, str)
    viewRequested = Signal(object)
    markReviewedRequested = Signal(object)

    def __init__(self, database: Database, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.i18n = i18n
        self.project_id: int | None = None
        self.summaries: list[ReviewSummary] = []
        self.history_entries: list[CommitHistoryEntry] = []
        self.history_errors: list[str] = []
        self._expanded_history: set[tuple[int, str]] = set()
        self._loading_history_details: set[tuple[int, str]] = set()

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 28, 30, 24)
        root.setSpacing(12)
        header = QHBoxLayout()
        titles = QVBoxLayout()
        self.title = QLabel()
        self.title.setObjectName("pageTitle")
        self.subtitle = QLabel()
        self.subtitle.setWordWrap(True)
        self.subtitle.setObjectName("pageSubtitle")
        titles.addWidget(self.title)
        titles.addWidget(self.subtitle)
        header.addLayout(titles, 1)
        root.addLayout(header)

        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self._tab_changed)
        root.addWidget(self.tabs, 1)

        self.review_tab = QWidget()
        review_root = QVBoxLayout(self.review_tab)
        review_root.setContentsMargins(0, 4, 0, 0)
        review_root.setSpacing(10)

        controls = QHBoxLayout()
        self.filter = QComboBox()
        self.filter.currentIndexChanged.connect(self._render)
        self.refresh_button = QPushButton()
        self.refresh_button.clicked.connect(self.refreshRequested)
        controls.addWidget(self.filter)
        controls.addStretch(1)
        controls.addWidget(self.refresh_button)
        review_root.addLayout(controls)

        self.explain = QLabel()
        self.explain.setWordWrap(True)
        self.explain.setObjectName("helperBanner")
        review_root.addWidget(self.explain)

        self.live_hint = QLabel()
        self.live_hint.setWordWrap(True)
        self.live_hint.setObjectName("mutedText")
        review_root.addWidget(self.live_hint)

        self.container = QWidget()
        self.cards = QVBoxLayout(self.container)
        self.cards.setContentsMargins(0, 4, 0, 0)
        self.cards.setSpacing(10)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(self.container)
        review_root.addWidget(scroll, 1)

        self.history_tab = QWidget()
        history_root = QVBoxLayout(self.history_tab)
        history_root.setContentsMargins(0, 4, 0, 0)
        history_root.setSpacing(10)
        history_header = QHBoxLayout()
        self.history_title = QLabel()
        self.history_title.setObjectName("sectionTitle")
        self.history_refresh = QPushButton()
        self.history_refresh.clicked.connect(self.historyRequested)
        history_header.addWidget(self.history_title)
        history_header.addStretch(1)
        history_header.addWidget(self.history_refresh)
        history_root.addLayout(history_header)
        self.history_help = QLabel()
        self.history_help.setWordWrap(True)
        self.history_help.setObjectName("helperBanner")
        history_root.addWidget(self.history_help)
        self.history_status = QLabel()
        self.history_status.setWordWrap(True)
        self.history_status.setObjectName("mutedText")
        history_root.addWidget(self.history_status)

        self.history_container = QWidget()
        self.history_cards = QVBoxLayout(self.history_container)
        self.history_cards.setContentsMargins(0, 4, 0, 0)
        self.history_cards.setSpacing(9)
        history_scroll = QScrollArea()
        history_scroll.setWidgetResizable(True)
        history_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        history_scroll.setWidget(self.history_container)
        history_root.addWidget(history_scroll, 1)

        self.tabs.addTab(self.review_tab, "")
        self.tabs.addTab(self.history_tab, "")
        self.i18n.languageChanged.connect(lambda _language: self.retranslate_ui())
        self.retranslate_ui()

    def set_project(self, project_id: int) -> None:
        changed = self.project_id != project_id
        self.project_id = project_id
        if changed:
            self.history_entries = []
            self.history_errors = []
            self._expanded_history.clear()
            self._loading_history_details.clear()
        self._render_history()
        if changed and self.tabs.currentWidget() is self.history_tab:
            self.historyRequested.emit()

    def retranslate_ui(self) -> None:
        tr = self.i18n.language == "tr"
        self.title.setText(self.i18n.t("review.title"))
        self.refresh_button.setText(self.i18n.t("review.refresh"))
        self.refresh_button.setToolTip(self.i18n.t("tip.review.refresh"))
        self.tabs.setTabText(0, "İncelenecekler" if tr else "Needs review")
        self.tabs.setTabText(1, "Proje Geçmişi" if tr else "Project history")
        self.explain.setText(
            "Burada gördüğünüz her kartın anlamı basit: DevNest, bir not/karar/mimari bilgisini belirli bir kod alanıyla ilişkilendirir. "
            "Siz o bilgiyi son kez kontrol ettikten sonra o kod alanı değişirse kart burada görünür. Bu, bilginin yanlış olduğu anlamına gelmez; yeniden bakmanız gerektiğini söyler."
            if tr else
            "Each card has one simple meaning: DevNest connects a note, decision or architecture item to a part of the code. "
            "If that code changes after your last check, the card appears here. It does not claim the knowledge is wrong; it only asks you to look again."
        )
        self.live_hint.setText(
            "● Canlı takip açık: Yerel Git deposunda yeni bir commit algılandığında bu ekranı değiştirmenize gerek kalmadan liste otomatik yenilenir."
            if tr else
            "● Live tracking is on: when a new commit is detected in a local Git repository, this list updates automatically without changing pages."
        )
        self.history_title.setText("Seçili projenin commit geçmişi" if tr else "Commit history for the selected project")
        self.history_refresh.setText("Geçmişi yenile" if tr else "Refresh history")
        self.history_refresh.setToolTip(
            "Üstte seçili projeye bağlı depoların commit geçmişini yeniden okur. Kodda hiçbir değişiklik yapmaz."
            if tr else
            "Reload commit history for repositories connected to the project selected at the top. This never changes code."
        )
        self.history_help.setText(
            "Bu bölüm, seçili projeye bağlı depolardaki commitleri en yeniden eskiye gösterir. Her commit altında hangi dosyaların eklendiğini, değiştirildiğini, silindiğini veya taşındığını normal dille görebilirsiniz."
            if tr else
            "This section shows commits from repositories connected to the selected project, newest first. Each commit explains which files were added, changed, deleted or moved in plain language."
        )
        current = self.filter.currentData()
        self.filter.blockSignals(True)
        self.filter.clear()
        self.filter.addItem(self.i18n.t("review.all"), "all")
        self.filter.addItem(self.i18n.t("review.notes"), "note")
        self.filter.addItem(self.i18n.t("review.decisions"), "decision")
        self.filter.addItem(self.i18n.t("review.architecture"), "diagram_item")
        index = self.filter.findData(current)
        self.filter.setCurrentIndex(max(0, index))
        self.filter.blockSignals(False)
        self._update_subtitle()
        self._render()
        self._render_history()

    def _tab_changed(self, index: int) -> None:
        if index == 1 and not self.history_entries:
            self.historyRequested.emit()

    def set_summaries(self, summaries: list[ReviewSummary]) -> None:
        self.summaries = summaries
        self._update_subtitle()
        self._render()

    def set_checking(self) -> None:
        self.subtitle.setText(
            "Depolardaki son commit kontrol ediliyor… Bu sırada uygulamayı kullanmaya devam edebilirsiniz."
            if self.i18n.language == "tr" else
            "Checking the latest repository commits… You can keep using the app while this runs."
        )

    def set_check_failed(self, message: str) -> None:
        self.subtitle.setText(
            f"Depo şu anda kontrol edilemedi: {message}. Yerel notlarınız ve diğer özellikler çalışmaya devam eder."
            if self.i18n.language == "tr" else
            f"Repository check is currently unavailable: {message}. Local notes and other features remain available."
        )

    def set_history_loading(self) -> None:
        self.history_status.setText(
            "Commit geçmişi arka planda okunuyor…" if self.i18n.language == "tr" else "Loading commit history in the background…"
        )

    def set_history_failed(self, message: str) -> None:
        self.history_status.setText(
            f"Geçmiş okunamadı: {message}" if self.i18n.language == "tr" else f"History could not be loaded: {message}"
        )

    def set_history(self, entries: list[CommitHistoryEntry], errors: list[str] | None = None) -> None:
        self.history_entries = sorted(entries, key=lambda x: x.commit.authored_at or "", reverse=True)
        self.history_errors = list(errors or [])
        valid = {(entry.repository_id, entry.commit.sha) for entry in self.history_entries}
        self._expanded_history.intersection_update(valid)
        self._loading_history_details.intersection_update(valid)
        self._render_history()

    def update_history_details(self, repository_id: int, sha: str, files: list[ChangedFile]) -> None:
        key = (repository_id, sha)
        self._loading_history_details.discard(key)
        self._expanded_history.add(key)
        for entry in self.history_entries:
            if entry.repository_id == repository_id and entry.commit.sha == sha:
                entry.changed_files = list(files)
                entry.files_loaded = True
                break
        self._render_history()

    def history_details_failed(self, repository_id: int, sha: str) -> None:
        self._loading_history_details.discard((repository_id, sha))
        self._render_history()

    def _toggle_history_entry(self, repository_id: int, sha: str) -> None:
        key = (repository_id, sha)
        if key in self._expanded_history:
            self._expanded_history.discard(key)
            self._render_history()
            return
        self._expanded_history.add(key)
        entry = next((item for item in self.history_entries if item.repository_id == repository_id and item.commit.sha == sha), None)
        if entry is not None and not entry.files_loaded:
            self._loading_history_details.add(key)
            self.historyDetailsRequested.emit(repository_id, sha)
        self._render_history()

    def _update_subtitle(self) -> None:
        needs = sum(1 for x in self.summaries if x.status == ReviewStatus.NEEDS_REVIEW)
        self.subtitle.setText(self.i18n.t("review.count", count=needs))

    def _render(self) -> None:
        while self.cards.count():
            item = self.cards.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        selected_type = str(self.filter.currentData()) if self.filter.count() else "all"
        visible = [
            summary for summary in self.summaries
            if summary.status == ReviewStatus.NEEDS_REVIEW
            and (selected_type == "all" or summary.resource_link.resource_type == selected_type)
        ]
        if not visible:
            empty = QLabel(self.i18n.t("review.empty"))
            empty.setWordWrap(True)
            empty.setObjectName("emptyState")
            self.cards.addWidget(empty, 1)
            return
        for summary in visible:
            frame = QFrame()
            frame.setObjectName("reviewCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(16, 13, 16, 13)
            layout.setSpacing(7)
            top = QHBoxLayout()
            label = QLabel(self._resource_title(summary))
            label.setObjectName("cardTitle")
            badge = StatusBadge(summary.status)
            top.addWidget(label)
            top.addStretch(1)
            top.addWidget(badge)
            layout.addLayout(top)

            repo = self.database.get_repository(summary.resource_link.repository_id)
            repo_name = (repo.full_name or repo.name) if repo else "—"
            repo_label = QLabel(("Depo: " if self.i18n.language == "tr" else "Repository: ") + repo_name)
            repo_label.setObjectName("mutedText")
            layout.addWidget(repo_label)

            details = QLabel(
                f"{self.i18n.t('review.checked_at')}: {(summary.baseline_sha or '—')[:10]}    "
                f"{self.i18n.t('review.current')}: {(summary.current_sha or '—')[:10]}\n"
                f"{self.i18n.t('review.since')}: {summary.commit_count} {self.i18n.t('review.commits')} · "
                f"{len(summary.linked_changed_files)} {self.i18n.t('review.files')}"
            )
            details.setObjectName("mutedText")
            layout.addWidget(details)

            if summary.linked_changed_files:
                preview = QLabel(self._changed_files_preview(summary.linked_changed_files))
                preview.setWordWrap(True)
                preview.setObjectName("changePreview")
                layout.addWidget(preview)

            actions = QHBoxLayout()
            view = QPushButton(self.i18n.t("review.view"))
            view.setObjectName("primaryButton")
            view.setToolTip(self.i18n.t("tip.review.view"))
            view.clicked.connect(lambda _checked=False, s=summary: self.viewRequested.emit(s))
            mark = QPushButton(self.i18n.t("review.mark"))
            mark.setToolTip(self.i18n.t("tip.review.mark"))
            mark.clicked.connect(lambda _checked=False, s=summary: self.markReviewedRequested.emit(s))
            actions.addWidget(view)
            actions.addWidget(mark)
            actions.addStretch(1)
            layout.addLayout(actions)
            self.cards.addWidget(frame)
        self.cards.addStretch(1)

    def _render_history(self) -> None:
        while self.history_cards.count():
            item = self.history_cards.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        project = self.database.get_project(self.project_id) if self.project_id is not None else None
        tr = self.i18n.language == "tr"
        project_name = project.name if project else ("Seçili proje yok" if tr else "No project selected")
        if self.history_errors:
            self.history_status.setText(
                (f"{len(self.history_entries)} commit gösteriliyor · Bazı depolar okunamadı: " if tr else
                 f"Showing {len(self.history_entries)} commits · Some repositories could not be read: ")
                + " | ".join(self.history_errors[:3])
            )
        elif self.history_entries:
            self.history_status.setText(
                f"{project_name} · {len(self.history_entries)} commit" if tr else f"{project_name} · {len(self.history_entries)} commits"
            )
        else:
            self.history_status.setText(
                f"{project_name} için henüz commit geçmişi yüklenmedi." if tr else f"Commit history has not been loaded for {project_name} yet."
            )
            empty = QLabel(
                "Bu projeye yerel Git veya erişilebilir GitHub deposu bağlayın; sonra ‘Geçmişi yenile’ düğmesine basın."
                if tr else
                "Connect a local Git or accessible GitHub repository to this project, then choose ‘Refresh history’."
            )
            empty.setWordWrap(True)
            empty.setObjectName("emptyState")
            self.history_cards.addWidget(empty, 1)
            return

        for entry in self.history_entries:
            key = (entry.repository_id, entry.commit.sha)
            expanded = key in self._expanded_history
            frame = QFrame()
            frame.setObjectName("reviewCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(16, 12, 16, 12)
            layout.setSpacing(6)

            header = QHBoxLayout()
            title_box = QVBoxLayout()
            title_box.setSpacing(3)
            title = QLabel(entry.commit.message or ("İsimsiz commit" if tr else "Untitled commit"))
            title.setObjectName("cardTitle")
            meta_bits = [entry.repository_name, entry.commit.short_sha]
            if entry.commit.author:
                meta_bits.append(entry.commit.author)
            if entry.commit.authored_at:
                meta_bits.append(self._friendly_date(entry.commit.authored_at))
            meta = QLabel(" · ".join(meta_bits))
            meta.setObjectName("mutedText")
            title_box.addWidget(title)
            title_box.addWidget(meta)
            arrow = QPushButton("▴" if expanded else "▾")
            arrow.setObjectName("disclosureButton")
            arrow.setFixedSize(34, 34)
            arrow.setToolTip(
                ("Bu committe değişen dosyaları gizle." if expanded else "Bu committe hangi dosyaların değiştiğini göster.")
                if tr else
                ("Hide files changed in this commit." if expanded else "Show which files changed in this commit.")
            )
            arrow.clicked.connect(
                lambda _checked=False, rid=entry.repository_id, sha=entry.commit.sha: self._toggle_history_entry(rid, sha)
            )
            header.addLayout(title_box, 1)
            header.addWidget(arrow, 0, Qt.AlignmentFlag.AlignTop)
            layout.addLayout(header)

            if expanded:
                details = QFrame()
                details.setObjectName("historyCommitDetails")
                details_layout = QVBoxLayout(details)
                details_layout.setContentsMargins(12, 10, 12, 10)
                details_layout.setSpacing(7)
                if key in self._loading_history_details:
                    loading = QLabel("Dosya değişiklikleri yükleniyor…" if tr else "Loading file changes…")
                    loading.setObjectName("mutedText")
                    details_layout.addWidget(loading)
                elif entry.files_loaded:
                    if entry.changed_files:
                        intro = QLabel("Bu committe değişenler:" if tr else "Changes in this commit:")
                        intro.setObjectName("bundleSectionTitle")
                        details_layout.addWidget(intro)
                        for changed in entry.changed_files:
                            change = QLabel(f"{self._human_status(changed.status, tr)}  —  {changed.path}")
                            change.setWordWrap(True)
                            change.setObjectName("changePreview")
                            details_layout.addWidget(change)
                            if changed.previous_path:
                                previous = QLabel(
                                    f"Önceki yol: {changed.previous_path}" if tr else f"Previous path: {changed.previous_path}"
                                )
                                previous.setObjectName("mutedText")
                                details_layout.addWidget(previous)
                    else:
                        none = QLabel("Bu commit için dosya değişikliği bulunamadı." if tr else "No file changes were found for this commit.")
                        none.setObjectName("mutedText")
                        details_layout.addWidget(none)
                else:
                    # Normally this is visible for only a split second before the
                    # async GitHub detail request starts. Keep it understandable if
                    # a provider is temporarily unavailable.
                    wait = QLabel("Dosya ayrıntısı henüz yüklenmedi." if tr else "File details have not loaded yet.")
                    wait.setObjectName("mutedText")
                    details_layout.addWidget(wait)
                layout.addWidget(details)
            self.history_cards.addWidget(frame)
        self.history_cards.addStretch(1)

    def _resource_title(self, summary: ReviewSummary) -> str:
        link = summary.resource_link
        if link.resource_type == "decision":
            try:
                decision = self.database.get_decision(int(link.resource_id))
            except (TypeError, ValueError):
                decision = None
            if decision:
                return f"{decision.title} · {decision.decision_key}"
        if link.resource_type == "note":
            try:
                note = self.database.get_note(int(link.resource_id))
            except (TypeError, ValueError):
                note = None
            if note:
                return ("Not · " if self.i18n.language == "tr" else "Note · ") + note.title
        if link.resource_type == "diagram_item":
            try:
                note = self.database.get_note(int(link.resource_parent_id))
            except (TypeError, ValueError):
                note = None
            if note:
                return ("Mimari · " if self.i18n.language == "tr" else "Architecture · ") + note.title
        kind = {
            "note": "Not" if self.i18n.language == "tr" else "Note",
            "decision": "Karar" if self.i18n.language == "tr" else "Decision",
            "diagram_item": "Mimari" if self.i18n.language == "tr" else "Architecture",
        }.get(link.resource_type, link.resource_type)
        return kind

    def _changed_files_preview(self, files: list[ChangedFile]) -> str:
        tr = self.i18n.language == "tr"
        lines = ["Bu bilgiyle doğrudan ilişkili değişiklikler:" if tr else "Changes directly related to this knowledge:"]
        for item in files[:4]:
            lines.append(f"• {self._human_status(item.status, tr)} — {item.path}")
        if len(files) > 4:
            lines.append(f"• +{len(files) - 4} başka dosya" if tr else f"• +{len(files) - 4} more files")
        return "\n".join(lines)

    @staticmethod
    def _human_status(status: str, tr: bool) -> str:
        code = (status or "M").upper()[:1]
        if tr:
            return {
                "A": "Yeni dosya eklendi",
                "M": "Dosya değiştirildi",
                "D": "Dosya silindi",
                "R": "Dosya taşındı/yeniden adlandırıldı",
                "C": "Dosya kopyalandı",
                "T": "Dosya türü değişti",
            }.get(code, "Dosyada değişiklik yapıldı")
        return {
            "A": "New file added",
            "M": "File changed",
            "D": "File deleted",
            "R": "File moved/renamed",
            "C": "File copied",
            "T": "File type changed",
        }.get(code, "File changed")

    @staticmethod
    def _friendly_date(value: str) -> str:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return value

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from app.database import Database
from app.i18n import I18n
from app.models import ChangedFile, ReviewStatus, ReviewSummary
from app.widgets.status_badge import StatusBadge


class ReviewInboxPage(QWidget):
    refreshRequested = Signal()
    viewRequested = Signal(object)
    markReviewedRequested = Signal(object)

    def __init__(self, database: Database, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.i18n = i18n
        self.summaries: list[ReviewSummary] = []
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
        self.filter = QComboBox()
        self.filter.currentIndexChanged.connect(self._render)
        self.refresh_button = QPushButton()
        self.refresh_button.clicked.connect(self.refreshRequested)
        header.addLayout(titles, 1)
        header.addWidget(self.filter)
        header.addWidget(self.refresh_button)
        root.addLayout(header)

        self.explain = QLabel()
        self.explain.setWordWrap(True)
        self.explain.setObjectName("helperBanner")
        root.addWidget(self.explain)

        self.live_hint = QLabel()
        self.live_hint.setWordWrap(True)
        self.live_hint.setObjectName("mutedText")
        root.addWidget(self.live_hint)

        self.container = QWidget()
        self.cards = QVBoxLayout(self.container)
        self.cards.setContentsMargins(0, 4, 0, 0)
        self.cards.setSpacing(10)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(self.container)
        root.addWidget(scroll, 1)
        self.i18n.languageChanged.connect(lambda _language: self.retranslate_ui())
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        tr = self.i18n.language == "tr"
        self.title.setText(self.i18n.t("review.title"))
        self.refresh_button.setText(self.i18n.t("review.refresh"))
        self.refresh_button.setToolTip(self.i18n.t("tip.review.refresh"))
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

    def _resource_title(self, summary: ReviewSummary) -> str:
        link = summary.resource_link
        if link.resource_type == "decision":
            try:
                decision = self.database.get_decision(int(link.resource_id))
            except (TypeError, ValueError):
                decision = None
            if decision:
                return f"{decision.decision_key} · {decision.title}"
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
        for item in files[:3]:
            lines.append(f"• {self._human_change(item.status)}: {item.path}")
        if len(files) > 3:
            lines.append((f"• ve {len(files) - 3} değişiklik daha…" if tr else f"• and {len(files) - 3} more change(s)…"))
        return "\n".join(lines)

    def _human_change(self, status: str) -> str:
        tr = self.i18n.language == "tr"
        code = (status or "M").upper()[:1]
        if tr:
            return {"A": "Yeni dosya eklendi", "M": "Dosyanın içeriği değişti", "D": "Dosya silindi", "R": "Dosyanın adı/yeri değişti", "C": "Dosya kopyalandı", "T": "Dosya türü değişti"}.get(code, "Dosya değişti")
        return {"A": "New file added", "M": "File contents changed", "D": "File deleted", "R": "File renamed or moved", "C": "File copied", "T": "File type changed"}.get(code, "File changed")

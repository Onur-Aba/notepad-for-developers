from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from app.i18n import I18n
from app.models import ReviewStatus, ReviewSummary
from app.widgets.status_badge import StatusBadge


class ReviewInboxPage(QWidget):
    refreshRequested = Signal()
    viewRequested = Signal(object)
    markReviewedRequested = Signal(object)

    def __init__(self, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
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
        self.title.setText(self.i18n.t("review.title"))
        self.refresh_button.setText(self.i18n.t("review.refresh"))
        self.refresh_button.setToolTip(self.i18n.t("tip.review.refresh"))
        self.explain.setText(
            "Bu liste bir 'hata listesi' değildir. Buradaki anlam yalnızca şudur: Bu bilgiye bağladığınız kod, bilgiyi son kontrol ettiğiniz commit'ten sonra değişti."
            if self.i18n.language == "tr" else
            "This is not an error list. It only means that code connected to this knowledge changed after the commit where you last checked it."
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

    def _update_subtitle(self) -> None:
        needs = sum(1 for x in self.summaries if x.status == ReviewStatus.NEEDS_REVIEW)
        self.subtitle.setText(self.i18n.t("review.count", count=needs))

    def _render(self) -> None:
        while self.cards.count():
            item = self.cards.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        selected_type = str(self.filter.currentData()) if self.filter.count() else "all"
        visible = [s for s in self.summaries if s.status == ReviewStatus.NEEDS_REVIEW and (selected_type == "all" or s.resource_link.resource_type == selected_type)]
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
            top = QHBoxLayout()
            label = QLabel(self._resource_title(summary))
            label.setObjectName("cardTitle")
            badge = StatusBadge(summary.status)
            top.addWidget(label)
            top.addStretch(1)
            top.addWidget(badge)
            details = QLabel(
                f"{self.i18n.t('review.checked_at')}: {(summary.baseline_sha or '—')[:10]}    "
                f"{self.i18n.t('review.current')}: {(summary.current_sha or '—')[:10]}\n"
                f"{self.i18n.t('review.since')}: {summary.commit_count} {self.i18n.t('review.commits')} · "
                f"{len(summary.linked_changed_files)} {self.i18n.t('review.files')}"
            )
            details.setObjectName("mutedText")
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
            layout.addLayout(top)
            layout.addWidget(details)
            layout.addLayout(actions)
            self.cards.addWidget(frame)
        self.cards.addStretch(1)

    def _resource_title(self, summary: ReviewSummary) -> str:
        link = summary.resource_link
        if self.i18n.language == "tr":
            kind = {"note": "Not", "decision": "Karar", "diagram_item": "Mimari"}.get(link.resource_type, link.resource_type)
        else:
            kind = {"note": "Note", "decision": "Decision", "diagram_item": "Architecture"}.get(link.resource_type, link.resource_type)
        return f"{kind} · {link.target_value or self.i18n.t('resources.repo')}"

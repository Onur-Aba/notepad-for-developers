from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.database import Database
from app.i18n import I18n


class MetricCard(QFrame):
    def __init__(self, title: str = "", value: str = "0", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("metricCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(5)
        self.title = QLabel(title)
        self.title.setObjectName("cardLabel")
        self.value = QLabel(value)
        self.value.setObjectName("metricValue")
        layout.addWidget(self.title)
        layout.addWidget(self.value)


class DashboardPage(QWidget):
    reviewRequested = Signal()
    projectRequested = Signal(int)

    def __init__(self, database: Database, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.i18n = i18n
        self._needs_review_count = 0
        self._current_count = 0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 28, 30, 24)
        outer.setSpacing(12)
        self.title = QLabel()
        self.title.setObjectName("pageTitle")
        self.subtitle = QLabel()
        self.subtitle.setWordWrap(True)
        self.subtitle.setObjectName("pageSubtitle")
        outer.addWidget(self.title)
        outer.addWidget(self.subtitle)
        outer.addSpacing(8)

        cards = QGridLayout()
        cards.setHorizontalSpacing(12)
        self.projects_card = MetricCard()
        self.review_card = MetricCard()
        self.current_card = MetricCard()
        self.repositories_card = MetricCard()
        for index, card in enumerate((self.projects_card, self.review_card, self.current_card, self.repositories_card)):
            cards.addWidget(card, 0, index)
        outer.addLayout(cards)

        self.review_panel = QFrame()
        self.review_panel.setObjectName("attentionPanel")
        review_layout = QHBoxLayout(self.review_panel)
        review_layout.setContentsMargins(16, 14, 16, 14)
        review_text = QVBoxLayout()
        self.review_section = QLabel()
        self.review_section.setObjectName("sectionTitle")
        self.review_explain = QLabel()
        self.review_explain.setObjectName("mutedText")
        self.review_explain.setWordWrap(True)
        review_text.addWidget(self.review_section)
        review_text.addWidget(self.review_explain)
        self.review_button = QPushButton()
        self.review_button.setObjectName("primaryButton")
        self.review_button.clicked.connect(self.reviewRequested)
        review_layout.addLayout(review_text, 1)
        review_layout.addWidget(self.review_button)
        outer.addWidget(self.review_panel)

        self.recent_title = QLabel()
        self.recent_title.setObjectName("sectionTitle")
        outer.addWidget(self.recent_title)
        self.project_container = QWidget()
        self.project_layout = QVBoxLayout(self.project_container)
        self.project_layout.setContentsMargins(0, 0, 0, 0)
        self.project_layout.setSpacing(9)
        outer.addWidget(self.project_container, 1)

        self.i18n.languageChanged.connect(lambda _language: self.retranslate_ui())
        self.retranslate_ui()
        self.refresh()

    def retranslate_ui(self) -> None:
        self.title.setText(self.i18n.t("dashboard.title"))
        self.subtitle.setText(self.i18n.t("dashboard.subtitle"))
        self.projects_card.title.setText(self.i18n.t("dashboard.projects"))
        self.review_card.title.setText(self.i18n.t("dashboard.needs_review"))
        self.current_card.title.setText(self.i18n.t("dashboard.current"))
        self.repositories_card.title.setText(self.i18n.t("dashboard.repositories"))
        self.review_section.setText(self.i18n.t("dashboard.review_section"))
        self.review_explain.setText(self.i18n.t("dashboard.review_explain"))
        self.review_button.setText(self.i18n.t("dashboard.open_review"))
        self.review_button.setToolTip(self.i18n.t("tip.dashboard.review"))
        self.recent_title.setText(self.i18n.t("dashboard.recent_projects"))
        self.refresh(self._needs_review_count, self._current_count)

    def refresh(self, needs_review_count: int | None = None, current_count: int | None = None) -> None:
        projects = self.database.list_project_summaries()
        repositories = self.database.list_repositories()
        if needs_review_count is not None:
            self._needs_review_count = needs_review_count
        if current_count is not None:
            self._current_count = current_count
        self.projects_card.value.setText(str(len(projects)))
        self.repositories_card.value.setText(str(len(repositories)))
        self.review_card.value.setText(str(self._needs_review_count))
        self.current_card.value.setText(str(self._current_count))
        self.review_panel.setProperty("attention", self._needs_review_count > 0)
        self.review_panel.style().unpolish(self.review_panel)
        self.review_panel.style().polish(self.review_panel)

        while self.project_layout.count():
            item = self.project_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        if not projects:
            empty = QLabel(self.i18n.t("dashboard.empty"))
            empty.setWordWrap(True)
            empty.setObjectName("emptyState")
            self.project_layout.addWidget(empty)
            self.project_layout.addStretch(1)
            return
        for project in projects[:6]:
            card = QFrame()
            card.setObjectName("projectCard")
            layout = QHBoxLayout(card)
            layout.setContentsMargins(16, 12, 14, 12)
            text = QVBoxLayout()
            name = QLabel(project.name)
            name.setObjectName("cardTitle")
            detail = QLabel(
                f"{project.repository_count} {self.i18n.t('projects.repositories')}  ·  "
                f"{project.note_count} {self.i18n.t('projects.notes')}  ·  "
                f"{project.decision_count} {self.i18n.t('projects.decisions')}"
            )
            detail.setObjectName("mutedText")
            text.addWidget(name)
            text.addWidget(detail)
            open_button = QPushButton(self.i18n.t("dashboard.open"))
            open_button.setToolTip(self.i18n.t("tip.dashboard.open_project"))
            open_button.clicked.connect(lambda _checked=False, pid=project.id: self.projectRequested.emit(pid))
            layout.addLayout(text, 1)
            layout.addWidget(open_button)
            self.project_layout.addWidget(card)
        self.project_layout.addStretch(1)

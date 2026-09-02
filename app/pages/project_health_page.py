from __future__ import annotations

from collections import Counter, defaultdict

from PySide6.QtWidgets import QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.database import Database
from app.i18n import I18n
from app.models import ReviewStatus, ReviewSummary
from app.pages.dashboard_page import MetricCard


class ProjectHealthPage(QWidget):
    def __init__(self, database: Database, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.database = database; self.i18n = i18n; self.project_id: int | None = None; self.summaries: list[ReviewSummary] = []
        root = QVBoxLayout(self); root.setContentsMargins(30,28,30,24); root.setSpacing(12)
        self.title = QLabel(); self.title.setObjectName("pageTitle"); self.subtitle = QLabel(); self.subtitle.setObjectName("pageSubtitle"); self.subtitle.setWordWrap(True)
        root.addWidget(self.title); root.addWidget(self.subtitle)
        controls = QHBoxLayout(); self.repo_filter = QComboBox(); self.repo_filter.currentIndexChanged.connect(self.refresh); controls.addWidget(self.repo_filter); controls.addStretch(1); root.addLayout(controls)
        grid = QGridLayout(); self.cards = {status: MetricCard() for status in ReviewStatus}
        for i,status in enumerate(ReviewStatus): grid.addWidget(self.cards[status],0,i)
        root.addLayout(grid)
        self.breakdown = QFrame(); self.breakdown.setObjectName("dashboardPanel"); self.breakdown_layout = QVBoxLayout(self.breakdown); root.addWidget(self.breakdown,1)
        self.i18n.languageChanged.connect(lambda _lang: self.retranslate_ui()); self.retranslate_ui()

    def set_project(self, project_id: int) -> None:
        self.project_id = project_id; self._repos(); self.refresh()

    def set_summaries(self, summaries: list[ReviewSummary]) -> None:
        self.summaries = summaries; self.refresh()

    def _repos(self) -> None:
        current = self.repo_filter.currentData(); self.repo_filter.blockSignals(True); self.repo_filter.clear()
        self.repo_filter.addItem("Tüm depolar" if self.i18n.language=="tr" else "All repositories", None)
        if self.project_id:
            for repo in self.database.list_repositories(self.project_id): self.repo_filter.addItem(repo.full_name or repo.name, repo.id)
        idx=self.repo_filter.findData(current); self.repo_filter.setCurrentIndex(max(0,idx)); self.repo_filter.blockSignals(False)

    def retranslate_ui(self) -> None:
        tr=self.i18n.language=="tr"; self.title.setText("Proje Sağlığı" if tr else "Project Health")
        self.subtitle.setText("Dokümantasyon ve review durumunun tek bakışta özeti." if tr else "A single view of documentation and review coverage.")
        names={ReviewStatus.CURRENT:("Güncel","Current"),ReviewStatus.NEEDS_REVIEW:("İncelenecek","Needs Review"),ReviewStatus.NOT_REVIEWED:("İncelenmedi","Not Reviewed"),ReviewStatus.CANNOT_COMPARE:("Karşılaştırılamıyor","Cannot Compare")}
        for status,card in self.cards.items(): card.title.setText(names[status][0 if tr else 1])
        self._repos(); self.refresh()

    def refresh(self,*_args) -> None:
        rid=self.repo_filter.currentData() if self.repo_filter.count() else None
        values=[s for s in self.summaries if s.resource_link.project_id==self.project_id and (rid is None or s.resource_link.repository_id==int(rid))]
        # Collapse multiple links belonging to the same knowledge item using the worst status.
        priority={ReviewStatus.NEEDS_REVIEW:4,ReviewStatus.CANNOT_COMPARE:3,ReviewStatus.NOT_REVIEWED:2,ReviewStatus.CURRENT:1}
        collapsed={}
        for s in values:
            key=(s.resource_link.resource_type,s.resource_link.resource_id,s.resource_link.resource_parent_id,s.resource_link.repository_id)
            if key not in collapsed or priority[s.status]>priority[collapsed[key].status]: collapsed[key]=s
        counts=Counter(s.status for s in collapsed.values())
        for status,card in self.cards.items(): card.value.setText(str(counts[status]))
        while self.breakdown_layout.count():
            item=self.breakdown_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        tr=self.i18n.language=="tr"; heading=QLabel("Alanlara göre" if tr else "By knowledge type"); heading.setObjectName("sectionTitle"); self.breakdown_layout.addWidget(heading)
        by_type=defaultdict(Counter)
        for s in collapsed.values(): by_type[s.resource_link.resource_type][s.status]+=1
        labels={"note":("Notlar","Notes"),"decision":("Kararlar","Decisions"),"diagram_item":("Mimari öğeler","Architecture nodes")}
        for kind in ("note","decision","diagram_item"):
            c=by_type[kind]; text=(f"{labels[kind][0]} — Güncel {c[ReviewStatus.CURRENT]} · İncelenecek {c[ReviewStatus.NEEDS_REVIEW]} · İncelenmedi {c[ReviewStatus.NOT_REVIEWED]} · Karşılaştırılamıyor {c[ReviewStatus.CANNOT_COMPARE]}" if tr else f"{labels[kind][1]} — Current {c[ReviewStatus.CURRENT]} · Needs Review {c[ReviewStatus.NEEDS_REVIEW]} · Not Reviewed {c[ReviewStatus.NOT_REVIEWED]} · Cannot Compare {c[ReviewStatus.CANNOT_COMPARE]}")
            label=QLabel(text); label.setWordWrap(True); label.setObjectName("mutedText"); self.breakdown_layout.addWidget(label)
        unlinked_notes = 0
        if self.project_id:
            for n in self.database.list_notes(project_id=self.project_id):
                if not self.database.list_resource_links("note", n.id): unlinked_notes += 1
        warn=QLabel((f"Kod bağlantısı olmayan {unlinked_notes} not var." if tr else f"{unlinked_notes} note(s) have no code link.")); warn.setObjectName("helperBanner"); warn.setWordWrap(True); self.breakdown_layout.addWidget(warn); self.breakdown_layout.addStretch(1)

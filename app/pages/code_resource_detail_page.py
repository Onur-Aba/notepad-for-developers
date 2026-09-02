from __future__ import annotations

import json
from collections import Counter
from datetime import datetime

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from app.database import Database
from app.i18n import I18n
from app.models import ReviewStatus, ReviewSummary


class CodeResourceDetailPage(QWidget):
    backRequested = Signal()
    knowledgeRequested = Signal(str, str, str)

    def __init__(self, database: Database, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.database = database; self.i18n = i18n
        self.project_id: int | None = None; self.repository_id: int | None = None; self.path = ""
        self._review_summaries: list[ReviewSummary] = []
        root = QVBoxLayout(self); root.setContentsMargins(30,26,30,24); root.setSpacing(12)
        top = QHBoxLayout(); self.back = QPushButton(); self.back.clicked.connect(self.backRequested); self.title=QLabel(); self.title.setObjectName("pageTitle"); top.addWidget(self.back); top.addWidget(self.title); top.addStretch(1); root.addLayout(top)
        self.subtitle=QLabel(); self.subtitle.setObjectName("pageSubtitle"); self.subtitle.setWordWrap(True); root.addWidget(self.subtitle)
        self.summary=QLabel(); self.summary.setObjectName("helperBanner"); self.summary.setWordWrap(True); root.addWidget(self.summary)
        self.container=QWidget(); self.content=QVBoxLayout(self.container); self.content.setContentsMargins(0,0,0,0); self.content.setSpacing(10)
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QScrollArea.Shape.NoFrame); scroll.setWidget(self.container); root.addWidget(scroll,1)
        self.i18n.languageChanged.connect(lambda _l:self.retranslate_ui()); self.retranslate_ui()

    def open_resource(self, project_id: int, repository_id: int, path: str) -> None:
        self.project_id=project_id; self.repository_id=repository_id; self.path=path.replace("\\","/").strip("/")
        repo=self.database.get_repository(repository_id)
        title=self.path or (repo.full_name or repo.name if repo else "Repository")
        self.title.setText(title)
        if repo:
            self.subtitle.setText(f"{repo.full_name or repo.name} · /{self.path}" if self.path else f"{repo.full_name or repo.name} · /")
        self.database.touch_recent("code", f"{repository_id}:{self.path}", title, project_id, (repo.full_name or repo.name) if repo else "")
        self.refresh()

    def set_review_summaries(self, summaries: list[ReviewSummary]) -> None:
        self._review_summaries = list(summaries)
        if self.repository_id is not None:
            self.refresh()

    def retranslate_ui(self) -> None:
        tr=self.i18n.language=="tr"; self.back.setText("← Geri" if tr else "← Back")
        if self.repository_id is None:
            self.title.setText("Kod Kaynağı" if tr else "Code Resource")
            self.subtitle.setText("Dosya, bağlı bilgi ve review geçmişi burada birlikte görünür." if tr else "Files, linked knowledge and review history appear together here.")
        else: self.refresh()

    def refresh(self) -> None:
        while self.content.count():
            item=self.content.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if self.repository_id is None: return
        tr=self.i18n.language=="tr"; links=self.database.resource_links_for_path(self.repository_id,self.path)
        counts=Counter(kind for _row,_title,kind in links)
        matching = self._matching_review_summaries(links)
        review_counts = Counter(summary.status for summary in matching)
        linked_ids = {int(row["id"]) for row, _title, _kind in links}
        summarized_ids = {summary.resource_link.id for summary in matching}
        missing = max(0, len(linked_ids - summarized_ids))
        if missing:
            review_counts[ReviewStatus.NOT_REVIEWED] += missing
        review_text = (
            f"Review: {review_counts[ReviewStatus.CURRENT]} Current · "
            f"{review_counts[ReviewStatus.NEEDS_REVIEW]} Needs Review · "
            f"{review_counts[ReviewStatus.NOT_REVIEWED]} Not Reviewed · "
            f"{review_counts[ReviewStatus.CANNOT_COMPARE]} Cannot Compare"
        )
        backlinks_text = (
            f"Backlinks: {counts['decision']} karar · {counts['note']} not · {counts['architecture']} mimari öğe"
            if tr else
            f"Backlinks: {counts['decision']} decision(s) · {counts['note']} note(s) · {counts['architecture']} architecture node(s)"
        )
        self.summary.setText(backlinks_text + "\n" + review_text)

        self._heading("Mevcut review durumu" if tr else "Current review status")
        if links:
            status_label = QLabel(review_text)
            status_label.setObjectName("mutedText")
            status_label.setWordWrap(True)
            self.content.addWidget(status_label)
        else:
            status_label = QLabel("Bağlı bilgi olmadığı için review durumu yok." if tr else "There is no review status because no knowledge item links to this path.")
            status_label.setObjectName("mutedText")
            self.content.addWidget(status_label)

        self._heading("Bu dosyayı referans alanlar" if tr else "Backlinks")
        if links:
            for row,title,kind in links:
                frame=QFrame(); frame.setObjectName("reviewCard"); lay=QHBoxLayout(frame); lay.setContentsMargins(14,10,14,10)
                label=QLabel(f"{kind.title()} · {title}"); label.setWordWrap(True); lay.addWidget(label,1)
                open_btn=QPushButton("Aç" if tr else "Open")
                open_btn.clicked.connect(lambda _c=False, r=row: self.knowledgeRequested.emit(str(r["resource_type"]),str(r["resource_id"]),str(r["resource_parent_id"] or "")))
                lay.addWidget(open_btn); self.content.addWidget(frame)
        else:
            empty=QLabel("Bu dosyaya bağlı karar/not/mimari öğesi yok." if tr else "No decision, note or architecture node links to this path."); empty.setObjectName("emptyInlineState"); self.content.addWidget(empty)

        self._heading("Review geçmişi" if tr else "Review history")
        histories=[]
        seen=set()
        for row,_title,_kind in links:
            key=(str(row["resource_type"]),str(row["resource_id"]),str(row["resource_parent_id"] or ""))
            if key in seen: continue
            seen.add(key)
            histories.extend(self.database.list_review_history(*key, limit=20))
        histories.sort(key=lambda r:str(r["reviewed_at"]), reverse=True)
        if histories:
            for h in histories[:30]:
                label=QLabel(f"{self._date(str(h['reviewed_at']))}  →  {str(h['baseline_sha'])[:12]} · {h['repository_name']}"); label.setObjectName("mutedText"); self.content.addWidget(label)
        else:
            label=QLabel("Henüz review kaydı yok." if tr else "No review history yet."); label.setObjectName("mutedText"); self.content.addWidget(label)

        self._heading("Son commitler" if tr else "Recent commits")
        commits=self._recent_commits()
        if commits:
            for commit in commits[:25]:
                label=QLabel(f"{commit.get('sha','')[:8]} · {commit.get('message','')}\n{commit.get('author') or ''} {self._date(str(commit.get('authored_at') or ''))}".strip()); label.setObjectName("mutedText"); label.setWordWrap(True); self.content.addWidget(label)
        else:
            label=QLabel("Bu yol için cache'lenmiş commit bulunamadı." if tr else "No cached commits were found for this path."); label.setObjectName("mutedText"); self.content.addWidget(label)
        self.content.addStretch(1)

    def _matching_review_summaries(self, links) -> list[ReviewSummary]:
        link_ids = {int(row["id"]) for row, _title, _kind in links}
        return [
            summary for summary in self._review_summaries
            if summary.resource_link.id in link_ids
            and summary.resource_link.repository_id == self.repository_id
        ]

    def _recent_commits(self) -> list[dict[str,object]]:
        rows=self.database.connection.execute("SELECT changed_files_json,commits_json,detected_at FROM repository_changes WHERE repository_id=? ORDER BY detected_at DESC LIMIT 100",(self.repository_id,)).fetchall()
        result=[]; seen=set(); path=self.path
        for row in rows:
            try: files=json.loads(str(row["changed_files_json"] or "[]")); commits=json.loads(str(row["commits_json"] or "[]"))
            except json.JSONDecodeError: continue
            relevant=not path
            for f in files if isinstance(files,list) else []:
                p=str((f or {}).get("path") or "").replace("\\","/").strip("/") if isinstance(f,dict) else ""
                if p==path or (path and p.startswith(path+"/")): relevant=True; break
            if not relevant: continue
            for c in commits if isinstance(commits,list) else []:
                if not isinstance(c,dict): continue
                sha=str(c.get("sha") or "")
                if sha and sha not in seen: seen.add(sha); result.append(c)
        return result

    def _heading(self,text:str)->None:
        label=QLabel(text); label.setObjectName("sectionTitle"); self.content.addWidget(label)

    @staticmethod
    def _date(value:str)->str:
        if not value: return ""
        try: return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone().strftime("%Y-%m-%d %H:%M")
        except ValueError: return value

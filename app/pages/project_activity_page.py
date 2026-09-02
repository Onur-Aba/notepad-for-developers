from __future__ import annotations

import json
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QMessageBox, QScrollArea, QVBoxLayout, QWidget

from app.database import Database
from app.i18n import I18n


class ActivityCard(QFrame):
    """A timeline card that exposes a lightweight click affordance."""

    clicked = Signal(object)

    def __init__(self, payload, parent=None) -> None:
        super().__init__(parent)
        self.payload = payload
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt API
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.payload)
        super().mouseReleaseEvent(event)


class ProjectActivityPage(QWidget):
    def __init__(self, database: Database, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.i18n = i18n
        self.project_id: int | None = None
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 28, 30, 24)
        root.setSpacing(12)
        self.title = QLabel(); self.title.setObjectName("pageTitle")
        self.subtitle = QLabel(); self.subtitle.setObjectName("pageSubtitle"); self.subtitle.setWordWrap(True)
        root.addWidget(self.title); root.addWidget(self.subtitle)
        controls = QHBoxLayout()
        self.repo_filter = QComboBox(); self.repo_filter.currentIndexChanged.connect(self.refresh)
        self.period = QComboBox(); self.period.currentIndexChanged.connect(self.refresh)
        controls.addWidget(self.repo_filter); controls.addWidget(self.period); controls.addStretch(1)
        root.addLayout(controls)
        self.container = QWidget(); self.cards = QVBoxLayout(self.container); self.cards.setContentsMargins(0,0,0,0); self.cards.setSpacing(8)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QScrollArea.Shape.NoFrame); scroll.setWidget(self.container)
        root.addWidget(scroll, 1)
        self.i18n.languageChanged.connect(lambda _lang: self.retranslate_ui())
        self.retranslate_ui()

    def set_project(self, project_id: int) -> None:
        self.project_id = project_id
        self._rebuild_repositories()
        self.refresh()

    def _rebuild_repositories(self) -> None:
        current = self.repo_filter.currentData()
        self.repo_filter.blockSignals(True); self.repo_filter.clear()
        self.repo_filter.addItem("Tüm depolar" if self.i18n.language == "tr" else "All repositories", None)
        if self.project_id is not None:
            for repo in self.database.list_repositories(self.project_id):
                self.repo_filter.addItem(repo.full_name or repo.name, repo.id)
        idx = self.repo_filter.findData(current); self.repo_filter.setCurrentIndex(max(0, idx)); self.repo_filter.blockSignals(False)

    def retranslate_ui(self) -> None:
        tr = self.i18n.language == "tr"
        self.title.setText("Proje Aktivite Zaman Çizelgesi" if tr else "Project Activity Timeline")
        self.subtitle.setText(
            "Commit, karar, not, review ve repository bağlantılarını tek kronolojik akışta görün. Bir kayda tıklayarak ayrıntısını açabilirsiniz."
            if tr else "See commits, decisions, notes, reviews and repository connections in one chronological stream. Click an entry to view details."
        )
        current_days = self.period.currentData() if self.period.count() else 14
        self.period.blockSignals(True); self.period.clear()
        for days, tr_label, en_label in ((14,"Son 2 hafta","Last 2 weeks"),(30,"Son 30 gün","Last 30 days"),(90,"Son 90 gün","Last 90 days"),(0,"Tüm geçmiş","All time")):
            self.period.addItem(tr_label if tr else en_label, days)
        idx = self.period.findData(current_days); self.period.setCurrentIndex(max(0, idx)); self.period.blockSignals(False)
        self._rebuild_repositories(); self.refresh()

    def refresh(self, *_args) -> None:
        while self.cards.count():
            item = self.cards.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if self.project_id is None:
            return
        rid = self.repo_filter.currentData() if self.repo_filter.count() else None
        days = int(self.period.currentData() or 0)
        rows = self.database.list_activity(self.project_id, limit=500, repository_id=int(rid) if rid is not None else None, days=days or None)
        tr = self.i18n.language == "tr"
        if not rows:
            empty = QLabel("Bu filtrelerde aktivite yok." if tr else "No activity matches these filters.")
            empty.setObjectName("emptyState"); self.cards.addWidget(empty); self.cards.addStretch(1); return
        for row in rows:
            frame = ActivityCard(row); frame.setObjectName("reviewCard")
            frame.setToolTip("Detayları görmek için tıklayın" if tr else "Click to view details")
            frame.clicked.connect(self._show_event_details)
            lay = QVBoxLayout(frame); lay.setContentsMargins(14,10,14,10); lay.setSpacing(4)
            key = str(row["event_type"])
            top = QHBoxLayout(); kind = QLabel(self._event_label(key)); kind.setObjectName("cardLabel"); kind.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            date = QLabel(self._date(str(row["created_at"]))); date.setObjectName("mutedText"); date.setAlignment(Qt.AlignmentFlag.AlignRight); date.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            top.addWidget(kind); top.addStretch(1); top.addWidget(date); lay.addLayout(top)
            title = QLabel(self._event_title(row)); title.setObjectName("cardTitle"); title.setWordWrap(True); title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True); lay.addWidget(title)
            detail = self._event_detail(row)
            if detail:
                d = QLabel(detail); d.setObjectName("activityDetailText"); d.setWordWrap(True); d.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True); lay.addWidget(d)
            self.cards.addWidget(frame)
        self.cards.addStretch(1)

    def _event_label(self, key: str) -> str:
        tr = self.i18n.language == "tr"
        labels = {
            "project_created": ("Proje oluşturuldu","Project created"), "note_created": ("Not oluşturuldu","Note created"),
            "note_updated": ("Not güncellendi","Note updated"), "decision_created": ("Karar oluşturuldu","Decision created"),
            "decision_title_changed": ("Karar başlığı değişti","Decision title changed"), "decision_status_changed": ("Karar durumu değişti","Decision status changed"),
            "decision_content_updated": ("Karar güncellendi","Decision updated"), "code_linked": ("Kod bağlandı","Code linked"),
            "code_unlinked": ("Kod bağlantısı kaldırıldı","Code unlinked"), "marked_reviewed": ("Review yapıldı","Reviewed"),
            "repository_linked": ("Repo bağlandı","Repository linked"), "repository_unlinked": ("Repo ayrıldı","Repository unlinked"),
            "commits_detected": ("Yeni commitler","New commits"), "repository_access_changed": ("Repo erişimi değişti","Repository access changed"),
            "project_imported": ("Proje içe aktarıldı","Project imported"), "project_updated": ("Proje güncellendi", "Project updated"),
            "architecture_updated": ("Mimari güncellendi", "Architecture updated"), "decision_deleted": ("Karar silindi", "Decision deleted"),
        }
        pair = labels.get(key, (key.replace("_"," ").title(), key.replace("_"," ").title()))
        return pair[0 if tr else 1]

    def _event_title(self, row) -> str:
        key = str(row["event_type"])
        if key == "marked_reviewed":
            label = self._resource_name(row)
            if label:
                return label
            return "Review" if self.i18n.language == "tr" else "Review"
        return str(row["title"] or self._event_label(key))

    def _event_detail(self, row) -> str:
        detail = str(row["detail"] or "").strip()
        if str(row["event_type"]) != "repository_access_changed":
            return detail
        state = detail.casefold()
        tr = self.i18n.language == "tr"
        if state == "unavailable":
            return (
                "GitHub erişimi şu anda doğrulanamıyor. Yerel depo bağlıysa yerel çalışma devam eder."
                if tr else "GitHub access cannot be verified right now. Local work remains available when a local repository is connected."
            )
        if state in {"unknown", "unchecked"}:
            return "GitHub erişimi henüz doğrulanmadı." if tr else "GitHub access has not been verified yet."
        if state == "local_only":
            return "Bu depo yalnızca yerel klasör üzerinden kullanılıyor." if tr else "This repository is being used through a local folder only."
        if state == "available":
            return "GitHub erişimi kullanılabilir." if tr else "GitHub access is available."
        return (f"GitHub erişim durumu: {detail}" if tr else f"GitHub access state: {detail}") if detail else ""

    def _resource_name(self, row) -> str:
        kind = str(row["resource_type"] or "")
        rid = str(row["resource_id"] or "")
        if not rid:
            return ""
        try:
            if kind == "note":
                note = self.database.get_note(int(rid), include_deleted=True)
                return note.title if note else f"Not #{rid}"
            if kind == "decision":
                decision = self.database.get_decision(int(rid))
                return f"{decision.decision_key} · {decision.title}" if decision else f"Karar #{rid}"
            if kind == "diagram_item":
                return (f"Mimari öğe · {rid}" if self.i18n.language == "tr" else f"Architecture item · {rid}")
        except (TypeError, ValueError):
            pass
        return rid

    def _show_event_details(self, row) -> None:
        tr = self.i18n.language == "tr"
        key = str(row["event_type"])
        try:
            metadata = json.loads(str(row["metadata_json"] or "{}"))
        except (json.JSONDecodeError, TypeError):
            metadata = {}
        if not isinstance(metadata, dict):
            metadata = {}

        lines: list[str] = []
        lines.append(("İşlem: " if tr else "Event: ") + self._event_label(key))
        lines.append(("Zaman: " if tr else "Time: ") + self._date(str(row["created_at"])))

        resource = self._resource_name(row)
        if resource:
            lines.append(("Öğe: " if tr else "Item: ") + resource)
        resource_type = str(row["resource_type"] or "")
        if resource_type:
            type_names = {
                "note": ("Not", "Note"), "decision": ("Karar", "Decision"),
                "diagram_item": ("Mimari öğe", "Architecture item"), "project": ("Proje", "Project"),
            }
            pair = type_names.get(resource_type, (resource_type, resource_type))
            lines.append(("Tür: " if tr else "Type: ") + pair[0 if tr else 1])

        repository_id = row["repository_id"]
        if repository_id is not None:
            repo = self.database.get_repository(int(repository_id))
            if repo:
                lines.append("Repository: " + (repo.full_name or repo.name))

        sha = str(metadata.get("sha") or "")
        branch = str(metadata.get("branch") or "")
        if sha:
            lines.append(("Commit: " if tr else "Commit: ") + sha)
        if branch:
            lines.append(("Branch: " if tr else "Branch: ") + branch)

        detail = self._event_detail(row)
        if detail:
            lines.append(("Açıklama: " if tr else "Details: ") + detail)

        # Surface useful metadata without dumping internal JSON keys that are
        # already represented above.
        extras = []
        for meta_key, value in metadata.items():
            if meta_key in {"sha", "branch"} or value in (None, "", [], {}):
                continue
            extras.append(f"{meta_key}: {value}")
        if extras:
            lines.append(("Ek bilgi: " if tr else "Additional info: ") + " · ".join(extras))

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Information)
        box.setWindowTitle("Aktivite Detayı" if tr else "Activity Details")
        box.setText(self._event_title(row))
        box.setInformativeText("\n".join(lines))
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.exec()

    @staticmethod
    def _date(value: str) -> str:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return value

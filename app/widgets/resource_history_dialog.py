from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QListWidget, QTabWidget, QVBoxLayout, QWidget

from app.database import Database
from app.i18n import I18n


class ResourceHistoryDialog(QDialog):
    def __init__(self, database: Database, resource_type: str, resource_id: str | int,
                 resource_parent_id: str | int | None, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.i18n = i18n
        tr = i18n.language == "tr"
        self.setWindowTitle("Geçmiş" if tr else "History")
        self.resize(760, 560)
        root = QVBoxLayout(self)
        title, _kind = database.describe_resource(resource_type, str(resource_id), "" if resource_parent_id is None else str(resource_parent_id))
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        root.addWidget(heading)
        tabs = QTabWidget()
        root.addWidget(tabs, 1)

        review_list = QListWidget()
        reviews = database.list_review_history(resource_type, resource_id, resource_parent_id)
        for row in reviews:
            date = self._date(str(row["reviewed_at"]))
            review_list.addItem(f"{date}  →  {str(row['baseline_sha'])[:12]}\n{row['repository_name']} · {row['branch'] or '—'}")
        if not reviews:
            review_list.addItem("Henüz review geçmişi yok." if tr else "No review history yet.")
        tabs.addTab(review_list, "Review geçmişi" if tr else "Review history")

        if resource_type == "decision":
            decision_list = QListWidget()
            history = database.list_decision_history(int(resource_id))
            for row in history:
                detail = str(row["detail"] or "")
                decision_list.addItem(f"{self._date(str(row['created_at']))} · {row['title']}\n{detail}".rstrip())
            if not history:
                decision_list.addItem("Henüz karar geçmişi yok." if tr else "No decision history yet.")
            tabs.insertTab(0, decision_list, "Karar zaman çizelgesi" if tr else "Decision timeline")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText("Kapat" if tr else "Close")
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    @staticmethod
    def _date(value: str) -> str:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return value

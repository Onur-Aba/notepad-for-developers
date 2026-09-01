from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QDialog, QLabel, QListWidget, QListWidgetItem, QVBoxLayout

from app.database import Database
from app.i18n import I18n


class GlobalSearchDialog(QDialog):
    resultActivated = Signal(str, int)

    def __init__(self, database: Database, query: str, i18n: I18n | None = None, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.i18n = i18n
        tr = bool(i18n and i18n.language == "tr")
        self.setWindowTitle((f"DevNest'te Ara — {query}" if tr else f"Search DevNest — {query}"))
        self.resize(720, 520)
        root = QVBoxLayout(self)
        heading = QLabel((f'“{query}” için sonuçlar' if tr else f'Results for “{query}”'))
        heading.setObjectName("sectionTitle")
        root.addWidget(heading)
        helper = QLabel(
            "Bir sonucu çift tıklayın. DevNest sizi doğru projeye ve ilgili not/karar sayfasına götürür."
            if tr else
            "Double-click a result. DevNest will switch to the correct project and open the matching note or decision."
        )
        helper.setWordWrap(True)
        helper.setObjectName("helperBanner")
        root.addWidget(helper)
        self.list = QListWidget()
        root.addWidget(self.list, 1)
        kind_labels = ({"project": "Proje", "note": "Not", "decision": "Karar"} if tr else {"project": "Project", "note": "Note", "decision": "Decision"})
        for kind, item_id, title, preview in database.global_search(query):
            item = QListWidgetItem(f"{kind_labels.get(kind, kind.title())} · {title}\n{preview}")
            item.setData(Qt.ItemDataRole.UserRole, (kind, item_id))
            self.list.addItem(item)
        if self.list.count() == 0:
            self.list.addItem("Eşleşen proje, not veya karar bulunamadı." if tr else "No matching projects, notes or decisions.")
        self.list.itemDoubleClicked.connect(self._activate)

    def _activate(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(data, tuple) and len(data) == 2:
            self.resultActivated.emit(str(data[0]), int(data[1]))
            self.accept()

from __future__ import annotations

from collections import defaultdict

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QDialog, QLabel, QTreeWidget, QTreeWidgetItem, QVBoxLayout

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
        self.resize(820, 600)
        root = QVBoxLayout(self)
        heading = QLabel((f'“{query}” için sonuçlar' if tr else f'Results for “{query}”'))
        heading.setObjectName("sectionTitle")
        root.addWidget(heading)
        helper = QLabel(
            "Başlık, içerik, etiket, DEC ID, repository, dosya yolu ve commit mesajları aranır. Sonuçlar kategoriye göre gruplanır."
            if tr else
            "Searches titles, content, tags, DEC IDs, repositories, file paths and commit messages. Results are grouped by category."
        )
        helper.setWordWrap(True); helper.setObjectName("helperBanner"); root.addWidget(helper)
        self.tree = QTreeWidget(); self.tree.setHeaderHidden(True); root.addWidget(self.tree, 1)
        labels_tr = {"project":"Projeler","note":"Notlar","decision":"Kararlar","repository":"Repository'ler","code":"Kod / Dosya Yolları","commit":"Commit Mesajları"}
        labels_en = {"project":"Projects","note":"Notes","decision":"Decisions","repository":"Repositories","code":"Code / File Paths","commit":"Commit Messages"}
        grouped: dict[str, list[tuple[int,str,str]]] = defaultdict(list)
        for kind, item_id, title, preview in database.global_search(query):
            grouped[kind].append((item_id, title, preview))
        order = ("project","note","decision","repository","code","commit")
        for kind in order:
            rows = grouped.get(kind, [])
            if not rows:
                continue
            parent_item = QTreeWidgetItem([f"{(labels_tr if tr else labels_en).get(kind, kind.title())} ({len(rows)})"])
            parent_item.setFlags(parent_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.tree.addTopLevelItem(parent_item)
            for item_id, title, preview in rows:
                child = QTreeWidgetItem([f"{title}\n{preview}".rstrip()])
                child.setData(0, Qt.ItemDataRole.UserRole, (kind, item_id))
                parent_item.addChild(child)
            parent_item.setExpanded(True)
        if self.tree.topLevelItemCount() == 0:
            self.tree.addTopLevelItem(QTreeWidgetItem(["Eşleşen sonuç bulunamadı." if tr else "No matching results."]))
        self.tree.itemDoubleClicked.connect(self._activate)
        self.tree.itemActivated.connect(self._activate)

    def _activate(self, item: QTreeWidgetItem, _column: int = 0) -> None:
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, tuple) and len(data) == 2:
            self.resultActivated.emit(str(data[0]), int(data[1]))
            self.accept()

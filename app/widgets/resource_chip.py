from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QPushButton

from app.i18n import I18n
from app.models import ResourceLink


_ICONS = {
    "repository": "◫",
    "directory": "📁",
    "file": "📄",
    "branch": "⑂",
    "commit": "◉",
    "pull_request": "#",
}


class ResourceChip(QPushButton):
    openRequested = Signal(int)
    unlinkRequested = Signal(int)

    def __init__(self, link: ResourceLink, i18n: I18n | None = None, parent=None) -> None:
        self.i18n = i18n
        tr = bool(i18n and i18n.language == "tr")
        label = link.target_value or ("Tüm depo" if tr else "Repository")
        super().__init__(f"{_ICONS.get(link.target_type, '•')} {label}", parent)
        self.link = link
        self.setObjectName("resourceChip")
        self.setToolTip(
            "Bu etiket, notun hangi kodla ilgili olduğunu gösterir. Sağ tıklarsanız bağlantıyı DevNest'ten kaldırabilirsiniz; kaynak kod silinmez."
            if tr else
            "This label shows which code the note is connected to. Right-click to remove only the DevNest link; the source code is never deleted."
        )
        self.clicked.connect(lambda: self.openRequested.emit(self.link.id))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)

    def _menu(self, pos) -> None:
        from PySide6.QtWidgets import QMenu
        tr = bool(self.i18n and self.i18n.language == "tr")
        menu = QMenu(self)
        open_action = menu.addAction("Bağlı kaynağı aç" if tr else "Open linked resource")
        unlink = menu.addAction("DevNest bağlantısını kaldır" if tr else "Unlink from DevNest")
        chosen = menu.exec(self.mapToGlobal(pos))
        if chosen == open_action:
            self.openRequested.emit(self.link.id)
        elif chosen == unlink:
            self.unlinkRequested.emit(self.link.id)

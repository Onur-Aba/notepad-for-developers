from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QTableWidget, QTableWidgetItem, QVBoxLayout

from app.constants import SHORTCUTS
from app.i18n import I18n


class ShortcutsDialog(QDialog):
    def __init__(self, i18n: I18n | None = None, parent=None) -> None:
        super().__init__(parent)
        tr = bool(i18n and i18n.language == "tr")
        self.setWindowTitle("Klavye Kısayolları" if tr else "Keyboard Shortcuts")
        self.resize(520, 430)
        root = QVBoxLayout(self)
        table = QTableWidget(len(SHORTCUTS), 2)
        table.setHorizontalHeaderLabels(["İşlem" if tr else "Action", "Kısayol" if tr else "Shortcut"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        translated = {
            "New Note": "Yeni Not",
            "Export TXT": "TXT Dışa Aktar",
            "Find in Note": "Notta Bul",
            "Checkbox": "Onay Kutusu",
            "Toggle Sidebar": "Not Panelini Aç/Kapat",
            "Editor Tab": "Yazı Sekmesi",
            "Diagram Tab": "Diyagram Sekmesi",
        }
        for row, (name, shortcut) in enumerate(SHORTCUTS.items()):
            table.setItem(row, 0, QTableWidgetItem(translated.get(name, name) if tr else name))
            table.setItem(row, 1, QTableWidgetItem(shortcut))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText("Kapat" if tr else "Close")
        buttons.rejected.connect(self.reject)
        buttons.clicked.connect(lambda _button: self.accept())
        root.addWidget(table)
        root.addWidget(buttons)

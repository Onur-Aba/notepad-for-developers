from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QTableWidget, QTableWidgetItem, QVBoxLayout

from app.constants import SHORTCUTS


class ShortcutsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.resize(480, 430)
        root = QVBoxLayout(self)
        table = QTableWidget(len(SHORTCUTS), 2)
        table.setHorizontalHeaderLabels(["Action", "Shortcut"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, (name, shortcut) in enumerate(SHORTCUTS.items()):
            table.setItem(row, 0, QTableWidgetItem(name))
            table.setItem(row, 1, QTableWidgetItem(shortcut))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.clicked.connect(lambda _button: self.accept())
        root.addWidget(table)
        root.addWidget(buttons)

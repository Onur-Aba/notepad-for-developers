from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout

from app.i18n import I18n


class CommandPaletteDialog(QDialog):
    commandActivated = Signal(str)

    def __init__(self, commands: list[tuple[str, str, str]], i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.commands = commands; self.i18n = i18n
        self.setWindowTitle("Komut Paleti" if i18n.language == "tr" else "Command Palette")
        self.resize(620, 440)
        root = QVBoxLayout(self)
        hint = QLabel("Komut yazın ve Enter'a basın." if i18n.language == "tr" else "Type a command and press Enter.")
        hint.setObjectName("mutedText"); root.addWidget(hint)
        self.search = QLineEdit(); self.search.setPlaceholderText("Komut ara…" if i18n.language == "tr" else "Search commands…"); root.addWidget(self.search)
        self.list = QListWidget(); root.addWidget(self.list, 1)
        self.search.textChanged.connect(self._render); self.search.returnPressed.connect(self._activate_current)
        self.list.itemDoubleClicked.connect(lambda item:self._activate(item)); self.list.itemActivated.connect(self._activate)
        self._render(); self.search.setFocus()

    def _render(self) -> None:
        q=self.search.text().strip().casefold(); self.list.clear()
        for command_id,label,shortcut in self.commands:
            if q and q not in label.casefold() and q not in command_id.casefold(): continue
            text=f"{label}\n{shortcut}" if shortcut else label
            item=QListWidgetItem(text); item.setData(Qt.ItemDataRole.UserRole,command_id); self.list.addItem(item)
        if self.list.count(): self.list.setCurrentRow(0)

    def _activate_current(self) -> None:
        item=self.list.currentItem()
        if item: self._activate(item)

    def _activate(self,item:QListWidgetItem) -> None:
        command_id=str(item.data(Qt.ItemDataRole.UserRole)); self.commandActivated.emit(command_id); self.accept()

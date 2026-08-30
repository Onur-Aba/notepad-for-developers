from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models import NoteSummary


class NoteCard(QWidget):
    def __init__(self, note: NoteSummary, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(7, 5, 7, 5)
        layout.setSpacing(2)
        title = QLabel(note.title)
        title.setStyleSheet("font-weight: 600;")
        preview = QLabel(note.preview or "No content")
        preview.setWordWrap(False)
        preview.setStyleSheet("font-size: 11px;")
        date = QLabel(self._format_date(note.updated_at))
        date.setStyleSheet("font-size: 10px;")
        layout.addWidget(title)
        layout.addWidget(preview)
        layout.addWidget(date)

    @staticmethod
    def _format_date(value: str) -> str:
        try:
            dt = datetime.fromisoformat(value)
            return dt.astimezone().strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return value


class Sidebar(QWidget):
    noteSelected = Signal(int)
    newNoteRequested = Signal()
    trashRequested = Signal()
    renameRequested = Signal(int)
    duplicateRequested = Signal(int)
    deleteRequested = Signal(int)
    exportRequested = Signal(int)
    searchChanged = Signal(str)
    sortChanged = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(210)
        self.setMaximumWidth(520)
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(7)

        top = QHBoxLayout()
        label = QLabel("Notes")
        label.setStyleSheet("font-size: 15px; font-weight: 700;")
        new_button = QPushButton("+")
        new_button.setToolTip("New Note (Ctrl+N)")
        new_button.setFixedWidth(34)
        new_button.clicked.connect(self.newNoteRequested)
        top.addWidget(label)
        top.addStretch(1)
        top.addWidget(new_button)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search notes…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.searchChanged)

        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Recently edited", "updated")
        self.sort_combo.addItem("Alphabetical", "title")
        self.sort_combo.currentIndexChanged.connect(
            lambda _index: self.sortChanged.emit(str(self.sort_combo.currentData()))
        )

        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._show_context_menu)
        self.list.currentItemChanged.connect(self._on_current_changed)

        trash = QPushButton("Trash")
        trash.setToolTip("Restore or permanently delete notes")
        trash.clicked.connect(self.trashRequested)

        root.addLayout(top)
        root.addWidget(self.search)
        root.addWidget(self.sort_combo)
        root.addWidget(self.list, 1)
        root.addWidget(trash)

    def set_notes(self, notes: list[NoteSummary], selected_id: int | None = None) -> None:
        self.list.blockSignals(True)
        self.list.clear()
        selected_item: QListWidgetItem | None = None
        for note in notes:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, note.id)
            card = NoteCard(note)
            item.setSizeHint(card.sizeHint())
            self.list.addItem(item)
            self.list.setItemWidget(item, card)
            if note.id == selected_id:
                selected_item = item
        if selected_item is not None:
            self.list.setCurrentItem(selected_item)
        self.list.blockSignals(False)

    def select_note(self, note_id: int) -> None:
        for index in range(self.list.count()):
            item = self.list.item(index)
            if int(item.data(Qt.ItemDataRole.UserRole)) == note_id:
                self.list.setCurrentItem(item)
                self.list.scrollToItem(item)
                return

    def _on_current_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is not None:
            self.noteSelected.emit(int(current.data(Qt.ItemDataRole.UserRole)))

    def _show_context_menu(self, pos) -> None:
        item = self.list.itemAt(pos)
        if item is None:
            return
        note_id = int(item.data(Qt.ItemDataRole.UserRole))
        menu = QMenu(self)
        rename = menu.addAction("Rename")
        duplicate = menu.addAction("Duplicate")
        export = menu.addAction("Export TXT")
        menu.addSeparator()
        delete = menu.addAction("Delete to Trash")
        chosen = menu.exec(self.list.mapToGlobal(pos))
        if chosen == rename:
            self.renameRequested.emit(note_id)
        elif chosen == duplicate:
            self.duplicateRequested.emit(note_id)
        elif chosen == export:
            self.exportRequested.emit(note_id)
        elif chosen == delete:
            self.deleteRequested.emit(note_id)

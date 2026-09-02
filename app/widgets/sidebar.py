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

from app.i18n import I18n
from app.models import NoteSummary


class NoteCard(QWidget):
    def __init__(self, note: NoteSummary, no_content: str = "No content", parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(9, 8, 9, 8)
        layout.setSpacing(4)
        self.setMinimumHeight(72)
        title = QLabel(note.title)
        title.setObjectName("noteCardTitle")
        title.setMinimumHeight(18)
        preview = QLabel(note.preview or no_content)
        preview.setWordWrap(False)
        preview.setObjectName("noteCardPreview")
        preview.setMinimumHeight(16)
        date = QLabel(self._format_date(note.updated_at))
        date.setObjectName("noteCardDate")
        date.setMinimumHeight(15)
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
    noteSelectionCleared = Signal()
    newNoteRequested = Signal()
    trashRequested = Signal()
    renameRequested = Signal(int)
    duplicateRequested = Signal(int)
    deleteRequested = Signal(int)
    exportRequested = Signal(int)
    searchChanged = Signal(str)
    sortChanged = Signal(str)

    def __init__(self, i18n: I18n | None = None, parent=None) -> None:
        super().__init__(parent)
        self.i18n = i18n
        self._notes: list[NoteSummary] = []
        self._selected_id: int | None = None
        self.setObjectName("noteSidebar")
        self.setMinimumWidth(240)
        self.setMaximumWidth(520)
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(9)

        top = QHBoxLayout()
        self.label = QLabel("Notes")
        self.label.setObjectName("secondaryPanelTitle")
        self.new_button = QPushButton("+")
        self.new_button.setObjectName("iconActionButton")
        self.new_button.setFixedWidth(38)
        self.new_button.clicked.connect(self.newNoteRequested)
        top.addWidget(self.label)
        top.addStretch(1)
        top.addWidget(self.new_button)

        self.search = QLineEdit()
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.searchChanged)

        self.sort_combo = QComboBox()
        self.sort_combo.currentIndexChanged.connect(
            lambda _index: self.sortChanged.emit(str(self.sort_combo.currentData()))
        )

        self.list = QListWidget()
        self.list.setObjectName("noteList")
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._show_context_menu)
        self.list.currentItemChanged.connect(self._on_current_changed)

        self.trash = QPushButton()
        self.trash.clicked.connect(self.trashRequested)

        root.addLayout(top)
        root.addWidget(self.search)
        root.addWidget(self.sort_combo)
        root.addWidget(self.list, 1)
        root.addWidget(self.trash)
        if self.i18n:
            self.i18n.languageChanged.connect(lambda _language: self.retranslate_ui())
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        tr = self.i18n.t if self.i18n else lambda key, **_kw: {
            "nav.notes": "Notes", "top.search": "Search notes…",
        }.get(key, key)
        self.label.setText(tr("nav.notes"))
        self.search.setPlaceholderText("Notlarda ara…" if self.i18n and self.i18n.language == "tr" else "Search notes…")
        self.new_button.setToolTip(
            "Yeni bir boş not oluşturur. Not otomatik kaydedilir; daha sonra koda bağlayabilirsiniz."
            if self.i18n and self.i18n.language == "tr"
            else "Create a new blank note. It saves automatically and can be connected to code later."
        )
        current_data = self.sort_combo.currentData()
        self.sort_combo.blockSignals(True)
        self.sort_combo.clear()
        if self.i18n and self.i18n.language == "tr":
            self.sort_combo.addItem("En son düzenlenen", "updated")
            self.sort_combo.addItem("Alfabetik", "title")
            self.trash.setText("Çöp Kutusu")
            self.trash.setToolTip("Silinen notları geri yüklemek veya kalıcı olarak silmek için açın.")
        else:
            self.sort_combo.addItem("Recently edited", "updated")
            self.sort_combo.addItem("Alphabetical", "title")
            self.trash.setText("Trash")
            self.trash.setToolTip("Open deleted notes so you can restore them or remove them permanently.")
        index = self.sort_combo.findData(current_data)
        self.sort_combo.setCurrentIndex(max(0, index))
        self.sort_combo.blockSignals(False)
        if self._notes:
            self.set_notes(self._notes, self._selected_id)

    def set_notes(self, notes: list[NoteSummary], selected_id: int | None = None) -> None:
        self._notes = list(notes)
        self._selected_id = selected_id
        self.list.blockSignals(True)
        self.list.clear()
        selected_item: QListWidgetItem | None = None
        no_content = "İçerik yok" if self.i18n and self.i18n.language == "tr" else "No content"
        for note in notes:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, note.id)
            card = NoteCard(note, no_content)
            hint = card.sizeHint()
            # QListWidget item padding is outside the embedded card's sizeHint.
            # Reserve explicit vertical room so the preview/date are never clipped.
            hint.setHeight(max(82, hint.height() + 10))
            item.setSizeHint(hint)
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
                self._selected_id = note_id
                return

    def _on_current_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is not None:
            note_id = int(current.data(Qt.ItemDataRole.UserRole))
            self._selected_id = note_id
            self.noteSelected.emit(note_id)
            return
        self._selected_id = None
        self.noteSelectionCleared.emit()

    def _show_context_menu(self, pos) -> None:
        item = self.list.itemAt(pos)
        if item is None:
            return
        note_id = int(item.data(Qt.ItemDataRole.UserRole))
        menu = QMenu(self)
        tr_mode = bool(self.i18n and self.i18n.language == "tr")
        rename = menu.addAction("Yeniden adlandır" if tr_mode else "Rename")
        duplicate = menu.addAction("Kopyasını oluştur" if tr_mode else "Duplicate")
        export = menu.addAction("TXT dışa aktar" if tr_mode else "Export TXT")
        menu.addSeparator()
        delete = menu.addAction("Çöp kutusuna taşı" if tr_mode else "Delete to Trash")
        chosen = menu.exec(self.list.mapToGlobal(pos))
        if chosen == rename:
            self.renameRequested.emit(note_id)
        elif chosen == duplicate:
            self.duplicateRequested.emit(note_id)
        elif chosen == export:
            self.exportRequested.emit(note_id)
        elif chosen == delete:
            self.deleteRequested.emit(note_id)

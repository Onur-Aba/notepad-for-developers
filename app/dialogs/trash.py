from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.database import Database, DatabaseError
from app.i18n import I18n


class TrashDialog(QDialog):
    def __init__(self, database: Database, i18n: I18n | None = None, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.i18n = i18n
        self.changed = False
        tr = self._tr
        self.setWindowTitle("Çöp Kutusu" if tr else "Trash")
        self.resize(760, 430)
        root = QVBoxLayout(self)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Başlık", "Silinme / güncellenme", "Önizleme"] if tr else ["Title", "Deleted / updated", "Preview"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        row = QHBoxLayout()
        restore = QPushButton("Geri Yükle" if tr else "Restore")
        permanent = QPushButton("Kalıcı Olarak Sil" if tr else "Permanently Delete")
        empty = QPushButton("Çöp Kutusunu Boşalt" if tr else "Empty Trash")
        optimize = QPushButton("Veritabanını Küçült" if tr else "Optimize Database")
        close = QPushButton("Kapat" if tr else "Close")
        restore.clicked.connect(self.restore_selected)
        permanent.clicked.connect(self.permanently_delete_selected)
        empty.clicked.connect(self.empty_trash)
        optimize.clicked.connect(self.optimize_database)
        close.clicked.connect(self.accept)
        row.addWidget(restore)
        row.addWidget(permanent)
        row.addStretch(1)
        row.addWidget(empty)
        row.addWidget(optimize)
        row.addWidget(close)

        root.addWidget(self.table, 1)
        root.addLayout(row)
        self.refresh()

    @property
    def _tr(self) -> bool:
        return bool(self.i18n and self.i18n.language == "tr")

    def refresh(self) -> None:
        notes = self.database.list_trash()
        self.table.setRowCount(len(notes))
        for r, note in enumerate(notes):
            title = QTableWidgetItem(note.title)
            title.setData(Qt.ItemDataRole.UserRole, note.id)
            try:
                stamp = datetime.fromisoformat(note.updated_at).astimezone().strftime("%Y-%m-%d %H:%M")
            except ValueError:
                stamp = note.updated_at
            self.table.setItem(r, 0, title)
            self.table.setItem(r, 1, QTableWidgetItem(stamp))
            self.table.setItem(r, 2, QTableWidgetItem(note.preview))
        self.table.resizeColumnsToContents()

    def _selected_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return int(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def restore_selected(self) -> None:
        note_id = self._selected_id()
        if note_id is None:
            QMessageBox.information(self, "Çöp Kutusu" if self._tr else "Trash", "Önce bir not seçin." if self._tr else "Select a note first.")
            return
        try:
            self.database.restore_note(note_id)
            self.changed = True
            self.refresh()
        except DatabaseError as exc:
            QMessageBox.critical(self, "Geri Yükleme Başarısız" if self._tr else "Restore Failed", str(exc))

    def permanently_delete_selected(self) -> None:
        note_id = self._selected_id()
        if note_id is None:
            QMessageBox.information(self, "Çöp Kutusu" if self._tr else "Trash", "Önce bir not seçin." if self._tr else "Select a note first.")
            return
        answer = QMessageBox.warning(
            self,
            "Kalıcı Olarak Sil" if self._tr else "Permanently Delete",
            "Bu işlem notu ve ona ait diyagram verisini kalıcı olarak siler. Geri alınamaz." if self._tr else "This permanently deletes the note and its diagram data. This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.database.permanently_delete_note(note_id)
            self.changed = True
            self.refresh()
        except DatabaseError as exc:
            QMessageBox.critical(self, "Silme Başarısız" if self._tr else "Delete Failed", str(exc))

    def empty_trash(self) -> None:
        if not self.database.list_trash():
            QMessageBox.information(self, "Çöp Kutusu" if self._tr else "Trash", "Çöp kutusu zaten boş." if self._tr else "Trash is already empty.")
            return
        answer = QMessageBox.warning(
            self,
            "Çöp Kutusunu Boşalt" if self._tr else "Empty Trash",
            "Çöp kutusundaki bütün notlar ve bağlı diyagram verileri kalıcı olarak silinsin mi?" if self._tr else "Permanently delete every note in Trash and its linked diagram data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            count = self.database.empty_trash()
            self.changed = True
            self.refresh()
            QMessageBox.information(self, "Çöp Kutusu" if self._tr else "Trash", (f"{count} not kalıcı olarak silindi." if self._tr else f"Permanently deleted {count} note(s)."))
        except DatabaseError as exc:
            QMessageBox.critical(self, "Çöp Kutusu Boşaltılamadı" if self._tr else "Empty Trash Failed", str(exc))

    def optimize_database(self) -> None:
        answer = QMessageBox.question(
            self,
            "Veritabanını Küçült" if self._tr else "Optimize Database",
            "SQLite VACUUM çalıştırılsın mı? Kalıcı silmelerden sonra veritabanı dosyasının boyutunu azaltabilir." if self._tr else "Run SQLite VACUUM now? This can reduce the database file size after permanent deletions.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.database.optimize()
            QMessageBox.information(self, "Veritabanını Küçült" if self._tr else "Optimize Database", "Veritabanı düzenleme tamamlandı." if self._tr else "Database optimization completed.")
        except DatabaseError as exc:
            QMessageBox.critical(self, "Optimizasyon Başarısız" if self._tr else "Optimize Failed", str(exc))

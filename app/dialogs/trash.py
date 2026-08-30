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


class TrashDialog(QDialog):
    def __init__(self, database: Database, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.changed = False
        self.setWindowTitle("Trash")
        self.resize(720, 420)
        root = QVBoxLayout(self)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Title", "Deleted / updated", "Preview"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        row = QHBoxLayout()
        restore = QPushButton("Restore")
        permanent = QPushButton("Permanently Delete")
        empty = QPushButton("Empty Trash")
        optimize = QPushButton("Optimize Database")
        close = QPushButton("Close")
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
            QMessageBox.information(self, "Trash", "Select a note first.")
            return
        try:
            self.database.restore_note(note_id)
            self.changed = True
            self.refresh()
        except DatabaseError as exc:
            QMessageBox.critical(self, "Restore Failed", str(exc))

    def permanently_delete_selected(self) -> None:
        note_id = self._selected_id()
        if note_id is None:
            QMessageBox.information(self, "Trash", "Select a note first.")
            return
        answer = QMessageBox.warning(
            self,
            "Permanently Delete",
            "This permanently deletes the note and its diagram data. This cannot be undone.",
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
            QMessageBox.critical(self, "Delete Failed", str(exc))

    def empty_trash(self) -> None:
        if not self.database.list_trash():
            QMessageBox.information(self, "Trash", "Trash is already empty.")
            return
        answer = QMessageBox.warning(
            self,
            "Empty Trash",
            "Permanently delete every note in Trash and its linked diagram data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            count = self.database.empty_trash()
            self.changed = True
            self.refresh()
            QMessageBox.information(self, "Trash", f"Permanently deleted {count} note(s).")
        except DatabaseError as exc:
            QMessageBox.critical(self, "Empty Trash Failed", str(exc))

    def optimize_database(self) -> None:
        answer = QMessageBox.question(
            self,
            "Optimize Database",
            "Run SQLite VACUUM now? This can reduce the database file size after permanent deletions.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.database.optimize()
            QMessageBox.information(self, "Optimize Database", "Database optimization completed.")
        except DatabaseError as exc:
            QMessageBox.critical(self, "Optimize Failed", str(exc))

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database import Database, DatabaseError
from app.i18n import I18n


class TrashDialog(QDialog):
    def __init__(self, database: Database, i18n: I18n | None = None, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.i18n = i18n
        self.changed = False
        self.setObjectName("trashDialog")
        self.setWindowTitle("Çöp Kutusu" if self._tr else "Trash")
        self.resize(900, 620)
        self.setMinimumSize(720, 480)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 16)
        root.setSpacing(12)

        title = QLabel("Çöp Kutusu" if self._tr else "Trash")
        title.setObjectName("dialogTitle")
        root.addWidget(title)
        intro = QLabel(
            "Projeler burada içindekilerle birlikte tek paket olarak görünür. Sağdaki oka basarak hangi notların, kararların, diyagramların ve depo bağlantılarının o projeyle birlikte çöp kutusuna taşındığını görebilirsiniz."
            if self._tr else
            "Projects appear here as one bundle with their contents. Use the arrow on the right to see which notes, decisions, diagrams and repository links moved to Trash with the project."
        )
        intro.setWordWrap(True)
        intro.setObjectName("helperBanner")
        root.addWidget(intro)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)
        self._build_project_tab()
        self._build_note_tab()

        footer = QHBoxLayout()
        self.optimize = QPushButton("Veritabanını Küçült" if self._tr else "Optimize Database")
        self.optimize.setToolTip(
            "Kalıcı silmelerden sonra SQLite veritabanı dosyasındaki boş alanı küçültür."
            if self._tr else
            "Reclaim unused SQLite file space after permanent deletions."
        )
        self.optimize.clicked.connect(self.optimize_database)
        close = QPushButton("Kapat" if self._tr else "Close")
        close.clicked.connect(self.accept)
        footer.addWidget(self.optimize)
        footer.addStretch(1)
        footer.addWidget(close)
        root.addLayout(footer)

        self.refresh()

    @property
    def _tr(self) -> bool:
        return bool(self.i18n and self.i18n.language == "tr")

    def _build_project_tab(self) -> None:
        self.project_tab = QWidget()
        layout = QVBoxLayout(self.project_tab)
        layout.setContentsMargins(8, 10, 8, 8)
        self.project_container = QWidget()
        self.project_cards = QVBoxLayout(self.project_container)
        self.project_cards.setContentsMargins(0, 0, 0, 0)
        self.project_cards.setSpacing(10)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(self.project_container)
        layout.addWidget(scroll, 1)
        self.tabs.addTab(self.project_tab, "Projeler" if self._tr else "Projects")

    def _build_note_tab(self) -> None:
        self.note_tab = QWidget()
        root = QVBoxLayout(self.note_tab)
        root.setContentsMargins(8, 10, 8, 8)
        hint = QLabel(
            "Burada yalnızca tek tek sildiğiniz notlar görünür. Bir projeyle birlikte silinen notlar Projeler sekmesinin altında gruplanır."
            if self._tr else
            "Only notes deleted individually appear here. Notes deleted with a project are grouped under the Projects tab."
        )
        hint.setWordWrap(True)
        hint.setObjectName("mutedText")
        root.addWidget(hint)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(
            ["Başlık", "Silinme / güncellenme", "Önizleme"] if self._tr else ["Title", "Deleted / updated", "Preview"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table, 1)

        row = QHBoxLayout()
        restore = QPushButton("Geri Yükle" if self._tr else "Restore")
        permanent = QPushButton("Kalıcı Olarak Sil" if self._tr else "Permanently Delete")
        permanent.setObjectName("dangerButton")
        empty = QPushButton("Tek Tek Silinen Notları Boşalt" if self._tr else "Empty Individually Deleted Notes")
        restore.clicked.connect(self.restore_selected)
        permanent.clicked.connect(self.permanently_delete_selected)
        empty.clicked.connect(self.empty_trash)
        row.addWidget(restore)
        row.addWidget(permanent)
        row.addStretch(1)
        row.addWidget(empty)
        root.addLayout(row)
        self.tabs.addTab(self.note_tab, "Notlar" if self._tr else "Notes")

    def refresh(self) -> None:
        self._refresh_projects()
        self._refresh_notes()

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _refresh_projects(self) -> None:
        self._clear_layout(self.project_cards)
        projects = self.database.list_trashed_projects()
        if not projects:
            empty = QLabel("Çöp kutusunda proje yok." if self._tr else "There are no projects in Trash.")
            empty.setObjectName("emptyState")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.project_cards.addWidget(empty, 1)
            return

        for project in projects:
            details = self.database.project_trash_contents(project.id)
            card = QFrame()
            card.setObjectName("trashProjectCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 13, 16, 13)
            card_layout.setSpacing(8)

            header = QHBoxLayout()
            text = QVBoxLayout()
            name = QLabel(project.name)
            name.setObjectName("cardTitle")
            try:
                stamp = datetime.fromisoformat(project.trashed_at or project.updated_at).astimezone().strftime("%Y-%m-%d %H:%M")
            except ValueError:
                stamp = project.trashed_at or project.updated_at
            meta = QLabel((f"Çöp kutusuna taşındı: {stamp}" if self._tr else f"Moved to Trash: {stamp}"))
            meta.setObjectName("mutedText")
            text.addWidget(name)
            text.addWidget(meta)
            arrow = QPushButton("▾")
            arrow.setObjectName("disclosureButton")
            arrow.setFixedSize(34, 34)
            arrow.setToolTip(
                "Bu projeyle birlikte çöp kutusuna taşınan içerikleri göster/gizle."
                if self._tr else
                "Show or hide the contents moved to Trash with this project."
            )
            header.addLayout(text, 1)
            header.addWidget(arrow, 0, Qt.AlignmentFlag.AlignTop)
            card_layout.addLayout(header)

            detail_widget = QFrame()
            detail_widget.setObjectName("trashBundleDetails")
            detail_widget.setVisible(False)
            detail_layout = QVBoxLayout(detail_widget)
            detail_layout.setContentsMargins(14, 12, 14, 12)
            detail_layout.setSpacing(9)
            self._add_bundle_section(detail_layout, "Notlar" if self._tr else "Notes", details["notes"])
            self._add_bundle_section(detail_layout, "Kararlar" if self._tr else "Decisions", details["decisions"])
            self._add_bundle_section(detail_layout, "Mimari / Diyagramlar" if self._tr else "Architecture / Diagrams", details["diagrams"])
            self._add_bundle_section(detail_layout, "Depo bağlantıları" if self._tr else "Repository links", details["repositories"])
            metadata = QLabel(
                (f"Kod bağlantıları: {details['resource_links']} · İnceleme başlangıçları: {details['review_baselines']}" if self._tr else
                 f"Code links: {details['resource_links']} · Review baselines: {details['review_baselines']}")
            )
            metadata.setObjectName("mutedText")
            detail_layout.addWidget(metadata)
            card_layout.addWidget(detail_widget)

            def toggle(_checked=False, panel=detail_widget, button=arrow):
                visible = not panel.isVisible()
                panel.setVisible(visible)
                button.setText("▴" if visible else "▾")

            arrow.clicked.connect(toggle)

            actions = QHBoxLayout()
            restore = QPushButton("Projeyi Geri Yükle" if self._tr else "Restore Project")
            restore.setObjectName("primaryButton")
            restore.setToolTip(
                "Projeyi ve proje silinirken aktif olan içeriklerini eski yerine geri getirir. Daha önce tek tek sildiğiniz notlar silinmiş kalır."
                if self._tr else
                "Restore the project and the content that was active when the project was deleted. Notes deleted earlier remain deleted."
            )
            restore.clicked.connect(lambda _checked=False, pid=project.id: self.restore_project(pid))
            permanent = QPushButton("Kalıcı Olarak Sil" if self._tr else "Permanently Delete")
            permanent.setObjectName("dangerButton")
            permanent.clicked.connect(lambda _checked=False, pid=project.id, n=project.name: self.permanently_delete_project(pid, n))
            actions.addWidget(restore)
            actions.addStretch(1)
            actions.addWidget(permanent)
            card_layout.addLayout(actions)
            self.project_cards.addWidget(card)
        self.project_cards.addStretch(1)

    def _add_bundle_section(self, layout: QVBoxLayout, title: str, values: object) -> None:
        items = list(values) if isinstance(values, (list, tuple)) else []
        heading = QLabel(f"{title} ({len(items)})")
        heading.setObjectName("bundleSectionTitle")
        layout.addWidget(heading)
        if not items:
            empty = QLabel("—")
            empty.setObjectName("mutedText")
            layout.addWidget(empty)
            return
        for value in items:
            label = QLabel(f"• {value}")
            label.setWordWrap(True)
            label.setObjectName("bundleItem")
            layout.addWidget(label)

    def _refresh_notes(self) -> None:
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

    def restore_project(self, project_id: int) -> None:
        try:
            self.database.restore_project(project_id)
            self.changed = True
            self.refresh()
        except DatabaseError as exc:
            QMessageBox.critical(self, "Geri Yükleme Başarısız" if self._tr else "Restore Failed", str(exc))

    def permanently_delete_project(self, project_id: int, project_name: str) -> None:
        prompt = (
            f'Bu işlem “{project_name}” projesini ve içindeki tüm DevNest verilerini kalıcı olarak siler. Geri alınamaz.\n\nDevam etmek için proje adını aynen yazın:'
            if self._tr else
            f'This permanently deletes “{project_name}” and all DevNest data inside it. This cannot be undone.\n\nType the project name exactly to continue:'
        )
        typed, ok = QInputDialog.getText(
            self, "Projeyi Kalıcı Sil" if self._tr else "Permanently Delete Project", prompt
        )
        if not ok:
            return
        if typed != project_name:
            QMessageBox.warning(
                self, "Proje Adı Eşleşmedi" if self._tr else "Project Name Did Not Match",
                "Proje adı eşleşmedi. Hiçbir şey silinmedi." if self._tr else "The project name did not match. Nothing was deleted."
            )
            return
        try:
            self.database.permanently_delete_project(project_id)
            self.changed = True
            self.refresh()
        except DatabaseError as exc:
            QMessageBox.critical(self, "Silme Başarısız" if self._tr else "Delete Failed", str(exc))

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
            QMessageBox.information(self, "Çöp Kutusu" if self._tr else "Trash", "Tek tek silinmiş not yok." if self._tr else "There are no individually deleted notes.")
            return
        answer = QMessageBox.warning(
            self,
            "Silinen Notları Boşalt" if self._tr else "Empty Deleted Notes",
            "Yalnızca tek tek silinen notlar kalıcı olarak silinsin mi? Proje paketleri etkilenmez." if self._tr else "Permanently delete only individually deleted notes? Project bundles are not affected.",
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

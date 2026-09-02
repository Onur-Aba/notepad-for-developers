from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout

from app.i18n import I18n
from app.services.workspace_transfer import BackupManager

class BackupManagerDialog(QDialog):
    restored = Signal()
    def __init__(self,manager:BackupManager,i18n:I18n,parent=None)->None:
        super().__init__(parent); self.manager=manager; self.i18n=i18n; tr=i18n.language=="tr"
        self.setWindowTitle("Backup Yöneticisi" if tr else "Backup Manager"); self.resize(720,520)
        root=QVBoxLayout(self); intro=QLabel("Manuel SQLite backup alın, mevcut backup'ları görün veya geri yükleyin." if tr else "Create manual SQLite backups, inspect existing backups, or restore one."); intro.setWordWrap(True); intro.setObjectName("helperBanner"); root.addWidget(intro)
        self.list=QListWidget(); root.addWidget(self.list,1)
        row=QHBoxLayout(); self.create=QPushButton("Yeni backup al" if tr else "Create backup"); self.restore=QPushButton("Seçileni geri yükle" if tr else "Restore selected"); row.addWidget(self.create); row.addWidget(self.restore); row.addStretch(1); root.addLayout(row)
        self.create.clicked.connect(self._create); self.restore.clicked.connect(self._restore)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Close); buttons.button(QDialogButtonBox.StandardButton.Close).setText("Kapat" if tr else "Close"); buttons.rejected.connect(self.reject); root.addWidget(buttons); self.refresh()
    def refresh(self)->None:
        self.list.clear()
        for path in self.manager.list_backups():
            item=QListWidgetItem(f"{path.name}\n{datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')} · {path.stat().st_size/1024:.1f} KB"); item.setData(Qt.ItemDataRole.UserRole,str(path)); self.list.addItem(item)
    def _create(self)->None:
        path=self.manager.create_backup(); self.refresh(); QMessageBox.information(self,"Backup",str(path))
    def _restore(self)->None:
        item=self.list.currentItem()
        if not item:return
        tr=self.i18n.language=="tr"; answer=QMessageBox.warning(self,"Backup", "Seçili backup mevcut çalışma alanının yerine geri yüklenecek. Öncesinde otomatik güvenlik backup'ı alınır. Devam?" if tr else "The selected backup will replace the current workspace. A safety backup is created first. Continue?", QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.Cancel,QMessageBox.StandardButton.Cancel)
        if answer!=QMessageBox.StandardButton.Yes:return
        self.manager.restore_backup(item.data(Qt.ItemDataRole.UserRole)); self.restored.emit(); self.accept()

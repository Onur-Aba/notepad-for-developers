from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout

from app.database import Database
from app.i18n import I18n


class NotificationCenterDialog(QDialog):
    teamRequested = Signal()

    def __init__(self,database:Database,i18n:I18n,parent=None)->None:
        super().__init__(parent); self.database=database; self.i18n=i18n; tr=i18n.language=="tr"
        self.setWindowTitle("Bildirim Merkezi" if tr else "Notification Center"); self.resize(680,520)
        root=QVBoxLayout(self); self.heading=QLabel(); self.heading.setObjectName("pageTitle"); root.addWidget(self.heading)
        self.list=QListWidget(); self.list.itemDoubleClicked.connect(self._activate); self.list.currentItemChanged.connect(lambda _c,_p:self._sync_actions()); root.addWidget(self.list,1)
        actions=QHBoxLayout()
        self.open_team=QPushButton("Ekip davetlerini aç" if tr else "Open team invitations"); self.open_team.clicked.connect(self._open_team); self.open_team.hide(); actions.addWidget(self.open_team)
        actions.addStretch(1)
        self.mark=QPushButton("Tümünü okundu işaretle" if tr else "Mark all as read"); self.mark.clicked.connect(self._mark); actions.addWidget(self.mark); root.addLayout(actions)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Close); buttons.button(QDialogButtonBox.StandardButton.Close).setText("Kapat" if tr else "Close"); buttons.rejected.connect(self.reject); root.addWidget(buttons)
        self.refresh()
    def refresh(self)->None:
        tr=self.i18n.language=="tr"; rows=self.database.list_notifications(limit=200); unread=self.database.unread_notification_count(); self.heading.setText((f"Bildirimler · {unread} okunmamış" if tr else f"Notifications · {unread} unread")); self.list.clear()
        for r in rows:
            marker="● " if not bool(r["is_read"]) else "  "; item=QListWidgetItem(f"{marker}{r['title']}\n{r['detail']}\n{self._date(str(r['created_at']))}"); item.setData(Qt.ItemDataRole.UserRole,str(r["event_type"])); self.list.addItem(item)
        if not rows:self.list.addItem("Henüz bildirim yok." if tr else "No notifications yet.")
        self._sync_actions()
    def _mark(self)->None:self.database.mark_notifications_read(); self.refresh()
    def _sync_actions(self)->None:
        item=self.list.currentItem(); self.open_team.setVisible(bool(item and str(item.data(Qt.ItemDataRole.UserRole))=="team_invite"))
    def _activate(self,item:QListWidgetItem)->None:
        if str(item.data(Qt.ItemDataRole.UserRole))=="team_invite": self._open_team()
    def _open_team(self)->None:
        self.database.mark_notifications_read(); self.teamRequested.emit(); self.accept()
    @staticmethod
    def _date(v:str)->str:
        try:return datetime.fromisoformat(v.replace("Z","+00:00")).astimezone().strftime("%Y-%m-%d %H:%M")
        except ValueError:return v

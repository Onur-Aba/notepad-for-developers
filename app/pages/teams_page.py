from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame,
    QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QScrollArea, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

from app.i18n import I18n
from app.integrations.supabase.client import SupabaseError
from app.services.async_tasks import AsyncTaskRunner
from app.services.cloud_service import CloudService, PERMISSIONS, PERMISSION_LABELS


class RoleEditorDialog(QDialog):
    """Role editor without a user-controlled hierarchy number.

    The server derives the internal hierarchy score from the permission set.
    This prevents arbitrary rank inflation and keeps the rule deterministic.
    """

    def __init__(self, i18n: I18n, role: dict | None = None, parent=None) -> None:
        super().__init__(parent)
        self.i18n = i18n
        self.tr = i18n.language == "tr"
        self.role = role or {}
        self.setWindowTitle("Rol" if self.tr else "Role")
        self.resize(560, 650)
        root = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit(str(self.role.get("name") or ""))
        self.name.setMaxLength(80)
        form.addRow("Rol adı" if self.tr else "Role name", self.name)
        root.addLayout(form)

        hint = QLabel(
            "Hiyerarşi seviyesi elle girilmez. DevNest, verdiğin yetkilere göre rolün seviyesini sunucuda otomatik hesaplar. Daha güçlü yönetim/silme yetkileri daha üst rol oluşturur; yine de hiç kimse kendisini, eşit yetkideki veya daha üst bir rolü değiştiremez."
            if self.tr else
            "Hierarchy is not entered manually. DevNest calculates the role level on the server from the permissions you grant. Stronger management/delete permissions produce a higher role; nobody can edit themselves, an equal role, or a higher role."
        )
        hint.setWordWrap(True)
        hint.setObjectName("pageSubtitle")
        root.addWidget(hint)

        perms = self.role.get("permissions") if isinstance(self.role.get("permissions"), dict) else {}
        self.checks: dict[str, QCheckBox] = {}
        for key in PERMISSIONS:
            box = QCheckBox(PERMISSION_LABELS["tr" if self.tr else "en"][key])
            box.setChecked(bool(perms.get(key, False)))
            root.addWidget(box)
            self.checks[key] = box
        root.addStretch(1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Kaydet" if self.tr else "Save")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("İptal" if self.tr else "Cancel")
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _accept(self) -> None:
        if self.name.text().strip():
            self.accept()

    def values(self) -> tuple[str, dict[str, bool]]:
        return self.name.text().strip(), {key: box.isChecked() for key, box in self.checks.items()}


class MemberPermissionsDialog(QDialog):
    def __init__(self, service: CloudService, team_id: str, member: dict, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.service = service
        self.team_id = team_id
        self.member = member
        self.i18n = i18n
        self.tr = i18n.language == "tr"
        profile = member.get("profile") or {}
        self.setWindowTitle(("Kişiye özel yetkiler · " if self.tr else "Member overrides · ") + str(profile.get("username") or member.get("user_id")))
        self.resize(580, 650)
        root = QVBoxLayout(self)
        hint = QLabel(
            "Buradaki ayar rol kuralının üstüne yazılır. 'Rolü kullan' seçeneği özel kuralı kaldırır."
            if self.tr else
            "These settings override the role. 'Use role' removes the personal override."
        )
        hint.setWordWrap(True)
        hint.setObjectName("pageSubtitle")
        root.addWidget(hint)
        try:
            overrides = service.member_overrides(team_id, str(member["user_id"]))
        except SupabaseError as exc:
            overrides = {}
            error = QLabel(str(exc)); error.setObjectName("helperBanner"); root.addWidget(error)
        self.combos: dict[str, QComboBox] = {}
        form = QFormLayout()
        root.addLayout(form)
        for key in PERMISSIONS:
            combo = QComboBox()
            combo.addItem("Rolü kullan" if self.tr else "Use role", None)
            combo.addItem("İzin ver" if self.tr else "Allow", True)
            combo.addItem("Engelle" if self.tr else "Deny", False)
            if key in overrides:
                combo.setCurrentIndex(1 if overrides[key] else 2)
            form.addRow(PERMISSION_LABELS["tr" if self.tr else "en"][key], combo)
            self.combos[key] = combo
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _save(self) -> None:
        try:
            for key, combo in self.combos.items():
                self.service.set_member_override(self.team_id, str(self.member["user_id"]), key, combo.currentData())
        except SupabaseError as exc:
            QMessageBox.warning(self, "Yetki güncellenemedi" if self.tr else "Permission update failed", str(exc))
            return
        self.accept()


class RoleVisibilityDialog(QDialog):
    def __init__(self, service: CloudService, team_id: str, role: dict, roles: list[dict], i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.service = service
        self.team_id = team_id
        self.role = role
        self.i18n = i18n
        self.tr = i18n.language == "tr"
        self.setWindowTitle("Departman / rol görünürlüğü" if self.tr else "Department / role visibility")
        self.resize(520, 520)
        root = QVBoxLayout(self)
        text = QLabel(
            f"{role.get('name')} rolündeki kişilerin hangi diğer rolleri/departmanları görebileceğini seç."
            if self.tr else
            f"Choose which other roles/departments people in {role.get('name')} can see."
        )
        text.setWordWrap(True)
        root.addWidget(text)
        current = service.role_visibility(team_id, str(role["id"]))
        self.checks: list[tuple[QCheckBox, str]] = []
        for target in roles:
            if str(target["id"]) == str(role["id"]):
                continue
            box = QCheckBox(str(target.get("name") or "Role"))
            box.setChecked(str(target["id"]) in current)
            root.addWidget(box)
            self.checks.append((box, str(target["id"])))
        root.addStretch(1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _save(self) -> None:
        try:
            self.service.set_role_visibility(self.team_id, str(self.role["id"]), [rid for box, rid in self.checks if box.isChecked()])
        except SupabaseError as exc:
            QMessageBox.warning(self, "Hata" if self.tr else "Error", str(exc))
            return
        self.accept()


class ResourceAccessDialog(QDialog):
    def __init__(self, service: CloudService, team_id: str, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.service = service
        self.team_id = team_id
        self.i18n = i18n
        self.tr = i18n.language == "tr"
        self.setWindowTitle("Özel içerik erişimi" if self.tr else "Private resource access")
        self.resize(700, 650)
        root = QVBoxLayout(self)
        hint = QLabel(
            "Bir not/karar/mimari öğesini kısıtlayınca yalnız seçtiğin ekip üyeleri görebilir. Proje sahibi her zaman erişir."
            if self.tr else
            "When a note/decision/architecture item is restricted, only selected team members can see it. The project owner always retains access."
        )
        hint.setWordWrap(True)
        hint.setObjectName("pageSubtitle")
        root.addWidget(hint)
        form = QFormLayout()
        self.project = QComboBox()
        self.resource = QComboBox()
        form.addRow("Proje" if self.tr else "Project", self.project)
        form.addRow("İçerik" if self.tr else "Resource", self.resource)
        root.addLayout(form)
        self.restricted = QCheckBox("Bu içeriği özel/kısıtlı yap" if self.tr else "Make this resource private/restricted")
        root.addWidget(self.restricted)
        self.members = QListWidget()
        root.addWidget(self.members, 1)
        self.projects = service.team_projects(team_id)
        for project in self.projects:
            self.project.addItem(f"TEAM · {project.get('name')}", str(project["id"]))
        self.project.currentIndexChanged.connect(self._load_resources)
        self.resource.currentIndexChanged.connect(self._load_access)
        self.restricted.toggled.connect(self.members.setEnabled)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
        self._load_resources()

    def _load_resources(self) -> None:
        self.resource.clear()
        pid = self.project.currentData()
        if not pid:
            return
        try:
            rows = self.service.cloud_resources(str(pid))
        except SupabaseError as exc:
            QMessageBox.warning(self, "Hata" if self.tr else "Error", str(exc)); return
        for row in rows:
            if row.get("resource_type") in {"note", "decision", "architecture"}:
                self.resource.addItem(f"{str(row.get('resource_type')).title()} · {row.get('title')}", (str(row.get("resource_type")), str(row.get("local_key"))))
        self._load_access()

    def _load_access(self) -> None:
        self.members.clear()
        pid = self.project.currentData()
        data = self.resource.currentData()
        if not pid or not data:
            return
        typ, key = data
        try:
            state = self.service.resource_access_state(self.team_id, str(pid), typ, key)
            members = self.service.team_members(self.team_id)
        except SupabaseError as exc:
            QMessageBox.warning(self, "Hata" if self.tr else "Error", str(exc)); return
        self.restricted.blockSignals(True)
        self.restricted.setChecked(bool(state["restricted"]))
        self.restricted.blockSignals(False)
        self.members.setEnabled(self.restricted.isChecked())
        allowed = set(state["users"])
        for member in members:
            if member.get("is_owner"):
                continue
            profile = member.get("profile") or {}
            role = member.get("role") or {}
            item = QListWidgetItem(f"@{profile.get('username') or member.get('user_id')} · {role.get('name') or '-'}")
            item.setData(Qt.ItemDataRole.UserRole, str(member["user_id"]))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if str(member["user_id"]) in allowed else Qt.CheckState.Unchecked)
            self.members.addItem(item)

    def _save(self) -> None:
        pid = self.project.currentData()
        data = self.resource.currentData()
        if not pid or not data:
            return
        typ, key = data
        users = [
            str(self.members.item(i).data(Qt.ItemDataRole.UserRole))
            for i in range(self.members.count())
            if self.members.item(i).checkState() == Qt.CheckState.Checked
        ]
        try:
            self.service.set_resource_allowed_users(self.team_id, str(pid), typ, key, users, restricted=self.restricted.isChecked())
        except SupabaseError as exc:
            QMessageBox.warning(self, "Hata" if self.tr else "Error", str(exc)); return
        self.accept()


class CloudResourceEditorDialog(QDialog):
    """Small online editor for team note/decision resources.

    It uses revision-based optimistic updates, which is what can later produce a
    clear conflict in the owner's manual backup dialog instead of last-write-wins.
    """

    def __init__(self, service: CloudService, row: dict, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.service = service
        self.row = row
        self.i18n = i18n
        self.tr = i18n.language == "tr"
        self.payload = dict(row.get("payload") or {}) if isinstance(row.get("payload"), dict) else {}
        kind = str(row.get("resource_type") or "")
        self.setWindowTitle(("TEAM online içerik · " if self.tr else "TEAM online content · ") + str(row.get("title") or ""))
        self.resize(760, 620)
        root = QVBoxLayout(self)
        warning = QLabel(
            "Bu düzenleme doğrudan ekibin ONLINE kopyasına yazılır. Proje sahibinin yerel kopyası farklıysa, sonraki manuel yedeklemede DevNest iki sürümü karşılaştırıp çakışma uyarısı gösterecektir."
            if self.tr else
            "This edit is written directly to the team's ONLINE copy. If the project owner's local copy differs, DevNest will compare both versions and show a conflict on the next manual backup."
        )
        warning.setWordWrap(True)
        warning.setObjectName("helperBanner")
        root.addWidget(warning)
        form = QFormLayout()
        self.title = QLineEdit(str(row.get("title") or self.payload.get("title") or ""))
        self.title.setMaxLength(500)
        form.addRow("Başlık" if self.tr else "Title", self.title)
        self.status = None
        if kind == "decision":
            self.status = QComboBox()
            current = str(self.payload.get("status") or "proposed")
            for value in ("proposed", "accepted", "superseded", "rejected"):
                self.status.addItem(value, value)
            idx = self.status.findData(current)
            if idx >= 0:
                self.status.setCurrentIndex(idx)
            form.addRow("Durum" if self.tr else "Status", self.status)
        root.addLayout(form)
        self.editor = QTextEdit()
        html = str(self.payload.get("content_html") or "")
        if html:
            self.editor.setHtml(html)
        else:
            self.editor.setPlainText(str(self.payload.get("content_plain") or ""))
        root.addWidget(self.editor, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Online'a kaydet" if self.tr else "Save online")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _save(self) -> None:
        title = self.title.text().strip()
        if not title:
            return
        payload = dict(self.payload)
        payload["title"] = title
        payload["content_html"] = self.editor.toHtml()
        payload["content_plain"] = self.editor.toPlainText()
        payload["updated_at"] = datetime.now(timezone.utc).isoformat()
        if self.status is not None:
            payload["status"] = str(self.status.currentData())
        try:
            self.row = self.service.update_cloud_resource(self.row, title, payload)
        except SupabaseError as exc:
            QMessageBox.warning(self, "Online kayıt başarısız" if self.tr else "Online save failed", str(exc))
            return
        self.accept()


class TeamDetailDialog(QDialog):
    def __init__(self, service: CloudService, team: dict, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.service = service
        self.team = team
        self.i18n = i18n
        self.tr = i18n.language == "tr"
        self.user_id = service.client.ensure_session().user_id
        self.is_owner = str(team.get("owner_id")) == self.user_id
        self.projects: list[dict] = []
        self.members: list[dict] = []
        self.roles: list[dict] = []
        self.activity: list[dict] = []
        self.runner = AsyncTaskRunner()
        self._refresh_generation = 0
        self.setWindowTitle(f"TEAM · {team.get('name')}")
        self.resize(940, 750)
        root = QVBoxLayout(self)
        title = QLabel(f"TEAM · {team.get('name')}")
        title.setObjectName("pageTitle")
        root.addWidget(title)
        self.loading = QLabel("Ekip bilgileri yükleniyor…" if self.tr else "Loading team information…")
        self.loading.setObjectName("mutedText")
        root.addWidget(self.loading)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)
        self._build_projects()
        self._build_members()
        self._build_roles()
        self._build_online_resources()
        self._build_activity()
        self.tabs.currentChanged.connect(self._tab_changed)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
        QTimer.singleShot(0, self.refresh_all)

    def _build_projects(self) -> None:
        widget = QWidget(); layout = QVBoxLayout(widget)
        row = QHBoxLayout()
        self.assign = QPushButton("Projeyi ekibe ata" if self.tr else "Assign project to team")
        self.assign.clicked.connect(self._assign_project); self.assign.setEnabled(self.is_owner)
        row.addWidget(self.assign); row.addStretch(1); layout.addLayout(row)
        self.project_list = QListWidget(); layout.addWidget(self.project_list, 1)
        self.remove_project = QPushButton("Seçili projeyi ekipten çıkar" if self.tr else "Remove selected project from team")
        self.remove_project.setEnabled(self.is_owner); self.remove_project.clicked.connect(self._remove_project)
        layout.addWidget(self.remove_project)
        self.tabs.addTab(widget, "Projeler" if self.tr else "Projects")

    def _build_members(self) -> None:
        widget = QWidget(); layout = QVBoxLayout(widget)
        row = QHBoxLayout()
        self.invite = QPushButton("Kullanıcı adıyla davet et" if self.tr else "Invite by username")
        self.invite.clicked.connect(self._invite)
        row.addWidget(self.invite); row.addStretch(1); layout.addLayout(row)
        self.member_list = QListWidget(); layout.addWidget(self.member_list, 1)
        controls = QHBoxLayout()
        self.role_combo = QComboBox()
        self.assign_role_btn = QPushButton("Rol ata" if self.tr else "Assign role")
        self.assign_role_btn.clicked.connect(self._assign_role)
        self.overrides = QPushButton("Kişiye özel yetkiler" if self.tr else "Member-specific permissions")
        self.overrides.clicked.connect(self._member_overrides)
        controls.addWidget(self.role_combo); controls.addWidget(self.assign_role_btn); controls.addWidget(self.overrides)
        layout.addLayout(controls)
        self.tabs.addTab(widget, "Üyeler" if self.tr else "Members")

    def _build_roles(self) -> None:
        widget = QWidget(); layout = QVBoxLayout(widget)
        row = QHBoxLayout()
        self.new_role = QPushButton("Yeni rol" if self.tr else "New role")
        self.edit_role = QPushButton("Rolü düzenle" if self.tr else "Edit role")
        self.visibility = QPushButton("Rol görünürlüğü" if self.tr else "Role visibility")
        self.private = QPushButton("Özel içerik erişimi" if self.tr else "Private resource access")
        self.new_role.clicked.connect(self._new_role); self.edit_role.clicked.connect(self._edit_role)
        self.visibility.clicked.connect(self._role_visibility); self.private.clicked.connect(self._private_access)
        row.addWidget(self.new_role); row.addWidget(self.edit_role); row.addWidget(self.visibility); row.addStretch(1); row.addWidget(self.private)
        layout.addLayout(row)
        self.role_list = QListWidget(); layout.addWidget(self.role_list, 1)
        note = QLabel(
            "Rol seviyesi görünmez ve elle düzenlenmez; sunucu yetkilerden otomatik hesaplar. manage_roles yetkisi olsa bile kişi kendisini, eşit yetkideki veya üst rolü değiştiremez."
            if self.tr else
            "Role level is hidden and cannot be edited manually; the server derives it from permissions. Even with manage_roles, a member cannot change themselves, an equal-permission role, or a higher role."
        )
        note.setWordWrap(True); note.setObjectName("mutedText"); layout.addWidget(note)
        self.tabs.addTab(widget, "Roller & Erişim" if self.tr else "Roles & Access")

    def _build_online_resources(self) -> None:
        widget = QWidget(); layout = QVBoxLayout(widget)
        hint = QLabel(
            "Ekip üyelerinin online not/karar düzenlemeleri burada yapılabilir. Düzenleme izinleri RLS ve rol yetkileriyle kontrol edilir."
            if self.tr else
            "Team members can edit online notes/decisions here. Edit access is enforced by RLS and role permissions."
        )
        hint.setWordWrap(True); hint.setObjectName("pageSubtitle"); layout.addWidget(hint)
        row = QHBoxLayout()
        self.resource_project_combo = QComboBox(); self.resource_project_combo.currentIndexChanged.connect(self._load_online_resources)
        self.resource_refresh = QPushButton("İçerikleri yenile" if self.tr else "Refresh resources"); self.resource_refresh.clicked.connect(self._load_online_resources)
        row.addWidget(self.resource_project_combo, 1); row.addWidget(self.resource_refresh); layout.addLayout(row)
        self.online_resource_list = QListWidget(); self.online_resource_list.itemDoubleClicked.connect(lambda _item: self._edit_online_resource()); layout.addWidget(self.online_resource_list, 1)
        self.edit_online_button = QPushButton("Seçili online içeriği düzenle" if self.tr else "Edit selected online content")
        self.edit_online_button.setObjectName("primaryButton"); self.edit_online_button.clicked.connect(self._edit_online_resource); layout.addWidget(self.edit_online_button)
        self.tabs.addTab(widget, "Online İçerik" if self.tr else "Online Content")

    def _build_activity(self) -> None:
        widget = QWidget(); layout = QVBoxLayout(widget)
        self.activity_list = QListWidget(); layout.addWidget(self.activity_list, 1)
        self.tabs.addTab(widget, "Ekip Aktivitesi" if self.tr else "Team Activity")

    def refresh_all(self) -> None:
        self._refresh_generation += 1
        generation = self._refresh_generation
        self.loading.setText("Ekip bilgileri yükleniyor…" if self.tr else "Loading team information…")
        self.loading.setVisible(True)
        self.tabs.setEnabled(False)

        def success(snapshot: dict) -> None:
            if generation != self._refresh_generation:
                return
            self.projects = snapshot.get("projects", [])
            self.members = snapshot.get("members", [])
            self.roles = snapshot.get("roles", [])
            self.activity = snapshot.get("activity", [])
            self._render_snapshot()
            self.loading.setVisible(False)
            self.tabs.setEnabled(True)

        def error(exc: Exception) -> None:
            if generation != self._refresh_generation:
                return
            self.loading.setText(str(exc))
            self.loading.setVisible(True)
            self.tabs.setEnabled(True)

        self.runner.submit(lambda: self.service.team_detail_snapshot(str(self.team["id"])), success, error)

    def _render_snapshot(self) -> None:
        self.project_list.clear()
        for project in self.projects:
            item = QListWidgetItem(f"TEAM · {project.get('name')}\n{project.get('description') or ''}")
            item.setData(Qt.ItemDataRole.UserRole, str(project["id"]))
            self.project_list.addItem(item)
        self.member_list.clear()
        for member in self.members:
            profile = member.get("profile") or {}
            role = member.get("role") or {}
            owner = " · OWNER" if member.get("is_owner") else ""
            item = QListWidgetItem(f"@{profile.get('username') or member.get('user_id')} · {role.get('name') or '-'}{owner}")
            item.setData(Qt.ItemDataRole.UserRole, str(member.get("user_id")))
            self.member_list.addItem(item)
        self.role_list.clear(); self.role_combo.clear()
        for role in self.roles:
            perms = role.get("permissions") if isinstance(role.get("permissions"), dict) else {}
            count = sum(1 for value in perms.values() if bool(value))
            label = f"{role.get('name')} · {count} yetki" if self.tr else f"{role.get('name')} · {count} permissions"
            item = QListWidgetItem(label); item.setData(Qt.ItemDataRole.UserRole, str(role["id"])); self.role_list.addItem(item)
            self.role_combo.addItem(str(role.get("name") or "Role"), str(role["id"]))
        self.activity_list.clear()
        for event in self.activity:
            actor = event.get("actor") or {}
            who = ("@" + str(actor.get("username"))) if actor.get("username") else ("system" if not event.get("actor_id") else str(event.get("actor_id"))[:8])
            self.activity_list.addItem(f"{event.get('created_at')} · {who} · {event.get('title')}\n{event.get('detail') or ''}")
        current_project = self.resource_project_combo.currentData()
        self.resource_project_combo.blockSignals(True); self.resource_project_combo.clear()
        for project in self.projects:
            self.resource_project_combo.addItem(f"TEAM · {project.get('name')}", str(project["id"]))
        if current_project:
            idx = self.resource_project_combo.findData(current_project)
            if idx >= 0: self.resource_project_combo.setCurrentIndex(idx)
        self.resource_project_combo.blockSignals(False)
        if self.tabs.currentWidget() is not None and self.tabs.tabText(self.tabs.currentIndex()) in {"Online İçerik", "Online Content"}:
            self._load_online_resources()

    def _tab_changed(self, index: int) -> None:
        if self.tabs.tabText(index) in {"Online İçerik", "Online Content"}:
            self._load_online_resources()

    def _load_online_resources(self) -> None:
        pid = self.resource_project_combo.currentData()
        self.online_resource_list.clear()
        if not pid:
            return
        self.online_resource_list.addItem("Yükleniyor…" if self.tr else "Loading…")
        self.online_resource_list.setEnabled(False)
        self.edit_online_button.setEnabled(False)

        def success(rows: list[dict]) -> None:
            self.online_resource_list.clear()
            for row in rows:
                typ = str(row.get("resource_type") or "")
                if typ not in {"note", "decision"}:
                    continue
                label_type = "Not" if (self.tr and typ == "note") else "Karar" if self.tr else typ.title()
                item = QListWidgetItem(f"{label_type} · {row.get('title') or '—'}\n{row.get('updated_at') or ''}")
                item.setData(Qt.ItemDataRole.UserRole, row)
                self.online_resource_list.addItem(item)
            if not self.online_resource_list.count():
                self.online_resource_list.addItem("Düzenlenebilir online not/karar yok." if self.tr else "No editable online notes/decisions.")
            self.online_resource_list.setEnabled(True)
            self.edit_online_button.setEnabled(True)

        def error(exc: Exception) -> None:
            self.online_resource_list.clear(); self.online_resource_list.addItem(str(exc)); self.online_resource_list.setEnabled(True)

        self.runner.submit(lambda: self.service.cloud_resources(str(pid)), success, error)

    def _edit_online_resource(self) -> None:
        item = self.online_resource_list.currentItem()
        row = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not isinstance(row, dict):
            return
        dialog = CloudResourceEditorDialog(self.service, row, self.i18n, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_online_resources()
            self.refresh_all()

    def _assign_project(self) -> None:
        try:
            projects = self.service.owned_cloud_projects()
        except SupabaseError as exc:
            QMessageBox.warning(self, "Online", str(exc)); return
        existing = {str(p["id"]) for p in self.projects}
        available = [p for p in projects if str(p["id"]) not in existing]
        if not available:
            QMessageBox.information(self, "DevNest Online", "Önce Online Yedekleme ekranından bir projeyi yedekle." if self.tr else "Back up a project from Online Backup first.")
            return
        labels = [str(p.get("name")) for p in available]
        choice, ok = QInputDialog.getItem(self, "Proje" if self.tr else "Project", "Ekip projesi:" if self.tr else "Team project:", labels, 0, False)
        if not ok:
            return
        project = available[labels.index(choice)]
        try:
            self.service.assign_team_project(str(self.team["id"]), str(project["id"])); self.refresh_all()
        except SupabaseError as exc:
            QMessageBox.warning(self, "Hata" if self.tr else "Error", str(exc))

    def _remove_project(self) -> None:
        item = self.project_list.currentItem()
        if not item: return
        try:
            self.service.unassign_team_project(str(self.team["id"]), str(item.data(Qt.ItemDataRole.UserRole))); self.refresh_all()
        except SupabaseError as exc:
            QMessageBox.warning(self, "Hata" if self.tr else "Error", str(exc))

    def _invite(self) -> None:
        username, ok = QInputDialog.getText(self, "Davet" if self.tr else "Invite", "Kullanıcı adı:" if self.tr else "Username:")
        if not ok or not username.strip(): return
        try:
            self.service.invite_username(str(self.team["id"]), username)
            QMessageBox.information(self, "Davet" if self.tr else "Invite", "Davet gönderildi." if self.tr else "Invitation sent.")
        except SupabaseError as exc:
            QMessageBox.warning(self, "Hata" if self.tr else "Error", str(exc))

    def _selected_member(self):
        item = self.member_list.currentItem(); uid = str(item.data(Qt.ItemDataRole.UserRole)) if item else ""
        return next((m for m in self.members if str(m.get("user_id")) == uid), None)

    def _assign_role(self) -> None:
        member = self._selected_member(); role_id = self.role_combo.currentData()
        if not member or not role_id or member.get("is_owner"): return
        try:
            self.service.assign_role(str(self.team["id"]), str(member["user_id"]), str(role_id)); self.refresh_all()
        except SupabaseError as exc:
            QMessageBox.warning(self, "Hata" if self.tr else "Error", str(exc))

    def _member_overrides(self) -> None:
        member = self._selected_member()
        if not member or member.get("is_owner"): return
        if MemberPermissionsDialog(self.service, str(self.team["id"]), member, self.i18n, self).exec() == QDialog.DialogCode.Accepted:
            self.refresh_all()

    def _new_role(self) -> None:
        dialog = RoleEditorDialog(self.i18n, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted: return
        name, permissions = dialog.values()
        try:
            self.service.create_role(str(self.team["id"]), name, permissions); self.refresh_all()
        except SupabaseError as exc:
            QMessageBox.warning(self, "Hata" if self.tr else "Error", str(exc))

    def _selected_role(self):
        item = self.role_list.currentItem(); rid = str(item.data(Qt.ItemDataRole.UserRole)) if item else ""
        return next((r for r in self.roles if str(r.get("id")) == rid), None)

    def _edit_role(self) -> None:
        role = self._selected_role()
        if not role: return
        dialog = RoleEditorDialog(self.i18n, role, self)
        if dialog.exec() != QDialog.DialogCode.Accepted: return
        name, permissions = dialog.values()
        try:
            self.service.update_role(str(role["id"]), name, permissions); self.refresh_all()
        except SupabaseError as exc:
            QMessageBox.warning(self, "Hata" if self.tr else "Error", str(exc))

    def _role_visibility(self) -> None:
        role = self._selected_role()
        if not role: return
        try:
            RoleVisibilityDialog(self.service, str(self.team["id"]), role, self.roles, self.i18n, self).exec()
        except SupabaseError as exc:
            QMessageBox.warning(self, "Hata" if self.tr else "Error", str(exc))

    def _private_access(self) -> None:
        try:
            ResourceAccessDialog(self.service, str(self.team["id"]), self.i18n, self).exec()
        except SupabaseError as exc:
            QMessageBox.warning(self, "Hata" if self.tr else "Error", str(exc))


class TeamsPage(QWidget):
    pendingCountChanged = Signal(int)
    onlineRequested = Signal()

    def __init__(self, service: CloudService, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.service = service
        self.i18n = i18n
        self.runner = AsyncTaskRunner()
        self._generation = 0
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 28, 30, 24); root.setSpacing(12)
        head = QHBoxLayout(); titles = QVBoxLayout()
        self.title = QLabel(); self.title.setObjectName("pageTitle")
        self.subtitle = QLabel(); self.subtitle.setObjectName("pageSubtitle"); self.subtitle.setWordWrap(True)
        titles.addWidget(self.title); titles.addWidget(self.subtitle); head.addLayout(titles, 1)
        self.create = QPushButton(); self.create.setObjectName("primaryButton"); self.create.clicked.connect(self._create_team)
        self.refresh_button = QPushButton(); self.refresh_button.clicked.connect(lambda: self.refresh(force=True))
        head.addWidget(self.refresh_button); head.addWidget(self.create); root.addLayout(head)
        self.container = QWidget(); self.cards = QVBoxLayout(self.container); self.cards.setSpacing(10)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QScrollArea.Shape.NoFrame); scroll.setWidget(self.container)
        root.addWidget(scroll, 1)
        self.i18n.languageChanged.connect(lambda _lang: self.retranslate_ui())
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        tr = self.i18n.language == "tr"
        self.title.setText("Ekipler" if tr else "Teams")
        self.subtitle.setText(
            "Ekip davetlerini, TEAM projelerini, otomatik yetki hiyerarşisini ve özel içerik erişimini buradan yönet."
            if tr else
            "Manage invitations, TEAM projects, automatic permission hierarchy, and private-resource access here."
        )
        self.create.setText("Ekip oluştur" if tr else "Create team")
        self.refresh_button.setText("Yenile" if tr else "Refresh")

    def _clear_cards(self) -> None:
        while self.cards.count():
            item = self.cards.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()

    def refresh(self, force: bool = False) -> None:
        self._generation += 1
        generation = self._generation
        self._clear_cards()
        tr = self.i18n.language == "tr"
        if not self.service.client.configured or not self.service.client.signed_in:
            frame = QFrame(); frame.setObjectName("projectCard"); layout = QVBoxLayout(frame)
            lab = QLabel("Ekipleri kullanmak için DevNest Online'a bağlan." if tr else "Connect to DevNest Online to use Teams."); lab.setWordWrap(True); layout.addWidget(lab)
            button = QPushButton("Online'a bağlan" if tr else "Connect online"); button.setObjectName("primaryButton"); button.clicked.connect(self.onlineRequested); layout.addWidget(button)
            self.cards.addWidget(frame); self.cards.addStretch(1); self.pendingCountChanged.emit(0)
            return

        loading = QFrame(); loading.setObjectName("projectCard"); layout = QVBoxLayout(loading)
        loading_title = QLabel("Ekipler yükleniyor…" if tr else "Loading teams…"); loading_title.setObjectName("cardTitle"); layout.addWidget(loading_title)
        loading_hint = QLabel("Tek bir online özet isteği kullanılıyor; ekran yanıt beklerken donmaz." if tr else "Using one online snapshot request; the page remains responsive while it loads.")
        loading_hint.setObjectName("mutedText"); layout.addWidget(loading_hint)
        self.cards.addWidget(loading); self.cards.addStretch(1)
        self.refresh_button.setEnabled(False)

        def success(overview: dict) -> None:
            if generation != self._generation: return
            self.refresh_button.setEnabled(True)
            self._render_overview(overview)

        def error(exc: Exception) -> None:
            if generation != self._generation: return
            self.refresh_button.setEnabled(True); self._clear_cards()
            label = QLabel(str(exc)); label.setWordWrap(True); label.setObjectName("helperBanner"); self.cards.addWidget(label); self.cards.addStretch(1); self.pendingCountChanged.emit(0)

        self.runner.submit(lambda: self.service.team_overview(force=force), success, error)

    def _render_overview(self, overview: dict) -> None:
        self._clear_cards()
        tr = self.i18n.language == "tr"
        invites = overview.get("invitations") if isinstance(overview.get("invitations"), list) else []
        teams = overview.get("teams") if isinstance(overview.get("teams"), list) else []
        self.pendingCountChanged.emit(len(invites))
        if invites:
            heading = QLabel(f"Bekleyen davetler · {len(invites)}" if tr else f"Pending invitations · {len(invites)}"); heading.setObjectName("cardTitle"); self.cards.addWidget(heading)
            by_team = {str(team["id"]): team for team in teams if team.get("id")}
            for invitation in invites:
                frame = QFrame(); frame.setObjectName("projectCard"); row = QHBoxLayout(frame)
                team = by_team.get(str(invitation.get("team_id")), {})
                row.addWidget(QLabel(f"TEAM · {team.get('name') or invitation.get('team_name') or invitation.get('team_id')}"), 1)
                accept = QPushButton("Kabul et" if tr else "Accept"); accept.setObjectName("primaryButton")
                decline = QPushButton("Reddet" if tr else "Decline")
                accept.clicked.connect(lambda _=False, invitation_id=str(invitation["id"]): self._respond(invitation_id, True))
                decline.clicked.connect(lambda _=False, invitation_id=str(invitation["id"]): self._respond(invitation_id, False))
                row.addWidget(accept); row.addWidget(decline); self.cards.addWidget(frame)
        pending_team_ids = {str(inv.get("team_id")) for inv in invites}
        visible_teams = [team for team in teams if str(team.get("id")) not in pending_team_ids]
        if not visible_teams:
            self.cards.addWidget(QLabel("Henüz üye olduğun ekip yok." if tr else "You are not a member of any team yet."))
        session = self.service.client.session
        user_id = session.user_id if session else ""
        for team in visible_teams:
            frame = QFrame(); frame.setObjectName("projectCard"); row = QHBoxLayout(frame); text = QVBoxLayout()
            name = QLabel(f"TEAM · {team.get('name')}"); name.setObjectName("cardTitle")
            owner = str(team.get("owner_id")) == user_id
            meta = QLabel("Sahibi sensin" if (tr and owner) else "You are the owner" if owner else "Üyesin" if tr else "Member"); meta.setObjectName("mutedText")
            text.addWidget(name); text.addWidget(meta); row.addLayout(text, 1)
            open_button = QPushButton("Aç" if tr else "Open"); open_button.setObjectName("primaryButton"); open_button.clicked.connect(lambda _=False, team=team: self._open_team(team)); row.addWidget(open_button)
            self.cards.addWidget(frame)
        self.cards.addStretch(1)

    def _create_team(self) -> None:
        tr = self.i18n.language == "tr"
        if not self.service.client.signed_in:
            self.onlineRequested.emit(); return
        name, ok = QInputDialog.getText(self, "Ekip oluştur" if tr else "Create team", "Ekip adı:" if tr else "Team name:")
        if not ok or not name.strip(): return
        try:
            self.service.create_team(name); self.refresh(force=True)
        except SupabaseError as exc:
            QMessageBox.warning(self, "Hata" if tr else "Error", str(exc))

    def _respond(self, invitation_id: str, accept: bool) -> None:
        try:
            self.service.respond_invitation(invitation_id, accept); self.refresh(force=True)
        except SupabaseError as exc:
            QMessageBox.warning(self, "Hata" if self.i18n.language == "tr" else "Error", str(exc))

    def _open_team(self, team: dict) -> None:
        try:
            TeamDetailDialog(self.service, team, self.i18n, self).exec(); self.refresh(force=True)
        except SupabaseError as exc:
            QMessageBox.warning(self, "Online", str(exc))

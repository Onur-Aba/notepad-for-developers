from __future__ import annotations

import difflib

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QDialogButtonBox, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QMessageBox, QProgressBar, QPushButton, QTextEdit,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout,
)

from app.i18n import I18n
from app.integrations.supabase.client import SupabaseError
from app.services.cloud_service import CloudConflict, CloudPreflight, CloudService

ROLE_KIND = Qt.ItemDataRole.UserRole
ROLE_ID = Qt.ItemDataRole.UserRole + 1
ROLE_CONFLICT_KEY = Qt.ItemDataRole.UserRole + 2


class CloudConflictDialog(QDialog):
    """Lets the user inspect online edits before anything is overwritten."""

    def __init__(self, conflicts: list[CloudConflict], i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.conflicts = conflicts
        self.i18n = i18n
        self.tr = i18n.language == "tr"
        self.combos: dict[str, QComboBox] = {}
        self.setWindowTitle("Online değişiklik çakışması" if self.tr else "Online change conflict")
        self.resize(850, 650)
        root = QVBoxLayout(self)

        title = QLabel("⚠ Aynı içerik online ortamda da değiştirilmiş" if self.tr else "⚠ The same content was also changed online")
        title.setObjectName("pageTitle")
        root.addWidget(title)
        explanation = QLabel(
            "DevNest hiçbir değişikliği otomatik olarak ezmedi. Aşağıdaki not/kararlar bu cihazın son yedeğinden sonra başka bir kullanıcı tarafından değişmiş. Bir öğe seçerek neyin değiştiğini incele ve hangi sürümün kullanılacağını belirle."
            if self.tr else
            "DevNest did not overwrite anything automatically. These notes/decisions were changed by another user after this device's last backup. Select an item to inspect the changes and choose which version should win."
        )
        explanation.setWordWrap(True)
        explanation.setObjectName("pageSubtitle")
        root.addWidget(explanation)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            "İçerik" if self.tr else "Content",
            "Online değişiklik" if self.tr else "Online change",
            "Bu yedeklemede" if self.tr else "For this backup",
        ])
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.currentItemChanged.connect(self._show_details)
        root.addWidget(self.tree, 1)

        detail_label = QLabel("Değişiklik detayı" if self.tr else "Change details")
        detail_label.setObjectName("cardTitle")
        root.addWidget(detail_label)
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setMinimumHeight(180)
        root.addWidget(self.details)

        for conflict in conflicts:
            kind = "Not" if (self.tr and conflict.resource_type == "note") else "Karar" if self.tr else conflict.resource_type.title()
            summary = "; ".join(conflict.changed_summary[:3]) or ("Online içerik değişti" if self.tr else "Online content changed")
            item = QTreeWidgetItem([f"{kind} · {conflict.title}", summary, ""])
            item.setData(0, ROLE_CONFLICT_KEY, conflict.key)
            item.setToolTip(0, conflict.title)
            self.tree.addTopLevelItem(item)
            combo = QComboBox()
            combo.addItem("Online sürümü yerelde kullan" if self.tr else "Use online version locally", "remote")
            combo.addItem("Yerel sürümü online'a yükle" if self.tr else "Upload local version", "local")
            combo.addItem("Şimdilik atla" if self.tr else "Skip for now", "skip")
            # Safest default: keep the newer online change and pull it locally.
            combo.setCurrentIndex(0)
            self.tree.setItemWidget(item, 2, combo)
            self.combos[conflict.key] = combo

        if self.tree.topLevelItemCount():
            self.tree.setCurrentItem(self.tree.topLevelItem(0))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Seçimlerle devam et" if self.tr else "Continue with choices")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Yedeklemeyi iptal et" if self.tr else "Cancel backup")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def resolutions(self) -> dict[str, str]:
        return {key: str(combo.currentData()) for key, combo in self.combos.items()}

    def _show_details(self, item: QTreeWidgetItem | None, _previous: QTreeWidgetItem | None = None) -> None:
        if item is None:
            self.details.clear()
            return
        key = str(item.data(0, ROLE_CONFLICT_KEY) or "")
        conflict = next((c for c in self.conflicts if c.key == key), None)
        if conflict is None:
            self.details.clear()
            return
        local_text = str(conflict.local_payload.get("content_plain") or "")
        remote_text = str(conflict.remote_payload.get("content_plain") or "")
        diff = "\n".join(difflib.unified_diff(
            local_text.splitlines(), remote_text.splitlines(),
            fromfile="LOCAL", tofile="ONLINE", lineterm="", n=2,
        ))
        if len(diff) > 12000:
            diff = diff[:12000] + "\n…"
        lines = [
            ("Tür" if self.tr else "Type") + f": {conflict.resource_type}",
            ("Yerel başlık" if self.tr else "Local title") + f": {conflict.local_title or '—'}",
            ("Online başlık" if self.tr else "Online title") + f": {conflict.remote_title or '—'}",
            ("Değiştiren" if self.tr else "Changed by") + f": {conflict.remote_updated_by_name or (conflict.remote_updated_by[:8] if conflict.remote_updated_by else '—')}",
            ("Online güncellenme" if self.tr else "Online updated") + f": {conflict.remote_updated_at or '—'}",
            ("Online revision" if self.tr else "Online revision") + f": {conflict.remote_revision}",
            "",
            ("Tespit edilen değişiklikler:" if self.tr else "Detected changes:"),
        ]
        lines.extend(f"• {line}" for line in conflict.changed_summary)
        if diff:
            lines.extend(["", ("Metin farkı (yerel → online):" if self.tr else "Text diff (local → online):"), diff])
        self.details.setPlainText("\n".join(lines))


class CloudSyncDialog(QDialog):
    signedOut = Signal()
    localContentChanged = Signal()

    def __init__(self, service: CloudService, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.service = service
        self.i18n = i18n
        self.tr = i18n.language == "tr"
        self.service.disable_auto_sync()
        self.setWindowTitle("Online Yedekleme" if self.tr else "Online Backup")
        self.resize(860, 720)
        root = QVBoxLayout(self)

        session = service.client.session
        who = (session.username or session.email) if session else ""
        title = QLabel(f"DevNest Online · {who}" if who else "DevNest Online")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        banner = QFrame()
        banner.setObjectName("helperBanner")
        banner_layout = QVBoxLayout(banner)
        banner_title = QLabel("☁ Bu ekran ONLINE YEDEKLEME içindir" if self.tr else "☁ This screen uploads an ONLINE BACKUP")
        banner_title.setObjectName("cardTitle")
        banner_layout.addWidget(banner_title)
        banner_text = QLabel(
            "Aşağıda işaretlediğin proje ve içerikler internet üzerinden Supabase hesabına gönderilir. İşaretlemek tek başına yükleme yapmaz: yerel değişiklikler yalnızca “Seçilenleri online'a yedekle” tuşuna bastığında yüklenir. Bir projenin içinden tek not seçsen bile proje adı/kimliği üst kayıt olarak korunur. Yerel klasör yolları, parolalar ve API anahtarları gönderilmez."
            if self.tr else
            "Projects and items checked below are sent over the internet to your Supabase account. Checking an item does not upload it by itself: local changes are uploaded only when you press “Back up selected items online”. Even when only one note is selected, the parent project name/identity is kept. Local filesystem paths, passwords and API keys are not uploaded."
        )
        banner_text.setWordWrap(True)
        banner_layout.addWidget(banner_text)
        root.addWidget(banner)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            "Online'a yüklenecek içerik" if self.tr else "Content to upload online",
            "Tür" if self.tr else "Type",
        ])
        self.tree.setUniformRowHeights(True)
        self.tree.setAlternatingRowColors(True)
        header = self.tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        root.addWidget(self.tree, 1)

        manual_hint = QLabel(
            "Yerel-first çalışma: Değişiklikler otomatik yüklenmez. Online projelerde yaptığın yeni değişiklikleri göndermek için bu ekrandaki yedekleme tuşunu kullan."
            if self.tr else
            "Local-first workflow: changes are never uploaded automatically. Use the backup button on this screen whenever you want to publish new changes to an online project."
        )
        manual_hint.setWordWrap(True)
        manual_hint.setObjectName("mutedText")
        root.addWidget(manual_hint)

        self.progress_label = QLabel("")
        self.progress_label.setObjectName("mutedText")
        root.addWidget(self.progress_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setVisible(False)
        root.addWidget(self.progress)

        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setObjectName("mutedText")
        root.addWidget(self.status)

        row = QHBoxLayout()
        self.sync_button = QPushButton("Seçilenleri online'a yedekle" if self.tr else "Back up selected items online")
        self.sync_button.setObjectName("primaryButton")
        self.sync_button.clicked.connect(self._sync)
        self.logout_button = QPushButton("Online hesaptan çık" if self.tr else "Sign out")
        self.logout_button.clicked.connect(self._logout)
        row.addWidget(self.sync_button)
        row.addStretch(1)
        row.addWidget(self.logout_button)
        root.addLayout(row)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.buttons.button(QDialogButtonBox.StandardButton.Close).setText("Kapat" if self.tr else "Close")
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)
        self._populate()

    def _populate(self) -> None:
        saved = self.service.saved_selection()
        self.tree.clear()
        group_labels = {
            "notes": "Notlar" if self.tr else "Notes",
            "decisions": "Kararlar" if self.tr else "Decisions",
            "architecture": "Mimari" if self.tr else "Architecture",
            "repositories": "Repository'ler" if self.tr else "Repositories",
        }
        type_labels = {
            "notes": "Note",
            "decisions": "Decision",
            "architecture": "Architecture",
            "repositories": "Repository",
        }
        fallback = {
            "notes": "İsimsiz not" if self.tr else "Untitled note",
            "decisions": "İsimsiz karar" if self.tr else "Untitled decision",
            "architecture": "İsimsiz mimari" if self.tr else "Untitled architecture",
            "repositories": "İsimsiz repository" if self.tr else "Unnamed repository",
        }

        for entry in self.service.project_tree():
            project = entry["project"]
            pid = str(project.id)
            project_saved = saved.get(pid, {})
            project_label = str(project.name or ("İsimsiz proje" if self.tr else "Untitled project"))
            root = QTreeWidgetItem([project_label, "Project"])
            root.setToolTip(0, project_label)
            root.setData(0, ROLE_KIND, "project")
            root.setData(0, ROLE_ID, pid)
            root.setFlags(root.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsAutoTristate)
            root.setCheckState(0, Qt.CheckState.Unchecked)
            self.tree.addTopLevelItem(root)

            for group_key in ("notes", "decisions", "architecture", "repositories"):
                values = entry[group_key]
                group = QTreeWidgetItem([f"{group_labels[group_key]} ({len(values)})", group_labels[group_key]])
                group.setData(0, ROLE_KIND, "group")
                group.setData(0, ROLE_ID, group_key)
                group.setFlags(group.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsAutoTristate)
                group.setCheckState(0, Qt.CheckState.Unchecked)
                root.addChild(group)
                selected = set(project_saved.get(group_key, []))
                for item_id, label in values:
                    clean_label = str(label or "").strip() or f"{fallback[group_key]} #{item_id}"
                    child = QTreeWidgetItem([clean_label, type_labels[group_key]])
                    child.setToolTip(0, clean_label)
                    child.setData(0, ROLE_KIND, group_key)
                    child.setData(0, ROLE_ID, str(item_id))
                    child.setFlags(child.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    child.setCheckState(0, Qt.CheckState.Checked if str(item_id) in selected else Qt.CheckState.Unchecked)
                    group.addChild(child)
            root.setExpanded(True)
        self.tree.scrollToTop()

    def selection(self) -> dict[str, dict[str, list[str]]]:
        result: dict[str, dict[str, list[str]]] = {}
        for i in range(self.tree.topLevelItemCount()):
            root = self.tree.topLevelItem(i)
            pid = str(root.data(0, ROLE_ID))
            groups: dict[str, list[str]] = {"notes": [], "decisions": [], "architecture": [], "repositories": []}
            for gi in range(root.childCount()):
                group = root.child(gi)
                key = str(group.data(0, ROLE_ID))
                if key not in groups:
                    continue
                groups[key] = [
                    str(group.child(ci).data(0, ROLE_ID))
                    for ci in range(group.childCount())
                    if group.child(ci).checkState(0) == Qt.CheckState.Checked
                ]
            if root.checkState(0) != Qt.CheckState.Unchecked:
                groups["_project"] = ["1"]
            result[pid] = groups
        return result

    def _set_busy(self, busy: bool) -> None:
        self.sync_button.setEnabled(not busy)
        self.logout_button.setEnabled(not busy)
        self.tree.setEnabled(not busy)
        close_button = self.buttons.button(QDialogButtonBox.StandardButton.Close)
        if close_button:
            close_button.setEnabled(not busy)
        self.progress.setVisible(busy)
        if busy:
            self.progress.setValue(0)

    def _phase_progress(self, start: int, end: int, current: int, total: int, label: str) -> None:
        total = max(1, int(total))
        ratio = max(0.0, min(1.0, max(0, current) / total))
        percent = int(start + (end - start) * ratio)
        self.progress.setValue(max(0, min(99, percent)))
        self.progress_label.setText(label)
        # Network operations are synchronous, but explicit event pumping makes
        # the progress bar visibly advance between safe upload operations.
        QApplication.processEvents()

    def _sync(self) -> None:
        selection = self.selection()
        self.service.save_selection(selection, False)
        selected_count = sum(len(values) for groups in selection.values() for key, values in groups.items() if key != "_project")
        selected_projects = sum(1 for groups in selection.values() if any(bool(v) for v in groups.values()))
        if not selected_projects:
            self.status.setText("Online'a yedeklenecek hiçbir içerik seçili değil." if self.tr else "No content is selected for online backup.")
            return

        self._set_busy(True)
        self.status.clear()
        try:
            self.progress_label.setText("Online değişiklikler kontrol ediliyor…" if self.tr else "Checking online changes…")
            preflight = self.service.preflight_sync(selection, lambda c, t, l: self._phase_progress(0, 25, c, t, l))
            resolutions: dict[str, str] = {}
            if preflight.conflicts:
                self.progress.setValue(25)
                conflict_dialog = CloudConflictDialog(preflight.conflicts, self.i18n, self)
                if conflict_dialog.exec() != QDialog.DialogCode.Accepted:
                    self.status.setText("Yedekleme iptal edildi; hiçbir çakışan içerik ezilmedi." if self.tr else "Backup cancelled; no conflicting content was overwritten.")
                    return
                resolutions = conflict_dialog.resolutions()

            self.progress_label.setText("Seçilen içerikler online'a yükleniyor…" if self.tr else "Uploading selected content online…")
            counts = self.service.sync_selection(
                selection,
                preflight=preflight,
                conflict_resolutions=resolutions,
                progress=lambda c, t, l: self._phase_progress(25, 99, c, t, l),
            )
            self.progress.setValue(100)
            self.progress_label.setText("Online yedekleme tamamlandı" if self.tr else "Online backup complete")
            if counts.get("pulled"):
                self.localContentChanged.emit()
            self.status.setText(
                (f"✓ {counts['projects']} proje ve {counts['resources']} içerik online'a yedeklendi. "
                 f"{counts.get('pulled', 0)} online sürüm yerelde kullanıldı, {counts.get('skipped', 0)} çakışma atlandı, "
                 f"{counts['removed']} eski kişisel yedek kaydı kaldırıldı.")
                if self.tr else
                (f"✓ Backed up {counts['projects']} projects and {counts['resources']} items online. "
                 f"Used {counts.get('pulled', 0)} online versions locally, skipped {counts.get('skipped', 0)} conflicts, "
                 f"and removed {counts['removed']} stale personal backup records.")
            )
        except SupabaseError as exc:
            if getattr(exc, "code", None) == "DEVNEST_CONFLICT":
                QMessageBox.warning(
                    self,
                    "Yeni online değişiklik bulundu" if self.tr else "New online change detected",
                    (str(exc) + ("\n\nOnline Yedekleme'yi tekrar çalıştır; DevNest en yeni sürümü karşılaştıracak." if self.tr else "\n\nRun Online Backup again and DevNest will compare the newest version.")),
                )
            else:
                QMessageBox.warning(self, "Yedekleme başarısız" if self.tr else "Backup failed", str(exc))
            self.progress_label.setText("Yedekleme tamamlanamadı" if self.tr else "Backup did not complete")
        finally:
            self._set_busy(False)
            # Keep the finished bar visible long enough to make success clear.
            self.progress.setVisible(True)

    def _logout(self) -> None:
        answer = QMessageBox.question(
            self,
            "Çıkış" if self.tr else "Sign out",
            "Online hesaptan çıkılsın mı? Yerel projelerin silinmez." if self.tr else "Sign out of DevNest Online? Local projects are not deleted.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.service.client.sign_out()
        self.signedOut.emit()
        self.accept()

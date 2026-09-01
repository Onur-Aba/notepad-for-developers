from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QListWidget, QListWidgetItem, QTabWidget, QVBoxLayout

from app.i18n import I18n
from app.models import ChangedFile, ReviewSummary
from app.services.change_detection_service import dedupe_changed_files, dedupe_commits


class ReviewDetailsDialog(QDialog):
    def __init__(self, summary: ReviewSummary, i18n: I18n | None = None, parent=None) -> None:
        super().__init__(parent)
        self.i18n = i18n
        tr = bool(i18n and i18n.language == "tr")
        self.setWindowTitle("Son Kontrolden Beri Ne Değişti?" if tr else "What Changed Since the Last Check?")
        self.resize(860, 590)
        root = QVBoxLayout(self)

        explain = QLabel(
            "Bu pencere Git'in teknik A/M/D harflerini göstermek yerine değişikliği normal dille anlatır. "
            "Önce 'Bu bilgiyle ilgili dosyalar' sekmesine bakın. Bunlar, not/karar/mimari öğesine doğrudan bağladığınız kod alanında değişen dosyalardır."
            if tr else
            "This window explains changes in plain language instead of Git's technical A/M/D letters. "
            "Start with the 'Files related to this knowledge' tab. Those are the files that changed inside the code area directly connected to this note, decision or architecture item."
        )
        explain.setWordWrap(True)
        explain.setObjectName("helperBanner")
        root.addWidget(explain)

        header = QLabel(
            (f"Son kontrol edilen commit: {(summary.baseline_sha or '—')[:12]}   →   Şimdiki commit: {(summary.current_sha or '—')[:12]}\n"
             f"Arada {summary.commit_count} commit var · Bu bilgiyle ilgili {len(summary.linked_changed_files)} dosya değişti")
            if tr else
            (f"Last checked commit: {(summary.baseline_sha or '—')[:12]}   →   Current commit: {(summary.current_sha or '—')[:12]}\n"
             f"There are {summary.commit_count} commit(s) in between · {len(summary.linked_changed_files)} file(s) related to this knowledge changed")
        )
        header.setObjectName("dashboardPanel")
        root.addWidget(header)

        tabs = QTabWidget()

        related_files = QListWidget()
        linked_files = dedupe_changed_files(list(summary.linked_changed_files))
        if linked_files:
            for item in linked_files:
                related_files.addItem(self._file_item(item, tr, linked=True))
        else:
            related_files.addItem(
                "Bu bilgiye doğrudan bağlı dosyalarda değişiklik bulunamadı."
                if tr else "No changed files were found in the code directly linked to this knowledge."
            )

        commits = QListWidget()
        unique_commits = dedupe_commits(list(summary.commits))
        if unique_commits:
            for commit in unique_commits:
                author = f" · {commit.author}" if commit.author else ""
                item = QListWidgetItem(f"{commit.short_sha} · {commit.message}{author}")
                item.setToolTip(
                    ("Bu commit, son kontrol noktasından sonra yapılmış bir kod değişikliğidir." if tr else
                     "This commit was made after the last review point.")
                )
                commits.addItem(item)
        else:
            commits.addItem("Gösterilecek commit yok." if tr else "There are no commits to show.")

        all_files = QListWidget()
        all_changed = dedupe_changed_files(list(summary.changed_files))
        linked_keys = {(x.path, x.previous_path) for x in linked_files}
        if all_changed:
            for item in all_changed:
                all_files.addItem(self._file_item(item, tr, linked=(item.path, item.previous_path) in linked_keys))
        else:
            all_files.addItem("Gösterilecek dosya değişikliği yok." if tr else "There are no file changes to show.")

        tabs.addTab(related_files, (f"Bu bilgiyle ilgili dosyalar ({len(linked_files)})" if tr else f"Files related to this knowledge ({len(linked_files)})"))
        tabs.addTab(commits, (f"Commitler ({len(unique_commits)})" if tr else f"Commits ({len(unique_commits)})"))
        tabs.addTab(all_files, (f"Depodaki tüm değişen dosyalar ({len(all_changed)})" if tr else f"All changed files in repository ({len(all_changed)})"))
        root.addWidget(tabs, 1)

        footer = QLabel(
            "Ne yapmalısınız? İlgili dosyalara ve karar/not içeriğine bakın. Hâlâ doğruysa 'Bunu kontrol ettim' deyin; DevNest şimdiki commit'i yeni başlangıç noktası olarak kaydeder."
            if tr else
            "What should you do? Read the related files and the decision/note. If the knowledge is still correct, choose 'I checked this'; DevNest saves the current commit as the new reference point."
        )
        footer.setWordWrap(True)
        footer.setObjectName("mutedText")
        root.addWidget(footer)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText("Kapat" if tr else "Close")
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        root.addWidget(buttons)

    @staticmethod
    def _human_status(status: str, tr: bool) -> str:
        code = (status or "M").upper()[:1]
        if tr:
            return {
                "A": "Yeni dosya eklendi",
                "M": "Dosyanın içeriği değişti",
                "D": "Dosya silindi",
                "R": "Dosyanın adı veya yeri değişti",
                "C": "Dosya kopyalandı",
                "T": "Dosya türü değişti",
            }.get(code, "Dosyada değişiklik yapıldı")
        return {
            "A": "New file added",
            "M": "File contents changed",
            "D": "File deleted",
            "R": "File renamed or moved",
            "C": "File copied",
            "T": "File type changed",
        }.get(code, "File changed")

    @classmethod
    def _file_item(cls, item: ChangedFile, tr: bool, linked: bool) -> QListWidgetItem:
        status = cls._human_status(item.status, tr)
        text = f"{status}\n{item.path}"
        if item.previous_path:
            text += (f"\nÖnceki yol: {item.previous_path}" if tr else f"\nPrevious path: {item.previous_path}")
        if linked:
            text += ("\n✓ Bu bilgiyle doğrudan bağlantılı" if tr else "\n✓ Directly connected to this knowledge")
        widget_item = QListWidgetItem(text)
        widget_item.setToolTip(
            ("Git durumu teknik harf yerine açıklama olarak gösteriliyor." if tr else
             "The Git status is shown as a plain-language explanation instead of a technical letter.")
        )
        return widget_item

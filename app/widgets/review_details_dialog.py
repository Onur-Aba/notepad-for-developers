from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QListWidget, QTabWidget, QVBoxLayout

from app.i18n import I18n
from app.models import ReviewSummary


class ReviewDetailsDialog(QDialog):
    def __init__(self, summary: ReviewSummary, i18n: I18n | None = None, parent=None) -> None:
        super().__init__(parent)
        tr = bool(i18n and i18n.language == "tr")
        self.setWindowTitle("Son Kontrolden Beri Değişiklikler" if tr else "Changes Since Review")
        self.resize(780, 540)
        root = QVBoxLayout(self)
        explain = QLabel(
            "Aşağıdaki liste, son kontrol noktasından bugüne kadar depoda nelerin değiştiğini gösterir. 'Bağlı' işaretli dosyalar özellikle bu bilgiyle ilişkilendirdiğiniz alanlardır."
            if tr else
            "This shows what changed in the repository since the last review point. Files marked as linked are specifically connected to this knowledge item."
        )
        explain.setWordWrap(True)
        explain.setObjectName("helperBanner")
        root.addWidget(explain)
        header = QLabel(
            (f"Son kontrol: {(summary.baseline_sha or '—')[:12]}   →   Güncel: {(summary.current_sha or '—')[:12]}\n"
             f"{summary.commit_count} commit · {len(summary.linked_changed_files)} bağlı dosya değişti")
            if tr else
            (f"Reviewed: {(summary.baseline_sha or '—')[:12]}   →   Current: {(summary.current_sha or '—')[:12]}\n"
             f"{summary.commit_count} commits · {len(summary.linked_changed_files)} linked files changed")
        )
        header.setObjectName("dashboardPanel")
        root.addWidget(header)
        tabs = QTabWidget()
        files = QListWidget()
        linked_paths = {x.path for x in summary.linked_changed_files}
        for item in summary.changed_files:
            marker = item.status or "M"
            text = f"{marker}  {item.path}"
            if item.path in linked_paths:
                text += "   ← " + ("bağlı" if tr else "linked")
            files.addItem(text)
        commits = QListWidget()
        for commit in summary.commits:
            commits.addItem(f"{commit.short_sha}   {commit.message}   {commit.author or ''}")
        prs = QListWidget()
        for pr in summary.pull_requests:
            prs.addItem(f"#{pr.number}   {pr.title}   {pr.state}")
        tabs.addTab(files, "Değişen Dosyalar" if tr else "Changed Files")
        tabs.addTab(commits, "Commit'ler" if tr else "Commits")
        tabs.addTab(prs, "Pull Request'ler" if tr else "Pull Requests")
        root.addWidget(tabs, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        if tr:
            buttons.button(QDialogButtonBox.StandardButton.Close).setText("Kapat")
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        root.addWidget(buttons)

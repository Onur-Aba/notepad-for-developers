from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from app.database import Database
from app.i18n import I18n


class RepositoryDiagnosticsDialog(QDialog):
    def __init__(self, database: Database, project_id: int, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.project_id = project_id
        self.i18n = i18n
        tr = i18n.language == "tr"
        self.setWindowTitle("Repository Erişim Tanılama" if tr else "Repository Access Diagnostics")
        self.resize(640, 430)
        root = QVBoxLayout(self)
        intro = QLabel(
            "Teknik hata metni yerine bağlantı zincirinin hangi adımda koptuğunu gösterir."
            if tr else
            "Shows which step of the access chain is failing instead of only exposing a technical error."
        )
        intro.setWordWrap(True)
        intro.setObjectName("helperBanner")
        root.addWidget(intro)
        self.repo = QComboBox()
        for repository in database.list_repositories(project_id):
            self.repo.addItem(repository.full_name or repository.name, repository.id)
        self.repo.currentIndexChanged.connect(self.refresh)
        root.addWidget(self.repo)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setObjectName("dashboardPanel")
        root.addWidget(self.status, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText("Kapat" if tr else "Close")
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
        self.refresh()

    def refresh(self, *_args) -> None:
        tr = self.i18n.language == "tr"
        rid = self.repo.currentData()
        repository = self.database.get_repository(int(rid)) if rid is not None else None
        account = self.database.get_github_account()
        installations = self.database.list_github_installations()
        if not repository:
            self.status.setText("Bu projeye repo bağlı değil." if tr else "No repository is linked to this project.")
            return

        local = bool(repository.local_git_root and Path(repository.local_git_root).exists())
        github_linked = repository.github_repo_id is not None
        github_account = account is not None
        app_installed = bool(installations) if github_linked else False
        permission = repository.github_access_state == "available" if github_linked else False

        def mark(ok: bool) -> str:
            return "✓" if ok else "✗"

        if not github_linked:
            permission_text = "— GitHub bağlantısı yok" if tr else "— No GitHub connection"
        elif permission:
            permission_text = "✓ — Erişim doğrulandı" if tr else "✓ — Access verified"
        elif repository.github_access_state in {"unknown", "unchecked"}:
            permission_text = "? — Henüz doğrulanmadı" if tr else "? — Not verified yet"
        else:
            permission_text = "✗ — GitHub erişimi doğrulanamadı" if tr else "✗ — GitHub access could not be verified"

        lines = [
            ("GitHub hesabı " if tr else "GitHub account ") + mark(github_account) + (f" — {account.login}" if account else ""),
            ("GitHub App kurulu " if tr else "GitHub App installed ") + (mark(app_installed) if github_linked else "—"),
            ("Repository izni " if tr else "Repository permission ") + permission_text,
            ("Yerel repo " if tr else "Local repo ") + mark(local) + f" — {repository.local_git_root or '—'}",
        ]
        if local and not permission:
            lines.append(
                "Yerel repo kullanılabilir; GitHub erişim problemi yerel çalışmayı engellemez."
                if tr else
                "The local repository is available; a GitHub access problem does not block local work."
            )
        self.status.setText("\n\n".join(lines))

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QVBoxLayout,
)

from app.services.local_git import GitError, GitRepositoryInfo, inspect_repository


class ProjectDialog(QDialog):
    def __init__(self, parent=None, *, name: str = "", local_path: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setMinimumWidth(560)
        self.repo_info: GitRepositoryInfo | None = None

        root = QVBoxLayout(self)
        intro = QLabel("Create a local-first DevNest project. A Git repository is optional and can be attached later.")
        intro.setWordWrap(True); root.addWidget(intro)
        form = QFormLayout(); root.addLayout(form)
        self.name_edit = QLineEdit(name); self.name_edit.setPlaceholderText("Project name")
        form.addRow("Name", self.name_edit)

        path_row = QHBoxLayout()
        self.path_edit = QLineEdit(local_path); self.path_edit.setPlaceholderText("C:\\Projects\\my-repo (optional)")
        browse = QPushButton("Browse…"); browse.clicked.connect(self._browse)
        inspect = QPushButton("Inspect Git"); inspect.clicked.connect(self._inspect)
        path_row.addWidget(self.path_edit, 1); path_row.addWidget(browse); path_row.addWidget(inspect)
        form.addRow("Local repository", path_row)

        self.detected = QLabel("No repository inspected yet.")
        self.detected.setWordWrap(True); root.addWidget(self.detected)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)

    def _browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Git repository")
        if path:
            self.path_edit.setText(path)
            if not self.name_edit.text().strip(): self.name_edit.setText(Path(path).name)
            self._inspect()

    def _inspect(self) -> None:
        path = self.path_edit.text().strip()
        if not path:
            self.repo_info = None; self.detected.setText("Local repository is optional."); return
        try:
            self.repo_info = inspect_repository(path)
            remote = self.repo_info.remote_url or "No origin remote"
            self.detected.setText(
                f"✓ Git repository\nRoot: {self.repo_info.root}\nBranch: {self.repo_info.branch or 'detached'}\n"
                f"HEAD: {self.repo_info.head_sha[:12]}\nOrigin: {remote}"
            )
            self.path_edit.setText(str(self.repo_info.root))
            if not self.name_edit.text().strip(): self.name_edit.setText(self.repo_info.root.name)
        except GitError as exc:
            self.repo_info = None
            self.detected.setText(f"Not ready: {exc}")

    def _accept(self) -> None:
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Project", "Enter a project name."); return
        if self.path_edit.text().strip() and self.repo_info is None:
            try: self.repo_info = inspect_repository(self.path_edit.text().strip())
            except GitError as exc:
                QMessageBox.warning(self, "Repository", f"The selected folder is not a usable Git repository.\n\n{exc}"); return
        self.accept()

    def values(self) -> tuple[str, GitRepositoryInfo | None]:
        return self.name_edit.text().strip(), self.repo_info

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.database import Database
from app.i18n import I18n
from app.models import Repository, TargetType
from app.services.async_tasks import AsyncTaskRunner


GitHubContentsLoader = Callable[[Repository, str], list[dict[str, Any]] | dict[str, Any]]


class GitHubPathBrowser(QDialog):
    """Small lazy directory browser for GitHub-only repositories.

    Every directory navigation performs one background Contents API request. It
    intentionally never downloads the whole repository tree.
    """

    def __init__(self, repository: Repository, target_type: str, loader: GitHubContentsLoader, parent=None) -> None:
        super().__init__(parent)
        self.repository = repository
        self.target_type = target_type
        self.loader = loader
        self.runner = AsyncTaskRunner()
        self.current_path = ""
        self.selected_path = ""
        self.setWindowTitle(f"Browse {repository.full_name or repository.name}")
        self.resize(680, 520)

        root = QVBoxLayout(self)
        intro = QLabel("Browse repository contents from GitHub (read-only). Directories load only when opened.")
        intro.setWordWrap(True)
        root.addWidget(intro)
        nav = QHBoxLayout()
        self.up_button = QPushButton("Up")
        self.up_button.clicked.connect(self._go_up)
        self.path_label = QLabel("/")
        self.path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        nav.addWidget(self.up_button)
        nav.addWidget(self.path_label, 1)
        root.addLayout(nav)
        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self._open_item)
        self.list.currentItemChanged.connect(lambda _c, _p: self._update_select_state())
        root.addWidget(self.list, 1)
        self.status = QLabel("Loading…")
        self.status.setObjectName("mutedText")
        root.addWidget(self.status)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        self.select_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.select_button.setText("Select")
        buttons.accepted.connect(self._choose)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
        self._load("")

    def _load(self, path: str) -> None:
        self.current_path = path.strip("/")
        self.path_label.setText("/" + self.current_path if self.current_path else "/")
        self.up_button.setEnabled(bool(self.current_path))
        self.list.clear()
        self.list.setEnabled(False)
        self.select_button.setEnabled(False)
        self.status.setText("Loading repository contents…")
        self.runner.submit(
            lambda: self.loader(self.repository, self.current_path),
            self._loaded,
            self._failed,
        )

    def _loaded(self, data: list[dict[str, Any]] | dict[str, Any]) -> None:
        entries = data if isinstance(data, list) else [data]
        entries = [entry for entry in entries if isinstance(entry, dict)]
        entries.sort(key=lambda entry: (entry.get("type") != "dir", str(entry.get("name", "")).casefold()))
        for entry in entries:
            kind = str(entry.get("type") or "file")
            path = str(entry.get("path") or entry.get("name") or "")
            name = str(entry.get("name") or path)
            item = QListWidgetItem(("📁 " if kind == "dir" else "📄 ") + name)
            item.setData(Qt.ItemDataRole.UserRole, (kind, path))
            self.list.addItem(item)
        self.list.setEnabled(True)
        self.status.setText("Double-click a directory to open it. GitHub access remains read-only.")
        self._update_select_state()

    def _failed(self, exc: Exception) -> None:
        self.list.setEnabled(True)
        self.status.setText(f"Could not load this path: {exc}")
        self._update_select_state()

    def _go_up(self) -> None:
        parts = [part for part in self.current_path.split("/") if part]
        self._load("/".join(parts[:-1]))

    def _open_item(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(data, tuple) or len(data) != 2:
            return
        kind, path = str(data[0]), str(data[1])
        if kind == "dir":
            self._load(path)
        elif self.target_type == TargetType.FILE.value:
            self.selected_path = path
            self.accept()

    def _update_select_state(self) -> None:
        item = self.list.currentItem()
        if self.target_type == TargetType.DIRECTORY.value:
            # The current directory itself is a valid choice, including repository root.
            self.select_button.setEnabled(True)
            if item:
                data = item.data(Qt.ItemDataRole.UserRole)
                if isinstance(data, tuple) and data[0] == "dir":
                    self.select_button.setText("Select Directory")
                else:
                    self.select_button.setText("Select Current Directory")
            else:
                self.select_button.setText("Select Current Directory")
        else:
            data = item.data(Qt.ItemDataRole.UserRole) if item else None
            self.select_button.setEnabled(bool(isinstance(data, tuple) and data[0] == "file"))
            self.select_button.setText("Select File")

    def _choose(self) -> None:
        item = self.list.currentItem()
        data = item.data(Qt.ItemDataRole.UserRole) if item else None
        if self.target_type == TargetType.FILE.value:
            if isinstance(data, tuple) and data[0] == "file":
                self.selected_path = str(data[1])
                self.accept()
            return
        if isinstance(data, tuple) and data[0] == "dir":
            self.selected_path = str(data[1]).rstrip("/") + "/"
        else:
            self.selected_path = (self.current_path.rstrip("/") + "/") if self.current_path else ""
        self.accept()


class ResourceLinkDialog(QDialog):
    def __init__(self, database: Database, project_id: int,
                 github_contents_loader: GitHubContentsLoader | None = None, i18n: I18n | None = None, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.project_id = project_id
        self.github_contents_loader = github_contents_loader
        self.i18n = i18n
        t = i18n.t if i18n else (lambda key, **_kwargs: key)
        self.setWindowTitle(t("resources.dialog_title") if i18n else "Link Resource")
        self.setMinimumWidth(560)
        root = QVBoxLayout(self)
        intro = QLabel(t("resources.intro") if i18n else "Link this knowledge to a read-only repository resource. DevNest stores only the reference and review baseline.")
        intro.setWordWrap(True)
        root.addWidget(intro)
        form = QFormLayout()
        self.repository = QComboBox()
        for repo in database.list_repositories(project_id):
            label = repo.full_name or repo.name
            if repo.local_git_root:
                label += " · Local"
            elif repo.github_repo_id is not None:
                label += " · GitHub"
            self.repository.addItem(label, repo.id)
        self.target_type = QComboBox()
        for label, value in (
            (t("resources.repo") if i18n else "Repository", TargetType.REPOSITORY.value),
            (t("resources.directory") if i18n else "Directory", TargetType.DIRECTORY.value),
            (t("resources.file") if i18n else "File", TargetType.FILE.value),
            (t("resources.branch") if i18n else "Branch", TargetType.BRANCH.value),
            (t("resources.commit") if i18n else "Commit", TargetType.COMMIT.value),
            (t("resources.pr") if i18n else "Pull Request", TargetType.PULL_REQUEST.value),
        ):
            self.target_type.addItem(label, value)
        self.target_value = QLineEdit()
        self.target_value.setPlaceholderText("backend/auth/ or backend/auth/session.py")
        browse_row = QHBoxLayout()
        self.browse = QPushButton(t("resources.browse_local") if i18n else "Browse Local…")
        self.browse.clicked.connect(self._browse_local)
        self.github_browse = QPushButton(t("resources.browse_github") if i18n else "Browse GitHub…")
        self.github_browse.clicked.connect(self._browse_github)
        if self.i18n:
            self.repository.setToolTip("Bu bilginin hangi depoya ait olduğunu seçin." if self.i18n.language == "tr" else "Choose which repository this knowledge belongs to.")
            self.target_type.setToolTip("Tüm depo yerine belirli bir klasör veya dosya seçerseniz DevNest yalnızca o alanı takip eder." if self.i18n.language == "tr" else "Choose a folder or file when you want DevNest to watch only one part of the repository.")
            self.target_value.setToolTip("Depo içindeki yol veya referans. Dosya/klasör seçmek değişiklik takibi için en açıklayıcı seçenektir." if self.i18n.language == "tr" else "The path or reference inside the repository. File/folder links are the clearest choice for change tracking.")
        browse_row.addWidget(self.browse)
        browse_row.addWidget(self.github_browse)
        browse_row.addStretch(1)
        form.addRow(t("resources.repository") if i18n else "Repository", self.repository)
        form.addRow(t("resources.type") if i18n else "Type", self.target_type)
        form.addRow(t("resources.target") if i18n else "Target", self.target_value)
        form.addRow("", browse_row)
        root.addLayout(form)
        self.hint = QLabel()
        self.hint.setObjectName("mutedText")
        self.hint.setWordWrap(True)
        root.addWidget(self.hint)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(t("resources.link") if i18n else "Link")
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
        self.target_type.currentIndexChanged.connect(self._update_state)
        self.repository.currentIndexChanged.connect(self._update_state)
        self._update_state()

    def _selected_repo(self) -> Repository | None:
        rid = self.repository.currentData()
        return self.database.get_repository(int(rid)) if rid is not None else None

    def _update_state(self) -> None:
        target_type = str(self.target_type.currentData())
        repo = self._selected_repo()
        is_path = target_type in {TargetType.FILE.value, TargetType.DIRECTORY.value}
        self.target_value.setEnabled(target_type != TargetType.REPOSITORY.value)
        self.browse.setVisible(bool(repo and repo.local_git_root and is_path))
        self.github_browse.setVisible(bool(repo and not repo.local_git_root and repo.full_name and is_path and self.github_contents_loader))
        if target_type == TargetType.REPOSITORY.value:
            self.target_value.clear()
            self.hint.setText(self.i18n.t("resources.hint.repo") if self.i18n else "Any code change after the baseline can require review for a repository-level link.")
        elif target_type == TargetType.DIRECTORY.value:
            self.hint.setText(self.i18n.t("resources.hint.dir") if self.i18n else "Directory matching is boundary-aware: backend/auth/ matches nested files, not backend/authentication/.")
        elif target_type in {TargetType.COMMIT.value, TargetType.PULL_REQUEST.value}:
            self.hint.setText(self.i18n.t("resources.hint.ref") if self.i18n else "Commit and PR links are implementation references; path changes remain the primary review mechanism.")
        else:
            self.hint.setText(self.i18n.t("resources.hint.path") if self.i18n else "Paths are stored relative to the repository root and normalized with forward slashes.")

    def _browse_local(self) -> None:
        repo = self._selected_repo()
        if not repo or not repo.local_git_root:
            return
        root = Path(repo.local_git_root)
        target_type = str(self.target_type.currentData())
        if target_type == TargetType.DIRECTORY.value:
            chosen = QFileDialog.getExistingDirectory(self, "Select Repository Directory", str(root))
        else:
            chosen, _ = QFileDialog.getOpenFileName(self, "Select Repository File", str(root))
        if not chosen:
            return
        try:
            relative = Path(chosen).resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            QMessageBox.warning(self, "Outside Repository", "Select a file or directory inside the linked repository.")
            return
        if target_type == TargetType.DIRECTORY.value and relative:
            relative += "/"
        self.target_value.setText(relative)

    def _browse_github(self) -> None:
        repo = self._selected_repo()
        if not repo or not self.github_contents_loader:
            return
        browser = GitHubPathBrowser(repo, str(self.target_type.currentData()), self.github_contents_loader, self)
        if browser.exec() == QDialog.DialogCode.Accepted:
            self.target_value.setText(browser.selected_path)

    def _validate(self) -> None:
        if self.repository.currentData() is None:
            QMessageBox.warning(self, "Repository Required", "Link a repository to this project first.")
            return
        target_type = str(self.target_type.currentData())
        value = self.target_value.text().strip()
        if target_type != TargetType.REPOSITORY.value and not value:
            # Empty path is meaningful only when selecting the repository root as a directory.
            if target_type != TargetType.DIRECTORY.value:
                QMessageBox.warning(self, "Target Required", "Enter or select a repository target.")
                return
        self.accept()

    def selection(self) -> tuple[int, str, str]:
        return int(self.repository.currentData()), str(self.target_type.currentData()), self.target_value.text().strip().replace("\\", "/")

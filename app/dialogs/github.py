from __future__ import annotations

import time
import webbrowser

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout,
)

from app.services.github_client import GitHubAuthorizationPending, GitHubClient, GitHubError, GitHubSlowDown


class GitHubConnectDialog(QDialog):
    def __init__(self, client: GitHubClient, parent=None) -> None:
        super().__init__(parent)
        self.client = client
        self.device = None
        self.deadline = 0.0
        self.setWindowTitle("Connect GitHub")
        self.setMinimumWidth(480)
        root = QVBoxLayout(self)
        intro = QLabel("DevNest uses GitHub Device Flow. Your browser handles authorization; DevNest never asks for your GitHub password.")
        intro.setWordWrap(True); root.addWidget(intro)
        self.code = QLineEdit(); self.code.setReadOnly(True); self.code.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code.setStyleSheet("font-size: 22px; font-weight: 700; letter-spacing: 2px; padding: 8px;")
        root.addWidget(self.code)
        row = QHBoxLayout(); self.open_button = QPushButton("Open GitHub"); self.open_button.clicked.connect(self._open)
        self.start_button = QPushButton("Generate code"); self.start_button.clicked.connect(self.start)
        row.addWidget(self.start_button); row.addWidget(self.open_button); root.addLayout(row)
        self.status = QLabel("Generate a code to begin."); self.status.setWordWrap(True); root.addWidget(self.status)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel); buttons.rejected.connect(self.reject); root.addWidget(buttons)
        self.timer = QTimer(self); self.timer.timeout.connect(self._poll)
        QTimer.singleShot(0, self.start)

    def start(self) -> None:
        try:
            self.device = self.client.start_device_flow(); self.deadline = time.monotonic() + self.device.expires_in
            self.code.setText(self.device.user_code); self.status.setText("Enter this code on GitHub, then approve DevNest.")
            self.timer.start(max(5, self.device.interval) * 1000)
        except GitHubError as exc:
            self.status.setText(str(exc)); self.timer.stop()

    def _open(self) -> None:
        if self.device: webbrowser.open(self.device.verification_uri)

    def _poll(self) -> None:
        if not self.device: return
        if time.monotonic() >= self.deadline:
            self.timer.stop(); self.status.setText("Code expired. Generate a new code."); return
        try:
            self.client.poll_device_flow(self.device.device_code)
            user = self.client.authenticated_user(); self.timer.stop()
            self.status.setText(f"Connected as @{user.get('login', 'GitHub user')}"); QTimer.singleShot(400, self.accept)
        except GitHubAuthorizationPending:
            self.status.setText("Waiting for GitHub authorization…")
        except GitHubSlowDown:
            self.timer.setInterval(self.timer.interval() + 5000)
        except GitHubError as exc:
            self.timer.stop(); self.status.setText(str(exc))


class GitHubRepositoryDialog(QDialog):
    def __init__(self, client: GitHubClient, parent=None, install_url: str = "") -> None:
        super().__init__(parent)
        self.client = client; self.repositories: list[dict[str, object]] = []
        self.setWindowTitle("GitHub Repositories"); self.resize(700, 560)
        root = QVBoxLayout(self)
        top = QHBoxLayout(); self.search = QLineEdit(); self.search.setPlaceholderText("Search repositories…")
        refresh = QPushButton("Refresh"); refresh.clicked.connect(self.load)
        top.addWidget(self.search, 1); top.addWidget(refresh)
        if install_url:
            manage = QPushButton("Manage GitHub access"); manage.clicked.connect(lambda: webbrowser.open(install_url)); top.addWidget(manage)
        root.addLayout(top)
        self.list = QListWidget(); self.list.itemDoubleClicked.connect(lambda _item, _column: self.accept()); root.addWidget(self.list, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)
        self.search.textChanged.connect(self._filter); QTimer.singleShot(0, self.load)

    def load(self) -> None:
        try: self.repositories = self.client.list_repositories()
        except GitHubError as exc:
            QMessageBox.warning(self, "GitHub", str(exc)); return
        self._filter(self.search.text())
        if not self.repositories:
            item = QListWidgetItem("No DevNest GitHub App repositories are available. Install/manage the app access, then Refresh.")
            item.setFlags(Qt.ItemFlag.NoItemFlags); self.list.addItem(item)

    def _filter(self, text: str) -> None:
        term = text.strip().casefold(); self.list.clear()
        for repo in self.repositories:
            full = str(repo.get("full_name", ""))
            if term and term not in full.casefold(): continue
            privacy = "private" if repo.get("private") else "public"
            item = QListWidgetItem(f"{full}   ·   {privacy}   ·   {repo.get('default_branch', 'main')}")
            item.setData(Qt.ItemDataRole.UserRole, repo); self.list.addItem(item)

    def selected_repository(self) -> dict[str, object] | None:
        item = self.list.currentItem(); data = item.data(Qt.ItemDataRole.UserRole) if item else None
        return data if isinstance(data, dict) else None

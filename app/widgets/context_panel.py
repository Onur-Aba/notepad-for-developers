from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from app.models import ExternalRef, Repository, ResourceLink


class ContextPanel(QWidget):
    documentKindChanged = Signal(str)
    scanRequested = Signal()
    markReviewedRequested = Signal()
    addRepositoryLinkRequested = Signal()
    addDirectoryLinkRequested = Signal()
    addFileLinkRequested = Signal()
    removeResourceRequested = Signal(int)
    addCommitRequested = Signal()
    addPullRequestRequested = Signal()
    removeExternalRequested = Signal(int)
    openResourceRequested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self); root.setContentsMargins(14, 12, 14, 12); root.setSpacing(10)
        header = QHBoxLayout(); title = QLabel("Engineering Context"); title.setStyleSheet("font-size: 17px; font-weight: 700;")
        self.kind = QComboBox(); self.kind.addItem("Note", "note"); self.kind.addItem("Decision", "decision")
        self.kind.currentIndexChanged.connect(lambda _i: self.documentKindChanged.emit(str(self.kind.currentData())))
        header.addWidget(title); header.addStretch(1); header.addWidget(QLabel("Type:")); header.addWidget(self.kind); root.addLayout(header)

        self.repo_label = QLabel("No repository attached to this project."); self.repo_label.setWordWrap(True); root.addWidget(self.repo_label)
        status_row = QHBoxLayout(); self.status = QLabel("No linked code"); self.status.setStyleSheet("font-weight: 700;")
        scan = QPushButton("Scan now"); scan.clicked.connect(self.scanRequested)
        self.review = QPushButton("✓ Mark as Reviewed"); self.review.clicked.connect(self.markReviewedRequested)
        status_row.addWidget(self.status); status_row.addStretch(1); status_row.addWidget(scan); status_row.addWidget(self.review); root.addLayout(status_row)

        root.addWidget(self._section("Code links"))
        link_buttons = QHBoxLayout()
        for text, signal in (("+ Repository", self.addRepositoryLinkRequested), ("+ Folder", self.addDirectoryLinkRequested), ("+ File", self.addFileLinkRequested)):
            button = QPushButton(text); button.clicked.connect(signal); link_buttons.addWidget(button)
        link_buttons.addStretch(1); root.addLayout(link_buttons)
        self.resources = QTreeWidget(); self.resources.setHeaderLabels(["Target", "Scope", "Baseline", "Status"]); self.resources.setRootIsDecorated(False)
        self.resources.itemDoubleClicked.connect(self._resource_double_clicked); root.addWidget(self.resources, 1)
        remove_resource = QPushButton("Remove selected code link"); remove_resource.clicked.connect(self._remove_resource); root.addWidget(remove_resource)

        root.addWidget(self._section("Implementation references"))
        refs_row = QHBoxLayout(); commit = QPushButton("+ Commit"); commit.clicked.connect(self.addCommitRequested)
        pr = QPushButton("+ Pull Request"); pr.clicked.connect(self.addPullRequestRequested); refs_row.addWidget(commit); refs_row.addWidget(pr); refs_row.addStretch(1); root.addLayout(refs_row)
        self.refs = QListWidget(); self.refs.setMaximumHeight(160); root.addWidget(self.refs)
        remove_ref = QPushButton("Remove selected reference"); remove_ref.clicked.connect(self._remove_external); root.addWidget(remove_ref)

        self.hint = QLabel("Tip: select a diagram node before adding a code link to attach the path to that specific architecture node.")
        self.hint.setWordWrap(True); self.hint.setStyleSheet("font-size: 11px;"); root.addWidget(self.hint)

    @staticmethod
    def _section(text: str) -> QLabel:
        label = QLabel(text); label.setStyleSheet("font-size: 13px; font-weight: 700; margin-top: 5px;"); return label

    def set_kind(self, kind: str) -> None:
        idx = self.kind.findData(kind); self.kind.blockSignals(True); self.kind.setCurrentIndex(max(0, idx)); self.kind.blockSignals(False)

    def set_repository(self, repo: Repository | None) -> None:
        if repo is None:
            self.repo_label.setText("No repository attached to this project."); return
        parts = []
        if repo.local_path: parts.append(f"Local: {repo.local_path}")
        if repo.github_full_name: parts.append(f"GitHub: {repo.github_full_name}")
        branch = repo.default_branch or "unknown branch"
        self.repo_label.setText(("  •  ".join(parts) if parts else "Repository") + f"  •  {branch}")

    def set_data(self, links: list[ResourceLink], refs: list[ExternalRef]) -> None:
        self.resources.clear(); needs_review = False
        for link in links:
            scope = "Diagram node" if link.diagram_item_id else "Document"
            baseline = (link.baseline_sha or "—")[:10]
            status = "⚠ Needs Review" if link.needs_review else "✓ Current"
            needs_review = needs_review or link.needs_review
            label = link.display_label or link.resource_value or "Repository"
            item = QTreeWidgetItem([label, scope, baseline, status]); item.setData(0, Qt.ItemDataRole.UserRole, link.id)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, link.resource_value); self.resources.addTopLevelItem(item)
        if not links: self.status.setText("No linked code")
        elif needs_review: self.status.setText("⚠ Needs Review — linked code changed")
        else: self.status.setText("✓ Current — linked code unchanged since review")
        self.review.setEnabled(bool(links))

        self.refs.clear()
        for ref in refs:
            prefix = {"pull_request": "PR", "commit": "Commit", "branch": "Branch"}.get(ref.ref_type, ref.ref_type)
            text = f"{prefix} {ref.ref_value} — {ref.title}" if ref.title else f"{prefix} {ref.ref_value}"
            item = QListWidgetItem(text); item.setData(Qt.ItemDataRole.UserRole, ref.id); self.refs.addItem(item)

    def _remove_resource(self) -> None:
        item = self.resources.currentItem()
        if item: self.removeResourceRequested.emit(int(item.data(0, Qt.ItemDataRole.UserRole)))

    def _remove_external(self) -> None:
        item = self.refs.currentItem()
        if item: self.removeExternalRequested.emit(int(item.data(Qt.ItemDataRole.UserRole)))

    def _resource_double_clicked(self, item: QTreeWidgetItem, _column: int) -> None:
        value = str(item.data(0, Qt.ItemDataRole.UserRole + 1) or "")
        if value: self.openResourceRequested.emit(value)

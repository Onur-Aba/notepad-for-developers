from __future__ import annotations

from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.database import Database
from app.i18n import I18n
from app.models import ReviewStatus, ReviewSummary
from app.widgets.diagram_view import DiagramView, DiagramShape, DiagramText, DiagramFreehand
from app.widgets.status_badge import StatusBadge
from app.widgets.resource_history_dialog import ResourceHistoryDialog


class ArchitecturePage(QWidget):
    linkNodeRequested = Signal(int, str)
    viewChangesRequested = Signal(int, str)
    markReviewedRequested = Signal(int, str)

    def __init__(self, database: Database, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.i18n = i18n
        self.project_id: int | None = None
        self.note_id: int | None = None
        self._dirty = False
        self._review_summaries: list[ReviewSummary] = []
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.save)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        self.page_title = QLabel()
        self.page_title.setObjectName("pageTitle")
        self.page_subtitle = QLabel()
        self.page_subtitle.setWordWrap(True)
        self.page_subtitle.setObjectName("pageSubtitle")
        root.addWidget(self.page_title)
        root.addWidget(self.page_subtitle)
        self.help = QLabel()
        self.help.setObjectName("helperBanner")
        self.help.setWordWrap(True)
        root.addWidget(self.help)
        splitter = QSplitter()
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 8, 0)
        self.diagrams_label = QLabel()
        self.diagrams_label.setObjectName("secondaryPanelTitle")
        left_layout.addWidget(self.diagrams_label)
        self.list = QListWidget()
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._show_diagram_menu)
        self.list.currentItemChanged.connect(self._diagram_selected)
        left_layout.addWidget(self.list, 1)
        self.diagram = DiagramView()
        self.diagram.diagramChanged.connect(self._changed)
        self.diagram.scene.selectionChanged.connect(self._selection_changed)
        inspector = QWidget()
        inspector.setObjectName("inspectorPanel")
        inspector.setMinimumWidth(260)
        inspector_layout = QVBoxLayout(inspector)
        self.inspector_title = QLabel()
        self.inspector_title.setObjectName("sectionTitle")
        self.node_name = QLabel()
        self.node_name.setObjectName("cardTitle")
        self.status = StatusBadge()
        self.links = QLabel()
        self.links.setWordWrap(True)
        self.links.setObjectName("mutedText")
        self.changes_summary = QLabel()
        self.changes_summary.setWordWrap(True)
        self.changes_summary.setObjectName("mutedText")
        self.link_button = QPushButton()
        self.link_button.clicked.connect(self._emit_link)
        self.changes_button = QPushButton()
        self.changes_button.clicked.connect(self._emit_changes)
        self.review_button = QPushButton()
        self.review_button.clicked.connect(self._emit_review)
        self.history_button = QPushButton()
        self.history_button.clicked.connect(self._show_history)
        inspector_layout.addWidget(self.inspector_title)
        inspector_layout.addWidget(self.node_name)
        inspector_layout.addWidget(self.status)
        inspector_layout.addWidget(self.links)
        inspector_layout.addWidget(self.changes_summary)
        inspector_layout.addWidget(self.link_button)
        inspector_layout.addWidget(self.changes_button)
        inspector_layout.addWidget(self.review_button)
        inspector_layout.addWidget(self.history_button)
        inspector_layout.addStretch(1)
        splitter.addWidget(left)
        splitter.addWidget(self.diagram)
        splitter.addWidget(inspector)
        splitter.setSizes([220, 760, 280])
        root.addWidget(splitter, 1)
        self.i18n.languageChanged.connect(lambda _language: self.retranslate_ui())
        self.retranslate_ui()
        self._selection_changed()

    def retranslate_ui(self) -> None:
        self.page_title.setText(self.i18n.t("architecture.title"))
        self.page_subtitle.setText(self.i18n.t("architecture.subtitle"))
        self.help.setText(
            "Bir kutuyu seçin ve 'Kod bağla' deyin. Örneğin 'Authentication' kutusunu backend/auth/ klasörüne bağlarsanız, o klasör değiştiğinde DevNest kutuyu yeniden kontrol etmeniz gerektiğini gösterebilir."
            if self.i18n.language == "tr" else
            "Select a box and use 'Connect code'. For example, connect an Authentication box to backend/auth/ and DevNest can tell you when that area changed after your last check."
        )
        self.diagrams_label.setText(self.i18n.t("architecture.diagrams"))
        self.inspector_title.setText(self.i18n.t("architecture.inspector"))
        self.link_button.setText(self.i18n.t("architecture.link"))
        self.changes_button.setText(self.i18n.t("architecture.view"))
        self.review_button.setText(self.i18n.t("architecture.review"))
        self.history_button.setText("Geçmiş" if self.i18n.language == "tr" else "History")
        self.link_button.setToolTip(self.i18n.t("tip.notes.link"))
        self.changes_button.setToolTip(self.i18n.t("tip.notes.changes"))
        self.review_button.setToolTip(self.i18n.t("tip.notes.review"))
        self.history_button.setToolTip("Seçili mimari öğesinin review geçmişini gösterir." if self.i18n.language == "tr" else "Show review history for the selected architecture node.")
        self._selection_changed()

    def set_project(self, project_id: int) -> None:
        self.save()
        self.project_id = project_id
        self.note_id = None
        self.refresh()

    def refresh(self) -> None:
        self.list.blockSignals(True)
        self.list.clear()
        notes = self.database.list_diagram_notes(self.project_id)
        for note in notes:
            item = QListWidgetItem(note.title)
            item.setData(Qt.ItemDataRole.UserRole, note.id)
            self.list.addItem(item)
        self.list.blockSignals(False)
        if self.list.count():
            self.list.setCurrentRow(0)
        else:
            self.diagram.load_data({"items": [], "edges": [], "paths": []})
            self.note_id = None

    def _show_diagram_menu(self, pos) -> None:
        item = self.list.itemAt(pos)
        if item is None:
            return
        note_id = int(item.data(Qt.ItemDataRole.UserRole))
        note = self.database.get_note(note_id)
        if note is None:
            return
        tr = self.i18n.language == "tr"
        menu = QMenu(self)
        rename = menu.addAction("Mimari adını değiştir…" if tr else "Rename architecture…")
        delete = menu.addAction("Mimari diyagramını sil…" if tr else "Delete architecture diagram…")
        chosen = menu.exec(self.list.mapToGlobal(pos))
        if chosen == rename:
            title, ok = QInputDialog.getText(
                self, "Mimari adını değiştir" if tr else "Rename architecture",
                "Yeni ad:" if tr else "New name:", text=note.title,
            )
            if ok and title.strip():
                self.database.rename_note(note_id, title.strip())
                self.refresh()
        elif chosen == delete:
            answer = QMessageBox.question(
                self, "Mimari diyagramını sil" if tr else "Delete architecture diagram",
                (
                    f'“{note.title}” için çizilen diyagram silinsin mi?\n\nNotun yazılı içeriği silinmez. Diyagram kutularına ait DevNest kod bağlantıları kaldırılır.'
                    if tr else
                    f'Delete the diagram drawn for “{note.title}”?\n\nThe note text is preserved. DevNest code links attached to diagram nodes are removed.'
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if answer == QMessageBox.StandardButton.Yes:
                self.save()
                self.database.delete_diagram(note_id)
                self.note_id = None
                self.refresh()

    def _diagram_selected(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        self.save()
        if current is None:
            return
        self.note_id = int(current.data(Qt.ItemDataRole.UserRole))
        note = self.database.get_note(self.note_id)
        if note:
            self.database.touch_recent("architecture", self.note_id, note.title, note.project_id)
        self.diagram.load_data(self.database.get_diagram(self.note_id))
        self._dirty = False
        self._apply_canvas_statuses()
        self._selection_changed()

    def _changed(self) -> None:
        if self.note_id is None:
            return
        self._dirty = True
        self.timer.start(750)

    def save(self) -> None:
        self.timer.stop()
        if self._dirty and self.note_id is not None:
            self.database.save_diagram(self.note_id, self.diagram.to_data())
            self._dirty = False

    def selected_item_id(self) -> str | None:
        selected = self.diagram.scene.selectedItems()
        if not selected:
            return None
        item = selected[0]
        return getattr(item, "item_id", None)

    def _selection_changed(self) -> None:
        item_id = self.selected_item_id()
        enabled = bool(item_id and self.note_id)
        self.link_button.setEnabled(enabled)
        self.changes_button.setEnabled(enabled)
        self.review_button.setEnabled(enabled)
        self.history_button.setEnabled(enabled)
        if not enabled:
            self.node_name.setText(self.i18n.t("architecture.select"))
            self.links.setText(self.i18n.t("architecture.links") + "\n" + self.i18n.t("architecture.none"))
            self.changes_summary.setText(self.i18n.t("architecture.changes") + "\n" + self.i18n.t("architecture.no_compare"))
            self.status.set_status(ReviewStatus.NOT_REVIEWED)
            return
        selected = self.diagram.scene.selectedItems()[0]
        text = getattr(selected, "text", None)
        if callable(text):
            text = text()
        if not isinstance(text, str):
            text = getattr(selected, "toPlainText", lambda: "Architecture item")()
        self.node_name.setText(text or ("Mimari öğesi" if self.i18n.language == "tr" else "Architecture item"))
        links = self.database.list_resource_links("diagram_item", item_id, self.note_id)
        self.links.setText(self.i18n.t("architecture.links") + "\n" + ("\n".join(link.target_value or self.i18n.t("resources.repo") for link in links) if links else self.i18n.t("architecture.none")))
        matches = self._matching_summaries(item_id)
        status = self._aggregate_status(matches, bool(links))
        self.status.set_status(status)
        if matches:
            preferred = next((summary for summary in matches if summary.status == ReviewStatus.NEEDS_REVIEW), matches[0])
            changed = preferred.linked_changed_files
            lines = [f"{self.i18n.t('architecture.changes')}\n{len(changed)} " + ("bağlı dosya · " if self.i18n.language == "tr" else "linked files · ") + f"{preferred.commit_count} commits"]
            lines.extend(file.path for file in changed[:6])
            if len(changed) > 6:
                lines.append((f"+ {len(changed) - 6} daha" if self.i18n.language == "tr" else f"+ {len(changed) - 6} more"))
            self.changes_summary.setText("\n".join(lines))
        else:
            self.changes_summary.setText(self.i18n.t("architecture.changes") + "\n" + self.i18n.t("architecture.no_compare"))

    def set_review_summaries(self, summaries: list[ReviewSummary]) -> None:
        self._review_summaries = [summary for summary in summaries if summary.resource_link.resource_type == "diagram_item"]
        self._apply_canvas_statuses()
        self._selection_changed()

    def _matching_summaries(self, item_id: str) -> list[ReviewSummary]:
        parent = "" if self.note_id is None else str(self.note_id)
        return [
            summary for summary in self._review_summaries
            if summary.resource_link.resource_id == str(item_id)
            and summary.resource_link.resource_parent_id == parent
        ]

    @staticmethod
    def _aggregate_status(summaries: list[ReviewSummary], has_links: bool = True) -> ReviewStatus:
        if not summaries:
            return ReviewStatus.NOT_REVIEWED if has_links else ReviewStatus.NOT_REVIEWED
        for status in (ReviewStatus.NEEDS_REVIEW, ReviewStatus.CANNOT_COMPARE, ReviewStatus.NOT_REVIEWED, ReviewStatus.CURRENT):
            if any(summary.status == status for summary in summaries):
                return status
        return ReviewStatus.NOT_REVIEWED

    def _apply_canvas_statuses(self) -> None:
        if self.note_id is None:
            self.diagram.set_review_statuses({})
            return
        parent = str(self.note_id)
        grouped: dict[str, list[ReviewSummary]] = {}
        for summary in self._review_summaries:
            if summary.resource_link.resource_parent_id == parent:
                grouped.setdefault(summary.resource_link.resource_id, []).append(summary)
        self.diagram.set_review_statuses({item_id: self._aggregate_status(values).value for item_id, values in grouped.items()})

    def _emit_link(self) -> None:
        item_id = self.selected_item_id()
        if item_id and self.note_id:
            self.linkNodeRequested.emit(self.note_id, item_id)

    def _emit_changes(self) -> None:
        item_id = self.selected_item_id()
        if item_id and self.note_id:
            self.viewChangesRequested.emit(self.note_id, item_id)

    def _emit_review(self) -> None:
        item_id = self.selected_item_id()
        if item_id and self.note_id:
            self.markReviewedRequested.emit(self.note_id, item_id)

    def _show_history(self) -> None:
        item_id = self.selected_item_id()
        if item_id and self.note_id:
            ResourceHistoryDialog(self.database, "diagram_item", item_id, self.note_id, self.i18n, self).exec()

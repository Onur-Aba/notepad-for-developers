from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QInputDialog, QLabel, QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget

from app.database import Database, DatabaseError
from app.dialogs.project_delete import DeleteProjectDialog
from app.i18n import I18n
from app.services.project_service import ProjectService
from app.services.repository_service import RepositoryService
from app.widgets.project_wizard import CreateProjectWizard


class ProjectsPage(QWidget):
    projectOpened = Signal(int)
    projectsChanged = Signal()
    localRepositoryRequested = Signal(int, str)

    def __init__(self, database: Database, project_service: ProjectService,
                 repository_service: RepositoryService, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.project_service = project_service
        self.repository_service = repository_service
        self.i18n = i18n
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 28, 30, 24)
        root.setSpacing(12)
        header = QHBoxLayout()
        titles = QVBoxLayout()
        self.title = QLabel()
        self.title.setObjectName("pageTitle")
        self.subtitle = QLabel()
        self.subtitle.setWordWrap(True)
        self.subtitle.setObjectName("pageSubtitle")
        titles.addWidget(self.title)
        titles.addWidget(self.subtitle)
        self.create_button = QPushButton()
        self.create_button.setObjectName("primaryButton")
        self.create_button.clicked.connect(self.create_project)
        header.addLayout(titles, 1)
        header.addWidget(self.create_button)
        root.addLayout(header)

        self.help = QLabel()
        self.help.setObjectName("helperBanner")
        self.help.setWordWrap(True)
        root.addWidget(self.help)

        self.container = QWidget()
        self.cards = QVBoxLayout(self.container)
        self.cards.setContentsMargins(0, 4, 0, 0)
        self.cards.setSpacing(10)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(self.container)
        root.addWidget(scroll, 1)
        self.i18n.languageChanged.connect(lambda _language: self.retranslate_ui())
        self.retranslate_ui()
        self.refresh()

    def retranslate_ui(self) -> None:
        self.title.setText(self.i18n.t("projects.title"))
        self.subtitle.setText(self.i18n.t("projects.subtitle"))
        self.create_button.setText(self.i18n.t("projects.create"))
        self.create_button.setToolTip(self.i18n.t("tip.projects.create"))
        self.help.setText(
            "Bir proje = bir ürün veya kod tabanı. Önce projeyi açın; sonra not, karar ve depo bağlantılarını o projenin içinde tutun."
            if self.i18n.language == "tr" else
            "One project = one product or codebase. Open the project first, then keep its notes, decisions and repository connections inside it."
        )
        self.refresh()

    def refresh(self) -> None:
        while self.cards.count():
            item = self.cards.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        projects = self.database.list_project_summaries()
        if not projects:
            empty = QLabel(self.i18n.t("projects.empty"))
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setWordWrap(True)
            empty.setObjectName("emptyState")
            self.cards.addWidget(empty, 1)
            return
        for project in projects:
            frame = QFrame()
            frame.setObjectName("projectCard")
            row = QHBoxLayout(frame)
            row.setContentsMargins(16, 14, 14, 14)
            text = QVBoxLayout()
            text.setSpacing(5)
            name = QLabel(project.name)
            name.setObjectName("cardTitle")
            desc = QLabel(project.description or self.i18n.t("projects.no_description"))
            desc.setWordWrap(True)
            desc.setObjectName("mutedText")
            counts = QLabel(
                f"{project.repository_count} {self.i18n.t('projects.repositories')}   ·   "
                f"{project.note_count} {self.i18n.t('projects.notes')}   ·   "
                f"{project.decision_count} {self.i18n.t('projects.decisions')}   ·   "
                f"{project.diagram_count} {self.i18n.t('projects.diagrams')}"
            )
            counts.setObjectName("projectMeta")
            text.addWidget(name)
            text.addWidget(desc)
            text.addWidget(counts)
            favorite = QPushButton("★" if self.database.is_favorite("project", project.id) else "☆")
            favorite.setFixedWidth(42)
            favorite.setToolTip("Projeyi favorilerde üstte tut." if self.i18n.language == "tr" else "Keep this project at the top of favorites.")
            favorite.clicked.connect(lambda _checked=False, pid=project.id: self._toggle_favorite(pid))
            open_button = QPushButton(self.i18n.t("projects.open"))
            open_button.setObjectName("primaryButton")
            open_button.setToolTip(self.i18n.t("tip.projects.open"))
            open_button.clicked.connect(lambda _checked=False, pid=project.id: self.projectOpened.emit(pid))
            edit = QPushButton("Düzenle" if self.i18n.language == "tr" else "Edit")
            edit.setToolTip(
                "Projenin adını ve açıklamasını değiştirir. Notlar, kararlar ve depo bağlantıları aynı kalır."
                if self.i18n.language == "tr" else
                "Change the project name and description. Notes, decisions and repository connections stay the same."
            )
            edit.clicked.connect(lambda _checked=False, pid=project.id: self._edit_project(pid))
            archive = QPushButton(self.i18n.t("projects.archive"))
            archive.setToolTip(self.i18n.t("tip.projects.archive"))
            archive.clicked.connect(lambda _checked=False, pid=project.id, n=project.name: self._archive(pid, n))
            delete = QPushButton("Sil" if self.i18n.language == "tr" else "Delete")
            delete.setObjectName("dangerButton")
            delete.setToolTip(
                "Projeyi ve bu projeye ait DevNest içeriğini Çöp Kutusu'na taşır. İki ayrı doğrulama adımı vardır; işlem hemen kalıcı silme yapmaz."
                if self.i18n.language == "tr" else
                "Move the project and its DevNest contents to Trash. There are two confirmation steps; this does not permanently delete immediately."
            )
            delete.clicked.connect(lambda _checked=False, pid=project.id: self._delete_project(pid))
            row.addLayout(text, 1)
            row.addWidget(favorite)
            row.addWidget(open_button)
            row.addWidget(edit)
            row.addWidget(archive)
            row.addWidget(delete)
            self.cards.addWidget(frame)
        self.cards.addStretch(1)

    def _toggle_favorite(self, project_id: int) -> None:
        favorite = not self.database.is_favorite("project", project_id)
        self.database.set_favorite("project", project_id, favorite, project_id)
        self.refresh()
        self.projectsChanged.emit()

    def create_project(self) -> None:
        # Existing wizard is intentionally preserved for compatibility.
        wizard = CreateProjectWizard(self.database, self.i18n, self)
        if wizard.exec() != QDialog.DialogCode.Accepted:
            return
        values = wizard.values()
        try:
            project = self.project_service.create(str(values["name"]), str(values["description"]))
            mode = str(values["mode"])
            github_id = values["github_repository_id"]
            if github_id is not None and mode in {"github", "both"}:
                repo = self.database.get_repository(int(github_id))
                if repo:
                    self.database.link_repository_to_project(project.id, repo.id, repo.default_branch)
            local_path = str(values["local_path"] or "")
            if local_path and mode in {"local", "both"}:
                self.localRepositoryRequested.emit(project.id, local_path)
            self.refresh()
            self.projectsChanged.emit()
            self.projectOpened.emit(project.id)
        except DatabaseError as exc:
            QMessageBox.critical(self, "Proje Oluşturulamadı" if self.i18n.language == "tr" else "Create Project Failed", str(exc))

    def _edit_project(self, project_id: int) -> None:
        project = self.database.get_project(project_id)
        if project is None:
            return
        tr = self.i18n.language == "tr"
        name, ok = QInputDialog.getText(
            self, "Projeyi düzenle" if tr else "Edit project",
            "Proje adı:" if tr else "Project name:", text=project.name,
        )
        if not ok or not name.strip():
            return
        description, ok = QInputDialog.getText(
            self, "Projeyi düzenle" if tr else "Edit project",
            "Kısa açıklama:" if tr else "Short description:", text=project.description,
        )
        if not ok:
            return
        try:
            self.project_service.rename(project_id, name.strip(), description.strip())
        except DatabaseError as exc:
            QMessageBox.critical(self, "Proje Güncellenemedi" if tr else "Update Project Failed", str(exc))
            return
        self.refresh()
        self.projectsChanged.emit()

    def _archive(self, project_id: int, name: str) -> None:
        if self.i18n.language == "tr":
            title = "Projeyi Arşivle"
            text = f'"{name}" projesi arşivlensin mi? Notlar, kararlar ve depo bilgileri silinmez.'
        else:
            title = "Archive Project"
            text = f'Archive "{name}"? Notes, decisions and repository data will be preserved.'
        answer = QMessageBox.question(
            self, title, text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.project_service.archive(project_id)
            self.refresh()
            self.projectsChanged.emit()
    def _delete_project(self, project_id: int) -> None:
        project = self.database.get_project(project_id)
        if project is None:
            return
        try:
            dialog = DeleteProjectDialog(self.database, project_id, self.i18n, self)
        except (DatabaseError, ValueError) as exc:
            QMessageBox.critical(
                self, "Proje Silinemedi" if self.i18n.language == "tr" else "Delete Project Failed", str(exc)
            )
            return
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.project_service.move_to_trash(project_id)
        except DatabaseError as exc:
            QMessageBox.critical(
                self, "Proje Silinemedi" if self.i18n.language == "tr" else "Delete Project Failed", str(exc)
            )
            return
        self.refresh()
        self.projectsChanged.emit()


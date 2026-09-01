from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.database import Database
from app.i18n import I18n


class DeleteProjectDialog(QDialog):
    """Two-step destructive confirmation for moving a whole project to Trash."""

    def __init__(self, database: Database, project_id: int, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.project_id = project_id
        self.i18n = i18n
        project = database.get_project(project_id)
        if project is None:
            raise ValueError("Project not found")
        self.project = project
        self.details = database.project_trash_contents(project_id)
        self.setObjectName("projectDeleteDialog")
        self.setModal(True)
        self.setWindowTitle("Projeyi Sil" if self._tr else "Delete Project")
        self.setMinimumWidth(620)
        self.resize(680, 500)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(16)

        title = QLabel("Projeyi çöp kutusuna taşı" if self._tr else "Move project to Trash")
        title.setObjectName("dialogTitle")
        root.addWidget(title)

        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)
        self.stack.addWidget(self._build_first_step())
        self.stack.addWidget(self._build_name_step())

        bottom = QHBoxLayout()
        self.cancel = QPushButton("İptal" if self._tr else "Cancel")
        self.cancel.clicked.connect(self.reject)
        bottom.addStretch(1)
        bottom.addWidget(self.cancel)
        root.addLayout(bottom)

    @property
    def _tr(self) -> bool:
        return self.i18n.language == "tr"

    def _build_first_step(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        warning = QFrame()
        warning.setObjectName("dangerPanel")
        warning_layout = QVBoxLayout(warning)
        warning_layout.setContentsMargins(16, 14, 16, 14)
        warning_layout.setSpacing(7)
        headline = QLabel(
            f'“{self.project.name}” projesinin tamamını silmek üzeresiniz.'
            if self._tr else
            f'You are about to delete the entire “{self.project.name}” project.'
        )
        headline.setObjectName("cardTitle")
        headline.setWordWrap(True)
        explanation = QLabel(
            "Bu işlem projeyi hemen kalıcı olarak yok etmez. Proje; notları, kararları, mimari diyagramları, kod bağlantıları ve depo eşleştirmeleriyle birlikte Çöp Kutusu'na taşınır. Çöp Kutusu'ndan geri yükleyebilirsiniz."
            if self._tr else
            "This does not immediately destroy the project. The project, its notes, decisions, architecture diagrams, code links and repository mappings move to Trash together and can be restored from there."
        )
        explanation.setWordWrap(True)
        explanation.setObjectName("mutedText")
        warning_layout.addWidget(headline)
        warning_layout.addWidget(explanation)
        layout.addWidget(warning)

        counts = self.details
        summary = QLabel(
            (
                f"Taşınacak içerik: {len(counts['notes'])} not · {len(counts['decisions'])} karar · "
                f"{len(counts['diagrams'])} diyagram · {len(counts['repositories'])} depo bağlantısı · "
                f"{counts['resource_links']} kod bağlantısı"
            )
            if self._tr else
            (
                f"Contents: {len(counts['notes'])} notes · {len(counts['decisions'])} decisions · "
                f"{len(counts['diagrams'])} diagrams · {len(counts['repositories'])} repository links · "
                f"{counts['resource_links']} code links"
            )
        )
        summary.setObjectName("helperBanner")
        summary.setWordWrap(True)
        layout.addWidget(summary)

        instruction = QLabel(
            "Devam etmek istiyorsanız önce aşağıdaki onay düğmesine basın. Sonraki adımda proje adını aynen yazmanız istenecek."
            if self._tr else
            "If you want to continue, press the confirmation button below. On the next step you must type the project name exactly."
        )
        instruction.setWordWrap(True)
        layout.addWidget(instruction)
        layout.addStretch(1)

        confirm = QPushButton("Evet, onaylıyorum" if self._tr else "Yes, I understand")
        confirm.setObjectName("dangerButton")
        confirm.setToolTip(
            "Bu düğme henüz hiçbir şeyi silmez; sadece ikinci doğrulama adımına geçer."
            if self._tr else
            "This button does not delete anything yet; it only opens the second confirmation step."
        )
        confirm.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        layout.addWidget(confirm, 0, Qt.AlignmentFlag.AlignRight)
        return page

    def _build_name_step(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        label = QLabel(
            "Son doğrulama: yanlış projeyi silmemek için proje adını aşağıdaki alana aynen yazın."
            if self._tr else
            "Final confirmation: type the project name exactly below so the wrong project is not deleted."
        )
        label.setWordWrap(True)
        label.setObjectName("helperBanner")
        layout.addWidget(label)

        expected = QLabel(self.project.name)
        expected.setObjectName("confirmationProjectName")
        expected.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(expected)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(self.project.name)
        self.name_edit.setMinimumHeight(40)
        self.name_edit.textChanged.connect(self._typed_name_changed)
        layout.addWidget(self.name_edit)

        self.match_hint = QLabel(
            "Sil düğmesi, proje adı birebir eşleştiğinde etkinleşir."
            if self._tr else
            "The delete button becomes available only when the project name matches exactly."
        )
        self.match_hint.setObjectName("mutedText")
        self.match_hint.setWordWrap(True)
        layout.addWidget(self.match_hint)
        layout.addStretch(1)

        buttons = QHBoxLayout()
        back = QPushButton("← Geri" if self._tr else "← Back")
        back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.delete_button = QPushButton("Projeyi Çöp Kutusuna Taşı" if self._tr else "Move Project to Trash")
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self.accept)
        buttons.addWidget(back)
        buttons.addStretch(1)
        buttons.addWidget(self.delete_button)
        layout.addLayout(buttons)
        return page

    def _typed_name_changed(self, value: str) -> None:
        matches = value == self.project.name
        self.delete_button.setEnabled(matches)
        if matches:
            self.match_hint.setText(
                "Proje adı eşleşti. Sil düğmesine basarsanız proje ve içeriği Çöp Kutusu'na taşınacak."
                if self._tr else
                "The project name matches. Pressing delete now moves the project and its contents to Trash."
            )
        else:
            self.match_hint.setText(
                "Proje adını büyük/küçük harfler dahil aynen yazın."
                if self._tr else
                "Type the project name exactly, including capitalization."
            )

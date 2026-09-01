from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.database import Database
from app.i18n import I18n


class CreateProjectWizard(QDialog):
    """Theme-native two-step project creation dialog.

    QWizard uses platform-owned header/page surfaces that can ignore application
    palettes on Windows. A small QDialog + QStackedWidget keeps every pixel under
    DevNest's theme while preserving the same two-step workflow and public API.
    """

    def __init__(self, database: Database, i18n: I18n | None = None, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.i18n = i18n
        self._step = 0
        self.setObjectName("projectWizard")
        self.setModal(True)
        self.setWindowTitle("Proje Oluştur" if self._tr else "Create Project")
        self.setMinimumSize(680, 520)
        self.resize(760, 580)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(14)

        top = QHBoxLayout()
        title_box = QVBoxLayout()
        self.title = QLabel("Proje Oluştur" if self._tr else "Create Project")
        self.title.setObjectName("dialogTitle")
        self.step_label = QLabel()
        self.step_label.setObjectName("mutedText")
        title_box.addWidget(self.title)
        title_box.addWidget(self.step_label)
        top.addLayout(title_box)
        top.addStretch(1)
        root.addLayout(top)

        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)
        self.stack.addWidget(self._build_info_page())
        self.stack.addWidget(self._build_repository_page())

        footer = QHBoxLayout()
        self.back_button = QPushButton("← Geri" if self._tr else "← Back")
        self.next_button = QPushButton("İleri →" if self._tr else "Next →")
        self.next_button.setObjectName("primaryButton")
        self.cancel_button = QPushButton("İptal" if self._tr else "Cancel")
        self.back_button.clicked.connect(self._back)
        self.next_button.clicked.connect(self._next_or_finish)
        self.cancel_button.clicked.connect(self.reject)
        footer.addWidget(self.back_button)
        footer.addStretch(1)
        footer.addWidget(self.cancel_button)
        footer.addWidget(self.next_button)
        root.addLayout(footer)
        self._sync_step_ui()

    @property
    def _tr(self) -> bool:
        return bool(self.i18n and self.i18n.language == "tr")

    def _build_info_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("dialogPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(14)

        help_box = QLabel(
            "Bir proje; aynı ürün veya kod tabanına ait notları, kararları, mimariyi ve depoları bir arada tutar. Örneğin ayrı ürünleriniz varsa her biri için ayrı proje oluşturun."
            if self._tr else
            "A project keeps notes, decisions, architecture and repositories for one product or codebase together. If you have separate products, create a separate project for each one."
        )
        help_box.setWordWrap(True)
        help_box.setObjectName("helperBanner")
        layout.addWidget(help_box)

        card = QFrame()
        card.setObjectName("dialogCard")
        form = QFormLayout(card)
        form.setContentsMargins(18, 18, 18, 18)
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(16)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.name = QLineEdit()
        self.name.setMinimumHeight(40)
        self.name.setPlaceholderText("Payment API")
        self.name.setToolTip(
            "Projeyi tanıyacağınız kısa bir ad yazın. Örneğin ürün, servis veya uygulama adı."
            if self._tr else
            "Use a short name you will recognize, such as the product, service or app name."
        )
        self.description = QLineEdit()
        self.description.setMinimumHeight(40)
        self.description.setPlaceholderText("İsteğe bağlı kısa açıklama" if self._tr else "Optional short description")
        form.addRow("Proje adı" if self._tr else "Project name", self.name)
        form.addRow("Açıklama" if self._tr else "Description", self.description)
        layout.addWidget(card)
        layout.addStretch(1)
        return page

    def _build_repository_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("dialogPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(14)

        explainer = QLabel(
            "Depo bağlamak zorunlu değil. Bağlarsanız DevNest, not ve kararların hangi koda ait olduğunu izleyebilir. Yerel Git klasörü çevrimdışı çalışır; GitHub bağlantısı ise uzak depo ve commit bilgilerini okur."
            if self._tr else
            "Connecting a repository is optional. When connected, DevNest can track which code belongs to notes and decisions. A local Git folder works offline; GitHub provides remote repository and commit information."
        )
        explainer.setWordWrap(True)
        explainer.setObjectName("helperBanner")
        layout.addWidget(explainer)

        card = QFrame()
        card.setObjectName("dialogCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(12)
        self.none = QRadioButton("Şimdilik depo bağlama" if self._tr else "Create without a repository for now")
        self.local = QRadioButton("Bilgisayarımdaki Git klasörünü bağla" if self._tr else "Connect a local Git repository")
        self.github = QRadioButton("GitHub'daki bir depoyu bağla" if self._tr else "Connect a GitHub repository")
        self.both = QRadioButton("Yerel klasör + GitHub deposunu birlikte bağla" if self._tr else "Connect both local Git and GitHub")
        self.none.setChecked(True)
        for radio in (self.none, self.local, self.github, self.both):
            radio.setMinimumHeight(30)
            card_layout.addWidget(radio)

        local_row = QHBoxLayout()
        self.local_path = QLineEdit()
        self.local_path.setMinimumHeight(40)
        self.local_path.setPlaceholderText(r"C:\Projects\payment-api")
        browse = QPushButton("Klasör seç…" if self._tr else "Choose folder…")
        browse.setMinimumHeight(40)
        browse.setToolTip(
            "Bilgisayarınızdaki Git proje klasörünü seçin. DevNest bu klasöre kod yazmaz."
            if self._tr else
            "Choose the Git project folder on your computer. DevNest does not write code into this folder."
        )
        browse.clicked.connect(self._browse)
        local_row.addWidget(self.local_path, 1)
        local_row.addWidget(browse)
        card_layout.addLayout(local_row)

        self.github_repo = QComboBox()
        self.github_repo.setMinimumHeight(40)
        self.github_repo.addItem("GitHub deposu seç…" if self._tr else "Choose a GitHub repository…", None)
        for repo in self.database.list_repositories():
            if repo.github_repo_id is not None and repo.full_name:
                self.github_repo.addItem(repo.full_name, repo.id)
        self.github_repo.setToolTip(
            "GitHub Depoları sayfasında DevNest'e okuma izni verdiğiniz depolardan birini seçin."
            if self._tr else
            "Choose one of the repositories you allowed DevNest to read on the GitHub Repositories page."
        )
        card_layout.addWidget(self.github_repo)
        layout.addWidget(card)
        layout.addStretch(1)
        return page

    def _sync_step_ui(self) -> None:
        self.stack.setCurrentIndex(self._step)
        self.back_button.setEnabled(self._step > 0)
        self.step_label.setText(
            (f"Adım {self._step + 1} / 2" if self._tr else f"Step {self._step + 1} of 2")
        )
        self.next_button.setText(
            ("Projeyi Oluştur" if self._tr else "Create Project")
            if self._step == 1 else
            ("İleri →" if self._tr else "Next →")
        )

    def _back(self) -> None:
        if self._step > 0:
            self._step -= 1
            self._sync_step_ui()

    def _next_or_finish(self) -> None:
        if self._step == 0:
            if not self.name.text().strip():
                QMessageBox.warning(
                    self,
                    "Proje Adı Gerekli" if self._tr else "Project Name Required",
                    "Proje adı boş olamaz." if self._tr else "Project name cannot be empty.",
                )
                self.name.setFocus()
                return
            self._step = 1
            self._sync_step_ui()
            return

        if (self.local.isChecked() or self.both.isChecked()) and not self.local_path.text().strip():
            QMessageBox.warning(
                self,
                "Yerel Depo Gerekli" if self._tr else "Local Repository Required",
                "Bilgisayarınızdaki Git klasörünü seçin." if self._tr else "Select a local Git repository.",
            )
            return
        if (self.github.isChecked() or self.both.isChecked()) and self.github_repo.currentData() is None:
            QMessageBox.warning(
                self,
                "GitHub Deposu Gerekli" if self._tr else "GitHub Repository Required",
                "Erişilebilen bir GitHub deposu seçin." if self._tr else "Select an accessible GitHub repository.",
            )
            return
        self.accept()

    def _browse(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Yerel Git Deposunu Seç" if self._tr else "Select Local Git Repository"
        )
        if path:
            self.local_path.setText(path)
            if self.none.isChecked():
                self.local.setChecked(True)

    def values(self) -> dict[str, object]:
        mode = "none"
        if self.local.isChecked():
            mode = "local"
        elif self.github.isChecked():
            mode = "github"
        elif self.both.isChecked():
            mode = "both"
        return {
            "name": self.name.text().strip(),
            "description": self.description.text().strip(),
            "mode": mode,
            "local_path": self.local_path.text().strip(),
            "github_repository_id": self.github_repo.currentData(),
        }

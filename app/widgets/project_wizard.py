from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWizard,
    QWizardPage,
)

from app.database import Database
from app.i18n import I18n


class CreateProjectWizard(QWizard):
    def __init__(self, database: Database, i18n: I18n | None = None, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.i18n = i18n
        tr = bool(i18n and i18n.language == "tr")
        self.setWindowTitle("Proje Oluştur" if tr else "Create Project")
        self.setMinimumWidth(610)

        info = QWizardPage()
        info.setTitle("Proje Oluştur" if tr else "Create Project")
        info.setSubTitle(
            "Bir proje, aynı ürün veya kod tabanına ait notları, kararları, mimariyi ve depoları bir arada tutar."
            if tr else
            "A project keeps notes, decisions, architecture and repositories for one product or codebase together."
        )
        form = QFormLayout(info)
        self.name = QLineEdit()
        self.name.setPlaceholderText("Payment API")
        self.name.setToolTip("Projeyi tanıyacağınız kısa bir ad yazın. Örneğin ürün veya servis adı." if tr else "Use a short name you will recognize, such as the product or service name.")
        self.description = QLineEdit()
        self.description.setPlaceholderText("İsteğe bağlı kısa açıklama" if tr else "Optional short description")
        form.addRow("Proje adı" if tr else "Project name", self.name)
        form.addRow("Açıklama" if tr else "Description", self.description)
        self.addPage(info)

        repo_page = QWizardPage()
        repo_page.setTitle("Kod Deposu" if tr else "Code Repository")
        repo_page.setSubTitle(
            "Şimdi bağlamak zorunda değilsiniz. Depo bağlamak, DevNest'in not ve kararların hangi koda ait olduğunu takip etmesini sağlar."
            if tr else
            "You can skip this for now. Connecting a repository lets DevNest understand which code your notes and decisions belong to."
        )
        layout = QVBoxLayout(repo_page)
        explainer = QLabel(
            "Yerel depo = bilgisayarınızdaki Git klasörü. GitHub deposu = GitHub'da DevNest'e okuma izni verdiğiniz depo. İkisini birlikte bağlamak en kullanışlı seçenektir."
            if tr else
            "Local repository means the Git folder on your computer. GitHub repository means a repository you allowed DevNest to read on GitHub. Connecting both gives the best offline and online experience."
        )
        explainer.setWordWrap(True)
        explainer.setObjectName("helperBanner")
        layout.addWidget(explainer)

        self.none = QRadioButton("Şimdilik depo bağlama" if tr else "Create without a repository for now")
        self.local = QRadioButton("Bilgisayarımdaki Git klasörünü bağla" if tr else "Connect a local Git repository")
        self.github = QRadioButton("GitHub'daki bir depoyu bağla" if tr else "Connect a GitHub repository")
        self.both = QRadioButton("Yerel klasör + GitHub deposunu birlikte bağla" if tr else "Connect both local Git and GitHub")
        self.none.setChecked(True)
        for radio in (self.none, self.local, self.github, self.both):
            layout.addWidget(radio)

        self.local_path = QLineEdit()
        self.local_path.setPlaceholderText(r"C:\Projects\payment-api")
        browse = QPushButton("Klasör seç…" if tr else "Choose folder…")
        browse.setToolTip("Bilgisayarınızdaki .git klasörüne sahip proje klasörünü seçin. DevNest bu klasöre yazma işlemi yapmaz." if tr else "Choose the project folder that contains a Git repository. DevNest will not write to this repository.")
        browse.clicked.connect(self._browse)
        layout.addWidget(self.local_path)
        layout.addWidget(browse)

        self.github_repo = QComboBox()
        self.github_repo.addItem("GitHub deposu seç…" if tr else "Choose a GitHub repository…", None)
        for repo in database.list_repositories():
            if repo.github_repo_id is not None and repo.full_name:
                self.github_repo.addItem(repo.full_name, repo.id)
        self.github_repo.setToolTip("GitHub Depoları sayfasında izin verdiğiniz depolardan birini seçin." if tr else "Choose one of the repositories you allowed on the GitHub Repositories page.")
        layout.addWidget(self.github_repo)
        self.addPage(repo_page)

    def validateCurrentPage(self) -> bool:
        tr = bool(self.i18n and self.i18n.language == "tr")
        if self.currentId() == 0 and not self.name.text().strip():
            QMessageBox.warning(self, "Proje Adı Gerekli" if tr else "Project Name Required", "Proje adı boş olamaz." if tr else "Project name cannot be empty.")
            return False
        if self.currentId() == 1:
            if (self.local.isChecked() or self.both.isChecked()) and not self.local_path.text().strip():
                QMessageBox.warning(self, "Yerel Depo Gerekli" if tr else "Local Repository Required", "Bilgisayarınızdaki Git klasörünü seçin." if tr else "Select a local Git repository.")
                return False
            if (self.github.isChecked() or self.both.isChecked()) and self.github_repo.currentData() is None:
                QMessageBox.warning(self, "GitHub Deposu Gerekli" if tr else "GitHub Repository Required", "Erişilebilen bir GitHub deposu seçin." if tr else "Select an accessible GitHub repository.")
                return False
        return super().validateCurrentPage()

    def _browse(self) -> None:
        tr = bool(self.i18n and self.i18n.language == "tr")
        path = QFileDialog.getExistingDirectory(self, "Yerel Git Deposunu Seç" if tr else "Select Local Git Repository")
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

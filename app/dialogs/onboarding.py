from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.i18n import I18n


class OnboardingDialog(QDialog):
    """Small first-launch tour with a real destination for every step."""

    navigateRequested = Signal(str)

    def __init__(self, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.i18n = i18n
        self.index = 0
        tr = i18n.language == "tr"
        self.setWindowTitle("DevNest'e Hoş Geldiniz" if tr else "Welcome to DevNest")
        self.resize(680, 420)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(12)

        self.step = QLabel()
        self.step.setObjectName("cardLabel")
        self.title = QLabel()
        self.title.setObjectName("pageTitle")
        self.body = QLabel()
        self.body.setWordWrap(True)
        self.body.setObjectName("helperBanner")
        root.addWidget(self.step)
        root.addWidget(self.title)
        root.addWidget(self.body, 1)

        row = QHBoxLayout()
        self.back = QPushButton()
        self.open_page = QPushButton()
        self.open_page.setObjectName("primaryButton")
        self.next = QPushButton()
        self.skip = QPushButton("Atla" if tr else "Skip")
        self.back.clicked.connect(self._back)
        self.open_page.clicked.connect(self._open_current_page)
        self.next.clicked.connect(self._next)
        self.skip.clicked.connect(self.reject)
        row.addWidget(self.back)
        row.addStretch(1)
        row.addWidget(self.skip)
        row.addWidget(self.open_page)
        row.addWidget(self.next)
        root.addLayout(row)

        self._render()

    def _steps(self) -> list[tuple[str, str, str, str]]:
        tr = self.i18n.language == "tr"
        if tr:
            return [
                (
                    "1. Project oluştur",
                    "Notları, kararları ve repository'leri aynı ürün altında tutun. Project ekranındaki oluşturma akışı sizi temel kurulumdan geçirir.",
                    "projects",
                    "Projeler'e git",
                ),
                (
                    "2. Repo bağla",
                    "Yerel Git klasörü veya izin verdiğiniz GitHub repository'sini projenize bağlayın. DevNest kaynak koda yazmaz.",
                    "github",
                    "Repository bağlantısını aç",
                ),
                (
                    "3. Bir karar oluştur",
                    "Sadece ne yaptığınızı değil, neden yaptığınızı DEC kimliğiyle kaydedin. Kararlar aktif projeye ait olarak tutulur.",
                    "decisions",
                    "Kararlar'a git",
                ),
                (
                    "4. Koda bağla ve takibi başlat",
                    "Bir not veya kararı açıp dosya/klasöre bağlayın. Review noktası kaydedildikten sonra sonraki commitler gerektiğinde yeniden inceleme isteyebilir.",
                    "notes",
                    "Notlar'a git",
                ),
            ]
        return [
            (
                "1. Create a project",
                "Keep notes, decisions and repositories together under one product. The Projects screen guides you through the basic setup.",
                "projects",
                "Open Projects",
            ),
            (
                "2. Connect a repository",
                "Connect a local Git folder or an allowed GitHub repository to your project. DevNest does not write to source code.",
                "github",
                "Open repository connection",
            ),
            (
                "3. Create a decision",
                "Record not only what changed, but why, using a stable DEC identifier. Decisions stay scoped to the active project.",
                "decisions",
                "Open Decisions",
            ),
            (
                "4. Link code and start tracking",
                "Open a note or decision and link a file/folder. After a review point is saved, later commits can trigger re-review.",
                "notes",
                "Open Notes",
            ),
        ]

    def _render(self) -> None:
        tr = self.i18n.language == "tr"
        steps = self._steps()
        title, body, _page, action_label = steps[self.index]
        self.step.setText(
            f"Adım {self.index + 1}/{len(steps)}" if tr else f"Step {self.index + 1}/{len(steps)}"
        )
        self.title.setText(title)
        self.body.setText(body)
        self.back.setText("Geri" if tr else "Back")
        self.back.setEnabled(self.index > 0)
        self.open_page.setText(action_label)
        self.next.setText(
            ("Bitir" if tr else "Finish")
            if self.index == len(steps) - 1
            else ("İleri" if tr else "Next")
        )

    def _back(self) -> None:
        self.index = max(0, self.index - 1)
        self._render()

    def _next(self) -> None:
        if self.index >= len(self._steps()) - 1:
            self.accept()
            return
        self.index += 1
        self._render()

    def _open_current_page(self) -> None:
        _title, _body, page, _action_label = self._steps()[self.index]
        self.navigateRequested.emit(page)

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.database import Database
from app.i18n import I18n


class ProjectDetailPage(QWidget):
    sectionRequested = Signal(str)
    backRequested = Signal()
    refreshRepositoryRequested = Signal(int)
    unlinkRepositoryRequested = Signal(int, int)

    def __init__(self, database: Database, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.i18n = i18n
        self.project_id: int | None = None
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 26, 30, 24)
        root.setSpacing(12)
        top = QHBoxLayout()
        self.back = QPushButton()
        self.back.clicked.connect(self.backRequested)
        self.title = QLabel("Project")
        self.title.setObjectName("pageTitle")
        top.addWidget(self.back)
        top.addWidget(self.title)
        top.addStretch(1)
        root.addLayout(top)

        self.nav_buttons: dict[str, QPushButton] = {}
        nav = QHBoxLayout()
        for key in ("overview", "notes", "decisions", "architecture", "activity", "health", "repository", "changes"):
            button = QPushButton()
            button.setObjectName("secondaryTabButton")
            section = "review" if key == "changes" else key
            button.clicked.connect(lambda _checked=False, value=section: self.sectionRequested.emit(value))
            nav.addWidget(button)
            self.nav_buttons[key] = button
        nav.addStretch(1)
        root.addLayout(nav)

        self.description = QLabel()
        self.description.setWordWrap(True)
        self.description.setObjectName("pageSubtitle")
        root.addWidget(self.description)
        self.summary = QLabel()
        self.summary.setObjectName("helperBanner")
        self.summary.setWordWrap(True)
        root.addWidget(self.summary)
        repo_heading = QHBoxLayout()
        self.repo_title = QLabel()
        self.repo_title.setObjectName("sectionTitle")
        self.repo_filter = QComboBox()
        self.repo_filter.currentIndexChanged.connect(lambda _i: self.set_project(self.project_id) if self.project_id else None)
        repo_heading.addWidget(self.repo_title)
        repo_heading.addStretch(1)
        repo_heading.addWidget(self.repo_filter)
        root.addLayout(repo_heading)
        self.repo_container = QWidget()
        self.repo_layout = QVBoxLayout(self.repo_container)
        self.repo_layout.setContentsMargins(0, 0, 0, 0)
        self.repo_layout.setSpacing(9)
        root.addWidget(self.repo_container, 1)
        self.i18n.languageChanged.connect(lambda _language: self.retranslate_ui())
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        self.back.setText(self.i18n.t("project_detail.back"))
        tips_tr = {
            "overview": "Bu projenin kısa özetini ve bağlı depolarını gösterir.",
            "notes": "Yalnızca bu projeye ait notları açar.",
            "decisions": "Yalnızca bu projeye ait teknik kararları açar.",
            "architecture": "Bu projeye ait mimari diyagramlarını açar.",
            "activity": "Bu projedeki commit, karar, not ve review geçmişini tek akışta gösterir.",
            "health": "Bu projenin review ve dokümantasyon sağlık özetini gösterir.",
            "repository": "Bu projeye bağlanmış kod depolarını burada görürsünüz.",
            "changes": "Bu projedeki bağlı kod değişiklikleri nedeniyle tekrar bakmanız gereken bilgileri açar.",
        }
        tips_en = {
            "overview": "Show a simple summary of this project and its connected repositories.",
            "notes": "Open only the notes that belong to this project.",
            "decisions": "Open only the technical decisions that belong to this project.",
            "architecture": "Open architecture diagrams that belong to this project.",
            "activity": "Show commits, decisions, notes and reviews for this project in one timeline.",
            "health": "Show review and documentation health for this project.",
            "repository": "See the code repositories connected to this project.",
            "changes": "Open knowledge in this project that should be checked again because connected code changed.",
        }
        for key, button in self.nav_buttons.items():
            if key == "activity":
                button.setText("Aktivite" if self.i18n.language == "tr" else "Activity")
            elif key == "health":
                button.setText("Sağlık" if self.i18n.language == "tr" else "Health")
            else:
                button.setText(self.i18n.t(f"project_detail.{key}"))
            button.setToolTip((tips_tr if self.i18n.language == "tr" else tips_en)[key])
        self.back.setToolTip("Proje listesine geri döner." if self.i18n.language == "tr" else "Go back to the project list.")
        self.repo_title.setText(self.i18n.t("project_detail.repo_title"))
        if self.project_id is not None:
            self.set_project(self.project_id)

    def _github_access_text(self, repo) -> str:
        tr = self.i18n.language == "tr"
        if repo.github_repo_id is None or repo.github_access_state == "local_only":
            return "GitHub bağlantısı yok; yerel depo kullanılabilir" if tr else "No GitHub connection; local repository can still be used"
        if repo.github_access_state == "available":
            return "Sadece okuma erişimi doğrulandı" if tr else "Read-only access verified"
        if repo.github_access_state in {"unknown", "unchecked"}:
            return "GitHub erişimi henüz doğrulanmadı" if tr else "GitHub access has not been verified yet"
        # Do not call the repository itself unavailable: only the remote access
        # check failed. This distinction matters when a healthy local clone exists.
        if repo.local_git_root:
            return "GitHub erişimi doğrulanamadı; yerel depo kullanılabilir" if tr else "GitHub access could not be verified; local repository is available"
        return "GitHub erişimi doğrulanamadı" if tr else "GitHub access could not be verified"

    def set_project(self, project_id: int) -> None:
        self.project_id = project_id
        project = self.database.get_project(project_id)
        if not project:
            return
        self.title.setText(project.name)
        self.description.setText(project.description or (
            "Yerel çalışan geliştirici bilgi çalışma alanı" if self.i18n.language == "tr" else "Local-first developer knowledge workspace"
        ))
        notes = self.database.list_notes(project_id=project_id)
        decisions = self.database.list_decisions(project_id)
        repositories = self.database.list_repositories(project_id)
        current_repo_filter = self.repo_filter.currentData() if self.repo_filter.count() else None
        self.repo_filter.blockSignals(True)
        self.repo_filter.clear()
        self.repo_filter.addItem("Tüm repository'ler" if self.i18n.language == "tr" else "All repositories", None)
        for repo in repositories:
            self.repo_filter.addItem(repo.full_name or repo.name, repo.id)
        index = self.repo_filter.findData(current_repo_filter)
        self.repo_filter.setCurrentIndex(max(0, index))
        self.repo_filter.blockSignals(False)
        selected_repo_id = self.repo_filter.currentData()
        visible_repositories = repositories if selected_repo_id is None else [r for r in repositories if r.id == int(selected_repo_id)]
        if self.i18n.language == "tr":
            self.summary.setText(
                f"Bu projede {len(repositories)} depo, {len(notes)} not ve {len(decisions)} karar var. "
                "Üstteki sekmeler yalnızca bu projeye ait bilgileri açar."
            )
        else:
            self.summary.setText(
                f"This project contains {len(repositories)} repositories, {len(notes)} notes and {len(decisions)} decisions. "
                "The tabs above open information that belongs only to this project."
            )
        while self.repo_layout.count():
            item = self.repo_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not visible_repositories:
            empty = QLabel(self.i18n.t("project_detail.empty_repo"))
            empty.setWordWrap(True)
            empty.setObjectName("emptyState")
            self.repo_layout.addWidget(empty)
        for repo in visible_repositories:
            frame = QFrame()
            frame.setObjectName("repositoryCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(16, 12, 16, 12)
            name = QLabel(repo.full_name or repo.name)
            name.setObjectName("cardTitle")
            if self.i18n.language == "tr":
                local = repo.local_git_root or "Yerel klasör bağlanmamış"
                github = self._github_access_text(repo)
                detail_text = (
                    f"Bilgisayardaki klasör: {local}\nGitHub: {github}\nİzlenen branch: {repo.default_branch or 'Bilinmiyor'}\n"
                    f"Son görülen commit: {(repo.last_seen_sha or 'Henüz kontrol edilmedi')[:12]}"
                )
            else:
                local = repo.local_git_root or "No local folder connected"
                github = self._github_access_text(repo)
                detail_text = (
                    f"Local folder: {local}\nGitHub: {github}\nMonitored branch: {repo.default_branch or 'Unknown'}\n"
                    f"Last seen commit: {(repo.last_seen_sha or 'Not checked yet')[:12]}"
                )
            detail = QLabel(detail_text)
            detail.setWordWrap(True)
            detail.setObjectName("repositoryDetailText")
            refresh = QPushButton(self.i18n.t("project_detail.refresh"))
            refresh.setToolTip(
                "Depodaki güncel commit'i ve değişiklikleri şimdi kontrol eder. Koda hiçbir şey yazmaz."
                if self.i18n.language == "tr" else
                "Check the repository's current commit and changes now. This does not write anything to the codebase."
            )
            refresh.clicked.connect(lambda _checked=False, rid=repo.id: self.refreshRepositoryRequested.emit(rid))
            remove = QPushButton("Projeden çıkar" if self.i18n.language == "tr" else "Remove from project")
            remove.setToolTip(
                "Bu depoyu yalnızca bu DevNest projesinden ayırır. Bilgisayardaki klasörü veya GitHub deposunu silmez."
                if self.i18n.language == "tr" else
                "Disconnect this repository only from this DevNest project. It does not delete the local folder or GitHub repository."
            )
            remove.clicked.connect(lambda _checked=False, pid=project_id, rid=repo.id: self.unlinkRepositoryRequested.emit(pid, rid))
            favorite = QPushButton("★" if self.database.is_favorite("repository", repo.id) else "☆")
            favorite.setFixedWidth(42)
            favorite.setToolTip("Repository'yi favorilere ekle/çıkar." if self.i18n.language == "tr" else "Add/remove repository from favorites.")
            favorite.clicked.connect(lambda _c=False, rid=repo.id: self._toggle_repository_favorite(rid))
            buttons = QHBoxLayout()
            buttons.addWidget(favorite)
            buttons.addWidget(refresh)
            buttons.addWidget(remove)
            buttons.addStretch(1)
            layout.addWidget(name)
            layout.addWidget(detail)
            layout.addLayout(buttons)
            self.repo_layout.addWidget(frame)
        self.repo_layout.addStretch(1)

    def _toggle_repository_favorite(self, repository_id: int) -> None:
        favorite = not self.database.is_favorite("repository", repository_id)
        self.database.set_favorite("repository", repository_id, favorite, self.project_id)
        if self.project_id is not None:
            self.set_project(self.project_id)

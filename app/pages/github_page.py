from __future__ import annotations

import threading
from typing import Any

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.database import Database
from app.i18n import I18n
from app.database import utc_now_iso
from app.integrations.github.auth import GitHubAuthService
from app.integrations.github.browser import BrowserLauncher
from app.integrations.github.client import GitHubClient
from app.integrations.github.config import GitHubConfig
from app.integrations.github.errors import GitHubAuthenticationError, GitHubConfigurationError, GitHubError
from app.models import GitHubInstallation
from app.services.async_tasks import AsyncTaskRunner
from app.services.credential_store import CredentialStore


class GitHubPage(QWidget):
    connectionStateChanged = Signal(str)
    repositoriesChanged = Signal()
    linkRepositoryRequested = Signal(int)
    unlinkRepositoryRequested = Signal(int)

    def __init__(self, database: Database, credential_store: CredentialStore,
                 config: GitHubConfig, browser: BrowserLauncher, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.database = database
        self.credential_store = credential_store
        self.config = config
        self.browser = browser
        self.i18n = i18n
        self.runner = AsyncTaskRunner()
        self.auth = GitHubAuthService(credential_store, config)
        self.cancel_event: threading.Event | None = None
        self._syncing = False
        self.current_project_id: int | None = None
        self._awaiting_installation = False
        self._install_page_opened = False
        self._installation_poll_in_progress = False
        self._installation_poll_attempts = 0
        self.installation_poll_timer = QTimer(self)
        self.installation_poll_timer.setInterval(6000)
        self.installation_poll_timer.timeout.connect(self._poll_for_installation)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        self.page_title = QLabel()
        self.page_title.setObjectName("pageTitle")
        self.page_subtitle = QLabel()
        self.page_subtitle.setObjectName("pageSubtitle")
        self.page_subtitle.setWordWrap(True)
        root.addWidget(self.page_title)
        root.addWidget(self.page_subtitle)
        self.plain_help = QLabel()
        self.plain_help.setObjectName("helperBanner")
        self.plain_help.setWordWrap(True)
        root.addWidget(self.plain_help)
        self.state_panel = QFrame()
        self.state_panel.setObjectName("dashboardPanel")
        panel = QVBoxLayout(self.state_panel)
        self.state_title = QLabel("GitHub isn't connected")
        self.state_title.setObjectName("sectionTitle")
        self.state_text = QLabel("Connect GitHub to browse accessible repositories, commits and pull requests. DevNest requests read-only access.")
        self.state_text.setWordWrap(True)
        actions = QHBoxLayout()
        self.connect_button = QPushButton("Connect GitHub")
        self.connect_button.setObjectName("primaryButton")
        self.connect_button.clicked.connect(self.connect_github)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_from_github)
        self.manage_button = QPushButton("Manage Access")
        self.manage_button.clicked.connect(self.manage_access)
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect)
        for button in (self.connect_button, self.refresh_button, self.manage_button, self.disconnect_button):
            actions.addWidget(button)
        actions.addStretch(1)
        panel.addWidget(self.state_title)
        panel.addWidget(self.state_text)
        panel.addLayout(actions)
        root.addWidget(self.state_panel)

        self.device_panel = QFrame()
        self.device_panel.setObjectName("projectCard")
        device_layout = QVBoxLayout(self.device_panel)
        self.device_heading = QLabel()
        device_layout.addWidget(self.device_heading)
        self.device_code = QLabel("—")
        self.device_code.setObjectName("deviceCode")
        self.device_url = QLineEdit()
        self.device_url.setReadOnly(True)
        row = QHBoxLayout()
        self.device_copy_button = QPushButton()
        self.device_copy_button.clicked.connect(lambda: QGuiApplication.clipboard().setText(self.device_code.text()))
        self.device_open_button = QPushButton()
        self.device_open_button.clicked.connect(lambda: self.browser.open(self.device_url.text()))
        self.device_cancel_button = QPushButton()
        self.device_cancel_button.clicked.connect(self.cancel_connection)
        row.addWidget(self.device_copy_button)
        row.addWidget(self.device_open_button)
        row.addWidget(self.device_cancel_button)
        row.addStretch(1)
        self.device_status = QLabel("Waiting for authorization…")
        device_layout.addWidget(self.device_code)
        device_layout.addWidget(self.device_url)
        device_layout.addLayout(row)
        device_layout.addWidget(self.device_status)
        self.device_panel.hide()
        root.addWidget(self.device_panel)

        search_row = QHBoxLayout()
        self.repos_label = QLabel()
        self.repos_label.setObjectName("sectionTitle")
        self.search = QLineEdit()
        self.search.setPlaceholderText(self.i18n.t("github.search"))
        self.search.textChanged.connect(self.render_cached)
        search_row.addWidget(self.repos_label)
        search_row.addStretch(1)
        search_row.addWidget(self.search)
        root.addLayout(search_row)
        self.sort_notice = QLabel()
        self.sort_notice.setObjectName("sortNotice")
        root.addWidget(self.sort_notice)
        self.repo_container = QWidget()
        self.repo_layout = QVBoxLayout(self.repo_container)
        self.repo_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(self.repo_container)
        root.addWidget(scroll, 1)
        self.i18n.languageChanged.connect(lambda _language: self.retranslate_ui())
        self.retranslate_ui()
        self.render_cached()
        self.update_connection_state()

    def set_current_project(self, project_id: int | None) -> None:
        self.current_project_id = project_id
        if hasattr(self, "repo_layout"):
            self.render_cached()

    def retranslate_ui(self) -> None:
        self.page_title.setText(self.i18n.t("github.title"))
        self.page_subtitle.setText(self.i18n.t("github.subtitle"))
        self.plain_help.setText(
            "GitHub burada yalnızca kod depolarınızı gösterir. Bir depoyu projeye eklemek, depodaki kodu değiştirmez; sadece DevNest projesiyle ilişkilendirir."
            if self.i18n.language == "tr" else
            "GitHub is only a source of repositories here. Adding a repository to a project does not change the code; it only connects the repository to your DevNest project."
        )
        self.connect_button.setText(self.i18n.t("github.connect"))
        self.refresh_button.setText(self.i18n.t("github.refresh"))
        self.manage_button.setText(self.i18n.t("github.manage"))
        self.disconnect_button.setText(self.i18n.t("github.disconnect"))
        self.connect_button.setToolTip(self.i18n.t("tip.github.connect"))
        self.refresh_button.setToolTip(self.i18n.t("tip.github.refresh"))
        self.manage_button.setToolTip(self.i18n.t("tip.github.manage"))
        self.disconnect_button.setToolTip(self.i18n.t("tip.github.disconnect"))
        tr = self.i18n.language == "tr"
        self.device_heading.setText("GitHub'ı açın ve DevNest'e izin verin" if tr else "Open GitHub and authorize DevNest")
        self.device_copy_button.setText("Kodu kopyala" if tr else "Copy code")
        self.device_open_button.setText("GitHub'ı aç" if tr else "Open GitHub")
        self.device_cancel_button.setText("İptal" if tr else "Cancel")
        if self.device_panel.isVisible() and not self.device_status.text().strip():
            self.device_status.setText("Yetkilendirme bekleniyor…" if tr else "Waiting for authorization…")
        self.repos_label.setText(self.i18n.t("github.repos"))
        self.search.setPlaceholderText(self.i18n.t("github.search"))
        self.sort_notice.setText(self.i18n.t("github.sort_notice"))
        if hasattr(self, "repo_layout"):
            self.render_cached()
        if hasattr(self, "state_title"):
            self.update_connection_state()

    def _set_connected_controls(self, connected: bool, has_cached_account: bool = False) -> None:
        self.connect_button.setVisible(not connected)
        self.refresh_button.setVisible(connected)
        self.manage_button.setVisible(connected)
        self.disconnect_button.setVisible(connected or has_cached_account)

    def update_connection_state(self) -> None:
        account = self.database.get_github_account()
        try:
            has_token = bool(self.credential_store.get().access_token)
        except Exception:
            has_token = False
        connected = bool(has_token)
        installations = self.database.list_github_installations() if connected else []
        tr = self.i18n.language == "tr"
        if connected and account:
            self.state_title.setText(f"@{account.login} · " + ("Bağlı" if tr else "Connected"))
        elif connected:
            self.state_title.setText("GitHub bağlı · hesap doğrulanıyor" if tr else "GitHub connected · validating account")
        elif account:
            self.state_title.setText("GitHub yeniden bağlanmalı" if tr else "GitHub reconnect required")
        else:
            self.state_title.setText(self.i18n.t("github.not_connected"))

        if connected and installations:
            owners = ", ".join(f"{item.account_login} ({item.account_type})" for item in installations[:4])
            available = sum(1 for repo in self.database.list_repositories() if repo.github_repo_id is not None and repo.github_access_state == "available")
            if tr:
                self.state_text.setText(f"GitHub bağlantısı hazır. {available} depo okunabiliyor. Hesap/kurulum: {owners}. DevNest kod gönderemez veya merge yapamaz.")
            else:
                self.state_text.setText(f"GitHub connection is ready. {available} repositories can be read. Account/installations: {owners}. DevNest cannot push code or merge pull requests.")
            self.manage_button.setText(self.i18n.t("github.manage"))
        elif connected:
            self.state_text.setText(
                "GitHub oturumu kaydedildi ama DevNest GitHub App henüz bir hesaba/depolara kurulmamış. 'Depoları seç' düğmesiyle GitHub'da izin vereceğiniz depoları seçin."
                if tr else
                "Your GitHub login is saved, but the DevNest GitHub App is not installed for any repositories yet. Use 'Choose repositories' to select what DevNest may read on GitHub."
            )
            self.manage_button.setText(self.i18n.t("github.manage"))
        elif account:
            self.state_text.setText((f"@{account.login} hesabının eski bilgisi duruyor ancak güvenli giriş bilgisi bulunamadı. Yeniden bağlanın." if tr else f"Cached account @{account.login} is preserved, but secure authorization is unavailable. Connect again."))
        else:
            extra = " GitHub App Client ID ayarlanmamış." if tr and not self.config.configured else (" Developer setup: DEVNEST_GITHUB_CLIENT_ID is not configured." if not tr and not self.config.configured else "")
            self.state_text.setText(self.i18n.t("github.connect_text") + extra)

        self._set_connected_controls(connected, account is not None)
        self.connectionStateChanged.emit("connected" if connected else ("reconnect" if account else "disconnected"))

    def refresh_if_connected(self) -> None:
        """Validate and synchronize a persisted connection without blocking startup."""
        try:
            has_token = bool(self.credential_store.get().access_token)
        except Exception:
            has_token = False
        if has_token:
            self.refresh_from_github()

    def connect_github(self) -> None:
        if not self.config.configured:
            QMessageBox.information(
                self, "GitHub App Ayarı Gerekli" if self.i18n.language == "tr" else "GitHub App Configuration Required",
                ("DevNest GitHub App için public DEVNEST_GITHUB_CLIENT_ID değerini (isteğe bağlı olarak DEVNEST_GITHUB_APP_SLUG değerini de) ayarlayın. Masaüstü uygulaması client secret veya private key kullanmaz."
                 if self.i18n.language == "tr" else
                 "Set the public DEVNEST_GITHUB_CLIENT_ID (and optionally DEVNEST_GITHUB_APP_SLUG) for your DevNest GitHub App. No client secret or private key is used by the desktop app."),
            )
            return
        self.connect_button.setEnabled(False)
        self.state_text.setText("GitHub güvenli bağlantısı başlatılıyor…" if self.i18n.language == "tr" else "Starting GitHub Device Flow…")
        self.runner.submit(self.auth.request_device_code, self._device_ready, self._network_error,
                           lambda: self.connect_button.setEnabled(True))

    def _device_ready(self, device) -> None:
        self.device_panel.show()
        self.device_code.setText(device.user_code)
        self.device_url.setText(device.verification_uri)
        QGuiApplication.clipboard().setText(device.user_code)
        opened = self.browser.open(device.verification_uri)
        if self.i18n.language == "tr":
            self.device_status.setText("Yetkilendirme bekleniyor…" + ("" if opened else " Tarayıcı otomatik açılamadı; yukarıdaki adresi kullanın."))
        else:
            self.device_status.setText("Waiting for authorization…" + ("" if opened else " Browser could not be opened automatically; use the URL above."))
        self.cancel_event = threading.Event()
        self.runner.submit(
            lambda: self.auth.poll_until_authorized(device, self.cancel_event),
            lambda _bundle: self._authorization_complete(),
            self._authorization_failed,
        )

    def _authorization_complete(self) -> None:
        self.device_status.setText("✓ GitHub yetkilendirmesi tamamlandı" if self.i18n.language == "tr" else "✓ GitHub authorization complete")
        self.device_panel.hide()
        self._awaiting_installation = True
        self._install_page_opened = False
        self._installation_poll_attempts = 0
        self.refresh_from_github()

    def _authorization_failed(self, exc: Exception) -> None:
        if self.cancel_event and self.cancel_event.is_set():
            self.device_status.setText("Bağlantı iptal edildi." if self.i18n.language == "tr" else "Connection cancelled.")
        else:
            self.device_status.setText(str(exc))
        self.update_connection_state()

    def cancel_connection(self) -> None:
        if self.cancel_event:
            self.cancel_event.set()
        self.device_panel.hide()
        self.state_text.setText("GitHub bağlantısı iptal edildi. Yerel DevNest özellikleri kullanılmaya devam eder." if self.i18n.language == "tr" else "GitHub connection cancelled. Local DevNest features remain available.")

    def _load_remote_data(self) -> dict[str, Any]:
        token = self.auth.get_valid_access_token()
        client = GitHubClient(token, self.config)
        user = client.get_authenticated_user()
        installations = client.list_user_installations()
        repositories: list[tuple[int, dict[str, Any]]] = []
        repository_errors: list[str] = []
        for installation in installations:
            try:
                items = client.list_installation_repositories(installation.id)
            except GitHubError as exc:
                repository_errors.append(f"{installation.account_login}: {exc}")
                continue
            for repo in items:
                repositories.append((installation.id, repo))
        return {
            "user": user,
            "installations": installations,
            "repositories": repositories,
            "repository_errors": repository_errors,
        }

    def _load_installations_only(self) -> list[GitHubInstallation]:
        token = self.auth.get_valid_access_token()
        return GitHubClient(token, self.config).list_user_installations()

    def refresh_from_github(self) -> None:
        if self._syncing:
            return
        self._syncing = True
        self.refresh_button.setEnabled(False)
        self.state_text.setText("Salt okunur GitHub bilgileri yenileniyor…" if self.i18n.language == "tr" else "Refreshing read-only GitHub metadata…")
        self.runner.submit(self._load_remote_data, self._sync_complete, self._network_error, self._sync_finished)

    def _sync_complete(self, data: dict[str, Any]) -> None:
        user = data["user"]
        if user.get("id") and user.get("login"):
            self.database.save_github_account(int(user["id"]), str(user["login"]), user.get("avatar_url"))
            self.state_title.setText(f"@{user['login']} · " + ("Bağlı" if self.i18n.language == "tr" else "Connected"))
        else:
            self.state_title.setText("GitHub Bağlı" if self.i18n.language == "tr" else "GitHub Connected")
        self._set_connected_controls(True, True)
        installations: list[GitHubInstallation] = data["installations"]
        self.database.save_github_installations(installations)
        for existing in self.database.list_repositories():
            if existing.github_repo_id is not None:
                self.database.set_repository_github_access_state(existing.id, "unavailable")
        for installation_id, raw in data["repositories"]:
            owner = (raw.get("owner") or {}).get("login")
            full_name = raw.get("full_name")
            self.database.upsert_repository(
                name=str(raw.get("name") or full_name or "Repository"),
                github_repo_id=int(raw["id"]) if raw.get("id") is not None else None,
                github_node_id=raw.get("node_id"), owner=owner, full_name=full_name,
                html_url=raw.get("html_url"), clone_url=raw.get("clone_url"), default_branch=raw.get("default_branch"),
                is_private=bool(raw.get("private")), installation_id=installation_id,
                language=raw.get("language"), description=raw.get("description"), last_pushed_at=raw.get("pushed_at"),
                github_access_state="available",
            )
        repository_errors = list(data.get("repository_errors") or [])
        if installations:
            self._awaiting_installation = False
            self.installation_poll_timer.stop()
            owners = ", ".join(f"{installation.account_login} ({installation.account_type})" for installation in installations[:4])
            tr = self.i18n.language == "tr"
            if data["repositories"]:
                self.state_text.setText(
                    (f"✓ GitHub bağlı · {len(data['repositories'])} depo erişilebilir · Salt okunur\nKurulumlar: {owners}")
                    if tr else
                    (f"✓ GitHub connected · {len(data['repositories'])} repositories available · Read-only\nInstallations: {owners}")
                )
            elif repository_errors:
                self.state_text.setText(
                    (("GitHub App kurulumu bulundu ancak repository erişimi okunamadı. Erişimi Yönet'i açıp Metadata/Contents/Pull requests izinlerinin salt okunur olduğunu ve repository seçildiğini doğrulayın.\n") if tr else
                     ("GitHub App installation was found, but repository access could not be read. Open Manage Access and verify Metadata/Contents/Pull requests are Read-only and repositories are selected.\n"))
                    + "\n".join(repository_errors[:3])
                )
            else:
                self.state_text.setText(
                    "GitHub App kurulumu bulundu ancak şu anda DevNest'e 0 repository gösteriyor. Erişimi Yönet'i açıp en az bir repository seçin."
                    if tr else
                    "GitHub App installation was found, but it currently exposes 0 repositories to DevNest. Open Manage Access and select at least one repository."
                )
            self.manage_button.setText("Erişimi Yönet" if tr else "Manage Access")
        else:
            tr = self.i18n.language == "tr"
            self.state_text.setText(
                "✓ GitHub yetkilendirmesi tamamlandı. Bir adım daha gerekli: DevNest GitHub App'i kurun ve okuyabileceği repository'leri seçin. Kurulumdan sonra bu sayfa otomatik güncellenecek."
                if tr else
                "✓ GitHub authorization is complete. One more GitHub step is required: install the DevNest GitHub App and select the repositories it may read. This page will update automatically after installation."
            )
            self.manage_button.setText("GitHub App'i Kur" if tr else "Install GitHub App")
            if self._awaiting_installation:
                self._begin_installation_wait()
        self.render_cached()
        self.repositoriesChanged.emit()
        self.connectionStateChanged.emit("connected")

    def _begin_installation_wait(self) -> None:
        if not self._install_page_opened:
            if self.config.install_url:
                self.browser.open(self.config.install_url)
                self._install_page_opened = True
            else:
                extra = (
                    "\nGitHub App slug ayarlı değil. GitHub → Settings → Applications → GitHub Apps yolunu açıp DevNest'i manuel kurun."
                    if self.i18n.language == "tr" else
                    "\nGitHub App slug is not configured, so open GitHub → Settings → Applications → GitHub Apps and install DevNest manually."
                )
                self.state_text.setText(self.state_text.text() + extra)
        if not self.installation_poll_timer.isActive():
            self.installation_poll_timer.start()

    def _poll_for_installation(self) -> None:
        if self._installation_poll_in_progress or self._syncing or not self._awaiting_installation:
            return
        self._installation_poll_attempts += 1
        if self._installation_poll_attempts > 50:  # ~5 minutes at a 6 second interval
            self.installation_poll_timer.stop()
            self.state_text.setText(
                "GitHub yetkilendirmesi kaydedildi. DevNest hâlâ GitHub App kurulumunu bekliyor. Kurulumdan/repository seçiminden sonra Yenile'ye basın; yeniden bağlanmanız gerekmez."
                if self.i18n.language == "tr" else
                "GitHub authorization is saved. DevNest is still waiting for a GitHub App installation. After installing/selecting repositories, press Refresh; no reconnection is required."
            )
            return
        self._installation_poll_in_progress = True
        self.runner.submit(
            self._load_installations_only,
            self._installation_poll_ready,
            self._installation_poll_error,
            lambda: setattr(self, "_installation_poll_in_progress", False),
        )

    def _installation_poll_ready(self, installations: list[GitHubInstallation]) -> None:
        if installations:
            self.installation_poll_timer.stop()
            self._awaiting_installation = False
            self.state_text.setText("✓ GitHub App kurulumu algılandı. Repository'ler yükleniyor…" if self.i18n.language == "tr" else "✓ GitHub App installation detected. Loading repositories…")
            self.refresh_from_github()
        else:
            self.state_text.setText(
                "GitHub yetkilendirmesi kaydedildi. GitHub App kurulumu/repository seçimi bekleniyor… DevNest'i yeniden başlatmanız gerekmez."
                if self.i18n.language == "tr" else
                "GitHub authorization is saved. Waiting for GitHub App installation/repository selection… You do not need to restart DevNest."
            )

    def _installation_poll_error(self, exc: Exception) -> None:
        if isinstance(exc, GitHubAuthenticationError):
            self.installation_poll_timer.stop()
            self._awaiting_installation = False
            self._network_error(exc)

    def _sync_finished(self) -> None:
        self._syncing = False
        self.refresh_button.setEnabled(True)

    def _network_error(self, exc: Exception) -> None:
        tr = self.i18n.language == "tr"
        if isinstance(exc, GitHubAuthenticationError):
            self.state_title.setText("GitHub yeniden bağlantı istiyor" if tr else "GitHub reconnection required")
            connected = False
            friendly = (
                "GitHub oturumunuz artık geçerli değil. Yeniden bağlandığınızda repository izinleri tekrar kontrol edilir."
                if tr else
                "Your GitHub session is no longer valid. Repository permissions will be checked again after you reconnect."
            )
        else:
            self.state_title.setText("GitHub erişimi doğrulanamadı" if tr else "GitHub access could not be verified")
            try:
                connected = bool(self.credential_store.get().access_token)
            except Exception:
                connected = False
            friendly = (
                "GitHub bağlantısı şu anda kontrol edilemedi. Yerel notlar, kararlar, mimari ve yerel Git çalışmaya devam eder."
                if tr else
                "GitHub connectivity could not be checked right now. Local notes, decisions, architecture and local Git remain available."
            )
        self.state_text.setText(friendly)
        self.state_text.setToolTip(str(exc))
        self._syncing = False
        self.refresh_button.setEnabled(True)
        self._set_connected_controls(connected, self.database.get_github_account() is not None)
        self.connectionStateChanged.emit("offline" if not isinstance(exc, GitHubAuthenticationError) else "reconnect")

    def manage_access(self) -> None:
        installations = self.database.list_github_installations()
        if installations:
            self.browser.open(f"{self.config.web_base_url}/settings/installations/{installations[0].id}")
            # Repository selections can change on GitHub. Refresh a few times in
            # the background so returning to DevNest does not require a restart.
            QTimer.singleShot(5000, self.refresh_from_github)
            QTimer.singleShot(15000, self.refresh_from_github)
            QTimer.singleShot(30000, self.refresh_from_github)
        elif self.config.install_url:
            self._awaiting_installation = True
            self._install_page_opened = True
            self._installation_poll_attempts = 0
            self.browser.open(self.config.install_url)
            self.installation_poll_timer.start()
        else:
            self.browser.open(f"{self.config.web_base_url}/settings/installations")

    def disconnect(self) -> None:
        answer = QMessageBox.question(
            self, "GitHub Bağlantısını Kes" if self.i18n.language == "tr" else "Disconnect GitHub",
            ("Bu bilgisayarda güvenli biçimde saklanan GitHub oturumu kaldırılsın mı? Yerel projeler, notlar, kararlar, diyagramlar, depo bağlantıları ve inceleme başlangıç noktaları korunur."
             if self.i18n.language == "tr" else
             "Remove DevNest's secure GitHub credentials? Local projects, notes, decisions, diagrams, repository references and review baselines will be preserved."),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.installation_poll_timer.stop()
        self._awaiting_installation = False
        try:
            self.auth.disconnect()
        except Exception as exc:
            QMessageBox.warning(self, "Güvenli Oturum Temizlenemedi" if self.i18n.language == "tr" else "Credential Cleanup", str(exc))
        self.database.disconnect_github_metadata()
        self.state_text.setText("GitHub bağlantısı kesildi. Yerel proje verileri korundu." if self.i18n.language == "tr" else "GitHub disconnected. Local project data was preserved.")
        self.retranslate_ui()
        self.render_cached()
        self.update_connection_state()

    def render_cached(self) -> None:
        while self.repo_layout.count():
            item = self.repo_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        term = self.search.text().strip().casefold() if hasattr(self, "search") else ""
        repos = [r for r in self.database.list_repositories() if r.github_repo_id is not None]
        # Most recently pushed repository first. Missing timestamps go to the bottom.
        repos.sort(key=lambda r: (r.last_pushed_at or "", r.updated_at or ""), reverse=True)
        if term:
            repos = [r for r in repos if term in (r.full_name or r.name).casefold() or term in (r.description or "").casefold()]
        if not repos:
            empty = QLabel(self.i18n.t("github.empty"))
            empty.setWordWrap(True)
            empty.setObjectName("emptyState")
            self.repo_layout.addWidget(empty)
            self.repo_layout.addStretch(1)
            return
        for repo in repos:
            card = QFrame()
            card.setObjectName("repositoryCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(16, 13, 16, 13)
            layout.setSpacing(6)
            top = QHBoxLayout()
            title = QLabel(repo.full_name or repo.name)
            title.setObjectName("cardTitle")
            visibility = self.i18n.t("github.private") if repo.is_private else self.i18n.t("github.public")
            visibility_label = QLabel(visibility)
            visibility_label.setObjectName("smallPill")
            top.addWidget(title)
            top.addStretch(1)
            top.addWidget(visibility_label)
            layout.addLayout(top)
            if repo.github_access_state == "available":
                access = self.i18n.t("github.read_only")
            elif repo.github_access_state == "local_only" or repo.github_repo_id is None:
                access = "Yerel repo" if self.i18n.language == "tr" else "Local repository"
            else:
                access = "GitHub erişimi doğrulanamadı" if self.i18n.language == "tr" else "GitHub access not verified"
            pushed = repo.last_pushed_at or self.i18n.t("github.not_available")
            linked_projects = self.database.list_projects_for_repository(repo.id)
            project_names = ", ".join(project.name for project in linked_projects)
            project_line = (("DevNest projeleri: " + project_names) if project_names else "Henüz hiçbir DevNest projesine eklenmemiş") if self.i18n.language == "tr" else (("DevNest projects: " + project_names) if project_names else "Not added to any DevNest project yet")
            detail = QLabel(
                f"{self.i18n.t('github.branch')}: {repo.default_branch or '—'}    ·    "
                f"{self.i18n.t('github.access')}: {access}    ·    "
                f"{self.i18n.t('github.last_update')}: {pushed}\n"
                f"{repo.description or self.i18n.t('github.no_description')}\n"
                f"{project_line}"
            )
            detail.setWordWrap(True)
            detail.setObjectName("repositoryDetailText")
            layout.addWidget(detail)
            actions = QHBoxLayout()
            open_button = QPushButton(self.i18n.t("github.open"))
            open_button.setEnabled(bool(repo.html_url))
            open_button.setToolTip("Bu depoyu github.com üzerinde açar. DevNest'te hiçbir şeyi değiştirmez." if self.i18n.language == "tr" else "Open this repository on github.com. This does not change anything in DevNest or the repository.")
            open_button.clicked.connect(lambda _checked=False, url=repo.html_url: self.browser.open(url or ""))
            already_in_current = bool(self.current_project_id and self.database.project_repository(self.current_project_id, repo.id))
            if already_in_current:
                current_project = self.database.get_project(self.current_project_id) if self.current_project_id else None
                link_button = QPushButton("Projeden çıkar" if self.i18n.language == "tr" else "Remove from project")
                link_button.setObjectName("dangerButton")
                link_button.setToolTip(
                    (f"{current_project.name if current_project else 'Aktif proje'} ile bu depo arasındaki DevNest bağlantısını kaldırır. GitHub deposu veya bilgisayarınızdaki klasör silinmez."
                     if self.i18n.language == "tr" else
                     f"Disconnect this repository from {current_project.name if current_project else 'the current project'} in DevNest. The GitHub repository and local folder are not deleted.")
                )
                link_button.clicked.connect(lambda _checked=False, rid=repo.id: self.unlinkRepositoryRequested.emit(rid))
            else:
                link_button = QPushButton(self.i18n.t("github.link_project"))
                link_button.setObjectName("primaryButton")
                link_button.setToolTip(self.i18n.t("tip.github.link_project"))
                link_button.clicked.connect(lambda _checked=False, rid=repo.id: self.linkRepositoryRequested.emit(rid))
            actions.addWidget(link_button)
            actions.addWidget(open_button)
            actions.addStretch(1)
            layout.addLayout(actions)
            self.repo_layout.addWidget(card)
        self.repo_layout.addStretch(1)


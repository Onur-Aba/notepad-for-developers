from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from app.i18n import I18n

NAV_ITEMS = (
    ("dashboard", "nav.dashboard", "tip.nav.dashboard"),
    ("projects", "nav.projects", "tip.nav.projects"),
    ("notes", "nav.notes", "tip.nav.notes"),
    ("decisions", "nav.decisions", "tip.nav.decisions"),
    ("architecture", "nav.architecture", "tip.nav.architecture"),
    ("activity", "nav.activity", "tip.nav.activity"),
    ("health", "nav.health", "tip.nav.health"),
    ("review", "nav.review", "tip.nav.review"),
    ("teams", "nav.teams", "tip.nav.teams"),
)
INTEGRATION_ITEMS = (
    ("github", "nav.github", "tip.nav.github"),
    ("settings", "nav.settings", "tip.nav.settings"),
)


class NavigationSidebar(QWidget):
    pageSelected = Signal(str)
    trashRequested = Signal()
    onlineRequested = Signal()

    def __init__(self, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.i18n = i18n
        self.setObjectName("globalNavigation")
        # The outer product splitter controls this width. Keeping a useful range
        # prevents the navigation from becoming unreadably narrow or wasting the
        # entire window when dragged too far.
        self.setMinimumWidth(170)
        self.setMaximumWidth(420)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 16, 14, 14)
        root.setSpacing(5)

        self.brand = QLabel("DevNest")
        self.brand.setObjectName("productBrand")
        self.tagline = QLabel()
        self.tagline.setWordWrap(True)
        self.tagline.setObjectName("productTagline")
        root.addWidget(self.brand)
        root.addWidget(self.tagline)
        root.addSpacing(18)

        self.workspace_section = QLabel()
        self.workspace_section.setObjectName("navSectionLabel")
        root.addWidget(self.workspace_section)

        self.buttons: dict[str, QPushButton] = {}
        self._team_badge = 0
        self._online_connected = False
        self._online_username = ""
        self._label_keys: dict[str, str] = {}
        self._tooltip_keys: dict[str, str] = {}
        for key, label_key, tip_key in NAV_ITEMS:
            self._add_button(root, key, label_key, tip_key)

        root.addSpacing(14)
        self.integrations_section = QLabel()
        self.integrations_section.setObjectName("navSectionLabel")
        root.addWidget(self.integrations_section)
        for key, label_key, tip_key in INTEGRATION_ITEMS:
            self._add_button(root, key, label_key, tip_key)

        root.addStretch(1)
        self.online_button = QPushButton()
        self.online_button.setObjectName("primaryButton")
        self.online_button.clicked.connect(self.onlineRequested)
        root.addWidget(self.online_button)
        self.trash_button = QPushButton()
        self.trash_button.setObjectName("navTrashButton")
        self.trash_button.clicked.connect(self.trashRequested)
        root.addWidget(self.trash_button)

        self.privacy = QLabel()
        self.privacy.setWordWrap(True)
        self.privacy.setObjectName("navFooter")
        root.addWidget(self.privacy)

        self.i18n.languageChanged.connect(lambda _language: self.retranslate_ui())
        self.retranslate_ui()
        self.set_current("dashboard")

    def _add_button(self, layout: QVBoxLayout, key: str, label_key: str, tip_key: str) -> None:
        button = QPushButton()
        button.setObjectName("navButton")
        button.setCheckable(True)
        button.setAutoExclusive(True)
        button.clicked.connect(lambda _checked=False, page=key: self.pageSelected.emit(page))
        layout.addWidget(button)
        self.buttons[key] = button
        self._label_keys[key] = label_key
        self._tooltip_keys[key] = tip_key

    def retranslate_ui(self) -> None:
        self.tagline.setText(self.i18n.t("app.subtitle"))
        self.workspace_section.setText(self.i18n.t("nav.workspace"))
        self.integrations_section.setText(self.i18n.t("nav.integrations"))
        self.privacy.setText(self.i18n.t("nav.footer"))
        app = QApplication.instance()
        modern = bool(app is not None and app.property("devnestUiMode") == "modern")
        trash_prefix = "" if modern else "🗑  "
        self.trash_button.setText(trash_prefix + ("Çöp Kutusu" if self.i18n.language == "tr" else "Trash"))
        self.trash_button.setToolTip(
            "Tek tek sildiğiniz notları ve tamamını sildiğiniz projeleri burada görürsünüz. Projeler, içindeki not/karar/diyagramlarla birlikte tek paket olarak tutulur."
            if self.i18n.language == "tr" else
            "See individually deleted notes and entire deleted projects here. Projects stay grouped with their notes, decisions and diagrams as one bundle."
        )
        cloud_prefix = "" if modern else "☁  "
        if self._online_connected:
            label = (f"{cloud_prefix}Online · {self._online_username}" if self._online_username else f"{cloud_prefix}Online")
            self.online_button.setText(label)
            self.online_button.setToolTip("Online yedekleme seçimini ve hesabı yönet." if self.i18n.language == "tr" else "Manage online backup selection and account.")
        else:
            self.online_button.setText(cloud_prefix + ("Online'a bağlan" if self.i18n.language == "tr" else "Connect online"))
            self.online_button.setToolTip("Supabase destekli DevNest Online hesabına bağlan." if self.i18n.language == "tr" else "Connect to your Supabase-backed DevNest Online account.")
        for key, button in self.buttons.items():
            label = self.i18n.t(self._label_keys[key])
            if key == "teams" and self._team_badge:
                label = f"{label}  {self._team_badge}"
            button.setText(label)
            button.setToolTip(self.i18n.t(self._tooltip_keys[key]))

    def set_current(self, key: str) -> None:
        if key in self.buttons:
            self.buttons[key].setChecked(True)

    def set_team_badge(self, count: int) -> None:
        self._team_badge = max(0, int(count))
        self.retranslate_ui()

    def set_online_state(self, connected: bool, username: str = "") -> None:
        self._online_connected = bool(connected)
        self._online_username = username.strip()
        self.retranslate_ui()

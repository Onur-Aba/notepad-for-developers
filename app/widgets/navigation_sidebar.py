from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from app.i18n import I18n

NAV_ITEMS = (
    ("dashboard", "nav.dashboard", "tip.nav.dashboard"),
    ("projects", "nav.projects", "tip.nav.projects"),
    ("notes", "nav.notes", "tip.nav.notes"),
    ("decisions", "nav.decisions", "tip.nav.decisions"),
    ("architecture", "nav.architecture", "tip.nav.architecture"),
    ("review", "nav.review", "tip.nav.review"),
)
INTEGRATION_ITEMS = (
    ("github", "nav.github", "tip.nav.github"),
    ("settings", "nav.settings", "tip.nav.settings"),
)


class NavigationSidebar(QWidget):
    pageSelected = Signal(str)

    def __init__(self, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.i18n = i18n
        self.setObjectName("globalNavigation")
        self.setFixedWidth(224)
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
        button.setCursor(button.cursor())
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
        for key, button in self.buttons.items():
            button.setText(self.i18n.t(self._label_keys[key]))
            button.setToolTip(self.i18n.t(self._tooltip_keys[key]))

    def set_current(self, key: str) -> None:
        if key in self.buttons:
            self.buttons[key].setChecked(True)

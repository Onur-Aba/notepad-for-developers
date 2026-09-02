from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from app.i18n import I18n
from app.integrations.supabase.client import SupabaseClient, SupabaseError


class CloudAccountDialog(QDialog):
    """Sign-up/sign-in dialog. Passwords are never persisted by DevNest."""

    def __init__(self, client: SupabaseClient, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.client = client
        self.i18n = i18n
        self.authenticated = False
        tr = i18n.language == "tr"
        self.setWindowTitle("DevNest Online" if not tr else "DevNest Online'a bağlan")
        self.resize(520, 540)
        root = QVBoxLayout(self)
        title = QLabel("DevNest Online")
        title.setObjectName("pageTitle")
        root.addWidget(title)
        intro = QLabel(
            "Hesap bilgileri Supabase Auth üzerinden gönderilir. Parolanız DevNest veritabanına veya ayarlara kaydedilmez."
            if tr else
            "Account credentials are sent to Supabase Auth. Your password is never stored in the DevNest database or settings."
        )
        intro.setWordWrap(True); intro.setObjectName("pageSubtitle"); root.addWidget(intro)

        if not client.configured:
            warning = QLabel(
                "Supabase yapılandırılmamış. Önce DEVNEST_SUPABASE_URL ve DEVNEST_SUPABASE_PUBLISHABLE_KEY ortam değişkenlerini ayarlayın."
                if tr else
                "Supabase is not configured. Set DEVNEST_SUPABASE_URL and DEVNEST_SUPABASE_PUBLISHABLE_KEY first."
            )
            warning.setObjectName("helperBanner"); warning.setWordWrap(True); root.addWidget(warning)

        tabs = QTabWidget(); root.addWidget(tabs, 1)
        register = QWidget(); register_form = QFormLayout(register)
        self.first = QLineEdit(); self.first.setMaxLength(80)
        self.last = QLineEdit(); self.last.setMaxLength(80)
        self.username = QLineEdit(); self.username.setMaxLength(32)
        self.email = QLineEdit(); self.email.setMaxLength(254)
        self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.EchoMode.Password); self.password.setMaxLength(128)
        register_form.addRow("İsim" if tr else "First name", self.first)
        register_form.addRow("Soyisim" if tr else "Last name", self.last)
        register_form.addRow("Kullanıcı adı" if tr else "Username", self.username)
        register_form.addRow("E-posta" if tr else "Email", self.email)
        register_form.addRow("Parola" if tr else "Password", self.password)
        hint = QLabel(
            "Kullanıcı adı: 3-32 karakter (harf, sayı, _, . veya -). Parola en az 10 karakter."
            if tr else "Username: 3-32 characters (letters, numbers, _, . or -). Password: at least 10 characters."
        )
        hint.setWordWrap(True); hint.setObjectName("mutedText"); register_form.addRow("", hint)
        self.register_button = QPushButton("Hesap oluştur" if tr else "Create account")
        self.register_button.setObjectName("primaryButton"); self.register_button.clicked.connect(self._register)
        register_form.addRow("", self.register_button)
        tabs.addTab(register, "Kayıt ol" if tr else "Create account")

        login = QWidget(); login_form = QFormLayout(login)
        self.login_email = QLineEdit(); self.login_email.setMaxLength(254)
        self.login_password = QLineEdit(); self.login_password.setEchoMode(QLineEdit.EchoMode.Password); self.login_password.setMaxLength(128)
        login_form.addRow("E-posta" if tr else "Email", self.login_email)
        login_form.addRow("Parola" if tr else "Password", self.login_password)
        self.login_button = QPushButton("Giriş yap" if tr else "Sign in")
        self.login_button.setObjectName("primaryButton"); self.login_button.clicked.connect(self._login)
        login_form.addRow("", self.login_button)
        tabs.addTab(login, "Giriş yap" if tr else "Sign in")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("İptal" if tr else "Cancel")
        buttons.rejected.connect(self.reject); root.addWidget(buttons)

    def _register(self) -> None:
        tr = self.i18n.language == "tr"
        try:
            immediate = self.client.sign_up(
                self.first.text(), self.last.text(), self.username.text(), self.email.text(), self.password.text()
            )
        except SupabaseError as exc:
            QMessageBox.warning(self, "Kayıt başarısız" if tr else "Registration failed", str(exc)); return
        self.password.clear()
        if not immediate:
            QMessageBox.information(
                self, "E-postanı doğrula" if tr else "Confirm your email",
                "Supabase e-posta doğrulaması açık. E-postandaki bağlantıyı doğruladıktan sonra bu penceredeki Giriş yap sekmesinden giriş yap."
                if tr else
                "Supabase email confirmation is enabled. Confirm the link in your email, then use the Sign in tab in this window."
            )
            return
        self.authenticated = True
        self.accept()

    def _login(self) -> None:
        tr = self.i18n.language == "tr"
        try:
            self.client.sign_in(self.login_email.text(), self.login_password.text())
        except SupabaseError as exc:
            QMessageBox.warning(self, "Giriş başarısız" if tr else "Sign in failed", str(exc)); return
        self.login_password.clear()
        self.authenticated = True
        self.accept()

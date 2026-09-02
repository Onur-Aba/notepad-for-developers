from __future__ import annotations

import logging
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from app.constants import APP_NAME, ORGANIZATION_DOMAIN, ORGANIZATION_NAME, VERSION
from app.database import Database, DatabaseError
from app.main_window import MainWindow
from app.paths import resource_path
from app.services.logging_setup import configure_logging
from app.settings import SettingsManager
from app.themes.theme_manager import ThemeManager


def main() -> int:
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("DevNest.DevNest.2")
        except (AttributeError, OSError):
            pass
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(VERSION)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setOrganizationDomain(ORGANIZATION_DOMAIN)
    app.setDesktopFileName("devnest")

    icon_candidates = (
        resource_path("resources/devnest.ico") if sys.platform == "win32" else resource_path("resources/devnest.svg"),
        resource_path("resources/devnest.svg"),
    )
    for icon_path in icon_candidates:
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
            break

    configure_logging()
    logger = logging.getLogger(__name__)

    try:
        database = Database()
    except DatabaseError as exc:
        logger.exception("Application startup failed")
        QMessageBox.critical(None, "DevNest — Database Error", str(exc))
        return 1

    settings = SettingsManager()
    theme_manager = ThemeManager(app)
    window = MainWindow(database, settings, theme_manager)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

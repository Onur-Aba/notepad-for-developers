from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QWidget

from app.i18n import I18n


class TagsEditor(QWidget):
    tagsChanged = Signal(list)

    def __init__(self, i18n: I18n, parent=None) -> None:
        super().__init__(parent)
        self.i18n = i18n
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        self.label = QLabel()
        self.label.setObjectName("fieldLabel")
        self.edit = QLineEdit()
        self.edit.setObjectName("tagsInput")
        self.edit.editingFinished.connect(self._emit)
        layout.addWidget(self.label)
        layout.addWidget(self.edit, 1)
        self.i18n.languageChanged.connect(lambda _lang: self.retranslate_ui())
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        tr = self.i18n.language == "tr"
        self.label.setText("Etiketler" if tr else "Tags")
        self.edit.setPlaceholderText("backend, security, database…" if tr else "backend, security, database…")
        self.edit.setToolTip(
            "Virgülle ayırın. Zorunlu değildir; global aramada ve filtrelemede kullanılabilir."
            if tr else "Separate with commas. Tags are optional and searchable globally."
        )

    def set_tags(self, tags: list[str]) -> None:
        self.edit.blockSignals(True)
        self.edit.setText(", ".join(tags))
        self.edit.blockSignals(False)

    def tags(self) -> list[str]:
        return [part.strip().lstrip("#") for part in self.edit.text().split(",") if part.strip().lstrip("#")]

    def _emit(self) -> None:
        self.tagsChanged.emit(self.tags())

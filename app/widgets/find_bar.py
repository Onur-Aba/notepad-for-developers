from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QButtonGroup, QCheckBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget


class FindLineEdit(QLineEdit):
    escapePressed = Signal()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.escapePressed.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class EditorFindBar(QWidget):
    queryChanged = Signal(str)
    findRequested = Signal(str)
    closeRequested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("editorFindBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(7, 6, 7, 6)
        layout.setSpacing(6)

        self.query_edit = FindLineEdit(self)
        self.query_edit.setObjectName("editorFindInput")
        self.query_edit.setPlaceholderText("Find in note…")
        self.query_edit.setClearButtonEnabled(True)
        self.query_edit.setMinimumWidth(180)
        self.query_edit.setMaximumWidth(320)
        self.query_edit.textChanged.connect(self.queryChanged)
        self.query_edit.returnPressed.connect(self._emit_find)
        self.query_edit.escapePressed.connect(self.closeRequested)
        layout.addWidget(self.query_edit, 1)

        self.result_label = QLabel("0 matches", self)
        self.result_label.setObjectName("editorFindCount")
        self.result_label.setMinimumWidth(68)
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.result_label)

        self.down_checkbox = QCheckBox("↓ Down", self)
        self.down_checkbox.setObjectName("editorFindDirection")
        self.up_checkbox = QCheckBox("↑ Up", self)
        self.up_checkbox.setObjectName("editorFindDirection")
        self.direction_group = QButtonGroup(self)
        self.direction_group.setExclusive(True)
        self.direction_group.addButton(self.down_checkbox)
        self.direction_group.addButton(self.up_checkbox)
        self.down_checkbox.toggled.connect(self._ensure_direction_selected)
        self.up_checkbox.toggled.connect(self._ensure_direction_selected)
        self.down_checkbox.setChecked(True)
        layout.addWidget(self.down_checkbox)
        layout.addWidget(self.up_checkbox)

        self.find_button = QPushButton("Find", self)
        self.find_button.setObjectName("editorFindButton")
        self.find_button.setToolTip("Find the next match in the selected direction (Enter)")
        self.find_button.clicked.connect(self._emit_find)
        layout.addWidget(self.find_button)

        self.close_button = QPushButton("×", self)
        self.close_button.setObjectName("editorFindClose")
        self.close_button.setFixedWidth(30)
        self.close_button.setToolTip("Close search (Esc)")
        self.close_button.clicked.connect(self.closeRequested)
        layout.addWidget(self.close_button)

    def direction(self) -> str:
        return "up" if self.up_checkbox.isChecked() else "down"

    def set_query(self, text: str) -> None:
        self.query_edit.setText(text)

    def focus_query(self, select_all: bool = True) -> None:
        self.query_edit.setFocus(Qt.FocusReason.ShortcutFocusReason)
        if select_all:
            self.query_edit.selectAll()

    def set_result_count(self, count: int, active_index: int | None = None) -> None:
        if count <= 0:
            self.result_label.setText("0 matches")
        elif active_index is None:
            self.result_label.setText(f"{count} matches")
        else:
            self.result_label.setText(f"{active_index + 1} / {count}")

    def _ensure_direction_selected(self, _checked: bool) -> None:
        if not self.down_checkbox.isChecked() and not self.up_checkbox.isChecked():
            self.down_checkbox.setChecked(True)

    def _emit_find(self) -> None:
        if self.query_edit.text():
            self.findRequested.emit(self.direction())

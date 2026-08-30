from __future__ import annotations

import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QFontDatabase, QKeyEvent, QMouseEvent, QTextBlock, QTextCharFormat, QTextCursor, QTextListFormat
from PySide6.QtWidgets import QMenu, QTextEdit

from app.constants import TAB_SPACES

TASK_LINE_RE = re.compile(r"^(?P<indent>[ ]*)(?P<marker>☐|☑)(?: (?P<text>.*))?$")


class NoteEditor(QTextEdit):
    taskStateChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.auto_checkbox_enabled = True
        self.tab_spaces = TAB_SPACES
        self.base_font_size = 12
        self.setAcceptRichText(True)
        self.setUndoRedoEnabled(True)
        self.setPlaceholderText("Write notes, tasks, bugs, ideas, or plans…")
        self.setTabChangesFocus(False)
        self.setMouseTracking(True)
        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(self.base_font_size)
        self.setFont(font)

    def set_editor_font_size(self, size: int) -> None:
        self.base_font_size = max(8, min(32, size))
        font = self.font()
        font.setPointSize(self.base_font_size)
        self.setFont(font)

    def apply_font_family(self, family: str) -> None:
        if not family:
            return
        fmt = QTextCharFormat()
        fmt.setFontFamilies([family])
        self._merge_format(fmt)

    def apply_font_point_size(self, size: int) -> None:
        size = max(8, min(48, int(size)))
        fmt = QTextCharFormat()
        fmt.setFontPointSize(float(size))
        self._merge_format(fmt)

    def apply_font_weight(self, weight: int) -> None:
        weight = max(100, min(900, int(round(weight / 100.0) * 100)))
        fmt = QTextCharFormat()
        fmt.setFontWeight(weight)
        self._merge_format(fmt)

    def set_tab_width(self, spaces: int) -> None:
        self.tab_spaces = max(2, min(8, spaces))
        metrics = self.fontMetrics()
        self.setTabStopDistance(metrics.horizontalAdvance(" ") * self.tab_spaces)

    def set_auto_checkbox(self, enabled: bool) -> None:
        self.auto_checkbox_enabled = enabled

    def insert_checkbox(self) -> None:
        cursor = self.textCursor()
        block = cursor.block()
        match = TASK_LINE_RE.match(block.text())
        if match:
            self.toggle_checkbox(block)
            return
        block_pos = block.position()
        leading = len(block.text()) - len(block.text().lstrip(" "))
        cursor.setPosition(block_pos + leading)
        cursor.insertText("☐ ")
        self.setTextCursor(cursor)
        self._apply_task_style(cursor.block(), checked=False)
        self.taskStateChanged.emit()

    def toggle_checkbox_at_cursor(self) -> bool:
        block = self.textCursor().block()
        if not TASK_LINE_RE.match(block.text()):
            return False
        self.toggle_checkbox(block)
        return True

    def toggle_checkbox(self, block: QTextBlock) -> None:
        match = TASK_LINE_RE.match(block.text())
        if not match:
            return
        marker_pos = block.position() + len(match.group("indent"))
        cursor = QTextCursor(self.document())
        cursor.setPosition(marker_pos)
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
        checked = match.group("marker") == "☐"
        cursor.insertText("☑" if checked else "☐")
        updated_block = self.document().findBlock(marker_pos)
        self._apply_task_style(updated_block, checked=checked)
        self.taskStateChanged.emit()

    def _apply_task_style(self, block: QTextBlock, checked: bool) -> None:
        match = TASK_LINE_RE.match(block.text())
        if not match:
            return
        indent_len = len(match.group("indent"))
        marker_pos = block.position() + indent_len
        text_start = marker_pos + 1
        if block.text()[indent_len + 1 :].startswith(" "):
            text_start += 1

        marker_cursor = QTextCursor(self.document())
        marker_cursor.setPosition(marker_pos)
        marker_cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
        marker_fmt = QTextCharFormat()
        marker_fmt.setFontStrikeOut(False)
        marker_cursor.mergeCharFormat(marker_fmt)

        if text_start < block.position() + len(block.text()):
            text_cursor = QTextCursor(self.document())
            text_cursor.setPosition(text_start)
            text_cursor.setPosition(block.position() + len(block.text()), QTextCursor.MoveMode.KeepAnchor)
            text_fmt = QTextCharFormat()
            text_fmt.setFontStrikeOut(checked)
            text_cursor.mergeCharFormat(text_fmt)

    def toggle_bold(self) -> None:
        fmt = QTextCharFormat()
        current = self.textCursor().charFormat().fontWeight()
        fmt.setFontWeight(QFont.Weight.Normal if current >= QFont.Weight.Bold else QFont.Weight.Bold)
        self._merge_format(fmt)

    def toggle_italic(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self.textCursor().charFormat().fontItalic())
        self._merge_format(fmt)

    def toggle_underline(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not self.textCursor().charFormat().fontUnderline())
        self._merge_format(fmt)

    def toggle_strikethrough(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontStrikeOut(not self.textCursor().charFormat().fontStrikeOut())
        self._merge_format(fmt)

    def _merge_format(self, fmt: QTextCharFormat) -> None:
        cursor = self.textCursor()
        cursor.mergeCharFormat(fmt)
        self.mergeCurrentCharFormat(fmt)

    def set_heading(self, level: int) -> None:
        sizes = {0: self.base_font_size, 1: self.base_font_size + 10, 2: self.base_font_size + 6, 3: self.base_font_size + 3}
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        fmt = QTextCharFormat()
        fmt.setFontPointSize(sizes.get(level, self.base_font_size))
        fmt.setFontWeight(QFont.Weight.Bold if level else QFont.Weight.Normal)
        cursor.mergeCharFormat(fmt)

    def make_bullet_list(self) -> None:
        self._make_list(QTextListFormat.Style.ListDisc)

    def make_numbered_list(self) -> None:
        self._make_list(QTextListFormat.Style.ListDecimal)

    def _make_list(self, style: QTextListFormat.Style) -> None:
        cursor = self.textCursor()
        list_format = QTextListFormat()
        list_format.setStyle(style)
        current_list = cursor.currentList()
        if current_list is not None:
            list_format.setIndent(current_list.format().indent())
        else:
            list_format.setIndent(1)
        cursor.createList(list_format)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        modifiers = event.modifiers()

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.auto_checkbox_enabled:
            if self._handle_task_enter():
                return

        if key == Qt.Key.Key_Tab and not (modifiers & Qt.KeyboardModifier.ControlModifier):
            if self._handle_task_indent(outdent=bool(modifiers & Qt.KeyboardModifier.ShiftModifier)):
                return

        if key == Qt.Key.Key_Backtab:
            if self._handle_task_indent(outdent=True):
                return

        super().keyPressEvent(event)

    def _handle_task_enter(self) -> bool:
        cursor = self.textCursor()
        if cursor.hasSelection():
            return False
        block = cursor.block()
        match = TASK_LINE_RE.match(block.text())
        if not match:
            return False

        text = (match.group("text") or "").strip()
        indent = match.group("indent")
        if not text:
            marker_start = block.position() + len(indent)
            remove_cursor = QTextCursor(self.document())
            remove_cursor.setPosition(marker_start)
            remove_cursor.setPosition(block.position() + len(block.text()), QTextCursor.MoveMode.KeepAnchor)
            remove_cursor.removeSelectedText()
            remove_cursor.setPosition(marker_start)
            self.setTextCursor(remove_cursor)
            return True

        checked = match.group("marker") == "☑"
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
        cursor.insertBlock()
        cursor.insertText(f"{indent}☐ ")
        self.setTextCursor(cursor)
        self._apply_task_style(block, checked=checked)
        self._apply_task_style(cursor.block(), checked=False)
        reset_fmt = QTextCharFormat()
        reset_fmt.setFontStrikeOut(False)
        self.mergeCurrentCharFormat(reset_fmt)
        return True

    def _handle_task_indent(self, outdent: bool) -> bool:
        cursor = self.textCursor()
        block = cursor.block()
        match = TASK_LINE_RE.match(block.text())
        if not match:
            return False
        block_start = block.position()
        old_pos = cursor.position()
        leading = match.group("indent")
        edit = QTextCursor(self.document())
        if outdent:
            remove_count = min(self.tab_spaces, len(leading))
            if remove_count == 0:
                return True
            edit.setPosition(block_start)
            edit.setPosition(block_start + remove_count, QTextCursor.MoveMode.KeepAnchor)
            edit.removeSelectedText()
            cursor.setPosition(max(block_start, old_pos - remove_count))
        else:
            edit.setPosition(block_start)
            edit.insertText(" " * self.tab_spaces)
            cursor.setPosition(old_pos + self.tab_spaces)
        self.setTextCursor(cursor)
        return True

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            cursor = self.cursorForPosition(event.position().toPoint())
            block = cursor.block()
            match = TASK_LINE_RE.match(block.text())
            if match:
                marker_index = len(match.group("indent"))
                relative = cursor.position() - block.position()
                if relative in {marker_index, marker_index + 1}:
                    self.toggle_checkbox(block)
                    event.accept()
                    return
        super().mousePressEvent(event)

    def contextMenuEvent(self, event) -> None:
        menu: QMenu = self.createStandardContextMenu()
        menu.addSeparator()
        add_checkbox = menu.addAction("Add / Toggle Checkbox")
        add_checkbox.triggered.connect(self.insert_checkbox)
        toggle_checked = menu.addAction("Toggle Checked")
        toggle_checked.setEnabled(bool(TASK_LINE_RE.match(self.textCursor().block().text())))
        toggle_checked.triggered.connect(self.toggle_checkbox_at_cursor)
        strike = menu.addAction("Strikethrough")
        strike.triggered.connect(self.toggle_strikethrough)
        menu.exec(event.globalPos())

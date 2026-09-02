from __future__ import annotations

import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QTextBlock,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextFormat,
    QTextListFormat,
)
from PySide6.QtWidgets import QApplication, QMenu, QScrollBar, QTextEdit

from app.widgets.find_bar import EditorFindBar

from app.constants import TAB_SPACES

TASK_LINE_RE = re.compile(r"^(?P<indent>[ ]*)(?P<marker>☐|☑)(?: (?P<text>.*))?$")
NUMBERED_TEXT_LINE_RE = re.compile(r"^(?P<indent>[ ]*)(?P<number>\d+)\.(?: (?P<text>.*))?$")

class SearchMarkerScrollBar(QScrollBar):
    def __init__(self, orientation: Qt.Orientation, parent=None) -> None:
        super().__init__(orientation, parent)
        self._markers: list[float] = []
        self._active_marker: float | None = None
        self._marker_color = QColor("#d0a84b")
        self._active_color = QColor("#f2cf70")

    def set_markers(self, markers: list[float], active_marker: float | None = None) -> None:
        self._markers = [max(0.0, min(1.0, marker)) for marker in markers]
        self._active_marker = None if active_marker is None else max(0.0, min(1.0, active_marker))
        self.update()

    def set_marker_colors(self, marker: str, active: str) -> None:
        self._marker_color = QColor(marker)
        self._active_color = QColor(active)
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self.orientation() != Qt.Orientation.Vertical or not self._markers:
            return
        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)
        top = 2
        marker_height = 2
        usable_height = max(1, self.height() - top * 2 - marker_height)
        width = max(3, self.width() - 4)
        for ratio in self._markers:
            y = top + int(round(ratio * usable_height))
            painter.fillRect(2, y, width, marker_height, self._marker_color)
        if self._active_marker is not None:
            y = top + int(round(self._active_marker * usable_height))
            painter.fillRect(1, max(0, y - 1), max(4, self.width() - 2), 4, self._active_color)


class NoteEditor(QTextEdit):
    taskStateChanged = Signal()
    numberedListModeChanged = Signal(bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.auto_checkbox_enabled = True
        self.blank_line_after_enter = False
        self.numbered_list_mode_enabled = False
        self.tab_spaces = TAB_SPACES
        self.base_font_size = 12
        self.setAcceptRichText(True)
        self.setUndoRedoEnabled(True)
        self.setPlaceholderText("Write notes, tasks, bugs, ideas, or plans…")
        self.setTabChangesFocus(False)
        self.setMouseTracking(True)

        self._search_query = ""
        self._search_ranges: list[tuple[int, int]] = []
        self._search_active_index: int | None = None
        self._search_anchor_position = 0
        self._search_match_background = QColor("#d9c36a")
        self._search_match_foreground = QColor("#1a1a1a")
        self._search_current_background = QColor("#f0b94d")
        self._search_current_foreground = QColor("#111111")

        self._search_scrollbar = SearchMarkerScrollBar(Qt.Orientation.Vertical, self)
        self.setVerticalScrollBar(self._search_scrollbar)
        self.find_bar = EditorFindBar(self)
        self.find_bar.hide()
        self.find_bar.queryChanged.connect(self._set_search_query)
        self.find_bar.findRequested.connect(self.find_search_match)
        self.find_bar.closeRequested.connect(self.hide_find_bar)
        self.textChanged.connect(self._refresh_search_after_edit)

        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(self.base_font_size)
        self.setFont(font)
        self.retranslate_ui()

    def _is_tr(self) -> bool:
        app = QApplication.instance()
        return bool(app is not None and app.property("devnestLanguage") == "tr")

    def retranslate_ui(self) -> None:
        self.setPlaceholderText(
            "Notlarınızı, görevlerinizi, hataları, fikirleri veya planları yazın…"
            if self._is_tr() else
            "Write notes, tasks, bugs, ideas, or plans…"
        )
        self.find_bar.retranslate_ui()

    def show_find_bar(self) -> None:
        selected = self.textCursor().selectedText().replace("\u2029", "\n")
        if selected and "\n" not in selected and len(selected) <= 160:
            self.find_bar.set_query(selected)
        self._search_anchor_position = self.textCursor().selectionEnd()
        self.find_bar.show()
        self.find_bar.raise_()
        self._position_find_bar()
        if self.find_bar.query_edit.text():
            self._set_search_query(self.find_bar.query_edit.text())
        self.find_bar.focus_query(select_all=True)

    def hide_find_bar(self) -> None:
        self.find_bar.hide()
        self._search_query = ""
        self._search_ranges.clear()
        self._search_active_index = None
        self.setExtraSelections([])
        self._search_scrollbar.set_markers([])
        self.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def is_find_bar_visible(self) -> bool:
        return self.find_bar.isVisible()

    def search_match_ranges(self) -> tuple[tuple[int, int], ...]:
        return tuple(self._search_ranges)

    def active_search_range(self) -> tuple[int, int] | None:
        if self._search_active_index is None or not self._search_ranges:
            return None
        return self._search_ranges[self._search_active_index]

    def set_search_theme(
        self,
        *,
        match_background: str,
        match_foreground: str,
        current_background: str,
        current_foreground: str,
        marker: str,
        current_marker: str,
    ) -> None:
        self._search_match_background = QColor(match_background)
        self._search_match_foreground = QColor(match_foreground)
        self._search_current_background = QColor(current_background)
        self._search_current_foreground = QColor(current_foreground)
        self._search_scrollbar.set_marker_colors(marker, current_marker)
        self._render_search_highlights()

    def find_search_match(self, direction: str = "down") -> bool:
        if not self._search_ranges:
            self.find_bar.set_result_count(0)
            return False

        direction = "up" if direction == "up" else "down"
        if self._search_active_index is None:
            self._search_active_index = self._initial_search_index(direction)
        elif direction == "down":
            self._search_active_index = (self._search_active_index + 1) % len(self._search_ranges)
        else:
            self._search_active_index = (self._search_active_index - 1) % len(self._search_ranges)

        start, end = self._search_ranges[self._search_active_index]
        cursor = QTextCursor(self.document())
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
        self.find_bar.set_result_count(len(self._search_ranges), self._search_active_index)
        self._render_search_highlights()
        return True

    def _initial_search_index(self, direction: str) -> int:
        anchor = max(0, min(self.document().characterCount() - 1, self._search_anchor_position))
        if direction == "up":
            for index in range(len(self._search_ranges) - 1, -1, -1):
                start, end = self._search_ranges[index]
                if end <= anchor:
                    return index
            return len(self._search_ranges) - 1
        for index, (start, _end) in enumerate(self._search_ranges):
            if start >= anchor:
                return index
        return 0

    def _set_search_query(self, query: str) -> None:
        self._search_query = query
        self._search_active_index = None
        self._search_anchor_position = self.textCursor().selectionEnd()
        self._collect_search_matches()
        self.find_bar.set_result_count(len(self._search_ranges))
        self._render_search_highlights()

    def _refresh_search_after_edit(self) -> None:
        if not self._search_query:
            return
        active_start = None
        if self._search_active_index is not None and self._search_ranges:
            active_start = self._search_ranges[self._search_active_index][0]
        self._collect_search_matches()
        self._search_active_index = None
        if active_start is not None and self._search_ranges:
            nearest = min(range(len(self._search_ranges)), key=lambda index: abs(self._search_ranges[index][0] - active_start))
            self._search_active_index = nearest
        self.find_bar.set_result_count(len(self._search_ranges), self._search_active_index)
        self._render_search_highlights()

    def _collect_search_matches(self) -> None:
        self._search_ranges.clear()
        query = self._search_query
        if not query:
            return
        document = self.document()
        cursor = QTextCursor(document)
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        while True:
            match = document.find(query, cursor)
            if match.isNull() or not match.hasSelection():
                break
            start = match.selectionStart()
            end = match.selectionEnd()
            if end <= start:
                break
            self._search_ranges.append((start, end))
            cursor.setPosition(end)

    def _render_search_highlights(self) -> None:
        selections: list[QTextEdit.ExtraSelection] = []
        for index, (start, end) in enumerate(self._search_ranges):
            selection = QTextEdit.ExtraSelection()
            cursor = QTextCursor(self.document())
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            selection.cursor = cursor
            if index == self._search_active_index:
                selection.format.setBackground(self._search_current_background)
                selection.format.setForeground(self._search_current_foreground)
            else:
                selection.format.setBackground(self._search_match_background)
                selection.format.setForeground(self._search_match_foreground)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, False)
            selections.append(selection)
        self.setExtraSelections(selections)
        marker_positions = [self._search_marker_ratio(start) for start, _end in self._search_ranges]
        active_marker = None
        if self._search_active_index is not None and self._search_ranges:
            active_marker = marker_positions[self._search_active_index]
        self._search_scrollbar.set_markers(marker_positions, active_marker)

    def _search_marker_ratio(self, position: int) -> float:
        document = self.document()
        document_height = max(1.0, document.size().height())
        cursor = QTextCursor(document)
        cursor.setPosition(max(0, min(position, document.characterCount() - 1)))
        block = cursor.block()
        layout = block.layout()
        block_rect = document.documentLayout().blockBoundingRect(block)
        line = layout.lineForTextPosition(cursor.positionInBlock()) if layout is not None else None
        y = block_rect.top()
        if line is not None and line.isValid():
            y += line.y() + line.height() / 2.0
        return max(0.0, min(1.0, y / document_height))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._position_find_bar()

    def _position_find_bar(self) -> None:
        if not self.find_bar.isVisible():
            return
        self.find_bar.adjustSize()
        available_width = max(260, self.viewport().width() - 18)
        width = min(max(self.find_bar.sizeHint().width(), 520), available_width)
        self.find_bar.resize(width, self.find_bar.sizeHint().height())
        x = max(6, self.viewport().geometry().right() - width - 6)
        y = self.viewport().geometry().top() + 6
        self.find_bar.move(x, y)
        self.find_bar.raise_()

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
        self._merge_font_format(fmt)

    def apply_font_point_size(self, size: int) -> None:
        size = max(8, min(48, int(size)))
        fmt = QTextCharFormat()
        fmt.setFontPointSize(float(size))
        self._merge_font_format(fmt)

    def apply_font_weight(self, weight: int) -> None:
        weight = max(100, min(900, int(round(weight / 100.0) * 100)))
        fmt = QTextCharFormat()
        fmt.setFontWeight(weight)
        self._merge_font_format(fmt)

    def set_tab_width(self, spaces: int) -> None:
        self.tab_spaces = max(2, min(8, spaces))
        metrics = self.fontMetrics()
        self.setTabStopDistance(metrics.horizontalAdvance(" ") * self.tab_spaces)

    def set_auto_checkbox(self, enabled: bool, apply_to_document: bool = False) -> None:
        self.auto_checkbox_enabled = enabled
        if apply_to_document:
            self.apply_auto_checkbox_to_document(enabled)

    def apply_auto_checkbox_to_document(self, enabled: bool) -> None:
        """Turn every non-empty text line into/out of a task line in one undo step."""
        document = self.document()
        blocks: list[QTextBlock] = []
        block = document.firstBlock()
        while block.isValid():
            blocks.append(block)
            block = block.next()
        edit = QTextCursor(document)
        edit.beginEditBlock()
        try:
            for block in reversed(blocks):
                text = block.text()
                match = TASK_LINE_RE.match(text)
                if enabled:
                    if not text.strip() or match:
                        continue
                    leading = len(text) - len(text.lstrip(" "))
                    cursor = QTextCursor(document)
                    cursor.setPosition(block.position() + leading)
                    cursor.insertText("☐ ")
                else:
                    if not match:
                        continue
                    leading = len(match.group("indent"))
                    marker_start = block.position() + leading
                    remove_count = 1
                    if text[leading + 1:].startswith(" "):
                        remove_count += 1
                    cursor = QTextCursor(document)
                    cursor.setPosition(marker_start)
                    cursor.setPosition(marker_start + remove_count, QTextCursor.MoveMode.KeepAnchor)
                    cursor.removeSelectedText()
        finally:
            edit.endEditBlock()
        if enabled:
            block = document.firstBlock()
            while block.isValid():
                match = TASK_LINE_RE.match(block.text())
                if match:
                    self._apply_task_style(block, checked=match.group("marker") == "☑")
                block = block.next()
        self.taskStateChanged.emit()

    def set_blank_line_after_enter(self, enabled: bool) -> None:
        self.blank_line_after_enter = enabled

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
        self._merge_font_format(fmt)

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

    def _merge_font_format(self, fmt: QTextCharFormat) -> None:
        """Apply font properties without leaving task/list markers behind.

        Checkbox markers are ordinary document characters, while Qt bullet and
        numbered-list markers are block decorations.  When the cursor is on a
        decorated line we therefore update both the text fragments and the
        block character format used to paint the list marker.
        """
        visible_cursor = self.textCursor()
        start = visible_cursor.selectionStart()
        end = visible_cursor.selectionEnd()

        if visible_cursor.hasSelection():
            visible_cursor.mergeCharFormat(fmt)
            self._format_decorated_markers(start, end, fmt)
            self.setTextCursor(visible_cursor)
            self.mergeCurrentCharFormat(fmt)
            return

        block = visible_cursor.block()
        is_task = bool(TASK_LINE_RE.match(block.text()))
        is_list_item = block.textList() is not None
        if is_task or is_list_item:
            line_cursor = QTextCursor(self.document())
            line_cursor.setPosition(block.position())
            line_cursor.setPosition(block.position() + len(block.text()), QTextCursor.MoveMode.KeepAnchor)
            if line_cursor.hasSelection():
                line_cursor.mergeCharFormat(fmt)
            if is_list_item:
                block_cursor = QTextCursor(block)
                block_cursor.mergeBlockCharFormat(fmt)
            self.setTextCursor(visible_cursor)
            self.mergeCurrentCharFormat(fmt)
            return

        visible_cursor.mergeCharFormat(fmt)
        self.setTextCursor(visible_cursor)
        self.mergeCurrentCharFormat(fmt)

    def _format_decorated_markers(self, start: int, end: int, fmt: QTextCharFormat) -> None:
        document = self.document()
        block = document.findBlock(start)
        if end > start and document.findBlock(end).position() == end:
            last_position = max(start, end - 1)
        else:
            last_position = end
        last_block = document.findBlock(last_position)

        while block.isValid():
            task_match = TASK_LINE_RE.match(block.text())
            if task_match:
                marker_position = block.position() + len(task_match.group("indent"))
                marker_cursor = QTextCursor(document)
                marker_cursor.setPosition(marker_position)
                marker_cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
                marker_cursor.mergeCharFormat(fmt)
            if block.textList() is not None:
                block_cursor = QTextCursor(block)
                block_cursor.mergeBlockCharFormat(fmt)
            if block == last_block:
                break
            block = block.next()

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
        """Enable the plain-text numbered list mode.

        Unlike QTextList's decimal markers, these numbers are real document
        characters so Select All / Copy / TXT export includes them.
        """
        self.set_numbered_list_mode(True)

    def set_numbered_list_mode(self, enabled: bool) -> None:
        self.numbered_list_mode_enabled = bool(enabled)
        if self.numbered_list_mode_enabled:
            self._number_selected_or_current_blocks()

    def _number_selected_or_current_blocks(self) -> None:
        visible_cursor = self.textCursor()
        document = self.document()
        selection_start = visible_cursor.selectionStart()
        selection_end = visible_cursor.selectionEnd()
        original_position = visible_cursor.position()
        original_position_in_block = visible_cursor.positionInBlock()
        original_block_text = visible_cursor.block().text()
        original_match = NUMBERED_TEXT_LINE_RE.match(original_block_text)
        original_indent_len = (
            len(original_match.group("indent"))
            if original_match
            else len(original_block_text) - len(original_block_text.lstrip(" "))
        )
        original_prefix_len = 0
        if original_match:
            original_prefix = f"{original_match.group('number')}."
            if original_block_text[len(original_match.group("indent")) + len(original_prefix) :].startswith(" "):
                original_prefix += " "
            original_prefix_len = len(original_prefix)
            if not visible_cursor.hasSelection():
                # Re-enabling the mode on an existing numbered item should
                # continue from that number instead of resetting it to 1.
                return

        end_lookup = max(selection_start, selection_end - 1) if visible_cursor.hasSelection() else selection_start
        first_block = document.findBlock(selection_start)
        last_block = document.findBlock(end_lookup)

        blocks: list[QTextBlock] = []
        block = first_block
        while block.isValid():
            blocks.append(block)
            if block == last_block:
                break
            block = block.next()

        # Edit from bottom to top so positions of blocks that still need work
        # remain stable while prefixes are inserted/replaced.
        edit = QTextCursor(document)
        edit.beginEditBlock()
        try:
            for number, block in reversed(list(enumerate(blocks, start=1))):
                text = block.text()
                existing = NUMBERED_TEXT_LINE_RE.match(text)
                indent = existing.group("indent") if existing else text[: len(text) - len(text.lstrip(" "))]
                prefix_start = block.position() + len(indent)
                block_cursor = QTextCursor(document)
                block_cursor.setPosition(prefix_start)
                if existing:
                    old_prefix = f"{existing.group('number')}."
                    if text[len(indent) + len(old_prefix) :].startswith(" "):
                        old_prefix += " "
                    block_cursor.setPosition(prefix_start + len(old_prefix), QTextCursor.MoveMode.KeepAnchor)
                block_cursor.insertText(f"{number}. ")
        finally:
            edit.endEditBlock()

        # Preserve the caret relative to the user's text. The prefix is real
        # text, so a cursor positioned after the insertion point must move by
        # exactly the prefix length delta.
        if not visible_cursor.hasSelection() and blocks:
            new_prefix_len = len("1. ")
            prefix_delta = new_prefix_len - original_prefix_len
            new_position = original_position
            if original_position_in_block >= original_indent_len:
                new_position += prefix_delta
            current = QTextCursor(document)
            current.setPosition(max(0, min(document.characterCount() - 1, new_position)))
            self.setTextCursor(current)

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

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.numbered_list_mode_enabled and self._handle_numbered_list_enter():
                return
            if self.auto_checkbox_enabled and self._handle_auto_checkbox_enter():
                return
            if self.blank_line_after_enter:
                self._handle_spaced_enter(event)
                return

        if key == Qt.Key.Key_Tab and not (modifiers & Qt.KeyboardModifier.ControlModifier):
            if self._handle_task_indent(outdent=bool(modifiers & Qt.KeyboardModifier.ShiftModifier)):
                return

        if key == Qt.Key.Key_Backtab:
            if self._handle_task_indent(outdent=True):
                return

        super().keyPressEvent(event)

    def _handle_numbered_list_enter(self) -> bool:
        cursor = self.textCursor()
        if cursor.hasSelection():
            return False
        block = cursor.block()
        match = NUMBERED_TEXT_LINE_RE.match(block.text())
        if not match:
            return False

        item_text = (match.group("text") or "").strip()
        indent = match.group("indent")
        number = int(match.group("number"))
        if not item_text:
            marker_start = block.position() + len(indent)
            remove_cursor = QTextCursor(self.document())
            remove_cursor.setPosition(marker_start)
            remove_cursor.setPosition(block.position() + len(block.text()), QTextCursor.MoveMode.KeepAnchor)
            remove_cursor.removeSelectedText()
            remove_cursor.setPosition(marker_start)
            self.setTextCursor(remove_cursor)
            self.numbered_list_mode_enabled = False
            self.numberedListModeChanged.emit(False)
            return True

        cursor.insertBlock()
        if self.blank_line_after_enter:
            cursor.insertBlock()
        cursor.insertText(f"{indent}{number + 1}. ")
        self.setTextCursor(cursor)
        return True

    def _handle_auto_checkbox_enter(self) -> bool:
        """Continue Auto Checkbox on *every* Enter press while the mode is enabled.

        Existing task lines keep their indentation and split text at the caret.
        If a legacy/plain line somehow exists while Auto Checkbox is on, Enter
        still starts the new line with a fresh unchecked marker. This makes the
        mode deterministic instead of depending on whether the current line was
        already converted when the toggle was enabled.
        """
        cursor = self.textCursor()
        if cursor.hasSelection():
            return False
        if TASK_LINE_RE.match(cursor.block().text()):
            return self._handle_task_enter()

        cursor.insertBlock()
        if self.blank_line_after_enter:
            cursor.insertBlock()
        cursor.insertText("☐ ")
        self.setTextCursor(cursor)
        self._apply_task_style(cursor.block(), checked=False)
        reset_fmt = QTextCharFormat()
        reset_fmt.setFontStrikeOut(False)
        self.mergeCurrentCharFormat(reset_fmt)
        return True

    def _handle_task_enter(self) -> bool:
        cursor = self.textCursor()
        if cursor.hasSelection():
            return False
        block = cursor.block()
        match = TASK_LINE_RE.match(block.text())
        if not match:
            return False

        indent = match.group("indent")
        marker = match.group("marker")
        marker_text_start = block.position() + len(indent) + 1
        if block.text()[len(indent) + 1:].startswith(" "):
            marker_text_start += 1
        block_end = block.position() + len(block.text())
        caret = cursor.position()

        # Enter inside a task must split the line exactly at the caret. Any text
        # to the right moves after the checkbox on the next line instead of
        # being stranded on the previous line.
        tail = ""
        if caret < block_end:
            tail_cursor = QTextCursor(self.document())
            tail_cursor.setPosition(caret)
            tail_cursor.setPosition(block_end, QTextCursor.MoveMode.KeepAnchor)
            tail = tail_cursor.selectedText().replace("\u2029", "\n")
            tail_cursor.removeSelectedText()
            cursor = self.textCursor()
            cursor.setPosition(caret)

        cursor.insertBlock()
        if self.blank_line_after_enter:
            cursor.insertBlock()
        cursor.insertText(f"{indent}☐ ")
        if tail:
            cursor.insertText(tail)
        self.setTextCursor(cursor)
        previous_block = cursor.block().previous()
        if previous_block.isValid():
            self._apply_task_style(previous_block, checked=marker == "☑")
        self._apply_task_style(cursor.block(), checked=False)
        reset_fmt = QTextCharFormat()
        reset_fmt.setFontStrikeOut(False)
        self.mergeCurrentCharFormat(reset_fmt)
        return True

    def _handle_spaced_enter(self, event: QKeyEvent) -> None:
        """Handle Enter as two native Enter presses, leaving one blank line."""
        super().keyPressEvent(event)
        cursor = self.textCursor()
        cursor.insertBlock()
        self.setTextCursor(cursor)

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
        strike = menu.addAction("Üstü çizili" if tr else "Strikethrough")
        strike.triggered.connect(self.toggle_strikethrough)
        menu.exec(event.globalPos())

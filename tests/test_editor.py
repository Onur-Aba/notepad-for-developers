from __future__ import annotations

import pytest

pytest.importorskip("PySide6.QtWidgets")
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication

from app.services.txt_codec import import_text_to_html
from app.widgets.note_editor import NoteEditor


@pytest.fixture(scope="module")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _character_strike_out(editor: NoteEditor, position: int) -> bool:
    """Return the format of the character that starts at *position*.

    QTextCursor.charFormat() at a bare boundary position describes the cursor's
    insertion format and can reflect the character immediately before it.
    Selecting the character makes the assertion deterministic across Qt builds.
    """
    cursor = QTextCursor(editor.document())
    cursor.setPosition(position)
    cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
    return cursor.charFormat().fontStrikeOut()


def test_checkbox_toggle_applies_and_removes_strike(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("☐ API'yi hazırla")
    block = editor.document().firstBlock()
    editor.toggle_checkbox(block)
    assert editor.toPlainText().startswith("☑")

    checked_block = editor.document().firstBlock()
    first_task_char = checked_block.position() + 2
    last_task_char = checked_block.position() + len(checked_block.text()) - 1
    assert _character_strike_out(editor, first_task_char) is True
    assert _character_strike_out(editor, last_task_char) is True

    editor.toggle_checkbox(checked_block)
    assert editor.toPlainText().startswith("☐")
    unchecked_block = editor.document().firstBlock()
    first_task_char = unchecked_block.position() + 2
    last_task_char = unchecked_block.position() + len(unchecked_block.text()) - 1
    assert _character_strike_out(editor, first_task_char) is False
    assert _character_strike_out(editor, last_task_char) is False


def test_imported_checkbox_html_stays_recognizable(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setHtml(import_text_to_html("    [x] Database\n[ ] API"))
    assert editor.toPlainText().splitlines() == ["    ☑ Database", "☐ API"]


def test_auto_checkbox_enter_continues_task(app: QApplication) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor = NoteEditor()
    editor.set_auto_checkbox(True)
    editor.setPlainText("☐ Backend")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText() == "☐ Backend\n☐ "


def test_empty_auto_checkbox_enter_continues_task_mode(app: QApplication) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor = NoteEditor()
    editor.set_auto_checkbox(True)
    editor.setPlainText("☐ ")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText() == "☐ \n☐ "


def test_font_controls_apply_rich_text_formatting(app: QApplication) -> None:
    from PySide6.QtGui import QFont

    editor = NoteEditor()
    editor.setPlainText("format me")
    cursor = editor.textCursor()
    cursor.select(QTextCursor.SelectionType.Document)
    editor.setTextCursor(cursor)
    family = editor.font().family()
    editor.apply_font_family(family)
    editor.apply_font_point_size(18)
    editor.apply_font_weight(800)

    fmt = editor.textCursor().charFormat()
    assert round(fmt.fontPointSize()) == 18
    assert int(fmt.fontWeight()) == int(QFont.Weight.ExtraBold)
    assert family in fmt.font().families() or fmt.font().family() == family



def _character_format(editor: NoteEditor, position: int):
    cursor = QTextCursor(editor.document())
    cursor.setPosition(position)
    cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
    return cursor.charFormat()


def test_font_controls_apply_to_checkbox_marker_and_whole_task_line(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("☐ API endpoint")
    cursor = editor.textCursor()
    cursor.setPosition(len("☐ API"))
    editor.setTextCursor(cursor)

    editor.apply_font_point_size(20)
    editor.apply_font_weight(700)

    block = editor.document().firstBlock()
    marker_fmt = _character_format(editor, block.position())
    text_fmt = _character_format(editor, block.position() + 2)
    assert round(marker_fmt.fontPointSize()) == 20
    assert round(text_fmt.fontPointSize()) == 20
    assert int(marker_fmt.fontWeight()) == 700
    assert int(text_fmt.fontWeight()) == 700


def test_font_controls_apply_to_bullet_list_marker_block_format(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("Bullet item")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.Start)
    editor.setTextCursor(cursor)
    editor.make_bullet_list()
    editor.apply_font_point_size(19)
    editor.apply_font_weight(700)

    block = editor.document().firstBlock()
    assert block.textList() is not None
    assert round(block.charFormat().fontPointSize()) == 19
    assert int(block.charFormat().fontWeight()) == 700
    text_fmt = _character_format(editor, block.position())
    assert round(text_fmt.fontPointSize()) == 19
    assert int(text_fmt.fontWeight()) == 700


def test_blank_line_after_enter_setting(app: QApplication) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor = NoteEditor()
    editor.set_auto_checkbox(False)
    editor.set_blank_line_after_enter(True)
    editor.setPlainText("First line")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText() == "First line\n\n"


def test_blank_line_after_enter_with_auto_checkbox(app: QApplication) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor = NoteEditor()
    editor.set_auto_checkbox(True)
    editor.set_blank_line_after_enter(True)
    editor.setPlainText("☐ Backend")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText() == "☐ Backend\n\n☐ "



def test_plain_text_list_mode_numbers_selected_lines_and_select_all_includes_markers(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("Alpha\nBeta\nGamma")
    editor.selectAll()
    editor.set_numbered_list_mode(True)

    expected = "1. Alpha\n2. Beta\n3. Gamma"
    assert editor.toPlainText() == expected
    block = editor.document().firstBlock()
    while block.isValid():
        assert block.textList() is None
        block = block.next()

    editor.selectAll()
    selected = editor.textCursor().selectedText().replace("\u2029", "\n")
    assert selected == expected


def test_plain_text_list_mode_enter_continues_numbering(app: QApplication) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor = NoteEditor()
    editor.set_auto_checkbox(False)
    editor.setPlainText("First item")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    editor.set_numbered_list_mode(True)

    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText() == "1. First item\n2. "


def test_plain_text_list_mode_works_with_double_enter(app: QApplication) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor = NoteEditor()
    editor.set_auto_checkbox(False)
    editor.set_blank_line_after_enter(True)
    editor.setPlainText("First item")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    editor.set_numbered_list_mode(True)

    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText() == "1. First item\n\n2. "


def test_empty_plain_text_list_item_exits_list_mode(app: QApplication) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor = NoteEditor()
    editor.setPlainText("1. ")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    editor.set_numbered_list_mode(True)

    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText() == ""
    assert editor.numbered_list_mode_enabled is False


def test_reenabling_list_mode_on_existing_item_keeps_its_number(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("7. Existing item")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)

    editor.set_numbered_list_mode(True)
    assert editor.toPlainText() == "7. Existing item"


def test_inline_find_highlights_all_matches_and_advances_down(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("git one\ngit two\nGIT three")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.Start)
    editor.setTextCursor(cursor)

    editor.show_find_bar()
    editor.find_bar.set_query("git")

    ranges = editor.search_match_ranges()
    assert len(ranges) == 3
    assert len(editor.extraSelections()) == 3
    assert editor.active_search_range() is None

    assert editor.find_search_match("down") is True
    assert editor.active_search_range() == ranges[0]
    assert editor.find_search_match("down") is True
    assert editor.active_search_range() == ranges[1]
    assert editor.find_search_match("down") is True
    assert editor.active_search_range() == ranges[2]
    assert editor.find_search_match("down") is True
    assert editor.active_search_range() == ranges[0]


def test_inline_find_advances_up_and_direction_boxes_are_exclusive(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("git one\ngit two\ngit three")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)

    editor.show_find_bar()
    editor.find_bar.set_query("git")
    assert editor.find_bar.down_checkbox.isChecked() is True
    assert editor.find_bar.up_checkbox.isChecked() is False

    editor.find_bar.up_checkbox.click()
    assert editor.find_bar.up_checkbox.isChecked() is True
    assert editor.find_bar.down_checkbox.isChecked() is False

    ranges = editor.search_match_ranges()
    assert editor.find_search_match("up") is True
    assert editor.active_search_range() == ranges[-1]
    assert editor.find_search_match("up") is True
    assert editor.active_search_range() == ranges[-2]

    editor.find_bar.down_checkbox.click()
    assert editor.find_bar.down_checkbox.isChecked() is True
    assert editor.find_bar.up_checkbox.isChecked() is False


def test_inline_find_scrollbar_receives_one_marker_per_match(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("alpha\n" * 30 + "needle\n" + "beta\n" * 30 + "needle\n")
    editor.show_find_bar()
    editor.find_bar.set_query("needle")

    assert len(editor.search_match_ranges()) == 2
    assert len(editor._search_scrollbar._markers) == 2
    assert all(0.0 <= marker <= 1.0 for marker in editor._search_scrollbar._markers)


def test_inline_find_close_clears_highlights(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("git git")
    editor.show_find_bar()
    editor.find_bar.set_query("git")
    assert len(editor.extraSelections()) == 2

    editor.hide_find_bar()
    assert editor.is_find_bar_visible() is False
    assert editor.extraSelections() == []
    assert editor.search_match_ranges() == ()

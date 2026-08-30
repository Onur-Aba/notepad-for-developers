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


def test_checkbox_toggle_applies_and_removes_strike(app: QApplication) -> None:
    editor = NoteEditor()
    editor.setPlainText("☐ API'yi hazırla")
    block = editor.document().firstBlock()
    editor.toggle_checkbox(block)
    assert editor.toPlainText().startswith("☑")

    cursor = QTextCursor(editor.document())
    cursor.setPosition(block.position() + 2)
    assert cursor.charFormat().fontStrikeOut() is True

    editor.toggle_checkbox(editor.document().firstBlock())
    assert editor.toPlainText().startswith("☐")
    cursor.setPosition(editor.document().firstBlock().position() + 2)
    assert cursor.charFormat().fontStrikeOut() is False


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


def test_empty_auto_checkbox_enter_exits_task_mode(app: QApplication) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor = NoteEditor()
    editor.set_auto_checkbox(True)
    editor.setPlainText("☐ ")
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    QTest.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText() == ""


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

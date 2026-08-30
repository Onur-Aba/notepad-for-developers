from __future__ import annotations

from app.services.txt_codec import (
    export_internal_plain_text,
    import_text_to_html,
    parse_line,
    parse_text,
    parsed_to_internal_text,
)


def test_detects_supported_checkbox_markers() -> None:
    samples = {
        "[ ] Task": False,
        "[x] Task": True,
        "[X] Task": True,
        "☐ Task": False,
        "☑ Task": True,
        "✓ Task": True,
    }
    for source, expected_checked in samples.items():
        line = parse_line(source)
        assert line.is_task is True
        assert line.checked is expected_checked
        assert line.text == "Task"


def test_normal_text_is_not_a_task() -> None:
    line = parse_line("Bug: token refresh fails")
    assert line.is_task is False
    assert line.text == "Bug: token refresh fails"


def test_nested_indentation_is_preserved() -> None:
    lines = parse_text("[ ] Backend\n    [ ] API\n\t[x] Database")
    assert lines[0].indent == ""
    assert lines[1].indent == "    "
    assert lines[2].indent == "\t"
    internal = parsed_to_internal_text(lines)
    assert internal == "☐ Backend\n    ☐ API\n    ☑ Database"


def test_unicode_checkbox_html_marks_checked_task_as_struck() -> None:
    rendered = import_text_to_html("☐ Frontend\n☑ Login\n✓ Deploy")
    assert "☐" in rendered
    assert rendered.count("☑") == 2
    assert rendered.count("line-through") == 2


def test_export_converts_internal_checkbox_state() -> None:
    source = "☐ Login ekranı\n☑ Database bağlantısı\n    ☐ API"
    assert export_internal_plain_text(source) == "[ ] Login ekranı\n[x] Database bağlantısı\n    [ ] API"


def test_txt_round_trip_preserves_task_states_and_indentation() -> None:
    original = "[ ] Backend\n    [x] Database\nNormal açıklama\n\t[X] JWT"
    internal = parsed_to_internal_text(parse_text(original))
    exported = export_internal_plain_text(internal)
    reparsed = parse_text(exported)
    assert [(x.is_task, x.checked, x.text) for x in reparsed] == [
        (True, False, "Backend"),
        (True, True, "Database"),
        (False, False, "Normal açıklama"),
        (True, True, "JWT"),
    ]
    assert reparsed[1].indent == "    "
    assert reparsed[3].indent == "    "

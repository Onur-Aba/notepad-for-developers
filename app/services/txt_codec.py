from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path

TASK_RE = re.compile(
    r"^(?P<indent>[\t ]*)(?P<marker>\[\s\]|\[[xX]\]|☐|☑|✓)(?:[\t ]*)(?P<text>.*)$"
)
INTERNAL_TASK_RE = re.compile(r"^(?P<indent>[\t ]*)(?P<marker>☐|☑)(?:[\t ]?)(?P<text>.*)$")


@dataclass(frozen=True, slots=True)
class ParsedLine:
    text: str
    is_task: bool
    checked: bool = False
    indent: str = ""


def parse_line(line: str) -> ParsedLine:
    match = TASK_RE.match(line)
    if not match:
        return ParsedLine(text=line, is_task=False)
    marker = match.group("marker")
    return ParsedLine(
        text=match.group("text"),
        is_task=True,
        checked=marker.lower() == "[x]" or marker in {"☑", "✓"},
        indent=match.group("indent"),
    )


def parse_text(text: str) -> list[ParsedLine]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return [parse_line(line) for line in normalized.split("\n")]


def _indent_html(indent: str) -> str:
    return html.escape(indent.expandtabs(4))


def parsed_to_html(lines: list[ParsedLine]) -> str:
    blocks: list[str] = ["<!DOCTYPE html><html><head><meta charset=\"utf-8\"></head><body>"]
    for line in lines:
        if line.is_task:
            marker = "☑" if line.checked else "☐"
            task_text = html.escape(line.text)
            if line.checked:
                task_text = f'<span style="text-decoration: line-through;">{task_text}</span>'
            blocks.append(
                f'<p style="margin:0; white-space:pre-wrap;">{_indent_html(line.indent)}{marker} {task_text}</p>'
            )
        else:
            escaped = html.escape(line.text).replace("\t", "    ")
            blocks.append(f'<p style="margin:0; white-space:pre-wrap;">{escaped if escaped else "<br>"}</p>')
    blocks.append("</body></html>")
    return "".join(blocks)



def parsed_to_internal_text(lines: list[ParsedLine]) -> str:
    output: list[str] = []
    for line in lines:
        if line.is_task:
            marker = "☑" if line.checked else "☐"
            suffix = f" {line.text}" if line.text else ""
            output.append(f"{line.indent.expandtabs(4)}{marker}{suffix}")
        else:
            output.append(line.text)
    return "\n".join(output)


def import_text_to_html(text: str) -> str:
    return parsed_to_html(parse_text(text))


def export_internal_plain_text(text: str) -> str:
    output: list[str] = []
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    for line in normalized.split("\n"):
        match = INTERNAL_TASK_RE.match(line)
        if not match:
            output.append(line)
            continue
        prefix = "[x]" if match.group("marker") == "☑" else "[ ]"
        text_part = match.group("text")
        output.append(f"{match.group('indent')}{prefix}{(' ' + text_part) if text_part else ''}")
    return "\n".join(output)


def read_utf8_text(path: Path) -> str:
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise UnicodeError("The file is not valid UTF-8/UTF-8-SIG text.") from exc


def write_utf8_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")

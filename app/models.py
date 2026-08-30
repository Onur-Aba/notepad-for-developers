from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Note:
    id: int
    title: str
    content_html: str
    content_plain: str
    created_at: str
    updated_at: str
    is_deleted: bool


@dataclass(slots=True)
class NoteSummary:
    id: int
    title: str
    preview: str
    created_at: str
    updated_at: str
    is_deleted: bool

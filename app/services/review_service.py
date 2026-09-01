from __future__ import annotations

from app.database import Database
from app.models import ResourceLink, ReviewBaseline


class ReviewService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def mark_reviewed(self, link: ResourceLink, current_sha: str, branch: str | None) -> ReviewBaseline:
        if not current_sha:
            raise ValueError("A current repository commit is required before marking reviewed.")
        baseline = self.database.upsert_review_baseline(
            link.resource_type, link.resource_id, link.repository_id, current_sha, branch,
            resource_parent_id=link.resource_parent_id,
        )
        self.database.add_activity(link.project_id, "marked_reviewed", "Marked as Reviewed", f"{current_sha[:8]} · {link.target_value or link.target_type}")
        return baseline

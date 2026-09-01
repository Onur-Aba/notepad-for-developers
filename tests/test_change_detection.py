from __future__ import annotations

from app.models import ReviewStatus
from app.services.change_detection_service import ChangeDetectionService


def test_review_status_truth_table() -> None:
    assert ChangeDetectionService.status_from_comparison(False, True, False) == ReviewStatus.NOT_REVIEWED
    assert ChangeDetectionService.status_from_comparison(True, False, False) == ReviewStatus.CANNOT_COMPARE
    assert ChangeDetectionService.status_from_comparison(True, True, False) == ReviewStatus.CURRENT
    assert ChangeDetectionService.status_from_comparison(True, True, True) == ReviewStatus.NEEDS_REVIEW

from app.models import ChangedFile, CommitInfo, ResourceLink, ReviewSummary
from app.services.change_detection_service import dedupe_commits, merge_review_summaries


def _link(link_id: int, target: str) -> ResourceLink:
    return ResourceLink(
        id=link_id,
        project_id=1,
        resource_type="decision",
        resource_id="7",
        resource_parent_id="",
        repository_id=3,
        target_type="file",
        target_value=target,
        github_node_id=None,
        metadata={},
        created_at="2026-09-01T00:00:00+00:00",
    )


def test_duplicate_commit_sha_is_shown_once() -> None:
    commits = [
        CommitInfo("a" * 40, "same commit"),
        CommitInfo("a" * 40, "same commit"),
    ]
    assert [item.sha for item in dedupe_commits(commits)] == ["a" * 40]


def test_multiple_links_for_same_decision_repository_merge_into_one_review_item() -> None:
    commit = CommitInfo("b" * 40, "change auth")
    first = ReviewSummary(
        _link(1, "auth/a.py"), ReviewStatus.NEEDS_REVIEW,
        baseline_sha="1" * 40, current_sha="2" * 40, commit_count=1,
        changed_files=[ChangedFile("M", "auth/a.py")],
        linked_changed_files=[ChangedFile("M", "auth/a.py")], commits=[commit],
    )
    second = ReviewSummary(
        _link(2, "auth/b.py"), ReviewStatus.NEEDS_REVIEW,
        baseline_sha="1" * 40, current_sha="2" * 40, commit_count=1,
        changed_files=[ChangedFile("M", "auth/b.py")],
        linked_changed_files=[ChangedFile("M", "auth/b.py")], commits=[commit],
    )
    merged = merge_review_summaries([first, second])
    assert len(merged) == 1
    assert merged[0].commit_count == 1
    assert len(merged[0].commits) == 1
    assert {item.path for item in merged[0].linked_changed_files} == {"auth/a.py", "auth/b.py"}

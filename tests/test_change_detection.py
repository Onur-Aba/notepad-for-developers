from __future__ import annotations

from app.models import ReviewStatus
from app.services.change_detection_service import ChangeDetectionService


def test_review_status_truth_table() -> None:
    assert ChangeDetectionService.status_from_comparison(False, True, False) == ReviewStatus.NOT_REVIEWED
    assert ChangeDetectionService.status_from_comparison(True, False, False) == ReviewStatus.CANNOT_COMPARE
    assert ChangeDetectionService.status_from_comparison(True, True, False) == ReviewStatus.CURRENT
    assert ChangeDetectionService.status_from_comparison(True, True, True) == ReviewStatus.NEEDS_REVIEW

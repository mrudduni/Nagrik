import pytest
from app.services.resolution import ResolutionTracker


def test_valid_transitions():
    assert "ACKNOWLEDGED" in ResolutionTracker.VALID_TRANSITIONS["SUBMITTED"]
    assert "ASSIGNED" in ResolutionTracker.VALID_TRANSITIONS["ACKNOWLEDGED"]
    assert "RESOLUTION_CLAIMED" in ResolutionTracker.VALID_TRANSITIONS["IN_PROGRESS"]
    assert "CITIZEN_VERIFIED" in ResolutionTracker.VALID_TRANSITIONS["RESOLUTION_CLAIMED"]
    assert "REOPENED" in ResolutionTracker.VALID_TRANSITIONS["RESOLUTION_CLAIMED"]
    assert "CLOSED" in ResolutionTracker.VALID_TRANSITIONS["CITIZEN_VERIFIED"]


def test_invalid_transitions():
    # Cannot jump directly from SUBMITTED to RESOLUTION_CLAIMED
    assert "RESOLUTION_CLAIMED" not in ResolutionTracker.VALID_TRANSITIONS["SUBMITTED"]
    # Cannot reopen a CLOSED complaint directly without flow
    assert "REOPENED" not in ResolutionTracker.VALID_TRANSITIONS["CLOSED"]

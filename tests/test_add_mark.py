"""Unit tests for the add_mark seam using stub, fake, and mock doubles."""

from typing import Any
from unittest.mock import Mock

import pytest

from errors import NotFoundError, ValidationError
from gradebook import add_mark
from models import Mark


def fixed_now() -> str:
    """Stub returning a constant ISO timestamp string."""
    return "2026-10-12 09:00:00"


def test_valid_mark_is_stored_with_the_time(state: dict[str, Any]) -> None:
    """Verify that a valid mark is appended with the stub timestamp."""
    save = Mock()
    add_mark(state, Mark("S1", "A1", 15.0), fixed_now, save)
    assert state["marks"] == [
        {"student": "S1", "assessment": "A1", "score": 15.0, "at": "2026-10-12 09:00:00"}
    ]


def test_valid_mark_calls_save_once(state: dict[str, Any]) -> None:
    """Verify that adding a valid mark calls the save mock exactly once."""
    save = Mock()
    add_mark(state, Mark("S1", "A1", 15.0), fixed_now, save)
    save.assert_called_once_with()


@pytest.mark.parametrize(
    ("mark", "error"),
    [
        pytest.param(Mark("NOPE", "A1", 5.0), NotFoundError, id="unknown-student"),
        pytest.param(Mark("S1", "GHOST", 5.0), NotFoundError, id="unknown-assessment"),
        pytest.param(Mark("S1", "A1", 21.0), ValidationError, id="score-above-total"),
    ],
)
def test_rejected_mark_changes_nothing(
    state: dict[str, Any], mark: Mark, error: type[Exception]
) -> None:
    """Verify that rejected marks raise expected error, leave state clean, and never call save."""
    save = Mock()
    with pytest.raises(error):
        add_mark(state, mark, fixed_now, save)
    assert state["marks"] == []
    save.assert_not_called()


def test_new_mark_replaces_old_mark_for_same_student_and_assessment(
    state: dict[str, Any],
) -> None:
    """Verify that after two marks for the same student and assessment (scores 5 and 18) there is exactly one mark, with score 18."""
    save = Mock()
    add_mark(state, Mark("S1", "A1", 5.0), fixed_now, save)
    add_mark(state, Mark("S1", "A1", 18.0), fixed_now, save)
    assert len(state["marks"]) == 1
    assert state["marks"][0]["score"] == 18.0
    assert state["marks"][0]["student"] == "S1"
    assert state["marks"][0]["assessment"] == "A1"


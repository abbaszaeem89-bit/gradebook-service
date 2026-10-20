"""Tests for add_assessment using state fixture and Mock as save."""

from typing import Any
from unittest.mock import Mock

import pytest

from errors import ConflictError, ValidationError
from gradebook import add_assessment
from models import Assessment

# ── helper ──────────────────────────────────────────────────────────────────

def _state() -> dict[str, Any]:
    return {"students": {}, "assessments": {}, "marks": []}


def _make_assessment(**kwargs: object) -> Assessment:
    defaults: dict[str, object] = {
        "id": "AX",
        "title": "Quiz 1",
        "weight": 40.0,
        "total": 20.0,
    }
    defaults.update(kwargs)
    return Assessment(**defaults)  # type: ignore[arg-type]


# ── valid assessment is stored and saved once ────────────────────────────────

def test_valid_assessment_is_stored(state: dict[str, Any]) -> None:
    """A valid assessment is recorded in state."""
    save = Mock()
    a = _make_assessment(weight=40.0)
    add_assessment(state, a, save)
    assert "AX" in state["assessments"]


def test_valid_assessment_calls_save_once(state: dict[str, Any]) -> None:
    """A valid assessment calls save exactly once."""
    save = Mock()
    a = _make_assessment(weight=40.0)
    add_assessment(state, a, save)
    save.assert_called_once_with()


# ── assessment that pushes total above 100 is rejected ─────────────────────

def test_overweight_assessment_raises(state: dict[str, Any]) -> None:
    """An assessment that would push total weight above 100 raises ValidationError."""
    save = Mock()
    # existing weight 60 + new weight 50 = 110 → rejected
    state["assessments"]["A0"] = {"id": "A0", "title": "Existing", "weight": 60.0, "total": 10.0}
    a = _make_assessment(id="AX", weight=50.0)
    with pytest.raises(ValidationError, match="100"):
        add_assessment(state, a, save)


def test_overweight_assessment_not_stored(state: dict[str, Any]) -> None:
    """A rejected assessment is not stored."""
    save = Mock()
    state["assessments"]["A0"] = {"id": "A0", "title": "Existing", "weight": 60.0, "total": 10.0}
    a = _make_assessment(id="AX", weight=50.0)
    with pytest.raises(ValidationError):
        add_assessment(state, a, save)
    assert "AX" not in state["assessments"]


def test_overweight_assessment_does_not_call_save(state: dict[str, Any]) -> None:
    """A rejected assessment does not call save."""
    save = Mock()
    state["assessments"]["A0"] = {"id": "A0", "title": "Existing", "weight": 60.0, "total": 10.0}
    a = _make_assessment(id="AX", weight=50.0)
    with pytest.raises(ValidationError):
        add_assessment(state, a, save)
    save.assert_not_called()


# ── duplicate assessment raises ConflictError ────────────────────────────────

def test_duplicate_assessment_raises_conflict(state: dict[str, Any]) -> None:
    """Attempting to add an assessment with an existing id raises ConflictError."""
    save = Mock()
    a = _make_assessment(id="A1", weight=10.0)
    with pytest.raises(ConflictError):
        add_assessment(state, a, save)


def test_duplicate_assessment_does_not_call_save(state: dict[str, Any]) -> None:
    """Duplicate assessment does not call save."""
    save = Mock()
    a = _make_assessment(id="A1", weight=10.0)
    with pytest.raises(ConflictError):
        add_assessment(state, a, save)
    save.assert_not_called()

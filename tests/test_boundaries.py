"""Boundary / parametrized tests for weight and score edges."""

from typing import Any
from unittest.mock import Mock

import pytest

from errors import ValidationError
from gradebook import add_mark
from models import Mark
from rules import ensure_weight_fits

# ── ensure_weight_fits boundaries ───────────────────────────────────────────

@pytest.mark.parametrize(
    "existing,new_weight",
    [
        pytest.param([], 0.0, id="weight-zero-fits"),
        pytest.param([], 100.0, id="weight-100-fits"),
    ],
)
def test_weight_fits(existing: list[float], new_weight: float) -> None:
    """Weights 0 and 100 are each accepted."""
    ensure_weight_fits(existing, new_weight)  # must not raise


@pytest.mark.parametrize(
    "existing,new_weight",
    [
        pytest.param([], -0.01, id="weight-negative-rejected"),
        pytest.param([], 100.01, id="weight-over-100-rejected"),
    ],
)
def test_weight_rejected(existing: list[float], new_weight: float) -> None:
    """Weights -0.01 and 100.01 are each rejected."""
    with pytest.raises(ValidationError):
        ensure_weight_fits(existing, new_weight)


# ── assessment total boundaries ─────────────────────────────────────────────

@pytest.mark.parametrize(
    "total",
    [
        pytest.param(0.01, id="total-0.01-accepted"),
    ],
)
def test_assessment_total_accepted(total: float) -> None:
    """Total 0.01 is accepted."""
    from models import Assessment
    Assessment(id="A_test", title="Quiz", weight=10.0, total=total)


@pytest.mark.parametrize(
    "total",
    [
        pytest.param(0.0, id="total-0-rejected"),
    ],
)
def test_assessment_total_rejected(total: float) -> None:
    """Total 0 is rejected."""
    from models import Assessment
    with pytest.raises(ValidationError):
        Assessment(id="A_test", title="Quiz", weight=10.0, total=total)


# ── score boundaries for add_mark ───────────────────────────────────────────

@pytest.fixture()
def state_with_assessment() -> dict[str, Any]:
    """State with student S1 and assessment A1 (total 20)."""
    return {
        "students": {"S1": {"id": "S1", "name": "Ayesha"}},
        "assessments": {"A1": {"id": "A1", "title": "Quiz 1", "weight": 20.0, "total": 20.0}},
        "marks": [],
    }


@pytest.mark.parametrize(
    "score",
    [
        pytest.param(0.0, id="score-zero-accepted"),
        pytest.param(20.0, id="score-at-total-accepted"),
    ],
)
def test_score_accepted(state_with_assessment: dict[str, Any], score: float) -> None:
    """Scores 0 and 20 (total) are accepted."""
    save = Mock()

    def fixed_now() -> str:
        return "2026-10-20T00:00:00Z"

    add_mark(state_with_assessment, Mark("S1", "A1", score), fixed_now, save)
    assert len(state_with_assessment["marks"]) == 1


@pytest.mark.parametrize(
    "score",
    [
        pytest.param(-0.01, id="score-below-zero-rejected"),
        pytest.param(20.01, id="score-above-total-rejected"),
    ],
)
def test_score_rejected(state_with_assessment: dict[str, Any], score: float) -> None:
    """Scores -0.01 and 20.01 are each rejected and nothing is stored."""
    save = Mock()

    def fixed_now() -> str:
        return "2026-10-20T00:00:00Z"

    with pytest.raises(ValidationError):
        add_mark(state_with_assessment, Mark("S1", "A1", score), fixed_now, save)
    assert state_with_assessment["marks"] == []
    save.assert_not_called()

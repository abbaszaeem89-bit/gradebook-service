"""Tests for domain models, validation, and parsers."""

import pytest

from errors import ValidationError
from models import (
    Assessment,
    Mark,
    parse_assessment,
    parse_mark,
    parse_number,
    parse_student,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        pytest.param("15", 15.0, id="numeric-string"),
        pytest.param(15, 15.0, id="int"),
        pytest.param("2.5", 2.5, id="decimal-string"),
    ],
)
def test_good_numbers_are_accepted(raw: object, expected: float) -> None:
    assert parse_number(raw, "score") == expected


@pytest.mark.parametrize(
    "raw",
    [
        pytest.param("abc", id="text"),
        pytest.param(True, id="bool"),
        pytest.param(None, id="none"),
        pytest.param([], id="list"),
        pytest.param("nan", id="nan"),
        pytest.param("inf", id="inf"),
    ],
)
def test_bad_numbers_are_rejected(raw: object) -> None:
    with pytest.raises(ValidationError, match="score"):
        parse_number(raw, "score")


def test_zero_total_rejected() -> None:
    """Verify that an assessment with a zero or non-positive total is rejected."""
    with pytest.raises(ValidationError, match="total"):
        Assessment(id="A1", title="Midterm", weight=20.0, total=0.0)

    with pytest.raises(ValidationError, match="total"):
        parse_assessment({"id": "A1", "title": "Midterm", "weight": 20.0, "total": 0.0})


def test_negative_score_rejected() -> None:
    """Verify that a negative score is rejected by Mark and parse_mark."""
    with pytest.raises(ValidationError, match="score"):
        Mark(student="S1", assessment="A1", score=-1.0)

    with pytest.raises(ValidationError, match="score"):
        parse_mark({"student": "S1", "assessment": "A1", "score": -10.0})


def test_missing_field_rejected() -> None:
    """Verify that missing required fields in payload raise ValidationError."""
    with pytest.raises(ValidationError, match="name"):
        parse_student({"id": "S1"})

    with pytest.raises(ValidationError, match="total"):
        parse_assessment({"id": "A1", "title": "Quiz 1", "weight": 10.0})

    with pytest.raises(ValidationError, match="score"):
        parse_mark({"student": "S1", "assessment": "A1"})


def test_non_dict_payload_rejected() -> None:
    """Verify that non-dict payloads raise ValidationError."""
    with pytest.raises(ValidationError, match="dict"):
        parse_student(5)

    with pytest.raises(ValidationError, match="dict"):
        parse_assessment(["A1", "Quiz", 10, 20])

    with pytest.raises(ValidationError, match="dict"):
        parse_mark("invalid")


def test_valid_assessment_parsed_correctly() -> None:
    """Verify that a valid assessment payload is parsed into an Assessment instance."""
    raw = {"id": "A1", "title": "Final Exam", "weight": "40.0", "total": "100.0"}
    assessment = parse_assessment(raw)
    assert assessment == Assessment(id="A1", title="Final Exam", weight=40.0, total=100.0)

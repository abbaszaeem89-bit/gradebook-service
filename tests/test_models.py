"""Tests for domain models, validation, and parsers."""

import pytest

from errors import ValidationError
from models import (
    Assessment,
    Mark,
    Student,
    parse_assessment,
    parse_mark,
    parse_number,
    parse_student,
    parse_text,
)


def test_numeric_string_accepted() -> None:
    """Verify that a numeric string is accepted and parsed to float."""
    assert parse_number("42.5", "score") == 42.5
    assert parse_number("100", "total") == 100.0


def test_invalid_text_rejected() -> None:
    """Verify that non-numeric text strings are rejected with ValidationError."""
    with pytest.raises(ValidationError, match="score"):
        parse_number("abc", "score")


def test_boolean_rejected() -> None:
    """Verify that boolean values are rejected by parse_number."""
    with pytest.raises(ValidationError, match="weight"):
        parse_number(True, "weight")
    with pytest.raises(ValidationError, match="score"):
        parse_number(False, "score")


def test_nan_rejected() -> None:
    """Verify that nan is rejected by parse_number."""
    with pytest.raises(ValidationError, match="score"):
        parse_number(float("nan"), "score")
    with pytest.raises(ValidationError, match="score"):
        parse_number("nan", "score")


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


def test_parse_text_strips_spaces_and_rejects_blank() -> None:
    """Verify that parse_text strips whitespace and rejects empty/blank strings."""
    assert parse_text("  Ayesha  ", "name") == "Ayesha"
    with pytest.raises(ValidationError, match="name"):
        parse_text("   ", "name")
    with pytest.raises(ValidationError, match="id"):
        Student(id="", name="Ayesha")

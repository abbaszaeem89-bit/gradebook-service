"""Domain models and validation for the gradebook service."""

import math
from dataclasses import dataclass

from errors import ValidationError


@dataclass(frozen=True)
class Student:
    """Represents a student enrolled in the gradebook."""

    id: str
    name: str

    def __post_init__(self) -> None:
        if not self.id:
            raise ValidationError("id cannot be empty")
        if not self.name:
            raise ValidationError("name cannot be empty")


@dataclass(frozen=True)
class Assessment:
    """Represents an assessment component with weight and total points."""

    id: str
    title: str
    weight: float
    total: float

    def __post_init__(self) -> None:
        if not self.id:
            raise ValidationError("id cannot be empty")
        if not self.title:
            raise ValidationError("title cannot be empty")
        if self.weight < 0.0 or self.weight > 100.0:
            raise ValidationError("weight must be between 0 and 100")
        if self.total <= 0.0:
            raise ValidationError("total must be greater than 0")


@dataclass(frozen=True)
class Mark:
    """Represents a mark earned by a student on an assessment."""

    student: str
    assessment: str
    score: float

    def __post_init__(self) -> None:
        if not self.student:
            raise ValidationError("student cannot be empty")
        if not self.assessment:
            raise ValidationError("assessment cannot be empty")
        if self.score < 0.0:
            raise ValidationError("score cannot be negative")


def parse_number(raw: object, field: str) -> float:
    """Parse raw value as a float, rejecting booleans, None, structures, non-numerics, nan, and inf."""
    if isinstance(raw, bool) or raw is None:
        raise ValidationError(f"Field '{field}' must be a number, got {type(raw).__name__}")
    if isinstance(raw, (int, float)):
        val = float(raw)
    elif isinstance(raw, str):
        try:
            val = float(raw)
        except ValueError as err:
            raise ValidationError(f"Field '{field}' must be a valid number, got {raw!r}") from err
    else:
        raise ValidationError(f"Field '{field}' must be a number, got {type(raw).__name__}")

    if math.isnan(val) or math.isinf(val):
        raise ValidationError(f"Field '{field}' cannot be nan or inf")
    return val


def parse_text(raw: object, field: str) -> str:
    """Parse raw value as non-blank string with surrounding spaces stripped."""
    if not isinstance(raw, str):
        raise ValidationError(f"Field '{field}' must be a string, got {type(raw).__name__}")
    cleaned = raw.strip()
    if not cleaned:
        raise ValidationError(f"Field '{field}' cannot be empty or blank")
    return cleaned


def parse_student(payload: object) -> Student:
    """Parse and validate student dictionary payload."""
    if not isinstance(payload, dict):
        raise ValidationError("Student payload must be a dict")
    if "id" not in payload:
        raise ValidationError("Field 'id' is required")
    if "name" not in payload:
        raise ValidationError("Field 'name' is required")
    student_id = parse_text(payload["id"], "id")
    name = parse_text(payload["name"], "name")
    return Student(id=student_id, name=name)


def parse_assessment(payload: object) -> Assessment:
    """Parse and validate assessment dictionary payload."""
    if not isinstance(payload, dict):
        raise ValidationError("Assessment payload must be a dict")
    for required in ("id", "title", "weight", "total"):
        if required not in payload:
            raise ValidationError(f"Field '{required}' is required")
    assessment_id = parse_text(payload["id"], "id")
    title = parse_text(payload["title"], "title")
    weight = parse_number(payload["weight"], "weight")
    total = parse_number(payload["total"], "total")
    return Assessment(id=assessment_id, title=title, weight=weight, total=total)


def parse_mark(payload: object) -> Mark:
    """Parse and validate mark dictionary payload."""
    if not isinstance(payload, dict):
        raise ValidationError("Mark payload must be a dict")
    for required in ("student", "assessment", "score"):
        if required not in payload:
            raise ValidationError(f"Field '{required}' is required")
    student = parse_text(payload["student"], "student")
    assessment = parse_text(payload["assessment"], "assessment")
    score = parse_number(payload["score"], "score")
    return Mark(student=student, assessment=assessment, score=score)

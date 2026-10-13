"""Domain models and validation for the gradebook service."""

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

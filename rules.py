"""Business rules for the gradebook service.

This module contains domain rules that are independent of HTTP or storage.
"""

from errors import ValidationError

MAX_TOTAL_WEIGHT: float = 100.0
TOLERANCE: float = 1e-9


def ensure_weight_fits(existing_weights: list[float], new_weight: float) -> None:
    """Raise ValidationError if adding new_weight would push the total above MAX_TOTAL_WEIGHT.

    A tolerance of TOLERANCE is allowed to accommodate floating-point arithmetic
    (e.g. 9.3 + 27.3 + 33.7 + 29.7 sums to slightly above 100 in binary float).

    Args:
        existing_weights: The weights of assessments already in the gradebook.
        new_weight: The weight of the assessment being added.

    Raises:
        ValidationError: if sum(existing_weights) + new_weight > MAX_TOTAL_WEIGHT + TOLERANCE.
    """
    if new_weight < 0.0:
        raise ValidationError(
            f"Weight cannot be negative, got {new_weight}."
        )
    total = sum(existing_weights) + new_weight
    if total > MAX_TOTAL_WEIGHT + TOLERANCE:
        raise ValidationError(
            f"Total weight would be {total:.10g}, which exceeds the maximum of {MAX_TOTAL_WEIGHT:.0f}."
        )

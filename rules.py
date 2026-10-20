from errors import ValidationError


def ensure_weight_fits(existing_weights: list[float], new_weight: float) -> None:
    if sum(existing_weights) + new_weight > 100:
        raise ValidationError("Total weight exceeds 100")

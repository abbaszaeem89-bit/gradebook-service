"""Custom domain exceptions for the gradebook service."""


class GradebookError(Exception):
    """Base exception for all gradebook service errors."""


class ValidationError(GradebookError):
    """Raised when input data or entity fails validation rules."""


class NotFoundError(GradebookError):
    """Raised when a requested student or assessment does not exist."""


class ConflictError(GradebookError):
    """Raised when attempting to create an entity that already exists."""

"""Shared test fixtures for the gradebook service test suite."""

from typing import Any

import pytest

import gradebook


@pytest.fixture
def state() -> dict[str, Any]:
    """Provide a fresh fixture gradebook state dictionary."""
    return {
        "students": {"S1": {"id": "S1", "name": "Ayesha"}},
        "assessments": {
            "A1": {"id": "A1", "title": "Quiz 1", "weight": 10, "total": 20},
            "A2": {"id": "A2", "title": "Midterm", "weight": 30, "total": 50},
        },
        "marks": [],
    }


@pytest.fixture
def loaded(state: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Patch gradebook.STATE with the fixture state and return it."""
    monkeypatch.setattr(gradebook, "STATE", state)
    return state

"""Property-based tests using hypothesis to hunt for defects in pct()."""

import unittest.mock
from typing import Any
from unittest.mock import Mock

from hypothesis import given, settings
from hypothesis import strategies as st

import gradebook
from gradebook import add_mark
from models import Mark


@given(scores=st.lists(st.integers(min_value=0, max_value=20), min_size=1, max_size=5))
@settings(max_examples=200)
def test_pct_does_not_exceed_weight(scores: list[int]) -> None:
    """For any sequence of scores, each student's pct() must not exceed the assessment weight.

    This fails because add_mark appends duplicate marks instead of replacing them,
    causing pct() to accumulate points beyond the assessment weight.
    """
    state: dict[str, Any] = {
        "students": {"S1": {"id": "S1", "name": "Ayesha"}},
        "assessments": {"A1": {"id": "A1", "title": "Quiz 1", "weight": 10.0, "total": 20.0}},
        "marks": [],
    }

    def fixed_now() -> str:
        return "2026-10-20T00:00:00Z"

    for score in scores:
        add_mark(state, Mark("S1", "A1", float(score)), fixed_now, Mock())

    with unittest.mock.patch.object(gradebook, "STATE", state):
        result = float(gradebook.pct("S1"))

    assert result <= 10.0

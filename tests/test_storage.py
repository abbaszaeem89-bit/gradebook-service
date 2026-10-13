"""Storage persistence and file recovery tests using tmp_path."""

import json
from pathlib import Path
from typing import Any

import pytest

import gradebook


@pytest.fixture
def data_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture pointing gradebook.DATA to a temporary file path."""
    path = tmp_path / "gradebook.json"
    monkeypatch.setattr(gradebook, "DATA", str(path))
    return path


def test_saved_gradebook_loads_back_unchanged(
    data_file: Path, state: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify that state saved to disk is loaded back completely unchanged."""
    monkeypatch.setattr(gradebook, "STATE", state)
    gradebook.save()
    monkeypatch.setattr(gradebook, "STATE", {})
    gradebook.load()
    assert gradebook.STATE == state


def test_missing_file_gives_an_empty_gradebook(
    data_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify that a missing file initializes STATE to an empty gradebook."""
    monkeypatch.setattr(gradebook, "STATE", {})
    gradebook.load()
    assert gradebook.STATE == {"students": {}, "assessments": {}, "marks": []}


def test_corrupt_file_stops_loading_with_a_json_error(data_file: Path) -> None:
    """Verify that corrupt JSON raises json.JSONDecodeError instead of swallowing it."""
    data_file.write_text("{bad")
    with pytest.raises(json.JSONDecodeError):
        gradebook.load()

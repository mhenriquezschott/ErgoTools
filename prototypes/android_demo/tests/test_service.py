"""Isolated native-project round trips and invalid-edit protection for the demo.

These tests use pytest-owned projects only. Domain calculators and SQLite adapters
are real and unchanged; no test patches calculation results or uses maintained data.
"""

import json
from pathlib import Path

import pytest
from demo_service import (
    calculate_and_save,
    compatibility_probe,
    create_project,
    read_project,
    source,
)


def test_sample_edit_save_reopen_retains_exact_values(tmp_path: Path) -> None:
    """Check complete persistence and a meaningful second calculation.

    Args:
        tmp_path: Pytest-owned native project directory.

    Returns:
        None; exact inputs and known results remain available after repository reopen.
    """
    path = tmp_path / "tablet.ergprj"
    create_project(path)
    assert read_project(path)["damage"] is None
    first = calculate_and_save(path, source())
    assert first["probability_percent"] == pytest.approx(13.190999733969136)
    assert first["damage"] == 0.0003
    assert read_project(path) == first
    second = calculate_and_save(path, source(30, 98.1, 100))
    assert second["load_n"] == 98.1
    assert second["probability_percent"] == pytest.approx(16.016181175764896)
    assert read_project(path) == second
    assert second["name"] == "Elena Muñoz"


def test_invalid_input_preserves_existing_project(tmp_path: Path) -> None:
    """Reject invalid input before replacing the last valid saved assessment.

    Args:
        tmp_path: Disposable existing sample directory.

    Returns:
        None; rejected input leaves native file bytes and stored results unchanged.
    """
    path = tmp_path / "tablet.ergprj"
    create_project(path)
    valid = calculate_and_save(path, source())
    previous = path.read_bytes()
    with pytest.raises(ValueError):
        calculate_and_save(path, source(-1, 49, 100))
    assert path.read_bytes() == previous
    assert read_project(path) == valid


def test_compatibility_probe_is_separate_from_interactive_sample(
    tmp_path: Path,
) -> None:
    """A repeated startup probe cannot overwrite the user's edited sample.

    Args:
        tmp_path: Private application-like storage directory.

    Returns:
        None; evidence is reproducible and saved interactive inputs remain intact.
    """
    sample = tmp_path / "tablet_sample.ergprj"
    create_project(sample)
    edited = calculate_and_save(sample, source(30, 98.1, 100))
    for _ in range(2):
        result = compatibility_probe(tmp_path)
        assert result["reopened"]["load_n"] == 49
        assert result["sqlite_serialize"] and result["sqlite_deserialize"]
        assert read_project(sample) == edited
        saved = json.loads((tmp_path / "compatibility_probe.json").read_text())
        assert saved == result

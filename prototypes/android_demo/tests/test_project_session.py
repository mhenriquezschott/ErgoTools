"""M01 project lifecycle regressions using real native files and private folders.

No maintained fixtures are modified. These tests cover explicit Save boundaries,
invalid imports, full-byte preservation, restart recovery and separate Save As.
"""

import sqlite3
from pathlib import Path

import pytest
from demo_service import read_project
from mobile_assessment import accept_inputs, assessment
from project_session import ProjectSession, project_info

from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile


@pytest.mark.parametrize("units", ["metric", "imperial"])
def test_empty_project_explicit_save_and_restart(tmp_path: Path, units: str) -> None:
    """New projects stay unsaved until Save and reopen without fabricated workers.

    Args:
        tmp_path: Private storage root.
        units: Each supported project measurement system.

    Returns:
        None; project metadata, empty state and identity survive restart.
    """
    session = ProjectSession(tmp_path)
    assert session.active is None
    session.create("Packing study", units)
    assert session.active["dirty"]
    assert session.state["recent"] == []
    assert project_info(session.working) == {
        "title": "Packing study",
        "units": units,
        "workers": 0,
        "assessments": 0,
    }
    assert assessment(session.working) is None
    session.save()
    restarted = ProjectSession(tmp_path)
    assert not restarted.active["dirty"]
    assert restarted.active["id"] == session.active["id"]
    with AssessmentProjectFile.open(restarted.working) as native:
        assert native.metadata.title == "Packing study"


def test_invalid_import_preserves_active_and_recent(tmp_path: Path) -> None:
    """A failed file validation cannot replace the active saved project.

    Args:
        tmp_path: Disposable mobile storage.

    Returns:
        None; both native and catalog bytes remain unchanged.
    """
    session = ProjectSession(tmp_path)
    session.create("Good")
    session.save()
    before = session.working.read_bytes(), session.catalog.read_bytes()
    with pytest.raises(sqlite3.DatabaseError):
        session.activate(b"not sqlite", "broken.ergprj", "Test import")
    assert (session.working.read_bytes(), session.catalog.read_bytes()) == before
    with pytest.raises(ValueError):
        session.create("  ")
    assert session.working.read_bytes() == before[0]


def test_import_and_save_preserve_complete_native_bytes(tmp_path: Path) -> None:
    """Import is detached and Save retains every byte, not a LiFFT-only projection.

    Args:
        tmp_path: Independent source and mobile app folders.

    Returns:
        None; source remains unchanged and saved tablet copy is byte-identical.
    """
    original = ProjectSession(tmp_path / "source")
    original.create("Sample", sample=True)
    original.save()
    data = original.working.read_bytes()
    mobile = ProjectSession(tmp_path / "mobile")
    mobile.activate(data, "../../source.ergprj", "Imported from source.ergprj")
    assert mobile.active["name"] == "source.ergprj"
    mobile.save()
    record = mobile.state["recent"][0]
    assert (mobile.folder / "projects" / f"{record['id']}.ergprj").read_bytes() == data
    assert original.working.read_bytes() == data


def test_edit_calculate_discard_and_explicit_save(tmp_path: Path) -> None:
    """Calculated results remain private until Save; Discard restores prior data.

    Args:
        tmp_path: Owned native project folder.

    Returns:
        None; known exact results and explicit saved-file boundaries hold.
    """
    session = ProjectSession(tmp_path)
    session.create("Sample", sample=True)
    selected = assessment(session.working)
    accept_inputs(session.working, selected, ["30", "49", "100"], calculate=True)
    session.save()
    identity = session.active["id"]
    saved_path = session.folder / "projects" / f"{identity}.ergprj"
    saved_bytes = saved_path.read_bytes()
    accept_inputs(
        session.working,
        assessment(session.working),
        ["30", "98.1", "100"],
        calculate=True,
    )
    session.mark_changed()
    assert not session.state["recent"][0]["dirty"]
    assert read_project(session.working)["probability_percent"] == pytest.approx(
        16.016181175764896
    )
    assert saved_path.read_bytes() == saved_bytes
    restarted = ProjectSession(tmp_path)
    assert restarted.active["dirty"]
    assert read_project(restarted.working)["load_n"] == 98.1
    restarted.discard()
    assert read_project(restarted.working)["load_n"] == 49
    accept_inputs(
        restarted.working,
        assessment(restarted.working),
        ["30", "98.1", "100"],
        calculate=True,
    )
    restarted.mark_changed()
    restarted.save()
    assert read_project(saved_path)["load_n"] == 98.1


def test_save_as_keeps_independent_recent_copies(tmp_path: Path) -> None:
    """Save As retains the old saved file and restores either recent entry exactly.

    Args:
        tmp_path: Private workspace.

    Returns:
        None; copied file identity is separate from core project identity.
    """
    session = ProjectSession(tmp_path)
    session.create("Sample", sample=True)
    session.save()
    first = session.active["id"]
    accept_inputs(
        session.working,
        assessment(session.working),
        ["30", "98.1", "100"],
        calculate=True,
    )
    session.mark_changed()
    session.save(name="Packing revision.ergprj", new_copy=True)
    second = session.active["id"]
    assert first != second
    assert len(session.state["recent"]) == 2
    session.open_recent(first)
    assert read_project(session.working)["load_n"] == 49
    session.open_recent(second)
    assert read_project(session.working)["load_n"] == 98.1
    assert not session.active["dirty"]


def test_incomplete_draft_saves_without_old_result(tmp_path: Path) -> None:
    """Save preserves incomplete inputs and invalidates the prior calculation.

    Args:
        tmp_path: Disposable tablet native project.

    Returns:
        None; invalid/nonfinite edits cannot corrupt the previously accepted draft.
    """
    session = ProjectSession(tmp_path)
    session.create("Sample", sample=True)
    selected = accept_inputs(
        session.working,
        assessment(session.working),
        ["30", "49", "100"],
        calculate=True,
    )
    selected = accept_inputs(
        session.working, selected, ["30", "", "100"], calculate=False
    )
    session.mark_changed()
    session.save()
    assert read_project(session.working)["load_n"] is None
    assert read_project(session.working)["damage"] is None
    before = session.working.read_bytes()
    for invalid in ("bad", "nan", "inf"):
        with pytest.raises(ValueError):
            accept_inputs(
                session.working, selected, ["30", invalid, "100"], calculate=False
            )
        assert session.working.read_bytes() == before


def test_unsaved_discard_and_recent_limit(tmp_path: Path) -> None:
    """New-project discard closes it and the catalog offers ten newest saved files.

    Args:
        tmp_path: Private app directory.

    Returns:
        None; names containing separators never become managed file paths.
    """
    session = ProjectSession(tmp_path)
    session.create("Unsaved")
    session.discard()
    assert session.active is None
    for n in range(11):
        session.create(f"Project {n}")
        session.save()
    assert len(session.state["recent"]) == 10
    assert session.state["recent"][0]["name"] == "Project 10.ergprj"


def test_unchanged_reimport_reuses_saved_tablet_entry(tmp_path: Path) -> None:
    """Repeated opens of identical exported bytes do not duplicate recent entries.

    Args:
        tmp_path: Owned source and tablet folders.

    Returns:
        None; changed contents remain an independent unsaved import.
    """
    session = ProjectSession(tmp_path)
    session.create("Sample", sample=True)
    session.save()
    original = session.active["id"]
    data = session.working.read_bytes()
    session.activate(data, "Sample.ergprj", "Imported from Sample.ergprj")
    assert session.active["id"] == original
    assert not session.active["dirty"]
    session.save()
    assert len(session.state["recent"]) == 1
    accept_inputs(
        session.working,
        assessment(session.working),
        ["30", "98.1", "100"],
        calculate=True,
    )
    changed = session.working.read_bytes()
    session.activate(changed, "Sample.ergprj", "Imported from Sample.ergprj")
    assert session.active["id"] != original
    assert session.active["dirty"]

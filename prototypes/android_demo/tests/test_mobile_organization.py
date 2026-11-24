"""Native organization/timing edits preserve all assessment data and shared history."""

from pathlib import Path

import pytest
from assessment_contexts import read_contexts
from demo_project import build_demo
from mobile_organization import (
    accept_record,
    accept_timing,
    organization_snapshot,
    record_from_form,
    remove_record,
)
from project_session import ProjectSession

from ergotools.application.rotation_timing import shift_clock
from ergotools.application.rotation_timing_actions import draw_timing_break
from ergotools.domain.organization_record import OrganizationKind, OrganizationRecord


def session_with_demo(folder: Path) -> ProjectSession:
    """Create an owned private native fixture with real shift timing and source data.

    Args:
        folder: Dedicated temporary test directory.

    Returns:
        Editable session independent of every maintained or external project.
    """
    source = folder / "demo.ergprj"
    build_demo(source)
    session = ProjectSession(folder / "private")
    session.activate(source.read_bytes(), "Demo.ergprj", "Test")
    return session


def test_shift_timing_history_and_stale_intent(tmp_path: Path) -> None:
    """Timing edits, Undo/Redo and reopening preserve source/result pairs exactly.

    Args:
        tmp_path: Disposable native storage.

    Returns:
        None; stale timing consent rejects atomically and all tools remain exact.
    """
    session = session_with_demo(tmp_path)
    source = read_contexts(session.working)["records"]
    hierarchy, templates = organization_snapshot(session.working)
    assert shift_clock(hierarchy, "Night").span_minutes == 480
    old = templates[0].timing
    proposal = draw_timing_break(old, 30, 45)
    session.change(
        "Add timing break", lambda: accept_timing(session.working, "Day", old, proposal)
    )
    assert organization_snapshot(session.working)[1][0].timing == proposal
    assert read_contexts(session.working)["records"] == source
    before = session.working.read_bytes()
    with pytest.raises(ValueError):
        accept_timing(session.working, "Day", old, proposal)
    assert session.working.read_bytes() == before
    session.replay()
    assert organization_snapshot(session.working)[1][0].timing == old
    session.replay(redo=True)
    session.save()
    session.open_recent(session.active["id"])
    assert organization_snapshot(session.working)[1][0].timing == proposal
    assert read_contexts(session.working)["records"] == source


def test_organization_native_guards_and_incompatible_clock_reset(
    tmp_path: Path,
) -> None:
    """Protect references, stale hierarchy and existing timing when clocks change.

    Args:
        tmp_path: Private disposable hierarchy.

    Returns:
        None; confirmed reset and clock change form one undoable native change.
    """
    session = session_with_demo(tmp_path)
    hierarchy, templates = organization_snapshot(session.working)
    before = session.working.read_bytes()
    with pytest.raises(ValueError):
        remove_record(
            session.working, hierarchy, OrganizationKind.PLANT, ("Harbor Plant",)
        )
    assert session.working.read_bytes() == before
    record = OrganizationRecord(
        OrganizationKind.SHIFT,
        ("Day",),
        (("start_time", "08:00"), ("end_time", "17:00")),
    )
    with pytest.raises(ValueError, match="duration"):
        accept_record(session.working, hierarchy, record, creating=False)
    assert session.working.read_bytes() == before
    session.change(
        "Edit shift",
        lambda: accept_record(
            session.working, hierarchy, record, creating=False, reset_timing=True
        ),
    )
    changed, timing = organization_snapshot(session.working)
    assert shift_clock(changed, "Day").span_minutes == 540 and not timing
    with pytest.raises(ValueError, match="changed"):
        accept_record(
            session.working, hierarchy, record, creating=False, reset_timing=True
        )
    session.replay()
    assert organization_snapshot(session.working) == (hierarchy, templates)
    new = OrganizationRecord(
        OrganizationKind.PLANT,
        ("Training Plant",),
        (("description", "Test-only location"), ("opening_date", "2020-03-15")),
    )
    session.change(
        "Add organization",
        lambda: accept_record(session.working, hierarchy, new, creating=True),
    )
    current, _ = organization_snapshot(session.working)
    assert "Training Plant" in current.plants
    session.change(
        "Delete organization",
        lambda: remove_record(session.working, current, new.kind, new.keys),
    )
    session.replay()
    assert "Training Plant" in organization_snapshot(session.working)[0].plants


def test_clearing_optional_clocks_requires_explicit_timing_reset(
    tmp_path: Path,
) -> None:
    """Clearing optional Shift clocks cannot leave an orphaned/incompatible template.

    Args:
        tmp_path: Dedicated temporary native project.

    Returns:
        None; refusal preserves bytes, confirmed reset is undoable and sources survive.
    """
    session = session_with_demo(tmp_path)
    original = session.working.read_bytes()
    records = read_contexts(session.working)["records"]
    hierarchy, _ = organization_snapshot(session.working)
    replacement = OrganizationRecord(
        OrganizationKind.SHIFT, ("Day",), (("description", "Clock not decided"),)
    )
    with pytest.raises(ValueError):
        accept_record(session.working, hierarchy, replacement, creating=False)
    assert session.working.read_bytes() == original
    session.change(
        "Edit shift",
        lambda: accept_record(
            session.working, hierarchy, replacement, creating=False, reset_timing=True
        ),
    )
    current, templates = organization_snapshot(session.working)
    assert not templates
    with pytest.raises(ValueError, match="start and end"):
        shift_clock(current, "Day")
    assert read_contexts(session.working)["records"] == records
    session.replay()
    assert session.working.read_bytes() == original


def test_form_parser_retains_untouched_empty_null_and_numeric_values() -> None:
    """Editing one field must not normalize unrelated optional organization metadata.

    Args:
        None; parsing is pure and independent of GUI/storage.

    Returns:
        None; exact untouched attributes retain order, precision and null/empty values.
    """
    original = OrganizationRecord(
        OrganizationKind.SHIFT,
        ("Night",),
        (
            ("description", "Before"),
            ("notes", ""),
            ("downtime", None),
            ("product_output", 123.456789),
            ("start_time", "22:00"),
            ("end_time", "06:00"),
        ),
    )
    replacement = record_from_form(
        original,
        "Night",
        {
            "description": "After",
            "notes": "",
            "downtime": "",
            "product_output": "123.456789",
            "start_time": "22:00",
            "end_time": "06:00",
        },
    )
    assert replacement.attributes == (
        ("description", "After"),
        *original.attributes[1:],
    )
    cleared = record_from_form(replacement, "Night", {"description": ""})
    assert dict(cleared.attributes) == dict(original.attributes[1:])

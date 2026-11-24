"""M02 native worker/history/precision tests, without Qt or Android dependencies.

Use real domain, native catalogs and shared DocumentSession history; no maintained
project is edited. Known assessment results and metadata survive demographic edits.
"""

import re
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import pytest
from demo_service import calculate_and_save, read_project, source
from mobile_workers import (
    BODY_INPUT_PATTERN,
    age,
    delete_worker,
    filter_workers,
    form_values,
    initial,
    load_workers,
    make_worker,
    put_worker,
)
from project_session import ProjectSession

from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.work_catalog import WorkerEntry
from ergotools.domain.worker_details import WorkerDetails


def test_four_worker_creation_undo_redo_is_one_worker_per_step(tmp_path: Path) -> None:
    """Each creation is separate, and returning to the saved empty state is clean.

    Args:
        tmp_path: Disposable app-private workspace.

    Returns:
        None; full-project history never coalesces multiple worker records.
    """
    session = ProjectSession(tmp_path)
    session.create("Worker test")
    session.save()
    for n in range(1, 5):
        worker = WorkerEntry(f"W{n:02}")
        session.change(
            f"Add worker · {worker.worker_id}",
            lambda w=worker: put_worker(session.working, w),
        )
    for count in (3, 2, 1, 0):
        session.replay()
        assert len(load_workers(session.working)[0]) == count
    assert not session.active["dirty"]
    for count in (1, 2, 3, 4):
        session.replay(redo=True)
        assert len(load_workers(session.working)[0]) == count
    assert session.active["dirty"]
    session.save()
    assert len(load_workers(ProjectSession(tmp_path).working)[0]) == 4


def test_every_worker_field_undo_and_save_boundary(tmp_path: Path) -> None:
    """Names, dates, categories, body and contact changes each undo independently.

    Args:
        tmp_path: Owned project directory.

    Returns:
        None; Save retains history and replay never modifies the saved file.
    """
    session = ProjectSession(tmp_path)
    session.create("Demographics")
    worker = WorkerEntry("W01")
    session.change("Add worker · W01", lambda: put_worker(session.working, worker))
    session.save()
    values = form_values(worker, MeasurementSystem.METRIC)
    snapshots = [worker]
    fields = {
        "first_name": "Ana",
        "last_name": "Muñoz",
        "birth_date": "1991-06-15",
        "sex": "Female",
        "height_cm": "165.5",
        "weight_kg": "65.25",
        "hiring_date": "2020-01-03",
        "city": "Valdivia",
        "postal_code": "00123",
        "email": "ana@example.com",
    }
    for field, value in fields.items():
        values[field] = value
        previous = worker
        worker = make_worker(values, MeasurementSystem.METRIC, previous)
        session.change(
            f"Edit worker · {field}",
            lambda w=worker, p=previous: put_worker(session.working, w, expected=p),
        )
        snapshots.append(worker)
    session.save()
    saved = (
        session.folder / "projects" / f"{session.active['id']}.ergprj"
    ).read_bytes()
    for expected in reversed(snapshots[:-1]):
        session.replay()
        assert load_workers(session.working)[0] == (expected,)
    assert (
        session.folder / "projects" / f"{session.active['id']}.ergprj"
    ).read_bytes() == saved
    assert session.active["dirty"]
    for expected in snapshots[1:]:
        session.replay(redo=True)
        assert load_workers(session.working)[0] == (expected,)
    assert not session.active["dirty"]


def test_duplicate_stale_invalid_and_failed_changes_leave_history_intact(
    tmp_path: Path,
) -> None:
    """Refused edits cannot publish partial files or consume Undo entries.

    Args:
        tmp_path: Private native project.

    Returns:
        None; duplicate IDs, invalid forms and stale updates preserve exact bytes.
    """
    session = ProjectSession(tmp_path)
    session.create("Safe edits")
    worker = WorkerEntry("W01", "Ana")
    session.change("Add worker · W01", lambda: put_worker(session.working, worker))
    before, label = session.working.read_bytes(), session.history.undo_label_key
    for expected in (None, replace(worker, first_name="Other")):
        with pytest.raises(ValueError):
            session.change(
                "Bad edit",
                lambda p=expected: put_worker(session.working, worker, expected=p),
            )
        assert session.working.read_bytes() == before
        assert session.history.undo_label_key == label
    session.change(
        "No change", lambda: put_worker(session.working, worker, expected=worker)
    )
    assert session.history.undo_label_key == label


def test_delete_restore_and_reference_protection(tmp_path: Path) -> None:
    """Deletion restores via Undo, while a worker's existing assessment is protected.

    Args:
        tmp_path: Dedicated tablet sample.

    Returns:
        None; relationships and exact known calculated results remain unchanged.
    """
    session = ProjectSession(tmp_path)
    session.create("Sample", sample=True)
    calculated = calculate_and_save(session.working, source())
    session.mark_changed()
    original = load_workers(session.working)[0][0]
    edited = replace(original, details=replace(original.details, weight_kg=85))
    session.change(
        "Edit worker · weight",
        lambda: put_worker(session.working, edited, expected=original),
    )
    assert (
        read_project(session.working)["probability_percent"]
        == calculated["probability_percent"]
    )
    before = session.working.read_bytes()
    with pytest.raises(ValueError, match="assessments"):
        session.change(
            "Delete worker · W01", lambda: delete_worker(session.working, "W01")
        )
    assert session.working.read_bytes() == before
    worker = WorkerEntry("W02", "Diego")
    session.change("Add worker · W02", lambda: put_worker(session.working, worker))
    session.change("Delete worker · W02", lambda: delete_worker(session.working, "W02"))
    assert len(load_workers(session.working)[0]) == 1
    session.replay()
    assert worker in load_workers(session.working)[0]
    session.replay(redo=True)
    assert len(load_workers(session.working)[0]) == 1


def test_imperial_body_units_and_untouched_details_retain_precision() -> None:
    """Editing a name never round-trips body values or drops hidden contact details.

    Args:
        None.

    Returns:
        None; changed display body values convert using existing canonical helpers.
    """
    worker = WorkerEntry(
        "W01",
        "Ana",
        details=WorkerDetails(
            height_cm=165.12345678901234,
            weight_kg=65.98765432109876,
            address="Street 1",
            postal_code="00123",
        ),
    )
    values = form_values(worker, MeasurementSystem.IMPERIAL)
    values["first_name"] = "Anna"
    updated = make_worker(values, MeasurementSystem.IMPERIAL, worker)
    assert updated.details == worker.details
    values["height_cm"], values["weight_kg"] = "70", "150"
    updated = make_worker(values, MeasurementSystem.IMPERIAL, worker)
    assert updated.details.height_cm == 177.8
    assert updated.details.weight_kg == pytest.approx(68.0388555)
    assert updated.details.postal_code == "00123"


@pytest.mark.parametrize(
    "key,value",
    [
        ("worker_id", ""),
        ("worker_id", "W 01"),
        ("height_cm", "nan"),
        ("weight_kg", "-1"),
        ("birth_date", "1899-02-30"),
        ("birth_date", (date.today() + timedelta(days=1)).isoformat()),
        ("hiring_date", (date.today() + timedelta(days=1)).isoformat()),
    ],
)
def test_invalid_form_values_are_rejected(key: str, value: str) -> None:
    """Reject invalid IDs, body values and dates before any storage operation.

    Args:
        key: Form field under test.
        value: Invalid literal or future date.

    Returns:
        None; absent optional values remain permitted elsewhere.
    """
    with pytest.raises(ValueError):
        make_worker({"worker_id": "W01", key: value}, MeasurementSystem.METRIC)


def test_date_order_age_and_calendar_defaults() -> None:
    """Age uses full dates, optional dates stay absent and hiring cannot predate birth.

    Args:
        None.

    Returns:
        None; no default DOB is silently inserted by creation.
    """
    worker = make_worker({"worker_id": "W01"}, MeasurementSystem.METRIC)
    assert age(worker) is None and worker.details.birth_date is None
    worker = replace(worker, details=WorkerDetails(birth_date="2000-06-15"))
    assert age(worker, date(2026, 6, 14)) == 25
    assert age(worker, date(2026, 6, 15)) == 26
    with pytest.raises(ValueError, match="before"):
        make_worker(
            {
                "worker_id": "W01",
                "birth_date": "2000-06-15",
                "hiring_date": "1999-06-15",
            },
            MeasurementSystem.METRIC,
        )
    with pytest.raises(ValueError, match="cannot be changed"):
        make_worker({"worker_id": "NEW"}, MeasurementSystem.METRIC, worker)


def test_search_alphabet_order_and_history_limit(tmp_path: Path) -> None:
    """Check Spanish search/initials and bounded history with redo invalidation.

    Args:
        tmp_path: Private native project.

    Returns:
        None; UI filtering never determines storage identity or command grouping.
    """
    workers = (
        WorkerEntry("W02", "Elena", "Muñoz"),
        WorkerEntry("W01", "Diego", "Soto"),
        WorkerEntry("W03", "Sofía", "Álvarez"),
    )
    assert initial(workers[2]) == "A"
    assert filter_workers(workers, "munoz") == (workers[0],)
    assert filter_workers(workers, "SOFIA") == (workers[2],)
    assert filter_workers(workers, letter="S") == (workers[1],)
    assert filter_workers(workers, by_id=True)[0].worker_id == "W01"
    session = ProjectSession(tmp_path)
    session.create("Bounded history")
    session.save()
    for n in range(27):
        w = WorkerEntry(f"W{n:02}")
        session.change(
            f"Add worker · {w.worker_id}",
            lambda worker=w: put_worker(session.working, worker),
        )
    for _ in range(30):
        session.replay()
    assert len(load_workers(session.working)[0]) == 2
    assert session.history.undo_label_key is None
    session.replay(redo=True)
    w = WorkerEntry("New")
    session.change("Add worker · New", lambda: put_worker(session.working, w))
    assert session.history.redo_label_key is None


@pytest.mark.parametrize(
    "value,allowed",
    [
        ("", True),
        ("178", True),
        ("85.5", True),
        ("65,2", True),
        (".", True),
        ("0.", True),
        ("-1", False),
        ("text", False),
        ("1.2.3", False),
    ],
)
def test_body_filter_allows_clearing_and_partial_decimals(
    value: str, allowed: bool
) -> None:
    """Characterize Flet hasMatch behavior so the final numeric digit can be deleted.

    Args:
        value: Candidate complete field text during keyboard editing.
        allowed: Whether the presentation filter should accept this transient text.

    Returns:
        None; complete-value validation remains a separate domain/form operation.
    """
    assert bool(re.search(BODY_INPUT_PATTERN, value)) is allowed

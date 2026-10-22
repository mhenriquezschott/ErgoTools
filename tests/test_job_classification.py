"""Batch reference parity, invalid requests and all-or-nothing histories.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from ergotools.application.job_classification import (
    ClassificationRequest,
    classify_assignments,
)
from ergotools.domain.assessments.context import WorkerContext
from ergotools.domain.job_catalog import (
    Job,
    JobCatalog,
    JobPlacement,
    WorkerJobAssignment,
)
from ergotools.domain.work_catalog import StationKey

# Exact synthetic station-at-shift context used by assignment/history transitions.
PLACE = StationKey("P", "S", "L", "1").at_shift("Day")
# Exact project/worker/workplace/shift ownership used to distinguish historical
# assignment links.
OWNER = WorkerContext("p", "w", PLACE)
# Immutable exact synthetic worker/job/catalog relationships used by these isolated
# regressions.
CATALOG = JobCatalog(
    "p",
    (Job("j", "Job"), Job("k", "Other")),
    (JobPlacement(1, "j", PLACE), JobPlacement(2, "k", PLACE)),
    (WorkerJobAssignment(1, OWNER, 1, started_at="2020", notes="original"),),
)
# Fixed 2026-10-01 decision date; transition tests do not depend on the machine
# calendar.
TODAY = date(2026, 10, 1)


def test_actual_reference_batch_classification() -> None:
    """Compare exact row metadata for classification, change, removal and no-op.

    Args:
        None.

    Returns:
        None.
    """
    fixture = json.loads(
        (
            Path(__file__).parent / "fixtures/job_classification_reference.json"
        ).read_text()
    )
    for case in fixture["cases"]:
        identity, placement, start, end, notes = case["initial"]
        source = replace(
            CATALOG,
            assignments=(
                WorkerJobAssignment(
                    identity, OWNER, placement, True, start, end, notes
                ),
            ),
        )
        result = classify_assignments(
            source,
            "w",
            (ClassificationRequest(1, case["target"], 2),),
            effective_date=TODAY,
        )
        assert [
            [
                item.assignment_id,
                item.placement_id,
                item.started_at,
                item.ended_at,
                int(item.active),
                item.notes,
            ]
            for item in result.assignments
        ] == case["rows"]


def test_late_failure_does_not_publish_partial_history() -> None:
    """A valid removal followed by a missing assignment leaves the input intact.

    Args:
        None.

    Returns:
        None.
    """
    with pytest.raises(ValueError):
        classify_assignments(
            CATALOG,
            "w",
            (ClassificationRequest(1, None, 2), ClassificationRequest(99, None, 3)),
            effective_date=TODAY,
        )
    assert len(CATALOG.assignments) == 1
    assert CATALOG.assignments[0].active


def test_multiple_contexts_and_successor_collisions() -> None:
    """Batch requests retain separate workplace ownership and reject reused IDs.

    Args:
        None.

    Returns:
        None.
    """
    owner = replace(OWNER, workplace=replace(PLACE, shift_id="Night"))
    source = replace(
        CATALOG,
        placements=(*CATALOG.placements, JobPlacement(3, "j", owner.workplace)),
        assignments=(*CATALOG.assignments, WorkerJobAssignment(2, owner, 3)),
    )
    with pytest.raises(ValueError, match="successor"):
        classify_assignments(
            source,
            "w",
            (
                ClassificationRequest(1, None, 3),
                ClassificationRequest(2, None, 3),
            ),
            effective_date=TODAY,
        )
    result = classify_assignments(
        source,
        "w",
        (
            ClassificationRequest(1, None, 3),
            ClassificationRequest(2, None, 4),
        ),
        effective_date=TODAY,
    )
    assert [item.active for item in result.assignments] == [False, False, True, True]
    assert [item.worker for item in result.assignments[2:]] == [OWNER, owner]


def test_invalid_batches_and_inactive_targets() -> None:
    """Reject typed/ownership/placement/date errors without silently skipping rows.

    Args:
        None.

    Returns:
        None.
    """
    for requests, worker, day in (
        ((ClassificationRequest(1, None),), "w", TODAY),
        ((ClassificationRequest(1, None, 1),), "w", TODAY),
        ((ClassificationRequest(1, 99),), "w", TODAY),
        ((ClassificationRequest(1, 2, 2),), "other", TODAY),
        ((ClassificationRequest(1, 1), ClassificationRequest(1, 1)), "w", TODAY),
        ((None,), "w", TODAY),
        ((), "", TODAY),
        ((), "w", "2026-10-01"),
    ):
        with pytest.raises(ValueError):
            classify_assignments(CATALOG, worker, requests, effective_date=day)
    for source in (
        replace(CATALOG, assignments=(replace(CATALOG.assignments[0], active=False),)),
        replace(CATALOG, jobs=(Job("j", "Job"), Job("k", "Other", False))),
        replace(
            CATALOG,
            placements=(
                CATALOG.placements[0],
                replace(CATALOG.placements[1], active=False),
            ),
        ),
        replace(
            CATALOG,
            placements=(
                CATALOG.placements[0],
                replace(
                    CATALOG.placements[1], workplace=replace(PLACE, shift_id="Night")
                ),
            ),
        ),
        replace(
            CATALOG, assignments=(replace(CATALOG.assignments[0], started_at="2099"),)
        ),
    ):
        with pytest.raises(ValueError):
            classify_assignments(
                source, "w", (ClassificationRequest(1, 2, 2),), effective_date=TODAY
            )
    for values in ((True, None), (1, True), (1, None, True)):
        with pytest.raises(ValueError):
            ClassificationRequest(*values)


def test_empty_and_unchanged_batches_preserve_identity() -> None:
    """No edits preserve the original snapshot; existing start and notes survive.

    Args:
        None.

    Returns:
        None.
    """
    assert classify_assignments(CATALOG, "w", (), effective_date=TODAY) is CATALOG
    assert (
        classify_assignments(
            CATALOG, "w", (ClassificationRequest(1, 1),), effective_date=TODAY
        )
        is CATALOG
    )
    source = replace(
        CATALOG, assignments=(replace(CATALOG.assignments[0], placement_id=None),)
    )
    result = classify_assignments(
        source, "w", (ClassificationRequest(1, 2),), effective_date=TODAY
    )
    assert result.assignments[0].started_at == "2020"
    assert result.assignments[0].notes == "original"

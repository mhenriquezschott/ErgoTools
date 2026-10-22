"""Reference assignment-history transitions and transactional application.

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

from ergotools.application.job_assignment import assign_worker
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
)
# Fixed 2026-10-01 decision date; transition tests do not depend on the machine
# calendar.
TODAY = date(2026, 10, 1)


def test_actual_reference_assignment_transitions() -> None:
    """Compare identities, history, dates and notes against reference function.

    Args:
        None.

    Returns:
        None.
    """
    fixture = json.loads(
        (Path(__file__).parent / "fixtures/job_assignment_reference.json").read_text()
    )
    for case in fixture["cases"]:
        initial = case["initial"]
        catalog = CATALOG
        if initial:
            identity, placement, start, end, notes = initial
            catalog = replace(
                catalog,
                assignments=(
                    WorkerJobAssignment(
                        identity, OWNER, placement, True, start, end, notes
                    ),
                ),
            )
        result = assign_worker(
            catalog,
            OWNER,
            2,
            effective_date=TODAY,
            new_assignment_id=2 if initial else 1,
        )
        assert result.assignment_id == case["result"]
        assert [
            [
                item.assignment_id,
                item.placement_id,
                item.started_at,
                item.ended_at,
                int(item.active),
                item.notes,
            ]
            for item in result.jobs.assignments
        ] == case["rows"]


def test_invalid_requests_and_future_history_leave_source_unchanged() -> None:
    """Reject inactive targets, wrong contexts, identity reuse and reversed dates.

    Args:
        None.

    Returns:
        None.
    """
    old = WorkerJobAssignment(1, OWNER, 1, started_at="2099-01-01")
    catalog = replace(CATALOG, assignments=(old,))
    for source, owner, placement, identity, day in (
        (catalog, OWNER, 99, 2, TODAY),
        (
            replace(catalog, jobs=(Job("j", "Job"), Job("k", "Other", False))),
            OWNER,
            2,
            2,
            TODAY,
        ),
        (
            replace(
                catalog,
                placements=(
                    CATALOG.placements[0],
                    replace(CATALOG.placements[1], active=False),
                ),
            ),
            OWNER,
            2,
            2,
            TODAY,
        ),
        (catalog, replace(OWNER, project_id="other"), 2, 2, TODAY),
        (
            catalog,
            replace(OWNER, workplace=replace(PLACE, shift_id="Night")),
            2,
            2,
            TODAY,
        ),
        (catalog, OWNER, 2, 1, TODAY),
        (catalog, OWNER, 2, 2, TODAY),
        (catalog, OWNER, True, 2, TODAY),
        (catalog, OWNER, 2, True, TODAY),
        (catalog, OWNER, 2, 2, "2026-10-01"),
    ):
        with pytest.raises(ValueError):
            assign_worker(
                source, owner, placement, effective_date=day, new_assignment_id=identity
            )
    assert catalog.assignments == (old,)


def test_classification_preserves_existing_start_and_inactive_history() -> None:
    """Classification retains row identity and start; repeated selection is a no-op.

    Args:
        None.

    Returns:
        None.
    """
    history = WorkerJobAssignment(5, OWNER, 1, False, "2020", "2021", "history")
    current = WorkerJobAssignment(6, OWNER, None, started_at="2022")
    catalog = replace(CATALOG, assignments=(history, current))
    result = assign_worker(catalog, OWNER, 2, effective_date=TODAY, new_assignment_id=5)
    assert result.assignment_id == 6
    assert result.jobs.assignments[0] is history
    assert result.jobs.assignments[1].started_at == "2022"
    again = assign_worker(
        result.jobs, OWNER, 2, effective_date=TODAY, new_assignment_id=5
    )
    assert again.jobs is result.jobs

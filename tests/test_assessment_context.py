"""Assessment ownership parity, isolation and malformed snapshot guards.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from ergotools.application.assessment_assignment import (
    AssignmentSnapshot,
    resolve_assessment_assignment,
)
from ergotools.domain.assessments.context import (
    AssessmentContext,
    WorkerContext,
    WorkplaceContext,
)
from ergotools.domain.assessments.document import AssessmentKind

# Explicit synthetic complete plant/section/line/station/shift identity.
WORKPLACE = WorkplaceContext("Plant", "Section", "Line", "Station", "Day")
# Immutable synthetic worker identity/details used to characterize catalog labels or
# exact ownership.
WORKER = WorkerContext("project", "w1", WORKPLACE)
# Synthetic assignment record retaining the exact owner, activity and history metadata
# under test.
ASSIGNMENT = AssignmentSnapshot(WORKER, 7, True, 10, True)


def test_reference_assignment_selection() -> None:
    """Replay actual reference SQL/method outputs without reference dependencies.

    Args:
        None.

    Returns:
        None.
    """
    fixture = json.loads(
        (
            Path(__file__).parent / "fixtures/assessment_context_reference.json"
        ).read_text()
    )
    for case in fixture["cases"]:
        candidate = AssignmentSnapshot(
            WorkerContext(
                "project", case["worker_id"], WorkplaceContext(*case["workplace"])
            ),
            fixture["assignment_id"],
            case["active"],
            case["job_placement_id"],
            case["placement_active"],
        )
        selected = resolve_assessment_assignment(WORKER, (candidate,))
        assert (selected.assignment_id if selected else None) == case[
            "expected_assignment_id"
        ], case["name"]


def test_each_ownership_component_is_significant() -> None:
    """Project, worker, every workplace field and tool prevent identity collisions.

    Args:
        None.

    Returns:
        None.
    """
    original = AssessmentContext(WORKER, AssessmentKind.LIFFT)
    contexts = {original}
    for field in ("project_id", "worker_id"):
        changed = replace(WORKER, **{field: "other"})
        contexts.add(replace(original, worker=changed))
        assert (
            resolve_assessment_assignment(
                WORKER, (replace(ASSIGNMENT, worker=changed),)
            )
            is None
        )
    for field in ("plant_name", "section_name", "line_name", "station_id", "shift_id"):
        changed = replace(WORKER, workplace=replace(WORKPLACE, **{field: "other"}))
        contexts.add(replace(original, worker=changed))
        assert (
            resolve_assessment_assignment(
                WORKER, (replace(ASSIGNMENT, worker=changed),)
            )
            is None
        )
    for kind in (AssessmentKind.DUET, AssessmentKind.TST):
        contexts.add(replace(original, kind=kind))
    assert len(contexts) == 10
    assert original == AssessmentContext(WORKER, AssessmentKind.LIFFT)


def test_assignment_lookup_is_read_only_and_order_independent() -> None:
    """Ignore inactive history and other projects without modifying source rows.

    Args:
        None.

    Returns:
        None.
    """
    inactive = replace(ASSIGNMENT, active=False, assignment_id=8)
    foreign = replace(ASSIGNMENT, worker=replace(WORKER, project_id="other"))
    rows = (inactive, foreign, ASSIGNMENT)
    assert resolve_assessment_assignment(WORKER, iter(rows)) is ASSIGNMENT
    assert resolve_assessment_assignment(WORKER, reversed(rows)) is ASSIGNMENT
    assert rows == (inactive, foreign, ASSIGNMENT)
    assert resolve_assessment_assignment(WORKER, ()) is None
    for value, field, replacement in (
        (WORKPLACE, "shift_id", "Night"),
        (WORKER, "worker_id", "w2"),
        (AssessmentContext(WORKER, AssessmentKind.LIFFT), "kind", AssessmentKind.DUET),
        (ASSIGNMENT, "active", False),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(value, field, replacement)


def test_duplicate_active_owners_fail_even_without_eligible_placements() -> None:
    """Refuse schema-invalid ambiguity instead of taking the first returned row.

    Args:
        None.

    Returns:
        None.
    """
    for candidate in (
        ASSIGNMENT,
        replace(ASSIGNMENT, job_placement_id=None),
        replace(ASSIGNMENT, placement_active=False),
    ):
        for rows in ((ASSIGNMENT, candidate), (candidate, ASSIGNMENT)):
            with pytest.raises(ValueError, match="Multiple active"):
                resolve_assessment_assignment(WORKER, rows)


@pytest.mark.parametrize("invalid", ["", " \t", None, 1, True])
def test_context_rejects_absent_or_untyped_identifiers(invalid: object) -> None:
    """Reject bad boundaries without inventing IDs by string coercion.

    Args:
        invalid: Deliberately invalid typed boundary value; must fail without partial
            state changes.

    Returns:
        None.
    """
    for field in ("plant_name", "section_name", "line_name", "station_id", "shift_id"):
        with pytest.raises(ValueError, match="nonblank"):
            replace(WORKPLACE, **{field: invalid})
    for field in ("project_id", "worker_id"):
        with pytest.raises(ValueError, match="nonblank"):
            replace(WORKER, **{field: invalid})


def test_context_retains_exact_spelling_and_rejects_untyped_objects() -> None:
    """Identity normalization and legacy tool-name mapping belong to adapters.

    Args:
        None.

    Returns:
        None.
    """
    workplace = replace(WORKPLACE, station_id=" 001 ")
    assert workplace.station_id == " 001 "
    assert workplace != replace(workplace, station_id="001")
    for constructor, arguments in (
        (WorkerContext, ("p", "w", None)),
        (AssessmentContext, (None, AssessmentKind.LIFFT)),
        (AssessmentContext, (WORKER, "LiFFT")),
        (AssignmentSnapshot, (None, 7, True, 10, True)),
    ):
        with pytest.raises(ValueError):
            constructor(*arguments)
    with pytest.raises(ValueError, match="typed worker"):
        resolve_assessment_assignment(None, ())


def test_assignment_rejects_ambiguous_row_types() -> None:
    """SQLite adapters must normalize flags but must not coerce ID strings.

    Args:
        None.

    Returns:
        None.
    """
    for field in ("assignment_id", "job_placement_id"):
        for value in (True, "7", 7.0):
            with pytest.raises(ValueError, match="integers"):
                replace(ASSIGNMENT, **{field: value})
    with pytest.raises(ValueError, match="integers"):
        replace(ASSIGNMENT, assignment_id=None)
    for field in ("active", "placement_active"):
        for value in (0, 1, "false", None):
            with pytest.raises(ValueError, match="booleans"):
                replace(ASSIGNMENT, **{field: value})

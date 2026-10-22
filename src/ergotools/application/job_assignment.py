"""Pure worker assignment transitions with explicit date and identity inputs.

Application layer. Compose immutable domain values through injected read/write ports.
This module owns no widgets, SQL connection, global clock or renderer; persistence and
modal consent belong to its caller.
"""

from dataclasses import dataclass, replace
from datetime import date

from ergotools.domain.assessments.context import WorkerContext, WorkplaceContext
from ergotools.domain.job_catalog import JobCatalog, WorkerJobAssignment


@dataclass(frozen=True, slots=True)
class AssignmentChange:
    """Pure assignment transition result for a subsequent atomic workspace replacement.

    Attributes:
        jobs: Complete proposed catalog, including retained historical rows.
        assignment_id: Stable active assignment identity selected by the transition.
    """

    jobs: JobCatalog
    assignment_id: int


def assign_worker(
    catalog: JobCatalog,
    worker: WorkerContext,
    placement_id: int | None,
    *,
    effective_date: date,
    new_assignment_id: int,
    creation_note: str = "Created from Worker Management.",
) -> AssignmentChange:
    """Assign an exact worker context while preserving classified history.

    The caller supplies the business date and an unused integer identity if a new row is
    needed. No clock, database or UI access occurs here. Commit the returned catalog
    through workspace expected-value replacement; hierarchy membership is validated
    there under the write lock. ValueError rejects invalid requests.

    An unclassified active assignment is classified in place. A classified reassignment
    closes its old row and creates a successor, so assessments keep their original
    assignment. No repository write occurs here.

    Args:
        catalog: Validated immutable jobs, placements and assignment history.
        worker: Exact project, worker and workplace to classify.
        placement_id: Existing active Job placement at this workplace, or None for
            a workplace-only assignment used by worker-based PLOT analysis.
        effective_date: Caller-supplied calendar date for new start/close dates;
            existing dates are retained.
        new_assignment_id: Unused integer identity required only when a successor
            assignment is created.
        creation_note: Origin note for a new assignment. Existing management calls
            retain their reference note; direct assessment association names its origin.

    Returns:
        Replacement catalog and selected active assignment identity; an identical
        assignment returns the unchanged catalog.

    Raises:
        ValueError: Date/identities, project, placement or successor identity is
            invalid, including invalid resulting date ranges.
    """
    if type(effective_date) is not date:
        raise ValueError("Effective date must be a calendar date.")
    if (placement_id is not None and type(placement_id) is not int) or type(
        new_assignment_id
    ) is not int:
        raise ValueError("Assignment and placement identities require integers.")
    if worker.project_id != catalog.project_id:
        raise ValueError("Worker belongs to another project.")
    placement = next(
        (item for item in catalog.placements if item.placement_id == placement_id),
        None,
    )
    if placement_id is not None and (
        placement is None
        or not placement.active
        or placement.workplace != worker.workplace
        or not next(
            job.active for job in catalog.jobs if job.job_id == placement.job_id
        )
    ):
        raise ValueError("Selected placement is not active in this workplace.")
    current = next(
        (item for item in catalog.assignments if item.worker == worker and item.active),
        None,
    )
    today = effective_date.isoformat()
    if current is not None and current.placement_id == placement_id:
        return AssignmentChange(catalog, current.assignment_id)
    if current is not None and current.placement_id is None:
        classified = replace(
            current,
            placement_id=placement_id,
            started_at=current.started_at if current.started_at is not None else today,
            notes="Classified from Worker Management.",
        )
        return AssignmentChange(
            replace(
                catalog,
                assignments=tuple(
                    classified if item is current else item
                    for item in catalog.assignments
                ),
            ),
            current.assignment_id,
        )
    if any(item.assignment_id == new_assignment_id for item in catalog.assignments):
        raise ValueError("New assignment identity is already in use.")
    previous = catalog.assignments
    if current is not None:
        closed = replace(
            current,
            active=False,
            ended_at=current.ended_at if current.ended_at is not None else today,
        )
        previous = tuple(closed if item is current else item for item in previous)
    created = WorkerJobAssignment(
        new_assignment_id,
        worker,
        placement_id,
        started_at=today,
        notes=(
            creation_note
            if current is None
            else "Job assignment changed from Worker Management."
        ),
    )
    return AssignmentChange(
        replace(catalog, assignments=(*previous, created)), new_assignment_id
    )


def change_worker_assignment(
    catalog: JobCatalog,
    worker_id: str,
    assignment_id: int,
    placement_id: int | None,
    *,
    workplace: WorkplaceContext | None = None,
    effective_date: date,
    new_assignment_id: int,
) -> AssignmentChange:
    """End an active assignment or replace it with an explicit job/workplace.

    Existing rows are closed rather than erased: saved assessments keep their original
    owner and workplace. A destination already occupied by another active assignment
    is rejected, never silently merged or reassigned. The caller commits once through
    expected-value catalog replacement; failures leave the original immutable catalog.

    Args:
        catalog: Validated immutable job/placement/assignment catalog.
        worker_id: Exact selected worker, required to own the active source row.
        assignment_id: Active assignment to end or replace.
        placement_id: Optional active destination Job. None with no workplace ends
            without a successor; None with a workplace assigns it without a Job.
        workplace: Explicit optional destination for workplace-only changes. A supplied
            Job placement must match this context.
        effective_date: Explicit calendar date used to close/start assignments.
        new_assignment_id: Unused successor identity required for a changed destination.

    Returns:
        Complete proposed catalog and successor identity, or the closed identity for
        removal. An unchanged placement returns the original catalog.

    Raises:
        ValueError: Ownership, date, identity, destination eligibility or dates are
            invalid, or another active assignment occupies the destination.
    """
    if type(effective_date) is not date or type(assignment_id) is not int:
        raise ValueError("Assignment and date require explicit valid types.")
    current = next(
        (a for a in catalog.assignments if a.assignment_id == assignment_id), None
    )
    if current is None or not current.active or current.worker.worker_id != worker_id:
        raise ValueError("Select an active assignment belonging to this Worker.")
    if placement_id is not None:
        if type(placement_id) is not int:
            raise ValueError("Placement identity requires an integer.")
        placement = next(
            (p for p in catalog.placements if p.placement_id == placement_id), None
        )
        if (
            placement is None
            or not placement.active
            or not next(j.active for j in catalog.jobs if j.job_id == placement.job_id)
        ):
            raise ValueError("Selected Job placement is unavailable.")
        if workplace is not None and workplace != placement.workplace:
            raise ValueError("Job placement does not match the selected workplace.")
        workplace = placement.workplace
    if workplace is not None:
        if not isinstance(workplace, WorkplaceContext):
            raise ValueError("Select a real workplace and shift.")
        if (
            current.placement_id == placement_id
            and current.worker.workplace == workplace
        ):
            return AssignmentChange(catalog, assignment_id)
        destination = replace(current.worker, workplace=workplace)
        if any(
            a.active and a.worker == destination and a.assignment_id != assignment_id
            for a in catalog.assignments
        ):
            raise ValueError(
                "This Worker already has an assignment at the selected "
                "workplace and shift."
            )
    closed = replace(current, active=False, ended_at=effective_date.isoformat())
    replacement = replace(
        catalog,
        assignments=tuple(closed if a is current else a for a in catalog.assignments),
    )
    if workplace is None:
        return AssignmentChange(replacement, assignment_id)
    return assign_worker(
        replacement,
        destination,
        placement_id,
        effective_date=effective_date,
        new_assignment_id=new_assignment_id,
    )

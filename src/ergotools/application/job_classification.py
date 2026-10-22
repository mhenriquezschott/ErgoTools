"""Atomic-in-memory batch classification changes preserving assignment history.

Application layer. Compose immutable domain values through injected read/write ports.
This module owns no widgets, SQL connection, global clock or renderer; persistence and
modal consent belong to its caller.
"""

from dataclasses import dataclass, replace
from datetime import date

from ergotools.domain.job_catalog import JobCatalog, WorkerJobAssignment


@dataclass(frozen=True, slots=True)
class ClassificationRequest:
    """One active assignment transition; apply the whole batch or reject it.

    Attributes:
        assignment_id: Exact active assignment owned by the selected worker.
        placement_id: Exact destination placement; None requests unclassification.
        successor_id: Unused identity for a classified row successor; unnecessary for an
            unchanged or currently unclassified row.
    """

    assignment_id: int
    placement_id: int | None
    successor_id: int | None = None

    def __post_init__(self) -> None:
        """Reject implicit integer conversions at the command boundary.

        Args:
            None.

        Returns:
            None; validate exact integer identities without coercion.

        Raises:
            ValueError: Any supplied identity is not an integer, including booleans.
        """
        if type(self.assignment_id) is not int or any(
            value is not None and type(value) is not int
            for value in (self.placement_id, self.successor_id)
        ):
            raise ValueError("Assignment and placement identities require integers.")


def classify_assignments(
    catalog: JobCatalog,
    worker_id: str,
    requests: tuple[ClassificationRequest, ...],
    *,
    effective_date: date,
) -> JobCatalog:
    """Return a complete replacement or raise without changing the source.

    Requests address distinct active rows in the original snapshot, belonging to one
    worker. Classified changes require an unused successor ID. Missing targets,
    inactive/incompatible placements and invalid resulting dates raise ValueError.
    Commit once through workspace expected-value replacement; no partial result escapes
    when a later request fails. This operation performs no I/O.

    Args:
        catalog: Validated original immutable catalog used for every request
            precondition.
        worker_id: Exact nonblank worker identity owning all requested active
            assignments.
        requests: Distinct active assignment transitions; None placement removes
            classification.
        effective_date: Caller-supplied calendar date for successor starts and
            previous-row closures.

    Returns:
        One complete replacement catalog; unchanged original when all requested
        classifications are already selected.

    Raises:
        ValueError: Requests are untyped/duplicated, ownership or placement is invalid,
            successor IDs collide, or resulting dates violate catalog constraints.
    """
    if type(effective_date) is not date:
        raise ValueError("Effective date must be a calendar date.")
    if not isinstance(worker_id, str) or not worker_id.strip():
        raise ValueError("Worker identity must be nonblank text.")
    requests = tuple(requests)
    if any(not isinstance(item, ClassificationRequest) for item in requests):
        raise ValueError("Classification requests require explicit types.")
    if len({item.assignment_id for item in requests}) != len(requests):
        raise ValueError("Each assignment may be requested only once.")
    original = {item.assignment_id: item for item in catalog.assignments}
    placements = {item.placement_id: item for item in catalog.placements}
    jobs = {item.job_id: item for item in catalog.jobs}
    replacements: dict[int, WorkerJobAssignment] = {}
    additions: list[WorkerJobAssignment] = []
    used = set(original)
    today = effective_date.isoformat()
    for request in requests:
        current = original.get(request.assignment_id)
        if (
            current is None
            or not current.active
            or current.worker.worker_id != worker_id
        ):
            raise ValueError("Active assignment does not belong to this worker.")
        if request.placement_id is not None:
            placement = placements.get(request.placement_id)
            if (
                placement is None
                or not placement.active
                or not jobs[placement.job_id].active
                or placement.workplace != current.worker.workplace
            ):
                raise ValueError("Selected placement is not active in this workplace.")
        if current.placement_id == request.placement_id:
            continue
        if current.placement_id is None:
            replacements[current.assignment_id] = replace(
                current,
                placement_id=request.placement_id,
                started_at=current.started_at
                if current.started_at is not None
                else today,
            )
            continue
        if request.successor_id is None or request.successor_id in used:
            raise ValueError("Classified changes require an unused successor identity.")
        used.add(request.successor_id)
        replacements[current.assignment_id] = replace(
            current,
            active=False,
            ended_at=current.ended_at if current.ended_at is not None else today,
        )
        additions.append(
            WorkerJobAssignment(
                request.successor_id,
                current.worker,
                request.placement_id,
                started_at=today,
                notes="Classification changed from Worker Management.",
            )
        )
    if not replacements:
        return catalog
    return replace(
        catalog,
        assignments=tuple(
            replacements.get(item.assignment_id, item) for item in catalog.assignments
        )
        + tuple(additions),
    )

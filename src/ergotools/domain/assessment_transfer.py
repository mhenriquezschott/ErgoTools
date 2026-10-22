"""Explicit copy/move of saved current assessments with historical ownership.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from collections.abc import Mapping
from dataclasses import dataclass, replace

from ergotools.domain.assessment_history import AssessmentHistory, AssignmentAssessment
from ergotools.domain.assessments.context import WorkerContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_catalog import JobCatalog, WorkerJobAssignment
from ergotools.domain.work_catalog import WorkCatalog


@dataclass(frozen=True, slots=True)
class TransferRequest:
    """Transfer selected saved tools; move removes only those assessments.

    Attributes:
        source_assignment_id: Exact assignment whose selected saved current assessments
            are transferred.
        destination: Exact destination project/worker/workplace owner, including shift.
        kinds: Ordered selected model identities; the transfer planner requires a
            nonempty unique selection.
        move: False copies; True additionally removes only the transferred source
            assessments.
    """

    source_assignment_id: int
    destination: WorkerContext
    kinds: tuple[AssessmentKind, ...]
    move: bool = False

    def __post_init__(self) -> None:
        """Snapshot tool selections and reject implicit identity/mode coercion.

        Args:
            None. Dataclass construction supplies the fields documented on
            TransferRequest.

        Returns:
            None. Construction validates this record before publishing it. Snapshot
            kinds as immutable tuples on the new frozen instance.

        Raises:
            ValueError: Transfer requires typed source, owner and mode.
        """
        object.__setattr__(self, "kinds", tuple(self.kinds))
        if (
            type(self.source_assignment_id) is not int
            or not isinstance(self.destination, WorkerContext)
            or type(self.move) is not bool
        ):
            raise ValueError("Transfer requires typed source, owner and mode.")


@dataclass(frozen=True, slots=True)
class TransferPlan:
    """Expected catalogs, exact source/copy pairs and explicitly removed assessments.

    Attributes:
        jobs: Immutable project job, placement and assignment snapshot.
        copies: Ordered pairs of original source records and newly identified
            destination records.
        removed_documents: Exact source document IDs to remove for a move; empty for a
            copy.
    """

    jobs: JobCatalog
    copies: tuple[tuple[AssignmentAssessment, AssignmentAssessment], ...]
    removed_documents: tuple[str, ...]


def plan_transfer(
    work: WorkCatalog,
    jobs: JobCatalog,
    history: AssessmentHistory,
    request: TransferRequest,
    document_ids: Mapping[AssessmentKind, str],
) -> TransferPlan:
    """Validate all selected tools and destinations before any save or write.

    Conflicts at any assignment in the destination context reject the entire request.
    Create an unclassified active assignment if none exists; retain existing
    assignments, jobs, profiles and assessments belonging to other owners.

    Args:
        work: Project worker/station/shift snapshot used to validate destination
            membership.
        jobs: Immutable job, placement and assignment catalog for the same project.
        history: Saved assignment-owned assessments; one per assignment/tool.
        request: Exact source assignment, destination owner, selected tools and
            copy/move intent.
        document_ids: Caller-allocated new document identity for every selected model;
            no IDs are generated here.

    Returns:
        Validated destination catalog, exact source/copy pairs and explicit move
        removals; no persistence occurs.

    Raises:
        ValueError: A typed transfer request is required. Select at least one tool and
            an explicit copy/move mode. Transfer tools must be unique typed identities.
            Transfer catalogs belong to different projects. Destination belongs to
            another project. Source assignment does not exist. Source and destination
            contexts are identical. Destination already contains selected assessment
            data. Selected source has no saved assessment. New assessment identity
            must be unique and nonblank.
        KeyError: A selected model has no caller-allocated destination document ID, or
            the destination worker/workplace is absent from the work catalog.
    """
    if not isinstance(request, TransferRequest):
        raise ValueError("A typed transfer request is required.")
    if type(request.move) is not bool or not request.kinds:
        raise ValueError("Select at least one tool and an explicit copy/move mode.")
    if len(set(request.kinds)) != len(request.kinds) or any(
        not isinstance(kind, AssessmentKind) for kind in request.kinds
    ):
        raise ValueError("Transfer tools must be unique typed identities.")
    if work.project_id != jobs.project_id or history.project_id != jobs.project_id:
        raise ValueError("Transfer catalogs belong to different projects.")
    owner = work.worker_context(
        request.destination.worker_id, request.destination.workplace
    )
    if owner != request.destination:
        raise ValueError("Destination belongs to another project.")
    source = next(
        (
            item
            for item in jobs.assignments
            if item.assignment_id == request.source_assignment_id
        ),
        None,
    )
    if source is None:
        raise ValueError("Source assignment does not exist.")
    if source.worker == owner:
        raise ValueError("Source and destination contexts are identical.")
    destinations = {
        item.assignment_id for item in jobs.assignments if item.worker == owner
    }
    if any(
        item.assignment_id in destinations and item.kind in request.kinds
        for item in history.entries
    ):
        raise ValueError("Destination already contains selected assessment data.")
    target = next(
        (item for item in jobs.assignments if item.worker == owner and item.active),
        None,
    )
    if target is None:
        target = WorkerJobAssignment(
            max((item.assignment_id for item in jobs.assignments), default=0) + 1,
            owner,
            None,
        )
        jobs = replace(jobs, assignments=(*jobs.assignments, target))
    copies = []
    existing_ids = {item.document_id for item in history.entries}
    for kind in request.kinds:
        current = history.current_for(source.assignment_id, kind)
        if current is None:
            raise ValueError("Selected source has no saved assessment.")
        identity = document_ids[kind]
        if (
            not isinstance(identity, str)
            or not identity.strip()
            or identity in existing_ids
        ):
            raise ValueError("New assessment identity must be unique and nonblank.")
        existing_ids.add(identity)
        copies.append(
            (
                current,
                replace(
                    current,
                    document_id=identity,
                    assignment_id=target.assignment_id,
                    worker_id=target.worker.worker_id,
                ),
            )
        )
    return TransferPlan(
        jobs,
        tuple(copies),
        tuple(source.document_id for source, _ in copies) if request.move else (),
    )

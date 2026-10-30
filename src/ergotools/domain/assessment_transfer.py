"""Explicit copy/move of saved current assessments with historical ownership.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from collections.abc import Mapping
from dataclasses import dataclass, replace

from ergotools.domain.assessment_history import AssessmentHistory, AssignmentAssessment
from ergotools.domain.assessments.context import WorkerContext, _require_identity
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_catalog import JobCatalog, WorkerJobAssignment
from ergotools.domain.work_catalog import WorkCatalog


@dataclass(frozen=True, slots=True)
class StandaloneDestination:
    """Exact standalone destination; no fabricated station or shift participates.

    Attributes:
        project_id: Saved project identity.
        worker_id: Existing destination worker, whose selected tools are independent.
    """

    project_id: str
    worker_id: str

    def __post_init__(self) -> None:
        """Require explicit nonblank project/worker identities without coercion.

        Args:
            None.

        Returns:
            None; no membership lookup or mutation occurs.

        Raises:
            ValueError: Either identity is missing or not a nonblank string.
        """
        _require_identity(self.project_id, self.worker_id)


@dataclass(frozen=True, slots=True)
class TransferRequest:
    """Transfer selected saved tools; move removes only those assessments.

    Attributes:
        source_assignment_id: Exact assignment, or None for standalone ownership.
        destination: Exact workplace/shift owner or standalone project/worker owner.
        kinds: Ordered selected model identities; the transfer planner requires a
            nonempty unique selection.
        move: False copies; True additionally removes only the transferred source
            assessments.
        source_worker_id: Required for a standalone source (assignment None); optional
            identity consistency check for an assigned source.
        replace_existing: Explicit consent to replace selected existing target tools;
            False retains conflict rejection for noninteractive callers.
    """

    source_assignment_id: int | None
    destination: WorkerContext | StandaloneDestination
    kinds: tuple[AssessmentKind, ...]
    move: bool = False
    source_worker_id: str | None = None
    replace_existing: bool = False

    def __post_init__(self) -> None:
        """Snapshot tool selections and reject implicit identity/mode coercion.

        Args:
            None. Dataclass construction supplies the fields documented on
            TransferRequest.

        Returns:
            None. Construction validates this record before publishing it. Snapshot
            kinds as immutable tuples on the new frozen instance.

        Raises:
            ValueError: Transfer requires typed source, owner and mode, including an
                explicit nonblank worker identity for standalone sources.
        """
        object.__setattr__(self, "kinds", tuple(self.kinds))
        if (
            (
                self.source_assignment_id is not None
                and type(self.source_assignment_id) is not int
            )
            or not isinstance(self.destination, (WorkerContext, StandaloneDestination))
            or type(self.move) is not bool
            or type(self.replace_existing) is not bool
        ):
            raise ValueError("Transfer requires typed source, owner and mode.")
        if self.source_assignment_id is None or self.source_worker_id is not None:
            _require_identity(self.source_worker_id or "")


@dataclass(frozen=True, slots=True)
class TransferPlan:
    """Expected catalogs, exact source/copy pairs and explicitly removed assessments.

    Attributes:
        jobs: Immutable project job, placement and assignment snapshot.
        copies: Ordered pairs of original source records and newly identified
            destination records.
        removed_documents: Exact source document IDs to remove for a move; empty for a
            copy.
        replaced_documents: Exact existing destination sources whose replacement
            was explicitly approved; unrelated tools and historical owners remain.
    """

    jobs: JobCatalog
    copies: tuple[tuple[AssignmentAssessment, AssignmentAssessment], ...]
    removed_documents: tuple[str, ...]
    replaced_documents: tuple[str, ...] = ()


def plan_transfer(
    work: WorkCatalog,
    jobs: JobCatalog,
    history: AssessmentHistory,
    request: TransferRequest,
    document_ids: Mapping[AssessmentKind, str],
) -> TransferPlan:
    """Validate all selected tools and destinations before any save or write.

    Selected existing target tools require explicit replacement consent. Only an active
    workplace assignment supplies the target; closed owners remain historical.
    Standalone destinations never create workplace records. Missing assignments are
    created unclassified. Self-transfer always fails, regardless of replacement consent.

    Args:
        work: Project worker/station/shift snapshot used to validate destination
            membership.
        jobs: Immutable job, placement and assignment catalog for the same project.
        history: Saved assigned and standalone assessments; one per owner/tool.
        request: Exact assigned/standalone source, destination owner, selected tools and
            copy/move intent.
        document_ids: Caller-allocated new document identity for every selected model;
            no IDs are generated here.

    Returns:
        Validated destination catalog, exact source/copy pairs and explicit move
        removals and approved destination replacements; no persistence occurs.

    Raises:
        ValueError: A typed transfer request is required. Select at least one tool and
            an explicit copy/move mode. Transfer tools must be unique typed identities.
            Transfer catalogs belong to different projects. Destination belongs to
            another project. Source assignment does not exist. Source and destination
            contexts are identical. Destination already contains selected assessment
            data. Selected source has no saved assessment. New assessment identity
            must be unique and nonblank. A source worker must exist and match its
            assignment when one is provided.
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
    destination = request.destination
    if destination.project_id != work.project_id:
        raise ValueError("Destination belongs to another project.")
    standalone = isinstance(destination, StandaloneDestination)
    if standalone:
        if not any(w.worker_id == destination.worker_id for w in work.workers):
            raise KeyError(destination.worker_id)
        owner = None
    else:
        assert isinstance(destination, WorkerContext)
        owner = work.worker_context(destination.worker_id, destination.workplace)
    source = next(
        (
            a
            for a in jobs.assignments
            if a.assignment_id == request.source_assignment_id
        ),
        None,
    )
    if request.source_assignment_id is not None:
        if source is None:
            raise ValueError("Source assignment does not exist.")
        if (
            request.source_worker_id is not None
            and request.source_worker_id != source.worker.worker_id
        ):
            raise ValueError("Source worker does not match the selected assignment.")
        if owner is not None and source.worker == owner:
            raise ValueError("Source and destination contexts are identical.")
    else:
        if not any(w.worker_id == request.source_worker_id for w in work.workers):
            raise ValueError("Standalone source worker does not exist.")
        if standalone and request.source_worker_id == destination.worker_id:
            raise ValueError("Source and destination contexts are identical.")
    target = next(
        (
            a
            for a in jobs.assignments
            if owner is not None and a.worker == owner and a.active
        ),
        None,
    )
    conflicts = tuple(
        e.document_id
        for e in history.entries
        if e.kind in request.kinds
        and (
            (
                standalone
                and e.assignment_id is None
                and e.worker_id == destination.worker_id
            )
            or (target is not None and e.assignment_id == target.assignment_id)
        )
    )
    if conflicts and not request.replace_existing:
        raise ValueError("Destination already contains selected assessment data.")
    if owner is not None and target is None:
        target = WorkerJobAssignment(
            max((item.assignment_id for item in jobs.assignments), default=0) + 1,
            owner,
            None,
        )
        jobs = replace(jobs, assignments=(*jobs.assignments, target))
    copies = []
    existing_ids = {item.document_id for item in history.entries}
    for kind in request.kinds:
        current = (
            history.current_for(source.assignment_id, kind)
            if source is not None
            else history.standalone_for(request.source_worker_id or "", kind)
        )
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
                    assignment_id=target.assignment_id if target is not None else None,
                    worker_id=destination.worker_id,
                ),
            )
        )
    return TransferPlan(
        jobs,
        tuple(copies),
        tuple(source.document_id for source, _ in copies) if request.move else (),
        conflicts,
    )

"""Direct worker assessment ownership with optional real workplace associations.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from dataclasses import dataclass

from ergotools.domain.assessments.context import _require_identity
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_catalog import JobCatalog


@dataclass(frozen=True, slots=True)
class AssignmentAssessment:
    """One worker's source document and optional workplace assignment identity.

    Attributes:
        document_id: Exact source-document identity; independent of database row order.
        assignment_id: Exact saved workplace assignment, including closed original
            assignments, or None for a standalone worker/tool assessment.
        worker_id: Required worker identity, independent of optional organization.
        kind: Stable assessment model identity; displayed tool names are localized
            separately.
    """

    document_id: str
    assignment_id: int | None
    kind: AssessmentKind
    worker_id: str

    def __post_init__(self) -> None:
        """Require an explicit document, assignment and tool identity.

        Args:
            None. Dataclass construction supplies the fields documented on
            AssignmentAssessment.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: Assignment identity requires an integer; the tool must use
                an explicit model and the document identity must be nonblank.
        """
        _require_identity(self.document_id)
        _require_identity(self.worker_id)
        if self.assignment_id is not None and type(self.assignment_id) is not int:
            raise ValueError("Assignment identity requires an integer.")
        if not isinstance(self.kind, AssessmentKind):
            raise ValueError("Assessment kind requires an explicit model.")


@dataclass(frozen=True, slots=True)
class AssessmentHistory:
    """Ordered project ownership records retaining inactive assignment histories.

    Each assignment/tool pair owns at most one assessment; each worker/tool also has at
    most one standalone assessment. Worker identity is mandatory in both cases.
    Closed worker assignments
    retain their own assessment; they are different owners, not assessment versions.
    Source existence/model checks and persistence belong to the repository.

    Attributes:
        project_id: Nonblank saved project identity, never derived from a file name.
        entries: Ordered worker-owned assessment records; source existence
            is checked by storage.
    """

    project_id: str
    entries: tuple[AssignmentAssessment, ...] = ()

    def __post_init__(self) -> None:
        """Reject duplicate document identities and assignment/tool owners.

        Args:
            None. Dataclass construction supplies the fields documented on
            AssessmentHistory.

        Returns:
            None. Construction validates this record before publishing it. Snapshot
            entries as immutable tuples on the new frozen instance.

        Raises:
            ValueError: History entries require explicit ownership records. Duplicate
                assessment document or assignment/tool ownership.
        """
        _require_identity(self.project_id)
        object.__setattr__(self, "entries", tuple(self.entries))
        if any(not isinstance(item, AssignmentAssessment) for item in self.entries):
            raise ValueError("History entries require explicit ownership records.")
        documents: set[str] = set()
        owners: set[tuple[str | int, AssessmentKind]] = set()
        for item in self.entries:
            owner = (
                item.assignment_id
                if item.assignment_id is not None
                else item.worker_id,
                item.kind,
            )
            if item.document_id in documents or owner in owners:
                raise ValueError(
                    "Duplicate assessment document or assignment/tool ownership."
                )
            documents.add(item.document_id)
            owners.add(owner)

    def validate_jobs(self, jobs: JobCatalog) -> None:
        """Require exact project and assignment membership, including closed rows.

        Args:
            jobs: Immutable job, placement and assignment catalog for the same project.

        Returns:
            None. Return normally only when the stated validation succeeds; invalid data
            raises instead.

        Raises:
            ValueError: Assessment history belongs to another project. Assessment
                history references a missing assignment.
        """
        if jobs.project_id != self.project_id:
            raise ValueError("Assessment history belongs to another project.")
        assignments = {item.assignment_id: item for item in jobs.assignments}
        for item in self.entries:
            if item.assignment_id is None:
                continue
            assignment = assignments.get(item.assignment_id)
            if assignment is None:
                raise ValueError("Assessment history references a missing assignment.")
            if item.worker_id != assignment.worker.worker_id:
                raise ValueError("Assessment worker differs from its assignment.")

    def current_for(
        self, assignment_id: int, kind: AssessmentKind
    ) -> AssignmentAssessment | None:
        """Resolve exact assignment/model ownership without workplace fallback.

        Closed assignments can retain their own assessments. Selection of an
        active worker assignment is a separate application responsibility.

        Args:
            assignment_id: Exact saved assignment identity; closed assignments remain
                addressable.
            kind: Stable assessment model identity, independent of translated tool
                names.

        Returns:
            The unique assignment/model record, or None when none is saved.

        Raises:
            ValueError: Lookup requires explicit assignment and model identities.
        """
        if type(assignment_id) is not int or not isinstance(kind, AssessmentKind):
            raise ValueError(
                "Lookup requires explicit assignment and model identities."
            )
        return next(
            (
                item
                for item in self.entries
                if item.assignment_id == assignment_id and item.kind == kind
            ),
            None,
        )

    def standalone_for(
        self, worker_id: str, kind: AssessmentKind
    ) -> AssignmentAssessment | None:
        """Find the unique worker/tool assessment with no organizational association.

        Args:
            worker_id: Exact worker identity in this project's catalog.
            kind: Requested ergonomic tool; no display-label interpretation occurs.

        Returns:
            Saved standalone ownership, or None. This lookup never writes or associates.

        Raises:
            ValueError: Worker or model identity is invalid.
        """
        _require_identity(worker_id)
        if not isinstance(kind, AssessmentKind):
            raise ValueError("Assessment kind requires an explicit model.")
        return next(
            (
                e
                for e in self.entries
                if e.worker_id == worker_id
                and e.kind is kind
                and e.assignment_id is None
            ),
            None,
        )

"""Explicit historical selection identities and optional project history access.

Application layer. Define immutable capability/operation contracts independently of Qt
and storage implementations. Callers own modal consent and borrowed project lifetime;
concrete adapters own I/O and transaction enforcement.
"""

from dataclasses import dataclass
from datetime import date
from typing import Protocol, runtime_checkable

from ergotools.domain.assessment_history import AssessmentHistory, AssignmentAssessment
from ergotools.domain.assessments.context import WorkplaceContext, _require_identity
from ergotools.domain.assessments.document import AssessmentKind


@dataclass(frozen=True, slots=True)
class AssignmentSelection:
    """Exact project/assignment/model; closed assignments remain addressable.

    Attributes:
        project_id: Exact project identity, independent of path or title.
        assignment_id: Exact integer historical assignment identity; a closed assignment
            remains selectable.
        kind: Stable tool identity for this assignment's assessment history.
        worker_id: Required for standalone selections; optional for exact assigned IDs.
    """

    project_id: str
    assignment_id: int | None
    kind: AssessmentKind
    worker_id: str | None = None

    def __post_init__(self) -> None:
        """Reject ambiguous IDs and model names before repository access.

        Args:
            None.

        Returns:
            None after validating explicit project, integer assignment and model
            identity; no lookup or reassignment occurs.

        Raises:
            ValueError: Project identity is blank or assignment/model identity has an
                unsupported type.
        """
        _require_identity(self.project_id)
        if (
            self.assignment_id is not None and type(self.assignment_id) is not int
        ) or not isinstance(self.kind, AssessmentKind):
            raise ValueError("Selection requires explicit assignment/model identities.")
        if self.assignment_id is None:
            _require_identity(self.worker_id or "")
        if self.worker_id is not None:
            _require_identity(self.worker_id)


@runtime_checkable
class HistoryRepository(Protocol):
    """Optional validated historical ownership capability."""

    @property
    def supports_assignment_history(self) -> bool:
        """Report format support without repository I/O.

        Args:
            None.

        Returns:
            True when the native format supports assignment-owned history; do not
            perform repository I/O.
        """
        ...

    def load_history(self) -> AssessmentHistory:
        """Return saved ownership with source-model and assignment checks.

        Args:
            None.

        Returns:
            Validated saved history with exact source-model and historical assignment
            membership.
        """
        ...


@dataclass(frozen=True, slots=True)
class HistorySnapshot:
    """Workspace-issued history view; identity guards assessment ownership operations.

    Attributes:
        history: Immutable workspace-issued saved ownership view used to scope
            assessment ownership operations.
    """

    history: AssessmentHistory


@runtime_checkable
class DeletableHistoryRepository(HistoryRepository, Protocol):
    """Atomic removal of one saved assessment and its ownership record."""

    def delete_historical_assessment(
        self, expected: AssessmentHistory, document_id: str
    ) -> AssessmentHistory:
        """Delete only this document; preserve unrelated assignment/tool assessments.

        Args:
            expected: Exact previously read saved catalog used as the atomic
                replacement/transition precondition.
            document_id: Exact saved source version identity to select/delete; never a
                visible assessment label.

        Returns:
            Committed history after deleting only the selected saved source/ownership;
            never create or select unrelated assessment data.
        """
        ...


@runtime_checkable
class AssociableAssessmentRepository(Protocol):
    """Optional transactional association capability; source/results stay untouched."""

    def associate_assessment(
        self, document_id: str, assignment_id: int
    ) -> AssessmentHistory:
        """Bind a standalone assessment to its worker's active workplace.

        Args:
            document_id: Exact saved standalone assessment identity.
            assignment_id: Same-worker active workplace assignment; Job is optional.

        Returns:
            Validated ownership after one atomic relationship update.
        """
        ...


@runtime_checkable
class WorkplaceAssociationRepository(AssociableAssessmentRepository, Protocol):
    """Atomic optional workplace creation and association of a standalone assessment."""

    def associate_assessment_at_workplace(
        self,
        document_id: str,
        workplace: WorkplaceContext,
        placement_id: int | None,
        *,
        effective_date: date,
    ) -> AssignmentAssessment:
        """Reuse/create the worker assignment and bind the source in one transaction.

        Args:
            document_id: Exact standalone source; its worker is authoritative.
            workplace: Explicit real station/shift, never a fabricated default.
            placement_id: Optional active Job at the destination; an existing assignment
                must keep its already selected Job.
            effective_date: Explicit date for a newly created workplace assignment.

        Returns:
            Associated ownership retaining source/result bytes and document identity.
            Failure leaves both assignment catalog and assessment ownership unchanged.
        """
        ...


@runtime_checkable
class WorkplaceAssessmentRepository[State](Protocol):
    """Atomically create/reuse a workplace owner and create/replace its tool source."""

    def add_workplace_assessment(
        self,
        worker_id: str,
        workplace: WorkplaceContext,
        placement_id: int | None,
        document_id: str,
        initial: State,
        *,
        effective_date: date,
        expected_document_id: str | None = None,
    ) -> AssignmentAssessment:
        """Create blank input at a station, guarding replacement with exact identity.

        Args:
            worker_id: Existing worker; standalone sources are never consumed.
            workplace: Real saved station and project shift.
            placement_id: Optional compatible Job; existing ownership stays unchanged.
            document_id: Fresh source identity used only for creation.
            initial: Blank typed source for the selected tool, with its units/task IDs.
            effective_date: Start date only if a workplace assignment is needed.
            expected_document_id: Confirmed existing source to replace; None forbids
                overwriting any existing source.

        Returns:
            Exact created/replaced owner. Assignment/source/result updates are atomic;
            replacement retains source identity and removes its calculated result.
        """
        ...

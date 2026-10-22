"""Widget-independent selection and creation from saved classified assignments.

Presentation layer. Interpret explicit user selections and project immutable values for
controls or interchange, independently of widget construction. Persistence and source
history use injected application services. Do not infer identity from captions, units
from interface language, or missing scientific quantities from zero. Storage errors
propagate to the host for localized reporting; user data remains literal.
"""

from dataclasses import dataclass, field

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.history_access import AssignmentSelection
from ergotools.application.job_access import JobSnapshot
from ergotools.application.project_workspace import ProjectWorkspace, TransitionOutcome
from ergotools.application.session import DocumentSession
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    assessment_kind,
)
from ergotools.presentation.assignment_options import (
    ClassifiedAssignment,
    classified_assignments,
)


@dataclass(frozen=True, slots=True)
class AssignmentCatalog:
    """Presenter-issued saved catalog with exact object authority.

    Attributes:
        snapshot: Latest workspace-issued jobs/placements/assignments snapshot.
    """

    snapshot: JobSnapshot


@dataclass(frozen=True, slots=True)
class AssignmentRequest:
    """One explicit complete choice bound to the current catalog and active source.

    Attributes:
        catalog: Exact presenter-issued catalog used for preparation.
        target: Exact assignment/model identity.
        session: Captured active session identity, or None with no source open; not
            owned by this choice.
        revision: Captured session revision, or None with no active source.
    """

    catalog: AssignmentCatalog
    target: AssignmentSelection
    session: DocumentSession[AssessmentDraft] | None = field(repr=False)
    revision: int | None


class AssignmentSelector:
    """Translate explicit assignment choices into safe workspace actions.

    This presenter uses active assignment/placement eligibility. Historical browsing
    can use workspace selection directly. The host must resolve pending widget text
    before preparing a request; no Qt controls or label parsing are involved.
    """

    def __init__(self, workspace: ProjectWorkspace[AssessmentDraft]) -> None:
        """Bind dependencies without reading or selecting project data.

        Args:
            workspace: Borrowed single-user workspace owning the project connection,
                active session and catalog authority.

        Returns:
            None; retain the workspace without reading, selecting or saving.
        """
        self._workspace = workspace
        self._catalog: AssignmentCatalog | None = None
        self._request: AssignmentRequest | None = None

    def refresh(self) -> AssignmentCatalog:
        """Invalidate old callbacks before I/O, including on failed refresh.

        Args:
            None.

        Returns:
            Fresh presenter-issued catalog; previous catalogs and prepared requests
            become invalid before I/O.

        Raises:
            RuntimeError: Required workspace catalog capability is absent or a
                transition is active.
            ValueError: Saved catalog ownership/order validation fails.
        """
        self._catalog = None
        self._request = None
        catalog = AssignmentCatalog(self._workspace.read_jobs())
        self._catalog = catalog
        return catalog

    def _check_catalog(self, catalog: AssignmentCatalog) -> None:
        """Read identity only; no project I/O or lifetime extension.

        Args:
            catalog: Exact presenter-issued catalog, still backed by the latest
                workspace snapshot.

        Returns:
            None when presenter and workspace authority both remain current.

        Raises:
            ValueError: Catalog belongs to another presenter, was refreshed or outlived
                its project handle.
        """
        if catalog is not self._catalog or not self._workspace.jobs_are_current(
            catalog.snapshot
        ):
            raise ValueError("Assignment catalog is stale or belongs to another owner.")

    def options(
        self, catalog: AssignmentCatalog, worker_id: str
    ) -> tuple[ClassifiedAssignment, ...]:
        """Return exact eligible saved assignments with display metadata.

        Args:
            catalog: Exact current presenter-issued job catalog.
            worker_id: Explicit worker identity whose eligible classified contexts are
                requested.

        Returns:
            Original-ordered active assignment/placement choices retaining literal job
            labels.

        Raises:
            ValueError: Catalog authority is stale/foreign.
        """
        self._check_catalog(catalog)
        return classified_assignments(catalog.snapshot.jobs, worker_id)

    def prepare(
        self,
        catalog: AssignmentCatalog,
        worker_id: str,
        assignment_id: int,
        kind: AssessmentKind,
    ) -> AssignmentRequest:
        """Require an explicit eligible identity; never pick a workplace fallback.

        Args:
            catalog: Exact current presenter-issued catalog.
            worker_id: Explicit stable worker identity; no default/fallback selection.
            assignment_id: Exact eligible active assignment identity for this worker.
            kind: Explicit supported assessment model.

        Returns:
            Fresh exact selection/request capturing current session identity and
            revision.

        Raises:
            ValueError: Catalog authority or typed selection identity is invalid.
            KeyError: Explicit worker/workplace or eligible assignment is absent.
        """
        self._request = None
        self._check_catalog(catalog)
        target = AssignmentSelection(
            catalog.snapshot.jobs.project_id, assignment_id, kind
        )
        if not any(
            option.assignment.assignment_id == assignment_id
            for option in self.options(catalog, worker_id)
        ):
            raise KeyError(assignment_id)
        active = self._workspace.active
        request = AssignmentRequest(
            catalog, target, active, active.revision if active is not None else None
        )
        self._request = request
        return request

    def _check_request(self, request: AssignmentRequest) -> None:
        """No I/O and no implicit retry or fallback selection.

        Args:
            request: Exact prepared choice issued by this presenter.

        Returns:
            None when catalog, current session identity and revision still match.

        Raises:
            ValueError: Choice is obsolete/foreign or source/catalog ownership changed
                since preparation.
        """
        if request is not self._request:
            raise ValueError(
                "Assignment request is obsolete or belongs to another owner."
            )
        self._check_catalog(request.catalog)
        active = self._workspace.active
        if request.session is not active or (
            active is not None and request.revision != active.revision
        ):
            raise ValueError("Active assessment changed after preparing the request.")

    def select(
        self, request: AssignmentRequest, *, choice: CloseChoice | None = None
    ) -> TransitionOutcome:
        """Open the unique saved assessment; cancellation permits deliberate retry.

        Args:
            request: Exact current prepared choice to activate.
            choice: Save/Discard/Cancel disposition for dirty source; None requires a
                clean session.

        Returns:
            Workspace transition outcome; successful activation consumes the request,
            while cancellation/failure permits deliberate retry.

        Raises:
            ValueError: Choice/catalog/source ownership is stale or invalid.
            KeyError: No saved assessment exists for that exact selection.
            RuntimeError: Required workspace capability is absent or a
                transition/session guard fails.
        """
        self._check_request(request)
        outcome = self._workspace.select_assignment(request.target, choice=choice)
        if outcome.completed:
            self._request = None
        return outcome

    def create(
        self,
        request: AssignmentRequest,
        document_id: str,
        initial: AssessmentDraft,
        *,
        choice: CloseChoice | None = None,
    ) -> TransitionOutcome:
        """Create the unique assessment for an assignment/tool; reject an existing one.

        Args:
            request: Exact current prepared choice whose model/ownership must match the
                source.
            document_id: Fresh stable source identity to insert exclusively.
            initial: Typed initial source for the chosen model; validate before any
                old-draft Save.
            choice: Save/Discard/Cancel disposition for dirty current source.

        Returns:
            Workspace transition outcome; success consumes the choice and activates a
            clean new source session.

        Raises:
            ValueError: Choice/source model, identity or existing
                saved ownership conflicts.
            RuntimeError: Required creation capability is absent or a workspace/session
                transition guard fails.
        """
        self._check_request(request)
        if assessment_kind(initial) != request.target.kind:
            raise ValueError("Initial source does not match the selected model.")
        entry = AssignmentAssessment(
            document_id,
            request.target.assignment_id,
            request.target.kind,
            next(
                a.worker.worker_id
                for a in request.catalog.snapshot.jobs.assignments
                if a.assignment_id == request.target.assignment_id
            ),
        )
        outcome = self._workspace.create_assignment_assessment(
            entry, initial, choice=choice
        )
        if outcome.completed:
            self._request = None
        return outcome

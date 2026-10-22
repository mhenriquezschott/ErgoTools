"""Single-active-project ownership and failure-safe typed document switching.

Application layer. Own repository and active-session lifetimes and coordinate immutable
catalog edits, source-bound saves, snapshots and dirty-state consent. All storage and
settings operations use injected ports; Qt controls, solvers and SQL are excluded. This
is a synchronous single-user coordinator, not a multiuser refresh service. Callback
authority prevents obsolete form actions within that ownership lifetime.
Repository/provider exceptions propagate unless explicitly converted to post-transition
warning keys; failed detached closes retain ownership for retry.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Protocol, runtime_checkable

from ergotools.application.assessment_binding import (
    AssessmentBinding,
    AssessmentBindings,
)
from ergotools.application.assessment_catalog import AssessmentEntry
from ergotools.application.document_lifecycle import CloseChoice, DocumentRepository
from ergotools.application.hierarchy_access import (
    HierarchyRepository,
    HierarchySnapshot,
    WorkerRepository,
)
from ergotools.application.historical_results import (
    HistoricalAssessmentResult,
)
from ergotools.application.history_access import (
    AssignmentSelection,
    AssociableAssessmentRepository,
    DeletableHistoryRepository,
    HistoryRepository,
    HistorySnapshot,
    WorkplaceAssociationRepository,
)
from ergotools.application.job_access import JobRepository, JobSnapshot
from ergotools.application.job_calculation import job_measurement_from_result
from ergotools.application.job_risk_access import JobRiskRepository, JobRiskSnapshot
from ergotools.application.open_document import remember_open_location
from ergotools.application.organization_management import plant_shift_count
from ergotools.application.plot_access import PlotRepository
from ergotools.application.project_editing import (
    EditingRepository,
    ProjectEditingSession,
)
from ergotools.application.project_preferences import ProjectPreferencesRepository
from ergotools.application.rotation_access import RotationRepository
from ergotools.application.saved_results import (
    ResultSave,
    SavedResultRepository,
    stored_result,
)
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.application.settings import SettingsStore
from ergotools.application.transfer_access import TransferRepository
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessment_transfer import TransferRequest, plan_transfer
from ergotools.domain.assessments.context import AssessmentContext, WorkplaceContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.job_catalog import Job, JobCatalog
from ergotools.domain.job_management import delete_job, save_job_details
from ergotools.domain.job_risk import JobRiskMeasurement, JobRiskValues
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.work_hierarchy import WorkHierarchy


class OwnedProject[State](DocumentRepository[State], Protocol):
    """Project repository whose ownership transfers from factory to workspace."""

    @property
    def metadata(self) -> ProjectMetadata:
        """Return validated immutable metadata for this connection.

        Args:
            None.

        Returns:
            Validated immutable project metadata for this owned connection.
        """
        ...

    def close(self) -> None:
        """Release resources idempotently; allow retry after a failed close.

        Args:
            None.

        Returns:
            None after idempotent release; a failed release must allow a later retry.

        Raises:
            ValueError: Dirty disposition is untyped or a requested source/result save
                fails validation.
            RuntimeError: Another transition is active or a requested session save
                violates its thread guard.
        """
        ...


@runtime_checkable
class SnapshotProject[State](OwnedProject[State], Protocol):
    """Optional complete-project snapshot capability, published to a new location."""

    def snapshot(
        self, location: str, document: DocumentKey | None, state: State | None
    ) -> OwnedProject[State]:
        """Copy saved data, optionally replace one source, and return an owned copy.

        Never write the original or replace an existing destination. Failure must leave
        the original usable; a completely published copy may be retained if acquiring
        its new handle subsequently fails.

        Args:
            location: Caller-normalized native destination; publication operations
                require a nonblank different location and never overwrite.
            document: Exact project/document identity to save in the copy; None together
                with state copies saved data only.
            state: Immutable draft matching document, or None for a saved-data-only
                snapshot.

        Returns:
            New exclusively owned validated copy handle. On post-publication acquisition
            failure, a complete destination may remain.
        """
        ...


@runtime_checkable
class DurableSnapshotProject[State](SnapshotProject[State], Protocol):
    """Copy the last explicitly saved data while private editing remains open."""

    def snapshot_saved(self, location: str) -> OwnedProject[State]:
        """Publish a complete last-Save backup without accepting pending edits.

        Args:
            location: New exclusive backup destination.

        Returns:
            Owned validated backup handle; active private data/history stay unchanged.
        """
        ...


@runtime_checkable
class MetadataSnapshotProject[State](SnapshotProject[State], Protocol):
    """Optional copy-only metadata editing for the original Save As workflow."""

    def snapshot_with_metadata(
        self,
        location: str,
        document: DocumentKey | None,
        state: State | None,
        metadata: ProjectMetadata,
    ) -> OwnedProject[State]:
        """Publish a validated copy with the same identity and new display details.

        Args:
            location: Caller-normalized native destination; publication operations
                require a nonblank different location and never overwrite.
            document: Exact project/document identity to save in the copy; None together
                with state copies saved data only.
            state: Immutable draft matching document, or None for a saved-data-only
                snapshot.
            metadata: Validated project display metadata; snapshot editing must retain
                the stable project identity.

        Returns:
            New exclusively owned validated copy handle with requested display details
            and unchanged project identity.
        """
        ...


@runtime_checkable
class PreparedSnapshotProject[State](SnapshotProject[State], Protocol):
    """Prepare all retained edits in a private copy before exclusive publication."""

    def snapshot_prepared(
        self,
        location: str,
        prepare: Callable[[OwnedProject[State]], None],
        metadata: ProjectMetadata | None = None,
    ) -> OwnedProject[State]:
        """Publish only after the caller has written every requested copy-only edit.

        Args:
            location: Nonexistent destination; existing files must never be replaced.
            prepare: Synchronous application operation receiving a private repository.
                Failure must remove staging data without publishing the destination.
            metadata: Optional same-identity metadata to apply to the private copy.

        Returns:
            Owned complete published repository. A final reopen failure may retain a
            complete destination; preparation failures must leave none.
        """
        ...


@runtime_checkable
class CatalogProject[State](OwnedProject[State], Protocol):
    """Optional owned-project capability for listing and exclusive document creation."""

    def list_assessments(self) -> tuple[AssessmentEntry, ...]:
        """Return validated persisted catalog entries in stable order.

        Args:
            None.

        Returns:
            Validated persisted source catalog in stable order.

        Raises:
            RuntimeError: An open project lacks source-catalog access or another
                transition is active.
        """
        ...

    def insert_assessment(self, document: DocumentKey, initial: State) -> None:
        """Persist exactly this new source or raise without replacing existing IDs.

        Args:
            document: Exact project/document identity to save in the copy; None together
                with state copies saved data only.
            initial: Validated initial immutable source to create and persist exactly,
                without replacing existing document IDs.

        Returns:
            None after exclusive source insertion; failure must not replace existing
            IDs.
        """
        ...


@runtime_checkable
class BoundAssessmentProject[State](CatalogProject[State], Protocol):
    """Optional atomic source-plus-ownership creation capability."""

    def find_assessment(self, context: AssessmentContext) -> DocumentKey | None:
        """Resolve saved ownership for preflight; writes must recheck uniqueness.

        Args:
            context: Exact worker/workplace/model ownership, independent of display
                labels.

        Returns:
            Exact saved source key for this ownership, or None; final creation must
            repeat uniqueness checks.
        """
        ...

    def create_bound_assessment(
        self, binding: AssessmentBinding, initial: State
    ) -> None:
        """Commit both records together or leave neither newly created record.

        Args:
            binding: Exact source identity and matching project/worker/workplace/model
                ownership to create atomically.
            initial: Validated initial immutable source to create and persist exactly,
                without replacing existing document IDs.

        Returns:
            None after source and ownership commit together; failure creates neither
            record.
        """
        ...


@runtime_checkable
class HistoricalProject[State](CatalogProject[State], HistoryRepository, Protocol):
    """Optional preflight and atomic historical source-creation capability."""

    def validate_historical_creation(
        self, entry: AssignmentAssessment, initial: State
    ) -> None:
        """Validate without mutation; final creation must repeat all constraints.

        Args:
            entry: Explicit assignment/tool ownership record for the new
                historically owned source.
            initial: Validated initial immutable source to create and persist exactly,
                without replacing existing document IDs.

        Returns:
            None after read-only preflight; final creation must repeat constraints under
            its write lock.
        """
        ...

    def create_historical_assessment(
        self,
        entry: AssignmentAssessment,
        initial: State,
        *,
        result: HistoricalAssessmentResult | None = None,
    ) -> None:
        """Commit source, historical ownership and optional calculation together.

        Args:
            entry: Explicit assignment/tool ownership record for the new
                historically owned source.
            initial: Validated initial immutable source to create and persist exactly,
                without replacing existing document IDs.
            result: Optional sole calculation matching the initial inputs.

        Returns:
            None after source and exact historical ownership commit atomically.
        """
        ...


@dataclass(frozen=True, slots=True)
class TransitionOutcome:
    """Transition result separating completion from nonfatal post-commit warnings.

    Attributes:
        completed: True after activation/close/copy succeeds; False for dirty-consent
            cancellation.
        warning_keys: Stable localized keys for cleanup or recency failures after
            successful transition.
    """

    completed: bool
    warning_keys: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ReleaseDiagnostic:
    """Detached-handle cleanup failure without raw exception contents or project data.

    Attributes:
        exception_type: Qualified exception class name for diagnostics.
        errno: OS error number when the error is an OSError; otherwise None.
        operation: Stable diagnostic operation identity, currently project.close.
    """

    exception_type: str
    errno: int | None
    operation: str = "project.close"


@dataclass(frozen=True, slots=True)
class _InitialAssessmentSave[State]:
    """Bind first Save to one atomic source/result/owner transaction.

    Attributes:
        project: Borrowed repository implementing historical creation.
        entry: Exact first-Save assignment/tool ownership.
        result: Optional sole result bound to the initial source.
    """

    project: HistoricalProject[State]
    entry: AssignmentAssessment
    result: HistoricalAssessmentResult | None

    def save(self, document: DocumentKey, state: State) -> None:
        """Create exactly this source/result/owner; the session marks clean on success.

        Args:
            document: Session identity, required to match the proposed creation entry.
            state: Edited source to create; no placeholder row is inserted earlier.

        Returns:
            None after the repository commits all first-Save data atomically.

        Raises:
            ValueError: Document identity does not match the proposed creation.
        """
        if document.document_id != self.entry.document_id:
            raise ValueError("Creation entry does not match source identity.")
        self.project.create_historical_assessment(self.entry, state, result=self.result)


class ProjectWorkspace[State]:
    """Own one project and active document plus handles awaiting cleanup retry.

    Locations must be normalized by the platform caller. Factories must return
    fresh exclusively owned handles, never the current handle. This coordinator
    is synchronous and single-threaded; snapshot I/O belongs to the repository.
    """

    def __init__(
        self,
        opener: Callable[[str], OwnedProject[State]],
        settings: SettingsStore,
        *,
        result_provider: Callable[[], HistoricalAssessmentResult | None] | None = None,
        creator: Callable[[str, ProjectMetadata, str, State], OwnedProject[State]]
        | None = None,
        unified_saving: bool = False,
        empty_creator: Callable[[str, ProjectMetadata], OwnedProject[State]]
        | None = None,
    ) -> None:
        """Configure adapters without opening files or loading preferences.

        Args:
            opener: Factory returning a fresh exclusively owned project handle for a
                caller-normalized native location.
            settings: Borrowed per-user preferences for recency, context choices and
                the integrated shared history budget.
            result_provider: Optional owner-thread callback returning the active
                source-bound calculation; None allows source-only saves.
            creator: Optional exclusive new-project factory; must reject existing
                destinations and clean incomplete initialization.
            unified_saving: Use private project editing and one durable Save boundary.
                False retains low-level diagnostic adapter contracts.
            empty_creator: Exclusive current-project factory without placeholder
                assessments or artificial worker/organization records.

        Returns:
            None; configure adapters and empty ownership/history without opening files
            or reading preferences.
        """
        self._confirmed_assessments: set[str] = set()
        self._unified_saving = unified_saving
        self._editing: ProjectEditingSession | None = None
        self._editing_owner: OwnedProject[State] | None = None
        self._result_provider = result_provider
        self._creator = creator
        self._empty_creator = empty_creator
        self._opener = opener
        self._settings = settings
        self._project: OwnedProject[State] | None = None
        self._active: DocumentSession[State] | None = None
        self._browse_sessions: dict[str, DocumentSession[State]] = {}
        self._browse_pending: dict[str, AssignmentAssessment] = {}
        self._browse_readonly: set[str] = set()
        self._location: str | None = None
        self._pending: list[tuple[OwnedProject[State], ReleaseDiagnostic]] = []
        self._busy = False
        self._risk_snapshot: tuple[OwnedProject[State], JobRiskSnapshot] | None = None
        self._job_snapshot: tuple[OwnedProject[State], JobSnapshot] | None = None
        self._history_snapshot: tuple[OwnedProject[State], HistorySnapshot] | None = (
            None
        )
        self._hierarchy_snapshot: (
            tuple[OwnedProject[State], HierarchySnapshot] | None
        ) = None

    @property
    def editing(self) -> ProjectEditingSession | None:
        """Return the shared editing owner, creating it on project activation.

        Args:
            None.

        Returns:
            Project-session owner for integrated editing, or None for diagnostics
            and when no project is open. Beginning a session never writes its file.

        Raises:
            RuntimeError: Integrated editing lacks the required repository capability.
            OSError: The personal settings needed for the history budget cannot be read.
            ValueError: Personal settings are malformed or contain an invalid budget.
        """
        if not self._unified_saving or self._project is None:
            return None
        if self._editing_owner is not self._project:
            if not isinstance(self._project, EditingRepository):
                raise RuntimeError("Project does not support private editing.")
            self._confirmed_assessments.clear()
            # Claim initialization before allocating checkpoints: finalizers can
            # notify live UI observers while Python collects unrelated windows.
            # Such readers see no owner until construction finishes, never start
            # a second private session on the same repository.
            self._editing_owner = self._project
            self._editing = None
            try:
                self._editing = ProjectEditingSession(
                    self._project.metadata.project_id,
                    self._project,
                    undo_limit=self._settings.load().undo_limit,
                )
            except Exception:
                self._editing_owner = None
                raise
            self._editing.subscribe(self._restore_project_edit)
            if self._active is not None:
                self._editing.seed_editor(
                    "assessment.source:" + self._active.document.document_id,
                    self._active.state,
                )
        return self._editing

    def _restore_project_edit(self) -> None:
        """Invalidate cached authorities and reload sources only during replay.

        Args:
            None.

        Returns:
            None; record notifications alone never reenter an active mutation.
        """
        editing = self._editing
        if editing is None or not editing.replaying or self._project is None:
            return
        self._hierarchy_snapshot = None
        self._job_snapshot = None
        self._history_snapshot = None
        self._risk_snapshot = None
        previous_active = self._active
        retained = dict(self._browse_sessions)
        if previous_active is not None:
            retained[previous_active.document.document_id] = previous_active
        active_key = previous_active.document if previous_active is not None else None
        self._browse_sessions.clear()
        self._browse_pending.clear()
        self._browse_readonly.clear()
        self._active = None
        for identity, session in retained.items():
            try:
                source = self._project.load(session.document)
            except KeyError:
                continue
            retained_source = editing.editor("assessment.source:" + identity)
            if retained_source == source:
                source = retained_source
            session.replace_from_owner(source)
            self._browse_sessions[identity] = session
            if session.document == active_key:
                self._active = session

    def stage_assessments(self, *, label: str = "assessment.edit") -> None:
        """Accept dirty source drafts into private project state without file writes.

        Args:
            label: Shared operation identity, normally assessment.edit; explicit
                clearing uses assessment.clear without adding a separate history.
                Must be nonblank.

        Returns:
            None; the source/result ports retain their validation and ownership rules.
            A completed action adds one project history step, independent of tab count.

        Raises:
            ValueError: The operation label is blank; no source is staged.
        """
        if not label.strip():
            raise ValueError("Assessment history label must not be blank.")
        editing = self.editing
        if editing is None or editing.replaying:
            return
        if self._active is not None:
            key = "assessment.source:" + self._active.document.document_id
            if editing.editor(key) is None:
                editing.seed_editor(key, self._active.state)
        if not any(s.is_dirty for s in self._browse_sessions.values()) and not (
            self._active is not None and self._active.is_dirty
        ):
            return
        sessions = dict(self._browse_sessions)
        if self._active is not None:
            sessions[self._active.document.document_id] = self._active
        dirty = tuple(session for session in sessions.values() if session.is_dirty)
        pending = dict(self._browse_pending)
        try:
            with editing.stage():
                self._save_browse()
                for identity, session in sessions.items():
                    editing.set_editor(
                        "assessment.source:" + identity,
                        session.state,
                        "assessment.edit",
                    )
        except Exception:
            self._browse_pending = pending
            self._history_snapshot = None
            for session in dirty:
                session.mark_unsaved()
            raise
        editing.record(label)

    def stage_calculation(self, result: HistoricalAssessmentResult | None) -> None:
        """Accept a fresh calculated output without publishing the project file.

        Args:
            result: Exact current-source calculation, or None for unavailable results.

        Returns:
            None; unchanged outputs add no action. Accepted derived data makes the
            project dirty, so closing cannot silently omit a newly calculated result.
        """
        editing = self.editing
        if editing is None or result is None or self._active is None:
            return
        self.stage_assessments()
        with editing.stage():
            self._persist_active(result)
        editing.record("assessment.calculate")

    @property
    def has_unsaved_changes(self) -> bool:
        """Report unsaved project data, retained partial drafts or source edits.

        Args:
            None.

        Returns:
            True when private data differs from the last main Save or an entered
            draft/source remains unsaved. View-only changes and untouched previews
            do not require a project Save prompt.
        """
        editing = self.editing
        return (
            (editing is not None and editing.is_dirty)
            or any(s.is_dirty for s in self._browse_sessions.values())
            or (self._active is not None and self._active.is_dirty)
        )

    @property
    def pending_assessments(self) -> tuple[AssignmentAssessment, ...]:
        """Expose first-file-Save ownership needing same-Job creation consent.

        Args:
            None.

        Returns:
            New accepted private entries and edited previews whose creation consent
            has not yet been accepted. No project file is written by browsing them.
        """
        pending = {
            identity: entry
            for identity, entry in self._browse_pending.items()
            if self._browse_sessions[identity].is_dirty
        }
        editing = self.editing
        if editing is not None and isinstance(self._project, CatalogProject):
            for source in self._project.list_assessments():
                identity = source.document.document_id
                entry = editing.editor("assessment.creation:" + identity)
                if isinstance(entry, AssignmentAssessment):
                    pending[identity] = entry
        return tuple(
            entry
            for identity, entry in pending.items()
            if identity not in self._confirmed_assessments
        )

    def confirm_assessment_creation(self, document_id: str) -> None:
        """Remember accepted creation consent across retries without a database flag.

        Args:
            document_id: Exact new assessment identity approved by the owning UI.

        Returns:
            None; consent is session-local and does not publish or mutate source data.
        """
        self._confirmed_assessments.add(document_id)

    def browse_document(
        self,
        document_id: str,
        *,
        initial: State | None = None,
        entry: AssignmentAssessment | None = None,
        readonly: bool = False,
    ) -> None:
        """Activate a saved source or an in-memory preview without writing data.

        Retain the previous session, including undo history and dirty inputs, so
        switching tools never saves or discards another tool's edits. A classified
        preview is inserted only on explicit Save; unclassified data is read-only.

        Args:
            document_id: Exact saved identity or fresh preview identity.
            initial: Preview source, or None to load an existing document.
            entry: Classified preview ownership to persist on first Save, or None.
            readonly: Prohibit Save for unclassified or context-free previews.

        Returns:
            None after activation; loading/validation failures leave the old view
            intact.

        Raises:
            RuntimeError: No project is open or another transition is active.
            ValueError: Preview ownership or source validation fails.
        """
        self._check()
        project = self._project
        if project is None:
            raise RuntimeError("No project is open.")
        key = DocumentKey(project.metadata.project_id, document_id)
        session = self._browse_sessions.get(document_id)
        if self._active is not None and self._active.document == key:
            session = self._active
        if session is None:
            source = project.load(key) if initial is None else initial
            if entry is not None:
                if not isinstance(project, HistoricalProject):
                    raise RuntimeError("Historical creation adapter is not configured.")
                project.validate_historical_creation(entry, source)
            # A blank preview starts clean. Editing it makes first Save necessary.
            session = DocumentSession(key, source, persisted=True)
        if self._active is not None:
            self._browse_sessions[self._active.document.document_id] = self._active
        self._browse_sessions[document_id] = session
        if entry is not None:
            self._browse_pending[document_id] = entry
        if readonly:
            self._browse_readonly.add(document_id)
        else:
            self._browse_readonly.discard(document_id)
        self._active = session

    def resolve_browse(self, choice: CloseChoice | None) -> bool:
        """Resolve retained sources before leaving a worker or workplace.

        Args:
            choice: Explicit cancellation or diagnostic Save/Discard disposition.
                Integrated navigation retains edits without a file Save decision.

        Returns:
            False on cancellation without accepting drafts. Integrated navigation
            accepts retained sources privately; diagnostics require Save/Discard
            consent when dirty. Acceptance/save failures retain drafts for retry.
        """
        self._check(choice)
        if choice is CloseChoice.CANCEL:
            return False
        if self.editing is not None:
            self.stage_assessments()
            return True
        if not self._permitted(choice):
            return False
        self._save_current(choice)
        self._active = None
        return True

    @property
    def active(self) -> DocumentSession[State] | None:
        """Return the session currently receiving edits and undo/redo actions.

        Args:
            None.

        Returns:
            Current owner-thread edit/history session, or None when no source is open.
        """
        return self._active

    @property
    def supports_assignment_history(self) -> bool:
        """Expose an optional active-project capability without I/O.

        Args:
            None.

        Returns:
            True when the active repository exposes supported saved assignment history;
            no I/O.
        """
        project: object = self._project
        return (
            isinstance(project, HistoryRepository)
            and project.supports_assignment_history
        )

    @property
    def location(self) -> str | None:
        """Return the normalized location associated with the active connection.

        Args:
            None.

        Returns:
            Normalized active connection location, or None when closed.
        """
        return self._location

    @property
    def project_metadata(self) -> ProjectMetadata | None:
        """Return the open project's immutable metadata without reading storage.

        Args:
            None.

        Returns:
            Active immutable metadata, or None when closed; no storage read.
        """
        return self._project.metadata if self._project is not None else None

    def update_display_settings(self, metadata: ProjectMetadata) -> None:
        """Save project display preferences through the owned adapter only.

        Args:
            metadata: Current project metadata with requested units and decimal counts.

        Returns:
            None; source sessions and their undo histories are unchanged.

        Raises:
            ValueError: No native preference-capable project is open.
        """
        self._check()
        project: object = self._project
        if not isinstance(project, ProjectPreferencesRepository):
            raise ValueError("No project display settings capability is available.")
        project.update_display_settings(metadata)

    def assessment_source(self, document_id: str) -> State:
        """Borrow exact retained inputs without changing the active assessment.

        Args:
            document_id: Existing source identity from this project's history.

        Returns:
            Current immutable session source when retained, otherwise persisted inputs.

        Raises:
            ValueError: No project is open.
        """
        if self._project is None:
            raise ValueError("No project is open.")
        if (
            self._active is not None
            and self._active.document.document_id == document_id
        ):
            return self._active.state
        session = self._browse_sessions.get(document_id)
        return (
            session.state
            if session is not None
            else self._project.load(
                DocumentKey(self._project.metadata.project_id, document_id)
            )
        )

    def job_measurement_from_assessment(self, document_id: str) -> JobRiskMeasurement:
        """Borrow current worker tasks/results for an independent Job copy.

        Args:
            document_id: Exact assessment identity in this project's ownership catalog.

        Returns:
            Detached immutable Job measurement; no ownership or worker data is changed.

        Raises:
            ValueError: Project/model is absent, or calculation is stale/incomplete.
            KeyError: The assessment is not owned by this project.
        """
        if self._project is None:
            raise ValueError("No project is open.")
        if not any(
            e.document_id == document_id for e in self.read_history().history.entries
        ):
            raise KeyError(document_id)
        source = self.assessment_source(document_id)
        if not isinstance(source, (LifftDraft, DuetDraft, TstDraft)):
            raise ValueError("Unsupported assessment source.")
        result = stored_result(
            self._project,
            DocumentKey(self._project.metadata.project_id, document_id),
            source,
        )
        return job_measurement_from_result(source, result)

    @property
    def pending_release_count(self) -> int:
        """Report handles requiring cleanup retry, including failed candidate opens.

        Args:
            None.

        Returns:
            Number of detached repository handles retained for release retry.
        """
        return len(self._pending)

    @property
    def release_diagnostics(self) -> tuple[ReleaseDiagnostic, ...]:
        """Return current pending cleanup failures as immutable technical records.

        Args:
            None.

        Returns:
            Immutable cleanup records with exception type/errno and no raw data or
            exception contents.
        """
        return tuple(diagnostic for _, diagnostic in self._pending)

    def _check(self, choice: CloseChoice | None = None) -> None:
        """Validate the synchronous transition guard and dirty disposition.

        Args:
            choice: Explicit project-departure Save/Discard/Cancel disposition.
                Integrated same-project navigation retains edits without Save;
                Cancel always prevents the transition. Dirty project departure and
                diagnostic source switching require explicit disposition.

        Returns:
            None when no transition is active and the optional dirty choice is typed.

        Raises:
            RuntimeError: Another transition already owns the workspace.
            ValueError: The supplied dirty-state choice is not a CloseChoice.
        """
        if self._busy:
            raise RuntimeError("A project transition is already in progress.")
        _ = self.editing
        if choice is not None and not isinstance(choice, CloseChoice):
            raise ValueError("Unsupported dirty-state choice.")

    def _permitted(self, choice: CloseChoice | None) -> bool:
        """Test dirty-state consent without I/O or querying result providers.

        Args:
            choice: Explicit Save/Discard/Cancel disposition. None permits only a clean
                current session; Cancel or absent required consent prevents the
                transition.

        Returns:
            True unless cancelled or the current session is dirty without an explicit
            disposition.
        """
        return choice is not CloseChoice.CANCEL and (
            not self.has_unsaved_changes or choice is not None
        )

    def _release(self, project: OwnedProject[State]) -> bool:
        """Close a detached owned handle while retaining failures for retry.

        Args:
            project: Owned detached repository to close; this workspace retains
                ownership if release fails.

        Returns:
            True after close succeeds; False after recording the failed detached handle
            for retry without masking another error.
        """
        try:
            project.close()
        except Exception as error:
            # Resource cleanup must not mask the original load/save error or
            # reverse an already committed transition. Retain ownership for retry.
            diagnostic = ReleaseDiagnostic(
                f"{type(error).__module__}.{type(error).__qualname__}",
                error.errno if isinstance(error, OSError) else None,
            )
            self._pending.append((project, diagnostic))
            return False
        return True

    def _save_current(self, choice: CloseChoice | None) -> None:
        """Resolve all retained tool drafts before completing a transition.

        Args:
            choice: Explicit Save/Discard/Cancel disposition. None permits only a clean
                current session; Cancel or absent required consent prevents the
                transition.

        Returns:
            None; save edited retained sources only with an explicit Save choice.
            Discard/Cancel do not query the result provider.

        Raises:
            ValueError: The selected Save supplies a result to an adapter without
                saved-result support.
            RuntimeError: The active session cannot be saved on this thread or
                reentrantly.
        """
        if choice is CloseChoice.SAVE and self.has_unsaved_changes:
            if self.editing is not None:
                self.stage_assessments()
                with self.editing.stage():
                    self._save_browse()
                self.editing.synchronize()
                self.editing.commit()
            else:
                self._save_browse()
        self._browse_sessions.clear()
        self._browse_pending.clear()
        self._browse_readonly.clear()

    def _save_browse(self, result: HistoricalAssessmentResult | None = None) -> None:
        """Persist dirty retained tabs and the active source without losing ownership.

        Args:
            result: Optional active source calculation; other tabs use the provider's
                identity-checked result or save inputs without an unrelated result.

        Returns:
            None; restore the active view even when a write fails. Each source uses
            the existing transactional repository contract.
        """
        active = self._active
        sessions = dict(self._browse_sessions)
        if active is not None:
            sessions[active.document.document_id] = active
        try:
            for session in sessions.values():
                if session is active or session.is_dirty:
                    self._active = session
                    self._persist_active(result if session is active else None)
        finally:
            self._active = active

    def _persist_active(self, result: HistoricalAssessmentResult | None = None) -> None:
        """Commit source and current output together, after target validation.

        The injected owner-thread provider must return only the active source
        calculation or None. Failed writes preserve the session clean marker;
        Discard/Cancel transitions never query the provider or write results.

        Args:
            result: Optional sole calculation bound to the exact active inputs; None
                uses the injected provider where applicable.

        Returns:
            None after source/current calculation commit and clean-marker update;
            failure preserves dirty intent.

        Raises:
            ValueError: A calculation is supplied but the active adapter cannot
                atomically save results.
            RuntimeError: The active session save is reentrant or invoked outside its
                owner thread.
        """
        assert self._active is not None and self._project is not None
        identity = self._active.document.document_id
        if identity in self._browse_readonly:
            if self._active.is_dirty:
                raise ValueError(
                    "A valid workplace assignment is required in this context."
                )
            return
        entry = self._browse_pending.get(identity)
        if entry is not None and not self._active.is_dirty:
            return
        if result is None and self._result_provider is not None:
            result = self._result_provider()
        if entry is not None:
            if not isinstance(self._project, HistoricalProject):
                raise RuntimeError("Historical creation adapter is not configured.")
            self._active.save(_InitialAssessmentSave(self._project, entry, result))
            if self.editing is not None:
                self.editing.set_editor(
                    "assessment.creation:" + identity, entry, "assessment.edit"
                )
            del self._browse_pending[identity]
            self._history_snapshot = None
            return
        if result is None:
            self._active.save(self._project)
        else:
            if not isinstance(self._project, SavedResultRepository):
                raise ValueError("Project does not support saved results.")
            self._active.save(ResultSave(self._project, result))

    def switch(
        self,
        location: str,
        document_id: str | None,
        *,
        choice: CloseChoice | None = None,
        remember: bool = True,
    ) -> TransitionOutcome:
        """Prepare a target before releasing current state; preserve failures for retry.

        A same-file/same-document request keeps unsaved history. Other dirty transitions
        require Save or Discard; Cancel does no I/O. Target failures close newly
        acquired handles; old-save failures retain the current draft. Successful
        activation precedes old-handle cleanup and recency updates, whose failures are
        returned as warnings rather than failed transitions. None opens a verified empty
        project without inventing an assessment.

        Args:
            location: Caller-normalized native destination; publication operations
                require a nonblank different location and never overwrite.
            document_id: Exact stable saved/source identity, never a row index or
                display caption.
            choice: Explicit Save/Discard/Cancel disposition. None permits only a clean
                current session; Cancel or absent required consent prevents the
                transition.
            remember: False for caller-owned temporary/untitled backing, which must not
                enter recent history before first explicit Save.

        Returns:
            Completion plus nonfatal cleanup/recency warning keys; False for
            cancellation or absent required consent.

        Raises:
            ValueError: Path/document identity is blank, empty opening finds saved
                assessments, or loaded source/metadata is invalid.
            RuntimeError: Another transition is active, the draft changes during
                loading, or the session save violates its thread guard.
        """
        self._check(choice)
        if not location.strip() or (
            document_id is not None and not document_id.strip()
        ):
            raise ValueError("Location and document identity must not be blank.")
        if choice is CloseChoice.CANCEL:
            return TransitionOutcome(False)
        current = self._active
        same_file = self._project is not None and location == self._location
        if (
            same_file
            and current is not None
            and current.document.document_id == document_id
        ):
            return TransitionOutcome(True)
        if not self._permitted(choice) and not (same_file and self.editing is not None):
            return TransitionOutcome(False)
        if same_file and self.editing is not None:
            self.stage_assessments()
        token = (current.revision, current.is_dirty) if current is not None else None
        self._busy = True
        candidate: OwnedProject[State] | None = None
        adopted = False
        try:
            candidate = self._project if same_file else self._opener(location)
            assert candidate is not None
            session: DocumentSession[State] | None = None
            if document_id is None:
                if not isinstance(candidate, CatalogProject):
                    raise ValueError(
                        "Empty project opening requires a catalog adapter."
                    )
                if candidate.list_assessments():
                    raise ValueError("Select an assessment from this nonempty project.")
            else:
                key = DocumentKey(candidate.metadata.project_id, document_id)
                loaded = candidate.load(key)
                session = DocumentSession(key, loaded, persisted=True)
            if current is not None and token != (current.revision, current.is_dirty):
                raise RuntimeError("The active draft changed during project loading.")
            if same_file and self.editing is not None:
                if self._active is not None:
                    self._browse_sessions[self._active.document.document_id] = (
                        self._active
                    )
            else:
                self._save_current(choice)
            previous = self._project
            self._project, self._active, self._location = candidate, session, location
            if previous is not candidate:
                self._hierarchy_snapshot = None
                self._job_snapshot = None
                self._risk_snapshot = None
                self._history_snapshot = None
            adopted = True
            warnings = []
            if previous is not None and not same_file and not self._release(previous):
                warnings.append("project.cleanup_failed")
            warning = (
                remember_open_location(location, self._settings) if remember else None
            )
            if warning is not None:
                warnings.append(warning)
            return TransitionOutcome(True, tuple(warnings))
        finally:
            try:
                if candidate is not None and not same_file and not adopted:
                    self._release(candidate)
            finally:
                self._busy = False

    def select_context(
        self, context: AssessmentContext, *, choice: CloseChoice | None = None
    ) -> TransitionOutcome:
        """Select a bound assessment in the current project without moving data.

        Cancel or a missing dirty decision performs no repository I/O. Validate exact
        ownership and load the target before saving or replacing the old session.
        Missing contexts raise KeyError; lookup/load/save failures keep the current
        session. Selecting its own context preserves dirty history, even with Save or
        Discard, because no document transition takes place. No project connection or
        recent-file preference changes here.

        Args:
            context: Exact worker/workplace/model ownership, independent of display
                labels.
            choice: Explicit Save/Discard/Cancel disposition. None permits only a clean
                current session; Cancel or absent required consent prevents the
                transition.

        Returns:
            Completion after selecting the exact bound source; False for
            cancelled/missing dirty consent.

        Raises:
            ValueError: Requested project ownership or the returned binding is
                inconsistent.
            RuntimeError: No binding-capable project is open, a transition is active, or
                the draft changes during selection.
            KeyError: No saved source is bound to the requested exact context.
        """
        self._check(choice)
        if choice is CloseChoice.CANCEL or (
            self.editing is None and not self._permitted(choice)
        ):
            return TransitionOutcome(False)
        project = self._project
        if project is None:
            raise RuntimeError("No project is open.")
        if context.worker.project_id != project.metadata.project_id:
            raise ValueError("Assessment context belongs to another project.")
        if not isinstance(project, AssessmentBindings):
            raise RuntimeError("Assessment ownership adapter is not configured.")
        current = self._active
        token = (current.revision, current.is_dirty) if current is not None else None
        self._busy = True
        try:
            key = project.find_assessment(context)
            if key is None:
                raise KeyError(context)
            expected = AssessmentBinding(key, context)
            if project.assessment_binding(key) != expected:
                raise ValueError(
                    "Repository returned inconsistent assessment ownership."
                )
            same_document = current is not None and current.document == key
            session = (
                current
                if same_document
                else DocumentSession(key, project.load(key), persisted=True)
            )
            if current is not None and token != (current.revision, current.is_dirty):
                raise RuntimeError("The active draft changed during context selection.")
            if same_document:
                return TransitionOutcome(True)
            if self.editing is not None:
                self.stage_assessments()
            else:
                self._save_current(choice)
            self._active = session
            return TransitionOutcome(True)
        finally:
            self._busy = False

    def select_assignment(
        self, target: AssignmentSelection, *, choice: CloseChoice | None = None
    ) -> TransitionOutcome:
        """Open the assessment for an explicit assignment/tool owner.

        Closed assignments remain selectable; active-workplace eligibility belongs to
        the presenter. Cancel/missing consent performs no repository I/O. Load and
        validate the target before saving the old source. Failures preserve the current
        session; same-document selection retains its edits and undo history.

        Args:
            target: Exact project/assignment/model whose saved assessment should
                open; closed assignments remain valid owners.
            choice: Explicit Save/Discard/Cancel disposition. None permits only a clean
                current session; Cancel or absent required consent prevents the
                transition.

        Returns:
            Completion after selecting the assignment/model current source; False for
            cancelled/missing dirty consent.

        Raises:
            ValueError: Requested project ownership or returned saved history is
                inconsistent.
            RuntimeError: No history-capable project is open, a transition is active, or
                the draft changes during selection.
            KeyError: The assignment/model has no current saved assessment.
        """
        self._check(choice)
        if choice is CloseChoice.CANCEL or (
            self.editing is None and not self._permitted(choice)
        ):
            return TransitionOutcome(False)
        project = self._project
        if project is None:
            raise RuntimeError("No project is open.")
        if target.project_id != project.metadata.project_id:
            raise ValueError("Assignment selection belongs to another project.")
        if not isinstance(project, HistoryRepository):
            raise RuntimeError("Assessment ownership adapter is not configured.")
        current = self._active
        token = (current.revision, current.is_dirty) if current is not None else None
        self._busy = True
        try:
            history = project.load_history()
            if history.project_id != target.project_id:
                raise ValueError("Repository returned foreign assessment history.")
            entry = (
                history.current_for(target.assignment_id, target.kind)
                if target.assignment_id is not None
                else history.standalone_for(target.worker_id or "", target.kind)
            )
            if entry is None:
                raise KeyError(target)
            key = DocumentKey(target.project_id, entry.document_id)
            same_document = current is not None and current.document == key
            session = (
                current
                if same_document
                else DocumentSession(key, project.load(key), persisted=True)
            )
            if current is not None and token != (current.revision, current.is_dirty):
                raise RuntimeError(
                    "The active draft changed during assignment selection."
                )
            if same_document:
                return TransitionOutcome(True)
            if self.editing is not None:
                self.stage_assessments()
            else:
                self._save_current(choice)
            self._active = session
            return TransitionOutcome(True)
        finally:
            self._busy = False

    def save(self, result: HistoricalAssessmentResult | None = None) -> bool:
        """Save the integrated project, including when no assessment is open.

        Keep history and ownership unchanged. Storage failures propagate with the draft
        still dirty; callers may retry. Saving does not update recent history.

        Args:
            result: Optional sole calculation bound to the exact active inputs; None
                uses the injected provider where applicable.

        Returns:
            True after complete integrated project publication or diagnostic source
            persistence. False with no project, or no diagnostic source. Main Save
            retains project history and its Redo branch.

        Raises:
            ValueError: Supplied/provider result cannot be saved by the current adapter
                or does not match the active source.
            RuntimeError: Another transition is active or the session save violates its
                owner-thread/reentrancy guard.
        """
        self._check()
        if self._project is None:
            return False
        editing = self.editing
        if self._active is None and editing is None:
            return False
        self._busy = True
        try:
            if editing is not None:
                self.stage_assessments()
                with editing.stage():
                    self._save_browse(result)
                editing.synchronize()
                editing.commit()
            else:
                self._save_browse(result)
            return True
        finally:
            self._busy = False

    def save_as(
        self,
        location: str,
        *,
        metadata: ProjectMetadata | None = None,
        result: HistoricalAssessmentResult | None = None,
    ) -> TransitionOutcome:
        """Activate a complete copy containing current edits; never save the original.

        The adapter publishes exclusively and returns a newly owned repository.
        Candidate validation precedes activation. The copied active source starts clean
        with fresh history; the original retains its last persisted state. Failed
        copying/loading retains the old session and its undo history.

        Args:
            location: Caller-normalized native destination; publication operations
                require a nonblank different location and never overwrite.
            metadata: Validated project display metadata; snapshot editing must retain
                the stable project identity.
            result: Optional sole calculation bound to the exact active inputs; None
                uses the injected provider where applicable.

        Returns:
            Completion plus nonfatal cleanup/recency warnings after copy activation with
            a fresh clean session.

        Raises:
            ValueError: Destination/metadata identity is invalid, copied metadata/source
                differs, or copied result storage is unsupported.
            RuntimeError: No snapshot-capable project is open, metadata-copy support is
                absent, or a transition/session guard fails.
        """
        self._check()
        project, current = self._project, self._active
        if project is None:
            raise RuntimeError("No project is open.")
        if not location.strip() or location == self._location:
            raise ValueError("Save As requires a different nonblank location.")
        if not isinstance(project, SnapshotProject):
            raise RuntimeError("Project snapshot adapter is not configured.")
        expected_metadata = metadata if metadata is not None else project.metadata
        if expected_metadata.project_id != project.metadata.project_id:
            raise ValueError("Save As cannot change project identity.")
        if metadata is not None and not isinstance(project, MetadataSnapshotProject):
            raise RuntimeError("Copy metadata adapter is not configured.")
        if result is None and self._result_provider is not None:
            result = self._result_provider()
        if self.editing is not None:
            self.editing.validate()
        self._busy = True
        candidate: OwnedProject[State] | None = None
        adopted = False
        try:
            sources = dict(self._browse_sessions)
            if current is not None:
                sources[current.document.document_id] = current
            copied: dict[str, DocumentSession[State]] = {}
            pending = dict(self._browse_pending)

            def prepare(copy: OwnedProject[State]) -> None:
                """Apply retained edits to an unpublished repository, never the source.

                Args:
                    copy: Private snapshot handle owned by the adapter during staging.

                Returns:
                    None after populating clean copied sessions; exceptions prevent
                    destination publication and leave live sessions untouched.

                Raises:
                    RuntimeError: A required historical creation adapter is absent.
                    ValueError: The copy cannot store the requested calculated result.
                """
                for identity, source_session in sources.items():
                    preview = pending.get(identity)
                    if identity in self._browse_readonly or (
                        preview is not None and not source_session.is_dirty
                    ):
                        copied[identity] = source_session
                        continue
                    if preview is not None:
                        if not isinstance(copy, HistoricalProject):
                            raise RuntimeError(
                                "Historical creation adapter is not configured."
                            )
                        copy.create_historical_assessment(preview, source_session.state)
                        del pending[identity]
                    cloned = DocumentSession(
                        source_session.document,
                        source_session.state,
                        persisted=not source_session.is_dirty,
                    )
                    if source_session.is_dirty:
                        cloned.save(copy)
                    if source_session is current and result is not None:
                        if not isinstance(copy, SavedResultRepository):
                            raise ValueError(
                                "Copied project does not support saved results."
                            )
                        cloned.save(ResultSave(copy, result))
                    copied[identity] = cloned

            if isinstance(project, PreparedSnapshotProject):
                candidate = project.snapshot_prepared(location, prepare, metadata)
            else:
                # Generic single-document adapters retain their original contract.
                document = current.document if current is not None else None
                state = current.state if current is not None else None
                if metadata is not None:
                    assert isinstance(project, MetadataSnapshotProject)
                    candidate = project.snapshot_with_metadata(
                        location, document, state, metadata
                    )
                else:
                    candidate = project.snapshot(location, document, state)
                if current is not None:
                    copied[current.document.document_id] = DocumentSession(
                        current.document,
                        candidate.load(current.document),
                        persisted=True,
                    )
            if candidate.metadata != expected_metadata:
                raise ValueError("Copied project metadata differs from the request.")
            session = (
                copied.get(current.document.document_id)
                if current is not None
                else None
            )
            self._browse_sessions = copied
            self._browse_pending = pending
            self._project, self._active, self._location = candidate, session, location
            adopted = True
            self._hierarchy_snapshot = None
            self._job_snapshot = None
            self._risk_snapshot = None
            self._history_snapshot = None
            warnings: tuple[str, ...] = (
                () if self._release(project) else ("project.cleanup_failed",)
            )
            warning = remember_open_location(location, self._settings)
            if warning is not None:
                warnings += (warning,)
            return TransitionOutcome(True, warnings)
        finally:
            if candidate is not None and not adopted:
                self._release(candidate)
            self._busy = False

    def backup(self, location: str) -> TransitionOutcome:
        """Copy only persisted project data; retain source/history/location/preferences.

        Unsaved draft input is deliberately excluded. Publication or validation failures
        propagate without releasing the current project.

        Args:
            location: Caller-normalized native destination; publication operations
                require a nonblank different location and never overwrite.

        Returns:
            Completion plus optional detached-copy cleanup warning; active source,
            history, location and preferences remain unchanged.

        Raises:
            ValueError: Destination is blank or equals the active location.
            RuntimeError: No snapshot-capable project is open or another transition is
                active.
        """
        self._check()
        project = self._project
        if project is None:
            raise RuntimeError("No project is open.")
        if not location.strip() or location == self._location:
            raise ValueError("Backup requires a different nonblank location.")
        if not isinstance(project, SnapshotProject):
            raise RuntimeError("Project snapshot adapter is not configured.")
        self._busy = True
        try:
            candidate = (
                project.snapshot_saved(location)
                if self.editing is not None
                and isinstance(project, DurableSnapshotProject)
                else project.snapshot(location, None, None)
            )
            warnings = () if self._release(candidate) else ("project.cleanup_failed",)
            return TransitionOutcome(True, warnings)
        finally:
            self._busy = False

    def create_empty(
        self,
        location: str,
        metadata: ProjectMetadata,
        *,
        choice: CloseChoice | None = None,
        remember: bool = False,
    ) -> TransitionOutcome:
        """Create and activate a genuinely empty project after resolving current edits.

        Args:
            location: Nonexistent normalized destination, usually temporary backing.
            metadata: Stable project identity and display defaults.
            choice: Explicit current Save/Discard/Cancel; None requires a clean session.
            remember: Register a successfully published user destination when True.

        Returns:
            Transition outcome with nonfatal cleanup/recency warnings. Cancellation
            creates no file. No worker, organization, source or result is invented.

        Raises:
            RuntimeError: Empty-project factory is absent or another transition runs.
            ValueError: Location/metadata is invalid or creation returns nonempty data.
            OSError: Exclusive creation fails, retaining the current project.
        """
        self._check(choice)
        if not self._permitted(choice):
            return TransitionOutcome(False)
        if self._empty_creator is None:
            raise RuntimeError("Empty-project creation is unavailable.")
        if not location.strip() or location == self._location:
            raise ValueError("New project requires a different nonblank location.")
        self._busy = True
        candidate: OwnedProject[State] | None = None
        adopted = False
        try:
            self._save_current(choice)
            candidate = self._empty_creator(location, metadata)
            if candidate.metadata != metadata:
                raise ValueError("Creator returned different project metadata.")
            if (
                not isinstance(candidate, CatalogProject)
                or candidate.list_assessments()
            ):
                raise ValueError("Empty creator returned assessment data.")
            previous = self._project
            self._project, self._active, self._location = candidate, None, location
            self._hierarchy_snapshot = None
            self._job_snapshot = None
            self._risk_snapshot = None
            self._history_snapshot = None
            adopted = True
            warnings = []
            if previous is not None and not self._release(previous):
                warnings.append("project.cleanup_failed")
            warning = (
                remember_open_location(location, self._settings) if remember else None
            )
            if warning is not None:
                warnings.append(warning)
            return TransitionOutcome(True, tuple(warnings))
        finally:
            if candidate is not None and not adopted:
                self._release(candidate)
            self._busy = False

    def create(
        self,
        location: str,
        metadata: ProjectMetadata,
        document_id: str,
        initial: State,
        *,
        choice: CloseChoice | None = None,
        remember: bool = True,
    ) -> TransitionOutcome:
        """Create a new project with its first saved draft, then activate it.

        Resolve dirty consent first. An explicitly requested current save finishes
        before creation; if creation fails, that current session remains active (and may
        now be clean). The creator must reject existing destinations and remove
        incomplete files on initialization failure. No Save As is implied. Set
        remember=False for owned temporary backing of an untitled desktop project; it
        must not enter recent history before its first explicit Save.

        Args:
            location: Caller-normalized native destination; publication operations
                require a nonblank different location and never overwrite.
            metadata: Validated identity and initial display/unit metadata for the new
                project.
            document_id: Exact stable saved/source identity, never a row index or
                display caption.
            initial: Validated initial immutable source to create and persist exactly,
                without replacing existing document IDs.
            choice: Explicit Save/Discard/Cancel disposition. None permits only a clean
                current session; Cancel or absent required consent prevents the
                transition.
            remember: False for caller-owned temporary/untitled backing, which must not
                enter recent history before first explicit Save.

        Returns:
            Completion plus nonfatal cleanup/recency warnings after exclusive project
            creation; False for cancelled/missing dirty consent.

        Raises:
            ValueError: Location/source identity is blank, destination equals the active
                location, or created metadata/source differs.
            RuntimeError: Creation is unconfigured, another transition is active, or the
                old draft changes during creation.
        """
        self._check(choice)
        if not location.strip() or not document_id.strip():
            raise ValueError("Location and document identity must not be blank.")
        if not self._permitted(choice):
            return TransitionOutcome(False)
        if self._creator is None:
            raise RuntimeError("Project creation adapter is not configured.")
        if location == self._location:
            raise ValueError("Cannot create over the active project location.")
        self._busy = True
        candidate: OwnedProject[State] | None = None
        adopted = False
        try:
            self._save_current(choice)
            current = self._active
            token = (
                (current.revision, current.is_dirty) if current is not None else None
            )
            candidate = self._creator(location, metadata, document_id, initial)
            if candidate.metadata != metadata:
                raise ValueError("Creator returned different project metadata.")
            key = DocumentKey(metadata.project_id, document_id)
            loaded = candidate.load(key)
            if loaded != initial:
                raise ValueError("Creator did not persist the requested initial draft.")
            if current is not None and token != (current.revision, current.is_dirty):
                raise RuntimeError("The active draft changed during project creation.")
            session = DocumentSession(key, loaded, persisted=True)
            previous = self._project
            self._project, self._active, self._location = candidate, session, location
            self._hierarchy_snapshot = None
            self._job_snapshot = None
            self._risk_snapshot = None
            self._history_snapshot = None
            adopted = True
            warnings = []
            if previous is not None and not self._release(previous):
                warnings.append("project.cleanup_failed")
            warning = (
                remember_open_location(location, self._settings) if remember else None
            )
            if warning is not None:
                warnings.append(warning)
            return TransitionOutcome(True, tuple(warnings))
        finally:
            try:
                if candidate is not None and not adopted:
                    self._release(candidate)
            finally:
                self._busy = False

    def _hierarchy_repository(self) -> HierarchyRepository:
        """Require a borrowed active hierarchy capability.

        Args:
            None.

        Returns:
            Borrowed active hierarchy-capable repository; lifetime remains owned by this
            workspace.

        Raises:
            RuntimeError: No project is open or the active adapter lacks hierarchy
                access.
        """
        if self._project is None:
            raise RuntimeError("No project is open.")
        if not isinstance(self._project, HierarchyRepository):
            raise RuntimeError("Project hierarchy adapter is not configured.")
        return self._project

    def read_hierarchy(self) -> HierarchySnapshot:
        """Refresh catalog data and invalidate all previously issued edit snapshots.

        Failed refresh also invalidates the old snapshot. Assessment source, history,
        dirty state and recent-file preferences remain untouched.

        Args:
            None.

        Returns:
            Fresh exact hierarchy snapshot; any previously issued hierarchy authority is
            invalidated even when read fails.

        Raises:
            ValueError: The repository returns hierarchy data owned by another project.
            RuntimeError: No hierarchy-capable project is open or another transition is
                active.
        """
        self._check()
        self._hierarchy_snapshot = None
        repository = self._hierarchy_repository()
        self._busy = True
        try:
            hierarchy = repository.load_hierarchy()
            assert self._project is not None
            if hierarchy.work.project_id != self._project.metadata.project_id:
                raise ValueError("Repository returned a foreign hierarchy.")
            snapshot = HierarchySnapshot(hierarchy)
            self._hierarchy_snapshot = (self._project, snapshot)
            return snapshot
        finally:
            self._busy = False

    def hierarchy_is_current(self, snapshot: HierarchySnapshot) -> bool:
        """Check issued snapshot identity without I/O or extending its lifetime.

        Args:
            snapshot: Latest exact workspace-issued snapshot for the current project
                handle; value-equal copies carry no replacement authority.

        Returns:
            True only for the latest exact issued hierarchy object from the active
            repository handle.
        """
        return (
            self._hierarchy_snapshot is not None
            and self._hierarchy_snapshot[0] is self._project
            and self._hierarchy_snapshot[1] is snapshot
        )

    def replace_hierarchy(
        self, snapshot: HierarchySnapshot, replacement: WorkHierarchy
    ) -> HierarchySnapshot:
        """Commit an explicit catalog replacement without saving assessment edits.

        Require the latest workspace-issued snapshot from this project handle. The
        repository compares expected saved data atomically. Failures retain the current
        snapshot for retry; a saved-data conflict needs a refresh. Success issues a
        fresh snapshot, invalidating old callbacks. Catalog changes commit immediately
        and are separate from assessment undo/redo.

        Args:
            snapshot: Latest exact workspace-issued snapshot for the current project
                handle; value-equal copies carry no replacement authority.
            replacement: Complete proposed immutable replacement for this snapshot,
                preserving project and protected reference identities.

        Returns:
            Fresh replacement authority after atomic expected-value commit; active
            assessment edits are not saved.

        Raises:
            ValueError: Snapshot authority is stale/foreign, project identity changes,
                or protected saved references reject the replacement.
            RuntimeError: No hierarchy-capable project is open or another transition is
                active.
        """
        self._check()
        if not self.hierarchy_is_current(snapshot):
            raise ValueError("Hierarchy snapshot is stale or belongs to another owner.")
        if replacement.work.project_id != snapshot.hierarchy.work.project_id:
            raise ValueError("Catalog replacement cannot cross projects.")
        repository = self._hierarchy_repository()
        refreshed = HierarchySnapshot(replacement)
        self._busy = True
        try:
            repository.replace_hierarchy(snapshot.hierarchy, replacement)
            assert self._project is not None
            self._hierarchy_snapshot = (self._project, refreshed)
            return refreshed
        finally:
            self._busy = False

    def save_worker_catalogs(
        self,
        hierarchy: HierarchySnapshot,
        replacement_hierarchy: WorkHierarchy,
        jobs: JobSnapshot,
        replacement_jobs: JobCatalog,
    ) -> tuple[HierarchySnapshot, JobSnapshot]:
        """Save worker/classification edits without changing assessment undo.

        Args:
            hierarchy: Latest exact workspace-issued hierarchy view before worker edits.
            replacement_hierarchy: Complete proposed worker/demographic hierarchy after
                form validation.
            jobs: Latest exact workspace-issued jobs/placements/assignments view.
            replacement_jobs: Complete proposed classification catalog; validate against
                replacement_hierarchy before atomic commit.

        Returns:
            Fresh hierarchy/job authorities after both catalogs commit atomically; risk
            authority is invalidated.

        Raises:
            ValueError: Either view is stale/foreign or proposed classifications fail
                hierarchy/reference validation.
            RuntimeError: No worker-catalog persistence capability is open or another
                transition is active.
        """
        self._check()
        if not self.hierarchy_is_current(hierarchy) or not self.jobs_are_current(jobs):
            raise ValueError("Worker form no longer matches this project.")
        if self._project is None:
            raise RuntimeError("No project is open.")
        if not isinstance(self._project, WorkerRepository):
            raise RuntimeError("Worker persistence is not configured.")
        replacement_jobs.validate_hierarchy(replacement_hierarchy)
        self._busy = True
        try:
            self._project.replace_worker_catalogs(
                hierarchy.hierarchy, replacement_hierarchy, jobs.jobs, replacement_jobs
            )
            next_hierarchy = HierarchySnapshot(replacement_hierarchy)
            next_jobs = JobSnapshot(replacement_jobs)
            self._hierarchy_snapshot = (self._project, next_hierarchy)
            self._job_snapshot = (self._project, next_jobs)
            self._risk_snapshot = None
            return next_hierarchy, next_jobs
        finally:
            self._busy = False

    def _jobs_repository(self) -> JobRepository:
        """Require a borrowed active jobs capability.

        Args:
            None.

        Returns:
            Borrowed active jobs-capable repository; do not close it in the caller.

        Raises:
            RuntimeError: No project is open or the active adapter lacks job access.
        """
        if self._project is None:
            raise RuntimeError("No project is open.")
        if not isinstance(self._project, JobRepository):
            raise RuntimeError("Project jobs adapter is not configured.")
        return self._project

    def plant_shift_count(self, plant_name: str) -> int:
        """Read the Plant's in-use shift count without invalidating editor authority.

        Args:
            plant_name: Literal Plant identity; a new/unlinked Plant has count zero.

        Returns:
            Distinct shifts used by active Job placements or worker workplace
            assignments. Read-only projection preserves dirty/history state and
            previously issued hierarchy/Job edit snapshots.

        Raises:
            RuntimeError: Workspace is busy/closed or Job persistence is unavailable.
            ValueError: Repository returned a catalog owned by another project.
        """
        self._check()
        repository = self._jobs_repository()
        self._busy = True
        try:
            jobs = repository.load_jobs()
            assert self._project is not None
            if jobs.project_id != self._project.metadata.project_id:
                raise ValueError("Repository returned a foreign job catalog.")
            return plant_shift_count(jobs, plant_name)
        finally:
            self._busy = False

    def read_jobs(self) -> JobSnapshot:
        """Refresh catalog data and invalidate all previously issued edit snapshots.

        Failed refresh also invalidates the old snapshot. Assessment source, history,
        dirty state and recent-file preferences remain untouched.

        Args:
            None.

        Returns:
            Fresh exact jobs snapshot; earlier jobs authority is invalidated even when
            read fails.

        Raises:
            ValueError: The repository returns jobs owned by another project.
            RuntimeError: No jobs-capable project is open or another transition is
                active.
        """
        self._check()
        self._job_snapshot = None
        repository = self._jobs_repository()
        self._busy = True
        try:
            jobs = repository.load_jobs()
            assert self._project is not None
            if jobs.project_id != self._project.metadata.project_id:
                raise ValueError("Repository returned a foreign job catalog.")
            snapshot = JobSnapshot(jobs)
            self._job_snapshot = (self._project, snapshot)
            return snapshot
        finally:
            self._busy = False

    def jobs_are_current(self, snapshot: JobSnapshot) -> bool:
        """Check issued snapshot identity without I/O or extending its lifetime.

        Args:
            snapshot: Latest exact workspace-issued snapshot for the current project
                handle; value-equal copies carry no replacement authority.

        Returns:
            True only for the latest exact jobs snapshot from the active repository
            handle.
        """
        return (
            self._job_snapshot is not None
            and self._job_snapshot[0] is self._project
            and self._job_snapshot[1] is snapshot
        )

    def replace_jobs(
        self, snapshot: JobSnapshot, replacement: JobCatalog
    ) -> JobSnapshot:
        """Commit an explicit catalog replacement without saving assessment edits.

        Require the latest workspace-issued snapshot from this project handle. The
        repository compares expected saved data atomically. Failures retain the current
        snapshot for retry; a saved-data conflict needs a refresh. Success issues a
        fresh snapshot, invalidating old callbacks. Catalog changes commit immediately
        and are separate from assessment undo/redo.

        Args:
            snapshot: Latest exact workspace-issued snapshot for the current project
                handle; value-equal copies carry no replacement authority.
            replacement: Complete proposed immutable replacement for this snapshot,
                preserving project and protected reference identities.

        Returns:
            Fresh jobs authority after expected-value commit; risk authority is
            invalidated and assessment edits remain unsaved.

        Raises:
            ValueError: Snapshot is stale/foreign, project identity changes, or saved
                reference/expected-value checks reject the replacement.
            RuntimeError: No jobs-capable project is open or another transition is
                active.
        """
        self._check()
        if not self.jobs_are_current(snapshot):
            raise ValueError("Job snapshot is stale or belongs to another owner.")
        if replacement.project_id != snapshot.jobs.project_id:
            raise ValueError("Catalog replacement cannot cross projects.")
        repository = self._jobs_repository()
        refreshed = JobSnapshot(replacement)
        self._busy = True
        try:
            repository.replace_jobs(snapshot.jobs, replacement)
            assert self._project is not None
            self._job_snapshot = (self._project, refreshed)
            self._risk_snapshot = None
            return refreshed
        finally:
            self._busy = False

    def _history_repository(self) -> HistoryRepository:
        """Require a borrowed active assessment-ownership capability.

        Args:
            None.

        Returns:
            Borrowed active assessment-ownership repository, owned by this workspace.

        Raises:
            RuntimeError: No project is open or the active adapter lacks saved
                assessment ownership.
        """
        if self._project is None:
            raise RuntimeError("No project is open.")
        if not isinstance(self._project, HistoryRepository):
            raise RuntimeError("History management adapter is not configured.")
        return self._project

    def read_history(self) -> HistorySnapshot:
        """Refresh history authority without saving or activating any assessment.

        Args:
            None.

        Returns:
            Fresh exact saved-history authority without activating or saving an
            assessment.

        Raises:
            ValueError: The repository returns assessment history owned by another
                project.
            RuntimeError: No mutable-history project is open or another transition is
                active.
        """
        self._check()
        self._history_snapshot = None
        repository = self._history_repository()
        self._busy = True
        try:
            history = repository.load_history()
            assert self._project is not None
            if history.project_id != self._project.metadata.project_id:
                raise ValueError("Repository returned foreign assessment history.")
            snapshot = HistorySnapshot(history)
            self._history_snapshot = (self._project, snapshot)
            return snapshot
        finally:
            self._busy = False

    def history_is_current(self, snapshot: HistorySnapshot) -> bool:
        """Check exact workspace/project-handle authority without database I/O.

        Args:
            snapshot: Latest exact workspace-issued snapshot for the current project
                handle; value-equal copies carry no replacement authority.

        Returns:
            True only for the latest exact history snapshot from this active project
            handle.
        """
        return (
            self._history_snapshot is not None
            and self._history_snapshot[0] is self._project
            and self._history_snapshot[1] is snapshot
        )

    def delete_active_assessment(self, snapshot: HistorySnapshot) -> HistorySnapshot:
        """Delete the explicitly confirmed open source, clearing its session on success.

        Pending widget text is the host's responsibility. Confirmation authorizes
        abandoning this source's unsaved edits. Failure retains the active session,
        dirty state and history. Integrated deletion changes private project state
        and is reversible through project history; diagnostics commit immediately.

        Args:
            snapshot: Latest exact workspace-issued snapshot for the current project
                handle; value-equal copies carry no replacement authority.

        Returns:
            Fresh history authority after confirmed source deletion; the active session
            is cleared only after successful commit.

        Raises:
            ValueError: The issued history snapshot is stale/foreign or the adapter
                rejects expected saved history.
            RuntimeError: No assessment/deletion capability is open or another
                transition is active.
            KeyError: The open source no longer exists in the issued history.
        """
        self._check()
        active = self._active
        if active is None:
            raise RuntimeError("No assessment is open.")
        if not self.history_is_current(snapshot):
            raise ValueError("History snapshot is stale or belongs to another owner.")
        document_id = active.document.document_id
        if not any(e.document_id == document_id for e in snapshot.history.entries):
            raise KeyError(document_id)
        repository: object = self._project
        if not isinstance(repository, DeletableHistoryRepository):
            raise RuntimeError("Assessment deletion is not configured.")
        self._busy = True
        try:
            result = repository.delete_historical_assessment(
                snapshot.history, document_id
            )
            self._active = None
            self._browse_sessions.pop(document_id, None)
            self._browse_pending.pop(document_id, None)
            self._browse_readonly.discard(document_id)
            refreshed = HistorySnapshot(result)
            assert self._project is not None
            self._history_snapshot = (self._project, refreshed)
            return refreshed
        finally:
            self._busy = False

    def transfer_assessments(
        self,
        jobs: JobSnapshot,
        history: HistorySnapshot,
        request: TransferRequest,
        document_ids: Mapping[AssessmentKind, str],
        *,
        choice: CloseChoice | None = None,
    ) -> TransitionOutcome:
        """Transfer saved sources; resolve dirty edits before removing the open source.

        Preflight precedes an explicitly chosen Save. Failed transfer retains the active
        session (possibly clean after that Save). Successful removal clears its session;
        no unrelated assessment is selected or reassigned automatically.

        Args:
            jobs: Latest exact workspace-issued jobs/placements/assignments view.
            history: Latest exact workspace-issued saved assessment ownership
                view.
            request: Explicit Copy/Move selection with exact source and destination
                assignment ownership.
            document_ids: Fresh destination source identity per selected model; the
                transfer planner validates uniqueness and completeness.
            choice: Explicit Save/Discard/Cancel disposition. None permits only a clean
                current session; Cancel or absent required consent prevents the
                transition.

        Returns:
            Completion after atomic saved-source/result Copy/Move; False only when
            removal needs unprovided dirty consent.

        Raises:
            ValueError: Issued job/history views are stale, transfer ownership/IDs
                conflict, or expected saved data changed.
            RuntimeError: Transfer capability is absent or another transition is active.
            KeyError: A required source/destination identity is absent from the transfer
                catalogs.
        """
        self._check(choice)
        if not self.jobs_are_current(jobs) or not self.history_is_current(history):
            raise ValueError("Reopen the transfer form before transferring.")
        repository: object = self._project
        if not isinstance(repository, TransferRepository):
            raise RuntimeError("Transfer adapter is not configured.")
        plan = plan_transfer(
            self.read_hierarchy().hierarchy.work,
            jobs.jobs,
            history.history,
            request,
            document_ids,
        )
        removes_active = (
            self._active is not None
            and self._active.document.document_id in plan.removed_documents
        )
        if removes_active and (
            choice is CloseChoice.CANCEL
            or (self.editing is None and not self._permitted(choice))
        ):
            return TransitionOutcome(False)
        self._busy = True
        try:
            if removes_active:
                if self.editing is not None:
                    self.stage_assessments()
                else:
                    self._save_current(choice)
            repository.transfer_assessments(
                jobs.jobs, history.history, request, document_ids
            )
            if removes_active:
                self._active = None
            self._job_snapshot = None
            self._history_snapshot = None
            return TransitionOutcome(True)
        finally:
            self._busy = False

    @property
    def supports_rotations(self) -> bool:
        """Report the full-project JROT capability without loading or writing data.

        Args:
            None.

        Returns:
            True when the full project exposes supported job risk and rotation
            capabilities; no I/O.
        """
        return self.supports_job_risk and isinstance(self._project, RotationRepository)

    def historical_result(self) -> HistoricalAssessmentResult | None:
        """Expose the active assessment's sole matching saved calculation.

        Args:
            None.

        Returns:
            Sole saved result matching the exact current source, or None after
            edits/invalidation or absent calculation; no automatic evaluation.
        """
        active = self._active
        project: object = self._project
        if active is None:
            return None
        result = stored_result(project, active.document, active.state)
        return result if result is not None and result.source == active.state else None

    def rotation_repository(self) -> RotationRepository:
        """Borrow JROT commands/catalogs from the active project-owned connection.

        The modal caller must finish before workspace switching/closure. Explicit scheme
        saves update this same adapter, including its format/version state.

        Args:
            None.

        Returns:
            Borrowed active full-project JROT port; modal callers must finish before
            workspace switching/closure.

        Raises:
            ValueError: No supported full project with JROT capability is open.
        """
        project: object = self._project
        if not self.supports_job_risk or not isinstance(project, RotationRepository):
            raise ValueError("JROT requires an open full project.")
        return project

    def plot_repository(self) -> PlotRepository:
        """Borrow the active full-project PLOT port without releasing its connection.

        The modal caller must finish before switching/closing this workspace. Its
        explicit saves update the same adapter's format/version state.

        Args:
            None.

        Returns:
            Borrowed active full-project PLOT port; modal callers must finish before
            workspace switching/closure.

        Raises:
            ValueError: No supported full project with PLOT capability is open.
        """
        project: object = self._project
        if not self.supports_job_risk or not isinstance(project, PlotRepository):
            raise ValueError("PLOT requires an open full project.")
        return project

    @property
    def supports_job_risk(self) -> bool:
        """Report optional risk capability without loading or changing a project.

        Args:
            None.

        Returns:
            True when the active repository reports supported job-profile evidence; no
            load or write.
        """
        project: object = self._project
        return isinstance(project, JobRiskRepository) and project.supports_job_risk

    def _risk_repository(self) -> JobRiskRepository:
        """Require a borrowed active supported job-risk capability.

        Args:
            None.

        Returns:
            Borrowed active supported risk repository; do not release its connection.

        Raises:
            RuntimeError: No project is open or its adapter lacks supported job risk
                profiles.
        """
        if self._project is None:
            raise RuntimeError("No project is open.")
        if not isinstance(self._project, JobRiskRepository):
            raise RuntimeError("Job risk adapter is not configured.")
        if not self._project.supports_job_risk:
            raise RuntimeError("The open project does not support current Job risks.")
        return self._project

    def read_job_risk(self) -> JobRiskSnapshot:
        """Refresh risk authority without saving or replacing assessment edits.

        Args:
            None.

        Returns:
            Fresh exact risk authority; previously issued risk authority is invalidated
            even when loading fails.

        Raises:
            ValueError: The repository returns a risk catalog owned by another project.
            RuntimeError: No supported risk project is open or another transition is
                active.
        """
        self._check()
        self._risk_snapshot = None
        repository = self._risk_repository()
        self._busy = True
        try:
            risk = repository.load_job_risk()
            assert self._project is not None
            if risk.project_id != self._project.metadata.project_id:
                raise ValueError("Repository returned a foreign risk catalog.")
            snapshot = JobRiskSnapshot(risk)
            self._risk_snapshot = (self._project, snapshot)
            return snapshot
        finally:
            self._busy = False

    def job_risk_is_current(self, snapshot: JobRiskSnapshot) -> bool:
        """Check exact view/project-handle authority with no repository I/O.

        Args:
            snapshot: Latest exact workspace-issued snapshot for the current project
                handle; value-equal copies carry no replacement authority.

        Returns:
            True only for the latest exact risk snapshot from this active project
            handle.
        """
        return (
            self._risk_snapshot is not None
            and self._risk_snapshot[0] is self._project
            and self._risk_snapshot[1] is snapshot
        )

    def delete_job(
        self,
        jobs: JobSnapshot,
        risk: JobRiskSnapshot,
        job_id: str,
    ) -> tuple[JobSnapshot, JobRiskSnapshot]:
        """Delete a saved job without saving or replacing active assessment edits.

        Args:
            jobs: Latest exact workspace-issued jobs/placements/assignments view.
            risk: Latest exact workspace-issued saved current risk view.
            job_id: Exact saved job identity affected by this operation.

        Returns:
            Fresh jobs/risk authorities after atomic deletion; inconsistent committed
            output invalidates both.

        Raises:
            ValueError: Issued views are stale/foreign, domain reference checks reject
                deletion, or committed output differs.
            RuntimeError: No supported risk project is open or another transition is
                active.
        """
        self._check()
        if not self.jobs_are_current(jobs) or not self.job_risk_is_current(risk):
            raise ValueError("Reload the current Job Management form before deleting.")
        repository = self._risk_repository()
        self._busy = True
        try:
            expected = delete_job(jobs.jobs, risk.risk, job_id)
            saved = repository.delete_job(jobs.jobs, risk.risk, job_id)
            if saved != expected:
                self._job_snapshot = None
                self._risk_snapshot = None
                raise ValueError(
                    "Saved records differ from the requested job deletion."
                )
            refreshed_jobs, refreshed_risk = (
                JobSnapshot(saved[0]),
                JobRiskSnapshot(saved[1]),
            )
            assert self._project is not None
            self._job_snapshot = (self._project, refreshed_jobs)
            self._risk_snapshot = (self._project, refreshed_risk)
            return refreshed_jobs, refreshed_risk
        finally:
            self._busy = False

    def save_job_details(
        self,
        jobs: JobSnapshot,
        risk: JobRiskSnapshot,
        job: Job,
        values: JobRiskValues | None,
    ) -> tuple[JobSnapshot, JobRiskSnapshot]:
        """Save the management form without saving or replacing the assessment.

        Publish both refreshed catalogs after the repository commits. Validation or
        write errors leave the existing form available for correction/retry.

        Args:
            jobs: Latest exact workspace-issued jobs/placements/assignments view.
            risk: Latest exact workspace-issued saved risk-values view.
            job: Validated same-identity job form fields to commit atomically with
                optional values evidence.
            values: Optional proposed job-risk values evidence from the same form;
                None preserves the selected values policy of the domain operation.

        Returns:
            Fresh Job/risk authorities after one atomic accepted edit. Active assessment
            inputs stay unchanged; integrated project history records the Job operation.

        Raises:
            ValueError: Issued views are stale/foreign, job/values validation fails, or
                committed form output differs.
            RuntimeError: No supported risk project is open or another transition is
                active.
        """
        self._check()
        if not self.jobs_are_current(jobs) or not self.job_risk_is_current(risk):
            raise ValueError("Reload the current Job Management form before saving.")
        repository = self._risk_repository()
        self._busy = True
        try:
            expected = save_job_details(jobs.jobs, risk.risk, job, values)
            saved = repository.save_job_details(jobs.jobs, risk.risk, job, values)
            if saved != expected:
                self._job_snapshot = None
                self._risk_snapshot = None
                raise ValueError("Saved job form differs from the requested changes.")
            refreshed_jobs, refreshed_risk = (
                JobSnapshot(saved[0]),
                JobRiskSnapshot(saved[1]),
            )
            assert self._project is not None
            self._job_snapshot = (self._project, refreshed_jobs)
            self._risk_snapshot = (self._project, refreshed_risk)
            return refreshed_jobs, refreshed_risk
        finally:
            self._busy = False

    def list_assessments(self) -> tuple[AssessmentEntry, ...]:
        """Read the active project's persisted catalog without editing or saving.

        Args:
            None.

        Returns:
            Stable saved catalog, or an empty tuple when no project is open; no editor
            save.

        Raises:
            RuntimeError: An open project lacks source-catalog access or another
                transition is active.
        """
        self._check()
        if self._project is None:
            return ()
        if not isinstance(self._project, CatalogProject):
            raise RuntimeError("Project catalog adapter is not configured.")
        self._busy = True
        try:
            return self._project.list_assessments()
        finally:
            self._busy = False

    def create_assessment(
        self,
        document_id: str,
        initial: State,
        *,
        choice: CloseChoice | None = None,
        context: AssessmentContext | None = None,
    ) -> TransitionOutcome:
        """Create and activate a new document inside the current project.

        Resolve dirty intent first; check existing IDs before a requested old save. Save
        completes before insertion. If insertion fails the old session remains active
        (possibly now clean). Successful insertion activates a clean new history without
        closing the project or updating recent-file preferences. With context, require
        atomic source/binding creation and preflight occupied ownership before saving. A
        later creation failure can leave the old draft clean if its separately requested
        save already succeeded.

        Args:
            document_id: Exact stable saved/source identity, never a row index or
                display caption.
            initial: Validated initial immutable source to create and persist exactly,
                without replacing existing document IDs.
            choice: Explicit Save/Discard/Cancel disposition. None permits only a clean
                current session; Cancel or absent required consent prevents the
                transition.
            context: Exact worker/workplace/model ownership, independent of display
                labels.

        Returns:
            Completion after exclusive source creation and activation of a fresh clean
            session; False for cancelled/missing dirty consent.

        Raises:
            ValueError: Source ID/context is already occupied, project ownership
                disagrees or initial source validation fails.
            RuntimeError: Required source/binding creation is absent or another
                transition is active.
        """
        self._check(choice)
        if choice is CloseChoice.CANCEL or (
            self.editing is None and not self._permitted(choice)
        ):
            return TransitionOutcome(False)
        project = self._project
        if project is None:
            raise RuntimeError("No project is open.")
        if not isinstance(project, CatalogProject):
            raise RuntimeError("Project catalog adapter is not configured.")
        key = DocumentKey(project.metadata.project_id, document_id)
        bound_project: BoundAssessmentProject[State] | None = None
        binding = AssessmentBinding(key, context) if context is not None else None
        if binding is not None:
            if not isinstance(project, BoundAssessmentProject):
                raise RuntimeError(
                    "Bound assessment creation adapter is not configured."
                )
            bound_project = project
        self._busy = True
        try:
            if any(entry.document == key for entry in project.list_assessments()):
                raise ValueError("Assessment identity already exists.")
            if bound_project is not None:
                assert binding is not None
                if bound_project.find_assessment(binding.context) is not None:
                    raise ValueError("Assessment context already exists.")
            if self.editing is not None:
                self.stage_assessments()
            else:
                self._save_current(choice)
            if bound_project is not None:
                assert binding is not None
                bound_project.create_bound_assessment(binding, initial)
            else:
                project.insert_assessment(key, initial)
            self._active = DocumentSession(key, initial, persisted=True)
            return TransitionOutcome(True)
        finally:
            self._busy = False

    def create_assignment_assessment(
        self,
        entry: AssignmentAssessment,
        initial: State,
        *,
        choice: CloseChoice | None = None,
    ) -> TransitionOutcome:
        """Create and activate a historically owned source after explicit consent.

        Preflight precedes any requested save of the old document. Creation repeats
        constraints atomically; failure retains the old session, possibly clean if its
        separate save succeeded. Ownership is explicit; an existing assessment for
        the same assignment/tool is rejected before any source insertion.

        Args:
            entry: Explicit assignment/tool ownership record for the new
                historically owned source.
            initial: Validated initial immutable source to create and persist exactly,
                without replacing existing document IDs.
            choice: Explicit Save/Discard/Cancel disposition. None permits only a clean
                current session; Cancel or absent required consent prevents the
                transition.

        Returns:
            Completion after atomic historical source creation and activation; False for
            cancelled/missing dirty consent.

        Raises:
            ValueError: Assignment/tool ownership/source validation or
                saved-state conflict checks fail.
            RuntimeError: Historical creation is absent, another transition is active,
                or the old draft changes during preflight.
        """
        self._check(choice)
        if choice is CloseChoice.CANCEL or (
            self.editing is None and not self._permitted(choice)
        ):
            return TransitionOutcome(False)
        project = self._project
        if project is None:
            raise RuntimeError("No project is open.")
        if not isinstance(project, HistoricalProject):
            raise RuntimeError("Historical creation adapter is not configured.")
        current = self._active
        token = (current.revision, current.is_dirty) if current is not None else None
        key = DocumentKey(project.metadata.project_id, entry.document_id)
        self._busy = True
        try:
            project.validate_historical_creation(entry, initial)
            if current is not None and token != (current.revision, current.is_dirty):
                raise RuntimeError(
                    "The active draft changed during creation preflight."
                )
            if self.editing is not None:
                self.stage_assessments()
            else:
                self._save_current(choice)
            project.create_historical_assessment(entry, initial)
            self._history_snapshot = None
            self._active = DocumentSession(key, initial, persisted=True)
            return TransitionOutcome(True)
        finally:
            self._busy = False

    def close(self, *, choice: CloseChoice | None = None) -> TransitionOutcome:
        """Resolve dirty intent before releasing the active session and connection.

        Args:
            choice: Explicit Save/Discard/Cancel disposition. None permits only a clean
                current session; Cancel or absent required consent prevents the
                transition.

        Returns:
            Completion plus optional release warning; False leaves the current
            project/session intact when dirty consent is missing or cancelled.

        Raises:
            ValueError: Dirty disposition is untyped or a requested source/result save
                fails validation.
            RuntimeError: Another transition is active or a requested session save
                violates its thread guard.
        """
        self._check(choice)
        if not self._permitted(choice):
            return TransitionOutcome(False)
        self._busy = True
        try:
            self._save_current(choice)
            previous = self._project
            self._project, self._active, self._location = None, None, None
            self._editing = None
            self._editing_owner = None
            self._hierarchy_snapshot = None
            self._job_snapshot = None
            self._risk_snapshot = None
            self._history_snapshot = None
            if previous is not None and not self._release(previous):
                return TransitionOutcome(True, ("project.cleanup_failed",))
            return TransitionOutcome(True)
        finally:
            self._busy = False

    def retry_releases(self) -> int:
        """Retry only detached handles; return the remaining pending count.

        Args:
            None.

        Returns:
            Remaining detached-handle count after one retry per pending handle; active
            project/session is unaffected.

        Raises:
            RuntimeError: Another workspace transition is active.
        """
        self._check()
        self._busy = True
        try:
            pending, self._pending = self._pending, []
            for project, _ in pending:
                self._release(project)
            return self.pending_release_count
        finally:
            self._busy = False

    def associate_assessment(self, document_id: str, assignment_id: int) -> None:
        """Associate saved standalone ownership without changing scientific data.

        Args:
            document_id: Saved standalone source after all pending edits are resolved.
            assignment_id: Explicit active destination belonging to the same worker.

        Returns:
            None; refresh cached ownership only after successful repository commit.

        Raises:
            RuntimeError: Project/capability is absent or unsaved inputs remain.
            ValueError: Destination or ownership violates domain constraints.
            KeyError: Source or assignment is absent.
        """
        self._check()
        if self.editing is not None:
            self.stage_assessments()
        elif self.has_unsaved_changes:
            raise RuntimeError(
                "Save or discard edits before associating an assessment."
            )
        project: object = self._project
        if not isinstance(project, AssociableAssessmentRepository):
            raise RuntimeError("Assessment association is unavailable.")
        project.associate_assessment(document_id, assignment_id)
        self._history_snapshot = None

    def associate_assessment_at_workplace(
        self,
        document_id: str,
        workplace: WorkplaceContext,
        placement_id: int | None,
        *,
        effective_date: date,
    ) -> AssignmentAssessment:
        """Associate directly from a real workplace without a separate worker dialog.

        Args:
            document_id: Saved standalone assessment after pending edits are resolved.
            workplace: Explicit real station and shift selected by the user.
            placement_id: Optional Job or the existing assignment's unchanged Job.
            effective_date: Explicit start date when the assignment must be created.

        Returns:
            Associated ownership after one atomic repository mutation. Inputs/results
            are unchanged; private editing requires main Save for durable publication.

        Raises:
            RuntimeError: Project/capability is absent or unsaved input remains.
            ValueError: Workplace/worker/Job ownership or uniqueness checks fail.
            KeyError: Source or workplace/worker membership is missing.
        """
        self._check()
        if self.editing is not None:
            self.stage_assessments()
        elif self.has_unsaved_changes:
            raise RuntimeError(
                "Save or discard edits before associating an assessment."
            )
        project: object = self._project
        if not isinstance(project, WorkplaceAssociationRepository):
            raise RuntimeError("Direct workplace association is unavailable.")
        entry = project.associate_assessment_at_workplace(
            document_id, workplace, placement_id, effective_date=effective_date
        )
        self._job_snapshot = None
        self._history_snapshot = None
        return entry

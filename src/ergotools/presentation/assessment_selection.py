"""Widget-independent catalog selection and bound assessment creation.

Presentation layer. Interpret explicit user selections and project immutable values for
controls or interchange, independently of widget construction. Persistence and source
history use injected application services. Do not infer identity from captions, units
from interface language, or missing scientific quantities from zero. Storage errors
propagate to the host for localized reporting; user data remains literal.
"""

from dataclasses import dataclass, field

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.hierarchy_access import HierarchySnapshot
from ergotools.application.project_workspace import ProjectWorkspace, TransitionOutcome
from ergotools.application.session import DocumentSession
from ergotools.domain.assessments.context import AssessmentContext, WorkplaceContext
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    assessment_kind,
)
from ergotools.presentation.worker_options import (
    WorkerOption,
    WorkerOrder,
    worker_options,
)


@dataclass(frozen=True, slots=True)
class SelectionCatalog:
    """Presenter-issued saved catalog with exact object authority.

    Attributes:
        snapshot: Latest workspace-issued hierarchy snapshot.
        workers: Original-form worker labels coupled to stable IDs in requested order.
    """

    snapshot: HierarchySnapshot
    workers: tuple[WorkerOption, ...]


@dataclass(frozen=True, slots=True)
class AssessmentSelection:
    """One explicit complete choice bound to the current catalog and active source.

    Attributes:
        catalog: Exact presenter-issued catalog used for preparation.
        context: Exact project/worker/workplace/model ownership.
        session: Captured active session identity, or None with no source open; not
            owned by this choice.
        revision: Captured session revision, or None with no active source.
    """

    catalog: SelectionCatalog
    context: AssessmentContext
    session: DocumentSession[AssessmentDraft] | None = field(repr=False)
    revision: int | None


class AssessmentSelector:
    """Own callback interpretation while delegating persistence and dirty choices.

    The caller must resolve uncommitted widget text before select/create. This
    presenter has no layout, dialog, default-selection or worker-label parsing
    policy. Incomplete hierarchy choices remain outside a complete selection.
    """

    def __init__(self, workspace: ProjectWorkspace[AssessmentDraft]) -> None:
        """Bind a workspace without loading a project or choosing any records.

        Args:
            workspace: Borrowed single-user workspace owning the project connection,
                active session and catalog authority.

        Returns:
            None; retain the workspace without reading, selecting or saving.
        """
        self._workspace = workspace
        self._catalog: SelectionCatalog | None = None
        self._selection: AssessmentSelection | None = None

    def refresh(self, order: WorkerOrder = WorkerOrder.ID) -> SelectionCatalog:
        """Invalidate previous callbacks before refreshing, including on failure.

        Args:
            order: Original worker-ID or null-first last-name ordering independent of UI
                language.

        Returns:
            Fresh presenter-issued catalog; previous catalogs and prepared requests
            become invalid before I/O.

        Raises:
            RuntimeError: Required workspace catalog capability is absent or a
                transition is active.
            ValueError: Saved catalog ownership/order validation fails.
        """
        self._catalog = None
        self._selection = None
        snapshot = self._workspace.read_hierarchy()
        catalog = SelectionCatalog(
            snapshot, worker_options(snapshot.hierarchy.work, order)
        )
        self._catalog = catalog
        return catalog

    def _check_catalog(self, catalog: SelectionCatalog) -> None:
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
        if catalog is not self._catalog or not self._workspace.hierarchy_is_current(
            catalog.snapshot
        ):
            raise ValueError(
                "Selection catalog is stale or belongs to another presenter."
            )

    def prepare(
        self,
        catalog: SelectionCatalog,
        worker_id: str,
        workplace: WorkplaceContext,
        kind: AssessmentKind,
    ) -> AssessmentSelection:
        """Validate a complete explicit choice and invalidate previous selections.

        Missing workers/stations/shifts raise KeyError. Empty branches cannot be coerced
        into a workplace, and no fallback to the first available ID occurs.

        Args:
            catalog: Exact current presenter-issued catalog.
            worker_id: Explicit stable worker identity; no default/fallback selection.
            workplace: Complete exact plant/section/line/station/shift selection.
            kind: Explicit supported assessment model.

        Returns:
            Fresh exact selection/request capturing current session identity and
            revision.

        Raises:
            ValueError: Catalog authority or typed selection identity is invalid.
            KeyError: Explicit worker/workplace or eligible assignment is absent.
        """
        self._selection = None
        self._check_catalog(catalog)
        owner = catalog.snapshot.hierarchy.work.worker_context(worker_id, workplace)
        session = self._workspace.active
        selected = AssessmentSelection(
            catalog,
            AssessmentContext(owner, kind),
            session,
            session.revision if session is not None else None,
        )
        self._selection = selected
        return selected

    def _check_selection(self, selected: AssessmentSelection) -> None:
        """No I/O and no implicit retry or fallback selection.

        Args:
            selected: Exact prepared choice issued by this presenter.

        Returns:
            None when catalog, current session identity and revision still match.

        Raises:
            ValueError: Choice is obsolete/foreign or source/catalog ownership changed
                since preparation.
        """
        if selected is not self._selection:
            raise ValueError(
                "Assessment selection is obsolete or belongs to another presenter."
            )
        self._check_catalog(selected.catalog)
        active = self._workspace.active
        if selected.session is not active or (
            active is not None and selected.revision != active.revision
        ):
            raise ValueError("Active assessment changed after selection was prepared.")

    def select(
        self, selected: AssessmentSelection, *, choice: CloseChoice | None = None
    ) -> TransitionOutcome:
        """Activate an existing bound assessment; Cancel/failure remains retryable.

        Args:
            selected: Exact current prepared choice to activate.
            choice: Save/Discard/Cancel disposition for dirty source; None requires a
                clean session.

        Returns:
            Workspace transition outcome; successful activation consumes the request,
            while cancellation/failure permits deliberate retry.

        Raises:
            ValueError: Choice/catalog/source ownership is stale or invalid.
            KeyError: No current saved version exists for that exact selection.
            RuntimeError: Required workspace capability is absent or a
                transition/session guard fails.
        """
        self._check_selection(selected)
        outcome = self._workspace.select_context(selected.context, choice=choice)
        if outcome.completed:
            self._selection = None
        return outcome

    def create(
        self,
        selected: AssessmentSelection,
        document_id: str,
        initial: AssessmentDraft,
        *,
        choice: CloseChoice | None = None,
    ) -> TransitionOutcome:
        """Create and bind atomically after checking that the selected model matches.

        Mismatched source types fail before any old-draft save. A completed action
        invalidates the callback; cancellation and failures permit deliberate retry.

        Args:
            selected: Exact current prepared choice whose model/ownership must match the
                source.
            document_id: Fresh stable source identity to insert exclusively.
            initial: Typed initial source for the chosen model; validate before any
                old-draft Save.
            choice: Save/Discard/Cancel disposition for dirty current source.

        Returns:
            Workspace transition outcome; success consumes the choice and activates a
            clean new source session.

        Raises:
            ValueError: Choice/source model, version/currentness/identity or existing
                saved ownership conflicts.
            RuntimeError: Required creation capability is absent or a workspace/session
                transition guard fails.
        """
        self._check_selection(selected)
        if assessment_kind(initial) != selected.context.kind:
            raise ValueError(
                "Initial source does not match the selected assessment model."
            )
        outcome = self._workspace.create_assessment(
            document_id, initial, choice=choice, context=selected.context
        )
        if outcome.completed:
            self._selection = None
        return outcome

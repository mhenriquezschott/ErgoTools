"""PLOT source edit history with explicit, possibly partial, position saves.

Application layer. Prepare immutable analysis/history values through injected ports. Qt
controls, chart rendering, SQL transactions and user consent remain outside this module;
only explicitly supplied persistence callbacks can write.
"""

from collections.abc import Callable
from dataclasses import dataclass, replace
from math import isfinite

from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.plot_filters import (
    PlotDemographics,
    PlotFilterSelection,
    PlotRiskView,
    paired_range,
)
from ergotools.domain.plot_positions import PlotPositions
from ergotools.domain.plot_scope import PlotScope

# Owner-selected maximum magnification: 400% of the fitted plant image.
MAX_PLOT_ZOOM = 4.0


@dataclass(frozen=True, slots=True)
class PlotFilterState:
    """Accepted controls, including disabled and unpaired bounds.

    Age uses years, weight kg and height cm; None means unset, never zero.

    Attributes:
        scope: Exact selected plant/hierarchy/shift scope.
        tool: Selected scientific model.
        risk_view: Individual/job analysis mode.
        enabled: Whether demographic predicates currently apply.
        sex: Literal saved sex category, or None for all.
        bounds: Six canonical lower/upper values: age, weight and height;
            disabled/incomplete values remain restorable.
    """

    scope: PlotScope
    tool: AssessmentKind
    risk_view: PlotRiskView
    enabled: bool
    sex: str | None
    bounds: tuple[float | None, ...]

    def __post_init__(self) -> None:
        """Reject invalid snapshots while retaining incomplete/reversed ranges.

        Args:
            None.

        Returns:
            None; validate six bounds and the projected selection.

        Raises:
            ValueError: Bounds count or typed filter selection/demographic values are
                invalid.
        """
        if len(self.bounds) != 6:
            raise ValueError("PLOT history requires six canonical bounds.")
        self.selection()

    def selection(self) -> PlotFilterSelection:
        """Project effective predicates without losing the original controls.

        The six canonical values are age years, weight kg and height cm, each lower then
        upper. Incomplete or reversed pairs project as no range.

        Args:
            None.

        Returns:
            Effective immutable predicates; disabled and incomplete bound controls
            remain preserved in this source state.

        Raises:
            ValueError: Scope, tool, mode, flags or demographic values fail selection
                validation.
        """
        pairs = tuple(
            paired_range(self.bounds[i], self.bounds[i + 1]) for i in (0, 2, 4)
        )
        return PlotFilterSelection(
            self.scope,
            self.tool,
            self.risk_view,
            PlotDemographics(self.enabled, self.sex, pairs[0], pairs[1], pairs[2]),
        )


@dataclass(frozen=True, slots=True)
class PlotNavigationState:
    """Session-only map view; never stored as project geometry or scientific data.

    Attributes:
        plant: Exact plant whose original-image center is captured.
        zoom: Magnification relative to fitted image size, from 1 through MAX_PLOT_ZOOM.
        center: View center in original image pixels.
        opacity: Marker-only opacity; the background image remains opaque.
    """

    plant: str
    zoom: float
    center: tuple[float, float]
    opacity: float

    def __post_init__(self) -> None:
        """Reject invalid view snapshots before they enter shared history.

        Args:
            None; frozen dataclass fields supply the proposed view.

        Returns:
            None; valid snapshots remain independent of widgets and storage.

        Raises:
            ValueError: A view component is missing, nonfinite or outside its range.
        """
        if (
            not self.plant
            or len(self.center) != 2
            or not all(isfinite(v) for v in (self.zoom, *self.center, self.opacity))
            or not 1 <= self.zoom <= MAX_PLOT_ZOOM
            or self.opacity not in (0.7, 0.8, 0.9, 1.0)
        ):
            raise ValueError("Invalid PLOT navigation snapshot.")


@dataclass(frozen=True, slots=True)
class PlotEditState:
    """One chronological map and analysis revision without widgets or image bytes.

    Attributes:
        positions: Immutable geometry in original image pixels.
        filters: Accepted control state, or None before initialization.
        applied: Last published effective selection, or None before Apply/after Clear.
        navigation: Session-only image view, or None before the first gesture.
    """

    positions: PlotPositions
    filters: PlotFilterState | None = None
    applied: PlotFilterSelection | None = None
    navigation: PlotNavigationState | None = None


@dataclass(frozen=True, slots=True)
class ReplacePlotFilters:
    """One command replacing accepted analysis controls without saving geometry.

    Attributes:
        document: Exact project/document owner.
        before: Expected current complete edit state.
        filters: Proposed controls including disabled/incomplete values.
        applied: Proposed published selection, or None.
        label_key: Stable localized history action key.
    """

    document: DocumentKey
    before: PlotEditState
    filters: PlotFilterState
    applied: PlotFilterSelection | None
    label_key: str = "plot.history.filters"

    def apply(self, state: PlotEditState) -> PlotEditState:
        """Reject stale/foreign commands before publishing the new selection.

        Args:
            state: Current geometry and accepted analysis controls.

        Returns:
            Replacement edit state with the proposed controls/applied selection and
            unchanged geometry.

        Raises:
            ValueError: Expected state is stale or current positions belong to another
                project.
        """
        if (
            state != self.before
            or state.positions.project_id != self.document.project_id
        ):
            raise ValueError("PLOT filter edit belongs to another revision.")
        navigation = state.navigation
        if navigation is not None and navigation.plant != self.filters.scope.plant:
            navigation = None
        return replace(
            state, filters=self.filters, applied=self.applied, navigation=navigation
        )


@dataclass(frozen=True, slots=True)
class ReplacePlotNavigation:
    """Replace a session-only view in the same chronological geometry timeline.

    Attributes:
        document: Exact map/project history owner.
        before: Expected complete immutable current state.
        navigation: Proposed relative zoom, image center and marker opacity.
        label_key: Localized map-view history description.
    """

    document: DocumentKey
    before: PlotEditState
    navigation: PlotNavigationState
    label_key: str = "plot.history.navigation"

    def apply(self, state: PlotEditState) -> PlotEditState:
        """Validate ownership/revision and retain geometry and filters verbatim.

        Args:
            state: Current map history revision.

        Returns:
            New view revision without any project-data mutation.

        Raises:
            ValueError: The revision is stale or belongs to another project.
        """
        if (
            state != self.before
            or state.positions.project_id != self.document.project_id
        ):
            raise ValueError("PLOT navigation belongs to another revision.")
        return replace(state, navigation=self.navigation)


@dataclass(frozen=True, slots=True)
class ReplacePlotPositions:
    """One complete map drag/batch command.

    Coordinates remain original-image pixels; immutable unchanged records are shared.

    Attributes:
        document: Exact project/document owner.
        before: Expected current geometry.
        after: Proposed complete geometry.
        label_key: Stable localized history action key.
    """

    document: DocumentKey
    before: PlotPositions
    after: PlotPositions
    label_key: str

    def apply(self, state: PlotEditState) -> PlotEditState:
        """Reject stale/foreign edits without modifying state or its redo branch.

        Args:
            state: Current geometry and accepted analysis controls.

        Returns:
            Replacement edit state with proposed geometry and unchanged filters.

        Raises:
            ValueError: Expected geometry is stale or replacement belongs to another
                project.
        """
        if (
            state.positions != self.before
            or self.after.project_id != self.document.project_id
        ):
            raise ValueError("PLOT edit belongs to another project or source revision.")
        return replace(state, positions=self.after)


class PlotPositionHistory:
    """Reuse document history; retain the persisted baseline for partial Save.

    Original controls save a selected worker/station or a worker batch, not every
    draft. A partial commit updates only that persisted subset. Dirty intent is
    therefore compared with the committed source, not a misleading global clean
    revision. Full-snapshot Save also marks the underlying session revision clean.
    Undo/redo never invokes persistence. This object owns no widgets or SQL.
    """

    def __init__(self, document: DocumentKey, positions: PlotPositions) -> None:
        """Bind a loaded immutable source to its project/document identity.

        Args:
            document: Exact project/document owner of this transient history.
            positions: Validated saved baseline in original image pixels.

        Returns:
            None; create an owned persisted DocumentSession and saved-position baseline.

        Raises:
            ValueError: Position/project ownership differs.
        """
        if document.project_id != positions.project_id:
            raise ValueError("PLOT history belongs to another project.")
        self.session = DocumentSession(
            document, PlotEditState(positions), persisted=True
        )
        self.saved = positions

    @property
    def state(self) -> PlotPositions:
        """Return current source geometry, including unsaved edits.

        Args:
            None.

        Returns:
            Current immutable position snapshot, including unsaved map edits.
        """
        return self.session.state.positions

    def reload_positions(self, positions: PlotPositions) -> None:
        """Rebase a changed persisted source; never replay obsolete full geometry.

        Ordinary Save updates saved before a reload, so it preserves history. A
        genuinely different saved snapshot invalidates prior geometry commands while
        retaining the current analysis controls as the new initial state.

        Args:
            positions: Validated newly read saved geometry in original image pixels.

        Returns:
            None; replace history only when saved geometry genuinely changed, retaining
            accepted analysis controls.

        Raises:
            ValueError: New geometry belongs to another project.
        """
        if positions.project_id != self.session.document.project_id:
            raise ValueError("PLOT geometry belongs to another project.")
        if positions != self.saved:
            self.session = DocumentSession(
                self.session.document,
                replace(self.session.state, positions=positions),
                persisted=True,
            )
            self.saved = positions

    def initialize_filters(
        self, filters: PlotFilterState, applied: PlotFilterSelection | None
    ) -> None:
        """Bind the initial view before any edits; no startup undo step is added.

        Args:
            filters: Initial accepted controls, including disabled and incomplete
                canonical bounds.
            applied: Initial published effective selection, or None before Apply.

        Returns:
            None; initialize the session without creating an Undo entry.

        Raises:
            ValueError: An Undo entry already exists; startup initialization cannot
                replace edited history.
        """
        if self.session.undo_label_key is not None:
            raise ValueError("Cannot initialize PLOT filters after editing.")
        self.session = DocumentSession(
            self.session.document,
            PlotEditState(self.state, filters, applied),
            persisted=True,
        )

    def edit_filters(
        self, filters: PlotFilterState, applied: PlotFilterSelection | None
    ) -> bool:
        """Record Apply, tool/scope selection or Clear in the same map history.

        Args:
            filters: Accepted control snapshot to record.
            applied: Published effective selection after Apply, or None after Clear.

        Returns:
            True when a new history entry is recorded; False for a no-op.

        Raises:
            ValueError: Command ownership or expected snapshot fails validation.
            RuntimeError: Session is used from another thread or during a reentrant
                operation.
        """
        return self.session.execute(
            ReplacePlotFilters(
                self.session.document, self.session.state, filters, applied
            )
        )

    @property
    def is_dirty(self) -> bool:
        """Compare current intent with the last successfully committed source.

        Args:
            None.

        Returns:
            True when current geometry differs from the committed baseline; filter-only
            edits do not require a geometry Save.
        """
        return self.state != self.saved

    def edit(self, positions: PlotPositions, label_key: str) -> bool:
        """Record one complete edit; no-ops retain redo and saved state.

        Args:
            positions: Complete proposed immutable geometry in original image pixels.
            label_key: Stable localized Undo/Redo action description key.

        Returns:
            True when a geometry edit is recorded; False for a no-op.

        Raises:
            ValueError: Command/project ownership or expected geometry fails validation.
            RuntimeError: Session is used from another thread or reentrantly.
        """
        return self.session.execute(
            ReplacePlotPositions(
                self.session.document, self.state, positions, label_key
            )
        )

    def save(
        self, positions: PlotPositions, writer: Callable[[PlotPositions], None]
    ) -> None:
        """Commit selected intent once; failures preserve drafts and history.

        The caller merges the chosen records into the persisted baseline. Other drafts
        stay unsaved. The writer must provide atomic persistence.

        Args:
            positions: Complete persisted baseline after merging only the user-selected
                records; other draft records can remain unsaved.
            writer: Borrowed atomic persistence callback; errors propagate without
                advancing saved baseline.

        Returns:
            None after a successful commit; only a complete current-state save marks the
            session revision clean.

        Raises:
            ValueError: Save geometry belongs to another project.
            RuntimeError: A full-session save is reentrant or occurs on another thread.
        """
        if positions.project_id != self.session.document.project_id:
            raise ValueError("PLOT save belongs to another project.")
        if positions == self.state:
            self.session.save(_PositionStore(writer))
        else:
            writer(positions)
        self.saved = positions


@dataclass(frozen=True, slots=True)
class _PositionStore:
    """Adapt the borrowed atomic position writer to the shared history save port.

    Attributes:
        writer: Callback committing a complete position snapshot, without owning the
            session.
    """

    writer: Callable[[PlotPositions], None]

    def save(self, document: DocumentKey, state: PlotEditState) -> None:
        """Adapt the same atomic position writer to the shared history save port.

        Args:
            document: Document ownership supplied by the shared session.
            state: Complete current history state whose geometry is written.

        Returns:
            None after the atomic writer succeeds; its failures propagate.

        Raises:
            ValueError: Document/project ownership disagrees with geometry.
        """
        if document.project_id != state.positions.project_id:
            raise ValueError("PLOT save belongs to another project.")
        self.writer(state.positions)

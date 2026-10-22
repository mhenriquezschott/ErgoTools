"""Widget-independent loading and saving for the Job workplace dialog.

Presentation layer. Interpret explicit user selections and project immutable values for
controls or interchange, independently of widget construction. Persistence and source
history use injected application services. Do not infer identity from captions, units
from interface language, or missing scientific quantities from zero. Storage errors
propagate to the host for localized reporting; user data remains literal.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from ergotools.application.hierarchy_access import HierarchySnapshot
from ergotools.application.job_access import JobSnapshot
from ergotools.application.job_placements import replace_active_placements
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.assessments.document import AssessmentDraft


@dataclass(frozen=True, slots=True)
class JobWorkplaceView:
    """One presenter-owned dialog snapshot across all shifts.

    Attributes:
        hierarchy: Exact hierarchy authority establishing available choices.
        catalog: Exact jobs authority used as the write precondition.
        job_id: Stable selected job identity.
        options: Complete exact available workplace tuples.
        selected: Current active placement workplaces; no caption parsing.
    """

    hierarchy: HierarchySnapshot
    catalog: JobSnapshot
    job_id: str
    options: tuple[WorkplaceContext, ...]
    selected: frozenset[WorkplaceContext]


class JobWorkplaces:
    """Coordinate immediate placement saves separately from assessment edits."""

    def __init__(self, workspace: ProjectWorkspace[AssessmentDraft]) -> None:
        """Inject the workspace without reading data or changing source state.

        Args:
            workspace: Borrowed project/workspace catalog capability; the host owns
                lifetime.

        Returns:
            None; retain dependency without I/O or assessment edits.
        """
        self._workspace = workspace
        self._view: JobWorkplaceView | None = None

    def load(self, job_id: str) -> JobWorkplaceView:
        """Refresh choices, invalidating prior callbacks even on failed loading.

        Args:
            job_id: Exact saved job identity to edit across all shifts.

        Returns:
            Fresh owned view with exact choices and current active selections; previous
            callbacks invalidate before reads.

        Raises:
            ValueError: The selected job is absent or saved catalogs have invalid
                ownership.
            RuntimeError: Required workspace capability is absent or a transition is
                active.
        """
        self._view = None
        hierarchy = self._workspace.read_hierarchy()
        catalog = self._workspace.read_jobs()
        if not any(item.job_id == job_id for item in catalog.jobs.jobs):
            raise ValueError("Job does not exist.")
        view = self._make_view(hierarchy, catalog, job_id)
        self._view = view
        return view

    def _make_view(
        self, hierarchy: HierarchySnapshot, catalog: JobSnapshot, job_id: str
    ) -> JobWorkplaceView:
        """Pure projection; no implicit save or source editor change.

        Args:
            hierarchy: Exact workspace-issued hierarchy authority.
            catalog: Exact workspace-issued job authority.
            job_id: Exact saved job identity whose placements are projected.

        Returns:
            Immutable view of all available workplace choices and current active
            placements.
        """
        return JobWorkplaceView(
            hierarchy,
            catalog,
            job_id,
            hierarchy.hierarchy.work.available_workplaces(),
            frozenset(
                item.workplace
                for item in catalog.jobs.placements
                if item.job_id == job_id and item.active
            ),
        )

    def save(
        self, view: JobWorkplaceView, workplaces: Iterable[WorkplaceContext]
    ) -> JobWorkplaceView:
        """Persist all shifts once; reject stale views and invalid memberships.

        Success returns fresh authority. Failure preserves the view for retry unless
        another refresh/project transition invalidated it. Dirty source edits and
        assessment undo history are not saved or discarded.

        Args:
            view: Exact current presenter-owned view still authorized by the workspace.
            workplaces: Explicit complete workplace selection across every shift;
                duplicates collapse.

        Returns:
            Fresh view and catalog authority after immediate atomic placement
            replacement.

        Raises:
            ValueError: View is stale/foreign, membership is invalid or protected
                references/expected saved values reject replacement.
            RuntimeError: Workspace capability is absent or a transition is active.
        """
        if (
            view is not self._view
            or not self._workspace.hierarchy_is_current(view.hierarchy)
            or not self._workspace.jobs_are_current(view.catalog)
        ):
            raise ValueError("Workplace view is stale or belongs to another owner.")
        requested = frozenset(workplaces)
        if not requested.issubset(view.options):
            raise ValueError("Selected workplace is not in the project hierarchy.")
        replacement = replace_active_placements(
            view.catalog.jobs, view.job_id, requested
        )
        catalog = self._workspace.replace_jobs(view.catalog, replacement)
        refreshed = self._make_view(view.hierarchy, catalog, view.job_id)
        self._view = refreshed
        return refreshed

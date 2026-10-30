"""Application-owned worker/tool/workplace browsing without implicit data creation.

Resolve saved worker/tool locations against direct ownership and optional real
workplace assignments. User preferences remember contexts; the workspace retains edited
tool
sessions and owns all persistence. No Qt, SQL, formulas or display units live here.
"""

from collections.abc import Callable
from dataclasses import dataclass, replace
from uuid import uuid4

from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.settings import SettingsStore
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.assessments.document import AssessmentDraft, AssessmentKind
from ergotools.domain.job_catalog import WorkerJobAssignment


def context_values(context: WorkplaceContext) -> tuple[str, ...]:
    """Expose exact workplace identity in reference hierarchy order.

    Args:
        context: Validated five-part workplace including shift.

    Returns:
        Plant, section, line, station and shift identifiers; no translation or units.
    """
    return (
        context.plant_name,
        context.section_name,
        context.line_name,
        context.station_id,
        context.shift_id,
    )


@dataclass(frozen=True, slots=True)
class AssessmentView:
    """Selected view, independent of whether an assessment has been saved.

    Attributes:
        worker_id: Exact selected worker identity, including workers without data.
        kind: Active ergonomic tool.
        workplace: Selected workplace, or None when no context is available.
        assignment_id: Exact workplace owner, or None for standalone views and for
            unavailable workplace assignments. A standalone view remains writable.
        document_id: Saved or in-memory preview identity.
        saved: Whether this exact view has persisted assessment data.
        job: Classified Job ID/name, or None for unclassified data.
    """

    worker_id: str
    kind: AssessmentKind
    workplace: WorkplaceContext | None
    assignment_id: int | None
    document_id: str
    saved: bool
    job: tuple[str, str] | None


class AssessmentNavigation:
    """Resolve views and remembered contexts for one integrated application host."""

    def __init__(
        self,
        workspace: ProjectWorkspace[AssessmentDraft],
        settings: SettingsStore | None,
    ) -> None:
        """Borrow project and preference owners without accessing storage.

        Args:
            workspace: Application-owned session and transactional persistence owner.
            settings: Per-user context preferences; None keeps memory only.

        Returns:
            None; start with no selected view.
        """
        self.workspace = workspace
        self.settings = settings
        self.view: AssessmentView | None = None
        self._previews: dict[
            tuple[str, str, AssessmentKind, WorkplaceContext | None], str
        ] = {}
        self._memory: dict[tuple[str, str, str], tuple[str, ...]] = {}

    def _classified(self, assignment: WorkerJobAssignment) -> bool:
        """Check whether optional Job classification permits editing this ownership.

        Args:
            assignment: Active or historical saved workplace owner; a Job is optional.

        Returns:
            True when no Job is selected, or its placement remains available. Closed
            historical sources retain the existing saved-data browser's edit behavior.
        """
        return assignment.placement_id is None or any(
            p.placement_id == assignment.placement_id and p.active
            for p in self.workspace.read_jobs().jobs.placements
        )

    def _eligible(self, assignment: WorkerJobAssignment) -> bool:
        """Check whether an assignment can own a newly created assessment.

        Args:
            assignment: Saved candidate assignment and its exact workplace/shift.

        Returns:
            True for active workplace assignments with no Job or an available placement.
        """
        return assignment.active and self._classified(assignment)

    def saved_contexts(
        self, worker_id: str, kind: AssessmentKind
    ) -> tuple[WorkplaceContext, ...]:
        """List saved current contexts, including readable unclassified assessments.

        Args:
            worker_id: Exact worker identity.
            kind: Requested ergonomic tool; other tools do not qualify.

        Returns:
            Unique contexts ordered by case-insensitive full workplace identity.
        """
        jobs = self.workspace.read_jobs().jobs
        owners = {
            e.assignment_id
            for e in self.workspace.read_history().history.entries
            if e.kind is kind
        }
        return tuple(
            sorted(
                {
                    a.worker.workplace
                    for a in jobs.assignments
                    if a.worker.worker_id == worker_id and a.assignment_id in owners
                },
                key=lambda p: tuple(v.casefold() for v in context_values(p)),
            )
        )

    def _remembered(
        self, worker_id: str, kind: AssessmentKind
    ) -> tuple[str, ...] | None:
        """Read the last-used context for this exact project, worker and tool.

        Args:
            worker_id: Selected worker identity.
            kind: Selected tool identity.

        Returns:
            Five stored identifiers, or None; callers revalidate against current data.
        """
        metadata = self.workspace.project_metadata
        assert metadata is not None
        key = (metadata.project_id, worker_id, kind.value)
        if self.settings is not None:
            for row in self.settings.load().assessment_contexts:
                if row[:3] == key:
                    return row[3:]
        return self._memory.get(key)

    def remember(self) -> None:
        """Persist the selected valid context outside project/scientific storage.

        Args:
            None.

        Returns:
            None; no preference is written for context-free or unclassified previews.
        """
        view = self.view
        metadata = self.workspace.project_metadata
        if view is None or view.workplace is None or metadata is None:
            return
        if not view.saved and view.assignment_id is None:
            return
        key = (metadata.project_id, view.worker_id, view.kind.value)
        values = context_values(view.workplace)
        self._memory[key] = values
        if self.settings is not None:
            settings = self.settings.load()
            rows = tuple(row for row in settings.assessment_contexts if row[:3] != key)
            updated = (*rows, (*key, *values))
            if (*key, *values) not in settings.assessment_contexts:
                self.settings.save(replace(settings, assessment_contexts=updated))

    def select_worker_default(
        self, worker_id: str, kind: AssessmentKind, blank: Callable[[], AssessmentDraft]
    ) -> AssessmentView:
        """Open standalone first, otherwise the alphabetically first saved workplace.

        Args:
            worker_id: Exact worker selected by the main navigation controls.
            kind: Active tool; other tools never supply fallback locations.
            blank: Deferred standalone factory used only if no saved source exists.

        Returns:
            Existing standalone or exact saved workplace source, otherwise an unsaved
            standalone preview. Remembered contexts do not override this worker default.

        Raises:
            KeyError: The worker is absent from the project.
            RuntimeError: No project is open or a transition is active.
            ValueError: Ownership or preview validation fails.
        """
        history = self.workspace.read_history().history
        if history.standalone_for(worker_id, kind) is not None:
            return self.select(worker_id, kind, blank, explicit=True)
        assignments = {
            a.assignment_id: a for a in self.workspace.read_jobs().jobs.assignments
        }
        sources = sorted(
            (
                (e, assignments[e.assignment_id])
                for e in history.entries
                if e.worker_id == worker_id
                and e.kind is kind
                and e.assignment_id is not None
            ),
            key=lambda pair: (
                tuple(v.casefold() for v in context_values(pair[1].worker.workplace)),
                not pair[1].active,
                pair[1].assignment_id,
                pair[0].document_id,
            ),
        )
        if not sources:
            return self.select(worker_id, kind, blank, explicit=True)
        entry, owner = sources[0]
        return self.select(
            worker_id,
            kind,
            blank,
            workplace=owner.worker.workplace,
            assignment_id=entry.assignment_id,
            explicit=True,
        )

    def select(
        self,
        worker_id: str,
        kind: AssessmentKind,
        blank: Callable[[], AssessmentDraft],
        *,
        workplace: WorkplaceContext | None = None,
        keep: bool = False,
        explicit: bool = False,
        assignment_id: int | None = None,
    ) -> AssessmentView:
        """Select saved data or a deferred preview without moving/copying assessments.

        Args:
            worker_id: Exact worker; missing assessment data never blocks navigation.
            kind: Requested ergonomic tool.
            blank: Factory producing a fresh typed source in the host's display units.
            workplace: Explicit requested context, or the current context for Keep mode.
            keep: Preserve workplace across workers/tools; otherwise restore remembered
                valid context then first saved context.
            explicit: Treat workplace as the exact picker choice, including a New
                context.
            assignment_id: Exact picker owner; None resolves the worker/workplace.

        Returns:
            Selected view; drafts and undo history are retained by workspace identity.

        Raises:
            KeyError: Worker is absent from the current project.
            RuntimeError: No project is open or a workspace transition is active.
            ValueError: Preview ownership validation fails.
        """
        hierarchy = self.workspace.read_hierarchy().hierarchy.work
        if not any(w.worker_id == worker_id for w in hierarchy.workers):
            raise KeyError(worker_id)
        saved = self.saved_contexts(worker_id, kind)
        if not explicit and (not keep or workplace is None):
            remembered = self._remembered(worker_id, kind)
            workplace = next(
                (p for p in saved if context_values(p) == remembered),
                saved[0] if saved else None,
            )
        jobs = self.workspace.read_jobs().jobs
        assignments = tuple(
            a
            for a in jobs.assignments
            if a.worker.worker_id == worker_id and a.worker.workplace == workplace
        )
        entries = tuple(
            e
            for e in self.workspace.read_history().history.entries
            if e.kind is kind
            and e.worker_id == worker_id
            and (
                (workplace is None and e.assignment_id is None)
                or any(a.assignment_id == e.assignment_id for a in assignments)
            )
        )
        if (
            assignment_id is None
            and keep
            and self.view is not None
            and self.view.worker_id == worker_id
        ):
            previous = next(
                (
                    e
                    for e in self.workspace.read_history().history.entries
                    if e.document_id == self.view.document_id
                ),
                None,
            )
            assignment_id = previous.assignment_id if previous is not None else None
        owner = next((a for a in assignments if a.assignment_id == assignment_id), None)
        if owner is None:
            owner = next((a for a in assignments if self._eligible(a)), None)
        fallback = (
            None
            if owner is not None and (explicit or keep)
            else (entries[0] if entries else None)
        )
        entry = next(
            (
                e
                for e in entries
                if owner is not None and e.assignment_id == owner.assignment_id
            ),
            fallback,
        )
        if entry is not None and entry.assignment_id is not None:
            owner = next(
                a for a in assignments if a.assignment_id == entry.assignment_id
            )
        eligible = workplace is None or (
            owner is not None
            and (self._classified(owner) if entry else self._eligible(owner))
        )
        key = (hierarchy.project_id, worker_id, kind, workplace)
        if entry is None and any(
            e.document_id == self._previews.get(key)
            for e in self.workspace.read_history().history.entries
        ):
            # An explicitly associated standalone source retains its old identity.
            # A later standalone preview must receive a new, unused document identity.
            self._previews.pop(key, None)
        document_id = (
            entry.document_id
            if entry is not None
            else self._previews.setdefault(key, uuid4().hex)
        )
        pending = (
            AssignmentAssessment(
                document_id, owner.assignment_id if owner else None, kind, worker_id
            )
            if entry is None and eligible
            else None
        )
        self.workspace.browse_document(
            document_id,
            initial=None if entry else blank(),
            entry=pending,
            readonly=not eligible,
        )
        job = None
        if eligible and owner is not None and owner.placement_id is not None:
            placement = next(
                p for p in jobs.placements if p.placement_id == owner.placement_id
            )
            job_record = next(j for j in jobs.jobs if j.job_id == placement.job_id)
            job = (job_record.job_id, job_record.name)
        self.view = AssessmentView(
            worker_id,
            kind,
            workplace,
            owner.assignment_id if eligible and owner else None,
            document_id,
            entry is not None,
            job,
        )
        self.remember()
        return self.view

    def adopt_active(self) -> None:
        """Synchronize navigation after Search or another explicit saved-source action.

        Args:
            None.

        Returns:
            None; preserve saved assessment, source edits and ownership. An unbound
            diagnostic source clears the browsing view instead of inventing an owner.
        """
        active = self.workspace.active
        if active is None:
            self.view = None
            return
        entry = next(
            (
                e
                for e in self.workspace.read_history().history.entries
                if e.document_id == active.document.document_id
            ),
            None,
        )
        if entry is None:
            if (
                self.view is None
                or self.view.document_id != active.document.document_id
            ):
                self.view = None
            return
        jobs = self.workspace.read_jobs().jobs
        owner = next(
            (a for a in jobs.assignments if a.assignment_id == entry.assignment_id),
            None,
        )
        eligible = owner is None or self._classified(owner)
        job = None
        if eligible and owner is not None and owner.placement_id is not None:
            placement = next(
                p for p in jobs.placements if p.placement_id == owner.placement_id
            )
            record = next(j for j in jobs.jobs if j.job_id == placement.job_id)
            job = (record.job_id, record.name)
        self.workspace.browse_document(entry.document_id, readonly=not eligible)
        self.view = AssessmentView(
            entry.worker_id,
            entry.kind,
            owner.worker.workplace if owner is not None else None,
            owner.assignment_id if eligible and owner is not None else None,
            entry.document_id,
            True,
            job,
        )
        self.remember()

    def overlay_sources(self) -> tuple[AssessmentDraft, ...]:
        """Read all tools for the selected assignment without navigating or saving.

        Args:
            None.

        Returns:
            Active assessment plus sibling-tool sources for the exact assignment.
            Retained edited sources win over saved sources; unrelated Jobs are excluded.
        """
        view = self.view
        active = self.workspace.active
        if view is None or active is None:
            return ()
        entries = self.workspace.read_history().history.entries
        owner = view.assignment_id
        if owner is None:
            entry = next(
                (e for e in entries if e.document_id == view.document_id), None
            )
            owner = entry.assignment_id if entry is not None else None
        sources = [active.state]
        if owner is not None or view.workplace is None:
            sources.extend(
                self.workspace.assessment_source(e.document_id)
                for e in entries
                if e.assignment_id == owner
                and e.worker_id == view.worker_id
                and e.kind is not view.kind
            )
        return tuple(sources)

    def duplicate_locations(
        self, entry: AssignmentAssessment
    ) -> tuple[WorkplaceContext, ...]:
        """Find other saved locations for the same worker, tool and classified Job.

        Args:
            entry: Deferred classified assessment being considered for first Save.

        Returns:
            Existing different workplaces requiring confirmation; other Jobs/tools
            and the same workplace are excluded.
        """
        if entry.assignment_id is None:
            return ()
        jobs = self.workspace.read_jobs().jobs
        owner = next(
            a for a in jobs.assignments if a.assignment_id == entry.assignment_id
        )
        return self.duplicate_workplace_locations(
            owner.worker.worker_id,
            entry.kind,
            owner.worker.workplace,
            owner.placement_id,
        )

    def duplicate_workplace_locations(
        self,
        worker_id: str,
        kind: AssessmentKind,
        workplace: WorkplaceContext,
        placement_id: int | None,
    ) -> tuple[WorkplaceContext, ...]:
        """Find same-Job observations before a proposed assignment is inserted.

        Args:
            worker_id: Saved worker whose independent observations are being created.
            kind: Current tool; other tools do not require duplicate-location consent.
            workplace: Proposed exact station/shift, excluded from other observations.
            placement_id: Optional saved Job placement; None needs no warning.

        Returns:
            Sorted existing locations for this worker/tool/Job, without writing data.

        Raises:
            KeyError: The proposed Job placement is absent from the saved catalog.
        """
        if placement_id is None:
            return ()
        jobs = self.workspace.read_jobs().jobs
        placement = next(
            (p for p in jobs.placements if p.placement_id == placement_id), None
        )
        if placement is None:
            raise KeyError(placement_id)
        placements = {
            p.placement_id for p in jobs.placements if p.job_id == placement.job_id
        }
        saved = {
            e.assignment_id
            for e in self.workspace.read_history().history.entries
            if e.kind is kind
        }
        return tuple(
            sorted(
                {
                    a.worker.workplace
                    for a in jobs.assignments
                    if a.assignment_id in saved
                    and a.placement_id in placements
                    and a.worker.worker_id == worker_id
                    and a.worker.workplace != workplace
                },
                key=context_values,
            )
        )

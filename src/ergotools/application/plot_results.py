"""Saved PLOT result selection, preserving active ownership and absent evidence.

Application layer. Prepare immutable analysis/history values through injected ports. Qt
controls, chart rendering, SQL transactions and user consent remain outside this module;
only explicitly supplied persistence callbacks can write.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from ergotools.application.assessment_export import (
    AssignedSummaryExportRow,
    ExportRepository,
    saved_assigned_summary,
)
from ergotools.application.saved_results import stored_result
from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_catalog import Job, JobPlacement
from ergotools.domain.job_risk import (
    JobRiskCatalog,
    JobRiskMeasurement,
    JobRiskValues,
)
from ergotools.domain.plot_filters import PlotFilterSelection
from ergotools.domain.plot_positions import PlotPositions
from ergotools.domain.plot_scope import PlotScope
from ergotools.domain.work_catalog import WorkerEntry
from ergotools.domain.work_hierarchy import WorkHierarchy


class PlotWorkerOrder(StrEnum):
    """Reference binary worker-ID or last-name ordering, independent of locale."""

    # Binary worker-ID ordering matches the original query, independent of locale.
    WORKER_ID = "worker_id"
    # Binary saved last-name ordering, with worker identity as a stable tie-breaker.
    LAST_NAME = "last_name"


class PlotResultRepository(ExportRepository, Protocol):
    """Read-only project capabilities needed by the original PLOT datasets."""

    def load_hierarchy(self) -> WorkHierarchy:
        """Return saved workers, complete workplace identities and shifts.

        Read-only capability; repository failures propagate.

        Args:
            None.

        Returns:
            Saved workers, complete station identities and independent shifts.
        """
        ...

    def load_job_risk(self) -> JobRiskCatalog:
        """Return validated job current_values without approval or implicit migration.

        No approval, unit conversion or implicit migration.

        Args:
            None.

        Returns:
            Validated recorded current values and measurements.
        """
        ...

    def load_plot_positions(self) -> PlotPositions:
        """Return saved marker/anchor geometry; older formats contain no positions.

        No fallback geometry or project write.

        Args:
            None.

        Returns:
            Saved worker-marker/station-anchor geometry; no positions for older formats
            lacking the capability.
        """
        ...


@dataclass(frozen=True, slots=True)
class PlotJobRisk:
    """Current Job values and the exact complete tool measurement.

    Attributes:
        values: Single current Job risk set; no version or evidence lifecycle.
        measurement: Recorded model risk/damage; missing quantities remain None.
    """

    values: JobRiskValues
    measurement: JobRiskMeasurement


@dataclass(frozen=True, slots=True)
class PlotWorkerResult:
    """One active assignment current tool version and optional job evidence.

    Attributes:
        worker: Literal worker display/demographic details.
        assessment: Saved current-version summary with original assignment ownership.
        placement: Linked placement, or None when unclassified.
        job: Linked job, or None when unclassified.
        job_risk: Current approved measurement for that model, or None.
    """

    worker: WorkerEntry
    assessment: AssignedSummaryExportRow
    placement: JobPlacement | None
    job: Job | None
    job_risk: PlotJobRisk | None


@dataclass(frozen=True, slots=True)
class PlotJobResult:
    """One active placed job; worker counts ignore demographic/model filters.

    Attributes:
        placement: Exact active workplace placement.
        job: Exact active job display record.
        assigned_worker_count: All active assignments linked to the placement, including
            workers without this tool.
        risk: Current complete selected-tool Job measurement, or None.
    """

    placement: JobPlacement
    job: Job
    assigned_worker_count: int
    risk: PlotJobRisk | None


@dataclass(frozen=True, slots=True)
class PlotResults:
    """Complete saved PLOT dataset.

    Job rows ignore worker demographic constraints; absent assessment evidence remains
    absent.

    Attributes:
        selection: Exact applied hierarchy/model/mode/demographic predicates.
        workers: Selected-tool current active-assignment rows in requested worker order.
        all_tools: All-model current rows for cross-tool summaries.
        jobs: Active scoped job placements in deterministic workplace order.
        positions: Saved original-image geometry; no manufactured positions.
    """

    selection: PlotFilterSelection
    workers: tuple[PlotWorkerResult, ...]
    all_tools: tuple[PlotWorkerResult, ...]
    jobs: tuple[PlotJobResult, ...]
    positions: PlotPositions


def _in_scope(scope: PlotScope, place: WorkplaceContext) -> bool:
    """Pure identity predicate; captions and geometry are irrelevant.

    Args:
        scope: Selected plant/hierarchy prefixes and optional exact shift.
        place: Full workplace identity to test.

    Returns:
        True when a selected path prefix and optional shift match.
    """
    path = (place.plant_name, place.section_name, place.line_name, place.station_id)
    return (scope.shift is None or scope.shift == place.shift_id) and any(
        path[: len(prefix)] == prefix for prefix in scope.paths
    )


def saved_plot_results(
    repository: PlotResultRepository,
    selection: PlotFilterSelection,
    *,
    current_year: int,
    order: PlotWorkerOrder = PlotWorkerOrder.WORKER_ID,
) -> PlotResults:
    """Load complete saved datasets before the caller publishes an Apply result.

    Use active assessments on active assignments and Job placements, with complete
    current Job values. Counts include all active assigned workers, even those
    without this tool or outside demographic constraints. No date-bound inference,
    editor access, project write or position fallback occurs.

    Repository failures propagate before publication. No date inference, unsaved editor
    access, geometry fallback or write occurs.

    Args:
        repository: Borrowed same-project saved-source, catalog and geometry readers.
        selection: Validated exact hierarchy/tool/mode and demographic predicates.
        current_year: Positive integer calendar year for original birth-year age
            filtering.
        order: Original binary worker-ID or last-name order, independent of UI language.

    Returns:
        Complete validated dataset for atomic caller publication, including
        selected-tool workers, all-tool rows, placed jobs and saved geometry.

    Raises:
        ValueError: Selection/year/order, catalog ownership/references or source
            evidence is invalid.
    """
    if (
        not isinstance(selection, PlotFilterSelection)
        or not isinstance(order, PlotWorkerOrder)
        or type(current_year) is not int
        or current_year < 1
    ):
        raise ValueError("PLOT requires typed filters/order and a positive year.")
    metadata = repository.metadata
    hierarchy = repository.load_hierarchy()
    selection.scope.validate(hierarchy)
    jobs = repository.load_jobs()
    history = repository.load_history()
    risks = repository.load_job_risk()
    positions = repository.load_plot_positions()
    if metadata.project_id != hierarchy.work.project_id:
        raise ValueError("PLOT hierarchy belongs to another project.")
    jobs.validate_hierarchy(hierarchy)
    history.validate_jobs(jobs)
    risks.validate_jobs(jobs)
    positions.validate(hierarchy, jobs)
    job_by_id = {item.job_id: item for item in jobs.jobs}
    placements = {item.placement_id: item for item in jobs.placements}
    assignments = {item.assignment_id: item for item in jobs.assignments}
    workers = {item.worker_id: item for item in hierarchy.work.workers}
    current_values = {
        values.job_id: values
        for values in risks.values
        if job_by_id[values.job_id].active
    }

    def evidence(job_id: str, kind: AssessmentKind) -> PlotJobRisk | None:
        """No missing evidence is replaced by zero.

        Args:
            job_id: Exact active job identity whose current values is
                considered.
            kind: Model measurement requested from that values.

        Returns:
            Exact current values/measurement pair, or None if either is
            absent.
        """
        values = current_values.get(job_id)
        if values is None:
            return None
        measurement = next(
            (item for item in values.measurements if item.kind is kind), None
        )
        return (
            PlotJobRisk(values, measurement)
            if measurement is not None and measurement.complete
            else None
        )

    all_tools = []
    for entry in history.entries:
        if entry.assignment_id is None:
            continue
        assignment = assignments[entry.assignment_id]
        worker = workers[assignment.worker.worker_id]
        if (
            not assignment.active
            or not _in_scope(selection.scope, assignment.worker.workplace)
            or not selection.demographics.matches(
                worker.details, current_year=current_year
            )
        ):
            continue
        source = repository.load(DocumentKey(metadata.project_id, entry.document_id))
        summary = saved_assigned_summary(
            metadata,
            entry,
            assignment,
            source,
            stored_result(
                repository, DocumentKey(metadata.project_id, entry.document_id), source
            ),
        )
        placement = (
            placements.get(assignment.placement_id)
            if assignment.placement_id is not None
            else None
        )
        job = job_by_id[placement.job_id] if placement is not None else None
        all_tools.append(
            PlotWorkerResult(
                worker,
                summary,
                placement,
                job,
                evidence(job.job_id, entry.kind) if job is not None else None,
            )
        )
    all_tools.sort(
        key=lambda row: (
            (row.worker.last_name or "")
            if order is PlotWorkerOrder.LAST_NAME
            else row.worker.worker_id,
            row.worker.worker_id,
            row.assessment.assignment_id,
            row.assessment.kind.value,
        )
    )
    counts: dict[int, int] = {}
    for assignment in jobs.assignments:
        if assignment.active and assignment.placement_id is not None:
            counts[assignment.placement_id] = counts.get(assignment.placement_id, 0) + 1
    placed_jobs = tuple(
        PlotJobResult(
            placement,
            job_by_id[placement.job_id],
            counts.get(placement.placement_id, 0),
            evidence(placement.job_id, selection.tool),
        )
        for placement in sorted(
            jobs.placements,
            key=lambda item: (
                item.workplace.plant_name,
                item.workplace.section_name,
                item.workplace.line_name,
                item.workplace.station_id,
                item.workplace.shift_id,
                item.job_id,
            ),
        )
        if placement.active
        and job_by_id[placement.job_id].active
        and _in_scope(selection.scope, placement.workplace)
    )
    return PlotResults(
        selection,
        tuple(row for row in all_tools if row.assessment.kind is selection.tool),
        tuple(all_tools),
        placed_jobs,
        positions,
    )

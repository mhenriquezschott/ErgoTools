"""Read-only summary export from saved current assignment assessments.

Application layer. Prepare immutable analysis/history values through injected ports. Qt
controls, chart rendering, SQL transactions and user consent remain outside this module;
only explicitly supplied persistence callbacks can write.
"""

from dataclasses import dataclass
from typing import Protocol

from ergotools.application.assessments.evaluation import (
    AssessmentEvaluator,
    EvaluationStatus,
)
from ergotools.application.historical_results import (
    HistoricalAssessmentResult,
)
from ergotools.application.saved_results import stored_result
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessment_history import AssessmentHistory, AssignmentAssessment
from ergotools.domain.assessments.context import WorkerContext, WorkplaceContext
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    assessment_kind,
)
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.job_catalog import JobCatalog, WorkerJobAssignment
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata


class ExportRepository(Protocol):
    """Read-only saved-source contract; no active editor or write capability."""

    @property
    def metadata(self) -> ProjectMetadata:
        """Return the project's stable identity and recorded unit defaults.

        Read only; no editor or project write capability.

        Args:
            None.

        Returns:
            Stable project identity and recorded source-unit defaults.
        """
        ...

    def load_history(self) -> AssessmentHistory:
        """Return validated persisted ownership.

        No unsaved editor substitution or persistence.

        Args:
            None.

        Returns:
            Validated saved assignment/tool ownership.
        """
        ...

    def load_jobs(self) -> JobCatalog:
        """Return saved assignments, including historical closed assignments.

        No reassignment or history pruning.

        Args:
            None.

        Returns:
            Saved assignments including closed historical rows.
        """
        ...

    def load(self, document: DocumentKey) -> AssessmentDraft:
        """Return one persisted source, without substituting unsaved editor data.

        Storage failures propagate; never return unsaved editor inputs.

        Args:
            document: Exact project/document identity of a saved assessment.

        Returns:
            Validated persisted source inputs with recorded units and ST convention.
        """
        ...


@dataclass(frozen=True, slots=True)
class StandaloneAssessmentOwner:
    """Worker-only export identity; absent workplace is never a manufactured context.

    Attributes:
        project_id: Stable project identity of the saved assessment.
        worker_id: Exact assessed worker identity.
        workplace: Always absent for a standalone assessment.
    """

    project_id: str
    worker_id: str
    workplace: WorkplaceContext | None = None


@dataclass(frozen=True, slots=True)
class SummaryExportRow:
    """One saved assessment with exact ownership and explicit evaluation state.

    Damage is dimensionless; probability is 0-1. None means unavailable. Saved percent
    is retained to avoid divide/multiply rounding during export, not as a second stored
    result.

    Attributes:
        document: Exact project/document identity.
        owner: Assessed worker identity and optional original workplace ownership.
        kind: Scientific model identity.
        assignment_id: Original workplace assignment, or None for standalone data.
        assignment_active: Whether the original assignment is still active.
        units: Recorded source units, or DUET project defaults.
        status: Explicit complete/partial/failed scientific state.
        total_damage: Dimensionless cumulative damage, or None.
        probability: High-risk probability on 0-1 scale, or None.
        issue_keys: Stable issue keys for unfinished or invalid rows.
        recorded_probability_percent: Exact sole saved result percent when available;
            otherwise None.
        recorded_unit_label: Exact saved result unit label when available; otherwise
            None.
    """

    document: DocumentKey
    owner: WorkerContext | StandaloneAssessmentOwner
    kind: AssessmentKind
    assignment_id: int | None
    assignment_active: bool
    units: MeasurementSystem
    status: EvaluationStatus
    total_damage: float | None
    probability: float | None
    issue_keys: tuple[str, ...]
    recorded_probability_percent: float | None = None
    recorded_unit_label: str | None = None


@dataclass(frozen=True, slots=True)
class AssignedSummaryExportRow(SummaryExportRow):
    """Station-based summary with validated mandatory assignment and workplace.

    Attributes:
        owner: Exact worker/workplace identity; standalone owners are excluded.
        assignment_id: Saved assignment identity required by PLOT geometry and scope.
    """

    owner: WorkerContext
    assignment_id: int


def saved_assessment_summary(
    metadata: ProjectMetadata,
    entry: AssignmentAssessment,
    assignment: WorkerJobAssignment | None,
    source: AssessmentDraft,
    recorded_result: HistoricalAssessmentResult | None = None,
) -> SummaryExportRow:
    """Read one saved source with explicit ownership and result provenance.

    Args:
        metadata: Project identity and DUET default unit label.
        entry: Exact assessment assignment/tool ownership.
        assignment: Matching saved workplace assignment, or None for standalone data.
        source: Persisted task inputs, units and ST direction convention.
        recorded_result: Sole saved calculation; only an exact source match is used.

    Returns:
        Source-bound summary retaining full-precision saved percent and damage.
        If no matching saved output exists, evaluate persisted inputs read-only;
        never reuse stale output or store an additional result. Invalid outcomes
        remain explicit with absent quantities. Editor inputs are not committed.

    Damage is dimensionless and probability is 0-1. No source units, approved job
    estimates, input history or scientific formulas are changed.

    Raises:
        ValueError: If assignment/project/model identities disagree.
    """
    if (
        (
            assignment is not None
            and (
                assignment.worker.project_id != metadata.project_id
                or entry.worker_id != assignment.worker.worker_id
            )
        )
        or entry.assignment_id
        != (assignment.assignment_id if assignment is not None else None)
        or assessment_kind(source) is not entry.kind
    ):
        raise ValueError("Saved result ownership or assessment model does not match.")
    key = DocumentKey(metadata.project_id, entry.document_id)
    recorded = recorded_result is not None and recorded_result.source == source
    recorded_percent = None
    recorded_unit_label = None
    units = (
        source.system
        if isinstance(source, (LifftDraft, TstDraft))
        else metadata.default_units
    )
    if recorded and recorded_result is not None:
        status = recorded_result.calculation_status or EvaluationStatus.RECORDED
        damage = recorded_result.damage
        recorded_percent = recorded_result.probability_percent
        recorded_unit_label = recorded_result.unit_label
        if recorded_unit_label in ("Metric", "Imperial"):
            units = MeasurementSystem(recorded_unit_label.lower())
        probability = None if recorded_percent is None else recorded_percent / 100
        issue_keys: tuple[str, ...] = recorded_result.issue_keys
    else:
        session: DocumentSession[AssessmentDraft] = DocumentSession(
            key, source, persisted=True
        )
        evaluator = AssessmentEvaluator()
        outcome = (
            evaluator.evaluate_lifft_grid(session)
            if isinstance(source, LifftDraft)
            else evaluator.evaluate_duet_grid(session)
            if isinstance(source, DuetDraft)
            else evaluator.evaluate_tst_grid(session)
        )
        summary = outcome.summary
        status = outcome.status
        damage = summary.total_damage if summary is not None else None
        probability = summary.probability if summary is not None else None
        issue_keys = tuple(issue.code for issue in outcome.issues)
    return SummaryExportRow(
        key,
        assignment.worker
        if assignment is not None
        else StandaloneAssessmentOwner(metadata.project_id, entry.worker_id),
        entry.kind,
        entry.assignment_id,
        assignment.active if assignment is not None else False,
        units,
        status,
        damage,
        probability,
        issue_keys,
        recorded_percent,
        recorded_unit_label,
    )


def saved_summary_rows(
    repository: ExportRepository, kind: AssessmentKind
) -> tuple[SummaryExportRow, ...]:
    """Export saved assessments of one tool, retaining historical ownership.

    No project writes, editor commits or display-unit conversions occur. Grid evaluation
    retains completed-row totals with explicit partial status; invalid and review
    outcomes have absent results. Exact saved source/result matches export their sole
    calculated output, without rounding or gauge clipping. They are never relabeled as
    fresh calculations; edited sources use the evaluator. Unrelated tools are
    excluded. Closed assignments are retained; exporting never reattaches their
    assessments to a newer assignment.

    Repository read/decode failures propagate. A matching sole saved calculation is
    used; otherwise persisted inputs are evaluated read-only. No additional result is
    written.

    Args:
        repository: Borrowed saved-source repository; optional saved-result capability
            is detected by stored_result.
        kind: Scientific model whose saved assessments are exported.

    Returns:
        Saved assessment summaries in exact workplace/worker/assignment order;
        closed assignments remain attached to their original owners.

    Raises:
        KeyError: Saved history refers to an absent assignment.
        ValueError: Saved ownership, model or source validation fails.
    """
    metadata = repository.metadata
    jobs = {item.assignment_id: item for item in repository.load_jobs().assignments}
    rows = []
    for entry in repository.load_history().entries:
        if entry.kind is not kind:
            continue
        assignment = (
            jobs.get(entry.assignment_id) if entry.assignment_id is not None else None
        )
        key = DocumentKey(metadata.project_id, entry.document_id)
        source = repository.load(key)
        archived = stored_result(repository, key, source)
        rows.append(
            saved_assessment_summary(metadata, entry, assignment, source, archived)
        )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.owner.workplace.plant_name
                if row.owner.workplace is not None
                else "",
                row.owner.workplace.section_name
                if row.owner.workplace is not None
                else "",
                row.owner.workplace.line_name
                if row.owner.workplace is not None
                else "",
                row.owner.workplace.station_id
                if row.owner.workplace is not None
                else "",
                row.owner.workplace.shift_id if row.owner.workplace is not None else "",
                row.owner.worker_id,
                row.assignment_id if row.assignment_id is not None else -1,
            ),
        )
    )


def saved_assigned_summary(
    metadata: ProjectMetadata,
    entry: AssignmentAssessment,
    assignment: WorkerJobAssignment,
    source: AssessmentDraft,
    recorded_result: HistoricalAssessmentResult | None = None,
) -> AssignedSummaryExportRow:
    """Project saved scientific evidence into a station-based analysis row.

    Args:
        metadata: Same-project metadata and unit defaults.
        entry: Assessment linked to the supplied real workplace assignment.
        assignment: Exact worker/workplace/shift; a Job placement is optional.
        source: Persisted task inputs with recorded units.
        recorded_result: Optional matching sole saved calculation.

    Returns:
        Validated summary with mandatory workplace and assignment identities. The
        shared calculation/result policy is identical to standalone export.

    Raises:
        ValueError: Source, model, project or worker ownership is inconsistent.
    """
    row = saved_assessment_summary(metadata, entry, assignment, source, recorded_result)
    return AssignedSummaryExportRow(
        row.document,
        assignment.worker,
        row.kind,
        assignment.assignment_id,
        row.assignment_active,
        row.units,
        row.status,
        row.total_damage,
        row.probability,
        row.issue_keys,
        row.recorded_probability_percent,
        row.recorded_unit_label,
    )

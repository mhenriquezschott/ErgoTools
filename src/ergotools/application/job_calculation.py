"""Current Job calculator operations using the established assessment evaluator.

Application layer. Immutable task edits invalidate outputs, Calculate uses the same
scientific path as worker assessments, and copying preserves exact matching outputs.
No UI, repository, profile lifecycle or alternate calculation implementation lives here.
"""

from dataclasses import replace
from uuid import uuid4

from ergotools.application.assessments.evaluation import EvaluationStatus
from ergotools.application.historical_results import HistoricalAssessmentResult
from ergotools.application.saved_results import calculate_saved_result
from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    assessment_kind,
    task_has_data,
)
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDirectionConvention, TstDraft
from ergotools.domain.job_risk import JobRiskMeasurement, JobTaskResult
from ergotools.domain.model_units import MeasurementSystem


def blank_job_source(kind: AssessmentKind, units: MeasurementSystem) -> AssessmentDraft:
    """Start one blank task without an assessment owner or artificial worker.

    Args:
        kind: Explicit LiFFT/DUET/ST identity.
        units: Initial source units; copied sources retain their own units instead.

    Returns:
        One independent blank task; new ST sources use the established UI convention.
    """
    if kind is AssessmentKind.LIFFT:
        return LifftDraft(units, (LifftTask(uuid4().hex),))
    if kind is AssessmentKind.DUET:
        return DuetDraft((DuetTask(uuid4().hex, 0),))
    return TstDraft(
        units,
        (TstTask(uuid4().hex, TstDirection.HANDLING_LOADS),),
        TstDirectionConvention.REFERENCE_UI,
    )


def resize_job_source(
    source: AssessmentDraft, *, remove: int | None = None
) -> AssessmentDraft:
    """Append one blank task or remove an explicitly selected task, preserving others.

    Args:
        source: Current immutable calculator source with 1-100 tasks.
        remove: Zero-based selected task to remove, or None to append one.

    Returns:
        Replacement source with stable retained task identities, units and convention.

    Raises:
        ValueError: Capacity or selected removal index would be invalid.
    """
    if remove is not None and (
        len(source.tasks) <= 1 or not 0 <= remove < len(source.tasks)
    ):
        raise ValueError("Select a task; at least one task must remain.")
    if remove is None and len(source.tasks) >= 100:
        raise ValueError("At most 100 tasks are allowed.")
    if isinstance(source, LifftDraft):
        return replace(
            source,
            tasks=(*source.tasks, LifftTask(uuid4().hex))
            if remove is None
            else tuple(t for i, t in enumerate(source.tasks) if i != remove),
        )
    if isinstance(source, DuetDraft):
        return replace(
            source,
            tasks=(*source.tasks, DuetTask(uuid4().hex, 0))
            if remove is None
            else tuple(t for i, t in enumerate(source.tasks) if i != remove),
        )
    return replace(
        source,
        tasks=(*source.tasks, TstTask(uuid4().hex, TstDirection.HANDLING_LOADS))
        if remove is None
        else tuple(t for i, t in enumerate(source.tasks) if i != remove),
    )


def job_measurement_from_result(
    source: AssessmentDraft, result: HistoricalAssessmentResult | None
) -> JobRiskMeasurement:
    """Copy exact source/results without recalculation or worker ownership links.

    Args:
        source: Exact retained worker or Job task inputs, including original units.
        result: Its current complete calculation, never an unrelated or stale output.

    Returns:
        Independent current Job/tool measurement containing tasks and exact totals.

    Raises:
        ValueError: Result is missing, stale, partial or lacks usable probabilities.
    """
    if (
        result is None
        or result.source != source
        or result.calculation_status is not EvaluationStatus.COMPLETE
        or result.probability_percent is None
    ):
        raise ValueError("Calculate a complete assessment before using its values.")
    return JobRiskMeasurement(
        assessment_kind(source),
        result.damage,
        result.probability_percent,
        result.unit_label,
        source,
        tuple(
            JobTaskResult(row.moment, row.damage, row.share_percent)
            for row in result.tasks
        ),
    )


def calculate_job_measurement(
    project_id: str, job_id: str, source: AssessmentDraft, units: MeasurementSystem
) -> JobRiskMeasurement:
    """Calculate a Job through the established worker-grid evaluator and precision.

    Args:
        project_id: Exact project identity for the temporary evaluation session.
        job_id: Real Job identity; no worker assessment is created.
        source: Current independent tasks and declared ST/unit conventions.
        units: Project display/default units used only for unit-independent DUET.

    Returns:
        Source-bound current measurement with unrounded calculator totals.

    Raises:
        ValueError: Inputs cannot produce a complete current calculation.
    """
    result = calculate_saved_result(
        DocumentKey(project_id, "job:" + job_id), source, units
    )
    return job_measurement_from_result(source, result)


def auto_calculate_job_measurement(
    project_id: str, job_id: str, source: AssessmentDraft, units: MeasurementSystem
) -> JobRiskMeasurement:
    """Evaluate completed Job inputs without exposing incomplete preview totals.

    Args:
        project_id: Current project identity for the detached evaluator.
        job_id: Destination Job identity; creates no worker record or ownership link.
        source: Immutable accepted task inputs with their units and ST convention.
        units: Default display units for unit-independent DUET inputs.

    Returns:
        Complete exact measurement when valid; otherwise inputs with absent outputs.
        Missing rows never invent numeric inputs or cause modal UI warnings.

    Raises:
        ValueError: The source model or declared default unit system is unsupported.
    """
    result = calculate_saved_result(
        DocumentKey(project_id, "job:" + job_id), source, units
    )
    if result is not None and result.calculation_status is EvaluationStatus.COMPLETE:
        return job_measurement_from_result(source, result)
    return JobRiskMeasurement(
        assessment_kind(source),
        source=source,
        unit=(
            source.system if isinstance(source, (LifftDraft, TstDraft)) else units
        ).value.title(),
    )


def copy_job_tasks(
    measurement: JobRiskMeasurement,
    task_ids: tuple[str, ...],
    *,
    project_id: str,
    units: MeasurementSystem,
) -> JobRiskMeasurement:
    """Copy selected inputs with source-matched outputs, never full-source totals.

    Args:
        measurement: Revalidated source Job/worker measurement; never mutated.
        task_ids: Nonempty unique retained identities in any selection order.
        project_id: Open project identity for the existing detached calculator.
        units: Display/default units for unit-independent DUET calculations.

    Returns:
        Original exact measurement when every task is selected. A proper subset keeps
        source order/units/convention and uses the established calculator if the source
        was calculated and selected inputs contain data. Uncalculated/blank selections
        retain inputs only. No project source, worker or repository is created/written.

    Raises:
        ValueError: Missing task source, empty/stale/duplicate selection, or inputs
            that cannot produce a complete calculation.
    """
    source = measurement.source
    if source is None:
        raise ValueError("This source has no task inputs to select.")
    selected = frozenset(task_ids)
    available = frozenset(task.task_id for task in source.tasks)
    if not selected or len(selected) != len(task_ids) or not selected <= available:
        raise ValueError("Select one or more existing source tasks.")
    if selected == available:
        return measurement
    # Replace each concrete source to retain its typed tasks and calculation convention.
    if isinstance(source, LifftDraft):
        subset: AssessmentDraft = replace(
            source, tasks=tuple(t for t in source.tasks if t.task_id in selected)
        )
    elif isinstance(source, DuetDraft):
        subset = replace(
            source, tasks=tuple(t for t in source.tasks if t.task_id in selected)
        )
    else:
        subset = replace(
            source, tasks=tuple(t for t in source.tasks if t.task_id in selected)
        )
    if measurement.complete and any(task_has_data(t) for t in subset.tasks):
        return calculate_job_measurement(project_id, "selected-tasks", subset, units)
    return JobRiskMeasurement(measurement.kind, source=subset)

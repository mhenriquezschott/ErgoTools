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

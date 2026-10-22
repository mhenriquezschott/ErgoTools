"""Current Job/tool ownership, numeric boundaries and immutable source validation.

Tests use synthetic values only; obsolete profile lifecycle is deliberately absent.
"""

from dataclasses import replace

import pytest

from ergotools.application.job_calculation import (
    blank_job_source,
    calculate_job_measurement,
    resize_job_source,
)
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_catalog import Job, JobCatalog
from ergotools.domain.job_risk import JobRiskCatalog, JobRiskMeasurement, JobRiskValues
from ergotools.domain.model_units import MeasurementSystem


@pytest.mark.parametrize("value", (-1, float("nan"), float("inf"), True, "1"))
def test_invalid_risk_values(value: object) -> None:
    """Reject nonfinite, negative and nonnumeric damage/probability without coercion.

    Args:
        value: Deliberately invalid scalar.

    Returns:
        None; both quantities reject it.
    """
    with pytest.raises(ValueError):
        JobRiskMeasurement(AssessmentKind.LIFFT, value, 0)
    with pytest.raises(ValueError):
        JobRiskMeasurement(AssessmentKind.LIFFT, 0, value)


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_current_set_boundaries_and_source(kind: AssessmentKind) -> None:
    """Keep zero distinct from missing and prohibit a different tool's source.

    Args:
        kind: Each maintained calculator identity.

    Returns:
        None; only a matching source is accepted.
    """
    zero = JobRiskMeasurement(kind, 0, 0)
    assert zero.complete and not JobRiskMeasurement(kind).complete
    assert JobRiskMeasurement(kind, 1, 100).complete
    for changes in ({"probability_percent": 100.1}, {"unit": 42}, {"kind": "LiFFT"}):
        with pytest.raises(ValueError):
            replace(zero, **changes)
    source = blank_job_source(kind, MeasurementSystem.METRIC)
    assert JobRiskMeasurement(kind, source=source).source == source
    other = next(k for k in AssessmentKind if k != kind)
    with pytest.raises(ValueError):
        JobRiskMeasurement(other, source=source)
    with pytest.raises(ValueError):
        JobRiskValues("j", (zero, zero))
    current = JobRiskCatalog("p", (JobRiskValues("j", (zero,)),))
    current.validate_jobs(JobCatalog("p", (Job("j", "Job"),)))
    assert current.for_job("absent") == JobRiskValues("absent")
    with pytest.raises(ValueError):
        current.validate_jobs(JobCatalog("foreign", (Job("j", "Job"),)))
    with pytest.raises(ValueError):
        current.validate_jobs(JobCatalog("p"))
    with pytest.raises(ValueError):
        JobRiskCatalog("p", (current.values[0], current.values[0]))


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_task_capacity_and_missing_calculation(kind: AssessmentKind) -> None:
    """Blank rows never fabricate a risk; plus/minus preserve earlier task identities.

    Args:
        kind: Each embedded calculator identity.

    Returns:
        None; one-to-one-hundred capacity and original tasks survive resizing.
    """
    source = blank_job_source(kind, MeasurementSystem.IMPERIAL)
    initial = source.tasks[0]
    with pytest.raises(ValueError):
        resize_job_source(source, remove=0)
    with pytest.raises(ValueError):
        calculate_job_measurement("p", "j", source, MeasurementSystem.IMPERIAL)
    for _ in range(99):
        source = resize_job_source(source)
    assert len(source.tasks) == 100 and source.tasks[0] == initial
    with pytest.raises(ValueError):
        resize_job_source(source)
    shorter = resize_job_source(source, remove=10)
    assert shorter.tasks == source.tasks[:10] + source.tasks[11:]

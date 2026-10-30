"""Independent selected-task copies reuse the established calculator and source units.

Application tests never write project files. Full copies retain exact recorded output;
subsets recompute totals/shares only on explicit copy and never mutate their source.
"""

from dataclasses import replace
from unittest.mock import patch

import pytest

from ergotools.application.job_calculation import (
    blank_job_source,
    calculate_job_measurement,
    copy_job_tasks,
)
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.job_risk import JobRiskMeasurement
from ergotools.domain.model_units import MeasurementSystem


@pytest.mark.parametrize("kind", list(AssessmentKind))
@pytest.mark.parametrize("units", list(MeasurementSystem))
def test_subset_copy_matches_its_own_calculation_and_preserves_full_copy(
    kind: AssessmentKind,
    units: MeasurementSystem,
) -> None:
    """Selected results correspond to selected inputs, including their own shares.

    Args:
        kind: Each supported calculator.
        units: Recorded source/default units; no reinterpretation is permitted.

    Returns:
        None; full-copy identity, subset calculation and source independence hold.
    """
    source = blank_job_source(kind, units)
    if isinstance(source, LifftDraft):
        source = replace(
            source,
            tasks=(
                LifftTask("a", 30, 49, 100),
                LifftTask("b", 40, 60, 300),
                LifftTask("blank"),
            ),
        )
    elif isinstance(source, DuetDraft):
        source = replace(
            source,
            tasks=(DuetTask("a", 6, 100), DuetTask("b", 8, 300), DuetTask("blank", 0)),
        )
    else:
        source = replace(
            source,
            tasks=(
                TstTask("a", TstDirection.HANDLING_LOADS, 30, 49, 100),
                TstTask("b", TstDirection.HANDLING_LOADS, 40, 60, 300),
                TstTask("blank", TstDirection.HANDLING_LOADS),
            ),
        )
    original = calculate_job_measurement("p", "source", source, units)
    with patch(
        "ergotools.application.job_calculation.calculate_job_measurement",
        side_effect=AssertionError("Full copies must retain exact results"),
    ):
        assert (
            copy_job_tasks(original, ("blank", "b", "a"), project_id="p", units=units)
            is original
        )
    selected = copy_job_tasks(original, ("b",), project_id="p", units=units)
    expected_source = replace(source, tasks=(source.tasks[1],))
    expected = calculate_job_measurement("p", "expected", expected_source, units)
    assert selected == expected
    assert len(selected.task_results) == 1
    assert selected.task_results[0].share_percent == 100
    assert original.source == source and len(source.tasks) == 3
    blank = copy_job_tasks(original, ("blank",), project_id="p", units=units)
    assert not blank.complete and blank.source.tasks == (source.tasks[2],)
    assert not blank.task_results
    pending = JobRiskMeasurement(kind, source=source)
    subset = copy_job_tasks(pending, ("a",), project_id="p", units=units)
    assert not subset.complete and subset.source.tasks == (source.tasks[0],)
    for invalid in ((), ("missing",), ("a", "a")):
        with pytest.raises(ValueError, match="Select"):
            copy_job_tasks(original, invalid, project_id="p", units=units)
    with pytest.raises(ValueError, match="no task"):
        copy_job_tasks(
            JobRiskMeasurement(kind, 0, 0), ("a",), project_id="p", units=units
        )

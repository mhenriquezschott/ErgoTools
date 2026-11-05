"""Independent arithmetic expectations for frozen guided rotation comparisons.

Pure synthetic evidence covers missing/observed/proposed starts, unequal weights,
unsupported models and distribution invariants. No solver or project write is needed.
"""

from dataclasses import replace
from fractions import Fraction

import pytest

from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation import RotationRisk, WorkerRotation
from ergotools.domain.rotation_comparison import (
    IndexSummary,
    compare_rotation_run,
    starting_indices,
)
from ergotools.domain.rotation_constraints import NoAdjacentHigh
from ergotools.domain.rotation_scenario import RotationDraftRow
from ergotools.domain.rotation_timing import MinuteInterval, RotationTiming, TimedBreak
from tests.test_rotation_scenarios import scenario_with_run


@pytest.mark.parametrize("observed", [True, False])
def test_same_frozen_context_preserves_mean_and_reports_each_worker_change(
    observed: bool,
) -> None:
    """Unbalanced 0/100 becomes 50/50 without claiming every worker improved.

    Args:
        observed: True supplies observation; False supplies an explicit proposal.

    Returns:
        None; exact independent arithmetic is identical for every analyzed tool.
    """
    run = scenario_with_run().run
    a, b = (t.key for t in run.inputs.targets)
    rows = (WorkerRotation("W1", (a, a)), WorkerRotation("W2", (b, b)))
    inputs = replace(run.inputs, **{"baseline" if observed else "proposed": rows})
    run = replace(run, inputs=inputs)
    for result in compare_rotation_run(run):
        assert result.before.values == (0, 100)
        assert result.after.values == (50, 50)
        assert result.changes == (50, -50)
        assert result.has_baseline is observed
        assert result.before.mean == result.after.mean == 50
        assert result.before.worst == 100 and result.after.worst == 50
        assert result.before.spread == 100 and result.after.spread == 0
    assert run.inputs.baseline == (rows if observed else None)


def test_absent_start_is_not_zero_or_a_fabricated_observation() -> None:
    """No path without a proposal retains missing before/delta values.

    Args:
        None.

    Returns:
        None; real optimized worker values remain available independently.
    """
    run = scenario_with_run().run
    results = compare_rotation_run(run)
    assert all(r.before is None and r.changes is None for r in results)
    assert all(r.after.values == (50, 50) for r in results)


@pytest.mark.parametrize("subtract, expected", [(True, 50), (False, Fraction(175, 4))])
def test_break_denominator_and_unequal_weights_are_preserved(
    subtract: bool, expected: Fraction | int
) -> None:
    """Comparison uses the saved productive blocks and denominator unchanged.

    Args:
        subtract: Net versus full-shift denominator.
        expected: Independently derived balanced worker index.

    Returns:
        None; displayed summaries are unrounded score projections, never dose.
    """
    run = scenario_with_run().run
    timing = RotationTiming(
        480,
        (TimedBreak(MinuteInterval(240, 300), "Lunch"),),
        (210, 210),
        equal_blocks=True,
        subtract_breaks=subtract,
    )
    run = replace(run, inputs=replace(run.inputs, timing=timing))
    assert compare_rotation_run(run)[0].after.values == pytest.approx(
        (float(expected),) * 2
    )
    unequal = replace(
        run,
        inputs=replace(
            run.inputs, timing=RotationTiming(240, (), (60, 180), equal_blocks=False)
        ),
    )
    assert compare_rotation_run(unequal)[0].after.values == (75, 25)


def test_old_baseline_can_violate_new_high_restriction() -> None:
    """A new rule may be why optimization is needed, without hiding the observation.

    Args:
        None.

    Returns:
        None; after remains independently rule-validated.
    """
    run = scenario_with_run().run
    a, b = (t.key for t in run.inputs.targets)
    inputs = replace(
        run.inputs,
        baseline=(WorkerRotation("W1", (a, a)), WorkerRotation("W2", (b, b))),
        rules=(NoAdjacentHigh("W2"),),
    )
    result = compare_rotation_run(replace(run, inputs=inputs))[0]
    assert result.before.values == (0, 100) and result.after.values == (50, 50)


def test_partial_start_and_missing_coefficient_are_not_silently_completed() -> None:
    """Current input review refuses incomplete cells or selected-tool evidence.

    Args:
        None.

    Returns:
        None; no all-zero defaults or values from another tool are substituted.
    """
    run = scenario_with_run().run
    rows = (RotationDraftRow("W1", (None, None)), RotationDraftRow("W2", (None, None)))
    inputs = replace(run.inputs, baseline=rows)
    with pytest.raises(ValueError):
        starting_indices(inputs, (), AssessmentKind.LIFFT)
    inputs = replace(run.inputs, baseline=run.arrangement)
    with pytest.raises(ValueError, match="complete"):
        starting_indices(
            inputs,
            (RotationRisk(inputs.targets[0].key, AssessmentKind.LIFFT, 0),),
            AssessmentKind.LIFFT,
        )


@pytest.mark.parametrize("version", [1, 99])
def test_unsupported_models_are_not_reinterpreted_as_weighted_results(
    version: int,
) -> None:
    """Historical/future matrices remain evidence without a newly invented score model.

    Args:
        version: Earlier known or unknown positive model identity.

    Returns:
        None; presentation can still display the frozen raw matrix explicitly.
    """
    run = replace(scenario_with_run().run, contract_version=version)
    with pytest.raises(ValueError, match="read-only"):
        compare_rotation_run(run)


@pytest.mark.parametrize("values", [(), (float("nan"),), (True,)])
def test_index_distribution_requires_real_finite_values(
    values: tuple[float, ...],
) -> None:
    """Reject unusable distributions before max/mean projection.

    Args:
        values: Empty, nonfinite or Boolean values.

    Returns:
        None; no clamping or inference occurs.
    """
    with pytest.raises(ValueError):
        IndexSummary(values)

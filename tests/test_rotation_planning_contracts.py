"""Source-bound neighbor, stale-result and strict weighted-run persistence contracts.

Synthetic exact catalogs exercise application validation independently of Qt/solvers.
"""

from dataclasses import replace
from datetime import date

import pytest

from ergotools.application.rotation_planning import (
    accepted_rotation_run,
    capture_rotation_boundary,
    neighbors_are_current,
    prepare_rotation_plan,
    rotation_run_signature,
)
from ergotools.application.rotation_scenarios import apply_rotation_run, run_is_current
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation import WorkerRotation
from ergotools.domain.rotation_constraints import NoAdjacentHigh
from ergotools.domain.rotation_scenario import RotationScenario
from ergotools.infrastructure.highs_rotation_optimizer import HighsRotationPlanner
from ergotools.infrastructure.rotation_scenario_serialization import (
    decode_scenario,
    encode_scenario,
)
from tests.test_rotation_scenarios import (
    scenario_catalogs,
    scenario_inputs,
    scenario_with_run,
)


def test_neighbor_snapshots_are_explicit_exact_and_nonrecursive() -> None:
    """Require a selected current source without inferring a recurring Shift boundary.

    Args:
        None.

    Returns:
        None; missing, changed or retired sources block freshness and preparation.
    """
    hierarchy, jobs, risks = scenario_catalogs()
    previous = scenario_with_run()
    boundary = capture_rotation_boundary(previous, previous=True)
    inputs = replace(
        scenario_inputs(),
        planned_date=date(2026, 11, 3),
        previous=boundary,
        rules=(NoAdjacentHigh("W1", previous=True),),
    )
    scenario = RotationScenario("timing", "next", "Next shift", inputs)
    assert not neighbors_are_current(scenario, (), hierarchy, jobs, risks)
    assert neighbors_are_current(scenario, (previous,), hierarchy, jobs, risks)
    prepared = prepare_rotation_plan(scenario, (previous,), hierarchy, jobs, risks)
    solution = HighsRotationPlanner().solve(prepared.problem)
    run = accepted_rotation_run(prepared, solution)
    accepted = apply_rotation_run(
        scenario, inputs, run, hierarchy, jobs, risks, (previous,)
    )
    assert run_is_current(accepted, hierarchy, jobs, risks, (previous,))
    assert not run_is_current(accepted, hierarchy, jobs, risks)
    assert decode_scenario(encode_scenario(accepted)) == accepted
    # Names are independent of accepted numerical/run evidence.
    renamed = replace(previous, name="Renamed")
    assert neighbors_are_current(scenario, (renamed,), hierarchy, jobs, risks)
    changed = replace(
        previous, inputs=replace(previous.inputs, tools=(AssessmentKind.LIFFT,))
    )
    assert not neighbors_are_current(scenario, (changed,), hierarchy, jobs, risks)
    with pytest.raises(ValueError, match="not checked"):
        prepare_rotation_plan(scenario, (changed,), hierarchy, jobs, risks)
    assert rotation_run_signature(run) == rotation_run_signature(
        decode_scenario(encode_scenario(accepted)).run
    )


def test_apply_revalidates_hard_rules_instead_of_trusting_a_feasible_status() -> None:
    """A forged feasible status cannot bypass independent schedule validation.

    Args:
        None.

    Returns:
        None; acceptance and strict decoding both reject the violation.
    """
    hierarchy, jobs, risks = scenario_catalogs()
    inputs = replace(scenario_inputs(), rules=(NoAdjacentHigh("W1"),))
    scenario = RotationScenario("timing", "one", "Packing", inputs)
    prepared = prepare_rotation_plan(scenario, (), hierarchy, jobs, risks)
    result = HighsRotationPlanner().solve(prepared.problem)
    run = accepted_rotation_run(prepared, result)
    low, high = (t.key for t in inputs.targets)
    forged = replace(
        run,
        arrangement=(
            WorkerRotation("W1", (high, high)),
            WorkerRotation("W2", (low, low)),
        ),
    )
    with pytest.raises(ValueError, match="consecutive"):
        apply_rotation_run(scenario, inputs, forged, hierarchy, jobs, risks)
    with pytest.raises(ValueError, match="consecutive"):
        decode_scenario(encode_scenario(replace(scenario, run=forged)))


def test_generation_without_coefficients_never_becomes_an_optimized_run() -> None:
    """No-path feasibility may omit risks but must retain truthful missing evidence.

    Args:
        None.

    Returns:
        None; absent values remain missing and generation cannot create run evidence.
    """
    hierarchy, jobs, risks = scenario_catalogs()
    risks = replace(risks, values=())
    scenario = RotationScenario("timing", "new", "New", scenario_inputs())
    prepared = prepare_rotation_plan(
        scenario, (), hierarchy, jobs, risks, generation=True
    )
    result = HighsRotationPlanner().solve(prepared.problem)
    assert prepared.coefficients == ()
    assert scenario.inputs.baseline is None
    with pytest.raises(ValueError, match="not an optimized"):
        accepted_rotation_run(prepared, result)


def test_participant_reshape_reports_rules_that_cannot_survive() -> None:
    """Structural edits retain surviving restrictions and report every removed rule.

    Args:
        None.

    Returns:
        None; the GUI can request consent and shared undo can restore the whole input.
    """
    from ergotools.application.rotation_entry import reshape_rotation_inputs
    from ergotools.domain.rotation_constraints import ExcludedPosition, FixedPosition

    inputs = scenario_inputs()
    fixed = FixedPosition("W1", inputs.targets[0].key)
    excluded = ExcludedPosition("W2", inputs.targets[1].key)
    high = NoAdjacentHigh("W2")
    original = replace(inputs, rules=(fixed, excluded, high))
    change = reshape_rotation_inputs(original, workers=(inputs.workers[1],))
    assert change.lost_rules == (fixed,)
    assert change.inputs.rules == (excluded, high)
    assert original.rules == (fixed, excluded, high)

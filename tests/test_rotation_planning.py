"""Independent rational enumeration of weighted/subset/hard-rule planning examples.

Tests compare approved real HiGHS outputs with exhaustive permutation
enumeration, not solver-reported statuses or a mirrored linear model. Fixtures are
wholly synthetic.
"""

from dataclasses import replace
from fractions import Fraction
from itertools import combinations, permutations, product

import pytest

from ergotools.application.rotation_optimization import RotationOptimizationError
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation import RotationBackend, RotationRisk, WorkerRotation
from ergotools.domain.rotation_constraints import (
    ExcludedPosition,
    FixedPosition,
    NoAdjacentHigh,
)
from ergotools.domain.rotation_planning import RotationPlanningProblem
from ergotools.domain.rotation_scheme import RotationTarget, RotationWorkerLink
from ergotools.domain.rotation_timing import MinuteInterval, RotationTiming, TimedBreak
from ergotools.infrastructure.highs_rotation_optimizer import HighsRotationPlanner
from tests.test_rotation_scenarios import scenario_inputs


def planning(
    values: tuple[tuple[int, ...], ...],
    minutes: tuple[int, ...],
    tools: tuple[AssessmentKind, ...] = (AssessmentKind.LIFFT,),
) -> RotationPlanningProblem:
    """Create an explicitly dated No-path problem without any manufactured observation.

    Args:
        values: Per-tool risk vectors in selected tool order.
        minutes: Positive productive budgets for each block.
        tools: One, two or three selected models.

    Returns:
        Complete plain planning input with independent opaque position identities.
    """
    n = len(values[0])
    inputs = replace(
        scenario_inputs(),
        workers=tuple(RotationWorkerLink(f"W{i}") for i in range(n)),
        targets=tuple(RotationTarget(f"J{i}") for i in range(n)),
        tools=tools,
        timing=RotationTiming(sum(minutes), (), minutes, False),
    )
    risks = tuple(
        RotationRisk(t.key, kind, value)
        for kind, vector in zip(tools, values, strict=True)
        for t, value in zip(inputs.targets, vector, strict=True)
    )
    return RotationPlanningProblem(inputs, risks, 10)


def enumerate_scores(
    problem: RotationPlanningProblem,
) -> tuple[tuple[tuple[Fraction, ...], ...], ...]:
    """Enumerate independently staffed schedules and rational weighted worker indices.

    Args:
        problem: Tiny finite planning example whose hard-rule validator filters
        feasibility.

    Returns:
        Per-feasible-schedule selected-tool/worker exact rational indices.
    """
    result = []
    timing = problem.inputs.timing
    for blocks in product(
        tuple(permutations(problem.target_keys)), repeat=problem.num_blocks
    ):
        rows = tuple(
            WorkerRotation(worker, tuple(block[w] for block in blocks))
            for w, worker in enumerate(problem.worker_ids)
        )
        try:
            problem.validate_schedule(rows)
        except ValueError:
            continue
        scores = []
        for kind in problem.inputs.tools:
            risk = {
                r.target_key: Fraction(r.probability_percent)
                for r in problem.risks
                if r.kind is kind
            }
            scores.append(
                tuple(
                    sum(
                        Fraction(minutes) * risk[key]
                        for minutes, key in zip(
                            timing.block_minutes, row.target_keys, strict=True
                        )
                    )
                    / timing.averaging_minutes
                    for row in rows
                )
            )
        result.append(tuple(scores))
    return tuple(result)


@pytest.mark.parametrize(
    ("values", "minutes", "expected"),
    [
        ((0,), (60, 180), 0),
        ((100, 100), (60, 180), 100),
        ((25, 25), (30, 90, 120), 25),
        ((10, 90), (120, 120), 50),
        ((0, 100), (60, 180), 75),
        ((0, 100), (60, 60, 120), 50),
        ((0, 50, 100), (60, 60, 60), 50),
        ((0, 100), (240,), 100),
        ((90,), (30, 90, 120), 90),
        ((0, 100), (60, 60, 60), Fraction(200, 3)),
    ],
)
def test_weighted_single_matches_independent_extreme_optimum(
    values: tuple[int, ...], minutes: tuple[int, ...], expected: Fraction | int
) -> None:
    """Solve obvious extremes and unequal-duration cases through direct HiGHS.

    Args:
        values: Explicit low/high/identical coefficients.
        minutes: Real productive block durations.
        expected: Independently hand-derived minimax worker score.

    Returns:
        None; exact enumeration and returned raw scores establish the optimum.
    """
    problem = planning((values,), minutes)
    assert min(max(scores[0]) for scores in enumerate_scores(problem)) == expected
    solution = HighsRotationPlanner().solve(problem)
    assert solution.backend is RotationBackend.HIGHS and len(solution.stages) == 2
    assert max(
        problem.scores(solution.schedule, AssessmentKind.LIFFT)
    ) == pytest.approx(float(expected), abs=0.0002)
    assert problem.inputs.baseline is None


@pytest.mark.parametrize(
    "tools", [tuple(c) for n in (2, 3) for c in combinations(AssessmentKind, n)]
)
def test_every_multitool_subset_preserves_first_stage_ceilings_and_best_spread(
    tools: tuple[AssessmentKind, ...],
) -> None:
    """Compare every multi-tool subset with independent enumeration.

    Args:
        tools: Every supported pair and the all-tool combination.

    Returns:
        None; objective, feasible individual bound vector and secondary spread are
        verified.
    """
    vectors = {
        AssessmentKind.LIFFT: (0, 100),
        AssessmentKind.DUET: (100, 0),
        AssessmentKind.TST: (20, 80),
    }
    problem = planning(tuple(vectors[k] for k in tools), (60, 180), tools)
    oracle = enumerate_scores(problem)
    best = min(sum(max(k) for k in scores) for scores in oracle)
    solution = HighsRotationPlanner().solve(problem)
    actual = tuple(problem.scores(solution.schedule, k) for k in tools)
    assert solution.backend is RotationBackend.HIGHS and len(solution.stages) == 2
    assert sum(max(k) for k in actual) == pytest.approx(float(best), abs=0.0004)
    bound = tuple(max(k) for k in actual)
    candidates = [
        scores
        for scores in oracle
        if all(float(max(s)) <= b + 0.0002 for s, b in zip(scores, bound, strict=True))
    ]
    assert sum(max(s) - min(s) for s in actual) == pytest.approx(
        float(min(sum(max(s) - min(s) for s in candidate) for candidate in candidates)),
        abs=0.0004,
    )


def test_break_basis_fixed_excluded_and_no_adjacent_rules_are_hard() -> None:
    """Verify break weighting and hard staffing restrictions.

    Args:
        None.

    Returns:
        None; both score divisors and independent hard-rule validation are exact.
    """
    problem = planning(((10, 90),), (210, 210))
    pauses = (TimedBreak(MinuteInterval(240, 300), "Lunch"),)
    timing = RotationTiming(480, pauses, (210, 210), True, True)
    net = replace(problem, inputs=replace(problem.inputs, timing=timing))
    gross = replace(
        net, inputs=replace(net.inputs, timing=replace(timing, subtract_breaks=False))
    )
    for p, expected in [(net, 50), (gross, 43.75)]:
        solution = HighsRotationPlanner().solve(p)
        assert max(p.scores(solution.schedule, AssessmentKind.LIFFT)) == pytest.approx(
            expected
        )
    key = problem.target_keys[1]
    fixed = replace(
        problem, inputs=replace(problem.inputs, rules=(FixedPosition("W0", key),))
    )
    solution = HighsRotationPlanner().solve(fixed)
    assert solution.schedule[0].target_keys == (key, key)
    assert max(fixed.scores(solution.schedule, AssessmentKind.LIFFT)) == 90
    with pytest.raises(ValueError, match="staff"):
        replace(
            problem,
            inputs=replace(
                problem.inputs,
                rules=(FixedPosition("W0", key), ExcludedPosition("W0", key)),
            ),
        )
    high = planning(((51, 100),), (120, 120))
    high = replace(high, inputs=replace(high.inputs, rules=(NoAdjacentHigh("W0"),)))
    with pytest.raises(RotationOptimizationError, match="Infeasible"):
        HighsRotationPlanner().solve(high)
    threshold = planning(((50, 51),), (120, 120))
    threshold = replace(
        threshold,
        inputs=replace(
            threshold.inputs, rules=(NoAdjacentHigh("W0"), NoAdjacentHigh("W1"))
        ),
    )
    assert threshold.high_positions() == frozenset((threshold.target_keys[1],))
    threshold.validate_schedule(HighsRotationPlanner().solve(threshold).schedule)


def test_no_path_feasibility_needs_no_fake_risks_or_observed_schedule() -> None:
    """Feasibility can precede Job assessments unless a High rule needs their values.

    Args:
        None.

    Returns:
        None; only an actual feasible proposed schedule is returned.
    """
    source = planning(((10, 90),), (120, 120))
    problem = RotationPlanningProblem(source.inputs, (), generation=True)
    solution = HighsRotationPlanner().solve(problem)
    problem.validate_schedule(solution.schedule)
    assert problem.inputs.baseline is None and problem.risks == ()
    with pytest.raises(ValueError, match="complete"):
        replace(problem, inputs=replace(problem.inputs, rules=(NoAdjacentHigh("W0"),)))
    with pytest.raises(RotationOptimizationError, match="cancel"):
        HighsRotationPlanner().solve(source, lambda: True)


@pytest.mark.parametrize("previous", [False, True])
def test_explicit_high_neighbor_forces_low_endpoint_and_missing_is_blocked(
    previous: bool,
) -> None:
    """Check both temporal directions against independently obvious endpoint rules.

    Args:
        previous: Select the preceding last block or following first block.

    Returns:
        None; absent requested sources and overlapping intervals never count as checked.
    """
    from datetime import datetime, timedelta

    from ergotools.domain.rotation_constraints import BoundaryExposure, RotationBoundary
    from ergotools.domain.rotation_planning import rotation_interval

    problem = planning(((0, 100),), (60, 60))
    start, end = rotation_interval(problem.inputs)
    neighbor_start = start - timedelta(hours=2) if previous else end
    neighbor_end = start if previous else end + timedelta(hours=2)
    assert type(neighbor_start) is datetime
    boundary = RotationBoundary(
        "neighbor",
        "a" * 64,
        neighbor_start,
        neighbor_end,
        (
            BoundaryExposure(
                "W0",
                "old-position",
                (RotationRisk("old-position", AssessmentKind.LIFFT, 100),),
            ),
        ),
    )
    rule = NoAdjacentHigh("W0", previous=previous, following=not previous)
    with pytest.raises(ValueError, match="not checked"):
        replace(problem, inputs=replace(problem.inputs, rules=(rule,)))
    inputs = replace(
        problem.inputs,
        rules=(rule,),
        **{"previous" if previous else "following": boundary},
    )
    constrained = replace(problem, inputs=inputs)
    result = HighsRotationPlanner().solve(constrained)
    row = result.schedule[0]
    endpoint = 0 if previous else -1
    assert row.target_keys[endpoint] == problem.target_keys[0]
    assert max(constrained.scores(result.schedule, AssessmentKind.LIFFT)) == 50
    invalid = replace(boundary, start=start, end=end)
    with pytest.raises(ValueError, match="overlap"):
        replace(
            problem,
            inputs=replace(
                inputs, **{"previous" if previous else "following": invalid}
            ),
        )


def test_selected_tool_fifty_is_not_high() -> None:
    """An unused tool never changes feasibility; current High means strictly over 50.

    Args:
        None.

    Returns:
        None; a legal all-50 schedule remains feasible under the High adjacency rule.
    """
    problem = planning(((50, 50),), (30, 90))
    restricted = replace(
        problem, inputs=replace(problem.inputs, rules=(NoAdjacentHigh("W0"),))
    )
    result = HighsRotationPlanner().solve(restricted)
    assert restricted.high_positions() == frozenset()
    assert restricted.scores(result.schedule, AssessmentKind.LIFFT) == (50, 50)


def test_population_mean_is_invariant_under_full_staffing() -> None:
    """Every staffed permutation has the same aggregate weighted Job-risk mean.

    Args:
        None.

    Returns:
        None; optimization may improve the worst worker but cannot lower this mean.
    """
    problem = planning(((10, 30, 80),), (15, 45))
    for tools in enumerate_scores(problem):
        assert sum(tools[0]) / 3 == 40

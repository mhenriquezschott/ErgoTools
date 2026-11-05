"""A consecutive-High rule changes ordering even when risk balancing is already optimal.

Actual HiGHS is checked against a staffing conservation bound and an independently
specified optimal schedule. Tied unconstrained solver ordering is intentionally free.
"""

from dataclasses import replace
from itertools import pairwise, permutations, product

import pytest

from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation import WorkerRotation
from ergotools.domain.rotation_constraints import NoAdjacentHigh
from ergotools.infrastructure.highs_rotation_optimizer import HighsRotationPlanner
from tests.test_rotation_planning import planning


def test_consecutive_high_can_be_optimal_until_explicitly_forbidden() -> None:
    """55% Jobs can be consecutive at the exact 20-point global optimum.

    Args:
        None.

    Returns:
        None; restricted and unrestricted real solves attain the same proven optimum,
        while only the restriction rejects the deliberately adjacent optimal baseline.
    """
    problem = planning(((0, 5, 55),), (80,) * 6)
    keys = problem.target_keys
    layout = ((0, 1, 2, 2, 0, 1), (2, 0, 1, 1, 2, 0), (1, 2, 0, 0, 1, 2))
    baseline = tuple(
        WorkerRotation(w, tuple(keys[j] for j in row))
        for w, row in zip(problem.worker_ids, layout, strict=True)
    )
    problem = replace(problem, inputs=replace(problem.inputs, baseline=baseline))
    problem.validate_schedule(baseline)
    assert problem.scores(baseline, AssessmentKind.LIFFT) == (20, 20, 20)
    # Each block contributes 0+5+55=60 across three workers. Hence mean20 is
    # invariant, and no feasible schedule's maximum can be below20.
    assert sum((0, 5, 55)) / 3 == 20
    assert any(a == b == keys[2] for a, b in pairwise(baseline[0].target_keys))
    solver = HighsRotationPlanner()
    unrestricted = solver.solve(problem)
    assert max(problem.scores(unrestricted.schedule, AssessmentKind.LIFFT)) == 20
    restricted = replace(
        problem,
        inputs=replace(
            problem.inputs, rules=tuple(NoAdjacentHigh(w) for w in problem.worker_ids)
        ),
    )
    with pytest.raises(ValueError):
        restricted.validate_schedule(baseline)
    result = solver.solve(restricted)
    assert restricted.scores(result.schedule, AssessmentKind.LIFFT) == (20, 20, 20)
    assert all(
        not any(a == b == keys[2] for a, b in pairwise(row.target_keys))
        for row in result.schedule
    )
    assert problem.inputs.baseline == restricted.inputs.baseline == baseline


def test_unequal_blocks_require_adjacency_at_the_unrestricted_optimum() -> None:
    """All best unrestricted schedules violate adjacency in the unequal example.

    Args:
        None.

    Returns:
        None; independent integer enumeration proves maxima20 and20.625, and the
        real optimizer attains each while honoring all restricted ordering rules.
    """
    minutes = (120, 20, 20, 20, 140, 160)
    risks = (0, 5, 55)
    best_free, best_restricted = 100_000, 100_000
    for columns in product(permutations(range(3)), repeat=6):
        rows = tuple(tuple(c[w] for c in columns) for w in range(3))
        maximum = max(
            sum(risks[j] * d for j, d in zip(row, minutes, strict=True)) for row in rows
        )
        best_free = min(best_free, maximum)
        if all(not any(a == b == 2 for a, b in pairwise(row)) for row in rows):
            best_restricted = min(best_restricted, maximum)
    assert best_free == 9600 and best_restricted == 9900
    assert best_free / 480 == 20 and best_restricted / 480 == 20.625
    problem = planning((risks,), minutes)
    solver = HighsRotationPlanner()
    free = solver.solve(problem)
    assert max(problem.scores(free.schedule, AssessmentKind.LIFFT)) == 20
    high = problem.target_keys[2]
    assert any(
        any(a == b == high for a, b in pairwise(row.target_keys))
        for row in free.schedule
    )
    restricted = replace(
        problem,
        inputs=replace(
            problem.inputs, rules=tuple(NoAdjacentHigh(w) for w in problem.worker_ids)
        ),
    )
    result = solver.solve(restricted)
    assert max(restricted.scores(result.schedule, AssessmentKind.LIFFT)) == 20.625
    assert all(
        not any(a == b == high for a, b in pairwise(row.target_keys))
        for row in result.schedule
    )

"""Larger controlled fixed/excluded/timing examples with exact independent bounds.

Direct HiGHS handles four workers, four Jobs and eight blocks. Analytical conservation,
integer score spacing and a long-block bound certify the expected optima independently
of solver status and production scoring. No maintained fixture is a test target.
"""

from dataclasses import replace

import pytest

from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation import WorkerRotation
from ergotools.domain.rotation_constraints import ExcludedPosition, FixedPosition
from ergotools.infrastructure.highs_rotation_optimizer import HighsRotationPlanner
from tests.test_rotation_planning import planning


def test_excluding_high_changes_every_unrestricted_optimum() -> None:
    """A worker who necessarily receives High at 21.25 can be explicitly excluded.

    Args:
        None.

    Returns:
        None; a count-based lower bound proves 21.875 for the restricted optimum,
        and real solves attain both values with full per-block staffing.
    """
    problem = planning(((0, 5, 25, 55),), (60,) * 8)
    solver = HighsRotationPlanner()
    free = solver.solve(problem)
    assert problem.scores(free.schedule, AssessmentKind.LIFFT) == (21.25,) * 4
    high = problem.target_keys[3]
    assert all(high in row.target_keys for row in free.schedule)
    # Eight staffed blocks contribute 85*8=680 risk-points across workers. With
    # maximum 21.25, every row's unnormalized sum must be 170. A High-free row
    # can reach at most 160 below that ceiling, so four such bounded rows cannot
    # sum to 680. All sums are multiples of 5; the next possible ceiling is 175.
    no_high_sums = [5 * a + 25 * b for a in range(9) for b in range(9 - a)]
    assert max(s for s in no_high_sums if s <= 170) == 160
    assert 160 + 3 * 170 < 680 and 175 / 8 == 21.875
    restricted = replace(
        problem,
        inputs=replace(
            problem.inputs,
            rules=(ExcludedPosition(problem.worker_ids[0], high),),
        ),
    )
    with pytest.raises(ValueError):
        restricted.validate_schedule(free.schedule)
    result = solver.solve(restricted)
    assert max(restricted.scores(result.schedule, AssessmentKind.LIFFT)) == 21.875
    assert high not in result.schedule[0].target_keys
    assert all(
        {r.target_keys[b] for r in result.schedule} == set(problem.target_keys)
        for b in range(8)
    )


def test_fixing_low_job_changes_a_previously_rotating_worker() -> None:
    """Fixing one worker to inspection leaves a nontrivial three-worker balance.

    Args:
        None.

    Returns:
        None; unrestricted 21.25 and fixed 28.75 match conservation/integer bounds;
        the fixed worker performs exactly the same Job in every block.
    """
    problem = planning(((0, 5, 25, 55),), (60,) * 8)
    solver = HighsRotationPlanner()
    free = solver.solve(problem)
    assert problem.scores(free.schedule, AssessmentKind.LIFFT) == (21.25,) * 4
    assert len(set(free.schedule[0].target_keys)) > 1
    low = problem.target_keys[0]
    fixed = replace(
        problem,
        inputs=replace(
            problem.inputs,
            rules=(FixedPosition(problem.worker_ids[0], low),),
        ),
    )
    with pytest.raises(ValueError):
        fixed.validate_schedule(free.schedule)
    # The other three rows must carry all 680 points. Their sums are multiples
    # of 5, so their maximum sum is at least ceil(680/15)*5=230; divide by8.
    assert ((680 + 14) // 15) * 5 / 8 == 28.75
    result = solver.solve(fixed)
    assert result.schedule[0].target_keys == (low,) * 8
    assert max(fixed.scores(result.schedule, AssessmentKind.LIFFT)) == 28.75
    assert fixed.scores(result.schedule, AssessmentKind.LIFFT)[0] == 0


def test_long_high_block_forces_low_risk_compensation_elsewhere() -> None:
    """A 270-minute High assignment must be offset by seven zero-risk short blocks.

    Args:
        None.

    Returns:
        None; equal optimum 21.25 becomes 30.9375 under the same Jobs/worker matrix,
        with the long High worker's other assignments all Low and every Job staffed.
    """
    equal = planning(((0, 5, 25, 55),), (60,) * 8)
    baseline = tuple(
        WorkerRotation(w, tuple(equal.target_keys[(i + b) % 4] for b in range(8)))
        for i, w in enumerate(equal.worker_ids)
    )
    equal = replace(equal, inputs=replace(equal.inputs, baseline=baseline))
    solver = HighsRotationPlanner()
    free = solver.solve(equal)
    assert equal.scores(free.schedule, AssessmentKind.LIFFT) == (21.25,) * 4
    unequal = replace(
        equal,
        inputs=replace(
            equal.inputs,
            timing=replace(equal.inputs.timing, block_minutes=(30,) * 7 + (270,)),
        ),
    )
    assert max(unequal.scores(baseline, AssessmentKind.LIFFT)) == 38.125
    result = solver.solve(unequal)
    high, low = unequal.target_keys[3], unequal.target_keys[0]
    long_worker = next(r for r in result.schedule if r.target_keys[-1] == high)
    assert long_worker.target_keys[:-1] == (low,) * 7
    assert 55 * 270 / 480 == 30.9375
    assert max(unequal.scores(result.schedule, AssessmentKind.LIFFT)) == 30.9375
    assert all(
        {r.target_keys[b] for r in result.schedule} == set(unequal.target_keys)
        for b in range(8)
    )
    assert unequal.inputs.baseline == equal.inputs.baseline == baseline

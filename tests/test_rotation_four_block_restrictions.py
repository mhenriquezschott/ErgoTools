"""Four-block restriction demonstrations certified independently of MILP expressions.

Pure test layer. Real HiGHS solves three-worker/three-Job cases. An independent exact
permutation oracle checks staffing, fixed/excluded/consecutive-High rules and minimax
answers for equal and strongly unequal blocks. No maintained project is a test target.
"""

from dataclasses import replace
from fractions import Fraction
from itertools import pairwise, permutations, product

import pytest

from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation import WorkerRotation
from ergotools.domain.rotation_constraints import (
    ExcludedPosition,
    FixedPosition,
    NoAdjacentHigh,
)
from ergotools.infrastructure.highs_rotation_optimizer import HighsRotationPlanner
from tests.test_rotation_planning import planning


def allowed_rows(
    rows: tuple[tuple[str, ...], ...], case: str, low: str, high: str
) -> bool:
    """Apply the declared demonstration restrictions without the production validator.

    Args:
        rows: Three independently staffed worker rows of four Job keys.
        case: adjacent, fixed, excluded, fixed_adjacent or excluded_adjacent.
        low: Zero-risk Job key.
        high: High-risk Job key; the remaining Job has 50% risk and is not High.

    Returns:
        True only when the literal demonstration rules are satisfied.
    """
    if case.startswith("fixed") and any(k != low for k in rows[0]):
        return False
    if case.startswith("excluded") and high in rows[0]:
        return False
    checked = rows[1:] if case == "fixed_adjacent" else rows
    return not (
        (case == "adjacent" or case.endswith("_adjacent"))
        and any(a == high and b == high for row in checked for a, b in pairwise(row))
    )


def exact_indices(
    rows: tuple[tuple[str, ...], ...], minutes: tuple[int, ...], risks: dict[str, int]
) -> tuple[Fraction, ...]:
    """Calculate time-weighted indices with fractions, separate from scoring code.

    Args:
        rows: Worker-major assignment grid.
        minutes: Four positive durations totaling 480 minutes.
        risks: Literal 0/50/100 demonstration values by Job key.

    Returns:
        Three exact weighted averages with no display or solver rounding.
    """
    return tuple(
        sum(
            Fraction(risks[k] * duration, 480)
            for k, duration in zip(row, minutes, strict=True)
        )
        for row in rows
    )


@pytest.mark.parametrize(
    ("case", "equal_expected", "unequal_expected"),
    [
        ("adjacent", Fraction(50), Fraction(125, 2)),
        ("fixed", Fraction(75), Fraction(325, 4)),
        ("excluded", Fraction(50), Fraction(125, 2)),
        ("fixed_adjacent", Fraction(75), Fraction(175, 2)),
        ("excluded_adjacent", Fraction(50), Fraction(75)),
    ],
)
@pytest.mark.parametrize("unequal", [False, True], ids=["equal", "very-unequal"])
def test_four_block_constraints_match_exact_known_answers(
    case: str, equal_expected: Fraction, unequal_expected: Fraction, unequal: bool
) -> None:
    """Correct a deliberately violating baseline while attaining the proven minimax.

    Args:
        case: Single or optional combined restriction type.
        equal_expected: Hand-checkable optimum for four equal blocks.
        unequal_expected: Hand-checkable optimum for 30/60/90/300-minute blocks.
        unequal: True selects the dominant final-block timeline.

    Returns:
        None; independently validates the actual solver schedule and preserves inputs.
    """
    minutes = (30, 60, 90, 300) if unequal else (120, 120, 120, 120)
    expected = unequal_expected if unequal else equal_expected
    problem = planning(((0, 50, 100),), minutes)
    low, medium, high = problem.target_keys
    ids = problem.worker_ids
    rules = []
    if case.startswith("fixed"):
        rules.append(FixedPosition(ids[0], low))
    if case.startswith("excluded"):
        rules.append(ExcludedPosition(ids[0], high))
    if case == "adjacent" or case.endswith("_adjacent"):
        rules.extend(
            NoAdjacentHigh(w) for w in (ids[1:] if case == "fixed_adjacent" else ids)
        )
    baseline = tuple(
        WorkerRotation(w, (key,) * 4)
        for w, key in zip(ids, (high, medium, low), strict=True)
    )
    problem = replace(
        problem, inputs=replace(problem.inputs, rules=tuple(rules), baseline=baseline)
    )
    original = problem.inputs
    risk = {low: 0, medium: 50, high: 100}
    assert exact_indices(tuple(r.target_keys for r in baseline), minutes, risk) == (
        100,
        50,
        0,
    )
    assert not allowed_rows(tuple(r.target_keys for r in baseline), case, low, high)
    oracle = []
    for columns in product(permutations(problem.target_keys), repeat=4):
        rows = tuple(tuple(column[w] for column in columns) for w in range(3))
        if allowed_rows(rows, case, low, high):
            oracle.append(max(exact_indices(rows, minutes, risk)))
    assert min(oracle) == expected
    result = HighsRotationPlanner().solve(problem)
    actual = tuple(r.target_keys for r in result.schedule)
    assert all({row[b] for row in actual} == set(problem.target_keys) for b in range(4))
    assert allowed_rows(actual, case, low, high)
    assert float(max(exact_indices(actual, minutes, risk))) == pytest.approx(
        float(expected), abs=1e-6
    )
    assert problem.scores(result.schedule, AssessmentKind.LIFFT) == pytest.approx(
        tuple(float(n) for n in exact_indices(actual, minutes, risk))
    )
    assert problem.inputs == original

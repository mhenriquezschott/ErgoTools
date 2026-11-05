"""Hand-checkable production optimizer examples for the guided JROT design baseline.

Test layer. Real CBC and HiGHS solve tiny equal-block problems. An independent,
exhaustive assignment enumeration uses exact fractions to certify minimax values;
it never constructs solver expressions or relies on the production validator.
These tests establish existing behavior only. Unequal durations and new worker
restrictions have separate design vectors, not claims of implemented functionality.
No Qt, project/database mutation or dependency changes occur.
"""

from collections.abc import Iterator
from fractions import Fraction
from itertools import permutations, product

import pytest

from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation import (
    RotationBackend,
    RotationProblem,
    RotationRisk,
    RotationSolveStatus,
    WorkerRotation,
)
from ergotools.infrastructure.highs_rotation_optimizer import HighsRotationOptimizer

# Worker-major matrix of zero-based Job indices, used only for tiny enumeration.
type AssignmentGrid = tuple[tuple[int, ...], ...]


def assignment_grids(job_count: int, blocks: int) -> Iterator[AssignmentGrid]:
    """Enumerate one worker per Job in each block without using MILP constraints.

    Args:
        job_count: Positive number of workers and Jobs in the tiny fixture.
        blocks: Positive equal-duration block count; fixtures have at most three.

    Yields:
        Every worker-major matrix formed by independent Job permutations per block.
        Enumeration grows factorially and must remain confined to tiny tests.
    """
    for columns in product(permutations(range(job_count)), repeat=blocks):
        yield tuple(
            tuple(column[worker] for column in columns) for worker in range(job_count)
        )


def worker_scores(grid: AssignmentGrid, risks: tuple[int, ...]) -> tuple[Fraction, ...]:
    """Evaluate exact equal-block means independently of production score code.

    Args:
        grid: Complete nonempty tiny worker-major matrix with integer Job indices.
        risks: Present Job risks in percentage points, including valid zero values.

    Returns:
        Exact rational arithmetic mean for each worker; no display rounding.
    """
    return tuple(Fraction(sum(risks[job] for job in row), len(row)) for row in grid)


@pytest.mark.parametrize("multitool", [False, True], ids=["cbc", "highs"])
@pytest.mark.parametrize(
    ("risks", "blocks", "expected"),
    [
        ((0,), 1, Fraction(0)),
        ((100, 100), 2, Fraction(100)),
        ((25, 25), 3, Fraction(25)),
        ((10, 90), 2, Fraction(50)),
        ((0, 100), 3, Fraction(200, 3)),
        ((0, 50, 100), 3, Fraction(50)),
        ((0, 100), 1, Fraction(100)),
        ((90,), 3, Fraction(90)),
    ],
    ids=[
        "zero-is-present",
        "all-high-unavoidable",
        "identical-risks-no-improvement",
        "extreme-workers-balance",
        "odd-blocks-cannot-perfectly-balance",
        "three-workers-complete-cycle",
        "one-block-cannot-spread",
        "one-job-cannot-improve",
    ],
)
def test_real_optimizer_matches_known_and_exhaustive_scores(
    risks: tuple[int, ...], blocks: int, expected: Fraction, multitool: bool
) -> None:
    """Certify real optimal scores, staffing, input preservation and population mean.

    All three tools deliberately share coefficients in these baseline cases. Thus the
    all-tool first stage is three times the same minimax problem and its independently
    enumerable second stage minimizes three times the worker spread. Existing tests
    cover conflicting tool coefficients separately. Equivalent worker permutations
    are accepted rather than requiring one backend's arbitrary tie-breaking layout.

    Args:
        risks: Present tiny Job coefficients in percentage points, including zero.
        blocks: Positive equal-duration horizon, at most three blocks.
        expected: Hand-derived exact optimum for the worst worker's mean score.
        multitool: False runs single-tool HiGHS; True runs both multi-tool stages.

    Returns:
        None. Assertions compare exact-enumeration expectations to actual solver output.
    """
    current = tuple(
        WorkerRotation(f"W{worker + 1:02}", (f"J{worker + 1:02}",) * blocks)
        for worker in range(len(risks))
    )
    kinds = tuple(AssessmentKind) if multitool else (AssessmentKind.LIFFT,)
    problem = RotationProblem(
        current,
        tuple(
            RotationRisk(f"J{job + 1:02}", kind, percent)
            for kind in kinds
            for job, percent in enumerate(risks)
        ),
        5,
    )
    enumerated = tuple(assignment_grids(len(risks), blocks))
    optimum = min(max(worker_scores(grid, risks)) for grid in enumerated)
    assert optimum == expected
    optimizer = HighsRotationOptimizer()
    result = (
        optimizer.optimize_all_tools(problem)
        if multitool
        else optimizer.optimize_single_tool(problem, AssessmentKind.LIFFT)
    )
    assert result.backend == (RotationBackend.HIGHS)
    assert result.stages == (RotationSolveStatus.OPTIMAL,) * (2 if multitool else 1)
    assert problem.current == current
    assert tuple(row.worker_id for row in result.schedule) == tuple(
        row.worker_id for row in current
    )
    job_indices = {f"J{job + 1:02}": job for job in range(len(risks))}
    grid = tuple(
        tuple(job_indices[key] for key in row.target_keys) for row in result.schedule
    )
    assert grid in enumerated
    observed = worker_scores(grid, risks)
    assert max(observed) == expected
    assert sum(observed) / len(observed) == Fraction(sum(risks), len(risks))
    if multitool:
        minimum_spread = min(
            max(scores) - min(scores)
            for candidate in enumerated
            if max(scores := worker_scores(candidate, risks)) == optimum
        )
        assert max(observed) - min(observed) == minimum_spread

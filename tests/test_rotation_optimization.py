"""Original JROT constraints, required routing and incumbent safety regressions.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from itertools import permutations, product
from math import inf, nan
from unittest.mock import patch

import pulp
import pytest

from ergotools.application.rotation_optimization import RotationOptimizationError
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation import (
    RotationBackend,
    RotationProblem,
    RotationRisk,
    RotationSolveStatus,
    WorkerRotation,
)
from ergotools.infrastructure.pulp_rotation_optimizer import PulpRotationOptimizer


@pytest.fixture
def problem() -> RotationProblem:
    """Two differently spelled target keys that PuLP would sanitize identically.

    Args:
        None.

    Returns:
        Tiny immutable two-worker/two-block problem with colliding sanitized target
        captions but distinct opaque identities.
    """
    values = ((10, 90), (80, 20), (20, 60))
    return RotationProblem(
        (
            WorkerRotation("W-1", ("job-A", "job-A")),
            WorkerRotation("W 1", ("job A", "job A")),
        ),
        tuple(
            RotationRisk(key, kind, percent)
            for kind, risks in zip(AssessmentKind, values, strict=True)
            for key, percent in zip(("job-A", "job A"), risks, strict=True)
        ),
        5,
    )


def averages(
    problem: RotationProblem, schedule: tuple[WorkerRotation, ...], kind: AssessmentKind
) -> tuple[float, ...]:
    """Compute unrounded worker averages independently of model variables.

    Args:
        problem: Immutable validated tiny rotation problem; fixtures use exhaustive or
            controlled expected outcomes.
        schedule: Complete proposed worker/time-block assignments, validated against the
            tiny problem.
        kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
            captions are not keys.

    Returns:
        Unrounded per-worker observed probability-percent averages computed
        independently from the supplied schedule.
    """
    risks = problem.risk_by_target(kind)
    return tuple(sum(risks[key] for key in row.target_keys) / 2 for row in schedule)


def feasible_schedules(problem: RotationProblem) -> list[tuple[WorkerRotation, ...]]:
    """Exhaust the tiny fixture rather than duplicating MILP implementation.

    Args:
        problem: Immutable validated tiny rotation problem; fixtures use exhaustive or
            controlled expected outcomes.

    Returns:
        All feasible schedules for the tiny problem found by independent enumeration,
        not by copying solver constraints.
    """
    results = []
    for keys in product(problem.target_keys, repeat=4):
        rows = tuple(
            WorkerRotation(row.worker_id, tuple(keys[index * 2 : index * 2 + 2]))
            for index, row in enumerate(problem.current)
        )
        try:
            problem.validate_schedule(rows)
        except ValueError:
            continue
        results.append(rows)
    return results


def test_cbc_single_tool_matches_exhaustive_minimax(problem: RotationProblem) -> None:
    """Use CBC explicitly and attain the known min-max value without label merging.

    Args:
        problem: Immutable validated tiny rotation problem; fixtures use exhaustive or
            controlled expected outcomes.

    Returns:
        None.
    """
    optimizer = PulpRotationOptimizer()
    with patch.object(pulp, "HiGHS", side_effect=AssertionError("Wrong backend")):
        result = optimizer.optimize_single_tool(problem, AssessmentKind.LIFFT)
    assert result.backend == RotationBackend.CBC
    assert result.stages == (RotationSolveStatus.OPTIMAL,)
    problem.validate_schedule(result.schedule)
    expected = min(
        max(averages(problem, rows, AssessmentKind.LIFFT))
        for rows in feasible_schedules(problem)
    )
    assert (
        max(averages(problem, result.schedule, AssessmentKind.LIFFT)) == expected == 50
    )
    assert problem.current[0].target_keys == ("job-A", "job-A")


def test_highs_two_stages_match_exhaustive_objective(problem: RotationProblem) -> None:
    """Only HiGHS is constructed and each stage receives the full time limit/gap.

    Args:
        problem: Immutable validated tiny rotation problem; fixtures use exhaustive or
            controlled expected outcomes.

    Returns:
        None.
    """
    with (
        patch.object(pulp, "PULP_CBC_CMD", side_effect=AssertionError("Wrong backend")),
        patch.object(pulp, "HiGHS", wraps=pulp.HiGHS) as highs,
    ):
        result = PulpRotationOptimizer().optimize_all_tools(problem)
    assert result.backend == RotationBackend.HIGHS
    assert result.stages == (RotationSolveStatus.OPTIMAL,) * 2
    assert highs.call_count == 2
    assert all(
        call.kwargs == {"msg": False, "timeLimit": 5, "gapRel": 0.01}
        for call in highs.call_args_list
    )
    schedules = feasible_schedules(problem)
    expected = min(
        sum(max(averages(problem, rows, kind)) for kind in AssessmentKind)
        for rows in schedules
    )
    assert (
        sum(max(averages(problem, result.schedule, kind)) for kind in AssessmentKind)
        == expected
        == 140
    )
    assert (
        sum(
            max(averages(problem, result.schedule, kind))
            - min(averages(problem, result.schedule, kind))
            for kind in AssessmentKind
        )
        == 0
    )


@pytest.mark.parametrize("multitool", [False, True])
def test_zero_probability_remains_real_data(
    problem: RotationProblem, multitool: bool
) -> None:
    """Complete zero coefficients are solved instead of treated as absent.

    Args:
        problem: Immutable validated tiny rotation problem; fixtures use exhaustive or
            controlled expected outcomes.
        multitool: True selects all-tool optimization in the parametrized solver
            regression.

    Returns:
        None.
    """
    zero = replace(
        problem,
        risks=tuple(replace(risk, probability_percent=0) for risk in problem.risks),
    )
    optimizer = PulpRotationOptimizer()
    result = (
        optimizer.optimize_all_tools(zero)
        if multitool
        else optimizer.optimize_single_tool(zero, AssessmentKind.LIFFT)
    )
    zero.validate_schedule(result.schedule)


@pytest.mark.parametrize("percent", [nan, inf, -1, 101, True, None])
def test_invalid_risk_values_are_rejected(percent: float) -> None:
    """Missing, nonfinite and out-of-range probabilities cannot reach a solver.

    Args:
        percent: Observed probability percentage or explicit invalid/absent boundary
            case.

    Returns:
        None.
    """
    with pytest.raises(ValueError, match="finite percent"):
        RotationRisk("target", AssessmentKind.LIFFT, percent)


def test_problem_validation_and_required_tools(problem: RotationProblem) -> None:
    """Reject incomplete identities, shape, risk keys and time limits before solve.

    Args:
        problem: Immutable validated tiny rotation problem; fixtures use exhaustive or
            controlled expected outcomes.

    Returns:
        None.
    """
    with pytest.raises(ValueError):
        WorkerRotation("", ("target",))
    with pytest.raises(ValueError):
        WorkerRotation("w", ())
    for rows in (
        (),
        (problem.current[0],) * 2,
        (problem.current[0], WorkerRotation("other", ("job A",))),
    ):
        with pytest.raises(ValueError, match="Workers"):
            replace(problem, current=rows)
    for risks in (
        (*problem.risks, problem.risks[0]),
        (replace(problem.risks[0], target_key="unknown"),),
    ):
        with pytest.raises(ValueError, match="Risk keys"):
            replace(problem, risks=risks)
    for limit in (0, -1, nan, inf, True):
        with pytest.raises(ValueError, match="time limit"):
            replace(problem, time_limit_seconds=limit)
    missing = replace(problem, risks=problem.risks[:-1])
    with pytest.raises(ValueError, match="requires"):
        PulpRotationOptimizer().optimize_all_tools(missing)
    with pytest.raises(ValueError, match="requires"):
        PulpRotationOptimizer().optimize_single_tool(missing, AssessmentKind.TST)
    with pytest.raises(ValueError, match="supported"):
        problem.risk_by_target("bad")


@pytest.mark.parametrize("backend", ["PULP_CBC_CMD", "HiGHS"])
def test_required_solver_failure_does_not_fallback(
    problem: RotationProblem, backend: str
) -> None:
    """Report missing backend and backend execution errors without substitution.

    Args:
        problem: Immutable validated tiny rotation problem; fixtures use exhaustive or
            controlled expected outcomes.
        backend: Required explicit CBC/HiGHS backend selected by the scenario; no
            fallback is accepted.

    Returns:
        None.
    """
    optimizer = PulpRotationOptimizer()
    for failure in (None, pulp.PulpSolverError("failure"), OSError("failure")):
        with patch.object(pulp, backend) as factory:
            factory.return_value.available.return_value = failure is not None
            with (
                patch.object(pulp.LpProblem, "solve", side_effect=failure),
                pytest.raises(RotationOptimizationError),
            ):
                if backend == "HiGHS":
                    optimizer.optimize_all_tools(problem)
                else:
                    optimizer.optimize_single_tool(problem, AssessmentKind.LIFFT)
            assert factory.call_count == 1


def test_infeasible_counts_report_no_solution(problem: RotationProblem) -> None:
    """A target used more times than blocks cannot satisfy per-block uniqueness.

    Args:
        problem: Immutable validated tiny rotation problem; fixtures use exhaustive or
            controlled expected outcomes.

    Returns:
        None.
    """
    impossible = replace(
        problem, current=(problem.current[0], WorkerRotation("W 1", ("job-A", "job A")))
    )
    for multitool in (False, True):
        with pytest.raises(RotationOptimizationError, match="Infeasible"):
            if multitool:
                PulpRotationOptimizer().optimize_all_tools(impossible)
            else:
                PulpRotationOptimizer().optimize_single_tool(
                    impossible, AssessmentKind.LIFFT
                )


@pytest.mark.parametrize("model_status", [pulp.LpStatusOptimal, pulp.LpStatusNotSolved])
def test_feasible_incumbent_is_not_mislabeled_optimal(
    problem: RotationProblem, model_status: int
) -> None:
    """CBC/HiGHS may map a time-limited incumbent to Optimal problem status.

    Args:
        problem: Immutable validated tiny rotation problem; fixtures use exhaustive or
            controlled expected outcomes.
        model_status: Injected PuLP problem status; incumbent validation remains
            independent of this flag.

    Returns:
        None.
    """
    solve = pulp.LpProblem.solve

    def stopped(model: pulp.LpProblem, solver: pulp.LpSolver) -> int:
        """Run the actual solve then mark its incumbent merely feasible.

        Run the actual solve then mark its incumbent merely feasible, proving problem
        status cannot falsely certify optimality.

        Args:
            model: PuLP problem solved by the real backend, then observed or
                deliberately corrupted by this callback.
            solver: Explicit approved backend instance passed through to the original
                solve method.

        Returns:
            Original solve status integer after downgrading incumbent optimality
            evidence.
        """
        status = solve(model, solver)
        model.status = model_status
        model.sol_status = pulp.LpSolutionIntegerFeasible
        return status

    with patch.object(pulp.LpProblem, "solve", stopped):
        result = PulpRotationOptimizer().optimize_single_tool(
            problem, AssessmentKind.LIFFT
        )
    assert result.stages == (RotationSolveStatus.FEASIBLE,)
    problem.validate_schedule(result.schedule)


@pytest.mark.parametrize(
    "corruption",
    ["none", "fractional", "nan", "empty", "collision", "totals", "no-incumbent"],
)
def test_solver_status_never_overrides_schedule_constraints(
    problem: RotationProblem, corruption: str
) -> None:
    """Reject fractional/absent values and whole-schedule violations after solve.

    Args:
        problem: Immutable validated tiny rotation problem; fixtures use exhaustive or
            controlled expected outcomes.
        corruption: Named invalid incumbent/constraint mutation applied after the real
            solve.

    Returns:
        None.
    """
    solve = pulp.LpProblem.solve

    def corrupt(model: pulp.LpProblem, solver: pulp.LpSolver) -> int:
        """Corrupt the real solver incumbent deliberately.

        Run the actual solve then inject the selected
        missing/fractional/nonfinite/collision/count-invalid incumbent.

        Args:
            model: PuLP problem solved by the real backend, then observed or
                deliberately corrupted by this callback.
            solver: Explicit approved backend instance passed through to the original
                solve method.

        Returns:
            Original solve status integer after applying the selected invalid incumbent
            mutation.
        """
        status = solve(model, solver)
        variables = {v.name: v for v in model.variables()}
        if corruption == "no-incumbent":
            model.status = pulp.LpStatusNotSolved
            model.sol_status = pulp.LpSolutionNoSolutionFound
        elif corruption in ("none", "fractional", "nan"):
            variables["assign_0_0_0"].varValue = {
                "none": None,
                "fractional": 0.5,
                "nan": nan,
            }[corruption]
        else:
            for worker in range(2):
                for block in range(2):
                    for target in range(2):
                        selected = (
                            target == block
                            if corruption == "collision"
                            else target == 0
                            if corruption == "totals"
                            else False
                        )
                        variables[f"assign_{worker}_{block}_{target}"].varValue = int(
                            selected
                        )
        return status

    with (
        patch.object(pulp.LpProblem, "solve", corrupt),
        pytest.raises(RotationOptimizationError),
    ):
        PulpRotationOptimizer().optimize_single_tool(problem, AssessmentKind.LIFFT)


def test_second_stage_cannot_exceed_frozen_ceilings(problem: RotationProblem) -> None:
    """Even a complete feasible schedule must satisfy the first-stage ceilings.

    Args:
        problem: Immutable validated tiny rotation problem; fixtures use exhaustive or
            controlled expected outcomes.

    Returns:
        None.
    """
    solve = pulp.LpProblem.solve
    calls = 0

    def violate(model: pulp.LpProblem, solver: pulp.LpSolver) -> int:
        """Corrupt only the second-stage assignments.

        Corrupt only the second-stage assignments to exceed frozen first-stage ceilings
        after a real solve.

        Args:
            model: PuLP problem solved by the real backend, then observed or
                deliberately corrupted by this callback.
            solver: Explicit approved backend instance passed through to the original
                solve method.

        Returns:
            Original solve status integer after deliberate second-stage ceiling
            violation.
        """
        nonlocal calls
        status = solve(model, solver)
        calls += 1
        if calls == 2:
            for variable in model.variables():
                if variable.name.startswith("assign_"):
                    _, worker, _, target = variable.name.split("_")
                    variable.varValue = int(worker == target)
        return status

    with (
        patch.object(pulp.LpProblem, "solve", violate),
        pytest.raises(RotationOptimizationError, match="ceiling"),
    ):
        PulpRotationOptimizer().optimize_all_tools(problem)
    assert calls == 2


def test_three_worker_multitool_matches_conditional_exhaustive_oracle() -> None:
    """Compare both actual stages to independent enumeration on an uneven pool.

    Args:
        None.

    Returns:
        None.
    """
    keys = ("A", "B", "C", "D")
    problem = RotationProblem(
        (
            WorkerRotation("w1", ("A", "A")),
            WorkerRotation("w2", ("B", "B")),
            WorkerRotation("w3", ("C", "D")),
        ),
        tuple(
            RotationRisk(key, kind, percent)
            for kind, values in zip(
                AssessmentKind,
                ((90, 10, 30, 70), (20, 80, 60, 40), (0, 60, 90, 20)),
                strict=True,
            )
            for key, percent in zip(keys, values, strict=True)
        ),
        5,
    )
    candidates = []
    for first, second in product(permutations(keys, 3), repeat=2):
        rows = tuple(
            WorkerRotation(row.worker_id, (first[index], second[index]))
            for index, row in enumerate(problem.current)
        )
        try:
            problem.validate_schedule(rows)
        except ValueError:
            continue
        candidates.append(rows)
    solve = pulp.LpProblem.solve
    bounds = {}
    first_schedule = None

    def observe(model: pulp.LpProblem, solver: pulp.LpSolver) -> int:
        """Observe first-stage exact ceiling variables and opaque schedule.

        Observe first-stage exact ceiling variables and opaque schedule before comparing
        both real stages with independent enumeration.

        Args:
            model: PuLP problem solved by the real backend, then observed or
                deliberately corrupted by this callback.
            solver: Explicit approved backend instance passed through to the original
                solve method.

        Returns:
            Original solve status integer after capturing the first-stage exact ceilings
            and schedule.
        """
        nonlocal first_schedule
        status = solve(model, solver)
        if not bounds:
            variables = {v.name: v for v in model.variables()}
            bounds.update(
                {
                    kind: variables[f"ceiling_{kind.value}"].varValue
                    for kind in AssessmentKind
                }
            )
            first_schedule = tuple(
                WorkerRotation(
                    row.worker_id,
                    tuple(
                        next(
                            key
                            for target, key in enumerate(keys)
                            if variables[f"assign_{worker}_{block}_{target}"].varValue
                            > 0.5
                        )
                        for block in range(2)
                    ),
                )
                for worker, row in enumerate(problem.current)
            )
        return status

    with patch.object(pulp.LpProblem, "solve", observe):
        result = PulpRotationOptimizer().optimize_all_tools(problem)
    optimum = min(
        sum(max(averages(problem, rows, kind)) for kind in AssessmentKind)
        for rows in candidates
    )
    assert first_schedule is not None
    assert (
        sum(max(averages(problem, first_schedule, kind)) for kind in AssessmentKind)
        == optimum
    )
    remaining = [
        rows
        for rows in candidates
        if all(
            max(averages(problem, rows, kind)) <= bounds[kind] + 0.0001
            for kind in AssessmentKind
        )
    ]
    best_spread = min(
        sum(
            max(averages(problem, rows, kind)) - min(averages(problem, rows, kind))
            for kind in AssessmentKind
        )
        for rows in remaining
    )
    assert (
        sum(
            max(averages(problem, result.schedule, kind))
            - min(averages(problem, result.schedule, kind))
            for kind in AssessmentKind
        )
        == best_spread
    )


def test_multitool_second_stage_requires_incumbent(problem: RotationProblem) -> None:
    """Do not publish stale first-stage variables when stage two has no solution.

    Args:
        problem: Immutable validated tiny rotation problem; fixtures use exhaustive or
            controlled expected outcomes.

    Returns:
        None.
    """
    solve = pulp.LpProblem.solve
    calls = 0

    def stop(model: pulp.LpProblem, solver: pulp.LpSolver) -> int:
        """Clear only the second-stage solution status.

        Clear only the second-stage solution status after a real solve so stale
        first-stage variables cannot be published.

        Args:
            model: PuLP problem solved by the real backend, then observed or
                deliberately corrupted by this callback.
            solver: Explicit approved backend instance passed through to the original
                solve method.

        Returns:
            Original solve status integer after deliberately removing second-stage
            incumbent status.
        """
        nonlocal calls
        status = solve(model, solver)
        calls += 1
        if calls == 2:
            model.status = pulp.LpStatusNotSolved
            model.sol_status = pulp.LpSolutionNoSolutionFound
        return status

    with (
        patch.object(pulp.LpProblem, "solve", stop),
        pytest.raises(RotationOptimizationError, match="No feasible"),
    ):
        PulpRotationOptimizer().optimize_all_tools(problem)
    assert calls == 2

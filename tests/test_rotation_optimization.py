"""Original JROT constraints, required routing and incumbent safety regressions.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from itertools import permutations, product
from math import inf, nan
from types import SimpleNamespace
from unittest.mock import patch

import highspy
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
from ergotools.infrastructure.highs_rotation_optimizer import HighsRotationOptimizer


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


def test_highs_single_tool_matches_exhaustive_minimax(problem: RotationProblem) -> None:
    """Use HiGHS directly and attain the known min-max value without label merging.

    Args:
        problem: Immutable validated tiny rotation problem; fixtures use exhaustive or
            controlled expected outcomes.

    Returns:
        None.
    """
    optimizer = HighsRotationOptimizer()
    result = optimizer.optimize_single_tool(problem, AssessmentKind.LIFFT)
    assert result.backend == RotationBackend.HIGHS
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
    options = []
    set_option = highspy.Highs.setOptionValue

    def observe_option(
        model: highspy.Highs, name: str, value: bool | float
    ) -> highspy.HighsStatus:
        """Record actual per-pass options while calling the native setter.

        Args:
            model: Owned HiGHS model being configured.
            name: Native option identifier.
            value: Logging flag, seconds or relative gap.

        Returns:
            Native setter status, unchanged.
        """
        options.append((model, name, value))
        return set_option(model, name, value)

    with patch.object(highspy.Highs, "setOptionValue", observe_option):
        result = HighsRotationOptimizer().optimize_all_tools(problem)
    assert result.backend == RotationBackend.HIGHS
    assert result.stages == (RotationSolveStatus.OPTIMAL,) * 2
    assert [v for _, n, v in options if n == "time_limit"] == [5, 5]
    assert [v for _, n, v in options if n == "mip_rel_gap"] == [0.01, 0.01]
    assert len({id(m) for m, n, _ in options if n == "time_limit"}) == 2
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
    optimizer = HighsRotationOptimizer()
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
        HighsRotationOptimizer().optimize_all_tools(missing)
    with pytest.raises(ValueError, match="requires"):
        HighsRotationOptimizer().optimize_single_tool(missing, AssessmentKind.TST)
    with pytest.raises(ValueError, match="supported"):
        problem.risk_by_target("bad")


@pytest.mark.parametrize("multitool", [False, True])
def test_required_solver_failure_does_not_fallback(
    problem: RotationProblem, multitool: bool
) -> None:
    """Normalize direct HiGHS execution failures without an alternate engine.

    Args:
        problem: Immutable tiny schedule with known feasible risks.
        multitool: Exercise single-tool and all-tool execution paths.

    Returns:
        None; native error status and OS/runtime failures never publish a schedule.
    """
    optimizer = HighsRotationOptimizer()
    for failure in (RuntimeError("failure"), OSError("failure"), None):
        with (
            patch.object(
                highspy.Highs,
                "run",
                side_effect=failure,
                return_value=highspy.HighsStatus.kError,
            ) as run,
            pytest.raises(RotationOptimizationError),
        ):
            if multitool:
                optimizer.optimize_all_tools(problem)
            else:
                optimizer.optimize_single_tool(problem, AssessmentKind.LIFFT)
            assert run.call_count == 1


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
                HighsRotationOptimizer().optimize_all_tools(impossible)
            else:
                HighsRotationOptimizer().optimize_single_tool(
                    impossible, AssessmentKind.LIFFT
                )


@pytest.mark.parametrize(
    "model_status",
    [
        highspy.HighsModelStatus.kTimeLimit,
        highspy.HighsModelStatus.kIterationLimit,
        highspy.HighsModelStatus.kInterrupt,
    ],
)
def test_feasible_incumbent_is_not_mislabeled_optimal(
    problem: RotationProblem, model_status: highspy.HighsModelStatus
) -> None:
    """A valid primal at a native limit is feasible rather than falsely optimal.

    Args:
        problem: Immutable tiny feasible rotation problem.
        model_status: Native nonoptimal stopping reason after a real solve.

    Returns:
        None; independent assignment validation still accepts the valid incumbent.
    """
    with patch.object(highspy.Highs, "getModelStatus", return_value=model_status):
        result = HighsRotationOptimizer().optimize_single_tool(
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
    """Reject corrupted real HiGHS primal values despite an optimal model status.

    Args:
        problem: Tiny independently enumerable feasible schedule.
        corruption: Missing/nonfinite/fractional value, invalid staffing
            or invalid primal validity flag.

    Returns:
        None; backend certification never overrides independent numeric/staffing checks.
    """
    get_solution = highspy.Highs.getSolution

    def corrupt(model: highspy.Highs) -> SimpleNamespace:
        """Return a controlled mutation of the real native primal snapshot.

        Args:
            model: Owned model already solved by actual HiGHS.

        Returns:
            Detached value/validity view; native model state itself is unchanged.
        """
        real = get_solution(model)
        values = list(real.col_value)
        variables = {v.name: v.index for v in model.getVariables()}
        if corruption in ("none", "fractional", "nan"):
            values[variables["assign_0_0_0"]] = {
                "none": None,
                "fractional": 0.5,
                "nan": nan,
            }[corruption]
        elif corruption != "no-incumbent":
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
                        values[variables[f"assign_{worker}_{block}_{target}"]] = int(
                            selected
                        )
        return SimpleNamespace(
            col_value=values,
            value_valid=real.value_valid and corruption != "no-incumbent",
        )

    with (
        patch.object(highspy.Highs, "getSolution", corrupt),
        pytest.raises(RotationOptimizationError),
    ):
        HighsRotationOptimizer().optimize_single_tool(problem, AssessmentKind.LIFFT)


def test_second_stage_cannot_exceed_frozen_ceilings(problem: RotationProblem) -> None:
    """Reject a feasible second-stage arrangement exceeding first-stage ceilings.

    Args:
        problem: Tiny independently enumerable original schedule.

    Returns:
        None; real HiGHS runs twice but corrupted second-stage assignments are rejected.
    """
    run = highspy.Highs.run
    get_solution = highspy.Highs.getSolution
    calls = 0

    def count(model: highspy.Highs) -> highspy.HighsStatus:
        """Count native passes without changing their solve behavior.

        Args:
            model: Owned actual HiGHS model.

        Returns:
            Native execution status after incrementing the observed pass count.
        """
        nonlocal calls
        calls += 1
        return run(model)

    def violate(model: highspy.Highs) -> highspy.HighsSolution:
        """Alter only second-stage assignments in a detached primal snapshot.

        Args:
            model: Actual solved model with opaque index-based names.

        Returns:
            Native validity and deliberately ceiling-violating assignment values.
        """
        real = get_solution(model)
        values = list(real.col_value)
        if calls == 2:
            for variable in model.getVariables():
                if variable.name.startswith("assign_"):
                    _, worker, _, target = variable.name.split("_")
                    values[variable.index] = int(worker == target)
        real.col_value = values
        return real

    with (
        patch.object(highspy.Highs, "run", count),
        patch.object(highspy.Highs, "getSolution", violate),
        pytest.raises(RotationOptimizationError, match="ceiling"),
    ):
        HighsRotationOptimizer().optimize_all_tools(problem)
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
    solve = highspy.Highs.run
    bounds = {}
    first_schedule = None

    def observe(model: highspy.Highs) -> highspy.HighsStatus:
        """Observe first-stage exact ceiling variables and opaque schedule.

        Observe first-stage exact ceiling variables and opaque schedule before comparing
        both real stages with independent enumeration.

        Args:
            model: HiGHS model solved by the real backend, then observed or
                deliberately corrupted by this callback.

        Returns:
            Original solve status integer after capturing the first-stage exact ceilings
            and schedule.
        """
        nonlocal first_schedule
        status = solve(model)
        if not bounds:
            variables = {v.name: v for v in model.getVariables()}
            bounds.update(
                {
                    kind: model.val(variables[f"ceiling_{kind.value}"])
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
                            if model.val(variables[f"assign_{worker}_{block}_{target}"])
                            > 0.5
                        )
                        for block in range(2)
                    ),
                )
                for worker, row in enumerate(problem.current)
            )
        return status

    with patch.object(highspy.Highs, "run", observe):
        result = HighsRotationOptimizer().optimize_all_tools(problem)
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
    """Reject stale first-stage values when the second pass has no valid incumbent.

    Args:
        problem: Tiny independently enumerable feasible original schedule.

    Returns:
        None; no first-pass schedule is silently substituted after second-pass failure.
    """
    run = highspy.Highs.run
    get_solution = highspy.Highs.getSolution
    calls = 0

    def count(model: highspy.Highs) -> highspy.HighsStatus:
        """Count actual passes while preserving the native solver result.

        Args:
            model: Owned HiGHS model.

        Returns:
            Native run status, unchanged.
        """
        nonlocal calls
        calls += 1
        return run(model)

    def invalidate(
        model: highspy.Highs,
    ) -> highspy.HighsSolution | SimpleNamespace:
        """Invalidate only the second native primal snapshot.

        Args:
            model: Owned real solved model.

        Returns:
            Original values but no valid incumbent flag on the second pass.
        """
        real = get_solution(model)
        if calls != 2:
            return real
        return SimpleNamespace(col_value=real.col_value, value_valid=False)

    with (
        patch.object(highspy.Highs, "run", count),
        patch.object(highspy.Highs, "getSolution", invalidate),
        pytest.raises(RotationOptimizationError, match="No feasible"),
    ):
        HighsRotationOptimizer().optimize_all_tools(problem)
    assert calls == 2

"""Direct HiGHS 1.11.0 adapter for original and guided JROT models.

Infrastructure layer. Build owned binary optimization models from plain
application/domain inputs, invoke only the approved backend and validate incumbent
schedules. The original adapter preserves reference objectives. Guided planning
uses two passes for every tool subset: minimax first, then spread minimization.
HiGHS serves every tool subset without engine selection or fallback. The original
all-tool ceiling/spread objective remains intact. This adapter has no Qt, database,
worker lifetime or cancellation ownership. Every stage gets the requested seconds;
neither failure nor timeout substitutes another backend. All risk coefficients use
percentages, not 0-1 probabilities.
"""

from collections import Counter
from collections.abc import Callable, Sequence
from math import isfinite

import highspy
from highspy.highs import highs_linear_expression, highs_var

from ergotools.application.rotation_optimization import (
    RotationOptimizationError,
    RotationSolveShape,
)
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation import (
    RotationBackend,
    RotationProblem,
    RotationSolution,
    RotationSolveStatus,
    WorkerRotation,
)
from ergotools.domain.rotation_constraints import NoAdjacentHigh
from ergotools.domain.rotation_planning import (
    RotationPlanningProblem,
    allowed_positions,
)

# Dimensionless solver relative gap: 0.01 means one percent, matching reference policy.
RELATIVE_GAP = 0.01
# Allowed all-tool second-stage ceiling slack in percentage points, as in reference.
CEILING_TOLERANCE = 0.0001
# Maximum binary-distance error; also retained in the original ceiling verification.
INTEGRAL_TOLERANCE = 0.00001

type Variables = dict[tuple[int, int, str], highs_var]


class HighsRotationOptimizer:
    """Solve original objectives with one HiGHS runtime and owned models.

    Calls create independent models and make no project writes. Run from an owned
    background worker when composed into Qt; this adapter itself has no Qt/thread
    lifecycle or cancellation policy. Errors never substitute another backend.
    """

    def optimize_single_tool(
        self, problem: RotationProblem, kind: AssessmentKind
    ) -> RotationSolution:
        """Minimize maximum worker average with direct HiGHS.

        Args:
            problem: Validated original worker-by-block schedule, target risks and
                positive time budget in seconds.
            kind: Exact scientific model whose scheduled target percentages define the
                objective.

        Returns:
            Validated HiGHS schedule, with one optimal/feasible
            status.

        Raises:
            ValueError: A scheduled target lacks a valid selected-model risk.
            RotationOptimizationError: The backend fails or its incumbent lacks
                complete valid binary assignments.
        """
        risks = problem.risk_by_target(kind)
        model, variables = _base_model(problem)
        maximum = model.addVariable(name="max_average", lb=0)
        for worker in range(len(problem.current)):
            model.addConstr(_average(problem, variables, worker, risks) <= maximum)
        model.setObjective(maximum)
        status, schedule = _solve(model, variables, problem)
        return RotationSolution(schedule, RotationBackend.HIGHS, (status,))

    def optimize_all_tools(self, problem: RotationProblem) -> RotationSolution:
        """Minimize tool ceilings then their spread, with HiGHS for both stages.

        The reference upper bound tolerance is 0.0001 percentage points. Each stage gets
        the full requested time limit, not half a shared budget.

        Args:
            problem: Validated original schedule and all three tools' target
                percentages; each stage receives the full time budget in seconds.

        Returns:
            Validated HiGHS schedule and both stage statuses, retaining first-stage
            per-tool maximum bounds within tolerance.

        Raises:
            ValueError: A scheduled target lacks any required tool risk.
            RotationOptimizationError: HiGHS is unavailable/fails, an incumbent is
                incomplete/nonbinary or the final schedule violates a first-stage
                ceiling.
        """
        risks = {kind: problem.risk_by_target(kind) for kind in AssessmentKind}
        model, variables = _base_model(problem)
        ceilings = {
            kind: model.addVariable(name=f"ceiling_{kind.value}", lb=0)
            for kind in AssessmentKind
        }
        floors = {
            kind: model.addVariable(name=f"floor_{kind.value}", lb=0)
            for kind in AssessmentKind
        }
        for worker in range(len(problem.current)):
            for kind in AssessmentKind:
                average = _average(problem, variables, worker, risks[kind])
                model.addConstr(average <= ceilings[kind])
                model.addConstr(average >= floors[kind])
        model.setObjective(highspy.Highs.qsum(ceilings.values()))
        first_status, first_schedule = _solve(model, variables, problem)
        best_ceilings = {kind: _number(ceilings[kind]) for kind in AssessmentKind}
        _verify_ceilings(first_schedule, risks, best_ceilings)
        for kind in AssessmentKind:
            model.addConstr(ceilings[kind] <= best_ceilings[kind] + CEILING_TOLERANCE)
        model.setObjective(
            highspy.Highs.qsum(ceilings[kind] - floors[kind] for kind in AssessmentKind)
        )
        second_status, schedule = _solve(model, variables, problem)
        _verify_ceilings(schedule, risks, best_ceilings)
        return RotationSolution(
            schedule, RotationBackend.HIGHS, (first_status, second_status)
        )


def _base_model(problem: RotationProblem) -> tuple[highspy.Highs, Variables]:
    """Build the original binary assignment model.

    Constrain one target per worker/period, at most one worker per target/period and
    original total target counts.

    Numeric variable names retain exact distinct labels outside the solver; no solver or
    project write runs here.

    Args:
        problem: Validated current schedule providing workers, periods and exact target
            multiplicities.

    Returns:
        Owned minimization model and binary variables keyed by worker index, block index
        and exact target key.
    """
    model = highspy.Highs()
    model.setOptionValue("output_flag", False)
    # Index-based variable names keep distinct application identities independent of
    # target keys such as 'job-A' and 'job A', including scoped placements.
    variables = {
        (worker, block, key): model.addBinary(name=f"assign_{worker}_{block}_{target}")
        for worker in range(len(problem.current))
        for block in range(problem.num_blocks)
        for target, key in enumerate(problem.target_keys)
    }
    for worker in range(len(problem.current)):
        for block in range(problem.num_blocks):
            model.addConstr(
                highspy.Highs.qsum(
                    variables[worker, block, key] for key in problem.target_keys
                )
                == 1
            )
    totals = Counter(key for row in problem.current for key in row.target_keys)
    for key in problem.target_keys:
        model.addConstr(
            highspy.Highs.qsum(
                variables[worker, block, key]
                for worker in range(len(problem.current))
                for block in range(problem.num_blocks)
            )
            == totals[key]
        )
        for block in range(problem.num_blocks):
            model.addConstr(
                highspy.Highs.qsum(
                    variables[worker, block, key]
                    for worker in range(len(problem.current))
                )
                <= 1
            )
    return model, variables


def _average(
    problem: RotationProblem,
    variables: Variables,
    worker: int,
    risks: dict[str, float],
) -> highs_linear_expression:
    """Pure model construction; no solving, rounding or storage.

    Args:
        problem: Validated schedule with a positive period count and exact target keys.
        variables: Complete binary assignment variable map from _base_model.
        worker: Zero-based worker row index.
        risks: Selected-tool target probabilities on 0-100 percent scale.

    Returns:
        Affine expression for this worker's average outcome percent across
        equal-duration periods.

    Raises:
        KeyError: The internal variable or risk map lacks a required exact key.
    """
    return highspy.Highs.qsum(
        variables[worker, block, key] * (risks[key] / problem.num_blocks)
        for block in range(problem.num_blocks)
        for key in problem.target_keys
    )


def _solve(
    model: highspy.Highs,
    variables: Variables,
    problem: RotationSolveShape,
) -> tuple[RotationSolveStatus, tuple[WorkerRotation, ...]]:
    """Run only HiGHS with independent stage state and validate its primal incumbent.

    Args:
        model: Owned linear model with current objective and constraints.
        variables: Exact indexed binary assignment variables bound to this model.
        problem: Frozen schedule shape and positive per-stage time limit in seconds.

    Returns:
        Honest optimal/feasible termination evidence and independently validated rows.
        Limits without a valid feasible incumbent never publish stale prior results.

    Raises:
        RotationOptimizationError: Options/run fail, no feasible primal exists or
            independent numeric/staffing/rule/ceiling validation rejects the solution.
    """
    try:
        stage = highspy.Highs()
        for name, value in (
            ("output_flag", False),
            ("time_limit", problem.time_limit_seconds),
            ("mip_rel_gap", RELATIVE_GAP),
        ):
            if stage.setOptionValue(name, value) == highspy.HighsStatus.kError:
                raise RotationOptimizationError("HiGHS rejected a solve option.")
        if stage.passModel(model.getModel()) == highspy.HighsStatus.kError:
            raise RotationOptimizationError("HiGHS rejected the optimization model.")
        outcome = stage.run()
        status = stage.getModelStatus()
        solution = stage.getSolution()
        info = stage.getInfo()
    except (OSError, RuntimeError) as error:
        raise RotationOptimizationError(f"HiGHS solver failed: {error}") from error
    accepted_statuses = (
        highspy.HighsModelStatus.kOptimal,
        highspy.HighsModelStatus.kTimeLimit,
        highspy.HighsModelStatus.kIterationLimit,
        highspy.HighsModelStatus.kObjectiveBound,
        highspy.HighsModelStatus.kObjectiveTarget,
        highspy.HighsModelStatus.kSolutionLimit,
        highspy.HighsModelStatus.kInterrupt,
        highspy.HighsModelStatus.kMemoryLimit,
    )
    if (
        outcome == highspy.HighsStatus.kError
        or status not in accepted_statuses
        or not solution.value_valid
        or info.primal_solution_status != highspy.SolutionStatus.kSolutionStatusFeasible
    ):
        raise RotationOptimizationError(
            "No feasible rotation returned: " + stage.modelStatusToString(status) + "."
        )
    schedule = _extract(problem, variables, solution.col_value)
    try:
        problem.validate_schedule(schedule)
    except ValueError as error:
        raise RotationOptimizationError(str(error)) from error
    evidence = (
        RotationSolveStatus.OPTIMAL
        if status == highspy.HighsModelStatus.kOptimal
        else RotationSolveStatus.FEASIBLE
    )
    if model.setSolution(solution) == highspy.HighsStatus.kError:
        raise RotationOptimizationError(
            "HiGHS could not retain the validated incumbent."
        )
    return evidence, schedule


def _number(variable: highs_var, values: Sequence[float] | None = None) -> float:
    """Read only; integer feasibility is checked separately during extraction.

    Args:
        variable: Solved HiGHS variable expected to have a finite numeric value.
        values: Optional current-stage primal vector; otherwise read the retained
            independently validated result on the owned model.

    Returns:
        Finite solver value without rounding or clamping.

    Raises:
        RotationOptimizationError: Solver value is absent or nonfinite.
    """
    current: Sequence[float]
    if values is None:
        solution = variable.highs.getSolution()
        current = solution.col_value if solution.value_valid else ()
    else:
        current = values
    value = current[variable.index] if variable.index < len(current) else None
    if value is None or not isfinite(value):
        raise RotationOptimizationError(
            "The solver returned an absent/nonfinite value."
        )
    return value


def _extract(
    problem: RotationSolveShape, variables: Variables, values: Sequence[float]
) -> tuple[WorkerRotation, ...]:
    """Validate binary values before extracting a complete schedule.

    Args:
        problem: Validated original row/period ordering and exact target keys.
        variables: Solved complete worker/period/target binary map.
        values: Current-pass primal vector before accepting it on the model.

    Returns:
        Worker rotations in original worker and period order, with exactly one
        selected target per block.

    Raises:
        RotationOptimizationError: A value is absent/nonfinite/nonbinary within
            tolerance or a block has zero/multiple selected targets.
        KeyError: The internal variable map lacks a required index/key.
    """
    rows = []
    for worker, worker_id in enumerate(problem.worker_ids):
        keys = []
        for block in range(problem.num_blocks):
            selected = []
            for key in problem.target_keys:
                value = _number(variables[worker, block, key], values)
                if min(abs(value), abs(value - 1)) > INTEGRAL_TOLERANCE:
                    raise RotationOptimizationError(
                        "The solver returned a nonbinary value."
                    )
                if value > 0.5:
                    selected.append(key)
            if len(selected) != 1:
                raise RotationOptimizationError(
                    "The solver returned an incomplete block."
                )
            keys.append(selected[0])
        rows.append(WorkerRotation(worker_id, tuple(keys)))
    return tuple(rows)


def _verify_ceilings(
    schedule: tuple[WorkerRotation, ...],
    risks: dict[AssessmentKind, dict[str, float]],
    ceilings: dict[AssessmentKind, float],
) -> None:
    """Pure post-solve verification; no model or source change.

    Args:
        schedule: Complete stage schedule whose per-worker tool averages are verified.
        risks: Tool-to-target risk percentages for all three scientific models.
        ceilings: First-stage maximum values in percent for each model.

    Returns:
        None when all worker averages remain within first-stage ceiling plus the two
        established tolerances.

    Raises:
        RotationOptimizationError: Any worker/model average exceeds the frozen ceiling
            and tolerances.
        KeyError: An internal tool/target or ceiling is absent.
    """
    for kind in AssessmentKind:
        for row in schedule:
            average = sum(risks[kind][key] for key in row.target_keys) / len(
                row.target_keys
            )
            if average > ceilings[kind] + CEILING_TOLERANCE + INTEGRAL_TOLERANCE:
                raise RotationOptimizationError("The solver exceeded a tool ceiling.")


class HighsRotationPlanner:
    """Solve guided weighted/subset models using the same approved backend runtime.

    The original model builders and objectives above stay separate and
    unchanged. Neither observation nor proposed seed is used as a fake baseline
    or extra constraint.
    """

    def solve(
        self,
        problem: RotationPlanningProblem,
        cancelled: Callable[[], bool] | None = None,
    ) -> RotationSolution:
        """Generate a feasible plan or minimize weighted ceilings then their spreads.

        Args:
            problem: Complete frozen planning context and explicit generation
            purpose.
            cancelled: Cooperative intent; running stages finish within their own
            bounds.

        Returns:
            Feasible validated schedule with backend termination evidence.

        Raises:
            RotationOptimizationError: Cancellation, infeasibility or invalid
            backend output.
        """
        if cancelled is not None and cancelled():
            raise RotationOptimizationError("Planning cancelled.")
        backend = RotationBackend.HIGHS
        model, variables = _planning_model(problem)
        if problem.generation:
            model.setObjective(highspy.Highs.qsum([]))
            status, rows = _solve(model, variables, problem)
            return RotationSolution(rows, backend, (status,))
        tools = problem.inputs.tools
        ceilings = {
            kind: model.addVariable(name=f"ceiling_{kind.value}", lb=0)
            for kind in tools
        }
        floors = {
            kind: model.addVariable(name=f"floor_{kind.value}", lb=0) for kind in tools
        }
        for worker in range(len(problem.worker_ids)):
            for kind in tools:
                score = _planning_score(problem, variables, worker, kind)
                model.addConstr(score <= ceilings[kind])
                model.addConstr(score >= floors[kind])
        model.setObjective(highspy.Highs.qsum(ceilings.values()))
        first_status, first = _solve(model, variables, problem)
        bounds = {kind: _number(value) for kind, value in ceilings.items()}
        _check_planning_ceilings(problem, first, bounds)
        if cancelled is not None and cancelled():
            raise RotationOptimizationError("Planning cancelled before second stage.")
        for kind in tools:
            model.addConstr(ceilings[kind] <= bounds[kind] + CEILING_TOLERANCE)
        model.setObjective(
            highspy.Highs.qsum(ceilings[kind] - floors[kind] for kind in tools)
        )
        second_status, rows = _solve(model, variables, problem)
        _check_planning_ceilings(problem, rows, bounds)
        return RotationSolution(rows, backend, (first_status, second_status))


def _planning_model(
    problem: RotationPlanningProblem,
) -> tuple[highspy.Highs, Variables]:
    """Build exact per-block staffing plus fixed/excluded/High adjacency constraints.

    Args:
        problem: Frozen independently validated restrictions/timing and tool subset.

    Returns:
        Owned linear model and complete opaque-keyed binary assignment variables.
    """
    model = highspy.Highs()
    model.setOptionValue("output_flag", False)
    variables = {
        (w, b, key): model.addBinary(name=f"plan_{w}_{b}_{j}")
        for w in range(len(problem.worker_ids))
        for b in range(problem.num_blocks)
        for j, key in enumerate(problem.target_keys)
    }
    allowed = allowed_positions(problem.inputs)
    for w, worker in enumerate(problem.worker_ids):
        for b in range(problem.num_blocks):
            model.addConstr(
                highspy.Highs.qsum(variables[w, b, key] for key in problem.target_keys)
                == 1
            )
            for key in problem.target_keys:
                if key not in allowed[worker]:
                    model.addConstr(variables[w, b, key] <= 0)
    for b in range(problem.num_blocks):
        for key in problem.target_keys:
            model.addConstr(
                highspy.Highs.qsum(
                    variables[w, b, key] for w in range(len(problem.worker_ids))
                )
                == 1
            )
    high = (
        problem.high_positions()
        if any(isinstance(r, NoAdjacentHigh) for r in problem.inputs.rules)
        else frozenset()
    )
    for rule in problem.inputs.rules:
        if not isinstance(rule, NoAdjacentHigh):
            continue
        w = problem.worker_ids.index(rule.worker_id)
        for b in range(problem.num_blocks - 1):
            model.addConstr(
                highspy.Highs.qsum(
                    variables[w, period, key] for period in (b, b + 1) for key in high
                )
                <= 1
            )
        for previous, checked, b in (
            (True, rule.previous, 0),
            (False, rule.following, problem.num_blocks - 1),
        ):
            if checked and problem.boundary_high(rule.worker_id, previous=previous):
                model.addConstr(
                    highspy.Highs.qsum(variables[w, b, key] for key in high) <= 0
                )
    return model, variables


def _planning_score(
    problem: RotationPlanningProblem,
    variables: Variables,
    worker: int,
    kind: AssessmentKind,
) -> highs_linear_expression:
    """Construct the weighted Job-risk index without changing repetition/damage models.

    Args:
        problem: Complete copied work/break timing and selected-tool coefficients.
        variables: Complete assignment model variables.
        worker: Exact zero-based participant index.
        kind: Selected analysis tool.

    Returns:
        Unrounded percentage-point index, with no assignments during breaks.
    """
    assert problem.inputs.timing is not None
    risks = problem.risk_by_target(kind)
    return highspy.Highs.qsum(
        variables[worker, b, key]
        * ((minutes * risks[key]) / problem.inputs.timing.averaging_minutes)
        for b, minutes in enumerate(problem.inputs.timing.block_minutes)
        for key in problem.target_keys
    )


def _check_planning_ceilings(
    problem: RotationPlanningProblem,
    rows: tuple[WorkerRotation, ...],
    bounds: dict[AssessmentKind, float],
) -> None:
    """Independently check returned scores against preserved ceilings.

    Args:
        problem: Exact frozen score basis and staffing/rules.
        rows: Extracted independently feasible schedule.
        bounds: Actual first-stage individual per-tool ceilings.

    Returns:
        None only within the established percentage-point tolerances.

    Raises:
        RotationOptimizationError: A candidate exceeds any preserved tool ceiling.
    """
    for kind, ceiling in bounds.items():
        if (
            max(problem.scores(rows, kind))
            > ceiling + CEILING_TOLERANCE + INTEGRAL_TOLERANCE
        ):
            raise RotationOptimizationError(
                "The solver exceeded a weighted tool ceiling."
            )

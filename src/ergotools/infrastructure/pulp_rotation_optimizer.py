"""PuLP 3.2.2 adapter for the original CBC/HiGHS JROT models.

Infrastructure layer. Build owned binary optimization models from plain
application/domain inputs, invoke only the approved backend and validate incumbent
schedules. CBC serves single-tool minimax risk; HiGHS serves the two-stage all-tool
ceiling/spread objective. This adapter has no Qt, database, worker lifetime or
cancellation ownership. Every stage gets the requested seconds and neither failure nor
timeout substitutes another backend. All risk coefficients/objectives use percentages,
not 0-1 probabilities.
"""

from collections import Counter
from math import isfinite

import pulp

from ergotools.application.rotation_optimization import RotationOptimizationError
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation import (
    RotationBackend,
    RotationProblem,
    RotationSolution,
    RotationSolveStatus,
    WorkerRotation,
)

# Dimensionless solver relative gap: 0.01 means one percent, matching reference policy.
RELATIVE_GAP = 0.01
# Allowed all-tool second-stage ceiling slack in percentage points, as in reference.
CEILING_TOLERANCE = 0.0001
# Maximum binary-distance error; also retained in the original ceiling verification.
INTEGRAL_TOLERANCE = 0.00001

type Variables = dict[tuple[int, int, str], pulp.LpVariable]


class PulpRotationOptimizer:
    """Solve original objectives with explicit backend routing and owned models.

    Calls create independent models and make no project writes. Run from an owned
    background worker when composed into Qt; this adapter itself has no Qt/thread
    lifecycle or cancellation policy. Errors never substitute another backend.
    """

    def optimize_single_tool(
        self, problem: RotationProblem, kind: AssessmentKind
    ) -> RotationSolution:
        """Minimize maximum worker average percent using only bundled CBC.

        Args:
            problem: Validated original worker-by-block schedule, target risks and
                positive time budget in seconds.
            kind: Exact scientific model whose scheduled target percentages define the
                objective.

        Returns:
            Validated worker schedule using bundled CBC, with one optimal/feasible
            status.

        Raises:
            ValueError: A scheduled target lacks a valid selected-model risk.
            RotationOptimizationError: CBC is unavailable/fails or its incumbent lacks
                complete valid binary assignments.
        """
        risks = problem.risk_by_target(kind)
        model, variables = _base_model(problem)
        maximum = pulp.LpVariable("max_average", lowBound=0)
        for worker in range(len(problem.current)):
            model.addConstraint(_average(problem, variables, worker, risks) <= maximum)
        model.setObjective(maximum)
        status, schedule = _solve(model, variables, problem, RotationBackend.CBC)
        return RotationSolution(schedule, RotationBackend.CBC, (status,))

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
            kind: pulp.LpVariable(f"ceiling_{kind.value}", lowBound=0)
            for kind in AssessmentKind
        }
        floors = {
            kind: pulp.LpVariable(f"floor_{kind.value}", lowBound=0)
            for kind in AssessmentKind
        }
        for worker in range(len(problem.current)):
            for kind in AssessmentKind:
                average = _average(problem, variables, worker, risks[kind])
                model.addConstraint(average <= ceilings[kind])
                model.addConstraint(average >= floors[kind])
        model.setObjective(pulp.lpSum(ceilings.values()))
        first_status, first_schedule = _solve(
            model, variables, problem, RotationBackend.HIGHS
        )
        best_ceilings = {kind: _number(ceilings[kind]) for kind in AssessmentKind}
        _verify_ceilings(first_schedule, risks, best_ceilings)
        for kind in AssessmentKind:
            model.addConstraint(
                ceilings[kind] <= best_ceilings[kind] + CEILING_TOLERANCE
            )
        model.setObjective(
            pulp.lpSum(ceilings[kind] - floors[kind] for kind in AssessmentKind)
        )
        second_status, schedule = _solve(
            model, variables, problem, RotationBackend.HIGHS
        )
        _verify_ceilings(schedule, risks, best_ceilings)
        return RotationSolution(
            schedule, RotationBackend.HIGHS, (first_status, second_status)
        )


def _base_model(problem: RotationProblem) -> tuple[pulp.LpProblem, Variables]:
    """Build the original binary assignment model.

    Constrain one target per worker/period, at most one worker per target/period and
    original total target counts.

    Numeric variable names avoid PuLP sanitization merging distinct labels; no solver or
    project write runs here.

    Args:
        problem: Validated current schedule providing workers, periods and exact target
            multiplicities.

    Returns:
        Owned minimization model and binary variables keyed by worker index, block index
        and exact target key.
    """
    model = pulp.LpProblem("JobRotationOptimization", pulp.LpMinimize)
    # Index-based variable names avoid PuLP's label sanitization merging distinct
    # target keys such as 'job-A' and 'job A', including scoped placements.
    variables = {
        (worker, block, key): pulp.LpVariable(
            f"assign_{worker}_{block}_{target}", cat="Binary"
        )
        for worker in range(len(problem.current))
        for block in range(problem.num_blocks)
        for target, key in enumerate(problem.target_keys)
    }
    for worker in range(len(problem.current)):
        for block in range(problem.num_blocks):
            model.addConstraint(
                pulp.LpConstraint(
                    e=pulp.lpSum(
                        variables[worker, block, key] for key in problem.target_keys
                    ),
                    sense=pulp.LpConstraintEQ,
                    rhs=1,
                )
            )
    totals = Counter(key for row in problem.current for key in row.target_keys)
    for key in problem.target_keys:
        model.addConstraint(
            pulp.LpConstraint(
                e=pulp.lpSum(
                    variables[worker, block, key]
                    for worker in range(len(problem.current))
                    for block in range(problem.num_blocks)
                ),
                sense=pulp.LpConstraintEQ,
                rhs=totals[key],
            )
        )
        for block in range(problem.num_blocks):
            model.addConstraint(
                pulp.lpSum(
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
) -> pulp.LpAffineExpression:
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
    return (
        pulp.lpSum(
            variables[worker, block, key] * risks[key]
            for block in range(problem.num_blocks)
            for key in problem.target_keys
        )
        / problem.num_blocks
    )


def _solve(
    model: pulp.LpProblem,
    variables: Variables,
    problem: RotationProblem,
    backend: RotationBackend,
) -> tuple[RotationSolveStatus, tuple[WorkerRotation, ...]]:
    """Construct a fresh solver with a dimensionless 0.01 relative gap.

    Mutate only the owned model solution; no project state is saved.

    Args:
        model: Owned PuLP model with the current stage objective and constraints.
        variables: Complete binary worker/period/target variable map.
        problem: Validated original schedule and per-stage solver time budget in
            seconds.
        backend: Explicit CBC single-tool or HiGHS multi-tool routing; no fallback
            backend.

    Returns:
        Optimal/feasible status and complete schedule validated against original
        multiplicity and period constraints.

    Raises:
        RotationOptimizationError: Required backend is unavailable/fails, no feasible
            incumbent exists or extracted schedule violates constraints.
    """
    solver: pulp.LpSolver
    if backend == RotationBackend.CBC:
        solver = pulp.PULP_CBC_CMD(
            msg=False, timeLimit=problem.time_limit_seconds, gapRel=RELATIVE_GAP
        )
    else:
        solver = pulp.HiGHS(
            msg=False, timeLimit=problem.time_limit_seconds, gapRel=RELATIVE_GAP
        )
    try:
        if not solver.available():
            raise RotationOptimizationError(
                f"The required {backend.value} is unavailable."
            )
        model.solve(solver)
    except (pulp.PulpSolverError, OSError, RuntimeError) as error:
        raise RotationOptimizationError(
            f"The required {backend.value} solver failed: {error}"
        ) from error
    if model.status not in (
        pulp.LpStatusOptimal,
        pulp.LpStatusNotSolved,
    ) or model.sol_status not in (
        pulp.LpSolutionOptimal,
        pulp.LpSolutionIntegerFeasible,
    ):
        name = pulp.LpStatus.get(model.status, str(model.status))
        raise RotationOptimizationError(f"No feasible rotation returned: {name}.")
    schedule = _extract(problem, variables)
    try:
        problem.validate_schedule(schedule)
    except ValueError as error:
        raise RotationOptimizationError(str(error)) from error
    status = (
        RotationSolveStatus.OPTIMAL
        if model.status == pulp.LpStatusOptimal
        and model.sol_status == pulp.LpSolutionOptimal
        else RotationSolveStatus.FEASIBLE
    )
    return status, schedule


def _number(variable: pulp.LpVariable) -> float:
    """Read only; integer feasibility is checked separately during extraction.

    Args:
        variable: Solved PuLP variable expected to have a finite numeric value.

    Returns:
        Finite solver value without rounding or clamping.

    Raises:
        RotationOptimizationError: Solver value is absent or nonfinite.
    """
    value = pulp.value(variable)
    if value is None or not isfinite(value):
        raise RotationOptimizationError(
            "The solver returned an absent/nonfinite value."
        )
    return value


def _extract(
    problem: RotationProblem, variables: Variables
) -> tuple[WorkerRotation, ...]:
    """Read model values only; select values above 0.5 after binary-distance validation.

    Args:
        problem: Validated original row/period ordering and exact target keys.
        variables: Solved complete worker/period/target binary map.

    Returns:
        Worker rotations in original worker and period order, with exactly one selected
        target per block.

    Raises:
        RotationOptimizationError: A value is absent/nonfinite/nonbinary within
            tolerance or a block has zero/multiple selected targets.
        KeyError: The internal variable map lacks a required index/key.
    """
    rows = []
    for worker, current in enumerate(problem.current):
        keys = []
        for block in range(problem.num_blocks):
            selected = []
            for key in problem.target_keys:
                value = _number(variables[worker, block, key])
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
        rows.append(WorkerRotation(current.worker_id, tuple(keys)))
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

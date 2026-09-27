"""Pure optimization services used by JROT background workers."""

from __future__ import annotations

from collections import Counter

import pulp


class RotationOptimizationError(RuntimeError):
    pass


def active_solver_backend():
    """Return the preferred available MILP backend used by JROT."""
    if hasattr(pulp, "HiGHS") and pulp.HiGHS(msg=False).available():
        return "HiGHS"
    if pulp.PULP_CBC_CMD(msg=False).available():
        return "CBC"
    raise RotationOptimizationError(
        "No supported optimization solver is available. Install highspy or CBC."
    )


def _make_solver(time_limit):
    options = {"msg": False, "timeLimit": time_limit, "gapRel": 0.01}
    if active_solver_backend() == "HiGHS":
        return pulp.HiGHS(**options)
    return pulp.PULP_CBC_CMD(**options)


def optimize_single_tool(
    worker_ids,
    current_assignments,
    job_risk,
    num_blocks,
    time_limit,
):
    job_list = sorted({job for jobs in current_assignments.values() for job in jobs})
    model, variables, max_average = _base_model(
        worker_ids, current_assignments, job_list, num_blocks
    )
    for worker_id in worker_ids:
        model += (
            pulp.lpSum(
                variables[worker_id][block][job_id] * job_risk[job_id]
                for block in range(num_blocks)
                for job_id in job_list
            )
            <= max_average * num_blocks
        )
    model += max_average
    status = model.solve(_make_solver(time_limit))
    _require_solution(status)
    schedule = _extract_schedule(variables, worker_ids, job_list, num_blocks)
    return {
        worker_id: (
            jobs,
            [job_risk[job_id] for job_id in jobs],
            round(sum(job_risk[job_id] for job_id in jobs) / num_blocks, 1),
        )
        for worker_id, jobs in schedule.items()
    }


def optimize_all_tools(
    worker_ids,
    current_assignments,
    tool_risk,
    num_blocks,
    time_limit,
):
    job_list = sorted({job for jobs in current_assignments.values() for job in jobs})
    model, variables, _ = _base_model(
        worker_ids, current_assignments, job_list, num_blocks
    )
    tools = sorted(tool_risk)
    ceilings = model.add_variable_dicts("tool_ceiling", tools, lowBound=0)
    floors = model.add_variable_dicts("tool_floor", tools, lowBound=0)
    averages = {}
    for worker_id in worker_ids:
        for tool_id in tools:
            average = pulp.lpSum(
                variables[worker_id][block][job_id] * tool_risk[tool_id][job_id]
                for block in range(num_blocks)
                for job_id in job_list
            ) / num_blocks
            averages[worker_id, tool_id] = average
            model += average <= ceilings[tool_id]
            model += average >= floors[tool_id]

    ceiling_objective = pulp.lpSum(ceilings[tool_id] for tool_id in tools)
    model += ceiling_objective
    status = model.solve(_make_solver(time_limit))
    _require_solution(status)
    best_ceilings = {tool_id: pulp.value(ceilings[tool_id]) for tool_id in tools}
    for tool_id, ceiling in best_ceilings.items():
        model += ceilings[tool_id] <= ceiling + 1e-4
    model.setObjective(
        pulp.lpSum(ceilings[tool_id] - floors[tool_id] for tool_id in tools)
    )
    status = model.solve(_make_solver(time_limit))
    _require_solution(status)
    return _extract_schedule(variables, worker_ids, job_list, num_blocks)


def _base_model(worker_ids, current_assignments, job_list, num_blocks):
    if not worker_ids or not job_list:
        raise RotationOptimizationError("The rotation must contain Workers and Job targets.")
    if any(len(current_assignments.get(worker_id, ())) != num_blocks for worker_id in worker_ids):
        raise RotationOptimizationError("Every Worker must have one Job in every time block.")

    model = pulp.LpProblem("JobRotationOptimization", pulp.LpMinimize)
    variables = model.add_variable_dicts(
        "assign", (worker_ids, range(num_blocks), job_list), cat="Binary"
    )
    for worker_id in worker_ids:
        for block in range(num_blocks):
            model += pulp.lpSum(
                variables[worker_id][block][job_id] for job_id in job_list
            ) == 1
    totals = Counter(
        job_id
        for jobs in current_assignments.values()
        for job_id in jobs
    )
    for job_id in job_list:
        model += pulp.lpSum(
            variables[worker_id][block][job_id]
            for worker_id in worker_ids
            for block in range(num_blocks)
        ) == totals[job_id]
    for block in range(num_blocks):
        for job_id in job_list:
            model += pulp.lpSum(
                variables[worker_id][block][job_id] for worker_id in worker_ids
            ) <= 1
    max_average = model.add_variable("max_average", lowBound=0)
    return model, variables, max_average


def _require_solution(status):
    if hasattr(status, "has_solution"):
        if status.has_solution:
            return
        status_value = getattr(status, "status", status)
        status_name = getattr(status_value, "name", str(status_value))
        raise RotationOptimizationError(f"The solver finished with status: {status_name}.")
    status_name = pulp.LpStatus.get(status, str(status))
    if status_name not in {"Optimal", "Not Solved"}:
        raise RotationOptimizationError(f"The solver finished with status: {status_name}.")


def _extract_schedule(variables, worker_ids, job_list, num_blocks):
    schedule = {worker_id: [] for worker_id in worker_ids}
    for worker_id in worker_ids:
        for block in range(num_blocks):
            selected = [
                job_id
                for job_id in job_list
                if (pulp.value(variables[worker_id][block][job_id]) or 0) > 0.5
            ]
            if len(selected) != 1:
                raise RotationOptimizationError(
                    "The solver did not return a complete feasible schedule."
                )
            schedule[worker_id].append(selected[0])
    return schedule

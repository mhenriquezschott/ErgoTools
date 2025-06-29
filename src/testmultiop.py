# -*- coding: utf-8 -*-
"""
optimize_rotation_multi_tool.py
--------------------------------
Standalone script *and* helper module that:

1. Builds an initial round‑robin rotation schedule with random risk
   values for LiFFT, DUET and ST.
2. Prints **baseline** average risks per worker.
3. Optimises the rotation with a two‑stage lexicographic MILP.
4. Prints **optimised** averages.

New in this version
-------------------
* Verbose progress messages (`verbose=True`)
* Optional `time_limit` (in seconds) passed to the MILP solver.
* Graceful exit: if the solver hits the time limit the best incumbent
  solution is still extracted and displayed.

Requires Python ≥3.9, Pyomo ≥6 and a MILP solver (GLPK used here).
"""

from __future__ import annotations

import random
import time
from typing import Dict, List, Sequence

from pyomo.environ import (
    Binary,
    ConcreteModel,
    Constraint,
    Objective,
    Set,
    SolverFactory,
    Var,
    minimize,
    value,
)
from pyomo.opt import TerminationCondition

# ---------------------------------------------------------------------------
# Utility: unified time‑limit handling for common solvers                    |
# ---------------------------------------------------------------------------

def _solve_with_limit(model, solver_name: str, time_limit: int | None, tee: bool):
    solver = SolverFactory(solver_name)
    if time_limit is not None:
        if solver_name == "glpk":
            solver.options["tmlim"] = time_limit  # seconds
        elif solver_name == "cbc":
            solver.options["seconds"] = time_limit
        elif solver_name.startswith("gurobi"):
            solver.options["TimeLimit"] = time_limit
    return solver.solve(model, tee=tee)

# ---------------------------------------------------------------------------
# Core optimiser                                                             |
# ---------------------------------------------------------------------------
def optimise_multi_tool(
    worker_ids, job_list, num_blocks, tool_risk,
    solver_name="glpk", time_limit=None, mip_gap=None, verbose=True
):
    """
    Two-stage MILP with *per-tool* fairness.

    Stage 1  minimise  Σ_t g_max[t]       (lowest possible worst average
                                             inside each tool)
    Stage 2  minimise  Σ_t (g_max[t]−g_min[t])
               subject to the g_max from Stage 1
    """
    import time
    from typing import Dict, List
    from pyomo.environ import (
        ConcreteModel, Set, Var, Binary, Constraint,
        Objective, minimize, SolverFactory, value
    )

    # ---------- helper: configure solver ----------------------------------
    def _make_solver(name):
        s = SolverFactory(name)
        if time_limit is not None:
            if name == "glpk":
                s.options["tmlim"] = time_limit
            elif name == "cbc":
                s.options["seconds"] = time_limit
            elif name.startswith("gurobi"):
                s.options["TimeLimit"] = time_limit
        if mip_gap is not None:
            if name == "glpk":
                s.options["mipgap"] = mip_gap
            elif name == "cbc":
                s.options["ratio"] = mip_gap
            elif name.startswith("gurobi"):
                s.options["MIPGap"] = mip_gap
        return s

    t0 = time.time()
    if verbose:
        print("\n[OPT] Building MILP model …")

    # ---------- model skeleton --------------------------------------------
    m = ConcreteModel("PerToolFairness")
    m.W = Set(initialize=list(worker_ids))
    m.B = Set(initialize=range(num_blocks))
    m.J = Set(initialize=list(job_list))
    m.T = Set(initialize=list(tool_risk))

    m.x = Var(m.W, m.B, m.J, domain=Binary)

    # assignment constraints ------------------------------------------------
    m.one_job_per_worker_block = Constraint(
        m.W, m.B, rule=lambda md, w, b: sum(md.x[w, b, j] for j in md.J) == 1
    )
    m.one_worker_per_job_block = Constraint(
        m.B, m.J, rule=lambda md, b, j: sum(md.x[w, b, j] for w in md.W) <= 1
    )
    m.unique_job_per_worker = Constraint(
        m.W, m.J, rule=lambda md, w, j: sum(md.x[w, b, j] for b in md.B) <= 1
    )

    # average risk per worker-tool -----------------------------------------
    inv_blocks = 1.0 / num_blocks
    m.avgRisk = Var(m.W, m.T)
    m.avgRisk_def = Constraint(
        m.W, m.T,
        rule=lambda md, w, t: md.avgRisk[w, t] ==
        inv_blocks * sum(md.x[w, b, j] * tool_risk[t].get(j, 0.0)
                         for b in md.B for j in md.J)
    )

    # per-tool upper / lower bounds ----------------------------------------
    m.g_max = Var(m.T)                          # worst avg in tool t
    m.g_min = Var(m.T)                          # best  avg in tool t
    m.upper_tool = Constraint(
        m.W, m.T, rule=lambda md, w, t: md.avgRisk[w, t] <= md.g_max[t]
    )
    m.lower_tool = Constraint(
        m.W, m.T, rule=lambda md, w, t: md.avgRisk[w, t] >= md.g_min[t]
    )

    # objectives ------------------------------------------------------------
    m.o1 = Objective(expr=sum(m.g_max[t] for t in m.T), sense=minimize)
    m.o2 = Objective(expr=sum(m.g_max[t] - m.g_min[t] for t in m.T),
                     sense=minimize)
    m.o2.deactivate()

    # ---------- stage 1 ----------------------------------------------------
    if verbose:
        print("[OPT] Stage 1 – minimise per-tool ceilings …")
    solver = _make_solver(solver_name)
    res1 = solver.solve(m, tee=verbose)
    if verbose:
        print("[OPT] Stage 1 done – Σ g_max =", round(sum(value(m.g_max[t]) for t in m.T), 2))

    # ---------- stage 2 ----------------------------------------------------
    # lock in the ceilings we just found
    for t in m.T:
        m.g_max[t].fix(value(m.g_max[t]))
    m.o1.deactivate(); m.o2.activate()

    if verbose:
        print("[OPT] Stage 2 – minimise per-tool spreads …")
    solver = _make_solver(solver_name)
    res2 = solver.solve(m, tee=verbose)
    if verbose:
        spread = sum(value(m.g_max[t] - m.g_min[t]) for t in m.T)
        print(f"[OPT] Stage 2 done – total spread = {spread:.2f}")
        print(f"[OPT] Total time: {time.time() - t0:.1f} s")

    # ---------- extract schedule ------------------------------------------
    schedule: Dict[str, List[str]] = {w: [""] * num_blocks for w in worker_ids}
    for w in worker_ids:
        for b in m.B:
            for j in job_list:
                if value(m.x[w, b, j]) > 0.5:
                    schedule[w][b] = j
                    break
    return schedule










# ---------------------------------------------------------------------------
# FULL REPLACEMENT OF optimise_multi_tool                                    |
# Minimises global spread (max - min across *all* worker-tool pairs)         |
# ---------------------------------------------------------------------------
def optimise_multi_toolSameAvgAllTools(
    worker_ids, job_list, num_blocks, tool_risk,
    solver_name="glpk", time_limit=None, mip_gap=None, verbose=True
):
    import time
    from typing import Dict, List
    from pyomo.environ import (
        ConcreteModel, Set, Var, Binary, Constraint,
        Objective, minimize, value, SolverFactory
    )

    # --- helper to configure solver ---------------------------------------
    def _make_solver(name):
        s = SolverFactory(name)
        if time_limit is not None:
            if name == "glpk":
                s.options["tmlim"] = time_limit
            elif name == "cbc":
                s.options["seconds"] = time_limit
            elif name.startswith("gurobi"):
                s.options["TimeLimit"] = time_limit
        if mip_gap is not None:
            if name == "glpk":
                s.options["mipgap"] = mip_gap
            elif name == "cbc":
                s.options["ratio"] = mip_gap
            elif name.startswith("gurobi"):
                s.options["MIPGap"] = mip_gap
        return s

    t0 = time.time()
    if verbose:
        print("\n[OPT] Building MILP model …")

    m = ConcreteModel("MultiToolRotation")
    m.W = Set(initialize=list(worker_ids))
    m.B = Set(initialize=range(num_blocks))
    m.J = Set(initialize=list(job_list))
    m.T = Set(initialize=list(tool_risk))

    m.x = Var(m.W, m.B, m.J, domain=Binary)

    # --- assignment constraints ------------------------------------------
    m.one_job_per_worker_block = Constraint(
        m.W, m.B, rule=lambda md, w, b: sum(md.x[w, b, j] for j in md.J) == 1
    )
    m.one_worker_per_job_block = Constraint(
        m.B, m.J, rule=lambda md, b, j: sum(md.x[w, b, j] for w in md.W) <= 1
    )
    m.unique_job_per_worker = Constraint(
        m.W, m.J, rule=lambda md, w, j: sum(md.x[w, b, j] for b in md.B) <= 1
    )

    inv_blocks = 1 / num_blocks
    m.avgRisk = Var(m.W, m.T)
    m.avgRisk_def = Constraint(
        m.W, m.T,
        rule=lambda md, w, t: md.avgRisk[w, t] ==
        inv_blocks * sum(md.x[w, b, j] * tool_risk[t].get(j, 0.0)
                         for b in md.B for j in md.J)
    )

    # ---------------- Stage 1: fairness ceiling ---------------------------
    m.z_max = Var()
    m.upper_z = Constraint(
        m.W, m.T, rule=lambda md, w, t: md.avgRisk[w, t] <= md.z_max
    )
    m.o1 = Objective(expr=m.z_max, sense=minimize)

    # ---------------- Stage 2: global spread ------------------------------
    m.z_min = Var()
    m.lower_z = Constraint(
        m.W, m.T, rule=lambda md, w, t: md.avgRisk[w, t] >= md.z_min
    )
    m.spread = Objective(expr=m.z_max - m.z_min, sense=minimize)
    m.spread.deactivate()

    # --- Stage 1 solve ----------------------------------------------------
    if verbose:
        print("[OPT] Stage 1 – minimise worst-case …")
    solver = _make_solver(solver_name)
    res1 = solver.solve(m, tee=verbose)
    if verbose:
        print("[OPT] Stage 1 done – z_max =", round(value(m.z_max), 2))

    # --- Stage 2 solve ----------------------------------------------------
    m.o1.deactivate()
    m.spread.activate()
    m.z_max.fix(value(m.z_max))          # keep the ceiling we just found
    if verbose:
        print("[OPT] Stage 2 – minimise global spread …")
    solver = _make_solver(solver_name)
    res2 = solver.solve(m, tee=verbose)
    if verbose:
        print("[OPT] Stage 2 done – spread =",
              round(value(m.z_max - m.z_min), 2))
        print(f"[OPT] Total time: {time.time() - t0:.1f} s")

    # --- Extract schedule -------------------------------------------------
    schedule: Dict[str, List[str]] = {w: [""] * num_blocks for w in worker_ids}
    for w in worker_ids:
        for b in m.B:
            for j in job_list:
                if value(m.x[w, b, j]) > 0.5:
                    schedule[w][b] = j
                    break
    return schedule




def optimise_multi_toolKindofWorking(
    worker_ids: Sequence[str],
    job_list: Sequence[str],
    num_blocks: int,
    tool_risk: Dict[str, Dict[str, float]],
    solver_name: str = "glpk",
    time_limit: int | None = None,      # seconds per stage
    mip_gap: float | None = None,       # stop when gap ≤ this ratio
    verbose: bool = True,
) -> Dict[str, List[str]]:
    """
    Two-stage lexicographic MILP:
    1. minimise the worst average risk across *all* workers & tools
       (variable z_max ─ fairness ceiling)
    2. with that ceiling fixed, minimise the *per-worker spread*
       max_t(avgRisk[w,t]) − min_t(avgRisk[w,t])

    Returns
    -------
    schedule : {worker_id: [job_b0, job_b1, …]}
    """
    import time
    from pyomo.environ import (
        ConcreteModel, Set, Var, Binary, Constraint, Objective,
        minimize, SolverFactory, value
    )

    # ------------------ helper to configure solver ------------------------
    def _make_solver(name: str):
        s = SolverFactory(name)
        if time_limit is not None:
            if name == "glpk":
                s.options["tmlim"] = time_limit
            elif name == "cbc":
                s.options["seconds"] = time_limit
            elif name.startswith("gurobi"):
                s.options["TimeLimit"] = time_limit
        if mip_gap is not None:
            if name == "glpk":
                s.options["mipgap"] = mip_gap
            elif name == "cbc":
                s.options["ratio"] = mip_gap
            elif name.startswith("gurobi"):
                s.options["MIPGap"] = mip_gap
        return s

    t0 = time.time()
    if verbose:
        print("\n[OPT] Building MILP model …")

    # ------------------ model skeleton -----------------------------------
    m = ConcreteModel("MultiToolRotation")
    m.W = Set(initialize=list(worker_ids))
    m.B = Set(initialize=range(num_blocks))
    m.J = Set(initialize=list(job_list))
    m.T = Set(initialize=list(tool_risk))

    m.x = Var(m.W, m.B, m.J, domain=Binary)

    # assignment constraints
    m.one_job_per_worker_block = Constraint(
        m.W, m.B, rule=lambda mod, w, b: sum(mod.x[w, b, j] for j in mod.J) == 1
    )
    m.one_worker_per_job_block = Constraint(
        m.B, m.J, rule=lambda mod, b, j: sum(mod.x[w, b, j] for w in mod.W) <= 1
    )
    m.unique_job_per_worker = Constraint(
        m.W, m.J, rule=lambda mod, w, j: sum(mod.x[w, b, j] for b in mod.B) <= 1
    )

    # average risk per worker-tool
    inv_blocks = 1.0 / num_blocks
    m.avgRisk = Var(m.W, m.T)
    m.avgRisk_def = Constraint(
        m.W, m.T,
        rule=lambda mod, w, t: mod.avgRisk[w, t] ==
        inv_blocks * sum(
            mod.x[w, b, j] * tool_risk[t].get(j, 0.0)
            for b in mod.B for j in mod.J)
    )

    # fairness ceiling z_max
    m.z_max = Var()
    m.upper_z = Constraint(
        m.W, m.T, rule=lambda mod, w, t: mod.avgRisk[w, t] <= mod.z_max
    )

    # ---------- spread variables (stage-2) --------------------------------
    m.maxRisk = Var(m.W)
    m.minRisk = Var(m.W)

    m.maxRisk_def = Constraint(
        m.W, m.T, rule=lambda mod, w, t: mod.maxRisk[w] >= mod.avgRisk[w, t]
    )
    m.minRisk_def = Constraint(
        m.W, m.T, rule=lambda mod, w, t: mod.minRisk[w] <= mod.avgRisk[w, t]
    )

    # objective 1: minimise the ceiling
    m.o1 = Objective(expr=m.z_max, sense=minimize)

    # objective 2: minimise total spread
    m.o2 = Objective(
        expr=sum(m.maxRisk[w] - m.minRisk[w] for w in m.W),
        sense=minimize
    )
    m.o2.deactivate()

    # ---------------- stage-1 solve ---------------------------------------
    if verbose:
        print("[OPT] Stage 1 (fairness) – solving …")
    solver = _make_solver(solver_name)
    res1 = solver.solve(m, tee=verbose)
    if verbose:
        print("[OPT] Stage 1 done – z_max =", round(value(m.z_max), 3),
              "| status:", res1.solver.status)

    # ---------------- stage-2 solve ---------------------------------------
    m.z_max.fix(value(m.z_max))
    m.o1.deactivate()
    m.o2.activate()
    if verbose:
        print("[OPT] Stage 2 (spread) – solving …")
    solver = _make_solver(solver_name)
    res2 = solver.solve(m, tee=verbose)
    if verbose:
        print("[OPT] Stage 2 done – status:",
              res2.solver.status, "/", res2.solver.termination_condition)
        print(f"[OPT] Total time: {time.time() - t0:.1f} s")

    # ---------------- extract schedule ------------------------------------
    schedule: Dict[str, List[str]] = {w: [""] * num_blocks for w in worker_ids}
    for w in worker_ids:
        for b in m.B:
            for j in job_list:
                if value(m.x[w, b, j]) > 0.5:
                    schedule[w][b] = j
                    break
    return schedule


# ---------------------------------------------------------------------------
# Helper functions for the demo                                              |
# ---------------------------------------------------------------------------

def average_risk(schedule: Dict[str, List[str]], tool_risk: Dict[str, Dict[str, float]]):
    num_blocks = len(next(iter(schedule.values())))
    return {
        t: {
            w: round(sum(tool_risk[t].get(j, 0.0) for j in jobs) / num_blocks, 1)
            for w, jobs in schedule.items()
        }
        for t in tool_risk
    }


def print_schedule(title: str, schedule: Dict[str, List[str]], tool_risk):
    print(f"\n=== {title} ===")
    avgs = average_risk(schedule, tool_risk)
    for t in tool_risk:
        print(f"\n[{t}]")
        for w in sorted(schedule):
            print(f"{w}: {schedule[w]} -> Avg: {avgs[t][w]}%")


def baseline_round_robin(workers, jobs, num_blocks):
    return {w: [jobs[(idx + b) % len(jobs)] for b in range(num_blocks)] for idx, w in enumerate(workers)}



# ---------------------------------------------------------------------------
# Random, non-repeating baseline schedule
# ---------------------------------------------------------------------------
def baseline_random(
    workers: Sequence[str],
    jobs: Sequence[str],
    num_blocks: int,
    rng: random.Random = random,
) -> Dict[str, List[str]]:
    """
    Create a starting rotation that is *random* yet feasible:

    * Each block (column) is a random permutation of `jobs`, so every
      job appears exactly once per block.
    * Requires len(workers) == len(jobs).
    """
    if len(workers) != len(jobs):
        raise ValueError("baseline_random needs len(workers) == len(jobs)")

    schedule: Dict[str, List[str]] = {w: [] for w in workers}
    for _ in range(num_blocks):
        perm = jobs[:]
        rng.shuffle(perm)
        for w, j in zip(workers, perm):
            schedule[w].append(j)
    return schedule



# ---------------------------------------------------------------------------
# Annotate job list with risk values (use “@” as delimiter)                 |
# ---------------------------------------------------------------------------
def annotated(jobs: List[str], risk_map: Dict[str, float]) -> str:
    """Return 'Job-01@12.3 Job-04@40.5 …'."""
    #return " ".join(f"{j}@{risk_map.get(j, 0.0):.1f}" for j in jobs)
    return " ".join(f"{j}@{risk_map.get(j, 0.0):04.1f}" for j in jobs)


# ---------------------------------------------------------------------------
# Pretty printer with per-job risks                                         |
# ---------------------------------------------------------------------------
def print_schedule(
    title: str,
    schedule: Dict[str, List[str]],
    tool_risk: Dict[str, Dict[str, float]],
) -> None:
    """
    Print, for every tool and worker:
        Worker: Job-ID:risk Job-ID:risk … -> Avg: xx.x%
    """
    print(f"\n=== {title} ===")
    num_blocks = len(next(iter(schedule.values())))

    for tool, risk_map in tool_risk.items():
        print(f"\n[{tool}]")
        for w in sorted(schedule):
            jobs = schedule[w]
            avg = sum(risk_map.get(j, 0.0) for j in jobs) / num_blocks
            print(f"{w}: {annotated(jobs, risk_map)} -> Avg: {avg:.1f}%")



# ---------------------------------------------------------------------------
# Helper: draw a "very low / medium / very high" risk value                 |
# ---------------------------------------------------------------------------
def random_risk() -> float:
    """
    30 % chance of   0–10 %
    40 % chance of  10–60 %
    30 % chance of  60–100 %
    """
    r = random.random()
    if r < 0.30:                      # very low
        return round(random.uniform(0, 10), 1)
    elif r < 0.70:                    # medium
        return round(random.uniform(10, 60), 1)
    else:                             # very high
        return round(random.uniform(60, 100), 1)



# ---------------------------------------------------------------------------
# Demo CLI                                                                   |
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # --------- timing header ------------------------------------------------
    import time
    from datetime import datetime

    start_ts = time.time()
    print(f"\n=== Run started  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

    # --------- demo data ----------------------------------------------------
    import random

    random.seed(1)

    #workers     = [f"V{i:03d}" for i in range(1, 9)]          # 8 workers
    #jobs        = [f"Job-{i:02d}" for i in range(1, 9)]        # 8 jobs
    #num_blocks  = 4
    
    #workers    = [f"V{i:03d}"  for i in range(1, 5)]   # 4 workers
    #jobs       = [f"Job-{i:02d}" for i in range(1, 5)]  # 4 jobs
    #num_blocks = 4                                     # 4 time-blocks


    workers     = [f"V{i:03d}" for i in range(1, 7)]          # 6 workers
    jobs        = [f"Job-{i:02d}" for i in range(1, 7)]        # 6 jobs
    num_blocks  = 4
    
    
    tools       = ["LiFFT", "DUET", "ST"]

    # random risk table (5 % – 70 %)
    tool_risk = {
        t: {j: round(random.uniform(3, 85), 1) for j in jobs} for t in tools
    }
    #tool_risk = {
    #    t: {j: random_risk() for j in jobs} for t in tools
    #}

    # --------- baseline schedule & metrics ---------------------------------
    #base_sched = baseline_round_robin(workers, jobs, num_blocks)
    #print_schedule("Original Average Risk per Worker", base_sched, tool_risk)
    base_sched = baseline_random(workers, jobs, num_blocks)
    print_schedule("Original Average Risk per Worker", base_sched, tool_risk)

    # --------- optimisation -------------------------------------------------
    opt_sched = optimise_multi_tool(
        worker_ids=workers,
        job_list=jobs,
        num_blocks=num_blocks,
        tool_risk=tool_risk,
        solver_name="highs",  # glpk, cbc, highs
        #time_limit=1800,    # seconds per stage
        time_limit=180,    # seconds per stage
        mip_gap=0.01,      # stop when gap ≤ 1 %
        verbose=True,
    )
    print_schedule("Original Average Risk per Worker", base_sched, tool_risk)

    print_schedule("Optimised Average Risk per Worker", opt_sched, tool_risk)

    # --------- timing footer ------------------------------------------------
    end_ts = time.time()
    print(f"\n=== Run finished : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    print(f"Total wall-clock time: {end_ts - start_ts:.1f} s")


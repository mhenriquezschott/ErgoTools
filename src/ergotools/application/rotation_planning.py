"""Prepare/freeze/validate real guided planning without Qt, SQL or solver imports.

Application layer. Resolve explicitly selected neighboring accepted runs, retain
their boundary evidence, and reject retired inputs before result acceptance. A
feasibility proposal never becomes an observed baseline or a claimed optimized
result.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime

from ergotools.domain.job_catalog import JobCatalog
from ergotools.domain.job_risk import JobRiskCatalog
from ergotools.domain.rotation import RotationRisk, RotationSolution
from ergotools.domain.rotation_constraints import BoundaryExposure, RotationBoundary
from ergotools.domain.rotation_planning import (
    RotationPlanningProblem,
    rotation_interval,
)
from ergotools.domain.rotation_scenario import (
    ROTATION_RUN_MODEL_VERSION,
    RotationCoefficient,
    RotationRun,
    RotationScenario,
)
from ergotools.domain.task_catalog import TaskDefinition
from ergotools.domain.work_hierarchy import WorkHierarchy


def _date_json(value: object) -> str:
    """Serialize only typed local/UTC temporal values in canonical run signatures.

    Args:
        value: Nonprimitive encountered by the standard JSON encoder.

    Returns:
        Exact ISO datetime/date, without rounding any coefficients.

    Raises:
        TypeError: An unsupported nonprimitive entered the immutable contract.
    """
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError("Unsupported run signature value.")


def rotation_run_signature(run: RotationRun) -> str:
    """Bind a neighboring reference to its exact immutable accepted run, not its name.

    Args:
        run: Typed complete evidence including frozen inputs/coefficients/labels.

    Returns:
        Deterministic SHA-256, independent of database timestamps and scenario
        rename.
    """
    return hashlib.sha256(
        json.dumps(
            asdict(run),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
            default=_date_json,
        ).encode("utf-8")
    ).hexdigest()


def capture_rotation_boundary(
    source: RotationScenario, *, previous: bool
) -> RotationBoundary:
    """Copy the exact last/first block from one explicitly selected accepted run.

    Args:
        source: Selected neighboring scenario; caller checks live freshness
        separately.
        previous: True takes its last block; False its first block.

    Returns:
        Independently readable fixed local interval and per-worker frozen tool
        evidence.

    Raises:
        ValueError: No supported accepted run is present.
    """
    run = source.run
    if run is None or run.contract_version != ROTATION_RUN_MODEL_VERSION:
        raise ValueError("Choose a supported accepted neighboring run.")
    start, end = rotation_interval(run.inputs)
    block = -1 if previous else 0
    rows = []
    for row in run.arrangement:
        key = row.target_keys[block]
        values = tuple(
            RotationRisk(key, c.measurement.kind, c.measurement.probability_percent)
            for c in run.coefficients
            if c.target_key == key and c.measurement.probability_percent is not None
        )
        rows.append(BoundaryExposure(row.worker_id, key, values))
    return RotationBoundary(
        source.scenario_id, rotation_run_signature(run), start, end, tuple(rows)
    )


def neighbors_are_current(
    scenario: RotationScenario,
    scenarios: tuple[RotationScenario, ...],
    hierarchy: WorkHierarchy,
    jobs: JobCatalog,
    risks: JobRiskCatalog,
) -> bool:
    """Check the freshness of explicitly selected neighboring runs.

    Args:
        scenario: Current plan with optional copied boundary snapshots.
        scenarios: Same-project current catalog.
        hierarchy: Current worker/organization snapshot.
        jobs: Current Job/placement snapshot.
        risks: Current Job values used to qualify neighboring accepted runs.

    Returns:
        False for missing, unsupported, stale or altered fixed boundary evidence.
        Neighbor-of-neighbor compliance is not inferred by this local boundary
        check.
    """
    from ergotools.application.rotation_scenarios import own_run_is_current

    for boundary, previous in (
        (scenario.inputs.previous, True),
        (scenario.inputs.following, False),
    ):
        if boundary is None:
            continue
        source = next(
            (
                s
                for s in scenarios
                if s.scenario_id == boundary.scenario_id
                and s.project_id == scenario.project_id
            ),
            None,
        )
        if (
            source is None
            or source.scenario_id == scenario.scenario_id
            or not own_run_is_current(source, hierarchy, jobs, risks)
        ):
            return False
        if capture_rotation_boundary(source, previous=previous) != boundary:
            return False
    return True


@dataclass(frozen=True, slots=True)
class PreparedRotationPlan:
    """Detached solve context; no widget/repository/thread may mutate this value.

    Attributes:
        scenario_id: Exact target identity captured on the GUI thread.
        problem: Complete input/timing/rules and available selected coefficients.
        coefficients: Exact complete selected-tool Job sources/results and task
        labels.
        job_labels: Ordered position/name pairs, including labels for unassessed
        generation.
        worker_labels: Ordered literal worker IDs/names.
    """

    scenario_id: str
    problem: RotationPlanningProblem
    coefficients: tuple[RotationCoefficient, ...]
    job_labels: tuple[tuple[str, str], ...]
    worker_labels: tuple[str, ...]


def prepare_rotation_plan(
    scenario: RotationScenario,
    scenarios: tuple[RotationScenario, ...],
    hierarchy: WorkHierarchy,
    jobs: JobCatalog,
    risks: JobRiskCatalog,
    definitions: tuple[TaskDefinition, ...] = (),
    *,
    generation: bool = False,
    time_limit_seconds: float = 60,
) -> PreparedRotationPlan:
    """Freeze real data and validate references before solving.

    Args:
        scenario: Explicit selected scenario; no baseline is invented for the No
        path.
        scenarios: Current same-project catalog for fixed neighbor freshness.
        hierarchy: Current real participants and workplace records.
        jobs: Current Job activities/placements.
        risks: Exact single current Job/tool measurements.
        definitions: Project-local reusable labels resolved once into immutable
        evidence.
        generation: True requests feasibility, allowing absent risks if no High rule
        uses them.
        time_limit_seconds: Per-stage positive bounded solver budget.

    Returns:
        Complete detached solve context with no data writes or generated default
        schedule.

    Raises:
        ValueError: Ownership, setup, requested boundary or required coefficients
        are invalid.
    """
    if not (
        scenario.project_id
        == hierarchy.work.project_id
        == jobs.project_id
        == risks.project_id
    ):
        raise ValueError("Planning catalogs belong to different projects.")
    scenario.inputs.validate_references(hierarchy, jobs)
    if not neighbors_are_current(scenario, scenarios, hierarchy, jobs, risks):
        raise ValueError(
            "Neighbor boundary is not checked: resolve its missing/stale accepted run."
        )
    if generation and scenario.inputs.baseline is not None:
        raise ValueError("Generate a proposal only when no observed rotation exists.")
    labels = {d.definition_id: d.name for d in definitions}
    names = {j.job_id: j.name or j.job_id for j in jobs.jobs}
    workers = {
        w.worker_id: " · ".join(
            (w.worker_id, " ".join(v for v in (w.first_name, w.last_name) if v))
        )
        for w in hierarchy.work.workers
    }
    coefficients = []
    for target in scenario.inputs.targets:
        for kind in scenario.inputs.tools:
            item = next(
                (
                    m
                    for m in risks.for_job(target.job_id).measurements
                    if m.kind is kind and m.complete
                ),
                None,
            )
            if item is not None:
                task_names = (
                    tuple(
                        labels[t.task_definition_id]
                        if t.task_definition_id is not None
                        else t.task_name
                        for t in item.source.tasks
                    )
                    if item.source
                    else ()
                )
                coefficients.append(
                    RotationCoefficient(
                        target.key, names[target.job_id], item, task_names
                    )
                )
    frozen = tuple(coefficients)
    values = tuple(
        RotationRisk(
            c.target_key, c.measurement.kind, c.measurement.probability_percent
        )
        for c in frozen
        if c.measurement.probability_percent is not None
    )
    problem = RotationPlanningProblem(
        scenario.inputs, values, time_limit_seconds, generation
    )
    return PreparedRotationPlan(
        scenario.scenario_id,
        problem,
        frozen,
        tuple((t.key, names[t.job_id]) for t in scenario.inputs.targets),
        tuple(workers[w.worker_id] for w in scenario.inputs.workers),
    )


def accepted_rotation_run(
    prepared: PreparedRotationPlan, solution: RotationSolution
) -> RotationRun:
    """Build immutable evidence from an independently validated solution.

    Args:
        prepared: Captured optimization context, never a feasibility-only
        generation.
        solution: Backend output validated again without trusting status alone.

    Returns:
        Current-model frozen run with UTC completion and explicit numerical
        settings.

    Raises:
        ValueError: Generation cannot be presented as optimization, or
        staffing/rules fail.
    """
    if prepared.problem.generation:
        raise ValueError("A feasibility proposal is not an optimized run.")
    prepared.problem.validate_schedule(solution.schedule)
    return RotationRun(
        prepared.problem.inputs,
        prepared.coefficients,
        solution.schedule,
        solution.backend,
        solution.stages,
        (
            ("time_limit_seconds", str(prepared.problem.time_limit_seconds)),
            ("relative_gap", "0.01"),
            ("ceiling_tolerance", "0.0001"),
            ("score", "duration_weighted_job_risk_index"),
            ("primary_objective", "minimize_maximum_indices"),
            (
                "secondary_objective",
                "minimize_ranges" if len(solution.stages) == 2 else "not_recorded",
            ),
        ),
        datetime.now(UTC),
        ROTATION_RUN_MODEL_VERSION,
        prepared.worker_labels,
    )

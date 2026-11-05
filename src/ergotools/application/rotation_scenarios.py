"""Pure named-scenario lifecycle and borrowed project persistence capability.

Application layer. Creation is explicit, selection is separate view state, and
duplicate operations never mutate the source. This checkpoint does not run solvers
or implement guided screens. Callers own previews/confirmation; the shared project
owns history/Save.
"""

from dataclasses import replace
from datetime import date
from typing import Protocol, runtime_checkable

from ergotools.application.rotation_timing import ShiftTimingTemplate, shift_clock
from ergotools.application.task_catalog import label_assessment_task
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_catalog import JobCatalog
from ergotools.domain.job_risk import JobRiskCatalog, JobRiskMeasurement
from ergotools.domain.rotation import RotationRisk
from ergotools.domain.rotation_scenario import (
    ROTATION_RUN_MODEL_VERSION,
    RotationCoefficient,
    RotationInputs,
    RotationRun,
    RotationScenario,
)
from ergotools.domain.rotation_scheme import RotationMode, RotationScheme
from ergotools.domain.task_catalog import TaskDefinition
from ergotools.domain.work_hierarchy import WorkHierarchy


@runtime_checkable
class RotationScenarioRepository(Protocol):
    """Expected-state scenario edits and independent last-viewed project state."""

    def load_rotation_scenarios(self) -> tuple[RotationScenario, ...]:
        """Read name/ID ordered plans, including explicitly untimed older schemes.

        Args:
            None.

        Returns:
            Complete immutable scenario catalog; no defaults or records are created.
        """
        ...

    def replace_rotation_scenario(
        self, expected: RotationScenario | None, replacement: RotationScenario | None
    ) -> None:
        """Accept one guarded scenario and coherent selection edit.

        Args:
            expected: Exact previous state, or None for a new independent identity.
            replacement: Desired current record, or None for explicitly confirmed
                deletion.

        Returns:
            None; Main Save publishes the accepted shared project edit.
        """
        ...

    def last_rotation_selection(self) -> str | None:
        """Read last-viewed identity without repairing absent/stale selection.

        Args:
            None.

        Returns:
            Stored ID or None; the pure opening helper chooses a fallback.
        """
        ...

    def select_rotation_scenario(self, scenario_id: str | None) -> None:
        """Accept view selection independently of scientific scenario inputs.

        Args:
            scenario_id: Existing exact identity, or None to clear explicit selection.

        Returns:
            None; selecting never creates a scenario or invalidates a run.
        """
        ...


def scenario_order(scenario: RotationScenario) -> tuple[str, str, str]:
    """Provide locale-independent name/ID fallback order without rewriting user text.

    Args:
        scenario: Typed current or unresolved older scenario.

    Returns:
        Case-folded name and identity, then exact identity as deterministic tie-breaker.
    """
    return (
        scenario.name.casefold(),
        scenario.scenario_id.casefold(),
        scenario.scenario_id,
    )


def opening_scenario(
    scenarios: tuple[RotationScenario, ...], last_viewed: str | None
) -> RotationScenario | None:
    """Choose last-viewed or first named scenario without writing a default.

    Args:
        scenarios: Complete current project catalog.
        last_viewed: Optional persisted view identity; stale values are harmless.

    Returns:
        Existing selected/fallback scenario; None means initial step/drawer-open
        creation.
    """
    return next(
        (s for s in scenarios if s.scenario_id == last_viewed),
        min(scenarios, key=scenario_order, default=None),
    )


def create_scenario(
    project_id: str, scenario_id: str, name: str, planned_date: date
) -> RotationScenario:
    """Prepare an explicit new empty plan with a user-accepted local date.

    Args:
        project_id: Current exact project identity.
        scenario_id: Caller-generated stable independent identity.
        name: Required user label, preserved literally.
        planned_date: Required local start date; never inferred for an older plan.

    Returns:
        New incomplete plan without participants, observation, inferred timing or
        result.

    Raises:
        ValueError: Date/identity/name is invalid.
    """
    if type(planned_date) is not date:
        raise ValueError("A new rotation requires its planned local date.")
    return RotationScenario(
        project_id, scenario_id, name, RotationInputs(planned_date=planned_date)
    )


def scenario_from_scheme(scheme: RotationScheme) -> RotationScenario:
    """Project a current older scheme without inventing date, times or a solved run.

    Args:
        scheme: Current saved legacy-compatible scheme with original provenance.

    Returns:
        Same identity/name/schedule and links as an explicitly untimed scenario view.
    """
    tools = (
        (scheme.primary_kind,)
        if scheme.mode is RotationMode.SINGLE_TOOL and scheme.primary_kind is not None
        else tuple(AssessmentKind)
    )
    return RotationScenario(
        scheme.project_id,
        scheme.scheme_id,
        scheme.name,
        RotationInputs(
            workers=scheme.workers,
            targets=scheme.targets,
            tools=tools,
            baseline=scheme.current,
            scope=scheme.scope,
            shift_id=scheme.scope[0].shift_id if scheme.scope else None,
        ),
        scheme.description,
        legacy_mode=scheme.mode,
        legacy_primary_kind=scheme.primary_kind,
    )


def copy_shift_timing(
    scenario: RotationScenario,
    hierarchy: WorkHierarchy,
    template: ShiftTimingTemplate,
) -> RotationScenario:
    """Copy accepted Shift clocks/timing without linking the scenario to future edits.

    Args:
        scenario: Current independent plan.
        hierarchy: Current project Shift clock context.
        template: Explicit selected reusable template, validated against that context.

    Returns:
        Plan with a complete clock/timing copy; incompatible schedules raise first.

    Raises:
        ValueError: Ownership/span or existing schedule horizon is incompatible.
    """
    if scenario.project_id != hierarchy.work.project_id:
        raise ValueError("Rotation belongs to a different project.")
    template.validate(hierarchy)
    clock = shift_clock(hierarchy, template.shift_id)
    return replace(
        scenario,
        inputs=replace(
            scenario.inputs,
            shift_id=template.shift_id,
            start_minute=clock.start_minute,
            timing=template.timing,
        ),
    )


def duplicate_scenario(
    source: RotationScenario,
    scenario_id: str,
    name: str,
    planned_date: date,
    *,
    use_optimized_baseline: bool = False,
) -> RotationScenario:
    """Prepare another independent scenario, optionally promoting a saved result once.

    Args:
        source: Original retained unchanged.
        scenario_id: New independent identity, distinct from the source.
        name: Explicit editable label for the new scenario.
        planned_date: Explicit local start date.
        use_optimized_baseline: True copies accepted run inputs and promotes its
            arrangement once; False copies current inputs as they are.

    Returns:
        New plan with source provenance and no inherited optimization claim.

    Raises:
        ValueError: Date/new identity is invalid, or the requested accepted run is
            absent.
    """
    create_scenario(source.project_id, scenario_id, name, planned_date)
    inputs = source.inputs
    if use_optimized_baseline:
        if source.run is None:
            raise ValueError("Select an accepted optimized run before reworking it.")
        inputs = replace(
            source.run.inputs, baseline=source.run.arrangement, proposed=None
        )
    return RotationScenario(
        source.project_id,
        scenario_id,
        name,
        replace(inputs, planned_date=planned_date),
        source.description,
        source.scenario_id,
    )


def own_run_is_current(
    scenario: RotationScenario,
    hierarchy: WorkHierarchy,
    jobs: JobCatalog,
    risks: JobRiskCatalog,
) -> bool:
    """Check current input, reference and coefficient freshness without solving.

    Args:
        scenario: Current editable plan and retained run.
        hierarchy: Current organization snapshot.
        jobs: Current Job/placement catalog.
        risks: Current independent Job values.

    Returns:
        False for absent/stale input, missing reference or changed Job measurements;
        renaming the scenario alone does not affect the run.
    """
    if not (
        scenario.project_id
        == hierarchy.work.project_id
        == jobs.project_id
        == risks.project_id
    ):
        return False
    if not scenario.run_matches_inputs or scenario.run is None:
        return False
    if scenario.run.contract_version != ROTATION_RUN_MODEL_VERSION:
        return False
    try:
        scenario.inputs.validate_references(hierarchy, jobs)
        for coefficient in scenario.run.coefficients:
            target = next(
                t for t in scenario.inputs.targets if t.key == coefficient.target_key
            )
            current = next(
                m
                for m in risks.for_job(target.job_id).measurements
                if m.kind is coefficient.measurement.kind
            )
            if _numerical_measurement(current) != _numerical_measurement(
                coefficient.measurement
            ):
                return False
    except (ValueError, KeyError, StopIteration):
        return False
    return True


def run_is_current(
    scenario: RotationScenario,
    hierarchy: WorkHierarchy,
    jobs: JobCatalog,
    risks: JobRiskCatalog,
    scenarios: tuple[RotationScenario, ...] = (),
) -> bool:
    """Qualify own inputs/coefficients and every explicitly frozen immediate boundary.

    Args:
        scenario: Current selected plan and retained run.
        hierarchy: Current same-project participants and organization.
        jobs: Current Job/placement data.
        risks: Current exact Job values.
        scenarios: Required current catalog when explicit neighboring references
        exist.

    Returns:
        False when any own or immediate-neighbor context is stale or unavailable.
    """
    from ergotools.application.rotation_planning import neighbors_are_current

    return own_run_is_current(
        scenario, hierarchy, jobs, risks
    ) and neighbors_are_current(scenario, scenarios, hierarchy, jobs, risks)


def freeze_rotation_coefficients(
    inputs: RotationInputs,
    jobs: JobCatalog,
    risks: JobRiskCatalog,
    definitions: tuple[TaskDefinition, ...] = (),
) -> tuple[RotationCoefficient, ...]:
    """Capture selected Job values and labels without linking to future catalog edits.

    Args:
        inputs: Exact target/tool selection for one pending run.
        jobs: Current complete Job catalog.
        risks: Current Job inputs/results in their recorded source units.
        definitions: Current project task labels for explicitly referenced occurrences.

    Returns:
        Ordered immutable coefficients, retaining original precision.

    Raises:
        ValueError: A selected Job/tool value or referenced reusable label is missing.
    """
    names = {d.definition_id: d.name for d in definitions}
    job_names = {j.job_id: j.name for j in jobs.jobs}
    coefficients = []
    try:
        for target in inputs.targets:
            for kind in inputs.tools:
                measurement = next(
                    m
                    for m in risks.for_job(target.job_id).measurements
                    if m.kind is kind
                )
                task_names = (
                    tuple(
                        names[t.task_definition_id]
                        if t.task_definition_id is not None
                        else t.task_name
                        for t in measurement.source.tasks
                    )
                    if measurement.source is not None
                    else ()
                )
                coefficients.append(
                    RotationCoefficient(
                        target.key,
                        job_names[target.job_id]
                        if job_names[target.job_id].strip()
                        else target.job_id,
                        measurement,
                        task_names,
                    )
                )
    except (KeyError, StopIteration) as error:
        raise ValueError(
            "Every selected Job/tool and reusable label must be available."
        ) from error
    return tuple(coefficients)


def _numerical_measurement(measurement: JobRiskMeasurement) -> JobRiskMeasurement:
    """Project comparison values without descriptive task metadata.

    Args:
        measurement: Current or frozen complete/partial Job measurements.

    Returns:
        Same numeric inputs/results/units and row identities, with task labels detached.
    """
    source = measurement.source
    if source is None:
        return measurement
    for task in source.tasks:
        source = label_assessment_task(source, task.task_id, None, None)
    return replace(measurement, source=source)


def apply_rotation_run(
    current: RotationScenario,
    expected_inputs: RotationInputs,
    run: RotationRun,
    hierarchy: WorkHierarchy,
    jobs: JobCatalog,
    risks: JobRiskCatalog,
    scenarios: tuple[RotationScenario, ...] = (),
) -> RotationScenario:
    """Prepare explicit result acceptance while rejecting retired solve ownership.

    Args:
        current: Latest plan, including independent name/description edits.
        expected_inputs: Exact planning snapshot captured when the solve started.
        run: Complete validated returned result context.
        hierarchy: Current project hierarchy.
        jobs: Current target/placement catalog.
        risks: Current Job coefficients and source inputs.
        scenarios: Current catalog for explicit neighboring-run freshness.

    Returns:
        Updated plan retaining its current label; the caller's guarded repository
        edit remains the sole atomic application/history boundary.

    Raises:
        ValueError: Planning inputs or selected current Job data changed during
        solving.
    """
    candidate = replace(current, run=run)
    if (
        current.inputs != expected_inputs
        or run.inputs != expected_inputs
        or not run_is_current(candidate, hierarchy, jobs, risks, scenarios)
    ):
        raise ValueError("Rotation inputs or Job values changed; optimize again.")
    from ergotools.domain.rotation_planning import RotationPlanningProblem

    RotationPlanningProblem(
        run.inputs,
        tuple(
            RotationRisk(
                c.target_key, c.measurement.kind, c.measurement.probability_percent
            )
            for c in run.coefficients
            if c.measurement.probability_percent is not None
        ),
    ).validate_schedule(run.arrangement)
    return candidate

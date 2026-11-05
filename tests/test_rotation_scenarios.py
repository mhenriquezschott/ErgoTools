"""Named-scenario lifecycle, strict codecs and immutable exact run evidence.

Pure checks use two explicit workers/Jobs and real HiGHS solves. Independent
expected matrices/scores certify that persistence does not reinterpret solver outcomes.
No maintained project, preference, reference or dependency is changed.
"""

import json
from dataclasses import replace
from datetime import UTC, date, datetime

import pytest

from ergotools.application.job_calculation import calculate_job_measurement
from ergotools.application.rotation_scenarios import (
    copy_shift_timing,
    create_scenario,
    duplicate_scenario,
    freeze_rotation_coefficients,
    opening_scenario,
    run_is_current,
    scenario_from_scheme,
)
from ergotools.application.rotation_timing import ShiftTimingTemplate
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.job_catalog import Job, JobCatalog
from ergotools.domain.job_risk import JobRiskCatalog, JobRiskMeasurement, JobRiskValues
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.rotation import (
    RotationBackend,
    RotationProblem,
    RotationRisk,
    RotationSolveStatus,
    WorkerRotation,
)
from ergotools.domain.rotation_scenario import (
    ROTATION_RUN_MODEL_VERSION,
    RotationInputs,
    RotationRun,
    RotationScenario,
)
from ergotools.domain.rotation_scheme import (
    RotationMode,
    RotationScheme,
    RotationTarget,
    RotationWorkerLink,
)
from ergotools.domain.rotation_timing import MinuteInterval, TimedBreak, equal_timing
from ergotools.domain.task_catalog import TaskDefinition
from ergotools.domain.work_catalog import WorkerEntry
from ergotools.domain.work_hierarchy import WorkHierarchy
from ergotools.infrastructure.highs_rotation_optimizer import HighsRotationOptimizer
from ergotools.infrastructure.rotation_scenario_serialization import (
    decode_scenario,
    encode_scenario,
)
from tests.test_rotation_timing_storage import timing_hierarchy


def scenario_catalogs() -> tuple[WorkHierarchy, JobCatalog, JobRiskCatalog]:
    """Build two real labeled workers/Jobs with explicit zero/high tool values.

    Args:
        None.

    Returns:
        Same-project synthetic catalogs with no assessments or permanent assignments.
    """
    hierarchy = timing_hierarchy()
    hierarchy = replace(
        hierarchy,
        work=replace(
            hierarchy.work,
            workers=(
                WorkerEntry("W1", "Ana", "Ruiz"),
                WorkerEntry("W2", "Bruno", "Silva"),
            ),
        ),
    )
    jobs = JobCatalog("timing", (Job("J1", "Packing"), Job("J2", "Palletizing")))
    risks = JobRiskCatalog(
        "timing",
        tuple(
            JobRiskValues(
                job,
                tuple(
                    JobRiskMeasurement(
                        kind,
                        0.001 if job == "J1" else 0.01,
                        0 if job == "J1" else 100,
                        "Metric",
                    )
                    for kind in AssessmentKind
                ),
            )
            for job in ("J1", "J2")
        ),
    )
    return hierarchy, jobs, risks


def scenario_inputs() -> RotationInputs:
    """Build a dated No-path plan with two equal blocks and no observed baseline.

    Args:
        None.

    Returns:
        Complete participant/timing inputs independent of Shift template mutation.
    """
    return RotationInputs(
        date(2026, 11, 2),
        shift_id="Day",
        start_minute=480,
        timing=equal_timing(480, 2),
        workers=(RotationWorkerLink("W1"), RotationWorkerLink("W2")),
        targets=(RotationTarget("J1"), RotationTarget("J2")),
    )


def balanced_rows(inputs: RotationInputs) -> tuple[WorkerRotation, ...]:
    """Construct an independently obvious two-Job balanced matrix.

    Args:
        inputs: Two workers, positions and work blocks.

    Returns:
        Alternating target rows, one worker at each position in every block.
    """
    a, b = (t.key for t in inputs.targets)
    return (WorkerRotation("W1", (a, b)), WorkerRotation("W2", (b, a)))


def scenario_with_run() -> RotationScenario:
    """Provide explicit accepted-context evidence without claiming a solver was invoked.

    Args:
        None.

    Returns:
        Balanced all-tool run with known coefficients and UTC completion metadata.
    """
    _, jobs, risks = scenario_catalogs()
    inputs = scenario_inputs()
    run = RotationRun(
        inputs,
        freeze_rotation_coefficients(inputs, jobs, risks),
        balanced_rows(inputs),
        RotationBackend.HIGHS,
        (RotationSolveStatus.FEASIBLE, RotationSolveStatus.FEASIBLE),
        (("time_limit_seconds", "60"), ("relative_gap", "0.01")),
        datetime(2026, 10, 31, 12, 0, tzinfo=UTC),
        ROTATION_RUN_MODEL_VERSION,
        ("W1 · Ana Ruiz", "W2 · Bruno Silva"),
    )
    return RotationScenario("timing", "rotation-1", "Morning packing", inputs, run=run)


def test_named_opening_is_read_only_and_names_never_establish_identity() -> None:
    """Choose deterministic fallback without merging independent scenarios.

    Args:
        None.

    Returns:
        None; creation requires a date and never invents an observation.
    """
    assert opening_scenario((), None) is None
    a = create_scenario("timing", "2", "alpha", date(2026, 11, 2))
    b = create_scenario("timing", "1", "Alpha", date(2026, 11, 2))
    assert opening_scenario((a, b), "stale") == b
    assert opening_scenario((a, b), "2") == a
    assert a.inputs.baseline is None and a.inputs.timing is None and a.run is None
    with pytest.raises(ValueError):
        create_scenario("timing", "x", " ", date(2026, 11, 2))
    with pytest.raises(ValueError):
        create_scenario("timing", "x", "A", None)
    with pytest.raises(ValueError):
        create_scenario("timing", "x", "A", datetime(2026, 11, 2))


def test_old_scheme_keeps_date_unknown_and_exact_original_provenance() -> None:
    """A former optimized scheme cannot become a fabricated timed accepted run.

    Args:
        None.

    Returns:
        None; links, baseline, primary model and description remain exact.
    """
    inputs = scenario_inputs()
    old = RotationScheme(
        "timing",
        "old",
        "Former plan",
        inputs.workers,
        inputs.targets,
        balanced_rows(inputs),
        mode=RotationMode.SINGLE_TOOL,
        primary_kind=AssessmentKind.DUET,
        description="Historical",
    )
    scenario = scenario_from_scheme(old)
    assert scenario.inputs.planned_date is None and scenario.inputs.timing is None
    assert scenario.inputs.baseline == old.current and scenario.run is None
    assert (
        scenario.legacy_mode is old.mode
        and scenario.legacy_primary_kind is old.primary_kind
    )
    assert decode_scenario(encode_scenario(scenario)) == scenario


def test_duplicate_optimized_baseline_promotes_once_and_preserves_source() -> None:
    """Rework creates a new named identity and leaves source observation/result intact.

    Args:
        None.

    Returns:
        None; renaming retains freshness; scientific edits retain old evidence.
    """
    source = scenario_with_run()
    before = encode_scenario(source)
    duplicate = duplicate_scenario(
        source, "new", "Alternative", date(2026, 11, 3), use_optimized_baseline=True
    )
    assert duplicate.source_scenario_id == source.scenario_id and duplicate.run is None
    assert duplicate.inputs.baseline == source.run.arrangement
    assert duplicate.inputs.planned_date == date(2026, 11, 3)
    assert encode_scenario(source) == before
    assert replace(source, name="Renamed", description="Notes").run_matches_inputs
    changed = replace(
        source, inputs=replace(source.inputs, planned_date=date(2026, 11, 5))
    )
    assert not changed.run_matches_inputs and changed.run == source.run
    assert decode_scenario(encode_scenario(changed)) == changed
    with pytest.raises(ValueError):
        duplicate_scenario(source, source.scenario_id, "Same ID", date(2026, 11, 3))
    with pytest.raises(ValueError):
        duplicate_scenario(
            replace(source, run=None),
            "new",
            "No run",
            date(2026, 11, 3),
            use_optimized_baseline=True,
        )


def test_template_copy_and_job_changes_do_not_reinterpret_retained_run() -> None:
    """Keep copied clocks independent and detect changed Job values.

    Args:
        None.

    Returns:
        None; original coefficients, labels and time pieces remain unchanged.
    """
    hierarchy, jobs, risks = scenario_catalogs()
    source = scenario_with_run()
    assert run_is_current(source, hierarchy, jobs, risks)
    inputs = source.inputs
    copied = copy_shift_timing(
        source, hierarchy, ShiftTimingTemplate("Night", equal_timing(480, 2))
    )
    assert copied.inputs.start_minute == 1320 and copied.run == source.run
    assert not copied.run_matches_inputs and inputs.start_minute == 480
    altered = replace(
        risks,
        values=(
            replace(
                risks.values[0],
                measurements=tuple(
                    replace(m, probability_percent=20)
                    for m in risks.values[0].measurements
                ),
            ),
            risks.values[1],
        ),
    )
    assert not run_is_current(source, hierarchy, jobs, altered)
    assert source.run.coefficients[0].measurement.probability_percent == 0
    assert not run_is_current(replace(source, run=None), hierarchy, jobs, risks)


@pytest.mark.parametrize(
    "mutation",
    [
        "overlap",
        "boolean_clock",
        "duplicate_worker",
        "duplicate_tool",
        "date_datetime",
        "wrong_horizon",
        "unknown_target",
        "mutable_workers",
    ],
)
def test_invalid_scenario_inputs_reject_exact_type_or_shape(mutation: str) -> None:
    """Inconsistent drafts never enter persistence or lose explicit identity.

    Args:
        mutation: Deliberate clock, identity or structural corruption.

    Returns:
        None; construction rejects before any project operation.
    """
    inputs = scenario_inputs()
    with pytest.raises(ValueError):
        if mutation == "overlap":
            replace(
                inputs,
                timing=equal_timing(
                    480,
                    2,
                    (
                        TimedBreak(MinuteInterval(1, 30)),
                        TimedBreak(MinuteInterval(20, 40)),
                    ),
                ),
            )
        elif mutation == "boolean_clock":
            replace(inputs, start_minute=True)
        elif mutation == "duplicate_worker":
            replace(inputs, workers=(inputs.workers[0],) * 2)
        elif mutation == "duplicate_tool":
            replace(inputs, tools=(AssessmentKind.LIFFT,) * 2)
        elif mutation == "date_datetime":
            replace(inputs, planned_date=datetime(2026, 11, 2))
        elif mutation == "wrong_horizon":
            replace(
                inputs,
                baseline=(WorkerRotation("W1", ("x",)), WorkerRotation("W2", ("x",))),
            )
        elif mutation == "unknown_target":
            replace(
                inputs,
                baseline=(
                    WorkerRotation("W1", ("x", "x")),
                    WorkerRotation("W2", ("x", "x")),
                ),
            )
        else:
            replace(inputs, workers=list(inputs.workers))


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown",
        "duplicate",
        "version_bool",
        "date",
        "clock_float",
        "run_digest",
        "run_missing",
        "coefficient",
        "utc_missing",
    ],
)
def test_strict_codec_rejects_corrupt_context(mutation: str) -> None:
    """Unknown/duplicate fields and changed run evidence cannot silently decode.

    Args:
        mutation: Explicit payload corruption, including tampered frozen evidence.

    Returns:
        None; precise valid payloads still roundtrip.
    """
    source = scenario_with_run()
    payload = encode_scenario(source)
    assert decode_scenario(payload) == source
    data = json.loads(payload)
    if mutation == "unknown":
        data["unknown"] = 1
    elif mutation == "version_bool":
        data["version"] = True
    elif mutation == "date":
        data["inputs"]["planned_date"] = "20261102"
    elif mutation == "clock_float":
        data["inputs"]["start_minute"] = 480.0
    elif mutation == "run_digest":
        data["run"]["coefficients"][0]["probability"] = 10
    elif mutation == "run_missing":
        del data["run"]["inputs"]
    elif mutation == "coefficient":
        data["run"]["coefficients"][0]["source"] = False
    elif mutation == "utc_missing":
        data["run"]["completed_at"] = "2026-10-31T12:00:00"
    with pytest.raises(ValueError):
        decode_scenario(
            '{"format":"x","format":"y"}'
            if mutation == "duplicate"
            else json.dumps(data)
        )


def test_frozen_task_names_sources_and_outputs_keep_calculator_precision() -> None:
    """Run evidence keeps resolved labels independently of future reusable renames.

    Args:
        None.

    Returns:
        None; exact LiFFT inputs/results, units and literal names roundtrip.
    """
    hierarchy, jobs, _ = scenario_catalogs()
    source = LifftDraft(
        MeasurementSystem.METRIC,
        (
            LifftTask(
                "task",
                30.123456789,
                49.050000001,
                100.25,
                "Fallback",
                "task-definition",
            ),
        ),
    )
    measurement = calculate_job_measurement(
        "timing", "J1", source, MeasurementSystem.METRIC
    )
    inputs = replace(scenario_inputs(), tools=(AssessmentKind.LIFFT,))
    risks = JobRiskCatalog(
        "timing", tuple(JobRiskValues(j.job_id, (measurement,)) for j in jobs.jobs)
    )
    coefficients = freeze_rotation_coefficients(
        inputs, jobs, risks, (TaskDefinition("task-definition", "Lift carton"),)
    )
    assert coefficients[0].task_names == ("Lift carton",)
    run = RotationRun(
        inputs,
        coefficients,
        balanced_rows(inputs),
        RotationBackend.CBC,
        (RotationSolveStatus.FEASIBLE,),
        (("time_limit_seconds", "60"),),
        datetime(2026, 10, 31, tzinfo=UTC),
        ROTATION_RUN_MODEL_VERSION,
        ("Ana", "Bruno"),
    )
    scenario = RotationScenario("timing", "precise", "Exact", inputs, run=run)
    assert decode_scenario(encode_scenario(scenario)) == scenario
    assert run_is_current(scenario, hierarchy, jobs, risks)
    renamed = replace(
        measurement,
        source=replace(source, tasks=(replace(source.tasks[0], task_name="Other"),)),
    )
    assert run_is_current(
        scenario,
        hierarchy,
        jobs,
        replace(
            risks,
            values=tuple(replace(v, measurements=(renamed,)) for v in risks.values),
        ),
    )
    assert scenario.run.coefficients[0].task_names == ("Lift carton",)
    with pytest.raises(ValueError):
        freeze_rotation_coefficients(inputs, jobs, risks)


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_real_cbc_and_highs_result_context_survives_without_resolving(
    kind: AssessmentKind,
) -> None:
    """Actual one/all-tool results retain staffing and hand-derived 50% worker scores.

    Args:
        kind: Primary model for the real CBC run; HiGHS always uses all three.

    Returns:
        None; serialized result equals the actual solver arrangement and frozen values.
    """
    _, jobs, risks = scenario_catalogs()
    inputs = scenario_inputs()
    baseline = balanced_rows(inputs)
    inputs = replace(inputs, baseline=baseline, tools=(kind,))
    problem = RotationProblem(
        baseline,
        tuple(
            RotationRisk(t.key, k, 0 if t.job_id == "J1" else 100)
            for t in inputs.targets
            for k in AssessmentKind
        ),
    )
    optimizer = HighsRotationOptimizer()
    for tools, solution in [
        ((kind,), optimizer.optimize_single_tool(problem, kind)),
        (tuple(AssessmentKind), optimizer.optimize_all_tools(problem)),
    ]:
        selected = replace(inputs, tools=tools)
        run = RotationRun(
            selected,
            freeze_rotation_coefficients(selected, jobs, risks),
            solution.schedule,
            solution.backend,
            solution.stages,
            (("time_limit_seconds", "60"),),
            datetime(2026, 10, 31, tzinfo=UTC),
            ROTATION_RUN_MODEL_VERSION,
            ("Ana", "Bruno"),
        )
        scenario = RotationScenario(
            "timing", "actual", "Real solver", selected, run=run
        )
        assert decode_scenario(encode_scenario(scenario)) == scenario
        for row in run.arrangement:
            assert (
                sum(0 if k == inputs.targets[0].key else 100 for k in row.target_keys)
                / 2
                == 50
            )


@pytest.mark.parametrize(
    "case",
    [
        "naive_utc",
        "missing_date",
        "missing_timing",
        "unstaffed",
        "missing_coefficient",
        "duplicate_coefficient",
        "wrong_backend",
        "wrong_stages",
        "duplicate_setting",
        "mutable_setting",
        "empty_setting",
        "bad_contract",
        "bool_contract",
        "missing_label",
    ],
)
def test_incomplete_run_context_is_rejected_before_persistence(case: str) -> None:
    """Reject missing run evidence, incorrect routing and invalid staffing.

    Args:
        case: Deliberate immutable result-context corruption.

    Returns:
        None; invalid context cannot become an accepted typed run.
    """
    source = scenario_with_run()
    run = source.run
    with pytest.raises(ValueError):
        if case == "naive_utc":
            replace(run, completed_at=datetime(2026, 10, 31))
        elif case == "missing_date":
            replace(run, inputs=replace(run.inputs, planned_date=None))
        elif case == "missing_timing":
            replace(run, inputs=replace(run.inputs, timing=None, start_minute=None))
        elif case == "unstaffed":
            replace(
                run,
                arrangement=(
                    run.arrangement[0],
                    replace(
                        run.arrangement[1], target_keys=run.arrangement[0].target_keys
                    ),
                ),
            )
        elif case == "missing_coefficient":
            replace(run, coefficients=run.coefficients[:-1])
        elif case == "duplicate_coefficient":
            replace(run, coefficients=(run.coefficients[0],) * len(run.coefficients))
        elif case == "wrong_backend":
            replace(run, backend=RotationBackend.CBC)
        elif case == "wrong_stages":
            replace(run, stages=(RotationSolveStatus.FEASIBLE,))
        elif case == "duplicate_setting":
            replace(run, settings=(("gap", "1"), ("gap", "2")))
        elif case == "mutable_setting":
            replace(run, settings=[("gap", "1")])
        elif case == "empty_setting":
            replace(run, settings=())
        elif case == "bad_contract":
            replace(run, contract_version=0)
        elif case == "bool_contract":
            replace(run, contract_version=True)
        else:
            replace(run, worker_labels=("Ana",))


def test_late_run_acceptance_retains_rename_but_rejects_changed_inputs_or_risks() -> (
    None
):
    """Result ownership follows exact scientific snapshots rather than visible labels.

    Args:
        None.

    Returns:
        None; renames accept; changed inputs, risks or project ownership reject.
    """
    from ergotools.application.rotation_scenarios import apply_rotation_run

    hierarchy, jobs, risks = scenario_catalogs()
    source = scenario_with_run()
    renamed = replace(source, name="Still running", run=None)
    result = apply_rotation_run(
        renamed, source.inputs, source.run, hierarchy, jobs, risks
    )
    assert result.name == renamed.name and result.run == source.run
    with pytest.raises(ValueError):
        apply_rotation_run(
            replace(
                renamed, inputs=replace(renamed.inputs, planned_date=date(2026, 11, 5))
            ),
            source.inputs,
            source.run,
            hierarchy,
            jobs,
            risks,
        )
    with pytest.raises(ValueError):
        apply_rotation_run(
            renamed,
            source.inputs,
            source.run,
            hierarchy,
            jobs,
            replace(risks, values=()),
        )
    assert not run_is_current(
        source,
        replace(hierarchy, work=replace(hierarchy.work, project_id="foreign")),
        jobs,
        risks,
    )


def test_partial_observed_schedule_roundtrips_without_becoming_no_baseline() -> None:
    """Saved in-progress cells remain absent values, distinct from the No-path choice.

    Args:
        None.

    Returns:
        None; partial rows persist but cannot form an accepted run or solver schedule.
    """
    from ergotools.domain.rotation_scenario import (
        RotationDraftRow,
        complete_rotation_rows,
    )

    inputs = scenario_inputs()
    a, b = (t.key for t in inputs.targets)
    partial = (RotationDraftRow("W1", (a, None)), RotationDraftRow("W2", (None, b)))
    entered = replace(inputs, baseline=partial)
    scenario = RotationScenario("timing", "partial", "Entered so far", entered)
    assert decode_scenario(encode_scenario(scenario)) == scenario
    assert scenario.inputs.baseline is not None and scenario.inputs.proposed is None
    with pytest.raises(ValueError):
        complete_rotation_rows(partial)
    with pytest.raises(ValueError):
        replace(scenario_with_run().run, inputs=entered)
    completed = replace(
        inputs,
        baseline=(RotationDraftRow("W1", (a, b)), RotationDraftRow("W2", (b, a))),
    )
    assert completed.baseline == balanced_rows(inputs)


def test_unknown_future_run_model_is_retained_but_never_current_or_applied() -> None:
    """Readable future evidence cannot be represented as a current supported result.

    Args:
        None.

    Returns:
        None; exact evidence survives, while current-result acceptance rejects it.
    """
    from ergotools.application.rotation_scenarios import apply_rotation_run

    hierarchy, jobs, risks = scenario_catalogs()
    source = scenario_with_run()
    future = replace(source, run=replace(source.run, contract_version=99))
    assert decode_scenario(encode_scenario(future)) == future
    assert not run_is_current(future, hierarchy, jobs, risks)
    with pytest.raises(ValueError):
        apply_rotation_run(source, source.inputs, future.run, hierarchy, jobs, risks)


def test_input_reference_validation_rejects_cross_project_catalogs() -> None:
    """Repeated visible IDs never permit Job ownership from another project.

    Args:
        None.

    Returns:
        None; direct pure validation rejects the same foreign-data mismatch as storage.
    """
    hierarchy, jobs, _ = scenario_catalogs()
    with pytest.raises(ValueError, match="different projects"):
        scenario_inputs().validate_references(
            hierarchy, replace(jobs, project_id="foreign")
        )

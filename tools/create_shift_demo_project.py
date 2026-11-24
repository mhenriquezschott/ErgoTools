"""Create the owner's twenty-worker Shift View fixture, using public native APIs.

Developer tooling. Copy only the comparison project's embedded plant image and
explicitly chosen reference coordinates; never copy its personal/assessment data.
The new project is published exclusively, with named calculated tasks for all tools,
twenty complete placements and paired unrestricted/restricted real optimizations.
"""

from dataclasses import replace
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from ergotools.application.assessments.evaluation import AssessmentEvaluator
from ergotools.application.job_calculation import calculate_job_measurement
from ergotools.application.rotation_planning import (
    accepted_rotation_run,
    prepare_rotation_plan,
)
from ergotools.application.saved_results import result_snapshot
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessments.context import WorkerContext
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    assessment_kind,
)
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.job_catalog import (
    Job,
    JobCatalog,
    JobPlacement,
    WorkerJobAssignment,
)
from ergotools.domain.job_risk import JobRiskValues
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.organization_record import OrganizationKind, OrganizationRecord
from ergotools.domain.plot_positions import (
    PlotPoint,
    PlotPositions,
    StationPosition,
    WorkerAssignmentMarker,
    WorkerPositionSource,
)
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.rotation import WorkerRotation
from ergotools.domain.rotation_constraints import NoAdjacentHigh
from ergotools.domain.rotation_scenario import RotationInputs, RotationScenario
from ergotools.domain.rotation_scheme import RotationTarget, RotationWorkerLink
from ergotools.domain.rotation_timing import MinuteInterval, RotationTiming, TimedBreak
from ergotools.domain.task_catalog import TaskDefinition
from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy
from ergotools.domain.worker_details import WorkerDetails
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.highs_rotation_optimizer import HighsRotationPlanner

# Fictional native project identity; no operational project is migrated or overwritten.
PROJECT_ID = "shift-playback-twenty-2026"
# Original-image locations sampled from the comparison project's five work areas.
POINTS = (
    (300, 30),
    (350, 70),
    (425, 70),
    (550, 70),
    (460, 170),
    (615, 170),
    (790, 170),
    (955, 170),
    (465, 410),
    (635, 410),
    (465, 515),
    (690, 515),
    (1070, 405),
    (1245, 405),
    (1070, 533),
    (1370, 533),
    (410, 680),
    (580, 680),
    (885, 810),
    (1090, 810),
)
# Synthetic people, never copied from the comparison data.
PEOPLE = (
    ("Ana", "Ruiz"),
    ("Bruno", "Silva"),
    ("Carla", "Vega"),
    ("Diego", "Soto"),
    ("Elena", "Muñoz"),
    ("Felipe", "Rojas"),
    ("Gabriela", "Torres"),
    ("Hugo", "Navarro"),
    ("Isabel", "Morales"),
    ("Javier", "Castro"),
    ("Laura", "Reyes"),
    ("Mateo", "Fuentes"),
    ("Natalia", "Díaz"),
    ("Óscar", "Paredes"),
    ("Paula", "Molina"),
    ("Rafael", "Sánchez"),
    ("Sofía", "Carrasco"),
    ("Tomás", "Vargas"),
    ("Valentina", "León"),
    ("Andrés", "Campos"),
)
# Task inputs span light inspection to heavy handling; results are calculated.
PATTERNS = (
    (20.0, 19.62, 200.0, 1),
    (30.0, 49.05, 500.0, 3),
    (45.0, 98.1, 700.0, 5),
    (60.0, 196.2, 1000.0, 7),
)
# Literal meaningful Job names, grouped spatially in the sample map.
NAMES = (
    "Tray inspection",
    "Portion sorting",
    "Case packing",
    "Container transfer",
    "Label checking",
    "Tray loading",
    "Bag sealing",
    "Crate stacking",
    "Quality sampling",
    "Carton forming",
    "Manual weighing",
    "Pallet loading",
    "Seal inspection",
    "Material replenishment",
    "Case closing",
    "Bin tipping",
    "Dispatch checking",
    "Carton labeling",
    "Pallet wrapping",
    "Heavy replenishment",
)


def shift_sources(
    identity: str, index: int, multiplier: float = 1.0
) -> tuple[AssessmentDraft, ...]:
    """Create two named metric tasks for each ergonomic tool.

    Args:
        identity: Unique Job/worker prefix for stable task IDs.
        index: Zero-based workload family/variation.
        multiplier: Worker-only repetition variation, preserving Job independence.

    Returns:
        Complete LiFFT, DUET and ST sources; no direct result input.
    """
    arm, force, reps, omni = PATTERNS[index % 4]
    reps *= multiplier * (1 + (index // 4) * 0.03)
    return (
        LifftDraft(
            MeasurementSystem.METRIC,
            (
                LifftTask(
                    identity + "-l1", arm, force, reps, task_name="Main handling cycle"
                ),
                LifftTask(
                    identity + "-l2",
                    arm * 0.8,
                    force * 0.5,
                    reps * 0.3,
                    task_name="Material repositioning",
                ),
            ),
        ),
        DuetDraft(
            (
                DuetTask(identity + "-d1", omni, reps, task_name="Repeated hand cycle"),
                DuetTask(
                    identity + "-d2",
                    max(0, omni - 1),
                    reps * 0.3,
                    task_name="Finishing and release",
                ),
            )
        ),
        TstDraft(
            MeasurementSystem.METRIC,
            (
                TstTask(
                    identity + "-s1",
                    TstDirection.HANDLING_LOADS,
                    arm,
                    force,
                    reps,
                    task_name="Primary reach and transfer",
                ),
                TstTask(
                    identity + "-s2",
                    TstDirection.HANDLING_LOADS,
                    arm * 0.8,
                    force * 0.5,
                    reps * 0.3,
                    task_name="Return and reposition",
                ),
            ),
        ),
    )


def create_shift_demo(path: Path, reference: Path) -> None:
    """Build one full mapped project and real paired runs without schema changes.

    Args:
        path: Nonexistent destination; existing files are never overwritten.
        reference: Read-only comparison project providing only its plant image.

    Returns:
        None after exclusive validated native publication.

    Raises:
        FileExistsError: Destination already exists.
        ValueError: Reference image, task data or solver outcome is incomplete.
        OSError: Native file access/publication fails.
    """
    if path.exists():
        raise FileExistsError(path)
    with AssessmentProjectFile.open(reference) as original:
        image = original.load_plant_image(original.load_hierarchy().plants[0])
    if image is None:
        raise ValueError("The reference plant image is required.")
    plant, section, line, shift = (
        "Riverside Foods",
        "Packing & dispatch",
        "Integrated packing",
        "Day",
    )
    stations = tuple(
        StationKey(plant, section, line, f"ST{i + 1:02}") for i in range(20)
    )
    workers = tuple(
        WorkerEntry(
            f"W{i + 1:02}",
            first,
            last,
            WorkerDetails(
                birth_date=f"{1968 + (i * 7) % 37}-05-14",
                sex="Female" if i % 2 == 0 else "Male",
                height_cm=158 + (i * 3) % 29,
                weight_kg=55 + (i * 5) % 36,
                hiring_date="2020-03-02",
            ),
        )
        for i, (first, last) in enumerate(PEOPLE)
    )
    hierarchy = WorkHierarchy(
        WorkCatalog(PROJECT_ID, workers, stations, (shift,)),
        (plant,),
        (SectionKey(plant, section),),
        (LineKey(plant, section, line),),
        (
            OrganizationRecord(
                OrganizationKind.SHIFT,
                (shift,),
                (
                    ("start_time", "08:00"),
                    ("end_time", "18:00"),
                    ("description", "Packing and dispatch day shift"),
                ),
            ),
        ),
    )
    jobs = tuple(Job(f"J{i + 1:02}", name) for i, name in enumerate(NAMES))
    placements = tuple(
        JobPlacement(i + 1, j.job_id, stations[i].at_shift(shift))
        for i, j in enumerate(jobs)
    )
    assignments = tuple(
        WorkerJobAssignment(
            i + 1,
            WorkerContext(PROJECT_ID, w.worker_id, placements[i].workplace),
            i + 1,
        )
        for i, w in enumerate(workers)
    )
    timing = RotationTiming(
        600,
        (
            TimedBreak(MinuteInterval(135, 155), "Morning break"),
            TimedBreak(MinuteInterval(290, 310), "Lunch break"),
            TimedBreak(MinuteInterval(445, 465), "Afternoon break"),
        ),
        (135, 135, 135, 135),
        True,
        True,
    )
    with (
        TemporaryDirectory(prefix="ergotools-shift-demo-") as folder,
        AssessmentProjectFile.create_empty(
            Path(folder) / "private.ergprj",
            ProjectMetadata(
                PROJECT_ID, "Shift View · Riverside Foods", MeasurementSystem.METRIC
            ),
        ) as project,
    ):
        project.save_hierarchy(hierarchy)
        project.replace_task_definitions(
            (),
            tuple(
                TaskDefinition(f"shift-task-{i}", name)
                for i, name in enumerate(
                    (
                        "Main handling cycle",
                        "Material repositioning",
                        "Repeated hand cycle",
                        "Finishing and release",
                        "Primary reach and transfer",
                        "Return and reposition",
                    )
                )
            ),
        )
        project.save_jobs(JobCatalog(PROJECT_ID, jobs, placements, assignments))
        project.save_plant_image(plant, image)
        project.save_plot_positions(
            PlotPositions(
                PROJECT_ID,
                tuple(
                    StationPosition(s, PlotPoint(*p))
                    for s, p in zip(stations, POINTS, strict=True)
                ),
                tuple(
                    WorkerAssignmentMarker(
                        i + 1,
                        PlotPoint(*p),
                        size=50,
                        scale=0.6,
                        visible=True,
                        source=WorkerPositionSource.MANUAL,
                    )
                    for i, p in enumerate(POINTS)
                ),
            )
        )
        project.replace_shift_timing(shift, None, timing)
        catalog, risks = project.load_jobs(), project.load_job_risk()
        evaluator = AssessmentEvaluator()
        for i, job in enumerate(jobs):
            values = JobRiskValues(
                job.job_id,
                tuple(
                    calculate_job_measurement(
                        PROJECT_ID, job.job_id, s, MeasurementSystem.METRIC
                    )
                    for s in shift_sources(job.job_id, i)
                ),
            )
            catalog, risks = project.save_job_details(catalog, risks, job, values)
            for source in shift_sources(f"W{i + 1:02}", i, 0.85 + (i % 5) * 0.07):
                kind = assessment_kind(source)
                document = DocumentKey(PROJECT_ID, f"worker-{i + 1}-{kind.value}")
                evaluate = {
                    AssessmentKind.LIFFT: evaluator.evaluate_lifft_grid,
                    AssessmentKind.DUET: evaluator.evaluate_duet_grid,
                    AssessmentKind.TST: evaluator.evaluate_tst_grid,
                }[kind]
                result = result_snapshot(
                    evaluate(DocumentSession(document, source)),
                    MeasurementSystem.METRIC,
                )
                project.create_historical_assessment(
                    AssignmentAssessment(
                        document.document_id, i + 1, kind, workers[i].worker_id
                    ),
                    source,
                    result=result,
                )
        targets = tuple(RotationTarget(p.job_id, p.placement_id) for p in placements)
        baseline = tuple(
            WorkerRotation(
                w.worker_id, tuple(targets[(i + b * 4) % 20].key for b in range(4))
            )
            for i, w in enumerate(workers)
        )
        for restricted in (False, True):
            inputs = RotationInputs(
                date(2026, 11, 12),
                hierarchy.lines[0],
                shift,
                480,
                timing,
                tuple(
                    RotationWorkerLink(w.worker_id, i + 1)
                    for i, w in enumerate(workers)
                ),
                targets,
                tuple(AssessmentKind),
                baseline,
                scope=tuple(p.workplace for p in placements),
                rules=tuple(NoAdjacentHigh(w.worker_id) for w in workers)
                if restricted
                else (),
            )
            scenario = RotationScenario(
                PROJECT_ID,
                "shift-demo-" + str(int(restricted)),
                "02 · Avoid consecutive High Jobs"
                if restricted
                else "01 · Unrestricted balanced rotation",
                inputs,
                description=(
                    "Baseline keeps workers within workload families; "
                    "optimized arrangements redistribute exposures across "
                    "the full mapped floor."
                ),
            )
            prepared = prepare_rotation_plan(
                scenario, (), hierarchy, catalog, risks, time_limit_seconds=30
            )
            solution = HighsRotationPlanner().solve(prepared.problem)
            scenario = replace(scenario, run=accepted_rotation_run(prepared, solution))
            project.replace_rotation_scenario(None, scenario)
        with project.snapshot(str(path.resolve()), None, None):
            pass


def main() -> None:
    """Create the named fixture exclusively from the maintained comparison image.

    Args:
        None.

    Returns:
        None; existing files are protected.
    """
    create_shift_demo(
        Path("test_projects/native/shift_view_demo.ergprj"),
        Path("test_projects/native/comparative_risk_test.ergprj"),
    )


if __name__ == "__main__":
    main()

"""Opt-in fictional tablet demonstration, built through unchanged native project APIs.

The generator refuses existing targets. All calculations use the shared evaluators;
no hand-entered risk results, production fixture mutations or schema changes occur.
"""

from dataclasses import replace
from pathlib import Path

from assessment_contexts import create_assessment, read_contexts, transfer_assessment
from assessment_tasks import persist_source, task_from_form
from mobile_assessment import assessment

from ergotools.application.rotation_timing_actions import equalize_contiguous_timing
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_catalog import Job, JobCatalog, JobPlacement
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.organization_record import OrganizationKind, OrganizationRecord
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.rotation_timing import MinuteInterval, TimedBreak, equal_timing
from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy
from ergotools.domain.worker_details import WorkerDetails
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile


def build_demo(path: Path) -> None:
    """Build four workers, all tools and varied independent workplace assessments.

    Args:
        path: New owned temporary native destination; parent must already exist.

    Returns:
        None; eighteen calculated assessments and one empty source are persisted.

    Raises:
        FileExistsError: Caller must never overwrite an existing sample/user file.
    """
    if path.exists():
        raise FileExistsError(path)
    project_id = "tablet-demo-v1"
    workers = tuple(
        WorkerEntry(identity, first, last, WorkerDetails(dob, sex, height, mass))
        for identity, first, last, dob, sex, height, mass in (
            ("W01", "Elena", "Muñoz", "1991-06-15", "Female", 165, 65),
            ("W02", "Diego", "Soto", "1984-02-12", "Male", 178, 82),
            ("W03", "Carla", "Vega", "1976-09-23", "Female", 160, 60),
            ("W04", "Mateo", "Rojas", "2000-01-18", "Male", 172, 74),
        )
    )
    stations = tuple(
        StationKey(plant, section, line, station)
        for plant, section, line in (
            ("Harbor Plant", "Packing", "Line A"),
            ("Riverside Plant", "Assembly", "Line B"),
        )
        for station in ("ST01", "ST02")
    )
    first, second = stations[0].at_shift("Day"), stations[2].at_shift("Night")
    with AssessmentProjectFile.create_empty(
        path,
        ProjectMetadata(
            project_id, "Tablet worker-assessment demo", MeasurementSystem.METRIC
        ),
    ) as project:
        project.save_hierarchy(
            WorkHierarchy(
                WorkCatalog(project_id, workers, stations, ("Day", "Night")),
                ("Harbor Plant", "Riverside Plant"),
                tuple(
                    SectionKey(s.plant_name, s.section_name)
                    for s in (stations[0], stations[2])
                ),
                tuple(
                    LineKey(s.plant_name, s.section_name, s.line_name)
                    for s in (stations[0], stations[2])
                ),
            )
        )
        project.save_jobs(
            JobCatalog(
                project_id,
                (Job("J01", "Manual packing"), Job("J02", "Container transfer")),
                (JobPlacement(1, "J01", first), JobPlacement(2, "J02", second)),
            )
        )
    for i, worker in enumerate(workers):
        for kind in AssessmentKind:
            identity = create_assessment(path, worker.worker_id, kind, None)
            record = assessment(path, worker.worker_id, identity, kind)
            values = (
                (30, 49, 100, 3),
                (70, 294, 1000, 10),
                (50, 147.2, 500, 6),
                (45, 98.1, 200, 5),
            )[i]
            arm, load, repetitions, effort = values
            row = task_from_form(
                record["source"].tasks[0],
                {
                    "task_name": (
                        "Packing boxes",
                        "Container transfer",
                        "Loading crates",
                        "Sorting packages",
                    )[i],
                    "lever_arm": str(arm),
                    "load": str(load),
                    "repetitions": str(repetitions),
                    "omni_res_scale": str(effort),
                    "direction": "1",
                },
                {},
            )
            persist_source(path, record, replace(record["source"], tasks=(row,)))
    for worker, workplace, kinds in (
        ("W01", first, (AssessmentKind.LIFFT, AssessmentKind.DUET)),
        ("W02", second, tuple(AssessmentKind)),
    ):
        for kind in kinds:
            transfer_assessment(
                path, assessment(path, worker, kind=kind), worker, workplace
            )
    create_assessment(path, "W03", AssessmentKind.TST, stations[1].at_shift("Day"))
    closed_id = transfer_assessment(
        path,
        assessment(path, "W01", kind=AssessmentKind.TST),
        "W01",
        stations[0].at_shift("Night"),
    )
    catalog = read_contexts(path)
    closed = next(
        r for r in catalog["records"] if r["document"].document_id == closed_id
    )
    with AssessmentProjectFile.open(path) as project:
        jobs = project.load_jobs()
        placements = {first: 1, second: 2}
        project.save_jobs(
            replace(
                jobs,
                assignments=tuple(
                    replace(a, active=False)
                    if a.assignment_id == closed["owner"].assignment_id
                    else replace(a, placement_id=placements[a.worker.workplace])
                    if a.worker.workplace in placements
                    else a
                    for a in jobs.assignments
                ),
            )
        )

    # Fresh fictional samples include real shift metadata and a reusable timing example.
    # No existing user/maintained project is changed by rebuilding this new sample.
    with AssessmentProjectFile.open(path) as project:
        hierarchy = project.load_hierarchy()
        project.save_hierarchy(
            replace(
                hierarchy,
                organization=(
                    OrganizationRecord(
                        OrganizationKind.SHIFT,
                        ("Day",),
                        (
                            ("description", "Day production and packing"),
                            ("start_time", "08:00"),
                            ("end_time", "16:00"),
                        ),
                    ),
                    OrganizationRecord(
                        OrganizationKind.SHIFT,
                        ("Night",),
                        (
                            ("description", "Overnight assembly"),
                            ("start_time", "22:00"),
                            ("end_time", "06:00"),
                        ),
                    ),
                ),
            )
        )
        timing = equalize_contiguous_timing(
            equal_timing(
                480,
                1,
                (
                    TimedBreak(MinuteInterval(120, 135), "Morning break"),
                    TimedBreak(MinuteInterval(300, 330), "Lunch"),
                ),
            ),
            3,
        )
        project.begin_editing(lambda label: None)
        project.replace_shift_timing("Day", None, timing)
        project.commit_editing()

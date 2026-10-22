"""Create the owner's clean six-worker JROT meeting fixture using current APIs.

Developer tooling, never imported by the application. Synthetic named workers,
realistic packing locations and independent calculated Job sources use native format
19 without schema changes. Stage privately and publish exclusively; never overwrite
an existing project, copy a populated database, or modify the reference application.
"""

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from ergotools.application.job_calculation import calculate_job_measurement
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.job_catalog import Job, JobCatalog, JobPlacement
from ergotools.domain.job_risk import JobRiskValues
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.organization_record import OrganizationKind, OrganizationRecord
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy
from ergotools.domain.worker_details import WorkerDetails
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile

# Stable synthetic project identity; not a migrated/operational container.
PROJECT_ID = "jrot-six-worker-demo-2026"
# One owner-authorized additional native fixture, not a duplicate maintained project.
DEFAULT_PATH = Path("test_projects/native/jrot_workflow_demo.ergprj")
# Fictional demographics: ISO birth dates, cm and kg. No personal records are copied.
WORKERS = (
    ("W01", "Ana", "Morales", "1998-05-14", "Female", 164, 62),
    ("W02", "Bruno", "Reyes", "1991-02-09", "Male", 178, 81),
    ("W03", "Carla", "Soto", "1983-03-20", "Female", 168, 68),
    ("W04", "Diego", "Navarro", "1975-06-05", "Male", 175, 79),
    ("W05", "Elena", "Fuentes", "2002-01-18", "Female", 160, 57),
    ("W06", "Felipe", "Rojas", "1987-07-11", "Male", 182, 86),
)
# Job task patterns: name, lever arm cm, force N, repetitions/day and OMNI-RES.
# Each tool gets two explicit tasks, with varied workloads; no example risk is invented.
JOBS = (
    ("Label inspection", 20.0, 19.62, 200.0, 2),
    ("Tray loading", 30.0, 49.05, 500.0, 3),
    ("Case packing", 40.0, 98.1, 800.0, 5),
    ("Case sealing", 35.0, 73.575, 600.0, 4),
    ("Pallet stacking", 55.0, 147.15, 1000.0, 7),
    ("Material replenishment", 45.0, 122.625, 700.0, 6),
)


def demo_hierarchy() -> WorkHierarchy:
    """Build two food-packing plants with complete scoped station ancestry.

    Args:
        None.

    Returns:
        Six workers, two plants, four sections, eight lines, 24 stations and two
        eight-hour recurring shifts. Repeated short station IDs remain scoped.
    """
    plants = ("Valdivia Foods", "Osorno Foods")
    sections = tuple(
        SectionKey(p, name)
        for p in plants
        for name in ("Fresh packing", "Frozen packing")
    )
    lines = tuple(
        LineKey(s.plant_name, s.section_name, name)
        for s in sections
        for name in ("Packing Line 1", "Packing Line 2")
    )
    stations = tuple(
        StationKey(line.plant_name, line.section_name, line.line_name, f"ST{i:02}")
        for line in lines
        for i in range(1, 4)
    )
    workers = tuple(
        WorkerEntry(
            identity,
            first,
            last,
            WorkerDetails(
                birth_date=birth,
                sex=sex,
                height_cm=height,
                weight_kg=weight,
                hiring_date="2020-03-02" if identity != "W05" else "2023-03-06",
            ),
        )
        for identity, first, last, birth, sex, height, weight in WORKERS
    )
    organization = tuple(
        OrganizationRecord(
            OrganizationKind.PLANT,
            (p,),
            (
                (
                    "description",
                    "Synthetic food-packing facility for JROT demonstrations",
                ),
                ("location", p.split()[0]),
                ("operational_hours", 16),
            ),
        )
        for p in plants
    )
    organization += (
        OrganizationRecord(
            OrganizationKind.SHIFT,
            ("Day",),
            (
                ("description", "Day packing shift"),
                ("start_time", "06:00"),
                ("end_time", "14:00"),
            ),
        ),
        OrganizationRecord(
            OrganizationKind.SHIFT,
            ("Evening",),
            (
                ("description", "Evening packing shift"),
                ("start_time", "14:00"),
                ("end_time", "22:00"),
            ),
        ),
    )
    return WorkHierarchy(
        WorkCatalog(PROJECT_ID, workers, stations, ("Day", "Evening")),
        plants,
        sections,
        lines,
        organization,
    )


def demo_sources(job_id: str, index: int) -> tuple[AssessmentDraft, ...]:
    """Supply two reproducible metric tasks per tool for one Job.

    Args:
        job_id: Stable J01-J06 identity, used to make source task IDs unambiguous.
        index: Zero-based position in the documented six-Job pattern.

    Returns:
        LiFFT, DUET and ST sources, using established handling-load ST semantics.
    """
    _, arm, force, reps, omni = JOBS[index]
    return (
        LifftDraft(
            MeasurementSystem.METRIC,
            (
                LifftTask(job_id + "-l1", arm, force, reps),
                LifftTask(job_id + "-l2", arm * 0.8, force * 0.5, reps * 0.4),
            ),
        ),
        DuetDraft(
            (
                DuetTask(job_id + "-d1", omni, reps),
                DuetTask(job_id + "-d2", max(0, omni - 1), reps * 0.4),
            )
        ),
        TstDraft(
            MeasurementSystem.METRIC,
            (
                TstTask(job_id + "-s1", TstDirection.HANDLING_LOADS, arm, force, reps),
                TstTask(
                    job_id + "-s2",
                    TstDirection.HANDLING_LOADS,
                    arm * 0.8,
                    force * 0.5,
                    reps * 0.4,
                ),
            ),
        ),
    )


def create_demo(path: Path) -> None:
    """Publish one complete new native project through existing validated adapters.

    Args:
        path: Nonexistent target with an existing parent directory.

    Returns:
        None; callers can load the ordinary .ergprj in the current application.

    Raises:
        FileExistsError: Target exists; no overwrite/replacement flag is provided.
        OSError: Staging or exclusive publication fails.
        ValueError: Domain or calculator validation rejects the documented seed.
    """
    if path.exists():
        raise FileExistsError(path)
    hierarchy = demo_hierarchy()
    jobs = tuple(
        Job(
            f"J{i + 1:02}",
            row[0],
            description="Packing activity; two metric tasks per tool.",
        )
        for i, row in enumerate(JOBS)
    )
    placements: list[JobPlacement] = []
    for line in hierarchy.lines:
        for shift in hierarchy.work.shifts:
            for index, job in enumerate(jobs):
                station = StationKey(
                    line.plant_name,
                    line.section_name,
                    line.line_name,
                    f"ST{index // 2 + 1:02}",
                )
                placements.append(
                    JobPlacement(
                        len(placements) + 1, job.job_id, station.at_shift(shift)
                    )
                )
    with (
        TemporaryDirectory(prefix="ergotools-jrot-seed-") as directory,
        AssessmentProjectFile.create_empty(
            Path(directory) / "staged.ergprj",
            ProjectMetadata(
                PROJECT_ID, "JROT six-worker demonstration", MeasurementSystem.METRIC
            ),
        ) as project,
    ):
        project.save_hierarchy(hierarchy)
        project.save_jobs(JobCatalog(PROJECT_ID, jobs, tuple(placements)))
        catalog, risks = project.load_jobs(), project.load_job_risk()
        for index, job in enumerate(jobs):
            values = JobRiskValues(
                job.job_id,
                tuple(
                    calculate_job_measurement(
                        PROJECT_ID, job.job_id, source, MeasurementSystem.METRIC
                    )
                    for source in demo_sources(job.job_id, index)
                ),
            )
            catalog, risks = project.save_job_details(catalog, risks, job, values)
        with project.snapshot(str(path.resolve()), None, None):
            pass


def main() -> None:
    """Create the documented fixture or an explicitly supplied nonexistent target.

    Args:
        None; command-line --output selects the new .ergprj path.

    Returns:
        None; errors propagate, preserving any existing target.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_PATH)
    create_demo(parser.parse_args().output)


if __name__ == "__main__":
    main()

"""Reference job constraints, transactional persistence and classified projections.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from ergotools.domain.assessments.context import WorkerContext
from ergotools.domain.job_catalog import (
    Job,
    JobCatalog,
    JobPlacement,
    WorkerJobAssignment,
)
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.draft_store import StoreFormatError
from ergotools.presentation.assignment_options import classified_assignments

# Explicit synthetic project identity/title/default units; assessment units are
# preserved independently.
META = ProjectMetadata("p", "Jobs", MeasurementSystem.IMPERIAL)
# Exact synthetic station ancestry; repeated station captions on other branches remain
# distinct.
STATION = StationKey("P", "S", "L", "1")
# Exact synthetic station-at-shift context used by assignment/history transitions.
PLACE = STATION.at_shift("Day")
# Exact project/worker/workplace/shift ownership used to distinguish historical
# assignment links.
OWNER = WorkerContext("p", "w", PLACE)
# Immutable synthetic complete hierarchy, including the empty branches/shifts needed by
# these tests.
HIERARCHY = WorkHierarchy(
    WorkCatalog("p", (WorkerEntry("w"),), (STATION,), ("Day", "Night")),
    ("P",),
    (SectionKey("P", "S"),),
    (LineKey("P", "S", "L"),),
)
# Synthetic saved job metadata including deliberately retained optional/activity values.
JOB = Job("j", "Operator", False, "Description")
# Synthetic job/workplace placement with exact original activity/date/notes metadata.
PLACEMENT = JobPlacement(1, "j", PLACE, True, "2000-01-01", "2000-12-31", "Past")
# Synthetic assignment record retaining the exact owner, activity and history metadata
# under test.
ASSIGNMENT = WorkerJobAssignment(1, OWNER, 1, True, "2099-01-01", None, "Future")
# Immutable exact synthetic worker/job/catalog relationships used by these isolated
# regressions.
CATALOG = JobCatalog("p", (JOB,), (PLACEMENT,), (ASSIGNMENT,))


def seed(path: Path) -> None:
    """Seed only a temporary version-five project with synthetic job data.

    Args:
        path: Disposable test file path; the caller controls creation and cleanup.

    Returns:
        None.
    """
    with AssessmentProjectFile.create_with_jobs(path, META) as project:
        project.save_hierarchy(HIERARCHY)
        project.save_jobs(CATALOG)


def test_reference_overlap_trigger_parity() -> None:
    """Inclusive boundary and open-bound behavior match the actual reference trigger.

    Args:
        None.

    Returns:
        None.
    """
    fixture = json.loads(
        (Path(__file__).parent / "fixtures/job_overlap_reference.json").read_text()
    )
    for case in fixture["cases"]:
        place = PLACE if case["context"] == 1 else STATION.at_shift("Night")
        candidate = JobPlacement(
            2, case["job"], place, case["active"], case["start"], case["end"]
        )
        if case["accepted"]:
            JobCatalog("p", (JOB, Job("other", "Other")), (PLACEMENT, candidate))
        else:
            with pytest.raises(ValueError, match="overlap"):
                JobCatalog("p", (JOB, Job("other", "Other")), (PLACEMENT, candidate))


def test_roundtrip_history_and_classified_projection(tmp_path: Path) -> None:
    """Retain notes/order/dates while matching reference activity-only eligibility.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "jobs.sqlite"
    history = replace(ASSIGNMENT, assignment_id=2, active=False, placement_id=None)
    inactive_place = replace(PLACEMENT, placement_id=2, active=False)
    night = replace(
        ASSIGNMENT,
        assignment_id=3,
        worker=replace(OWNER, workplace=STATION.at_shift("Night")),
        placement_id=None,
    )
    catalog = replace(
        CATALOG,
        placements=(inactive_place, PLACEMENT),
        assignments=(history, ASSIGNMENT, night),
    )
    with AssessmentProjectFile.create_with_jobs(path, META) as project:
        assert project.load_jobs() == JobCatalog("p")
        project.save_hierarchy(HIERARCHY)
        project.save_jobs(catalog)
    with AssessmentProjectFile.open(path) as project:
        assert project.format_version == 5
        assert project.load_jobs() == catalog
        options = classified_assignments(project.load_jobs(), "w")
        assert len(options) == 2
        assert options[0].job_id == "j"
        assert options[0].job_name == "Operator"
        assert options[0].assignment.placement_active
        assert options[1].job_id is None
        assert options[1].assignment.worker.workplace.shift_id == "Night"
        assert classified_assignments(catalog, "missing") == ()
        disabled = replace(catalog, assignments=(replace(ASSIGNMENT, placement_id=2),))
        project.save_jobs(disabled)
        assert classified_assignments(project.load_jobs(), "w") == ()


def test_relationships_unique_active_owners_and_typed_fields() -> None:
    """Reject missing jobs/placements, foreign contexts and ambiguous typed data.

    Args:
        None.

    Returns:
        None.
    """
    for changes in (
        {"jobs": ()},
        {"jobs": (JOB, JOB)},
        {"placements": (PLACEMENT, PLACEMENT)},
        {"assignments": (ASSIGNMENT, ASSIGNMENT)},
        {"placements": ()},
        {"assignments": (ASSIGNMENT, replace(ASSIGNMENT, assignment_id=2))},
        {
            "assignments": (
                replace(ASSIGNMENT, worker=replace(OWNER, project_id="other")),
            )
        },
        {
            "assignments": (
                replace(
                    ASSIGNMENT,
                    worker=replace(OWNER, workplace=STATION.at_shift("Night")),
                ),
            )
        },
        {"jobs": (None,)},
    ):
        with pytest.raises(ValueError):
            replace(CATALOG, **changes)
    for item, changes in (
        (JOB, {"active": 1}),
        (JOB, {"description": 1}),
        (PLACEMENT, {"placement_id": True}),
        (PLACEMENT, {"workplace": None}),
        (PLACEMENT, {"valid_to": "1999"}),
        (ASSIGNMENT, {"worker": None}),
        (ASSIGNMENT, {"placement_id": True}),
        (ASSIGNMENT, {"ended_at": "1999"}),
        (ASSIGNMENT, {"notes": 1}),
    ):
        with pytest.raises(ValueError):
            replace(item, **changes)


def test_job_and_hierarchy_saves_preserve_cross_catalog_integrity(
    tmp_path: Path,
) -> None:
    """Both mutation directions protect active and historical relationship owners.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "jobs.sqlite"
    seed(path)
    with AssessmentProjectFile.open(path) as project:
        for work in (
            replace(HIERARCHY.work, workers=()),
            replace(HIERARCHY.work, stations=()),
            replace(HIERARCHY.work, shifts=("Night",)),
        ):
            with pytest.raises((ValueError, KeyError)):
                project.save_hierarchy(replace(HIERARCHY, work=work))
            assert project.load_hierarchy() == HIERARCHY
        with pytest.raises(ValueError):
            project.save_jobs(JobCatalog("other"))
        missing = replace(ASSIGNMENT, worker=replace(OWNER, worker_id="missing"))
        with pytest.raises(KeyError):
            project.save_jobs(replace(CATALOG, assignments=(missing,)))
        assert project.load_jobs() == CATALOG
        project.save_jobs(replace(CATALOG, jobs=(replace(JOB, name="Renamed"),)))
        assert classified_assignments(project.load_jobs(), "w")[0].job_name == "Renamed"


def test_sql_failure_rolls_back_deleted_and_inserted_records(tmp_path: Path) -> None:
    """An abort late in replacement restores all three previous tables.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "jobs.sqlite"
    seed(path)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(
            "CREATE TRIGGER fail BEFORE INSERT ON worker_assignments "
            "BEGIN SELECT RAISE(ABORT, 'injected'); END"
        )
    with AssessmentProjectFile.open(path) as project:
        changed = replace(CATALOG, jobs=(replace(JOB, name="Changed"),))
        with pytest.raises(sqlite3.IntegrityError):
            project.save_jobs(changed)
        assert project.load_jobs() == CATALOG
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute("DROP TRIGGER fail")
        project.save_jobs(changed)
        assert project.load_jobs() == changed


@pytest.mark.parametrize("damage", ["job", "context", "worker", "flag"])
def test_damaged_relationships_reject_open(tmp_path: Path, damage: str) -> None:
    """Open validates stored relationships instead of silently repairing history.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        damage: Dimensionless damage boundary input (or deliberate invalid text) for the
            stated scenario.

    Returns:
        None.
    """
    path = tmp_path / "jobs.sqlite"
    seed(path)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute(
            {
                "job": "DELETE FROM jobs",
                "context": "UPDATE worker_assignments SET station='wrong'",
                "worker": "UPDATE worker_assignments SET worker_id='missing'",
                "flag": "UPDATE jobs SET active=2",
            }[damage]
        )
    before = path.read_bytes()
    with pytest.raises((ValueError, KeyError)):
        AssessmentProjectFile.open(path)
    assert path.read_bytes() == before


def test_old_format_creation_cleanup_and_closed_handles(tmp_path: Path) -> None:
    """New capability is opt-in; failed creation and closed handles are safe.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "jobs.sqlite"
    with (
        patch(
            "ergotools.infrastructure.assessment_project_file.create_job_schema",
            side_effect=OSError("injected"),
        ),
        pytest.raises(OSError),
    ):
        AssessmentProjectFile.create_with_jobs(path, META)
    assert not path.exists()
    with AssessmentProjectFile.create_catalogued(path, META):
        pass
    before = path.read_bytes()
    with AssessmentProjectFile.open(path) as project:
        with pytest.raises(StoreFormatError):
            project.load_jobs()
        with pytest.raises(StoreFormatError):
            project.save_jobs(CATALOG)
    assert path.read_bytes() == before
    project = AssessmentProjectFile.open(path)
    project.close()
    with pytest.raises(RuntimeError):
        project.load_jobs()


def test_job_read_uses_one_database_snapshot(tmp_path: Path) -> None:
    """A concurrent WAL writer cannot mix jobs from separate read snapshots.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    from ergotools.infrastructure.job_catalog_store import JobCatalogStore

    path = tmp_path / "jobs.sqlite"
    seed(path)
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
    original = JobCatalogStore.read
    changed = replace(CATALOG, jobs=(replace(JOB, name="Concurrent"),))
    with AssessmentProjectFile.open(path) as reader:
        written = False

        def read_then_write(store: JobCatalogStore) -> JobCatalog:
            """Read one catalog snapshot, then commit a separate WAL update only once.

            Read one catalog snapshot, then commit a separate WAL update only once to
            prove the returned read cannot mix snapshots.

            Args:
                store: Injected test-owned storage adapter receiving the controlled
                    write/read callback.

            Returns:
                The catalog from the initial consistent SQLite snapshot, unaffected by
                the separately committed WAL write.
            """
            nonlocal written
            result = original(store)
            if not written:
                written = True
                with closing(sqlite3.connect(path)) as writer, writer:
                    writer.execute("UPDATE jobs SET name='Concurrent'")
            return result

        with patch.object(JobCatalogStore, "read", read_then_write):
            assert reader.load_jobs() == CATALOG
        assert written
        assert reader.load_jobs() == changed

"""Job deletion cascades, retained assignments and transaction rollback.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path

import pytest

from ergotools.domain.job_catalog import WorkerJobAssignment
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from tests.test_history_persistence import ENTRY, HIERARCHY
from tests.test_job_management_save import first_values
from tests.test_risk_projects import seed


def prepare(path: Path) -> None:
    """Add an unassessed worker assignment and profiles for two separate jobs.

    Args:
        path: Disposable test file path; the caller controls creation and cleanup.

    Returns:
        None.
    """
    seed(path)
    with AssessmentProjectFile.open(path) as project:
        jobs = project.load_jobs()
        owner = HIERARCHY.work.worker_context("x", jobs.placements[1].workplace)
        jobs = replace(
            jobs, assignments=(*jobs.assignments, WorkerJobAssignment(2, owner, 2))
        )
        project.save_jobs(jobs)
        for job in jobs.jobs:
            project.save_job_details(
                project.load_jobs(),
                project.load_job_risk(),
                job,
                first_values(job.job_id),
            )


def test_delete_cascades_and_append_after_position_gap(tmp_path: Path) -> None:
    """Delete one job, retain worker/assessment records, then edit/create profiles.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "project.sqlite"
    prepare(path)
    with AssessmentProjectFile.open(path) as project:
        jobs, risk = project.load_jobs(), project.load_job_risk()
        saved_jobs, saved_risk = project.delete_job(jobs, risk, "k")
        assert tuple(item.job_id for item in saved_jobs.jobs) == ("j",)
        assert saved_jobs.assignments[0] == jobs.assignments[0]
        assert saved_jobs.assignments[1] == replace(
            jobs.assignments[1], placement_id=None
        )
        assert tuple(item.placement_id for item in saved_jobs.placements) == (1,)
        assert tuple(item.job_id for item in saved_risk.values) == ("j",)
        saved_jobs, risk = project.save_job_details(
            saved_jobs, saved_risk, saved_jobs.jobs[0], first_values("j")
        )
    with AssessmentProjectFile.open(path) as project:
        assert project.load_jobs() == saved_jobs
        assert project.load_job_risk() == risk
        assert project.load_history().entries == (ENTRY,)
    with closing(sqlite3.connect(path)) as connection:
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM risk_measurements WHERE job_id='k'"
            ).fetchone()[0]
            == 0
        )


def test_assessment_link_blocks_deletion_without_changes(tmp_path: Path) -> None:
    """A historically classified job cannot lose its recorded assessment link.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "project.sqlite"
    prepare(path)
    with AssessmentProjectFile.open(path) as project:
        jobs, risk = project.load_jobs(), project.load_job_risk()
        with pytest.raises(ValueError, match="referenced by an assessment"):
            project.delete_job(jobs, risk, "j")
        with pytest.raises(ValueError, match="existing job"):
            project.delete_job(jobs, risk, "missing")
        assert project.load_jobs() == jobs
        assert project.load_job_risk() == risk
        assert project.load_history().entries == (ENTRY,)


@pytest.mark.parametrize("table", ("risk_measurements", "job_placements", "jobs"))
def test_delete_write_failure_rolls_back_every_record(
    tmp_path: Path, table: str
) -> None:
    """A failure at each cascade stage restores evidence, placements and assignments.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        table: Owned risk table or explicit SQL table identity selected for fault
            injection.

    Returns:
        None.
    """
    path = tmp_path / "project.sqlite"
    prepare(path)
    with AssessmentProjectFile.open(path) as project:
        jobs, risk = project.load_jobs(), project.load_job_risk()
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute(
                f"CREATE TRIGGER reject_delete BEFORE DELETE ON {table} "
                "BEGIN SELECT RAISE(ABORT, 'delete failed'); END"
            )
        with pytest.raises(sqlite3.IntegrityError, match="delete failed"):
            project.delete_job(jobs, risk, "k")
        assert project.load_jobs() == jobs
        assert project.load_job_risk() == risk
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute("DROP TRIGGER reject_delete")
        project.delete_job(jobs, risk, "k")

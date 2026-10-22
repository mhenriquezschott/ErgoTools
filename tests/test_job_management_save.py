"""Atomic current Job details/risk replacement, source preservation and rollback."""

import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path

import pytest

from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_catalog import Job
from ergotools.domain.job_risk import JobRiskMeasurement, JobRiskValues
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from tests.test_history_persistence import ENTRY, SOURCE
from tests.test_risk_projects import seed


def first_values(job_id: str = "new") -> JobRiskValues:
    """Return zero-valued current LiFFT outputs with explicitly retained units.

    Args:
        job_id: Real parent Job ID in the caller's disposable project.

    Returns:
        One current risk set, without profile identity or lifecycle.
    """
    return JobRiskValues(
        job_id, (JobRiskMeasurement(AssessmentKind.LIFFT, 0, 0, "Imperial"),)
    )


def test_first_save_replace_and_metadata_only(tmp_path: Path) -> None:
    """Save/reopen direct values; editing replaces them and metadata alone retains them.

    Args:
        tmp_path: Disposable project directory.

    Returns:
        None; sources and assignment history remain exact.
    """
    path = tmp_path / "project.sqlite"
    seed(path)
    with AssessmentProjectFile.open(path) as project:
        original = project.load_jobs()
        jobs, risk = project.save_job_details(
            original,
            project.load_job_risk(),
            Job(" new ", " Assembly ", False, " Description "),
            first_values(),
        )
        assert jobs.jobs[-1] == Job("new", "Assembly", False, "Description")
        assert risk.for_job("new") == first_values()
        changed = replace(
            first_values(),
            measurements=(JobRiskMeasurement(AssessmentKind.DUET, 1, 50),),
        )
        jobs, risk = project.save_job_details(
            jobs, risk, Job("new", "Revised"), changed
        )
        jobs, risk = project.save_job_details(jobs, risk, Job("new", "Renamed"), None)
        assert risk.for_job("new") == changed
        assert (
            jobs.assignments == original.assignments
            and jobs.placements == original.placements
        )
    with AssessmentProjectFile.open(path) as reopened:
        assert reopened.load_jobs() == jobs and reopened.load_job_risk() == risk
        assert reopened.load_history().entries == (ENTRY,)
        assert reopened.load(DocumentKey("p", ENTRY.document_id)) == SOURCE


@pytest.mark.parametrize("failure", ("job", "measurement"))
def test_storage_failure_rolls_back_entire_form(tmp_path: Path, failure: str) -> None:
    """Injected SQLite failures restore metadata and current risks together.

    Args:
        tmp_path: Disposable project directory.
        failure: Table write that is forced to fail.

    Returns:
        None; the same expected state supports retry after removing the fault.
    """
    path = tmp_path / "project.sqlite"
    seed(path)
    with AssessmentProjectFile.open(path) as project:
        jobs, risk = project.load_jobs(), project.load_job_risk()
        table, event = (
            ("jobs", "UPDATE") if failure == "job" else ("risk_measurements", "INSERT")
        )
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute(
                f"CREATE TRIGGER fail_save BEFORE {event} ON {table} "
                "BEGIN SELECT RAISE(ABORT, 'simulated write failure'); END"
            )
        with pytest.raises(sqlite3.IntegrityError, match="simulated"):
            project.save_job_details(
                jobs, risk, Job("j", "Must roll back"), first_values("j")
            )
        assert project.load_jobs() == jobs and project.load_job_risk() == risk
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute("DROP TRIGGER fail_save")
        saved, _ = project.save_job_details(
            jobs, risk, Job("j", "Retry"), first_values("j")
        )
        assert saved.jobs[0].name == "Retry"


def test_missing_risk_is_allowed_but_foreign_owner_is_not(tmp_path: Path) -> None:
    """Jobs may be created without risks; another Job's values cannot be smuggled in.

    Args:
        tmp_path: Disposable project directory.

    Returns:
        None; invalid ownership leaves the saved catalogs unchanged.
    """
    path = tmp_path / "project.sqlite"
    seed(path)
    with AssessmentProjectFile.open(path) as project:
        jobs, risk = project.save_job_details(
            project.load_jobs(), project.load_job_risk(), Job("new", "No values"), None
        )
        assert not risk.for_job("new").measurements
        with pytest.raises(ValueError):
            project.save_job_details(jobs, risk, Job("new", "Wrong"), first_values("j"))
        assert project.load_jobs() == jobs and project.load_job_risk() == risk

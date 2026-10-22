"""Explicit risk-capable projects and combined historical reference protection.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_risk import JobRiskMeasurement, JobRiskValues
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.draft_store import StoreFormatError
from ergotools.infrastructure.job_catalog_store import JobCatalogStore
from ergotools.infrastructure.job_risk_store import JobRiskStore
from tests.test_history_persistence import ENTRY, HIERARCHY, JOBS, META, SOURCE


def seed(path: Path) -> None:
    """Build a complete synthetic version-seven project with historical source.

    Args:
        path: Disposable test file path; the caller controls creation and cleanup.

    Returns:
        None.
    """
    with AssessmentProjectFile.create_with_job_risks(
        path, replace(META, default_units=MeasurementSystem.METRIC)
    ) as project:
        project.save_hierarchy(HIERARCHY)
        project.save_jobs(JOBS)
        project.create_historical_assessment(ENTRY, SOURCE)


def test_current_risks_reopen_without_changing_sources(tmp_path: Path) -> None:
    """Current values and original worker history survive replacement/reopen exactly.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; no alternate profile or evidence tables exist.
    """
    path = tmp_path / "project.sqlite"
    seed(path)
    with AssessmentProjectFile.open(path) as project:
        jobs = project.load_jobs()
        _, risks = project.save_job_details(
            jobs,
            project.load_job_risk(),
            jobs.jobs[0],
            JobRiskValues(
                "j", (JobRiskMeasurement(AssessmentKind.LIFFT, 0, 0, "Imperial"),)
            ),
        )
    with AssessmentProjectFile.open(path) as project:
        assert project.load_job_risk() == risks
        assert project.load(DocumentKey("p", ENTRY.document_id)) == SOURCE
        assert project.load_history().entries == (ENTRY,)
    with closing(sqlite3.connect(path)) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert not tables & {"risk_profiles", "risk_metadata"}


@pytest.mark.parametrize(
    "factory",
    (
        "create",
        "create_contextual",
        "create_catalogued",
        "create_with_jobs",
        "create_historical",
    ),
)
def test_older_project_formats_are_not_upgraded(tmp_path: Path, factory: str) -> None:
    """Diagnostic older formats gain no Job-risk capability by merely being read.

    Args:
        tmp_path: Disposable native project directory.
        factory: Existing diagnostic constructor.

    Returns:
        None; unsupported capability raises without altering the version.
    """
    path = tmp_path / "old.sqlite"
    with getattr(AssessmentProjectFile, factory)(path, META) as project:
        version = project.format_version
        assert not project.supports_job_risk
        with pytest.raises(StoreFormatError):
            project.load_job_risk()
    with AssessmentProjectFile.open(path) as project:
        assert project.format_version == version


@pytest.mark.parametrize("damage", ("orphan", "source", "missing_table"))
def test_project_open_rejects_invalid_risk_data(tmp_path: Path, damage: str) -> None:
    """Native read rejects corrupt sources, missing schemas and dangling Job parents.

    Args:
        tmp_path: Disposable project directory.
        damage: Deliberate database corruption.

    Returns:
        None; no corrupt project handle is exposed.
    """
    path = tmp_path / "damaged.sqlite"
    seed(path)
    with AssessmentProjectFile.open(path) as project:
        jobs = project.load_jobs()
        project.save_job_details(
            jobs,
            project.load_job_risk(),
            jobs.jobs[0],
            JobRiskValues("j", (JobRiskMeasurement(AssessmentKind.LIFFT, 0, 0),)),
        )
    with closing(sqlite3.connect(path)) as connection, connection:
        if damage == "orphan":
            connection.execute("UPDATE risk_measurements SET job_id='missing'")
        elif damage == "source":
            connection.execute("UPDATE risk_measurements SET source='bad'")
        else:
            connection.execute("DROP TABLE risk_measurements")
    with pytest.raises((ValueError, sqlite3.Error)):
        AssessmentProjectFile.open(path)


def test_failed_creation_cleanup_and_transaction_guard(tmp_path: Path) -> None:
    """Failed schema creation cleans its own file and never overwrites an existing one.

    Args:
        tmp_path: Disposable project directory.

    Returns:
        None; transaction ownership remains enforced.
    """
    path = tmp_path / "failed.sqlite"
    with (
        patch(
            "ergotools.infrastructure.assessment_project_file.create_risk_schema",
            side_effect=OSError("schema failure"),
        ),
        pytest.raises(OSError),
    ):
        AssessmentProjectFile.create_with_job_risks(path, META)
    assert not path.exists()
    seed(path)
    with pytest.raises(FileExistsError):
        AssessmentProjectFile.create_with_job_risks(path, META)
    with closing(sqlite3.connect(path)) as connection:
        jobs = JobCatalogStore(connection, "p")
        risk = JobRiskStore(connection, "p", jobs.read)
        with pytest.raises(RuntimeError):
            risk.validate_job_change(JOBS, JOBS)

"""Current risk storage conflicts, caller transaction ownership and injectedrollback."""

import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path

import pytest

from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_risk import JobRiskMeasurement, JobRiskValues
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.job_catalog_store import JobCatalogStore
from ergotools.infrastructure.job_risk_store import JobRiskStore, create_risk_schema
from tests.test_job_management_save import first_values
from tests.test_risk_projects import seed


def test_competing_writer_and_foreign_expected(tmp_path: Path) -> None:
    """Stale and foreign current-value snapshots cannot overwrite another writer.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; the concurrent result is retained exactly.
    """
    path = tmp_path / "conflict.sqlite"
    seed(path)
    with (
        AssessmentProjectFile.open(path) as first,
        AssessmentProjectFile.open(path) as other,
    ):
        jobs, before = first.load_jobs(), first.load_job_risk()
        _, changed = other.save_job_details(
            jobs, before, jobs.jobs[0], first_values("j")
        )
        for expected in (before, replace(changed, project_id="foreign")):
            with pytest.raises(ValueError, match="changed"):
                first.save_job_details(jobs, expected, jobs.jobs[0], first_values("j"))
        assert first.load_job_risk() == changed


def test_transaction_ownership_and_postwrite_validation(tmp_path: Path) -> None:
    """Nested operations and trigger-induced output drift fail without partial writes.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; ownership and verified round trips remain enforced.
    """
    path = tmp_path / "scope.sqlite"
    seed(path)
    with closing(sqlite3.connect(path)) as connection:
        with pytest.raises(RuntimeError):
            create_risk_schema(connection, "p")
        jobs_store = JobCatalogStore(connection, "p")
        store = JobRiskStore(connection, "p", jobs_store.read)
        connection.execute("BEGIN")
        with pytest.raises(RuntimeError):
            store.read()
        connection.rollback()
        connection.execute(
            "CREATE TRIGGER drift AFTER INSERT ON risk_measurements "
            "BEGIN UPDATE risk_measurements SET probability=99 WHERE "
            "job_id=NEW.job_id AND kind=NEW.kind; END"
        )
    with AssessmentProjectFile.open(path) as project:
        jobs, risks = project.load_jobs(), project.load_job_risk()
        with pytest.raises(ValueError, match="differ"):
            project.save_job_details(jobs, risks, jobs.jobs[0], first_values("j"))
        assert project.load_jobs() == jobs and project.load_job_risk() == risks


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_missing_outputs_remain_missing(tmp_path: Path, kind: AssessmentKind) -> None:
    """An uncalculated calculator source round trips without manufacturing zero risk.

    Args:
        tmp_path: Disposable native project directory.
        kind: Each retained calculator identity.

    Returns:
        None; exact source identity and blank task survive reopen.
    """
    from ergotools.application.job_calculation import blank_job_source
    from ergotools.domain.model_units import MeasurementSystem

    path = tmp_path / "source.sqlite"
    seed(path)
    source = blank_job_source(kind, MeasurementSystem.METRIC)
    value = JobRiskValues("j", (JobRiskMeasurement(kind, source=source),))
    with AssessmentProjectFile.open(path) as project:
        jobs = project.load_jobs()
        project.save_job_details(jobs, project.load_job_risk(), jobs.jobs[0], value)
    with AssessmentProjectFile.open(path) as reopened:
        assert reopened.load_job_risk().for_job("j") == value
        assert not reopened.load_job_risk().for_job("j").measurements[0].complete


@pytest.mark.parametrize("mutation", ("source", "output_shape", "output_version"))
def test_calculated_task_outputs_are_bound_to_exact_sources(
    tmp_path: Path, mutation: str
) -> None:
    """Corrupt same-sized input changes cannot masquerade as a current Job calculation.

    Args:
        tmp_path: Disposable native project directory.
        mutation: Deliberate input-binding or task-output envelope corruption.

    Returns:
        None; opening fails instead of displaying stale or invented outputs.
    """
    import json

    from ergotools.application.job_calculation import calculate_job_measurement
    from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
    from ergotools.domain.model_units import MeasurementSystem
    from ergotools.infrastructure.assessment_serialization import (
        decode_assessment,
        encode_assessment,
    )

    source = LifftDraft(MeasurementSystem.METRIC, (LifftTask("task", 30, 49.05, 100),))
    path = tmp_path / "binding.sqlite"
    seed(path)
    value = calculate_job_measurement("p", "j", source, MeasurementSystem.METRIC)
    with AssessmentProjectFile.open(path) as project:
        jobs = project.load_jobs()
        project.save_job_details(
            jobs, project.load_job_risk(), jobs.jobs[0], JobRiskValues("j", (value,))
        )
    with closing(sqlite3.connect(path)) as connection, connection:
        if mutation == "source":
            text = connection.execute(
                "SELECT source FROM risk_measurements"
            ).fetchone()[0]
            saved = decode_assessment(text)
            changed = replace(saved, tasks=(replace(saved.tasks[0], load=50),))
            connection.execute(
                "UPDATE risk_measurements SET source=?", (encode_assessment(changed),)
            )
        else:
            data = json.loads(
                connection.execute(
                    "SELECT task_results FROM risk_measurements"
                ).fetchone()[0]
            )
            if mutation == "output_shape":
                data["tasks"] = [[1, 2]]
            else:
                data["version"] = 2
            connection.execute(
                "UPDATE risk_measurements SET task_results=?", (json.dumps(data),)
            )
    with pytest.raises(ValueError):
        AssessmentProjectFile.open(path)

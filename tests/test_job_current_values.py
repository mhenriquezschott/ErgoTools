"""Single current Job risk replacement and dependent rotation invalidation."""

from dataclasses import replace
from pathlib import Path

from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_risk import JobRiskMeasurement, JobRiskValues
from ergotools.domain.rotation_scheme import RotationMode
from tests.test_rotation_persistence import scheme, seed


def test_risk_edit_retains_schedule_and_invalidates_optimization(
    tmp_path: Path,
) -> None:
    """An affected optimized schedule keeps every cell but requires an explicit rerun.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; metadata-only updates preserve existing provenance.
    """
    with seed(tmp_path / "rotation.sqlite") as project:
        original = replace(
            scheme(), mode=RotationMode.SINGLE_TOOL, primary_kind=AssessmentKind.LIFFT
        )
        project.save_rotation_scheme(original)
        jobs, risks = project.load_jobs(), project.load_job_risk()
        project.save_job_details(
            jobs, risks, replace(jobs.jobs[0], name="Renamed"), None
        )
        assert project.load_rotation_schemes() == (original,)
        jobs, risks = project.load_jobs(), project.load_job_risk()
        project.save_job_details(
            jobs,
            risks,
            jobs.jobs[0],
            JobRiskValues("j", (JobRiskMeasurement(AssessmentKind.LIFFT, 1, 80),)),
        )
        saved = project.load_rotation_schemes()[0]
        assert saved.current == original.current and saved.targets == original.targets
        assert saved.mode is RotationMode.MANUAL and saved.primary_kind is None


def test_closed_rotation_draft_cannot_restore_obsolete_provenance(
    tmp_path: Path,
) -> None:
    """Main Save refreshes retained JROT values even if its window was never reopened.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; Job edits survive the retained rotation validator without old risk values.
    """
    from ergotools.application.rotation_draft import (
        RotationProjectDraft,
        stage_rotation_draft,
    )
    from ergotools.application.rotation_history import RotationEditState
    from ergotools.application.rotation_pool import rotation_pool

    with seed(tmp_path / "retained.sqlite") as project:
        original = replace(
            scheme(), mode=RotationMode.SINGLE_TOOL, primary_kind=AssessmentKind.LIFFT
        )
        project.save_rotation_scheme(original)
        pool = rotation_pool(project, original.scope, saved=original)
        draft = RotationProjectDraft(
            original.scheme_id,
            RotationEditState(
                pool,
                2,
                (("w", *original.current[0].target_keys),),
                original.scope,
                False,
                original.mode,
                original.primary_kind,
            ),
            original,
        )
        jobs, risks = project.load_jobs(), project.load_job_risk()
        project.save_job_details(
            jobs,
            risks,
            jobs.jobs[0],
            JobRiskValues("j", (JobRiskMeasurement(AssessmentKind.LIFFT, 1, 80),)),
        )
        stage_rotation_draft(project, draft)
        saved = project.load_rotation_schemes()[0]
        assert saved.current == original.current and saved.mode is RotationMode.MANUAL
        assert (
            project.load_job_risk().for_job("j").measurements[0].probability_percent
            == 80
        )


def test_rotation_write_failure_rolls_back_job_and_current_risks(
    tmp_path: Path,
) -> None:
    """A late dependent-schedule failure cannot publish half a current Job change.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; retry after removing the fault retains arrangements and clears provenance.
    """
    import sqlite3
    from contextlib import closing

    import pytest

    path = tmp_path / "atomic.sqlite"
    with seed(path) as project:
        original = replace(
            scheme(), mode=RotationMode.SINGLE_TOOL, primary_kind=AssessmentKind.LIFFT
        )
        project.save_rotation_scheme(original)
        jobs, risks = project.load_jobs(), project.load_job_risk()
        values = JobRiskValues("j", (JobRiskMeasurement(AssessmentKind.LIFFT, 1, 80),))
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute(
                "CREATE TRIGGER fail_rotation BEFORE UPDATE ON rotation_schemes "
                "BEGIN SELECT RAISE(ABORT,'late failure'); END"
            )
        with pytest.raises(sqlite3.IntegrityError, match="late failure"):
            project.save_job_details(
                jobs, risks, replace(jobs.jobs[0], name="Uncommitted"), values
            )
        assert project.load_jobs() == jobs
        assert project.load_job_risk() == risks
        assert project.load_rotation_schemes() == (original,)
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute("DROP TRIGGER fail_rotation")
        project.save_job_details(jobs, risks, jobs.jobs[0], values)
        saved = project.load_rotation_schemes()[0]
        assert saved.current == original.current and saved.mode is RotationMode.MANUAL

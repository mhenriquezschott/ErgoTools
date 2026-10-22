"""Workspace risk authority, source isolation and adapter failure recovery.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from ergotools.application.assessments.lifft_commands import AddLifftTask
from ergotools.application.assessments.project_edits import LifftProjectEdit
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.job_risk_access import JobRiskSnapshot
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.domain.assessments.document import AssessmentDraft, AssessmentKind
from ergotools.domain.assessments.lifft_draft import LifftTask
from ergotools.domain.job_risk import JobRiskCatalog, JobRiskMeasurement, JobRiskValues
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.settings_store import JsonSettingsStore
from tests.test_history_persistence import ENTRY, META, SOURCE
from tests.test_risk_projects import seed


def workspace_at(tmp_path: Path) -> ProjectWorkspace[AssessmentDraft]:
    """Open a synthetic risk-capable project through its public adapter.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        Owned synthetic risk-capable workspace opened through its real public adapter;
        caller closes it.
    """
    path = tmp_path / "project.sqlite"
    seed(path)
    workspace: ProjectWorkspace[AssessmentDraft] = ProjectWorkspace(
        lambda location: AssessmentProjectFile.open(Path(location)),
        JsonSettingsStore(tmp_path / "settings.json"),
    )
    workspace.switch(str(path), ENTRY.document_id)
    return workspace


def test_job_changes_preserve_active_source_and_reject_stale_views(
    tmp_path: Path,
) -> None:
    """Job edits leave the active assessment untouched and cannot reuse old authorities.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; successful writes refresh both authorities together.
    """
    workspace = workspace_at(tmp_path)
    try:
        active = workspace.active
        active.execute(
            LifftProjectEdit(
                AddLifftTask(active.document, LifftTask("t", 12, 10, 100), 0)
            )
        )
        revision = active.revision
        settings = (tmp_path / "settings.json").read_bytes()
        jobs, risks = workspace.read_jobs(), workspace.read_job_risk()
        current = JobRiskValues(
            "j", (JobRiskMeasurement(AssessmentKind.LIFFT, 0, 0, "Imperial"),)
        )
        saved_jobs, saved_risks = workspace.save_job_details(
            jobs, risks, jobs.jobs.jobs[0], current
        )
        assert (
            workspace.active is active
            and active.is_dirty
            and active.revision == revision
        )
        assert (tmp_path / "settings.json").read_bytes() == settings
        assert saved_risks.risk.for_job("j") == current
        with pytest.raises(ValueError):
            workspace.save_job_details(jobs, risks, jobs.jobs.jobs[0], current)
        assert workspace.jobs_are_current(saved_jobs) and workspace.job_risk_is_current(
            saved_risks
        )
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("change", ("refresh", "jobs", "switch", "reopen"))
def test_risk_view_invalidation(tmp_path: Path, change: str) -> None:
    """Refresh, catalog writes and project lifetimes revoke old callback authority.

    Args:
        tmp_path: Disposable native project directory.
        change: Operation revoking the original view.

    Returns:
        None; manufactured equal snapshots never acquire authority.
    """
    workspace = workspace_at(tmp_path)
    try:
        view = workspace.read_job_risk()
        assert not workspace.job_risk_is_current(JobRiskSnapshot(view.risk))
        if change == "refresh":
            workspace.read_job_risk()
        elif change == "jobs":
            jobs = workspace.read_jobs()
            workspace.replace_jobs(jobs, jobs.jobs)
        elif change == "switch":
            other = tmp_path / "other.sqlite"
            seed(other)
            workspace.switch(str(other), ENTRY.document_id)
        else:
            workspace.close()
            workspace.switch(str(tmp_path / "project.sqlite"), ENTRY.document_id)
        assert not workspace.job_risk_is_current(view)
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_failure_retry_and_inconsistent_adapter(tmp_path: Path) -> None:
    """Write failure permits retry; inconsistent returned values revoke authority.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; failed calls do not publish replacement views.
    """
    workspace = workspace_at(tmp_path)
    try:
        jobs, risks = workspace.read_jobs(), workspace.read_job_risk()
        values = JobRiskValues("j", (JobRiskMeasurement(AssessmentKind.DUET, 1, 50),))
        with (
            patch.object(
                AssessmentProjectFile, "save_job_details", side_effect=OSError("disk")
            ),
            pytest.raises(OSError),
        ):
            workspace.save_job_details(jobs, risks, jobs.jobs.jobs[0], values)
        assert workspace.job_risk_is_current(risks)
        with (
            patch.object(
                AssessmentProjectFile,
                "save_job_details",
                return_value=(jobs.jobs, risks.risk),
            ),
            pytest.raises(ValueError, match="differs"),
        ):
            workspace.save_job_details(jobs, risks, jobs.jobs.jobs[0], values)
        assert not workspace.job_risk_is_current(risks)
        jobs, risks = workspace.read_jobs(), workspace.read_job_risk()
        _, saved = workspace.save_job_details(jobs, risks, jobs.jobs.jobs[0], values)
        assert saved.risk.for_job("j") == values
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_failed_or_foreign_refresh_revokes_authority(tmp_path: Path) -> None:
    """Even failed refreshes revoke previously issued risk views.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; successful retry restores valid authority.
    """
    workspace = workspace_at(tmp_path)
    try:
        view = workspace.read_job_risk()
        with (
            patch.object(
                AssessmentProjectFile, "load_job_risk", side_effect=OSError("read")
            ),
            pytest.raises(OSError),
        ):
            workspace.read_job_risk()
        assert not workspace.job_risk_is_current(view)
        with (
            patch.object(
                AssessmentProjectFile,
                "load_job_risk",
                return_value=JobRiskCatalog("foreign"),
            ),
            pytest.raises(ValueError),
        ):
            workspace.read_job_risk()
        assert workspace.job_risk_is_current(workspace.read_job_risk())
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_capability_and_no_open_project(tmp_path: Path) -> None:
    """Closed or older diagnostic projects expose no current Job-risk capability.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; reading never upgrades an old project.
    """
    workspace = workspace_at(tmp_path)
    workspace.close()
    assert not workspace.supports_job_risk
    with pytest.raises(RuntimeError):
        workspace.read_job_risk()
    old = tmp_path / "old.sqlite"
    with AssessmentProjectFile.create_with_document(old, META, "a", SOURCE):
        pass
    try:
        workspace.switch(str(old), "a")
        assert not workspace.supports_job_risk
        with pytest.raises(RuntimeError):
            workspace.read_job_risk()
    finally:
        workspace.close()

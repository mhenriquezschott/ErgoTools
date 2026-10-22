"""Presenter ownership, active eligibility, dirty choices and creation integration.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from ergotools.application.assessments.lifft_commands import AddLifftTask
from ergotools.application.assessments.project_edits import LifftProjectEdit
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessments.document import AssessmentDraft, AssessmentKind
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
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
from ergotools.infrastructure.settings_store import JsonSettingsStore
from ergotools.presentation.assignment_selection import AssignmentSelector

# Immutable synthetic imperial LiFFT draft; missing inputs remain absent rather than
# becoming zeros.
SOURCE = LifftDraft(MeasurementSystem.IMPERIAL)


@pytest.fixture
def workspace(tmp_path: Path) -> Iterator[ProjectWorkspace[AssessmentDraft]]:
    """Own a temporary historical project with active and closed assignments.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Yields:
        Owned temporary historical workspace; fixture cleanup closes the coordinator
        after the test.
    """
    station = StationKey("P", "S", "L", "1")
    hierarchy = WorkHierarchy(
        WorkCatalog("p", (WorkerEntry("w"),), (station,), ("Day",)),
        ("P",),
        (SectionKey("P", "S"),),
        (LineKey("P", "S", "L"),),
    )
    worker = hierarchy.work.worker_context("w", station.at_shift("Day"))
    jobs = JobCatalog(
        "p",
        (Job("j", "Job", False),),
        (JobPlacement(1, "j", worker.workplace),),
        (WorkerJobAssignment(1, worker, 1, False), WorkerJobAssignment(2, worker, 1)),
    )
    path = tmp_path / "project.sqlite"
    with AssessmentProjectFile.create_historical(
        path, ProjectMetadata("p", "Test", MeasurementSystem.IMPERIAL)
    ) as project:
        project.save_hierarchy(hierarchy)
        project.save_jobs(jobs)
        for name, identity in (("old", 1), ("active", 2)):
            project.create_historical_assessment(
                AssignmentAssessment(
                    name,
                    identity,
                    AssessmentKind.LIFFT,
                    worker_id=next(
                        a.worker.worker_id
                        for a in jobs.assignments
                        if a.assignment_id == identity
                    ),
                ),
                SOURCE,
            )
    workspace = ProjectWorkspace(
        lambda location: AssessmentProjectFile.open(Path(location)),
        JsonSettingsStore(tmp_path / "settings.json"),
    )
    try:
        workspace.switch(str(path), "old")
        yield workspace
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_explicit_active_selection_and_cancel_retry(
    workspace: ProjectWorkspace,
) -> None:
    """Ignore job activity, exclude closed rows and preserve cancelled requests.

    Args:
        workspace: Test-owned project/session coordinator; operational project data are
            never used.

    Returns:
        None.
    """
    selector = AssignmentSelector(workspace)
    catalog = selector.refresh()
    assert [
        item.assignment.assignment_id for item in selector.options(catalog, "w")
    ] == [2]
    assert selector.options(catalog, "missing") == ()
    for worker, identity in (("w", 1), ("other", 2), ("w", 99)):
        with pytest.raises(KeyError):
            selector.prepare(catalog, worker, identity, AssessmentKind.LIFFT)
    request = selector.prepare(catalog, "w", 2, AssessmentKind.LIFFT)
    assert not selector.select(request, choice=CloseChoice.CANCEL).completed
    assert selector.select(request).completed
    assert workspace.active.document.document_id == "active"
    with pytest.raises(ValueError):
        selector.select(request)


def test_forged_refreshed_and_changed_source_requests(
    workspace: ProjectWorkspace,
) -> None:
    """Equal copies and callbacks prepared before edits or refresh cannot act.

    Args:
        workspace: Test-owned project/session coordinator; operational project data are
            never used.

    Returns:
        None.
    """
    selector = AssignmentSelector(workspace)
    catalog = selector.refresh()
    with pytest.raises(ValueError):
        selector.options(replace(catalog), "w")
    request = selector.prepare(catalog, "w", 2, AssessmentKind.LIFFT)
    with pytest.raises(ValueError):
        selector.select(replace(request))
    active = workspace.active
    active.execute(
        LifftProjectEdit(AddLifftTask(active.document, LifftTask("t", 12, 10, 100), 0))
    )
    with pytest.raises(ValueError, match="Active"):
        selector.select(request, choice=CloseChoice.SAVE)
    request = selector.prepare(catalog, "w", 2, AssessmentKind.LIFFT)
    assert not selector.select(request).completed
    assert selector.select(request, choice=CloseChoice.DISCARD).completed
    request = selector.prepare(catalog, "w", 2, AssessmentKind.LIFFT)
    workspace.read_jobs()
    with pytest.raises(ValueError, match="catalog"):
        selector.select(request)
    with (
        patch.object(AssessmentProjectFile, "load_jobs", side_effect=OSError("read")),
        pytest.raises(OSError),
    ):
        selector.refresh()
    with pytest.raises(ValueError):
        selector.options(catalog, "w")


def test_create_selected_model_and_failed_retry(workspace: ProjectWorkspace) -> None:
    """Model mismatch fails early; cancellation and repository failure permit retry.

    Args:
        workspace: Test-owned project/session coordinator; operational project data are
            never used.

    Returns:
        None.
    """
    selector = AssignmentSelector(workspace)
    catalog = selector.refresh()
    request = selector.prepare(catalog, "w", 2, AssessmentKind.DUET)
    with pytest.raises(ValueError, match="model"):
        selector.create(request, "new", SOURCE)
    assert not selector.create(
        request, "new", DuetDraft(), choice=CloseChoice.CANCEL
    ).completed
    with (
        patch.object(
            AssessmentProjectFile,
            "create_historical_assessment",
            side_effect=OSError("insert"),
        ),
        pytest.raises(OSError),
    ):
        selector.create(request, "new", DuetDraft())
    assert selector.create(request, "new", DuetDraft()).completed
    assert workspace.active.document.document_id == "new"
    with pytest.raises(ValueError):
        selector.create(request, "again", DuetDraft())
    request = selector.prepare(catalog, "w", 2, AssessmentKind.DUET)
    with pytest.raises(ValueError):
        selector.create(request, "later", DuetDraft())
    assert workspace.active.document.document_id == "new"


def test_project_close_and_external_snapshot_refresh_invalidate(
    workspace: ProjectWorkspace,
) -> None:
    """Project handle ownership and presenter refresh cannot transfer authority.

    Args:
        workspace: Test-owned project/session coordinator; operational project data are
            never used.

    Returns:
        None.
    """
    selector = AssignmentSelector(workspace)
    catalog = selector.refresh()
    request = selector.prepare(catalog, "w", 2, AssessmentKind.LIFFT)
    selector.refresh()
    with pytest.raises(ValueError):
        selector.select(request)
    catalog = selector.refresh()
    request = selector.prepare(catalog, "w", 2, AssessmentKind.LIFFT)
    workspace.close()
    with pytest.raises(ValueError):
        selector.select(request)

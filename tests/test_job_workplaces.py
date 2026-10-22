"""Reference placement selection and safe persistence through the workspace.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from ergotools.application.assessments.lifft_commands import AddLifftTask
from ergotools.application.assessments.project_edits import LifftProjectEdit
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.job_placements import replace_active_placements
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessments.document import AssessmentDraft, AssessmentKind
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
from ergotools.presentation.job_workplaces import JobWorkplaces

# Exact three-station synthetic ancestry sequence in stable catalog order.
STATIONS = tuple(StationKey("P", "S", "L", str(n)) for n in (1, 2, 3))
# Synthetic Day contexts for each station; other shifts remain independent.
PLACES = tuple(station.at_shift("Day") for station in STATIONS)
# Immutable synthetic complete hierarchy, including the empty branches/shifts needed by
# these tests.
HIERARCHY = WorkHierarchy(
    WorkCatalog("p", (WorkerEntry("w"),), STATIONS, ("Day", "Night")),
    ("P",),
    (SectionKey("P", "S"),),
    (LineKey("P", "S", "L"),),
)
# Exact project/worker/workplace/shift ownership used to distinguish historical
# assignment links.
OWNER = HIERARCHY.work.worker_context("w", PLACES[0])
# Immutable synthetic jobs, placements and assignment history with exact retained links.
JOBS = JobCatalog(
    "p",
    (Job("j", "Job", False), Job("k", "Other")),
    (
        JobPlacement(1, "j", PLACES[0], notes="original"),
        JobPlacement(2, "j", PLACES[1], False, "2020-01-01", "2020-12-31", "older"),
        JobPlacement(3, "j", PLACES[1], False, "2021-01-01", "2021-12-31", "latest"),
        JobPlacement(4, "k", PLACES[0], notes="other"),
    ),
    (WorkerJobAssignment(1, OWNER, 1),),
)
# Exact synthetic current assessment version linked to assignment 1.
ENTRY = AssignmentAssessment(
    "a",
    1,
    AssessmentKind.LIFFT,
    worker_id=next(
        a.worker.worker_id for a in JOBS.assignments if a.assignment_id == 1
    ),
)
# Immutable synthetic imperial LiFFT draft; missing inputs remain absent rather than
# becoming zeros.
SOURCE = LifftDraft(MeasurementSystem.IMPERIAL)


def test_reference_placement_transitions() -> None:
    """Match original deactivate/reactivate/add behavior, including saved metadata.

    Args:
        None.

    Returns:
        None.
    """
    fixture = json.loads(
        (Path(__file__).parent / "fixtures/job_placements_reference.json").read_text()
    )
    for case in fixture["cases"]:
        requested = [STATIONS[int(n) - 1].at_shift("Day") for n in case["selected"]]
        result = replace_active_placements(JOBS, "j", requested)
        rows = [
            [
                p.placement_id,
                p.job_id,
                p.workplace.station_id,
                int(p.active),
                p.valid_from,
                p.valid_to,
                p.notes,
            ]
            for p in result.placements
        ]
        assert rows == case["rows"]
        assert result.assignments == JOBS.assignments


def test_duplicate_noop_and_invalid_job() -> None:
    """Repeated selections are harmless; unknown jobs and untyped contexts fail.

    Args:
        None.

    Returns:
        None.
    """
    assert replace_active_placements(JOBS, "j", (PLACES[0], PLACES[0])) is JOBS
    with pytest.raises(ValueError, match="Job does not exist"):
        replace_active_placements(JOBS, "missing", ())
    with pytest.raises(ValueError, match="typed contexts"):
        replace_active_placements(JOBS, "j", ("invalid",))


def seed_workspace(tmp_path: Path) -> ProjectWorkspace[AssessmentDraft]:
    """Open a synthetic project with a historically referenced placement.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        Owned initialized synthetic workspace retaining an assessment-referenced
        historical placement.
    """
    path = tmp_path / "project.sqlite"
    with AssessmentProjectFile.create_initialized_historical(
        path,
        ProjectMetadata("p", "Jobs", MeasurementSystem.IMPERIAL),
        HIERARCHY,
        JOBS,
        ENTRY,
        SOURCE,
    ):
        pass
    workspace: ProjectWorkspace[AssessmentDraft] = ProjectWorkspace(
        lambda location: AssessmentProjectFile.open(Path(location)),
        JsonSettingsStore(tmp_path / "settings.json"),
    )
    workspace.switch(str(path), "a")
    return workspace


def test_save_all_shifts_preserves_dirty_source_and_history(tmp_path: Path) -> None:
    """Unchecking and rechecking retain assessment ownership and pending edits.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = seed_workspace(tmp_path)
    try:
        active = workspace.active
        active.execute(
            LifftProjectEdit(
                AddLifftTask(active.document, LifftTask("t", 12, 10, 100), 0)
            )
        )
        editor = JobWorkplaces(workspace)
        view = editor.load("j")
        assert len(view.options) == 6
        assert view.selected == frozenset((PLACES[0],))
        night = STATIONS[2].at_shift("Night")
        saved = editor.save(view, (PLACES[1], night))
        assert saved.selected == frozenset((PLACES[1], night))
        assert workspace.active is active and active.is_dirty
        with AssessmentProjectFile.open(tmp_path / "project.sqlite") as project:
            assert project.load_history().entries == (ENTRY,)
            assert project.load(active.document) == SOURCE
            assert project.load_jobs().assignments == JOBS.assignments
        with pytest.raises(ValueError, match="stale"):
            editor.save(view, ())
        cleared = editor.save(saved, ())
        assert not cleared.selected
        restored = editor.save(cleared, (PLACES[0],))
        assert next(
            p for p in restored.catalog.jobs.placements if p.placement_id == 1
        ).active
        assert workspace.read_history().history.entries == (ENTRY,)
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("invalidate", ("jobs", "hierarchy", "close", "failed_load"))
def test_stale_view_rejected(tmp_path: Path, invalidate: str) -> None:
    """Refresh, project close and a failed load invalidate modal callback authority.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        invalidate: Named source/view operation used to revoke previously prepared
            editor authority.

    Returns:
        None.
    """
    workspace = seed_workspace(tmp_path)
    editor = JobWorkplaces(workspace)
    try:
        view = editor.load("j")
        if invalidate == "jobs":
            workspace.read_jobs()
        elif invalidate == "hierarchy":
            workspace.read_hierarchy()
        elif invalidate == "close":
            workspace.close()
        else:
            with pytest.raises(ValueError, match="Job does not exist"):
                editor.load("missing")
        with pytest.raises(ValueError, match="stale"):
            editor.save(view, ())
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_failure_retry_and_external_conflict(tmp_path: Path) -> None:
    """Invalid membership and I/O failure preserve saved data and allow retry.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = seed_workspace(tmp_path)
    try:
        editor = JobWorkplaces(workspace)
        view = editor.load("j")
        with pytest.raises(ValueError, match="hierarchy"):
            editor.save(view, (replace(PLACES[0], shift_id="missing"),))
        with (
            patch.object(
                AssessmentProjectFile, "replace_jobs", side_effect=OSError("write")
            ),
            pytest.raises(OSError),
        ):
            editor.save(view, ())
        assert editor.save(view, (PLACES[0],)).selected == view.selected
        view = editor.load("j")
        with AssessmentProjectFile.open(tmp_path / "project.sqlite") as project:
            project.save_jobs(replace(JOBS, jobs=(Job("j", "Renamed"), JOBS.jobs[1])))
        with pytest.raises(ValueError, match="changed"):
            editor.save(view, ())
        view = editor.load("j")
        assert not editor.save(view, ()).selected
    finally:
        workspace.close(choice=CloseChoice.DISCARD)

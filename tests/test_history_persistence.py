"""Historical ownership round trips, atomic creation and referenced-row guards.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
from contextlib import closing
from dataclasses import replace
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from ergotools.application.assessments.lifft_commands import AddLifftTask
from ergotools.application.assessments.project_edits import LifftProjectEdit
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.job_classification import (
    ClassificationRequest,
    classify_assignments,
)
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.session import DocumentKey
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    assessment_kind,
)
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst_draft import TstDraft
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
from ergotools.infrastructure.settings_store import JsonSettingsStore

# Explicit synthetic project identity/title/default units; assessment units are
# preserved independently.
META = ProjectMetadata("p", "History", MeasurementSystem.IMPERIAL)
# Exact synthetic station ancestry; repeated station captions on other branches remain
# distinct.
STATION = StationKey("P", "S", "L", "1")
# Immutable synthetic complete hierarchy, including the empty branches/shifts needed by
# these tests.
HIERARCHY = WorkHierarchy(
    WorkCatalog("p", (WorkerEntry("w"), WorkerEntry("x")), (STATION,), ("Day",)),
    ("P",),
    (SectionKey("P", "S"),),
    (LineKey("P", "S", "L"),),
)
# Exact project/worker/workplace/shift ownership used to distinguish historical
# assignment links.
OWNER = HIERARCHY.work.worker_context("w", STATION.at_shift("Day"))
# Immutable synthetic jobs, placements and assignment history with exact retained links.
JOBS = JobCatalog(
    "p",
    (Job("j", "Job"), Job("k", "Other")),
    (JobPlacement(1, "j", OWNER.workplace), JobPlacement(2, "k", OWNER.workplace)),
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


def seed(path: Path) -> None:
    """Create only a synthetic version-six database.

    Args:
        path: Disposable test file path; the caller controls creation and cleanup.

    Returns:
        None.
    """
    with AssessmentProjectFile.create_historical(path, META) as project:
        project.save_hierarchy(HIERARCHY)
        project.save_jobs(JOBS)
        project.create_historical_assessment(ENTRY, SOURCE)


def test_reassignment_roundtrip_retains_separate_current_assessments(
    tmp_path: Path,
) -> None:
    """Closed and successor assignments retain independent current sources.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "history.sqlite"
    seed(path)
    changed = classify_assignments(
        JOBS, "w", (ClassificationRequest(1, 2, 2),), effective_date=date(2026, 10, 1)
    )
    with AssessmentProjectFile.open(path) as project:
        project.replace_jobs(JOBS, changed)
        project.create_historical_assessment(
            replace(ENTRY, document_id="b", assignment_id=2), SOURCE
        )
    with AssessmentProjectFile.open(path) as project:
        assert project.format_version == 6
        history = project.load_history()
        assert history.current_for(1, AssessmentKind.LIFFT) == ENTRY
        assert history.current_for(2, AssessmentKind.LIFFT).document_id == "b"
        assert project.load(DocumentKey("p", "a")) == SOURCE
        project.save_jobs(
            replace(changed, jobs=(Job("j", "Renamed"), Job("k", "Other")))
        )


def test_referenced_assignment_and_placement_identity_guards(tmp_path: Path) -> None:
    """Removal or repurposing fails while the saved history remains readable.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "history.sqlite"
    seed(path)
    with AssessmentProjectFile.open(path) as project:
        for changed in (
            replace(JOBS, assignments=()),
            replace(
                JOBS,
                assignments=(
                    replace(JOBS.assignments[0], worker=replace(OWNER, worker_id="x")),
                ),
            ),
            replace(JOBS, assignments=(replace(JOBS.assignments[0], placement_id=2),)),
            replace(JOBS, placements=(replace(JOBS.placements[0], job_id="k"),)),
        ):
            with pytest.raises(ValueError):
                project.save_jobs(changed)
            assert project.load_jobs() == JOBS
            assert project.load_history().entries == (ENTRY,)


def test_conflicting_or_invalid_creation_rolls_back_source(tmp_path: Path) -> None:
    """Missing owners/current conflicts/model mismatch never leave an orphan draft.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "history.sqlite"
    seed(path)
    with AssessmentProjectFile.open(path) as project:
        for entry, source in (
            (replace(ENTRY, document_id="b", assignment_id=99), SOURCE),
            (replace(ENTRY, document_id="b"), SOURCE),
            (replace(ENTRY, document_id="b"), SOURCE),
            (replace(ENTRY, document_id="b"), DuetDraft()),
        ):
            with pytest.raises(ValueError):
                project.create_historical_assessment(entry, source)
            with pytest.raises(KeyError):
                project.load(DocumentKey("p", "b"))
        assert project.load_history().entries == (ENTRY,)


def test_sql_failure_rolls_back_both_records_and_allows_retry(tmp_path: Path) -> None:
    """A database failure after source insertion rolls the source back too.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "history.sqlite"
    seed(path)
    with AssessmentProjectFile.open(path) as repository:
        jobs = repository.load_jobs()
        repository.save_jobs(
            replace(
                jobs,
                assignments=(
                    *jobs.assignments,
                    WorkerJobAssignment(2, OWNER, 2, active=False),
                ),
            )
        )
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(
            "CREATE TRIGGER fail BEFORE INSERT ON assessment_ownership "
            "BEGIN SELECT RAISE(ABORT,'injected'); END"
        )
    entry = replace(ENTRY, document_id="b", assignment_id=2)
    with AssessmentProjectFile.open(path) as project:
        with pytest.raises(sqlite3.IntegrityError):
            project.create_historical_assessment(entry, SOURCE)
        with pytest.raises(KeyError):
            project.load(DocumentKey("p", "b"))
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute("DROP TRIGGER fail")
        project.create_historical_assessment(entry, SOURCE)
        assert project.load_history().entries == (ENTRY, entry)


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM draft_documents",
        "DELETE FROM worker_assignments",
        "UPDATE assessment_ownership SET kind='duet'",
        "UPDATE assessment_ownership SET assignment_id=999",
    ],
)
def test_corrupted_links_reject_open_without_modifying_file(
    tmp_path: Path, sql: str
) -> None:
    """Damaged source, model, assignment or flags fail explicitly.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        sql: Explicit test-only SQL statement used for controlled schema/trigger
            corruption.

    Returns:
        None.
    """
    path = tmp_path / "history.sqlite"
    seed(path)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute(sql)
    before = path.read_bytes()
    with pytest.raises(ValueError):
        AssessmentProjectFile.open(path)
    assert path.read_bytes() == before


def test_old_format_and_closed_history_handles_fail_explicitly(tmp_path: Path) -> None:
    """Opt-in storage does not upgrade old files or reuse closed connections.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "history.sqlite"
    with (
        AssessmentProjectFile.create_with_jobs(path, META) as project,
        pytest.raises(StoreFormatError),
    ):
        project.load_history()
    with pytest.raises(RuntimeError):
        project.load_history()


def test_initial_classification_allowed_and_context_binding_disabled(
    tmp_path: Path,
) -> None:
    """Unclassified history can gain its first job without dual ownership models.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    from ergotools.application.assessment_binding import AssessmentBinding
    from ergotools.domain.assessments.context import AssessmentContext

    path = tmp_path / "history.sqlite"
    unclassified = replace(
        JOBS, assignments=(replace(JOBS.assignments[0], placement_id=None),)
    )
    with AssessmentProjectFile.create_historical(path, META) as project:
        project.save_hierarchy(HIERARCHY)
        project.save_jobs(unclassified)
        project.create_historical_assessment(ENTRY, SOURCE)
        classified = classify_assignments(
            unclassified,
            "w",
            (ClassificationRequest(1, 1),),
            effective_date=date(2026, 10, 1),
        )
        project.replace_jobs(unclassified, classified)
        assert project.load_history().entries == (ENTRY,)
        with pytest.raises(StoreFormatError, match="assignment ownership"):
            project.bind_assessment(
                AssessmentBinding(
                    DocumentKey("p", "a"),
                    AssessmentContext(OWNER, AssessmentKind.LIFFT),
                )
            )


def test_single_ownership_schema_has_no_unused_context_binding_table(
    tmp_path: Path,
) -> None:
    """Keep only the ownership table used by assignment/tool assessment functionality.

    Args:
        tmp_path: Test-owned temporary directory for a synthetic saved project.

    Returns:
        None; source inputs and ownership remain, without the unused binding table.
    """
    path = tmp_path / "history.sqlite"
    seed(path)
    with closing(sqlite3.connect(path)) as connection:
        tables = {
            r[0]
            for r in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert "assessment_ownership" in tables and "assessment_bindings" not in tables
    with AssessmentProjectFile.open(path) as project:
        assert project.load_history().entries == (ENTRY,)
        assert project.load(DocumentKey("p", "a")) == SOURCE


def test_workspace_historical_selection_preserves_dirty_decisions(
    tmp_path: Path,
) -> None:
    """Save/discard/cancel select exact assignments, including closed history.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    from unittest.mock import patch

    from ergotools.application.assessments.lifft_commands import AddLifftTask
    from ergotools.application.assessments.project_edits import LifftProjectEdit
    from ergotools.application.document_lifecycle import CloseChoice
    from ergotools.application.history_access import AssignmentSelection
    from ergotools.application.project_workspace import ProjectWorkspace
    from ergotools.domain.assessments.lifft_draft import LifftTask
    from ergotools.infrastructure.settings_store import JsonSettingsStore

    path = tmp_path / "history.sqlite"
    seed(path)
    changed = classify_assignments(
        JOBS, "w", (ClassificationRequest(1, 2, 2),), effective_date=date(2026, 10, 1)
    )
    with AssessmentProjectFile.open(path) as project:
        project.replace_jobs(JOBS, changed)
        project.create_historical_assessment(
            replace(ENTRY, document_id="b", assignment_id=2), SOURCE
        )
    workspace = ProjectWorkspace(
        lambda location: AssessmentProjectFile.open(Path(location)),
        JsonSettingsStore(tmp_path / "settings.json"),
    )
    target = AssignmentSelection("p", 2, AssessmentKind.LIFFT)
    try:
        workspace.switch(str(path), "a")
        old = workspace.active
        old.execute(
            LifftProjectEdit(AddLifftTask(old.document, LifftTask("t", 12, 10, 100), 0))
        )
        with patch.object(
            AssessmentProjectFile,
            "load_history",
            side_effect=AssertionError("unexpected IO"),
        ):
            assert not workspace.select_assignment(target).completed
            assert not workspace.select_assignment(
                target, choice=CloseChoice.CANCEL
            ).completed
        same = AssignmentSelection("p", 1, AssessmentKind.LIFFT)
        assert workspace.select_assignment(same, choice=CloseChoice.DISCARD).completed
        assert workspace.active is old and old.is_dirty
        with (
            patch.object(AssessmentProjectFile, "load", side_effect=OSError("load")),
            pytest.raises(OSError),
        ):
            workspace.select_assignment(target, choice=CloseChoice.SAVE)
        assert workspace.active is old and old.is_dirty
        with (
            patch.object(AssessmentProjectFile, "save", side_effect=OSError("save")),
            pytest.raises(OSError),
        ):
            workspace.select_assignment(target, choice=CloseChoice.SAVE)
        assert workspace.active is old and old.is_dirty
        assert workspace.select_assignment(target, choice=CloseChoice.SAVE).completed
        assert not old.is_dirty and workspace.active.document.document_id == "b"
        assert workspace.select_assignment(same).completed
        assert workspace.active.state == old.state
        with pytest.raises(KeyError):
            workspace.select_assignment(replace(target, assignment_id=99))
        with pytest.raises(ValueError):
            workspace.select_assignment(replace(target, project_id="other"))
        with (
            patch.object(
                AssessmentProjectFile,
                "load_history",
                side_effect=lambda: workspace.save(),
            ),
            pytest.raises(RuntimeError, match="already in progress"),
        ):
            workspace.select_assignment(target)
        assert workspace.active.document.document_id == "a"
    finally:
        workspace.close(choice=CloseChoice.DISCARD)
    with pytest.raises(RuntimeError, match="No project"):
        workspace.select_assignment(target)


def test_workspace_history_rejects_bad_adapters_and_changed_source(
    tmp_path: Path,
) -> None:
    """Foreign history and reentrant source edits cannot activate a candidate.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    from unittest.mock import patch

    from ergotools.application.assessments.lifft_commands import AddLifftTask
    from ergotools.application.assessments.project_edits import LifftProjectEdit
    from ergotools.application.document_lifecycle import CloseChoice
    from ergotools.application.history_access import AssignmentSelection
    from ergotools.application.project_workspace import ProjectWorkspace
    from ergotools.domain.assessment_history import AssessmentHistory
    from ergotools.domain.assessments.lifft_draft import LifftTask
    from ergotools.infrastructure.project_file import ProjectFile
    from ergotools.infrastructure.settings_store import JsonSettingsStore

    path = tmp_path / "history.sqlite"
    seed(path)
    workspace = ProjectWorkspace(
        lambda location: AssessmentProjectFile.open(Path(location)),
        JsonSettingsStore(tmp_path / "settings.json"),
    )
    target = AssignmentSelection("p", 1, AssessmentKind.LIFFT)
    try:
        workspace.switch(str(path), "a")
        with (
            patch.object(
                AssessmentProjectFile,
                "load_history",
                return_value=AssessmentHistory("other"),
            ),
            pytest.raises(ValueError, match="foreign"),
        ):
            workspace.select_assignment(target)
        current = workspace.active

        def edited_history() -> AssessmentHistory:
            """Edit the active source while the fake adapter returns saved history.

            Edit the active source while the fake adapter returns saved history,
            exercising changed-source activation rejection.

            Args:
                None.

            Returns:
                Saved history after deliberately editing the active source; must not be
                accepted as unchanged activation consent.
            """
            current.execute(
                LifftProjectEdit(
                    AddLifftTask(current.document, LifftTask("t", 12, 10, 100), 0)
                )
            )
            return AssessmentHistory("p", (ENTRY,))

        with (
            patch.object(
                AssessmentProjectFile, "load_history", side_effect=edited_history
            ),
            pytest.raises(RuntimeError, match="draft changed"),
        ):
            workspace.select_assignment(target)
        assert workspace.active is current and current.is_dirty
    finally:
        workspace.close(choice=CloseChoice.DISCARD)
    old_path = tmp_path / "old.sqlite"
    with ProjectFile.create_with_document(old_path, META, "a", SOURCE):
        pass
    legacy = ProjectWorkspace(
        lambda location: ProjectFile.open(Path(location)),
        JsonSettingsStore(tmp_path / "old-settings.json"),
    )
    try:
        legacy.switch(str(old_path), "a")
        with pytest.raises(RuntimeError, match="adapter"):
            legacy.select_assignment(target)
    finally:
        legacy.close()
    for identity, kind in ((True, AssessmentKind.LIFFT), (1, "lifft")):
        with pytest.raises(ValueError):
            AssignmentSelection("p", identity, kind)


def test_workspace_creation_preflight_precedes_old_save(tmp_path: Path) -> None:
    """Invalid owners/models/versions leave the old source dirty and unsaved.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    from unittest.mock import patch

    from ergotools.application.assessments.lifft_commands import AddLifftTask
    from ergotools.application.assessments.project_edits import LifftProjectEdit
    from ergotools.application.document_lifecycle import CloseChoice
    from ergotools.application.project_workspace import ProjectWorkspace
    from ergotools.domain.assessments.lifft_draft import LifftTask
    from ergotools.infrastructure.settings_store import JsonSettingsStore

    path = tmp_path / "history.sqlite"
    seed(path)
    with AssessmentProjectFile.open(path) as repository:
        jobs = repository.load_jobs()
        repository.save_jobs(
            replace(
                jobs,
                assignments=(
                    *jobs.assignments,
                    WorkerJobAssignment(2, OWNER, 2, active=False),
                ),
            )
        )
    workspace = ProjectWorkspace(
        lambda location: AssessmentProjectFile.open(Path(location)),
        JsonSettingsStore(tmp_path / "settings.json"),
    )
    entry = replace(ENTRY, document_id="b", assignment_id=2)
    try:
        workspace.switch(str(path), "a")
        old = workspace.active
        old.execute(
            LifftProjectEdit(AddLifftTask(old.document, LifftTask("t", 12, 10, 100), 0))
        )
        with patch.object(
            AssessmentProjectFile,
            "validate_historical_creation",
            side_effect=AssertionError("unexpected IO"),
        ):
            assert not workspace.create_assignment_assessment(entry, SOURCE).completed
            assert not workspace.create_assignment_assessment(
                entry, SOURCE, choice=CloseChoice.CANCEL
            ).completed
        for invalid, source in (
            (replace(entry, assignment_id=99), SOURCE),
            (replace(entry, assignment_id=1), SOURCE),
            (replace(entry, document_id="a"), SOURCE),
            (entry, DuetDraft()),
        ):
            with pytest.raises(ValueError):
                workspace.create_assignment_assessment(
                    invalid, source, choice=CloseChoice.SAVE
                )
            assert workspace.active is old and old.is_dirty
        with AssessmentProjectFile.open(path) as project:
            assert project.load(DocumentKey("p", "a")) == SOURCE
        assert workspace.create_assignment_assessment(
            entry, SOURCE, choice=CloseChoice.SAVE
        ).completed
        assert not old.is_dirty
        assert workspace.active.document.document_id == "b"
        assert not workspace.active.is_dirty
        with AssessmentProjectFile.open(path) as project:
            assert project.load_history().entries == (ENTRY, entry)
            assert project.load(DocumentKey("p", "a")) == old.state
    finally:
        workspace.close(choice=CloseChoice.DISCARD)
    with pytest.raises(RuntimeError, match="No project"):
        workspace.create_assignment_assessment(entry, SOURCE)


def test_workspace_creation_failures_preserve_active_session(tmp_path: Path) -> None:
    """Late failure may leave the separately saved old draft clean, never replaced.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    from unittest.mock import patch

    from ergotools.application.assessments.lifft_commands import AddLifftTask
    from ergotools.application.assessments.project_edits import LifftProjectEdit
    from ergotools.application.document_lifecycle import CloseChoice
    from ergotools.application.project_workspace import ProjectWorkspace
    from ergotools.domain.assessments.lifft_draft import LifftTask
    from ergotools.infrastructure.settings_store import JsonSettingsStore

    path = tmp_path / "history.sqlite"
    seed(path)
    with AssessmentProjectFile.open(path) as repository:
        jobs = repository.load_jobs()
        repository.save_jobs(
            replace(
                jobs,
                assignments=(
                    *jobs.assignments,
                    WorkerJobAssignment(2, OWNER, 2, active=False),
                ),
            )
        )
    workspace = ProjectWorkspace(
        lambda location: AssessmentProjectFile.open(Path(location)),
        JsonSettingsStore(tmp_path / "settings.json"),
    )
    entry = replace(ENTRY, document_id="b", assignment_id=2)
    try:
        workspace.switch(str(path), "a")
        old = workspace.active
        command = LifftProjectEdit(
            AddLifftTask(old.document, LifftTask("t", 12, 10, 100), 0)
        )
        with (
            patch.object(
                AssessmentProjectFile,
                "validate_historical_creation",
                side_effect=lambda *_: old.execute(command),
            ),
            pytest.raises(RuntimeError, match="draft changed"),
        ):
            workspace.create_assignment_assessment(entry, SOURCE)
        assert workspace.active is old and old.is_dirty
        with (
            patch.object(
                AssessmentProjectFile,
                "validate_historical_creation",
                side_effect=lambda *_: workspace.save(),
            ),
            pytest.raises(RuntimeError, match="already in progress"),
        ):
            workspace.create_assignment_assessment(
                entry, SOURCE, choice=CloseChoice.SAVE
            )
        with (
            patch.object(AssessmentProjectFile, "save", side_effect=OSError("save")),
            pytest.raises(OSError),
        ):
            workspace.create_assignment_assessment(
                entry, SOURCE, choice=CloseChoice.SAVE
            )
        assert old.is_dirty
        with (
            patch.object(
                AssessmentProjectFile,
                "create_historical_assessment",
                side_effect=OSError("insert"),
            ),
            pytest.raises(OSError),
        ):
            workspace.create_assignment_assessment(
                entry, SOURCE, choice=CloseChoice.SAVE
            )
        assert workspace.active is old and not old.is_dirty
        with AssessmentProjectFile.open(path) as project:
            assert project.load_history().entries == (ENTRY,)
        assert workspace.create_assignment_assessment(entry, SOURCE).completed
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_preflight_duplicate_unbound_source_and_unsupported_adapter(
    tmp_path: Path,
) -> None:
    """Existing unbound IDs are protected; legacy adapters do not gain new APIs.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    from ergotools.application.project_workspace import ProjectWorkspace
    from ergotools.infrastructure.project_file import ProjectFile
    from ergotools.infrastructure.settings_store import JsonSettingsStore

    path = tmp_path / "history.sqlite"
    seed(path)
    with AssessmentProjectFile.open(path) as project:
        project.insert_assessment(DocumentKey("p", "unbound"), SOURCE)
        with pytest.raises(ValueError, match="document"):
            project.validate_historical_creation(
                replace(ENTRY, document_id="unbound"),
                SOURCE,
            )
    legacy_path = tmp_path / "old.sqlite"
    with ProjectFile.create_with_document(legacy_path, META, "a", SOURCE):
        pass
    workspace = ProjectWorkspace(
        lambda location: ProjectFile.open(Path(location)),
        JsonSettingsStore(tmp_path / "settings.json"),
    )
    try:
        workspace.switch(str(legacy_path), "a")
        with pytest.raises(RuntimeError, match="adapter"):
            workspace.create_assignment_assessment(ENTRY, SOURCE)
    finally:
        workspace.close()


@pytest.mark.parametrize("default_units", tuple(MeasurementSystem))
@pytest.mark.parametrize(
    "source",
    (
        LifftDraft(MeasurementSystem.IMPERIAL, (LifftTask("t", 12, 10, 100),)),
        LifftDraft(MeasurementSystem.METRIC, (LifftTask("t", 30, 5, 100),)),
        DuetDraft(),
        TstDraft(MeasurementSystem.IMPERIAL),
        TstDraft(MeasurementSystem.METRIC),
    ),
)
def test_initialized_project_preserves_units_and_ownership(
    tmp_path: Path, default_units: MeasurementSystem, source: AssessmentDraft
) -> None:
    """Defaults never convert the first source or invent assignment ownership.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        default_units: Declared original project system used by the owner-approved
            body-unit normalization policy.
        source: Immutable draft or disposable source path supplied by the stated
            storage/publication scenario.

    Returns:
        None.
    """
    metadata = replace(META, default_units=default_units)
    entry = replace(ENTRY, kind=assessment_kind(source))
    path = tmp_path / "initialized.sqlite"
    with AssessmentProjectFile.create_initialized_historical(
        path, metadata, HIERARCHY, JOBS, entry, source
    ) as project:
        assert project.format_version == 6
        assert project.load_history().entries == (entry,)
    with AssessmentProjectFile.open(path) as project:
        assert project.metadata == metadata
        assert project.load_hierarchy() == HIERARCHY
        assert project.load_jobs() == JOBS
        assert project.load(DocumentKey("p", "a")) == source


@pytest.mark.parametrize(
    "stage", ("save_hierarchy", "save_jobs", "create_historical_assessment")
)
def test_initialized_project_removes_partial_file(tmp_path: Path, stage: str) -> None:
    """A failure at each setup stage closes and removes the new database.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        stage: Named write/setup stage where this test injects a failure.

    Returns:
        None.
    """
    path = tmp_path / "incomplete.sqlite"
    with (
        patch.object(AssessmentProjectFile, stage, side_effect=OSError("setup failed")),
        pytest.raises(OSError, match="setup failed"),
    ):
        AssessmentProjectFile.create_initialized_historical(
            path, META, HIERARCHY, JOBS, ENTRY, SOURCE
        )
    assert not path.exists()
    # A retry at exactly the same destination must succeed.
    with AssessmentProjectFile.create_initialized_historical(
        path, META, HIERARCHY, JOBS, ENTRY, SOURCE
    ) as project:
        assert project.load_history().entries == (ENTRY,)


def test_initialized_project_rejects_invalid_setup_before_creation(
    tmp_path: Path,
) -> None:
    """Foreign ownership, missing assignments and model mismatch create no file.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "invalid.sqlite"
    candidates = (
        (replace(META, project_id="foreign"), HIERARCHY, JOBS, ENTRY, SOURCE),
        (META, HIERARCHY, replace(JOBS, assignments=()), ENTRY, SOURCE),
        (META, HIERARCHY, JOBS, ENTRY, DuetDraft()),
        (
            META,
            replace(HIERARCHY, work=replace(HIERARCHY.work, workers=())),
            JOBS,
            ENTRY,
            SOURCE,
        ),
    )
    for metadata, hierarchy, jobs, entry, source in candidates:
        with pytest.raises((ValueError, KeyError)):
            AssessmentProjectFile.create_initialized_historical(
                path, metadata, hierarchy, jobs, entry, source
            )
        assert not path.exists()


def test_initialized_project_never_removes_existing_destination(tmp_path: Path) -> None:
    """An unrelated existing file is byte-for-byte intact after refused creation.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "existing.sqlite"
    content = b"existing user data"
    path.write_bytes(content)
    with pytest.raises(FileExistsError):
        AssessmentProjectFile.create_initialized_historical(
            path, META, HIERARCHY, JOBS, ENTRY, SOURCE
        )
    assert path.read_bytes() == content


def test_initialized_project_workspace_creation_and_cancel(tmp_path: Path) -> None:
    """The existing coordinator adopts setup and preserves dirty edits on cancel.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """

    def create(
        location: str,
        metadata: ProjectMetadata,
        document_id: str,
        source: AssessmentDraft,
    ) -> AssessmentProjectFile:
        """Initialize one exact historical assignment/source.

        Initialize one exact historical assignment/source using the injected document ID
        and actual typed source kind.

        Args:
            location: Disposable project location provided to the injected
                adapter/factory.
            metadata: Explicit synthetic project metadata; defaults never reinterpret
                source input units.
            document_id: Stable assessment identity supplied to the test project
                initializer.
            source: Immutable draft or disposable source path supplied by the stated
                storage/publication scenario.

        Returns:
            New owned native project initialized with the exact historical owner and
            supplied typed source; caller closes it.
        """
        return AssessmentProjectFile.create_initialized_historical(
            Path(location),
            metadata,
            HIERARCHY,
            JOBS,
            replace(ENTRY, document_id=document_id, kind=assessment_kind(source)),
            source,
        )

    settings = JsonSettingsStore(tmp_path / "settings.json")
    workspace: ProjectWorkspace[AssessmentDraft] = ProjectWorkspace(
        lambda location: AssessmentProjectFile.open(Path(location)),
        settings,
        creator=create,
    )
    path = tmp_path / "workspace.sqlite"
    cancelled = tmp_path / "cancelled.sqlite"
    try:
        assert workspace.create(str(path), META, "a", SOURCE).completed
        active = workspace.active
        assert active is not None and not active.is_dirty
        assert workspace.supports_assignment_history
        assert workspace.read_jobs().jobs == JOBS
        assert workspace.read_history().history.entries == (ENTRY,)
        active.execute(
            LifftProjectEdit(
                AddLifftTask(active.document, LifftTask("task", 12, 10, 100), 0)
            )
        )
        assert not workspace.create(
            str(cancelled), META, "b", SOURCE, choice=CloseChoice.CANCEL
        ).completed
        assert workspace.active is active and active.is_dirty
        assert not cancelled.exists()
        workspace.save()
    finally:
        workspace.close(choice=CloseChoice.DISCARD)
    with AssessmentProjectFile.open(path) as project:
        assert len(project.load(DocumentKey("p", "a")).tasks) == 1
        assert project.load_history().entries == (ENTRY,)

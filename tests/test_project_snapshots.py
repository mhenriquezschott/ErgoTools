"""Whole-project snapshots, original protection and integrated copy workflows.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import os
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_history_persistence import META
from tests.test_saved_tool_data import window as window


@pytest.mark.parametrize("index", [0, 1, 2])
def test_save_as_copies_all_data_and_only_changes_selected_source(
    window: LifftWindow, tmp_path: Path, index: int
) -> None:
    """Menu Save As includes accepted input in the copy, never the original.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        index: Zero-based selected input/row/case index used by the parametrized
            regression.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(index)
    workspace = window.presenter.workspace
    original = Path(workspace.location)
    active = workspace.active
    with AssessmentProjectFile.open(original) as project:
        entries = project.list_assessments()
        sources = {entry.document: project.load(entry.document) for entry in entries}
        hierarchy, jobs, history, risk = (
            project.load_hierarchy(),
            project.load_jobs(),
            project.load_history(),
            project.load_job_risk(),
        )
    field = (window.task_panel if index == 0 else window.secondary_panel()).inputs[0][
        2 if index == 0 else -1
    ]
    field.setText("350")
    field.textEdited.emit("350")
    destination = tmp_path / "copy.ergprj"
    with (
        patch.object(window, "choose_file", return_value=str(destination)),
        patch.object(window, "choose_project_details", return_value=(META.title, "")),
    ):
        window._assessment_menu.save_as.trigger()
    assert workspace.location == str(destination)
    assert workspace.active is not active and not workspace.active.is_dirty
    assert workspace.active.state.tasks[0].repetitions == 350
    assert window._settings_store.load().recent_documents[0] == str(destination)
    with AssessmentProjectFile.open(original) as project:
        assert all(project.load(key) == source for key, source in sources.items())
    with AssessmentProjectFile.open(destination) as project:
        assert project.metadata.project_id == META.project_id
        assert project.metadata.title == META.title
        assert project.metadata.default_units == META.default_units
        assert project.metadata.description == ""
        assert project.metadata.created_at is not None
        assert project.load_hierarchy() == hierarchy
        assert project.load_jobs() == jobs
        assert project.load_history() == history
        assert project.load_job_risk() == risk
        assert project.list_assessments() == entries
        for key, source in sources.items():
            saved = project.load(key)
            assert saved == (
                workspace.active.state if key == active.document else source
            )
    assert not list(tmp_path.glob(".ergotools-snapshot-*"))


def test_picker_cancel_existing_destination_and_invalid_input(
    window: LifftWindow, tmp_path: Path
) -> None:
    """Cancelled/rejected locations retain pending text, source and current project.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = window.presenter.workspace
    active, location = workspace.active, workspace.location
    field = window.task_panel.inputs[0][2]
    field.setText("bad")
    field.textEdited.emit("bad")
    with patch.object(window, "choose_file", return_value=""):
        window._assessment_menu.save_as.trigger()
    assert field.text() == "bad" and workspace.active is active
    existing = tmp_path / "existing.ergprj"
    existing.write_bytes(b"keep")
    with patch.object(window, "choose_file", return_value=str(existing)):
        window._assessment_menu.save_as.trigger()
    assert existing.read_bytes() == b"keep" and field.text() == "bad"
    destination = tmp_path / "invalid.ergprj"
    with (
        patch.object(window, "choose_file", return_value=str(destination)),
        patch.object(window, "choose_project_details", return_value=(META.title, "")),
    ):
        window._assessment_menu.save_as.trigger()
    assert not destination.exists()
    assert workspace.active is active and workspace.location == location
    assert field.text() == "bad" and not active.is_dirty


def test_backup_preserves_pending_edits_history_and_preferences(
    window: LifftWindow, tmp_path: Path
) -> None:
    """Backup contains saved source data even while the editor has invalid text.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = window.presenter.workspace
    active, location = workspace.active, workspace.location
    active_state = active.state
    settings = window._settings_store.load()
    field = window.task_panel.inputs[0][2]
    field.setText("bad")
    field.textEdited.emit("bad")
    destination = tmp_path / "backup.ergprj"
    with (
        patch.object(window, "choose_file", return_value=str(destination)),
        patch.object(window, "choose_project_details", return_value=(META.title, "")),
    ):
        window._assessment_menu.backup.trigger()
    assert workspace.active is active and workspace.location == location
    assert active.state is active_state and field.text() == "bad"
    assert window._settings_store.load() == settings
    with AssessmentProjectFile.open(destination) as project:
        assert project.load(active.document) == active_state
    # A committed-but-unsaved valid edit is likewise excluded.
    field.setText("350")
    field.textEdited.emit("350")
    window.task_panel.commit_inputs()
    destination = tmp_path / "dirty-backup.ergprj"
    with (
        patch.object(window, "choose_file", return_value=str(destination)),
        patch.object(window, "choose_project_details", return_value=(META.title, "")),
    ):
        window._assessment_menu.backup.trigger()
    assert active.is_dirty and active.state.tasks[0].repetitions == 350
    with AssessmentProjectFile.open(destination) as project:
        assert project.load(active.document).tasks[0].repetitions == 100


@pytest.mark.parametrize("backup", [False, True])
def test_publication_failure_retains_current_and_removes_temporary(
    window: LifftWindow, tmp_path: Path, backup: bool
) -> None:
    """A filesystem failure neither changes ownership nor leaves an incomplete copy.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        backup: True tests saved-state Backup; False tests accepted-edit Save As
            publication.

    Returns:
        None.
    """
    workspace = window.presenter.workspace
    active, location = workspace.active, workspace.location
    destination = tmp_path / "failed.ergprj"
    with (
        patch(
            "ergotools.infrastructure.assessment_project_file.os.link",
            side_effect=OSError("publish failed"),
        ),
        pytest.raises(OSError),
    ):
        (workspace.backup if backup else workspace.save_as)(str(destination))
    assert workspace.active is active and workspace.location == location
    assert not destination.exists() and not list(tmp_path.glob(".ergotools-snapshot-*"))
    # Guard is released and retry succeeds.
    assert (workspace.backup if backup else workspace.save_as)(
        str(destination)
    ).completed


def test_snapshot_includes_committed_wal_and_rejects_existing_destination(
    tmp_path: Path,
) -> None:
    """SQLite backup reads committed WAL pages instead of just the main file.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    source = LifftDraft(META.default_units, (LifftTask("l", 12, 20, 100),))
    path = tmp_path / "wal.ergprj"
    with AssessmentProjectFile.create_with_document(path, META, "l", source) as project:
        project._connection.execute("PRAGMA journal_mode=WAL")
        project._connection.execute("PRAGMA wal_autocheckpoint=0")
        changed = replace(source, tasks=(replace(source.tasks[0], repetitions=350),))
        key = DocumentKey(META.project_id, "l")
        project.save(key, changed)
        assert Path(str(path) + "-wal").stat().st_size > 0
        destination = tmp_path / "snapshot.ergprj"
        with project.snapshot(str(destination), None, None) as copied:
            assert copied.load(key) == changed
        before = destination.read_bytes()
        with pytest.raises(FileExistsError):
            project.snapshot(str(destination), None, None)
        assert destination.read_bytes() == before
        with pytest.raises(ValueError):
            project.snapshot(str(tmp_path / "bad.ergprj"), key, None)


def test_publication_race_never_overwrites_new_destination(
    window: LifftWindow,
    tmp_path: Path,
) -> None:
    """Exclusive publication still rejects a file created after initial preflight.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    destination = tmp_path / "race.ergprj"
    original_link = os.link

    def competing_link(source: Path, target: Path) -> None:
        """Create competing destination bytes immediately.

        Create competing destination bytes immediately before the actual exclusive link
        to verify they cannot be overwritten.

        Args:
            source: Immutable draft or disposable source path supplied by the stated
                storage/publication scenario.
            target: Explicit disposable publication destination; racing-writer tests
                protect any pre-existing bytes.

        Returns:
            None.
        """
        destination.write_bytes(b"another file")
        original_link(source, target)

    with (
        patch(
            "ergotools.infrastructure.assessment_project_file.os.link",
            side_effect=competing_link,
        ),
        pytest.raises(FileExistsError),
    ):
        window.presenter.workspace.backup(str(destination))
    assert destination.read_bytes() == b"another file"
    assert not list(tmp_path.glob(".ergotools-snapshot-*"))


def test_copy_source_write_failure_leaves_original_and_destination_untouched(
    window: LifftWindow,
    tmp_path: Path,
) -> None:
    """Saving the draft into a temporary copy must succeed before publication.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = window.presenter.workspace
    active = workspace.active
    location = workspace.location
    panel = window.task_panel
    field = panel.inputs[0][2]
    field.setText("777")
    field.textEdited.emit("777")
    panel.commit_inputs()
    saved_source = active.state
    destination = tmp_path / "failed-write.ergprj"
    with (
        patch.object(
            AssessmentProjectFile, "save", side_effect=OSError("write failed")
        ),
        pytest.raises(OSError),
    ):
        workspace.save_as(str(destination))
    assert workspace.active is active and workspace.location == location
    assert not destination.exists() and not list(tmp_path.glob(".ergotools-snapshot-*"))
    with AssessmentProjectFile.open(Path(location)) as project:
        assert project.load(active.document) != saved_source


def test_save_as_recency_failure_is_warning_after_success(
    window: LifftWindow,
    tmp_path: Path,
) -> None:
    """A preferences failure must not misreport an already published active copy.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = window.presenter.workspace
    destination = tmp_path / "copy.ergprj"
    with patch.object(
        type(window._settings_store), "save", side_effect=OSError("settings")
    ):
        result = workspace.save_as(str(destination))
    assert result.completed and result.warning_keys == (
        "settings.recent_update_failed",
    )
    assert workspace.location == str(destination)
    assert destination.exists() and not workspace.active.is_dirty

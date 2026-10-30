"""M04 original lifecycle and owner-approved legacy body-unit corrections.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_legacy_catalogs import legacy_catalog as legacy_catalog
from tests.test_legacy_reconciliation import old_source as old_source
from tests.test_optional_assessment_context import start_standalone_worker
from tests.test_saved_tool_data import window as window
from tools.project_migration.ergotools_migration.legacy_conversion import (
    convert_legacy_project,
)
from tools.project_migration.ergotools_migration.legacy_project import (
    read_legacy_descriptor,
)


@pytest.mark.parametrize(
    "system", [MeasurementSystem.METRIC, MeasurementSystem.IMPERIAL]
)
def test_declared_legacy_worker_units_normalize_once_and_archive_raw_values(
    old_source: Path, tmp_path: Path, system: MeasurementSystem
) -> None:
    """Interpret untagged body numbers using the approved project-default policy.

    Args:
        old_source: Disposable original-format fixture containing unversioned LiFFT rows
            and exact saved ownership.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        system: Explicit metric/imperial display or source system exercised by this
            scenario.

    Returns:
        None.
    """
    text = old_source.read_text()
    text = text.replace(
        "<MeasurementSystem>Imperial</MeasurementSystem>",
        "<MeasurementSystem>" + system.value.title() + "</MeasurementSystem>",
    )
    old_source.write_text(text)
    descriptor = read_legacy_descriptor(old_source, "converted")
    with closing(sqlite3.connect(descriptor.database_path)) as connection, connection:
        connection.execute("UPDATE Worker SET height=72.5,weight=150 WHERE id='w'")
    original = descriptor.database_path.read_bytes()
    target = tmp_path / "body-converted.ergprj"
    expected = (
        (72.5, 150)
        if system is MeasurementSystem.METRIC
        else (72.5 * 2.54, 150 * 0.45359237)
    )
    with convert_legacy_project(old_source, target, "converted") as project:
        worker = next(
            w for w in project.load_hierarchy().work.workers if w.worker_id == "w"
        )
        assert (worker.details.height_cm, worker.details.weight_kg) == expected
        with closing(sqlite3.connect(descriptor.database_path)) as connection:
            assert connection.execute(
                "SELECT height,weight FROM Worker WHERE id='w'"
            ).fetchone() == (72.5, 150)
    with AssessmentProjectFile.open(target) as project:
        worker = next(
            w for w in project.load_hierarchy().work.workers if w.worker_id == "w"
        )
        assert (worker.details.height_cm, worker.details.weight_kg) == expected
    assert descriptor.database_path.read_bytes() == original


def test_empty_project_open_management_copy_and_reopen_without_invented_sources(
    window: LifftWindow, tmp_path: Path
) -> None:
    """An empty project's real catalogs remain usable without a dummy assessment.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    target = tmp_path / "empty.ergprj"
    metadata = ProjectMetadata("empty", "Empty project", MeasurementSystem.METRIC)
    with AssessmentProjectFile.create_with_job_risks(target, metadata):
        pass
    before = target.read_bytes()
    window.open_project_location(str(target))
    workspace = window.presenter.workspace
    assert workspace.active is None and workspace.project_metadata == metadata
    assert window.main_navigation.buttons["workers"].isEnabled()
    assert window.main_navigation.toolbar_actions["organization"].isEnabled()
    assert window.main_navigation.toolbar_actions["jobs"].isEnabled()
    assert window._assessment_menu.properties.isEnabled()
    assert target.read_bytes() == before
    backup, copied = tmp_path / "backup.ergprj", tmp_path / "copied.ergprj"
    assert workspace.backup(str(backup)).completed
    assert workspace.save_as(str(copied)).completed
    assert workspace.close().completed
    window.refresh()
    window.open_project_location(str(backup))
    assert workspace.active is None and workspace.project_metadata == metadata
    for path in (target, backup, copied):
        with AssessmentProjectFile.open(path) as project:
            assert project.list_assessments() == () and project.metadata == metadata


def test_empty_open_cancel_and_nonempty_without_selection_retain_owner(
    window: LifftWindow, tmp_path: Path
) -> None:
    """Empty-target adoption honors dirty Cancel; nonempty targets require selection.

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
    window.presenter.commit(
        window.presenter.bind(), active.state.tasks[0].task_id, "load", "99"
    )
    target = tmp_path / "empty.ergprj"
    with AssessmentProjectFile.create_with_job_risks(
        target, workspace.project_metadata
    ):
        pass
    with patch.object(window, "dirty_choice", return_value=CloseChoice.CANCEL):
        window.open_project_location(str(target))
    assert workspace.active is active and active.is_dirty
    with pytest.raises(ValueError, match="Select an assessment"):
        workspace.switch(workspace.location, None, choice=CloseChoice.DISCARD)
    assert workspace.active is active


def test_first_save_failure_cancel_retry_and_temporary_cleanup(
    window: LifftWindow, tmp_path: Path
) -> None:
    """Failed or cancelled first publication preserves work; retry adopts clean copy.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    with patch.object(window, "choose_file") as chooser:
        window.new_project()
    chooser.assert_not_called()
    start_standalone_worker(window)
    workspace = window.presenter.workspace
    owner = workspace.active
    temporary = Path(workspace.location)
    assert temporary.is_file()
    assert str(temporary) not in window._settings_store.load().recent_documents
    assert not window.main_navigation.toolbar_actions["jobs"].isEnabled()
    assert not window._assessment_menu.backup.isEnabled()
    field = window.task_panel.inputs[0][1]
    field.setText("20")
    field.textEdited.emit("20")
    target = tmp_path / "first.ergprj"
    with (
        patch.object(window, "choose_file", return_value=str(target)),
        patch.object(
            window, "choose_project_details", return_value=("First", "literal")
        ),
        patch.object(workspace, "save_as", side_effect=OSError("injected failure")),
        pytest.raises(OSError),
    ):
        window.save_project()
    assert (
        workspace.active is owner
        and workspace.has_unsaved_changes
        and temporary.exists()
    )
    assert field.text() == "20" and not target.exists()
    with patch.object(window, "choose_file", return_value=""):
        window.save_project()
    assert workspace.active is owner and temporary.exists()
    with (
        patch.object(window, "choose_file", return_value=str(target)),
        patch.object(
            window, "choose_project_details", return_value=("First", "literal")
        ),
    ):
        window.save_project()
    assert workspace.location == str(target) and not workspace.active.is_dirty
    assert not temporary.parent.exists() and window._unsaved_backing is None
    assert window.main_navigation.toolbar_actions["jobs"].isEnabled()
    assert str(temporary) not in window._settings_store.load().recent_documents
    with AssessmentProjectFile.open(target) as project:
        assert project.metadata.title == "First"
        assert project.load(workspace.active.document).tasks[0].load == 20


@pytest.mark.parametrize("accept_destination", [False, True])
def test_unsaved_dirty_save_consent_respects_first_save_cancellation(
    window: LifftWindow, tmp_path: Path, accept_destination: bool
) -> None:
    """First Save must succeed before a dirty-project transition can continue.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        accept_destination: True accepts explicit publication destination; False cancels
            without writing.

    Returns:
        None.
    """
    window.new_project()
    start_standalone_worker(window)
    workspace = window.presenter.workspace
    window.presenter.commit(
        window.presenter.bind(), workspace.active.state.tasks[0].task_id, "load", "20"
    )
    temporary = Path(workspace.location)
    target = tmp_path / "consented.ergprj"
    clicked = []

    def choose_save() -> None:
        """Click the actual Save dirty-consent button.

        Click the actual Save dirty-consent button and record that the native modal was
        entered.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, QMessageBox)
        next(b for b in dialog.buttons() if b.text() == window.text("save")).click()
        clicked.append(True)

    with (
        patch.object(
            window,
            "choose_file",
            return_value=str(target) if accept_destination else "",
        ),
        patch.object(window, "choose_project_details", return_value=("Saved", "")),
    ):
        QTimer.singleShot(0, choose_save)
        result = window.dirty_choice()
    assert clicked == [True]
    assert result is (CloseChoice.DISCARD if accept_destination else CloseChoice.CANCEL)
    assert target.exists() is accept_destination
    assert temporary.exists() is not accept_destination

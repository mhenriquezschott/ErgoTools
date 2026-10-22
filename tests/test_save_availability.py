"""Main Save projects existing private dirty state without accepting or writing edits.

Temporary native projects exercise all tools, both languages, pending validation,
shared replay, first Save and worker mutations. Owner/reference projects stay untouched.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtWidgets import QApplication

from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_saved_tool_data import window as window
from tests.test_task_input_history import reopen_grid


def assert_save(window: LifftWindow, enabled: bool) -> None:
    """Check the visible toolbar, menu and underlying Save command together.

    Args:
        window: Borrowed main window with integrated controls.
        enabled: Expected availability after the current operation.

    Returns:
        None; every Save entry must agree without invoking refresh in the test.
    """
    assert window.buttons["save"].isEnabled() is enabled
    assert window.main_navigation.toolbar_actions["save"].isEnabled() is enabled
    assert window._assessment_menu.actions_by_key["save"].isEnabled() is enabled


@pytest.mark.parametrize("index", range(3))
@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("system", list(MeasurementSystem))
def test_save_pending_accept_replay_publish(
    window: LifftWindow,
    tmp_path: Path,
    index: int,
    language: Language,
    system: MeasurementSystem,
) -> None:
    """Save follows pending fields, accepted edits, replay and durable publication.

    Args:
        window: Integrated real window with borrowed shared history.
        tmp_path: Disposable native project directory.
        index: LiFFT, DUET or ST tab index.
        language: English or Spanish captions.
        system: Metric or imperial source/display units.

    Returns:
        None; source projection never writes, Save keeps history and replay updates
        availability at both the original and newly saved baseline.
    """
    reopen_grid(window, tmp_path, index, system, language)
    assert_save(window, False)
    panel = window.secondary_panel() or window.task_panel
    field = panel.inputs[0][-1]
    original = field.text()
    path = Path(window.presenter.workspace.location)
    durable = path.read_bytes()
    field.setText("350")
    field.textEdited.emit("350")
    assert_save(window, True)
    assert path.read_bytes() == durable
    field.setText(original)
    field.textEdited.emit(original)
    assert_save(window, False)
    field.setText("350")
    field.textEdited.emit("350")
    field.editingFinished.emit()
    assert_save(window, True)
    undo = window.main_navigation.toolbar_actions["undo"]
    redo = window.main_navigation.toolbar_actions["redo"]
    window.setFocus()
    undo.trigger()
    assert_save(window, False)
    redo.trigger()
    assert_save(window, True)
    with patch.object(window.presenter.workspace, "save", return_value=False):
        window.main_navigation.toolbar_actions["save"].trigger()
    assert_save(window, True)
    assert path.read_bytes() == durable
    window.main_navigation.toolbar_actions["save"].trigger()
    assert_save(window, False)
    assert path.read_bytes() != durable
    undo.trigger()
    assert_save(window, True)
    redo.trigger()
    assert_save(window, False)
    window.refresh_navigation()
    window.enable_controls()
    assert_save(window, False)
    assert window._assessment_menu.save_as.isEnabled()
    window.calculate()
    assert_save(window, True)
    window.save_project()
    assert_save(window, False)


@pytest.mark.parametrize("index", range(3))
@pytest.mark.parametrize("language", list(Language))
def test_invalid_pending_save_remains_available_and_validates(
    window: LifftWindow, tmp_path: Path, index: int, language: Language
) -> None:
    """Invalid pending text can invoke existing Save validation without file changes.

    Args:
        window: Integrated main window with real validation.
        tmp_path: Disposable project directory.
        index: LiFFT, DUET or ST active tab.
        language: English or Spanish UI.

    Returns:
        None; validation retains text and correcting back to saved disables Save.
    """
    reopen_grid(window, tmp_path, index, MeasurementSystem.METRIC, language)
    panel = window.secondary_panel() or window.task_panel
    field = panel.inputs[0][-1]
    original = field.text()
    path = Path(window.presenter.workspace.location)
    durable = path.read_bytes()
    field.setText("invalid")
    field.textEdited.emit("invalid")
    assert_save(window, True)
    window.main_navigation.toolbar_actions["save"].trigger()
    assert field.text() == "invalid"
    assert path.read_bytes() == durable
    assert_save(window, True)
    field.setText(original)
    field.textEdited.emit(original)
    assert_save(window, False)


@pytest.mark.parametrize("language", list(Language))
def test_worker_notification_and_first_save(
    window: LifftWindow, tmp_path: Path, language: Language
) -> None:
    """Worker changes notify main Save; an empty temporary project needs first Save.

    Args:
        window: Existing integrated project window.
        tmp_path: Private first-Save destination.
        language: English or Spanish controls.

    Returns:
        None; data mutation updates Save without closing or refreshing a dialog.
    """
    window.language = language
    workspace = window.presenter.workspace
    window.save_project()
    assert_save(window, False)
    snapshot = workspace.read_hierarchy()
    workers = snapshot.hierarchy.work.workers
    changed = replace(workers[0], first_name="Changed")
    workspace.replace_hierarchy(
        snapshot,
        replace(
            snapshot.hierarchy,
            work=replace(snapshot.hierarchy.work, workers=(changed, *workers[1:])),
        ),
    )
    assert_save(window, True)
    window.save_project()
    assert_save(window, False)
    with patch.object(window, "choose_project_details", return_value=("", "")):
        window.main_navigation.toolbar_actions["new"].trigger()
    assert window._is_unsaved_project()
    assert_save(window, True)
    with patch.object(window, "choose_file", return_value=""):
        window.main_navigation.toolbar_actions["save"].trigger()
    assert_save(window, True)
    with (
        patch.object(
            window, "choose_file", return_value=str(tmp_path / "first.ergprj")
        ),
        patch.object(window, "choose_project_details", return_value=("", "")),
    ):
        window.main_navigation.toolbar_actions["save"].trigger()
    assert_save(window, False)
    window.close_project()
    QApplication.processEvents()
    assert_save(window, False)

"""Regression tests for project filters, toolbar groups and chronological UI replay.

Test layer: synthetic classified assessments and owned native Qt controls; do not
modify reference code, operational databases, dependency versions or permanent projects.
"""

import hashlib
import sqlite3
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QFileDialog

from ergotools.application.settings import Language
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.lifft_store import StoreFormatError
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.project_properties_dialog import (
    ProjectPropertiesDialog,
)
from tests.test_saved_tool_data import window as window


def replay(window: LifftWindow, redo: bool = False) -> None:
    """Invoke actual main-toolbar replay with document rather than typing focus.

    Args:
        window: Fixture-owned integrated assessment window.
        redo: Reapply the next chronological operation instead of reverting one.

    Returns:
        None; actions share the main menu and standard keyboard history owner.
    """
    window.setFocus()
    window.history_actions.refresh()
    action = window.main_navigation.toolbar_actions["redo" if redo else "undo"]
    assert action.isEnabled()
    action.trigger()


@pytest.mark.parametrize("index", [1, 2])
def test_selector_navigation_and_source_replay_are_chronological(
    window: LifftWindow,
    index: int,
) -> None:
    """Selector edit, tool navigation and their reversals retain exact source data.

    Args:
        window: Classified project with all three tool assessments and two workers.
        index: DUET or Shoulder Tool tab index.

    Returns:
        None; verify original objects/values, source-before-navigation ordering and
        redo branching without any implicit project Save.
    """
    window.assessment_tabs.setCurrentIndex(index)
    panel = window.secondary_panel()
    active = window.presenter.workspace.active
    before = active.state
    combo = panel.inputs[0][0]
    combo.setCurrentIndex((combo.currentIndex() + 1) % combo.count())
    changed = active.state
    assert changed != before and not panel.pending
    target = 2 if index == 1 else 0
    window.assessment_tabs.setCurrentIndex(target)
    replay(window)
    assert window.assessment_tabs.currentIndex() == index
    assert window.presenter.workspace.active is active and active.state is changed
    replay(window)
    assert active.state is before
    replay(window, True)
    assert active.state is changed
    replay(window, True)
    assert window.assessment_tabs.currentIndex() == target
    replay(window)
    replay(window)
    panel = window.secondary_panel()
    combo = panel.inputs[0][0]
    combo.setCurrentIndex((combo.currentIndex() + 2) % combo.count())
    window.setFocus()
    window.history_actions.refresh()
    assert not window.main_navigation.toolbar_actions["redo"].isEnabled()


def test_worker_navigation_replays_without_writing_or_save_consent(
    window: LifftWindow,
) -> None:
    """Worker Undo/Redo restores exact context without a project Save prompt.

    Args:
        window: Fixture-owned classified project with workers w and x.

    Returns:
        None; assert navigation reversibility, unchanged project bytes and retained
        history without treating navigation as a destructive record operation.
    """
    path = Path(window.presenter.workspace.location)
    original = hashlib.sha256(path.read_bytes()).hexdigest()
    before = window.assessment_navigation.view
    window.navigate_worker("x")
    after = window.assessment_navigation.view
    assert after.worker_id == "x"
    with patch.object(window, "dirty_choice") as departure:
        replay(window)
    departure.assert_not_called()
    assert window.assessment_navigation.view == before
    replay(window, True)
    assert window.assessment_navigation.view == after
    assert hashlib.sha256(path.read_bytes()).hexdigest() == original


def test_toolbar_groups_workplace_menu_and_real_properties(window: LifftWindow) -> None:
    """Expose setup groups, menu export and a real owned Properties dialog.

    Args:
        window: Fixture-owned integrated saved project.

    Returns:
        None; assert exact group order and populated Properties invocation.
    """
    nav = window.main_navigation
    groups = [[]]
    keys = {action: key for key, action in nav.toolbar_actions.items()}
    for action in nav.toolbar.actions():
        if action.isSeparator():
            groups.append([])
        else:
            groups[-1].append(keys[action])
    assert groups == [
        ["undo", "redo"],
        ["new", "open", "save"],
        ["plot", "jrot"],
        ["organization", "jobs"],
    ]
    QApplication.processEvents()
    assert all(
        nav.toolbar.widgetForAction(action).isVisible()
        for action in nav.toolbar.actions()
        if not action.isSeparator()
    )
    assert nav.toolbar_actions["export"] not in nav.toolbar.actions()
    assert window._assessment_menu.export_csv.isEnabled()
    for language, caption in (
        (Language.ENGLISH, "Workplace"),
        (Language.SPANISH, "Lugar de trabajo"),
    ):
        window.language = language
        window.translate()
        assert window._assessment_menu.work_setup.title() == caption
    inspected = []

    def inspect() -> None:
        """Inspect and close the actual read-only Properties modal.

        Args:
            None.

        Returns:
            None; retain a plain observed title rather than the modal widget.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, ProjectPropertiesDialog)
        assert dialog.fields["name"].text()
        assert all(field.isReadOnly() for field in dialog.fields.values())
        inspected.append(dialog.windowTitle())
        dialog.close_button.click()

    QTimer.singleShot(0, inspect)
    window._assessment_menu.properties.trigger()
    assert inspected


@pytest.mark.parametrize("saving", [False, True])
def test_project_file_picker_only_advertises_ergprj(
    window: LifftWindow,
    saving: bool,
) -> None:
    """Both ordinary project dialogs expose only the product project extension.

    Args:
        window: Fixture-owned integrated saved project.
        saving: Save destination picker instead of Open picker.

    Returns:
        None; cancel the real dialog without creating or overwriting anything.
    """
    inspected = []

    def inspect(dialog: QFileDialog) -> int:
        """Inspect the actual owned dialog at exec, without a timer/modal race.

        Args:
            dialog: Real project picker whose configuration is complete before exec.

        Returns:
            Rejected Qt result; assertions retain the exact extension/default-suffix
            contract without depending on global modal focus or filesystem timing.
        """
        assert not dialog.testOption(QFileDialog.Option.DontUseNativeDialog)
        assert dialog.nameFilters() == ["ErgoTools projects (*.ergprj)"]
        if saving:
            assert dialog.defaultSuffix() == "ergprj"
        inspected.append(True)
        return QFileDialog.Rejected

    with patch.object(QFileDialog, "exec", inspect):
        assert window.choose_file(saving) == ""
    assert inspected


def test_unrelated_sqlite_is_rejected_without_modification(tmp_path: Path) -> None:
    """An arbitrary SQLite container is not accepted as an ErgoTools project.

    Args:
        tmp_path: Disposable database directory; misleading extension is deliberate.

    Returns:
        None; verify format validation and byte-for-byte preservation after rejection.
    """
    path = tmp_path / "unrelated.ergprj"
    with closing(sqlite3.connect(path)) as database, database:
        database.execute("CREATE TABLE unrelated(value TEXT)")
    before = path.read_bytes()
    with pytest.raises((StoreFormatError, sqlite3.DatabaseError, ValueError)):
        AssessmentProjectFile.open(path)
    assert path.read_bytes() == before

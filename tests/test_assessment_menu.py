"""Visible menu access and explicit post-delete creation with retained versions.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QTreeWidgetItemIterator

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.assessment_context_dialog import (
    AssessmentContextDialog,
)
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_saved_tool_data import KINDS
from tests.test_saved_tool_data import window as window


@pytest.mark.parametrize("index", [0, 1, 2])
def test_menu_create_after_delete_cancel_version_and_save(
    window: LifftWindow, index: int
) -> None:
    """Cancel retains pending deletion; recreation preserves unique ownership and tasks.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        index: Zero-based selected input/row/case index used by the parametrized
            regression.

    Returns:
        None.
    """
    workspace = window.presenter.workspace
    path = Path(workspace.location)
    window.assessment_tabs.setCurrentIndex(index)
    # Clear retains ownership; explicit backend deletion sets up this existing
    # creation regression without exposing a duplicate destructive control.
    workspace.delete_active_assessment(workspace.read_history())
    window._empty_kind = KINDS[index]
    window.refresh()
    menu = window._assessment_menu
    assert menu is not None and menu.isVisible()
    action = menu.actions_by_key["new_assessment"]
    # Deletion is a private project edit even with no active assessment.
    assert action.isEnabled() and menu.actions_by_key["save"].isEnabled()
    assert workspace.has_unsaved_changes
    with patch.object(window, "choose_item", return_value=("", False)):
        action.trigger()
    assert workspace.active is None

    def cancel() -> None:
        """Reject the actual assignment chooser after deletion.

        Reject the actual assignment chooser after deletion and verify cancellation
        leaves no replacement source.

        Args:
            None.

        Returns:
            None.
        """
        modal = QApplication.activeModalWidget()
        assert isinstance(modal, AssessmentContextDialog)
        modal.reject()

    with patch.object(window, "choose_item", return_value=("w", True)):
        QTimer.singleShot(0, cancel)
        action.trigger()
    assert workspace.active is None
    # The approved project session retains deletion privately until the main Save.
    before = {
        entry.document: workspace.assessment_source(entry.document.document_id)
        for entry in workspace.list_assessments()
    }

    def accept() -> None:
        """Find exact synthetic assignment 1 in typed tree data.

        Find exact synthetic assignment 1 in typed tree data and accept its explicit
        post-delete recreation.

        Args:
            None.

        Returns:
            None.

        Raises:
            AssertionError: The deliberately rejected boundary/routing condition occurs,
                or the expected synthetic modal data are unavailable.
        """
        modal = QApplication.activeModalWidget()
        assert isinstance(modal, AssessmentContextDialog)
        iterator = QTreeWidgetItemIterator(modal.tree)
        while iterator.value() is not None:
            item = iterator.value()
            option = item.data(0, Qt.UserRole)
            if option is not None and option.assignment.assignment_id == 1:
                modal.tree.setCurrentItem(item)
                modal.use.click()
                return
            iterator += 1
        raise AssertionError("Synthetic classified assignment was not offered")

    if index == 2:
        window.language = Language.SPANISH
        window.translate()
        window.enable_controls()
        assert menu.project.title() == "Proyecto" and menu.edit.title() == "Editar"
    with patch.object(window, "choose_item", return_value=("w", True)):
        QTimer.singleShot(0, accept)
        action.trigger()
    active = workspace.active
    assert active is not None and window.active_kind() is KINDS[index]
    assert len(active.state.tasks) == 15 and all(
        t.repetitions is None for t in active.state.tasks
    )
    assert menu.actions_by_key["save"].isEnabled()
    panel = window.task_panel if index == 0 else window.secondary_panel()
    field = panel.inputs[0][2 if index == 0 else -1]
    field.setText("350")
    field.textEdited.emit("350")
    menu.actions_by_key["save"].trigger()
    entry = next(
        e
        for e in workspace.read_history().history.entries
        if e.document_id == active.document.document_id
    )
    assert entry.assignment_id == 1 and entry.kind is KINDS[index]
    assert not hasattr(entry, "version") and not hasattr(entry, "is_current")
    with AssessmentProjectFile.open(path) as project:
        assert project.load(active.document).tasks[0].repetitions == 350
        assert all(project.load(key) == source for key, source in before.items())
    # A second current creation is refused rather than replacing/promoting silently.
    with patch.object(window, "choose_item", return_value=("w", True)):
        QTimer.singleShot(0, accept)
        action.trigger()
    assert (
        workspace.active is active
        and workspace.active.state.tasks[0].repetitions == 350
    )


def test_menu_undo_redo_and_project_availability(window: LifftWindow) -> None:
    """Menu actions share history and update availability without duplicate edits.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    menu = window._assessment_menu
    before = window.presenter.workspace.active.state
    window.presenter.set_task_count(2)
    window.refresh()
    menu.actions_by_key["undo"].trigger()
    assert window.presenter.workspace.active.state is before
    assert menu.actions_by_key["redo"].isEnabled()
    menu.actions_by_key["redo"].trigger()
    assert len(window.presenter.workspace.active.state.tasks) == 2
    window.presenter.workspace.close(choice=CloseChoice.DISCARD)
    window.refresh()
    assert (
        menu.actions_by_key["new"].isEnabled()
        and menu.actions_by_key["open"].isEnabled()
    )
    assert not menu.actions_by_key["new_assessment"].isEnabled()

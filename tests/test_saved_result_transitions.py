"""Calculated-result Save on transitions and Save As transaction acceptance.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.saved_result_store import SavedResultStore
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_saved_tool_data import window as window


def edit_and_calculate(window: LifftWindow, index: int) -> None:
    """Commit a deliberate repetitions edit through the real integrated controls.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        index: Zero-based selected input/row/case index used by the parametrized
            regression.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(index)
    panel = window.task_panel if index == 0 else window.secondary_panel()
    field = panel.inputs[0][2 if index == 0 else -1]
    field.setText("321")
    field.textEdited.emit("321")
    window.run(window.calculate)
    assert window.presenter.workspace.has_unsaved_changes
    assert window.current_result_snapshot() is not None


@pytest.mark.parametrize("index", [0, 1, 2])
def test_same_project_switch_retains_calculation_until_main_save(
    window: LifftWindow,
    index: int,
) -> None:
    """Navigation retains edited inputs/results privately with their original ownership.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        index: Zero-based selected input/row/case index used by the parametrized
            regression.

    Returns:
        None.
    """
    edit_and_calculate(window, index)
    workspace = window.presenter.workspace
    active, location = workspace.active, workspace.location
    result = window.current_result_snapshot()
    target = active.document.document_id.rsplit("-", 1)[0] + "-3"
    assert workspace.switch(location, target).completed
    with AssessmentProjectFile.open(Path(location)) as reopened:
        assert reopened.load(active.document) != active.state
        assert reopened.load_saved_result(active.document) is None
    assert workspace.editing.repository.load_saved_result(active.document) == result
    workspace.save()
    with AssessmentProjectFile.open(Path(location)) as reopened:
        assert reopened.load(active.document) == active.state
        assert reopened.load_saved_result(active.document) == result
    assert not active.is_dirty


@pytest.mark.parametrize("choice", [CloseChoice.CANCEL, CloseChoice.DISCARD])
def test_cancel_and_discard_never_write_calculated_results(
    window: LifftWindow,
    choice: CloseChoice,
) -> None:
    """Only the explicit Save decision can persist an edited calculation.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        choice: Explicit Save/Discard/Cancel disposition used to verify transition
            ordering.

    Returns:
        None.
    """
    edit_and_calculate(window, 0)
    workspace = window.presenter.workspace
    active, location = workspace.active, workspace.location
    with AssessmentProjectFile.open(Path(location)) as original:
        before = original.load(active.document)
    with patch.object(SavedResultStore, "write", side_effect=AssertionError("write")):
        outcome = workspace.switch(location, "lifft-3", choice=choice)
    assert outcome.completed is (choice is CloseChoice.DISCARD)
    if choice is CloseChoice.CANCEL:
        assert workspace.active is active and workspace.has_unsaved_changes
    with AssessmentProjectFile.open(Path(location)) as reopened:
        assert reopened.load(active.document) == before
        assert reopened.load_saved_result(active.document) is None


def test_invalid_target_and_failed_main_save_keep_private_result(
    window: LifftWindow,
) -> None:
    """Invalid targets and failed main Save retain accepted source and result.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    edit_and_calculate(window, 0)
    workspace = window.presenter.workspace
    active, location = workspace.active, workspace.location
    result = window.current_result_snapshot()
    with AssessmentProjectFile.open(Path(location)) as original:
        before = original.load(active.document)
    with (
        patch.object(SavedResultStore, "write", side_effect=AssertionError("write")),
        pytest.raises(KeyError),
    ):
        workspace.switch(location, "missing", choice=CloseChoice.SAVE)
    with (
        patch.object(
            SavedResultStore, "write", side_effect=sqlite3.OperationalError("fixture")
        ),
        pytest.raises(sqlite3.OperationalError),
    ):
        workspace.save(result)
    assert workspace.active is active and workspace.has_unsaved_changes
    assert window.current_result_snapshot() == result
    with AssessmentProjectFile.open(Path(location)) as reopened:
        assert reopened.load(active.document) == before
        assert reopened.load_saved_result(active.document) is None


@pytest.mark.parametrize("index", [0, 1, 2])
def test_save_as_saves_calculation_only_into_copy(
    window: LifftWindow,
    tmp_path: Path,
    index: int,
) -> None:
    """Save As adopts the calculated copy without changing source project records.

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
    edit_and_calculate(window, index)
    workspace = window.presenter.workspace
    active, location = workspace.active, workspace.location
    result = window.current_result_snapshot()
    with AssessmentProjectFile.open(Path(location)) as original:
        before = original.load(active.document)
    destination = tmp_path / "copy.ergprj"
    assert workspace.save_as(str(destination), result=result).completed
    assert workspace.active.state == active.state and not workspace.active.is_dirty
    assert workspace.historical_result() == result
    with AssessmentProjectFile.open(Path(location)) as original:
        assert original.load(active.document) == before
        assert original.load_saved_result(active.document) is None
    with AssessmentProjectFile.open(destination) as copied:
        assert copied.load_saved_result(active.document) == result


def test_save_as_result_failure_preserves_original_session(
    window: LifftWindow,
    tmp_path: Path,
) -> None:
    """Failed copy-result storage retains original ownership/history for retry.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    edit_and_calculate(window, 0)
    workspace = window.presenter.workspace
    active, location = workspace.active, workspace.location
    result = window.current_result_snapshot()
    destination = tmp_path / "failed-copy.ergprj"
    with (
        patch.object(
            SavedResultStore, "write", side_effect=sqlite3.OperationalError("fixture")
        ),
        pytest.raises(sqlite3.OperationalError),
    ):
        workspace.save_as(str(destination), result=result)
    assert workspace.active is active and workspace.location == location
    assert workspace.has_unsaved_changes and window.current_result_snapshot() == result
    with AssessmentProjectFile.open(Path(location)) as original:
        assert original.load(active.document) != active.state
        assert original.load_saved_result(active.document) is None
    # Retained sources and results are prepared before exclusive publication.
    assert not destination.exists()

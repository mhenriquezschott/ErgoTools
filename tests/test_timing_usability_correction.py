"""Owner-reported timing and reusable-name behavior on private native projects."""

from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QCoreApplication, QEvent, QPoint, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.rotation_timing_actions import (
    draw_timing_break,
    equalize_contiguous_timing,
    join_work_blocks,
)
from ergotools.bootstrap import load_icons
from ergotools.domain.language import Language
from ergotools.domain.rotation_timing import equal_timing
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.rotation_timing_dialog import RotationTimingDialog
from ergotools.presentation.desktop.task_name_dialog import TaskNameDialog
from tests.test_rotation_timing_storage import timing_workspace
from tests.test_task_count_integration import window as window

# Native ownership outlives every test dialog and its shared history subscription.
_APP = QApplication.instance() or QApplication([])


def retire(dialog: RotationTimingDialog | TaskNameDialog) -> None:
    """Dispose an owned window without re-accepting intentionally invalid test fields.

    Args:
        dialog: Private native editor.

    Returns:
        None; deferred controls retire before the private project closes.
    """
    dialog.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


@pytest.mark.parametrize("language", list(Language))
def test_add_break_mouse_undo_redo_and_no_repeated_block_identity(
    tmp_path: Path, language: Language
) -> None:
    """The public +Break is an immediately reversible complete edit, not a blank trap.

    Args:
        tmp_path: Disposable native project.
        language: Both maintained interface languages.

    Returns:
        None; actual title buttons restore exact timing one action at a time.
    """
    workspace = timing_workspace(tmp_path)
    dialog = RotationTimingDialog(workspace, "Day", load_icons(), language)
    try:
        dialog.show()
        _APP.processEvents()
        QTest.mouseClick(dialog.use_button, Qt.LeftButton)
        before = workspace.load_shift_timings()[0].timing
        revision = workspace.editing.history.revision
        QTest.mouseClick(dialog.add_break_button, Qt.LeftButton)
        after = workspace.load_shift_timings()[0].timing
        assert len(after.breaks) == 1 and len(after.blocks()) == 5
        assert after.productive_minutes == 465
        assert all(len(block.pieces) == 1 for block in after.blocks())
        assert not after.equal_blocks and dialog.unequal_button.isChecked()
        assert workspace.editing.history.revision == revision + 1
        QTest.mouseClick(dialog.history.undo_button, Qt.LeftButton)
        assert workspace.load_shift_timings()[0].timing == before
        QTest.mouseClick(dialog.history.redo_button, Qt.LeftButton)
        assert workspace.load_shift_timings()[0].timing == after
    finally:
        retire(dialog)
        workspace.close(choice=CloseChoice.DISCARD)


def test_equal_confirmation_moves_pauses_keeps_names_lengths_and_is_reversible(
    tmp_path: Path,
) -> None:
    """Equalization never hides fragmented work or silently deletes a pause.

    Args:
        tmp_path: Disposable native workspace.

    Returns:
        None; No preserves all data and Yes with insufficient count asks to increase it.
    """
    workspace = timing_workspace(tmp_path)
    dialog = RotationTimingDialog(workspace, "Day", load_icons())
    try:
        source = draw_timing_break(equal_timing(480, 4), 60, 90)
        source = draw_timing_break(source, 270, 300)
        assert dialog._commit(source, force=True)
        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.No
        ) as question:
            dialog.mode_equal()
        assert question.call_count == 1 and dialog._model == source
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            dialog.mode_equal()
        equal = dialog._model
        assert equal.equal_blocks and all(
            len(block.pieces) == 1 for block in equal.blocks()
        )
        assert max(equal.block_minutes) - min(equal.block_minutes) <= 1
        assert [(p.name, p.interval.end - p.interval.start) for p in equal.breaks] == [
            (None, 30),
            (None, 30),
        ]
        assert workspace.editing.replay(redo=False) and dialog._model == source
        with patch.object(QMessageBox, "question", return_value=QMessageBox.No):
            dialog.count.setValue(1)
        assert dialog._model == source
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            dialog.count.setValue(1)
        assert len(dialog._model.block_minutes) == 1
        assert all(len(block.pieces) == 1 for block in dialog._model.blocks())
        assert len(dialog._model.breaks) == 2
    finally:
        retire(dialog)
        workspace.close(choice=CloseChoice.DISCARD)


def test_cursor_guide_hover_resize_hand_and_join_gap_guard(tmp_path: Path) -> None:
    """Pointer feedback identifies the action and clock without changing accepted data.

    Args:
        tmp_path: Disposable native timing project.

    Returns:
        None; hover creates no history and joins cannot leap an existing break.
    """
    workspace = timing_workspace(tmp_path)
    dialog = RotationTimingDialog(workspace, "Day", load_icons())
    try:
        dialog.show()
        source = draw_timing_break(equal_timing(480, 1), 180, 240)
        assert dialog._commit(source, force=True)
        timeline = dialog.timeline
        with pytest.raises(ValueError, match="Remove the break"):
            join_work_blocks(source, 1)
        timeline.set_tool("split")
        point = QPoint(round(timeline._x(90)), 60)
        revision = workspace.editing.history.revision
        QTest.mouseMove(timeline, point)
        assert timeline._hover_minute == 90 and timeline._hover_segment == ("block", 0)
        timeline.set_tool("move")
        assert timeline.cursor_at(timeline._x(180)) == Qt.SizeHorCursor
        assert timeline.cursor_at(timeline._x(210)) == Qt.OpenHandCursor
        assert (
            timeline.cursor_at(timeline._x(210), dragging=True) == Qt.ClosedHandCursor
        )
        assert workspace.editing.history.revision == revision
        equal = equalize_contiguous_timing(source, 2)
        assert equal.block_minutes == (210, 210)
        assert equal.breaks[0].interval.start == 210
    finally:
        retire(dialog)
        workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("language", list(Language))
def test_task_name_manager_uses_existing_catalog_history_and_private_save(
    tmp_path: Path, language: Language
) -> None:
    """Names can be created/edited/searched/deleted and replayed without disk writes.

    Args:
        tmp_path: Disposable native project.
        language: Both maintained UI languages.

    Returns:
        None; existing catalog identities remain stable through rename and replay.
    """
    workspace = timing_workspace(tmp_path)
    path = Path(workspace.location)
    before = path.read_bytes()
    dialog = TaskNameDialog(workspace, load_icons(), language)
    try:
        dialog.show()
        dialog.name.setText("Empaque manual")
        dialog.description.setText("Preparación y embalaje")
        assert dialog.commit()
        identity = dialog.identity
        dialog.name.setText("Empaque final")
        assert dialog.commit()
        assert workspace.load_task_definitions()[0].definition_id == identity
        QTest.mouseClick(dialog.history.undo_button, Qt.LeftButton)
        assert dialog.name.text() == "Empaque manual"
        QTest.mouseClick(dialog.history.redo_button, Qt.LeftButton)
        assert dialog.name.text() == "Empaque final"
        dialog.search.setText("zzzz")
        assert dialog.table.topLevelItem(0).isHidden()
        dialog.search.clear()
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            dialog.delete_name()
        assert workspace.load_task_definitions() == ()
        assert workspace.editing.replay(redo=False)
        assert workspace.load_task_definitions()[0].definition_id == identity
        assert path.read_bytes() == before
    finally:
        retire(dialog)
        workspace.close(choice=CloseChoice.DISCARD)


def test_name_manager_keeps_referenced_worker_task_and_results(
    window: LifftWindow, tmp_path: Path
) -> None:
    """Deleting a referenced name is rejected atomically rather than breaking tasks.

    Args:
        window: Private native Main owner with shared project history.
        tmp_path: Disposable native project directory.

    Returns:
        None; source inputs/results and history cursor remain exactly unchanged.
    """
    from ergotools.domain.model_units import MeasurementSystem
    from ergotools.domain.task_catalog import TaskDefinition
    from tests.test_task_input_history import reopen_grid

    reopen_grid(window, tmp_path, 0, MeasurementSystem.METRIC, Language.ENGLISH)
    workspace = window.presenter.workspace
    definition = TaskDefinition("packing", "Packing")
    workspace.replace_task_definitions((), (definition,))
    panel = window.task_panel
    panel.task_actions.refresh_names()
    control = panel.task_grid.task_names[0]
    control.setCurrentIndex(control.findData("packing"))
    control.activated.emit(control.currentIndex())
    source = workspace.active.state
    result = workspace.historical_result()
    dialog = TaskNameDialog(workspace, load_icons(), Language.ENGLISH)
    try:
        dialog.identity = "packing"
        dialog.reload()
        revision = workspace.editing.history.revision
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            dialog.delete_name()
        assert "used by an assessment" in dialog.error.text()
        assert workspace.load_task_definitions() == (definition,)
        assert (
            workspace.active.state == source and workspace.historical_result() == result
        )
        assert workspace.editing.history.revision == revision
    finally:
        retire(dialog)

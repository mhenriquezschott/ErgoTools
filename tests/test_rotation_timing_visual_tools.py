"""Actual timeline/manual tools use one complete model and shared project Undo/Redo."""

from pathlib import Path

import pytest
from PyQt5.QtCore import QCoreApplication, QEvent, QPoint, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.bootstrap import load_icons
from ergotools.domain.language import Language
from ergotools.presentation.desktop.rotation_timing_dialog import RotationTimingDialog
from tests.test_rotation_timing_storage import timing_workspace

# Keep Qt alive until every owned test timeline and its workspace subscription retire.
_APP = QApplication.instance() or QApplication([])


def point(dialog: RotationTimingDialog, minute: int) -> QPoint:
    """Project a test clock to the actual native work/break bar.

    Args:
        dialog: Current native timing editor.
        minute: Relative elapsed minute chosen independently by the test.

    Returns:
        Logical widget position inside the segment bar.
    """
    return QPoint(round(dialog.timeline._x(minute)), 60)


def drag(dialog: RotationTimingDialog, first: int, last: int) -> None:
    """Perform one real pointer gesture, including final release projection.

    Args:
        dialog: Owned timing window.
        first: Starting relative clock minute.
        last: Final relative clock minute.

    Returns:
        None; native host callbacks own all acceptance and history.
    """
    QTest.mousePress(dialog.timeline, Qt.LeftButton, pos=point(dialog, first))
    QTest.mouseMove(dialog.timeline, point(dialog, last))
    QTest.mouseRelease(dialog.timeline, Qt.LeftButton, pos=point(dialog, last))
    _APP.processEvents()


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("shift", ["Day", "Night"])
def test_pointer_break_tools_and_escape_replay_one_gesture_at_a_time(
    tmp_path: Path, language: Language, shift: str
) -> None:
    """Drawing, moving, edge resizing and removing real pauses remain fully reversible.

    Args:
        tmp_path: Private native project directory.
        language: English/Spanish controls.
        shift: Ordinary or overnight eight-hour clock.

    Returns:
        None; Escape cancels a preview and returns the ordinary selection cursor.
    """
    workspace = timing_workspace(tmp_path)
    dialog = RotationTimingDialog(workspace, shift, load_icons(), language)
    try:
        dialog.show()
        _APP.processEvents()
        dialog.use_button.click()
        dialog.timeline_tools["draw_break"].click()
        revision = workspace.editing.history.revision
        drag(dialog, 180, 210)
        assert workspace.editing.history.revision == revision + 1
        paused = workspace.load_shift_timings()[0].timing
        assert (paused.breaks[0].interval.start, paused.breaks[0].interval.end) == (
            180,
            210,
        )
        assert paused.productive_minutes == 450
        dialog.timeline_tools["move"].click()
        drag(dialog, 195, 225)
        moved = workspace.load_shift_timings()[0].timing
        assert (moved.breaks[0].interval.start, moved.breaks[0].interval.end) == (
            210,
            240,
        )
        drag(dialog, 240, 255)
        assert workspace.load_shift_timings()[0].timing.breaks[0].interval.end == 255
        dialog.timeline_tools["remove"].click()
        QTest.mouseClick(dialog.timeline, Qt.LeftButton, pos=point(dialog, 230))
        removed = workspace.load_shift_timings()[0].timing
        assert removed.block_minutes == (120, 60, 53, 127, 120)
        assert removed.productive_minutes == 480 and not removed.breaks
        assert all(len(block.pieces) == 1 for block in removed.blocks())
        assert workspace.editing.replay(redo=False)
        assert workspace.load_shift_timings()[0].timing.breaks[0].interval.end == 255
        assert workspace.editing.replay(redo=True)
        revision = workspace.editing.history.revision
        dialog.timeline_tools["draw_break"].click()
        QTest.mousePress(dialog.timeline, Qt.LeftButton, pos=point(dialog, 60))
        QTest.mouseMove(dialog.timeline, point(dialog, 90))
        QTest.keyClick(dialog.timeline, Qt.Key_Escape)
        QTest.mouseRelease(dialog.timeline, Qt.LeftButton, pos=point(dialog, 90))
        assert workspace.editing.history.revision == revision
        assert workspace.load_shift_timings()[0].timing == removed
        assert dialog.timeline_tools["select"].isChecked()
    finally:
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        workspace.close(choice=CloseChoice.DISCARD)


def test_split_join_manual_clock_and_break_duration_share_history(
    tmp_path: Path,
) -> None:
    """Manual and pointer editing use the same boundaries and preserve other budgets.

    Args:
        tmp_path: Disposable current native project.

    Returns:
        None; buttons, clocks and durations retain individual Undo steps.
    """
    workspace = timing_workspace(tmp_path)
    dialog = RotationTimingDialog(workspace, "Day", load_icons())
    try:
        dialog.show()
        _APP.processEvents()
        dialog.use_button.click()
        dialog.timeline_tools["split"].click()
        QTest.mouseClick(dialog.timeline, Qt.LeftButton, pos=point(dialog, 60))
        assert workspace.load_shift_timings()[0].timing.block_minutes == (
            60,
            60,
            120,
            120,
            120,
        )
        dialog.timeline_tools["join"].click()
        QTest.mouseClick(dialog.timeline, Qt.LeftButton, pos=point(dialog, 60))
        assert workspace.load_shift_timings()[0].timing.block_minutes == (120,) * 4
        dialog.block_table.setCurrentCell(0, 0)
        dialog.add_block_button.click()
        assert workspace.load_shift_timings()[0].timing.block_minutes == (
            60,
            60,
            120,
            120,
            120,
        )
        dialog.remove_block_button.click()
        assert workspace.load_shift_timings()[0].timing.block_minutes == (120,) * 4
        end = dialog.block_clocks[0][1]
        end.set_value("09:00")
        end.editingFinished.emit()
        assert workspace.load_shift_timings()[0].timing.block_minutes == (
            60,
            180,
            120,
            120,
        )
        dialog.add_break_button.click()
        _, first, last = dialog.break_rows[0]
        first.set_value("12:00")
        last.set_value("12:30")
        last.editingFinished.emit()
        dialog.break_spins[0].setValue(45)
        dialog.break_spins[0].editingFinished.emit()
        assert workspace.load_shift_timings()[0].timing.breaks[0].interval.end == 285
        assert dialog.break_rows[0][2].clock_text() == "12:45"
        assert workspace.editing.replay(redo=False)
        assert dialog.break_rows[0][2].clock_text() == "12:30"
    finally:
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        workspace.close(choice=CloseChoice.DISCARD)


def test_add_block_at_break_edge_and_focused_break_duration_prepare(
    tmp_path: Path,
) -> None:
    """Midpoint splits around pauses and still-focused duration text use normal history.

    Args:
        tmp_path: Disposable native timing workspace.

    Returns:
        None; no Qt callback exception or lost final duration input occurs.
    """
    workspace = timing_workspace(tmp_path)
    dialog = RotationTimingDialog(workspace, "Day", load_icons())
    try:
        dialog.show()
        _APP.processEvents()
        dialog.count.setValue(1)
        dialog.timeline_tools["draw_break"].click()
        drag(dialog, 180, 300)
        dialog.add_block_button.click()
        assert workspace.load_shift_timings()[0].timing.block_minutes == (90, 90, 180)
        spin = dialog.break_spins[0]
        spin.setFocus()
        edit = spin.lineEdit()
        edit.selectAll()
        QTest.keyClicks(edit, "60")
        assert dialog.prepare()
        assert workspace.load_shift_timings()[0].timing.breaks[0].interval.end == 240
    finally:
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        workspace.close(choice=CloseChoice.DISCARD)


def test_real_guided_split_requires_lost_cell_consent_and_undo_restores_everything(
    tmp_path: Path,
) -> None:
    """The real scenario timing port guards existing assignment data, not just geometry.

    Args:
        tmp_path: Private populated guided project.

    Returns:
        None; No preserves all inputs, Yes clears affected cells only, Undo is exact.
    """
    from dataclasses import replace
    from unittest.mock import patch

    from ergotools.application.rotation_entry import RotationEntryChange
    from ergotools.application.rotation_timing_actions import split_work_block
    from tests.test_jrot_planning_ui import dispose, planning_dialog
    from tests.test_rotation_scenarios import balanced_rows

    host = planning_dialog(tmp_path, Language.ENGLISH)
    try:
        record = host.current()
        host.edit_inputs(
            record,
            RotationEntryChange(
                replace(record.inputs, baseline=balanced_rows(record.inputs))
            ),
        )
        original = host.current()
        timing = original.inputs.timing
        split = split_work_block(timing, 120)
        with patch.object(host, "confirm", return_value=False) as consent:
            assert not host.write_timing(original.scenario_id, timing, split)
        consent.assert_called_once()
        assert host.current() == original
        with patch.object(host, "confirm", return_value=True):
            assert host.write_timing(original.scenario_id, timing, split)
        assert host.current().inputs.baseline[0].target_keys[:2] == (None, None)
        assert (
            host.current().inputs.baseline[0].target_keys[2]
            == original.inputs.baseline[0].target_keys[1]
        )
        assert host.owner.replay(redo=False)
        assert host.current() == original
        assert host.owner.replay(redo=True)
        assert host.current().inputs.timing == split
    finally:
        dispose(host)


def test_cancelled_structural_change_restores_manual_count_without_another_prompt(
    tmp_path: Path,
) -> None:
    """Declining data-loss consent restores the accepted form as well as project data.

    Args:
        tmp_path: Private guided workspace with entered assignments.

    Returns:
        None; closing afterwards does not resubmit the cancelled timing edit.
    """
    from dataclasses import replace
    from functools import partial
    from unittest.mock import patch

    from ergotools.application.rotation_entry import RotationEntryChange
    from tests.test_jrot_planning_ui import dispose, planning_dialog
    from tests.test_rotation_scenarios import balanced_rows

    host = planning_dialog(tmp_path, Language.ENGLISH)
    child = None
    try:
        record = host.current()
        host.edit_inputs(
            record,
            RotationEntryChange(
                replace(record.inputs, baseline=balanced_rows(record.inputs))
            ),
        )
        original = host.current()
        child = RotationTimingDialog(
            host.workspace,
            "Day",
            load_icons(),
            parent=host,
            read_target=partial(host.timing_target, original.scenario_id),
            write_target=partial(host.write_timing, original.scenario_id),
        )
        child.show()
        with patch.object(host, "confirm", return_value=False) as consent:
            child.count.setValue(3)
        consent.assert_called_once()
        assert host.current() == original
        assert child.count.value() == 2 and child.prepare()
        assert not child._draft_pending
    finally:
        if child is not None:
            child.close()
            child.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        dispose(host)


def test_invalid_work_input_is_not_lost_by_break_edit_and_combined_correction_is_atomic(
    tmp_path: Path,
) -> None:
    """The common validator prevents one section from overwriting pending sibling data.

    Args:
        tmp_path: Private complete timing project.

    Returns:
        None; corrections survive until their complete model can be accepted.
    """
    workspace = timing_workspace(tmp_path)
    dialog = RotationTimingDialog(workspace, "Day", load_icons())
    try:
        dialog.use_button.click()
        dialog.add_break_button.click()
        _, first, last = dialog.break_rows[0]
        first.set_value("12:00")
        last.set_value("13:00")
        last.editingFinished.emit()
        dialog.unequal_button.click()
        original = workspace.load_shift_timings()[0].timing
        dialog.block_spins[0].setValue(420)
        dialog.block_spins[0].editingFinished.emit()
        assert workspace.load_shift_timings()[0].timing == original
        dialog.break_spins[0].setValue(45)
        dialog.break_spins[0].editingFinished.emit()
        assert workspace.load_shift_timings()[0].timing == original
        assert dialog.block_spins[0].value() == 420
        assert dialog.break_spins[0].value() == 45
        dialog.block_spins[0].setValue(90)
        dialog.block_spins[0].editingFinished.emit()
        accepted = workspace.load_shift_timings()[0].timing
        assert accepted.breaks[0].interval.end == 285
        assert accepted.block_minutes == (90, 150, 75, 120)
        assert dialog._pending_duration is None
        assert dialog._pending_block_clock is None
        assert dialog._pending_break_duration is None
        revision = workspace.editing.history.revision
        assert dialog.prepare() and workspace.editing.history.revision == revision
    finally:
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        workspace.close(choice=CloseChoice.DISCARD)


def test_removing_overlap_keeps_the_other_breaks_edited_end_clock(
    tmp_path: Path,
) -> None:
    """Duration origins follow controls safely when table rows shift.

    Args:
        tmp_path: Private current timing project.

    Returns:
        None; deleting another row retains the full pending interval.
    """
    workspace = timing_workspace(tmp_path)
    dialog = RotationTimingDialog(workspace, "Day", load_icons())
    try:
        dialog.use_button.click()
        for start, end in (("09:00", "10:00"), ("12:00", "12:30")):
            dialog.add_break_button.click()
            _, first, last = dialog.break_rows[-1]
            first.set_value(start)
            last.set_value(end)
            last.editingFinished.emit()
        original = workspace.load_shift_timings()[0].timing
        _, first, last = dialog.break_rows[1]
        first.set_value("09:30")
        first.editingFinished.emit()
        assert workspace.load_shift_timings()[0].timing == original
        dialog.break_table.setCurrentCell(0, 0)
        dialog.remove_break_button.click()
        accepted = workspace.load_shift_timings()[0].timing
        assert len(accepted.breaks) == 1
        assert (accepted.breaks[0].interval.start, accepted.breaks[0].interval.end) == (
            90,
            270,
        )
        assert dialog.break_rows[0][2].clock_text() == "12:30"
        assert workspace.editing.replay(redo=False)
        assert workspace.load_shift_timings()[0].timing == original
    finally:
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("shift", ["Day", "Night"])
def test_selected_boundary_clock_and_contextual_action_cursors(
    tmp_path: Path, language: Language, shift: str
) -> None:
    """Real boundary selection keeps its exact clock and tools describe their targets.

    Args:
        tmp_path: Private synthetic project, never a maintained fixture.
        language: Both supported timeline caption languages.
        shift: Day or overnight clock, including the next-day marker.

    Returns:
        None; selection/hover creates no edit, drag/Undo restores boundary clocks,
        and three distinct bitmap cursors survive press and tool changes.
    """
    from PyQt5.QtGui import QCursor

    from ergotools.presentation.desktop.rotation_timeline import timing_action_cursor

    workspace = timing_workspace(tmp_path)
    dialog = RotationTimingDialog(workspace, shift, load_icons(), language)
    try:
        dialog.show()
        _APP.processEvents()
        dialog.use_button.click()
        timeline = dialog.timeline
        revision = workspace.editing.history.revision
        QTest.mouseClick(timeline, Qt.LeftButton, pos=point(dialog, 120))
        assert timeline.selected_boundary_minute() == 120
        assert timeline.clock.label(120) in timeline.tooltip_at(timeline._x(120))
        assert workspace.editing.history.revision == revision
        QTest.mousePress(timeline, Qt.LeftButton, pos=point(dialog, 120))
        timeline.preview_at(timeline._x(135))
        assert timeline.selected_boundary_minute() == 135
        QTest.keyClick(timeline, Qt.Key_Escape)
        assert timeline.selected_boundary_minute() == 120
        QTest.mouseRelease(timeline, Qt.LeftButton, pos=point(dialog, 135))
        drag(dialog, 120, 135)
        assert timeline.selected_boundary_minute() == 135
        assert workspace.editing.replay(redo=False)
        assert timeline.selected_boundary_minute() == 120
        assert workspace.editing.replay(redo=True)
        assert timeline.selected_boundary_minute() == 135
        dialog.add_break_button.click()
        pause = timeline.timing.breaks[0]
        middle = (pause.interval.start + pause.interval.end) / 2
        for minute in (45, middle):
            tooltip = timeline.tooltip_at(timeline._x(minute))
            assert "min" in tooltip and " - " in tooltip
            expected_kind = (
                timeline.text("Work block", "Bloque de trabajo")
                if minute == 45
                else timeline.text("Break", "Descanso")
            )
            assert expected_kind in tooltip
        images = []
        for tool in ("split", "join", "remove"):
            timeline.set_tool(tool)
            cursor = timeline.tool_cursor()
            assert isinstance(cursor, QCursor) and not cursor.pixmap().isNull()
            images.append(cursor.pixmap().toImage())
            assert cursor.hotSpot() == (
                QPoint(18, 17) if tool == "join" else QPoint(16, 15)
            )
            assert cursor.pixmap().width() == (36 if tool == "join" else 31)
            QTest.mouseMove(timeline, point(dialog, 45))
            assert timeline.toolTip() == timeline.tooltip_at(timeline._x(45))
            QTest.mousePress(timeline, Qt.LeftButton, pos=point(dialog, 45))
            active = timeline.cursor_at(timeline._x(45), dragging=True)
            assert isinstance(active, QCursor)
            assert active.pixmap().toImage() == cursor.pixmap().toImage()
            QTest.keyClick(timeline, Qt.Key_Escape)
            QTest.mouseRelease(timeline, Qt.LeftButton, pos=point(dialog, 45))
        assert all(images[i] != images[j] for i in range(3) for j in range(i))
        with pytest.raises(ValueError, match="Unsupported"):
            timing_action_cursor("invalid")
    finally:
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        workspace.close(choice=CloseChoice.DISCARD)

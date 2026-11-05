"""Native timing editor, gesture boundaries and shared project history acceptance.

All dialogs borrow synthetic private current projects. Tests verify real controls,
No-default cancellation, midnight inputs, table/drag chronology and sole Main Save.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.bootstrap import load_icons
from ergotools.domain.organization_record import OrganizationKind
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.organization_dialog import OrganizationDialog
from ergotools.presentation.desktop.rotation_timing_dialog import RotationTimingDialog
from tests.test_rotation_timing_storage import timing_workspace

# Retain native Qt ownership until every test-owned editor has closed.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("language", list(Language))
def test_open_close_does_not_create_template_and_explicit_use_replays(
    tmp_path: Path,
    language: Language,
) -> None:
    """Preview is read-only until an explicit action; one creation is one history step.

    Args:
        tmp_path: Disposable project/preferences directory.
        language: Both maintained interface languages.

    Returns:
        None; accepted templates remain private until the main workspace Save.
    """
    workspace = timing_workspace(tmp_path)
    path = Path(workspace.location)
    before = path.read_bytes()
    dialog = RotationTimingDialog(workspace, "Day", load_icons(), language)
    try:
        dialog.show()
        _APP.processEvents()
        assert dialog.timeline.timing.block_minutes == (120,) * 4
        assert not dialog.remove_break_button.isEnabled()
        assert (
            workspace.load_shift_timings() == () and not workspace.has_unsaved_changes
        )
        dialog.accept()
        assert workspace.load_shift_timings() == ()
        dialog.show()
        dialog.use_button.click()
        assert workspace.load_shift_timings()[0].timing.block_minutes == (120,) * 4
        assert dialog.history.undo_button.isEnabled()
        assert workspace.editing.replay(redo=False)
        assert workspace.load_shift_timings() == () and dialog.use_button.isEnabled()
        assert workspace.editing.replay(redo=True)
        assert not dialog.use_button.isEnabled() and dialog.clear_button.isEnabled()
        assert path.read_bytes() == before
        dialog.accept()
        assert workspace.save()
        with AssessmentProjectFile.open(path) as project:
            assert project.load_shift_timings()[0].timing == dialog._model
    finally:
        dialog.deleteLater()
        workspace.close(choice=CloseChoice.DISCARD)
        _APP.processEvents()


@pytest.mark.parametrize(
    "shift,start,end",
    [
        ("Day", "12:00", "13:00"),
        ("Night", "00:00", "00:30"),
        ("Full", "23:00", "00:00"),
    ],
)
def test_break_entry_is_atomic_and_invalid_rows_block_replay(
    tmp_path: Path,
    shift: str,
    start: str,
    end: str,
) -> None:
    """Clock controls distinguish valid midnight from absent unfinished input.

    Args:
        tmp_path: Disposable native project directory.
        shift: Ordinary, overnight or 24-hour recurring Shift.
        start: Explicit break clock, including midnight.
        end: Explicit terminal break clock, including the next-day origin.

    Returns:
        None; incomplete/overlapping rows never partially replace saved timing.
    """
    workspace = timing_workspace(tmp_path)
    dialog = RotationTimingDialog(workspace, shift, load_icons())
    try:
        dialog._append_break()
        dialog._draft_pending = True
        name, first, last = dialog.break_rows[0]
        first.set_value(start)
        first.editingFinished.emit()
        assert workspace.load_shift_timings() == () and dialog.error.text()
        assert not dialog.prepare()
        name.setText("Meal break")
        last.set_value(end)
        last.editingFinished.emit()
        saved = workspace.load_shift_timings()[0].timing
        assert len(saved.breaks) == 1 and saved.breaks[0].name == "Meal break"
        assert sum(saved.block_minutes) == saved.productive_minutes
        revision = workspace.editing.history.revision
        dialog.subtract.click()
        assert not workspace.load_shift_timings()[0].timing.subtract_breaks
        assert workspace.editing.history.revision == revision + 1
        assert workspace.editing.replay(redo=False)
        assert dialog.subtract.isChecked()
        dialog._append_break()
        dialog._draft_pending = True
        _, first2, last2 = dialog.break_rows[1]
        first2.set_value(start)
        last2.set_value(end)
        last2.editingFinished.emit()
        assert dialog.error.text() and not dialog.prepare()
        assert workspace.load_shift_timings()[0].timing == saved
        dialog.break_table.setCurrentCell(1, 0)
        dialog.remove_break_button.click()
        assert dialog.prepare() and workspace.load_shift_timings()[0].timing == saved
    finally:
        dialog.deleteLater()
        workspace.close(choice=CloseChoice.DISCARD)
        _APP.processEvents()


def test_duration_drag_escape_and_keyboard_are_single_reversible_edits(
    tmp_path: Path,
) -> None:
    """A pointer preview writes nothing; release/arrow creates exactly one edit.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; mode/durations and view controls restore with the shared history cursor.
    """
    workspace = timing_workspace(tmp_path)
    dialog = RotationTimingDialog(workspace, "Day", load_icons())
    dialog.show()
    _APP.processEvents()
    try:
        dialog.use_button.click()
        original = workspace.load_shift_timings()[0].timing
        timeline = dialog.timeline
        start = QPoint(round(timeline._x(120)), 60)
        finish = QPoint(round(timeline._x(60)), 60)
        revision = workspace.editing.history.revision
        QTest.mousePress(timeline, Qt.MouseButton.LeftButton, pos=start)
        QTest.mouseMove(timeline, finish)
        assert workspace.load_shift_timings()[0].timing == original
        QTest.keyClick(timeline, Qt.Key.Key_Escape)
        QTest.mouseRelease(timeline, Qt.MouseButton.LeftButton, pos=finish)
        assert workspace.editing.history.revision == revision
        assert timeline.timing == original
        QTest.mousePress(timeline, Qt.MouseButton.LeftButton, pos=start)
        QTest.mouseMove(timeline, finish)
        QTest.mouseRelease(timeline, Qt.MouseButton.LeftButton, pos=finish)
        moved = workspace.load_shift_timings()[0].timing
        assert moved.block_minutes == (60, 180, 120, 120)
        assert workspace.editing.history.revision == revision + 1
        assert workspace.editing.replay(redo=False)
        assert dialog.equal_button.isChecked() and timeline.timing == original
        assert workspace.editing.replay(redo=True)
        assert dialog.unequal_button.isChecked() and timeline.timing == moved
        timeline._boundary = 1
        timeline.setFocus()
        QTest.keyClick(timeline, Qt.Key.Key_Right)
        assert workspace.load_shift_timings()[0].timing.block_minutes == (
            65,
            175,
            120,
            120,
        )
        spin = dialog.block_spins[0]
        spin.setValue(480)
        spin.editingFinished.emit()
        accepted = workspace.load_shift_timings()[0].timing
        assert not dialog.prepare() and spin.value() == 480
        assert workspace.load_shift_timings()[0].timing == accepted
        spin.setValue(70)
        spin.editingFinished.emit()
        assert dialog.prepare()
        assert workspace.load_shift_timings()[0].timing.block_minutes == (
            70,
            170,
            120,
            120,
        )
    finally:
        dialog.deleteLater()
        workspace.close(choice=CloseChoice.DISCARD)
        _APP.processEvents()


def test_clear_confirmation_and_organization_pending_clock_access(
    tmp_path: Path,
) -> None:
    """Pending clocks can open and clear the accepted timing template.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; pending metadata accepts after clear, then Undo restores both records.
    """
    workspace = timing_workspace(tmp_path)
    timing = RotationTimingDialog(workspace, "Day", load_icons())
    timing.use_button.click()
    saved = workspace.load_shift_timings()[0].timing
    with patch.object(QMessageBox, "question", return_value=QMessageBox.No):
        timing.clear_button.click()
    assert workspace.load_shift_timings()[0].timing == saved
    timing.accept()
    parent = OrganizationDialog(
        workspace, load_icons(), initial_entity=OrganizationKind.SHIFT
    )
    try:
        parent.select_keys(OrganizationKind.SHIFT, ("Day",))
        parent.editors["end_time"].set_value("17:00")
        assert not parent.accept_pending_entity()

        def clear_current(dialog: RotationTimingDialog) -> int:
            """Exercise the real child editor against accepted, not unfinished clocks.

            Args:
                dialog: Owned native timing modal borrowing the same project.

            Returns:
                Accepted after explicit removal, with parent fields untouched.
            """
            assert dialog.clock.span_minutes == 480
            with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
                dialog.clear_button.click()
            dialog.accept()
            return QDialog.Accepted

        with patch.object(RotationTimingDialog, "exec", clear_current):
            parent.rotation_timing_button.click()
        assert parent.editors["end_time"].clock_text() == "17:00"
        assert workspace.load_shift_timings() == ()
        assert parent.accept_pending_entity()
        assert workspace.editing.replay(redo=False)
        assert workspace.editing.replay(redo=False)
        assert workspace.load_shift_timings()[0].timing == saved
    finally:
        parent.deleteLater()
        timing.deleteLater()
        workspace.close(choice=CloseChoice.DISCARD)
        _APP.processEvents()


def test_real_enter_and_focused_close_keep_unequal_duration(tmp_path: Path) -> None:
    """Enter completes only the input; no hidden dialog default changes timing mode.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; focused native text is accepted before Close even without prior Enter.
    """
    workspace = timing_workspace(tmp_path)
    dialog = RotationTimingDialog(workspace, "Day", load_icons())
    dialog.show()
    _APP.processEvents()
    try:
        dialog.unequal_button.click()
        spin = dialog.block_spins[0]
        spin.setFocus()
        editor = spin.lineEdit()
        editor.selectAll()
        QTest.keyClicks(editor, "60")
        QTest.keyClick(editor, Qt.Key.Key_Return)
        assert dialog.isVisible() and dialog.unequal_button.isChecked()
        assert workspace.load_shift_timings()[0].timing.block_minutes == (
            60,
            180,
            120,
            120,
        )
        editor.selectAll()
        QTest.keyClicks(editor, "75")
        dialog.accept()
        assert workspace.load_shift_timings()[0].timing.block_minutes == (
            75,
            165,
            120,
            120,
        )
    finally:
        dialog.deleteLater()
        workspace.close(choice=CloseChoice.DISCARD)
        _APP.processEvents()


def test_unequal_count_confirmation_and_pending_cancel(tmp_path: Path) -> None:
    """Cancelling redistribution or unfinished input preserves accepted timing.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; Yes records one count change and No never sweeps away existing input.
    """
    workspace = timing_workspace(tmp_path)
    dialog = RotationTimingDialog(workspace, "Day", load_icons())
    dialog.show()
    _APP.processEvents()
    try:
        dialog.unequal_button.click()
        dialog.block_spins[0].setValue(60)
        dialog.block_spins[0].editingFinished.emit()
        original = workspace.load_shift_timings()[0].timing
        revision = workspace.editing.history.revision
        with patch.object(QMessageBox, "question", return_value=QMessageBox.No):
            dialog.count.setValue(2)
        assert dialog.count.value() == 4
        assert workspace.editing.history.revision == revision
        assert workspace.load_shift_timings()[0].timing == original
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            dialog.count.setValue(2)
        assert workspace.load_shift_timings()[0].timing.block_minutes == (240, 240)
        assert workspace.editing.history.revision == revision + 1
        assert workspace.editing.replay(redo=False)
        assert workspace.load_shift_timings()[0].timing == original
        dialog._append_break()
        dialog._draft_pending = True
        with patch.object(QMessageBox, "question", return_value=QMessageBox.No):
            dialog.reject()
        assert dialog.isVisible()
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            dialog.reject()
        assert not dialog.isVisible()
        assert workspace.load_shift_timings()[0].timing == original
    finally:
        dialog.deleteLater()
        workspace.close(choice=CloseChoice.DISCARD)
        _APP.processEvents()


def test_duration_completion_keeps_unfinished_break_and_accepts_whole_form(
    tmp_path: Path,
) -> None:
    """No duration acceptance may discard pending clocks in a different table.

    Args:
        tmp_path: Disposable project directory.

    Returns:
        None; correction accepts the complete break/duration proposal as one edit.
    """
    workspace = timing_workspace(tmp_path)
    dialog = RotationTimingDialog(workspace, "Day", load_icons())
    try:
        dialog.unequal_button.click()
        original = workspace.load_shift_timings()[0].timing
        revision = workspace.editing.history.revision
        dialog._append_break()
        dialog._draft_pending = True
        _, start, end = dialog.break_rows[0]
        start.set_value("12:00")
        dialog.block_spins[0].setValue(60)
        dialog.block_spins[0].editingFinished.emit()
        assert not dialog.prepare()
        assert len(dialog.break_rows) == 1 and start.clock_text() == "12:00"
        assert dialog.block_spins[0].value() == 60
        assert workspace.load_shift_timings()[0].timing == original
        assert workspace.editing.history.revision == revision
        end.set_value("13:00")
        assert dialog.prepare()
        saved = workspace.load_shift_timings()[0].timing
        assert saved.block_minutes == (60, 180, 60, 120)
        assert len(saved.breaks) == 1
        assert workspace.editing.history.revision == revision + 1
        assert workspace.editing.replay(redo=False)
        assert workspace.load_shift_timings()[0].timing == original
    finally:
        dialog.deleteLater()
        workspace.close(choice=CloseChoice.DISCARD)
        _APP.processEvents()


def test_multiple_pending_durations_require_correction_without_losing_input(
    tmp_path: Path,
) -> None:
    """A second duration cannot silently overwrite the first invalid cell draft.

    Args:
        tmp_path: Disposable project directory.

    Returns:
        None; correcting one token accepts the remaining one against neighboring work.
    """
    workspace = timing_workspace(tmp_path)
    dialog = RotationTimingDialog(workspace, "Day", load_icons())
    try:
        dialog.unequal_button.click()
        original = workspace.load_shift_timings()[0].timing
        revision = workspace.editing.history.revision
        dialog.block_spins[0].setValue(480)
        dialog.block_spins[0].editingFinished.emit()
        dialog.block_spins[1].setValue(80)
        dialog.block_spins[1].editingFinished.emit()
        assert not dialog.prepare()
        assert tuple(spin.value() for spin in dialog.block_spins) == (480, 80, 120, 120)
        assert workspace.load_shift_timings()[0].timing == original
        assert workspace.editing.history.revision == revision
        dialog.block_spins[0].setValue(120)
        dialog.block_spins[0].editingFinished.emit()
        assert dialog.prepare()
        assert workspace.load_shift_timings()[0].timing.block_minutes == (
            120,
            80,
            160,
            120,
        )
        assert workspace.editing.history.revision == revision + 1
    finally:
        dialog.deleteLater()
        workspace.close(choice=CloseChoice.DISCARD)
        _APP.processEvents()

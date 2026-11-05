"""Uniform work/break movement, removal and coordinated equality invariants."""

from pathlib import Path
from random import Random
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QCoreApplication, QEvent, QPoint, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.rotation_segments import (
    TimingSegment,
    from_timing_segments,
    move_timing_segment,
    redistribute_timing_segments,
    remove_timing_segment,
    resize_timing_boundary,
    timing_segments,
)
from ergotools.bootstrap import load_icons
from ergotools.domain.language import Language
from ergotools.domain.rotation_timing import RotationTiming
from ergotools.presentation.desktop.rotation_timing_dialog import RotationTimingDialog
from tests.test_rotation_timing_storage import timing_workspace

# Keep native ownership through deferred dialog cleanup and history notifications.
_APP = QApplication.instance() or QApplication([])


def example() -> RotationTiming:
    """Build the owner's alternating eight-hour screenshot as explicit segments.

    Args:
        None.

    Returns:
        365 productive minutes and 115 break minutes, with named pauses.
    """
    return from_timing_segments(
        (
            TimingSegment("work", 92),
            TimingSegment("break", 40, "Coffee"),
            TimingSegment("work", 91),
            TimingSegment("break", 40, "Lunch"),
            TimingSegment("work", 91),
            TimingSegment("break", 35, "Rest"),
            TimingSegment("work", 91),
        ),
        subtract_breaks=True,
    )


def assert_coverage(timing: RotationTiming) -> None:
    """Check independent per-minute coverage and one interval per numbered block.

    Args:
        timing: Complete candidate from any segment operation.

    Returns:
        None; every shift minute is exactly work or a break, never both.
    """
    minutes = [0] * timing.shift_minutes
    for block in timing.blocks():
        assert len(block.pieces) == 1
        for piece in block.pieces:
            for minute in range(piece.start, piece.end):
                minutes[minute] += 1
    breaks = {m for b in timing.breaks for m in range(b.interval.start, b.interval.end)}
    assert all(
        count == (0 if minute in breaks else 1) for minute, count in enumerate(minutes)
    )
    assert sum(timing.block_minutes) == timing.shift_minutes - len(breaks) > 0


@pytest.mark.parametrize(
    "index,expected", [(0, (132, 40, 35)), (3, (40, 40, 126)), (1, (86, 85, 35))]
)
def test_remove_work_extends_actual_neighbors(
    index: int, expected: tuple[int, ...]
) -> None:
    """Edge and interior work removal extend pauses instead of requiring deletion first.

    Args:
        index: Exact selected work ordinal.
        expected: Hand-computed neighboring break durations after sharing removed time.

    Returns:
        None; remaining work and break names stay positive and complete.
    """
    result = remove_timing_segment(example(), "work", index)
    assert tuple(b.interval.end - b.interval.start for b in result.breaks) == expected
    assert len(result.block_minutes) == 3 and result.shift_minutes == 480
    assert [b.name for b in result.breaks] == ["Coffee", "Lunch", "Rest"]
    assert_coverage(result)


def test_remove_break_and_move_first_work_to_end_keep_full_shift() -> None:
    """Removing pauses shares time; moving an edge block is a real reordering.

    Args:
        None.

    Returns:
        None; movement preserves all segment lengths and names.
    """
    source = example()
    removed = remove_timing_segment(source, "break", 0)
    assert removed.block_minutes == (112, 111, 91, 91)
    moved = move_timing_segment(source, "work", 0, 400)
    assert moved.block_minutes == (91, 91, 91, 92)
    assert moved.breaks[0].interval.start == 0
    assert sorted(
        (s.kind, s.minutes, s.name or "") for s in timing_segments(moved)
    ) == sorted((s.kind, s.minutes, s.name or "") for s in timing_segments(source))
    for value in (removed, moved):
        assert_coverage(value)


@pytest.mark.parametrize("equal_work", [False, True])
def test_equal_breaks_preserves_budget_and_cooperates_with_work(
    equal_work: bool,
) -> None:
    """Break equality retains the total budget and names, cooperating with work.

    Args:
        equal_work: Whether the work equality choice must also hold.

    Returns:
        None; unequal work is retained unless equalization was explicitly requested.
    """
    source = example()
    result = redistribute_timing_segments(
        source, work_count=4, break_count=3, equal_work=equal_work, equal_breaks=True
    )
    assert tuple(b.interval.end - b.interval.start for b in result.breaks) == (
        39,
        38,
        38,
    )
    assert result.productive_minutes == 365
    assert result.block_minutes == (
        (92, 91, 91, 91) if equal_work else source.block_minutes
    )
    assert [b.name for b in result.breaks] == ["Coffee", "Lunch", "Rest"]
    assert_coverage(result)


def test_mixed_operations_and_invalid_budgets_never_lose_coverage() -> None:
    """Repeated edits expose edge combinations beyond one scripted happy path.

    Args:
        None.

    Returns:
        None; every accepted proposal has positive, uninterrupted work coverage.
    """
    rng = Random(811)
    current = example()
    for _ in range(400):
        kind = rng.choice(("work", "break"))
        count = len(current.block_minutes if kind == "work" else current.breaks)
        if not count:
            continue
        index = rng.randrange(count)
        old = current
        try:
            if rng.choice((True, False)):
                current = move_timing_segment(current, kind, index, rng.randrange(480))
            else:
                current = remove_timing_segment(current, kind, index)
            assert_coverage(current)
        except ValueError:
            assert current == old
    with pytest.raises(ValueError):
        redistribute_timing_segments(
            example(), work_count=4, break_count=200, equal_work=True, equal_breaks=True
        )
    with pytest.raises(ValueError):
        resize_timing_boundary(example(), 1, 0)


@pytest.mark.parametrize("language", list(Language))
def test_native_move_remove_and_equal_breaks_shared_history(
    tmp_path: Path, language: Language
) -> None:
    """Actual controls support work movement/removal, pause equality and replay.

    Args:
        tmp_path: Private native project directory.
        language: Both maintained interface languages.

    Returns:
        None; No preserves data and mouse Undo restores the accepted prior timing.
    """
    workspace = timing_workspace(tmp_path)
    dialog = RotationTimingDialog(workspace, "Day", load_icons(), language)
    try:
        dialog.show()
        assert dialog._commit(example(), force=True)
        before = dialog._model
        dialog.block_table.setCurrentCell(3, 0)
        with patch.object(QMessageBox, "question", return_value=QMessageBox.No):
            dialog.remove_block()
        assert dialog._model == before
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            dialog.remove_block()
        assert dialog._model.breaks[-1].interval.end == 480
        QTest.mouseClick(dialog.history.undo_button, Qt.LeftButton)
        assert dialog._model == before
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            dialog.equal_break_button.click()
        assert tuple(
            b.interval.end - b.interval.start for b in dialog._model.breaks
        ) == (39, 38, 38)
        assert dialog.break_count.value() == 3 and dialog.equal_break_button.isChecked()
        assert (
            dialog.count.geometry().height() == dialog.break_count.geometry().height()
        )
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            dialog.break_count.setValue(2)
        assert (
            len(dialog._model.breaks) == 2 and dialog._model.productive_minutes == 365
        )
        timeline = dialog.timeline
        timeline.set_tool("move")
        start = QPoint(round(timeline._x(30)), 60)
        end = QPoint(round(timeline._x(450)), 60)
        before_move = dialog._model
        QTest.mousePress(timeline, Qt.LeftButton, pos=start)
        QTest.mouseMove(timeline, end)
        QTest.mouseRelease(timeline, Qt.LeftButton, pos=end)
        assert dialog._model != before_move
        assert_coverage(dialog._model)
        QTest.mouseClick(dialog.history.undo_button, Qt.LeftButton)
        assert dialog._model == before_move
    finally:
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        workspace.close(choice=CloseChoice.DISCARD)

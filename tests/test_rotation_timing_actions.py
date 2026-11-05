"""Visual timing proposals preserve positive work and explicit break semantics."""

import pytest

from ergotools.application.rotation_timing_actions import (
    change_timing_break,
    draw_timing_break,
    join_timing_breaks,
    join_work_blocks,
    remove_work_block,
    split_work_block,
)
from ergotools.domain.rotation_timing import MinuteInterval, TimedBreak, equal_timing


def test_split_join_remove_keep_all_work_and_other_boundaries() -> None:
    """A block removal joins minutes instead of deleting work or creating a break.

    Args:
        None.

    Returns:
        None; independent hand-calculated durations and complete coverage stay exact.
    """
    original = equal_timing(480, 4)
    split = split_work_block(original, 60)
    assert split.block_minutes == (60, 60, 120, 120, 120)
    assert join_work_blocks(split, 1).block_minutes == original.block_minutes
    assert remove_work_block(split, 0).block_minutes == original.block_minutes
    assert remove_work_block(original, 3).block_minutes == (120, 120, 240)
    assert sum(p.end - p.start for b in split.blocks() for p in b.pieces) == 480
    for clock in (0, 120, 480):
        with pytest.raises(ValueError):
            split_work_block(original, clock)
    with pytest.raises(ValueError):
        remove_work_block(equal_timing(480, 1), 0)


def test_break_create_move_resize_remove_and_invalid_proposals_are_atomic() -> None:
    """Pause edits preserve independent cuts and make uninterrupted work blocks.

    Args:
        None.

    Returns:
        None; no break minute is assigned work and invalid overlaps retain the original.
    """
    original = equal_timing(480, 4)
    paused = draw_timing_break(original, 180, 210)
    assert paused.block_minutes == (120, 60, 30, 120, 120)
    assert not paused.equal_blocks and all(len(b.pieces) == 1 for b in paused.blocks())
    assert paused.productive_minutes == paused.averaging_minutes == 450
    moved = change_timing_break(paused, 0, TimedBreak(MinuteInterval(210, 240), "Meal"))
    resized = change_timing_break(
        moved, 0, TimedBreak(MinuteInterval(210, 255), "Meal")
    )
    assert resized.productive_minutes == 435
    assert change_timing_break(resized, 0, None).block_minutes == (120, 113, 127, 120)
    for b in resized.blocks():
        assert all(p.end <= 210 or p.start >= 255 for p in b.pieces)
    with pytest.raises(ValueError):
        draw_timing_break(resized, 240, 270)
    with pytest.raises(ValueError):
        split_work_block(resized, 230)
    with pytest.raises(ValueError):
        draw_timing_break(original, 0, 480)
    assert original == equal_timing(480, 4)


def test_only_touching_breaks_join_without_removing_intervening_work() -> None:
    """Combining adjacent pauses preserves their literal names and productive minutes.

    Args:
        None.

    Returns:
        None; no implicit break is created across a real working gap.
    """
    first = TimedBreak(MinuteInterval(100, 110), "Coffee")
    second = TimedBreak(MinuteInterval(110, 120), "Rest")
    original = equal_timing(480, 4, (first, second))
    joined = join_timing_breaks(original, 0)
    assert joined.breaks == (TimedBreak(MinuteInterval(100, 120), "Coffee / Rest"),)
    assert joined.block_minutes == original.block_minutes
    separated = equal_timing(480, 4, (first, TimedBreak(MinuteInterval(115, 125))))
    with pytest.raises(ValueError):
        join_timing_breaks(separated, 0)


def test_split_at_either_break_edge_preserves_the_same_productive_cut() -> None:
    """A break edge is a valid interior work-budget cut, not a minute of break work.

    Args:
        None.

    Returns:
        None; the two clock edges refer to the same productive offset.
    """
    original = equal_timing(180, 1, (TimedBreak(MinuteInterval(60, 120)),))
    left, right = split_work_block(original, 60), split_work_block(original, 120)
    assert left == right and left.block_minutes == (60, 60)
    assert left.blocks()[0].pieces == (MinuteInterval(0, 60),)
    assert left.blocks()[1].pieces == (MinuteInterval(120, 180),)

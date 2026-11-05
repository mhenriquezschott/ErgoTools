"""Independent minute-grid oracles for Shift timing, not optimizer-status assertions.

Pure tests enumerate individual work/break minutes and compare projected pieces to an
independent set oracle. No scientific probabilities, recovery model or database is used.
"""

from dataclasses import replace
from fractions import Fraction

import pytest

from ergotools.application.rotation_timing import ShiftClock, clock_minute, edit_timing
from ergotools.domain.rotation_timing import (
    MinuteInterval,
    TimedBreak,
    equal_minutes,
    equal_timing,
    move_block_boundary,
)


def test_lunch_split_matches_hand_derived_140_minute_blocks() -> None:
    """An 8-hour shift minus lunch divides into three 140-minute assignments.

    Args:
        None.

    Returns:
        None; exact clock pieces show that one block crosses the entire lunch gap.
    """
    timing = equal_timing(480, 3, (TimedBreak(MinuteInterval(240, 300), "Lunch"),))
    assert timing.block_minutes == (140, 140, 140)
    assert tuple(b.pieces for b in timing.blocks()) == (
        (MinuteInterval(0, 140),),
        (MinuteInterval(140, 240), MinuteInterval(300, 340)),
        (MinuteInterval(340, 480),),
    )
    assert timing.averaging_minutes == 420
    retained = replace(timing, subtract_breaks=False)
    assert retained.blocks() == timing.blocks() and retained.averaging_minutes == 480
    assert Fraction(50 * timing.productive_minutes, timing.averaging_minutes) == 50
    assert Fraction(
        50 * retained.productive_minutes, retained.averaging_minutes
    ) == Fraction(175, 4)


def test_small_minute_grid_exhaustively_covers_work_once() -> None:
    """Enumerate tiny shifts/breaks/counts with an independent integer-minute oracle.

    Args:
        None.

    Returns:
        None; all work appears exactly once, no break work appears, and totals agree.
    """
    cases = 0
    for span in range(1, 13):
        alternatives = [
            (),
            *(
                (TimedBreak(MinuteInterval(a, b)),)
                for a in range(span)
                for b in range(a + 1, span + 1)
                if b - a < span
            ),
        ]
        for pauses in alternatives:
            unavailable = {
                m for p in pauses for m in range(p.interval.start, p.interval.end)
            }
            work = set(range(span)) - unavailable
            for count in range(1, min(4, len(work)) + 1):
                timing = equal_timing(span, count, pauses)
                seen = []
                for block, budget in zip(
                    timing.blocks(), timing.block_minutes, strict=True
                ):
                    minutes = [
                        m
                        for piece in block.pieces
                        for m in range(piece.start, piece.end)
                    ]
                    assert len(minutes) == budget and budget > 0
                    seen.extend(minutes)
                assert set(seen) == work and len(seen) == len(work)
                for elapsed in range(span + 1):
                    assert timing.productive_offset(elapsed) == len(
                        {m for m in work if m < elapsed}
                    )
                cases += 1
    assert cases > 1000


def test_equal_remainder_boundary_edits_and_break_changes() -> None:
    """Remainders are explicit, and moving one cut changes only its neighbors.

    Args:
        None.

    Returns:
        None; unequal prefix retention, final remainder and source immutability hold.
    """
    assert equal_minutes(481, 4) == (121, 120, 120, 120)
    original = equal_timing(480, 4)
    unequal = move_block_boundary(original, 1, 60)
    assert unequal.block_minutes == (60, 180, 120, 120)
    assert not unequal.equal_blocks and original.block_minutes == (120,) * 4
    pause = (TimedBreak(MinuteInterval(240, 255)),)
    revised = edit_timing(unequal, pause, 4, equal=False, subtract_breaks=False)
    assert revised.block_minutes == (60, 180, 120, 105)
    assert revised.averaging_minutes == 480
    changed_count = edit_timing(revised, pause, 3, equal=False, subtract_breaks=True)
    assert changed_count.equal_blocks and changed_count.block_minutes == (155,) * 3


@pytest.mark.parametrize("minute", ["8:00", "24:00", "08:60", "", "08.00", "aa:00"])
def test_clock_rejects_ambiguous_or_incomplete_input(minute: str) -> None:
    """Whole canonical clocks have no implicit locale, rounding or missing defaults.

    Args:
        minute: Invalid 24-hour input.

    Returns:
        None; parsing fails without manufacturing a time.
    """
    with pytest.raises(ValueError):
        clock_minute(minute)


def test_overnight_and_full_day_clocks_keep_next_day_meaning() -> None:
    """Midnight and terminal repeated clocks differ from missing time.

    Args:
        None.

    Returns:
        None; relative minutes and explicit next-day labels remain exact.
    """
    night = ShiftClock(clock_minute("22:00"), 480)
    assert night.offset("01:00") == 180 and night.label(480) == "06:00 (+1)"
    full = ShiftClock(clock_minute("08:00"), 1440)
    assert full.offset("08:00") == 0 and full.offset("08:00", end=True) == 1440
    assert full.label(1440) == "08:00 (+1)"


@pytest.mark.parametrize(
    "case",
    [
        "overlap",
        "outside",
        "all_break",
        "zero_block",
        "missing_work",
        "false_equal",
        "bool_minutes",
        "bool_option",
    ],
)
def test_invalid_timing_rejects_without_partial_projection(case: str) -> None:
    """Malformed collections cannot create zero-duration or overlapping assignments.

    Args:
        case: Explicit inconsistent whole-timing input.

    Returns:
        None; no valid partial timing is returned.
    """
    base = equal_timing(10, 2)
    changes = {
        "overlap": {
            "breaks": (
                TimedBreak(MinuteInterval(1, 4)),
                TimedBreak(MinuteInterval(3, 5)),
            )
        },
        "outside": {"breaks": (TimedBreak(MinuteInterval(8, 11)),)},
        "all_break": {"breaks": (TimedBreak(MinuteInterval(0, 10)),)},
        "zero_block": {"block_minutes": (0, 10)},
        "missing_work": {"block_minutes": (4, 5)},
        "false_equal": {"block_minutes": (1, 9)},
        "bool_minutes": {"shift_minutes": True},
        "bool_option": {"subtract_breaks": 1},
    }
    with pytest.raises(ValueError):
        replace(base, **changes[case])


@pytest.mark.parametrize(
    "boundary,offset", [(0, 5), (2, 5), (1, 0), (1, 10), (True, 3)]
)
def test_boundary_rejects_removal_crossing_or_boolean_identity(
    boundary: int, offset: int
) -> None:
    """Positive neighboring blocks survive every accepted boundary edit.

    Args:
        boundary: Invalid/noninterior boundary identity.
        offset: Proposed cumulative productive-minute cut.

    Returns:
        None; complete original timing remains exact.
    """
    original = equal_timing(10, 2)
    with pytest.raises(ValueError):
        move_block_boundary(original, boundary, offset)
    assert original.block_minutes == (5, 5)


def test_adjacent_boundary_breaks_and_minute_capacity() -> None:
    """Adjacent/end pauses create no empty work, including a full day of minute blocks.

    Args:
        None.

    Returns:
        None; every projected piece is positive and its exact total covers all work.
    """
    timing = equal_timing(
        10,
        2,
        (
            TimedBreak(MinuteInterval(0, 2)),
            TimedBreak(MinuteInterval(2, 3)),
            TimedBreak(MinuteInterval(8, 10)),
        ),
    )
    assert tuple(b.pieces for b in timing.blocks()) == (
        (MinuteInterval(3, 6),),
        (MinuteInterval(6, 8),),
    )
    full = equal_timing(1440, 1440)
    assert len(full.blocks()) == 1440
    assert full.blocks()[-1].pieces == (MinuteInterval(1439, 1440),)

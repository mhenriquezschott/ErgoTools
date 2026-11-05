"""Complete work/break editing proposals shared by graphical and manual timing hosts.

Application layer. Operations preserve complete positive work coverage and the existing
clock-cut policy. No solver, scientific model, repository or new stored fields.
"""

from dataclasses import replace
from itertools import pairwise

from ergotools.application.rotation_segments import (
    redistribute_timing_segments,
    remove_timing_segment,
)
from ergotools.domain.rotation_timing import (
    MinuteInterval,
    RotationTiming,
    TimedBreak,
    equal_minutes,
    equal_timing,
)


def split_work_block(timing: RotationTiming, elapsed: int) -> RotationTiming:
    """Split the working block at an interior whole-minute clock position.

    Args:
        timing: Complete accepted timing, retained on invalid input.
        elapsed: Shift-relative clock offset; breaks and existing cuts are ineligible.

    Returns:
        Unequal-mode timing with two positive pieces replacing exactly one block.

    Raises:
        ValueError: The clock lies in a break, at an edge or on an existing cut.
    """
    offset = timing.productive_offset(elapsed)
    if any(p.interval.start < elapsed < p.interval.end for p in timing.breaks):
        raise ValueError("Split inside a work block, not inside a break.")
    before = 0
    for index, minutes in enumerate(timing.block_minutes):
        after = before + minutes
        if before < offset < after:
            values = (
                *timing.block_minutes[:index],
                offset - before,
                after - offset,
                *timing.block_minutes[index + 1 :],
            )
            return replace(timing, block_minutes=values, equal_blocks=False)
        before = after
    raise ValueError("Split inside a work block, away from an existing boundary.")


def join_work_blocks(timing: RotationTiming, boundary: int) -> RotationTiming:
    """Remove one interior cut while retaining every productive minute.

    Args:
        timing: Original complete timing.
        boundary: One-based cut between the neighboring blocks to join.

    Returns:
        Unequal-mode timing; the two neighboring durations are summed.

    Raises:
        ValueError: No such interior boundary exists.
    """
    if type(boundary) is not int or not 1 <= boundary < len(timing.block_minutes):
        raise ValueError("Choose a boundary between two work blocks to join.")
    blocks = separate_work_blocks(timing).blocks()
    if len(blocks) != len(timing.block_minutes):
        raise ValueError("Separate interrupted blocks before joining them.")
    if blocks[boundary - 1].pieces[-1].end != blocks[boundary].pieces[0].start:
        raise ValueError("Remove the break before joining these work blocks.")
    values = (
        *timing.block_minutes[: boundary - 1],
        sum(timing.block_minutes[boundary - 1 : boundary + 1]),
        *timing.block_minutes[boundary + 1 :],
    )
    return replace(timing, block_minutes=values, equal_blocks=False)


def remove_work_block(timing: RotationTiming, index: int) -> RotationTiming:
    """Remove work and extend its immediate neighbors to cover the freed time.

    Args:
        timing: Original complete timing.
        index: Zero-based selected block.

    Returns:
        Same shift span; either neighboring work or breaks may expand. The host
        confirms changes to the total working-time budget.

    Raises:
        ValueError: Selection is invalid or this is the sole remaining work block.
    """
    return remove_timing_segment(timing, "work", index)


def change_timing_break(
    timing: RotationTiming,
    index: int | None,
    replacement: TimedBreak | None,
) -> RotationTiming:
    """Edit a pause while preserving independent work cuts and uninterrupted blocks.

    Args:
        timing: Original complete timing with canonical productive coverage.
        index: Existing zero-based break, or None to add one.
        replacement: New typed break; None removes the selected existing break.

    Returns:
        Complete proposal retaining averaging policy and independent clock cuts.

    Raises:
        ValueError: Selection, overlap, bounds or remaining productive budgets fail.
    """
    values = list(timing.breaks)
    if index is None:
        if replacement is None:
            raise ValueError("Choose a positive break interval.")
        values.append(replacement)
    else:
        if type(index) is not int or not 0 <= index < len(values):
            raise ValueError("Select a break first.")
        if replacement is None:
            return remove_timing_segment(timing, "break", index)
        else:
            values[index] = replacement
    return edit_contiguous_breaks(
        timing, tuple(sorted(values, key=lambda p: p.interval.start))
    )


def draw_timing_break(timing: RotationTiming, start: int, end: int) -> RotationTiming:
    """Prepare a positive graphical break without guessing clocks or saving data.

    Args:
        timing: Complete current plan.
        start: Shift-relative start minute.
        end: Shift-relative end minute after start.

    Returns:
        Complete new-break proposal using the same rules as manual fields.

    Raises:
        ValueError: Interval overlaps a break or cannot retain positive work blocks.
    """
    return change_timing_break(timing, None, TimedBreak(MinuteInterval(start, end)))


def join_timing_breaks(timing: RotationTiming, index: int) -> RotationTiming:
    """Join touching breaks without turning an intervening work interval into a pause.

    Args:
        timing: Complete original plan.
        index: Zero-based selected break; prefer its next touching neighbor.

    Returns:
        Same work coverage with touching intervals and optional names combined.

    Raises:
        ValueError: No touching neighbor exists or selection is invalid.
    """
    if type(index) is not int or not 0 <= index < len(timing.breaks):
        raise ValueError("Select a break first.")
    pauses = timing.breaks
    left = index
    if (
        index + 1 >= len(pauses)
        or pauses[index].interval.end != pauses[index + 1].interval.start
    ):
        left = index - 1
    if left < 0 or pauses[left].interval.end != pauses[left + 1].interval.start:
        raise ValueError(
            "Join only touching breaks; work between breaks must remain work."
        )
    first, last = pauses[left : left + 2]
    names = tuple(dict.fromkeys(p.name for p in (first, last) if p.name))
    combined = TimedBreak(
        MinuteInterval(first.interval.start, last.interval.end),
        " / ".join(names) or None,
    )
    return replace(timing, breaks=(*pauses[:left], combined, *pauses[left + 2 :]))


def separate_work_blocks(timing: RotationTiming) -> RotationTiming:
    """Give every uninterrupted work interval its own chronological block identity.

    Args:
        timing: Complete timing, including compatible older interrupted budgets.

    Returns:
        Equivalent minute coverage with one piece per block; unequal results cannot
        retain the Equal flag. No break, duration, name or averaging basis is lost.
    """
    values = tuple(p.end - p.start for b in timing.blocks() for p in b.pieces)
    return replace(
        timing,
        block_minutes=values,
        equal_blocks=timing.equal_blocks
        and values == equal_minutes(timing.productive_minutes, len(values)),
    )


def edit_contiguous_breaks(
    previous: RotationTiming, breaks: tuple[TimedBreak, ...]
) -> RotationTiming:
    """Edit pauses while preserving real work-to-work cuts and splitting at breaks.

    Args:
        previous: Complete accepted clock coverage, never modified in place.
        breaks: Proposed ordered pauses with exact clocks and optional names.

    Returns:
        One block per uninterrupted segment. Adding an interior break splits work;
        removing it rejoins neighboring work unless an independent cut remains.

    Raises:
        ValueError: Pauses overlap, escape the shift or leave no productive work.
    """
    probe = equal_timing(
        previous.shift_minutes, 1, breaks, subtract_breaks=previous.subtract_breaks
    )
    blocks = separate_work_blocks(previous).blocks()
    cuts = {
        left.pieces[0].end
        for left, right in pairwise(blocks)
        if left.pieces[0].end == right.pieces[0].start
    }
    values: list[int] = []
    for piece in probe.blocks()[0].pieces:
        points = (
            piece.start,
            *sorted(c for c in cuts if piece.start < c < piece.end),
            piece.end,
        )
        values.extend(right - left for left, right in pairwise(points))
    budgets = tuple(values)
    return RotationTiming(
        previous.shift_minutes,
        breaks,
        budgets,
        previous.equal_blocks
        and budgets == equal_minutes(probe.productive_minutes, len(budgets)),
        previous.subtract_breaks,
    )


def equalize_contiguous_timing(timing: RotationTiming, count: int) -> RotationTiming:
    """Distribute work equally and relocate pauses only to work-block boundaries.

    Args:
        timing: Complete timing retaining break order, names and durations.
        count: Explicit number of positive work blocks.

    Returns:
        Canonical equal budgets with uninterrupted work and evenly spaced break cuts.

    Raises:
        ValueError: Requested positive minute budgets are impossible.
    """
    return redistribute_timing_segments(
        timing,
        work_count=count,
        break_count=len(timing.breaks),
        equal_work=True,
        equal_breaks=False,
    )

"""Uniform work/break segment operations for the rotation editor.

Application layer. Every segment has positive duration and every shift minute belongs
exactly once to work or a pause. Ports/history/storage remain with the existing hosts.
"""

from dataclasses import dataclass, replace

from ergotools.domain.rotation_timing import (
    MinuteInterval,
    RotationTiming,
    TimedBreak,
    equal_minutes,
)


@dataclass(frozen=True, slots=True)
class TimingSegment:
    """One uninterrupted editor interval, in chronological sequence.

    Attributes:
        kind: work or break; work has no descriptive metadata.
        minutes: Strictly positive whole-minute duration.
        name: Optional literal break name.
    """

    kind: str
    minutes: int
    name: str | None = None

    def __post_init__(self) -> None:
        """Validate a complete segment without accepting any project mutation.

        Args:
            None.

        Returns:
            None after typed validation.

        Raises:
            ValueError: Kind, duration or name is invalid.
        """
        if (
            self.kind not in ("work", "break")
            or type(self.minutes) is not int
            or self.minutes < 1
        ):
            raise ValueError("Segments need a valid kind and positive whole minutes.")
        if self.name is not None and (
            self.kind != "break"
            or not isinstance(self.name, str)
            or not self.name.strip()
        ):
            raise ValueError("Only breaks may have nonempty names.")


def timing_segments(timing: RotationTiming) -> tuple[TimingSegment, ...]:
    """Read chronological work pieces and breaks without changing compatible data.

    Args:
        timing: Existing complete relative timing.

    Returns:
        Complete ordered segment coverage, including distinct adjacent work blocks.
    """
    positioned = [
        (p.start, TimingSegment("work", p.end - p.start))
        for b in timing.blocks()
        for p in b.pieces
    ]
    positioned.extend(
        (
            b.interval.start,
            TimingSegment("break", b.interval.end - b.interval.start, b.name),
        )
        for b in timing.breaks
    )
    return tuple(segment for _, segment in sorted(positioned, key=lambda row: row[0]))


def from_timing_segments(
    values: tuple[TimingSegment, ...],
    *,
    subtract_breaks: bool,
    equal_work: bool = False,
) -> RotationTiming:
    """Encode complete segments using the existing portable timing model.

    Args:
        values: Positive chronological work/break segments.
        subtract_breaks: Existing averaging-basis choice.
        equal_work: Retain Equal mode only if actual work budgets are canonical.

    Returns:
        Existing typed timing with one uninterrupted interval per work block.

    Raises:
        ValueError: No work remains or total daily span exceeds the supported range.
    """
    work = tuple(s.minutes for s in values if s.kind == "work")
    if not work:
        raise ValueError("Keep at least one work block in the shift.")
    pauses = []
    cursor = 0
    for segment in values:
        if segment.kind == "break":
            pauses.append(
                TimedBreak(
                    MinuteInterval(cursor, cursor + segment.minutes), segment.name
                )
            )
        cursor += segment.minutes
    return RotationTiming(
        cursor,
        tuple(pauses),
        work,
        equal_work and work == equal_minutes(sum(work), len(work)),
        subtract_breaks,
    )


def segment_position(timing: RotationTiming, kind: str, index: int) -> int:
    """Resolve an exact work/break ordinal to its chronological segment position.

    Args:
        timing: Complete original plan.
        kind: work or break.
        index: Zero-based ordinal within that kind.

    Returns:
        Zero-based position in the chronological sequence.

    Raises:
        ValueError: Selection is absent or invalid.
    """
    positions = [i for i, s in enumerate(timing_segments(timing)) if s.kind == kind]
    if type(index) is not int or not 0 <= index < len(positions):
        raise ValueError("Select an existing work block or break.")
    return positions[index]


def remove_timing_segment(
    timing: RotationTiming, kind: str, index: int
) -> RotationTiming:
    """Remove a segment and extend immediate neighbors to cover its clock space.

    Args:
        timing: Complete original timing.
        kind: work or break.
        index: Selected ordinal within that kind.

    Returns:
        Same full shift span; at an edge the sole neighbor absorbs all time, while
        interior neighbors share it, with the odd extra minute going left.

    Raises:
        ValueError: Selection is invalid or removal would eliminate all work.
    """
    values = list(timing_segments(timing))
    position = segment_position(timing, kind, index)
    if kind == "work" and sum(s.kind == "work" for s in values) == 1:
        raise ValueError("Keep at least one work block in the shift.")
    removed = values.pop(position)
    if position == 0:
        values[0] = replace(values[0], minutes=values[0].minutes + removed.minutes)
    elif position == len(values):
        values[-1] = replace(values[-1], minutes=values[-1].minutes + removed.minutes)
    else:
        left = (removed.minutes + 1) // 2
        values[position - 1] = replace(
            values[position - 1], minutes=values[position - 1].minutes + left
        )
        values[position] = replace(
            values[position], minutes=values[position].minutes + removed.minutes - left
        )
    return from_timing_segments(
        tuple(values),
        subtract_breaks=timing.subtract_breaks,
        equal_work=timing.equal_blocks,
    )


def resize_timing_boundary(
    timing: RotationTiming, boundary: int, elapsed: int
) -> RotationTiming:
    """Resize any adjacent pair without crossing or deleting a positive segment.

    Args:
        timing: Complete original sequence.
        boundary: Interior chronological cut, one based.
        elapsed: Proposed whole-minute relative clock.

    Returns:
        Same shift span and ordered metadata, with only neighboring durations changed.

    Raises:
        ValueError: Boundary or clock would empty/cross a segment.
    """
    values = list(timing_segments(timing))
    if (
        type(boundary) is not int
        or not 0 < boundary < len(values)
        or type(elapsed) is not int
    ):
        raise ValueError("Choose an interior segment boundary.")
    start = sum(s.minutes for s in values[: boundary - 1])
    end = start + values[boundary - 1].minutes + values[boundary].minutes
    if not start < elapsed < end:
        raise ValueError("Keep at least one minute in both neighboring segments.")
    values[boundary - 1] = replace(values[boundary - 1], minutes=elapsed - start)
    values[boundary] = replace(values[boundary], minutes=end - elapsed)
    return from_timing_segments(
        tuple(values),
        subtract_breaks=timing.subtract_breaks,
        equal_work=timing.equal_blocks,
    )


def move_timing_segment(
    timing: RotationTiming, kind: str, index: int, start: int
) -> RotationTiming:
    """Move work or a pause within neighbors, or reorder it when dragged past them.

    Args:
        timing: Frozen gesture origin.
        kind: work or break.
        index: Kind-relative ordinal at press.
        start: Requested new clock start, derived from pointer delta.

    Returns:
        Complete coverage. Local movement keeps selected length and borrows from its
        two neighbors; crossing them reorders whole segments without changing lengths.

    Raises:
        ValueError: Selection is invalid or no meaningful movement is possible.
    """
    if type(start) is not int:
        raise ValueError("Use a whole-minute segment start.")
    values = list(timing_segments(timing))
    position = segment_position(timing, kind, index)
    segment = values[position]
    before = sum(s.minutes for s in values[:position])
    if start == before:
        return timing
    if 0 < position < len(values) - 1:
        lower = before - values[position - 1].minutes + 1
        upper = before + values[position + 1].minutes - 1
        if lower <= start <= upper:
            delta = start - before
            values[position - 1] = replace(
                values[position - 1], minutes=values[position - 1].minutes + delta
            )
            values[position + 1] = replace(
                values[position + 1], minutes=values[position + 1].minutes - delta
            )
            return from_timing_segments(
                tuple(values),
                subtract_breaks=timing.subtract_breaks,
                equal_work=timing.equal_blocks,
            )
    center = start + segment.minutes / 2
    centers = []
    cursor = 0
    for i, item in enumerate(values):
        if i != position:
            centers.append(cursor + item.minutes / 2)
        cursor += item.minutes
    target = sum(c <= center for c in centers)
    values.pop(position)
    values.insert(target, segment)
    return from_timing_segments(
        tuple(values),
        subtract_breaks=timing.subtract_breaks,
        equal_work=timing.equal_blocks,
    )


def redistribute_timing_segments(
    timing: RotationTiming,
    *,
    work_count: int,
    break_count: int,
    equal_work: bool,
    equal_breaks: bool,
    break_minutes: int | None = None,
) -> RotationTiming:
    """Coordinate count/equality changes while preserving the other time budget.

    Args:
        timing: Complete source, retaining break names in chronological order.
        work_count: Desired positive work count.
        break_count: Desired nonnegative break count.
        equal_work: Redistribute total work equally when True.
        equal_breaks: Redistribute total pause time equally when True.
        break_minutes: Explicit new total pause budget, otherwise retain the old total;
            zero breaks explicitly restores all time to work.

    Returns:
        Whole-minute allocation with unchanged total shift length. Unchanged counts keep
        segment order; changed counts distribute breaks among the work gaps. Extra
        pauses may be adjacent rather than silently deleted or forcing new work blocks.

    Raises:
        ValueError: Counts or budgets cannot keep every requested segment positive.
    """
    timing = from_timing_segments(
        timing_segments(timing),
        subtract_breaks=timing.subtract_breaks,
        equal_work=timing.equal_blocks,
    )
    if (
        type(equal_work) is not bool
        or type(equal_breaks) is not bool
        or (
            break_minutes is not None
            and (
                type(break_minutes) is not int
                or not 0 <= break_minutes < timing.shift_minutes
            )
        )
    ):
        raise ValueError(
            "Use explicit equality choices and a valid total break budget."
        )
    if (
        type(work_count) is not int
        or work_count < 1
        or type(break_count) is not int
        or break_count < 0
    ):
        raise ValueError("Use a positive work count and a nonnegative break count.")
    total = (
        timing.shift_minutes - timing.productive_minutes
        if break_minutes is None
        else break_minutes
    )
    total = total if break_count else 0
    work_total = timing.shift_minutes - total
    old_breaks = tuple(b.interval.end - b.interval.start for b in timing.breaks)
    work = (
        equal_minutes(work_total, work_count)
        if equal_work or work_count != len(timing.block_minutes)
        else (*timing.block_minutes[:-1], work_total - sum(timing.block_minutes[:-1]))
    )
    breaks = (
        equal_minutes(total, break_count)
        if break_count and (equal_breaks or break_count != len(old_breaks))
        else ((*old_breaks[:-1], total - sum(old_breaks[:-1])) if break_count else ())
    )
    work_values = [TimingSegment("work", n) for n in work]
    break_values = [
        TimingSegment(
            "break", n, timing.breaks[i].name if i < len(timing.breaks) else None
        )
        for i, n in enumerate(breaks)
    ]
    if work_count == len(timing.block_minutes) and break_count == len(timing.breaks):
        wi = bi = 0
        result = []
        for segment in timing_segments(timing):
            if segment.kind == "work":
                result.append(work_values[wi])
                wi += 1
            else:
                result.append(break_values[bi])
                bi += 1
    else:
        result = []
        cursor = 0
        for i, item in enumerate(work_values):
            result.append(item)
            until = (
                ((i + 1) * break_count // (work_count - 1))
                if work_count > 1 and i < work_count - 1
                else break_count
            )
            result.extend(break_values[cursor:until])
            cursor = until
    return from_timing_segments(
        tuple(result), subtract_breaks=timing.subtract_breaks, equal_work=equal_work
    )

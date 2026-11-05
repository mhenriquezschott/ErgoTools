"""Minute-exact work/break timing, independent of risk models and optimization.

Domain layer. Timings partition productive minutes into positive blocks and project
those blocks into local-clock pieces around shared breaks. No recovery, repetitions,
dose, timezone conversion, database or solver behavior is implied by these values.
"""

from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class MinuteInterval:
    """One positive half-open interval in minutes relative to the shift start.

    Attributes:
        start: Inclusive minute offset, including zero.
        end: Exclusive minute offset, at most 1440 for a daily shift.
    """

    start: int
    end: int

    def __post_init__(self) -> None:
        """Reject fractional, Boolean, negative or empty daily intervals.

        Args:
            None.

        Returns:
            None after validating exact minute endpoints.

        Raises:
            ValueError: Endpoints do not describe a positive daily interval.
        """
        if (
            type(self.start) is not int
            or type(self.end) is not int
            or not (0 <= self.start < self.end <= 1440)
        ):
            raise ValueError("Use positive whole-minute intervals inside the shift.")


@dataclass(frozen=True, slots=True)
class TimedBreak:
    """A shared break interval with optional literal user text.

    Attributes:
        interval: Nonworking minutes relative to shift start.
        name: Optional activity label; not an ergonomic coefficient.
    """

    interval: MinuteInterval
    name: str | None = None

    def __post_init__(self) -> None:
        """Validate typed endpoints and optional descriptive text.

        Args:
            None.

        Returns:
            None; no interval sorting or inference occurs.

        Raises:
            ValueError: Interval is untyped or a supplied name is not nonblank text.
        """
        if not isinstance(self.interval, MinuteInterval) or (
            self.name is not None
            and (not isinstance(self.name, str) or not self.name.strip())
        ):
            raise ValueError("Break requires a valid interval and optional name.")


@dataclass(frozen=True, slots=True)
class WorkBlock:
    """Projected pieces belonging to one block's unchanged Job assignment.

    Attributes:
        index: Zero-based chronological block index.
        pieces: Ordered working intervals; gaps are breaks, never assigned work.
    """

    index: int
    pieces: tuple[MinuteInterval, ...]


@dataclass(frozen=True, slots=True)
class RotationTiming:
    """Complete relative-minute template with explicit averaging-basis policy.

    Attributes:
        shift_minutes: Full daily elapsed local-clock interval, 1-1440 minutes.
        breaks: Ordered nonoverlapping shared break intervals inside the shift.
        block_minutes: Positive productive minutes per block; sum covers all work.
        equal_blocks: True requires the canonical equal distribution, with remainder
            minutes assigned to earlier blocks. False permits unequal durations.
        subtract_breaks: True uses productive minutes as future planning-score divisor;
            False uses the full shift interval. Neither assigns Jobs during breaks.
    """

    shift_minutes: int
    breaks: tuple[TimedBreak, ...]
    block_minutes: tuple[int, ...]
    equal_blocks: bool = True
    subtract_breaks: bool = True

    def __post_init__(self) -> None:
        """Freeze collections and reject incomplete or inconsistent minute accounting.

        Args:
            None.

        Returns:
            None after validating one complete reusable timing.

        Raises:
            ValueError: Duration, breaks, policy or block coverage is invalid.
        """
        object.__setattr__(self, "breaks", tuple(self.breaks))
        object.__setattr__(self, "block_minutes", tuple(self.block_minutes))
        if type(self.shift_minutes) is not int or not 1 <= self.shift_minutes <= 1440:
            raise ValueError("Shift duration must be 1-1440 whole minutes.")
        if (
            type(self.equal_blocks) is not bool
            or type(self.subtract_breaks) is not bool
        ):
            raise ValueError("Timing options must be explicit Boolean values.")
        previous = 0
        for item in self.breaks:
            if not isinstance(item, TimedBreak) or (
                item.interval.start < previous or item.interval.end > self.shift_minutes
            ):
                raise ValueError(
                    "Breaks must be ordered, inside the shift and not overlap."
                )
            previous = item.interval.end
        net = self.productive_minutes
        if net <= 0:
            raise ValueError("The shift must contain productive time.")
        if (
            not self.block_minutes
            or any(type(n) is not int or n <= 0 for n in self.block_minutes)
            or sum(self.block_minutes) != net
        ):
            raise ValueError(
                "Positive block durations must cover all productive minutes."
            )
        if self.equal_blocks and self.block_minutes != equal_minutes(
            net, len(self.block_minutes)
        ):
            raise ValueError("Equal blocks must use the canonical minute distribution.")

    @property
    def productive_minutes(self) -> int:
        """Read total work duration without interpreting breaks as recovery.

        Args:
            None.

        Returns:
            Full shift minutes minus every recorded break interval.
        """
        return self.shift_minutes - sum(
            b.interval.end - b.interval.start for b in self.breaks
        )

    @property
    def averaging_minutes(self) -> int:
        """Read the proposed planning-score divisor; no scientific score is computed.

        Args:
            None.

        Returns:
            Productive minutes when subtracting breaks; full shift otherwise.
        """
        return self.productive_minutes if self.subtract_breaks else self.shift_minutes

    def blocks(self) -> tuple[WorkBlock, ...]:
        """Project each productive budget into ordered clock pieces around breaks.

        Args:
            None.

        Returns:
            One WorkBlock per duration; every work minute appears exactly once and
            no break minute appears in a block.
        """
        spans = []
        cursor = 0
        for pause in self.breaks:
            if cursor < pause.interval.start:
                spans.append(MinuteInterval(cursor, pause.interval.start))
            cursor = pause.interval.end
        if cursor < self.shift_minutes:
            spans.append(MinuteInterval(cursor, self.shift_minutes))
        result = []
        position = 0
        cursor = spans[0].start
        for index, budget in enumerate(self.block_minutes):
            pieces = []
            while budget:
                span = spans[position]
                used = min(budget, span.end - cursor)
                pieces.append(MinuteInterval(cursor, cursor + used))
                budget -= used
                cursor += used
                if cursor == span.end:
                    position += 1
                    if position < len(spans):
                        cursor = spans[position].start
            result.append(WorkBlock(index, tuple(pieces)))
        return tuple(result)

    def productive_offset(self, elapsed: int) -> int:
        """Map a clock offset to cumulative work, constant through a break.

        Args:
            elapsed: Whole-minute offset inside this shift, inclusive of its end.

        Returns:
            Number of working minutes before that offset.

        Raises:
            ValueError: Offset is fractional, Boolean or outside the shift.
        """
        if type(elapsed) is not int or not 0 <= elapsed <= self.shift_minutes:
            raise ValueError("Clock offset must be inside the shift.")
        return elapsed - sum(
            max(0, min(elapsed, b.interval.end) - b.interval.start) for b in self.breaks
        )


def equal_minutes(productive: int, count: int) -> tuple[int, ...]:
    """Partition integer work minutes with at most one minute between block lengths.

    Args:
        productive: Strictly positive whole working minutes.
        count: Positive block count, no larger than productive minutes.

    Returns:
        Canonical durations, assigning remainder minutes to earliest blocks.

    Raises:
        ValueError: Work/count cannot produce positive whole-minute blocks.
    """
    if (
        type(productive) is not int
        or type(count) is not int
        or not 1 <= count <= productive
    ):
        raise ValueError("Block count cannot exceed productive minutes.")
    base, remainder = divmod(productive, count)
    return tuple(base + (i < remainder) for i in range(count))


def equal_timing(
    shift_minutes: int,
    count: int,
    breaks: tuple[TimedBreak, ...] = (),
    *,
    subtract_breaks: bool = True,
) -> RotationTiming:
    """Construct equal productive blocks while retaining actual minute remainders.

    Args:
        shift_minutes: Daily elapsed span in whole local-clock minutes.
        count: Desired positive block count.
        breaks: Explicit ordered shared pauses; none are inferred.
        subtract_breaks: Explicit future averaging basis, independent of work coverage.

    Returns:
        Validated complete timing; work pieces are derived on demand.

    Raises:
        ValueError: Span, break structure, count or option is invalid.
    """
    net = shift_minutes - sum(b.interval.end - b.interval.start for b in breaks)
    return RotationTiming(
        shift_minutes, breaks, equal_minutes(net, count), True, subtract_breaks
    )


def move_block_boundary(
    timing: RotationTiming, boundary: int, productive_offset: int
) -> RotationTiming:
    """Move one interior boundary, retaining every other boundary and total work.

    Args:
        timing: Complete original timing, never mutated.
        boundary: Interior cut index, 1 through block count minus one.
        productive_offset: Proposed cumulative work minutes before this cut.

    Returns:
        Unequal-mode timing with only the two neighboring durations changed.

    Raises:
        ValueError: Cut/index would remove a block or cross a neighboring boundary.
    """
    if type(boundary) is not int or not 1 <= boundary < len(timing.block_minutes):
        raise ValueError("Choose an interior block boundary.")
    before = sum(timing.block_minutes[: boundary - 1])
    after = sum(timing.block_minutes[: boundary + 1])
    if type(productive_offset) is not int or not before < productive_offset < after:
        raise ValueError(
            "Keep at least one productive minute in each neighboring block."
        )
    values = list(timing.block_minutes)
    values[boundary - 1] = productive_offset - before
    values[boundary] = after - productive_offset
    return replace(timing, block_minutes=tuple(values), equal_blocks=False)

"""Shift timing capability and pure editor preparation, separate from optimization.

Application layer. Resolve recurring clock metadata and validate reusable relative
minute templates. Copying a timing into a future rotation remains explicit; changing
Shift metadata cannot reinterpret saved arrangements or calculator observations.
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from ergotools.domain.organization_record import OrganizationKind
from ergotools.domain.rotation_timing import RotationTiming, TimedBreak, equal_timing
from ergotools.domain.work_hierarchy import WorkHierarchy


def clock_minute(text: str) -> int:
    """Read a canonical 24-hour clock without locale or timezone inference.

    Args:
        text: Exact HH:mm, hours 00-23 and minutes 00-59.

    Returns:
        Whole minutes after local midnight.

    Raises:
        ValueError: Clock is absent, malformed or outside a daily clock.
    """
    if (
        not isinstance(text, str)
        or len(text) != 5
        or text[2] != ":"
        or not (
            text[:2].isascii()
            and text[:2].isdigit()
            and text[3:].isascii()
            and text[3:].isdigit()
        )
    ):
        raise ValueError("Enter a complete 24-hour clock as HH:mm.")
    hour, minute = int(text[:2]), int(text[3:])
    if hour > 23 or minute > 59:
        raise ValueError("Enter a complete 24-hour clock as HH:mm.")
    return hour * 60 + minute


@dataclass(frozen=True, slots=True)
class ShiftClock:
    """Complete recurring daily clock context, with no calendar/DST inference.

    Attributes:
        start_minute: Clock origin after midnight, 0-1439.
        span_minutes: Positive daily elapsed local-clock span, 1-1440.
    """

    start_minute: int
    span_minutes: int

    def __post_init__(self) -> None:
        """Validate a complete daily local-clock interval.

        Args:
            None.

        Returns:
            None after structural validation.

        Raises:
            ValueError: Origin/span are not valid whole daily minutes.
        """
        if (
            type(self.start_minute) is not int
            or not 0 <= self.start_minute < 1440
            or (
                type(self.span_minutes) is not int or not 1 <= self.span_minutes <= 1440
            )
        ):
            raise ValueError("Shift requires a complete positive daily clock interval.")

    def offset(self, text: str, *, end: bool = False) -> int:
        """Interpret a break clock relative to this shift, including midnight.

        Args:
            text: Canonical 24-hour break clock.
            end: True allows the terminal repeated origin of a 24-hour shift.

        Returns:
            Relative clock offset. Timing validation checks interval membership.

        Raises:
            ValueError: Clock is malformed.
        """
        value = (clock_minute(text) - self.start_minute) % 1440
        return 1440 if end and value == 0 and self.span_minutes == 1440 else value

    def label(self, offset: int) -> str:
        """Format a relative minute as 24-hour time with explicit next-day suffix.

        Args:
            offset: Relative minute of a work/break interval in this daily span.

        Returns:
            HH:mm, adding (+1) when the local calendar day has advanced.
        """
        absolute = self.start_minute + offset
        return f"{absolute // 60 % 24:02d}:{absolute % 60:02d}" + (
            " (+1)" if absolute >= 1440 else ""
        )


def shift_clock(hierarchy: WorkHierarchy, shift_id: str) -> ShiftClock:
    """Resolve current recurring start/end metadata without manufacturing missing time.

    Args:
        hierarchy: Current exact project hierarchy.
        shift_id: Saved project-wide Shift identity.

    Returns:
        Complete clock; end at/before start follows existing next-day convention.

    Raises:
        ValueError: Shift or either complete clock is missing/invalid.
    """
    if shift_id not in hierarchy.work.shifts:
        raise ValueError("Select an existing Shift.")
    attributes = next(
        (
            dict(r.attributes)
            for r in hierarchy.organization
            if r.kind is OrganizationKind.SHIFT and r.keys == (shift_id,)
        ),
        {},
    )
    start, end = attributes.get("start_time"), attributes.get("end_time")
    if not isinstance(start, str) or not isinstance(end, str) or not start or not end:
        raise ValueError(
            "Set Shift start and end times before defining rotation timing."
        )
    first, last = clock_minute(start), clock_minute(end)
    return ShiftClock(first, (last - first) % 1440 or 1440)


@dataclass(frozen=True, slots=True)
class ShiftTimingTemplate:
    """One optional reusable timing owned by an existing project-wide Shift.

    Attributes:
        shift_id: Stable saved Shift identity.
        timing: Relative work/break minutes, independent of calendar dates and risks.
    """

    shift_id: str
    timing: RotationTiming

    def __post_init__(self) -> None:
        """Require explicit typed ownership and complete minute accounting.

        Args:
            None.

        Returns:
            None; project membership is checked separately against the hierarchy.

        Raises:
            ValueError: Identity or timing is untyped/blank.
        """
        if (
            not isinstance(self.shift_id, str)
            or not self.shift_id.strip()
            or not isinstance(self.timing, RotationTiming)
        ):
            raise ValueError(
                "Timing template requires a Shift identity and typed timing."
            )

    def validate(self, hierarchy: WorkHierarchy) -> None:
        """Protect stored relative timing from duration changes or missing ownership.

        Args:
            hierarchy: Proposed complete hierarchy under the caller's write boundary.

        Returns:
            None when current Shift clocks describe exactly the stored daily span.

        Raises:
            ValueError: Shift disappeared, clocks are incomplete or duration changed.
        """
        if self.shift_id not in hierarchy.work.shifts:
            raise ValueError(
                "Clear the rotation timing template before removing its Shift."
            )
        if (
            shift_clock(hierarchy, self.shift_id).span_minutes
            != self.timing.shift_minutes
        ):
            raise ValueError(
                "Clear the rotation timing template before changing Shift duration."
            )


@runtime_checkable
class RotationTimingRepository(Protocol):
    """Optional project timing capability with one guarded replace per Shift."""

    def load_shift_timings(self) -> tuple[ShiftTimingTemplate, ...]:
        """Read saved templates without creating defaults.

        Args:
            None.

        Returns:
            Stable Shift-ID-ordered templates; absence means untimed.
        """
        ...

    def replace_shift_timing(
        self,
        shift_id: str,
        expected: RotationTiming | None,
        replacement: RotationTiming | None,
    ) -> None:
        """Accept one atomic template edit, leaving source/results/rotations intact.

        Args:
            shift_id: Existing Shift identity in the owning project.
            expected: Exact previous timing, None requires absence.
            replacement: Complete desired timing, None explicitly clears it.

        Returns:
            None after private acceptance; Main Save owns durable publication.
        """
        ...


def edit_timing(
    previous: RotationTiming,
    breaks: tuple[TimedBreak, ...],
    count: int,
    *,
    equal: bool,
    subtract_breaks: bool,
) -> RotationTiming:
    """Prepare a complete edited template without silently rescaling unequal prefixes.

    Args:
        previous: Last valid timing, retained if preparation fails.
        breaks: Explicit proposed pauses in chronological order.
        count: Desired positive number of work blocks.
        equal: Canonical equal distribution when True.
        subtract_breaks: Explicit averaging-basis option.

    Returns:
        Valid timing. Count changes redistribute equally; unchanged unequal counts keep
        earlier budgets and adjust the last block to the available productive remainder.

    Raises:
        ValueError: Breaks/count are invalid or retained blocks leave no final work.
    """
    if (
        type(count) is not int
        or type(equal) is not bool
        or type(subtract_breaks) is not bool
    ):
        raise ValueError("Timing requires whole block counts and Boolean options.")
    if equal or count != len(previous.block_minutes):
        return equal_timing(
            previous.shift_minutes, count, breaks, subtract_breaks=subtract_breaks
        )
    net = previous.shift_minutes - sum(
        b.interval.end - b.interval.start for b in breaks
    )
    minutes = (*previous.block_minutes[:-1], net - sum(previous.block_minutes[:-1]))
    return RotationTiming(
        previous.shift_minutes, breaks, minutes, False, subtract_breaks
    )

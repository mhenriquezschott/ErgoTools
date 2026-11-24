"""Read-only rotation-to-map projection and elapsed schedule-index calculation.

Application layer. Playback resolves full baseline block-one assignment positions,
uses retained run coefficients for paired before/after schedules, and never writes
positions, worker assessments, history or rotation data. Qt owns wall-clock pacing.
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from ergotools.application.plot_results import PlotResultRepository
from ergotools.application.rotation_scenarios import freeze_rotation_coefficients
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.plot_positions import PlotPoint
from ergotools.domain.rotation import WorkerRotation
from ergotools.domain.rotation_scenario import (
    ROTATION_RUN_MODEL_VERSION,
    RotationScenario,
    complete_rotation_rows,
)
from ergotools.domain.rotation_timing import RotationTiming
from ergotools.domain.task_catalog import TaskDefinition


@runtime_checkable
class ShiftPlaybackRepository(PlotResultRepository, Protocol):
    """Borrow project catalogs and named rotations, without any mutation capability."""

    def load_rotation_scenarios(self) -> tuple[RotationScenario, ...]:
        """Read current named plans and their retained results.

        Args:
            None.

        Returns:
            Saved rotations; storage errors propagate without a partial playback.
        """
        ...

    def load_task_definitions(self) -> tuple[TaskDefinition, ...]:
        """Read reusable names when freezing a baseline without a retained run.

        Args:
            None.

        Returns:
            Current typed task definitions; labels are never inferred from IDs.
        """
        ...


@dataclass(frozen=True)
class ShiftDestination:
    """One fixed placement destination in original plant-image pixels.

    Attributes:
        key: Exact rotation target key.
        job_id: Display Job identifier.
        name: Literal Job name.
        point: Position established by baseline block one.
        risk: Frozen/current selected-tool Job probability, in percent.
    """

    key: str
    job_id: str
    name: str
    point: PlotPoint
    risk: float


@dataclass(frozen=True)
class ShiftPlayback:
    """Complete immutable data needed for one schedule playback.

    Attributes:
        name: Rotation label.
        plant: Single mapped plant.
        start: Local clock origin, minutes after midnight.
        timing: Real copied work/break timing.
        rows: Selected baseline or optimized worker schedule.
        destinations: Fixed Job positions and risk values.
        workers: Ordered ID, literal name and sex for each participant.
        recorded: True when coefficients/timing belong to a retained run.
        issues: Missing mappings preventing playback; available destinations remain
            useful for a static, explicitly incomplete map.
    """

    name: str
    plant: str
    start: int
    timing: RotationTiming
    rows: tuple[WorkerRotation, ...]
    destinations: tuple[ShiftDestination, ...]
    workers: tuple[tuple[str, str, str | None], ...]
    recorded: bool
    issues: tuple[str, ...] = ()

    def index(self, worker: int, elapsed: float) -> float:
        """Accumulate completed productive exposure over the fixed JROT divisor.

        Args:
            worker: Zero-based schedule row.
            elapsed: Shift-relative clock minutes, including breaks.

        Returns:
            Partial contribution in percentage points for a complete snapshot; final
            value equals JROT's weighted index. Callers must not calculate indices
            when issues report missing destinations. Breaks add no exposure and imply
            no recovery.
        """
        risks = {d.key: d.risk for d in self.destinations}
        total = 0.0
        for block, target in zip(
            self.timing.blocks(), self.rows[worker].target_keys, strict=True
        ):
            used = sum(max(0.0, min(elapsed, p.end) - p.start) for p in block.pieces)
            total += used * risks[target]
        return total / self.timing.averaging_minutes

    def phase(self, elapsed: float) -> tuple[int, int, float]:
        """Resolve the current block or a break's next-block motion fraction.

        Args:
            elapsed: Shift-relative clock minutes, clamped to this shift.

        Returns:
            Previous/current block, destination block and movement fraction. Work
            returns identical indices; break movement uses smoothstep easing.
        """
        blocks = self.timing.blocks()
        for index, block in enumerate(blocks):
            for piece in block.pieces:
                if piece.start <= elapsed < piece.end:
                    return index, index, 0.0
        previous = max(
            (b.index for b in blocks if b.pieces[-1].end <= elapsed), default=0
        )
        following = next(
            (b.index for b in blocks if b.pieces[0].start > elapsed), previous
        )
        if previous == following:
            return previous, previous, 0.0
        a, b = blocks[previous].pieces[-1].end, blocks[following].pieces[0].start
        fraction = max(0.0, min(1.0, (elapsed - a) / max(1, b - a)))
        return previous, following, fraction * fraction * (3 - 2 * fraction)


def prepare_shift(
    repository: ShiftPlaybackRepository,
    scenario: RotationScenario,
    kind: AssessmentKind,
    optimized: bool,
    *,
    allow_partial: bool = False,
) -> ShiftPlayback:
    """Resolve complete baseline destinations and a paired selected schedule.

    Args:
        repository: Borrowed read-only catalogs and original-pixel geometry.
        scenario: Named rotation, freshly loaded when selected or refreshed.
        kind: One selected analyzed ergonomic tool.
        optimized: True selects the retained optimization; False its paired baseline.
        allow_partial: Return available mapped destinations and diagnostic issues
            instead of failing at the first missing assignment/coordinate/risk.

    Returns:
        Single-plant playback, or an explicitly incomplete snapshot when partial
        preparation is requested. Its issues disable playback; available destinations
        remain usable for a static map. No coordinates or risk values are fabricated.

    Raises:
        ValueError: Timing, baseline, placement, Job risk or map positions are missing
            or contradictory. A baseline is needed to establish initial destinations.
    """
    run = scenario.run
    if run is not None and run.contract_version != ROTATION_RUN_MODEL_VERSION:
        raise ValueError("Reoptimize this older rotation before Shift View playback.")
    inputs = run.inputs if run else scenario.inputs
    if inputs.timing is None or inputs.start_minute is None or inputs.baseline is None:
        raise ValueError("Set complete timing and baseline assignments in JROT first.")
    baseline = complete_rotation_rows(inputs.baseline)
    if optimized and run is None:
        raise ValueError("Keep an optimization result in JROT before playing it here.")
    rows = run.arrangement if optimized and run else baseline
    if kind not in inputs.tools:
        raise ValueError("This tool was not analyzed in the selected rotation.")
    jobs = repository.load_jobs()
    coefficients = (
        run.coefficients
        if run
        else freeze_rotation_coefficients(
            inputs, jobs, repository.load_job_risk(), repository.load_task_definitions()
        )
    )
    risks = {
        c.target_key: c.measurement.probability_percent
        for c in coefficients
        if c.measurement.kind is kind
    }
    names = {
        c.target_key: c.job_name for c in coefficients if c.measurement.kind is kind
    }
    assignments = {a.assignment_id: a for a in jobs.assignments}
    placements = {p.placement_id: p for p in jobs.placements}
    links = {w.worker_id: w for w in inputs.workers}
    people = {w.worker_id: w for w in repository.load_hierarchy().work.workers}
    positions = repository.load_plot_positions()
    targets = {t.key: t for t in inputs.targets}
    destinations = []
    issues: list[str] = []
    plants = set()
    if len(baseline) != len(targets) or len(
        {r.target_keys[0] for r in baseline}
    ) != len(targets):
        raise ValueError("Baseline block one must staff every Job position once.")
    for row in baseline:
        key = row.target_keys[0]
        target = targets[key]
        placement = placements.get(target.placement_id) if target.placement_id else None
        assignment = assignments.get(links[row.worker_id].assignment_id or -1)
        if (
            placement is None
            or assignment is None
            or assignment.placement_id != placement.placement_id
        ):
            message = (
                f"{row.worker_id}: block-one Job must match "
                "its mapped workplace assignment."
            )
            if not allow_partial:
                raise ValueError(message)
            issues.append(message)
            continue
        point = positions.worker_point(assignment.assignment_id, jobs)
        if point is None:
            message = f"Place {row.worker_id} on the plant map for baseline block one."
            if not allow_partial:
                raise ValueError(message)
            issues.append(message)
            continue
        risk = risks.get(key)
        if risk is None:
            message = f"{target.job_id}: no calculated value for this tool."
            if not allow_partial:
                raise ValueError(message)
            issues.append(message)
            continue
        plants.add(placement.workplace.plant_name)
        destinations.append(
            ShiftDestination(key, target.job_id, names[key], point, risk)
        )
    if len(plants) > 1 or (not plants and not allow_partial):
        raise ValueError("This Shift View requires destinations in one plant.")
    worker_rows = []
    for row in rows:
        person = people[row.worker_id]
        name = f"{person.first_name or ''} {person.last_name or ''}".strip()
        worker_rows.append(
            (row.worker_id, name, person.details.sex if person.details else None)
        )
    workers = tuple(worker_rows)
    return ShiftPlayback(
        scenario.name,
        next(iter(plants), ""),
        inputs.start_minute,
        inputs.timing,
        rows,
        tuple(destinations),
        workers,
        run is not None,
        tuple(issues),
    )


@dataclass(frozen=True)
class PlaybackStage:
    """One work, break or zero-clock-gap transition in player wall time.

    Attributes:
        begin: Real shift-relative start minute.
        end: Real shift-relative end minute; equal on no-break transitions.
        seconds: Preview duration, separate from exposure-clock minutes.
        previous: Previous/current work block.
        following: Destination work block; equal during work.
    """

    begin: float
    end: float
    seconds: float
    previous: int
    following: int


def playback_stages(
    data: ShiftPlayback, seconds_per_block: float, motion_seconds: float
) -> tuple[PlaybackStage, ...]:
    """Build preview pacing while preserving actual exposure durations.

    Args:
        data: Prepared immutable schedule.
        seconds_per_block: Preview seconds per complete productive block.
        motion_seconds: Preview seconds per break; no-break moves use half this time.

    Returns:
        Ordered player stages, including explicit moves at adjacent block boundaries.

    Raises:
        ValueError: Player durations are nonpositive.
    """
    if seconds_per_block <= 0 or motion_seconds <= 0:
        raise ValueError("Use positive preview durations.")
    parts = sorted(
        [(p.start, p.end, b.index) for b in data.timing.blocks() for p in b.pieces]
        + [(b.interval.start, b.interval.end, -1) for b in data.timing.breaks]
    )
    result: list[PlaybackStage] = []
    previous = 0
    for n, (a, b, block) in enumerate(parts):
        if block >= 0:
            if result and parts[n - 1][2] >= 0 and previous != block:
                result.append(
                    PlaybackStage(a, a, motion_seconds * 0.5, previous, block)
                )
            result.append(
                PlaybackStage(
                    a,
                    b,
                    seconds_per_block * (b - a) / data.timing.block_minutes[block],
                    block,
                    block,
                )
            )
            previous = block
        else:
            following = next((p[2] for p in parts[n + 1 :] if p[2] >= 0), previous)
            result.append(PlaybackStage(a, b, motion_seconds, previous, following))
    return tuple(result)

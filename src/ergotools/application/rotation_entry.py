"""Pure guided-entry edits over independent saved rotation inputs.

Application layer. Reshape explicit entered matrices while retaining surviving cells
and reporting any lost data before acceptance. Catalog choices never invent
participants, coefficients or an observed baseline; readiness identifies incomplete
inputs before the independent production solve validator.
"""

from dataclasses import dataclass, replace

from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.job_catalog import JobCatalog
from ergotools.domain.job_risk import JobRiskCatalog
from ergotools.domain.rotation import WorkerRotation
from ergotools.domain.rotation_constraints import (
    ExcludedPosition,
    FixedPosition,
    RotationRule,
)
from ergotools.domain.rotation_scenario import (
    RotationDraftRow,
    RotationInputs,
    complete_rotation_rows,
)
from ergotools.domain.rotation_scheme import RotationTarget, RotationWorkerLink
from ergotools.domain.rotation_timing import RotationTiming, equal_timing
from ergotools.domain.work_hierarchy import LineKey, WorkHierarchy


@dataclass(frozen=True, slots=True)
class RotationEntryChange:
    """Prepared complete input replacement plus explicit destructive consequences.

    Attributes:
        inputs: Desired structurally valid draft, not yet accepted or saved.
        lost_rules: Active restrictions whose removed worker/position cannot
        survive.
        lost_cells: Observed/proposed, worker ID, one-based block and removed target
        key.
    """

    inputs: RotationInputs
    lost_cells: tuple[tuple[str, str, int, str], ...] = ()
    lost_rules: tuple[RotationRule, ...] = ()


def reshape_rotation_inputs(
    previous: RotationInputs,
    *,
    workers: tuple[RotationWorkerLink, ...] | None = None,
    targets: tuple[RotationTarget, ...] | None = None,
    timing: RotationTiming | None = None,
    replace_timing: bool = False,
    start_minute: int | None = None,
) -> RotationEntryChange:
    """Retain entered cells by exact worker/position identity across setup changes.

    Args:
        previous: Last accepted independent plan.
        workers: Desired ordered participants; None preserves them.
        targets: Desired unique positions; None preserves them.
        timing: Desired copied timing when replace_timing is True, including clear.
        replace_timing: Explicitly distinguishes keeping timing from clearing it.
        start_minute: Copied clock origin when replacing timing; paired with timing.

    Returns:
        Prepared input and every nonempty discarded cell. New slots are None, never
        inferred assignments. An empty observed matrix remains distinct from no
        baseline.
    """
    chosen_workers = previous.workers if workers is None else workers
    chosen_targets = previous.targets if targets is None else targets
    chosen_timing = timing if replace_timing else previous.timing
    horizon = (
        len(chosen_timing.block_minutes)
        if chosen_timing is not None
        else next(
            (
                len(rows[0].target_keys)
                for rows in (previous.baseline, previous.proposed)
                if rows
            ),
            1,
        )
    )
    keys = {t.key for t in chosen_targets}
    identities = {w.worker_id for w in chosen_workers}
    lost = []
    schedules: dict[str, tuple[WorkerRotation | RotationDraftRow, ...] | None] = {}
    for field, rows in (
        ("baseline", previous.baseline),
        ("proposed", previous.proposed),
    ):
        if rows is None:
            schedules[field] = None
            continue
        old = {r.worker_id: r for r in rows}
        for row in rows:
            for block, key in enumerate(row.target_keys):
                if key is not None and (
                    row.worker_id not in identities
                    or block >= horizon
                    or key not in keys
                ):
                    lost.append((field, row.worker_id, block + 1, key))
        result = []
        for worker in chosen_workers:
            existing = (
                old[worker.worker_id].target_keys if worker.worker_id in old else ()
            )
            result.append(
                RotationDraftRow(
                    worker.worker_id,
                    tuple(
                        existing[b]
                        if b < len(existing) and existing[b] in keys
                        else None
                        for b in range(horizon)
                    ),
                )
            )
        schedules[field] = tuple(result)
    return RotationEntryChange(
        replace(
            previous,
            workers=chosen_workers,
            targets=chosen_targets,
            timing=chosen_timing,
            start_minute=start_minute if replace_timing else previous.start_minute,
            baseline=schedules["baseline"],
            proposed=schedules["proposed"],
            rules=tuple(
                r
                for r in previous.rules
                if r.worker_id in identities
                and (
                    not isinstance(r, (FixedPosition, ExcludedPosition))
                    or r.target_key in keys
                )
            ),
        ),
        tuple(lost),
        tuple(
            r
            for r in previous.rules
            if r.worker_id not in identities
            or (
                isinstance(r, (FixedPosition, ExcludedPosition))
                and r.target_key not in keys
            )
        ),
    )


def choose_observed_rotation(
    inputs: RotationInputs, observed: bool
) -> RotationEntryChange:
    """Prepare Yes/No without manufacturing an observed schedule or losing it silently.

    Args:
        inputs: Current draft, possibly without participants/timing.
        observed: Explicit Yes/No choice.

    Returns:
        Empty/partial observed rows for Yes; None for No, reporting removed entered
        cells.
    """
    if observed:
        if inputs.baseline is not None:
            return RotationEntryChange(inputs)
        horizon = len(inputs.timing.block_minutes) if inputs.timing is not None else 1
        return RotationEntryChange(
            replace(
                inputs,
                baseline=tuple(
                    RotationDraftRow(w.worker_id, (None,) * horizon)
                    for w in inputs.workers
                ),
            )
        )
    lost = tuple(
        ("baseline", r.worker_id, b + 1, k)
        for r in inputs.baseline or ()
        for b, k in enumerate(r.target_keys)
        if k is not None
    )
    return RotationEntryChange(replace(inputs, baseline=None), lost)


def set_rotation_cell(
    inputs: RotationInputs,
    worker_id: str,
    block: int,
    target_key: str | None,
) -> RotationInputs:
    """Edit one slot without accepting a whole matrix of widget defaults.

    Args:
        inputs: Current explicit Yes/No draft.
        worker_id: Existing participating worker.
        block: Zero-based work block.
        target_key: Exact offered position key, or None to clear this slot.

    Returns:
        Replacement retaining every other cell. No-path edits belong to proposed rows.

    Raises:
        ValueError: Worker, block or offered position is invalid.
    """
    horizon = (
        len(inputs.timing.block_minutes)
        if inputs.timing is not None
        else next(
            (
                len(rows[0].target_keys)
                for rows in (inputs.baseline, inputs.proposed)
                if rows
            ),
            1,
        )
    )
    if (
        worker_id not in {w.worker_id for w in inputs.workers}
        or type(block) is not int
        or not 0 <= block < horizon
    ):
        raise ValueError("Choose a current worker and work block.")
    if target_key is not None and target_key not in {t.key for t in inputs.targets}:
        raise ValueError("Choose an offered Job position.")
    field = "baseline" if inputs.baseline is not None else "proposed"
    rows = getattr(inputs, field) or tuple(
        RotationDraftRow(w.worker_id, (None,) * horizon) for w in inputs.workers
    )
    replacement = []
    for row in rows:
        values = list(row.target_keys)
        if row.worker_id == worker_id:
            values[block] = target_key
        replacement.append(RotationDraftRow(row.worker_id, tuple(values)))
    return (
        replace(inputs, baseline=tuple(replacement))
        if field == "baseline"
        else replace(inputs, proposed=tuple(replacement))
    )


def rotation_entry_targets(
    inputs: RotationInputs,
    jobs: JobCatalog,
) -> tuple[RotationTarget, ...]:
    """Offer global Jobs or exact placement positions for the applied workplace scope.

    Args:
        inputs: Current saved scope, independent of permanent worker assignments.
        jobs: Current complete Job catalog.

    Returns:
        Active unique global Job targets, or active placements inside exact scope.
        Repeated Jobs at different placements retain different keys.
    """
    active = {j.job_id for j in jobs.jobs if j.active}
    if not inputs.scope:
        return tuple(RotationTarget(j.job_id) for j in jobs.jobs if j.active)
    return tuple(
        RotationTarget(p.job_id, p.placement_id)
        for p in jobs.placements
        if p.active and p.job_id in active and p.workplace in inputs.scope
    )


def scope_rotation_inputs(
    inputs: RotationInputs,
    hierarchy: WorkHierarchy,
    jobs: JobCatalog,
    line: LineKey | None,
    shift_id: str | None,
    workplace: bool,
) -> RotationEntryChange:
    """Prepare explicit scope and prune only targets unavailable in that new scope.

    Args:
        inputs: Current independent draft.
        hierarchy: Current organization data.
        jobs: Current Job/placement catalog.
        line: Exact chosen Line, or None for all locations.
        shift_id: Exact chosen Shift, or None during incomplete global setup.
        workplace: True requires a real Line, Shift and at least one Station.

    Returns:
        Prepared scope with surviving exact positions/cells, plus removed-cell warning
        data.

    Raises:
        ValueError: Selected scope cannot describe a real workplace.
    """
    if line is not None and line not in hierarchy.lines:
        raise ValueError("Select an existing Line.")
    if shift_id is not None and shift_id not in hierarchy.work.shifts:
        raise ValueError("Select an existing Shift.")
    contexts: tuple[WorkplaceContext, ...] = ()
    if workplace:
        contexts = tuple(
            s.at_shift(shift_id)
            for s in hierarchy.work.stations
            if line is not None
            and shift_id is not None
            and (s.plant_name, s.section_name, s.line_name)
            == (line.plant_name, line.section_name, line.line_name)
        )
        if not contexts:
            raise ValueError("Workplace scope requires a Line, Shift and Station.")
    scoped = replace(inputs, line=line, shift_id=shift_id, scope=contexts)
    offered = {t.key for t in rotation_entry_targets(scoped, jobs)}
    return reshape_rotation_inputs(
        scoped, targets=tuple(t for t in inputs.targets if t.key in offered)
    )


def rotation_entry_issues(
    inputs: RotationInputs, risks: JobRiskCatalog
) -> tuple[str, ...]:
    """Describe basic readiness without substituting J06's full independent validator.

    Args:
        inputs: Current possibly incomplete entry.
        risks: Current Job values; missing remains absent, never zero.

    Returns:
        Stable diagnostic keys for missing setup, staffing, schedule or coefficients.
        Hard rules/neighbor feasibility and actual solves remain outside this helper.
    """
    issues = []
    if inputs.planned_date is None:
        issues.append("date")
    if inputs.timing is None:
        issues.append("timing")
    if not inputs.workers or len(inputs.workers) != len(inputs.targets):
        issues.append("participants")
    if not inputs.targets:
        issues.append("jobs")
    if inputs.baseline is not None:
        try:
            rows = complete_rotation_rows(inputs.baseline)
            if not rows or any(
                {r.target_keys[b] for r in rows} != {t.key for t in inputs.targets}
                for b in range(len(rows[0].target_keys))
            ):
                issues.append("staffing")
        except ValueError:
            issues.append("schedule")
    for target in inputs.targets:
        measurements = risks.for_job(target.job_id).measurements
        if any(
            not any(m.kind is k and m.complete for m in measurements)
            for k in inputs.tools
        ):
            issues.append("coefficients")
            break
    return tuple(issues)


def reclock_rotation_inputs(
    inputs: RotationInputs, start: int, end: int
) -> RotationEntryChange:
    """Prepare clocks while retaining relative breaks and unequal prefixes.

    Args:
        inputs: Current scenario copy, independent of recurring Shift metadata.
        start: Local minute after midnight, 0-1439.
        end: Local minute after midnight; at/before start means next day.

    Returns:
        Complete copied timing/clock and any truncated schedule cells. Without prior
        timing, four equal blocks are proposed, limited by available whole minutes.

    Raises:
        ValueError: Clocks, retained breaks or unequal budgets cannot fit the new span.
    """
    if (
        type(start) is not int
        or type(end) is not int
        or not (0 <= start < 1440 and 0 <= end < 1440)
    ):
        raise ValueError("Use complete local clocks from 00:00 through 23:59.")
    span = (end - start) % 1440 or 1440
    previous = inputs.timing
    if previous is None:
        timing = equal_timing(span, min(4, span))
    elif previous.equal_blocks:
        timing = equal_timing(
            span,
            len(previous.block_minutes),
            previous.breaks,
            subtract_breaks=previous.subtract_breaks,
        )
    else:
        net = span - sum(b.interval.end - b.interval.start for b in previous.breaks)
        timing = RotationTiming(
            span,
            previous.breaks,
            (*previous.block_minutes[:-1], net - sum(previous.block_minutes[:-1])),
            False,
            previous.subtract_breaks,
        )
    return reshape_rotation_inputs(
        inputs, timing=timing, replace_timing=True, start_minute=start
    )


def reshape_timed_rotation_inputs(
    previous: RotationInputs,
    timing: RotationTiming | None,
    start_minute: int | None,
) -> RotationEntryChange:
    """Preserve unchanged clock-span cells across a structural timing edit.

    Args:
        previous: Exact accepted independent scenario inputs.
        timing: Complete timing proposal, or explicit clear.
        start_minute: Copied daily clock origin paired with the new timing.

    Returns:
        Prepared replacement and every nonempty affected cell requiring consent.
        A split/join never shifts unrelated cells by array index or invents assignments
        for changed blocks. Same-count duration edits retain their block identities.
    """
    ordinary = reshape_rotation_inputs(
        previous, timing=timing, replace_timing=True, start_minute=start_minute
    )
    before = previous.timing
    if (
        before is None
        or timing is None
        or len(before.block_minutes) == len(timing.block_minutes)
    ):
        return ordinary
    old_spans = {block.pieces: block.index for block in before.blocks()}
    mapping = tuple(old_spans.get(block.pieces) for block in timing.blocks())
    retained = {index for index in mapping if index is not None}
    schedules: dict[str, tuple[RotationDraftRow, ...] | None] = {}
    lost: list[tuple[str, str, int, str]] = []
    for field, rows in (
        ("baseline", previous.baseline),
        ("proposed", previous.proposed),
    ):
        if rows is None:
            schedules[field] = None
            continue
        updated = []
        for row in rows:
            updated.append(
                RotationDraftRow(
                    row.worker_id,
                    tuple(
                        row.target_keys[index] if index is not None else None
                        for index in mapping
                    ),
                )
            )
            lost.extend(
                (field, row.worker_id, index + 1, key)
                for index, key in enumerate(row.target_keys)
                if key is not None and index not in retained
            )
        schedules[field] = tuple(updated)
    return RotationEntryChange(
        replace(
            ordinary.inputs,
            baseline=schedules["baseline"],
            proposed=schedules["proposed"],
        ),
        tuple(lost),
        ordinary.lost_rules,
    )

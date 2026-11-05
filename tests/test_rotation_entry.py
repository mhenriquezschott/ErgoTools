"""Guided draft transformations preserve exact cells and explicit observation intent.

Pure application checks use immutable synthetic catalogs. No Qt, maintained project,
optimizer, clinical formula or migration target is involved.
"""

from dataclasses import replace

import pytest

from ergotools.application.rotation_entry import (
    choose_observed_rotation,
    reshape_rotation_inputs,
    rotation_entry_issues,
    rotation_entry_targets,
    scope_rotation_inputs,
    set_rotation_cell,
)
from ergotools.domain.job_catalog import JobPlacement
from ergotools.domain.rotation_scenario import RotationDraftRow, RotationInputs
from ergotools.domain.rotation_scheme import RotationWorkerLink
from ergotools.domain.rotation_timing import equal_timing
from ergotools.domain.work_catalog import StationKey
from ergotools.domain.work_hierarchy import LineKey, SectionKey
from tests.test_rotation_scenarios import (
    balanced_rows,
    scenario_catalogs,
    scenario_inputs,
)


def test_yes_before_participants_is_distinct_from_no_and_stays_empty() -> None:
    """Yes persists explicitly without inventing participants, targets or cells.

    Args:
        None.

    Returns:
        None; selecting workers later introduces only explicit None slots.
    """
    empty = RotationInputs()
    yes = choose_observed_rotation(empty, True).inputs
    assert yes.baseline == () and yes.workers == () and yes.targets == ()
    assert choose_observed_rotation(yes, True).inputs == yes
    selected = reshape_rotation_inputs(yes, workers=(RotationWorkerLink("A"),))
    assert selected.inputs.baseline == (RotationDraftRow("A", (None,)),)
    assert not selected.lost_cells
    assert choose_observed_rotation(selected.inputs, False).inputs.baseline is None
    assert choose_observed_rotation(empty, False).inputs == empty


def test_reshape_retains_cells_by_identity_and_reports_every_removed_value() -> None:
    """Removing/reordering workers, targets and blocks never cross-assigns a cell.

    Args:
        None.

    Returns:
        None; new cells stay absent and lost values can be shown before acceptance.
    """
    inputs = scenario_inputs()
    inputs = replace(
        inputs, baseline=balanced_rows(inputs), proposed=balanced_rows(inputs)
    )
    change = reshape_rotation_inputs(
        inputs,
        workers=tuple(reversed(inputs.workers)),
        targets=inputs.targets[:1],
        timing=equal_timing(480, 1),
        start_minute=480,
        replace_timing=True,
    )
    a, b = (t.key for t in inputs.targets)
    assert change.inputs.baseline == (
        RotationDraftRow("W2", (None,)),
        RotationDraftRow("W1", (a,)),
    )
    assert len(change.lost_cells) == 6
    assert ("baseline", "W2", 1, b) in change.lost_cells
    assert ("proposed", "W1", 2, b) in change.lost_cells
    larger = reshape_rotation_inputs(
        inputs, timing=equal_timing(480, 3), start_minute=480, replace_timing=True
    )
    assert larger.inputs.baseline[0].target_keys == (a, b, None)
    assert larger.lost_cells == ()
    assert reshape_rotation_inputs(inputs).inputs == inputs


@pytest.mark.parametrize("observed", [True, False])
def test_cell_edits_are_single_slot_and_missing_never_becomes_zero(
    observed: bool,
) -> None:
    """Observed and proposed matrices use the same exact one-cell mutation contract.

    Args:
        observed: Explicit Yes or No observation intent.

    Returns:
        None; repeated editing does not coalesce unrelated entered cells.
    """
    initial = scenario_inputs()
    initial = choose_observed_rotation(initial, observed).inputs
    first = set_rotation_cell(initial, "W1", 0, initial.targets[0].key)
    second = set_rotation_cell(first, "W1", 1, initial.targets[1].key)
    rows = second.baseline if observed else second.proposed
    assert rows[0].target_keys == tuple(t.key for t in initial.targets)
    assert rows[1].target_keys == (None, None)
    restored = set_rotation_cell(second, "W1", 1, None)
    assert restored == first
    with pytest.raises(ValueError, match="worker"):
        set_rotation_cell(initial, "missing", 0, None)
    with pytest.raises(ValueError, match="block"):
        set_rotation_cell(initial, "W1", 99, None)
    with pytest.raises(ValueError, match="offered"):
        set_rotation_cell(initial, "W1", 0, "unknown")


def test_scope_retains_exact_placements_and_excludes_inactive_or_other_lines() -> None:
    """One Job at two physical stations remains two positions in Workplace scope.

    Args:
        None.

    Returns:
        None; All Jobs offers one global entry per active Job instead.
    """
    hierarchy, jobs, _ = scenario_catalogs()
    station = StationKey("Plant", "Section", "Line", "ST01")
    hierarchy = replace(
        hierarchy,
        work=replace(
            hierarchy.work, stations=(station, replace(station, station_id="ST02"))
        ),
        plants=("Plant",),
        sections=(SectionKey("Plant", "Section"),),
        lines=(LineKey("Plant", "Section", "Line"),),
    )
    context = station.at_shift("Day")
    jobs = replace(
        jobs,
        placements=(
            JobPlacement(1, "J1", context),
            JobPlacement(2, "J1", replace(context, station_id="ST02")),
            JobPlacement(3, "J2", context, False),
        ),
    )
    line = hierarchy.lines[0]
    scoped = scope_rotation_inputs(
        RotationInputs(), hierarchy, jobs, line, "Day", True
    ).inputs
    targets = rotation_entry_targets(scoped, jobs)
    assert len(targets) == 2 and targets[0].key != targets[1].key
    assert all(t.job_id == "J1" for t in targets)
    global_inputs = scope_rotation_inputs(
        scoped, hierarchy, jobs, None, "Day", False
    ).inputs
    assert len(rotation_entry_targets(global_inputs, jobs)) == 2
    assert not global_inputs.scope
    with pytest.raises(ValueError, match="requires"):
        scope_rotation_inputs(scoped, hierarchy, jobs, None, "Day", True)
    with pytest.raises(ValueError, match="Shift"):
        scope_rotation_inputs(scoped, hierarchy, jobs, line, "missing", True)


def test_readiness_requires_complete_observation_but_accepts_real_zero_risk() -> None:
    """Diagnostics distinguish missing coefficients, unstaffed blocks and valid zero.

    Args:
        None.

    Returns:
        None; these basic checks make no solver feasibility or optimization claim.
    """
    _, _, risks = scenario_catalogs()
    inputs = scenario_inputs()
    assert rotation_entry_issues(inputs, risks) == ()
    partial = choose_observed_rotation(inputs, True).inputs
    assert "schedule" in rotation_entry_issues(partial, risks)
    observed = replace(inputs, baseline=balanced_rows(inputs))
    assert rotation_entry_issues(observed, risks) == ()
    missing = replace(risks, values=())
    assert "coefficients" in rotation_entry_issues(observed, missing)
    duplicate = replace(
        observed,
        baseline=tuple(
            replace(r, target_keys=(inputs.targets[0].key,) * 2)
            for r in observed.baseline
        ),
    )
    assert "staffing" in rotation_entry_issues(duplicate, risks)
    assert set(rotation_entry_issues(RotationInputs(), risks)) == {
        "date",
        "timing",
        "participants",
        "jobs",
    }


def test_empty_observed_draft_cannot_be_an_accepted_workerless_run() -> None:
    """Keep incomplete drafts separate from accepted run staffing requirements.

    Args:
        None.

    Returns:
        None; the run rejects zero workers even when draft shape is intentionally empty.
    """
    from tests.test_rotation_scenarios import scenario_with_run

    run = scenario_with_run().run
    empty = replace(run.inputs, workers=(), targets=(), baseline=(), proposed=())
    with pytest.raises(ValueError, match="participating"):
        replace(run, inputs=empty, arrangement=(), coefficients=(), worker_labels=())


def test_independent_clocks_preserve_breaks_and_unequal_prefixes() -> None:
    """Clock origin/span edits are copies with exact retained relative minute semantics.

    Args:
        None.

    Returns:
        None; invalid shortening cannot rescale entered blocks or erase breaks.
    """
    from ergotools.application.rotation_entry import reclock_rotation_inputs
    from ergotools.domain.rotation_timing import (
        MinuteInterval,
        RotationTiming,
        TimedBreak,
    )

    old = scenario_inputs()
    night = reclock_rotation_inputs(old, 1320, 360).inputs
    assert night.start_minute == 1320 and night.timing == old.timing
    assert old.start_minute == 480
    untimed = reclock_rotation_inputs(RotationInputs(baseline=()), 0, 480).inputs
    assert untimed.timing.block_minutes == (120,) * 4 and untimed.baseline == ()
    pauses = (TimedBreak(MinuteInterval(240, 300), "Lunch"),)
    unequal = replace(old, timing=RotationTiming(480, pauses, (120, 300), False, False))
    changed = reclock_rotation_inputs(unequal, 480, 1020).inputs
    assert changed.timing.block_minutes == (120, 360)
    assert changed.timing.breaks == pauses and not changed.timing.subtract_breaks
    with pytest.raises(ValueError):
        reclock_rotation_inputs(unequal, 480, 600)
    for first, last in [(-1, 0), (0, 1440), (False, 480)]:
        with pytest.raises(ValueError):
            reclock_rotation_inputs(old, first, last)


def test_structural_timing_edits_keep_untouched_spans_and_warn_for_changed_cells() -> (
    None
):
    """Splits/joins never relabel a later assignment as an unrelated earlier block.

    Args:
        None.

    Returns:
        None; changed blocks become explicit None and all discarded source cells count.
    """
    from ergotools.application.rotation_entry import reshape_timed_rotation_inputs
    from ergotools.application.rotation_timing_actions import (
        join_work_blocks,
        split_work_block,
    )

    original = scenario_inputs()
    rows = balanced_rows(original)
    original = replace(original, baseline=rows, proposed=rows)
    split = split_work_block(original.timing, 120)
    change = reshape_timed_rotation_inputs(original, split, original.start_minute)
    a, b = (t.key for t in original.targets)
    assert change.inputs.baseline == (
        RotationDraftRow("W1", (None, None, b)),
        RotationDraftRow("W2", (None, None, a)),
    )
    assert len(change.lost_cells) == 4
    assert all(item[2] == 1 for item in change.lost_cells)
    timing = equal_timing(480, 4)
    four = replace(
        original,
        timing=timing,
        baseline=(
            RotationDraftRow("W1", (a, b, a, b)),
            RotationDraftRow("W2", (b, a, b, a)),
        ),
        proposed=None,
    )
    joined = reshape_timed_rotation_inputs(
        four, join_work_blocks(timing, 2), four.start_minute
    )
    assert joined.inputs.baseline == (
        RotationDraftRow("W1", (a, None, b)),
        RotationDraftRow("W2", (b, None, a)),
    )
    assert len(joined.lost_cells) == 4
    assert {item[2] for item in joined.lost_cells} == {2, 3}

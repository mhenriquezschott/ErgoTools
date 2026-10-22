"""Pure workplace-selection changes preserving existing placement history.

Application layer. Compose immutable domain values through injected read/write ports.
This module owns no widgets, SQL connection, global clock or renderer; persistence and
modal consent belong to its caller.
"""

from collections.abc import Iterable
from dataclasses import replace

from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.job_catalog import JobCatalog, JobPlacement


def replace_active_placements(
    catalog: JobCatalog, job_id: str, workplaces: Iterable[WorkplaceContext]
) -> JobCatalog:
    """Apply the Job Management selection without moving worker assignments.

    Removed placements become inactive. Newly selected workplaces reactivate the
    highest-ID inactive placement, retaining dates and notes, or receive a new
    placement. Job activity does not gate this reference operation. Duplicate selections
    collapse; empty selection makes the job organization-neutral.

    New IDs follow the snapshot maximum in deterministic workplace order. Commit through
    workspace expected-value replacement to reject competing writers. The repository
    checks hierarchy membership under its write lock. This pure operation does not save,
    change dates, delete records or transfer assessments.

    Args:
        catalog: Validated immutable catalog with retained placement and assignment
            history.
        job_id: Exact saved job identity whose placement selection changes.
        workplaces: Typed workplace choices; duplicates collapse and empty selection
            makes the job organization-neutral.

    Returns:
        Complete replacement catalog; unchanged original for an identical active
        selection.

    Raises:
        ValueError: The job is absent, a workplace is untyped or the resulting catalog
            is invalid.
    """
    if not any(job.job_id == job_id for job in catalog.jobs):
        raise ValueError("Job does not exist.")
    requested = frozenset(workplaces)
    if any(not isinstance(place, WorkplaceContext) for place in requested):
        raise ValueError("Workplace selections require typed contexts.")
    current = {
        item.workplace
        for item in catalog.placements
        if item.job_id == job_id and item.active
    }
    if requested == current:
        return catalog
    placements = [
        replace(item, active=False)
        if item.job_id == job_id and item.active and item.workplace not in requested
        else item
        for item in catalog.placements
    ]
    next_id = max((item.placement_id for item in placements), default=0) + 1
    added = sorted(
        requested - current,
        key=lambda place: (
            place.plant_name,
            place.section_name,
            place.line_name,
            place.station_id,
            place.shift_id,
        ),
    )
    for place in added:
        candidates = [
            item
            for item in placements
            if item.job_id == job_id and item.workplace == place and not item.active
        ]
        if candidates:
            selected = max(candidates, key=lambda item: item.placement_id)
            placements = [
                replace(item, active=True) if item is selected else item
                for item in placements
            ]
        else:
            placements.append(JobPlacement(next_id, job_id, place))
            next_id += 1
    return replace(catalog, placements=tuple(placements))

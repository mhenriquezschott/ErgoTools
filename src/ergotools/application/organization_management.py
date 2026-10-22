"""Pure organization edits composed with existing hierarchy reference protection.

Application layer. Compose immutable domain values through injected read/write ports.
This module owns no widgets, SQL connection, global clock or renderer; persistence and
modal consent belong to its caller.
"""

from dataclasses import replace

from ergotools.domain.job_catalog import JobCatalog
from ergotools.domain.organization_record import OrganizationKind, OrganizationRecord
from ergotools.domain.work_catalog import StationKey
from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy


def organization_keys(
    hierarchy: WorkHierarchy, kind: OrganizationKind
) -> tuple[tuple[str, ...], ...]:
    """Return exact scoped identities in saved order, including empty parents.

    Args:
        hierarchy: Validated saved hierarchy including independent shifts and empty
            parents.
        kind: Organization level whose full scoped identities are requested.

    Returns:
        Scoped identity tuples in saved order; plant and shift identities have one
        component.
    """
    match kind:
        case OrganizationKind.PLANT:
            return tuple((p,) for p in hierarchy.plants)
        case OrganizationKind.SECTION:
            return tuple((s.plant_name, s.section_name) for s in hierarchy.sections)
        case OrganizationKind.LINE:
            return tuple(
                (line.plant_name, line.section_name, line.line_name)
                for line in hierarchy.lines
            )
        case OrganizationKind.STATION:
            return tuple(
                (s.plant_name, s.section_name, s.line_name, s.station_id)
                for s in hierarchy.work.stations
            )
        case OrganizationKind.SHIFT:
            return tuple((s,) for s in hierarchy.work.shifts)


def save_organization(
    hierarchy: WorkHierarchy, record: OrganizationRecord, *, creating: bool
) -> WorkHierarchy:
    """Create/update one record; reject missing parents, duplicates and renames.

    Storage commits through workspace.replace_hierarchy, retaining the existing guards
    for assignments, placements and assessments. This function does no I/O.

    Args:
        hierarchy: Immutable original hierarchy to modify in memory.
        record: Validated exact identity and descriptive fields; renaming an existing
            identity is not supported.
        creating: True requires an absent identity; False requires an existing identity.

    Returns:
        Complete replacement hierarchy with the one created/updated descriptive record.

    Raises:
        ValueError: Identity availability disagrees with creating, a required parent is
            absent, or replacement hierarchy constraints fail.
    """
    present = record.keys in organization_keys(hierarchy, record.kind)
    if creating == present:
        raise ValueError("Organization identifier already exists or is unavailable.")
    result = hierarchy
    if creating:
        match record.kind:
            case OrganizationKind.PLANT:
                result = replace(hierarchy, plants=(*hierarchy.plants, record.keys[0]))
            case OrganizationKind.SECTION:
                result = replace(
                    hierarchy, sections=(*hierarchy.sections, SectionKey(*record.keys))
                )
            case OrganizationKind.LINE:
                result = replace(
                    hierarchy, lines=(*hierarchy.lines, LineKey(*record.keys))
                )
            case OrganizationKind.STATION:
                result = replace(
                    hierarchy,
                    work=replace(
                        hierarchy.work,
                        stations=(*hierarchy.work.stations, StationKey(*record.keys)),
                    ),
                )
            case OrganizationKind.SHIFT:
                result = replace(
                    hierarchy,
                    work=replace(
                        hierarchy.work, shifts=(*hierarchy.work.shifts, record.keys[0])
                    ),
                )
    records = tuple(
        r for r in result.organization if (r.kind, r.keys) != (record.kind, record.keys)
    )
    return replace(result, organization=(*records, record))


def delete_organization(
    hierarchy: WorkHierarchy, kind: OrganizationKind, keys: tuple[str, ...]
) -> WorkHierarchy:
    """Remove an unreferenced subtree; repository guards protect saved consumers.

    Args:
        hierarchy: Immutable hierarchy whose subtree is removed in memory.
        kind: Selected organization level; shifts are independent of plant subtrees.
        keys: Full exact scoped identity, including every parent component.

    Returns:
        Replacement hierarchy without that subtree and its descriptive records;
        saved-reference validation still belongs to the repository.

    Raises:
        ValueError: The selected identity no longer exists or the resulting hierarchy is
            invalid.
    """
    if keys not in organization_keys(hierarchy, kind):
        raise ValueError("Selected organization record no longer exists.")
    if kind is OrganizationKind.SHIFT:
        return replace(
            hierarchy,
            work=replace(
                hierarchy.work,
                shifts=tuple(s for s in hierarchy.work.shifts if s != keys[0]),
            ),
            organization=tuple(
                r for r in hierarchy.organization if (r.kind, r.keys) != (kind, keys)
            ),
        )

    def retained(record_keys: tuple[str, ...]) -> bool:
        """Pure local subtree predicate; no storage or mutation.

        Args:
            record_keys: Full candidate identity in the same hierarchy.

        Returns:
            True when the candidate is outside the selected identity prefix and should
            remain.
        """
        return record_keys[: len(keys)] != keys

    return replace(
        hierarchy,
        plants=tuple(p for p in hierarchy.plants if retained((p,))),
        sections=tuple(
            s for s in hierarchy.sections if retained((s.plant_name, s.section_name))
        ),
        lines=tuple(
            line
            for line in hierarchy.lines
            if retained((line.plant_name, line.section_name, line.line_name))
        ),
        work=replace(
            hierarchy.work,
            stations=tuple(
                s
                for s in hierarchy.work.stations
                if retained((s.plant_name, s.section_name, s.line_name, s.station_id))
            ),
        ),
        organization=tuple(
            r
            for r in hierarchy.organization
            if r.kind is OrganizationKind.SHIFT or retained(r.keys)
        ),
    )


def plant_shift_count(jobs: JobCatalog, plant_name: str) -> int:
    """Count distinct shifts in use by active Jobs or worker workplaces in one Plant.

    Project-wide unused Shift definitions do not establish Plant membership. Repeated
    stations, Jobs and workers at the same shift count once. Activity follows existing
    explicit flags, never inferred dates; unclassified active workers also count.

    Args:
        jobs: Validated project Job placements and worker workplace assignments.
        plant_name: Exact Plant identity, preserving case and meaningful whitespace.

    Returns:
        Number of unique shift IDs used in the Plant; zero without a qualifying link.
        Closed/inactive assignments and inactive Job/placement links do not count.
    """
    active_jobs = {job.job_id for job in jobs.jobs if job.active}
    shifts = {
        placement.workplace.shift_id
        for placement in jobs.placements
        if placement.active
        and placement.job_id in active_jobs
        and placement.workplace.plant_name == plant_name
    }
    shifts.update(
        assignment.worker.workplace.shift_id
        for assignment in jobs.assignments
        if assignment.active and assignment.worker.workplace.plant_name == plant_name
    )
    return len(shifts)

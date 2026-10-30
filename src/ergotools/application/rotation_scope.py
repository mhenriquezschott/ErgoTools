"""Read-only JROT station/shift options from saved project catalogs.

Application layer. Compose immutable domain values through injected read/write ports.
This module owns no widgets, SQL connection, global clock or renderer; persistence and
modal consent belong to its caller.
"""

from dataclasses import dataclass
from typing import Protocol

from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.job_catalog import JobCatalog
from ergotools.domain.work_hierarchy import WorkHierarchy


class RotationScopeReader(Protocol):
    """Supply the saved hierarchy and job pool without project writes."""

    def load_hierarchy(self) -> WorkHierarchy:
        """Read exact station, independent shift and worker identities.

        Borrow the owning repository; do not create connections or change project data.

        Args:
            None.

        Returns:
            Saved hierarchy with exact station, independent shift and worker identities.
        """
        ...

    def load_jobs(self) -> JobCatalog:
        """Read placements including inactive historical records.

        Read only; project write and connection ownership remain with the repository.

        Args:
            None.

        Returns:
            Saved job catalog including inactive historical placements.
        """
        ...


@dataclass(frozen=True, slots=True)
class RotationScopeOptions:
    """Original-form scope choices.

    A shift with only inactive jobs remains listed, while selectable contexts require
    active jobs. Current Job risk availability is checked when building the pool.

    Attributes:
        shifts: Unique active-placement shift identities in case-insensitive order.
        contexts: Unique active-job workplace identities in deterministic
            case-insensitive order.
    """

    shifts: tuple[str, ...]
    contexts: tuple[WorkplaceContext, ...]


def rotation_scope_options(repository: RotationScopeReader) -> RotationScopeOptions:
    """Read saved catalog options without opening another connection or migrating.

    Repeated active job placements in one workplace produce one station choice.
    Candidate identity is the full workplace tuple, never translated captions.

    Args:
        repository: Borrowed read-only ports for the same project hierarchy and job
            catalog.

    Returns:
        Case-insensitive sorted shifts from active placements and unique contexts whose
        placements and jobs are active.

    Raises:
        ValueError: The job catalog references a different project or absent hierarchy
            identities.
    """
    hierarchy = repository.load_hierarchy()
    jobs = repository.load_jobs()
    jobs.validate_hierarchy(hierarchy)
    active_jobs = {job.job_id for job in jobs.jobs if job.active}
    placements = tuple(item for item in jobs.placements if item.active)
    shifts = tuple(
        sorted({item.workplace.shift_id for item in placements}, key=str.casefold)
    )
    contexts = {item.workplace for item in placements if item.job_id in active_jobs}
    return RotationScopeOptions(
        shifts,
        tuple(
            sorted(
                contexts,
                key=lambda item: (
                    item.plant_name.casefold(),
                    item.section_name.casefold(),
                    item.line_name.casefold(),
                    item.station_id.casefold(),
                    item.shift_id.casefold(),
                ),
            )
        ),
    )

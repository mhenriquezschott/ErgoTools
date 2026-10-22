"""Typed job/placement/assignment snapshots preserving reference relationships.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from dataclasses import dataclass

from ergotools.domain.assessments.context import (
    WorkerContext,
    WorkplaceContext,
    _require_identity,
)
from ergotools.domain.work_catalog import StationKey
from ergotools.domain.work_hierarchy import WorkHierarchy


def _record(record_id: int, active: bool) -> None:
    """Require explicit integer record identity and boolean activity.

    Args:
        record_id: Exact integer database identity; booleans and implicit numeric
            coercions are rejected.
        active: Explicit boolean activity flag; no truthiness conversion is performed.

    Returns:
        None. Return normally only when the stated validation succeeds; invalid data
        raises instead.

    Raises:
        ValueError: Record IDs and activity flags require int and bool.
    """
    if type(record_id) is not int or type(active) is not bool:
        raise ValueError("Record IDs and activity flags require int and bool.")


def _texts(*values: str | None) -> None:
    """Validate optional job metadata without trimming or replacing absent values.

    Args:
        values: Optional job metadata strings; None and empty strings are retained.

    Returns:
        None. Return normally only when the stated validation succeeds; invalid data
        raises instead.

    Raises:
        ValueError: Optional metadata must be text or absent.
    """
    if any(value is not None and not isinstance(value, str) for value in values):
        raise ValueError("Optional metadata must be text or absent.")


def _dates(start: str | None, end: str | None, notes: str | None) -> None:
    """Validate optional date/note text and preserve reference lexical date ordering.

    Args:
        start: Optional saved start-date text; ordering follows the reference lexical
            comparison.
        end: Optional saved end-date text; comparison occurs only when both bounds are
            present.
        notes: Optional unchanged note text; None remains distinct from an empty string.

    Returns:
        None. Return normally only when the stated validation succeeds; invalid data
        raises instead.

    Raises:
        ValueError: Date range is reversed.
    """
    _texts(start, end, notes)
    if start is not None and end is not None and start > end:
        raise ValueError("Date range is reversed.")


@dataclass(frozen=True, slots=True)
class Job:
    """Stable job identity and display metadata, separate from current risk values.

    Attributes:
        job_id: Literal saved job identity, independent of the displayed job name.
        name: Saved display name; identity is held separately and domain operations
            define trimming policy.
        active: Explicit activity flag; historical references can retain inactive
            records.
        description: Optional saved description; None is distinct from an empty string.
    """

    job_id: str
    name: str
    active: bool = True
    description: str | None = None

    def __post_init__(self) -> None:
        """Preserve empty names allowed by SQL while requiring a stable job ID.

        Args:
            None. Dataclass construction supplies the fields documented on Job.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: Job name and activity require text and bool.
        """
        _require_identity(self.job_id)
        if not isinstance(self.name, str) or type(self.active) is not bool:
            raise ValueError("Job name and activity require text and bool.")
        _texts(self.description)


@dataclass(frozen=True, slots=True)
class JobPlacement:
    """One job at an exact workplace, retaining reference text date bounds.

    Attributes:
        placement_id: Exact integer saved placement identity; membership is validated
            against the hierarchy.
        job_id: Literal saved job identity, independent of the displayed job name.
        workplace: Typed plant/section/line/station/shift ownership.
        active: Explicit activity flag; historical references can retain inactive
            records.
        valid_from: Optional saved start-date text with reference lexical ordering.
        valid_to: Optional saved end-date text, not earlier lexically than a present
            start.
        notes: Optional evidence or relationship note, retained as saved text.
    """

    placement_id: int
    job_id: str
    workplace: WorkplaceContext
    active: bool = True
    valid_from: str | None = None
    valid_to: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        """Validate typed fields and reference lexical date ordering.

        Args:
            None. Dataclass construction supplies the fields documented on JobPlacement.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: Placement requires a typed workplace.
        """
        _record(self.placement_id, self.active)
        _require_identity(self.job_id)
        if not isinstance(self.workplace, WorkplaceContext):
            raise ValueError("Placement requires a typed workplace.")
        _dates(self.valid_from, self.valid_to, self.notes)


@dataclass(frozen=True, slots=True)
class WorkerJobAssignment:
    """Worker ownership with optional placement and retained assignment history.

    Attributes:
        assignment_id: Exact saved integer assignment identity, including closed
            historical assignments.
        worker: Typed project/worker/workplace owner.
        placement_id: Exact job-placement identity; None means an unclassified
            assignment or an unplaced rotation target.
        active: Explicit activity flag; historical references can retain inactive
            records.
        started_at: Optional saved assignment start-date text with reference lexical
            ordering.
        ended_at: Optional assignment end-date text, not earlier lexically than a
            present start.
        notes: Optional evidence or relationship note, retained as saved text.
    """

    assignment_id: int
    worker: WorkerContext
    placement_id: int | None
    active: bool = True
    started_at: str | None = None
    ended_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        """Reject implicit IDs/flags and reversed reference date ranges.

        Args:
            None. Dataclass construction supplies the fields documented on
            WorkerJobAssignment.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: Assignment requires typed worker ownership. Placement ID must be
                an integer or absent.
        """
        _record(self.assignment_id, self.active)
        if not isinstance(self.worker, WorkerContext):
            raise ValueError("Assignment requires typed worker ownership.")
        if self.placement_id is not None and type(self.placement_id) is not int:
            raise ValueError("Placement ID must be an integer or absent.")
        _dates(self.started_at, self.ended_at, self.notes)


@dataclass(frozen=True, slots=True)
class JobCatalog:
    """Project snapshot without implicit reassignment or date filtering.

    Attributes:
        project_id: Nonblank saved project identity, never derived from a file name.
        jobs: Immutable project job, placement and assignment snapshot.
        placements: Ordered job-to-workplace placement records, retaining inactive
            history.
        assignments: Ordered worker/job assignment records; unclassified and closed
            assignments are retained.
    """

    project_id: str
    jobs: tuple[Job, ...] = ()
    placements: tuple[JobPlacement, ...] = ()
    assignments: tuple[WorkerJobAssignment, ...] = ()

    def __post_init__(self) -> None:
        """Reject ambiguous identities, dangling links and active-history conflicts.

        Args:
            None. Dataclass construction supplies the fields documented on JobCatalog.

        Returns:
            None. Construction validates this record before publishing it. Snapshot
            jobs, placements, assignments as immutable tuples on the new frozen
            instance.

        Raises:
            ValueError: Duplicate job catalog identity. Catalog records must have
                explicit types. Placement references a missing job. Assignment belongs
                to another project. Assignment and placement contexts must match.
                Multiple active assignments for one worker context. Active job
                placements may not overlap.
        """
        _require_identity(self.project_id)
        object.__setattr__(self, "jobs", tuple(self.jobs))
        object.__setattr__(self, "placements", tuple(self.placements))
        object.__setattr__(self, "assignments", tuple(self.assignments))
        for values, kind in (
            (self.jobs, Job),
            (self.placements, JobPlacement),
            (self.assignments, WorkerJobAssignment),
        ):
            if any(not isinstance(value, kind) for value in values):
                raise ValueError("Catalog records must have explicit types.")
        jobs = {job.job_id for job in self.jobs}
        placements = {item.placement_id: item for item in self.placements}
        if (
            len(jobs) != len(self.jobs)
            or len(placements) != len(self.placements)
            or len({item.assignment_id for item in self.assignments})
            != len(self.assignments)
        ):
            raise ValueError("Duplicate job catalog identity.")
        active_placements: list[JobPlacement] = []
        for item in self.placements:
            if item.job_id not in jobs:
                raise ValueError("Placement references a missing job.")
            if item.active:
                for prior in active_placements:
                    if (
                        (prior.job_id, prior.workplace) == (item.job_id, item.workplace)
                        and (
                            prior.valid_from
                            if prior.valid_from is not None
                            else "0001-01-01"
                        )
                        <= (
                            item.valid_to if item.valid_to is not None else "9999-12-31"
                        )
                        and (
                            item.valid_from
                            if item.valid_from is not None
                            else "0001-01-01"
                        )
                        <= (
                            prior.valid_to
                            if prior.valid_to is not None
                            else "9999-12-31"
                        )
                    ):
                        raise ValueError("Active job placements may not overlap.")
                active_placements.append(item)
        active_workers: set[WorkerContext] = set()
        for assignment in self.assignments:
            if assignment.worker.project_id != self.project_id:
                raise ValueError("Assignment belongs to another project.")
            if assignment.placement_id is not None:
                placement = placements.get(assignment.placement_id)
                if (
                    placement is None
                    or placement.workplace != assignment.worker.workplace
                ):
                    raise ValueError("Assignment and placement contexts must match.")
            if assignment.active:
                if assignment.worker in active_workers:
                    raise ValueError(
                        "Multiple active assignments for one worker context."
                    )
                active_workers.add(assignment.worker)

    def validate_hierarchy(self, hierarchy: WorkHierarchy) -> None:
        """Require all historical and active references to exist in the catalog.

        Args:
            hierarchy: Complete project hierarchy, including empty parents and
                independent shifts.

        Returns:
            None. Return normally only when the stated validation succeeds; invalid data
            raises instead.

        Raises:
            ValueError: Job catalog belongs to another project. Placement references a
                missing workplace.
            KeyError: A retained assignment refers to a missing worker or complete
                workplace in the hierarchy.
        """
        if self.project_id != hierarchy.work.project_id:
            raise ValueError("Job catalog belongs to another project.")
        for item in self.placements:
            place = item.workplace
            if (
                StationKey(
                    place.plant_name,
                    place.section_name,
                    place.line_name,
                    place.station_id,
                )
                not in hierarchy.work.stations
                or place.shift_id not in hierarchy.work.shifts
            ):
                raise ValueError("Placement references a missing workplace.")
        for assignment in self.assignments:
            hierarchy.work.worker_context(
                assignment.worker.worker_id, assignment.worker.workplace
            )

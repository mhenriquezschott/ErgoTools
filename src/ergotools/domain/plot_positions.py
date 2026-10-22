"""Original-image pixel geometry owned by stations and worker assignments.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from dataclasses import dataclass, replace
from enum import StrEnum
from math import isfinite

from ergotools.domain.assessments.context import _require_identity
from ergotools.domain.job_catalog import JobCatalog
from ergotools.domain.work_catalog import StationKey
from ergotools.domain.work_hierarchy import WorkHierarchy


def _number(value: float, minimum: float | None = None) -> None:
    """Validate a geometry number and its optional inclusive lower bound.

    Args:
        value: Source quantity to validate; None denotes absence rather than numeric
            zero.
        minimum: Optional inclusive lower limit in the same units as value; None imposes
            no lower bound.

    Returns:
        None. Return normally only when the stated validation succeeds; invalid data
        raises instead.

    Raises:
        ValueError: PLOT geometry requires finite numbers in the allowed range.
    """
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(value)
        or (minimum is not None and value < minimum)
    ):
        raise ValueError("PLOT geometry requires finite numbers in the allowed range.")


@dataclass(frozen=True, slots=True)
class PlotPoint:
    """Unscaled original-image pixel coordinates; negative values remain allowed.

    Attributes:
        x: Horizontal coordinate in unscaled original-image pixels; negative coordinates
            remain allowed.
        y: Vertical coordinate in unscaled original-image pixels; negative coordinates
            remain allowed.
    """

    x: float
    y: float

    def __post_init__(self) -> None:
        """Reject boolean, nonnumeric and nonfinite coordinates.

        Args:
            None. Dataclass construction supplies the fields documented on PlotPoint.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: The typed record or one of its referenced identities violates
                the invariants described above.
        """
        _number(self.x)
        _number(self.y)


class StationPositionSource(StrEnum):
    """Original station anchor provenance, independent of translated captions."""

    # Anchor explicitly positioned by the user.
    MANUAL = "manual"
    # Anchor initialized from the first saved worker point.
    WORKER = "worker"
    # Anchor provenance inherited from reference job positioning.
    JOB = "job"
    # Anchor imported by the external project converter.
    MIGRATION = "migration"


class WorkerPositionSource(StrEnum):
    """Original worker marker provenance; unplaced means absent coordinates."""

    # Marker has no coordinates; never fabricate an origin point.
    UNPLACED = "unplaced"
    # Initial worker point inherited from its station anchor.
    STATION_ANCHOR = "station_anchor"
    # Worker point explicitly saved by the user.
    MANUAL = "manual"
    # Worker point imported by the external project converter.
    MIGRATION = "migration"


@dataclass(frozen=True, slots=True)
class StationPosition:
    """One full station identity shared across its placements and shifts.

    Attributes:
        station: Complete station ancestry; all shifts/placements share its anchor.
        point: Typed coordinate in unscaled original-image pixels.
        source: Explicit position provenance, never inferred from localized captions.
    """

    station: StationKey
    point: PlotPoint
    source: StationPositionSource = StationPositionSource.MANUAL

    def __post_init__(self) -> None:
        """Require exact typed station, original-pixel point and provenance.

        Args:
            None. Dataclass construction supplies the fields documented on
            StationPosition.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: Station positions require typed identity and geometry.
        """
        if (
            not isinstance(self.station, StationKey)
            or not isinstance(self.point, PlotPoint)
            or not isinstance(self.source, StationPositionSource)
        ):
            raise ValueError("Station positions require typed identity and geometry.")


@dataclass(frozen=True, slots=True)
class WorkerAssignmentMarker:
    """Assignment-owned position/style shared across its assessment tools.

    Size and thickness are original pixels; scale is dimensionless.
    Locked/visible/enabled are independent flags. Creation is hidden by default.

    Attributes:
        assignment_id: Exact saved integer assignment identity, including closed
            historical assignments.
        point: Original-image pixel point, or None only with explicitly unplaced
            provenance.
        size: Positive marker size in original-image pixels.
        scale: Positive dimensionless marker scale multiplier.
        line_thickness: Nonnegative marker outline width in original-image pixels.
        locked: Explicit flag controlling whether the marker can be dragged.
        visible: Explicit marker visibility flag; newly created markers start hidden.
        enabled: Explicit marker enablement for analysis; independent of visibility and
            dragging lock.
        source: Explicit position provenance, never inferred from localized captions.
    """

    assignment_id: int
    point: PlotPoint | None = None
    size: float = 50
    scale: float = 1
    line_thickness: float = 1
    locked: bool = False
    visible: bool = False
    enabled: bool = True
    source: WorkerPositionSource = WorkerPositionSource.UNPLACED

    def __post_init__(self) -> None:
        """Retain original constraints without coercing malformed flags or points.

        Args:
            None. Dataclass construction supplies the fields documented on
            WorkerAssignmentMarker.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: Worker marker requires an integer assignment ID. Worker marker
                size and scale must be positive. Worker marker flags require bool.
                Worker marker requires typed point and provenance. Only unplaced markers
                can have absent coordinates.
        """
        if type(self.assignment_id) is not int:
            raise ValueError("Worker marker requires an integer assignment ID.")
        for value in (self.size, self.scale, self.line_thickness):
            _number(value, 0)
        if self.size == 0 or self.scale == 0:
            raise ValueError("Worker marker size and scale must be positive.")
        if any(
            type(value) is not bool
            for value in (self.locked, self.visible, self.enabled)
        ):
            raise ValueError("Worker marker flags require bool.")
        if not isinstance(self.source, WorkerPositionSource) or (
            self.point is not None and not isinstance(self.point, PlotPoint)
        ):
            raise ValueError("Worker marker requires typed point and provenance.")
        if (self.source is WorkerPositionSource.UNPLACED) != (self.point is None):
            raise ValueError("Only unplaced markers can have absent coordinates.")


def assignment_station(jobs: JobCatalog, assignment_id: int) -> StationKey:
    """Resolve active or historical assignment ancestry without successor fallback.

    Args:
        jobs: Immutable job, placement and assignment catalog for the same project.
        assignment_id: Exact saved assignment identity; closed assignments remain
            addressable.

    Returns:
        Exact original station ancestry from the named assignment, independent of
        activity or successor assignments.

    Raises:
        ValueError: Assignment ID requires int.
        KeyError: The requested saved identity or required catalog member does not
            exist.
    """
    if type(assignment_id) is not int:
        raise ValueError("Assignment ID requires int.")
    assignment = next(
        (item for item in jobs.assignments if item.assignment_id == assignment_id), None
    )
    if assignment is None:
        raise KeyError(assignment_id)
    place = assignment.worker.workplace
    return StationKey(
        place.plant_name, place.section_name, place.line_name, place.station_id
    )


@dataclass(frozen=True, slots=True)
class PlotPositions:
    """Immutable project geometry without renderer, unit conversion or I/O.

    Attributes:
        project_id: Nonblank saved project identity, never derived from a file name.
        stations: Ordered exact station anchor records with no duplicate station
            identities.
        workers: Ordered assignment-owned marker records with unique assignment IDs.
    """

    project_id: str
    stations: tuple[StationPosition, ...] = ()
    workers: tuple[WorkerAssignmentMarker, ...] = ()

    def __post_init__(self) -> None:
        """Reject duplicate/untyped geometry rather than merge conflicting rows.

        Args:
            None. Dataclass construction supplies the fields documented on
            PlotPositions.

        Returns:
            None. Construction validates this record before publishing it. Snapshot
            stations, workers as immutable tuples on the new frozen instance.

        Raises:
            ValueError: PLOT geometry requires typed records. Duplicate PLOT geometry
                identity.
        """
        _require_identity(self.project_id)
        object.__setattr__(self, "stations", tuple(self.stations))
        object.__setattr__(self, "workers", tuple(self.workers))
        if any(not isinstance(item, StationPosition) for item in self.stations) or any(
            not isinstance(item, WorkerAssignmentMarker) for item in self.workers
        ):
            raise ValueError("PLOT geometry requires typed records.")
        if len({item.station for item in self.stations}) != len(self.stations) or len(
            {item.assignment_id for item in self.workers}
        ) != len(self.workers):
            raise ValueError("Duplicate PLOT geometry identity.")

    def validate(self, hierarchy: WorkHierarchy, jobs: JobCatalog) -> None:
        """Reject foreign projects and missing station/assignment ownership.

        Args:
            hierarchy: Complete project hierarchy, including empty parents and
                independent shifts.
            jobs: Immutable job, placement and assignment catalog for the same project.

        Returns:
            None. Return normally only when the stated validation succeeds; invalid data
            raises instead.

        Raises:
            ValueError: PLOT positions belong to another project.
            KeyError: A saved worker marker references an assignment absent from jobs.
        """
        self.validate_hierarchy(hierarchy)
        if jobs.project_id != self.project_id:
            raise ValueError("PLOT positions belong to another project.")
        for marker in self.workers:
            assignment_station(jobs, marker.assignment_id)

    def validate_hierarchy(self, hierarchy: WorkHierarchy) -> None:
        """Require station membership without silently deleting geometry.

        Args:
            hierarchy: Complete project hierarchy, including empty parents and
                independent shifts.

        Returns:
            None. Return normally only when the stated validation succeeds; invalid data
            raises instead.

        Raises:
            ValueError: PLOT positions reference an unavailable station/project.
        """
        if hierarchy.work.project_id != self.project_id or any(
            item.station not in hierarchy.work.stations for item in self.stations
        ):
            raise ValueError("PLOT positions reference an unavailable station/project.")

    def validate_job_change(self, current: JobCatalog, replacement: JobCatalog) -> None:
        """Protect referenced assignment identity while allowing activity changes.

        Args:
            current: Previously saved job/assignment catalog whose referenced identities
                must be preserved.
            replacement: Proposed immutable replacement catalog; referenced ownership
                cannot be rewritten.

        Returns:
            None. Return normally only when the stated validation succeeds; invalid data
            raises instead.

        Raises:
            ValueError: Saved markers protect their original assignments.
        """
        old = {item.assignment_id: item.worker for item in current.assignments}
        new = {item.assignment_id: item.worker for item in replacement.assignments}
        if replacement.project_id != self.project_id or any(
            new.get(item.assignment_id) != old.get(item.assignment_id)
            for item in self.workers
        ):
            raise ValueError("Saved markers protect their original assignments.")

    def station_position(self, station: StationKey) -> StationPosition | None:
        """Return exact saved ancestry; no anchor is distinct from the origin.

        Args:
            station: Complete plant/section/line/station identity; shifts share the
                station anchor.

        Returns:
            Stored station anchor, or None; an absent anchor is different from a point
            at the image origin.
        """
        return next((item for item in self.stations if item.station == station), None)

    def marker(self, assignment_id: int) -> WorkerAssignmentMarker | None:
        """Return one exact assignment marker without creating a record.

        Args:
            assignment_id: Exact saved assignment identity; closed assignments remain
                addressable.

        Returns:
            Stored assignment marker, or None; no default marker is created by lookup.

        Raises:
            ValueError: Assignment ID requires int.
        """
        if type(assignment_id) is not int:
            raise ValueError("Assignment ID requires int.")
        return next(
            (item for item in self.workers if item.assignment_id == assignment_id), None
        )

    def with_station(
        self, position: StationPosition, *, initialize_only: bool = False
    ) -> "PlotPositions":
        """Initialize once or move an anchor; leave stored worker points intact.

        Args:
            position: Typed station anchor in unscaled original-image pixels, with its
                recorded provenance.
            initialize_only: If True, retain an existing anchor; otherwise replace it.
                Worker points are unaffected.

        Returns:
            New geometry snapshot with the anchor inserted/replaced; self when
            initialize_only retains an existing anchor.

        Raises:
            ValueError: Station editing requires typed position and intent.
        """
        if (
            not isinstance(position, StationPosition)
            or type(initialize_only) is not bool
        ):
            raise ValueError("Station editing requires typed position and intent.")
        existing = self.station_position(position.station)
        if initialize_only and existing is not None:
            return self
        stations = (
            tuple(
                position if item.station == position.station else item
                for item in self.stations
            )
            if existing is not None
            else (*self.stations, position)
        )
        return replace(self, stations=stations)

    def ensure_marker(self, assignment_id: int, jobs: JobCatalog) -> "PlotPositions":
        """Create a hidden marker at its anchor or explicitly unplaced, once.

        Args:
            assignment_id: Exact saved assignment identity; closed assignments remain
                addressable.
            jobs: Immutable job, placement and assignment catalog for the same project.

        Returns:
            Geometry with one hidden marker at its station anchor or explicitly
            unplaced; self when already present.

        Raises:
            ValueError: Marker assignments belong to another project.
            KeyError: The requested assignment does not exist in the supplied jobs
                snapshot.
        """
        if jobs.project_id != self.project_id:
            raise ValueError("Marker assignments belong to another project.")
        station = assignment_station(jobs, assignment_id)
        if self.marker(assignment_id) is not None:
            return self
        anchor = self.station_position(station)
        marker = WorkerAssignmentMarker(
            assignment_id,
            anchor.point if anchor is not None else None,
            source=WorkerPositionSource.STATION_ANCHOR
            if anchor is not None
            else WorkerPositionSource.UNPLACED,
        )
        return replace(self, workers=(*self.workers, marker))

    def with_saved_marker(
        self, marker: WorkerAssignmentMarker, jobs: JobCatalog
    ) -> "PlotPositions":
        """Save a manual worker point; initialize only a missing station anchor.

        Args:
            marker: Assignment-owned point and style to save; an actual point is
                required.
            jobs: Immutable job, placement and assignment catalog for the same project.

        Returns:
            New geometry with manual worker provenance and, only if absent, an anchor
            initialized from that point.

        Raises:
            ValueError: Saving a worker requires its project and actual point.
            KeyError: The marker's assignment does not exist in the supplied jobs
                snapshot.
        """
        if (
            not isinstance(marker, WorkerAssignmentMarker)
            or jobs.project_id != self.project_id
            or marker.point is None
        ):
            raise ValueError("Saving a worker requires its project and actual point.")
        station = assignment_station(jobs, marker.assignment_id)
        existing = self.marker(marker.assignment_id)
        marker = replace(marker, source=WorkerPositionSource.MANUAL)
        workers = (
            tuple(
                marker if item.assignment_id == marker.assignment_id else item
                for item in self.workers
            )
            if existing is not None
            else (*self.workers, marker)
        )
        updated = replace(self, workers=workers)
        assert marker.point is not None
        return updated.with_station(
            StationPosition(station, marker.point, StationPositionSource.WORKER),
            initialize_only=True,
        )

    def worker_point(self, assignment_id: int, jobs: JobCatalog) -> PlotPoint | None:
        """Resolve worker point then station anchor; never fabricate origin fallback.

        Args:
            assignment_id: Exact saved assignment identity; closed assignments remain
                addressable.
            jobs: Immutable job, placement and assignment catalog for the same project.

        Returns:
            Original-image pixel point from the worker or its station anchor, or None if
            both are absent.

        Raises:
            ValueError: Marker assignments belong to another project.
            KeyError: The requested assignment does not exist; do not fall back to a
                successor.
        """
        if jobs.project_id != self.project_id:
            raise ValueError("Marker assignments belong to another project.")
        station = assignment_station(jobs, assignment_id)
        marker = self.marker(assignment_id)
        if marker is not None and marker.point is not None:
            return marker.point
        anchor = self.station_position(station)
        return anchor.point if anchor is not None else None

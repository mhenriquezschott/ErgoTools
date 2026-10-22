"""Immutable project selection data, separate from full worker and plant records.

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
from ergotools.domain.worker_details import WorkerDetails


@dataclass(frozen=True, slots=True)
class WorkerEntry:
    """Stable worker identity, optional names and independently typed details.

    Attributes:
        worker_id: Literal saved worker identity; names never establish ownership.
        first_name: Optional original first-name text; empty names remain allowed.
        last_name: Optional original last-name text; empty names remain allowed.
        details: Optional independently validated worker demographics and employment
            metadata.
    """

    worker_id: str
    first_name: str | None = None
    last_name: str | None = None
    details: WorkerDetails | None = None

    def __post_init__(self) -> None:
        """Preserve exact identifiers/names; empty optional names remain allowed.

        Args:
            None. Dataclass construction supplies the fields documented on WorkerEntry.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: Worker details require a typed record. Worker names must be
                strings or absent.
        """
        _require_identity(self.worker_id)
        if self.details is not None and not isinstance(self.details, WorkerDetails):
            raise ValueError("Worker details require a typed record.")
        if any(
            value is not None and not isinstance(value, str)
            for value in (self.first_name, self.last_name)
        ):
            raise ValueError("Worker names must be strings or absent.")


@dataclass(frozen=True, slots=True)
class StationKey:
    """Station identity includes its complete plant/section/line ancestry.

    Attributes:
        plant_name: Literal plant identity; case and nonblank whitespace are preserved.
        section_name: Literal section identity scoped by its owning plant.
        line_name: Literal line identity scoped by its plant and section.
        station_id: Literal station identity scoped by complete plant/section/line
            ancestry.
    """

    plant_name: str
    section_name: str
    line_name: str
    station_id: str

    def __post_init__(self) -> None:
        """Reject incomplete station ownership without trimming stored values.

        Args:
            None. Dataclass construction supplies the fields documented on StationKey.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: The typed record or one of its referenced identities violates
                the invariants described above.
        """
        _require_identity(
            self.plant_name, self.section_name, self.line_name, self.station_id
        )

    def at_shift(self, shift_id: str) -> WorkplaceContext:
        """Construct exact workplace ownership; the catalog validates membership.

        Args:
            shift_id: Exact nonblank project-wide shift identity; membership is checked
                by the catalog.

        Returns:
            Typed workplace snapshot combining this station ancestry and the supplied
            shift without catalog lookup.

        Raises:
            ValueError: The supplied shift identity is not a nonblank string.
        """
        return WorkplaceContext(
            self.plant_name,
            self.section_name,
            self.line_name,
            self.station_id,
            shift_id,
        )


@dataclass(frozen=True, slots=True)
class WorkCatalog:
    """Project-owned selection snapshot; not a worker or plant editing aggregate.

    Adapters supply all stations and independent shifts, including ones without
    assignments. Input order is preserved; names never establish identity. Duplicate
    identities fail rather than silently hiding conflicting records.

    Attributes:
        project_id: Nonblank saved project identity, never derived from a file name.
        workers: Ordered immutable worker records with unique identities.
        stations: Complete station identities in adapter-supplied order, including
            stations without assignments.
        shifts: Independent project-wide shift identities; no station cross-product is
            stored.
    """

    project_id: str
    workers: tuple[WorkerEntry, ...] = ()
    stations: tuple[StationKey, ...] = ()
    shifts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Snapshot collections and reject ambiguous or untyped catalog records.

        Args:
            None. Dataclass construction supplies the fields documented on WorkCatalog.

        Returns:
            None. Construction validates this record before publishing it. Snapshot
            workers, stations, shifts as immutable tuples on the new frozen instance.

        Raises:
            ValueError: Catalog workers must be typed entries. Catalog stations must be
                typed keys. Catalog identities must be unique within their scope.
        """
        _require_identity(self.project_id)
        object.__setattr__(self, "workers", tuple(self.workers))
        object.__setattr__(self, "stations", tuple(self.stations))
        object.__setattr__(self, "shifts", tuple(self.shifts))
        if any(not isinstance(worker, WorkerEntry) for worker in self.workers):
            raise ValueError("Catalog workers must be typed entries.")
        if any(not isinstance(station, StationKey) for station in self.stations):
            raise ValueError("Catalog stations must be typed keys.")
        _require_identity(*self.shifts)
        identities = (
            tuple(worker.worker_id for worker in self.workers),
            self.stations,
            self.shifts,
        )
        if any(len(set(values)) != len(values) for values in identities):
            raise ValueError("Catalog identities must be unique within their scope.")

    def available_workplaces(self) -> tuple[WorkplaceContext, ...]:
        """Return the reference station/shift cross product in binary key order.

        Empty stations or shifts yield no complete workplace. This deliberately does not
        filter job placements or worker assignments. The result may be large; adapters
        should avoid repeatedly projecting unchanged snapshots.

        Args:
            None.

        Returns:
            Complete station/shift cross product sorted by literal ancestry and shift;
            empty when either set is empty.
        """
        stations = sorted(
            self.stations,
            key=lambda station: (
                station.plant_name,
                station.section_name,
                station.line_name,
                station.station_id,
            ),
        )
        return tuple(
            station.at_shift(shift)
            for station in stations
            for shift in sorted(self.shifts)
        )

    def worker_context(
        self, worker_id: str, workplace: WorkplaceContext
    ) -> WorkerContext:
        """Validate membership before selection; missing catalog entries raise KeyError.

        This identifies a possible assessment owner, not an assignment or saved
        assessment. The workspace still resolves the persisted binding separately.

        Args:
            worker_id: Exact saved worker identity, independent of the displayed worker
                name.
            workplace: Complete station ancestry and shift to validate against this
                catalog.

        Returns:
            Typed project/worker/workplace owner after exact membership checks; no
            assignment or assessment is created.

        Raises:
            KeyError: The requested saved identity or required catalog member does not
                exist.
        """
        if not any(worker.worker_id == worker_id for worker in self.workers):
            raise KeyError(worker_id)
        station = StationKey(
            workplace.plant_name,
            workplace.section_name,
            workplace.line_name,
            workplace.station_id,
        )
        if station not in self.stations or workplace.shift_id not in self.shifts:
            raise KeyError(workplace)
        return WorkerContext(self.project_id, worker_id, workplace)

"""Transactional project-owned PLOT geometry with explicit membership validation.

Infrastructure layer. Adapt immutable domain catalogs to parameterized SQLite or
explicit JSON payloads. The owning project retains this connection, thread lifetime and
cross-feature transaction coordination. No Qt controls, automatic old-project migration
or scientific recalculation occurs here. Stored source units/measurement scales remain
unchanged. Read methods do not silently repair corrupt records; standalone writes own
rollback and composed writes require caller rollback on any failure.
"""

import sqlite3

from ergotools.domain.plot_positions import (
    PlotPoint,
    PlotPositions,
    StationPosition,
    StationPositionSource,
    WorkerAssignmentMarker,
    WorkerPositionSource,
)
from ergotools.domain.work_catalog import StationKey
from ergotools.infrastructure.job_catalog_store import _flag
from ergotools.infrastructure.lifft_store import StoreFormatError


def create_position_schema(connection: sqlite3.Connection) -> None:
    """Create geometry inside an explicit caller-owned project transaction.

    Args:
        connection: Borrowed dedicated owner-thread SQLite connection; caller retains
            close ownership and owns any enclosing transaction.

    Returns:
        None after station-anchor and assignment-marker table creation in the caller's
        transaction.

    Raises:
        sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
            transaction owner must roll back composed writes.
        RuntimeError: The operation requires an idle default-mode connection or an
            existing caller-owned transaction as specified; that precondition is not
            met.
    """
    if not connection.in_transaction:
        raise RuntimeError("Position schema requires a project transaction.")
    connection.execute(
        "CREATE TABLE plot_station_positions (plant TEXT,section TEXT,line TEXT,"
        "station TEXT,x REAL NOT NULL,y REAL NOT NULL,source TEXT NOT NULL,"
        "position INTEGER NOT NULL UNIQUE,PRIMARY KEY(plant,section,line,station))"
    )
    connection.execute(
        "CREATE TABLE plot_worker_markers (assignment_id INTEGER PRIMARY KEY,"
        "x REAL,y REAL,size REAL NOT NULL,scale REAL NOT NULL,thickness REAL NOT NULL,"
        "locked INTEGER NOT NULL,visible INTEGER NOT NULL,enabled INTEGER NOT NULL,"
        "source TEXT NOT NULL,position INTEGER NOT NULL UNIQUE)"
    )


class PlotPositionStore:
    """Borrow the project connection; caller owns transactions and membership checks."""

    def __init__(self, connection: sqlite3.Connection, project_id: str) -> None:
        """Retain identity/connection without performing reads or writes.

        Args:
            connection: Borrowed dedicated owner-thread SQLite connection; caller
                retains close ownership and owns any enclosing transaction.
            project_id: Exact stable project identity used to validate stored ownership.

        Returns:
            None; retain scope/connection without I/O.
        """
        self._connection = connection
        self._project_id = project_id

    def read(self) -> PlotPositions:
        """Validate stored geometry; malformed flags/coordinates are format errors.

        Args:
            None.

        Returns:
            Validated ordered original-image geometry and marker styling/flags,
            including absent complete point pairs.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            StoreFormatError: Stored flags, point pairs, coordinates, ownership or style
                values are malformed.
        """
        try:
            stations = tuple(
                StationPosition(
                    StationKey(*row[:4]),
                    PlotPoint(row[4], row[5]),
                    StationPositionSource(row[6]),
                )
                for row in self._connection.execute(
                    "SELECT plant,section,line,station,x,y,source "
                    "FROM plot_station_positions ORDER BY position"
                )
            )
            workers = []
            for row in self._connection.execute(
                "SELECT assignment_id,x,y,size,scale,thickness,locked,visible,enabled,"
                "source FROM plot_worker_markers ORDER BY position"
            ):
                if (row[1] is None) != (row[2] is None):
                    raise ValueError("Incomplete marker point.")
                workers.append(
                    WorkerAssignmentMarker(
                        row[0],
                        None if row[1] is None else PlotPoint(row[1], row[2]),
                        row[3],
                        row[4],
                        row[5],
                        _flag(row[6]),
                        _flag(row[7]),
                        _flag(row[8]),
                        WorkerPositionSource(row[9]),
                    )
                )
            return PlotPositions(self._project_id, stations, tuple(workers))
        except (ValueError, TypeError) as error:
            raise StoreFormatError("Invalid saved PLOT positions.") from error

    def write_in_transaction(self, positions: PlotPositions) -> None:
        """Replace validated geometry as part of one owned-project transaction.

        Args:
            positions: Validated same-project station/worker geometry in original-image
                pixels with explicit marker flags.

        Returns:
            None after replacing both ordered geometry tables inside the caller's
            transaction.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            RuntimeError: The operation requires an idle default-mode connection or an
                existing caller-owned transaction as specified; that precondition is not
                met.
            ValueError: Geometry belongs to another project.
        """
        if not self._connection.in_transaction:
            raise RuntimeError("Position writes require a project transaction.")
        if positions.project_id != self._project_id:
            raise ValueError("Position project identity does not match.")
        self._connection.execute("DELETE FROM plot_station_positions")
        self._connection.execute("DELETE FROM plot_worker_markers")
        self._connection.executemany(
            "INSERT INTO plot_station_positions VALUES (?,?,?,?,?,?,?,?)",
            [
                (
                    item.station.plant_name,
                    item.station.section_name,
                    item.station.line_name,
                    item.station.station_id,
                    item.point.x,
                    item.point.y,
                    item.source.value,
                    index,
                )
                for index, item in enumerate(positions.stations)
            ],
        )
        self._connection.executemany(
            "INSERT INTO plot_worker_markers VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    item.assignment_id,
                    item.point.x if item.point else None,
                    item.point.y if item.point else None,
                    item.size,
                    item.scale,
                    item.line_thickness,
                    int(item.locked),
                    int(item.visible),
                    int(item.enabled),
                    item.source.value,
                    index,
                )
                for index, item in enumerate(positions.workers)
            ],
        )

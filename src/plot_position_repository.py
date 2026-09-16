"""PLOT station-anchor and worker-marker persistence."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


class PlotPositionError(ValueError):
    """Raised when a PLOT position request is invalid."""


@dataclass(frozen=True, order=True)
class StationKey:
    plant_name: str
    section_name: str
    line_name: str
    station_id: str


@dataclass(frozen=True)
class StationPosition:
    key: StationKey
    x: float
    y: float
    position_source: str


@dataclass(frozen=True)
class WorkerAssignmentMarker:
    worker_assignment_id: int
    x: float | None
    y: float | None
    size: float
    scale: float
    line_thickness: float
    locked: bool
    visible: bool
    enabled: bool
    position_source: str


STATION_POSITION_SOURCES = frozenset({"manual", "worker", "job", "migration"})
WORKER_POSITION_SOURCES = frozenset(
    {"unplaced", "station_anchor", "manual", "migration"}
)


def _finite_number(value, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise PlotPositionError(f"{label} must be a number.") from error
    if number != number or number in (float("inf"), float("-inf")):
        raise PlotPositionError(f"{label} must be finite.")
    return number


def _positive_number(value, label: str, *, allow_zero: bool = False) -> float:
    number = _finite_number(value, label)
    if number < 0 or (number == 0 and not allow_zero):
        qualifier = "non-negative" if allow_zero else "greater than zero"
        raise PlotPositionError(f"{label} must be {qualifier}.")
    return number


def _station_exists(connection: sqlite3.Connection, key: StationKey) -> bool:
    return connection.execute(
        """
        SELECT 1
        FROM Station
        WHERE plant_name = ? AND section_name = ? AND line_name = ? AND id = ?
        """,
        (key.plant_name, key.section_name, key.line_name, key.station_id),
    ).fetchone() is not None


def station_key_for_assignment(
    connection: sqlite3.Connection,
    worker_assignment_id: int,
) -> StationKey:
    row = connection.execute(
        """
        SELECT context.plant_name, context.section_name, context.line_name,
               context.station_id
        FROM WorkerAssignment AS assignment
        JOIN WorkplaceContext AS context
          ON context.id = assignment.workplace_context_id
        WHERE assignment.id = ?
        """,
        (worker_assignment_id,),
    ).fetchone()
    if row is None:
        raise PlotPositionError(
            f"Worker Assignment does not exist: {worker_assignment_id}"
        )
    return StationKey(*row)


def station_position(
    connection: sqlite3.Connection,
    key: StationKey,
) -> StationPosition | None:
    row = connection.execute(
        """
        SELECT x, y, position_source
        FROM PlotStationPosition
        WHERE plant_name = ? AND section_name = ? AND line_name = ?
          AND station_id = ?
        """,
        (key.plant_name, key.section_name, key.line_name, key.station_id),
    ).fetchone()
    if row is None:
        return None
    return StationPosition(key, float(row[0]), float(row[1]), str(row[2]))


def initialize_station_position(
    connection: sqlite3.Connection,
    key: StationKey,
    x,
    y,
    *,
    position_source: str,
) -> bool:
    """Set an unknown Station anchor once and leave existing anchors unchanged."""
    if position_source not in STATION_POSITION_SOURCES:
        raise PlotPositionError(f"Invalid Station position source: {position_source}")
    if not _station_exists(connection, key):
        raise PlotPositionError(
            "Station does not exist: "
            f"{key.plant_name} / {key.section_name} / {key.line_name} / {key.station_id}"
        )
    result = connection.execute(
        """
        INSERT OR IGNORE INTO PlotStationPosition (
            plant_name, section_name, line_name, station_id,
            x, y, position_source, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            key.plant_name,
            key.section_name,
            key.line_name,
            key.station_id,
            _finite_number(x, "Station X"),
            _finite_number(y, "Station Y"),
            position_source,
        ),
    )
    return result.rowcount == 1


def set_station_position(
    connection: sqlite3.Connection,
    key: StationKey,
    x,
    y,
    *,
    position_source: str = "manual",
) -> None:
    """Create or deliberately move a Station anchor."""
    if position_source not in STATION_POSITION_SOURCES:
        raise PlotPositionError(f"Invalid Station position source: {position_source}")
    if not _station_exists(connection, key):
        raise PlotPositionError(
            "Station does not exist: "
            f"{key.plant_name} / {key.section_name} / {key.line_name} / {key.station_id}"
        )
    connection.execute(
        """
        INSERT INTO PlotStationPosition (
            plant_name, section_name, line_name, station_id,
            x, y, position_source, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT (plant_name, section_name, line_name, station_id)
        DO UPDATE SET x = excluded.x,
                      y = excluded.y,
                      position_source = excluded.position_source,
                      updated_at = CURRENT_TIMESTAMP
        """,
        (
            key.plant_name,
            key.section_name,
            key.line_name,
            key.station_id,
            _finite_number(x, "Station X"),
            _finite_number(y, "Station Y"),
            position_source,
        ),
    )


def worker_assignment_marker(
    connection: sqlite3.Connection,
    worker_assignment_id: int,
) -> WorkerAssignmentMarker | None:
    row = connection.execute(
        """
        SELECT worker_assignment_id, x, y, size, scale, line_thickness,
               locked, visible, enabled, position_source
        FROM PlotWorkerAssignmentMarker
        WHERE worker_assignment_id = ?
        """,
        (worker_assignment_id,),
    ).fetchone()
    if row is None:
        return None
    return WorkerAssignmentMarker(
        worker_assignment_id=int(row[0]),
        x=None if row[1] is None else float(row[1]),
        y=None if row[2] is None else float(row[2]),
        size=float(row[3]),
        scale=float(row[4]),
        line_thickness=float(row[5]),
        locked=bool(row[6]),
        visible=bool(row[7]),
        enabled=bool(row[8]),
        position_source=str(row[9]),
    )


def ensure_worker_assignment_marker(
    connection: sqlite3.Connection,
    worker_assignment_id: int,
) -> WorkerAssignmentMarker:
    """Create a hidden marker at its Station anchor, or as explicitly unplaced."""
    key = station_key_for_assignment(connection, worker_assignment_id)
    anchor = station_position(connection, key)
    if anchor is None:
        values = (None, None, "unplaced")
    else:
        values = (anchor.x, anchor.y, "station_anchor")
    connection.execute(
        """
        INSERT OR IGNORE INTO PlotWorkerAssignmentMarker (
            worker_assignment_id, x, y, visible, position_source
        ) VALUES (?, ?, ?, 0, ?)
        """,
        (worker_assignment_id, *values),
    )
    marker = worker_assignment_marker(connection, worker_assignment_id)
    if marker is None:
        raise PlotPositionError(
            f"Could not create marker for Worker Assignment {worker_assignment_id}."
        )
    return marker


def save_worker_assignment_marker(
    connection: sqlite3.Connection,
    worker_assignment_id: int,
    *,
    x,
    y,
    size=50,
    scale=1,
    line_thickness=1,
    locked=False,
    visible=True,
    enabled=True,
) -> WorkerAssignmentMarker:
    """Save a Worker marker and initialize its Station anchor when absent."""
    key = station_key_for_assignment(connection, worker_assignment_id)
    x_value = _finite_number(x, "Worker marker X")
    y_value = _finite_number(y, "Worker marker Y")
    ensure_worker_assignment_marker(connection, worker_assignment_id)
    connection.execute(
        """
        UPDATE PlotWorkerAssignmentMarker
        SET x = ?, y = ?, size = ?, scale = ?, line_thickness = ?,
            locked = ?, visible = ?, enabled = ?, position_source = 'manual',
            updated_at = CURRENT_TIMESTAMP
        WHERE worker_assignment_id = ?
        """,
        (
            x_value,
            y_value,
            _positive_number(size, "Worker marker size"),
            _positive_number(scale, "Worker marker scale"),
            _positive_number(
                line_thickness,
                "Worker marker line thickness",
                allow_zero=True,
            ),
            int(bool(locked)),
            int(bool(visible)),
            int(bool(enabled)),
            worker_assignment_id,
        ),
    )
    initialize_station_position(
        connection,
        key,
        x_value,
        y_value,
        position_source="worker",
    )
    marker = worker_assignment_marker(connection, worker_assignment_id)
    if marker is None:
        raise PlotPositionError(
            f"Could not save marker for Worker Assignment {worker_assignment_id}."
        )
    return marker

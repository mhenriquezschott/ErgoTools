"""PLOT station-anchor and worker-marker persistence."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Iterable, Sequence


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


def plot_worker_records(
    connection: sqlite3.Connection,
    *,
    tool_id: str | None,
    scope_paths: Iterable[Sequence[str]] = (),
    plant_name: str | None = None,
    section_names: Iterable[str] = (),
    line_names: Iterable[str] = (),
    station_ids: Iterable[str] = (),
    shift_id: str | None = None,
    gender: str | None = None,
    birth_year_range: tuple[int, int] | None = None,
    weight_range: tuple[float, float] | None = None,
    height_range: tuple[float, float] | None = None,
    order_by: str = "worker_id",
) -> list[dict]:
    """Return current PLOT Worker rows from the normalized assessment model."""
    if order_by not in {"worker_id", "last_name"}:
        raise PlotPositionError(f"Unsupported PLOT Worker ordering: {order_by}")
    order_column = "assignment.worker_id" if order_by == "worker_id" else "w.last_name"
    query = """
        SELECT assignment.id AS worker_assignment_id,
               assignment.worker_id,
               context.plant_name, context.section_name, context.line_name,
               context.station_id, context.shift_id,
               assessment.tool_id,
               assessment.total_cumulative_damage,
               assessment.probability_outcome,
               0.0 AS result_3, 0.0 AS result_4, 0.0 AS result_5,
               0.0 AS result_6, 0.0 AS result_7, 0.0 AS result_8,
               0.0 AS result_9, assessment.unit,
               COALESCE(marker.x, station_position.x, 0.0) AS x,
               COALESCE(marker.y, station_position.y, 0.0) AS y,
               COALESCE(marker.size, 50.0) AS width,
               COALESCE(marker.size, 50.0) AS ws_height,
               COALESCE(marker.line_thickness, 1.0) AS line_thickness,
               COALESCE(marker.scale, 1.0) AS scale_x,
               COALESCE(marker.scale, 1.0) AS scale_y,
               0.0 AS crop_x, 0.0 AS crop_y,
               COALESCE(marker.size, 50.0) AS crop_width,
               COALESCE(marker.size, 50.0) AS crop_height,
               1.0 AS zoom, 0.0 AS rotation,
               0 AS mirror_h, 0 AS mirror_v, 'Horizontal' AS orientation,
               0 AS r, 0 AS g, 0 AS b,
               0.0 AS brightness, 0.0 AS contrast, 0.0 AS saturation,
               COALESCE(marker.locked, 0) AS lock,
               COALESCE(marker.visible, 0) AS visible,
               0.0 AS transparency,
               COALESCE(marker.enabled, 1) AS enable,
               w.first_name, w.last_name,
               w.year_of_birth, w.month_of_birth, w.day_of_birth,
               w.gender, w.height AS worker_height, w.weight AS worker_weight,
               placement.job_id, job.name AS job_name,
               job_risk.profile_id AS job_risk_profile_id,
               job_risk.profile_name AS job_risk_profile_name,
               job_risk.profile_version AS job_risk_profile_version,
               job_risk.source_type AS job_risk_source_type,
               job_risk.total_cumulative_damage AS job_total_cumulative_damage,
               job_risk.probability_outcome AS job_probability_outcome,
               job_risk.unit AS job_unit
        FROM IndividualAssessment AS assessment
        JOIN WorkerAssignment AS assignment
          ON assignment.id = assessment.worker_assignment_id
        JOIN WorkplaceContext AS context
          ON context.id = assignment.workplace_context_id
        JOIN Worker AS w ON w.id = assignment.worker_id
        LEFT JOIN PlotWorkerAssignmentMarker AS marker
          ON marker.worker_assignment_id = assignment.id
        LEFT JOIN PlotStationPosition AS station_position
          ON station_position.plant_name = context.plant_name
         AND station_position.section_name = context.section_name
         AND station_position.line_name = context.line_name
         AND station_position.station_id = context.station_id
        LEFT JOIN JobPlacement AS placement
          ON placement.id = assignment.job_placement_id
        LEFT JOIN Job AS job ON job.id = placement.job_id
        LEFT JOIN CurrentJobRiskMeasurement AS job_risk
          ON job_risk.job_id = placement.job_id
         AND job_risk.tool_id = assessment.tool_id
    """
    filters = ["assessment.is_current = 1", "assignment.active = 1"]
    parameters: list[object] = []
    normalized_paths = [
        tuple(str(value) for value in path if str(value))
        for path in scope_paths
    ]
    normalized_paths = [path for path in normalized_paths if path]
    if normalized_paths:
        hierarchy_columns = (
            "context.plant_name",
            "context.section_name",
            "context.line_name",
            "context.station_id",
        )
        path_filters = []
        for path in normalized_paths:
            branch = []
            for column, value in zip(hierarchy_columns, path):
                branch.append(f"{column} = ?")
                parameters.append(value)
            path_filters.append("(" + " AND ".join(branch) + ")")
        filters.append("(" + " OR ".join(path_filters) + ")")
    else:
        if plant_name:
            filters.append("context.plant_name = ?")
            parameters.append(plant_name)
        for column, values in (
            ("context.section_name", tuple(section_names)),
            ("context.line_name", tuple(line_names)),
            ("context.station_id", tuple(station_ids)),
        ):
            if values:
                filters.append(f"{column} IN ({', '.join('?' for _ in values)})")
                parameters.extend(values)
    if shift_id:
        filters.append("context.shift_id = ?")
        parameters.append(shift_id)
    if tool_id:
        filters.append("assessment.tool_id = ?")
        parameters.append(tool_id)
    if gender:
        filters.append("w.gender = ?")
        parameters.append(gender)
    for column, value_range in (
        ("w.year_of_birth", birth_year_range),
        ("w.weight", weight_range),
        ("w.height", height_range),
    ):
        if value_range is not None:
            filters.append(f"{column} BETWEEN ? AND ?")
            parameters.extend(value_range)

    cursor = connection.execute(
        query + " WHERE " + " AND ".join(filters) + f" ORDER BY {order_column}",
        parameters,
    )
    columns = tuple(description[0] for description in cursor.description)
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def plot_job_records(
    connection: sqlite3.Connection,
    *,
    tool_id: str,
    scope_paths: Iterable[Sequence[str]] = (),
    plant_name: str | None = None,
    shift_id: str | None = None,
) -> list[dict]:
    """Return active placed Jobs and their current approved risk for PLOT."""
    query = """
        SELECT placement.id AS job_placement_id,
               placement.job_id, job.name AS job_name,
               context.plant_name, context.section_name, context.line_name,
               context.station_id, context.shift_id,
               (
                   SELECT COUNT(*)
                   FROM WorkerAssignment AS assigned_worker
                   WHERE assigned_worker.job_placement_id = placement.id
                     AND assigned_worker.active = 1
               ) AS assigned_worker_count,
               position.x, position.y, position.position_source,
               risk.profile_id AS job_risk_profile_id,
               risk.profile_name AS job_risk_profile_name,
               risk.profile_version AS job_risk_profile_version,
               risk.source_type AS job_risk_source_type,
               risk.total_cumulative_damage,
               risk.probability_outcome,
               risk.unit
        FROM JobPlacement AS placement
        JOIN Job AS job ON job.id = placement.job_id
        JOIN WorkplaceContext AS context
          ON context.id = placement.workplace_context_id
        LEFT JOIN CurrentJobRiskMeasurement AS risk
          ON risk.job_id = placement.job_id AND risk.tool_id = ?
        LEFT JOIN PlotStationPosition AS position
          ON position.plant_name = context.plant_name
         AND position.section_name = context.section_name
         AND position.line_name = context.line_name
         AND position.station_id = context.station_id
        WHERE placement.active = 1 AND job.active = 1
    """
    parameters: list[object] = [tool_id]
    filters = []
    normalized_paths = [
        tuple(str(value) for value in path if str(value))
        for path in scope_paths
    ]
    normalized_paths = [path for path in normalized_paths if path]
    if normalized_paths:
        hierarchy_columns = (
            "context.plant_name",
            "context.section_name",
            "context.line_name",
            "context.station_id",
        )
        path_filters = []
        for path in normalized_paths:
            branch = []
            for column, value in zip(hierarchy_columns, path):
                branch.append(f"{column} = ?")
                parameters.append(value)
            path_filters.append("(" + " AND ".join(branch) + ")")
        filters.append("(" + " OR ".join(path_filters) + ")")
    elif plant_name:
        filters.append("context.plant_name = ?")
        parameters.append(plant_name)
    if shift_id:
        filters.append("context.shift_id = ?")
        parameters.append(shift_id)
    if filters:
        query += " AND " + " AND ".join(filters)
    query += """
        ORDER BY context.plant_name, context.section_name, context.line_name,
                 context.station_id, context.shift_id, placement.job_id
    """
    cursor = connection.execute(query, parameters)
    columns = tuple(description[0] for description in cursor.description)
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


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

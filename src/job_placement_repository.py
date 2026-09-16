"""Job placement queries and transactional updates."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from typing import Iterable, Mapping


class JobPlacementError(ValueError):
    """Raised when a Job placement request is invalid."""


@dataclass(frozen=True, order=True)
class WorkplaceKey:
    plant_name: str
    section_name: str
    line_name: str
    station_id: str
    shift_id: str


def available_workplaces(connection: sqlite3.Connection) -> list[WorkplaceKey]:
    """Return valid station/shift choices without creating database rows."""
    rows = connection.execute(
        """
        SELECT station.plant_name, station.section_name, station.line_name,
               station.id, shift.id
        FROM Station AS station
        CROSS JOIN Shift AS shift
        ORDER BY station.plant_name, station.section_name, station.line_name,
                 station.id, shift.id
        """
    ).fetchall()
    return [WorkplaceKey(*row) for row in rows]


def active_job_placement_keys(
    connection: sqlite3.Connection,
    job_id: str,
) -> set[WorkplaceKey]:
    rows = connection.execute(
        """
        SELECT context.plant_name, context.section_name, context.line_name,
               context.station_id, context.shift_id
        FROM JobPlacement AS placement
        JOIN WorkplaceContext AS context
          ON context.id = placement.workplace_context_id
        WHERE placement.job_id = ? AND placement.active = 1
        ORDER BY context.plant_name, context.section_name, context.line_name,
                 context.station_id, context.shift_id
        """,
        (job_id,),
    ).fetchall()
    return {WorkplaceKey(*row) for row in rows}


def active_job_placement_count(connection: sqlite3.Connection, job_id: str) -> int:
    return int(
        connection.execute(
            "SELECT COUNT(*) FROM JobPlacement WHERE job_id = ? AND active = 1",
            (job_id,),
        ).fetchone()[0]
    )


def _context_id(connection: sqlite3.Connection, key: WorkplaceKey) -> int:
    station_exists = connection.execute(
        """
        SELECT 1 FROM Station
        WHERE plant_name = ? AND section_name = ? AND line_name = ? AND id = ?
        """,
        (key.plant_name, key.section_name, key.line_name, key.station_id),
    ).fetchone()
    if station_exists is None:
        raise JobPlacementError(
            f"Station does not exist: {key.plant_name} / {key.section_name} / "
            f"{key.line_name} / {key.station_id}"
        )
    if connection.execute("SELECT 1 FROM Shift WHERE id = ?", (key.shift_id,)).fetchone() is None:
        raise JobPlacementError(f"Shift does not exist: {key.shift_id}")
    connection.execute(
        """
        INSERT OR IGNORE INTO WorkplaceContext (
            plant_name, section_name, line_name, station_id, shift_id
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            key.plant_name,
            key.section_name,
            key.line_name,
            key.station_id,
            key.shift_id,
        ),
    )
    return int(
        connection.execute(
            """
            SELECT id FROM WorkplaceContext
            WHERE plant_name = ? AND section_name = ? AND line_name = ?
              AND station_id = ? AND shift_id = ?
            """,
            (
                key.plant_name,
                key.section_name,
                key.line_name,
                key.station_id,
                key.shift_id,
            ),
        ).fetchone()[0]
    )


def replace_active_job_placements(
    connection: sqlite3.Connection,
    job_id: str,
    workplace_keys: Iterable[WorkplaceKey],
) -> None:
    """Replace current placements while retaining deactivated history."""
    if connection.execute("SELECT 1 FROM Job WHERE id = ?", (job_id,)).fetchone() is None:
        raise JobPlacementError(f"Job does not exist: {job_id}")
    requested = set(workplace_keys)
    current = active_job_placement_keys(connection, job_id)

    for key in current - requested:
        connection.execute(
            """
            UPDATE JobPlacement
            SET active = 0
            WHERE job_id = ? AND active = 1
              AND workplace_context_id = (
                  SELECT id FROM WorkplaceContext
                  WHERE plant_name = ? AND section_name = ? AND line_name = ?
                    AND station_id = ? AND shift_id = ?
              )
            """,
            (
                job_id,
                key.plant_name,
                key.section_name,
                key.line_name,
                key.station_id,
                key.shift_id,
            ),
        )

    for key in requested - current:
        context_id = _context_id(connection, key)
        inactive = connection.execute(
            """
            SELECT id FROM JobPlacement
            WHERE job_id = ? AND workplace_context_id = ? AND active = 0
            ORDER BY id DESC LIMIT 1
            """,
            (job_id, context_id),
        ).fetchone()
        if inactive:
            connection.execute(
                "UPDATE JobPlacement SET active = 1 WHERE id = ?",
                (inactive[0],),
            )
            continue
        connection.execute(
            """
            INSERT INTO JobPlacement (job_id, workplace_context_id, active)
            VALUES (?, ?, 1)
            """,
            (job_id, context_id),
        )


def worker_assignments(connection: sqlite3.Connection, worker_id: str) -> list[dict]:
    rows = connection.execute(
        """
        SELECT assignment.id, assignment.workplace_context_id,
               context.plant_name, context.section_name, context.line_name,
               context.station_id, context.shift_id,
               assignment.job_placement_id, job.id, job.name,
               COALESCE(placement.active, 0)
        FROM WorkerAssignment AS assignment
        JOIN WorkplaceContext AS context
          ON context.id = assignment.workplace_context_id
        LEFT JOIN JobPlacement AS placement
          ON placement.id = assignment.job_placement_id
        LEFT JOIN Job AS job ON job.id = placement.job_id
        WHERE assignment.worker_id = ? AND assignment.active = 1
        ORDER BY context.plant_name, context.section_name, context.line_name,
                 context.station_id, context.shift_id
        """,
        (worker_id,),
    ).fetchall()
    columns = (
        "assignment_id",
        "workplace_context_id",
        "plant_name",
        "section_name",
        "line_name",
        "station_id",
        "shift_id",
        "job_placement_id",
        "job_id",
        "job_name",
        "placement_active",
    )
    return [dict(zip(columns, row)) for row in rows]


def job_placement_options(
    connection: sqlite3.Connection,
    workplace_context_id: int,
) -> list[dict]:
    rows = connection.execute(
        """
        SELECT placement.id, placement.job_id, job.name
        FROM JobPlacement AS placement
        JOIN Job AS job ON job.id = placement.job_id
        WHERE placement.workplace_context_id = ?
          AND placement.active = 1
          AND job.active = 1
        ORDER BY placement.job_id
        """,
        (workplace_context_id,),
    ).fetchall()
    return [
        {"placement_id": row[0], "job_id": row[1], "job_name": row[2] or ""}
        for row in rows
    ]


def active_job_placements(connection: sqlite3.Connection) -> list[dict]:
    """Return active Jobs placed in exact workplace and shift contexts."""
    rows = connection.execute(
        """
        SELECT placement.id, placement.job_id, job.name,
               placement.workplace_context_id,
               context.plant_name, context.section_name, context.line_name,
               context.station_id, context.shift_id
        FROM JobPlacement AS placement
        JOIN Job AS job ON job.id = placement.job_id
        JOIN WorkplaceContext AS context
          ON context.id = placement.workplace_context_id
        WHERE placement.active = 1 AND job.active = 1
        ORDER BY context.plant_name, context.section_name, context.line_name,
                 context.station_id, context.shift_id, placement.job_id
        """
    ).fetchall()
    columns = (
        "placement_id", "job_id", "job_name", "workplace_context_id",
        "plant_name", "section_name", "line_name", "station_id", "shift_id",
    )
    return [dict(zip(columns, row)) for row in rows]


def assign_worker_to_job_placement(
    connection: sqlite3.Connection,
    worker_id: str,
    placement_id: int,
) -> int:
    """Create or transition the worker's active assignment to a Job Placement.

    A change from one classified Job to another closes the former assignment
    and creates a new row. Assessments linked to the former assignment retain
    their historical Job meaning.
    """
    if connection.execute("SELECT 1 FROM Worker WHERE id = ?", (worker_id,)).fetchone() is None:
        raise JobPlacementError(f"Worker does not exist: {worker_id}")
    placement = connection.execute(
        """
        SELECT placement.workplace_context_id
        FROM JobPlacement AS placement
        JOIN Job AS job ON job.id = placement.job_id
        WHERE placement.id = ? AND placement.active = 1 AND job.active = 1
        """,
        (placement_id,),
    ).fetchone()
    if placement is None:
        raise JobPlacementError("The selected Job Placement is not active.")
    context_id = int(placement[0])
    existing = connection.execute(
        """
        SELECT id, job_placement_id
        FROM WorkerAssignment
        WHERE worker_id = ? AND workplace_context_id = ? AND active = 1
        """,
        (worker_id, context_id),
    ).fetchone()
    if existing is None:
        return int(
            connection.execute(
                """
                INSERT INTO WorkerAssignment (
                    worker_id, workplace_context_id, job_placement_id,
                    started_at, active, notes
                ) VALUES (?, ?, ?, ?, 1, 'Created from Worker Management.')
                """,
                (worker_id, context_id, placement_id, date.today().isoformat()),
            ).lastrowid
        )
    assignment_id, current_placement_id = int(existing[0]), existing[1]
    if current_placement_id == placement_id:
        return assignment_id
    if current_placement_id is None:
        connection.execute(
            """
            UPDATE WorkerAssignment
            SET job_placement_id = ?, started_at = COALESCE(started_at, ?),
                notes = 'Classified from Worker Management.'
            WHERE id = ?
            """,
            (placement_id, date.today().isoformat(), assignment_id),
        )
        return assignment_id

    connection.execute(
        """
        UPDATE WorkerAssignment
        SET active = 0, ended_at = COALESCE(ended_at, ?)
        WHERE id = ?
        """,
        (date.today().isoformat(), assignment_id),
    )
    return int(
        connection.execute(
            """
            INSERT INTO WorkerAssignment (
                worker_id, workplace_context_id, job_placement_id,
                started_at, active, notes
            ) VALUES (?, ?, ?, ?, 1, 'Job assignment changed from Worker Management.')
            """,
            (worker_id, context_id, placement_id, date.today().isoformat()),
        ).lastrowid
    )


def update_worker_assignment_jobs(
    connection: sqlite3.Connection,
    worker_id: str,
    assignments: Mapping[int, int | None],
) -> None:
    """Classify active Worker Assignments using compatible active placements."""
    for assignment_id, placement_id in assignments.items():
        assignment = connection.execute(
            """
            SELECT workplace_context_id, job_placement_id
            FROM WorkerAssignment
            WHERE id = ? AND worker_id = ? AND active = 1
            """,
            (assignment_id, worker_id),
        ).fetchone()
        if assignment is None:
            raise JobPlacementError(
                f"Active Worker Assignment does not exist: {assignment_id}"
            )
        if placement_id is not None:
            compatible = connection.execute(
                """
                SELECT 1
                FROM JobPlacement AS placement
                JOIN Job AS job ON job.id = placement.job_id
                WHERE placement.id = ?
                  AND placement.workplace_context_id = ?
                  AND placement.active = 1
                  AND job.active = 1
                """,
                (placement_id, assignment[0]),
            ).fetchone()
            if compatible is None:
                raise JobPlacementError(
                    "The selected Job Placement is not active in this worker's workplace context."
                )
        current_placement_id = assignment[1]
        if current_placement_id == placement_id:
            continue
        if current_placement_id is None:
            connection.execute(
                """
                UPDATE WorkerAssignment
                SET job_placement_id = ?, started_at = COALESCE(started_at, ?)
                WHERE id = ?
                """,
                (placement_id, date.today().isoformat(), assignment_id),
            )
            continue
        connection.execute(
            """
            UPDATE WorkerAssignment
            SET active = 0, ended_at = COALESCE(ended_at, ?)
            WHERE id = ?
            """,
            (date.today().isoformat(), assignment_id),
        )
        connection.execute(
            """
            INSERT INTO WorkerAssignment (
                worker_id, workplace_context_id, job_placement_id,
                started_at, active, notes
            ) VALUES (?, ?, ?, ?, 1, 'Classification changed from Worker Management.')
            """,
            (
                worker_id, assignment[0], placement_id,
                date.today().isoformat(),
            ),
        )

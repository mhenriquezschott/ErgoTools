"""Database access for reproducible JROT schemes and scoped rotation pools."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


class RotationDataError(ValueError):
    """Raised when a rotation cannot be persisted without losing provenance."""


@dataclass(frozen=True)
class RotationWorker:
    worker_id: str
    first_name: str | None
    last_name: str | None
    worker_assignment_id: int | None
    context_id: int | None


@dataclass(frozen=True)
class RotationTargetOption:
    job_id: str
    job_name: str
    job_placement_id: int | None
    context_id: int | None
    profile_id: int
    profile_version: int
    source_type: str
    source_reference: str | None
    plant_name: str | None
    section_name: str | None
    line_name: str | None
    station_id: str | None
    shift_id: str | None

    @property
    def key(self) -> tuple[str, int | None]:
        return self.job_id, self.job_placement_id

    @property
    def display_name(self) -> str:
        if self.station_id is None:
            return self.job_id
        return f"{self.job_id} - {self.station_id}"


def list_rotation_schemes(connection: sqlite3.Connection) -> list[dict]:
    rows = connection.execute(
        """
        SELECT scheme.id, scheme.name, scheme.description,
               scheme.num_workers, scheme.num_timeblocks,
               scheme.optimization_mode, scheme.primary_tool_id,
               COUNT(DISTINCT scope.workplace_context_id) AS scope_count
        FROM RotationScheme AS scheme
        LEFT JOIN RotationSchemeScope AS scope ON scope.scheme_id = scheme.id
        GROUP BY scheme.id
        ORDER BY scheme.id COLLATE NOCASE
        """
    ).fetchall()
    columns = (
        "id", "name", "description", "num_workers", "num_timeblocks",
        "optimization_mode", "primary_tool_id", "scope_count",
    )
    return [dict(zip(columns, row)) for row in rows]


def available_scope_contexts(
    connection: sqlite3.Connection,
    *,
    shift_id: str | None = None,
) -> list[dict]:
    parameters: list[object] = []
    shift_clause = ""
    if shift_id is not None:
        shift_clause = "AND context.shift_id = ?"
        parameters.append(shift_id)
    rows = connection.execute(
        f"""
        SELECT DISTINCT context.id, context.plant_name, context.section_name,
               context.line_name, context.station_id, context.shift_id
        FROM WorkplaceContext AS context
        JOIN JobPlacement AS placement
          ON placement.workplace_context_id = context.id
         AND placement.active = 1
        JOIN Job AS job ON job.id = placement.job_id AND job.active = 1
        WHERE 1 = 1 {shift_clause}
        ORDER BY context.plant_name COLLATE NOCASE,
                 context.section_name COLLATE NOCASE,
                 context.line_name COLLATE NOCASE,
                 context.station_id COLLATE NOCASE,
                 context.shift_id COLLATE NOCASE
        """,
        parameters,
    ).fetchall()
    columns = ("id", "plant_name", "section_name", "line_name", "station_id", "shift_id")
    return [dict(zip(columns, row)) for row in rows]


def rotation_workers(
    connection: sqlite3.Connection,
    context_ids: Sequence[int] = (),
) -> list[RotationWorker]:
    if not context_ids:
        rows = connection.execute(
            """
            SELECT worker.id, worker.first_name, worker.last_name, NULL, NULL
            FROM Worker AS worker
            ORDER BY worker.id COLLATE NOCASE
            """
        ).fetchall()
    else:
        placeholders = ", ".join("?" for _ in context_ids)
        rows = connection.execute(
            f"""
            WITH ranked AS (
                SELECT worker.id, worker.first_name, worker.last_name,
                       assignment.id AS worker_assignment_id,
                       assignment.workplace_context_id,
                       ROW_NUMBER() OVER (
                           PARTITION BY worker.id
                           ORDER BY assignment.id
                       ) AS assignment_rank
                FROM Worker AS worker
                JOIN WorkerAssignment AS assignment
                  ON assignment.worker_id = worker.id
                 AND assignment.active = 1
                WHERE assignment.workplace_context_id IN ({placeholders})
            )
            SELECT id, first_name, last_name,
                   worker_assignment_id, workplace_context_id
            FROM ranked
            WHERE assignment_rank = 1
            ORDER BY id COLLATE NOCASE
            """,
            tuple(context_ids),
        ).fetchall()
    return [RotationWorker(*row) for row in rows]


def rotation_targets(
    connection: sqlite3.Connection,
    context_ids: Sequence[int] = (),
) -> list[RotationTargetOption]:
    if not context_ids:
        rows = connection.execute(
            """
            SELECT job.id, job.name, NULL, NULL,
                   profile.id, profile.version, profile.source_type,
                   profile.source_reference,
                   NULL, NULL, NULL, NULL, NULL
            FROM Job AS job
            JOIN JobRiskProfile AS profile
              ON profile.job_id = job.id
             AND profile.status = 'approved'
             AND profile.is_current = 1
            WHERE job.active = 1
            ORDER BY job.id COLLATE NOCASE
            """
        ).fetchall()
    else:
        placeholders = ", ".join("?" for _ in context_ids)
        rows = connection.execute(
            f"""
            SELECT job.id, job.name, placement.id, context.id,
                   profile.id, profile.version, profile.source_type,
                   profile.source_reference,
                   context.plant_name, context.section_name, context.line_name,
                   context.station_id, context.shift_id
            FROM JobPlacement AS placement
            JOIN Job AS job ON job.id = placement.job_id AND job.active = 1
            JOIN WorkplaceContext AS context
              ON context.id = placement.workplace_context_id
            JOIN JobRiskProfile AS profile
              ON profile.job_id = job.id
             AND profile.status = 'approved'
             AND profile.is_current = 1
            WHERE placement.active = 1
              AND placement.workplace_context_id IN ({placeholders})
            ORDER BY job.id COLLATE NOCASE,
                     context.plant_name COLLATE NOCASE,
                     context.section_name COLLATE NOCASE,
                     context.line_name COLLATE NOCASE,
                     context.station_id COLLATE NOCASE
            """,
            tuple(context_ids),
        ).fetchall()
    return [RotationTargetOption(*row) for row in rows]


def target_measurements(
    connection: sqlite3.Connection,
    targets: Iterable[RotationTargetOption],
) -> dict[tuple[str, int | None], dict[str, dict]]:
    target_list = list(targets)
    if not target_list:
        return {}
    profile_ids = sorted({target.profile_id for target in target_list})
    placeholders = ", ".join("?" for _ in profile_ids)
    rows = connection.execute(
        f"""
        SELECT profile_id, tool_id, total_cumulative_damage,
               probability_outcome, unit, notes
        FROM JobRiskMeasurement
        WHERE profile_id IN ({placeholders})
        """,
        tuple(profile_ids),
    ).fetchall()
    by_profile: dict[int, dict[str, dict]] = {}
    for profile_id, tool_id, damage, probability, unit, notes in rows:
        by_profile.setdefault(profile_id, {})[tool_id] = {
            "total_cumulative_damage": damage,
            "probability_outcome": probability,
            "unit": unit,
            "notes": notes,
        }
    return {target.key: by_profile.get(target.profile_id, {}) for target in target_list}


def missing_target_measurements(
    connection: sqlite3.Connection,
    targets: Iterable[RotationTargetOption],
    required_tools: Sequence[str],
) -> list[tuple[RotationTargetOption, str]]:
    target_list = list(targets)
    measurements = target_measurements(connection, target_list)
    missing: list[tuple[RotationTargetOption, str]] = []
    for target in target_list:
        available = measurements[target.key]
        for tool_id in required_tools:
            measurement = available.get(tool_id)
            if not measurement or measurement["probability_outcome"] is None:
                missing.append((target, tool_id))
    return missing


def load_rotation_scheme(connection: sqlite3.Connection, scheme_id: str) -> dict | None:
    row = connection.execute(
        """
        SELECT id, name, description, num_workers, num_timeblocks,
               optimization_mode, primary_tool_id, created_at, updated_at
        FROM RotationScheme
        WHERE id = ?
        """,
        (scheme_id,),
    ).fetchone()
    if row is None:
        return None
    columns = (
        "id", "name", "description", "num_workers", "num_timeblocks",
        "optimization_mode", "primary_tool_id", "created_at", "updated_at",
    )
    result = dict(zip(columns, row))
    result["context_ids"] = [
        context_id
        for (context_id,) in connection.execute(
            """
            SELECT workplace_context_id
            FROM RotationSchemeScope
            WHERE scheme_id = ?
            ORDER BY workplace_context_id
            """,
            (scheme_id,),
        )
    ]
    result["targets"] = [
        RotationTargetOption(*target_row)
        for target_row in connection.execute(
            """
            SELECT target.job_id, job.name, target.job_placement_id,
                   context.id, profile.id, profile.version,
                   profile.source_type, profile.source_reference,
                   context.plant_name, context.section_name, context.line_name,
                   context.station_id, context.shift_id
            FROM RotationTarget AS target
            JOIN Job AS job ON job.id = target.job_id
            JOIN JobRiskProfile AS profile
              ON profile.id = target.job_risk_profile_id
            LEFT JOIN JobPlacement AS placement
              ON placement.id = target.job_placement_id
            LEFT JOIN WorkplaceContext AS context
              ON context.id = placement.workplace_context_id
            WHERE target.scheme_id = ?
            ORDER BY target.job_id COLLATE NOCASE, target.id
            """,
            (scheme_id,),
        )
    ]
    result["assignments"] = [
        {
            "block_index": block_index,
            "worker_id": worker_id,
            "worker_assignment_id": worker_assignment_id,
            "rotation_target_id": target_id,
            "job_id": job_id,
            "job_placement_id": placement_id,
            "profile_id": profile_id,
        }
        for (
            block_index, worker_id, worker_assignment_id, target_id,
            job_id, placement_id, profile_id,
        ) in connection.execute(
            """
            SELECT assignment.block_index, assignment.worker_id,
                   assignment.worker_assignment_id, target.id,
                   target.job_id, target.job_placement_id,
                   target.job_risk_profile_id
            FROM RotationAssignment AS assignment
            JOIN RotationTarget AS target
              ON target.id = assignment.rotation_target_id
            WHERE assignment.scheme_id = ?
            ORDER BY assignment.block_index, assignment.worker_id COLLATE NOCASE
            """,
            (scheme_id,),
        )
    ]
    return result


def save_rotation_scheme(
    connection: sqlite3.Connection,
    *,
    scheme_id: str,
    name: str,
    description: str | None,
    num_workers: int,
    num_timeblocks: int,
    optimization_mode: str,
    primary_tool_id: str | None,
    context_ids: Sequence[int],
    assignments: Iterable[Mapping],
) -> None:
    assignment_list = list(assignments)
    if not scheme_id.strip() or not name.strip():
        raise RotationDataError("Rotation ID and name are required.")
    if num_workers <= 0 or num_timeblocks <= 0:
        raise RotationDataError("Worker and time-block counts must be positive.")
    if optimization_mode not in {"manual", "single_tool", "all_tools"}:
        raise RotationDataError("Unsupported optimization mode.")
    if len(assignment_list) != num_workers * num_timeblocks:
        raise RotationDataError("Every Worker and time block must have a Job target.")

    connection.execute(
        """
        INSERT INTO RotationScheme (
            id, name, description, num_workers, num_timeblocks,
            optimization_mode, primary_tool_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            description = excluded.description,
            num_workers = excluded.num_workers,
            num_timeblocks = excluded.num_timeblocks,
            optimization_mode = excluded.optimization_mode,
            primary_tool_id = excluded.primary_tool_id,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            scheme_id.strip(), name.strip(), description or None,
            num_workers, num_timeblocks, optimization_mode, primary_tool_id,
        ),
    )
    connection.execute("DELETE FROM RotationAssignment WHERE scheme_id = ?", (scheme_id,))
    connection.execute("DELETE FROM RotationTarget WHERE scheme_id = ?", (scheme_id,))
    connection.execute("DELETE FROM RotationSchemeScope WHERE scheme_id = ?", (scheme_id,))
    connection.executemany(
        """
        INSERT INTO RotationSchemeScope (scheme_id, workplace_context_id)
        VALUES (?, ?)
        """,
        ((scheme_id, context_id) for context_id in sorted(set(context_ids))),
    )

    target_ids: dict[tuple[str, int | None], int] = {}
    for assignment in assignment_list:
        key = (assignment["job_id"], assignment.get("job_placement_id"))
        if key in target_ids:
            continue
        cursor = connection.execute(
            """
            INSERT INTO RotationTarget (
                scheme_id, job_id, job_placement_id, job_risk_profile_id
            ) VALUES (?, ?, ?, ?)
            """,
            (scheme_id, key[0], key[1], assignment["profile_id"]),
        )
        target_ids[key] = int(cursor.lastrowid)

    connection.executemany(
        """
        INSERT INTO RotationAssignment (
            scheme_id, block_index, worker_id,
            worker_assignment_id, rotation_target_id
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            (
                scheme_id,
                assignment["block_index"],
                assignment["worker_id"],
                assignment.get("worker_assignment_id"),
                target_ids[(assignment["job_id"], assignment.get("job_placement_id"))],
            )
            for assignment in assignment_list
        ),
    )


def delete_rotation_scheme(connection: sqlite3.Connection, scheme_id: str) -> None:
    connection.execute("DELETE FROM RotationScheme WHERE id = ?", (scheme_id,))

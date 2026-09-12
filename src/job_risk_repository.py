"""Database operations for versioned job-level ergonomic risk."""

from __future__ import annotations

import sqlite3
from typing import Iterable, Mapping

from risk_colors import job_risk_color


def _editable_profile_id(connection: sqlite3.Connection, job_id: str) -> int:
    row = connection.execute(
        """
        SELECT id, source_type
        FROM JobRiskProfile
        WHERE job_id = ? AND status = 'approved' AND is_current = 1
        """,
        (job_id,),
    ).fetchone()
    if row and row[1] != "imported":
        return int(row[0])

    if row:
        connection.execute(
            """
            UPDATE JobRiskProfile
            SET status = 'retired', is_current = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (row[0],),
        )
    next_version = connection.execute(
        "SELECT COALESCE(MAX(version), 0) + 1 FROM JobRiskProfile WHERE job_id = ?",
        (job_id,),
    ).fetchone()[0]
    cursor = connection.execute(
        """
        INSERT INTO JobRiskProfile (
            job_id, name, version, status, is_current, source_type, methodology
        ) VALUES (?, 'Current job estimate', ?, 'approved', 1, 'expert',
                  'Entered or updated in ErgoTools Job Management.')
        """,
        (job_id, next_version),
    )
    return int(cursor.lastrowid)


def save_job_with_measurements(
    connection: sqlite3.Connection,
    *,
    job_id: str,
    name: str,
    description: str,
    measurements: Iterable[Mapping],
) -> int:
    """Save a Job and its editable current profile, retaining legacy compatibility."""
    connection.execute(
        """
        INSERT INTO Job (id, name, description)
        VALUES (?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            description = excluded.description,
            active = 1,
            updated_at = CURRENT_TIMESTAMP
        """,
        (job_id, name, description),
    )
    profile_id = _editable_profile_id(connection, job_id)
    for measurement in measurements:
        tool_id = str(measurement["tool_id"])
        damage = measurement.get("total_cumulative_damage")
        probability = measurement.get("probability_outcome")
        connection.execute(
            """
            INSERT INTO JobRiskMeasurement (
                profile_id, tool_id, total_cumulative_damage, probability_outcome, unit
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(profile_id, tool_id) DO UPDATE SET
                total_cumulative_damage = excluded.total_cumulative_damage,
                probability_outcome = excluded.probability_outcome,
                unit = excluded.unit
            """,
            (profile_id, tool_id, damage, probability, measurement.get("unit")),
        )

        # Temporary compatibility write. Removed after every consumer uses profiles.
        color = job_risk_color(tool_id, damage, measurement.get("unit") or "Metric")
        connection.execute(
            """
            INSERT INTO JobMeasurement (
                job_id, tool_id, total_cumulative_damage, probability_outcome, color
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(job_id, tool_id) DO UPDATE SET
                total_cumulative_damage = excluded.total_cumulative_damage,
                probability_outcome = excluded.probability_outcome,
                color = excluded.color
            """,
            (job_id, tool_id, damage, probability, color),
        )
    connection.execute(
        "UPDATE JobRiskProfile SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (profile_id,),
    )
    return profile_id


def current_measurements(connection: sqlite3.Connection, job_id: str) -> dict[str, dict]:
    rows = connection.execute(
        """
        SELECT tool_id, total_cumulative_damage, probability_outcome, unit
        FROM CurrentJobRiskMeasurement
        WHERE job_id = ?
        """,
        (job_id,),
    ).fetchall()
    return {
        row[0]: {
            "total_cumulative_damage": row[1],
            "probability_outcome": row[2],
            "unit": row[3],
        }
        for row in rows
    }


def jobs_for_tool(connection: sqlite3.Connection, tool_id: str) -> list[dict]:
    rows = connection.execute(
        """
        SELECT job_id AS id, job_name AS name, probability_outcome,
               total_cumulative_damage, tool_id, unit, profile_id, profile_version,
               source_type, source_reference
        FROM CurrentJobRiskMeasurement
        WHERE tool_id = ?
        ORDER BY job_id
        """,
        (tool_id,),
    ).fetchall()
    columns = (
        "id",
        "name",
        "probability_outcome",
        "total_cumulative_damage",
        "tool_id",
        "unit",
        "profile_id",
        "profile_version",
        "source_type",
        "source_reference",
    )
    results = []
    for row in rows:
        result = dict(zip(columns, row))
        result["color"] = job_risk_color(
            result["tool_id"],
            result["total_cumulative_damage"],
            result["unit"] or "Metric",
        )
        results.append(result)
    return results

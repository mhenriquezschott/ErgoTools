"""Database operations for versioned job-level ergonomic risk."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Iterable, Mapping

from risk_colors import job_risk_color


@dataclass(frozen=True)
class JobRiskIssue:
    job_id: str
    tool_id: str
    reason: str


class JobRiskProfileError(ValueError):
    """Raised when a requested Job Risk Profile transition is invalid."""


PROFILE_SOURCE_TYPES = ("expert", "external", "study", "aggregate", "imported")


def job_profiles(connection: sqlite3.Connection, job_id: str) -> list[dict]:
    rows = connection.execute(
        """
        SELECT id, job_id, name, version, status, is_current, source_type,
               source_reference, methodology, sample_size, assessed_on,
               notes, created_at, updated_at
        FROM JobRiskProfile
        WHERE job_id = ?
        ORDER BY version DESC
        """,
        (job_id,),
    ).fetchall()
    columns = (
        "id",
        "job_id",
        "name",
        "version",
        "status",
        "is_current",
        "source_type",
        "source_reference",
        "methodology",
        "sample_size",
        "assessed_on",
        "notes",
        "created_at",
        "updated_at",
    )
    return [dict(zip(columns, row)) for row in rows]


def profile_measurements(connection: sqlite3.Connection, profile_id: int) -> dict[str, dict]:
    rows = connection.execute(
        """
        SELECT tool_id, total_cumulative_damage, probability_outcome, unit, notes
        FROM JobRiskMeasurement
        WHERE profile_id = ?
        """,
        (profile_id,),
    ).fetchall()
    return {
        row[0]: {
            "total_cumulative_damage": row[1],
            "probability_outcome": row[2],
            "unit": row[3],
            "notes": row[4],
        }
        for row in rows
    }


def create_draft_profile(
    connection: sqlite3.Connection,
    job_id: str,
    *,
    copy_from_profile_id: int | None = None,
) -> int:
    if connection.execute("SELECT 1 FROM Job WHERE id = ?", (job_id,)).fetchone() is None:
        raise JobRiskProfileError(f"Job does not exist: {job_id}")
    next_version = connection.execute(
        "SELECT COALESCE(MAX(version), 0) + 1 FROM JobRiskProfile WHERE job_id = ?",
        (job_id,),
    ).fetchone()[0]

    source = None
    if copy_from_profile_id is not None:
        source = connection.execute(
            """
            SELECT name, source_reference, methodology, sample_size, assessed_on, notes
            FROM JobRiskProfile
            WHERE id = ? AND job_id = ?
            """,
            (copy_from_profile_id, job_id),
        ).fetchone()
        if source is None:
            raise JobRiskProfileError("The source profile does not belong to this Job.")

    source = source or ("New estimate", None, None, None, None, None)
    cursor = connection.execute(
        """
        INSERT INTO JobRiskProfile (
            job_id, name, version, status, is_current, source_type,
            source_reference, methodology, sample_size, assessed_on, notes
        ) VALUES (?, ?, ?, 'draft', 0, 'expert', ?, ?, ?, ?, ?)
        """,
        (job_id, f"{source[0]} - revision", next_version, *source[1:]),
    )
    profile_id = int(cursor.lastrowid)
    if copy_from_profile_id is not None:
        connection.execute(
            """
            INSERT INTO JobRiskMeasurement (
                profile_id, tool_id, total_cumulative_damage,
                probability_outcome, unit, notes
            )
            SELECT ?, tool_id, total_cumulative_damage,
                   probability_outcome, unit, notes
            FROM JobRiskMeasurement
            WHERE profile_id = ?
            """,
            (profile_id, copy_from_profile_id),
        )
    return profile_id


def save_draft_profile(
    connection: sqlite3.Connection,
    profile_id: int,
    *,
    name: str,
    source_type: str,
    source_reference: str | None,
    methodology: str | None,
    sample_size: int | None,
    assessed_on: str | None,
    notes: str | None,
    measurements: Iterable[Mapping],
) -> None:
    if not name.strip():
        raise JobRiskProfileError("Profile name is required.")
    if source_type not in PROFILE_SOURCE_TYPES:
        raise JobRiskProfileError(f"Unsupported profile source type: {source_type}")
    profile = connection.execute(
        "SELECT status FROM JobRiskProfile WHERE id = ?",
        (profile_id,),
    ).fetchone()
    if profile is None:
        raise JobRiskProfileError("Job Risk Profile does not exist.")
    if profile[0] != "draft":
        raise JobRiskProfileError("Only draft profiles can be edited.")
    connection.execute(
        """
        UPDATE JobRiskProfile
        SET name = ?, source_type = ?, source_reference = ?, methodology = ?,
            sample_size = ?, assessed_on = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            name.strip(),
            source_type,
            source_reference or None,
            methodology or None,
            sample_size,
            assessed_on or None,
            notes or None,
            profile_id,
        ),
    )
    connection.execute("DELETE FROM JobRiskMeasurement WHERE profile_id = ?", (profile_id,))
    for measurement in measurements:
        if measurement.get("total_cumulative_damage") is None and measurement.get(
            "probability_outcome"
        ) is None:
            continue
        connection.execute(
            """
            INSERT INTO JobRiskMeasurement (
                profile_id, tool_id, total_cumulative_damage,
                probability_outcome, unit, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                measurement["tool_id"],
                measurement.get("total_cumulative_damage"),
                measurement.get("probability_outcome"),
                measurement.get("unit"),
                measurement.get("notes"),
            ),
        )


def approve_profile(connection: sqlite3.Connection, profile_id: int) -> None:
    profile = connection.execute(
        "SELECT job_id, status FROM JobRiskProfile WHERE id = ?",
        (profile_id,),
    ).fetchone()
    if profile is None:
        raise JobRiskProfileError("Job Risk Profile does not exist.")
    if profile[1] != "draft":
        raise JobRiskProfileError("Only a draft profile can be approved.")
    complete_measurements = connection.execute(
        """
        SELECT COUNT(*) FROM JobRiskMeasurement
        WHERE profile_id = ?
          AND total_cumulative_damage IS NOT NULL
          AND probability_outcome IS NOT NULL
        """,
        (profile_id,),
    ).fetchone()[0]
    if complete_measurements == 0:
        raise JobRiskProfileError(
            "At least one complete ergonomic-tool measurement is required before approval."
        )
    connection.execute(
        "UPDATE JobRiskProfile SET is_current = 0 WHERE job_id = ? AND is_current = 1",
        (profile[0],),
    )
    connection.execute(
        """
        UPDATE JobRiskProfile
        SET status = 'approved', is_current = 1, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (profile_id,),
    )
    _sync_legacy_job_measurements(connection, profile[0], profile_id)


def make_profile_current(connection: sqlite3.Connection, profile_id: int) -> None:
    profile = connection.execute(
        "SELECT job_id, status FROM JobRiskProfile WHERE id = ?",
        (profile_id,),
    ).fetchone()
    if profile is None:
        raise JobRiskProfileError("Job Risk Profile does not exist.")
    if profile[1] != "approved":
        raise JobRiskProfileError("Only an approved profile can be made current.")
    connection.execute(
        "UPDATE JobRiskProfile SET is_current = 0 WHERE job_id = ? AND is_current = 1",
        (profile[0],),
    )
    connection.execute(
        "UPDATE JobRiskProfile SET is_current = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (profile_id,),
    )
    _sync_legacy_job_measurements(connection, profile[0], profile_id)


def retire_profile(connection: sqlite3.Connection, profile_id: int) -> None:
    profile = connection.execute(
        "SELECT job_id, status, is_current FROM JobRiskProfile WHERE id = ?",
        (profile_id,),
    ).fetchone()
    if profile is None:
        raise JobRiskProfileError("Job Risk Profile does not exist.")
    if profile[1] == "retired":
        raise JobRiskProfileError("This profile is already retired.")
    connection.execute(
        """
        UPDATE JobRiskProfile
        SET status = 'retired', is_current = 0, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (profile_id,),
    )
    if profile[2]:
        connection.execute("DELETE FROM JobMeasurement WHERE job_id = ?", (profile[0],))


def _sync_legacy_job_measurements(
    connection: sqlite3.Connection,
    job_id: str,
    profile_id: int,
) -> None:
    """Maintain the temporary legacy table from one approved current profile."""
    connection.execute("DELETE FROM JobMeasurement WHERE job_id = ?", (job_id,))
    rows = connection.execute(
        """
        SELECT tool_id, total_cumulative_damage, probability_outcome, unit
        FROM JobRiskMeasurement
        WHERE profile_id = ?
          AND total_cumulative_damage IS NOT NULL
          AND probability_outcome IS NOT NULL
        """,
        (profile_id,),
    ).fetchall()
    for tool_id, damage, probability, unit in rows:
        connection.execute(
            """
            INSERT INTO JobMeasurement (
                job_id, tool_id, total_cumulative_damage, probability_outcome, color
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (job_id, tool_id, damage, probability, job_risk_color(tool_id, damage, unit or "Metric")),
        )


def job_risk_issues(
    connection: sqlite3.Connection,
    job_ids: Iterable[str],
    tool_ids: Iterable[str],
) -> list[JobRiskIssue]:
    """Return every reason the requested jobs cannot be used for optimization."""
    issues = []
    normalized_jobs = sorted({str(job_id).strip() for job_id in job_ids if str(job_id).strip()})
    normalized_tools = tuple(dict.fromkeys(str(tool_id).strip() for tool_id in tool_ids))
    for job_id in normalized_jobs:
        job = connection.execute(
            "SELECT active FROM Job WHERE id = ?",
            (job_id,),
        ).fetchone()
        if job is None:
            for tool_id in normalized_tools:
                issues.append(JobRiskIssue(job_id, tool_id, "job does not exist"))
            continue
        if not job[0]:
            for tool_id in normalized_tools:
                issues.append(JobRiskIssue(job_id, tool_id, "job is inactive"))
            continue

        profile = connection.execute(
            """
            SELECT id
            FROM JobRiskProfile
            WHERE job_id = ? AND status = 'approved' AND is_current = 1
            """,
            (job_id,),
        ).fetchone()
        if profile is None:
            for tool_id in normalized_tools:
                issues.append(
                    JobRiskIssue(job_id, tool_id, "no current approved risk profile")
                )
            continue

        for tool_id in normalized_tools:
            measurement = connection.execute(
                """
                SELECT total_cumulative_damage, probability_outcome
                FROM JobRiskMeasurement
                WHERE profile_id = ? AND tool_id = ?
                """,
                (profile[0], tool_id),
            ).fetchone()
            if measurement is None:
                issues.append(
                    JobRiskIssue(job_id, tool_id, "measurement is not available")
                )
            elif measurement[0] is None or measurement[1] is None:
                issues.append(
                    JobRiskIssue(job_id, tool_id, "measurement is incomplete")
                )
    return issues


def format_job_risk_issues(issues: Iterable[JobRiskIssue]) -> str:
    rows = list(issues)
    lines = [
        "Optimization cannot start because required Job risk data is unavailable.",
        "",
    ]
    lines.extend(
        f"{issue.job_id} - {issue.tool_id}: {issue.reason}." for issue in rows
    )
    lines.extend(("", "Complete or approve these measurements in Job Management."))
    return "\n".join(lines)


def _editable_profile_id(
    connection: sqlite3.Connection,
    job_id: str,
    profile_metadata: Mapping | None = None,
) -> int:
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
    metadata = dict(profile_metadata or {})
    profile_name = str(metadata.get("name") or "Current job estimate").strip()
    source_type = str(metadata.get("source_type") or "expert")
    if source_type not in PROFILE_SOURCE_TYPES:
        raise JobRiskProfileError(f"Unsupported profile source type: {source_type}")
    cursor = connection.execute(
        """
        INSERT INTO JobRiskProfile (
            job_id, name, version, status, is_current, source_type,
            source_reference, methodology, sample_size, assessed_on, notes
        ) VALUES (?, ?, ?, 'approved', 1, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_id,
            profile_name,
            next_version,
            source_type,
            metadata.get("source_reference") or None,
            metadata.get("methodology")
            or "Entered or updated in ErgoTools Job Management.",
            metadata.get("sample_size"),
            metadata.get("assessed_on") or None,
            metadata.get("notes") or None,
        ),
    )
    return int(cursor.lastrowid)


def save_job_with_measurements(
    connection: sqlite3.Connection,
    *,
    job_id: str,
    name: str,
    description: str,
    measurements: Iterable[Mapping],
    profile_metadata: Mapping | None = None,
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
    profile_id = _editable_profile_id(connection, job_id, profile_metadata)
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

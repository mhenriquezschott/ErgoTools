"""Collapse earlier native profile storage to one current Job/tool set.

External conversion tooling only. Operate on a private caller-owned SQLite copy,
retain selected numeric values exactly, rewrite schedule keys without changing their
Job arrangements, and remove rejected profile/evidence structures. Never alteroriginals.
"""

import json
import sqlite3

from ergotools.infrastructure.job_risk_store import create_risk_schema


def upgrade_job_risks(connection: sqlite3.Connection) -> None:
    """Replace older profile rows and frozen scheme targets inside one transaction.

    Args:
        connection: Private conversion copy with an active caller-owned transaction.

    Returns:
        None; only uniquely selected current measurements survive. Jobs without a
        selected set remain without risk values; no historical fallback is invented.

    Raises:
        RuntimeError: No private conversion transaction exists.
        ValueError: Multiple selected profiles or ambiguous rotation keys exist.
    """
    if not connection.in_transaction:
        raise RuntimeError("Job risk upgrade requires a private transaction.")
    columns = {r[1] for r in connection.execute("PRAGMA table_info(risk_measurements)")}
    if "profile_id" not in columns:
        return
    selected = connection.execute(
        "SELECT id,job_id FROM risk_profiles WHERE is_current=1 ORDER BY position"
    ).fetchall()
    if len({r[1] for r in selected}) != len(selected):
        raise ValueError(
            "More than one current Job risk set; choose one before migration."
        )
    profile_rows = {
        row[0]: row[1]
        for row in connection.execute("SELECT id,job_id FROM risk_profiles")
    }
    previous_outputs = {
        identity: tuple(
            connection.execute(
                (
                    "SELECT kind,damage,probability FROM risk_measurements WHERE "
                    "profile_id=? ORDER BY kind"
                ),
                (identity,),
            )
        )
        for identity in profile_rows
    }
    selected_outputs = {job: previous_outputs[identity] for identity, job in selected}
    retained = [
        (job, *row)
        for identity, job in selected
        for row in connection.execute(
            (
                "SELECT kind,damage,probability,unit,position FROM "
                "risk_measurements WHERE profile_id=? ORDER BY position"
            ),
            (identity,),
        )
    ]
    project_id = connection.execute(
        "SELECT project_id FROM project_metadata"
    ).fetchone()[0]
    connection.execute(
        "ALTER TABLE risk_measurements RENAME TO obsolete_job_measurements"
    )
    create_risk_schema(connection, project_id)
    connection.executemany(
        (
            "INSERT INTO risk_measurements(job_id,kind,damage,probability"
            ",unit,position) VALUES (?,?,?,?,?,?)"
        ),
        retained,
    )
    connection.execute("DROP TABLE obsolete_job_measurements")
    connection.execute("DROP TABLE risk_profiles")
    connection.execute("DROP TABLE risk_metadata")
    if connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='rotation_schemes'"
    ).fetchone():
        for identity, payload in connection.execute(
            "SELECT scheme_id,payload FROM rotation_schemes"
        ).fetchall():
            scheme = json.loads(payload)
            if scheme["version"] != 1:
                raise ValueError("Unsupported earlier rotation payload.")
            changed_risks = False
            for job, profile, _place in scheme["targets"]:
                if profile_rows.get(profile) != job:
                    raise ValueError(
                        "Saved rotation references a foreign Job risk set."
                    )
                if previous_outputs[profile] != selected_outputs.get(job, ()):
                    changed_risks = True
            if changed_risks:
                scheme["mode"] = "manual"
                scheme["primary_kind"] = None
            keys = {
                f"{len(job)}:{job}:{place}:{profile}": f"{len(job)}:{job}:{place}"
                for job, profile, place in scheme["targets"]
            }
            if len(set(keys.values())) != len(keys):
                raise ValueError(
                    "Multiple frozen targets collapse to one Job/placement."
                )
            scheme["targets"] = [
                [job, place] for job, profile, place in scheme["targets"]
            ]
            scheme["current"] = [
                [worker, [keys[key] for key in row]]
                for worker, row in scheme["current"]
            ]
            scheme["version"] = 2
            connection.execute(
                "UPDATE rotation_schemes SET payload=? WHERE scheme_id=?",
                (
                    json.dumps(
                        scheme,
                        ensure_ascii=False,
                        allow_nan=False,
                        separators=(",", ":"),
                    ),
                    identity,
                ),
            )

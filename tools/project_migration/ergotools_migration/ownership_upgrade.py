"""Remove assessment-version storage in a caller-owned conversion transaction.

External migration layer only. The caller supplies a private SQLite backup; original
files are never opened or modified here. One ownership row per assignment/tool retains
all task and result payloads. Only proven empty noncurrent duplicate LiFFT drafts with
no result may be discarded; populated/ambiguous duplicates stop before any SQL change.
"""

import sqlite3

from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.infrastructure.assessment_serialization import decode_assessment


def upgrade_assessment_ownership(connection: sqlite3.Connection) -> tuple[str, ...]:
    """Replace version bookkeeping with unique, foreign-keyed assessment ownership.

    Args:
        connection: Private conversion-copy connection in an explicit transaction;
            the caller owns rollback, publication and close. Never an operational file.

    Returns:
        Exact document IDs of verified blank duplicates removed. All retained source
        and result payload bytes, worker/job identities and analysis tables stay intact.

    Raises:
        ValueError: Source rows are missing/foreign, a duplicate contains data/results,
            no unambiguous retained record exists, or obsolete bindings contain data.
        RuntimeError: The caller has not started a conversion transaction.
        sqlite3.Error: A schema/read/write/integrity operation fails; caller rolls back.
    """
    if not connection.in_transaction:
        raise RuntimeError(
            "Ownership upgrade requires a private conversion transaction."
        )
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    if "assessment_ownership" in tables:
        if "assessment_history" in tables or "assessment_bindings" in tables:
            raise ValueError("Mixed assessment ownership schemas require review.")
        columns = {
            r[1] for r in connection.execute("PRAGMA table_info(assessment_ownership)")
        }
        if "worker_id" not in columns:
            _add_worker_ownership(connection)
        return ()
    bindings = connection.execute("SELECT count(*) FROM assessment_bindings").fetchone()
    if bindings is not None and bindings[0]:
        raise ValueError("Context-only bindings need explicit reconciliation.")
    rows = connection.execute(
        "SELECT document_id,assignment_id,kind,version,is_current,position "
        "FROM assessment_history ORDER BY position"
    ).fetchall()
    groups: dict[tuple[int, str], list[tuple[str, int, str, int, int, int]]] = {}
    for row in rows:
        groups.setdefault((row[1], row[2]), []).append(row)
    retained = []
    removed: list[str] = []
    for group in groups.values():
        if len(group) == 1:
            retained.append(group[0])
            continue
        meaningful: list[tuple[str, int, str, int, int, int]] = []
        blanks: list[tuple[str, int, str, int, int, int]] = []
        for row in group:
            payload = connection.execute(
                "SELECT payload FROM draft_documents WHERE document_id=?", (row[0],)
            ).fetchall()
            if len(payload) != 1:
                raise ValueError("Assessment source identity is absent or ambiguous.")
            source = decode_assessment(payload[0][0])
            result = connection.execute(
                "SELECT 1 FROM saved_assessment_results WHERE document_id=?", (row[0],)
            ).fetchone()
            blank = (
                row[2] == "lifft"
                and row[3] > 1
                and not row[4]
                and isinstance(source, LifftDraft)
                and result is None
                and all(
                    t.lever_arm is None and t.load is None and t.repetitions is None
                    for t in source.tasks
                )
            )
            (blanks if blank else meaningful).append(row)
        if len(meaningful) != 1:
            raise ValueError(
                "Multiple populated assessments require an explicit data decision."
            )
        retained.append(meaningful[0])
        removed.extend(row[0] for row in blanks)
    assignment_ids = {
        r[0] for r in connection.execute("SELECT id FROM worker_assignments")
    }
    if any(row[1] not in assignment_ids for row in retained):
        raise ValueError("Assessment references a missing worker assignment.")
    connection.execute(
        "CREATE TABLE assessment_ownership (document_id TEXT PRIMARY KEY NOT NULL,"
        "assignment_id INTEGER NOT NULL REFERENCES worker_assignments(id) "
        "DEFERRABLE INITIALLY DEFERRED,kind TEXT NOT NULL "
        "CHECK(kind IN ('lifft','duet','tst')),position INTEGER NOT NULL UNIQUE,"
        "UNIQUE(assignment_id,kind))"
    )
    connection.executemany(
        "INSERT INTO assessment_ownership VALUES (?,?,?,?)",
        (
            (r[0], r[1], r[2], position)
            for position, r in enumerate(sorted(retained, key=lambda r: r[5]))
        ),
    )
    connection.executemany(
        "DELETE FROM draft_documents WHERE document_id=?",
        ((identity,) for identity in removed),
    )
    connection.execute("DROP TABLE assessment_history")
    connection.execute("DROP TABLE assessment_bindings")
    _add_worker_ownership(connection)
    return tuple(removed)


def _add_worker_ownership(connection: sqlite3.Connection) -> None:
    """Replace required assignment ownership with worker/optional assignment links.

    Args:
        connection: Private conversion-copy connection inside the caller's transaction.
            The caller owns rollback, complete-project validation and publication.

    Returns:
        None. Preserve every source/result and organizational identity, including
        genuine records named Default. No default cleanup or calculation occurs.

    Raises:
        ValueError: An ownership row references an absent worker assignment.
        sqlite3.Error: Schema/data replacement fails; the caller rolls back.
    """
    rows = connection.execute(
        "SELECT o.document_id,a.worker_id,o.assignment_id,o.kind,o.position "
        "FROM assessment_ownership o LEFT JOIN worker_assignments a "
        "ON a.id=o.assignment_id ORDER BY o.position"
    ).fetchall()
    if any(row[1] is None for row in rows):
        raise ValueError("Assessment references a missing worker assignment.")
    connection.execute("DROP TABLE assessment_ownership")
    connection.execute(
        "CREATE TABLE assessment_ownership(document_id TEXT PRIMARY KEY NOT NULL,"
        "worker_id TEXT NOT NULL,"
        "assignment_id INTEGER REFERENCES worker_assignments(id) "
        "DEFERRABLE INITIALLY DEFERRED,kind TEXT NOT NULL "
        "CHECK(kind IN ('lifft','duet','tst')),position INTEGER NOT NULL UNIQUE,"
        "UNIQUE(assignment_id,kind))"
    )
    connection.execute(
        "CREATE UNIQUE INDEX standalone_assessment_owner ON assessment_ownership"
        "(worker_id,kind) WHERE assignment_id IS NULL"
    )
    connection.executemany("INSERT INTO assessment_ownership VALUES(?,?,?,?,?)", rows)

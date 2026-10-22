"""Worker-owned assessment storage with optional workplace association protection.

Infrastructure layer. Adapt immutable domain catalogs to parameterized SQLite or
explicit JSON payloads. The owning project retains this connection, thread lifetime and
cross-feature transaction coordination. No Qt controls, automatic old-project migration
or scientific recalculation occurs here. Stored source units/measurement scales remain
unchanged. Read methods do not silently repair corrupt records; standalone writes own
rollback and composed writes require caller rollback on any failure.
"""

import sqlite3
from dataclasses import replace

from ergotools.domain.assessment_history import (
    AssessmentHistory,
    AssignmentAssessment,
)
from ergotools.domain.assessments.document import AssessmentKind, assessment_kind
from ergotools.domain.job_catalog import JobCatalog
from ergotools.infrastructure.assessment_serialization import decode_assessment
from ergotools.infrastructure.work_hierarchy_store import decode_hierarchy


def create_history_schema(connection: sqlite3.Connection) -> None:
    """Create worker/tool ownership with optional assignment links transactionally.

    Args:
        connection: Borrowed dedicated owner-thread SQLite connection; caller retains
            close ownership and owns any enclosing transaction.

    Returns:
        None after ownership table and unique assignment/tool index creation; caller
        commits/rolls back.

    Raises:
        sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
            transaction owner must roll back composed writes.
    """
    connection.execute(
        "CREATE TABLE assessment_ownership (document_id TEXT PRIMARY KEY NOT NULL,"
        "worker_id TEXT NOT NULL,"
        "assignment_id INTEGER REFERENCES worker_assignments(id) "
        "DEFERRABLE INITIALLY DEFERRED,"
        "kind TEXT NOT NULL CHECK(kind IN ('lifft','duet','tst')),"
        "position INTEGER NOT NULL UNIQUE,UNIQUE(assignment_id,kind))"
    )
    connection.execute(
        "CREATE UNIQUE INDEX standalone_assessment_owner ON assessment_ownership "
        "(worker_id,kind) WHERE assignment_id IS NULL"
    )


class AssessmentHistoryStore:
    """Borrow a connection; transaction ownership stays with the project adapter."""

    def __init__(self, connection: sqlite3.Connection, project_id: str) -> None:
        """Configure project scope without changing schema.

        Args:
            connection: Borrowed dedicated owner-thread SQLite connection; caller
                retains close ownership and owns any enclosing transaction.
            project_id: Exact stable project identity used to validate stored ownership.

        Returns:
            None; retain project scope after checking the exact ownership columns.

        Raises:
            ValueError: Ownership columns differ from the unique assignment/tool schema.
            sqlite3.Error: Schema inspection fails.
        """
        columns = tuple(
            row[1]
            for row in connection.execute("PRAGMA table_info(assessment_ownership)")
        )
        if columns != ("document_id", "worker_id", "assignment_id", "kind", "position"):
            raise ValueError("Unsupported assessment ownership schema.")
        self._connection = connection
        self._project_id = project_id

    def read(self, jobs: JobCatalog) -> AssessmentHistory:
        """Validate every historical assignment and matching source model.

        Args:
            jobs: Validated same-project parent job/placement/assignment catalog.

        Returns:
            Ordered worker ownership with matching source models, existing workers and
            optional same-worker assignment references.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            ValueError: Saved ownership/source models, assignment references, expected
                history or resulting history invariants are invalid.
        """
        history = AssessmentHistory(
            self._project_id,
            tuple(
                AssignmentAssessment(row[0], row[1], AssessmentKind(row[2]), row[3])
                for row in self._connection.execute(
                    "SELECT document_id,assignment_id,kind,worker_id "
                    "FROM assessment_ownership ORDER BY position"
                )
            ),
        )
        history.validate_jobs(jobs)
        payload = self._connection.execute(
            "SELECT payload FROM work_catalog"
        ).fetchone()
        if payload is None:
            raise ValueError("Assessment ownership requires a worker catalog.")
        workers = {w.worker_id for w in decode_hierarchy(payload[0]).work.workers}
        if any(e.worker_id not in workers for e in history.entries):
            raise ValueError("Assessment references a missing worker.")
        for entry in history.entries:
            row = self._connection.execute(
                "SELECT payload FROM draft_documents "
                "WHERE project_id=? AND document_id=?",
                (self._project_id, entry.document_id),
            ).fetchone()
            if row is None:
                raise ValueError("Historical assessment source is missing.")
            if assessment_kind(decode_assessment(row[0])) != entry.kind:
                raise ValueError("Historical source model does not match ownership.")
        return history

    def insert(self, entry: AssignmentAssessment, jobs: JobCatalog) -> None:
        """Insert ownership in a caller-owned transaction; validate before commit.

        Args:
            entry: Exact source identity and its unique assignment/tool ownership.
            jobs: Validated same-project parent job/placement/assignment catalog.

        Returns:
            None after inserting one ownership record and revalidating all references;
            caller owns commit/rollback.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            RuntimeError: The operation requires an idle default-mode connection or an
                existing caller-owned transaction as specified; that precondition is not
                met.
            ValueError: Saved ownership/source models, assignment references, expected
                history or resulting history invariants are invalid.
        """
        if not self._connection.in_transaction:
            raise RuntimeError("History insertion requires an active transaction.")
        current = self.read(jobs)
        candidate = AssessmentHistory(self._project_id, (*current.entries, entry))
        candidate.validate_jobs(jobs)
        self._connection.execute(
            "INSERT INTO assessment_ownership VALUES (?,?,?,?,?)",
            (
                entry.document_id,
                entry.worker_id,
                entry.assignment_id,
                entry.kind.value,
                len(current.entries),
            ),
        )
        self.read(jobs)

    def initialize_in_transaction(
        self, history: AssessmentHistory, jobs: JobCatalog
    ) -> None:
        """Seed empty ownership in source order after all sources have been inserted.

        Validate the complete history once, then read every stored source/model before
        returning. The caller owns rollback; existing history is protected.

        Args:
            history: Complete proposed same-project assessment ownership history in
                source insertion order.
            jobs: Validated same-project parent job/placement/assignment catalog.

        Returns:
            None after seeding an empty store and verifying exact readback in source
            order.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            RuntimeError: The operation requires an idle default-mode connection or an
                existing caller-owned transaction as specified; that precondition is not
                met.
            ValueError: Saved ownership/source models, assignment references, expected
                history or resulting history invariants are invalid.
        """
        if not self._connection.in_transaction:
            raise RuntimeError("History initialization requires an active transaction.")
        if history.project_id != self._project_id:
            raise ValueError("Initial history belongs to another project.")
        history.validate_jobs(jobs)
        if self.read(jobs).entries:
            raise ValueError("History initialization requires an empty store.")
        self._connection.executemany(
            "INSERT INTO assessment_ownership VALUES (?,?,?,?,?)",
            [
                (
                    entry.document_id,
                    entry.worker_id,
                    entry.assignment_id,
                    entry.kind.value,
                    position,
                )
                for position, entry in enumerate(history.entries)
            ],
        )
        if self.read(jobs) != history:
            raise ValueError("Initial assessment history did not round-trip exactly.")

    def validate_change(self, current: JobCatalog, replacement: JobCatalog) -> None:
        """Keep referenced worker/workplace and classified job identities stable.

        Closing assignments and initial classification remain allowed. Job display
        metadata is mutable; a placed job ID must not be repurposed through edits.

        Args:
            current: Validated saved catalog before the proposed transition.
            replacement: Proposed immutable catalog after the transition, retaining
                protected identities.

        Returns:
            None when referenced assignments retain worker/workplace and existing
            classified placement/job identities.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            ValueError: Saved ownership/source models, assignment references, expected
                history or resulting history invariants are invalid.
        """
        history = self.read(current)
        history.validate_jobs(replacement)
        before = {item.assignment_id: item for item in current.assignments}
        after = {item.assignment_id: item for item in replacement.assignments}
        old_places = {item.placement_id: item for item in current.placements}
        new_places = {item.placement_id: item for item in replacement.placements}
        for entry in history.entries:
            if entry.assignment_id is None:
                continue
            old, new = before[entry.assignment_id], after[entry.assignment_id]
            if old.worker != new.worker:
                raise ValueError("Referenced assignment ownership cannot change.")
            if old.placement_id is not None:
                if old.placement_id != new.placement_id:
                    raise ValueError("Referenced classification cannot be replaced.")
                old_place = old_places[old.placement_id]
                new_place = new_places[old.placement_id]
                if (old_place.job_id, old_place.workplace) != (
                    new_place.job_id,
                    new_place.workplace,
                ):
                    raise ValueError("Referenced placement identity cannot change.")

    def delete(
        self, expected: AssessmentHistory, document_id: str, jobs: JobCatalog
    ) -> AssessmentHistory:
        """Remove exact source/owner together inside the caller's transaction.

        Compare saved ownership before writing. Position gaps are compacted to preserve
        insertion order and avoid future insertion identity collisions. Any failure must
        roll back through the project transaction owner.

        Args:
            expected: Optional/exact previously read catalog used as a conflict
                precondition under the write lock; None disables that comparison only
                where allowed.
            document_id: Exact saved assessment identity to select/delete; never a
                displayed row position.
            jobs: Validated same-project parent job/placement/assignment catalog.

        Returns:
            Validated history after exact source/ownership removal and stable position
            compaction; no unrelated assessment changes.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            RuntimeError: The operation requires an idle default-mode connection or an
                existing caller-owned transaction as specified; that precondition is not
                met.
            ValueError: Saved ownership/source models, assignment references, expected
                history or resulting history invariants are invalid.
            KeyError: The requested exact source identity is absent from history.
        """
        if not self._connection.in_transaction:
            raise RuntimeError("Assessment deletion requires an active transaction.")
        current = self.read(jobs)
        if current != expected:
            raise ValueError("Assessment history changed since the expected snapshot.")
        if not any(e.document_id == document_id for e in current.entries):
            raise KeyError(document_id)
        replacement = replace(
            current,
            entries=tuple(e for e in current.entries if e.document_id != document_id),
        )
        self._connection.execute(
            "DELETE FROM assessment_ownership WHERE document_id=?", (document_id,)
        )
        self._connection.execute(
            "DELETE FROM draft_documents WHERE project_id=? AND document_id=?",
            (self._project_id, document_id),
        )
        for position, entry in enumerate(replacement.entries):
            self._connection.execute(
                "UPDATE assessment_ownership SET position=? WHERE document_id=?",
                (position, entry.document_id),
            )
        result = self.read(jobs)
        if result != replacement:
            raise ValueError("Deleted assessment history is inconsistent.")
        return result

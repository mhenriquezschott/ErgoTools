"""Transactional job/placement/assignment snapshots in version-five projects.

Infrastructure layer. Adapt immutable domain catalogs to parameterized SQLite or
explicit JSON payloads. The owning project retains this connection, thread lifetime and
cross-feature transaction coordination. No Qt controls, automatic old-project migration
or scientific recalculation occurs here. Stored source units/measurement scales remain
unchanged. Read methods do not silently repair corrupt records; standalone writes own
rollback and composed writes require caller rollback on any failure.
"""

import sqlite3
from collections.abc import Callable

from ergotools.domain.assessments.context import WorkerContext, WorkplaceContext
from ergotools.domain.job_catalog import (
    Job,
    JobCatalog,
    JobPlacement,
    WorkerJobAssignment,
)
from ergotools.domain.work_hierarchy import WorkHierarchy
from ergotools.infrastructure.draft_store import _idle

# Exact workplace SQL column order, matching _place and decoded constructor arguments.
_PLACE_COLUMNS = "plant, section, line, station, shift"
# Fixed nonnull text declaration for every full workplace identity component.
_PLACE_SCHEMA = (
    "plant TEXT NOT NULL, section TEXT NOT NULL, line TEXT NOT "
    "NULL, station TEXT NOT NULL, shift TEXT NOT NULL"
)


def _place(place: WorkplaceContext) -> tuple[str, ...]:
    """Project the full workplace identity into parameterized SQL order.

    Args:
        place: Full plant/section/line/station/shift identity in SQL field order.

    Returns:
        Plant, section, line, station and shift strings in exact SQL column order.
    """
    return (
        place.plant_name,
        place.section_name,
        place.line_name,
        place.station_id,
        place.shift_id,
    )


def _flag(value: int) -> bool:
    """Reject ambiguous stored activity flags instead of coercing truthiness.

    Args:
        value: Raw SQL or decoded JSON value to validate without coercion.

    Returns:
        Exact boolean projection of integer zero/one; no truthiness coercion.

    Raises:
        ValueError: Stored flags/relationships, project/hierarchy membership, expected
            catalog or protected references are invalid.
    """
    if type(value) is not int or value not in (0, 1):
        raise ValueError("Invalid stored activity flag.")
    return bool(value)


def create_job_schema(connection: sqlite3.Connection) -> None:
    """Create ordered relationship tables inside the project-create transaction.

    Args:
        connection: Borrowed dedicated owner-thread SQLite connection; caller retains
            close ownership and owns any enclosing transaction.

    Returns:
        None after ordered job, placement and assignment tables are created in the
        caller's transaction.

    Raises:
        sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
            transaction owner must roll back composed writes.
    """
    connection.execute(
        "CREATE TABLE jobs (id TEXT PRIMARY KEY NOT NULL, name TEXT "
        "NOT NULL, active INTEGER NOT NULL CHECK(active IN (0,1)), "
        "description TEXT, position INTEGER NOT NULL UNIQUE)"
    )
    connection.execute(
        f"CREATE TABLE job_placements (id INTEGER PRIMARY KEY, job_id "
        f"TEXT NOT NULL, {_PLACE_SCHEMA}, active INTEGER NOT NULL "
        f"CHECK(active IN (0,1)), valid_from TEXT, valid_to TEXT, notes "
        f"TEXT, position INTEGER NOT NULL UNIQUE)"
    )
    connection.execute(
        f"CREATE TABLE worker_assignments (id INTEGER PRIMARY KEY, "
        f"worker_id TEXT NOT NULL, {_PLACE_SCHEMA}, placement_id "
        f"INTEGER, active INTEGER NOT NULL CHECK(active IN (0,1)), "
        f"started_at TEXT, ended_at TEXT, notes TEXT, position INTEGER "
        f"NOT NULL UNIQUE)"
    )


class JobCatalogStore:
    """Borrow a dedicated connection; all cross-table rules are adapter-validated.

    Replacement is a snapshot operation, not a historical reassignment command.
    Direct SQL edits are unsupported. Existing assessment contexts are independent
    of job IDs; this layer does not invent historical assessment-assignment links.
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
        project_id: str,
        *,
        validate_change: Callable[[JobCatalog, JobCatalog], None] | None = None,
    ) -> None:
        """Configure project scope without creating or migrating tables.

        Args:
            connection: Borrowed dedicated owner-thread SQLite connection; caller
                retains close ownership and owns any enclosing transaction.
            project_id: Exact stable project identity used to validate stored ownership.
            validate_change: Optional same-transaction guard protecting referenced
                assignment/placement identities before catalog replacement.

        Returns:
            None; retain scope and optional change guard without creating tables or
            reading.
        """
        self._validate_change = validate_change
        self._connection = connection
        self._project_id = project_id

    def read(self) -> JobCatalog:
        """Reconstruct ordered typed records, rejecting damaged relationships.

        Args:
            None.

        Returns:
            Ordered immutable jobs, placements and assignments with validated internal
            relationships.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            ValueError: Stored flags/relationships, project/hierarchy membership,
                expected catalog or protected references are invalid.
        """
        jobs = tuple(
            Job(row[0], row[1], _flag(row[2]), row[3])
            for row in self._connection.execute(
                "SELECT id,name,active,description FROM jobs ORDER BY position"
            )
        )
        placements = tuple(
            JobPlacement(
                row[0],
                row[1],
                WorkplaceContext(*row[2:7]),
                _flag(row[7]),
                row[8],
                row[9],
                row[10],
            )
            for row in self._connection.execute(
                f"SELECT "
                f"id,job_id,{_PLACE_COLUMNS},active,valid_from,valid_to,notes "
                f"FROM job_placements ORDER BY position"
            )
        )
        assignments = tuple(
            WorkerJobAssignment(
                row[0],
                WorkerContext(self._project_id, row[1], WorkplaceContext(*row[2:7])),
                row[7],
                _flag(row[8]),
                row[9],
                row[10],
                row[11],
            )
            for row in self._connection.execute(
                f"SELECT "
                f"id,worker_id,{_PLACE_COLUMNS},placement_id,active,"
                "started_at,ended_at,notes "
                f"FROM worker_assignments ORDER BY position"
            )
        )
        return JobCatalog(self._project_id, jobs, placements, assignments)

    def validate_hierarchy(self, hierarchy: WorkHierarchy) -> None:
        """Protect job/assignment references during hierarchy reads and replacements.

        Args:
            hierarchy: Validated same-project hierarchy for membership/reference checks.

        Returns:
            None when every saved placement/assignment belongs to this hierarchy.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            ValueError: Stored flags/relationships, project/hierarchy membership,
                expected catalog or protected references are invalid.
        """
        self.read().validate_hierarchy(hierarchy)

    def delete_in_transaction(self, job_id: str) -> None:
        """Delete job/placements, retaining unclassified worker assignments.

        The owner checks history before calling and commits the combined profile and job
        deletion. This method never starts or commits a transaction.

        Args:
            job_id: Exact saved job identity for the requested operation.

        Returns:
            None after deleting the job/placements and unclassifying retained
            assignments; caller owns combined commit.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            RuntimeError: The operation requires an idle default-mode connection or an
                existing caller-owned transaction as specified; that precondition is not
                met.
        """
        if not self._connection.in_transaction:
            raise RuntimeError("Job deletion requires an active transaction.")
        self._connection.execute(
            "UPDATE worker_assignments SET placement_id=NULL WHERE placement_id IN "
            "(SELECT id FROM job_placements WHERE job_id=?)",
            (job_id,),
        )
        self._connection.execute("DELETE FROM job_placements WHERE job_id=?", (job_id,))
        self._connection.execute("DELETE FROM jobs WHERE id=?", (job_id,))

    def save_details_in_transaction(self, job: Job) -> None:
        """Upsert display fields only inside the owning Job Management transaction.

        Placement and worker-assignment rows are never rewritten by a form save. The
        owner validates catalogs and commits or rolls back the combined save.

        Args:
            job: Validated literal job form fields; placements/assignments are separate
                records.

        Returns:
            None after job-field upsert; placement/assignment rows and existing order
            remain unchanged.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            RuntimeError: The operation requires an idle default-mode connection or an
                existing caller-owned transaction as specified; that precondition is not
                met.
        """
        if not self._connection.in_transaction:
            raise RuntimeError("Job details require an active transaction.")
        self._connection.execute(
            "INSERT INTO jobs (id,name,active,description,position) "
            "VALUES (?,?,?,?,(SELECT COALESCE(MAX(position),-1)+1 FROM jobs)) "
            "ON CONFLICT(id) DO UPDATE SET name=excluded.name, "
            "active=excluded.active,description=excluded.description",
            (job.job_id, job.name, int(job.active), job.description),
        )

    def save(
        self,
        catalog: JobCatalog,
        hierarchy_loader: Callable[[], WorkHierarchy],
        *,
        expected: JobCatalog | None = None,
    ) -> None:
        """Replace all three record sets atomically after cross-catalog validation.

        Args:
            catalog: Complete validated same-project catalog in explicit record order.
            hierarchy_loader: Same-connection hierarchy reader invoked under the write
                lock; must not commit or open another connection.
            expected: Optional/exact previously read catalog used as a conflict
                precondition under the write lock; None disables that comparison only
                where allowed.

        Returns:
            None after all three catalogs commit together under one BEGIN IMMEDIATE
            transaction.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            RuntimeError: The operation requires an idle default-mode connection or an
                existing caller-owned transaction as specified; that precondition is not
                met.
            ValueError: Stored flags/relationships, project/hierarchy membership,
                expected catalog or protected references are invalid.
        """
        _idle(self._connection)
        if catalog.project_id != self._project_id:
            raise ValueError("Job catalog belongs to another project.")
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            hierarchy = hierarchy_loader()
            self.write_in_transaction(catalog, hierarchy, expected=expected)

    def write_in_transaction(
        self,
        catalog: JobCatalog,
        hierarchy: WorkHierarchy,
        *,
        expected: JobCatalog | None = None,
    ) -> None:
        """Validate/write within an owner's transaction; never commit separately.

        Args:
            catalog: Complete validated same-project catalog in explicit record order.
            hierarchy: Validated same-project hierarchy for membership/reference checks.
            expected: Optional/exact previously read catalog used as a conflict
                precondition under the write lock; None disables that comparison only
                where allowed.

        Returns:
            None after expected-value/reference checks and ordered replacement of all
            relationship tables and an in-place Job upsert; caller commits/rolls back.
            Surviving parent Jobs retain their foreign-key-owned calculator/risk rows.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            RuntimeError: The operation requires an idle default-mode connection or an
                existing caller-owned transaction as specified; that precondition is not
                met.
            ValueError: Stored flags/relationships, project/hierarchy membership,
                expected catalog or protected references are invalid.
        """
        if not self._connection.in_transaction:
            raise RuntimeError("Job writes require an active transaction.")
        if catalog.project_id != self._project_id:
            raise ValueError("Job catalog belongs to another project.")

        current = self.read()
        if expected is not None and current != expected:
            raise ValueError("Job catalog changed since the expected snapshot.")
        current.validate_hierarchy(hierarchy)
        catalog.validate_hierarchy(hierarchy)
        if self._validate_change is not None:
            self._validate_change(current, catalog)
        for table in ("worker_assignments", "job_placements"):
            self._connection.execute(f"DELETE FROM {table}")
        retained_ids = {job.job_id for job in catalog.jobs}
        self._connection.executemany(
            "DELETE FROM jobs WHERE id=?",
            [(job.job_id,) for job in current.jobs if job.job_id not in retained_ids],
        )
        self._connection.executemany(
            "INSERT INTO jobs VALUES (?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET name=excluded.name, active=excluded.active, "
            "description=excluded.description, position=excluded.position",
            [
                (item.job_id, item.name, int(item.active), item.description, index)
                for index, item in enumerate(catalog.jobs)
            ],
        )
        self._connection.executemany(
            "INSERT INTO job_placements VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    item.placement_id,
                    item.job_id,
                    *_place(item.workplace),
                    int(item.active),
                    item.valid_from,
                    item.valid_to,
                    item.notes,
                    index,
                )
                for index, item in enumerate(catalog.placements)
            ],
        )
        self._connection.executemany(
            "INSERT INTO worker_assignments VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    item.assignment_id,
                    item.worker.worker_id,
                    *_place(item.worker.workplace),
                    item.placement_id,
                    int(item.active),
                    item.started_at,
                    item.ended_at,
                    item.notes,
                    index,
                )
                for index, item in enumerate(catalog.assignments)
            ],
        )

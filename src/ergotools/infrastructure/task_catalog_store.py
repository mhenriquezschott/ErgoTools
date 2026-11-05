"""Transactional reusable task-name storage on the project-owned SQLite connection.

Infrastructure layer. No implicit schema creation on read, scientific recalculation,
source relabeling or definition merging. The project adapter owns references, lifetime
and transaction boundaries; this store never publishes a project file.
"""

import sqlite3

from ergotools.domain.task_catalog import TaskDefinition
from ergotools.infrastructure.draft_store import StoreFormatError


def create_task_schema(connection: sqlite3.Connection) -> None:
    """Create the current empty catalog inside a caller-owned schema transaction.

    Args:
        connection: Borrowed project connection with an active write transaction.

    Returns:
        None after creating the one project-local definition table.

    Raises:
        RuntimeError: Caller has not started the schema transaction.
        sqlite3.DatabaseError: Table creation fails; caller must roll back.
    """
    if not connection.in_transaction:
        raise RuntimeError("Task catalog creation requires a project transaction.")
    connection.execute(
        "CREATE TABLE task_definitions (definition_id TEXT PRIMARY KEY NOT NULL, "
        "name TEXT NOT NULL, description TEXT)"
    )


class TaskCatalogStore:
    """Borrow project storage; identity and source-reference checks stay explicit."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Retain the borrowed connection without reading or creating records.

        Args:
            connection: Owner-thread project connection; caller retains close ownership.

        Returns:
            None; no I/O or transaction starts during construction.
        """
        self._connection = connection

    def read(self) -> tuple[TaskDefinition, ...]:
        """Read exact typed definitions in stable binary identity order.

        Args:
            None.

        Returns:
            Immutable complete catalog, including definitions not currently referenced.

        Raises:
            sqlite3.DatabaseError: Catalog schema/read fails.
            StoreFormatError: Saved metadata cannot construct a valid definition.
        """
        try:
            return tuple(
                TaskDefinition(*row)
                for row in self._connection.execute(
                    "SELECT definition_id,name,description FROM task_definitions "
                    "ORDER BY definition_id"
                )
            )
        except ValueError as error:
            raise StoreFormatError("Invalid reusable task definition.") from error

    def replace_in_transaction(
        self,
        expected: tuple[TaskDefinition, ...],
        replacement: tuple[TaskDefinition, ...],
    ) -> None:
        """Write a complete already reference-validated catalog without committing.

        Args:
            expected: Exact previous catalog, checked again under the write lock.
            replacement: Desired distinct-ID typed definitions; labels may repeat.

        Returns:
            None after replacement; no assessment source/results are rewritten.

        Raises:
            RuntimeError: Caller has no active transaction.
            ValueError: Catalog is stale, untyped or has duplicate identities.
            sqlite3.DatabaseError: Write fails; caller must roll back.
        """
        if not self._connection.in_transaction:
            raise RuntimeError("Task catalog replacement requires a transaction.")
        if (
            self.read() != expected
            or not isinstance(replacement, tuple)
            or any(not isinstance(d, TaskDefinition) for d in replacement)
            or len({d.definition_id for d in replacement}) != len(replacement)
        ):
            raise ValueError("Task catalog is stale or has invalid definitions.")
        if expected == replacement:
            return
        self._connection.execute("DELETE FROM task_definitions")
        self._connection.executemany(
            "INSERT INTO task_definitions VALUES (?,?,?)",
            [(d.definition_id, d.name, d.description) for d in replacement],
        )

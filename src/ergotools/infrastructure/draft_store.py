"""Transactional draft storage in an explicitly initialized new SQLite database.

The caller owns and closes the connection. No legacy schema is opened, migrated or
inferred. Use a dedicated default-mode connection on its owner thread.

Infrastructure layer. Adapt validated application/domain values to explicit storage or
interchange formats. Use parameterized SQLite or caller-selected file paths; no Qt UI,
scientific formula changes or automatic old-project conversion. Connection ownership and
transaction boundaries are specified by each operation; I/O failures propagate unless
wrapped as a format error.
"""

import sqlite3
from abc import ABC, abstractmethod
from typing import ClassVar, Self

from ergotools.application.session import DocumentKey


class DocumentExistsError(ValueError):
    """A create-only document operation addressed an already persisted identity."""


class StoreFormatError(ValueError):
    """Database identity/version is unsupported; no migration is attempted."""


def _idle(connection: sqlite3.Connection) -> None:
    """Read connection state only; never begin, commit or roll back a transaction.

    Args:
        connection: Borrowed dedicated default-mode SQLite connection; no active
            transaction is permitted.

    Returns:
        None when the connection is idle and uses ordinary deferred transaction control.

    Raises:
        RuntimeError: Connection uses explicit autocommit, isolation_level=None or an
            existing transaction.
    """
    if (
        connection.autocommit != sqlite3.LEGACY_TRANSACTION_CONTROL
        or connection.isolation_level is None
        or connection.in_transaction
    ):
        raise RuntimeError("Storage requires an idle default-mode connection.")


class SqliteDraftStore[State](ABC):
    """Version-one document adapter; saves one project/document atomically."""

    format_id: ClassVar[str]

    @abstractmethod
    def encode(self, state: State) -> str:
        """Validate and serialize a source snapshot before a transaction starts.

        Pure codec hook; no persistence.

        Args:
            state: Typed immutable source snapshot for this adapter model.

        Returns:
            Validated complete source payload ready before transaction acquisition.

        Raises:
            ValueError: Source structure/values cannot be represented by the adapter
                codec.
        """

    @abstractmethod
    def decode(self, payload: str) -> State:
        """Validate and reconstruct a complete source snapshot.

        Pure codec hook; do not tolerate a partially decoded source.

        Args:
            payload: Complete stored UTF-8 JSON source text for this adapter model.

        Returns:
            Validated immutable typed source snapshot.

        Raises:
            ValueError: Payload structure, version, model or values are invalid.
        """

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Verify the format without creating schema or taking connection ownership.

        Args:
            connection: Borrowed idle default-mode owner-thread SQLite connection;
                caller retains close ownership.

        Returns:
            None after verifying the exact adapter format marker.

        Raises:
            RuntimeError: Connection is not idle/default-mode.
            StoreFormatError: Draft metadata is missing, unsupported or ambiguous.
        """
        _idle(connection)
        self._connection = connection
        self._verify()

    def _verify(self) -> None:
        """Read only; no connection ownership or migration.

        Args:
            None.

        Returns:
            None when the single metadata row exactly matches this adapter
            format/version.

        Raises:
            StoreFormatError: Metadata query fails or marker/version/row count is
                unsupported.
        """
        try:
            rows = self._connection.execute(
                "SELECT format, version FROM draft_metadata"
            ).fetchall()
        except sqlite3.DatabaseError as error:
            raise StoreFormatError("Not an initialized draft database.") from error
        if rows != [(self.format_id, 1)]:
            raise StoreFormatError("Unsupported draft database format or version.")

    @classmethod
    def create(cls, connection: sqlite3.Connection) -> Self:
        """Initialize an empty database atomically; never adopt an existing schema.

        Args:
            connection: Borrowed idle default-mode SQLite connection with an entirely
                empty schema.

        Returns:
            Adapter borrowing the initialized connection after schema creation commits.

        Raises:
            RuntimeError: Connection is not idle/default-mode.
            StoreFormatError: Schema is nonempty or post-creation metadata verification
                fails.
            sqlite3.DatabaseError: Schema initialization fails; the owned transaction
                rolls back.
        """
        _idle(connection)
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            if connection.execute("SELECT 1 FROM sqlite_master LIMIT 1").fetchone():
                raise StoreFormatError(
                    "Draft initialization requires an empty database."
                )
            connection.execute(
                "CREATE TABLE draft_metadata (format TEXT NOT NULL, "
                "version INTEGER NOT NULL)"
            )
            connection.execute(
                "INSERT INTO draft_metadata VALUES (?, ?)", (cls.format_id, 1)
            )
            connection.execute(
                "CREATE TABLE draft_documents (project_id TEXT NOT NULL, "
                "document_id TEXT NOT NULL, payload TEXT NOT NULL, "
                "PRIMARY KEY (project_id, document_id))"
            )
        return cls(connection)

    def validate_replacement(self, existing: str | None, state: State) -> None:
        """Allow adapters to check stored identity inside the write transaction.

        No I/O in the base hook; the surrounding writer owns the transaction.

        Args:
            existing: Previous encoded source under the write lock, or None for a new
                identity.
            state: Already codec-validated proposed immutable source.

        Returns:
            None; base hook permits replacement and subclasses can reject identity/model
            changes.
        """
        return None

    def save(self, document: DocumentKey, state: State) -> None:
        """Commit one validated snapshot; roll back failures and propagate the error.

        Args:
            document: Exact project/document identity to upsert.
            state: Typed source to validate before acquiring the write transaction.

        Returns:
            None after one atomic source upsert commits.

        Raises:
            RuntimeError: Connection is not idle/default-mode.
            ValueError: Codec/replacement identity validation fails.
            sqlite3.DatabaseError: Write fails and the transaction rolls back.
        """
        self._write(document, state, insert_only=False)

    def insert(self, document: DocumentKey, state: State) -> None:
        """Create a document once; an existing ID raises DocumentExistsError.

        Args:
            document: Exact project/document identity to create exclusively.
            state: Typed source to validate before acquiring the write transaction.

        Returns:
            None after one atomic exclusive insertion commits.

        Raises:
            DocumentExistsError: The document identity already exists.
            RuntimeError: Connection is not idle/default-mode.
            ValueError: Codec/replacement validation fails.
            sqlite3.DatabaseError: Write fails and the transaction rolls back.
        """
        self._write(document, state, insert_only=True)

    def list_documents(self, project_id: str) -> tuple[tuple[DocumentKey, State], ...]:
        """Read validated source snapshots in document-ID order without any writes.

        Args:
            project_id: Exact project identity used as a parameterized filter.

        Returns:
            Validated document/source pairs in binary document-ID order.

        Raises:
            RuntimeError: Connection is not idle/default-mode.
            StoreFormatError: Stored format marker is invalid.
            ValueError: A saved identity/source cannot be decoded.
            sqlite3.DatabaseError: Source query fails.
        """
        _idle(self._connection)
        self._verify()
        rows = self._connection.execute(
            "SELECT document_id, payload FROM draft_documents "
            "WHERE project_id=? ORDER BY document_id COLLATE BINARY",
            (project_id,),
        ).fetchall()
        return tuple(
            (DocumentKey(project_id, row[0]), self.decode(row[1])) for row in rows
        )

    def _write(self, document: DocumentKey, state: State, *, insert_only: bool) -> None:
        """Commit one validated source within a standalone write transaction.

        Args:
            document: Exact project/document source identity.
            state: Immutable typed replacement source.
            insert_only: True rejects an existing identity; False permits a validated
                upsert.

        Returns:
            None after validation and one BEGIN IMMEDIATE transaction commit.

        Raises:
            RuntimeError: Connection is not idle/default-mode.
            DocumentExistsError: Exclusive insertion collides.
            ValueError: Codec, format or replacement validation fails.
            sqlite3.DatabaseError: Write fails and the transaction rolls back.
        """
        _idle(self._connection)
        payload = self.encode(state)
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            self._write_payload(document, state, payload, insert_only=insert_only)

    def save_in_transaction(self, document: DocumentKey, state: State) -> None:
        """Replace source inside a caller-owned transaction without committing.

        Args:
            document: Exact project/document identity to replace.
            state: Typed source to validate and encode in the current write transaction.

        Returns:
            None after replacement; caller must commit or roll back the composed
            transaction.

        Raises:
            RuntimeError: No caller-owned transaction is active.
            ValueError: Codec, format or replacement validation fails.
            sqlite3.DatabaseError: The composed source write fails.
        """
        if not self._connection.in_transaction:
            raise RuntimeError("Saving requires a caller-owned transaction.")
        self._write_payload(document, state, self.encode(state), insert_only=False)

    def insert_in_transaction(self, document: DocumentKey, state: State) -> None:
        """Insert using a caller-owned transaction; never commit or roll it back.

        The caller must hold the dedicated connection write transaction and roll it back
        if any composed operation fails. Public insert still owns its complete
        standalone transaction.

        Args:
            document: Exact new project/document identity.
            state: Typed source to encode in the caller-owned transaction.

        Returns:
            None after exclusive insertion; caller owns commit/rollback.

        Raises:
            RuntimeError: No caller-owned transaction is active.
            DocumentExistsError: The identity already exists.
            ValueError: Codec/format validation fails.
            sqlite3.DatabaseError: The composed insertion fails.
        """
        if not self._connection.in_transaction:
            raise RuntimeError("Insertion requires a caller-owned transaction.")
        self._write_payload(document, state, self.encode(state), insert_only=True)

    def _write_payload(
        self, document: DocumentKey, state: State, payload: str, *, insert_only: bool
    ) -> None:
        """Upsert a prevalidated source under the existing write lock.

        Args:
            document: Exact project/document identity used in parameterized SQL.
            state: Validated typed source used for replacement identity checks.
            payload: Already encoded representation of state.
            insert_only: True requires no previous row; False permits replacement after
                validation.

        Returns:
            None after source upsert inside the existing write transaction.

        Raises:
            DocumentExistsError: An exclusive insertion addresses an existing source.
            StoreFormatError: Metadata or immutable model identity is invalid.
            ValueError: Subclass replacement validation rejects the source.
            sqlite3.DatabaseError: Lookup/upsert fails.
        """
        self._verify()
        previous = self._connection.execute(
            "SELECT payload FROM draft_documents WHERE project_id=? AND document_id=?",
            (document.project_id, document.document_id),
        ).fetchone()
        if insert_only and previous is not None:
            raise DocumentExistsError("Assessment identity already exists.")
        self.validate_replacement(previous[0] if previous else None, state)
        self._connection.execute(
            "INSERT INTO draft_documents VALUES (?, ?, ?) "
            "ON CONFLICT(project_id, document_id) "
            "DO UPDATE SET payload=excluded.payload",
            (document.project_id, document.document_id, payload),
        )

    def load(self, document: DocumentKey) -> State:
        """Load a validated snapshot; raise KeyError for an absent document.

        Args:
            document: Exact project/document identity to retrieve.

        Returns:
            Complete validated saved source snapshot.

        Raises:
            KeyError: No saved source has that exact identity.
            RuntimeError: Connection is not idle/default-mode.
            StoreFormatError: Format marker is unsupported.
            ValueError: Stored source decoding fails.
            sqlite3.DatabaseError: Source query fails.
        """
        _idle(self._connection)
        self._verify()
        row = self._connection.execute(
            "SELECT payload FROM draft_documents WHERE project_id=? AND document_id=?",
            (document.project_id, document.document_id),
        ).fetchone()
        if row is None:
            raise KeyError(document)
        return self.decode(row[0])

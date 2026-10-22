"""SQLite ownership associations for explicitly created version-three projects.

Infrastructure layer. Adapt immutable domain catalogs to parameterized SQLite or
explicit JSON payloads. The owning project retains this connection, thread lifetime and
cross-feature transaction coordination. No Qt controls, automatic old-project migration
or scientific recalculation occurs here. Stored source units/measurement scales remain
unchanged. Read methods do not silently repair corrupt records; standalone writes own
rollback and composed writes require caller rollback on any failure.
"""

import sqlite3
from collections.abc import Callable

from ergotools.application.assessment_binding import AssessmentBinding
from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.context import (
    AssessmentContext,
    WorkerContext,
    WorkplaceContext,
)
from ergotools.domain.assessments.document import AssessmentKind, assessment_kind
from ergotools.infrastructure.assessment_serialization import decode_assessment
from ergotools.infrastructure.draft_store import StoreFormatError, _idle

# Full binding SQL projection order shared by decode and parameterized insertion.
_COLUMNS = (
    "project_id, document_id, worker_id, plant_name, section_name, "
    "line_name, station_id, shift_id, kind"
)


def create_binding_schema(connection: sqlite3.Connection) -> None:
    """Create ownership constraints inside the caller's project-create transaction.

    Args:
        connection: Borrowed dedicated owner-thread SQLite connection; caller retains
            close ownership and owns any enclosing transaction.

    Returns:
        None after ownership table creation; caller owns commit/rollback.

    Raises:
        sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
            transaction owner must roll back composed writes.
    """
    connection.execute(
        "CREATE TABLE assessment_bindings ("
        "project_id TEXT NOT NULL, document_id TEXT NOT NULL, "
        "worker_id TEXT NOT NULL, plant_name TEXT NOT NULL, "
        "section_name TEXT NOT NULL, line_name TEXT NOT NULL, "
        "station_id TEXT NOT NULL, shift_id TEXT NOT NULL, kind TEXT NOT NULL, "
        "PRIMARY KEY (project_id, document_id), "
        "UNIQUE (project_id, worker_id, plant_name, section_name, line_name, "
        "station_id, shift_id, kind))"
    )


def _context_values(context: AssessmentContext) -> tuple[str, ...]:
    """Project exact ownership into parameterized SQL order.

    Args:
        context: Exact project/worker/workplace/model identity; every component
            participates in lookup.

    Returns:
        Project, worker, plant, section, line, station, shift and model strings in exact
        SQL order.
    """
    owner = context.worker
    place = owner.workplace
    return (
        owner.project_id,
        owner.worker_id,
        place.plant_name,
        place.section_name,
        place.line_name,
        place.station_id,
        place.shift_id,
        context.kind.value,
    )


class AssessmentBindingStore:
    """Borrow the project's dedicated connection; never own or migrate it.

    Only this adapter writes associations. Direct SQL changes are unsupported;
    reads and project open validate references/model identity to detect damage.
    Version-four projects inject catalog membership validation; version three
    retains its original behavior without a persisted catalog.
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
        project_id: str,
        *,
        validate_owner: Callable[[WorkerContext], None] | None = None,
    ) -> None:
        """Validate stored bindings without creating or modifying schema.

        Args:
            connection: Borrowed dedicated owner-thread SQLite connection; caller
                retains close ownership and owns any enclosing transaction.
            project_id: Exact stable project identity used to validate stored ownership.
            validate_owner: Optional same-connection worker/workplace membership
                validator; no commit or connection ownership transfer.

        Returns:
            None after validating every stored binding without changing schema or taking
            close ownership.

        Raises:
            RuntimeError: The operation requires an idle default-mode connection or an
                existing caller-owned transaction as specified; that precondition is not
                met.
            ValueError: Binding/project/catalog/model identity is invalid or immutable
                ownership would change.
            KeyError: The binding references an absent saved source.
            StoreFormatError: Saved source model disagrees with the binding.
        """
        _idle(connection)
        self._validate_owner = validate_owner
        self._connection = connection
        self._project_id = project_id
        rows = connection.execute(
            f"SELECT {_COLUMNS} FROM assessment_bindings"
        ).fetchall()
        for row in rows:
            self._decode(row)

    def _decode(self, row: tuple[str, ...]) -> AssessmentBinding:
        """Reconstruct and validate the saved ownership or schedule payload.

        Args:
            row: Complete SQL row in the adapter's declared column order; raw values are
                validated before returning.

        Returns:
            Typed binding after source/model/membership validation.

        Raises:
            ValueError: Binding/project/catalog/model identity is invalid or immutable
                ownership would change.
            KeyError: The binding references an absent saved source.
            StoreFormatError: Saved source model disagrees with the binding.
        """
        binding = AssessmentBinding(
            DocumentKey(row[0], row[1]),
            AssessmentContext(
                WorkerContext(row[0], row[2], WorkplaceContext(*row[3:8])),
                AssessmentKind(row[8]),
            ),
        )
        self._validate(binding)
        return binding

    def _validate(self, binding: AssessmentBinding) -> None:
        """Check binding ownership against the exact saved source and optional catalog.

        Args:
            binding: Exact immutable source identity and original worker/workplace/model
                ownership.

        Returns:
            None when project ownership, optional catalog membership and saved source
            model all agree.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            ValueError: Binding/project/catalog/model identity is invalid or immutable
                ownership would change.
            KeyError: The binding references an absent saved source.
            StoreFormatError: Saved source model disagrees with the binding.
        """
        if binding.document.project_id != self._project_id:
            raise ValueError("Assessment belongs to another project.")
        if self._validate_owner is not None:
            self._validate_owner(binding.context.worker)
        row = self._connection.execute(
            "SELECT payload FROM draft_documents WHERE project_id=? AND document_id=?",
            (binding.document.project_id, binding.document.document_id),
        ).fetchone()
        if row is None:
            raise KeyError(binding.document)
        if assessment_kind(decode_assessment(row[0])) != binding.context.kind:
            raise StoreFormatError("Assessment ownership model does not match draft.")

    def bind(self, binding: AssessmentBinding) -> None:
        """Commit an immutable association; roll back conflicts or failed writes.

        Args:
            binding: Exact immutable source identity and original worker/workplace/model
                ownership.

        Returns:
            None after an immutable association commits atomically; conflicts roll back.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            RuntimeError: The operation requires an idle default-mode connection or an
                existing caller-owned transaction as specified; that precondition is not
                met.
            ValueError: Binding/project/catalog/model identity is invalid or immutable
                ownership would change.
            KeyError: The binding references an absent saved source.
            StoreFormatError: Saved source model disagrees with the binding.
        """
        _idle(self._connection)
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            self.bind_in_transaction(binding)

    def bind_in_transaction(self, binding: AssessmentBinding) -> None:
        """Validate and bind inside a caller-owned write transaction, without commit.

        The transaction owner must roll back all composed operations on failure.

        Args:
            binding: Exact immutable source identity and original worker/workplace/model
                ownership.

        Returns:
            None after validating/idempotently inserting ownership; caller must roll
            back composed failures.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            RuntimeError: The operation requires an idle default-mode connection or an
                existing caller-owned transaction as specified; that precondition is not
                met.
            ValueError: Binding/project/catalog/model identity is invalid or immutable
                ownership would change.
            KeyError: The binding references an absent saved source.
            StoreFormatError: Saved source model disagrees with the binding.
        """
        if not self._connection.in_transaction:
            raise RuntimeError("Binding requires a caller-owned transaction.")
        self._validate(binding)
        row = self._connection.execute(
            f"SELECT {_COLUMNS} FROM assessment_bindings "
            "WHERE project_id=? AND document_id=?",
            (binding.document.project_id, binding.document.document_id),
        ).fetchone()
        if row is not None:
            if self._decode(row) != binding:
                raise ValueError("An assessment cannot change ownership.")
            return
        self._connection.execute(
            f"INSERT INTO assessment_bindings ({_COLUMNS}) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                binding.document.project_id,
                binding.document.document_id,
                *_context_values(binding.context)[1:],
            ),
        )

    def get(self, document: DocumentKey) -> AssessmentBinding | None:
        """Return validated persisted ownership, or None for an unbound document.

        Args:
            document: Exact project/document identity used as a parameterized key.

        Returns:
            Validated saved ownership, or None only for an unbound source identity.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            RuntimeError: The operation requires an idle default-mode connection or an
                existing caller-owned transaction as specified; that precondition is not
                met.
            ValueError: Binding/project/catalog/model identity is invalid or immutable
                ownership would change.
            KeyError: The binding references an absent saved source.
            StoreFormatError: Saved source model disagrees with the binding.
        """
        _idle(self._connection)
        row = self._connection.execute(
            f"SELECT {_COLUMNS} FROM assessment_bindings "
            "WHERE project_id=? AND document_id=?",
            (document.project_id, document.document_id),
        ).fetchone()
        return None if row is None else self._decode(row)

    def find(self, context: AssessmentContext) -> DocumentKey | None:
        """Resolve all exact ownership fields; never select another shift or model.

        Args:
            context: Exact project/worker/workplace/model identity; every component
                participates in lookup.

        Returns:
            Exact saved document key, or None only for no matching full ownership tuple.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            RuntimeError: The operation requires an idle default-mode connection or an
                existing caller-owned transaction as specified; that precondition is not
                met.
            ValueError: Binding/project/catalog/model identity is invalid or immutable
                ownership would change.
            KeyError: The binding references an absent saved source.
            StoreFormatError: Saved source model disagrees with the binding.
        """
        _idle(self._connection)
        values = _context_values(context)
        row = self._connection.execute(
            f"SELECT {_COLUMNS} FROM assessment_bindings WHERE project_id=? "
            "AND worker_id=? AND plant_name=? AND section_name=? AND line_name=? "
            "AND station_id=? AND shift_id=? AND kind=?",
            values,
        ).fetchone()
        return None if row is None else self._decode(row).document

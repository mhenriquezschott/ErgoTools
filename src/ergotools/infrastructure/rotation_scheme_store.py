"""Explicit transactional scheme records on the workspace-owned connection.

Infrastructure layer. Adapt immutable domain catalogs to parameterized SQLite or
explicit JSON payloads. The owning project retains this connection, thread lifetime and
cross-feature transaction coordination. No Qt controls, automatic old-project migration
or scientific recalculation occurs here. Stored source units/measurement scales remain
unchanged. Read methods do not silently repair corrupt records; standalone writes own
rollback and composed writes require caller rollback on any failure.
"""

import json
import sqlite3

from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation import WorkerRotation
from ergotools.domain.rotation_scheme import (
    RotationMode,
    RotationScheme,
    RotationTarget,
    RotationWorkerLink,
)
from ergotools.infrastructure.lifft_store import StoreFormatError


def create_rotation_schema(connection: sqlite3.Connection) -> None:
    """Create an empty scheme table inside an explicit owner transaction.

    Args:
        connection: Borrowed dedicated owner-thread SQLite connection; caller retains
            close ownership and owns any enclosing transaction.

    Returns:
        None after rotation table creation inside an existing caller-owned transaction.

    Raises:
        sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
            transaction owner must roll back composed writes.
        RuntimeError: The operation requires an idle default-mode connection or an
            existing caller-owned transaction as specified; that precondition is not
            met.
    """
    if not connection.in_transaction:
        raise RuntimeError("Rotation schema requires a project transaction.")
    connection.execute(
        "CREATE TABLE rotation_schemes (scheme_id TEXT PRIMARY KEY,"
        "payload TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,"
        "updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )


class RotationSchemeStore:
    """Borrow a connection; project owner validates catalogs and owns transactions."""

    def __init__(self, connection: sqlite3.Connection, project_id: str) -> None:
        """Retain project identity without reading or creating tables.

        Args:
            connection: Borrowed dedicated owner-thread SQLite connection; caller
                retains close ownership and owns any enclosing transaction.
            project_id: Exact stable project identity used to validate stored ownership.

        Returns:
            None; retain project ownership without I/O.
        """
        self._connection = connection
        self._project_id = project_id

    def read(self) -> tuple[RotationScheme, ...]:
        """Read ordered schemes; malformed or foreign records are format errors.

        Args:
            None.

        Returns:
            Validated same-project schemes ordered by case-insensitive identity then
            binary tie-breaker.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            StoreFormatError: Payload structure/values or saved scheme/project ownership
                is invalid.
        """
        result = []
        try:
            for identity, payload in self._connection.execute(
                "SELECT scheme_id,payload FROM rotation_schemes "
                "ORDER BY scheme_id COLLATE NOCASE,scheme_id"
            ):
                scheme = _decode(payload)
                if (
                    scheme.scheme_id != identity
                    or scheme.project_id != self._project_id
                ):
                    raise ValueError("Rotation record identity does not match.")
                result.append(scheme)
        except (ValueError, TypeError, KeyError, IndexError) as error:
            raise StoreFormatError("Invalid saved rotation scheme.") from error
        return tuple(result)

    def write_in_transaction(self, scheme: RotationScheme) -> None:
        """Upsert one validated scheme without touching others or committing.

        Args:
            scheme: Validated same-project schedule with frozen
                Job/placement/assignment identities.

        Returns:
            None after upserting one scheme payload and updated timestamp; other schemes
            remain unchanged.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            RuntimeError: The operation requires an idle default-mode connection or an
                existing caller-owned transaction as specified; that precondition is not
                met.
            ValueError: Scheme belongs to another project.
        """
        if not self._connection.in_transaction:
            raise RuntimeError("Rotation writes require a project transaction.")
        if scheme.project_id != self._project_id:
            raise ValueError("Rotation belongs to a different project.")
        self._connection.execute(
            "INSERT INTO rotation_schemes(scheme_id,payload) VALUES (?,?) "
            "ON CONFLICT(scheme_id) DO UPDATE SET payload=excluded.payload,"
            "updated_at=CURRENT_TIMESTAMP",
            (scheme.scheme_id, _encode(scheme)),
        )

    def delete_in_transaction(self, scheme_id: str) -> None:
        """Delete an existing scheme under owner consent; unknown IDs raise KeyError.

        Args:
            scheme_id: Exact existing rotation identity selected for deletion.

        Returns:
            None after deleting exactly one scheme; caller commits/rolls back.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            RuntimeError: The operation requires an idle default-mode connection or an
                existing caller-owned transaction as specified; that precondition is not
                met.
            KeyError: No exact existing scheme was deleted.
        """
        if not self._connection.in_transaction:
            raise RuntimeError("Rotation deletion requires a project transaction.")
        cursor = self._connection.execute(
            "DELETE FROM rotation_schemes WHERE scheme_id=?", (scheme_id,)
        )
        if cursor.rowcount != 1:
            raise KeyError(scheme_id)


def _encode(scheme: RotationScheme) -> str:
    """Encode exact frozen rotation ownership and schedule without recalculation.

    Args:
        scheme: Validated same-project schedule with frozen Job/placement/assignment
            identities.

    Returns:
        Compact version-two Unicode JSON preserving exact schedule/target/link/scope
        order without derived calculations.
    """
    return json.dumps(
        {
            "version": 2,
            "project_id": scheme.project_id,
            "scheme_id": scheme.scheme_id,
            "name": scheme.name,
            "description": scheme.description,
            "mode": scheme.mode.value,
            "primary_kind": scheme.primary_kind.value if scheme.primary_kind else None,
            "workers": [[w.worker_id, w.assignment_id] for w in scheme.workers],
            "targets": [[t.job_id, t.placement_id] for t in scheme.targets],
            "current": [[r.worker_id, list(r.target_keys)] for r in scheme.current],
            "scope": [
                [c.plant_name, c.section_name, c.line_name, c.station_id, c.shift_id]
                for c in scheme.scope
            ],
        },
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    )


def _decode(payload: str) -> RotationScheme:
    """Reconstruct and validate the saved ownership or schedule payload.

    Args:
        payload: Complete saved JSON payload to decode; shape/version and domain values
            are validated.

    Returns:
        Validated immutable scheme with exact frozen links, schedule, scope and
        model/mode identities.

    Raises:
        ValueError: JSON, payload version/member/row shape or domain values are invalid.
        TypeError: A nested decoded value has an incompatible constructor type.
        KeyError: A required nested payload member is absent.
    """
    data = json.loads(payload)
    keys = {
        "version",
        "project_id",
        "scheme_id",
        "name",
        "description",
        "mode",
        "primary_kind",
        "workers",
        "targets",
        "current",
        "scope",
    }
    if (
        not isinstance(data, dict)
        or set(data) != keys
        or type(data["version"]) is not int
        or data["version"] != 2
    ):
        raise ValueError("Unsupported rotation payload.")
    for name, width in (("workers", 2), ("targets", 2), ("current", 2), ("scope", 5)):
        rows = data[name]
        if not isinstance(rows, list) or any(
            not isinstance(row, list) or len(row) != width for row in rows
        ):
            raise ValueError("Invalid rotation record shape.")
    if any(not isinstance(row[1], list) for row in data["current"]):
        raise ValueError("Invalid rotation target sequence.")
    return RotationScheme(
        data["project_id"],
        data["scheme_id"],
        data["name"],
        tuple(RotationWorkerLink(*row) for row in data["workers"]),
        tuple(RotationTarget(*row) for row in data["targets"]),
        tuple(WorkerRotation(row[0], tuple(row[1])) for row in data["current"]),
        tuple(WorkplaceContext(*row) for row in data["scope"]),
        RotationMode(data["mode"]),
        AssessmentKind(data["primary_kind"])
        if data["primary_kind"] is not None
        else None,
        data["description"],
    )

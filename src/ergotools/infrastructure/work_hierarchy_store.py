"""Atomic ordered hierarchy snapshots for version-four project repositories.

Infrastructure layer. Adapt immutable domain catalogs to parameterized SQLite or
explicit JSON payloads. The owning project retains this connection, thread lifetime and
cross-feature transaction coordination. No Qt controls, automatic old-project migration
or scientific recalculation occurs here. Stored source units/measurement scales remain
unchanged. Read methods do not silently repair corrupt records; standalone writes own
rollback and composed writes require caller rollback on any failure.
"""

import json
import sqlite3
from collections.abc import Callable
from dataclasses import asdict, fields

from ergotools.domain.assessments.context import WorkerContext, WorkplaceContext
from ergotools.domain.organization_record import (
    ORGANIZATION_FIELDS,
    OrganizationKind,
    OrganizationRecord,
)
from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy
from ergotools.domain.worker_details import WorkerDetails
from ergotools.infrastructure.draft_json import (
    DocumentFormatError,
    document_fields,
    document_number,
    document_text,
    unique_object,
)
from ergotools.infrastructure.draft_store import _idle


def _array(value: object) -> list[object]:
    """Require a JSON array without substituting another collection type.

    Args:
        value: Raw SQL or decoded JSON value to validate without coercion.

    Returns:
        The original JSON list after shape validation, without copying or coercion.

    Raises:
        ValueError: Decoded fields/domain values, same-project membership, protected
            saved references or expected hierarchy are invalid.
        DocumentFormatError: JSON shape/member types, version or singleton catalog
            structure is invalid.
    """
    if not isinstance(value, list):
        raise DocumentFormatError("Expected a catalog array.")
    return value


def _name(value: object) -> str | None:
    """Require optional worker text without coercing numeric values.

    Args:
        value: Raw SQL or decoded JSON value to validate without coercion.

    Returns:
        Original optional text, including literal empty text when supplied; None stays
        absent.

    Raises:
        ValueError: Decoded fields/domain values, same-project membership, protected
            saved references or expected hierarchy are invalid.
        DocumentFormatError: JSON shape/member types, version or singleton catalog
            structure is invalid.
    """
    if value is not None and not isinstance(value, str):
        raise DocumentFormatError("Expected an optional worker name.")
    return value


def _key(value: object, fields: tuple[str, ...]) -> tuple[str, ...]:
    """Read all exact identity members in their declared order.

    Args:
        value: Raw SQL or decoded JSON value to validate without coercion.
        fields: Exact expected identity field names in the required output order.

    Returns:
        Required text identity components in fields order after exact-member validation.

    Raises:
        ValueError: Decoded fields/domain values, same-project membership, protected
            saved references or expected hierarchy are invalid.
        DocumentFormatError: JSON shape/member types, version or singleton catalog
            structure is invalid.
    """
    record = document_fields(value, set(fields))
    return tuple(document_text(record[field]) for field in fields)


def encode_hierarchy(hierarchy: WorkHierarchy) -> str:
    """Encode ordered identity records with an explicit independent payload version.

    Args:
        hierarchy: Validated same-project hierarchy for membership/reference checks.

    Returns:
        Compact ASCII-safe version-three JSON preserving explicit order, empty parents
        and canonical worker cm/kg fields.

    Raises:
        ValueError: Decoded fields/domain values, same-project membership, protected
            saved references or expected hierarchy are invalid.
    """
    return json.dumps(
        {"version": 3, "hierarchy": asdict(hierarchy)},
        ensure_ascii=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def decode_hierarchy(payload: str) -> WorkHierarchy:
    """Reject ambiguous JSON, unknown fields, duplicate keys and orphan records.

    Args:
        payload: Complete saved JSON payload to decode; shape/version and domain values
            are validated.

    Returns:
        Validated hierarchy reconstructed from payload versions one through three;
        absent older optional data stays absent.

    Raises:
        ValueError: Decoded fields/domain values, same-project membership, protected
            saved references or expected hierarchy are invalid.
        DocumentFormatError: JSON shape/member types, version or singleton catalog
            structure is invalid.
    """
    envelope = document_fields(
        json.loads(payload, object_pairs_hook=unique_object), {"version", "hierarchy"}
    )
    if type(envelope["version"]) is not int or envelope["version"] not in (1, 2, 3):
        raise DocumentFormatError("Unsupported catalog payload version.")
    hierarchy_fields = {"work", "plants", "sections", "lines"}
    if envelope["version"] == 3:
        hierarchy_fields.add("organization")
    hierarchy = document_fields(envelope["hierarchy"], hierarchy_fields)
    organization = []
    for item in _array(hierarchy.get("organization", [])):
        record = document_fields(item, {"kind", "keys", "attributes"})
        kind = OrganizationKind(document_text(record["kind"]))
        field_types = dict(ORGANIZATION_FIELDS[kind.value])
        attributes = []
        for entry in _array(record["attributes"]):
            pair = _array(entry)
            if len(pair) != 2:
                raise DocumentFormatError("Invalid organization field pair.")
            name = document_text(pair[0])
            field_value = (
                document_number(pair[1])
                if field_types.get(name) == "number"
                else _name(pair[1])
            )
            attributes.append((name, field_value))
        organization.append(
            OrganizationRecord(
                kind,
                tuple(document_text(k) for k in _array(record["keys"])),
                tuple(attributes),
            )
        )
    work = document_fields(
        hierarchy["work"], {"project_id", "workers", "stations", "shifts"}
    )
    workers = []
    for value in _array(work["workers"]):
        expected = {"worker_id", "first_name", "last_name"}
        if envelope["version"] >= 2:
            expected.add("details")
        worker = document_fields(value, expected)
        details = None
        if worker.get("details") is not None:
            record = document_fields(
                worker["details"], {item.name for item in fields(WorkerDetails)}
            )
            details = WorkerDetails(
                birth_date=_name(record["birth_date"]),
                sex=_name(record["sex"]),
                height_cm=document_number(record["height_cm"]),
                weight_kg=document_number(record["weight_kg"]),
                hiring_date=_name(record["hiring_date"]),
                address=_name(record["address"]),
                city=_name(record["city"]),
                region=_name(record["region"]),
                country=_name(record["country"]),
                postal_code=_name(record["postal_code"]),
                email=_name(record["email"]),
            )
        workers.append(
            WorkerEntry(
                document_text(worker["worker_id"]),
                _name(worker["first_name"]),
                _name(worker["last_name"]),
                details,
            )
        )
    ancestry = ("plant_name", "section_name", "line_name")
    return WorkHierarchy(
        WorkCatalog(
            document_text(work["project_id"]),
            tuple(workers),
            tuple(
                StationKey(*_key(row, (*ancestry, "station_id")))
                for row in _array(work["stations"])
            ),
            tuple(document_text(row) for row in _array(work["shifts"])),
        ),
        tuple(document_text(row) for row in _array(hierarchy["plants"])),
        tuple(
            SectionKey(*_key(row, ancestry[:2]))
            for row in _array(hierarchy["sections"])
        ),
        tuple(LineKey(*_key(row, ancestry)) for row in _array(hierarchy["lines"])),
        tuple(organization),
    )


def create_hierarchy_schema(connection: sqlite3.Connection, project_id: str) -> None:
    """Seed an empty ordered catalog inside the project-creation transaction.

    Args:
        connection: Borrowed dedicated owner-thread SQLite connection; caller retains
            close ownership and owns any enclosing transaction.
        project_id: Exact stable project identity used to validate stored ownership.

    Returns:
        None after singleton table creation and empty same-project catalog insertion;
        caller owns transaction.

    Raises:
        sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
            transaction owner must roll back composed writes.
    """
    connection.execute(
        "CREATE TABLE work_catalog (singleton INTEGER PRIMARY KEY CHECK(singleton=1), "
        "payload TEXT NOT NULL)"
    )
    connection.execute(
        "INSERT INTO work_catalog VALUES (1, ?)",
        (encode_hierarchy(WorkHierarchy(WorkCatalog(project_id))),),
    )


class WorkHierarchyStore:
    """Borrow a dedicated connection; integrity is validated at adapter boundaries.

    Catalog and binding mutations use the same write lock. Direct SQL edits are
    unsupported; payload and cross-reference validation detects damaged data.
    JSON arrays retain explicit order and empty parents without lossy inference.
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
        project_id: str,
        *,
        validate_jobs: Callable[[WorkHierarchy], None] | None = None,
    ) -> None:
        """Configure a project-scoped adapter without creating schema.

        Args:
            connection: Borrowed dedicated owner-thread SQLite connection; caller
                retains close ownership and owns any enclosing transaction.
            project_id: Exact stable project identity used to validate stored ownership.
            validate_jobs: Optional same-connection callback protecting job/assignment
                references against hierarchy changes.

        Returns:
            None; retain project scope and reference callback without I/O.
        """
        self._validate_jobs = validate_jobs
        self._connection = connection
        self._project_id = project_id

    def _check_owner(self, hierarchy: WorkHierarchy, owner: WorkerContext) -> None:
        """Validate exact worker and workplace membership in the saved project.

        Args:
            hierarchy: Validated same-project hierarchy for membership/reference checks.
            owner: Exact project/worker/workplace ownership to validate against the
                hierarchy.

        Returns:
            None when project, worker and exact workplace membership all agree.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            ValueError: Decoded fields/domain values, same-project membership, protected
                saved references or expected hierarchy are invalid.
            KeyError: A referenced exact worker or workplace identity is absent.
        """
        if owner.project_id != hierarchy.work.project_id:
            raise ValueError("Catalog ownership cannot cross projects.")
        hierarchy.work.worker_context(owner.worker_id, owner.workplace)

    def _validate_references(self, hierarchy: WorkHierarchy) -> None:
        """Protect saved binding and job references against hierarchy replacement.

        Args:
            hierarchy: Validated same-project hierarchy for membership/reference checks.

        Returns:
            None when project identity, optional job guard and all saved context
            bindings remain valid.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            ValueError: Decoded fields/domain values, same-project membership, protected
                saved references or expected hierarchy are invalid.
            KeyError: A referenced exact worker or workplace identity is absent.
        """
        if hierarchy.work.project_id != self._project_id:
            raise ValueError("Catalog belongs to another project.")
        if self._validate_jobs is not None:
            self._validate_jobs(hierarchy)
        bindings = self._connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' "
            "AND name='assessment_bindings'"
        ).fetchone()
        if bindings:
            rows = self._connection.execute(
                "SELECT project_id, worker_id, plant_name, section_name, line_name, "
                "station_id, shift_id FROM assessment_bindings"
            ).fetchall()
        else:
            # Current projects validate the real assignment/tool ownership links;
            # no empty context-binding table is required or validation skipped.
            rows = self._connection.execute(
                "SELECT ?, a.worker_id,a.plant,a.section,a.line,a.station,a.shift "
                "FROM assessment_ownership AS o JOIN worker_assignments AS a "
                "ON a.id=o.assignment_id",
                (self._project_id,),
            ).fetchall()
            missing = self._connection.execute(
                "SELECT 1 FROM assessment_ownership AS o "
                "LEFT JOIN worker_assignments AS a ON a.id=o.assignment_id "
                "WHERE o.assignment_id IS NOT NULL AND a.id IS NULL LIMIT 1"
            ).fetchone()
            workers = {w.worker_id for w in hierarchy.work.workers}
            owners = self._connection.execute(
                "SELECT worker_id FROM assessment_ownership"
            ).fetchall()
            if any(row[0] not in workers for row in owners):
                raise ValueError("Assessment ownership references a missing worker.")
            if missing:
                raise ValueError(
                    "Assessment ownership references a missing assignment."
                )
        for row in rows:
            self._check_owner(
                hierarchy, WorkerContext(row[0], row[1], WorkplaceContext(*row[2:]))
            )

    def read(self) -> WorkHierarchy:
        """Read and validate inside an existing transaction or an idle connection.

        Args:
            None.

        Returns:
            Validated singleton hierarchy with exact ownership and saved-reference
            checks.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            ValueError: Decoded fields/domain values, same-project membership, protected
                saved references or expected hierarchy are invalid.
            DocumentFormatError: JSON shape/member types, version or singleton catalog
                structure is invalid.
            KeyError: A referenced exact worker or workplace identity is absent.
        """
        rows = self._connection.execute(
            "SELECT singleton, payload FROM work_catalog"
        ).fetchall()
        if len(rows) != 1 or rows[0][0] != 1:
            raise DocumentFormatError("Expected exactly one project catalog.")
        hierarchy = decode_hierarchy(rows[0][1])
        self._validate_references(hierarchy)
        return hierarchy

    def validate_owner(self, owner: WorkerContext) -> None:
        """Validate new binding membership under its caller's write transaction.

        Args:
            owner: Exact project/worker/workplace ownership to validate against the
                hierarchy.

        Returns:
            None when the proposed source owner exists in the validated saved catalog.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            ValueError: Decoded fields/domain values, same-project membership, protected
                saved references or expected hierarchy are invalid.
            KeyError: A referenced exact worker or workplace identity is absent.
        """
        self._check_owner(self.read(), owner)

    def save(
        self, hierarchy: WorkHierarchy, *, expected: WorkHierarchy | None = None
    ) -> None:
        """Commit all records together or preserve the previous catalog on failure.

        Args:
            hierarchy: Validated same-project hierarchy for membership/reference checks.
            expected: Optional/exact previously read catalog used as a conflict
                precondition under the write lock; None disables that comparison only
                where allowed.

        Returns:
            None after conflict/reference checks and one atomic singleton replacement
            commit.

        Raises:
            sqlite3.DatabaseError: A schema, catalog or source query/write fails; the
                transaction owner must roll back composed writes.
            RuntimeError: The operation requires an idle default-mode connection or an
                existing caller-owned transaction as specified; that precondition is not
                met.
            ValueError: Decoded fields/domain values, same-project membership, protected
                saved references or expected hierarchy are invalid.
            KeyError: A referenced exact worker or workplace identity is absent.
        """
        _idle(self._connection)
        payload = encode_hierarchy(hierarchy)
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            current = self.read()
            if expected is not None and current != expected:
                raise ValueError("Catalog changed since the expected snapshot.")
            self._validate_references(hierarchy)
            self._connection.execute(
                "UPDATE work_catalog SET payload=? WHERE singleton=1", (payload,)
            )

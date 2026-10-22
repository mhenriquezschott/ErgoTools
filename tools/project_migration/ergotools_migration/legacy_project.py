"""Read-only version-eight reference projects; never run legacy migrations.

Developer tooling layer; no normal application module imports this file. External
conversion code remains separately removable. This file owns only the operations
described above; it never changes original project files.
"""

import sqlite3
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PureWindowsPath
from types import MappingProxyType, TracebackType

from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata

LegacyRow = Mapping[str, object]


@dataclass(frozen=True, slots=True)
class LegacyDescriptor:
    """Original XML metadata and portable companion paths, with explicit new ID.

    Attributes:
        metadata: Typed destination metadata carrying the explicit new project identity
            and original declared defaults.
        database_path: Resolved original companion database path, opened read-only.
        images_path: Resolved original image folder, or None when the descriptor names
            none.
        original_xml: Exact original descriptor bytes, read without rewriting.
    """

    metadata: ProjectMetadata
    database_path: Path
    images_path: Path | None
    original_xml: bytes


def _relative(root: Path, value: str) -> Path:
    """Resolve a companion path within the original descriptor directory.

    Args:
        root: Original descriptor directory used to contain every resolved relative
            companion path.
        value: Original relative companion path text; Windows separators are accepted.

    Returns:
        Resolved path contained within root; original Windows separators are accepted.

    Raises:
        ValueError: A path is absolute or resolves outside the descriptor directory.
    """
    path = Path(value.replace("\\", "/"))
    if path.is_absolute() or PureWindowsPath(value).is_absolute():
        raise ValueError("Legacy companion paths must be relative to the project.")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("Legacy companion path leaves the project directory.")
    return resolved


def read_legacy_descriptor(path: Path, project_id: str) -> LegacyDescriptor:
    """Read original XML without changing it or opening its database.

    Args:
        path: Original .ergprj descriptor, preferably an isolated project copy.
        project_id: Explicit destination identity; the XML has no stable ID.

    Returns:
        Typed metadata and companion paths, accepting Windows path separators.

    Raises:
        ValueError: Unsupported/ambiguous metadata or nonportable companion path.
        OSError: Descriptor cannot be read.
        ET.ParseError: Descriptor is not well-formed XML.
    """
    original_xml = path.read_bytes()
    root = ET.fromstring(original_xml)
    if root.tag != "ErgoProject":
        raise ValueError("Expected an ErgoProject XML descriptor.")
    fields: dict[str, str] = {}
    for child in root:
        if child.tag in fields or len(child):
            raise ValueError("Ambiguous legacy project metadata.")
        fields[child.tag] = child.text or ""
    created = None
    date, time = fields.get("Date", ""), fields.get("Time", "")
    if date or time:
        created = datetime.strptime(date + " " + time, "%Y-%m-%d %H:%M:%S")
    units = {"Metric": MeasurementSystem.METRIC, "Imperial": MeasurementSystem.IMPERIAL}
    languages = {"English": Language.ENGLISH, "Spanish": Language.SPANISH}
    try:
        metadata = ProjectMetadata(
            project_id,
            fields["Name"],
            units[fields.get("MeasurementSystem", "Metric")],
            fields.get("Description"),
            created,
            languages[fields.get("Language", "English")],
        )
        data = fields["DataPath"]
        name = fields["DatabaseName"]
        if not data or not name or "/" in name or "\\" in name:
            raise ValueError("Legacy database name/path is missing or invalid.")
    except KeyError as error:
        raise ValueError("Unsupported or missing legacy project metadata.") from error
    database = _relative(path.parent, data + "/" + name)
    images = fields.get("ImagesPath")
    return LegacyDescriptor(
        metadata,
        database,
        _relative(path.parent, images) if images else None,
        original_xml,
    )


@dataclass(frozen=True, slots=True)
class LegacyInventory:
    """Consistent source schema/counts; no migrations or row normalization.

    Attributes:
        schema_version: Checked original SQLite schema version; only reviewed version
            eight is supported.
        table_counts: Ordered original table names and row counts from the same read
            transaction.
        columns: Original table names and ordered column identities discovered during
            initialization.
    """

    schema_version: int
    table_counts: tuple[tuple[str, int], ...]
    columns: tuple[tuple[str, tuple[str, ...]], ...]


class LegacyProject:
    """Own one read-only snapshot of the reviewed reference version-eight schema.

    Use as a context manager. SQL reads see one transaction; no schema repairs,
    result recalculation, conversion or implicit source writes are permitted.
    Older versions need a separate reviewed mapping, rather than guessed fields.
    """

    def __init__(self, descriptor: LegacyDescriptor) -> None:
        """Open existing companions read-only and reject corrupt/unsupported data.

        Args:
            descriptor: Parsed original metadata and companion locations; the database
                is opened read-only.

        Returns:
            None. Own a new read-only source connection and checked transaction; close
            initialization failures.

        Raises:
            ValueError: Source schema is not version eight or integrity/references fail.
            sqlite3.Error: The existing source database cannot be opened read-only or
                queried.
        """
        self.descriptor = descriptor
        connection = sqlite3.connect(
            descriptor.database_path.as_uri() + "?mode=ro", uri=True
        )
        self._initialize(connection)

    def _initialize(self, connection: sqlite3.Connection) -> None:
        """Verify and own a read-only version-eight source transaction.

        Args:
            connection: Source connection whose ownership transfers to this reader;
                closed if initialization fails.

        Returns:
            None. Retain a verified read-only connection and inspected columns, or close
            the connection on failure.

        Raises:
            ValueError: Schema version, integrity or foreign references fail validation.
            sqlite3.Error: The connection cannot enter or inspect the read-only
                snapshot; it is closed on failure.
        """
        self._connection = connection
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA query_only=ON")
            connection.execute("BEGIN")
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version != 8:
                raise ValueError("Only reviewed legacy schema version 8 is supported.")
            if connection.execute("PRAGMA quick_check").fetchall()[0][0] != "ok":
                raise ValueError("Legacy database integrity check failed.")
            if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise ValueError("Legacy database contains orphaned references.")
            self._columns = {
                str(row[0]): tuple(
                    str(column[1])
                    for column in connection.execute(
                        'PRAGMA table_info("' + str(row[0]).replace('"', '""') + '")'
                    )
                )
                for row in connection.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                )
            }
        except BaseException:
            connection.close()
            raise

    @classmethod
    def from_snapshot(
        cls, metadata: ProjectMetadata, database: bytes
    ) -> "LegacyProject":
        """Own an in-memory archived read snapshot; never open companion paths.

        The descriptor's placeholder path is never used for I/O. WAL header bytes change
        only in the decoding copy, as in archive integrity validation.

        Args:
            metadata: Typed destination metadata associated with this archived source
                snapshot.
            database: Serialized original version-eight database bytes; only an
                in-memory decoding copy can change.

        Returns:
            Owned in-memory read-only snapshot; the caller must close it. Original bytes
            and companion paths remain untouched.

        Raises:
            ValueError: Archived source schema or integrity is unsupported.
            sqlite3.Error: Serialized bytes cannot be decoded or inspected; failure
                closes the private connection.
        """
        instance = cls.__new__(cls)
        instance.descriptor = LegacyDescriptor(metadata, Path("archived.db"), None, b"")
        connection = sqlite3.connect(":memory:")
        try:
            if database[18:20] == b"\x02\x02":
                database = database[:18] + b"\x01\x01" + database[20:]
            connection.deserialize(database)
        except BaseException:
            connection.close()
            raise
        instance._initialize(connection)
        return instance

    def rows(self, table: str, *, order: tuple[str, ...] = ()) -> tuple[LegacyRow, ...]:
        """Read immutable rows; identifiers must exist in the inspected schema.

        Args:
            table: Exact table name discovered in the checked source schema; never
                arbitrary SQL.
            order: Ordered allowed column names from that table; empty preserves the
                SQLite query order.

        Returns:
            Immutable row mappings in the requested ordering, possibly empty; all reads
            share the owned transaction.

        Raises:
            ValueError: Requested table/ordering columns are absent.
            sqlite3.Error: Snapshot is closed or the database cannot be read.
        """
        if table not in self._columns or any(
            column not in self._columns[table] for column in order
        ):
            raise ValueError("Unknown legacy table or ordering column.")
        quoted = '"' + table.replace('"', '""') + '"'
        ordering = (
            " ORDER BY " + ",".join('"' + c.replace('"', '""') + '"' for c in order)
            if order
            else ""
        )
        return tuple(
            MappingProxyType(dict(row))
            for row in self._connection.execute("SELECT * FROM " + quoted + ordering)
        )

    def inventory(self) -> LegacyInventory:
        """Count all tables within this same source snapshot without writes.

        Args:
            None.

        Returns:
            Schema version, table counts and exact column names observed in this same
            consistent transaction.

        Raises:
            sqlite3.Error: The owned snapshot is closed or cannot be queried.
        """
        counts = tuple(
            (
                table,
                int(
                    self._connection.execute(
                        'SELECT COUNT(*) FROM "' + table.replace('"', '""') + '"'
                    ).fetchone()[0]
                ),
            )
            for table in self._columns
        )
        return LegacyInventory(8, counts, tuple(self._columns.items()))

    def database_snapshot(self) -> bytes:
        """Serialize this read transaction, including its committed WAL contents.

        The immutable result retains every original table/column/value and schema
        object. It is an SQLite snapshot, not necessarily a byte-identical copy of the
        source file's physical layout. No checkpoint or source write occurs.

        Args:
            None.

        Returns:
            Serialized visible SQLite pages, including committed WAL contents, without
            checkpointing or writing original files.

        Raises:
            sqlite3.Error: The owned source connection cannot serialize its visible
                database.
        """
        return self._connection.serialize()

    def close(self) -> None:
        """Release the read snapshot; never commit or migrate source data.

        Args:
            None.

        Returns:
            None. Release the owned source connection; never commit or migrate the
            source.
        """
        self._connection.close()

    def __enter__(self) -> "LegacyProject":
        """Return this explicitly owned source snapshot.

        Args:
            None.

        Returns:
            This already-open source snapshot; no second connection or transaction is
            created.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close on success and failure without suppressing the caller's error.

        Args:
            exc_type: Exception type from the with body, or None on normal exit; never
                suppressed.
            exc_value: Exception from the with body, or None; cleanup does not replace
                it on normal close.
            traceback: With-body traceback, or None; retained by normal Python exception
                propagation.

        Returns:
            None. Close the owned connection on both normal and exceptional exit; do not
            suppress with-body errors.
        """
        self.close()

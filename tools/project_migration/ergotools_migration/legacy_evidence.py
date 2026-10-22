"""Original project evidence retained separately from editable migrated records.

External tools layer: historical format-12/13 archive fixture support only. Current
conversion and native application operation do not call this archive writer/reader;
current output projects contain no archive or duplicate result store.
"""

import hashlib
import sqlite3
import xml.etree.ElementTree as ET
from contextlib import closing
from dataclasses import dataclass

from ergotools.domain.plant_layout_image import PlantLayoutImage
from ergotools.infrastructure.lifft_store import StoreFormatError
from ergotools.infrastructure.plant_image_import import validate_plant_image

from .legacy_plot import LegacyPlotData
from .legacy_project import LegacyProject


@dataclass(frozen=True, slots=True)
class LegacyEvidence:
    """Exact XML/images and a consistent version-eight SQLite source snapshot.

    Original cached results, timestamps, selector indices, unused display fields and
    source schema remain recoverable. None of this archive is fresh scientific evidence
    or an editable replacement for the typed destination records.

    Historical archive-fixture support only; current native conversion never uses this
    record or stores an original database archive.

    Attributes:
        descriptor_xml: Original XML bytes retained only in a crafted earlier-format
            archive fixture.
        database: Serialized version-eight source bytes retained only in the historical
            fixture.
        images: Original basename/image pairs required to validate the historical
            archive fixture; not current native storage.
    """

    descriptor_xml: bytes
    database: bytes
    images: tuple[tuple[str, PlantLayoutImage], ...] = ()

    def __post_init__(self) -> None:
        """Freeze named images and reject malformed archives before publication.

        Args:
            None.

        Returns:
            None. Freeze the named image pairs and validate the historical archive
            fixture in memory.

        Raises:
            ValueError: Historical archive metadata, schema or image names are invalid.
            sqlite3.Error: The serialized fixture database is invalid.
            OSError: An encoded fixture image cannot be decoded.
            ET.ParseError: The fixture XML is malformed.
        """
        object.__setattr__(self, "images", tuple(tuple(item) for item in self.images))
        self.validate()

    def validate(self) -> None:
        """Decode the source in memory, never open its original paths or execute it.

        Args:
            None.

        Returns:
            None. Check XML, serialized schema/integrity/links and every named encoded
            image; original paths are never opened.

        Raises:
            ValueError: Evidence has invalid metadata, schema version or image names.
            sqlite3.Error: The serialized database is invalid.
            OSError: An image cannot be decoded.
            ET.ParseError: Original XML is malformed.
        """
        if not isinstance(self.descriptor_xml, bytes) or not isinstance(
            self.database, bytes
        ):
            raise ValueError("Legacy evidence requires immutable source bytes.")
        if ET.fromstring(self.descriptor_xml).tag != "ErgoProject":
            raise ValueError("Legacy evidence requires the original project XML.")
        expected_names: set[str] = set()
        with closing(sqlite3.connect(":memory:")) as connection:
            database = self.database
            # deserialize cannot open a WAL-mode header without sidecars. The
            # serialized read snapshot already contains its visible pages; only
            # this in-memory decoding copy uses rollback-journal header bytes.
            # Archived source bytes remain untouched.
            if (
                database.startswith(b"SQLite format 3\x00")
                and database[18:20] == b"\x02\x02"
            ):
                database = database[:18] + b"\x01\x01" + database[20:]
            connection.deserialize(database)
            connection.execute("PRAGMA query_only=ON")
            if connection.execute("PRAGMA user_version").fetchone() != (8,):
                raise ValueError(
                    "Legacy evidence requires source schema version eight."
                )
            if connection.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                raise ValueError("Legacy evidence database is corrupt.")
            if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise ValueError("Legacy evidence has orphaned source references.")
            if connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='Plant'"
            ).fetchone():
                for (image_name,) in connection.execute("SELECT image_name FROM Plant"):
                    if image_name is not None and image_name != "":
                        if not isinstance(image_name, str):
                            raise ValueError("Original plant image name is invalid.")
                        expected_names.add(image_name)
        names: set[str] = set()
        for name, image in self.images:
            if (
                not isinstance(name, str)
                or not name
                or name in (".", "..")
                or any(character in name for character in "/\\:")
                or name in names
            ):
                raise ValueError("Legacy evidence image name is invalid or duplicated.")
            names.add(name)
            validate_plant_image(image)
        if names != expected_names:
            raise ValueError(
                "Legacy evidence is missing or adds original plant images."
            )


def read_legacy_evidence(
    project: LegacyProject, plot: LegacyPlotData
) -> LegacyEvidence:
    """Capture already-read companion bytes and the same open source transaction.

    Args:
        project: Caller-owned open read-only version-eight snapshot; this operation does
            not close it.
        plot: Already read plant image payloads and map data from the same source
            snapshot.

    Returns:
        Validated earlier-format archive fixture built from original XML, visible SQLite
        pages and already-read named images.

    Raises:
        ValueError: One image name identifies inconsistent bytes, or archive validation
            fails.
        sqlite3.Error: The original snapshot cannot be serialized or validated.
        OSError: An encoded image fails validation.
        ET.ParseError: The original descriptor XML is malformed.
    """
    images: dict[str, PlantLayoutImage] = {}
    for item in plot.images:
        previous = images.setdefault(item.image_name, item.image)
        if previous != item.image:
            raise ValueError("One original image name has inconsistent source bytes.")
    return LegacyEvidence(
        project.descriptor.original_xml,
        project.database_snapshot(),
        tuple(images.items()),
    )


def create_evidence_schema(connection: sqlite3.Connection) -> None:
    """Create version-one source archives inside the caller's creation transaction.

    Args:
        connection: Caller-owned SQLite connection borrowed without close/commit.

    Returns:
        None. Create the historical fixture tables inside the caller's transaction;
        never commit it.

    Raises:
        RuntimeError: The caller has no active creation transaction.
        sqlite3.Error: Historical schema table creation fails; the owner must roll back.
    """
    if not connection.in_transaction:
        raise RuntimeError("Evidence schema creation requires an active transaction.")
    connection.execute(
        "CREATE TABLE legacy_source_evidence (singleton INTEGER PRIMARY KEY "
        "CHECK(singleton=1),"
        "version INTEGER NOT NULL,descriptor BLOB NOT NULL,"
        "database_snapshot BLOB NOT NULL,"
        "descriptor_sha256 TEXT NOT NULL,database_sha256 TEXT NOT NULL)"
    )
    connection.execute(
        "CREATE TABLE legacy_source_images (name TEXT PRIMARY KEY,"
        "position INTEGER NOT NULL UNIQUE,"
        "image BLOB NOT NULL,sha256 TEXT NOT NULL)"
    )


class LegacyEvidenceStore:
    """Borrow a project connection; immutable source evidence is initialization-only."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Retain the connection without I/O or source-path dependencies.

        Args:
            connection: Caller-owned SQLite connection borrowed without close/commit.

        Returns:
            None. Borrow the connection without opening, configuring, committing or
            closing it.
        """
        self._connection = connection

    def initialize_in_transaction(self, evidence: LegacyEvidence) -> None:
        """Insert once without overwriting; owner rolls back on any failure.

        Args:
            evidence: Validated original-format archive fixture; not a second result
                store for current projects.

        Returns:
            None. Insert immutable historical archive bytes/hashes into empty fixture
            tables; the owner commits or rolls back.

        Raises:
            RuntimeError: No active caller-owned transaction exists.
            ValueError: Fixture storage is not empty or archive validation fails.
            sqlite3.Error: Historical fixture insertion fails; the owner must roll back.
        """
        if not self._connection.in_transaction:
            raise RuntimeError(
                "Evidence initialization requires an active transaction."
            )
        evidence.validate()
        if (
            self._connection.execute("SELECT 1 FROM legacy_source_evidence").fetchone()
            or self._connection.execute("SELECT 1 FROM legacy_source_images").fetchone()
        ):
            raise ValueError("Legacy evidence initialization requires empty storage.")
        self._connection.execute(
            "INSERT INTO legacy_source_evidence VALUES (1,1,?,?,?,?)",
            (
                evidence.descriptor_xml,
                evidence.database,
                hashlib.sha256(evidence.descriptor_xml).hexdigest(),
                hashlib.sha256(evidence.database).hexdigest(),
            ),
        )
        self._connection.executemany(
            "INSERT INTO legacy_source_images VALUES (?,?,?,?)",
            [
                (name, position, image.data, hashlib.sha256(image.data).hexdigest())
                for position, (name, image) in enumerate(evidence.images)
            ],
        )

    def read(self) -> LegacyEvidence:
        """Validate hashes and source bytes without opening any original file path.

        Args:
            None.

        Returns:
            Validated historical archive fixture with verified hashes and contiguous
            image positions; no current native fallback is provided.

        Raises:
            StoreFormatError: Decoded fixture metadata, hashes, image order or archive
                validation fail.
            sqlite3.Error: The initial historical-table query fails outside the
                format-validation wrapper.
        """
        rows = self._connection.execute(
            "SELECT * FROM legacy_source_evidence"
        ).fetchall()
        try:
            if len(rows) != 1 or rows[0][:2] != (1, 1):
                raise ValueError("Unsupported legacy evidence metadata.")
            _, _, descriptor, database, xml_hash, db_hash = rows[0]
            if (
                hashlib.sha256(descriptor).hexdigest() != xml_hash
                or hashlib.sha256(database).hexdigest() != db_hash
            ):
                raise ValueError("Legacy source evidence hash does not match.")
            images: list[tuple[str, PlantLayoutImage]] = []
            for name, position, data, digest in self._connection.execute(
                "SELECT name,position,image,sha256 FROM legacy_source_images "
                "ORDER BY position"
            ):
                if (
                    position != len(images)
                    or hashlib.sha256(data).hexdigest() != digest
                ):
                    raise ValueError("Legacy source image evidence does not match.")
                images.append((name, PlantLayoutImage(data)))
            return LegacyEvidence(descriptor, database, tuple(images))
        except (ValueError, TypeError, OSError, sqlite3.Error, ET.ParseError) as error:
            raise StoreFormatError(
                "Invalid preserved legacy source evidence."
            ) from error

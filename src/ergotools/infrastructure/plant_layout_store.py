"""Project-owned map bytes with no sidecar paths or plant-name filenames.

Infrastructure layer. Adapt validated application/domain values to explicit storage or
interchange formats. Use parameterized SQLite or caller-selected file paths; no Qt UI,
scientific formula changes or automatic old-project conversion. Connection ownership and
transaction boundaries are specified by each operation; I/O failures propagate unless
wrapped as a format error.
"""

import sqlite3

from ergotools.domain.plant_layout_image import PlantLayoutImage
from ergotools.domain.work_hierarchy import WorkHierarchy
from ergotools.infrastructure.lifft_store import StoreFormatError
from ergotools.infrastructure.plant_image_import import validate_plant_image


def create_layout_schema(connection: sqlite3.Connection) -> None:
    """Create map storage inside the caller's explicit project write transaction.

    Args:
        connection: Borrowed project connection inside its caller-owned write
            transaction.

    Returns:
        None after creating the embedded-map table; caller commits/rolls back.

    Raises:
        sqlite3.DatabaseError: Schema creation fails or table already exists.
    """
    connection.execute(
        "CREATE TABLE plant_layout_images (plant TEXT PRIMARY KEY NOT NULL, "
        "image BLOB NOT NULL CHECK(length(image) > 0))"
    )


class PlantLayoutStore:
    """Borrow the project connection; caller owns transaction and plant membership."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Keep the owned-project connection without performing writes.

        Args:
            connection: Borrowed project connection; close and transaction ownership
                remain with the project.

        Returns:
            None; retain connection without reads/writes.
        """
        self._connection = connection

    def validate_hierarchy(self, hierarchy: WorkHierarchy) -> None:
        """Reject orphan maps instead of silently deleting them with their plant.

        Args:
            hierarchy: Proposed immutable hierarchy whose plants must retain every saved
                map owner.

        Returns:
            None when every saved map still has its exact plant.

        Raises:
            ValueError: A saved image references a missing plant.
            sqlite3.DatabaseError: Map-owner query fails.
        """
        rows = self._connection.execute("SELECT plant FROM plant_layout_images")
        if any(row[0] not in hierarchy.plants for row in rows):
            raise ValueError("A saved layout references a missing plant.")

    def validate_images(self) -> None:
        """Decode persisted maps on open/snapshot; damaged images reject the project.

        Args:
            None.

        Returns:
            None after decoding/validating every saved map without replacement.

        Raises:
            StoreFormatError: A saved map has invalid encoded image data.
            sqlite3.DatabaseError: Map queries fail.
        """
        for (plant,) in self._connection.execute(
            "SELECT plant FROM plant_layout_images"
        ):
            self.read(plant)

    def read(self, plant: str) -> PlantLayoutImage | None:
        """Return validated encoded bytes; only an absent record returns None.

        Args:
            plant: Exact plant identity used as a parameterized key.

        Returns:
            Validated encoded image and pixel metadata, or None only when the row is
            absent.

        Raises:
            StoreFormatError: Saved map bytes fail typed/image validation.
            sqlite3.DatabaseError: Map lookup fails.
        """
        row = self._connection.execute(
            "SELECT image FROM plant_layout_images WHERE plant = ?", (plant,)
        ).fetchone()
        if row is None:
            return None
        try:
            image = PlantLayoutImage(row[0])
            validate_plant_image(image)
        except (ValueError, TypeError, OSError) as error:
            raise StoreFormatError("Invalid saved plant layout image.") from error
        return image

    def write_in_transaction(self, plant: str, image: PlantLayoutImage) -> None:
        """Replace one plant's map transactionally, retaining original bytes.

        Args:
            plant: Exact saved plant identity already membership-validated by the owner.
            image: Already validated encoded image; original bytes remain unchanged.

        Returns:
            None after image upsert; caller owns commit and rollback.

        Raises:
            sqlite3.DatabaseError: Map upsert fails.
        """
        self._connection.execute(
            "INSERT INTO plant_layout_images VALUES (?, ?) "
            "ON CONFLICT(plant) DO UPDATE SET image = excluded.image",
            (plant, image.data),
        )

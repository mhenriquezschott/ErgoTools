"""Immutable encoded plant map, independent of paths, renderers and units.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlantLayoutImage:
    """Retain original encoded pixels; decoding belongs to the image adapter.

    Attributes:
        data: Nonempty immutable original encoded map bytes; one project can retain
            multiple plants' images.
    """

    data: bytes

    def __post_init__(self) -> None:
        """Reject absent, empty or mutable payloads before publishing an image.

        Args:
            None. Dataclass construction supplies the fields documented on
            PlantLayoutImage.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: Plant layout requires nonempty encoded image bytes.
        """
        if not isinstance(self.data, bytes) or not self.data:
            raise ValueError("Plant layout requires nonempty encoded image bytes.")

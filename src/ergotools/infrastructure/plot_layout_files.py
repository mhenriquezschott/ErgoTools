"""Read explicitly injected plant-image files without changing their contents.

This generic image-provider adapter is separate from native project storage, which
embeds map bytes. Callers supply resolved paths; no original-project schema,
companion-path inference or conversion logic exists here.

Infrastructure layer. Keep these representations and concrete I/O outside the
domain/application core. Ownership, validation and transaction effects are documented at
each boundary below; no GUI or scientific formula is implemented here.
"""

from collections.abc import Mapping
from pathlib import Path


class FilePlantLayouts:
    """Injected saved-image catalog, ready for a reviewed project/import adapter."""

    def __init__(self, locations: Mapping[str, Path]) -> None:
        """Copy explicit plant/path associations without inferring filenames.

        Args:
            locations: Explicit resolved plant-to-image-path associations; copied so
                later caller mutations cannot redirect reads.

        Returns:
            None. Snapshot the explicit lookup mapping without reading any image.
        """
        self._locations = dict(locations)

    def read(self, plant: str) -> bytes | None:
        """Return image bytes, or None for unrecorded/missing files as in PLOT.

        Permission, directory and other storage errors propagate. A metadata/import
        caller must supply resolved paths; this adapter never changes project files.

        Args:
            plant: Exact saved plant identity used only to look up the injected path
                mapping.

        Returns:
            Original encoded file bytes, or None for an unmapped/missing image; never
            invent a fallback image.

        Raises:
            OSError: A mapped image has a permission, directory or other storage
                failure; FileNotFoundError alone is treated as absence.
        """
        path = self._locations.get(plant)
        if path is None:
            return None
        try:
            return path.read_bytes()
        except FileNotFoundError:
            return None

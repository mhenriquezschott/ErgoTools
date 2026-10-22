"""Read-only PLOT scope/layout loading through an injected image source.

Application layer. Compose immutable domain values through injected read/write ports.
This module owns no widgets, SQL connection, global clock or renderer; persistence and
modal consent belong to its caller.
"""

from dataclasses import dataclass
from typing import Protocol

from ergotools.domain.plant_layout_image import PlantLayoutImage
from ergotools.domain.plot_scope import PlotScope
from ergotools.domain.work_hierarchy import WorkHierarchy


class PlantLayoutReader(Protocol):
    """Provide saved image bytes for an exact plant identity; absent images are None."""

    def read(self, plant: str) -> bytes | None:
        """Read without changing metadata/images; propagate actual storage failures.

        Storage errors propagate to the caller; no metadata or image write occurs.

        Args:
            plant: Exact saved plant identity; never a translated caption.

        Returns:
            Encoded image bytes, or None for a plant with no saved map.
        """
        ...


@dataclass(frozen=True, slots=True)
class LoadedPlantLayout:
    """Validated map selection with decoding delegated to presentation.

    Attributes:
        scope: Exact validated PLOT plant/section/line scope.
        image: Encoded image bytes, or None when no plant map is saved.
    """

    scope: PlotScope
    image: bytes | None

    def __post_init__(self) -> None:
        """Reject empty or untyped image payloads rather than treat them as absence.

        Args:
            None.

        Returns:
            None; validate the selection and optional payload.

        Raises:
            ValueError: Scope is untyped or the image is empty/nonbytes instead of
                absent.
        """
        if not isinstance(self.scope, PlotScope):
            raise ValueError("Layout requires a typed PLOT scope.")
        if self.image is not None and (
            not isinstance(self.image, bytes) or not self.image
        ):
            raise ValueError("Layout image must be nonempty encoded bytes or absent.")


def load_plant_layout(
    hierarchy: WorkHierarchy, scope: PlotScope, reader: PlantLayoutReader
) -> LoadedPlantLayout:
    """Validate the exact scope before read-only I/O; never change assessment state.

    Reader storage errors propagate. No editor or project state changes.

    Args:
        hierarchy: Saved hierarchy against which every selected scope component is
            validated.
        scope: Exact plant and optional section/line selection.
        reader: Borrowed read-only encoded-image source.

    Returns:
        Validated scope and its optional encoded image, ready for presentation decoding.

    Raises:
        ValueError: Scope membership or returned image payload is invalid.
    """
    scope.validate(hierarchy)
    return LoadedPlantLayout(scope, reader.read(scope.plant))


class PlantLayoutWriter(Protocol):
    """Persist an explicitly accepted map for an exact saved plant identity."""

    def save_plant_image(self, plant: str, image: PlantLayoutImage) -> None:
        """Commit or raise; never change assessment source/session state.

        The concrete adapter validates membership and owns atomic persistence. No
        assessment source or session is changed.

        Args:
            plant: Exact existing plant identity whose embedded map is replaced.
            image: Validated encoded bytes, media type and original pixel dimensions.

        Returns:
            None after commit; failure must preserve the prior saved image.
        """
        ...


def save_plant_layout(
    hierarchy: WorkHierarchy,
    scope: PlotScope,
    image: PlantLayoutImage,
    writer: PlantLayoutWriter,
) -> None:
    """Save explicitly after preview; scope validation precedes project writes.

    Writer storage errors propagate; no assessment source or session change occurs.

    Args:
        hierarchy: Saved hierarchy used to validate the full selection before writes.
        scope: Exact accepted plant and optional hierarchy filters.
        image: Validated encoded plant map retaining its original pixel dimensions.
        writer: Borrowed atomic project-image persistence port.

    Returns:
        None after the accepted map is saved for scope.plant.

    Raises:
        ValueError: Scope membership or adapter image/plant validation fails.
    """
    scope.validate(hierarchy)
    writer.save_plant_image(scope.plant, image)

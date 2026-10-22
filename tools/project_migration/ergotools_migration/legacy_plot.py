"""Original plant images and version-eight map geometry without display-unit changes.

Developer tooling layer; no normal application module imports this file. External
conversion code remains separately removable. This file owns only the operations
described above; it never changes original project files.
"""

from dataclasses import dataclass

from ergotools.domain.plant_layout_image import PlantLayoutImage
from ergotools.domain.plot_positions import (
    PlotPoint,
    PlotPositions,
    StationPosition,
    StationPositionSource,
    WorkerAssignmentMarker,
    WorkerPositionSource,
)
from ergotools.domain.work_catalog import StationKey
from ergotools.infrastructure.plant_image_import import validate_plant_image

from .legacy_catalogs import LegacyCatalogs
from .legacy_project import LegacyProject, LegacyRow
from .legacy_values import (
    legacy_flag,
    legacy_integer,
    legacy_keys,
    legacy_number,
    legacy_text,
    optional_text,
)


@dataclass(frozen=True, slots=True)
class LegacyPlantImage:
    """Exact original encoded image, without recompression, crop or DPI conversion.

    Attributes:
        plant: Exact owning plant identity, independent of its image filename.
        image_name: Original portable companion basename used to read the map bytes.
        image: Original immutable encoded image bytes; no recompression or DPI change.
    """

    plant: str
    image_name: str
    image: PlantLayoutImage


@dataclass(frozen=True, slots=True)
class LegacyPlotData:
    """Typed current map plus raw original plant/assessment display metadata.

    Attributes:
        positions: Typed original-pixel station anchors and assignment-owned marker
            geometry.
        images: Every named plant image with exact owning plant and original encoded
            bytes.
        original_plants: Read-only original Plant rows, including display transforms not
            inferred as station geometry.
        assessment_markers: Original assessment-owned marker rows, retained separately
            from assignment-owned positions.
    """

    positions: PlotPositions
    images: tuple[LegacyPlantImage, ...]
    original_plants: tuple[LegacyRow, ...]
    assessment_markers: tuple[LegacyRow, ...]


def _number(value: object) -> float:
    """Require finite original-image geometry without changing its units.

    Args:
        value: Original SQLite storage value; primitive-specific validation below does
            not infer missing data.

    Returns:
        Finite geometry float in the original stored pixel/scale units; missing values
        fail.

    Raises:
        ValueError: The required geometry value is absent, nonnumeric or nonfinite.
    """
    number = legacy_number(value)
    if number is None:
        raise ValueError("Required legacy map geometry is missing.")
    return number


def read_legacy_plot(
    project: LegacyProject, catalogs: LegacyCatalogs
) -> LegacyPlotData:
    """Read unscaled image-pixel geometry and original encoded companion images.

    Source plant_layout.py uses ImagesPath/image_name; stale image_path does not
    override it. A named missing/corrupt companion fails, rather than silently dropping
    a map. No measurement-unit projection or inferred station positions. Raw Plant
    transforms and assessment markers remain available for conversion; they are not
    silently reinterpreted as assignment-owned marker geometry.

    Args:
        project: Caller-owned open read-only version-eight snapshot; this operation does
            not close it.
        catalogs: Validated source hierarchy/jobs/risks preserving exact original
            historical identities.

    Returns:
        Validated typed original-pixel positions, all named plant image bytes and raw
        original display metadata.

    Raises:
        ValueError: Invalid geometry, links, image data or nonportable image name.
        OSError: A named companion image cannot be read.
        KeyError: Required schema fields are absent.
    """
    positions = PlotPositions(
        catalogs.jobs.project_id,
        tuple(
            StationPosition(
                StationKey(
                    *legacy_keys(
                        row, "plant_name", "section_name", "line_name", "station_id"
                    )
                ),
                PlotPoint(_number(row["x"]), _number(row["y"])),
                StationPositionSource(legacy_text(row["position_source"])),
            )
            for row in project.rows(
                "PlotStationPosition",
                order=("plant_name", "section_name", "line_name", "station_id"),
            )
        ),
        tuple(
            WorkerAssignmentMarker(
                legacy_integer(row["worker_assignment_id"]),
                None
                if row["x"] is None and row["y"] is None
                else PlotPoint(_number(row["x"]), _number(row["y"])),
                _number(row["size"]),
                _number(row["scale"]),
                _number(row["line_thickness"]),
                legacy_flag(row["locked"]),
                legacy_flag(row["visible"]),
                legacy_flag(row["enabled"]),
                WorkerPositionSource(legacy_text(row["position_source"])),
            )
            for row in project.rows(
                "PlotWorkerAssignmentMarker", order=("worker_assignment_id",)
            )
        ),
    )
    positions.validate(catalogs.hierarchy, catalogs.jobs)
    plants = project.rows("Plant", order=("name",))
    images = []
    for row in plants:
        name = optional_text(row["image_name"])
        if not name:
            continue
        folder = project.descriptor.images_path
        if (
            folder is None
            or name in (".", "..")
            or any(c in name for c in ("/", "\\", ":"))
        ):
            raise ValueError("Plant image requires a portable name and ImagesPath.")
        image = PlantLayoutImage((folder / name).read_bytes())
        validate_plant_image(image)
        images.append(LegacyPlantImage(legacy_text(row["name"]), name, image))
    markers = project.rows("PlotAssessmentMarker", order=("individual_assessment_id",))
    ids = {legacy_integer(row["id"]) for row in project.rows("IndividualAssessment")}
    if any(
        legacy_integer(row["individual_assessment_id"]) not in ids for row in markers
    ):
        raise ValueError("Assessment map marker has no original owner.")
    return LegacyPlotData(positions, tuple(images), plants, markers)

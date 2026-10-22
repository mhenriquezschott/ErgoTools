"""PNG/JPEG import using the approved desktop image dependency.

Infrastructure layer. Keep these representations and concrete I/O outside the
domain/application core. Ownership, validation and transaction effects are documented at
each boundary below; no GUI or scientific formula is implemented here.
"""

from io import BytesIO
from pathlib import Path

from ergotools.domain.plant_layout_image import PlantLayoutImage


def validate_plant_image(image: PlantLayoutImage) -> None:
    """Decode all pixels; reject unsupported or corrupt images without rewriting.

    Pillow is imported only for the PLOT image feature. Older projects and portable
    domain/application APIs do not require it. Decoder/storage errors propagate.

    Args:
        image: Immutable original encoded plant-map bytes; decoding happens in memory
            without rewriting them.

    Returns:
        None after decoding all supported PNG/JPEG pixels; original encoded bytes remain
        unchanged.

    Raises:
        ValueError: Decoded format is not PNG or JPEG.
        OSError: Encoded image pixels cannot be decoded; decoder-specific resource-limit
            errors also propagate.
    """
    from PIL import Image

    with Image.open(BytesIO(image.data)) as decoded:
        if decoded.format not in ("PNG", "JPEG"):
            raise ValueError("Plant layouts support PNG and JPEG images only.")
        decoded.load()


def import_plant_image(path: Path) -> PlantLayoutImage:
    """Read and validate original PNG/JPG bytes without touching source or project.

    Args:
        path: Caller-selected original PNG/JPG file; native project storage is a
            separate operation.

    Returns:
        Validated original encoded map bytes; this operation neither copies into a
        project nor changes the source file.

    Raises:
        ValueError: Extension is not .png/.jpg, or image format validation fails.
        OSError: The original file cannot be read or its encoded pixels cannot be
            decoded.
    """
    if path.suffix.lower() not in (".png", ".jpg"):
        raise ValueError("Select a PNG or JPG plant image.")
    image = PlantLayoutImage(path.read_bytes())
    validate_plant_image(image)
    return image

"""Read package-owned visual assets without depending on a working directory.

Infrastructure layer. Keep these representations and concrete I/O outside the
domain/application core. Ownership, validation and transaction effects are documented at
each boundary below; no GUI or scientific formula is implemented here.
"""

from importlib.resources import files
from pathlib import PurePosixPath


def read_asset(asset_name: str) -> bytes:
    """Read an asset using its manifest-relative name, such as icons/save.png.

    Args:
        asset_name: A forward-slash relative path under the packaged resources.

    Returns:
        The original binary asset content.

    Raises:
        ValueError: If the name attempts to escape the packaged resource tree.
        FileNotFoundError: If the requested resource does not exist.
    """
    path = PurePosixPath(asset_name)
    if (
        not asset_name
        or not path.parts
        or path.is_absolute()
        or ".." in path.parts
        or "\\" in asset_name
        or ":" in asset_name
        or path.parts[0] not in {"icons", "models", "images", "documents"}
    ):
        raise ValueError("Expected a relative packaged asset path.")
    return files("ergotools.resources").joinpath(*path.parts).read_bytes()

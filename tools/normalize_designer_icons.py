"""Normalize supplied designer PNGs without redrawing artwork or editing originals.

Developer asset tool. Remove the white matte with alpha/color decontamination, trim
visible bounds, fit/center on the established 96px canvas, and emit ordinary/light
variants. Manifest provenance keeps source/processed hashes and crop geometry.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


def normalized_icon(
    source: Image.Image,
) -> tuple[Image.Image, tuple[int, int, int, int]]:
    """Recover white-matted linework and center it at consistent visual proportions.

    Args:
        source: Original designer image, never modified in place.

    Returns:
        Transparent 96x96 RGBA image, at most 80px artwork, and crop bounds.

    Raises:
        ValueError: No visible nonwhite artwork is present.
    """
    rgba = np.array(source.convert("RGBA"), dtype=np.float32)
    rgb = rgba[:, :, :3]
    alpha = np.minimum(1.0, (255.0 - rgb.min(axis=2)) / 240.0)
    alpha[alpha < 0.012] = 0
    foreground = np.clip(
        (rgb - 255.0 * (1 - alpha[:, :, None])) / np.maximum(alpha[:, :, None], 0.001),
        0,
        255,
    )
    rgba[:, :, :3] = foreground
    rgba[:, :, 3] *= alpha
    transparent = Image.fromarray(np.rint(rgba).astype(np.uint8))
    bounds = transparent.getbbox()
    if bounds is None:
        raise ValueError("Designer source contains no visible artwork.")
    cropped = transparent.crop(bounds)
    cropped.thumbnail((80, 80), Image.Resampling.LANCZOS)
    # Very faint fringe pixels may disappear during reduction. Center the actual
    # final alpha bounds, rather than the now-invisible original crop padding.
    reduced_bounds = cropped.getbbox()
    if reduced_bounds is None:
        raise ValueError("Designer artwork disappears at the target icon size.")
    cropped = cropped.crop(reduced_bounds)
    result = Image.new("RGBA", (96, 96))
    result.alpha_composite(
        cropped, ((96 - cropped.width) // 2, (96 - cropped.height) // 2)
    )
    return result, bounds


def main(argv: list[str] | None = None) -> int:
    """Build ordinary/light assets and replace their derived manifest records.

    Args:
        argv: Explicit optional arguments; None reads the command line.

    Returns:
        Zero after processing and hashing all designer PNGs. Originals remain exact.

    Raises:
        OSError: Designer files, destination or manifest cannot be read/written.
        ValueError: An input is blank or a filename is not snake_case.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args(argv)
    args.destination.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(args.manifest.read_text())
    records = []
    for path in sorted(args.source.glob("*.png")):
        if not all(c.islower() or c == "_" for c in path.stem):
            raise ValueError("Designer filenames must be snake_case.")
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        with Image.open(path) as image:
            source_size = image.size
            icon, bounds = normalized_icon(image)
        for light in (False, True):
            name = path.stem + ("_light" if light else "") + ".png"
            output = args.destination / name
            painted = icon.copy()
            if light:
                painted.paste((255, 255, 255), (0, 0, 96, 96))
                painted.putalpha(icon.getchannel("A"))
            painted.save(output, optimize=True)
            records.append(
                {
                    "path": "icons/" + name,
                    "source_sha256": before,
                    "source_name": path.name,
                    "source_size": source_size,
                    "crop": bounds,
                    "operation": (
                        "white-matte removal, decontamination, trim, "
                        "centered80px artwork on96px transparent canvas"
                    )
                    + ("; white glyph" if light else ""),
                    "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                }
            )
        assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    paths = {r["path"] for r in records}
    manifest["derived_assets"] = [
        r for r in manifest.get("derived_assets", []) if r["path"] not in paths
    ] + records
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Normalized {len(records) // 2} designer icons and light variants.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

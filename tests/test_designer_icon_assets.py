"""Designer artwork normalization, transparency and packaged semantic identities."""

import hashlib
import json
from importlib.resources import files
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from PyQt5.QtWidgets import QApplication

from ergotools.bootstrap import create_window, load_icons
from ergotools.infrastructure.resources import read_asset
from tools.normalize_designer_icons import normalized_icon

# Native QIcon creation needs one retained application, without opening windows.
_APP = QApplication.instance() or QApplication([])
# Stable semantic IDs, independent of local designer source files.
DESIGNER_NAMES = (
    "include_rows",
    "skip_rows",
    "include_all_rows",
    "task_inputs",
    "direct_result",
    "clear_assignments",
    "discard_preview",
    "clear_timing",
    "edit_timing",
    "about",
    "add_break",
    "add_work_block",
    "apply_timing",
    "clear_result_link",
    "column_mapping",
    "duplicate_rotation",
    "equal_breaks",
    "equal_work_blocks",
    "excluded_jobs",
    "fixed_job",
    "following_rotation_result",
    "generate_proposal",
    "keep_optimization_result",
    "no_adjacent_high",
    "previous_rotation_result",
    "project_backup",
    "project_properties",
    "remove_break",
    "remove_empty_rows",
    "remove_work_block",
    "replace_baseline",
    "rework_rotation",
    "save_as",
    "select_cell_range",
    "task_columns",
    "task_names",
    "unequal_breaks",
    "unequal_work_blocks",
    "validate_import",
    "worker_restrictions",
    "worksheet",
)


@pytest.mark.parametrize("name", DESIGNER_NAMES)
def test_designer_icons_are_centered_transparent_and_manifest_verified(
    name: str,
) -> None:
    """Each shipped semantic glyph has a clean canvas and an exact light silhouette.

    Args:
        name: Every supplied designer semantic identity.

    Returns:
        None; package loading needs no designer directory and preserves source records.
    """
    manifest = json.loads(
        files("ergotools.resources").joinpath("manifest.json").read_text()
    )
    entries = {a["path"]: a for a in (*manifest["assets"], *manifest["derived_assets"])}
    icons = load_icons()
    pictures = []
    for variant in (name, name + "_light"):
        data = read_asset("icons/" + variant + ".png")
        assert (
            hashlib.sha256(data).hexdigest()
            == entries["icons/" + variant + ".png"]["sha256"]
        )
        picture = Image.open(BytesIO(data)).convert("RGBA")
        assert picture.size == (96, 96)
        box = picture.getbbox()
        assert box is not None
        left, top, right, bottom = box
        assert abs(left - (96 - right)) <= 1 and abs(top - (96 - bottom)) <= 1
        assert left >= 5 and top >= 5 and right <= 91 and bottom <= 91
        assert picture.getpixel((0, 0))[3] == 0
        assert not icons[variant].isNull()
        pictures.append(picture)
    assert (
        pictures[0].getchannel("A").tobytes() == pictures[1].getchannel("A").tobytes()
    )
    assert all(
        pixel[:3] == (255, 255, 255) for pixel in pictures[1].getdata() if pixel[3]
    )


def test_normalizer_rejects_white_sources_and_keeps_input_image() -> None:
    """Normalization rejects empty artwork and never edits the borrowed designer image.

    Args:
        None.

    Returns:
        None; colored input pixels retain their intended foreground after matte removal.
    """
    white = Image.new("RGB", (20, 20), "white")
    with pytest.raises(ValueError):
        normalized_icon(white)
    white.putpixel((8, 10), (11, 50, 108))
    before = white.tobytes()
    result, bounds = normalized_icon(white)
    assert white.tobytes() == before and bounds == (8, 10, 9, 11)
    assert result.size == (96, 96) and result.getbbox() == (47, 47, 48, 48)


def test_composed_main_menu_keeps_dedicated_action_icons(tmp_path: Path) -> None:
    """Integrated composition never replaces dedicated menu glyphs with generic icons.

    Args:
        tmp_path: Private preferences folder; no project is opened.

    Returns:
        None; icon identity remains exact after ordinary translation/enable refresh.
    """
    window = create_window(
        tmp_path / "icons.json", original_controls=True, original_navigation=True
    )
    try:
        menu = window._assessment_menu
        menu.translate(window.language)
        menu.sync()
        for action, name in (
            (menu.properties, "project_properties"),
            (menu.about, "about"),
            (menu.save_as, "save_as"),
            (menu.backup, "project_backup"),
            (menu.task_names, "task_names"),
        ):
            assert action.icon().cacheKey() == window.icons[name].cacheKey()
    finally:
        window.close()
        window.deleteLater()
        _APP.processEvents()

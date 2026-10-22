"""PLOT image preview/save, atomic upgrades and complete-project copy regressions.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PyQt5.QtGui import QColor, QImage
from PyQt5.QtWidgets import QApplication

from ergotools.application.plot_layout import (
    LoadedPlantLayout,
    load_plant_layout,
    save_plant_layout,
)
from ergotools.domain.plant_layout_image import PlantLayoutImage
from ergotools.domain.plot_scope import PlotScope
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.lifft_store import StoreFormatError
from ergotools.infrastructure.plant_image_import import import_plant_image
from ergotools.infrastructure.plant_layout_store import PlantLayoutStore
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.plot_layout_canvas import PlotLayoutCanvas
from tests.test_history_persistence import HIERARCHY, META, SOURCE
from tests.test_saved_tool_data import window as window

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


def image_file(path: Path, color: str = "white") -> Path:
    """Make an actual PNG/JPG fixture with known original pixel dimensions.

    Args:
        path: Disposable test file path; the caller controls creation and cleanup.
        color: Expected source palette color or test image fill color; not recomputed
            from screenshots.

    Returns:
        Created test PNG/JPEG path with known original dimensions and requested fill
        color.
    """
    image = QImage(640, 360, QImage.Format_RGB32)
    image.fill(QColor(color))
    assert image.save(str(path), "JPG" if path.suffix == ".jpg" else "PNG")
    return path


def create_project(path: Path, version: int) -> AssessmentProjectFile:
    """Create a disposable full project with the existing literal hierarchy.

    Args:
        path: Disposable test file path; the caller controls creation and cleanup.
        version: Explicit historical/native test-format version used to exercise
            acceptance or rejection boundaries.

    Returns:
        New owned disposable full native project at the requested format version; caller
        closes the returned handle.
    """
    project = AssessmentProjectFile.create_with_document(
        path, META, "a", SOURCE, format_version=version
    )
    project.save_hierarchy(replace(HIERARCHY, plants=("P", "Empty", "../All")))
    return project


@pytest.mark.parametrize("version", [7, 8, 9])
@pytest.mark.parametrize("suffix", [".png", ".jpg"])
def test_preview_save_reopen_copy_and_backup(
    tmp_path: Path, version: int, suffix: str
) -> None:
    """Preview is read-only; save/copy/reopen preserve pixels, metadata and sources.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        version: Explicit historical/native test-format version used to exercise
            acceptance or rejection boundaries.
        suffix: Explicit filename/format suffix used by the parametrized export/path
            case.

    Returns:
        None.
    """
    path = tmp_path / "project.ergprj"
    original = image_file(tmp_path / f"outside{suffix}")
    image = import_plant_image(original)
    source_bytes = original.read_bytes()
    scope = PlotScope((("P",),), "Day")
    with create_project(path, version) as project:
        before = path.read_bytes()
        hierarchy = project.load_hierarchy()
        assert project.load_plant_image("P") is None
        assert path.read_bytes() == before and project.format_version == version
        canvas = PlotLayoutCanvas()

        canvas.set_layout(LoadedPlantLayout(scope, image.data))
        assert project.load_plant_image("P") is None and path.read_bytes() == before
        save_plant_layout(hierarchy, scope, image, project)
        assert project.format_version == 9 and project.metadata == META
        assert project.load_plant_image("P") == image
        assert project.load_plant_image("Empty") is None
        save_plant_layout(hierarchy, PlotScope((("../All",),)), image, project)
        assert project.load_plant_image("../All") == image
        assert not (tmp_path / "All_layout.png").exists()
        assert original.read_bytes() == source_bytes
        original.unlink()
        canvas.set_layout(load_plant_layout(hierarchy, scope, project))
        assert canvas.scene().sceneRect().width() == 640
        assert canvas.scene().sceneRect().height() == 360
        saved = path.read_bytes()
        with project.snapshot(str(tmp_path / "backup.ergprj"), None, None) as backup:
            assert backup.format_version == 9 and backup.metadata == META
            assert backup.load_plant_image("P") == image
        copied_metadata = replace(
            META, title="Copy", description="Literal <b>description</b>"
        )
        with project.snapshot_with_metadata(
            str(tmp_path / "copy.ergprj"), None, None, copied_metadata
        ) as copy:
            assert copy.format_version == 9 and copy.metadata == copied_metadata
            assert copy.load_plant_image("P") == image
            assert copy.load(copy.list_assessments()[0].document) == SOURCE
        assert project.metadata == META and path.read_bytes() == saved
        canvas.close()
    with AssessmentProjectFile.open(path) as reopened:
        assert reopened.format_version == 9 and reopened.load_plant_image("P") == image
        assert reopened.load(reopened.list_assessments()[0].document) == SOURCE


@pytest.mark.parametrize("version", [7, 8, 9])
def test_sql_failure_rolls_back_upgrade_and_replacement(
    tmp_path: Path, version: int
) -> None:
    """Failure after INSERT preserves schema/version/old image and allows retry.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        version: Explicit historical/native test-format version used to exercise
            acceptance or rejection boundaries.

    Returns:
        None.
    """
    path = tmp_path / "project.ergprj"
    first = import_plant_image(image_file(tmp_path / "first.png"))
    second = import_plant_image(image_file(tmp_path / "second.jpg", "blue"))
    with create_project(path, version) as project:
        if version == 9:
            project.save_plant_image("P", first)
        before = path.read_bytes()
        write = PlantLayoutStore.write_in_transaction

        def fail_after_write(
            store: PlantLayoutStore, plant: str, image: PlantLayoutImage
        ) -> None:
            """Perform the actual embedded-image insertion.

            Perform the actual embedded-image insertion and then raise a SQLite failure
            to verify transaction/schema rollback.

            Args:
                store: Injected test-owned storage adapter receiving the controlled
                    write/read callback.
                plant: Exact synthetic plant identity whose embedded image is
                    written/read.
                image: Validated test image bytes/metadata in original pixel dimensions.

            Returns:
                None.

            Raises:
                sqlite3.OperationalError: The deliberately injected SQLite
                    write/metadata failure is reached.
            """
            write(store, plant, image)
            raise sqlite3.OperationalError("injected after image insertion")

        with (
            patch.object(PlantLayoutStore, "write_in_transaction", fail_after_write),
            pytest.raises(sqlite3.OperationalError),
        ):
            project.save_plant_image("P", second)
        assert project.format_version == version and path.read_bytes() == before
        assert project.load_plant_image("P") == (first if version == 9 else None)
        with closing(sqlite3.connect(path)) as connection:
            assert connection.execute(
                "SELECT version FROM project_metadata"
            ).fetchone() == (version,)
            if version < 9:
                assert not connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE name = 'plant_layout_images'"
                ).fetchone()
        project.save_plant_image("P", second)
        assert project.format_version == 9 and project.load_plant_image("P") == second


def test_import_and_save_errors_preserve_project(tmp_path: Path) -> None:
    """Invalid/unsupported/missing inputs and unknown plants never upgrade/write.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    for data in (b"", bytearray(b"mutable"), None):
        with pytest.raises(ValueError):
            PlantLayoutImage(data)
    with pytest.raises(FileNotFoundError):
        import_plant_image(tmp_path / "missing.png")
    with pytest.raises(IsADirectoryError):
        folder = tmp_path / "directory.png"
        folder.mkdir()
        import_plant_image(folder)
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image")
    with pytest.raises(OSError):
        import_plant_image(bad)
    with pytest.raises(ValueError):
        import_plant_image(tmp_path / "unsupported.gif")
    from PIL import Image

    gif = tmp_path / "disguised.png"
    with Image.new("RGB", (10, 10)) as source:
        source.save(gif, format="GIF")
    with pytest.raises(ValueError):
        import_plant_image(gif)
    image = import_plant_image(image_file(tmp_path / "valid.png"))
    path = tmp_path / "project.ergprj"
    with create_project(path, 8) as project:
        before = path.read_bytes()
        with pytest.raises(ValueError):
            project.save_plant_image("Missing", image)
        with pytest.raises(OSError):
            project.save_plant_image("P", PlantLayoutImage(b"bad"))
        assert path.read_bytes() == before and project.format_version == 8
        writer = Mock()
        with pytest.raises(ValueError):
            save_plant_layout(
                project.load_hierarchy(), PlotScope((("Missing",),)), image, writer
            )
        writer.save_plant_image.assert_not_called()
    with pytest.raises(RuntimeError):
        project.save_plant_image("P", image)
    with pytest.raises(RuntimeError):
        project.load_plant_image("P")
    partial = tmp_path / "partial.ergprj"
    with AssessmentProjectFile.create(partial, META) as project:
        before = partial.read_bytes()
        with pytest.raises(StoreFormatError):
            project.save_plant_image("P", image)
        assert partial.read_bytes() == before and project.format_version == 2


def test_saved_layout_protects_plant_and_corruption_rejects_open(
    tmp_path: Path,
) -> None:
    """Plant removal cannot orphan maps; corrupt encoded bytes reject reopened files.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "project.ergprj"
    image = import_plant_image(image_file(tmp_path / "valid.png"))
    with create_project(path, 8) as project:
        project.save_plant_image("Empty", image)
        before = path.read_bytes()
        hierarchy = project.load_hierarchy()
        replacement = replace(hierarchy, plants=("P", "../All"))
        with pytest.raises(ValueError, match="layout"):
            project.save_hierarchy(replacement)
        with pytest.raises(ValueError, match="layout"):
            project.replace_hierarchy(hierarchy, replacement)
        assert project.load_hierarchy() == hierarchy and path.read_bytes() == before
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("UPDATE plant_layout_images SET image = ?", (b"broken",))
    with pytest.raises(StoreFormatError, match="image"):
        AssessmentProjectFile.open(path)


@pytest.mark.parametrize("tab", [0, 1, 2])
def test_map_preview_save_preserves_pending_assessment(
    window: LifftWindow, tmp_path: Path, tab: int
) -> None:
    """The actual project map workflow leaves LiFFT/DUET/ST pending edits alone.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        tab: Zero-based integrated tool-tab position used by the actual Qt interaction.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(tab)
    panel = window.task_panel if tab == 0 else window.secondary_panel()
    field = panel.inputs[0][2 if tab == 0 else -1]
    field.setText("bad")
    field.textEdited.emit("bad")
    workspace = window.presenter.workspace
    active, state = workspace.active, workspace.active.state
    settings = window._settings_store.load()
    project = workspace._project
    hierarchy = project.load_hierarchy()
    image = import_plant_image(image_file(tmp_path / "map.png"))
    scope = PlotScope(((hierarchy.plants[0],),))

    canvas = PlotLayoutCanvas()
    canvas.set_layout(LoadedPlantLayout(scope, image.data))
    save_plant_layout(hierarchy, scope, image, project)
    canvas.set_layout(load_plant_layout(hierarchy, scope, project))
    assert (
        field.text() == "bad" and workspace.active is active and active.state is state
    )
    assert window._settings_store.load() == settings
    assert window.main_navigation.toolbar_actions["plot"].isEnabled()
    canvas.close()

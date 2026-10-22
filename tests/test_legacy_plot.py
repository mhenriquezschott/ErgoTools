"""Original image precedence, raw pixels and exact assignment-owned map geometry.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
from contextlib import closing
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from ergotools.domain.plot_positions import WorkerPositionSource
from tests.test_legacy_catalogs import legacy_catalog as legacy_catalog
from tools.project_migration.ergotools_migration.legacy_catalogs import (
    read_legacy_catalogs,
)
from tools.project_migration.ergotools_migration.legacy_plot import read_legacy_plot
from tools.project_migration.ergotools_migration.legacy_project import (
    LegacyProject,
    read_legacy_descriptor,
)


@pytest.fixture
def mapped(legacy_catalog: Path) -> Path:
    """Use exact source table shapes, hidden/unplaced and selected positioned owners.

    Args:
        legacy_catalog: Disposable original-shape catalog fixture used only by the
            external converter tests.

    Returns:
        Disposable original descriptor path with source-shaped plant image and marker
        tables.
    """
    legacy_catalog.write_text(
        legacy_catalog.read_text().replace(
            "</ErgoProject>", "<ImagesPath>images</ImagesPath></ErgoProject>"
        )
    )
    folder = legacy_catalog.parent / "images"
    folder.mkdir()
    buffer = BytesIO()
    Image.new("RGB", (20, 12), "#087e91").save(buffer, format="PNG")
    (folder / "original.png").write_bytes(buffer.getvalue())
    descriptor = read_legacy_descriptor(legacy_catalog, "p")
    with closing(sqlite3.connect(descriptor.database_path)) as connection, connection:
        connection.executescript(
            "UPDATE Plant SET image_name='original.png',image_path='stale.png',"
            "rotation=20 WHERE name='P';"
            "INSERT INTO PlotStationPosition(plant_name,section_name,line_name,"
            "station_id,x,y,position_source) "
            "VALUES ('P','S','L','1',0,-20,'migration');"
            "INSERT INTO PlotWorkerAssignmentMarker(worker_assignment_id,x,y,size,"
            "scale,line_thickness,locked,visible,enabled,position_source) "
            "VALUES (30,12,0,50,1.2,0,1,1,0,'manual'),"
            "(31,NULL,NULL,50,1,1,0,0,1,'unplaced');"
        )
    return legacy_catalog


def test_original_images_and_geometry_are_not_converted(mapped: Path) -> None:
    """Preserve encoded bytes, zero/negative pixel points and independent flags.

    Args:
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.

    Returns:
        None.
    """
    descriptor = read_legacy_descriptor(mapped, "p")
    before = descriptor.database_path.read_bytes()
    with LegacyProject(descriptor) as project:
        result = read_legacy_plot(project, read_legacy_catalogs(project))
    assert (
        result.images[0].image.data
        == (mapped.parent / "images/original.png").read_bytes()
    )
    assert result.original_plants[0]["rotation"] == 20
    assert result.positions.stations[0].point.y == -20
    positioned, unplaced = result.positions.workers
    assert positioned.assignment_id == 30 and positioned.point.y == 0
    assert positioned.locked and positioned.visible and not positioned.enabled
    assert positioned.line_thickness == 0 and positioned.scale == 1.2
    assert unplaced.point is None and unplaced.source is WorkerPositionSource.UNPLACED
    assert descriptor.database_path.read_bytes() == before


@pytest.mark.parametrize("change", ["missing", "corrupt", "path", "geometry"])
def test_invalid_maps_fail_without_repair(mapped: Path, change: str) -> None:
    """A missing companion or malformed point cannot silently lose layout data.

    Args:
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.
        change: Parametrized mutation applied to an isolated snapshot/source to exercise
            a rejection boundary.

    Returns:
        None.
    """
    descriptor = read_legacy_descriptor(mapped, "p")
    image = mapped.parent / "images/original.png"
    if change == "missing":
        image.unlink()
    elif change == "corrupt":
        image.write_bytes(b"not an image")
    else:
        sql = (
            "UPDATE Plant SET image_name='../outside.png'"
            if change == "path"
            else "UPDATE PlotWorkerAssignmentMarker SET x=NULL "
            "WHERE worker_assignment_id=30"
        )
        with (
            closing(sqlite3.connect(descriptor.database_path)) as connection,
            connection,
        ):
            connection.execute("PRAGMA ignore_check_constraints=ON")
            connection.execute(sql)
    before = descriptor.database_path.read_bytes()
    with LegacyProject(descriptor) as project, pytest.raises((ValueError, OSError)):
        read_legacy_plot(project, read_legacy_catalogs(project))
    assert descriptor.database_path.read_bytes() == before

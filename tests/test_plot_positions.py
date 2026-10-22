"""PLOT anchor semantics, explicit format upgrades and atomic geometry persistence.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from ergotools.application.plot_results import saved_plot_results
from ergotools.domain.plot_filters import PlotFilterSelection
from ergotools.domain.plot_positions import (
    PlotPoint,
    PlotPositions,
    StationPosition,
    StationPositionSource,
    WorkerAssignmentMarker,
    WorkerPositionSource,
    assignment_station,
)
from ergotools.domain.plot_scope import PlotScope
from ergotools.domain.work_catalog import StationKey
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.lifft_store import StoreFormatError
from ergotools.infrastructure.plant_image_import import import_plant_image
from ergotools.infrastructure.plot_position_store import (
    PlotPositionStore,
    create_position_schema,
)
from tests.test_history_persistence import HIERARCHY, JOBS, META, SOURCE, STATION
from tests.test_plant_layout_persistence import image_file


def create_project(path: Path, version: int) -> AssessmentProjectFile:
    """Create only a synthetic full-format project with known ownership.

    Args:
        path: Disposable test file path; the caller controls creation and cleanup.
        version: Explicit historical/native test-format version used to exercise
            acceptance or rejection boundaries.

    Returns:
        New owned disposable full native project at the requested format version; caller
        closes the returned handle.
    """
    project = AssessmentProjectFile.create_with_document(
        path,
        META,
        "source",
        SOURCE,
        format_version=version,
    )
    project.save_hierarchy(HIERARCHY)
    project.save_jobs(JOBS)
    return project


def manual_marker(assignment: int, x: float, y: float) -> WorkerAssignmentMarker:
    """Construct an explicitly positioned, visible original worker marker.

    Args:
        assignment: Exact synthetic assignment integer identity owning a worker marker.
        x: Canonical horizontal map anchor in original image pixels.
        y: Canonical vertical map anchor in original image pixels.

    Returns:
        Visible manually positioned worker marker with exact assignment and
        original-image X/Y coordinates.
    """
    return WorkerAssignmentMarker(
        assignment,
        PlotPoint(x, y),
        visible=True,
        source=WorkerPositionSource.MANUAL,
    )


def test_reference_anchor_and_worker_movement_rules() -> None:
    """First worker initializes anchor; later worker/job moves do not rewrite points.

    Args:
        None.

    Returns:
        None.
    """
    empty = PlotPositions("p")
    assert empty.worker_point(1, JOBS) is None
    hidden = empty.ensure_marker(1, JOBS)
    assert hidden.marker(1).point is None and not hidden.marker(1).visible
    assert hidden.ensure_marker(1, JOBS) is hidden
    first = hidden.with_saved_marker(manual_marker(1, -20.5, 30), JOBS)
    assert first.station_position(STATION).source is StationPositionSource.WORKER
    assert first.station_position(STATION).point == PlotPoint(-20.5, 30)
    assert first.marker(1).source is WorkerPositionSource.MANUAL
    second = first.with_saved_marker(manual_marker(1, 200, 300), JOBS)
    assert second.station_position(STATION) == first.station_position(STATION)
    moved = second.with_station(
        StationPosition(STATION, PlotPoint(500, 600), StationPositionSource.JOB),
    )
    assert moved.worker_point(1, JOBS) == PlotPoint(200, 300)
    initialized = moved.with_station(
        StationPosition(STATION, PlotPoint(0, 0)),
        initialize_only=True,
    )
    assert initialized is moved
    inherited = empty.with_station(
        StationPosition(STATION, PlotPoint(0, 0)),
    ).ensure_marker(1, JOBS)
    assert inherited.marker(1).point == PlotPoint(0, 0)
    assert inherited.marker(1).source is WorkerPositionSource.STATION_ANCHOR
    assert hidden.with_station(
        StationPosition(STATION, PlotPoint(10, 20)),
    ).worker_point(1, JOBS) == PlotPoint(10, 20)
    assert assignment_station(JOBS, 1) == STATION


def test_invalid_geometry_and_foreign_membership() -> None:
    """Reject invalid sizes/flags/points, missing owners and conflicting identities.

    Args:
        None.

    Returns:
        None.
    """
    for value in (True, float("nan"), float("inf"), "1"):
        with pytest.raises(ValueError):
            PlotPoint(value, 0)
    for kwargs in (
        {"size": 0},
        {"scale": -1},
        {"line_thickness": -1},
        {"locked": 1},
        {"source": "unplaced"},
        {"point": PlotPoint(1, 2)},
        {"assignment_id": True},
    ):
        with pytest.raises(ValueError):
            WorkerAssignmentMarker(**({"assignment_id": 1} | kwargs))
    marker = manual_marker(1, 0, 0)
    with pytest.raises(ValueError):
        PlotPositions("p", workers=(marker, marker))
    with pytest.raises(ValueError):
        PlotPositions("p", stations=(None,))
    with pytest.raises(ValueError):
        StationPosition(STATION, PlotPoint(1, 2), "manual")
    empty = PlotPositions("p")
    for operation in (
        lambda: empty.marker(True),
        lambda: empty.ensure_marker(
            1, replace(JOBS, project_id="foreign", assignments=())
        ),
        lambda: empty.ensure_marker(99, JOBS),
        lambda: empty.with_saved_marker(WorkerAssignmentMarker(1), JOBS),
        lambda: empty.with_station(None),
        lambda: empty.worker_point(
            1, replace(JOBS, project_id="foreign", assignments=())
        ),
        lambda: empty.validate(
            HIERARCHY, replace(JOBS, project_id="foreign", assignments=())
        ),
        lambda: assignment_station(JOBS, True),
    ):
        with pytest.raises((ValueError, KeyError)):
            operation()
    absent = PlotPositions(
        "p",
        (StationPosition(StationKey("P", "S", "L", "missing"), PlotPoint(1, 2)),),
    )
    with pytest.raises(ValueError):
        absent.validate(HIERARCHY, JOBS)


@pytest.mark.parametrize("version", [7, 8, 9])
def test_explicit_upgrade_reopen_copy_and_result_geometry(
    tmp_path: Path,
    version: int,
) -> None:
    """Only explicit position Save upgrades; copies/results preserve exact geometry.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        version: Explicit historical/native test-format version used to exercise
            acceptance or rejection boundaries.

    Returns:
        None.
    """
    path = tmp_path / "positions.ergprj"
    with create_project(path, version) as project:
        before = path.read_bytes()
        assert project.load_plot_positions() == PlotPositions("p")
        assert path.read_bytes() == before and project.format_version == version
        positions = PlotPositions("p").with_saved_marker(
            replace(
                manual_marker(1, 24.5, -12),
                size=62,
                scale=1.2,
                line_thickness=0,
                locked=True,
                enabled=False,
            ),
            JOBS,
        )
        project.save_plot_positions(positions)
        assert (
            project.format_version == 10 and project.load_plot_positions() == positions
        )
        image = import_plant_image(image_file(tmp_path / "map.png"))
        project.save_plant_image("P", image)
        assert (
            project.format_version == 10 and project.load_plot_positions() == positions
        )
        results = saved_plot_results(
            project,
            PlotFilterSelection(PlotScope((("P",),))),
            current_year=2026,
        )
        assert results.positions == positions
        with project.snapshot(str(tmp_path / "backup.ergprj"), None, None) as backup:
            assert (
                backup.format_version == 10
                and backup.load_plot_positions() == positions
            )
            assert backup.load_plant_image("P") == image
        with project.snapshot_with_metadata(
            str(tmp_path / "copy.ergprj"),
            None,
            None,
            replace(META, title="Copy", description="Retain coordinates"),
        ) as copy:
            assert copy.format_version == 10 and copy.load_plot_positions() == positions
            assert copy.metadata.description == "Retain coordinates"
        assert project.load(project.list_assessments()[0].document) == SOURCE
    with AssessmentProjectFile.open(path) as reopened:
        assert reopened.load_plot_positions() == positions


@pytest.mark.parametrize("version", [7, 8, 9])
def test_upgrade_failure_rolls_back_schema_version_and_records(
    tmp_path: Path,
    version: int,
) -> None:
    """A late failure retains old metadata and removes uncommitted upgrade tables.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        version: Explicit historical/native test-format version used to exercise
            acceptance or rejection boundaries.

    Returns:
        None.
    """
    path = tmp_path / "rollback.ergprj"
    with create_project(path, version) as project:
        before = path.read_bytes()
        with (
            patch.object(
                PlotPositionStore,
                "write_in_transaction",
                side_effect=OSError("late failure"),
            ),
            pytest.raises(OSError),
        ):
            project.save_plot_positions(PlotPositions("p"))
        assert project.format_version == version and path.read_bytes() == before
        assert project.load_plot_positions() == PlotPositions("p")
        with closing(sqlite3.connect(path)) as connection:
            assert not connection.execute(
                "SELECT name FROM sqlite_master WHERE name='plot_worker_markers'",
            ).fetchall()
    with AssessmentProjectFile.open(path) as reopened:
        assert reopened.format_version == version


def test_existing_geometry_sql_failure_retains_previous_snapshot(
    tmp_path: Path,
) -> None:
    """Failure after deleting geometry restores both tables and original points.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "late.ergprj"
    with create_project(path, 9) as project:
        old = PlotPositions("p").with_saved_marker(manual_marker(1, 10, 20), JOBS)
        project.save_plot_positions(old)
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute(
                "CREATE TRIGGER fail_marker BEFORE INSERT ON plot_worker_markers "
                "BEGIN SELECT RAISE(ABORT,'controlled SQL failure'); END",
            )
        with pytest.raises(sqlite3.IntegrityError):
            project.save_plot_positions(
                old.with_saved_marker(manual_marker(1, 100, 200), JOBS),
            )
        assert project.load_plot_positions() == old and project.format_version == 10


def test_assignment_station_protection_and_explicit_removal(tmp_path: Path) -> None:
    """Markers protect unassessed assignments; closed ownership remains readable.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    with create_project(tmp_path / "guards.ergprj", 7) as project:
        positions = PlotPositions("p").ensure_marker(1, JOBS)
        project.save_plot_positions(positions)
        with pytest.raises(ValueError):
            project.replace_jobs(JOBS, replace(JOBS, assignments=()))
        renamed = replace(JOBS.assignments[0].worker, worker_id="x")
        with pytest.raises(ValueError):
            project.replace_jobs(
                JOBS,
                replace(
                    JOBS, assignments=(replace(JOBS.assignments[0], worker=renamed),)
                ),
            )
        closed = replace(
            JOBS, assignments=(replace(JOBS.assignments[0], active=False),)
        )
        project.replace_jobs(JOBS, closed)
        assert project.load_plot_positions() == positions
        project.save_plot_positions(PlotPositions("p"))
        project.replace_jobs(closed, replace(closed, assignments=(), placements=()))
        anchor = PlotPositions("p").with_station(
            StationPosition(STATION, PlotPoint(0, 0))
        )
        project.save_plot_positions(anchor)
        hierarchy = replace(HIERARCHY, work=replace(HIERARCHY.work, stations=()))
        with pytest.raises(ValueError):
            project.replace_hierarchy(HIERARCHY, hierarchy)
        with pytest.raises(ValueError):
            project.replace_worker_catalogs(
                HIERARCHY, hierarchy, project.load_jobs(), project.load_jobs()
            )
        project.save_plot_positions(PlotPositions("p"))
        project.replace_hierarchy(HIERARCHY, hierarchy)


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE plot_worker_markers SET visible=2",
        "UPDATE plot_worker_markers SET x=NULL",
        "UPDATE plot_worker_markers SET assignment_id=99",
        "UPDATE plot_station_positions SET station='missing'",
    ],
)
def test_corrupt_geometry_rejected_on_open(tmp_path: Path, statement: str) -> None:
    """Invalid flags, partial points and orphan references cannot become defaults.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        statement: Explicit SQL statement forwarded to the controlled temporary
            connection.

    Returns:
        None.
    """
    path = tmp_path / "corrupt.ergprj"
    with create_project(path, 10) as project:
        project.save_plot_positions(
            PlotPositions("p").with_saved_marker(manual_marker(1, 10, 20), JOBS),
        )
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(statement)
    with pytest.raises((StoreFormatError, ValueError)):
        AssessmentProjectFile.open(path)


def test_partial_format_and_transaction_boundaries(tmp_path: Path) -> None:
    """Reject partial-format upgrades, foreign geometry and unowned store writes.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    with (
        create_project(tmp_path / "partial.ergprj", 6) as project,
        pytest.raises(StoreFormatError),
    ):
        project.save_plot_positions(PlotPositions("p"))
    with create_project(tmp_path / "foreign.ergprj", 7) as project:
        with pytest.raises(ValueError):
            project.save_plot_positions(PlotPositions("foreign"))
        with pytest.raises(KeyError):
            project.save_plot_positions(
                PlotPositions("p", workers=(WorkerAssignmentMarker(99),)),
            )
        assert project.format_version == 7
    with closing(sqlite3.connect(":memory:")) as connection:
        with pytest.raises(RuntimeError):
            create_position_schema(connection)
        with pytest.raises(RuntimeError):
            PlotPositionStore(connection, "p").write_in_transaction(PlotPositions("p"))
        connection.execute("BEGIN")
        create_position_schema(connection)
        with pytest.raises(ValueError):
            PlotPositionStore(connection, "p").write_in_transaction(
                PlotPositions("foreign")
            )
        connection.rollback()

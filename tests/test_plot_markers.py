"""Native PLOT marker rendering, original geometry, drag intent and explicit saves.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest
from PyQt5.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QGraphicsItem

from ergotools.application.plot_layout import LoadedPlantLayout
from ergotools.application.plot_results import saved_plot_results
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.plot_filters import PlotFilterSelection, PlotRiskView
from ergotools.domain.plot_positions import (
    PlotPoint,
    PlotPositions,
    WorkerAssignmentMarker,
    WorkerPositionSource,
)
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.plant_image_import import import_plant_image
from ergotools.presentation.desktop.plot_layout_canvas import PlotLayoutCanvas
from ergotools.presentation.desktop.plot_marker_item import (
    MarkerAppearance,
    PlotMarkerItem,
)
from ergotools.presentation.desktop.plot_marker_layer import (
    PlotMarkerLayer,
    plot_damage_color,
)
from tests.test_plant_layout_persistence import image_file
from tests.test_plot_results import SCOPE
from tests.test_plot_results import project as project

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


def canvas_with_map(tmp_path: Path) -> PlotLayoutCanvas:
    """Create the real map widget with original-image coordinates.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        Live owned map canvas showing a synthetic original-pixel image; caller closes
        the widget.
    """
    canvas = PlotLayoutCanvas()
    canvas.resize(1100, 700)
    canvas.set_layout(
        LoadedPlantLayout(
            SCOPE,
            import_plant_image(image_file(tmp_path / "map.png")).data,
        )
    )
    canvas.show()
    QApplication.processEvents()
    return canvas


def move_mouse(
    canvas: PlotLayoutCanvas,
    point: QPoint,
    modifiers: Qt.KeyboardModifiers | None = None,
) -> None:
    """Send a real viewport move with explicit pressed-button state for xcb tests.

    Args:
        canvas: Owned real map canvas with a synthetic source image and original-image
            scene coordinates.
        point: Viewport mouse point in Qt logical pixels; the canvas maps it to
            image-space coordinates.
        modifiers: Explicit Qt key modifiers for a drag event; None uses no modifier
            keys.

    Returns:
        None.
    """
    QApplication.sendEvent(
        canvas.viewport(),
        QMouseEvent(
            QEvent.MouseMove,
            QPointF(point),
            QPointF(canvas.viewport().mapToGlobal(point)),
            Qt.NoButton,
            Qt.LeftButton,
            modifiers if modifiers is not None else Qt.KeyboardModifiers(Qt.NoModifier),
        ),
    )


def positions_for(project: AssessmentProjectFile) -> PlotPositions:
    """Seed visible workers and one shared anchor without faking risk results.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.

    Returns:
        Persisted visible worker markers and shared station anchor, retaining exact
        synthetic assignment ownership.
    """
    positions = PlotPositions("p")
    for identity, x in ((1, 100), (3, 200)):
        positions = positions.with_saved_marker(
            WorkerAssignmentMarker(
                identity,
                PlotPoint(x, 100),
                visible=True,
                source=WorkerPositionSource.MANUAL,
            ),
            project.load_jobs(),
        )
    project.save_plot_positions(positions)
    return positions


@pytest.mark.parametrize("language", [Language.ENGLISH, Language.SPANISH])
def test_render_modes_save_retry_cancel_and_image_guard(
    project: AssessmentProjectFile,
    tmp_path: Path,
    language: Language,
) -> None:
    """Items preserve results/map on failed Save and cancel pending intent.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    positions_for(project)
    canvas = canvas_with_map(tmp_path)
    errors = Mock()
    selected = Mock()
    layer = PlotMarkerLayer(
        canvas,
        project.load_jobs(),
        project.save_plot_positions,
        errors,
        language=language,
        current_year=2026,
        on_select=selected,
    )
    result = saved_plot_results(project, PlotFilterSelection(SCOPE), current_year=2026)
    layer.set_results(result)
    assert set(layer.items) == {("worker", 1), ("worker", 3)}
    circle = layer.items["worker", 1]
    unknown = layer.items["worker", 3]
    assert circle.appearance.shape == "circle" and unknown.appearance.shape == "hexagon"
    assert circle.anchor_point() == PlotPoint(100, 100)
    layer.select(circle)
    selected.assert_called_once_with(("worker", 1))
    assert circle.isSelected() and not unknown.isSelected()
    before = result.positions
    circle.setPos(150, 125)
    layer.moved(circle)
    with pytest.raises(ValueError):
        layer.set_results(result)
    layout = canvas.loaded_layout
    with pytest.raises(ValueError):
        canvas.set_layout(LoadedPlantLayout(SCOPE, None))
    assert canvas.loaded_layout is layout and layer.pending
    layer.save_positions = Mock(side_effect=OSError("controlled storage failure"))
    assert not layer.save(("worker", 1))
    assert layer.results.positions == before and circle.anchor_point() == PlotPoint(
        150, 125
    )
    assert layer.pending and errors.called
    layer.save_positions = project.save_plot_positions
    assert layer.save(("worker", 1)) and not layer.pending
    assert project.load_plot_positions().marker(1).point == PlotPoint(150, 125)
    circle.setPos(180, 180)
    layer.moved(circle)
    layer.cancel(("worker", 1))
    assert circle.anchor_point() == PlotPoint(150, 125) and not layer.pending
    comparison = replace(
        layer.results,
        selection=replace(result.selection, risk_view=PlotRiskView.COMPARISON),
    )
    layer.set_results(comparison)
    assert layer.items["worker", 1].appearance.comparison
    assert layer.items["worker", 1].appearance.job_probability == 0
    job_result = replace(
        comparison, selection=replace(result.selection, risk_view=PlotRiskView.JOB)
    )
    layer.set_results(job_result)
    job = layer.items["job", 1]
    assert job.size == 38 and job.appearance.label == "j" and job.anchored
    job.setPos(300, 200)
    layer.moved(job)
    layer.cancel(("job", 1))
    assert job.anchor_point() == PlotPoint(100, 100)
    job.setPos(300, 200)
    layer.moved(job)
    assert layer.save(("job", 1))
    assert layer.items["job", 1].anchor_point() == PlotPoint(300, 200)
    assert project.load_plot_positions().marker(1).point == PlotPoint(150, 125)
    assert canvas.scene().sceneRect().width() == 640
    canvas.set_layout(LoadedPlantLayout(SCOPE, None))
    assert not layer.items and layer.results is None
    canvas.close()
    canvas.deleteLater()


def test_unplaced_jobs_offsets_origin_and_pending_interlock(
    project: AssessmentProjectFile,
    tmp_path: Path,
) -> None:
    """Unplaced jobs stay dashed; pending moves block peers and preserve offsets.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    canvas = canvas_with_map(tmp_path)
    layer = PlotMarkerLayer(
        canvas,
        project.load_jobs(),
        project.save_plot_positions,
        Mock(),
        current_year=2026,
    )
    result = saved_plot_results(
        project,
        PlotFilterSelection(SCOPE, risk_view=PlotRiskView.JOB),
        current_year=2026,
    )
    # A second placed row at the same station exercises the original nine-pixel fanout.
    second = replace(
        result.jobs[0], placement=replace(result.jobs[0].placement, placement_id=99)
    )
    layer.set_results(replace(result, jobs=(*result.jobs, second)))
    first, peer = layer.items["job", 1], layer.items["job", 99]
    assert not first.anchored and first.anchor_point() == PlotPoint(18, 18)
    assert peer.offset == QPointF(9, 0)
    first.setPos(0, 0)
    layer.moved(first)
    assert not peer.isEnabled()
    assert layer.save(("job", 1))
    assert layer.items["job", 1].anchor_point() == PlotPoint(0, 0)
    assert layer.items["job", 99].anchor_point() == PlotPoint(0, 0)
    assert layer.items["job", 99].pos() == QPointF(9, 0)
    assert layer.items["job", 99].isEnabled()
    assert project.load_plot_positions().stations[0].point == PlotPoint(0, 0)
    canvas.close()
    canvas.deleteLater()


def test_native_drag_scale_lock_and_resize_keep_pixel_coordinates(
    tmp_path: Path,
) -> None:
    """Native drag uses image points; inverse resize never rewrites geometry.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    canvas = canvas_with_map(tmp_path)
    moved, selected = Mock(), Mock()
    item = PlotMarkerItem(
        PlotPoint(100, 100),
        MarkerAppearance("triangle", "#ff2e00"),
        selected,
        moved,
        view_scale=canvas.transform().m11(),
    )
    canvas.scene().addItem(item)
    point = canvas.mapFromScene(item.sceneBoundingRect().center())
    QTest.mousePress(canvas.viewport(), Qt.LeftButton, pos=point)
    move_mouse(canvas, point + QPoint(40, 20))
    QTest.mouseRelease(canvas.viewport(), Qt.LeftButton, pos=point + QPoint(40, 20))
    assert selected.call_count == 1 and moved.call_count == 1 and item.pending
    assert item.anchor_point().x > 100 and item.anchor_point().y > 100
    item.mark_saved()
    prior = item.anchor_point()
    scale = item.marker_scale
    point = canvas.mapFromScene(item.sceneBoundingRect().center())
    QTest.mousePress(canvas.viewport(), Qt.LeftButton, Qt.ControlModifier, point)
    move_mouse(canvas, point + QPoint(0, -30), Qt.KeyboardModifiers(Qt.ControlModifier))
    QTest.mouseRelease(
        canvas.viewport(), Qt.LeftButton, Qt.ControlModifier, point + QPoint(0, -30)
    )
    assert item.pending and item.marker_scale != scale
    item.cancel_edit()
    assert item.anchor_point() == prior and item.marker_scale == scale
    canvas.resize(1500, 950)
    QApplication.processEvents()
    item.set_view_scale(canvas.transform().m11())
    assert item.anchor_point() == prior
    locked = PlotMarkerItem(
        PlotPoint(200, 100),
        MarkerAppearance("circle", "#2eff00"),
        Mock(),
        Mock(),
        locked=True,
    )
    assert not locked.flags() & QGraphicsItem.ItemIsMovable
    with pytest.raises(ValueError):
        item.set_view_scale(0)
    canvas.close()
    canvas.deleteLater()


def test_hidden_unavailable_neutral_and_literal_tooltips(
    project: AssessmentProjectFile,
    tmp_path: Path,
) -> None:
    """Hidden markers stay absent; missing evidence has neutral escaped labels.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    positions = positions_for(project)
    project.save_plot_positions(
        replace(
            positions,
            workers=(
                replace(positions.workers[0], visible=False),
                positions.workers[1],
            ),
        )
    )
    canvas = canvas_with_map(tmp_path)
    layer = PlotMarkerLayer(
        canvas,
        project.load_jobs(),
        project.save_plot_positions,
        Mock(),
        current_year=2026,
    )
    result = saved_plot_results(
        project,
        PlotFilterSelection(SCOPE, AssessmentKind.TST),
        current_year=2026,
    )
    row = replace(
        result.workers[1],
        worker=replace(result.workers[1].worker, first_name="<b>&name"),
        assessment=replace(
            result.workers[1].assessment, probability=None, total_damage=None
        ),
    )
    layer.set_results(replace(result, workers=(result.workers[0], row)))
    assert set(layer.items) == {("worker", 3)}
    assert layer.items["worker", 3].appearance.color == "#D9E1E6"
    assert "&lt;b&gt;&amp;name" in layer.items["worker", 3].toolTip()
    assert "Individual Risk: Not available" in layer.items["worker", 3].toolTip()
    assert plot_damage_color(AssessmentKind.LIFFT, 0) == "#2eff00"
    assert plot_damage_color(AssessmentKind.DUET, 0).startswith("#")
    with pytest.raises(ValueError):
        layer.set_results(
            replace(
                result,
                selection=replace(result.selection, scope=type(SCOPE)((("Other",),))),
            )
        )
    layer.clear()
    with pytest.raises(ValueError):
        layer.save(("worker", 3))
    canvas.close()
    canvas.deleteLater()

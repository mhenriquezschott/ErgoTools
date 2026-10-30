"""Native PLOT navigation feedback, fitted zoom floor and marker-safe panning.

Test layer. Use real mouse/key/wheel events and disposable maps; navigation stays
inside project history, never creates image scrollbars or moves map assignments.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest
from PIL import Image
from PyQt5.QtCore import QPoint, QPointF, Qt
from PyQt5.QtGui import QWheelEvent
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from ergotools.application.plot_layout import LoadedPlantLayout
from ergotools.application.project_editing import ProjectEditingSession
from ergotools.bootstrap import load_icons
from ergotools.domain.plot_filters import PlotRiskView
from ergotools.domain.plot_positions import PlotPoint
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.plant_image_import import import_plant_image
from ergotools.presentation.desktop.plot_window import PlotWindow
from tests.test_plot_markers import canvas_with_map, move_mouse, positions_for
from tests.test_plot_results import SCOPE
from tests.test_plot_results import project as project
from tests.test_plot_window import host


def test_cursor_escape_target_zoom_and_fitted_floor(tmp_path: Path) -> None:
    """A large image can zoom back below 1:1; Esc is view cancellation only.

    Args:
        tmp_path: Disposable large-image directory.

    Returns:
        None; cursors clear and resizing retains the user's relative zoom.
    """
    canvas = canvas_with_map(tmp_path)
    image = tmp_path / "large.png"
    Image.new("RGB", (2400, 1600), "white").save(image)
    canvas.set_layout(LoadedPlantLayout(SCOPE, import_plant_image(image).data))
    QApplication.processEvents()
    initial = canvas.transform().m11()
    assert initial < 1
    center = canvas.viewport().rect().center()
    canvas.begin_zoom()
    assert canvas.zoom_pending and not canvas.isInteractive()
    assert canvas.viewport().cursor().shape() == Qt.CursorShape.BitmapCursor
    QTest.keyClick(canvas, Qt.Key.Key_Escape)
    assert not canvas.zoom_pending and canvas.isInteractive()
    assert canvas.transform().m11() == initial
    canvas.begin_zoom()
    original_point = canvas.mapToScene(center)
    QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=center)
    assert canvas.transform().m11() == pytest.approx(initial * 1.5)
    assert (canvas.mapToScene(center) - original_point).manhattanLength() < 3
    canvas.resize(1300, 800)
    QApplication.processEvents()
    QTest.qWait(20)
    assert canvas.transform().m11() / canvas._fit_scale == pytest.approx(1.5)
    canvas.zoom_out()
    QTest.mouseClick(
        canvas.viewport(),
        Qt.MouseButton.LeftButton,
        pos=canvas.viewport().rect().center(),
    )
    assert canvas.transform().m11() == pytest.approx(canvas._fit_scale)
    assert not canvas.can_zoom_out
    canvas.begin_zoom()
    canvas.begin_zoom()
    assert canvas.zoom_pending  # Repeated tool presses keep the tool active.
    canvas.cancel_navigation()
    assert not canvas.zoom_pending
    canvas.close()
    canvas.deleteLater()


def test_pan_wheel_and_escape_track_view_without_changing_marker_data(
    project: AssessmentProjectFile, tmp_path: Path
) -> None:
    """Navigation intercepts marker hits, preserves flags and consumes only active Esc.

    Args:
        project: Disposable real assignments/results/positions.
        tmp_path: Temporary image/widget directory.

    Returns:
        None; explicit pan and middle-drag change only hidden scroll offsets.
    """
    window = host(project, tmp_path)
    canvas = window.map_panel.canvas
    layer = window.layer
    before = (
        project.load_plot_positions(),
        project.load_history(),
        project.load_job_risk(),
    )
    original_points = {key: item.anchor_point() for key, item in layer.items.items()}
    revision = layer.history.session.revision
    center = canvas.viewport().rect().center()
    window.map_panel.buttons["zoom_in"].click()
    assert window.map_panel.buttons["zoom_in"].isChecked()
    QTest.keyClick(canvas, Qt.Key.Key_Escape)
    assert window.isVisible() and not canvas.zoom_pending
    window.map_panel.buttons["zoom_in"].click()
    QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=center)
    assert window.map_panel.buttons["pan"].isEnabled()
    window.map_panel.buttons["pan"].click()
    assert canvas.navigation_mode == "pan" and not canvas.isInteractive()
    view_before = canvas.mapToScene(center)
    start = canvas.mapFromScene(layer.items["worker", 1].sceneBoundingRect().center())
    QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=start)
    assert canvas.viewport().cursor().shape() == Qt.CursorShape.ClosedHandCursor
    end = start - QPoint(90, 60)
    move_mouse(canvas, end)
    QTest.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=end)
    assert canvas.mapToScene(center) != view_before
    QTest.keyClick(canvas, Qt.Key.Key_Escape)
    assert (
        window.isVisible()
        and canvas.navigation_mode == "select"
        and canvas.isInteractive()
    )
    view_before = canvas.mapToScene(center)
    QTest.mousePress(canvas.viewport(), Qt.MouseButton.MiddleButton, pos=center)
    move_mouse(canvas, center + QPoint(40, 25))
    QTest.mouseRelease(
        canvas.viewport(), Qt.MouseButton.MiddleButton, pos=center + QPoint(40, 25)
    )
    assert canvas.mapToScene(center) != view_before
    scale = canvas.transform().m11()
    wheel = QWheelEvent(
        QPointF(center),
        QPointF(canvas.viewport().mapToGlobal(center)),
        QPoint(),
        QPoint(0, 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    QApplication.sendEvent(canvas.viewport(), wheel)
    assert canvas.transform().m11() == pytest.approx(scale * 1.2)
    assert {
        key: item.anchor_point() for key, item in layer.items.items()
    } == original_points
    assert layer.history.session.revision > revision and not layer.pending
    assert (
        project.load_plot_positions(),
        project.load_history(),
        project.load_job_risk(),
    ) == before
    assert canvas.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    assert canvas.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    window.confirm_close = Mock(return_value=True)
    window.close()
    window.deleteLater()


@pytest.mark.parametrize("mode", list(PlotRiskView))
def test_zoom_scales_markers_with_image_and_recreated_items(
    project: AssessmentProjectFile, tmp_path: Path, mode: PlotRiskView
) -> None:
    """All glyphs magnify with plant pixels, retaining exact assignment anchors.

    Args:
        project: Disposable native assignments and risk data.
        tmp_path: Temporary map directory.
        mode: Individual, Job or Comparison representation of the same assignment.

    Returns:
        None; initial fit sizes remain stable, while user zoom scales every glyph.
    """
    window = host(project, tmp_path)
    try:
        window.filters.risk_buttons[mode].click()
        canvas = window.map_panel.canvas
        layer = window.layer
        key = ("job" if mode is PlotRiskView.JOB else "worker", 1)
        item = layer.items[key]
        original = item.anchor_point()
        initial_width = item.marker_rect().width() * canvas.transform().m11()
        positions = project.load_plot_positions()
        canvas.apply_zoom(1.5, canvas.viewport().rect().center())
        assert item.marker_rect().width() * canvas.transform().m11() == pytest.approx(
            initial_width * 1.5
        )
        assert item.anchor_point() == original
        layer.set_results(replace(layer.results))
        item = layer.items[key]
        assert item.marker_rect().width() * canvas.transform().m11() == pytest.approx(
            initial_width * 1.5
        )
        assert item.anchor_point() == original
        canvas.reset_view()
        # Qt can settle the viewport by a pixel; fitted inverse sizing is rounded.
        assert item.marker_rect().width() * canvas.transform().m11() == pytest.approx(
            initial_width, abs=0.5
        )
        assert project.load_plot_positions() == positions
        left, right = (
            window.map_panel.buttons[name] for name in ("zoom_in", "zoom_out")
        )
        assert left.parentWidget() is right.parentWidget()
        assert left.geometry().right() + 1 == right.geometry().left()
        assert (
            left.height() == right.height() == window.map_panel.buttons["open"].height()
        )
        assert left.width() + right.width() == 63
    finally:
        window.confirm_close = Mock(return_value=True)
        window.close()
        window.deleteLater()


def navigation_host(
    project: AssessmentProjectFile, tmp_path: Path, shared: bool
) -> PlotWindow:
    """Build a disposable map before optionally attaching shared project history.

    Args:
        project: Native repository with source assessments and assignments.
        tmp_path: Image directory isolated from maintained fixtures.
        shared: Use integrated project history rather than diagnostic map history.

    Returns:
        Shown caller-owned map window with settled fitted geometry.
    """
    image = tmp_path / "navigation.png"
    Image.new("RGB", (1800, 1200), "white").save(image)
    project.save_plant_image("P", import_plant_image(image))
    project.save_plot_positions(positions_for(project))
    editing = (
        ProjectEditingSession(project.metadata.project_id, project) if shared else None
    )
    window = PlotWindow(
        project,
        project,
        project,
        lambda path: import_plant_image(Path(path)),
        load_icons(),
        current_year=2026,
        editing=editing,
    )
    window.show()
    QApplication.processEvents()
    QTest.qWait(30)
    return window


@pytest.mark.parametrize("shared", [False, True])
def test_persistent_tools_and_chronological_view_replay(
    project: AssessmentProjectFile, tmp_path: Path, shared: bool
) -> None:
    """Repeated magnification, pan, Fit and opacity replay without project-data edits.

    Args:
        project: Disposable native source repository.
        tmp_path: Disposable image directory.
        shared: Both map-only and integrated application history must agree.

    Returns:
        None; one completed gesture is one history step and tools stay active.
    """
    window = navigation_host(project, tmp_path, shared)
    try:
        canvas = window.map_panel.canvas
        original_data = project.load_plot_positions()
        window.workers.selector.select_id(3)
        assert window.workers.selected_id == 3
        window.tabs.setCurrentIndex(0)
        window.map_panel.buttons["zoom_in"].click()
        window.map_panel.buttons["zoom_in"].click()
        assert window.map_panel.buttons["zoom_in"].isChecked()
        target = canvas.viewport().rect().center()
        for expected in (1.5, 2.25):
            QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=target)
            assert canvas.navigation_snapshot().zoom == pytest.approx(expected)
            assert canvas.navigation_mode == "zoom_in"
        window.history_actions.replay(redo=False)
        assert canvas.navigation_snapshot().zoom == pytest.approx(1.5)
        assert canvas.navigation_mode == "zoom_in"
        assert window.workers.selected_id == 3
        assert window.tabs.currentIndex() == 0
        window.history_actions.replay(redo=True)
        assert canvas.navigation_snapshot().zoom == pytest.approx(2.25)
        window.map_panel.buttons["pan"].click()
        before = canvas.navigation_snapshot()
        QTest.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=target)
        move_mouse(canvas, target - QPoint(90, 70))
        QTest.mouseRelease(
            canvas.viewport(), Qt.MouseButton.LeftButton, pos=target - QPoint(90, 70)
        )
        after = canvas.navigation_snapshot()
        assert after.center != before.center and canvas.navigation_mode == "pan"
        window.history_actions.replay(redo=False)
        assert canvas.navigation_snapshot().center == pytest.approx(
            before.center, abs=2
        )
        window.history_actions.replay(redo=True)
        assert canvas.navigation_snapshot().center == pytest.approx(after.center, abs=2)
        window.map_panel.buttons["fit"].click()
        assert (
            canvas.navigation_snapshot().zoom == 1
            and canvas.navigation_mode == "select"
        )
        window.history_actions.replay(redo=False)
        assert canvas.navigation_snapshot().zoom == pytest.approx(2.25)
        window.map_panel.buttons["opacity"].click()
        assert canvas.marker_opacity == 0.9
        window.history_actions.replay(redo=False)
        assert canvas.marker_opacity == 1
        window.map_panel.buttons["select"].click()
        assert canvas.navigation_mode == "select" and canvas.isInteractive()
        assert window.map_panel.buttons["select"].isChecked()
        assert project.load_plot_positions() == original_data
        if window.editing is not None:
            assert not window.editing.is_dirty
    finally:
        window.confirm_close = Mock(return_value=True)
        window.close()
        window.deleteLater()


def test_job_cancel_restores_accepted_move_and_supports_shared_replay(
    project: AssessmentProjectFile, tmp_path: Path
) -> None:
    """Cancel movement restores only the last selected move, including accepted drags.

    Args:
        project: Disposable native project with workplace assignments.
        tmp_path: Disposable image directory.

    Returns:
        None; Cancel is reversible, and invalid coordinate drafts can be discarded.
    """
    window = navigation_host(project, tmp_path, True)
    try:
        window.filters.risk_buttons[PlotRiskView.JOB].click()
        window.jobs.selector.select_id(3)
        original = window.layer.worker_settings(3).point
        item = window.layer.items["job", 3]
        item.setPos(123.125, 234.25)
        window.layer.moved(item)
        assert window.jobs.cancel_button.isEnabled()
        assert not item.pending  # Already accepted by the integrated editor.
        window.jobs.cancel_button.click()
        assert window.layer.worker_settings(3).point == original
        assert project.load_plot_positions().marker(3).point == original
        assert "restored" in window.jobs.movement_hint.text()
        assert "accepted" in window.jobs.status.text()
        assert window.jobs.selector.isEnabled()
        assert not window.jobs.cancel_button.isEnabled()
        window.setFocus()
        window.history_actions.replay(redo=False)
        assert window.layer.worker_settings(3).point.x == 123.125
        assert window.jobs.selected_id == 3
        window.history_actions.replay(redo=True)
        assert window.layer.worker_settings(3).point == original
        window.jobs.x_input.setFocus()
        window.jobs.x_input.selectAll()
        QTest.keyClicks(window.jobs.x_input, "invalid")
        assert window.jobs.cancel_button.isEnabled()
        window.jobs.cancel_button.click()
        assert not window.jobs.has_unaccepted_fields
        assert window.layer.worker_settings(3).point == original
        assert window.jobs.x_input.text() != "invalid"
    finally:
        window.confirm_close = Mock(return_value=True)
        window.close()
        window.deleteLater()


@pytest.mark.parametrize("shared", [False, True])
@pytest.mark.parametrize("corner", [False, True])
def test_worker_locate_recenters_zoomed_view_with_edge_clamping_and_history(
    project: AssessmentProjectFile, tmp_path: Path, shared: bool, corner: bool
) -> None:
    """Locate reveals an offscreen selected worker, centering it as bounds allow.

    Args:
        project: Disposable native assignment/source repository.
        tmp_path: Disposable image directory.
        shared: Exercise local PLOT and integrated project history.
        corner: Exercise both an interior point and a point near image boundaries.

    Returns:
        None; zoom/data stay exact and Undo/Redo restores the locate viewport.
    """
    window = navigation_host(project, tmp_path, shared)
    try:
        canvas = window.map_panel.canvas
        marker = replace(
            window.layer.worker_settings(3),
            point=PlotPoint(1680, 1080) if corner else PlotPoint(900, 600),
        )
        window.layer.preview_worker(marker)
        if not shared:
            window.layer.save_workers((marker,))
        data = project.load_plot_positions()
        canvas.apply_zoom(4, QPoint(30, 30))
        window.workers.selector.select_id(3)
        item = window.layer.items["worker", 3]
        target = item.sceneBoundingRect().center()
        assert not canvas.viewport().rect().contains(canvas.mapFromScene(target))
        before = canvas.navigation_snapshot()
        window.workers.locate_button.click()
        assert canvas.viewport().rect().contains(canvas.mapFromScene(target))
        if corner:
            assert (
                canvas.horizontalScrollBar().value()
                == canvas.horizontalScrollBar().maximum()
            )
        else:
            assert (
                canvas.mapFromScene(target) - canvas.viewport().rect().center()
            ).manhattanLength() <= 2
        assert canvas.navigation_snapshot().zoom == before.zoom
        assert project.load_plot_positions() == data
        window.setFocus()
        window.history_actions.replay(redo=False)
        assert canvas.navigation_snapshot().center == pytest.approx(
            before.center, abs=2
        )
        window.history_actions.replay(redo=True)
        assert canvas.viewport().rect().contains(canvas.mapFromScene(target))
        assert window.workers.selected_id == 3
        assert project.load_plot_positions() == data
    finally:
        window.confirm_close = Mock(return_value=True)
        window.close()
        window.deleteLater()


def test_zoom_limit_is_400_percent_for_click_wheel_and_history(
    project: AssessmentProjectFile, tmp_path: Path
) -> None:
    """All magnification paths clamp at four times fit and replay that boundary.

    Args:
        project: Disposable native source repository.
        tmp_path: Temporary image directory.

    Returns:
        None; repeated zoom-in clicks and wheel events never exceed the shared cap.
    """
    window = navigation_host(project, tmp_path, True)
    try:
        canvas = window.map_panel.canvas
        target = canvas.viewport().rect().center()
        window.map_panel.buttons["zoom_in"].click()
        for _ in range(8):
            QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=target)
        assert canvas.navigation_snapshot().zoom == 4
        assert canvas.transform().m11() / canvas.fitted_scale == pytest.approx(4)
        wheel = QWheelEvent(
            QPointF(target),
            QPointF(canvas.viewport().mapToGlobal(target)),
            QPoint(),
            QPoint(0, 1200),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.NoScrollPhase,
            False,
        )
        QApplication.sendEvent(canvas.viewport(), wheel)
        assert canvas.navigation_snapshot().zoom == 4
        window.setFocus()
        window.history_actions.replay(redo=False)
        assert canvas.navigation_snapshot().zoom < 4
        window.history_actions.replay(redo=True)
        assert canvas.navigation_snapshot().zoom == 4
        canvas.reset_view()
        canvas.apply_zoom(100, target)
        assert canvas.navigation_snapshot().zoom == 4
    finally:
        window.confirm_close = Mock(return_value=True)
        window.close()
        window.deleteLater()


@pytest.mark.parametrize("shared", [False, True])
def test_fitted_controls_and_live_zoom_tooltips_follow_history(
    project: AssessmentProjectFile, tmp_path: Path, shared: bool
) -> None:
    """Fit disables unavailable tools; live percentages follow zoom and replay.

    Args:
        project: Disposable native project with mapped assignments.
        tmp_path: Disposable image directory.
        shared: Exercise both local PLOT and integrated project history.

    Returns:
        None; unavailable cursor modes end at fit and tooltips never retain stale zoom.
    """
    window = navigation_host(project, tmp_path, shared)
    try:
        canvas = window.map_panel.canvas
        buttons = window.map_panel.buttons
        before = project.load_plot_positions()
        assert not buttons["zoom_out"].isEnabled() and not buttons["pan"].isEnabled()
        assert "Current zoom: 100%" in buttons["zoom_in"].toolTip()
        assert "Current zoom: 100%" in buttons["zoom_out"].toolTip()
        canvas.begin_pan()
        assert canvas.navigation_mode == "select"
        canvas.zoom_out()
        assert canvas.navigation_mode == "select"
        target = canvas.viewport().rect().center()
        canvas.apply_zoom(1.5, target)
        assert buttons["zoom_out"].isEnabled() and buttons["pan"].isEnabled()
        assert "Current zoom: 150%" in buttons["zoom_in"].toolTip()
        buttons["pan"].click()
        buttons["fit"].click()
        assert canvas.navigation_mode == "select" and buttons["select"].isChecked()
        assert not buttons["zoom_out"].isEnabled() and not buttons["pan"].isEnabled()
        assert "Current zoom: 100%" in buttons["zoom_out"].toolTip()
        window.setFocus()
        window.history_actions.replay(redo=False)
        assert buttons["zoom_out"].isEnabled() and buttons["pan"].isEnabled()
        assert "Current zoom: 150%" in buttons["zoom_out"].toolTip()
        canvas.reset_view()
        canvas.apply_zoom(3.375, target)
        assert "Current zoom: 337.5%" in buttons["zoom_in"].toolTip()
        canvas.apply_zoom(100, target)
        assert "Current zoom: 400%" in buttons["zoom_in"].toolTip()
        assert "maximum 400%" in buttons["zoom_out"].toolTip()
        buttons["zoom_out"].click()
        for _ in range(8):
            QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=target)
        assert canvas.navigation_snapshot().zoom == 1
        assert canvas.navigation_mode == "select"
        assert not buttons["zoom_out"].isEnabled() and not buttons["pan"].isEnabled()
        assert "Current zoom: 100%" in buttons["zoom_in"].toolTip()
        assert project.load_plot_positions() == before
    finally:
        window.confirm_close = Mock(return_value=True)
        window.close()
        window.deleteLater()

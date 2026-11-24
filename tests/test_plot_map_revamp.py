"""PLOT shared-filter playback, stable geometry and atomic multi-marker layout tests.

Private copies preserve the owner's updated plant image and placements. Native Qt
selection/edit gestures exercise real scene geometry; no maintained fixture is written.
"""

from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from shutil import copyfile

import pytest
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from ergotools.application.shift_playback import prepare_shift
from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.plot_scope import PlotScope
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.plant_image_import import import_plant_image
from ergotools.presentation.desktop.plot_window import PlotWindow
from tests.test_plot_markers import move_mouse

# One retained Qt application owns test scene/event lifetimes.
_APP = QApplication.instance() or QApplication([])
# The owner-provided map is only copied, never changed by regression tests.
_DEMO = Path("test_projects/native/shift_view_demo.ergprj")


@pytest.fixture
def map_window(tmp_path: Path) -> Iterator[PlotWindow]:
    """Open a private real project and always close without diagnostic Save prompts.

    Args:
        tmp_path: Disposable project directory.

    Yields:
        Real opt-in PLOT window; the private SQLite bytes must remain unchanged.
    """
    path = tmp_path / "copy.ergprj"
    copyfile(_DEMO, path)
    before = path.read_bytes()
    with AssessmentProjectFile.open(path) as project:
        dialog = PlotWindow(
            project,
            project,
            project,
            lambda s: import_plant_image(Path(s)),
            load_icons(),
            current_year=2026,
            shift_repository=project,
        )
        dialog.show()
        dialog.resize(1640, 1120)
        _APP.processEvents()
        # Settle the native window-manager and wrapped-label size hints before
        # comparing the ordinary window against a different mode's geometry.
        QTest.qWait(80)
        yield dialog
        dialog.confirm_close = lambda: True
        dialog.close()
        dialog.deleteLater()
        _APP.processEvents()
    assert path.read_bytes() == before


def test_shift_geometry_selection_and_both_exposure_columns(
    map_window: PlotWindow,
) -> None:
    """Preserve window size, exact anchors and linked read-only selection.

    Args:
        map_window: Disposable populated native map.

    Returns:
        None; selection and Locate never change saved geometry or require scrolling
        horizontally to see the final exposure column.
    """
    dialog = map_window
    rail = dialog.map_panel.rail_tools
    assert (
        rail.indexOf(dialog.map_tools)
        == rail.indexOf(dialog.map_panel.buttons["opacity"]) + 1
    )
    assert rail.indexOf(dialog.map_panel.buttons["select"]) == 1
    before = dialog.size()
    regions = [
        dialog.map_panel,
        dialog.map_panel.canvas,
        dialog.map_panel.rail,
        dialog.tabs,
    ]
    geometry = [widget.geometry() for widget in regions]
    view = dialog.map_panel.canvas.navigation_snapshot()
    selected = next(i for i in dialog.layer.items.values() if i.isSelected())
    assert dialog.map_tools.spacing.value() == round(selected.marker_rect().width())
    points = {
        row.worker.worker_id: dialog.layer.items[
            "worker", row.assessment.assignment_id
        ].pos()
        for row in dialog.layer.results.workers
    }
    dialog.shift_button.click()
    _APP.processEvents()
    player = dialog.shift_player
    assert player is not None and player.data is not None
    assert dialog.size() == before
    assert [widget.geometry() for widget in regions] == geometry
    assert dialog.map_panel.canvas.navigation_snapshot() == view
    assert (
        player.table.columnViewportPosition(2) + player.table.columnWidth(2)
        <= player.table.viewport().width()
    )
    for glyph in player.people:
        assert glyph.pos() == points[glyph.label]
        assert glyph.marker_rect().topLeft() == QPointF(0, 0)
    player.table.selectRow(3)
    assert player.selected_worker == player.data.rows[3].worker_id
    assert next(
        g for g in player.people if g.label == player.selected_worker
    ).isSelected()
    player.people[6].picked.emit(player.people[6].label)
    assert player.table.currentRow() == 6
    player.worker_overview.search.setText("Ana")
    assert player.worker_overview.selector.count() == 1
    player.worker_overview.search.clear()
    player.seek(300)
    player.locate_worker()
    assert not any(g.flags() & g.ItemIsMovable for g in player.people)
    player.leave()
    _APP.processEvents()
    assert dialog.size() == before
    widths = [
        b.width() for b in [*dialog.filters.risk_buttons.values(), dialog.shift_button]
    ]
    assert max(widths) - min(widths) <= 2


def test_shift_uses_shared_tool_demographics_and_workplace(
    map_window: PlotWindow,
) -> None:
    """Filter playback without solving again or changing retained evidence.

    Args:
        map_window: Disposable map and complete paired rotations.

    Returns:
        None; filtered scope shows only matching fixed squares and visiting workers.
    """
    dialog = map_window
    dialog.shift_button.click()
    player = dialog.shift_player
    assert player is not None
    player.seek(200)
    dialog.filters.tools.select_tool(AssessmentKind.DUET)
    dialog.filters.demographics.setChecked(True)
    dialog.filters.sex.setCurrentIndex(dialog.filters.sex.findData("Female"))
    dialog.filters.apply_filters()
    assert player.elapsed == 200
    assert len(player.visible_ids) == 10
    assert all(
        player.catalog_people[key].details.sex == "Female" for key in player.visible_ids
    )
    assert player.filter_selection.tool is AssessmentKind.DUET
    place = next(iter(player.target_places.values()))
    scope = PlotScope(
        ((place.plant_name, place.section_name, place.line_name, place.station_id),),
        place.shift_id,
    )
    assert dialog.filters.workplace.set_scope(scope)
    dialog.filters.demographics.setChecked(False)
    dialog.filters.apply_filters()
    assert sum(g.isVisible() for g in player.glyphs if g.job) == 1
    assert len(player.visible_ids) == 1
    assert player.play.isEnabled()
    player.apply_filters(
        replace(player.filter_selection, scope=PlotScope((("Other plant",),)))
    )
    assert player.rotation.count() == 0 and player.data is None
    assert not player.play.isEnabled() and not player.glyphs


def test_alignment_and_group_movement_are_one_history_step(
    map_window: PlotWindow,
) -> None:
    """Align and drag a selection atomically, with symmetric Undo and Redo.

    Args:
        map_window: Private diagnostic map with existing local chronological history.

    Returns:
        None; unrelated workers retain their exact coordinates.
    """
    layer = map_window.layer
    items = list(layer.items.values())[:2]
    for item in layer.items.values():
        item.setSelected(item in items)
    # Introduce a different Y via the ordinary single-item edit first.
    items[1].setPos(items[1].pos() + QPointF(0, 60))
    layer.moved(items[1])
    before = layer.history.state
    layer.align_selected(True)
    after = layer.history.state
    assert before != after
    assert items[0].mapToScene(items[0].marker_rect().center()).y() == pytest.approx(
        items[1].mapToScene(items[1].marker_rect().center()).y()
    )
    assert layer.undo()
    assert layer.history.state == before
    assert layer.redo()
    assert layer.history.state == after
    for item in items:
        item.setPos(item.pos() + QPointF(60, 40))
    layer.moved(items[0])
    moved = layer.history.state
    assert moved != after
    assert layer.undo()
    assert layer.history.state == after
    assert layer.redo()
    assert layer.history.state == moved


def test_rubber_selection_and_live_grid_snap(map_window: PlotWindow) -> None:
    """Select two warehouse icons by rectangle and snap an actual released drag.

    Args:
        map_window: Private map with the owner's separated initial work cells.

    Returns:
        None; grid visibility follows dragging and snap affects source anchors only.
    """
    canvas, layer = map_window.map_panel.canvas, map_window.layer
    items = list(layer.items.values())[:2]
    scene = canvas.scene()
    scene.clearSelection()
    area = items[0].sceneBoundingRect().united(items[1].sceneBoundingRect())
    start = canvas.mapFromScene(area.topLeft() - QPointF(12, 12))
    end = canvas.mapFromScene(area.bottomRight() + QPointF(12, 12))
    QTest.mousePress(canvas.viewport(), Qt.LeftButton, pos=start)
    move_mouse(canvas, end)
    QTest.mouseRelease(canvas.viewport(), Qt.LeftButton, pos=end)
    assert all(i.isSelected() for i in items)
    assert map_window.map_tools.horizontal.isEnabled()
    map_window.map_tools.snap.setChecked(True)
    map_window.map_tools.spacing.setValue(25)
    offset = items[1].pos() - items[0].pos()
    point = canvas.mapFromScene(items[0].mapToScene(items[0].marker_rect().center()))
    QTest.mousePress(canvas.viewport(), Qt.LeftButton, pos=point)
    assert canvas.dragging_markers
    move_mouse(
        canvas,
        point
        + canvas.mapFromScene(QPointF(30, 30))
        - canvas.mapFromScene(QPointF(0, 0)),
    )
    QTest.mouseRelease(canvas.viewport(), Qt.LeftButton, pos=point)
    assert not canvas.dragging_markers
    assert items[1].pos() - items[0].pos() == offset
    assert items[0].anchor_point().x % 25 == pytest.approx(0)
    assert items[0].anchor_point().y % 25 == pytest.approx(0)
    map_window.map_tools.grid.setChecked(True)
    assert canvas.grid_visible
    canvas.pointer_changed.emit(321.5, 221.5)
    assert "X 321.5" in map_window.workers.controls.cursor_position.text()
    assert "Y 221.5" in map_window.jobs.cursor_position.text()
    assert map_window.map_panel.canvas_column.count() == 1


def test_incomplete_mapping_keeps_available_destinations(tmp_path: Path) -> None:
    """Lose one marker and its station fallback without inventing origin geometry.

    Args:
        tmp_path: Disposable project directory.

    Returns:
        None; strict preparation explains the problem, partial preparation keeps 19.
    """
    path = tmp_path / "partial.ergprj"
    copyfile(_DEMO, path)
    with AssessmentProjectFile.open(path) as project:
        positions = project.load_plot_positions()
        marker = positions.workers[0]
        assignment = next(
            a
            for a in project.load_jobs().assignments
            if a.assignment_id == marker.assignment_id
        )
        place = assignment.worker.workplace
        project.save_plot_positions(
            replace(
                positions,
                workers=tuple(
                    m
                    for m in positions.workers
                    if m.assignment_id != marker.assignment_id
                ),
                stations=tuple(
                    s
                    for s in positions.stations
                    if s.station.station_id != place.station_id
                ),
            )
        )
        scenario = project.load_rotation_scenarios()[0]
        with pytest.raises(ValueError, match="Place"):
            prepare_shift(project, scenario, AssessmentKind.LIFFT, False)
        data = prepare_shift(
            project, scenario, AssessmentKind.LIFFT, False, allow_partial=True
        )
        assert len(data.destinations) == 19 and data.issues
        dialog = PlotWindow(
            project,
            project,
            project,
            lambda s: import_plant_image(Path(s)),
            load_icons(),
            current_year=2026,
            shift_repository=project,
        )
        dialog.show()
        dialog.shift_button.click()
        player = dialog.shift_player
        assert player is not None and player.data is not None
        assert sum(g.isVisible() for g in player.glyphs if g.job) == 19
        assert not player.play.isEnabled() and not player.timeline.isEnabled()
        assert "Playback unavailable" in player.problem.text()
        dialog.close()


def test_shift_transport_and_toggle_selection(map_window: PlotWindow) -> None:
    """Keep transport state across Reload/jumps and allow explicit no selection.

    Args:
        map_window: Private complete 20-participant rotation with real breaks.

    Returns:
        None; Locate blinks without writing data, and row deselection survives frames.
    """
    map_window.shift_button.click()
    player = map_window.shift_player
    assert player is not None and player.data is not None
    player.table.selectRow(2)
    player.locate_worker()
    assert player.locate_timer.isActive()
    glyph = next(g for g in player.people if g.label == player.selected_worker)
    player.pulse_worker()
    assert not glyph.isSelected()
    player.pulse_worker()
    assert glyph.isSelected()
    cell = player.table.visualItemRect(player.table.item(2, 0)).center()
    QTest.mouseClick(player.table.viewport(), Qt.LeftButton, pos=cell)
    assert player.selected_worker is None
    player.seek(40)
    assert player.selected_worker is None
    assert not any(g.isSelected() for g in player.people)
    player.jump_boundary(True)
    first_boundary = min(p.end for b in player.data.timing.blocks() for p in b.pieces)
    assert player.elapsed == first_boundary and not player.timer.isActive()
    player.toggle()
    assert player.timer.isActive()
    player.jump_boundary(True)
    assert player.elapsed > first_boundary and player.timer.isActive()
    player.jump_boundary(False)
    assert player.elapsed == first_boundary and player.timer.isActive()
    player.reload()
    assert player.elapsed == 0 and player.timer.isActive()
    player.pause()
    player.seek(300)
    player.reload()
    assert player.elapsed == 0 and not player.timer.isActive()
    player.seek(player.data.timing.shift_minutes)
    player.reload()
    assert player.elapsed == 0 and not player.timer.isActive()


@pytest.mark.parametrize("mode", ["individual", "job", "comparison"])
def test_leaving_shift_applies_the_clicked_ordinary_mode(
    map_window: PlotWindow, mode: str
) -> None:
    """Restore the exact requested mode instead of resetting to the former one.

    Args:
        map_window: Private complete mapped rotation.
        mode: Ordinary risk mode selected while Shift View is active.

    Returns:
        None; the player returns to the ordinary bottom outcome region.
    """
    from ergotools.domain.plot_filters import PlotRiskView

    dialog = map_window
    dialog.shift_button.click()
    assert dialog.shift_player.active
    dialog.filters.risk_buttons[PlotRiskView(mode)].click()
    _APP.processEvents()
    assert not dialog.shift_player.active
    assert dialog.layer.results.selection.risk_view is PlotRiskView(mode)
    assert dialog.outcome_stack.currentWidget() is dialog.outcome
    if mode == "comparison":
        assert dialog.workers.controls.isHidden()

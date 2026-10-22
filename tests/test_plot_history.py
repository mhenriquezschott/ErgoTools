"""Reversible PLOT edits, partial atomic saves and project-scoped history.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from ergotools.application.plot_history import PlotPositionHistory, ReplacePlotPositions
from ergotools.application.session import DocumentKey
from ergotools.domain.language import Language
from ergotools.domain.plot_filters import PlotRiskView
from ergotools.domain.plot_positions import (
    PlotPoint,
    PlotPositions,
    StationPosition,
    WorkerAssignmentMarker,
    WorkerPositionSource,
)
from ergotools.domain.work_catalog import StationKey
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from tests.test_plot_markers import move_mouse
from tests.test_plot_results import project as project
from tests.test_plot_window import host

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


def geometry() -> PlotPositions:
    """Create two independent saved records without a database or Qt history.

    Args:
        None.

    Returns:
        Immutable two-record saved map geometry used to test history without Qt or
        database state.
    """
    return PlotPositions(
        "p",
        workers=tuple(
            WorkerAssignmentMarker(
                i,
                PlotPoint(i * 10, 0),
                visible=True,
                source=WorkerPositionSource.MANUAL,
            )
            for i in (1, 2)
        ),
    )


def test_command_ownership_noops_branching_and_partial_save_failure() -> None:
    """Partial commits clean only saved records; failed writes retain all intent.

    Args:
        None.

    Returns:
        None.
    """
    initial = geometry()
    history = PlotPositionHistory(DocumentKey("p", "map"), initial)
    a = replace(
        initial, workers=(replace(initial.workers[0], scale=2), initial.workers[1])
    )
    b = replace(a, workers=(a.workers[0], replace(a.workers[1], locked=True)))
    writer = Mock()
    assert history.edit(a, "plot.history.settings")
    assert history.edit(b, "plot.history.settings")
    history.save(a, writer)
    assert history.is_dirty and history.saved == a and history.state == b
    writer.side_effect = OSError("atomic write rejected")
    with pytest.raises(OSError):
        history.save(b, writer)
    assert history.saved == a and history.state == b
    writer.side_effect = None
    history.save(b, writer)
    assert not history.is_dirty and not history.session.is_dirty
    assert history.session.undo() and history.state == a and history.is_dirty
    assert history.session.redo() and not history.is_dirty
    assert history.session.undo()
    assert not history.edit(a, "plot.history.settings")
    assert history.session.redo_label_key is not None
    assert history.edit(initial, "plot.history.cancel")
    assert history.session.redo_label_key is None
    with pytest.raises(ValueError):
        history.session.execute(
            ReplacePlotPositions(DocumentKey("other", "map"), initial, a, "edit")
        )
    with pytest.raises(ValueError):
        history.session.execute(
            ReplacePlotPositions(history.session.document, a, b, "edit")
        )
    with pytest.raises(ValueError):
        history.edit(PlotPositions("other"), "edit")
    with pytest.raises(ValueError):
        history.save(PlotPositions("other"), writer)
    with pytest.raises(ValueError):
        PlotPositionHistory(DocumentKey("other", "map"), initial)
    assert history.state == initial and writer.call_count == 3


@pytest.mark.parametrize("language", tuple(Language))
def test_native_gesture_flags_save_undo_redo_branch_and_focus(
    project: AssessmentProjectFile, tmp_path: Path, language: Language
) -> None:
    """Real mouse/shortcuts route to marker history or local typing, never SQL.

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
    w = host(project, tmp_path, language=language)
    layer = w.layer
    actions = w.history_actions
    writer = Mock(wraps=project.save_plot_positions)
    layer.save_positions = writer
    before = project.load_plot_positions()
    key = ("worker", 1)
    item = layer.items[key]
    layer.select(item)
    w.activateWindow()
    w.map_panel.canvas.setFocus()
    _APP.processEvents()
    assert not actions.undo_action.isEnabled() and not layer.undo()
    assert not layer.redo()
    point = w.map_panel.canvas.mapFromScene(item.sceneBoundingRect().center())
    QTest.mousePress(w.map_panel.canvas.viewport(), Qt.LeftButton, pos=point)
    move_mouse(w.map_panel.canvas, point + QPoint(30, 20))
    move_mouse(w.map_panel.canvas, point + QPoint(60, 30))
    QTest.mouseRelease(
        w.map_panel.canvas.viewport(), Qt.LeftButton, pos=point + QPoint(60, 30)
    )
    moved = item.anchor_point()
    assert moved != before.marker(1).point and writer.call_count == 0
    assert layer.history.session.revision == 1  # one gesture, not one event per move
    QTest.keySequence(w.map_panel.canvas, QKeySequence(QKeySequence.Undo))
    assert item.anchor_point() == before.marker(1).point and not layer.pending
    QTest.keySequence(w.map_panel.canvas, QKeySequence(QKeySequence.Redo))
    assert item.anchor_point() == moved and layer.pending
    assert layer.save(key) and writer.call_count == 1 and not layer.pending
    QTest.mouseClick(actions.undo_button, Qt.LeftButton)
    assert layer.pending and project.load_plot_positions().marker(1).point == moved
    QTest.mouseClick(actions.redo_button, Qt.LeftButton)
    assert not layer.pending and writer.call_count == 1
    # A scale gesture is one reversible command as well.
    point = w.map_panel.canvas.mapFromScene(item.sceneBoundingRect().center())
    scale = item.marker_scale
    QTest.mousePress(
        w.map_panel.canvas.viewport(), Qt.LeftButton, Qt.ControlModifier, point
    )
    move_mouse(w.map_panel.canvas, point + QPoint(0, -20), Qt.ControlModifier)
    move_mouse(w.map_panel.canvas, point + QPoint(0, -35), Qt.ControlModifier)
    QTest.mouseRelease(
        w.map_panel.canvas.viewport(),
        Qt.LeftButton,
        Qt.ControlModifier,
        point + QPoint(0, -35),
    )
    assert item.marker_scale != scale
    assert layer.undo() and item.marker_scale == scale and not layer.pending
    controls = w.workers.controls
    controls.locked.setChecked(True)
    assert layer.history.session.redo_label_key is None and item.locked
    assert layer.undo() and not item.locked
    # An empty field history must not fall through to marker Undo.
    controls.x_input.setFocus()
    _APP.processEvents()
    revision = layer.history.session.revision
    QTest.keySequence(controls.x_input, QKeySequence(QKeySequence.Undo))
    assert layer.history.session.revision == revision
    controls.x_input.selectAll()
    QTest.keyClicks(controls.x_input, "123")
    QTest.keySequence(controls.x_input, QKeySequence(QKeySequence.Undo))
    assert (
        controls.x_input.text() != "123" and layer.history.session.revision == revision
    )
    w.map_panel.canvas.setFocus()
    _APP.processEvents()
    assert not actions.undo_action.isEnabled()  # unresolved typing is retained
    layer.cancel(key)
    w.map_panel.canvas.setFocus()
    _APP.processEvents()
    assert actions.undo_action.text().startswith(
        "Deshacer" if language is Language.SPANISH else "Undo"
    )
    assert writer.call_count == 1
    w.close()
    w.deleteLater()


def test_typed_batch_failure_hidden_markers_cancel_and_history_rebind(
    project: AssessmentProjectFile, tmp_path: Path
) -> None:
    """One batch command retains its values on failure and survives clean Apply.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    w = host(project, tmp_path)
    layer = w.layer
    controls = w.workers.controls
    controls.show_success = Mock()
    layer.show_error = Mock()
    baseline = project.load_plot_positions()
    controls.select(("worker", 1))
    controls.x_input.setText("0")
    controls.y_input.setText("-5")
    controls.scale_input.setText("1.5")
    controls.field_edited("")
    writer = Mock(side_effect=OSError("full disk"))
    layer.save_positions = writer
    controls.save()
    assert layer.pending and controls.x_input.text() == "0"
    assert project.load_plot_positions() == baseline
    assert layer.undo() and not layer.pending
    assert layer.redo() and controls.x_input.text() == "0"
    layer.save_positions = project.save_plot_positions
    controls.save()
    assert not layer.pending
    saved = project.load_plot_positions()
    assert saved.marker(1).point == PlotPoint(0, -5)
    history = layer.history
    w.filters.apply_filters()
    assert layer.history is history and layer.undo()
    assert project.load_plot_positions() == saved
    assert layer.redo() and not layer.pending
    controls.visible.setChecked(False)
    assert not layer.items["worker", 1].isVisible()
    assert layer.undo() and layer.items["worker", 1].isVisible()
    assert not layer.pending
    # Save All applies the new scale once; undo does not undo the prior Save.
    before_batch = layer.history.state
    controls.all_scale_input.setText("2.5")
    controls.save_all()
    assert not layer.pending
    assert layer.undo() and layer.history.state == before_batch
    assert layer.worker_settings(1).scale == 1.5
    assert layer.worker_settings(3).scale == 1
    assert layer.redo() and not layer.pending
    # View changes now share the same chronological history as marker edits.
    w.filters.risk_buttons[PlotRiskView.JOB].click()
    assert layer.history is history
    w.filters.risk_buttons[PlotRiskView.INDIVIDUAL].click()
    assert layer.history is history
    w.close()
    w.deleteLater()


def test_job_zero_anchor_save_undo_missing_anchor_and_cancel(
    project: AssessmentProjectFile, tmp_path: Path
) -> None:
    """Undo of first placement restores absent anchor; peers follow a saved anchor.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    w = host(project, tmp_path)
    layer = w.layer
    project.save_plot_positions(PlotPositions("p"))
    w.filters.risk_buttons[PlotRiskView.JOB].click()
    saved_workers = project.load_plot_positions().workers
    key = ("job", 1)
    item = layer.items[key]
    assert not item.anchored
    item.setPos(0, 0)
    layer.moved(item)
    assert layer.save(key)
    assert layer.undo() and layer.pending and not layer.items[key].anchored
    assert project.load_plot_positions().stations[0].point == PlotPoint(0, 0)
    assert layer.save(key) and not layer.pending
    assert not project.load_plot_positions().stations
    assert layer.redo() and layer.pending
    layer.cancel(key)
    assert not layer.pending
    assert layer.undo() and layer.pending
    assert layer.save(key) and not layer.pending
    assert project.load_plot_positions().workers == saved_workers
    w.close()
    w.deleteLater()


def test_save_keeps_exact_drag_values_instead_of_rounded_field_projection(
    project: AssessmentProjectFile, tmp_path: Path
) -> None:
    """Save is not a new edit; one Undo restores the full fractional gesture.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    w = host(project, tmp_path)
    layer = w.layer
    controls = w.workers.controls
    controls.show_success = Mock()
    key = ("worker", 1)
    layer.select(layer.items[key])
    original = layer.history.state
    exact = PlotPoint(123.4567890123, -98.7654321098)
    layer.items[key].setPos(exact.x, exact.y)
    layer.items[key].marker_scale = 1.23456789
    layer.moved(layer.items[key])
    revision = layer.history.session.revision
    controls.save_button.click()
    assert layer.history.session.revision == revision and not layer.pending
    assert project.load_plot_positions().marker(1).point == exact
    assert project.load_plot_positions().marker(1).scale == 1.23456789
    assert layer.undo() and layer.history.state == original
    assert layer.redo() and not layer.pending
    w.filters.risk_buttons[PlotRiskView.JOB].click()
    key = ("job", 1)
    layer.select(layer.items[key])
    # A second stored station makes accidental remove/reappend ordering visible.
    positions = layer.results.positions.with_station(
        StationPosition(StationKey("P", "T", "L", "1"), PlotPoint(10, 10))
    )
    project.save_plot_positions(positions)
    result = replace(layer.results, positions=positions)
    layer.set_results(result)
    original = layer.history.state
    layer.items[key].setPos(exact.x, exact.y)
    layer.moved(layer.items[key])
    revision = layer.history.session.revision
    w.jobs.save_button.click()
    assert layer.history.session.revision == revision and not layer.pending
    assert (
        project.load_plot_positions().station_position(layer.job_station(1)).point
        == exact
    )
    assert layer.undo() and layer.history.state == original
    assert layer.redo() and not layer.pending
    w.close()
    w.deleteLater()

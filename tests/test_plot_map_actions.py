"""Original map rail interactions and PNG capture without implicit project writes.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QFileDialog

from ergotools.domain.language import Language
from ergotools.domain.plot_positions import WorkerAssignmentMarker
from ergotools.domain.plot_scope import PlotScope
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from tests.test_plot_results import project as project
from tests.test_plot_window import _APP, host


@pytest.mark.parametrize("language", tuple(Language))
def test_map_rail_click_zoom_opacity_reset_capture_and_pending_edits(
    project: AssessmentProjectFile, tmp_path: Path, language: Language
) -> None:
    """Real rail clicks preserve saved sources and pending markers at both sizes.

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
    window = host(project, tmp_path, language=language)
    panel = window.map_panel
    canvas = panel.canvas
    snapshot = project.load_plot_positions(), project.read("P")
    saved = window.layer.results
    window.layer.preview_worker(WorkerAssignmentMarker(1, visible=True, scale=1.3))
    pending = dict(window.layer.worker_drafts)
    item = window.layer.items[("worker", 1)]
    before = item.pos()
    was_pending = item.pending
    initial = canvas.transform().m11()
    QTest.mouseClick(panel.buttons["zoom_in"], Qt.MouseButton.LeftButton)
    assert (
        canvas.zoom_pending and canvas.cursor().shape() == Qt.CursorShape.BitmapCursor
    )
    QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=QPoint(250, 200))
    assert canvas.zoom_pending
    assert canvas.transform().m11() == pytest.approx(initial * 1.5)
    assert item.pos() == before and item.pending is was_pending
    for expected in (0.9, 0.8, 0.7, 1.0):
        QTest.mouseClick(panel.buttons["opacity"], Qt.MouseButton.LeftButton)
        assert all(
            marker.opacity() == expected for marker in window.layer.items.values()
        )
        assert canvas.background.opacity() == 1.0
    # Zoom out uses the same click-target interaction and the actual fitted floor.
    QTest.mouseClick(panel.buttons["zoom_out"], Qt.MouseButton.LeftButton)
    assert canvas.zoom_pending
    QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=QPoint(250, 200))
    assert canvas.transform().m11() == pytest.approx(initial)
    assert not panel.buttons["zoom_out"].isEnabled()
    assert not panel.buttons["pan"].isEnabled()
    panel.buttons["select"].click()
    assert not canvas.zoom_pending
    QTest.mouseClick(panel.buttons["fit"], Qt.MouseButton.LeftButton)
    assert canvas.transform().m11() == pytest.approx(initial)
    assert window.layer.results is saved and window.layer.worker_drafts == pending
    for size in ((1300, 1045), (1800, 1200)):
        window.resize(*size)
        _APP.processEvents()
        QTest.qWait(20)
        destination = tmp_path / f"view-{size[0]}.png"
        panel.choose_capture = Mock(return_value=str(destination))
        QTest.mouseClick(panel.buttons["capture"], Qt.MouseButton.LeftButton)
        expected = canvas.grab().toImage().convertToFormat(QImage.Format_RGBA8888)
        assert (
            QPixmap(str(destination)).toImage().convertToFormat(QImage.Format_RGBA8888)
            == expected
        )
    assert (project.load_plot_positions(), project.read("P")) == snapshot
    window.confirm_close = Mock(return_value=True)
    window.close()
    window.deleteLater()


def test_capture_cancel_encoder_failure_and_portable_chooser(
    project: AssessmentProjectFile, tmp_path: Path
) -> None:
    """Cancel is silent; encoder failures report actionable errors.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    window = host(project, tmp_path)
    panel = window.map_panel
    before = project.load_plot_positions(), project.read("P")
    panel.choose_capture = Mock(return_value="")
    panel.show_error = Mock()
    with patch.object(panel.canvas, "grab") as grab:
        panel.capture_image()
        grab.assert_not_called()
    panel.choose_capture.return_value = str(tmp_path / "capture.png")
    with patch.object(
        panel.canvas, "grab", return_value=Mock(save=Mock(return_value=False))
    ):
        panel.capture_image()
    with patch.object(panel.canvas, "grab", side_effect=OSError("fixture encoder")):
        panel.capture_image()
    assert panel.show_error.call_count == 2
    assert (project.load_plot_positions(), project.read("P")) == before
    # The native chooser receives a leaf filename even for a literal plant ID.
    panel.scope = PlotScope(((r"P:/bad\plant",),))
    with patch.object(QFileDialog, "getSaveFileName", return_value=("", "")) as choose:
        assert type(panel).choose_capture(panel) == ""
    suggested = choose.call_args.args[2]
    assert suggested.startswith("P__bad_plant_") and suggested.endswith(".png")
    window.close()
    window.deleteLater()


def test_map_actions_disable_without_pixels_and_clear_armed_zoom(
    project: AssessmentProjectFile, tmp_path: Path
) -> None:
    """An absent saved layout cancels zoom and disables map-only actions.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    window = host(project, tmp_path)
    panel = window.map_panel
    panel.canvas.begin_zoom()
    assert panel.canvas.zoom_pending
    assert window.filters.workplace.set_scope(PlotScope((("Empty",),)))
    assert not panel.canvas.zoom_pending and panel.canvas.background is None
    for key in ("zoom_in", "zoom_out", "fit", "opacity", "capture"):
        assert not panel.buttons[key].isEnabled()
    panel.canvas.begin_zoom()
    assert not panel.canvas.zoom_pending
    panel.canvas.zoom_out()
    panel.canvas.reset_view()
    panel.canvas.cycle_opacity()
    panel.choose_capture = Mock()
    panel.capture_image()
    panel.choose_capture.assert_not_called()
    window.close()
    window.deleteLater()

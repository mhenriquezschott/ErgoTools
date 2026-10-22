"""PLOT worker visual preview, explicit persistence and atomic batch settings.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QGraphicsItem

from ergotools.application.plot_results import saved_plot_results
from ergotools.bootstrap import load_icons
from ergotools.domain.language import Language
from ergotools.domain.plot_filters import PlotFilterSelection, PlotRiskView
from ergotools.domain.plot_positions import PlotPoint, PlotPositions
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.plot_marker_layer import PlotMarkerLayer
from ergotools.presentation.desktop.plot_worker_controls import PlotWorkerControls
from tests.test_plot_markers import canvas_with_map, positions_for
from tests.test_plot_results import SCOPE
from tests.test_plot_results import project as project

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("language", [Language.ENGLISH, Language.SPANISH])
def test_worker_preview_save_retry_and_atomic_save_all(
    project: AssessmentProjectFile,
    tmp_path: Path,
    language: Language,
) -> None:
    """Flag previews never write; failed single/batch saves keep all draft intent.

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
    positions = positions_for(project)
    canvas = canvas_with_map(tmp_path)
    errors = Mock()
    writer = Mock(wraps=project.save_plot_positions)
    layer = PlotMarkerLayer(
        canvas,
        project.load_jobs(),
        writer,
        errors,
        current_year=2026,
        language=language,
    )
    panel = PlotWorkerControls(
        layer, load_icons(), language=language, show_success=Mock()
    )
    layer.set_results(
        saved_plot_results(project, PlotFilterSelection(SCOPE), current_year=2026)
    )
    panel.select(("worker", 1))
    assert panel.visible.isChecked() and panel.scale_input.text() == "1.00"
    panel.locked.setChecked(True)
    assert layer.items["worker", 1].locked
    assert (
        not layer.items["worker", 1].flags()
        & QGraphicsItem.GraphicsItemFlag.ItemIsMovable
    )
    panel.visible.setChecked(False)
    panel.enabled.setChecked(False)
    assert not layer.items["worker", 1].isVisible()
    assert not layer.items["worker", 1].isEnabled()
    assert writer.call_count == 0 and project.load_plot_positions() == positions
    panel.show()
    QTest.mouseClick(panel.x_input, Qt.MouseButton.LeftButton)
    panel.x_input.selectAll()
    QTest.keyClicks(panel.x_input, "-25.5")
    assert panel.x_input.text() == "-25.5" and layer.pending
    panel.y_input.setText("0")
    panel.scale_input.setText("nan")
    panel.save()
    assert errors.called and writer.call_count == 0
    panel.scale_input.setText("1.75")
    layer.save_positions = Mock(side_effect=OSError("controlled failure"))
    panel.save()
    assert panel.x_input.text() == "-25.5" and layer.pending
    layer.save_positions = writer
    panel.save()
    marker = project.load_plot_positions().marker(1)
    assert marker.point == PlotPoint(-25.5, 0)
    assert (
        marker.scale == 1.75
        and marker.locked
        and not marker.visible
        and not marker.enabled
    )
    assert not layer.pending and writer.call_count == 1
    panel.visible.setChecked(True)
    panel.enabled.setChecked(True)
    panel.locked.setChecked(False)
    panel.select(("worker", 3))
    panel.locked.setChecked(True)
    before = project.load_plot_positions()
    panel.all_scale_input.setText("0")
    panel.save_all()
    assert project.load_plot_positions() == before and writer.call_count == 1
    panel.all_scale_input.setText("2.5")
    layer.save_positions = Mock(side_effect=OSError("controlled batch failure"))
    panel.save_all()
    assert project.load_plot_positions() == before and layer.pending
    assert set(layer.worker_drafts) == {1, 3}
    layer.save_positions = writer
    panel.save_all()
    after = project.load_plot_positions()
    assert writer.call_count == 2 and not layer.pending
    assert isinstance(panel.show_success, Mock) and panel.show_success.call_count == 2
    assert all(marker.scale == 2.5 for marker in after.workers)
    assert after.marker(1).point == PlotPoint(-25.5, 0)
    assert after.marker(1).visible and after.marker(1).enabled
    assert after.marker(3).locked
    panel.close()
    canvas.close()


def test_unplaced_hidden_creation_and_batch_validation(
    project: AssessmentProjectFile,
    tmp_path: Path,
) -> None:
    """Read/select never writes; unplaced batch cannot invent origin.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    canvas = canvas_with_map(tmp_path)
    errors = Mock()
    writer = Mock(wraps=project.save_plot_positions)
    layer = PlotMarkerLayer(
        canvas, project.load_jobs(), writer, errors, current_year=2026
    )
    panel = PlotWorkerControls(layer, load_icons(), show_success=Mock())
    assert not panel.save_button.isEnabled()
    panel.save()
    panel.save_all()
    panel.preview_flags(False)
    panel.field_edited("")
    panel.select(("job", 1))
    result = saved_plot_results(project, PlotFilterSelection(SCOPE), current_year=2026)
    layer.set_results(result)
    panel.select(("worker", 1))
    assert panel.x_input.text() == "" and not layer.items and not layer.pending
    assert project.load_plot_positions() == PlotPositions("p")
    panel.visible.setChecked(True)
    assert not layer.items and layer.pending
    panel.save_all()
    assert errors.called and writer.call_count == 0
    panel.x_input.setText("0")
    panel.y_input.setText("0")
    panel.scale_input.setText("1")
    panel.save()
    assert writer.call_count == 1 and ("worker", 1) in layer.items
    assert layer.items["worker", 1].isVisible() and not layer.pending
    assert project.load_plot_positions().marker(1).point == PlotPoint(0, 0)
    panel.select(("worker", 3))
    assert panel.x_input.text() == "0" and not panel.visible.isChecked()
    panel.visible.setChecked(True)
    assert ("worker", 3) in layer.items
    panel.save_all()
    assert writer.call_count == 2 and project.load_plot_positions().marker(
        3
    ).point == PlotPoint(0, 0)
    panel.locked.setChecked(True)
    layer.cancel(("worker", 3))
    assert not panel.locked.isChecked() and not layer.pending
    result = layer.results
    assert result is not None
    layer.set_results(
        replace(result, selection=replace(result.selection, risk_view=PlotRiskView.JOB))
    )
    assert not panel.save_button.isEnabled() and not panel.save_all_button.isEnabled()
    with pytest.raises(ValueError):
        layer.save_workers((layer.worker_settings(1),))
    layer.clear()
    assert not panel.save_button.isEnabled() and panel.x_input.text() == ""
    with pytest.raises(ValueError):
        layer.worker_settings(1)
    with pytest.raises(ValueError):
        panel.selected_settings() if panel.identity is None else layer.worker_settings(
            999
        )
    panel.close()
    canvas.close()

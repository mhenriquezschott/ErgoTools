"""Original job overview selection, edit interlocks and actual saved positions.

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
from PyQt5.QtWidgets import QApplication

from ergotools.application.plot_results import saved_plot_results
from ergotools.bootstrap import load_icons
from ergotools.domain.language import Language
from ergotools.domain.plot_filters import PlotFilterSelection, PlotRiskView
from ergotools.domain.plot_positions import PlotPoint
from ergotools.domain.plot_scope import PlotScope
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.plot_job_overview import PlotJobOverview
from ergotools.presentation.desktop.plot_marker_layer import PlotMarkerLayer
from ergotools.presentation.desktop.theme.plot import PLOT_STYLE
from tests.test_plot_markers import canvas_with_map, positions_for
from tests.test_plot_results import project as project

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("language", [Language.ENGLISH, Language.SPANISH])
def test_job_overview_save_cancel_failure_and_selection(
    project: AssessmentProjectFile,
    tmp_path: Path,
    language: Language,
) -> None:
    """Original fields preserve typed drafts, finite validation and stable owners.

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
    layer = PlotMarkerLayer(
        canvas,
        project.load_jobs(),
        project.save_plot_positions,
        errors,
        current_year=2026,
        language=language,
    )
    panel = PlotJobOverview(layer, load_icons(), language=language)
    panel.setStyleSheet(PLOT_STYLE)
    panel.resize(390, 640)
    panel.show()
    result = saved_plot_results(
        project,
        PlotFilterSelection(PlotScope((("P",),)), risk_view=PlotRiskView.JOB),
        current_year=2026,
    )
    layer.set_results(result)
    assert panel.combo.count() == 2 and panel.selected_id == 1
    assert panel.values["workers"].text() == "3"
    assert panel.values["risk"].text() == "0.0%"
    assert panel.values["damage"].text() == "0.0000"
    assert panel.x_input.text() == "100.0" and not panel.save_button.isEnabled()
    panel.navigate(99)
    assert panel.selected_id == 2
    assert panel.values["risk"].text() in ("Not available", "No disponible")
    assert panel.x_input.text() == ""
    layer.select(layer.items["job", 1])
    assert panel.selected_id == 1
    QTest.mouseClick(panel.x_input, Qt.MouseButton.LeftButton)
    panel.x_input.selectAll()
    QTest.keyClicks(panel.x_input, "nan")
    assert panel.x_input.text() == "nan" and layer.pending
    assert not panel.combo.isEnabled() and not panel.navigation[2].isEnabled()
    panel.navigate(1)
    assert panel.selected_id == 1
    panel.save()
    assert errors.called and layer.pending and panel.x_input.text() == "nan"
    panel.cancel()
    assert not layer.pending and panel.x_input.text() == "100.0"
    panel.x_input.setText("0")
    panel.y_input.setText("-12.5")
    panel.coordinate_edited("0")
    layer.save_positions = Mock(side_effect=OSError("controlled failure"))
    panel.save()
    assert layer.pending and panel.x_input.text() == "0"
    layer.save_positions = project.save_plot_positions
    panel.save()
    assert not layer.pending and panel.selected_id == 1
    assert panel.x_input.text() == "0.0" and panel.y_input.text() == "-12.5"
    assert panel.combo.isEnabled()
    assert project.load_plot_positions().marker(1).point == PlotPoint(100, 100)
    marker = layer.items["job", 1]
    marker.setPos(80, 95)
    layer.moved(marker)
    assert panel.x_input.text() == "80.0"
    panel.cancel()
    assert panel.x_input.text() == "0.0"
    panel.locate()
    assert panel.timer.isActive()
    for _ in range(10):
        panel.advance_locate()
    assert not panel.timer.isActive() and marker.isSelected()
    panel.locate()
    layer.clear()
    QApplication.processEvents()
    assert not panel.timer.isActive() and not panel.save_button.isEnabled()
    assert panel.combo.count() == 0
    panel.locate()
    panel.close()
    assert not panel.timer.isActive()
    canvas.close()


def test_job_overview_empty_and_literal_values(
    project: AssessmentProjectFile,
    tmp_path: Path,
) -> None:
    """Empty controls remain disabled and literal markup cannot become rich text.

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
    panel = PlotJobOverview(layer, load_icons())
    assert not panel.combo.isEnabled() and panel.values["risk"].text() == "\u2013"
    panel.save()
    panel.cancel()
    panel.locate()
    panel.navigate(10)
    panel.selection_changed(-1)
    panel.coordinate_edited("1")
    panel.advance_locate()
    result = saved_plot_results(
        project,
        PlotFilterSelection(PlotScope((("P",),)), risk_view=PlotRiskView.JOB),
        current_year=2026,
    )
    row = result.jobs[0]
    row = replace(row, job=replace(row.job, name="<b>Literal & name</b>"))
    result = replace(result, jobs=(row,))
    layer.set_results(result)
    assert panel.values["job"].text() == "j - <b>Literal & name</b>"
    assert panel.values["job"].textFormat() == Qt.TextFormat.PlainText
    panel.marker_selected(("worker", 1))
    assert panel.selected_id == 1
    panel.close()
    canvas.close()

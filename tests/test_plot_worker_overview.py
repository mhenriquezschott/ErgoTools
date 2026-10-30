"""PLOT worker overview selection, drafts and read-only result projection.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest
from PyQt5.QtWidgets import QApplication

from ergotools.application.plot_results import saved_plot_results
from ergotools.bootstrap import load_icons
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.plot_filters import PlotFilterSelection, PlotRiskView
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.plot_marker_layer import PlotMarkerLayer
from ergotools.presentation.desktop.plot_worker_overview import PlotWorkerOverview
from tests.test_plot_markers import canvas_with_map, positions_for
from tests.test_plot_results import SCOPE
from tests.test_plot_results import project as project

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("language", [Language.ENGLISH, Language.SPANISH])
def test_worker_overview_selection_drafts_units_and_locate(
    project: AssessmentProjectFile,
    tmp_path: Path,
    language: Language,
) -> None:
    """Changing real selectors keeps assignment drafts and performs no source writes.

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
    writer = Mock(wraps=project.save_plot_positions)
    layer = PlotMarkerLayer(
        canvas, project.load_jobs(), writer, Mock(), current_year=2026
    )
    panel = PlotWorkerOverview(
        layer, load_icons(), language=language, show_success=Mock()
    )
    panel.resize(500, 740)
    panel.show()
    results = saved_plot_results(project, PlotFilterSelection(SCOPE), current_year=2026)
    layer.set_results(results)
    assert len(panel.selector.rows) == 2 and panel.selected_id == 1
    assert panel.controls.identity == 1 and panel.selector.text() == "w · Zed, Ana"
    assert panel.values["age"].text() == "26"
    assert panel.values["weight"].text() == "70"
    assert panel.values["job_risk"].text() == "0.0%"
    assert panel.values["risk"].text() != "0.0%"
    assert writer.call_count == 0 and not layer.pending
    panel.controls.x_input.setText("-20.5")
    panel.controls.field_edited("-20.5")
    panel.navigate(1)
    assert panel.selected_id == 3 and panel.controls.identity == 3
    panel.controls.x_input.setText("325")
    panel.controls.field_edited("325")
    panel.navigate(0)
    assert panel.controls.x_input.text() == "-20.5"
    panel.controls.save_all()
    assert writer.call_count == 1 and not layer.pending
    assert project.load_plot_positions().marker(1).point.x == -20.5
    assert project.load_plot_positions().marker(3).point.x == 325
    panel.toggle_order()
    assert (
        panel.selector.rows[0].assessment.assignment_id == 3 and panel.selected_id == 1
    )
    panel.set_letter("A")
    assert len(panel.selector.rows) == 1 and panel.selected_id == 3
    assert not panel.letters["B"].isEnabled()
    layer.select(layer.items["worker", 1])
    assert panel.letter == "All" and panel.selected_id == 1
    applied = layer.results
    assert applied is not None
    layer.set_results(
        replace(
            applied,
            selection=replace(applied.selection, risk_view=PlotRiskView.COMPARISON),
        )
    )
    assert panel.selected_id == 1 and panel.preview.appearance is not None
    assert panel.preview.appearance.comparison
    before = project.load_hierarchy()
    panel.system = MeasurementSystem.IMPERIAL
    panel.refresh()
    assert panel.body_labels["weight"].text().endswith("(lb):")
    assert float(panel.values["weight"].text()) == pytest.approx(154.324, rel=1e-5)
    panel.system = MeasurementSystem.METRIC
    panel.refresh()
    assert panel.values["weight"].text() == "70" and project.load_hierarchy() == before
    panel.locate()
    assert panel.timer.isActive()
    for _ in range(10):
        panel.advance_locate()
    assert not panel.timer.isActive() and layer.items["worker", 1].isSelected()
    panel.controls.visible.setChecked(False)
    assert not panel.locate_button.isEnabled()
    panel.controls.save()
    assert writer.call_count == 2
    panel.navigate(1)
    panel.locate()
    panel.close()
    assert not panel.timer.isActive()
    layer.clear()
    assert panel.selected_id is None and panel.preview.appearance is None
    canvas.close()


def test_worker_overview_missing_scientific_risk_and_literal_names(
    project: AssessmentProjectFile,
    tmp_path: Path,
) -> None:
    """Zero job evidence and unavailable worker risk never manufacture a difference.

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
    panel = PlotWorkerOverview(layer, load_icons(), show_success=Mock())
    assert not panel.locate_button.isEnabled() and not panel.navigation[0].isEnabled()
    panel.selection_changed(-1)
    panel.marker_selected(("job", 1))
    panel.navigate(20)
    panel.locate()
    panel.advance_locate()
    result = saved_plot_results(project, PlotFilterSelection(SCOPE), current_year=2026)
    row = result.workers[0]
    assert row.job_risk is not None
    row = replace(
        row,
        worker=replace(row.worker, first_name="<b>A & B</b>", last_name=None),
        assessment=replace(row.assessment, probability=None, total_damage=None),
    )
    result = replace(
        result,
        workers=(row,),
        selection=replace(result.selection, risk_view=PlotRiskView.COMPARISON),
    )
    layer.set_results(result)
    assert panel.selector.text() == "w · <b>A & B</b>"
    assert panel.values["risk"].text() == "Not available"
    assert panel.values["difference"].text() == "Not available"
    assert panel.values["job_risk"].text() == "0.0%"
    assert panel.values["job_risk"].toolTip() == "Current Job risk values"
    assert (
        panel.preview.appearance is not None
        and panel.preview.appearance.color == "#D9E1E6"
    )
    assert panel.preview.appearance.comparison
    panel.controls.select(("worker", 1))
    panel.controls.x_input.setText("nan")
    panel.controls.field_edited("nan")
    panel.refresh()
    assert panel.controls.x_input.text() == "nan"
    layer.clear()
    assert panel.controls.x_input.text() == "" and not panel.controls.field_drafts
    panel.close()
    canvas.close()

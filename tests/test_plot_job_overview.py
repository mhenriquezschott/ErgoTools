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
    assert len(panel.selector.rows) == 3 and panel.selected_id == 1
    assert panel.values["occurrences"].text() == "2"
    assert panel.values["risk"].text() == "0.0%"
    assert panel.values["damage"].text() == "0.0000"
    assert panel.x_input.text() == "100.0" and not panel.save_button.isEnabled()
    panel.navigate(99)
    assert panel.selected_id == panel.selector.rows[-1].assessment.assignment_id
    panel.selector.select_id(5)
    assert panel.selected_id == 5
    assert panel.values["risk"].text() in ("Not available", "No disponible")
    assert panel.x_input.text() == ""
    layer.select(layer.items["job", 1])
    assert panel.selected_id == 1
    QTest.mouseClick(panel.x_input, Qt.MouseButton.LeftButton)
    panel.x_input.selectAll()
    QTest.keyClicks(panel.x_input, "nan")
    assert panel.x_input.text() == "nan" and layer.pending
    assert not panel.selector.isEnabled() and not panel.navigation[2].isEnabled()
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
    assert panel.selector.isEnabled()
    assert project.load_plot_positions().marker(1).point == PlotPoint(0, -12.5)
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
    assert len(panel.selector.rows) == 0
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
    assert not panel.selector.isEnabled() and panel.values["risk"].text() == "\u2013"
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
    row = result.workers[0]
    row = replace(row, job=replace(row.job, name="<b>Literal & name</b>"))
    result = replace(result, workers=(row,))
    layer.set_results(result)
    assert panel.values["job"].text() == "j — <b>Literal & name</b>"
    assert panel.values["job"].textFormat() == Qt.TextFormat.PlainText
    panel.marker_selected(("worker", 1))
    assert panel.selected_id == 1
    panel.close()
    canvas.close()


def test_job_chart_and_mapped_count_distinguish_jobs_from_placements(
    project: AssessmentProjectFile, tmp_path: Path
) -> None:
    """Risk bars identify Jobs, while overview counts repeated visible map squares.

    Args:
        project: Disposable native source/risk repository.
        tmp_path: Temporary plant-image directory.

    Returns:
        None; changing a row's placement does not merge or drop its mapped occurrence.
    """
    from tests.test_plot_window import host

    window = host(project, tmp_path)
    try:
        window.filters.risk_buttons[PlotRiskView.JOB].click()
        results = window.layer.results
        rows = results.workers
        selected = rows[0]
        peers = tuple(row for row in rows if row.job == selected.job)
        assert len(peers) == 2
        changed = tuple(
            replace(row, placement=None) if row is peers[-1] else row for row in rows
        )
        window.layer.set_results(replace(results, workers=changed))
        window.jobs.selector.select_id(selected.assessment.assignment_id)
        assert window.jobs.values["occurrences"].text() == "2"
        labels = [
            label.get_text()
            for label in window.tools.canvas.figure.axes[0].get_yticklabels()
        ]
        assert selected.job.job_id in labels
        assert all("(" not in text for text in labels)
    finally:
        window.confirm_close = Mock(return_value=True)
        window.close()
        window.deleteLater()


@pytest.mark.parametrize("language", list(Language))
def test_job_locate_is_labeled_visible_and_centers_selected_occurrence(
    project: AssessmentProjectFile, tmp_path: Path, language: Language
) -> None:
    """Job Locate is discoverable below risk values and uses the shared zoomed locator.

    Args:
        project: Disposable native source repository.
        tmp_path: Temporary image directory.
        language: English/Spanish label and layout must remain readable.

    Returns:
        None; clicking the visible button centers/highlights the selected Job square.
    """
    from tests.test_plot_window import host

    window = host(project, tmp_path, language=language)
    try:
        window.filters.risk_buttons[PlotRiskView.JOB].click()
        window.tabs.setCurrentIndex(1)
        QApplication.processEvents()
        panel = window.jobs
        button = panel.locate_button
        assert button.text() == (
            "Localizar" if language is Language.SPANISH else "Locate"
        )
        assert button.isVisible() and button.isEnabled()
        assert button.parentWidget() is panel.values["risk"].parentWidget()
        assert button.width() > 100
        canvas = window.map_panel.canvas
        canvas.apply_zoom(3, canvas.viewport().rect().center())
        point = panel.selected_marker().sceneBoundingRect().center()
        zoom = canvas.navigation_snapshot().zoom
        saved = project.load_plot_positions()
        QTest.mouseClick(button, Qt.MouseButton.LeftButton)
        assert canvas.viewport().rect().contains(canvas.mapFromScene(point))
        assert panel.timer.isActive()
        assert canvas.navigation_snapshot().zoom == zoom
        assert project.load_plot_positions() == saved
    finally:
        window.confirm_close = Mock(return_value=True)
        window.close()
        window.deleteLater()

"""PLOT outcome summary, strict station warnings and native gauge/dialog behavior.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest
from PyQt5.QtCore import QAbstractAnimation, QPoint, QRect, Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QWidget

from ergotools.application.plot_results import PlotResults, saved_plot_results
from ergotools.application.plot_summaries import plot_highlights
from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.plot_filters import PlotFilterSelection, PlotRiskView
from ergotools.domain.plot_positions import WorkerAssignmentMarker
from ergotools.domain.plot_scope import PlotScope
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.plot_highlight_dialog import PlotHighlightDialog
from ergotools.presentation.desktop.plot_marker_layer import PlotMarkerLayer
from ergotools.presentation.desktop.plot_outcome_panel import PlotOutcomePanel
from ergotools.presentation.desktop.plot_risk_gauge import PlotRiskGauge
from tests.test_plot_markers import canvas_with_map, positions_for
from tests.test_plot_results import SCOPE
from tests.test_plot_results import project as project

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


def assert_visible_children_fit(widget: QWidget) -> None:
    """Check the complete native control bounds after real minimum-size resizing.

    Args:
        widget: Live Qt widget whose rendered geometry/visible children are inspected.

    Returns:
        None.
    """
    for child in widget.findChildren(QWidget):
        if child.isVisible():
            bounds = QRect(child.mapTo(widget, QPoint(0, 0)), child.size())
            assert widget.rect().contains(bounds), (type(child).__name__, bounds)


def risky_results(project: AssessmentProjectFile) -> PlotResults:
    """Keep real saved ownership while providing explicit warning observations.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.

    Returns:
        Saved-owner result projection with explicit controlled station warning
        probabilities; project sources remain unchanged.
    """
    result = saved_plot_results(
        project, PlotFilterSelection(PlotScope((("P",),))), current_year=2026
    )
    return replace(
        result,
        workers=tuple(
            replace(row, assessment=replace(row.assessment, probability=value))
            for row, value in (
                (row, {1: 0.7, 3: 0.5, 5: 0.9}[row.assessment.assignment_id])
                for row in result.workers
            )
        ),
    )


def test_highlights_full_station_identity_threshold_enable_and_absence(
    project: AssessmentProjectFile,
) -> None:
    """Equal station IDs on different lines never merge; exact 50% is not high risk.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.

    Returns:
        None.
    """
    result = risky_results(project)
    details = plot_highlights(result)
    assert len(details) == 2 and [row.count for row in details] == [1, 1]
    assert [row.station.section_name for row in details] == ["S", "T"]
    assert [row.average_percent for row in details] == [70, 90]
    assert details[1].maximum_percent == 90
    hidden = replace(
        result,
        positions=replace(
            result.positions, workers=(WorkerAssignmentMarker(1, visible=False),)
        ),
    )
    assert plot_highlights(hidden) == details
    disabled = replace(
        result,
        positions=replace(
            result.positions, workers=(WorkerAssignmentMarker(1, enabled=False),)
        ),
    )
    assert plot_highlights(disabled) == (details[1],)
    missing = replace(
        result,
        workers=tuple(
            replace(row, assessment=replace(row.assessment, probability=None))
            for row in result.workers
        ),
    )
    assert not plot_highlights(missing)
    invalid = replace(
        result,
        workers=(
            replace(
                result.workers[0],
                assessment=replace(
                    result.workers[0].assessment, probability=float("nan")
                ),
            ),
        ),
    )
    with pytest.raises(ValueError, match="finite percentages"):
        plot_highlights(invalid)
    job = replace(
        result, selection=replace(result.selection, risk_view=PlotRiskView.JOB)
    )
    assert not plot_highlights(job)  # Approved zero; missing profile is not evidence.
    evidence = job.jobs[0].risk
    high = replace(
        evidence, measurement=replace(evidence.measurement, probability_percent=75)
    )
    job = replace(job, jobs=(replace(job.jobs[0], risk=high), job.jobs[1]))
    assert plot_highlights(job)[0].average_percent == 75
    assert project.load_plot_positions() == result.positions


def test_plot_gauge_animation_missing_clamp_and_invalid_values() -> None:
    """Original easing clears absence immediately and never restarts a target.

    Args:
        None.

    Returns:
        None.
    """
    gauge = PlotRiskGauge()
    gauge.resize(250, 120)
    gauge.show()
    gauge.set_probability(60)
    gauge.animation.setCurrentTime(350)
    middle = gauge.display_value
    assert 0 < middle < 60
    gauge.set_probability(60)
    assert gauge.animation.currentTime() == 350
    gauge.set_probability(80)
    assert gauge.animation.startValue() == middle
    gauge.animation.setCurrentTime(700)
    assert gauge.display_value == 80
    assert not gauge.grab().isNull()
    gauge.set_probability(0)
    assert gauge.has_value
    gauge.set_probability(None)
    assert not gauge.has_value and gauge.display_value == 0
    assert gauge.animation.state() == QAbstractAnimation.State.Stopped
    for value in (float("nan"), float("inf"), True):
        with pytest.raises(ValueError, match="finite percentage"):
            gauge.set_probability(value)
    gauge.set_probability(200)
    assert gauge.target_value == 100
    gauge.set_probability(-5)
    assert gauge.target_value == 0
    gauge.animation.stop()
    gauge.close()


@pytest.mark.parametrize("language", list(Language))
def test_outcome_modes_saved_membership_modal_details_and_clear(
    project: AssessmentProjectFile, tmp_path: Path, language: Language
) -> None:
    """Real warning details and saved gauges do not write or consume marker previews.

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
    panel = PlotOutcomePanel(layer, load_icons(), language=language)
    panel.resize(1500, 210)
    panel.show()
    _APP.processEvents()
    assert panel.summary is None and not panel.gauge.has_value
    assert panel.details_button.isHidden()
    panel.open_details()
    result = risky_results(project)
    layer.set_results(result)
    assert panel.gauge.target_value == 70 and len(panel.highlights) == 2
    assert not panel.details_button.isHidden()
    assert "70.0%" in panel.metrics[9].text()
    before = panel.summary
    layer.preview_worker(replace(result.positions.marker(1), enabled=False))
    assert panel.summary is before and panel.gauge.target_value == 70
    assert writer.call_count == 0
    assert layer.save_workers(tuple(layer.worker_drafts.values()))
    assert writer.call_count == 1 and panel.gauge.target_value == 70
    assert panel.summary.workers.total == 2 and len(panel.highlights) == 1
    saved = layer.results
    comparison = replace(
        saved, selection=replace(saved.selection, risk_view=PlotRiskView.COMPARISON)
    )
    layer.set_results(comparison)
    assert panel.stack.currentIndex() == 1 and panel.ranges.width() == 250
    assert panel.stack.width() == 450
    assert panel.individual_gauge.target_value == 70
    assert panel.job_gauge.target_value == 0 and panel.job_gauge.has_value
    assert "+50.0" in panel.metrics[9].text()  # Only Ben has a comparable profile.
    errors, visited = [], []

    def inspect_details() -> None:
        """Inspect the actual station highlight row, exact 90.0% risk.

        Inspect the actual station highlight row, exact 90.0% risk and selection
        behavior, close its native button and surface callback failures.

        Args:
            None.

        Returns:
            None.
        """
        modal = QApplication.activeModalWidget()
        try:
            assert isinstance(modal, PlotHighlightDialog)
            visited.append(modal)
            assert modal.table.topLevelItemCount() == 1
            row = modal.table.topLevelItem(0)
            assert row.text(0) == "1" and "T" in row.toolTip(0)
            assert row.text(2) == "90.0%"
            modal.table.setCurrentItem(row)
            assert row.isSelected()
            QTest.mouseClick(modal.close_button, Qt.MouseButton.LeftButton)
        except BaseException as error:
            errors.append(error)
            if modal is not None:
                modal.reject()

    QTimer.singleShot(0, inspect_details)
    QTest.mouseClick(panel.details_button, Qt.MouseButton.LeftButton)
    assert not errors and len(visited) == 1 and writer.call_count == 1
    panel.resize(700, 210)
    _APP.processEvents()
    assert panel.width() >= panel.layout().minimumSize().width()
    assert_visible_children_fit(panel)
    job = replace(saved, selection=replace(saved.selection, risk_view=PlotRiskView.JOB))
    layer.set_results(job)
    assert panel.stack.currentIndex() == 0 and panel.gauge.has_value
    assert panel.gauge.target_value == 0 and not panel.individual_gauge.has_value
    assert "2" in panel.metrics[0].text() and "0.0%" in panel.metrics[6].text()
    assert panel.details_button.isHidden()
    _APP.processEvents()
    assert_visible_children_fit(panel)
    layer.set_results(
        replace(job, jobs=tuple(replace(row, risk=None) for row in job.jobs))
    )
    assert not panel.gauge.has_value and "\u2013" in panel.metrics[6].text()
    _APP.processEvents()
    assert panel.highlight_label.height() >= panel.highlight_label.heightForWidth(
        panel.highlight_label.width()
    )
    assert_visible_children_fit(panel)
    layer.set_results(replace(saved, workers=(), all_tools=(), jobs=()))
    assert not panel.gauge.has_value and not panel.highlights
    assert panel.details_button.isHidden() and "0" in panel.metrics[0].text()
    layer.clear()
    assert panel.summary is None and not panel.gauge.has_value
    panel.close()
    for gauge in (panel.gauge, panel.individual_gauge, panel.job_gauge):
        assert gauge.animation.state() == QAbstractAnimation.State.Stopped
    canvas.close()


@pytest.mark.parametrize("language", list(Language))
def test_unavailable_worker_evidence_and_literal_station_details(
    project: AssessmentProjectFile, tmp_path: Path, language: Language
) -> None:
    """Missing outcomes stay absent and literal station IDs remain plain text.

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
    canvas = canvas_with_map(tmp_path)
    layer = PlotMarkerLayer(
        canvas, project.load_jobs(), Mock(), Mock(), current_year=2026
    )
    panel = PlotOutcomePanel(layer, load_icons(), language=language)
    result = saved_plot_results(
        project, PlotFilterSelection(SCOPE, tool=AssessmentKind.TST), current_year=2026
    )
    result = replace(
        result,
        workers=tuple(
            replace(
                row,
                assessment=replace(row.assessment, probability=None, total_damage=None),
            )
            for row in result.workers
        ),
    )
    layer.set_results(result)
    assert panel.summary.workers.total == 2 and not panel.gauge.has_value
    assert panel.title() in ("Shoulder Tool Outcome", "Resultado de Hombro")
    assert not panel.highlights and panel.details_button.isHidden()
    details = plot_highlights(risky_results(project))
    dialog = PlotHighlightDialog(
        details, AssessmentKind.LIFFT, load_icons(), language=language
    )
    assert dialog.table.topLevelItemCount() == 2
    assert dialog.table.topLevelItem(0).text(0) == "P / S / L / 1"
    assert dialog.table.topLevelItem(1).text(0) == "P / T / L / 1"
    literal = replace(
        details[0], station=replace(details[0].station, station_id="<b>A & B</b>")
    )
    dialog.close()
    dialog = PlotHighlightDialog(
        (literal,), AssessmentKind.TST, load_icons(), job_view=True, language=language
    )
    assert dialog.table.topLevelItem(0).text(0) == "<b>A & B</b>"
    assert "70.0%" in dialog.table.topLevelItem(0).toolTip(2)
    dialog.close()
    panel.close()
    canvas.close()

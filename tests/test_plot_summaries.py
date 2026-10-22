"""PLOT summary membership, available evidence, paired comparison and chart data.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from pathlib import Path

import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg

from ergotools.application.plot_results import saved_plot_results
from ergotools.application.plot_summaries import risk_average, summarize_plot
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.plot_filters import PlotFilterSelection
from ergotools.domain.plot_positions import WorkerAssignmentMarker
from ergotools.domain.plot_scope import PlotScope
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.plot_summary_figure import PlotChart, summary_figure
from tests.test_plot_markers import positions_for
from tests.test_plot_results import project as project


def test_summary_observations_population_deviation_and_missing_evidence(
    project: AssessmentProjectFile,
) -> None:
    """Unknown risk is absent, observed zero is real, and paired populations agree.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.

    Returns:
        None.
    """
    results = saved_plot_results(
        project, PlotFilterSelection(PlotScope((("P",),))), current_year=2026
    )
    first, second, third = results.workers
    assert first.job_risk is not None
    first = replace(
        first, assessment=replace(first.assessment, probability=0.2, total_damage=2)
    )
    second = replace(
        second,
        assessment=replace(second.assessment, probability=0.8, total_damage=4),
        job_risk=None,
    )
    third = replace(
        third, assessment=replace(third.assessment, probability=None, total_damage=None)
    )
    result = replace(results, workers=(first, second, third))
    summary = summarize_plot(result, current_year=2026)
    assert summary.workers.total == 3
    assert summary.workers.risk.count == 2
    assert summary.workers.risk.mean_percent == 50
    assert summary.workers.risk.deviation_percent == 30
    assert summary.workers.damage == 3
    assert summary.workers.comparable_count == 1
    assert summary.workers.difference_percentage_points == 20
    assert summary.workers.applicable_job_risk_percent == 0
    assert summary.workers.average_age == 26
    assert summary.workers.male_risk.mean_percent is None
    assert risk_average((0,)).mean_percent == 0
    assert risk_average(()).deviation_percent is None
    for values in ((float("nan"),), (float("inf"),), (-1,), (101,), (True,)):
        with pytest.raises(ValueError, match="finite percentages"):
            risk_average(values)
    with pytest.raises(ValueError, match="positive integer"):
        summarize_plot(result, current_year=True)
    assert (
        summarize_plot(replace(result, workers=()), current_year=2026).workers.total
        == 0
    )


def test_summary_enabled_assignment_and_all_tool_age_groups(
    project: AssessmentProjectFile,
) -> None:
    """Hidden/unplaced inclusion is independent of saved enable and source units.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.

    Returns:
        None.
    """
    results = saved_plot_results(
        project, PlotFilterSelection(PlotScope((("P",),))), current_year=2026
    )
    positions = replace(
        results.positions, workers=(WorkerAssignmentMarker(1, enabled=False),)
    )
    result = replace(results, positions=positions)
    summary = summarize_plot(result, current_year=2026)
    assert summary.workers.total == 2
    assert tuple(group.risk.count for group in summary.tools) == (2, 2, 2)
    assert all(group.group == "20-29" for group in summary.ages)
    assert all(
        group.risk.mean_percent is None
        for group in summary.sexes
        if group.group == "Male"
    )
    sources = tuple(
        replace(row, assessment=replace(row.assessment, units=MeasurementSystem.METRIC))
        for row in result.workers
    )
    assert (
        summarize_plot(replace(result, workers=sources), current_year=2026) == summary
    )
    assert project.load_plot_positions() == results.positions
    # No known age clears age chart data rather than retaining a previous chart.
    rows = tuple(
        replace(row, worker=replace(row.worker, details=None))
        for row in result.all_tools
    )
    assert not summarize_plot(replace(result, all_tools=rows), current_year=2026).ages


def test_job_summary_placement_weighting_positions_and_no_evidence(
    project: AssessmentProjectFile,
) -> None:
    """Zero approved job risk remains observed; absence changes no denominator.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.

    Returns:
        None.
    """
    positions_for(project)
    results = saved_plot_results(
        project, PlotFilterSelection(PlotScope((("P",),))), current_year=2026
    )
    summary = summarize_plot(results, current_year=2026)
    assert summary.jobs.unique_jobs == 2 and summary.jobs.placements == 2
    assert summary.jobs.positioned_stations == 1
    assert summary.jobs.unpositioned_stations == 1
    assert summary.jobs.jobs_with_risks == 1
    assert summary.jobs.risk.count == 1 and summary.jobs.risk.mean_percent == 0
    assert summary.jobs.minimum_risk_percent == summary.jobs.maximum_risk_percent == 0
    assert summary.placed_jobs[0].risk_percent == 0
    assert summary.placed_jobs[1].risk_percent is None
    original = results.jobs[0]
    duplicate = replace(
        original, placement=replace(original.placement, placement_id=77)
    )
    repeated = summarize_plot(
        replace(results, jobs=(original, duplicate)), current_year=2026
    )
    assert repeated.jobs.unique_jobs == 1 and repeated.jobs.risk.count == 2
    assert repeated.placed_jobs[0].placement_count == 2
    empty = summarize_plot(replace(results, jobs=()), current_year=2026)
    assert empty.jobs.damage is None and empty.jobs.risk.count == 0


@pytest.mark.parametrize("language", list(Language))
def test_source_charts_render_all_modes_and_clear_missing_data(
    project: AssessmentProjectFile,
    tmp_path: Path,
    language: Language,
) -> None:
    """Owned figures retain source labels/scales without any fabricated zero bar.

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
    results = saved_plot_results(
        project, PlotFilterSelection(PlotScope((("P",),))), current_year=2026
    )
    summary = summarize_plot(results, current_year=2026)
    for chart in PlotChart:
        figure = summary_figure(summary, chart, language=language)
        canvas = FigureCanvasAgg(figure)
        canvas.print_png(tmp_path / f"{language}-{chart}.png")
        axis = figure.axes[0]
        assert (
            axis.get_xlim() == (0, 100)
            if chart is PlotChart.JOB
            else axis.get_ylim() == (0, 100)
        )
        assert axis.get_title()
        assert not any(line.get_visible() for line in axis.get_xgridlines())
        if chart is PlotChart.TOOL:
            assert len(axis.patches) == 3  # All three tools now have saved evidence.
        if chart is PlotChart.JOB:
            assert len(axis.patches) == 1 and axis.patches[0].get_width() == 0
        figure.clear()
    empty = summarize_plot(
        replace(results, workers=(), all_tools=(), jobs=()), current_year=2026
    )
    for chart in PlotChart:
        figure = summary_figure(empty, chart, language=language)
        assert not figure.axes[0].patches and figure.axes[0].texts
        FigureCanvasAgg(figure).draw()
        figure.clear()

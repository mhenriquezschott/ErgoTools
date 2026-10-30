"""Job-only PLOT glyphs mirror Comparison assignment geometry without new storage.

Tests cover selected tools, demographics, hidden/unplaced slots, missing Job risks,
repeat Jobs and shared edit/history boundaries using disposable native projects.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest

from ergotools.application.plot_results import saved_plot_results
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.job_catalog import WorkerJobAssignment
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.plot_filters import (
    PlotDemographics,
    PlotFilterSelection,
    PlotRiskView,
)
from ergotools.domain.plot_positions import (
    PlotPoint,
    WorkerAssignmentMarker,
    WorkerPositionSource,
)
from ergotools.domain.work_catalog import WorkerEntry
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.plot_marker_layer import PlotMarkerLayer
from tests.test_plot_markers import canvas_with_map, positions_for
from tests.test_plot_results import SCOPE
from tests.test_plot_results import project as project


@pytest.mark.parametrize("kind", list(AssessmentKind))
@pytest.mark.parametrize("female_only", [False, True])
def test_job_and_comparison_share_exact_slot_geometry(
    project: AssessmentProjectFile,
    tmp_path: Path,
    kind: AssessmentKind,
    female_only: bool,
) -> None:
    """Mode switches alter appearance only, including repeated Job IDs and filters.

    Args:
        project: Disposable source and risk repository.
        tmp_path: Temporary synthetic plant image directory.
        kind: Each selected scientific tool; missing Job risks stay unavailable.
        female_only: Apply the same demographic predicate to both result populations.

    Returns:
        None; exact points, size, scale, flags and selected model's Job color match.
    """
    positions_for(project)
    canvas = canvas_with_map(tmp_path)
    layer = PlotMarkerLayer(
        canvas,
        project.load_jobs(),
        project.save_plot_positions,
        Mock(),
        current_year=2026,
    )
    selection = PlotFilterSelection(
        SCOPE,
        tool=kind,
        risk_view=PlotRiskView.COMPARISON,
        demographics=PlotDemographics(enabled=female_only, sex="Female"),
    )
    comparison = saved_plot_results(project, selection, current_year=2026)
    before = (
        project.load_plot_positions(),
        project.load_job_risk(),
        project.load_history(),
    )
    layer.set_results(comparison)
    frames = {
        identity: (
            item.anchor_point(),
            item.size,
            item.marker_scale,
            item.appearance.job_color,
            item.isEnabled(),
        )
        for (_, identity), item in layer.items.items()
    }
    job_result = saved_plot_results(
        project, replace(selection, risk_view=PlotRiskView.JOB), current_year=2026
    )
    layer.set_results(job_result)
    assert {identity for _, identity in layer.items} == set(frames)
    for (_, identity), item in layer.items.items():
        point, size, scale, color, enabled = frames[identity]
        assert (
            item.anchor_point(),
            item.size,
            item.marker_scale,
            item.appearance.color,
            item.isEnabled(),
        ) == (point, size, scale, color, enabled)
        assert item.appearance.shape == "job" and not item.appearance.comparison
        assert item.appearance.label == "j"
        assert "Individual Risk" not in item.toolTip()
    assert (
        project.load_plot_positions(),
        project.load_job_risk(),
        project.load_history(),
    ) == before
    canvas.close()
    canvas.deleteLater()


def test_missing_job_and_hidden_positions_remain_explicit(
    project: AssessmentProjectFile, tmp_path: Path
) -> None:
    """No Job becomes a neutral labeled slot; hidden/unplaced rows create no square.

    Args:
        project: Disposable assigned assessments with optional Job linkage.
        tmp_path: Temporary plant image directory.

    Returns:
        None; moving in Job mode survives a Comparison switch at the identical point.
    """
    positions = positions_for(project)
    jobs = project.load_jobs()
    hierarchy = project.load_hierarchy()
    work = replace(
        hierarchy.work,
        workers=(*hierarchy.work.workers, WorkerEntry("no-job", "Nora", "Ruiz")),
    )
    project.save_hierarchy(replace(hierarchy, work=work))
    owner = work.worker_context("no-job", jobs.assignments[0].worker.workplace)
    jobs = replace(
        jobs, assignments=(*jobs.assignments, WorkerJobAssignment(6, owner, None))
    )
    project.save_jobs(jobs)
    project.create_historical_assessment(
        AssignmentAssessment("no-job-lifft", 6, AssessmentKind.LIFFT, "no-job"),
        LifftDraft(MeasurementSystem.METRIC, (LifftTask("task", 30, 49, 100),)),
    )
    marker = positions.marker(3)
    positions = replace(
        positions, workers=tuple(replace(m, visible=False) for m in positions.workers)
    )
    positions = positions.with_saved_marker(
        WorkerAssignmentMarker(
            6, PlotPoint(40, 50), visible=True, source=WorkerPositionSource.MANUAL
        ),
        jobs,
    )
    project.save_plot_positions(positions)
    canvas = canvas_with_map(tmp_path)
    layer = PlotMarkerLayer(
        canvas,
        project.load_jobs(),
        project.save_plot_positions,
        Mock(),
        current_year=2026,
    )
    result = saved_plot_results(
        project,
        PlotFilterSelection(SCOPE, risk_view=PlotRiskView.JOB),
        current_year=2026,
    )
    layer.set_results(result)
    assert set(layer.items) == {("job", 6)}
    item = layer.items["job", 6]
    assert item.appearance.label == "—" and item.appearance.color == "#D9E1E6"
    assert item.appearance.job_probability is None
    item.setPos(0, -12.3456789)
    layer.moved(item)
    assert layer.save(("job", 6))
    assert project.load_plot_positions().marker(6).point == PlotPoint(0, -12.3456789)
    comparison = saved_plot_results(
        project,
        replace(result.selection, risk_view=PlotRiskView.COMPARISON),
        current_year=2026,
    )
    layer.set_results(comparison)
    assert set(layer.items) == {("worker", 6)}
    assert layer.items["worker", 6].anchor_point() == PlotPoint(0, -12.3456789)
    assert project.load_plot_positions().marker(3) == replace(marker, visible=False)
    canvas.close()
    canvas.deleteLater()


def test_job_map_counts_follow_visibility_without_recalculating_scope(
    project: AssessmentProjectFile, tmp_path: Path
) -> None:
    """Map counts follow shared visibility while placement statistics stay fixed.

    Args:
        project: Disposable native project with positioned assignments.
        tmp_path: Temporary plant-image directory.

    Returns:
        None; hiding and restoring one assignment changes only displayed map counts.
    """
    from tests.test_plot_window import host

    window = host(project, tmp_path)
    try:
        window.filters.risk_buttons[PlotRiskView.JOB].click()
        panel = window.outcome
        summary = panel.summary
        count = len(window.layer.items)
        assert panel.metrics[2].text().endswith(str(count))
        marker = window.layer.worker_settings(1)
        window.layer.preview_worker(replace(marker, visible=False))
        assert panel.summary is summary
        assert panel.metrics[2].text().endswith(str(count - 1))
        window.layer.preview_worker(marker)
        assert panel.metrics[2].text().endswith(str(count))
        window.layer.cancel(("job", 1))
        window.layer.set_results(replace(window.layer.results, workers=()))
        assert not window.jobs.selector.isEnabled()
        assert not window.jobs.values["risk"].styleSheet()
        assert not window.jobs.values["damage"].styleSheet()
    finally:
        window.confirm_close = Mock(return_value=True)
        window.close()
        window.deleteLater()


def test_job_tooltip_names_real_job_and_worker_without_duplicate_or_footer(
    project: AssessmentProjectFile, tmp_path: Path
) -> None:
    """Job tooltip names the Job and worker without duplicate IDs or a footer.

    Args:
        project: Disposable native project with positioned Job assignments.
        tmp_path: Temporary image directory.

    Returns:
        None; explanatory position footer is removed and stored names remain literal.
    """
    from tests.test_plot_window import host

    window = host(project, tmp_path)
    try:
        window.filters.risk_buttons[PlotRiskView.JOB].click()
        results = window.layer.results
        row = results.workers[0]
        assert row.job is not None
        for name in ("Packing", row.job.job_id):
            changed = replace(row, job=replace(row.job, name=name))
            window.layer.set_results(replace(results, workers=(changed,)))
            tooltip = window.layer.items["job", row.assessment.assignment_id].toolTip()
            caption = row.job.job_id + (f" — {name}" if name != row.job.job_id else "")
            assert f"Job: {caption}" in tooltip
            assert f"Job: {row.job.job_id} — {row.job.job_id}" not in tooltip
            assert f"Worker: {row.worker.worker_id}" in tooltip
            assert "Position shared" not in tooltip and "Map assignment:" not in tooltip
    finally:
        window.confirm_close = Mock(return_value=True)
        window.close()
        window.deleteLater()

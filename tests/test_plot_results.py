"""Saved PLOT dataset ownership, exact scope, profile joins and Apply isolation.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest

from ergotools.application.assessment_export import saved_assessment_summary
from ergotools.application.assessments.evaluation import EvaluationStatus
from ergotools.application.plot_results import PlotWorkerOrder, saved_plot_results
from ergotools.application.session import DocumentKey
from ergotools.bootstrap import load_icons
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.job_catalog import (
    Job,
    JobCatalog,
    JobPlacement,
    WorkerJobAssignment,
)
from ergotools.domain.job_risk import JobRiskMeasurement, JobRiskValues
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.plot_filters import PlotDemographics, PlotFilterSelection
from ergotools.domain.plot_scope import PlotScope
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy
from ergotools.domain.worker_details import WorkerDetails
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.plot_results import load_plot_results
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.plot_filters_panel import PlotFiltersPanel
from ergotools.presentation.desktop.plot_map_panel import PlotMapPanel
from tests.test_saved_tool_data import window as window

# Explicit synthetic project identity/title/default units; assessment units are
# preserved independently.
META = ProjectMetadata("p", "PLOT results", MeasurementSystem.IMPERIAL)
# Exact synthetic P/S/L PLOT prefix and literal All shift; the label is a stored shift
# identity here.
SCOPE = PlotScope((("P", "S", "L"),), "All")


@pytest.fixture
def project(tmp_path: Path) -> Iterator[AssessmentProjectFile]:
    """Seed exact duplicate station labels, literal All shift and saved versions.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Yields:
        Owned temporary native project seeded with exact catalogs/current versions;
        fixture cleanup closes its connection.
    """
    stations = (StationKey("P", "S", "L", "1"), StationKey("P", "T", "L", "1"))
    workers = (
        WorkerEntry(
            "w",
            "Ana",
            "Zed",
            WorkerDetails(birth_date="2000-12-31", sex="Female", weight_kg=70),
        ),
        WorkerEntry("x", "Ben", "Alpha"),
        WorkerEntry("z"),
    )
    hierarchy = WorkHierarchy(
        WorkCatalog("p", workers, stations, ("All", "Day")),
        ("P", "Empty"),
        (SectionKey("P", "S"), SectionKey("P", "T")),
        (LineKey("P", "S", "L"), LineKey("P", "T", "L")),
    )
    place = stations[0].at_shift("All")
    other = stations[1].at_shift("Day")
    jobs = JobCatalog(
        "p",
        (Job("j", "Job"), Job("k", "No profile")),
        (JobPlacement(1, "j", place), JobPlacement(2, "k", other)),
        (
            WorkerJobAssignment(1, hierarchy.work.worker_context("w", place), 1),
            WorkerJobAssignment(
                2,
                hierarchy.work.worker_context("w", place),
                1,
                active=False,
            ),
            WorkerJobAssignment(3, hierarchy.work.worker_context("x", place), 1),
            WorkerJobAssignment(4, hierarchy.work.worker_context("z", place), 1),
            WorkerJobAssignment(5, hierarchy.work.worker_context("w", other), 2),
        ),
    )
    with AssessmentProjectFile.create_with_job_risks(
        tmp_path / "plot.ergprj", META
    ) as repository:
        repository.save_hierarchy(hierarchy)
        repository.save_jobs(jobs)
        for assignment in (1, 2, 3, 5):
            for kind, source in (
                (
                    AssessmentKind.LIFFT,
                    LifftDraft(
                        MeasurementSystem.IMPERIAL,
                        (LifftTask("l", 12, 20, assignment * 100), LifftTask("empty")),
                    ),
                ),
                (AssessmentKind.DUET, DuetDraft((DuetTask("d", 6, 100),))),
                (
                    AssessmentKind.TST,
                    TstDraft(
                        MeasurementSystem.IMPERIAL,
                        (TstTask("s", TstDirection.DOWNWARD, 12, 20, 100),),
                    ),
                ),
            ):
                repository.create_historical_assessment(
                    AssignmentAssessment(
                        f"{kind}-{assignment}",
                        assignment,
                        kind,
                        worker_id=next(
                            a.worker.worker_id
                            for a in jobs.assignments
                            if a.assignment_id == assignment
                        ),
                    ),
                    source,
                )
        with pytest.raises(ValueError, match="assignment/tool"):
            repository.create_historical_assessment(
                AssignmentAssessment(
                    "old",
                    1,
                    AssessmentKind.LIFFT,
                    worker_id=next(
                        a.worker.worker_id
                        for a in jobs.assignments
                        if a.assignment_id == 1
                    ),
                ),
                LifftDraft(MeasurementSystem.IMPERIAL),
            )
        repository.save_job_details(
            repository.load_jobs(),
            repository.load_job_risk(),
            repository.load_jobs().jobs[0],
            JobRiskValues(
                "j",
                (
                    JobRiskMeasurement(AssessmentKind.LIFFT, 0, 0, "Imperial"),
                    JobRiskMeasurement(AssessmentKind.DUET, 2, None, "Metric"),
                ),
            ),
        )
        yield repository


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_current_active_sources_and_missing_job_values(
    project: AssessmentProjectFile,
    kind: AssessmentKind,
) -> None:
    """Closed/noncurrent rows stay out; partial/review and zero are not conflated.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
            captions are not keys.

    Returns:
        None.
    """
    before = (project.load_history(), project.load_jobs(), project.load_job_risk())
    result = saved_plot_results(
        project,
        PlotFilterSelection(SCOPE, kind),
        current_year=2026,
    )
    assert [row.assessment.assignment_id for row in result.workers] == [1, 3]
    assert len(result.all_tools) == 6
    assert all(row.assessment.assignment_active for row in result.all_tools)
    assert all(row.assessment.document.document_id != "old" for row in result.all_tools)
    assert len(result.jobs) == 1 and result.jobs[0].assigned_worker_count == 3
    row = result.workers[0]
    if kind is AssessmentKind.LIFFT:
        assert row.assessment.status is EvaluationStatus.COMPLETE
        assert row.assessment.total_damage > 0 and row.assessment.probability > 0
        assert row.job_risk.measurement.cumulative_damage == 0
        assert row.job_risk.measurement.probability_percent == 0
    elif kind is AssessmentKind.DUET:
        assert row.assessment.status is EvaluationStatus.COMPLETE
        assert row.job_risk is None
    else:
        assert row.assessment.status in (
            EvaluationStatus.COMPLETE,
            EvaluationStatus.PARTIAL,
        )
        assert (
            row.assessment.total_damage is not None
            and row.assessment.probability is not None
        )
        assert row.job_risk is None and result.jobs[0].risk is None
    assert before == (
        project.load_history(),
        project.load_jobs(),
        project.load_job_risk(),
    )


def test_scope_demographics_counts_and_binary_order(
    project: AssessmentProjectFile,
) -> None:
    """Exact ancestry and literal shifts never collapse identities or job counts.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.

    Returns:
        None.
    """
    filtered = saved_plot_results(
        project,
        PlotFilterSelection(
            SCOPE,
            demographics=PlotDemographics(True, "Female", (26, 26), (70, 70)),
        ),
        current_year=2026,
    )
    assert [row.worker.worker_id for row in filtered.workers] == ["w"]
    assert len(filtered.all_tools) == 3 and filtered.jobs[0].assigned_worker_count == 3
    assert (
        len(
            saved_plot_results(
                project,
                PlotFilterSelection(PlotScope((("P",),))),
                current_year=2026,
            ).workers
        )
        == 3
    )
    exact = saved_plot_results(
        project,
        PlotFilterSelection(PlotScope((("P", "T", "L", "1"),), "Day")),
        current_year=2026,
    )
    assert [row.assessment.assignment_id for row in exact.workers] == [5]
    assert exact.jobs[0].job.job_id == "k" and exact.jobs[0].risk is None
    assert (
        saved_plot_results(
            project,
            PlotFilterSelection(PlotScope((("P", "T"),), "All")),
            current_year=2026,
        ).workers
        == ()
    )
    assert (
        saved_plot_results(
            project,
            PlotFilterSelection(PlotScope((("Empty",),))),
            current_year=2026,
        ).jobs
        == ()
    )
    ordered = saved_plot_results(
        project,
        PlotFilterSelection(SCOPE),
        current_year=2026,
        order=PlotWorkerOrder.LAST_NAME,
    )
    assert [row.worker.worker_id for row in ordered.workers] == ["x", "w"]


def test_inactive_placement_job_and_cleared_values(
    project: AssessmentProjectFile,
) -> None:
    """Worker inclusion follows assignment activity, separately from job inclusion.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.

    Returns:
        None.
    """
    jobs = project.load_jobs()
    project.replace_jobs(
        jobs,
        replace(
            jobs,
            placements=(replace(jobs.placements[0], active=False), jobs.placements[1]),
        ),
    )
    results = saved_plot_results(project, PlotFilterSelection(SCOPE), current_year=2026)
    assert len(results.workers) == 2 and not results.jobs
    assert results.workers[0].job_risk is not None
    jobs = project.load_jobs()
    project.replace_jobs(
        jobs,
        replace(jobs, jobs=(replace(jobs.jobs[0], active=False), jobs.jobs[1])),
    )
    results = saved_plot_results(project, PlotFilterSelection(SCOPE), current_year=2026)
    assert len(results.workers) == 2 and results.workers[0].job_risk is None
    project.save_job_details(
        project.load_jobs(),
        project.load_job_risk(),
        project.load_jobs().jobs[0],
        JobRiskValues("j"),
    )
    assert (
        saved_plot_results(
            project,
            PlotFilterSelection(SCOPE),
            current_year=2026,
        )
        .workers[0]
        .job_risk
        is None
    )


def test_validation_precedes_source_reads(project: AssessmentProjectFile) -> None:
    """Unavailable scopes, wrong projects/models and source failures remain errors.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.

    Returns:
        None.
    """
    repository = Mock(wraps=project)
    repository.metadata = project.metadata
    for year in (True, 0):
        with pytest.raises(ValueError):
            saved_plot_results(
                repository, PlotFilterSelection(SCOPE), current_year=year
            )
    with pytest.raises(ValueError):
        saved_plot_results(
            repository,
            PlotFilterSelection(SCOPE),
            current_year=2026,
            order="worker_id",
        )
    repository.load_hierarchy.assert_not_called()
    with pytest.raises(ValueError):
        saved_plot_results(
            repository,
            PlotFilterSelection(PlotScope((("Missing",),))),
            current_year=2026,
        )
    repository.load.assert_not_called()
    repository.load_job_risk.return_value = replace(
        project.load_job_risk(),
        project_id="foreign",
    )
    with pytest.raises(ValueError):
        saved_plot_results(repository, PlotFilterSelection(SCOPE), current_year=2026)
    repository.load.assert_not_called()
    entry = project.load_history().entries[0]
    assignment = project.load_jobs().assignments[0]
    with pytest.raises(ValueError):
        saved_assessment_summary(META, entry, assignment, DuetDraft())
    with pytest.raises(ValueError):
        saved_assessment_summary(
            META,
            entry,
            replace(assignment, assignment_id=99),
            project.load(DocumentKey("p", entry.document_id)),
        )


def test_actual_apply_saved_data_and_failure_preserve_edits(
    window: LifftWindow,
    project: AssessmentProjectFile,
    tmp_path: Path,
) -> None:
    """Apply reads disk, retains pending inputs and publishes only success.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    location = str(tmp_path / "plot.ergprj")
    before = Path(location).read_bytes()
    active = window.presenter.workspace.active
    field = window.task_panel.inputs[0][2]
    field.setText("bad")
    field.textEdited.emit("bad")
    hierarchy = project.load_hierarchy()
    map_panel = PlotMapPanel(
        hierarchy,
        project,
        project,
        Mock(),
        load_icons(),
    )
    published = []

    def apply(selection: PlotFilterSelection) -> bool:
        """Read actual saved PLOT results for the supplied selection.

        Read actual saved PLOT results for the supplied selection, record the complete
        projection and report accepted publication.

        Args:
            selection: Immutable exact PLOT scope/tool/risk/demographic intent supplied
                to the test publication callback.

        Returns:
            True after recording the applied selection and its matching result
            projection.
        """
        results = load_plot_results(location, selection, current_year=2026)
        published.append(results)
        return True

    filters = PlotFiltersPanel(hierarchy, map_panel, load_icons(), apply)
    assert filters.workplace.set_scope(SCOPE)
    filters.apply_button.click()
    assert len(published[0].workers) == 2 and len(published[0].all_tools) == 6
    prior = filters.applied
    filters.demographics.setChecked(True)
    filters.sex.setCurrentIndex(filters.sex.findData("Female"))
    filters.apply_button.click()
    assert len(published[-1].workers) == 1
    prior = filters.applied
    filters.map_panel.show_error = Mock()
    filters.apply_selection = Mock(side_effect=OSError("controlled read failure"))
    filters.apply_button.click()
    assert filters.applied is prior and len(published) == 2
    assert filters.map_panel.show_error.called
    filters.clear_button.click()
    assert len(published) == 2
    assert field.text() == "bad" and window.task_panel.pending
    assert window.presenter.workspace.active is active
    assert Path(location).read_bytes() == before
    filters.close()
    filters.deleteLater()
    map_panel.close()
    map_panel.deleteLater()


def test_metric_review_invalid_inputs_and_read_failure(
    project: AssessmentProjectFile,
) -> None:
    """Unused metric slots stay complete; invalid inputs and I/O failures stay explicit.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.

    Returns:
        None.
    """
    key = DocumentKey("p", "lifft-1")
    original = project.load(key)
    project.save(key, replace(original, system=MeasurementSystem.METRIC))
    row = (
        saved_plot_results(
            project,
            PlotFilterSelection(SCOPE),
            current_year=2026,
        )
        .workers[0]
        .assessment
    )
    assert row.status is EvaluationStatus.COMPLETE
    assert row.total_damage is not None
    assert not row.issue_keys
    project.save(key, LifftDraft(original.system, (LifftTask("bad", -1, 20, 100),)))
    row = (
        saved_plot_results(
            project,
            PlotFilterSelection(SCOPE),
            current_year=2026,
        )
        .workers[0]
        .assessment
    )
    assert row.status is EvaluationStatus.INVALID_INPUT and row.probability is None
    repository = Mock(wraps=project)
    repository.metadata = project.metadata
    repository.load.side_effect = OSError("controlled source read failure")
    with pytest.raises(OSError):
        saved_plot_results(repository, PlotFilterSelection(SCOPE), current_year=2026)

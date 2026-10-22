"""Standalone assessments, optional workplaces and independent JROT integration.

Test layer. All writes use disposable projects and the approved baseline. Verify real
SQLite ownership, source/result identity, rollback and actual integrated Qt controls.
Organization names, including Default, never trigger manufactured records or deletion.
"""

import sqlite3
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QCoreApplication, QEvent
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox

from ergotools.application.assessment_export import saved_summary_rows
from ergotools.application.assessments.duet_commands import AddDuetTask
from ergotools.application.assessments.lifft_commands import AddLifftTask
from ergotools.application.assessments.project_edits import (
    DuetProjectEdit,
    LifftProjectEdit,
    TstProjectEdit,
)
from ergotools.application.assessments.tst_commands import AddTstTask
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.plot_results import saved_plot_results
from ergotools.application.rotation_pool import rotation_pool
from ergotools.application.rotation_preparation import prepare_rotation_problem
from ergotools.application.saved_results import calculate_saved_result
from ergotools.application.session import DocumentKey
from ergotools.application.settings import Language
from ergotools.bootstrap import create_window, load_icons
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessments.document import AssessmentDraft, AssessmentKind
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection
from ergotools.domain.assessments.tst_draft import TstDraft, TstTask
from ergotools.domain.job_catalog import Job, JobCatalog, WorkerJobAssignment
from ergotools.domain.job_risk import JobRiskMeasurement, JobRiskValues
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.plot_filters import PlotFilterSelection
from ergotools.domain.plot_scope import PlotScope
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.rotation import WorkerRotation
from ergotools.domain.rotation_scheme import RotationScheme
from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.pulp_rotation_optimizer import PulpRotationOptimizer
from ergotools.presentation.desktop.assessment_context_dialog import (
    AssessmentContextDialog,
)
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.worker_management_dialog import (
    WorkerManagementDialog,
)
from ergotools.presentation.desktop.workplace_assignment_dialog import (
    WorkplaceAssignmentDialog,
)
from ergotools.presentation.summary_csv import summary_csv_table

# Keep Qt alive until all owned widgets have received their deferred-delete events.
_APP = QApplication.instance() or QApplication([])
# All scenarios share a synthetic project identity and canonical metric input units.
META = ProjectMetadata("optional", "Optional organization", MeasurementSystem.METRIC)
# Genuine organization deliberately uses Default; no name-based cleanup is permitted.
STATION = StationKey("Default", "Default", "Default", "S1")


def start_standalone_worker(view: LifftWindow) -> None:
    """Select a minimal worker before editing an empty project's first assessment.

    Args:
        view: Integrated window whose newly created project has no worker assessment.

    Returns:
        None. Persist only a worker ID and activate an unsaved standalone LiFFT preview.
        No organizational record or assessment source is created before explicit Save.
    """
    workspace = view.presenter.workspace
    hierarchy, jobs = workspace.read_hierarchy(), workspace.read_jobs()
    work = replace(hierarchy.hierarchy.work, workers=(WorkerEntry("new-worker"),))
    workspace.save_worker_catalogs(
        hierarchy, replace(hierarchy.hierarchy, work=work), jobs, jobs.jobs
    )
    view.assessment_navigation.select(
        "new-worker",
        AssessmentKind.LIFFT,
        lambda: view.blank_lifft_source(view.presenter.system),
        explicit=True,
    )
    view.refresh()


def source_for(kind: AssessmentKind) -> AssessmentDraft:
    """Supply one complete task for each tool without rounding or display conversion.

    Args:
        kind: Exact scientific model identity.

    Returns:
        Immutable source with valid physical inputs and 30 repetitions.
    """
    if kind is AssessmentKind.LIFFT:
        return LifftDraft(MeasurementSystem.METRIC, (LifftTask("l", 10, 20, 30),))
    if kind is AssessmentKind.DUET:
        return DuetDraft((DuetTask("d", 6, 30),))
    return TstDraft(
        MeasurementSystem.METRIC, (TstTask("s", TstDirection.DOWNWARD, 10, 20, 30),)
    )


def add_real_workplace(project: AssessmentProjectFile) -> None:
    """Extend existing workers with real organization and a Job-optional assignment.

    Args:
        project: Open disposable project whose worker A already exists.

    Returns:
        None. Worker IDs and scientific sources/results remain unchanged.
    """
    work = replace(project.load_hierarchy().work, stations=(STATION,), shifts=("1",))
    hierarchy = WorkHierarchy(
        work,
        ("Default",),
        (SectionKey("Default", "Default"),),
        (LineKey("Default", "Default", "Default"),),
    )
    project.save_hierarchy(hierarchy)
    owner = work.worker_context("A", STATION.at_shift("1"))
    project.save_jobs(
        JobCatalog(META.project_id, assignments=(WorkerJobAssignment(1, owner, None),))
    )


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_standalone_save_associate_plot_and_reopen(
    tmp_path: Path, kind: AssessmentKind
) -> None:
    """All tools persist without organization, then join PLOT without copying results.

    Args:
        tmp_path: Disposable directory for native persistence.
        kind: Each ergonomic tool exercised independently.

    Returns:
        None; prove exact source/result bytes, same identity, no Job dependency,
        standalone CSV absence, and successful assigned reopen.
    """
    path = tmp_path / "standalone.ergprj"
    with AssessmentProjectFile.create_empty(path, META) as project:
        assert not project.list_assessments() and not project.load_hierarchy().plants
        project.save_hierarchy(
            WorkHierarchy(
                WorkCatalog(META.project_id, (WorkerEntry("A"), WorkerEntry("B")))
            )
        )
        source = source_for(kind)
        key = DocumentKey(META.project_id, "assessment")
        result = calculate_saved_result(key, source, META.default_units)
        project.create_historical_assessment(
            AssignmentAssessment(key.document_id, None, kind, "A"),
            source,
            result=result,
        )
        rows = saved_summary_rows(project, kind)
        assert len(rows) == 1 and rows[0].owner.worker_id == "A"
        assert rows[0].owner.workplace is None
        assert summary_csv_table(rows, "now")[1][2:7] == ("", "", "", "", "")
        before = (
            project._connection.execute(
                "SELECT payload FROM draft_documents"
            ).fetchall(),
            project._connection.execute(
                "SELECT payload FROM saved_assessment_results"
            ).fetchall(),
        )
        with pytest.raises(ValueError, match="missing worker"):
            project.save_hierarchy(
                WorkHierarchy(WorkCatalog(META.project_id, (WorkerEntry("B"),)))
            )
        add_real_workplace(project)
        selection = PlotFilterSelection(PlotScope((("Default",),), "1"), kind)
        assert not saved_plot_results(project, selection, current_year=2026).workers
        project.associate_assessment(key.document_id, 1)
        assert (
            len(saved_plot_results(project, selection, current_year=2026).workers) == 1
        )
        assert not project.load_jobs().jobs and not project.load_job_risk().values
        assert before == (
            project._connection.execute(
                "SELECT payload FROM draft_documents"
            ).fetchall(),
            project._connection.execute(
                "SELECT payload FROM saved_assessment_results"
            ).fetchall(),
        )
    with AssessmentProjectFile.open(path) as reopened:
        entry = reopened.load_history().entries[0]
        assert (entry.worker_id, entry.assignment_id, entry.document_id) == (
            "A",
            1,
            "assessment",
        )
        assert reopened.load_hierarchy().plants == ("Default",)
        assert reopened.load_saved_result(key) == result
        assert reopened._connection.execute("PRAGMA integrity_check").fetchone() == (
            "ok",
        )
        assert not reopened._connection.execute("PRAGMA foreign_key_check").fetchall()


def test_standalone_uniqueness_and_association_conflicts(tmp_path: Path) -> None:
    """Cross-worker, duplicate and already-assigned associations never mutate data.

    Args:
        tmp_path: Disposable native database directory.

    Returns:
        None; assert domain and SQL uniqueness plus complete rollback after failures.
    """
    with AssessmentProjectFile.create_empty(
        tmp_path / "conflicts.ergprj", META
    ) as project:
        project.save_hierarchy(
            WorkHierarchy(
                WorkCatalog(META.project_id, (WorkerEntry("A"), WorkerEntry("B")))
            )
        )
        source = source_for(AssessmentKind.LIFFT)
        entry = AssignmentAssessment("a", None, AssessmentKind.LIFFT, "A")
        project.create_historical_assessment(entry, source)
        project.create_historical_assessment(
            replace(entry, document_id="b", worker_id="B"), source
        )
        with pytest.raises(ValueError, match="ownership"):
            project.create_historical_assessment(
                replace(entry, document_id="duplicate"), source
            )
        with pytest.raises(sqlite3.IntegrityError), project._connection:
            project._connection.execute(
                "INSERT INTO assessment_ownership "
                "VALUES('duplicate','A',NULL,'lifft',99)"
            )
        add_real_workplace(project)
        before = project.load_history()
        with pytest.raises(ValueError, match="matching"):
            project.associate_assessment("b", 1)
        assert project.load_history() == before
        project.associate_assessment("a", 1)
        with pytest.raises(ValueError):
            project.associate_assessment("a", 1)
        project.create_historical_assessment(
            replace(entry, document_id="a-new"), source
        )
        before = project.load_history()
        with pytest.raises(ValueError, match="already"):
            project.associate_assessment("a-new", 1)
        assert project.load_history() == before


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_integrated_standalone_first_save_and_context_visibility(
    tmp_path: Path, language: Language, kind: AssessmentKind
) -> None:
    """Actual main window edits and saves all tools with the unused context row hidden.

    Args:
        tmp_path: Disposable application settings/project directory.
        language: English or Spanish interface.
        kind: Selected scientific assessment tool.

    Returns:
        None; first Save owns the selected worker, context collapse gives back height,
        real organization expands on reopen, and workplace-only picker is usable.
    """
    path = tmp_path / "ui.ergprj"
    with AssessmentProjectFile.create_empty(path, META) as project:
        project.save_hierarchy(
            WorkHierarchy(WorkCatalog(META.project_id, (WorkerEntry("A"),)))
        )
    view = create_window(
        tmp_path / "settings.json", original_navigation=True, enable_vtk=False
    )
    try:
        view.language = language
        view.open_project_location(str(path))
        view.show()
        _APP.processEvents()
        browser = view.assessment_navigation
        browser.select("A", kind, lambda: view._blank_kind(kind), explicit=True)
        view.refresh()
        assert not view.main_navigation.context_frame.isVisible()
        assert not view.main_navigation.context_toggle.isChecked()

        def choose_unassigned(dialog: AssessmentContextDialog) -> int:
            """Accept the only available context when no assignments exist.

            Args:
                dialog: Real chooser for a worker in an organization-free project.

            Returns:
                Accepted result without creating any persisted source or assignment.
            """
            assert dialog.tree.topLevelItemCount() == 0
            assert not dialog.use.isEnabled()
            assert dialog.standalone_button is not None
            dialog.standalone_button.click()
            return dialog.result()

        with patch.object(AssessmentContextDialog, "exec_", choose_unassigned):
            view.select_navigation_context()
        assert not view.presenter.workspace.read_history().history.entries
        active = view.presenter.workspace.active
        source = source_for(kind)
        if isinstance(source, LifftDraft):
            active.execute(
                LifftProjectEdit(AddLifftTask(active.document, source.tasks[0], 0))
            )
        elif isinstance(source, DuetDraft):
            active.execute(
                DuetProjectEdit(AddDuetTask(active.document, source.tasks[0], 0))
            )
        else:
            active.execute(
                TstProjectEdit(AddTstTask(active.document, source.tasks[0], 0))
            )
        view.refresh()
        view.save_project()
        assert not active.is_dirty
        entry = view.presenter.workspace.read_history().history.standalone_for(
            "A", kind
        )
        assert entry is not None
        view.main_navigation.context_toggle.setChecked(True)
        assert view.main_navigation.context_frame.isVisible()
        view.presenter.workspace.close(choice=CloseChoice.DISCARD)
        with AssessmentProjectFile.open(path) as project:
            add_real_workplace(project)
        view.open_project_location(str(path))
        assert view.main_navigation.context_toggle.isChecked()
        dialog = WorkerManagementDialog(
            view.presenter.workspace,
            load_icons(),
            META.default_units,
            language=language,
        )
        picker = WorkplaceAssignmentDialog(
            dialog._hierarchy.hierarchy,
            dialog._jobs.jobs,
            "A",
            load_icons(),
            language=language,
            parent=dialog,
        )
        try:
            assert len(picker._stations) == 1
            picker.select_workplace(STATION.at_shift("1"))
            picker.accept_selection()
            assert picker.result() == QDialog.Accepted
            assert picker.selected_placement_id is None
            assert picker.selected_workplace == STATION.at_shift("1")
        finally:
            picker.deleteLater()
            dialog.deleteLater()
    finally:
        view.presenter.workspace.close(choice=CloseChoice.DISCARD)
        view.close()
        view.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        _APP.processEvents()


def test_jrot_job_only_without_organization_or_worker_assessments(
    tmp_path: Path,
) -> None:
    """Real CBC/HiGHS and persisted schemes remain independent of worker assessments.

    Args:
        tmp_path: Disposable native project directory; no operational fixtures are used.

    Returns:
        None; both solver routes succeed using only worker IDs and approved Job risks,
        then the same scheme reopens without organization or assessment placeholders.
    """
    path = tmp_path / "job_only.ergprj"
    with AssessmentProjectFile.create_empty(path, META) as project:
        project.save_hierarchy(
            WorkHierarchy(
                WorkCatalog(META.project_id, (WorkerEntry("A"), WorkerEntry("B")))
            )
        )
        project.save_jobs(
            JobCatalog(META.project_id, (Job("J1", "Job 1"), Job("J2", "Job 2")))
        )
        for identity, job in enumerate(("J1", "J2"), 1):
            project.save_job_details(
                project.load_jobs(),
                project.load_job_risk(),
                next(item for item in project.load_jobs().jobs if item.job_id == job),
                JobRiskValues(
                    job,
                    tuple(
                        JobRiskMeasurement(kind, 0.1, identity * 20, "Metric")
                        for kind in AssessmentKind
                    ),
                ),
            )
        pool = rotation_pool(project)
        targets = tuple(choice.target for choice in pool.targets)
        keys = tuple(target.key for target in targets)
        scheme = RotationScheme(
            META.project_id,
            "R1",
            "Jobs only",
            tuple(choice.link for choice in pool.workers),
            targets,
            (WorkerRotation("A", keys), WorkerRotation("B", tuple(reversed(keys)))),
        )
        problem = prepare_rotation_problem(
            scheme, pool, tuple(AssessmentKind), time_limit_seconds=5
        )
        optimizer = PulpRotationOptimizer()
        assert optimizer.optimize_single_tool(problem, AssessmentKind.LIFFT).schedule
        assert optimizer.optimize_all_tools(problem).schedule
        project.save_rotation_scheme(scheme)
        assert not project.load_history().entries and not project.list_assessments()
    with AssessmentProjectFile.open(path) as project:
        assert project.load_rotation_schemes() == (scheme,)
        assert not project.load_hierarchy().plants


@pytest.mark.parametrize("language", list(Language))
def test_association_action_preserves_identity_and_standalone_navigation(
    tmp_path: Path,
    language: Language,
) -> None:
    """Use the actual association action without copying assessment inputs or results.

    Args:
        tmp_path: Disposable project/settings directory.
        language: English or Spanish chooser labels and accepted navigation.

    Returns:
        None; one tool is associated, other tools remain standalone, and returning to
        standalone navigation creates a fresh preview without another database row.
    """
    path = tmp_path / "associate.ergprj"
    with AssessmentProjectFile.create_empty(path, META) as project:
        project.save_hierarchy(
            WorkHierarchy(WorkCatalog(META.project_id, (WorkerEntry("A"),)))
        )
        for kind in AssessmentKind:
            project.create_historical_assessment(
                AssignmentAssessment(kind.value, None, kind, "A"), source_for(kind)
            )
        add_real_workplace(project)
    view = create_window(
        tmp_path / "settings.json", original_navigation=True, enable_vtk=False
    )
    try:
        view.language = language
        view.open_project_location(str(path))
        view.select_tool(0)
        view.select_standalone_assessment()
        original = view.presenter.workspace.active.document

        def choose(dialog: WorkplaceAssignmentDialog) -> int:
            """Choose a workplace-only leaf using the actual picker controls.

            Args:
                dialog: Owned real context picker under test.

            Returns:
                Accepted result after explicit station selection.
            """
            assert dialog._reuse_existing
            dialog.select_workplace(STATION.at_shift("1"))
            dialog.accept_button.click()
            assert dialog.selected_workplace == STATION.at_shift("1")
            return QDialog.Accepted

        with patch.object(WorkplaceAssignmentDialog, "exec_", choose):
            view.main_navigation.associate_button.click()
        workspace = view.presenter.workspace
        assert workspace.active.document == original
        history = workspace.read_history().history
        assert (
            history.current_for(1, AssessmentKind.LIFFT).document_id
            == original.document_id
        )
        assert history.standalone_for("A", AssessmentKind.DUET) is not None
        assert len(history.entries) == 3

        def choose_standalone(dialog: AssessmentContextDialog) -> int:
            """Accept unassigned navigation through the separate context-dialog button.

            Args:
                dialog: Real picker owning the optional standalone choice.

            Returns:
                Accepted result from the separate standalone button.
            """
            assert dialog.standalone_button is not None
            assert dialog.standalone_button.text() == (
                "Evaluación independiente"
                if language is Language.SPANISH
                else "Standalone assessment"
            )
            dialog.standalone_button.click()
            assert dialog.selected_standalone
            assert dialog.selected_assignment is None
            return dialog.result()

        with patch.object(
            AssessmentContextDialog, "exec_", return_value=QDialog.Rejected
        ):
            view.main_navigation.buttons["context"].click()
        assert workspace.active.document == original
        assert "standalone" not in view.main_navigation.buttons
        with patch.object(AssessmentContextDialog, "exec_", choose_standalone):
            view.main_navigation.buttons["context"].click()
        assert view.assessment_navigation.view.workplace is None
        assert workspace.active.document != original
        assert not view.assessment_navigation.view.saved
        assert len(workspace.read_history().history.entries) == 3
    finally:
        view.presenter.workspace.close(choice=CloseChoice.DISCARD)
        view.close()
        view.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        _APP.processEvents()


def test_first_worker_and_workplace_need_no_existing_assessment(tmp_path: Path) -> None:
    """Create the first worker/workplace through real forms from a source-free project.

    Args:
        tmp_path: Disposable native project/settings directory.

    Returns:
        None; a workplace-only assignment and explicitly selected first assessment
        work without an unowned placeholder source or Job record.
    """
    path = tmp_path / "first_worker.ergprj"
    with AssessmentProjectFile.create_empty(path, META) as project:
        hierarchy = WorkHierarchy(
            WorkCatalog(META.project_id, (), (STATION,), ("1",)),
            ("Default",),
            (SectionKey("Default", "Default"),),
            (LineKey("Default", "Default", "Default"),),
        )
        project.save_hierarchy(hierarchy)
    view = create_window(
        tmp_path / "settings.json", original_navigation=True, enable_vtk=False
    )
    try:
        view.open_project_location(str(path))
        assert view.presenter.workspace.active is None

        def choose_workplace(dialog: WorkplaceAssignmentDialog) -> int:
            """Choose the real Job-optional station through the actual row controls.

            Args:
                dialog: Owned Add assignment picker supplied by Worker Management.

            Returns:
                Accepted result after selecting the workplace-only row.
            """
            dialog.select_workplace(STATION.at_shift("1"))
            dialog.accept_selection()
            assert dialog.selected_workplace == STATION.at_shift("1")
            return QDialog.Accepted

        def create_worker(dialog: WorkerManagementDialog) -> int:
            """Save only worker ID, then add its real workplace without a Job.

            Args:
                dialog: Owned worker-management form opened from the main window.

            Returns:
                Accepted result; both record operations use real application ports.
            """
            dialog.worker_id_combo.setEditText("A")
            dialog.save_worker()
            with patch.object(WorkplaceAssignmentDialog, "exec", choose_workplace):
                dialog.add_worker_assignment()
            return QDialog.Accepted

        with (
            patch.object(WorkerManagementDialog, "exec", create_worker),
            patch.object(QMessageBox, "question", return_value=QMessageBox.Yes),
        ):
            view.open_worker_management()
        workspace = view.presenter.workspace
        assert not workspace.read_history().history.entries
        assert view.assessment_navigation.view.workplace is None

        def create_at_workplace(dialog: AssessmentContextDialog) -> int:
            """Create the first contextual assessment through its exact workplace.

            Args:
                dialog: Main worker/tool context chooser, separate from management.

            Returns:
                Accepted Create assessment intent for the first real assignment.
            """
            leaf = dialog.tree.topLevelItem(0).child(0).child(0).child(0)
            dialog.tree.setCurrentItem(leaf)
            assert dialog.use.text() == "Create assessment"
            dialog.use.click()
            return dialog.result()

        with patch.object(AssessmentContextDialog, "exec_", create_at_workplace):
            view.select_navigation_context()
        entry = workspace.read_history().history.entries[0]
        assert (entry.worker_id, entry.assignment_id) == ("A", 1)
        assert workspace.active.document.document_id == entry.document_id
        assert not workspace.read_jobs().jobs.jobs
        with AssessmentProjectFile.open(path) as project:
            assert project.list_assessments() == ()
            assert not project.load_jobs().assignments
        view.save_project()
        with AssessmentProjectFile.open(path) as project:
            assert len(project.list_assessments()) == 1
            assert project.load_jobs().assignments[0].placement_id is None
    finally:
        view.presenter.workspace.close(choice=CloseChoice.DISCARD)
        view.close()
        view.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        _APP.processEvents()

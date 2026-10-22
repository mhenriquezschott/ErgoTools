"""Basic developer-prototype acceptance: isolation, Yes flow and real solver paths.

Tests use detached catalogs/private fixture copies, never write maintained projects.
Focus on the owner's limited prototype scope, without adding broad production history,
localization, migration or report infrastructure.
"""

from hashlib import sha256
from pathlib import Path
from threading import Event
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QCoreApplication, QEvent, Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QComboBox, QLineEdit

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.jrot_prototype import (
    PrototypeCatalog,
    metric_prototype_source,
    read_prototype_catalog,
)
from ergotools.bootstrap import create_window, load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.rotation import (
    RotationBackend,
    RotationProblem,
    RotationSolution,
    RotationSolveStatus,
)
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.pulp_rotation_optimizer import PulpRotationOptimizer
from ergotools.presentation.desktop.jrot_prototype_dialog import JrotPrototypeDialog
from ergotools.presentation.desktop.jrot_prototype_selectors import (
    PrototypeRecordDialog,
    PrototypeScopeDialog,
)
from ergotools.presentation.desktop.preferences_dialog import PreferencesDialog
from tools.create_jrot_demo_project import create_demo, demo_sources

# Retain QApplication across the finite native/offscreen prototype probes.
_APP = QApplication.instance() or QApplication([])


def dispose(dialog: JrotPrototypeDialog) -> None:
    """Close an idle prototype and process its owned deferred widget deletion.

    Args:
        dialog: Test-owned prototype with no active solver thread.

    Returns:
        None; tests retain no parent/main-window singleton.
    """
    dialog.reject()
    dialog.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _APP.processEvents()


def advance_to(dialog: JrotPrototypeDialog, page: int) -> None:
    """Drive ordinary sequential Continue actions rather than bypass validation.

    Args:
        dialog: Test-owned Yes-path prototype.
        page: Zero-based target page, not earlier than its current position.

    Returns:
        None; assert each step actually advanced without a hidden error.
    """
    while dialog._page < page:
        previous = dialog._page
        dialog.advance()
        _APP.processEvents()
        assert dialog._page == previous + 1, dialog.error.text()


def wait_for_solve(dialog: JrotPrototypeDialog) -> None:
    """Pump GUI events until the bounded real test solve has safely finished.

    Args:
        dialog: Prototype owning the active CBC/HiGHS thread.

    Returns:
        None; a stale or failed preview is an assertion failure.
    """
    for _ in range(1000):
        QTest.qWait(10)
        if dialog.worker is None:
            break
    assert dialog.worker is None
    assert dialog.solution is not None, dialog.error.text()


@pytest.mark.parametrize("mode", [0, 1, 2, 3])
def test_yes_flow_real_solver_and_discard(mode: int) -> None:
    """Each single tool and all-three finish the actual flow without persistence.

    Args:
        mode: LiFFT, DUET, ST or all-three analysis selector index.

    Returns:
        None; the solver validates staffing and dialog close empties scratch state.
    """
    dialog = JrotPrototypeDialog(
        PrototypeCatalog("Sample"), PulpRotationOptimizer(), load_icons()
    )
    dialog.analysis.setCurrentIndex(mode)
    advance_to(dialog, 6)
    before = dialog.session.problem(dialog.kinds(), 3)
    dialog.session.restrictions.append(
        (dialog.session.workers[0], "Fix to one Job", dialog.session.jobs[-1].key)
    )
    assert dialog.session.problem(dialog.kinds(), 3) == before
    dialog.start_solve()
    wait_for_solve(dialog)
    assert dialog.solution is not None
    assert dialog.solution.backend is (
        RotationBackend.HIGHS if mode == 3 else RotationBackend.CBC
    )
    before.validate_schedule(dialog.solution.schedule)
    dialog.advance()
    assert dialog._page == 7
    assert dialog.statistics.rowCount() == (12 if mode == 3 else 4)
    dispose(dialog)
    assert dialog.session.jobs == []
    assert dialog.session.current == ()


def test_no_branch_and_staffing_validation() -> None:
    """No cannot solve; invalid staffing stays reviewable without trapping navigation.

    Args:
        None.

    Returns:
        None; failures leave the current inputs visible.
    """
    dialog = JrotPrototypeDialog(
        PrototypeCatalog("Sample"), PulpRotationOptimizer(), load_icons()
    )
    dialog.no.setChecked(True)
    assert not dialog.next.isEnabled()
    dialog.advance()
    assert dialog._page == 0 and "No path" in dialog.error.text()
    dialog.yes.setChecked(True)
    dialog.jobs_count.setValue(3)
    dialog.go(6)
    assert dialog._page == 6
    with pytest.raises(ValueError, match="same number"):
        dialog.start_solve()
    dialog.jobs_count.setValue(4)
    dialog.go(3)
    combo = dialog.matrix.cellWidget(1, 1)
    assert isinstance(combo, QComboBox)
    combo.setCurrentIndex(0)
    dialog.go(5)
    assert dialog._page == 5 and "exactly once" in dialog.baseline_context.text()
    dialog.go(0)
    assert dialog._page == 0  # Invalid staffing cannot trap Back/sidebar navigation.
    dispose(dialog)


def test_task_names_partial_skip_and_back_navigation() -> None:
    """Scratch names/zero/blank/outputs survive Back, while missing tools block solves.

    Args:
        None.

    Returns:
        None; only the selected tool/Job copy changes.
    """
    dialog = JrotPrototypeDialog(
        PrototypeCatalog("Sample"), PulpRotationOptimizer(), load_icons()
    )
    advance_to(dialog, 4)
    dialog._clear_tool()
    grid = dialog._current_grid()
    grid.names[0].setText("A named task")
    grid.names[0].textEdited.emit("A named task")
    for control, text in zip(grid.controls[0], ("30", "49.05", "100"), strict=True):
        assert isinstance(control, QLineEdit)
        control.setText(text)
        control.textEdited.emit(text)
    dialog._calculate()
    first = dialog.session.jobs[0]
    result = first.measurements[AssessmentKind.LIFFT]
    assert result.complete and result.probability_percent == pytest.approx(
        13.190999733969136
    )
    assert "A named task" in first.task_names.values()
    dialog.go(3)
    dialog.go(4)
    assert dialog.grids[AssessmentKind.LIFFT].names[0].text() == "A named task"
    dialog.tool_tabs.setCurrentIndex(1)
    dialog._skip_tool()
    assert first.status(tuple(AssessmentKind)) == "In progress"
    dialog.advance()
    assert dialog._page == 5 and "Calculate duet" in dialog.baseline_context.text()
    dialog.go(4)
    dialog.analysis.setCurrentIndex(0)
    advance_to(dialog, 6)
    assert dialog.kinds() == (AssessmentKind.LIFFT,)
    dispose(dialog)


def test_task_resize_retains_inputs_and_other_tools() -> None:
    """Task +/- retains the existing prefix and only invalidates this tool's totals.

    Args:
        None.

    Returns:
        None; no production task editor has been changed for task names.
    """
    dialog = JrotPrototypeDialog(
        PrototypeCatalog("Sample"), PulpRotationOptimizer(), load_icons()
    )
    advance_to(dialog, 4)
    job = dialog.session.jobs[0]
    other = job.measurements[AssessmentKind.DUET]
    grid = dialog._current_grid()
    original = grid.source.tasks[0]
    grid.resize_tasks()
    grid.commit()
    assert len(grid.source.tasks) == 2 and grid.source.tasks[0] == original
    grid.setCurrentCell(1, 0)
    grid.resize_tasks(True)
    grid.commit()
    assert grid.source.tasks == (original,)
    assert not job.measurements[AssessmentKind.LIFFT].complete
    assert job.measurements[AssessmentKind.DUET] == other
    dispose(dialog)


def test_project_sample_and_entered_values_are_independent(tmp_path: Path) -> None:
    """Real catalog, sample and newly entered task values can share a genuine solve.

    Args:
        tmp_path: Disposable native-copy directory; original fixture stays untouched.

    Returns:
        None; input file bytes/schema and detached catalog values remain exact.
    """
    original = Path("test_projects/native/comparative_risk_test.ergprj")
    baseline = original.read_bytes()
    path = tmp_path / "private.ergprj"
    path.write_bytes(baseline)
    with AssessmentProjectFile.open(path) as project:
        catalog = read_prototype_catalog(project, "Comparison copy")
    dialog = JrotPrototypeDialog(catalog, PulpRotationOptimizer(), load_icons())
    dialog.workers_count.setValue(4)
    dialog.jobs_count.setValue(4)
    advance_to(dialog, 1)
    project_keys = [job.key for job in dialog.available_jobs if job.origin == "Project"]
    choices = (project_keys[0], "sample-2", "entered-1", project_keys[1])
    for combo, key in zip(dialog._job_choices, choices, strict=True):
        combo.select_key(key)
    advance_to(dialog, 4)
    dialog.job_progress.setCurrentRow(2)
    for index, kind in enumerate(AssessmentKind):
        dialog.tool_tabs.setCurrentIndex(index)
        grid = dialog.grids[kind]
        controls = grid.controls[0]
        if kind is AssessmentKind.DUET:
            selector = controls[0]
            assert isinstance(selector, QComboBox)
            selector.setCurrentIndex(6)
            numbers, tokens = controls[1:], ("100",)
        elif kind is AssessmentKind.TST:
            numbers, tokens = controls[1:], ("30", "49.05", "100")
        else:
            numbers, tokens = controls, ("30", "49.05", "100")
        for field, text in zip(numbers, tokens, strict=True):
            assert isinstance(field, QLineEdit)
            field.setText(text)
            field.textEdited.emit(text)
        dialog._calculate()
    advance_to(dialog, 6)
    dialog.start_solve()
    wait_for_solve(dialog)
    dialog.advance()
    assert dialog._page == 7
    dispose(dialog)
    assert path.read_bytes() == baseline
    assert original.read_bytes() == baseline
    assert catalog.risks is not None
    assert all(
        value.source is None
        for values in catalog.risks.values
        for value in values.measurements
    )


def test_metric_copy_does_not_rewrite_source() -> None:
    """Imperial project inputs become cm/N only in a new ephemeral DTO.

    Args:
        None.

    Returns:
        None; original unit/input values remain exact.
    """
    source = LifftDraft(MeasurementSystem.IMPERIAL, (LifftTask("a", 10, 20, 100),))
    result = metric_prototype_source(source)
    assert isinstance(result, LifftDraft)
    assert result.tasks[0].lever_arm == pytest.approx(25.4)
    assert result.tasks[0].load == 89
    assert source.tasks[0].lever_arm == 10
    assert source.system is MeasurementSystem.IMPERIAL


def test_runtime_settings_apply_cancel_and_restart(tmp_path: Path) -> None:
    """Developer-only Apply writes no preferences/project; Cancel/restart disable it.

    Args:
        tmp_path: Private settings/project directory.

    Returns:
        None; the main application's ordinary preference schema remains unchanged.
    """
    settings = tmp_path / "settings.json"
    window = create_window(settings, original_navigation=True)
    assert not window._developer_enabled
    assert window._developer_menu is not None
    action = window._developer_menu.menuAction()
    assert action is not None and not action.isVisible()

    def enable() -> None:
        """Accept the actual modal developer checkbox without changing other drafts.

        Args:
            None.

        Returns:
            None; the surrounding test verifies zero writes.
        """
        modal = _APP.activeModalWidget()
        assert isinstance(modal, PreferencesDialog)
        modal.developer_option.setChecked(True)
        modal.accept()

    with patch.object(
        window.presenter.workspace,
        "update_display_settings",
        side_effect=AssertionError("project mutation"),
    ):
        QTimer.singleShot(0, enable)
        window.open_preferences()
    assert window._developer_enabled and action.isVisible()
    assert not settings.exists()

    def cancel() -> None:
        """Cancel an attempted disable, preserving the current runtime state.

        Args:
            None.

        Returns:
            None; no checkbox choice survives cancellation.
        """
        modal = _APP.activeModalWidget()
        assert isinstance(modal, PreferencesDialog)
        modal.developer_option.setChecked(False)
        modal.reject()

    QTimer.singleShot(0, cancel)
    window.open_preferences()
    assert window._developer_enabled and not settings.exists()
    window.close()
    fresh = create_window(settings, original_navigation=True)
    assert not fresh._developer_enabled
    fresh.close()
    window.deleteLater()
    fresh.deleteLater()
    _APP.processEvents()


def test_launcher_preserves_active_workspace(tmp_path: Path) -> None:
    """The real developer menu launcher receives no writer or main history callback.

    Args:
        tmp_path: Disposable workflow-project copy and separate settings.

    Returns:
        None; catalogs, active source, history/dirty state and disk bytes stay exact.
    """
    path = tmp_path / "workflow.ergprj"
    path.write_bytes(
        Path("test_projects/native/workflow_4_workers.ergprj").read_bytes()
    )
    baseline = path.read_bytes()
    window = create_window(tmp_path / "settings.json", original_navigation=True)
    with AssessmentProjectFile.open(path) as probe:
        document = probe.load_history().entries[0].document_id
    workspace = window.presenter.workspace
    workspace.switch(str(path), document)
    window.refresh()
    before = workspace.active
    dirty = workspace.has_unsaved_changes
    window.set_developer_mode(True)

    def exercise() -> None:
        """Enter temporary task text in the actual modal, then discard it.

        Args:
            None.

        Returns:
            None; no production command is invoked.
        """
        dialog = _APP.activeModalWidget()
        assert isinstance(dialog, JrotPrototypeDialog)
        advance_to(dialog, 4)
        dialog._clear_tool()
        dialog._current_grid().names[0].setText("Not saved anywhere")
        dialog.reject()

    QTimer.singleShot(0, exercise)
    window.open_developer_preview()
    assert workspace.active is before
    assert workspace.has_unsaved_changes == dirty
    assert path.read_bytes() == baseline
    workspace.close(choice=CloseChoice.DISCARD)
    window.close()
    window.deleteLater()
    _APP.processEvents()


def test_drawer_reallocates_width_and_pin_is_local() -> None:
    """Animated opening resizes content; pin prevents collapse until explicitly unset.

    Args:
        None.

    Returns:
        None; no preferences file or global widget state exists.
    """
    dialog = JrotPrototypeDialog(
        PrototypeCatalog("Sample"), PulpRotationOptimizer(), load_icons()
    )
    dialog.show()
    _APP.setActiveWindow(dialog)
    QTest.qWait(80)
    width = dialog.content.width()
    dialog.drawer.pin.setChecked(True)
    QTest.qWait(260)
    assert dialog.drawer.panel.maximumWidth() == 238
    assert dialog.content.width() < width
    dialog.drawer.reveal(False)
    QTest.qWait(260)
    assert dialog.drawer.panel.maximumWidth() == 238
    dialog.drawer.pin.setChecked(False)
    QTest.qWait(260)
    assert dialog.drawer.panel.maximumWidth() == 0
    assert dialog.content.width() == width
    dispose(dialog)


class WaitingOptimizer:
    """Controlled asynchronous port to verify safe close without terminating threads."""

    def __init__(self) -> None:
        """Own two synchronization events without starting a thread.

        Args:
            None.

        Returns:
            None.
        """
        self.started = Event()
        self.release = Event()

    def optimize_single_tool(
        self, problem: RotationProblem, kind: AssessmentKind
    ) -> RotationSolution:
        """Wait for test release, then return an unchanged valid schedule.

        Args:
            problem: Complete original input, never mutated.
            kind: Requested existing tool.

        Returns:
            Valid CBC-shaped result for publication-suppression testing only.
        """
        self.started.set()
        self.release.wait(5)
        return RotationSolution(
            problem.current, RotationBackend.CBC, (RotationSolveStatus.OPTIMAL,)
        )

    def optimize_all_tools(self, problem: RotationProblem) -> RotationSolution:
        """Provide the unused all-tool protocol method for this controlled probe.

        Args:
            problem: Complete original input.

        Returns:
            Valid two-stage-shaped result; this method is not a numerical solver test.
        """
        return RotationSolution(
            problem.current,
            RotationBackend.HIGHS,
            (RotationSolveStatus.OPTIMAL, RotationSolveStatus.OPTIMAL),
        )


def test_close_during_solve_defers_destruction() -> None:
    """Closing suppresses output and waits for the bounded worker before destruction.

    Args:
        None.

    Returns:
        None; no QThread is terminated or deleted while running.
    """
    optimizer = WaitingOptimizer()
    dialog = JrotPrototypeDialog(PrototypeCatalog("Sample"), optimizer, load_icons())
    dialog.analysis.setCurrentIndex(0)
    advance_to(dialog, 6)
    dialog.start_solve()
    assert optimizer.started.wait(1)
    dialog.reject()
    assert dialog.worker is not None and dialog._close_pending
    optimizer.release.set()
    for _ in range(200):
        QTest.qWait(10)
        if dialog.worker is None:
            break
    assert dialog.worker is None
    assert not dialog.session.jobs
    assert dialog.solution is None
    dispose(dialog)


def meeting_dialog() -> JrotPrototypeDialog:
    """Detach the meeting fixture without retaining an operational database handle.

    Args:
        None.

    Returns:
        Test-owned six-worker prototype with all real Job inputs available.
    """
    with AssessmentProjectFile.open(
        Path("test_projects/native/jrot_workflow_demo.ergprj")
    ) as project:
        catalog = read_prototype_catalog(project, "Six-worker meeting demo")
    return JrotPrototypeDialog(catalog, PulpRotationOptimizer(), load_icons())


def test_clean_fixture_quality_and_exclusive_regeneration(tmp_path: Path) -> None:
    """The clean meeting fixture has real source rows and no unexplained direct totals.

    Args:
        tmp_path: Private generator target; never overwrite the maintained demo.

    Returns:
        None; sources, demographics and scoped organization survive native reopen.
    """
    target = tmp_path / "new.ergprj"
    create_demo(target)
    baseline = target.read_bytes()
    with pytest.raises(FileExistsError):
        create_demo(target)
    assert target.read_bytes() == baseline
    with AssessmentProjectFile.open(target) as project:
        hierarchy, jobs, risks = (
            project.load_hierarchy(),
            project.load_jobs(),
            project.load_job_risk(),
        )
        assert (
            len(hierarchy.plants),
            len(hierarchy.sections),
            len(hierarchy.lines),
            len(hierarchy.work.stations),
        ) == (2, 4, 8, 24)
        assert hierarchy.work.shifts == ("Day", "Evening")
        assert len(jobs.jobs) == len(hierarchy.work.workers) == 6
        assert {w.worker_id for w in hierarchy.work.workers} == {
            f"W{i:02}" for i in range(1, 7)
        }
        assert all(
            w.first_name
            and w.last_name
            and w.details
            and w.details.sex
            and w.details.birth_date
            for w in hierarchy.work.workers
        )
        assert not project.load_history().entries
        for index, job in enumerate(jobs.jobs):
            values = risks.for_job(job.job_id)
            assert values is not None and len(values.measurements) == 3
            assert tuple(v.source for v in values.measurements) == demo_sources(
                job.job_id, index
            )
            assert all(
                v.complete
                and v.source is not None
                and len(v.source.tasks) == len(v.task_results) == 2
                for v in values.measurements
            )
        assert {p.workplace.shift_id for p in jobs.placements} == {"Day", "Evening"}
    assert target.read_bytes() == baseline


def test_six_real_workers_yes_flow_without_restrictions() -> None:
    """Six real Jobs/workers complete every step with actual HiGHS and no rules.

    Args:
        None.

    Returns:
        None; project bytes and source inputs remain exact after local optimization.
    """
    path = Path("test_projects/native/jrot_workflow_demo.ergprj")
    original = sha256(path.read_bytes()).hexdigest()
    dialog = meeting_dialog()
    assert dialog.workers_count.value() == dialog.jobs_count.value() == 6
    advance_to(dialog, 4)
    assert not dialog.session.restrictions
    assert len(dialog.session.workers) == len(set(dialog.session.workers)) == 6
    assert all(job.origin == "Project" for job in dialog.session.jobs)
    assert all(grid.rowCount() == 2 for grid in dialog.grids.values())
    assert "saved task input rows" in dialog.task_origin.text()
    advance_to(dialog, 6)
    problem = dialog.session.problem(dialog.kinds(), 3)
    dialog.start_solve()
    wait_for_solve(dialog)
    assert dialog.solution is not None
    problem.validate_schedule(dialog.solution.schedule)
    dialog.advance()
    assert dialog._page == 7 and dialog.statistics.rowCount() == 12
    dispose(dialog)
    assert sha256(path.read_bytes()).hexdigest() == original


def test_six_worker_mixed_project_sample_entered_roundtrip() -> None:
    """Real, sample and newly entered sources stay independent through backtracking.

    Args:
        None.

    Returns:
        None; all-three optimization runs after local entry without database writes.
    """
    dialog = meeting_dialog()
    dialog.go(1)
    dialog._job_choices[1].select_key("sample-2")
    dialog._job_choices[2].select_key("entered-1")
    dialog.go(4)
    dialog.job_progress.setCurrentRow(2)
    for index, kind in enumerate(AssessmentKind):
        dialog.tool_tabs.setCurrentIndex(index)
        grid = dialog._current_grid()
        grid.names[0].setText("Local meeting task")
        grid.names[0].textEdited.emit("Local meeting task")
        controls = grid.controls[0]
        if kind is AssessmentKind.DUET:
            selector = controls[0]
            assert isinstance(selector, QComboBox)
            selector.setCurrentIndex(5)
            numbers, values = controls[1:], ("600",)
        elif kind is AssessmentKind.TST:
            numbers, values = controls[1:], ("35", "49.05", "400")
        else:
            numbers, values = controls, ("35", "49.05", "400")
        for control, value in zip(numbers, values, strict=True):
            assert isinstance(control, QLineEdit)
            control.setText(value)
            control.textEdited.emit(value)
        dialog._calculate()
    local = dialog.session.jobs[2]
    for page in (0, 2, 3, 1, 4, 5, 6):
        dialog.go(page)
        assert dialog._page == page, dialog.error.text()
    assert dialog.session.jobs[2] is local
    assert "Local meeting task" in local.task_names.values()
    assert all(v.complete for v in local.measurements.values())
    dialog.start_solve()
    wait_for_solve(dialog)
    dialog.go(7)
    assert dialog._page == 7
    dispose(dialog)


def test_sidebar_and_back_do_not_require_ready_inputs() -> None:
    """Invalid selections/matrix and missing tasks cannot trap review navigation.

    Args:
        None.

    Returns:
        None; readiness errors are actionable only when calculation is requested.
    """
    dialog = meeting_dialog()
    dialog.show()
    dialog.drawer.pin.setChecked(True)
    QTest.qWait(260)
    for page in (7, 2, 0, 4, 1, 3, 6, 5, 2):
        assert dialog.drawer.buttons[page].isEnabled()
        QTest.mouseClick(dialog.drawer.buttons[page], Qt.MouseButton.LeftButton)
        assert dialog._page == page
    dialog._worker_choices[1].select_key(dialog._worker_choices[0].key)
    dialog.go(0)
    dialog.go(2)
    assert dialog._worker_choices[1].key == dialog._worker_choices[0].key
    dialog.go(6)
    with pytest.raises(ValueError, match="worker is selected twice"):
        dialog.start_solve()
    dialog.go(2)
    dialog._worker_choices[1].select_key("W02")
    dialog.go(3)
    cell = dialog.matrix.cellWidget(1, 1)
    assert isinstance(cell, QComboBox)
    cell.setCurrentIndex(0)
    dialog.go(0)
    dialog.go(3)
    assert dialog.matrix.cellWidget(1, 1) is cell
    assert cell.currentIndex() == 0
    cell.setCurrentIndex(1)
    dialog.go(4)
    dialog._clear_tool()
    dialog.go(5)
    assert "Calculate lifft" in dialog.baseline_context.text()
    dialog.go(0)
    dialog.blocks.setValue(6)
    dialog.go(3)
    assert dialog.matrix.columnCount() == 7
    dispose(dialog)


def test_owned_hierarchy_shift_and_worker_record_pickers() -> None:
    """Real themed picker acceptance/cancellation keeps full ancestry and exact IDs.

    Args:
        None.

    Returns:
        None; read-only dialog choices never create organization or worker records.
    """
    dialog = meeting_dialog()
    path = ("Osorno Foods", "Frozen packing", "Packing Line 2")

    def choose_scope() -> None:
        """Choose an exact existing Line and Evening shift in the owned modal.

        Args:
            None.

        Returns:
            None; double ancestry is retained despite repeated short Line names.
        """
        modal = _APP.activeModalWidget()
        assert isinstance(modal, PrototypeScopeDialog)
        plant = modal.tree.topLevelItem(2)
        assert plant is not None
        section = plant.child(1)
        assert section is not None
        line = section.child(1)
        assert line is not None
        modal.tree.setCurrentItem(line)
        modal.shift_tree.setCurrentItem(modal.shift_tree.topLevelItem(1))
        modal.accept_selection()

    QTimer.singleShot(0, choose_scope)
    dialog.choose_scope()
    assert dialog._scope_path == path and dialog._shift_id == "Evening"
    assert dialog.duration.value() == 8
    assert "Osorno Foods" in dialog.scope_summary.text()
    assert all(choice.key.startswith("project-") for choice in dialog._job_choices)
    dialog.go(2)

    def choose_worker() -> None:
        """Select a named record through the actual searchable worker tree.

        Args:
            None.

        Returns:
            None; picker stores the exact Worker ID, not its name caption.
        """
        modal = _APP.activeModalWidget()
        assert isinstance(modal, PrototypeRecordDialog)
        search = modal.findChild(QLineEdit)
        assert search is not None
        search.setText("W03")
        visible = [r for r in modal.rows if not r.isHidden()]
        assert len(visible) == 1
        modal.tree.setCurrentItem(visible[0])
        modal.accept_selection()

    QTimer.singleShot(0, choose_worker)
    dialog._worker_choices[0].choose()
    assert dialog._worker_choices[0].key == "W03"
    dispose(dialog)

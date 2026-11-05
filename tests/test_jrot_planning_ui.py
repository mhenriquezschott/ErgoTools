"""Real guided solver lifecycle, explicit retention and shared history checks.

All native projects and settings are disposable; no maintained fixture is written.
"""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from threading import Event

import pytest
from PyQt5.QtTest import QTest

from ergotools.application.rotation_entry import RotationEntryChange
from ergotools.application.rotation_optimization import RotationOptimizationError
from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.rotation import RotationSolution
from ergotools.domain.rotation_planning import RotationPlanningProblem
from ergotools.domain.rotation_scenario import RotationScenario
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.highs_rotation_optimizer import HighsRotationPlanner
from ergotools.presentation.desktop.jrot_dialog import JrotDialog
from tests.test_jrot_guided_ui import dispose
from tests.test_rotation_scenario_storage import scenario_workspace
from tests.test_rotation_scenarios import scenario_catalogs, scenario_inputs


def planning_dialog(tmp_path: Path, language: Language) -> JrotDialog:
    """Open a real risk-populated private project with no observed rotation.

    Args:
        tmp_path: Disposable native project directory.
        language: Current caption language.

    Returns:
        Owned test dialog using the actual approved backend adapter.
    """
    workspace = scenario_workspace(tmp_path)
    _, jobs, risks = scenario_catalogs()
    for job in jobs.jobs:
        workspace.save_job_details(
            workspace.read_jobs(),
            workspace.read_job_risk(),
            job,
            risks.for_job(job.job_id),
        )
    record = RotationScenario("timing", "R1", "Morning packing", scenario_inputs())
    workspace.rotation_scenarios().replace_rotation_scenario(None, record)
    dialog = JrotDialog(
        workspace, load_icons(), language=language, optimizer=HighsRotationPlanner()
    )
    dialog.show()
    QTest.qWait(20)
    return dialog


def await_result(dialog: JrotDialog) -> None:
    """Wait for a bounded solve and require retained results or a generated proposal.

    Args:
        dialog: Test-owned active solver controller.

    Returns:
        None; failure diagnostics include the actual visible error text.
    """
    for _ in range(1000):
        if not dialog.solve.busy:
            break
        QTest.qWait(10)
    assert not dialog.solve.busy
    assert not dialog.error.text(), dialog.error.text()
    assert (
        dialog.solve.preview is not None
        or dialog.current().run is not None
        or dialog.current().inputs.proposed is not None
    ), dialog.error.text()


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize(
    "tools", [(kind,) for kind in AssessmentKind] + [tuple(AssessmentKind)]
)
def test_real_optimization_explicit_keep_history_save_without_fabricated_baseline(
    tmp_path: Path, language: Language, tools: tuple[AssessmentKind, ...]
) -> None:
    """Explicit Keep accepts a real optimization without changing the baseline.

    Args:
        tmp_path: Private native project.
        language: Both maintained caption languages.
        tools: Actual CBC single-tool or HiGHS all-tool route.

    Returns:
        None; frozen accepted runs survive undo, redo and Main Save/reopen exactly.
    """
    dialog = planning_dialog(tmp_path, language)
    try:
        record = dialog.current()
        dialog.edit_inputs(
            record, RotationEntryChange(replace(record.inputs, tools=tools))
        )
        before = dialog.current()
        dialog.solve.start()
        await_result(dialog)
        assert dialog.current() == before
        assert dialog.solve.preview is not None
        dialog.solve.keep_result()
        assert dialog.solve.tabs.count() == len(tools)
        accepted = dialog.current()
        assert accepted.run is not None, dialog.error.text()
        assert len(accepted.run.stages) == 2
        assert dict(accepted.run.settings)["secondary_objective"] == "minimize_ranges"
        assert dialog.solve.preview is None
        assert all(
            score == pytest.approx(50)
            for kind in tools
            for score in dialog.solve.prepared.problem.scores(
                accepted.run.arrangement, kind
            )
        )
        assert accepted.inputs.baseline is None
        assert dialog.workspace.editing.replay(redo=False)
        dialog.reload()
        assert dialog.current() == before
        assert dialog.solve.tabs.count() == 0
        assert dialog.workspace.editing.replay(redo=True)
        dialog.reload()
        assert dialog.current() == accepted
        assert dialog.workspace.save()
        with AssessmentProjectFile.open(Path(dialog.workspace.location)) as project:
            assert project.load_rotation_scenarios() == (accepted,)
    finally:
        dispose(dialog)


def test_no_path_generation_applies_only_proposal_and_replays(tmp_path: Path) -> None:
    """Feasibility generation never creates an observation or an optimization run.

    Args:
        tmp_path: Disposable native project.

    Returns:
        None; accepting a generated proposal is one reversible project operation.
    """
    dialog = planning_dialog(tmp_path, Language.ENGLISH)
    try:
        before = dialog.current()
        dialog.solve.start(True)
        await_result(dialog)
        assert dialog.pages.currentIndex() == 3
        assert dialog.solve.preview is None
        proposal = dialog.current().inputs.proposed
        assert proposal is not None
        assert dialog.current().inputs.baseline is None
        assert dialog.current().inputs.proposed == proposal
        assert dialog.current().run is None
        assert dialog.workspace.editing.replay(redo=False)
        dialog.reload()
        assert dialog.current() == before
    finally:
        dispose(dialog)


class WaitingPlanner:
    """Deterministic cancellable worker for native close/lifetime checks."""

    def __init__(self) -> None:
        """Create an explicit release signal without retaining GUI/project objects.

        Args:
            None.

        Returns:
            None; the test releases bounded work after requesting cancellation.
        """
        self.release = Event()

    def solve(
        self,
        problem: RotationPlanningProblem,
        cancelled: Callable[[], bool] | None = None,
    ) -> RotationSolution:
        """Wait for a test signal then honor cancellation before any result is returned.

        Args:
            problem: Immutable problem captured on the GUI thread.
            cancelled: Independent cancellation predicate.

        Returns:
            Real backend solution only if cancellation was not requested.

        Raises:
            RotationOptimizationError: Test requested cancellation.
        """
        assert self.release.wait(5)
        if cancelled is not None and cancelled():
            raise RotationOptimizationError("Planning cancelled.")
        return HighsRotationPlanner().solve(problem, cancelled)


def test_cancel_preserves_inputs_and_keeps_owned_thread_until_finished(
    tmp_path: Path,
) -> None:
    """Cancel suppresses application and history while retaining thread ownership.

    Args:
        tmp_path: Disposable native project.

    Returns:
        None; no thread is terminated and no partial result reaches the project.
    """
    dialog = planning_dialog(tmp_path, Language.ENGLISH)
    planner = WaitingPlanner()
    dialog.solve.optimizer = planner
    try:
        before = dialog.current()
        dialog.solve.start()
        assert dialog.solve.busy
        dialog.solve.cancel()
        assert dialog.solve.busy
        assert dialog.current() == before
        planner.release.set()
        for _ in range(500):
            QTest.qWait(10)
            if not dialog.solve.busy:
                break
        assert not dialog.solve.busy
        assert dialog.solve.preview is None
        assert dialog.current() == before
        assert not dialog.solve.keep_button.isEnabled()
    finally:
        planner.release.set()
        dispose(dialog)


def test_retired_inputs_cannot_accept_late_solver_result(tmp_path: Path) -> None:
    """A different accepted scenario input retires a still-running detached solve.

    Args:
        tmp_path: Disposable project.

    Returns:
        None; changed inputs remain intact and the stale result has no Apply path.
    """
    dialog = planning_dialog(tmp_path, Language.ENGLISH)
    planner = WaitingPlanner()
    dialog.solve.optimizer = planner
    try:
        dialog.solve.start()
        current = dialog.current()
        changed = replace(current, inputs=replace(current.inputs, start_minute=600))
        dialog.repository.replace_rotation_scenario(current, changed)
        planner.release.set()
        for _ in range(500):
            QTest.qWait(10)
            if not dialog.solve.busy:
                break
        assert not dialog.solve.busy
        assert dialog.solve.preview is None
        assert dialog.current() == changed
        assert dialog.error.text()
        assert not dialog.solve.keep_button.isEnabled()
    finally:
        planner.release.set()
        dispose(dialog)


def test_window_close_cancels_and_waits_for_owned_worker(tmp_path: Path) -> None:
    """Native close retains the window until cooperative cancellation finishes.

    Args:
        tmp_path: Disposable project directory.

    Returns:
        None; solver lifetime never outlives a released GUI owner.
    """
    dialog = planning_dialog(tmp_path, Language.ENGLISH)
    planner = WaitingPlanner()
    dialog.solve.optimizer = planner
    try:
        before = dialog.current()
        dialog.solve.start()
        assert not dialog.close()
        assert dialog.solve.busy and dialog.isVisible()
        planner.release.set()
        for _ in range(500):
            QTest.qWait(10)
            if not dialog.solve.busy:
                break
        assert not dialog.solve.busy
        assert not dialog.isVisible()
        assert dialog.current() == before
        assert dialog.solve.preview is None
    finally:
        planner.release.set()
        dispose(dialog)


def test_generated_proposal_rejects_later_input_change(tmp_path: Path) -> None:
    """A generated proposal must pass the same freshness guard before acceptance.

    Args:
        tmp_path: Disposable project.

    Returns:
        None; a retired preview never overwrites newer accepted input.
    """
    dialog = planning_dialog(tmp_path, Language.ENGLISH)
    try:
        dialog.solve.start(True)
        current = dialog.current()
        newer = replace(current, inputs=replace(current.inputs, start_minute=600))
        dialog.repository.replace_rotation_scenario(current, newer)
        for _ in range(1000):
            if not dialog.solve.busy:
                break
            QTest.qWait(10)
        assert not dialog.solve.busy
        assert dialog.current() == newer
        assert dialog.current().run is None
        assert dialog.error.text()
    finally:
        dispose(dialog)


def test_rule_dialog_acceptance_is_one_shared_reversible_edit(tmp_path: Path) -> None:
    """The real modal returns typed rules while the guided owner records their edit.

    Args:
        tmp_path: Disposable native project.

    Returns:
        None; modal acceptance, undo and redo retain exact worker-position identities.
    """
    from PyQt5.QtCore import QTimer
    from PyQt5.QtWidgets import QApplication

    from ergotools.domain.rotation_constraints import FixedPosition, NoAdjacentHigh
    from ergotools.presentation.desktop.jrot_rules_dialog import JrotRulesDialog

    dialog = planning_dialog(tmp_path, Language.ENGLISH)
    try:
        before = dialog.current()

        def select_rules() -> None:
            """Accept a fixed low position and within-shift High restriction for W1.

            Args:
                None.

            Returns:
                None; all edits remain local until Use restrictions.
            """
            modal = QApplication.activeModalWidget()
            assert isinstance(modal, JrotRulesDialog)
            fixed, _, high, _, _ = modal.controls["W1"]
            fixed.setCurrentIndex(fixed.findData(before.inputs.targets[0].key))
            assert "J1" in fixed.currentText() and "Packing" in fixed.currentText()
            high.setChecked(True)
            modal.accept_rules()

        QTimer.singleShot(0, select_rules)
        dialog.edit_rules()
        assert dialog.current().inputs.rules == (
            FixedPosition("W1", before.inputs.targets[0].key),
            NoAdjacentHigh("W1"),
        )
        assert dialog.workspace.editing.replay(redo=False)
        dialog.reload()
        assert dialog.current() == before
        assert dialog.workspace.editing.replay(redo=True)
        dialog.reload()
        assert len(dialog.current().inputs.rules) == 2
    finally:
        dispose(dialog)


def test_review_navigation_retires_matrix_from_changed_inputs(tmp_path: Path) -> None:
    """A retired result disappears on review rather than resembling current data.

    Args:
        tmp_path: Disposable current project.

    Returns:
        None; visual matrix ownership follows the same freshness rules as Apply.
    """
    dialog = planning_dialog(tmp_path, Language.ENGLISH)
    try:
        dialog.solve.start()
        await_result(dialog)
        assert dialog.solve.tabs.count() == 3
        dialog.solve.keep_result()
        current = dialog.current()
        newer = replace(current, inputs=replace(current.inputs, start_minute=600))
        dialog.repository.replace_rotation_scenario(current, newer)
        dialog.go(6)
        assert dialog.solve.preview is None
        assert dialog.solve.tabs.count() == 3
        assert not dialog.solve.keep_button.isEnabled()
        assert dialog.current() == newer
    finally:
        dispose(dialog)

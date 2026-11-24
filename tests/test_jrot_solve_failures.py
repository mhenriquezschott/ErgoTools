"""Truthful guided failure UI and real infeasibility/limit boundaries.

All projects are private. Controlled native statuses exercise deterministic timeout
paths without depending on CPU speed; actual HiGHS proves the combined-rule case.
"""

from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import highspy
import pytest
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QMessageBox

from ergotools.application.rotation_entry import RotationEntryChange
from ergotools.application.rotation_optimization import (
    RotationFailureReason,
    RotationOptimizationError,
)
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.rotation import RotationSolution, RotationSolveStatus
from ergotools.domain.rotation_constraints import FixedPosition, NoAdjacentHigh
from ergotools.domain.rotation_planning import (
    RotationPlanningProblem,
    allowed_positions,
)
from ergotools.infrastructure.highs_rotation_optimizer import HighsRotationPlanner
from ergotools.presentation.desktop.jrot_dialog import JrotDialog
from tests.test_jrot_guided_ui import dispose
from tests.test_jrot_planning_ui import await_result, planning_dialog
from tests.test_rotation_planning import planning


@dataclass
class UnsuccessfulPlanner:
    """Deterministic worker-boundary failure, independent of native solver speed.

    Attributes:
        reason: Portable adapter failure category to present.
    """

    reason: RotationFailureReason

    def solve(
        self,
        problem: RotationPlanningProblem,
        cancelled: Callable[[], bool] | None = None,
    ) -> RotationSolution:
        """Reject without producing any schedule or accessing the project.

        Args:
            problem: Detached input accepted by controller preparation.
            cancelled: Optional cooperative cancellation intent.

        Returns:
            Never returns a schedule.

        Raises:
            RotationOptimizationError: Controlled backend failure.
        """
        raise RotationOptimizationError("Controlled native diagnostic", self.reason)


def wait_finished(dialog: JrotDialog) -> None:
    """Process queued completion without requiring successful optimization.

    Args:
        dialog: Private window owning the bounded worker.

    Returns:
        None; fails if the worker remains owned after five seconds.
    """
    for _ in range(500):
        if not dialog.solve.busy:
            break
        QTest.qWait(10)
    assert not dialog.solve.busy


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("retained", [False, True])
@pytest.mark.parametrize("reason", list(RotationFailureReason))
def test_failure_stays_visible_without_baseline_or_retained_fallback(
    tmp_path: Path, language: Language, retained: bool, reason: RotationFailureReason
) -> None:
    """Failed attempts cannot resemble success after navigation or refresh.

    Args:
        tmp_path: Private native file/settings directory.
        language: English or Spanish notices.
        retained: Whether a prior explicitly kept result must remain stored.
        reason: Proven infeasible, bounded no-result or other error.

    Returns:
        None; modal and persistent notices agree, no matrix/Keep/report is offered,
        exact prior data survives, and a successful retry restores normal behavior.
    """
    dialog = planning_dialog(tmp_path, language)
    try:
        if retained:
            dialog.solve.start()
            await_result(dialog)
            dialog.solve.keep_result()
            assert dialog.current().run is not None
        before = dialog.current()
        dialog.solve.optimizer = UnsuccessfulPlanner(reason)
        with patch.object(QMessageBox, "warning") as warning:
            dialog.solve.start()
            wait_finished(dialog)
            warning.assert_called_once()
            message = warning.call_args.args[2]
        assert message == dialog.solve.status.text() == dialog.error.text()
        assert "Controlled native" not in message
        assert dialog.current() == before
        assert dialog.solve.unsuccessful_attempt
        assert dialog.solve.preview is None and dialog.solve.run is None
        assert dialog.solve.tabs.count() == 0
        assert not dialog.solve.keep_button.isEnabled()
        for page in (7, 6, 7):
            dialog.go(page)
            dialog.solve.refresh()
            dialog.project_page()
            assert dialog.solve.status.text() == message
            assert dialog.solve.tabs.count() == dialog.comparison.tabs.count() == 0
            assert dialog.comparison.run is None
            assert dialog.comparison.notice.text() == message
            assert not dialog.comparison.report_button.isEnabled()
            assert not dialog.comparison.replace_button.isEnabled()
        dialog.solve.optimizer = HighsRotationPlanner()
        dialog.solve.start()
        await_result(dialog)
        assert not dialog.solve.unsuccessful_attempt
        assert dialog.solve.tabs.count() > 0
        assert dialog.current() == before
    finally:
        dispose(dialog)


@pytest.mark.parametrize("generation", [False, True])
def test_real_solver_infeasibility_reaches_dialog_without_changing_entry(
    tmp_path: Path, generation: bool
) -> None:
    """Real native infeasibility must be visible for optimization and proposal entry.

    Args:
        tmp_path: Private project, independent of maintained examples.
        generation: Failure in step 04 generation or step 07 optimization.

    Returns:
        None; actual solver diagnosis reaches the modal/status and no assignments
        or preserved result are changed.
    """
    dialog = planning_dialog(tmp_path, Language.ENGLISH)
    try:
        workspace = dialog.workspace
        for job in workspace.read_jobs().jobs.jobs:
            values = workspace.read_job_risk().risk.for_job(job.job_id)
            workspace.save_job_details(
                workspace.read_jobs(),
                workspace.read_job_risk(),
                job,
                replace(
                    values,
                    measurements=tuple(
                        replace(m, probability_percent=100) for m in values.measurements
                    ),
                ),
            )
        current = dialog.current()
        changed = replace(
            current.inputs, rules=(NoAdjacentHigh("W1"), NoAdjacentHigh("W2"))
        )
        assert dialog.edit_inputs(current, RotationEntryChange(changed))
        before = dialog.current()
        with patch.object(QMessageBox, "warning") as warning:
            dialog.solve.start(generation)
            wait_finished(dialog)
            warning.assert_called_once()
        assert "No feasible rotation exists" in dialog.solve.status.text()
        assert dialog.solve.unsuccessful_attempt and dialog.solve.tabs.count() == 0
        assert dialog.current() == before
    finally:
        dispose(dialog)


@pytest.mark.parametrize(
    "tools",
    [
        (AssessmentKind.LIFFT,),
        (AssessmentKind.LIFFT, AssessmentKind.DUET),
        tuple(AssessmentKind),
    ],
)
@pytest.mark.parametrize("generation", [False, True])
def test_combined_rules_are_infeasible_despite_valid_static_staffing(
    tools: tuple[AssessmentKind, ...], generation: bool
) -> None:
    """Two High Jobs cannot alternate over three restricted moving workers.

    Args:
        tools: One, two or three actual analyzed models.
        generation: Feasibility-only or two-pass optimization.

    Returns:
        None; static matching passes, HiGHS proves infeasible, and relaxing one
        adjacency rule produces an independently validated real solution.
    """
    problem = planning(tuple((75, 65, 5, 10, 15) for _ in tools), (60,) * 4, tools)
    keys = problem.target_keys
    rules = (
        NoAdjacentHigh("W0"),
        NoAdjacentHigh("W1"),
        NoAdjacentHigh("W2"),
        FixedPosition("W3", keys[3]),
        FixedPosition("W4", keys[4]),
    )
    problem = replace(
        problem, inputs=replace(problem.inputs, rules=rules), generation=generation
    )
    assert len(allowed_positions(problem.inputs)) == 5
    with pytest.raises(RotationOptimizationError) as failure:
        HighsRotationPlanner().solve(problem)
    assert failure.value.reason is RotationFailureReason.INFEASIBLE
    relaxed = replace(
        problem, inputs=replace(problem.inputs, rules=rules[:2] + rules[3:])
    )
    result = HighsRotationPlanner().solve(relaxed)
    relaxed.validate_schedule(result.schedule)


@pytest.mark.parametrize("pass_number", [1, 2])
@pytest.mark.parametrize("has_incumbent", [False, True])
def test_time_limit_never_fabricates_a_result_or_a_proof_of_infeasibility(
    pass_number: int, has_incumbent: bool
) -> None:
    """Distinguish a validated bounded incumbent from time exhaustion in either pass.

    Args:
        pass_number: First minimax or second balancing pass.
        has_incumbent: Whether the selected time-limited native pass has a valid primal.

    Returns:
        None; no-incumbent limits raise the typed time category, including when the
        first pass succeeded; valid incumbents stay explicitly feasible, not optimal.
    """
    problem = planning(((5, 75),), (60, 60))
    get_status = highspy.Highs.getModelStatus
    get_solution = highspy.Highs.getSolution
    count = 0

    def status(model: highspy.Highs) -> highspy.HighsModelStatus:
        """Substitute a limit status only on the selected real solve pass.

        Args:
            model: Native solved model owned by the adapter.

        Returns:
            Actual status except at the deterministic bounded-stage boundary.
        """
        nonlocal count
        count += 1
        return (
            highspy.HighsModelStatus.kTimeLimit
            if count == pass_number
            else get_status(model)
        )

    def solution(model: highspy.Highs) -> object:
        """Keep real values but remove validity when the selected pass has no incumbent.

        Args:
            model: Native model with a detached real primal.

        Returns:
            Actual native solution or controlled no-incumbent snapshot.
        """
        real = get_solution(model)
        if count == pass_number and not has_incumbent:
            return SimpleNamespace(value_valid=False, col_value=real.col_value)
        return real

    with (
        patch.object(highspy.Highs, "getModelStatus", status),
        patch.object(highspy.Highs, "getSolution", solution),
    ):
        if has_incumbent:
            result = HighsRotationPlanner().solve(problem)
            assert result.stages[pass_number - 1] is RotationSolveStatus.FEASIBLE
            problem.validate_schedule(result.schedule)
        else:
            with pytest.raises(RotationOptimizationError) as failure:
                HighsRotationPlanner().solve(problem)
            assert failure.value.reason is RotationFailureReason.TIME_LIMIT


def test_changing_risk_sources_releases_the_old_failure_notice(tmp_path: Path) -> None:
    """An old proof cannot be attributed to changed risk coefficients.

    Args:
        tmp_path: Private project with source-backed scenario preparation.

    Returns:
        None; normal no-result state resumes after the accepted source changes.
    """
    dialog = planning_dialog(tmp_path, Language.ENGLISH)
    try:
        dialog.solve.optimizer = UnsuccessfulPlanner(RotationFailureReason.INFEASIBLE)
        with patch.object(QMessageBox, "warning"):
            dialog.solve.start()
            wait_finished(dialog)
        assert dialog.solve.unsuccessful_attempt
        workspace = dialog.workspace
        job = workspace.read_jobs().jobs.jobs[0]
        values = workspace.read_job_risk().risk.for_job(job.job_id)
        workspace.save_job_details(
            workspace.read_jobs(),
            workspace.read_job_risk(),
            job,
            replace(
                values,
                measurements=tuple(
                    replace(m, probability_percent=20) for m in values.measurements
                ),
            ),
        )
        dialog.solve.refresh()
        dialog.project_page()
        assert not dialog.solve.unsuccessful_attempt
        assert not dialog.error.text()
        assert dialog.solve.tabs.count() == 0
        assert not dialog.comparison.report_button.isEnabled()
    finally:
        dispose(dialog)


@pytest.mark.parametrize("other_error", [False, True])
def test_selecting_another_rotation_releases_only_the_owned_attempt_notice(
    tmp_path: Path, other_error: bool
) -> None:
    """Never carry the previous rotation's failure into a different record.

    Args:
        tmp_path: Private project and preference directory.
        other_error: Another form error must survive context cleanup when present.

    Returns:
        None; the failure banner disappears and only unrelated errors can remain.
    """
    dialog = planning_dialog(tmp_path, Language.ENGLISH)
    try:
        dialog.solve.optimizer = UnsuccessfulPlanner(RotationFailureReason.INFEASIBLE)
        with patch.object(QMessageBox, "warning"):
            dialog.solve.start()
            wait_finished(dialog)
        assert dialog.solve.unsuccessful_attempt
        other = replace(dialog.current(), scenario_id="other", name="Other rotation")
        dialog.repository.replace_rotation_scenario(None, other)
        if other_error:
            dialog.show_error("Unrelated form error")
        dialog.select_record(other)
        assert not dialog.solve.unsuccessful_attempt
        assert dialog.error.text() == ("Unrelated form error" if other_error else "")
    finally:
        dispose(dialog)

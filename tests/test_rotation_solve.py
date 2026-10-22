"""Native selected-tool solve, explicit publication and owned cancellation tests.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from threading import Event
from time import monotonic
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from ergotools.application.rotation_preparation import prepare_rotation_problem
from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_risk import JobRiskMeasurement, JobRiskValues
from ergotools.domain.language import Language
from ergotools.domain.rotation import (
    RotationBackend,
    RotationProblem,
    RotationSolution,
    RotationSolveStatus,
)
from ergotools.domain.rotation_scheme import RotationMode
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.pulp_rotation_optimizer import PulpRotationOptimizer
from ergotools.presentation.desktop.rotation_dialog import RotationDialog
from tests.test_rotation_persistence import seed

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


def two_jobs(project: AssessmentProjectFile) -> None:
    """Add the second recorded risk to the existing isolated project fixture.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.

    Returns:
        None.
    """
    project.save_job_details(
        project.load_jobs(),
        project.load_job_risk(),
        next(job for job in project.load_jobs().jobs if job.job_id == "k"),
        JobRiskValues(
            "k", (JobRiskMeasurement(AssessmentKind.LIFFT, 0.2, 80, "Metric"),)
        ),
    )


def fill_rotation(dialog: RotationDialog) -> None:
    """Fill a two-worker/two-block schedule whose best worst average is 40%.

    Args:
        dialog: Live modal/form under test; the caller owns its lifetime and event-loop
            scheduling.

    Returns:
        None.
    """
    dialog.workers_combo.setCurrentText("2")
    dialog.blocks_combo.setCurrentText("2")
    dialog.apply_scope()
    dialog.scheme_combo.setEditText("CBC-ñ")
    assert dialog.grid is not None
    for row, worker in enumerate(("w", "x")):
        dialog.grid.set_choice(row, 0, worker)
        key = dialog.grid.pool.targets[row].target.key
        for column in (1, 2):
            dialog.grid.set_choice(row, column, key)


def wait_for(predicate: Callable[[], bool]) -> None:
    """Pump native events with a bounded deadline, rather than block the GUI.

    Args:
        predicate: GUI-thread completion condition checked while pumping events under a
            bounded deadline.

    Returns:
        None.
    """
    deadline = monotonic() + 10
    while not predicate() and monotonic() < deadline:
        QTest.qWait(5)
    assert predicate()


class ControlledOptimizer:
    """Hold one pure solver call until the test releases it, then return or fail."""

    def __init__(self, outcome: str = "success") -> None:
        """Choose the deterministic result without running a second backend.

        Args:
            outcome: Controlled solver success/error/invalid result selected without
                starting another backend.

        Returns:
            None.
        """
        self.started = Event()
        self.release = Event()
        self.outcome = outcome
        self.calls = 0

    def optimize_single_tool(
        self, problem: RotationProblem, kind: AssessmentKind
    ) -> RotationSolution:
        """Exercise asynchronous ownership without widgets/repository access.

        Args:
            problem: Immutable validated tiny rotation problem; fixtures use exhaustive
                or controlled expected outcomes.
            kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
                captions are not keys.

        Returns:
            Controlled validated selected-tool solution after the test's bounded
            synchronization; no widgets/storage are accessed.

        Raises:
            TimeoutError: The explicit controlled error named by this fault-injection
                callback is reached.
            RuntimeError: The controlled reentrancy/owned-resource failure is triggered.
        """
        self.calls += 1
        self.started.set()
        if not self.release.wait(10):
            raise TimeoutError("Test did not release worker")
        if self.outcome == "error":
            raise RuntimeError("Solver unavailable")
        return RotationSolution(
            problem.current,
            RotationBackend.HIGHS
            if self.outcome == "wrong-backend"
            else RotationBackend.CBC,
            (RotationSolveStatus.FEASIBLE,),
        )

    def optimize_all_tools(self, problem: RotationProblem) -> RotationSolution:
        """Fail if the selected-tool UI routes to the multi-tool port.

        Args:
            problem: Immutable validated tiny rotation problem; fixtures use exhaustive
                or controlled expected outcomes.

        Returns:
            No value: this selected-tool-only double always raises AssertionError when
            the multi-tool port is called.

        Raises:
            AssertionError: The selected-tool action incorrectly calls the multi-tool
                optimizer instead of the CBC port.
        """
        raise AssertionError("Selected-tool action must use CBC")


@pytest.mark.parametrize("language", list(Language))
def test_actual_cbc_preview_transfer_explicit_save(
    tmp_path: Path, language: Language
) -> None:
    """Actual CBC balances risks; neither solve nor transfer writes the project.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    path = tmp_path / "cbc.ergprj"
    with seed(path) as project, patch.object(RotationDialog, "_message"):
        two_jobs(project)
        dialog = RotationDialog(
            project, load_icons(), optimizer=PulpRotationOptimizer(), language=language
        )
        dialog.show()
        fill_rotation(dialog)
        controller = dialog.optimization
        assert controller is not None and dialog.grid is not None
        original = dialog.grid.current_scheme("CBC-ñ")
        before = path.read_bytes()
        assert dialog.optimize_button.isEnabled()
        QTest.mouseClick(dialog.optimize_button, Qt.MouseButton.LeftButton)
        wait_for(lambda: not controller.busy)
        assert controller.preview is not None
        assert dialog.grid.current_scheme("CBC-ñ") == original
        assert path.read_bytes() == before and project.load_rotation_schemes() == ()
        table = dialog.optimized_table
        for row in range(2):
            assert table.item(row, 3).text() == "40.0%"
            for column in (1, 2):
                assert not table.item(row, column).flags() & Qt.ItemFlag.ItemIsEditable
                assert (
                    table.item(row, column).data(Qt.ItemDataRole.UserRole)
                    in original.current[0].target_keys + original.current[1].target_keys
                )
        assert any("Imperial" in table.item(0, c).toolTip() for c in (1, 2))
        QTest.mouseClick(dialog.transfer_button, Qt.MouseButton.LeftButton)
        assert dialog.grid.current_scheme("CBC-ñ").current == controller.preview.current
        assert path.read_bytes() == before
        QTest.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
        (saved,) = project.load_rotation_schemes()
        assert (
            saved.mode is RotationMode.SINGLE_TOOL
            and saved.primary_kind is AssessmentKind.LIFFT
        )
        assert saved.current == controller.preview.current
        dialog.close()
    with AssessmentProjectFile.open(path) as reopened:
        assert reopened.load_rotation_schemes() == (saved,)
        assert reopened.load_job_risk().for_job("j").measurements[0].unit == "Imperial"


@pytest.mark.parametrize("close_action", ["cancel", "escape", "window"])
def test_owned_cancel_and_deferred_closure(tmp_path: Path, close_action: str) -> None:
    """Cancel never releases a running worker or publishes its eventual result.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        close_action: Named Reject/Close/window-manager action exercised while a solver
            is owned.

    Returns:
        None.
    """
    solver = ControlledOptimizer()
    with (
        seed(tmp_path / "cancel.ergprj") as project,
        patch.object(RotationDialog, "_message") as message,
    ):
        two_jobs(project)
        dialog = RotationDialog(project, load_icons(), optimizer=solver)
        dialog.show()
        fill_rotation(dialog)
        controller = dialog.optimization
        original = dialog.grid.current_scheme("CBC-ñ")
        beats = []
        timer = QTimer()
        timer.setInterval(1)
        timer.timeout.connect(lambda: beats.append(1))
        timer.start()
        controller.start()
        try:
            wait_for(solver.started.is_set)
            QTest.qWait(10)
            assert beats and controller.overlay.isVisible()
            assert (
                not dialog.setup_group.isEnabled() and not dialog.splitter.isEnabled()
            )
            dialog.resize(1720, 1000)
            _APP.processEvents()
            assert controller.overlay.geometry() == dialog.rect()
            if close_action == "cancel":
                QTest.mouseClick(controller.cancel_button, Qt.MouseButton.LeftButton)
            elif close_action == "escape":
                QTest.keyClick(dialog, Qt.Key.Key_Escape)
            else:
                dialog.close()
            assert controller.busy and dialog.isVisible()
            assert controller.worker.cancelled.is_set()
            assert not controller.cancel_button.isEnabled()
            controller.start()
            assert solver.calls == 1
        finally:
            solver.release.set()
            wait_for(lambda: not controller.busy)
            timer.stop()
        assert controller.preview is None and dialog.optimized_table.rowCount() == 0
        assert dialog.grid.current_scheme("CBC-ñ") == original
        assert project.load_rotation_schemes() == () and not message.called
        assert dialog.isVisible() == (close_action == "cancel")
        assert dialog.setup_group.isEnabled()
        dialog.close()


@pytest.mark.parametrize("outcome", ["error", "wrong-backend"])
def test_solver_failure_retains_input_and_unlocks(tmp_path: Path, outcome: str) -> None:
    """Backend failures/invalid routing are reported without publishing a table.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        outcome: Controlled solver success/error/invalid result selected without
            starting another backend.

    Returns:
        None.
    """
    solver = ControlledOptimizer(outcome)
    solver.release.set()
    with (
        seed(tmp_path / "fail.ergprj") as project,
        patch.object(RotationDialog, "_message") as message,
    ):
        two_jobs(project)
        dialog = RotationDialog(project, load_icons(), optimizer=solver)
        dialog.show()
        fill_rotation(dialog)
        controller = dialog.optimization
        original = dialog.grid.current_scheme("CBC-ñ")
        controller.start()
        wait_for(lambda: not controller.busy)
        assert message.call_args.kwargs["error"]
        assert dialog.grid.current_scheme("CBC-ñ") == original
        assert controller.preview is None and dialog.optimize_button.isEnabled()
        assert (
            dialog.optimized_table.rowCount() == 0
            and not controller.overlay.isVisible()
        )
        dialog.close()


def test_preview_and_applied_provenance_are_distinct(tmp_path: Path) -> None:
    """Save of a preview remains manual; transfer retains provenance until editing.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    solver = ControlledOptimizer()
    solver.release.set()
    with (
        seed(tmp_path / "provenance.ergprj") as project,
        patch.object(RotationDialog, "_message"),
    ):
        two_jobs(project)
        dialog = RotationDialog(project, load_icons(), optimizer=solver)
        fill_rotation(dialog)
        controller = dialog.optimization
        controller.start()
        wait_for(lambda: not controller.busy)
        dialog.save_scheme()
        assert project.load_rotation_schemes()[0].mode is RotationMode.MANUAL
        controller.transfer()
        dialog.select_kind(AssessmentKind.DUET)
        assert (
            controller.preview is None
            and controller.applied_kind is AssessmentKind.LIFFT
        )
        dialog.save_scheme()
        assert project.load_rotation_schemes()[0].mode is RotationMode.SINGLE_TOOL
        dialog.select_kind(AssessmentKind.LIFFT)
        key = dialog.grid.choice_key(0, 1)
        dialog.grid.set_choice(0, 1, None)
        dialog.grid.set_choice(0, 1, key)
        assert controller.applied_kind is None
        dialog.save_scheme()
        assert project.load_rotation_schemes()[0].mode is RotationMode.MANUAL
        controller.start()
        wait_for(lambda: not controller.busy)
        dialog.new_scheme()
        assert controller.preview is None and not dialog.optimize_button.isEnabled()
        dialog.close()


def test_invalid_limit_and_missing_measurement_do_not_start(tmp_path: Path) -> None:
    """Reject invalid boundary input without replacing a preview or calling solver.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    solver = ControlledOptimizer()
    with (
        seed(tmp_path / "invalid.ergprj") as project,
        patch.object(RotationDialog, "_message") as message,
    ):
        two_jobs(project)
        dialog = RotationDialog(project, load_icons(), optimizer=solver)
        fill_rotation(dialog)
        controller = dialog.optimization
        dialog.time_limit_input.setText("0")
        controller.start()
        assert not controller.busy and message.call_args.kwargs["error"]
        dialog.time_limit_input.setText("1")
        dialog.select_kind(AssessmentKind.DUET)
        assert not dialog.optimize_button.isEnabled()
        controller.start()
        assert not controller.busy and solver.calls == 0
        dialog.close()


def test_preparation_exact_evidence_zero_and_unused_targets(tmp_path: Path) -> None:
    """Only scheduled profiles require a risk; zero and recorded units survive.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    with seed(tmp_path / "prepare.ergprj") as project:
        dialog = RotationDialog(project, load_icons())
        grid = dialog.grid
        grid.set_choice(0, 0, "w")
        key = grid.pool.targets[0].target.key
        for column in range(1, grid.blocks + 1):
            grid.set_choice(0, column, key)
        scheme = grid.current_scheme("s")
        problem = prepare_rotation_problem(
            scheme, grid.pool, (AssessmentKind.LIFFT,), time_limit_seconds=60
        )
        assert problem.risks[0].probability_percent == 0
        for kinds in (
            (),
            (AssessmentKind.LIFFT, AssessmentKind.LIFFT),
            (AssessmentKind.DUET,),
        ):
            with pytest.raises(ValueError):
                prepare_rotation_problem(
                    scheme, grid.pool, kinds, time_limit_seconds=60
                )
        with pytest.raises(ValueError):
            prepare_rotation_problem(
                scheme,
                replace(grid.pool, project_id="foreign"),
                (AssessmentKind.LIFFT,),
                time_limit_seconds=60,
            )
        with pytest.raises(ValueError):
            prepare_rotation_problem(
                scheme,
                replace(grid.pool, targets=()),
                (AssessmentKind.LIFFT,),
                time_limit_seconds=60,
            )
        dialog.close()

"""Original comparison controls, actual HiGHS handoff and snapshot ownership.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QHeaderView

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
from tests.test_rotation_solve import (
    ControlledOptimizer,
    fill_rotation,
    two_jobs,
    wait_for,
)


def all_risks(project: AssessmentProjectFile) -> None:
    """Seed two exact profiles with zero and nonzero evidence in all three tools.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.

    Returns:
        None.
    """
    two_jobs(project)
    for identity, job_id in ((1, "j"), (2, "k")):
        current = project.load_job_risk().for_job(job_id)
        measurements = (
            *current.measurements,
            JobRiskMeasurement(
                AssessmentKind.DUET,
                0.1 if identity == 1 else 0.3,
                20 if identity == 1 else 60,
                "Imperial",
            ),
            JobRiskMeasurement(
                AssessmentKind.TST,
                0.05 if identity == 1 else 0.4,
                10 if identity == 1 else 90,
                "Metric",
            ),
        )
        project.save_job_details(
            project.load_jobs(),
            project.load_job_risk(),
            next(job for job in project.load_jobs().jobs if job.job_id == job_id),
            JobRiskValues(job_id, measurements),
        )


@pytest.mark.parametrize("language", list(Language))
def test_actual_highs_tabs_apply_save_reopen(
    tmp_path: Path, language: Language
) -> None:
    """HiGHS opens the original tabs; only Apply transfers, and only Save writes.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    path = tmp_path / "all.ergprj"
    with seed(path) as project, patch.object(RotationDialog, "_message"):
        all_risks(project)
        dialog = RotationDialog(
            project, load_icons(), optimizer=PulpRotationOptimizer(), language=language
        )
        dialog.show()
        fill_rotation(dialog)
        controller = dialog.optimization
        before = path.read_bytes()
        original = dialog.grid.current_scheme("CBC-ñ")
        assert dialog.optimize_all_button.isEnabled()
        QTest.mouseClick(dialog.optimize_all_button, Qt.MouseButton.LeftButton)
        wait_for(lambda: not controller.busy)
        comparison = controller.comparison
        assert comparison is not None and comparison.isVisible()
        assert controller.preview is None and dialog.optimized_table.rowCount() == 0
        assert dialog.grid.current_scheme("CBC-ñ") == original
        assert path.read_bytes() == before and project.load_rotation_schemes() == ()
        assert comparison.tabs.count() == 3
        for index, kind in enumerate(AssessmentKind):
            comparison.tabs.setCurrentIndex(index)
            current, optimized = comparison.tables[kind]
            assert current.item(0, 3).text() in ("0.0%", "20.0%", "10.0%")
            assert optimized.item(0, 3).text() in ("40.0%", "50.0%")
            assert not optimized.item(0, 1).flags() & Qt.ItemFlag.ItemIsEditable
            assert optimized.item(0, 1).data(Qt.ItemDataRole.UserRole) in {
                t.key for t in original.targets
            }
        # Tabs inspect risks; the source Apply targets the parent's current tool.
        QTest.mouseClick(comparison.apply_button, Qt.MouseButton.LeftButton)
        assert controller.comparison is None and not comparison.isVisible()
        assert dialog.kind is AssessmentKind.LIFFT
        assert controller.preview.mode is RotationMode.ALL_TOOLS
        assert controller.applied_kind is None
        assert dialog.grid.current_scheme("CBC-ñ").current == controller.preview.current
        assert path.read_bytes() == before
        QTest.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
        (saved,) = project.load_rotation_schemes()
        assert saved.mode is RotationMode.ALL_TOOLS and saved.primary_kind is None
        dialog.select_kind(AssessmentKind.DUET)
        dialog.save_scheme()
        assert project.load_rotation_schemes() == (saved,)
        dialog.close()
    with AssessmentProjectFile.open(path) as reopened:
        assert reopened.load_rotation_schemes() == (saved,)
        assert {t.job_id for t in saved.targets} == {"j", "k"}
        assert reopened.load_job_risk().for_job("j").measurements[0].unit == "Imperial"


@pytest.mark.parametrize("reset", ["edit", "scope", "close"])
def test_single_comparison_and_real_parent_reset(tmp_path: Path, reset: str) -> None:
    """The modeless comparison is owned and removed when its real inputs change.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        reset: Named Reset/Clear/Cancel operation used to characterize local history
            boundaries.

    Returns:
        None.
    """
    with (
        seed(tmp_path / "single.ergprj") as project,
        patch.object(RotationDialog, "_message"),
    ):
        all_risks(project)
        dialog = RotationDialog(
            project, load_icons(), optimizer=PulpRotationOptimizer()
        )
        dialog.show()
        fill_rotation(dialog)
        controller = dialog.optimization
        controller.start()
        wait_for(lambda: not controller.busy)
        assert dialog.compare_button.isEnabled()
        QTest.mouseClick(dialog.compare_button, Qt.MouseButton.LeftButton)
        comparison = controller.comparison
        assert (
            comparison.isVisible()
            and comparison.tabs is None
            and comparison.apply_button is None
        )
        assert set(comparison.tables) == {AssessmentKind.DUET, AssessmentKind.TST}
        assert comparison.minimumWidth() == 960 and comparison.minimumHeight() == 650
        table = comparison.tables[AssessmentKind.DUET][1]
        assert table.item(0, 3).text() == "40.0%"
        assert table.rowHeight(0) == 50
        assert table.item(0, 0).textAlignment() == int(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        assert (
            table.horizontalHeader().sectionResizeMode(0)
            == QHeaderView.ResizeMode.Stretch
        )
        before = project.load_rotation_schemes()
        if reset == "edit":
            dialog.grid.set_choice(0, 1, None)
        elif reset == "scope":
            dialog.apply_scope()
        else:
            dialog.close()
        assert controller.comparison is None and not comparison.isVisible()
        assert project.load_rotation_schemes() == before
        dialog.close()


class ControlledAllOptimizer(ControlledOptimizer):
    """Hold the all-tool port to exercise the shared owned-worker path."""

    def optimize_all_tools(self, problem: RotationProblem) -> RotationSolution:
        """Return the fixture's valid current schedule with two HiGHS stages.

        Args:
            problem: Immutable validated tiny rotation problem; fixtures use exhaustive
                or controlled expected outcomes.

        Returns:
            Current fixture schedule with the HiGHS backend and two feasible stages,
            returned only after the owned release event is signaled.

        Raises:
            TimeoutError: The explicit controlled error named by this fault-injection
                callback is reached.
            RuntimeError: The controlled reentrancy/owned-resource failure is triggered.
        """
        self.calls += 1
        self.started.set()
        if not self.release.wait(10):
            raise TimeoutError("Unreleased test solver")
        if self.outcome == "error":
            raise RuntimeError("HiGHS unavailable")
        return RotationSolution(
            problem.current,
            RotationBackend.CBC
            if self.outcome == "wrong-backend"
            else RotationBackend.HIGHS,
            (RotationSolveStatus.FEASIBLE, RotationSolveStatus.FEASIBLE),
        )


@pytest.mark.parametrize("outcome", ["cancel", "close", "error", "wrong-backend"])
def test_all_worker_cancellation_and_failure(tmp_path: Path, outcome: str) -> None:
    """All-tool cancellation/errors never open comparison or change current data.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        outcome: Controlled solver success/error/invalid result selected without
            starting another backend.

    Returns:
        None.
    """
    with (
        seed(tmp_path / "worker.ergprj") as project,
        patch.object(RotationDialog, "_message") as message,
    ):
        all_risks(project)
        solver = ControlledAllOptimizer(outcome)
        dialog = RotationDialog(project, load_icons(), optimizer=solver)
        dialog.show()
        fill_rotation(dialog)
        controller = dialog.optimization
        original = dialog.grid.current_scheme("CBC-ñ")
        controller.start_all()
        try:
            wait_for(solver.started.is_set)
            assert "All Tools" in controller.label.text()
            assert (
                not dialog.optimize_button.isEnabled()
                and not dialog.optimize_all_button.isEnabled()
            )
            controller.start()
            assert solver.calls == 1
            if outcome == "cancel":
                controller.cancel()
            elif outcome == "close":
                dialog.close()
            assert controller.busy and dialog.isVisible()
        finally:
            solver.release.set()
            wait_for(lambda: not controller.busy)
        assert controller.preview is None and controller.comparison is None
        assert dialog.grid.current_scheme("CBC-ñ") == original
        assert message.called == (outcome in ("error", "wrong-backend"))
        assert project.load_rotation_schemes() == ()
        dialog.close()


def test_missing_other_tool_risk_blocks_all_and_compare(tmp_path: Path) -> None:
    """Missing probabilities never appear as zero or silently route to CBC.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    with (
        seed(tmp_path / "missing.ergprj") as project,
        patch.object(RotationDialog, "_message") as message,
    ):
        two_jobs(project)
        solver = ControlledAllOptimizer()
        dialog = RotationDialog(project, load_icons(), optimizer=solver)
        fill_rotation(dialog)
        controller = dialog.optimization
        assert (
            dialog.optimize_button.isEnabled()
            and not dialog.optimize_all_button.isEnabled()
        )
        controller.start_all()
        assert solver.calls == 0 and message.call_args.kwargs["error"]
        solver.release.set()
        controller.start()
        wait_for(lambda: not controller.busy)
        assert controller.preview is not None and not dialog.compare_button.isEnabled()
        controller.compare()
        assert controller.comparison is None
        dialog.close()

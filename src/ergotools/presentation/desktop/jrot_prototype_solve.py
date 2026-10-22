"""Disposable prototype solver thread using the unchanged optimization port.

Presentation orchestration only. The worker holds immutable numerical input, not a
repository, window state or writer. Its owning dialog defers destruction until finished;
interruption suppresses publication rather than terminating a solver unsafely.
"""

import logging

from PyQt5.QtCore import QObject, QThread

from ergotools.application.rotation_optimization import RotationOptimizer
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation import RotationBackend, RotationProblem, RotationSolution

# Thread-boundary diagnostics use the existing logging configuration, never project I/O.
_LOGGER = logging.getLogger(__name__)


class PrototypeSolveThread(QThread):
    """One bounded real solve with an owned result/error, never project publication."""

    def __init__(
        self,
        optimizer: RotationOptimizer,
        problem: RotationProblem,
        kinds: tuple[AssessmentKind, ...],
        parent: QObject,
    ) -> None:
        """Retain immutable inputs before starting on the owning GUI thread.

        Args:
            optimizer: Existing injected CBC/HiGHS adapter through its application port.
            problem: Complete equal-duration input without preview-only restrictions.
            kinds: Exactly one tool or all three, validated before construction.
            parent: Dialog owner that remains alive until this worker finishes.

        Returns:
            None; construction does not start a solve.
        """
        super().__init__(parent)
        self.optimizer = optimizer
        self.problem = problem
        self.kinds = kinds
        self.solution: RotationSolution | None = None
        self.error = ""

    def run(self) -> None:
        """Solve and independently validate staffing before publishing a scratch result.

        Args:
            None.

        Returns:
            None; exceptions become a visible failure, not a fallback schedule/backend.
        """
        try:
            solution = (
                self.optimizer.optimize_all_tools(self.problem)
                if len(self.kinds) == 3
                else self.optimizer.optimize_single_tool(self.problem, self.kinds[0])
            )
            self.problem.validate_schedule(solution.schedule)
            expected = (
                RotationBackend.HIGHS if len(self.kinds) == 3 else RotationBackend.CBC
            )
            if solution.backend is not expected or len(solution.stages) != (
                2 if len(self.kinds) == 3 else 1
            ):
                raise ValueError("Unexpected solver backend or stage evidence.")
            if not self.isInterruptionRequested():
                self.solution = solution
        except Exception as error:
            # GUI worker boundary: log unexpected adapter failures and retain a message.
            _LOGGER.exception("Developer JROT prototype solve failed")
            self.error = str(error) or type(error).__name__

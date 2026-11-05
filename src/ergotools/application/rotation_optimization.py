"""Replaceable JROT optimization port; no solver types cross into the core.

Application layer. Define immutable capability/operation contracts independently of
Qt and storage implementations. Callers own modal consent and borrowed project
lifetime; concrete adapters own I/O and transaction enforcement.
"""

from collections.abc import Callable
from typing import Protocol

from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation import (
    RotationProblem,
    RotationSolution,
    WorkerRotation,
)
from ergotools.domain.rotation_planning import RotationPlanningProblem


class RotationOptimizationError(RuntimeError):
    """Required backend failed or did not produce a complete feasible schedule."""


class RotationOptimizer(Protocol):
    """Run the reference models without persistence, Qt or presentation coupling."""

    def optimize_single_tool(
        self, problem: RotationProblem, kind: AssessmentKind
    ) -> RotationSolution:
        """Minimize maximum worker average with HiGHS.

        Args:
            problem: Immutable complete schedule and frozen target probabilities in
                percent, with a per-stage time limit in seconds.
            kind: Explicit supported model whose complete target risk coefficients must
                be available.

        Returns:
            Validated schedule minimizing maximum worker average risk in percent,
            with termination evidence under configured tolerances.

        Raises:
            ValueError: The requested model or its complete target risk coefficients are
                invalid.
            RotationOptimizationError: The backend fails or produces no
                complete validated feasible schedule.
        """
        ...

    def optimize_all_tools(self, problem: RotationProblem) -> RotationSolution:
        """Run the two-stage three-tool HiGHS objective; limits apply per stage.

        Args:
            problem: Immutable complete schedule and frozen target probabilities in
                percent, with a per-stage time limit in seconds.

        Returns:
            Validated two-stage three-tool HiGHS schedule with stage evidence; each
            stage receives the configured time bound.

        Raises:
            ValueError: Required model risks or schedule inputs are incomplete/invalid.
            RotationOptimizationError: HiGHS is unavailable or either stage produces no
                complete validated feasible schedule.
        """
        ...


class RotationSolveShape(Protocol):
    """Shared extraction/validation shape for original and duration-aware models."""

    @property
    def worker_ids(self) -> tuple[str, ...]:
        """Read participant identities without manufacturing a baseline.

        Args:
            None.

        Returns:
            Exact extraction row order.
        """
        ...

    @property
    def target_keys(self) -> tuple[str, ...]:
        """Read distinct exact positions.

        Args:
            None.

        Returns:
            Opaque target identities.
        """
        ...

    @property
    def num_blocks(self) -> int:
        """Read positive assignment horizon.

        Args:
            None.

        Returns:
            Productive block count.
        """
        ...

    @property
    def time_limit_seconds(self) -> float:
        """Read the independently applied per-stage budget.

        Args:
            None.

        Returns:
            Positive seconds, never a shared split budget.
        """
        ...

    def validate_schedule(self, schedule: tuple[WorkerRotation, ...]) -> None:
        """Independently validate an extracted candidate.

        Args:
            schedule: Complete candidate in exact participant order.

        Returns:
            None for valid staffing and applicable hard rules.
        """
        ...


class RotationPlanningOptimizer(Protocol):
    """Replaceable planning solver without project mutation ownership."""

    def solve(
        self,
        problem: RotationPlanningProblem,
        cancelled: Callable[[], bool] | None = None,
    ) -> RotationSolution:
        """Generate feasibility or optimize the requested selected-tool objective.

        Args:
            problem: Frozen dated/timed positions, probabilities and restrictions.
            cancelled: Optional cooperative intent checked between bounded solve
            stages.

        Returns:
            Independently validated schedule and actual backend/stage evidence.

        Raises:
            RotationOptimizationError: Backend, feasibility, incumbent or
            cancellation failure.
        """
        ...

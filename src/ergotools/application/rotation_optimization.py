"""Replaceable JROT optimization port; no solver types cross into the core.

Application layer. Define immutable capability/operation contracts independently of Qt
and storage implementations. Callers own modal consent and borrowed project lifetime;
concrete adapters own I/O and transaction enforcement.
"""

from typing import Protocol

from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation import RotationProblem, RotationSolution


class RotationOptimizationError(RuntimeError):
    """Required backend failed or did not produce a complete feasible schedule."""


class RotationOptimizer(Protocol):
    """Run the reference models without persistence, Qt or presentation coupling."""

    def optimize_single_tool(
        self, problem: RotationProblem, kind: AssessmentKind
    ) -> RotationSolution:
        """Minimize maximum worker average percent with CBC; reject missing risks.

        Args:
            problem: Immutable complete schedule and frozen target probabilities in
                percent, with a per-stage time limit in seconds.
            kind: Explicit supported model whose complete target risk coefficients must
                be available.

        Returns:
            Validated CBC schedule minimizing maximum worker average risk in percent,
            with termination evidence under configured tolerances.

        Raises:
            ValueError: The requested model or its complete target risk coefficients are
                invalid.
            RotationOptimizationError: CBC is unavailable, fails, or produces no
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

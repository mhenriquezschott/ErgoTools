"""Reviewed narrow HiGHS1.11.0 public API used by the direct JROT adapter.

Typing boundary only; no executable solver replacement. Contracts checked against
installed highspy/highs.py and native _core signatures. Upstream names and the
expression-returning equality operator are intentional external API exceptions.
Risk coefficients are percentages; time_limit is seconds and mip_rel_gap dimensionless.
"""

from collections.abc import Iterable
from enum import IntEnum

from .highs import highs_linear_expression as highs_linear_expression
from .highs import highs_var as highs_var

class HighsStatus(IntEnum):
    """Native API call result, separate from model or primal feasibility."""

    kError = -1
    kOk = 0
    kWarning = 1

class HighsModelStatus(IntEnum):
    """Native reason a solve ended; limits alone never certify a primal solution."""

    kOptimal = 7
    kInfeasible = 8
    kTimeLimit = 13
    kIterationLimit = 14
    kObjectiveBound = 11
    kObjectiveTarget = 12
    kSolutionLimit = 16
    kInterrupt = 17
    kMemoryLimit = 18

class SolutionStatus(IntEnum):
    """Native independently reported solution feasibility status."""

    kSolutionStatusFeasible = 2

class HighsSolution:
    """Primal values indexed by model column and an explicit validity flag."""

    value_valid: bool
    col_value: list[float]

class HighsInfo:
    """Native solve evidence; primal feasibility is checked before extracting rows."""

    primal_solution_status: int

class Highs:
    """Owned native model with linear-expression helpers and explicit run lifecycle."""

    def __init__(self) -> None:
        """Create an empty model with no project or Qt ownership.

        Args:
            None.

        Returns:
            None; no solve is performed.
        """
        ...

    def addBinary(self, obj: float = 0, name: str | None = None) -> highs_var:
        """Add a zero/one integer column to this model.

        Args:
            obj: Initial objective coefficient.
            name: Opaque solver-facing name; application IDs remain outside the solver.

        Returns:
            Index wrapper bound to this model.
        """
        ...

    def addVariable(self, lb: float = 0, name: str | None = None) -> highs_var:
        """Add the exercised nonnegative continuous ceiling/floor column.

        Args:
            lb: Finite lower bound; upper bound defaults to infinity.
            name: Solver-facing ceiling/floor identity.

        Returns:
            Index wrapper; no objective is solved.
        """
        ...

    @staticmethod
    def qsum(
        items: Iterable[highs_var | highs_linear_expression | float],
    ) -> highs_linear_expression:
        """Combine linear terms, including an empty zero expression.

        Args:
            items: Variable/expression/coefficient iterable in caller order.

        Returns:
            Combined linear expression, never a computed solution score.
        """
        ...

    def addConstr(self, expr: highs_linear_expression) -> object:
        """Attach one previously constructed bounded expression.

        Args:
            expr: Equality or inequality over columns owned by this model.

        Returns:
            Native constraint wrapper; the adapter does not inspect it.
        """
        ...

    def setObjective(self, obj: highs_var | highs_linear_expression) -> None:
        """Replace objective costs while retaining existing constraints.

        Args:
            obj: Unbounded linear expression or single variable to minimize.

        Returns:
            None; solve remains explicit through run.
        """
        ...

    def getModel(self) -> object:
        """Copy the native coefficients, bounds and integrality for a new solve pass.

        Args:
            None.

        Returns:
            Native model snapshot; no previous solve clock or incumbent is attached.
        """
        ...

    def passModel(self, model: object) -> HighsStatus:
        """Load the exact frozen model into this fresh native solver.

        Args:
            model: Native model snapshot from getModel, including current objective.

        Returns:
            Native API status; rejected model data never authorize a solve.
        """
        ...

    def setSolution(self, solution: HighsSolution) -> HighsStatus:
        """Retain a validated native primal on the owned model for ceiling reads.

        Args:
            solution: Current-pass native solution after independent staffing checks.

        Returns:
            Native status; no optimizer is invoked by retaining this result.
        """
        ...

    def setOptionValue(self, name: str, value: bool | float) -> HighsStatus:
        """Set an exercised logging, time-budget or relative-gap option.

        Args:
            name: output_flag, time_limit or mip_rel_gap.
            value: Boolean logging flag, seconds, or dimensionless relative gap.

        Returns:
            Native success/warning/error; the adapter rejects errors.
        """
        ...

    def run(self) -> HighsStatus:
        """Optimize the current owned model with configured stage options.

        Args:
            None.

        Returns:
            Native API status; model status and primal evidence require separate checks.
        """
        ...

    def getModelStatus(self) -> HighsModelStatus:
        """Read the last model termination reason.

        Args:
            None.

        Returns:
            Native infeasibility or time/iteration/interruption/optimal stopping reason.
        """
        ...

    def getSolution(self) -> HighsSolution:
        """Read the current primal values with their explicit validity flag.

        Args:
            None.

        Returns:
            Native snapshot; empty/stale invalid solutions must be rejected.
        """
        ...

    def getInfo(self) -> HighsInfo:
        """Read independent primal feasibility evidence.

        Args:
            None.

        Returns:
            Native solve information; no model values are altered.
        """
        ...

    def modelStatusToString(self, status: HighsModelStatus) -> str:
        """Format the native model termination reason for owned errors.

        Args:
            status: Native termination code from getModelStatus.

        Returns:
            HiGHS diagnostic caption; never shown as injury probability.
        """
        ...

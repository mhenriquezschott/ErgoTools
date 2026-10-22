"""Declare the exercised PuLP 3.2.2 API for the JROT infrastructure adapter.

Typing boundary, not executable application code. PuLP lacks a py.typed marker;
these reviewed declarations describe only calls used by the approved solver
adapter, not every upstream overload or optional argument. Contracts were checked
against the installed baseline source. Upstream spellings remain intentional
naming exceptions. Domain risks use percent; PuLP itself assigns no physical units
to coefficients. No solver is imported, installed or run by this declaration file.
"""

from collections.abc import Iterable

# PuLP objective sense 1: minimize the supplied linear objective.
LpMinimize: int
# PuLP relation sense 0: expression equals the supplied right-hand-side target.
LpConstraintEQ: int
# PuLP problem status 1: backend reports optimal under its configured tolerances.
LpStatusOptimal: int
# PuLP problem status 0: no solved status was reported; inspect incumbent evidence.
LpStatusNotSolved: int
# PuLP solution status 1: optimal solution reported by the backend.
LpSolutionOptimal: int
# PuLP solution status 2: integer-feasible incumbent without optimal certification.
LpSolutionIntegerFeasible: int
# Baseline status-code captions used only for adapter failure diagnostics.
LpStatus: dict[int, str]

class PulpSolverError(Exception):
    """Upstream solver invocation/availability failure normalized by our adapter."""

    ...

class LpConstraint:
    """Upstream linear relation; construction does not attach it to a problem."""

    def __init__(self, e: LpAffineExpression, sense: int, rhs: float) -> None:
        """Build the exercised expression/sense/target relation.

        Args:
            e: Linear left-hand expression, including any constant term.
            sense: Upstream equality/inequality code; the adapter uses LpConstraintEQ.
            rhs: Finite numeric target in the expression's coefficient scale.

        Returns:
            None. Initialize the relation without solving or modifying a problem.

        Raises:
            PulpError: The upstream constructor rejects a nonfinite target.
        """
        ...

class LpAffineExpression:
    """Upstream linear coefficients and constant; arithmetic builds new expressions."""

    def __mul__(self, other: float) -> LpAffineExpression:
        """Scale this expression by the exercised finite scalar overload.

        Args:
            other: Finite multiplier; variable-by-variable products are outside
                this reviewed linear-only declaration.

        Returns:
            New expression with every coefficient and its constant scaled.

        Raises:
            PulpError: The multiplier is NaN or infinite.
        """
        ...

    def __truediv__(self, other: float) -> LpAffineExpression:
        """Divide this expression by one finite nonzero scalar.

        Args:
            other: Finite nonzero divisor; the adapter uses a positive block count.

        Returns:
            New expression with divided coefficients and constant.

        Raises:
            ZeroDivisionError: The scalar is zero.
            PulpError: The scalar is NaN or infinite.
        """
        ...

    def __sub__(self, other: LpAffineExpression | LpVariable) -> LpAffineExpression:
        """Subtract another linear expression or a single variable.

        Args:
            other: Linear right operand; coefficients retain the caller's scale.

        Returns:
            New difference expression without changing either operand.
        """
        ...

    def __le__(self, other: LpAffineExpression | LpVariable | float) -> LpConstraint:
        """Construct an upper-bound relation without evaluating it as a boolean.

        Args:
            other: Linear expression, variable or finite numeric upper bound.

        Returns:
            New less-than-or-equal constraint; it is not yet attached to a problem.

        Raises:
            PulpError: A supplied numeric right-hand side is nonfinite.
        """
        ...

    def __ge__(self, other: LpAffineExpression | LpVariable | float) -> LpConstraint:
        """Construct a lower-bound relation without solving or testing truthiness.

        Args:
            other: Linear expression, variable or finite numeric lower bound.

        Returns:
            New greater-than-or-equal constraint, separate from problem ownership.

        Raises:
            PulpError: A supplied numeric right-hand side is nonfinite.
        """
        ...

class LpVariable:
    """Upstream decision variable; its solved value is absent before assignment."""

    def __init__(self, name: str, lowBound: float | None = ..., cat: str = ...) -> None:
        """Create the exercised named continuous/integer/binary decision variable.

        Args:
            name: Solver-facing identifier; display labels are not used as keys.
            lowBound: Optional finite lower bound; None is unbounded below.
            cat: Upstream category string. Binary sets integer bounds zero and one.

        Returns:
            None. Initialize an unsolved variable without invoking a backend.

        Raises:
            PulpError: A supplied numeric bound is nonfinite.
        """
        ...

    def __mul__(self, other: float) -> LpAffineExpression:
        """Build one scalar-weighted variable expression.

        Args:
            other: Finite numeric coefficient, such as a target probability percent.

        Returns:
            New linear expression; the variable and its solved value stay unchanged.

        Raises:
            PulpError: The coefficient is NaN or infinite.
        """
        ...

    def __sub__(self, other: LpVariable) -> LpAffineExpression:
        """Build the linear difference between two decision variables.

        Args:
            other: Variable to subtract from this variable.

        Returns:
            New two-term expression without changing either variable.
        """
        ...

    def __le__(self, other: float) -> LpConstraint:
        """Construct an upper numeric bound on this decision variable.

        Args:
            other: Finite numeric upper bound.

        Returns:
            Unattached less-than-or-equal relation; no solve occurs.

        Raises:
            PulpError: The numeric bound is nonfinite.
        """
        ...

class LpSolver:
    """Reviewed common availability interface for explicit solver selection."""

    def available(self) -> bool | str:
        """Probe whether the selected backend can be invoked in this environment.

        Args:
            None.

        Returns:
            Availability truth value, or a command path for command-line backends.
            This is not evidence that an optimization succeeded.
        """
        ...

class PULP_CBC_CMD(LpSolver):
    """Owner-approved single-tool command-line CBC backend.

    Attributes:
        path: Backend executable path reported by the installed PuLP distribution.
    """

    path: str

    def __init__(
        self, *, msg: bool = ..., timeLimit: float = ..., gapRel: float = ...
    ) -> None:
        """Configure the exercised bounded CBC solve options without solving.

        Args:
            msg: Whether upstream solver messages are emitted.
            timeLimit: Per-stage wall-time limit in seconds.
            gapRel: Dimensionless relative optimality-gap tolerance; 0.01 means 1%.

        Returns:
            None. Initialize an explicit backend; the application permits no fallback.
        """
        ...

class HiGHS(LpSolver):
    """Owner-approved multi-tool backend through the installed highspy API."""

    def __init__(
        self, *, msg: bool = ..., timeLimit: float = ..., gapRel: float = ...
    ) -> None:
        """Configure bounded HiGHS options without creating a solved schedule.

        Args:
            msg: Whether upstream backend messages are emitted.
            timeLimit: Per-stage wall-time limit in seconds.
            gapRel: Dimensionless relative optimality-gap tolerance, not percent.

        Returns:
            None. Initialize the explicitly selected backend, with no CBC fallback.
        """
        ...

class LpProblem:
    """Mutable upstream problem owned by one optimization call, never shared UI state.

    Attributes:
        status: Problem termination code; the adapter validates the extracted schedule.
        sol_status: Separate incumbent/solution status; termination alone does not
            establish a valid schedule.
    """

    status: int
    sol_status: int

    def __init__(self, name: str, sense: int) -> None:
        """Initialize an empty named optimization model.

        Args:
            name: Solver-facing model identifier.
            sense: Objective direction; the adapter uses LpMinimize.

        Returns:
            None. Initialize empty mutable constraints/objective without solving.
        """
        ...

    def addConstraint(self, constraint: LpConstraint) -> None:
        """Attach one linear relation to this problem.

        Args:
            constraint: Constructed equality/inequality relation for this model.

        Returns:
            None. Mutate the problem's constraint and referenced-variable collections.

        Raises:
            TypeError: The supplied object is not an upstream constraint.
            PulpError: Constraint names collide under the default no-overlap policy.
        """
        ...

    def setObjective(self, expression: LpAffineExpression | LpVariable) -> None:
        """Replace this problem's objective with the supplied linear expression.

        Args:
            expression: Objective expression or a single variable to optimize.

        Returns:
            None. Mutate objective/resolve state; no backend runs yet.
        """
        ...

    def solve(self, solver: LpSolver) -> int:
        """Invoke the explicitly supplied solver and populate upstream solution state.

        Args:
            solver: Chosen CBC or HiGHS backend with approved time/gap bounds.

        Returns:
            Upstream termination code; mutate problem status, solution status and
            variable values. The adapter independently validates the candidate.

        Raises:
            PulpSolverError: The backend cannot run or reports an invocation failure.

        Solver-specific errors may also propagate and are normalized by our adapter.
        """
        ...

def lpSum(
    vector: Iterable[LpAffineExpression | LpVariable | float],
) -> LpAffineExpression:
    """Build the exercised linear sum without evaluating decision variable values.

    Args:
        vector: Finite coefficient terms, variables or expressions in caller order.

    Returns:
        New linear expression with combined coefficients and constants.

    Raises:
        PulpError: A numeric term is nonfinite.
    """
    ...

def value(expression: LpVariable) -> float | None:
    """Read the upstream value of one exercised decision variable.

    Args:
        expression: Decision variable whose solver assignment is needed.

    Returns:
        Assigned numeric value, or None when no value exists. Finiteness and
        integrality remain explicit responsibilities of the rotation adapter.
    """
    ...

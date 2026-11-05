"""Typed linear wrappers exercised from highspy.highs1.11.0.

Typing boundary only. Names/operator contracts match the installed implementation;
these declarations construct no runtime solver or project state.
"""

from . import Highs

class highs_var:
    """Owned index wrapper; its HiGHS instance supplies solution values and names."""

    index: int
    highs: Highs
    name: str

    def __mul__(self, other: float) -> highs_linear_expression:
        """Build a linear expression without reading a solution.

        Args:
            other: Finite scalar coefficient.

        Returns:
            New expression scaled by the supplied operand; the model is unchanged.
        """
        ...

    def __sub__(
        self, other: highs_var | highs_linear_expression
    ) -> highs_linear_expression:
        """Build a linear expression without reading a solution.

        Args:
            other: Variable/expression to subtract.

        Returns:
            New expression minus the supplied operand; the model is unchanged.
        """
        ...

    def __le__(self, other: float) -> highs_linear_expression:
        """Construct an upper-bound relation without attaching it.

        Args:
            other: Finite numeric upper bound.

        Returns:
            Bounded expression adopted only when addConstr is called.
        """
        ...

class highs_linear_expression:
    """Sparse coefficients, offset and optional bounds; no solve runs in arithmetic."""

    def __le__(self, other: highs_var | float) -> highs_linear_expression:
        """Build a upper-bound model relation.

        Args:
            other: Variable or finite scalar on the right-hand side.

        Returns:
            Bounded expression; addConstr owns its attachment to the model.
        """
        ...

    def __ge__(self, other: highs_var | float) -> highs_linear_expression:
        """Build a lower-bound model relation.

        Args:
            other: Variable or finite scalar on the right-hand side.

        Returns:
            Bounded expression; addConstr owns its attachment to the model.
        """
        ...

    def __eq__(self, other: object) -> highs_linear_expression:  # type: ignore[override]
        """Build upstream expression equality rather than Python boolean equality.

        Args:
            other: Numeric right-hand target for the exercised equality constraints.

        Returns:
            Linear equality expression; override exception matches highspy1.11 exactly.
        """
        ...

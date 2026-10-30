"""PLOT selection and source-compatible worker demographic predicates.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

import math
from dataclasses import dataclass
from enum import StrEnum

from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.plot_scope import PlotScope
from ergotools.domain.worker_details import WorkerDetails


class PlotRiskView(StrEnum):
    """Stable reference risk display modes, independent of localized captions."""

    # Display selected-tool individual assessment evidence.
    INDIVIDUAL = "individual"
    # Display selected-tool current Job risk values.
    JOB = "job"
    # Display individual/job evidence together.
    COMPARISON = "comparison"


def paired_range(
    lower: float | None, upper: float | None
) -> tuple[float, float] | None:
    """Retain reference behavior: missing/reversed paired bounds do not filter.

    Args:
        lower: Optional nonnegative lower bound in the paired quantity's canonical
            units.
        upper: Optional nonnegative upper bound in the same units as lower.

    Returns:
        Inclusive ordered pair, or None if either bound is absent or the pair is
        reversed.

    Raises:
        ValueError: PLOT bounds must be finite and nonnegative.
    """
    for value in (lower, upper):
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError("PLOT bounds must be finite and nonnegative.")
    return (
        (lower, upper)
        if lower is not None and upper is not None and lower <= upper
        else None
    )


@dataclass(frozen=True, slots=True)
class PlotDemographics:
    """Optional canonical demographic ranges with independent filter activation.

    Attributes:
        enabled: Explicit demographic-filter activation; retained values are ignored
            when False.
        sex: Optional original Male/Female category; None imposes no sex constraint.
        age: Optional inclusive paired bounds in years, evaluated using current year
            minus birth year.
        weight_kg: Optional inclusive lower/upper body-mass pair in canonical kilograms.
        height_cm: Optional inclusive lower/upper body-height pair in canonical
            centimeters.
    """

    enabled: bool = False
    sex: str | None = None
    age: tuple[float, float] | None = None
    weight_kg: tuple[float, float] | None = None
    height_cm: tuple[float, float] | None = None

    def __post_init__(self) -> None:
        """Validate immutable paired bounds without inferring missing worker data.

        Args:
            None. Dataclass construction supplies the fields documented on
            PlotDemographics.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: Invalid PLOT demographic selection. PLOT ranges require two
                ordered finite bounds.
        """
        if type(self.enabled) is not bool or self.sex not in (None, "Male", "Female"):
            raise ValueError("Invalid PLOT demographic selection.")
        for bounds in (self.age, self.weight_kg, self.height_cm):
            if bounds is not None and (
                not isinstance(bounds, tuple)
                or len(bounds) != 2
                or paired_range(*bounds) != bounds
            ):
                raise ValueError("PLOT ranges require two ordered finite bounds.")

    def matches(self, details: WorkerDetails | None, *, current_year: int) -> bool:
        """Match inclusive ranges with the reference birth-year age policy.

        Unknown values fail only active constraints. No date/clock I/O or unit
        conversion occurs here. A worker's birthday within the year is irrelevant to the
        original birth-year predicate; this is not exact calendar age.

        Args:
            details: Optional worker demographics with body length in cm and body mass
                in kg.
            current_year: Caller-supplied positive calendar year for the original birth-
                year age predicate.

        Returns:
            True if disabled or all active constraints match; unknown values fail only
            their active constraints.

        Raises:
            ValueError: PLOT requires an explicit positive calendar year.
        """
        if type(current_year) is not int or current_year < 1:
            raise ValueError("PLOT requires an explicit positive calendar year.")
        if not self.enabled:
            return True
        details = details or WorkerDetails()
        if self.sex is not None and details.sex != self.sex:
            return False
        age = current_year - int(details.birth_date[:4]) if details.birth_date else None
        for bounds, value in (
            (self.age, age),
            (self.weight_kg, details.weight_kg),
            (self.height_cm, details.height_cm),
        ):
            if bounds is not None and (
                value is None or not bounds[0] <= value <= bounds[1]
            ):
                return False
        return True


@dataclass(frozen=True, slots=True)
class PlotFilterSelection:
    """Selected scope/model/view plus canonical demographic constraints.

    Attributes:
        scope: One plant's normalized ancestry prefixes and optional project-wide shift.
        tool: Selected stable assessment model identity, independent of localized tab
            captions.
        risk_view: Individual, job or comparison display selection; evidence ownership
            remains unchanged.
        demographics: Retained canonical demographic selection, including its
            independent activation flag.
    """

    scope: PlotScope
    tool: AssessmentKind = AssessmentKind.LIFFT
    risk_view: PlotRiskView = PlotRiskView.INDIVIDUAL
    demographics: PlotDemographics = PlotDemographics()

    def __post_init__(self) -> None:
        """Reject untyped display aliases before applying any dataset operation.

        Args:
            None. Dataclass construction supplies the fields documented on
            PlotFilterSelection.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: PLOT filters require typed selection values.
        """
        if (
            not isinstance(self.scope, PlotScope)
            or not isinstance(self.tool, AssessmentKind)
            or not isinstance(self.risk_view, PlotRiskView)
            or not isinstance(self.demographics, PlotDemographics)
        ):
            raise ValueError("PLOT filters require typed selection values.")

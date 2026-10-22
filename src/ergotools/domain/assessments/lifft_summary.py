"""LiFFT aggregation of calculated tasks, independent of widgets and persistence.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from dataclasses import dataclass

from ergotools.domain.assessments.damage_summary import (
    DamageContribution as LifftContribution,
)
from ergotools.domain.assessments.damage_summary import summarize_damage
from ergotools.domain.assessments.lifft import LifftTaskResult, probability_from_damage
from ergotools.domain.assessments.lifft_draft import DraftError, InputIssue
from ergotools.domain.model_units import MeasurementSystem

__all__ = ["LifftContribution", "LifftSummary", "summarize_lifft_tasks"]


@dataclass(frozen=True, slots=True)
class LifftSummary:
    """Ordered contributions and total with an optional probability on the 0-1 scale.

    None means the positive-damage model was not evaluated for a zero total; it does not
    assert zero injury probability. Rounded shares need not sum to 100.

    Attributes:
        system: Explicit original arm/force system: cm/N or inches/lbf; independent of
            interface language.
        contributions: Ordered task damage and percentage-of-total records.
        total_damage: Row-order sum of intrinsically rounded task damages with no
            additional total rounding.
        probability: Dimensionless model probability on 0-1; None means the logarithmic
            model was not evaluated for zero damage.
    """

    system: MeasurementSystem
    contributions: tuple[LifftContribution, ...]
    total_damage: float
    probability: float | None


def summarize_lifft_tasks(
    tasks: tuple[LifftTaskResult, ...], system: MeasurementSystem
) -> LifftSummary:
    """Aggregate complete task results using reference row-order float addition.

    Consume already-rounded task damage without further total rounding. Do not use
    sum/fsum: Python versions differ in summation policy. Each contribution rounds to
    one decimal after division by the unrounded total. Empty/zero results have zero
    shares and no model probability. No inputs are recalculated.

    Raises:
        DraftError: Invalid/duplicate identity, mismatched units, invalid damage or a
            nonfinite accumulated total. No partial summary is returned.

    Args:
        tasks: Ordered calculated task rows; each retains its stable identity and
            already- rounded model damage.
        system: Explicit source measurement system: arm in cm and force in N, or arm in
            inches and force in lbf.

    Returns:
        Source system, unrounded row-order total, percent contributions and optional 0-1
        LiFFT probability.
    """
    if not isinstance(system, MeasurementSystem):
        raise DraftError(InputIssue("validation.unit", "system"))
    tasks = tuple(tasks)
    for task in tasks:
        if task.system is not system:
            raise DraftError(InputIssue("validation.unit", "system", task.task_id))
    total, contributions = summarize_damage(
        tuple((task.task_id, task.cumulative_damage) for task in tasks)
    )
    return LifftSummary(
        system, contributions, total, probability_from_damage(total) if total else None
    )

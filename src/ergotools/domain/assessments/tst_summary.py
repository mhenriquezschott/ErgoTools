"""Isolated TST aggregation of calculated tasks, retaining original result units.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from dataclasses import dataclass

from ergotools.domain.assessments.damage_summary import (
    DamageContribution,
    summarize_damage,
)
from ergotools.domain.assessments.tst import TstTaskResult, probability_from_damage
from ergotools.domain.assessments.validation import DraftError, InputIssue
from ergotools.domain.model_units import MeasurementSystem


@dataclass(frozen=True, slots=True)
class TstSummary:
    """Ordered task results/shares and total with optional 0-1 model probability.

    None probability means zero damage was not evaluated by the logarithmic model. This
    compatibility result is not approval of direction or metric UI semantics.

    Attributes:
        system: Explicit original arm/force system: cm/N or inches/lbf; independent of
            interface language.
        tasks: Ordered calculated ST results, retaining original units and model/display
            moments.
        contributions: Ordered task damage and percentage-of-total records.
        total_damage: Row-order sum of intrinsically rounded task damages with no
            additional total rounding.
        probability: Dimensionless model probability on 0-1; None means the logarithmic
            model was not evaluated for zero damage.
    """

    system: MeasurementSystem
    tasks: tuple[TstTaskResult, ...]
    contributions: tuple[DamageContribution, ...]
    total_damage: float
    probability: float | None


def summarize_tst_tasks(
    tasks: tuple[TstTaskResult, ...], system: MeasurementSystem
) -> TstSummary:
    """Sum rounded task damage in row order, preserving moments and units.

    Validate unit agreement before shared ID/damage checks. Shares round to one decimal;
    the total remains unrounded for probability. Empty/zero input yields absent
    probability and zero shares. No source calculation or persistence occurs. Raises
    DraftError for invalid units, IDs, damage or total overflow.

    Args:
        tasks: Ordered calculated task rows; each retains its stable identity and
            already- rounded model damage.
        system: Explicit source measurement system: arm in cm and force in N, or arm in
            inches and force in lbf.

    Returns:
        Source system and task results, unrounded row-order total, percent shares and
        optional 0-1 ST probability.

    Raises:
        DraftError: Source structure, completeness, numeric validity or task identity
            violates the constraints described above; issue retains field/task context.
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
    return TstSummary(
        system,
        tasks,
        contributions,
        total,
        probability_from_damage(total) if total else None,
    )

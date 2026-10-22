"""DUET assessment totals and probability without presentation or persistence.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from dataclasses import dataclass

from ergotools.domain.assessments.damage_summary import (
    DamageContribution,
    summarize_damage,
)
from ergotools.domain.assessments.duet import DuetTaskResult, probability_from_damage


@dataclass(frozen=True, slots=True)
class DuetSummary:
    """Ordered shares and total damage, with optional probability on the 0-1 scale.

    Zero/empty totals have no evaluated probability, not a zero-risk assertion. DUET
    scale/repetitions are dimensionless; no measurement-system tag is needed.

    Attributes:
        contributions: Ordered task damage and percentage-of-total records.
        total_damage: Row-order sum of intrinsically rounded task damages with no
            additional total rounding.
        probability: Dimensionless model probability on 0-1; None means the logarithmic
            model was not evaluated for zero damage.
    """

    contributions: tuple[DamageContribution, ...]
    total_damage: float
    probability: float | None


def summarize_duet_tasks(tasks: tuple[DuetTaskResult, ...]) -> DuetSummary:
    """Aggregate already-rounded task damage in row order, then evaluate DUET risk.

    Shares round to one decimal and need not sum to 100. No inputs are recalculated and
    no partial summary is published. Shared validation raises DraftError for
    invalid/duplicate IDs, invalid damage or total overflow. Zero/empty input supplies a
    clearing summary; source-assessment completeness is a separate rule.

    Args:
        tasks: Ordered calculated task rows; each retains its stable identity and
            already- rounded model damage.

    Returns:
        Unrounded sum of model-rounded damage, percentage contributions and optional 0-1
        DUET probability.

    Raises:
        DraftError: Task identity, damage or accumulated total fails shared summary
            validation; no partial summary is returned.
    """
    total, contributions = summarize_damage(
        tuple((task.task_id, task.cumulative_damage) for task in tasks)
    )
    return DuetSummary(
        contributions, total, probability_from_damage(total) if total else None
    )

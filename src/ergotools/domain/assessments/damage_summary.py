"""Shared row-order damage totals and contributions; no model probability policy.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

import math
from dataclasses import dataclass

from ergotools.domain.assessments.validation import DraftError, InputIssue


@dataclass(frozen=True, slots=True)
class DamageContribution:
    """Stable task identity, rounded task damage and percentage of total damage.

    Attributes:
        task_id: Stable source-row identity used to associate edits, issues and
            calculated results.
        cumulative_damage: Dimensionless cumulative model damage; task calculators
            retain their documented intrinsic rounding.
        percentage: Task share of total damage in percent, rounded to one decimal;
            shares need not sum to 100.
    """

    task_id: str
    cumulative_damage: float
    percentage: float


def summarize_damage(
    tasks: tuple[tuple[str, float], ...],
) -> tuple[float, tuple[DamageContribution, ...]]:
    """Return total and ordered shares from stable task IDs and rounded damage.

    Preserve explicit += instead of sum/fsum, then round each percentage to one decimal.
    Zero totals yield zero shares. Reject blank/duplicate IDs, invalid damage and total
    overflow with DraftError. Models validate their own metadata before calling. This
    helper never combines probability formulas or unit rules.

    Args:
        tasks: Ordered pairs of stable task ID and already-rounded dimensionless task
            damage.

    Returns:
        Unrounded row-order total and ordered task contributions with shares in percent
        rounded to one decimal.

    Raises:
        DraftError: Source structure, completeness, numeric validity or task identity
            violates the constraints described above; issue retains field/task context.
    """
    seen: set[str] = set()
    total = 0.0
    for task_id, damage in tasks:
        if not task_id.strip():
            raise DraftError(InputIssue("validation.required", "task_id"))
        if task_id in seen:
            raise DraftError(InputIssue("validation.duplicate", "task_id", task_id))
        seen.add(task_id)
        if isinstance(damage, bool):
            raise DraftError(InputIssue("validation.number", "damage", task_id))
        if not math.isfinite(damage):
            raise DraftError(InputIssue("validation.nonfinite", "damage", task_id))
        if damage < 0:
            raise DraftError(InputIssue("validation.nonnegative", "damage", task_id))
        total += damage
    if not math.isfinite(total):
        raise DraftError(InputIssue("validation.overflow", "total_damage"))
    contributions = tuple(
        DamageContribution(
            task_id,
            damage,
            round(damage / total * 100, 1) if total else 0.0,
        )
        for task_id, damage in tasks
    )
    return total, contributions

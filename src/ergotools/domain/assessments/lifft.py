"""Typed LiFFT task calculations preserving the working code's numerical policy.

Source: reference pyLiFFT.py, active version-1.4.0 risk expression and lookup values;
see docs/lifft_calculation.md for hashes, evidence and limitations. Behavioral
equivalence is not independent scientific validation. No GUI, aggregation, rounding-
policy correction or automatic persistence is performed.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

import math
from dataclasses import dataclass

from ergotools.domain.assessments.lifft_data import DAMAGE_PER_CYCLE
from ergotools.domain.assessments.lifft_draft import DraftError, InputIssue, LifftTask
from ergotools.domain.assessments.lifft_validation import validate_lifft_input
from ergotools.domain.model_units import (
    MeasurementSystem,
    model_moment_for_display,
    normalize_model_load,
)


@dataclass(frozen=True, slots=True)
class LifftTaskResult:
    """Source identity and computed values, with no translated strings or colors.

    model_moment_ft_lbf is rounded before lookup as in the reference. Displayed moment
    retains the reference metric expression pending scientific review; its name
    intentionally does not assert a validated SI moment conversion. cumulative_damage is
    per-cycle damage times repetitions, rounded to 4 places.

    Attributes:
        task_id: Stable source-row identity used to associate edits, issues and
            calculated results.
        system: Explicit original arm/force system: cm/N or inches/lbf; independent of
            interface language.
        model_moment_ft_lbf: Model moment in ft.lbf; each calculator defines whether
            rounding precedes damage evaluation.
        displayed_moment: One-decimal compatible display moment; the reference metric
            expression is not a validated SI conversion.
        cumulative_damage: Dimensionless cumulative model damage; task calculators
            retain their documented intrinsic rounding.
    """

    task_id: str
    system: MeasurementSystem
    model_moment_ft_lbf: float
    displayed_moment: float
    cumulative_damage: float


def probability_from_damage(damage: float) -> float:
    """Return the reference LiFFT probability on the 0-1 scale for positive damage.

    Preserve math.log(damage, 10), coefficients and evaluation order from the active
    reference method; do not substitute a different logarithm operation.
    Zero/negative/nonfinite damage raises ValueError. Zero-damage UI summaries require a
    separate explicit policy; no scientific zero-risk claim is made.

    Args:
        damage: Positive finite cumulative model damage, dimensionless; zero needs a
            separate summary policy.

    Returns:
        Dimensionless probability on the 0-1 scale from the unchanged reference
        logarithmic expression.

    Raises:
        ValueError: Probability requires positive finite damage.
    """
    if not math.isfinite(damage) or damage <= 0:
        raise ValueError("Probability requires positive finite damage.")
    log_damage = math.log(damage, 10)
    predictor = 1.7229 + 1.0239 * log_damage
    return math.exp(predictor) / (1 + math.exp(predictor))


def calculate_lifft_task(task: LifftTask, system: MeasurementSystem) -> LifftTaskResult:
    """Calculate a complete nonnegative task with the reference lookup and rounding.

    Inputs retain their draft system: inches/lbf or cm/N, repetitions per day.
    Fractional repetitions remain supported to match reference float arithmetic. The
    model moment is rounded to one decimal before integer table indexing; values
    at/above 200 use the last entry. Damage rounds to four decimals. Metric display
    conversion happens after lookup and remains compatibility-only.

    Raises:
        DraftError: Missing, boolean, negative/nonfinite input or arithmetic overflow.
        ValueError: Unsupported unit system or metric display overflow.

    Args:
        task: Immutable source row; absent fields remain None until completeness
            validation.
        system: Explicit source measurement system: arm in cm and force in N, or arm in
            inches and force in lbf.

    Returns:
        Stable task identity, source system, one-decimal model/display moments and four-
        decimal task damage.
    """
    arm = validate_lifft_input(task.lever_arm, "lever_arm", task.task_id)
    load = validate_lifft_input(task.load, "load", task.task_id)
    repetitions = validate_lifft_input(task.repetitions, "repetitions", task.task_id)
    normalized = normalize_model_load(arm, load, system)
    raw_moment = normalized.lever_arm_in / 12 * normalized.load_lbf
    if not math.isfinite(raw_moment):
        raise DraftError(InputIssue("validation.overflow", "moment", task.task_id))
    moment = round(raw_moment, 1)
    index = min(int(moment), len(DAMAGE_PER_CYCLE) - 1)
    raw_damage = DAMAGE_PER_CYCLE[index] * repetitions
    if not math.isfinite(raw_damage):
        raise DraftError(InputIssue("validation.overflow", "damage", task.task_id))
    return LifftTaskResult(
        task.task_id,
        system,
        moment,
        model_moment_for_display(moment, system),
        round(raw_damage, 4),
    )

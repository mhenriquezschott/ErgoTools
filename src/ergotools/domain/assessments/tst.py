"""Typed TST task model preserving reference 0.1.2 arithmetic and rounding order.

The application evaluator orchestrates this pure calculator for either unit system using
the document's explicit direction convention. See docs/tst_calculation.md for reference
evidence and scientific-review limits.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

import math
from dataclasses import dataclass
from enum import StrEnum

from ergotools.domain.assessments.validation import (
    DraftError,
    InputIssue,
    validate_nonnegative_input,
)
from ergotools.domain.model_units import (
    MeasurementSystem,
    model_moment_for_display,
    normalize_model_load,
)


class TstDirection(StrEnum):
    """Stable model direction IDs; reference UI selector indices require remapping."""

    # Model branch 0: handling loads; add load and arm moments.
    HANDLING_LOADS = "0"
    # Model branch 1: load moment only; original UI position 1 requires remapping.
    DOWNWARD = "1"
    # Model branch 2: absolute load-minus-arm moment; original UI position 2 requires
    # remapping.
    HORIZONTAL = "2"


@dataclass(frozen=True, slots=True)
class TstTask:
    """Original source fields; None marks unfinished inputs without zero substitution.

    Arm/load are inches/lbf or cm/N according to the supplied measurement system.
    Repetitions are per day and can be fractional. Physical/input checks occur at
    calculation; invalid source can remain editable pending correction.

    Attributes:
        task_id: Stable source-row identity used to associate edits, issues and
            calculated results.
        direction: Typed source direction; the owning draft convention determines
            whether reference selector remapping is needed.
        lever_arm: Original arm length in cm or inches according to the owning source
            system; None is unfinished.
        load: Original force in N or lbf according to the source system; never body
            mass. None is unfinished.
        repetitions: Repetitions per work day; None means unfinished input and
            fractional values remain supported.
    """

    task_id: str
    direction: TstDirection | None = None
    lever_arm: float | None = None
    load: float | None = None
    repetitions: float | None = None

    def __post_init__(self) -> None:
        """Require stable nonblank identity for field-specific validation issues.

        Args:
            None. Dataclass construction supplies the fields documented on TstTask.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            DraftError: Source structure, completeness, numeric validity or task
                identity violates the constraints described above; issue retains
                field/task context.
        """
        if not self.task_id.strip():
            raise DraftError(InputIssue("validation.required", "task_id"))


@dataclass(frozen=True, slots=True)
class TstTaskResult:
    """Unrounded model moment, compatible displayed moment and rounded task damage.

    model_moment_ft_lbf enters the damage expression without LiFFT-style rounding.
    displayed_moment preserves the disputed metric expression; no SI claim is made.

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


def validate_tst_direction(
    direction: TstDirection | None, task_id: str
) -> TstDirection:
    """Require an explicit model direction, never a UI selector index or string.

    Args:
        direction: Typed calculator direction; saved reference selector indices require
            the draft projection first.
        task_id: Stable task identity used for lookup or field-specific validation
            diagnostics.

    Returns:
        The original typed model direction; no selector-index remapping occurs here.

    Raises:
        DraftError: Source structure, completeness, numeric validity or task identity
            violates the constraints described above; issue retains field/task context.
    """
    if direction is None:
        raise DraftError(InputIssue("validation.required", "direction", task_id))
    if not isinstance(direction, TstDirection):
        raise DraftError(InputIssue("validation.tst_direction", "direction", task_id))
    return direction


def calculate_tst_task(task: TstTask, system: MeasurementSystem) -> TstTaskResult:
    """Calculate all three reference directions and round damage to five places.

    Preserve the arm-moment piecewise constants, load * arm / 12 order, unrounded moment
    in the 681-strength expression, and one-decimal moment display. Negative, missing,
    boolean/nonfinite fields and unsupported directions raise DraftError. Numeric
    overflow/underflow to a zero denominator becomes validation.overflow; no partial
    result is returned. Unsupported units raise ValueError.

    Args:
        task: Immutable source row; absent fields remain None until completeness
            validation.
        system: Explicit source measurement system: arm in cm and force in N, or arm in
            inches and force in lbf.

    Returns:
        Stable task identity and units, unrounded model moment, one-decimal display
        moment and five-decimal damage.

    Raises:
        DraftError: Source structure, completeness, numeric validity or task identity
            violates the constraints described above; issue retains field/task context.
    """
    direction = validate_tst_direction(task.direction, task.task_id)
    arm = validate_nonnegative_input(task.lever_arm, "lever_arm", task.task_id)
    load = validate_nonnegative_input(task.load, "load", task.task_id)
    repetitions = validate_nonnegative_input(
        task.repetitions, "repetitions", task.task_id
    )
    normalized = normalize_model_load(arm, load, system)
    arm = normalized.lever_arm_in
    if 1.715 <= arm < 27:
        arm_moment = (-8.27 + 4.8223 * arm) / 12.0
    elif arm >= 27:
        arm_moment = 121.9 / 12.0
    else:
        arm_moment = 0.0
    load_moment = normalized.load_lbf * arm / 12.0
    if direction is TstDirection.HANDLING_LOADS:
        moment = load_moment + arm_moment
    elif direction is TstDirection.DOWNWARD:
        moment = load_moment
    else:
        moment = abs(load_moment - arm_moment)
    if not math.isfinite(moment):
        raise DraftError(InputIssue("validation.overflow", "moment", task.task_id))
    try:
        per_cycle = 1.0 / (10 ** ((101.25 - 100 * (moment * 12 / 681)) / 14.83))
    except (OverflowError, ZeroDivisionError) as error:
        raise DraftError(
            InputIssue("validation.overflow", "damage", task.task_id)
        ) from error
    damage = per_cycle * repetitions
    if not math.isfinite(damage):
        raise DraftError(InputIssue("validation.overflow", "damage", task.task_id))
    return TstTaskResult(
        task.task_id,
        system,
        moment,
        model_moment_for_display(moment, system),
        round(damage, 5),
    )


def probability_from_damage(damage: float) -> float:
    """Return reference TST probability on the 0-1 scale for positive finite damage.

    Preserve the active 0.864/0.928 coefficients and math.log(damage, 10) order.
    Nonpositive/nonfinite input raises ValueError; zero-total policy is separate.

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
    predictor = 0.864 + 0.928 * math.log(damage, 10)
    return math.exp(predictor) / (1 + math.exp(predictor))

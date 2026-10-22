"""Pure DUET task calculations preserving the active reference version 1.3.0.

Reference equivalence is not scientific validation. See docs/duet_calculation.md for
source provenance, input-contract differences and pending workflow scope.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

import math
from dataclasses import dataclass

from ergotools.domain.assessments.duet_data import DAMAGE_PER_CYCLE
from ergotools.domain.assessments.validation import (
    DraftError,
    InputIssue,
    validate_nonnegative_input,
)


@dataclass(frozen=True, slots=True)
class DuetTask:
    """Original task identity, dimensionless OMNI-Res index and daily repetitions.

    None represents unfinished input. Range/completeness validation happens at
    calculation; invalid drafts can be retained for correction. No units apply to the
    scale, and repetition counts may be fractional as in the reference.

    Attributes:
        task_id: Stable source-row identity used to associate edits, issues and
            calculated results.
        omni_res_scale: Dimensionless integer OMNI-Res index 0-10 at calculation; None
            means unfinished input.
        repetitions: Repetitions per work day; None means unfinished input and
            fractional values remain supported.
    """

    task_id: str
    omni_res_scale: int | None = None
    repetitions: float | None = None

    def __post_init__(self) -> None:
        """Require a usable stable identity before addressing task input issues.

        Args:
            None. Dataclass construction supplies the fields documented on DuetTask.

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
class DuetTaskResult:
    """Immutable task identity and model damage rounded to five decimal places.

    Attributes:
        task_id: Stable source-row identity used to associate edits, issues and
            calculated results.
        cumulative_damage: Dimensionless cumulative model damage; task calculators
            retain their documented intrinsic rounding.
    """

    task_id: str
    cumulative_damage: float


def validate_duet_scale(scale: int | None, task_id: str) -> int:
    """Validate a complete integer selector index with task-specific issue context.

    Args:
        scale: OMNI-Res selector index from zero through ten; None denotes unfinished
            input.
        task_id: Stable task identity used for lookup or field-specific validation
            diagnostics.

    Returns:
        The original valid integer selector index, without coercion or clamping.

    Raises:
        DraftError: Source structure, completeness, numeric validity or task identity
            violates the constraints described above; issue retains field/task context.
    """
    if scale is None:
        raise DraftError(InputIssue("validation.required", "omni_res_scale", task_id))
    if isinstance(scale, bool) or not isinstance(scale, int) or not 0 <= scale <= 10:
        raise DraftError(InputIssue("validation.omni_scale", "omni_res_scale", task_id))
    return scale


def calculate_duet_task(task: DuetTask) -> DuetTaskResult:
    """Calculate table[index] * repetitions, rounded to five places, without I/O.

    Preserve every valid selector index (0-10), lookup value and arithmetic order.
    Unlike the reference's int coercion/negative indexing, fractional, boolean and out-
    of-range indices raise DraftError with validation.omni_scale. Missing
    scale/repetitions and invalid repetition numbers produce field-specific issues.

    Args:
        task: Immutable source row; absent fields remain None until completeness
            validation.

    Returns:
        Stable task identity and cumulative damage rounded to five decimal places by the
        model.

    Raises:
        DraftError: OMNI index or repetitions are missing, boolean, malformed, negative
            or nonfinite; the issue identifies the source field/task.
    """
    scale = validate_duet_scale(task.omni_res_scale, task.task_id)
    repetitions = validate_nonnegative_input(
        task.repetitions, "repetitions", task.task_id
    )
    return DuetTaskResult(task.task_id, round(DAMAGE_PER_CYCLE[scale] * repetitions, 5))


def probability_from_damage(damage: float) -> float:
    """Return reference DUET probability on the 0-1 scale for positive finite damage.

    Preserve math.log(damage, 10), coefficients and evaluation order. Zero is outside
    this expression's domain; assessment placeholders need separate policy. Raises
    ValueError for zero, negative or nonfinite damage.

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
    predictor = 0.573 + 0.747 * math.log(damage, 10)
    return math.exp(predictor) / (1 + math.exp(predictor))

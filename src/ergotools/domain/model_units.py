"""Explicit LiFFT/Shoulder conversion policy characterized from working models.

These constants preserve model compatibility; this is not a general SI converter. In
particular the reference metric moment expression awaits scientific review.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

import math
from dataclasses import dataclass
from enum import StrEnum

from ergotools.domain.assessments.validation import DraftError, InputIssue

# Exact international-inch length factor; source cm are divided by 2.54 for model
# inches.
_CENTIMETERS_PER_INCH = 2.54
# Reference model force factor, 4.45 N/lbf; deliberately retain it rather than
# substituting a physical converter.
_MODEL_NEWTONS_PER_POUND_FORCE = 4.45
# Original metric moment display divisor, retained for numerical compatibility; not
# validated SI conversion.
_MODEL_MOMENT_DIVISOR = 0.73756
# Original metric moment display multiplier, retained with the divisor; see model_units
# module caveat.
_MODEL_MOMENT_MULTIPLIER = 9.81


class MeasurementSystem(StrEnum):
    """Stable measurement identifiers independent of translated UI labels."""

    # Source arm inches and force lbf; body mass has a separate lb conversion.
    IMPERIAL = "imperial"
    # Source arm centimeters and force newtons; canonical body values use cm/kg.
    METRIC = "metric"


@dataclass(frozen=True, slots=True)
class ModelLoad:
    """Normalized model inputs; load is force, never body mass in pounds.

    Attributes:
        lever_arm_in: Finite normalized arm length in inches; signed inputs remain for
            model-specific validation.
        load_lbf: Finite normalized force in model-compatible pounds-force, distinct
            from body mass.
    """

    lever_arm_in: float
    load_lbf: float

    def __post_init__(self) -> None:
        """Reject nonfinite values at the model boundary.

        Args:
            None. Dataclass construction supplies the fields documented on ModelLoad.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: The typed record or one of its referenced identities violates
                the invariants described above.
        """
        _require_finite(self.lever_arm_in, self.load_lbf)


def _require_finite(*values: float) -> None:
    """Reject nonfinite model quantities before conversion or evaluation.

    Args:
        values: Model quantities in their existing units; signs are not checked here.

    Returns:
        None. Return normally only when the stated validation succeeds; invalid data
        raises instead.

    Raises:
        ValueError: Model quantities must be finite.
    """
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Model quantities must be finite.")


def normalize_model_load(
    lever_arm: float, load: float, system: MeasurementSystem
) -> ModelLoad:
    """Convert an input snapshot to the original models' inch/lbf convention.

    Args:
        lever_arm: Centimeters for metric, inches for imperial.
        load: Newtons for metric, pounds-force for imperial; never kilograms.
        system: Explicit input system, unrelated to interface language.

    Returns:
        Immutable inputs with no rounding or mutation of the original values.

    Raises:
        ValueError: A quantity is nonfinite or the system is unsupported.

    Signed finite inputs are preserved; model-specific physical validity belongs to the
    assessment validator. This does not implement live unit switching.
    """
    _require_finite(lever_arm, load)
    match system:
        case MeasurementSystem.METRIC:
            return ModelLoad(
                lever_arm / _CENTIMETERS_PER_INCH,
                load / _MODEL_NEWTONS_PER_POUND_FORCE,
            )
        case MeasurementSystem.IMPERIAL:
            return ModelLoad(lever_arm, load)
        case _:
            raise ValueError(f"Unsupported measurement system: {system}")


def model_moment_for_display(moment_ft_lbf: float, system: MeasurementSystem) -> float:
    """Preserve the reference moment display conversion and one-decimal rounding.

    The metric result carries the old UI's N.m label, but the expression is a
    compatibility rule, not a validated physical conversion. LiFFT rounds its model
    moment before damage evaluation; Shoulder does not. Callers must pass each model's
    value at that stage, not move rounding into the calculation.

    Raises:
        ValueError: Input/result is nonfinite or the system is unsupported.

    Args:
        moment_ft_lbf: Model moment in ft.lbf at the model-specific rounding stage
            described above.
        system: Explicit source measurement system: arm in cm and force in N, or arm in
            inches and force in lbf.

    Returns:
        One-decimal compatible display value: ft.lbf for imperial, the original
        N.m-labelled expression for metric.
    """
    _require_finite(moment_ft_lbf)
    match system:
        case MeasurementSystem.METRIC:
            result = (moment_ft_lbf / _MODEL_MOMENT_DIVISOR) * _MODEL_MOMENT_MULTIPLIER
        case MeasurementSystem.IMPERIAL:
            result = moment_ft_lbf
        case _:
            raise ValueError(f"Unsupported measurement system: {system}")
    _require_finite(result)
    return round(result, 1)


def project_model_input(
    value: float | None,
    field: str,
    task_id: str,
    source: MeasurementSystem,
    target: MeasurementSystem,
) -> float | None:
    """Project original arm/force inputs into display units without rounding.

    Only lever_arm (cm/in) and load (N/model lbf) are supported. The 4.45 force factor
    preserves model compatibility; this is not a mass or SI converter. Missing/signed
    source values survive. Same-unit values retain exact numeric identity, including
    integers. Always project from source to avoid toggle drift.

    Raises:
        DraftError: Input is nonfinite or conversion overflows/underflows to zero.
        ValueError: Units or quantity field are unsupported.

    Args:
        value: Source quantity to validate; None denotes absence rather than numeric
            zero.
        field: Stable quantity-field identifier for structured validation issues, never
            a translated caption.
        task_id: Stable task identity used for lookup or field-specific validation
            diagnostics.
        source: Measurement system of the preserved source quantity; always project from
            this original system.
        target: Requested display measurement system; this projection does not rewrite
            saved inputs.

    Returns:
        Unrounded display quantity or None; equal systems retain the original number
        exactly.
    """
    if not isinstance(source, MeasurementSystem) or not isinstance(
        target, MeasurementSystem
    ):
        raise ValueError("Unsupported measurement system.")
    if field == "lever_arm":
        factor = _CENTIMETERS_PER_INCH
    elif field == "load":
        factor = _MODEL_NEWTONS_PER_POUND_FORCE
    else:
        raise ValueError("Unsupported model input quantity.")
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DraftError(InputIssue("validation.number", field, task_id))
    try:
        finite = math.isfinite(value)
    except OverflowError as error:
        raise DraftError(InputIssue("validation.overflow", field, task_id)) from error
    if not finite:
        raise DraftError(InputIssue("validation.nonfinite", field, task_id))
    if source is target:
        return value
    converted = value * factor if target is MeasurementSystem.METRIC else value / factor
    if not math.isfinite(converted) or (converted == 0 and value != 0):
        raise DraftError(InputIssue("validation.overflow", field, task_id))
    return converted

"""Optional worker metadata with unambiguous body length and mass units.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

import math
from dataclasses import dataclass
from datetime import date

from ergotools.domain.model_units import MeasurementSystem


@dataclass(frozen=True, slots=True)
class WorkerDetails:
    """Demographics and employment data; body values are centimeters/kilograms.

    ISO dates and absent values remain independent of interface language. Hidden legacy
    anthropometry is outside this visible-form migration checkpoint.

    Attributes:
        birth_date: Optional canonical ISO calendar date (YYYY-MM-DD), independent of
            language.
        sex: Optional original Male/Female category; None imposes no sex constraint.
        height_cm: Optional canonical body length in centimeters.
        weight_kg: Optional canonical body mass in kilograms, distinct from model force.
        hiring_date: Optional canonical ISO hiring date (YYYY-MM-DD); no
            employment-duration inference.
        address: Optional saved street/address text.
        city: Optional saved city text.
        region: Optional saved region text.
        country: Optional saved country text.
        postal_code: Optional postal code text; numeric-looking codes retain leading
            zeros.
        email: Optional saved email text; this boundary checks type rather than mail
            deliverability.
    """

    birth_date: str | None = None
    sex: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    hiring_date: str | None = None
    address: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    postal_code: str | None = None
    email: str | None = None

    def __post_init__(self) -> None:
        """Reject malformed dates, nonfinite quantities and untyped metadata.

        Args:
            None. Dataclass construction supplies the fields documented on
            WorkerDetails.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: Unsupported worker sex. Worker dates require ISO calendar dates.
                Worker metadata must be text or absent. Body measurements must be finite
                and nonnegative.
        """
        for value in (self.birth_date, self.hiring_date):
            if value is not None and (
                not isinstance(value, str)
                or date.fromisoformat(value).isoformat() != value
            ):
                raise ValueError("Worker dates require ISO calendar dates.")
        if self.sex not in (None, "Female", "Male"):
            raise ValueError("Unsupported worker sex.")
        for value in (
            self.address,
            self.city,
            self.region,
            self.country,
            self.postal_code,
            self.email,
        ):
            if value is not None and not isinstance(value, str):
                raise ValueError("Worker metadata must be text or absent.")
        for quantity in (self.height_cm, self.weight_kg):
            if quantity is not None and (
                isinstance(quantity, bool)
                or not isinstance(quantity, (int, float))
                or not math.isfinite(quantity)
                or quantity < 0
            ):
                raise ValueError("Body measurements must be finite and nonnegative.")


def display_body_measurement(
    value: float | None, system: MeasurementSystem, *, mass: bool = False
) -> float | None:
    """Project cm/kg into cm/kg or in/lb without rounding saved values.

    Args:
        value: Canonical body length in cm or mass in kg, or None.
        system: Display measurement system: cm/kg for metric, inches/pounds mass for
            imperial.
        mass: True selects body mass (kg/lb); False selects body length (cm/in). Force
            conversion is separate.

    Returns:
        Unrounded body length in cm/in or mass in kg/lb for the display system; None
        remains absent.

    Raises:
        ValueError: Unsupported body measurement system.
    """
    if not isinstance(system, MeasurementSystem):
        raise ValueError("Unsupported body measurement system.")
    if value is None or system is MeasurementSystem.METRIC:
        return value
    return value / (0.45359237 if mass else 2.54)


def store_body_measurement(
    value: float | None, system: MeasurementSystem, *, mass: bool = False
) -> float | None:
    """Convert displayed cm/kg or in/lb into canonical body units once.

    Args:
        value: Displayed body length in cm/in or mass in kg/lb, or None.
        system: Display measurement system: cm/kg for metric, inches/pounds mass for
            imperial.
        mass: True selects body mass (kg/lb); False selects body length (cm/in). Force
            conversion is separate.

    Returns:
        Canonical unrounded body length in cm or mass in kg; None remains absent.

    Raises:
        ValueError: Unsupported body measurement system.
    """
    if not isinstance(system, MeasurementSystem):
        raise ValueError("Unsupported body measurement system.")
    if value is None or system is MeasurementSystem.METRIC:
        return value
    return value * (0.45359237 if mass else 2.54)

"""Project-owned decimal presentation policy, independent of calculation and units.

Domain layer: validate display precision only. No values are rounded here; scientific
sources and saved results remain exact. Defaults apply to projects without preferences.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DisplayPrecision:
    """Decimal counts for numeric display; never calculator precision.

    Attributes:
        inputs: Continuous editable values; repetitions remain whole-number displays.
        moment: Calculated moments in their recorded units.
        probability: Outcome percentages and assessment gauge text.
        damage: Per-task and cumulative damage, including very small values.
        contribution: Each task's percentage share of total damage.
    """

    inputs: int = 1
    moment: int = 1
    probability: int = 1
    damage: int = 4
    contribution: int = 1

    def __post_init__(self) -> None:
        """Reject unsupported precision before storage or UI construction.

        Args:
            None.

        Returns:
            None; validate all counts as integers between zero and eight.

        Raises:
            ValueError: A count is boolean, noninteger or outside zero through eight.
        """
        for value in (
            self.inputs,
            self.moment,
            self.probability,
            self.damage,
            self.contribution,
        ):
            if type(value) is not int or not 0 <= value <= 8:
                raise ValueError("Display decimals must be integers from 0 to 8.")

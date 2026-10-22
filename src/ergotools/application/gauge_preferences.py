"""Personal risk-gauge appearance, independent of Qt and project data.

Application layer. These immutable options describe presentation preferences only;
they never classify risk, change calculator precision or alter assessment storage.
The interval is measured in probability percentage points on the existing 0-100
display scale. Desktop widgets and the user-settings adapter consume this contract.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GaugeMarkerSettings:
    """Control risk-gauge annotations independently of the displayed value.

    Attributes:
        show_ticks: Draw both range-boundary ticks and evenly spaced unlabeled ticks.
        show_labels: Label existing risk-range boundaries, including scale endpoints.
        interval: Integer percentage-point spacing between unlabeled ticks, 1-100.
            Defaults to ten points. Boundary ticks remain exact off that grid.
    """

    show_ticks: bool = True
    show_labels: bool = True
    interval: int = 10

    def __post_init__(self) -> None:
        """Reject ambiguous flags and invalid interval values before use or storage.

        Args:
            None.

        Returns:
            None; retain the validated immutable options.

        Raises:
            ValueError: Flags are not booleans or interval is not an integer in 1-100.
        """
        if (
            type(self.show_ticks) is not bool
            or type(self.show_labels) is not bool
            or type(self.interval) is not int
            or not 1 <= self.interval <= 100
        ):
            raise ValueError("Invalid gauge marker settings.")

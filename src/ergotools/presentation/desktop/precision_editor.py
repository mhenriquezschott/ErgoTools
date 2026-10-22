"""Rounded numeric editors that preserve exact unchanged inputs.

Presentation layer: visible text uses project decimals, but grid commits receive the
original round-trip text until the user actually edits that field. No source mutation,
unit conversion or calculation occurs here. Qt ownership stays with the containing form.
"""

from PyQt5.QtWidgets import QLineEdit

from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.presentation.numeric_input import format_input_number


class PrecisionLineEdit(QLineEdit):
    """Keep exact initial text separate from the compact visible number."""

    def __init__(
        self, value: float | None, convention: DecimalConvention, decimals: int
    ) -> None:
        """Initialize compact text before connecting user-edit tracking.

        Args:
            value: Exact converted display quantity, or None for a blank source field.
            convention: Explicit decimal mark used for both visible and committed text.
            decimals: Validated project count; zero for repetition displays.

        Returns:
            None; the containing grid adopts Qt ownership.

        Raises:
            ValueError: Initial value, decimal convention or display format is invalid.
        """
        super().__init__()
        self._exact_text = format_input_number(value, convention)
        self._visible_text = (
            f"{value:.{decimals}f}".replace(".", convention.value)
            if value is not None
            else ""
        )
        self._edited = False
        self.setText(self._visible_text)
        self.textEdited.connect(self._mark_edited)

    def _mark_edited(self) -> None:
        """Remember intentional edits, including retyping the same rounded text.

        Args:
            None.

        Returns:
            None; the next commit uses the user's literal text.
        """
        self._edited = True

    def source_text(self) -> str:
        """Return exact unchanged input or the user's replacement token.

        Args:
            None.

        Returns:
            Initial full-precision token until an edit or programmatic text change;
            undoing all native typing restores that exact initial token;
            otherwise the current visible text for ordinary parser validation.
        """
        return (
            self._exact_text
            if self.text() == self._visible_text
            and (not self._edited or not self.isUndoAvailable())
            else self.text()
        )

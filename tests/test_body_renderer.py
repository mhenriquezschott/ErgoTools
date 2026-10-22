"""Verify renderer requests do not require VTK, Qt or project data.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import math
import unittest
from dataclasses import FrozenInstanceError

from ergotools.application.contracts.body_renderer import (
    BodyRegion,
    BodyViewState,
    RgbColor,
)


class BodyViewContractTests(unittest.TestCase):
    """Test backend-independent values and unavailable-overlay semantics."""

    def test_missing_overlay_is_explicit(self) -> None:
        """A missing result must not be represented as green or zero risk.

        Args:
            None.

        Returns:
            None.
        """
        state = BodyViewState(BodyRegion.LOW_BACK)
        self.assertIsNone(state.overlay_color)

    def test_state_is_immutable(self) -> None:
        """A renderer must not mutate a shared request while work is pending.

        Args:
            None.

        Returns:
            None.
        """
        state = BodyViewState(BodyRegion.SHOULDERS, RgbColor(0.0, 0.5, 1.0))
        with self.assertRaises(FrozenInstanceError):
            state.region = BodyRegion.FULL_BODY

    def test_color_channels_are_validated(self) -> None:
        """Invalid display channels must not reach a rendering backend.

        Args:
            None.

        Returns:
            None.
        """
        for value in (-0.01, 1.01, math.inf, math.nan):
            with self.subTest(value=value), self.assertRaises(ValueError):
                RgbColor(value, 0.5, 0.5)

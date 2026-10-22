"""Compatibility name for the shared risk gauge's compact PLOT profile.

Presentation layer. Main and PLOT gauges now use RiskGauge for rendering, marker
preferences, menus and input prompts. This adapter preserves existing PLOT imports,
constructor defaults and the set_probability API without duplicating drawing code.
"""

from collections.abc import Callable, Mapping

from PyQt5.QtGui import QIcon

from ergotools.application.gauge_preferences import GaugeMarkerSettings
from ergotools.presentation.desktop.result_scales import RiskGauge


class PlotRiskGauge(RiskGauge):
    """Select the shared compact profile; own no separate drawing or preferences."""

    def __init__(
        self,
        marker_settings: GaugeMarkerSettings | None = None,
        change_markers: Callable[[GaugeMarkerSettings], None] | None = None,
        *,
        dialog_icons: Mapping[str, QIcon] | None = None,
    ) -> None:
        """Retain PLOT timing/absence policy with shared marker controls.

        Args:
            marker_settings: Shared personal options, or None for defaults.
            change_markers: Injected host save/apply callback; None previews locally.
            dialog_icons: Optional packaged icons for the shared interval prompt.

        Returns:
            None; construct the same gauge control in its compact layout.
        """
        super().__init__(
            marker_settings, change_markers, compact=True, dialog_icons=dialog_icons
        )

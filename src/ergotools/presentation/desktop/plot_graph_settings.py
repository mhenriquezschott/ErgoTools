"""Owned PLOT graph presentation settings and original figure styling.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from matplotlib.container import BarContainer
from matplotlib.figure import Figure
from matplotlib.text import Text


class PlotAxisMode(StrEnum):
    """Original default, standard risk or explicit maximum choices."""

    # Use the original automatically determined chart value-axis limits.
    DEFAULT = "default"
    # Use the standard probability-percent risk axis range.
    RISK = "risk"
    # Use the explicit validated graph maximum selected by the user.
    CUSTOM = "custom"


@dataclass(frozen=True, slots=True)
class PlotGraphSettings:
    """Presentation-only source defaults; no assessment/project data is altered.

    Attributes:
        show_title: Whether to display the chart title.
        show_legend: Whether to display the source series legend.
        show_grid: Whether to draw the source value-axis grid.
        show_bar_values: Whether to annotate observed bars with their formatted values.
        axis_mode: Default, standard risk or custom value-axis scaling.
        axis_maximum: Finite positive custom value-axis maximum.
        text_scale: Text-size percentage applied once when generating a fresh figure.
    """

    show_title: bool = True
    show_legend: bool = True
    show_grid: bool = False
    show_bar_values: bool = False
    axis_mode: PlotAxisMode = PlotAxisMode.DEFAULT
    axis_maximum: float = 100
    text_scale: int = 100

    def __post_init__(self) -> None:
        """Reject values outside the original controls' supported ranges.

        Args:
            None.

        Returns:
            None.

        Raises:
            ValueError: Unsupported PLOT graph settings.
        """
        if (
            any(
                type(flag) is not bool
                for flag in (
                    self.show_title,
                    self.show_legend,
                    self.show_grid,
                    self.show_bar_values,
                )
            )
            or not isinstance(self.axis_mode, PlotAxisMode)
            or type(self.axis_maximum) not in (float, int)
            or not isfinite(self.axis_maximum)
            or not 1 <= self.axis_maximum <= 1000000
            or type(self.text_scale) is not int
            or not 80 <= self.text_scale <= 140
        ):
            raise ValueError("Unsupported PLOT graph settings.")


def style_summary_figure(
    figure: Figure, settings: PlotGraphSettings, *, horizontal: bool = False
) -> None:
    """Apply source preferences once to a newly created, owned figure.

    Horizontal job charts use the value axis X; worker charts use Y. Scaling never
    touches risk values, source units or saved assessments. Regenerate a figure when
    settings change to avoid repeated font multiplication and annotations.

    Args:
        figure: Owned Matplotlib figure; no pyplot global state or scientific values are
            modified.
        settings: Immutable graph presentation preferences; project and assessment
            values are unchanged.
        horizontal: True styles the value X axis; False styles the worker-chart Y axis.

    Returns:
        None.
    """
    if not figure.axes:
        return
    axis = figure.axes[0]
    axis.title.set_visible(settings.show_title)
    axis.title.set_wrap(True)
    legend = axis.get_legend()
    if legend is not None:
        legend.set_visible(settings.show_legend)
    if settings.show_grid:
        axis.grid(
            True,
            axis="x" if horizontal else "y",
            color="#C7D2DA",
            linestyle="--",
            linewidth=0.7,
            alpha=0.7,
        )
    else:
        axis.grid(False)
    if settings.axis_mode is not PlotAxisMode.DEFAULT:
        maximum = (
            100 if settings.axis_mode is PlotAxisMode.RISK else settings.axis_maximum
        )
        if horizontal:
            axis.set_xlim(0, maximum)
        else:
            axis.set_ylim(0, maximum)
    if settings.show_bar_values:
        for container in axis.containers:
            if isinstance(container, BarContainer):
                axis.bar_label(container, fmt="%.1f", padding=2, fontsize=6)
    for target in figure.axes:
        for item in target.findobj(match=Text):
            size = item.get_fontsize()
            if isinstance(size, (int, float)):
                item.set_fontsize(max(5.0, size * settings.text_scale / 100))
    figure.tight_layout(pad=0.6)

"""Narrow typed boundary for the approved Matplotlib Qt canvas and toolbar.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Callable
from typing import cast

from matplotlib.backends.backend_qt import NavigationToolbar2QT
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import QWidget


class PlotChartCanvas(FigureCanvasQTAgg):
    """Expose typed initialization/draw over Matplotlib's unannotated Qt methods."""

    def __init__(self, figure: Figure) -> None:
        """Initialize the approved backend with one explicitly owned figure.

        Args:
            figure: Owned Matplotlib figure; no pyplot global state or scientific values
                are modified.

        Returns:
            None.
        """
        cast(Callable[[Figure], None], super().__init__)(figure)

    def draw(self) -> None:
        """Delegate synchronously to the existing backend without type suppression.

        Args:
            None.

        Returns:
            None.
        """
        cast(Callable[[], None], super().draw)()

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        """Fit labels to the actual Qt canvas size without scaling fonts twice.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        cast(Callable[[QResizeEvent], None], super().resizeEvent)(event)
        if self.figure.axes and self.width() >= 100 and self.height() >= 100:
            self.figure.tight_layout(pad=0.6)


class PlotNavigationToolbar(NavigationToolbar2QT):
    """Retain Matplotlib navigation behavior behind a typed composition boundary."""

    def __init__(self, canvas: PlotChartCanvas, parent: QWidget) -> None:
        """Bind the existing toolbar to this viewer's canvas and Qt owner.

        Args:
            canvas: Owned Qt canvas whose figure or scene is composed here; this adapter
                does not acquire repository ownership.
            parent: Required Qt owner of the new control; ownership follows the parent
                widget lifetime.

        Returns:
            None.
        """
        cast(Callable[[PlotChartCanvas, QWidget], None], super().__init__)(
            canvas, parent
        )

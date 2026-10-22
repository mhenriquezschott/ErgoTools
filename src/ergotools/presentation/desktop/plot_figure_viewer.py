"""Original expanded PLOT viewer with a separately owned figure and toolbar.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Mapping

from matplotlib.figure import Figure
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QCloseEvent, QIcon
from PyQt5.QtWidgets import QDialog, QPushButton, QVBoxLayout, QWidget

from ergotools.domain.language import Language
from ergotools.presentation.desktop.plot_chart_canvas import (
    PlotChartCanvas,
    PlotNavigationToolbar,
)
from ergotools.presentation.desktop.plot_figure_export import export_plot
from ergotools.presentation.desktop.theme.plot import PLOT_STYLE


class PlotFigureViewer(QDialog):
    """Own an expanded figure; closing never steals or resizes the summary canvas."""

    def __init__(
        self,
        figure: Figure,
        icons: Mapping[str, QIcon],
        *,
        language: Language = Language.ENGLISH,
        parent: QWidget | None = None,
    ) -> None:
        """Retain original 900 x 650 viewer and navigation/save interactions.

        Args:
            figure: Owned Matplotlib figure; no pyplot global state or scientific values
                are modified.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        self.figure = figure
        self.language = language
        self.setWindowTitle(
            "Vista ampliada del gráfico"
            if language is Language.SPANISH
            else "Expanded Plot View"
        )
        self.setFixedSize(900, 650)
        self.setStyleSheet(PLOT_STYLE)
        layout = QVBoxLayout(self)
        self.canvas = PlotChartCanvas(figure)
        self.toolbar = PlotNavigationToolbar(self.canvas, self)
        # Keep original Matplotlib controls; use processed equivalents where present.
        captions = {
            "Home": ("Inicio", "actual_size"),
            "Back": ("Anterior", "previous"),
            "Forward": ("Siguiente", "next"),
            "Pan": ("Desplazar", None),
            "Zoom": ("Ampliar", "zoom_in"),
            "Subplots": ("Subgráficos", None),
            "Customize": ("Personalizar", None),
            "Save": ("Guardar", "save"),
        }
        for action in self.toolbar.actions():
            entry = captions.get(action.text())
            if entry is not None:
                spanish, asset = entry
                if asset is not None:
                    action.setIcon(icons[asset])
                if language is Language.SPANISH:
                    action.setText(spanish)
                    action.setToolTip(spanish)
        self.toolbar.setIconSize(QSize(24, 24))
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.save_button = QPushButton(
            "Guardar gráfico" if language is Language.SPANISH else "Save Plot"
        )
        self.save_button.clicked.connect(self.save_plot)
        layout.addWidget(self.save_button)

    def save_plot(self) -> None:
        """Use the original viewer chooser; failed export keeps this window open.

        Args:
            None.

        Returns:
            None.
        """
        export_plot(self.figure, self, self.language, "plot-summary", expanded=True)

    def closeEvent(self, event: QCloseEvent | None) -> None:  # noqa: N802
        """Release this viewer's figure only; the parent's canvas remains attached.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        self.figure.clear()
        super().closeEvent(event)

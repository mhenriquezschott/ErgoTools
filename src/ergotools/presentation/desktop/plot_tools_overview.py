"""Original PLOT Tools Overview panel composed with saved summaries and charts.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Mapping

from matplotlib.figure import Figure
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QIcon, QResizeEvent
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QGroupBox,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.plot_results import PlotResults
from ergotools.application.plot_summaries import PlotSummary, summarize_plot
from ergotools.domain.language import Language
from ergotools.domain.plot_filters import PlotRiskView
from ergotools.presentation.desktop.plot_chart_canvas import PlotChartCanvas
from ergotools.presentation.desktop.plot_figure_export import export_plot
from ergotools.presentation.desktop.plot_figure_viewer import PlotFigureViewer
from ergotools.presentation.desktop.plot_graph_dialog import PlotGraphDialog
from ergotools.presentation.desktop.plot_graph_settings import (
    PlotGraphSettings,
    style_summary_figure,
)
from ergotools.presentation.desktop.plot_marker_layer import PlotMarkerLayer
from ergotools.presentation.desktop.plot_summary_figure import PlotChart, summary_figure
from ergotools.presentation.desktop.plot_symbol_legend import PlotSymbolLegend
from ergotools.presentation.desktop.theme.plot import PLOT_STYLE


class PlotToolsOverview(QGroupBox):
    """Own source chart selection/settings/viewer; no project/editor writes occur.

    A 250-pixel canvas floor and normal vertical size hints reserve chart and text
    space when demographics opens or the current risk-mode explanation changes.
    """

    def __init__(
        self,
        layer: PlotMarkerLayer,
        icons: Mapping[str, QIcon],
        *,
        language: Language = Language.ENGLISH,
        parent: QWidget | None = None,
    ) -> None:
        """Compose the original panel; saved results alone trigger summary refresh.

        Args:
            layer: Existing PLOT marker/history owner; this view borrows its selection
                and save operations.
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
        self.layer = layer
        self.icons = icons
        self.language = language
        self.settings = PlotGraphSettings()
        self._results: PlotResults | None = None
        self.summary: PlotSummary | None = None
        self.setStyleSheet(PLOT_STYLE)
        self.setMinimumWidth(330)
        self.setMaximumWidth(420)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setSpacing(8)
        self.canvas = PlotChartCanvas(Figure(figsize=(3.1, 2.3)))
        self.canvas.setMinimumHeight(250)
        self.canvas.setObjectName("plotSummaryCanvas")
        self.canvas.setStyleSheet(
            "QWidget#plotSummaryCanvas "
            "{background:#FFFFFF;color:#1B2933;} QToolTip "
            "{background:#1B2933;color:#FFFFFF;border:1px solid "
            "#0B326C;padding:6px;}"
        )
        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.canvas.setToolTip(
            self.text(
                "Click the chart to open a larger interactive view.",
                "Pulse el gráfico para abrir una vista interactiva ampliada.",
            )
        )
        self.canvas.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.canvas.setAutoFillBackground(True)
        palette = self.canvas.palette()
        palette.setColor(self.canvas.backgroundRole(), QColor("#FFFFFF"))
        self.canvas.setPalette(palette)
        layout.addWidget(self.canvas, 2)
        layout.addSpacing(4)
        self.chart_combo = QComboBox()
        for en, es, chart in (
            (
                "Total Worker Distribution by Tool",
                "Distribución de trabajadores por herramienta",
                PlotChart.TOOL,
            ),
            (
                "Worker Risk Distribution by Gender & Tool",
                "Riesgo de trabajadores por sexo y herramienta",
                PlotChart.SEX,
            ),
            (
                "Worker Risk Distribution by Age & Tool",
                "Riesgo de trabajadores por edad y herramienta",
                PlotChart.AGE,
            ),
        ):
            self.chart_combo.addItem(self.text(en, es), chart)
        self.chart_combo.setToolTip(
            self.text(
                "Choose the summary visualization shown above.",
                "Elija la visualización de resumen.",
            )
        )
        layout.addWidget(self.chart_combo)
        description_panel = QWidget(self)
        description_layout = QVBoxLayout(description_panel)
        description_layout.setContentsMargins(0, 2, 0, 2)
        description_layout.setSpacing(8)
        self.description = QLabel(description_panel)
        self.compare = QLabel(description_panel)
        for label in (self.description, self.compare):
            label.setObjectName("plotDescription")
            label.setWordWrap(True)
            label.setAlignment(
                Qt.Alignment(Qt.AlignmentFlag.AlignLeft) | Qt.AlignmentFlag.AlignTop
            )
        description_layout.addWidget(self.description)
        description_layout.addStretch(2)
        description_layout.addWidget(self.compare)
        description_layout.addStretch(1)
        self.legend = PlotSymbolLegend(language=language, parent=description_panel)
        description_layout.addWidget(self.legend)
        layout.addWidget(description_panel, 1)
        self.settings_button = QPushButton(
            self.text("Graph Settings", "Configuración del gráfico")
        )
        self.settings_button.setObjectName("summarysettings_button")
        self.settings_button.setIcon(icons["settings"])
        self.settings_button.setIconSize(QSize(22, 22))
        self.settings_button.setToolTip(
            self.text(
                "Adjust graph labels, guides, text size, and vertical scale.",
                "Ajuste etiquetas, líneas guía, tamaño del texto y escala del gráfico.",
            )
        )
        self.settings_button.clicked.connect(self.open_settings)
        layout.addWidget(self.settings_button)
        self.chart_combo.currentIndexChanged.connect(self.draw_current)
        layer.changed.connect(self.refresh)
        self.draw_current()
        self.refresh()

    def text(self, english: str, spanish: str) -> str:
        """Translate source controls independently of saved identity and numbers.

        Args:
            english: English UI text; saved user values are never translated by this
                helper.
            spanish: Spanish UI text corresponding to the English caption.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return spanish if self.language is Language.SPANISH else english

    def chart(self) -> PlotChart:
        """Retain the selected worker chart while the separate job view is shown.

        Args:
            None.

        Returns:
            Current typed chart identity; job view temporarily overrides but preserves
            the worker-chart selection.
        """
        if self._results and self._results.selection.risk_view is PlotRiskView.JOB:
            return PlotChart.JOB
        return PlotChart(self.chart_combo.currentData())

    def refresh(self) -> None:
        """Rebuild on saved dataset publication; marker previews do not redraw.

        Args:
            None.

        Returns:
            None.
        """
        results = self.layer.results
        available = results is not None
        self.settings_button.setEnabled(available)
        self.chart_combo.setEnabled(available)
        if results is self._results:
            return
        self._results = results
        self.summary = (
            summarize_plot(results, current_year=self.layer.current_year)
            if results
            else None
        )
        self.draw_current()

    def make_figure(self) -> Figure:
        """Create a fresh owned figure, applying presentation preferences once.

        Args:
            None.

        Returns:
            Fresh owned figure with graph presentation preferences applied exactly once.
        """
        if self.summary is None:
            figure = Figure(figsize=(3.1, 2.3), facecolor="white")
            axis = figure.add_subplot()
            axis.text(
                0.5,
                0.5,
                self.text(
                    "No workers results match\nthe current filters.",
                    "Ningún trabajador coincide\ncon los filtros actuales.",
                ),
                ha="center",
                va="center",
                color="#526777",
                fontsize=9,
            )
            axis.set_axis_off()
            return figure
        assert self._results is not None
        figure = summary_figure(
            self.summary,
            self.chart(),
            language=self.language,
            tool=self._results.selection.tool,
        )
        style_summary_figure(
            figure, self.settings, horizontal=self.chart() is PlotChart.JOB
        )
        return figure

    def draw_current(self) -> None:
        """Replace the source canvas figure and mode description together.

        Args:
            None.

        Returns:
            None.
        """
        mode = (
            self._results.selection.risk_view
            if self._results
            else PlotRiskView.INDIVIDUAL
        )
        job = mode is PlotRiskView.JOB
        self.chart_combo.setVisible(not job)
        self.legend.set_mode(mode)
        if job:
            self.description.setText(
                self.text(
                    "<b>What this shows:</b> Current risk by Job in "
                    "the selected scope. Each bar is one Job, regardless of how "
                    "many squares represent it on the map.",
                    "<b>Qué muestra:</b> Riesgo actual por trabajo. "
                    "Cada barra representa "
                    "un trabajo, sin contar sus cuadrados repetidos en el mapa.",
                )
            )
            self.compare.setText(
                self.text(
                    "<b>Map:</b> Job-only squares use the same assignment positions as "
                    "Comparison. Labels identify Jobs; gray dashed squares have no "
                    "applicable Job risk. The chart covers Jobs in the "
                    "workplace scope.",
                    "<b>Mapa:</b> Los cuadrados usan las posiciones de Comparación. "
                    "La etiqueta identifica el trabajo; gris discontinuo indica riesgo "
                    "no disponible. El gráfico incluye los trabajos del ámbito.",
                )
            )
        else:
            descriptions = {
                PlotChart.TOOL: (
                    "Average outcome probability for each ergonomic tool.",
                    "Probabilidad media por herramienta.",
                    "<b>Scale:</b> 0\u2013100%; higher values indicate greater risk.",
                    "<b>Escala:</b> 0\u2013100%; valores mayores indican mayor riesgo.",
                ),
                PlotChart.SEX: (
                    "Average outcome probability by sex for each ergonomic tool.",
                    "Probabilidad media por sexo y herramienta.",
                    "<b>Compare:</b> Differences within and across tools.",
                    "<b>Compare:</b> Diferencias dentro y entre herramientas.",
                ),
                PlotChart.AGE: (
                    "Average outcome probability by worker age range and "
                    "ergonomic tool.",
                    "Probabilidad media por edad y herramienta.",
                    "<b>Compare:</b> Risk patterns between age groups.",
                    "<b>Compare:</b> Patrones de riesgo por edad.",
                ),
            }
            en, es, compare, compare_es = descriptions[self.chart()]
            self.description.setText(
                self.text(
                    "<b>What this shows:</b> "
                    + en
                    + " Error bars show one standard deviation.",
                    "<b>Qué muestra:</b> "
                    + es
                    + " Las barras de error muestran una desviación estándar.",
                )
            )
            comparison = self.text(compare, compare_es)
            if mode is PlotRiskView.COMPARISON:
                comparison += self.text(
                    " The inner worker symbol is individual risk; the filled "
                    "square is applicable Job risk.",
                    " El símbolo interior es el riesgo individual; el cuadrado "
                    "exterior es el riesgo del trabajo.",
                )
            self.compare.setText(comparison)
        figure = self.make_figure()
        old = self.canvas.figure
        figure.set_canvas(self.canvas)
        figure.set_size_inches(
            max(1, self.canvas.width()) / figure.dpi,
            max(1, self.canvas.height()) / figure.dpi,
            forward=False,
        )
        figure.tight_layout(pad=0.6)
        self.canvas.figure = figure
        # Matplotlib's callback registry belongs to the figure, not the Qt widget.
        # Bind each replacement exactly once so chart changes retain click-to-expand.
        self.canvas.mpl_connect("button_press_event", lambda _event: self.open_viewer())
        if old is not figure:
            old.clear()
        self.canvas.draw()
        self.canvas.updateGeometry()
        self.fit_content()

    def fit_content(self) -> None:
        """Publish the live wrapped-text/chart minimum to the containing splitter.

        Args:
            None.

        Returns:
            None. Reserve the actual height needed at this width, including mode
            explanations and legend; the host grows rather than overlapping controls.
            Wrapped explanations are measured at the current panel width.
        """
        layout = self.layout()
        assert layout is not None
        layout.invalidate()
        required = max(
            self.minimumSizeHint().height(), self.heightForWidth(self.width())
        )
        if self.minimumHeight() != required:
            self.setMinimumHeight(required)

    def resizeEvent(self, event: QResizeEvent | None) -> None:  # noqa: N802
        """Recompute wrapped explanation height after width changes.

        Args:
            event: Owned Qt resize notification, or None for diagnostic calls.

        Returns:
            None; resize the existing panel and propagate its live minimum height.
        """
        super().resizeEvent(event)
        self.fit_content()

    def save_plot(self, parent: QWidget | None = None) -> None:
        """Export the current applied figure without accepting settings-dialog edits.

        Args:
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        name = (
            self.chart_combo.currentText()
            if self.chart() is not PlotChart.JOB
            else "plot-job-risk"
        )
        export_plot(self.canvas.figure, parent or self, self.language, name)

    def open_settings(self) -> None:
        """Keep a local draft; Apply redraws once, Close preserves the chart.

        Args:
            None.

        Returns:
            None.
        """
        if self.summary is None:
            return
        dialog = PlotGraphDialog(
            self.settings,
            self.icons,
            self.save_plot,
            language=self.language,
            parent=self,
        )
        try:
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.settings = dialog.settings()
                self.draw_current()
        finally:
            dialog.close()
            dialog.deleteLater()

    def open_viewer(self) -> None:
        """Expand a separate figure so closing cannot corrupt the embedded canvas.

        Args:
            None.

        Returns:
            None.
        """
        if self.summary is None:
            return
        dialog = PlotFigureViewer(
            self.make_figure(), self.icons, language=self.language, parent=self
        )
        try:
            dialog.exec()
        finally:
            dialog.close()
            dialog.deleteLater()

"""Original PLOT filtered metrics, aggregate gauges and station highlights.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Callable, Mapping

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QCloseEvent, QIcon, QResizeEvent
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.gauge_preferences import GaugeMarkerSettings
from ergotools.application.plot_results import PlotResults
from ergotools.application.plot_summaries import (
    PlotSummary,
    StationHighlight,
    plot_highlights,
    summarize_plot,
)
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.plot_filters import PlotRiskView
from ergotools.domain.risk import classify_probability
from ergotools.presentation.desktop.plot_highlight_dialog import PlotHighlightDialog
from ergotools.presentation.desktop.plot_marker_layer import PlotMarkerLayer
from ergotools.presentation.desktop.plot_risk_gauge import PlotRiskGauge
from ergotools.presentation.desktop.theme.plot import PLOT_STYLE
from ergotools.presentation.desktop.theme.risk import RISK_APPEARANCES
from ergotools.presentation.localization import Translator


class PlotOutcomePanel(QGroupBox):
    """Own original outcome controls; saved snapshots drive all displayed values."""

    def __init__(
        self,
        layer: PlotMarkerLayer,
        icons: Mapping[str, QIcon],
        *,
        language: Language = Language.ENGLISH,
        gauge_markers: GaugeMarkerSettings | None = None,
        change_gauge_markers: Callable[[GaugeMarkerSettings], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Compose reviewed source layout, palette and injected marker publication.

        Args:
            layer: Existing PLOT marker/history owner; this view borrows its selection
                and save operations.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            gauge_markers: Shared main/PLOT marker appearance, or defaults.
            change_gauge_markers: Host callback that saves and synchronizes all gauges.
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
        self._results: PlotResults | None = None
        self.summary: PlotSummary | None = None
        self.highlights: tuple[StationHighlight, ...] = ()
        self.setObjectName("outcome_group")
        self.setStyleSheet(PLOT_STYLE)
        root = QHBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 10)
        root.setSpacing(24)
        summary_panel = QWidget(self)
        summary_panel.setObjectName("outcomeSummaryPanel")
        summary_layout = QVBoxLayout(summary_panel)
        summary_layout.setContentsMargins(10, 6, 10, 6)
        summary_layout.setSpacing(0)
        heading = QLabel(self.text("Filtered results", "Resultados filtrados"))
        heading.setObjectName("outcomeSectionHeading")
        heading.setFixedHeight(18)
        summary_layout.addWidget(heading)
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(2)
        self.metrics = tuple(QLabel() for _ in range(10))
        for index, label in enumerate(self.metrics):
            label.setFixedHeight(18)
            grid.addWidget(label, index // 2, index % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        summary_layout.addLayout(grid)
        highlight_row = QHBoxLayout()
        highlight_row.setContentsMargins(0, 2, 0, 0)
        self.highlight_title = QLabel(self.text("Highlights", "Destacados"))
        self.highlight_title.setObjectName("outcometitle_label")
        highlight_row.addWidget(self.highlight_title)
        highlight_row.addStretch(1)
        self.details_button = QPushButton(self.text("View details", "Ver detalles"))
        self.details_button.setIcon(icons["view"])
        self.details_button.setIconSize(QSize(20, 20))
        self.details_button.setFixedHeight(30)
        self.details_button.setToolTip(
            self.text(
                "Open station-level details for the current warning.",
                "Abrir los detalles por estación del aviso actual.",
            )
        )
        self.details_button.clicked.connect(self.open_details)
        self.details_button.hide()
        highlight_row.addWidget(self.details_button)
        summary_layout.addLayout(highlight_row)
        self.highlight_label = QLabel()
        self.highlight_label.setWordWrap(True)
        self.highlight_label.setFixedHeight(24)
        summary_layout.addWidget(self.highlight_label)
        summary_panel.setMinimumWidth(600)
        root.addWidget(summary_panel, 1)
        root.addStretch(1)
        cluster = QFrame(self)
        cluster.setObjectName("outcomeRiskCluster")
        cluster_layout = QHBoxLayout(cluster)
        cluster_layout.setContentsMargins(12, 8, 12, 8)
        cluster_layout.setSpacing(8)
        self.ranges = QWidget(cluster)
        ranges_layout = QVBoxLayout(self.ranges)
        ranges_layout.setContentsMargins(0, 0, 0, 0)
        ranges_layout.setSpacing(4)
        heading = QLabel(self.text("Risk ranges", "Rangos de riesgo"))
        heading.setObjectName("outcomeSectionHeading")
        ranges_layout.addWidget(heading)
        self.range_labels: list[QLabel] = []
        translator = Translator(language)
        for appearance in RISK_APPEARANCES.values():
            label = QLabel(
                f"<span style='color:{appearance.color_hex}; "
                "font-size:16px;'>●</span>  "
                f"{translator.text(appearance.message_key)}   {appearance.range_label}"
            )
            label.setObjectName("outcomeRangeLabel")
            label.setProperty("compact", False)
            self.range_labels.append(label)
            ranges_layout.addWidget(label)
        ranges_layout.addStretch(1)
        self.ranges.setFixedWidth(300)
        cluster_layout.addWidget(self.ranges)
        cluster_layout.addWidget(self.divider())
        self.stack = QStackedWidget(cluster)
        self.stack.setObjectName("outcomeResultStack")
        self.stack.setFixedWidth(440)
        single = QWidget(self.stack)
        single.setObjectName("outcomeResultPanel")
        single_layout = QVBoxLayout(single)
        single_layout.setContentsMargins(0, 0, 0, 0)
        single_layout.setSpacing(3)
        risk_header = QHBoxLayout()
        self.risk_title = QLabel()
        self.risk_title.setObjectName("outcomeSectionHeading")
        self.risk_title.setWordWrap(True)
        self.risk_label = QLabel()
        self.risk_label.setObjectName("outcomeRiskLabel")
        self.risk_label.setWordWrap(True)
        self.risk_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        risk_header.addStretch(1)
        risk_header.addWidget(self.risk_title)
        risk_header.addSpacing(12)
        risk_header.addWidget(self.risk_label)
        risk_header.addStretch(1)
        single_layout.addLayout(risk_header)
        self.gauge = PlotRiskGauge(
            gauge_markers, change_gauge_markers, dialog_icons=icons
        )
        self.gauge.setToolTip(
            self.text(
                "Average outcome probability for enabled workers in the "
                "current filter scope.",
                "Probabilidad media de los trabajadores habilitados en "
                "los filtros actuales.",
            )
        )
        single_layout.addWidget(self.gauge, 0, Qt.AlignmentFlag.AlignCenter)
        caption = QLabel(
            self.text(
                "Average probability of outcome", "Probabilidad media del resultado"
            )
        )
        caption.setObjectName("outcomeGaugeCaption")
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        single_layout.addWidget(caption)
        single_layout.addStretch(1)
        self.stack.addWidget(single)
        comparison = QWidget(self.stack)
        comparison.setObjectName("comparisonGaugePanel")
        comparison_layout = QHBoxLayout(comparison)
        comparison_layout.setContentsMargins(0, 0, 0, 0)
        comparison_layout.setSpacing(8)
        self.individual_gauge, self.individual_label = self.comparison_column(
            comparison_layout,
            self.text("Individual average", "Promedio individual"),
            self.text("Worker assessments", "Evaluaciones individuales"),
            self.text(
                "Average individual outcome probability for enabled "
                "workers in the current filter scope.",
                "Probabilidad individual media de los trabajadores habilitados.",
            ),
            gauge_markers=gauge_markers,
            change_gauge_markers=change_gauge_markers,
            icons=icons,
        )
        comparison_layout.addWidget(self.divider())
        self.job_gauge, self.job_label = self.comparison_column(
            comparison_layout,
            self.text("Job average", "Promedio del trabajo"),
            self.text("Applicable Job risks", "Riesgos del trabajo aplicables"),
            self.text(
                "Average applicable Job risk for enabled workers with an"
                " available Job risk value.",
                "Riesgo medio del trabajo para trabajadores con evidencia disponible.",
            ),
            gauge_markers=gauge_markers,
            change_gauge_markers=change_gauge_markers,
            icons=icons,
        )
        self.stack.addWidget(comparison)
        cluster_layout.addWidget(self.stack)
        self.risk_cluster = cluster
        cluster.setFixedWidth(701)
        root.addWidget(cluster)
        for gauge in (self.gauge, self.individual_gauge, self.job_gauge):
            gauge.marker_language = language
        self.setMinimumWidth(700)
        self.setFixedHeight(210)
        layer.changed.connect(self.refresh)
        self.update_view()
        self.refresh()

    def text(self, english: str, spanish: str) -> str:
        """Translate presentation only; station identities remain source literals.

        Args:
            english: English UI text; saved user values are never translated by this
                helper.
            spanish: Spanish UI text corresponding to the English caption.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return spanish if self.language is Language.SPANISH else english

    @staticmethod
    def divider() -> QFrame:
        """Construct the original one-pixel vertical risk-cluster divider.

        Args:
            None.

        Returns:
            New owned one-pixel source divider frame.
        """
        frame = QFrame()
        frame.setObjectName("riskClusterDivider")
        frame.setFrameShape(QFrame.Shape.VLine)
        frame.setFixedWidth(1)
        return frame

    @staticmethod
    def comparison_column(
        layout: QHBoxLayout,
        title: str,
        caption: str,
        tooltip: str,
        *,
        gauge_markers: GaugeMarkerSettings | None = None,
        change_gauge_markers: Callable[[GaugeMarkerSettings], None] | None = None,
        icons: Mapping[str, QIcon] | None = None,
    ) -> tuple[PlotRiskGauge, QLabel]:
        """Compose the source compact column; own its gauge and status explicitly.

        Args:
            layout: Owned horizontal comparison layout receiving the new gauge/status
                column.
            title: Localized message/window title; never used as a stored identifier.
            caption: Visible control heading; record identities remain separate item
                data.
            gauge_markers: Shared marker options, or defaults.
            change_gauge_markers: Injected preference save/synchronization callback.
            icons: Packaged prompt button icons, if supplied by the host.
            tooltip: Full literal scope value retained for accessible/hover display when
                the label is elided.

        Returns:
            Owned gauge and status label composed into the supplied layout.
        """
        column = QWidget()
        root = QVBoxLayout(column)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(1)
        heading = QLabel(title)
        heading.setObjectName("outcomeSectionHeading")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status = QLabel()
        status.setObjectName("comparisonRiskLabel")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gauge = PlotRiskGauge(gauge_markers, change_gauge_markers, dialog_icons=icons)
        gauge.setMinimumWidth(210)
        gauge.setToolTip(tooltip)
        caption_label = QLabel(caption)
        caption_label.setObjectName("comparisonGaugeCaption")
        caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(heading)
        root.addWidget(status)
        root.addWidget(gauge, 0, Qt.AlignmentFlag.AlignCenter)
        root.addWidget(caption_label)
        root.addStretch(1)
        layout.addWidget(column, 1)
        return gauge, status

    def refresh(self) -> None:
        """Publish saved membership once; visual previews do not recompute.

        Args:
            None.

        Returns:
            None.
        """
        results = self.layer.results
        if results is self._results:
            # Map membership can change without replacing immutable risk results.
            self.update_view()
            return
        self._results = results
        self.summary = (
            summarize_plot(results, current_year=self.layer.current_year)
            if results
            else None
        )
        self.highlights = plot_highlights(results) if results else ()
        self.update_view()

    def show_risk(
        self,
        gauge: PlotRiskGauge,
        label: QLabel,
        percent: float | None,
        *,
        comparison: bool = False,
    ) -> None:
        """Project absence and valid percentages on the shared categorical scale.

        Args:
            gauge: Owned risk gauge receiving an optional observed probability
                percentage.
            label: Owned status label to update from observed risk.
            percent: Observed probability in percent (0-100), or None for unavailable
                evidence.
            comparison: True applies comparison-specific captions/layout; risk data
                remain unchanged.

        Returns:
            None.
        """
        gauge.set_probability(percent)
        if percent is None:
            label.setText(
                self.text(
                    "<span style='color:#758590;'>●</span> Not available",
                    "<span style='color:#758590;'>●</span> No disponible",
                )
            )
        else:
            appearance = RISK_APPEARANCES[classify_probability(percent)]
            severity = Translator(self.language).text(appearance.message_key)
            spacing = " · " if comparison else "  ·  "
            label.setText(
                f"<span style='color:{appearance.color_hex};'>●</span> "
                f"{severity}{spacing}{percent:.1f}%"
            )

    def update_view(self) -> None:
        """Update original metrics, gauge mode, legend and warning together.

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
        kind = self._results.selection.tool if self._results else AssessmentKind.LIFFT
        name = {
            AssessmentKind.LIFFT: "LiFFT",
            AssessmentKind.DUET: "DUET",
            AssessmentKind.TST: "ST",
        }[kind]
        title_name = (
            self.text("Shoulder", "Hombro") if kind is AssessmentKind.TST else name
        )
        self.setTitle(
            self.text(f"{title_name} Tool Outcome", f"Resultado de {title_name}")
        )
        job = mode is PlotRiskView.JOB
        comparison = mode is PlotRiskView.COMPARISON
        self.stack.setCurrentIndex(1 if comparison else 0)
        self.ranges.setFixedWidth(250 if comparison else 300)
        self.stack.setFixedWidth(450 if comparison else 360)
        self.risk_cluster.setFixedWidth(741 if comparison else 701)
        for label in self.range_labels:
            label.setProperty("compact", comparison)
            style = label.style()
            assert style is not None
            style.unpolish(label)
            style.polish(label)
        subject = (
            self.text("Job", "trabajo") if job else self.text("worker", "trabajador")
        )
        score = (
            self.text("Job", "Trabajo")
            if job
            else self.text("Individual", "Individual")
        )
        self.risk_title.setText(
            self.text(
                f"{name} {score} Group Risk Score:", f"Riesgo grupal {name} {score}:"
            )
        )
        if job:
            self.risk_title.setText(
                self.text(
                    f"{name} Job average (workplace scope):",
                    f"Media del trabajo {name} (ámbito):",
                )
            )
        self.gauge.setToolTip(
            self.text(
                "Placement-weighted Job average in the current workplace scope. "
                "Repeated map occurrences reuse each Job's current assessment."
                if job
                else "Average outcome probability for enabled worker assignments.",
                "Media por ubicación del trabajo en el ámbito actual. Las ubicaciones "
                "del mapa usan la evaluación actual de cada trabajo."
                if job
                else "Probabilidad media de las asignaciones habilitadas.",
            )
        )
        values = self.metric_values(job=job, comparison=comparison, tool=name)
        for target, (metric_label, value) in zip(self.metrics, values, strict=True):
            target.setText(f"<b>{metric_label}:</b> {value}")
        summary = self.summary
        percent = (
            (
                summary.jobs.risk.mean_percent
                if job
                else summary.workers.risk.mean_percent
            )
            if summary
            else None
        )
        self.show_risk(self.gauge, self.risk_label, percent)
        self.show_risk(
            self.individual_gauge,
            self.individual_label,
            summary.workers.risk.mean_percent if summary and comparison else None,
            comparison=True,
        )
        self.show_risk(
            self.job_gauge,
            self.job_label,
            summary.workers.applicable_job_risk_percent
            if summary and comparison
            else None,
            comparison=True,
        )
        total = (
            (summary.jobs.placements if job else summary.workers.total)
            if summary
            else 0
        )
        if not total:
            message = self.text(
                f"No {subject} results match the current filters.",
                f"Ningún resultado de {subject} coincide con los filtros actuales.",
            )
        elif percent is None:
            message = (
                self.text(
                    "Active Job placements are in scope, but no current "
                    "Job risk value is available for this ergonomic "
                    "tool.",
                    "Hay trabajos ubicados, pero no hay valores actuales de "
                    "riesgo para esta herramienta.",
                )
                if job
                else self.text(
                    "Worker results are in scope, but no evaluated outcome "
                    "probability is available for this ergonomic tool.",
                    "Hay resultados de trabajadores, pero no existe una "
                    "probabilidad evaluada para esta herramienta.",
                )
            )
        elif self.highlights:
            count = sum(detail.count for detail in self.highlights)
            stations = len(self.highlights)
            message = self.text(
                f"Warning: {count} high-risk {subject} "
                f"{'result' if count == 1 else 'results'} found "
                f"across {stations} "
                f"{'station' if stations == 1 else 'stations'} (>50%).",
                f"Aviso: {count} resultados de {subject} de alto riesgo "
                f"en {stations} estaciones (>50%).",
            )
        else:
            message = self.text(
                f"No high-risk {subject} results were found "
                "in the current filter scope.",
                f"No se encontraron resultados de {subject} de alto riesgo "
                "en los filtros actuales.",
            )
        self.highlight_label.setText(message)
        self.highlight_label.setToolTip(message)
        self.highlight_label.setStyleSheet(
            "color: red; font-weight: bold;"
            if self.highlights
            else "color: #526777; font-weight: 600;"
        )
        self.details_button.setVisible(bool(self.highlights))
        self.fit_content()

    def fit_content(self) -> None:
        """Fit original fixed-format regions and wrapped warnings without clipping.

        Args:
            None.

        Returns:
            None.
        """
        layout = self.layout()
        assert layout is not None
        layout.invalidate()
        # The source's 700-pixel floor is smaller than its two fixed-format regions.
        self.setMinimumWidth(max(700, layout.minimumSize().width()))
        warning_height = max(
            24,
            self.highlight_label.heightForWidth(max(580, self.highlight_label.width())),
        )
        if self.highlight_label.height() != warning_height:
            self.highlight_label.setFixedHeight(warning_height)
            layout.invalidate()
        required_height = layout.totalHeightForWidth(
            max(self.width(), self.minimumWidth())
        )
        if self.height() != max(210, required_height):
            self.setFixedHeight(max(210, required_height))

    def resizeEvent(self, event: QResizeEvent | None) -> None:  # noqa: N802
        """Reflow warnings without refreshing datasets or restarting gauges.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        super().resizeEvent(event)
        self.fit_content()

    def metric_values(
        self, *, job: bool, comparison: bool, tool: str
    ) -> tuple[tuple[str, str], ...]:
        """Format the ten source cells; None stays absent rather than becoming zero.

        Args:
            job: True selects job-placement geometry/metrics instead of
                individual-worker geometry/metrics.
            comparison: True applies comparison-specific captions/layout; risk data
                remain unchanged.
            tool: Selected ergonomic tool whose saved risk evidence is presented.

        Returns:
            Ten localized caption/value pairs for the selected saved summary mode;
            absent observations remain dashes.
        """
        summary = self.summary

        def number(value: float | None, spec: str = ".1f", suffix: str = "") -> str:
            """Format an optional saved metric for display; absence uses a dash.

            Format an optional saved metric for display; absence uses a dash and
            receives no numeric suffix.

            Args:
                value: Observed metric, or None for missing evidence; formatting never
                    changes storage.
                spec: Python numeric display format; applies only to the returned text.
                suffix: Display suffix appended only when a numeric value is present.

            Returns:
                Display-formatted saved metric with suffix, or an en dash for
                unavailable evidence.
            """
            return "\u2013" if value is None else format(value, spec) + suffix

        if job and summary:
            jobs = summary.jobs
            return tuple(
                (self.text(en, es), value)
                for en, es, value in (
                    ("Jobs in scope", "Trabajos del ámbito", str(jobs.unique_jobs)),
                    ("Active placements", "Ubicaciones activas", str(jobs.placements)),
                    (
                        "Squares on map",
                        "Cuadrados en el mapa",
                        str(
                            sum(
                                item.isVisible()
                                for key, item in self.layer.items.items()
                                if key[0] == "job"
                            )
                        ),
                    ),
                    (
                        "Unmapped assignments",
                        "Asignaciones sin marcador",
                        str(
                            sum(
                                ("job", row.assessment.assignment_id)
                                not in self.layer.items
                                or not self.layer.items[
                                    "job", row.assessment.assignment_id
                                ].isVisible()
                                for row in self._results.workers
                            )
                        )
                        if self._results
                        else "0",
                    ),
                    (
                        "Jobs with risk values",
                        "Trabajos con valores de riesgo",
                        str(jobs.jobs_with_risks),
                    ),
                    (
                        "Average Job damage",
                        "Daño medio del trabajo",
                        number(jobs.damage, ".4f"),
                    ),
                    (
                        "Scoped placement average",
                        "Media de ubicaciones del ámbito",
                        number(jobs.risk.mean_percent, suffix="%"),
                    ),
                    (
                        "Minimum Job risk",
                        "Riesgo mínimo del trabajo",
                        number(jobs.minimum_risk_percent, suffix="%"),
                    ),
                    (
                        "Maximum Job risk",
                        "Riesgo máximo del trabajo",
                        number(jobs.maximum_risk_percent, suffix="%"),
                    ),
                    ("Ergonomic tool", "Herramienta ergonómica", tool),
                )
            )
        worker = summary.workers if summary else None
        return tuple(
            (self.text(en, es), value)
            for en, es, value in (
                (
                    "Total Workers",
                    "Total de trabajadores",
                    str(worker.total if worker else 0),
                ),
                (
                    "Average Age",
                    "Edad media",
                    str(int(worker.average_age))
                    if worker and worker.average_age is not None
                    else "\u2013",
                ),
                ("Males", "Hombres", str(worker.males if worker else 0)),
                ("Females", "Mujeres", str(worker.females if worker else 0)),
                (
                    "Male avg. damage",
                    "Daño medio masculino",
                    number(worker.male_damage if worker else None, ".4f"),
                ),
                (
                    "Female avg. damage",
                    "Daño medio femenino",
                    number(worker.female_damage if worker else None, ".4f"),
                ),
                (
                    "Male avg. risk",
                    "Riesgo medio masculino",
                    number(
                        worker.male_risk.mean_percent if worker else None, suffix="%"
                    ),
                ),
                (
                    "Female avg. risk",
                    "Riesgo medio femenino",
                    number(
                        worker.female_risk.mean_percent if worker else None, suffix="%"
                    ),
                ),
                (
                    "Overall avg. individual risk",
                    "Riesgo individual medio",
                    number(worker.risk.mean_percent if worker else None, suffix="%"),
                )
                if comparison
                else (
                    "Overall avg. damage",
                    "Daño medio total",
                    number(worker.damage if worker else None, ".4f"),
                ),
                (
                    "Avg. difference",
                    "Diferencia media",
                    number(
                        worker.difference_percentage_points if worker else None,
                        "+.1f",
                        self.text(" percentage points", " puntos porcentuales"),
                    ),
                )
                if comparison
                else (
                    "Overall avg. individual risk",
                    "Riesgo individual medio",
                    number(worker.risk.mean_percent if worker else None, suffix="%"),
                ),
            )
        )

    def open_details(self) -> None:
        """Open the original modal warning table for the currently saved snapshot.

        Args:
            None.

        Returns:
            None.
        """
        if not self.highlights or self._results is None:
            return
        dialog = PlotHighlightDialog(
            self.highlights,
            self._results.selection.tool,
            self.icons,
            job_view=self._results.selection.risk_view is PlotRiskView.JOB,
            language=self.language,
            parent=self,
        )
        try:
            dialog.exec()
        finally:
            dialog.close()
            dialog.deleteLater()

    def closeEvent(self, event: QCloseEvent | None) -> None:  # noqa: N802
        """Stop owned animations on closure without touching saved results.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        for gauge in (self.gauge, self.individual_gauge, self.job_gauge):
            gauge.animation.stop()
        super().closeEvent(event)

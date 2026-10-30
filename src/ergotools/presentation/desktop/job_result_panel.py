"""Job projections into the main assessment sidebar and inline summary controls.

Presentation layer. Reuse actual ResultsSidebar and ToolResultSummary widgets;
project existing immutable Job values without manufacturing worker assessments,
recalculating results or introducing any storage/history path.
"""

from collections.abc import Callable, Mapping

from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ergotools.application.gauge_preferences import GaugeMarkerSettings
from ergotools.application.settings import Language
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.display_precision import DisplayPrecision
from ergotools.domain.job_risk import JobRiskMeasurement
from ergotools.domain.risk import classify_probability
from ergotools.presentation.desktop.job_direct_values import JobDirectValues
from ergotools.presentation.desktop.results_sidebar import ResultsSidebar
from ergotools.presentation.desktop.theme.job_results import job_damage_color
from ergotools.presentation.desktop.theme.main_workspace import MAIN_WORKSPACE_STYLE
from ergotools.presentation.desktop.theme.risk import RISK_APPEARANCES
from ergotools.presentation.desktop.tool_result_summary import ToolResultSummary
from ergotools.presentation.desktop.workspace_text import workspace_text


class JobResultPanel(ResultsSidebar):
    """Project one selected Job/tool into the shared main cards, plus a risk legend."""

    def __init__(
        self,
        language: Language,
        convention: DecimalConvention,
        icons: Mapping[str, QIcon],
        markers: GaugeMarkerSettings | None = None,
        change_markers: Callable[[GaugeMarkerSettings], None] | None = None,
        *,
        parent: QWidget,
        precision: DisplayPrecision | None = None,
    ) -> None:
        """Construct the actual main sidebar without its individual-worker ownership.

        Args:
            language: Static UI wording and gauge prompt language.
            convention: Explicit decimal separator for labels/tooltips.
            icons: Packaged icons for the shared gauge settings dialog.
            markers: Personal marker preferences, independent of project values.
            change_markers: Host preference owner, never project history.
            parent: Required Qt lifetime owner.
            precision: Project display policy, separate from stored quantities.

        Returns:
            None; adding the legend creates no measurement or assessment record.
        """
        super().__init__(
            parent=parent,
            icons=icons,
            gauge_markers=markers,
            change_gauge_markers=change_markers,
        )
        self.language = language
        self.convention = convention
        self.display_precision = precision or DisplayPrecision()
        self.setStyleSheet(MAIN_WORKSPACE_STYLE)
        self.setMinimumWidth(290)
        self.setMaximumWidth(310)
        layout = self.layout()
        assert isinstance(layout, QVBoxLayout)
        card = QFrame()
        card.setObjectName("summaryCard")
        legend = QVBoxLayout(card)
        legend.setContentsMargins(8, 6, 8, 6)
        heading = QLabel(
            "Rangos de riesgo" if language is Language.SPANISH else "Risk ranges"
        )
        heading.setObjectName("summaryTitle")
        legend.addWidget(heading)
        for appearance in RISK_APPEARANCES.values():
            row = QHBoxLayout()
            label = QLabel(
                f'<span style="color:{appearance.color_hex}">●</span> '
                + workspace_text(appearance.english_label, language)
            )
            label.setWordWrap(False)
            row.addWidget(label, 1)
            row.addWidget(QLabel(appearance.range_label.replace(".", convention.value)))
            legend.addLayout(row)
        layout.insertWidget(layout.count() - 1, card)

    def show_measurement(self, item: JobRiskMeasurement) -> None:
        """Update shared cards from exact Job data, clearing every obsolete output.

        Args:
            item: Selected tool's source/current output; absence is distinct from zero.

        Returns:
            None; view formatting, bands and animation never modify stored quantities.
        """
        self.update_result(
            item.source,
            None,
            self.language,
            empty_kind=item.kind,
            precision=self.display_precision,
        )
        tool = {
            AssessmentKind.LIFFT: "LiFFT",
            AssessmentKind.DUET: "DUET",
            AssessmentKind.TST: "ST",
        }[item.kind]
        self.individual_risk_title.setText(
            ("Trabajo " if self.language is Language.SPANISH else "Job ") + tool
        )
        probability = item.probability_percent if item.complete else None
        self.risk_gauge.set_probability(probability)
        damage = item.cumulative_damage
        self.damage_value_label.setToolTip(
            "" if damage is None else str(damage).replace(".", self.convention.value)
        )
        if damage is not None:
            color = job_damage_color(item.kind, damage)
            self.damage_progress.set_value(damage, color)
            self.damage_value_label.setText(
                (
                    ">2.0" if damage > 2 else f"{damage:.{self.precision.damage}f}"
                ).replace(".", self.convention.value)
            )
            self.damage_value_label.setStyleSheet(
                result_value_style(color) + "font-size: 20px; padding: 7px 10px;"
            )
        if probability is not None:
            appearance = RISK_APPEARANCES[classify_probability(probability)]
            self.risk_severity_label.setText(
                "● "
                + workspace_text(
                    appearance.english_label.removesuffix(" Risk"), self.language
                )
            )
            self.risk_severity_label.setStyleSheet(
                f"color: {appearance.color_hex}; font-weight: 700;"
            )
        ready = item.complete
        self.assessment_status_label.setText(
            workspace_text("Ready" if ready else "Incomplete", self.language)
        )
        self.assessment_status_label.setProperty("ready", ready)
        style = self.assessment_status_label.style()
        assert style is not None
        style.unpolish(self.assessment_status_label)
        style.polish(self.assessment_status_label)
        self.assessment_status_detail.setText(
            (
                "Calculado a partir de tareas"
                if self.language is Language.SPANISH
                else "Calculated from task inputs"
            )
            if ready and item.source
            else (
                "Resultado directo · sin tareas registradas"
                if self.language is Language.SPANISH
                else "Direct result · no recorded tasks"
            )
            if ready
            else (
                "Agregue tareas y calcule."
                if self.language is Language.SPANISH
                else "Add tasks, then Calculate."
            )
        )
        moments = [t.moment for t in item.task_results if t.moment is not None]
        self.metric_labels["max_moment"].setText(
            f"{max(moments):.{self.precision.moment}f}" if moments else "—"
        )


def result_value_style(color: str) -> str:
    """Keep result backgrounds and foreground contrast consistent with main cards.

    Args:
        color: Valid tool-specific continuous damage palette color.

    Returns:
        Stylesheet for an assessment result label; values remain separately owned.
    """
    shade = QColor(color)
    luminance = 0.2126 * shade.redF() + 0.7152 * shade.greenF() + 0.0722 * shade.blueF()
    foreground = "#102A43" if luminance > 0.58 else "#FFFFFF"
    return (
        f"background: {color}; color: {foreground}; border-radius: 4px; "
        "padding: 6px 10px; font-weight: 700;"
    )


class JobCalculationSummary(QWidget):
    """Use the same inline damage/probability summary as all main assessment panels."""

    def __init__(
        self,
        language: Language,
        convention: DecimalConvention,
        precision: DisplayPrecision | None = None,
    ) -> None:
        """Build the shared summary without evaluating or storing any value.

        Args:
            language: English/Spanish caption language.
            convention: Explicit decimal mark for display only.
            precision: Project display decimals, without rounding stored values.

        Returns:
            None.
        """
        super().__init__()
        self.language = language
        self.convention = convention
        self.precision = precision or DisplayPrecision()
        self.summary = ToolResultSummary()
        self.setLayout(self.summary)
        self.direct_values: JobDirectValues | None = None

    def bind_direct_values(self, editor: JobDirectValues) -> None:
        """Use the direct editor in the existing total value cell, never a second form.

        Args:
            editor: Owned per-tool damage stack with exact input precision and signals.

        Returns:
            None; this binds presentation only and does not accept or calculate input.
        """
        self.direct_values = editor
        self.summary.addWidget(editor, 0, 1)
        editor.hide()

    def set_direct_mode(self, enabled: bool) -> None:
        """Swap colored damage display for its editable equivalent in direct mode.

        Args:
            enabled: True only for a selected tool without task inputs.

        Returns:
            None; probability remains derived and read-only in its existing row.
        """
        if self.direct_values is not None:
            self.direct_values.setVisible(enabled)
            self.summary.total_value.setVisible(not enabled)

    def show_measurement(self, item: JobRiskMeasurement) -> None:
        """Format existing selected-tool outputs into the shared main summary rows.

        Args:
            item: Source/current result; missing output clears the labels and colors.

        Returns:
            None; exact precision remains in tooltips, independent of visible rounding.
        """
        spanish = self.language is Language.SPANISH
        self.summary.total_title.setText(
            "Daño Acumulado Total:" if spanish else "Total Cumulative Damage:"
        )
        captions = {
            AssessmentKind.LIFFT: (
                "Probability of High Risk Job * (%):",
                "Probabilidad de Trabajo de Alto Riesgo * (%):",
            ),
            AssessmentKind.DUET: (
                "Probability of Distal Upper Extremity Outcome (%):",
                "Probabilidad de lesión de extremidad superior distal (%):",
            ),
            AssessmentKind.TST: (
                "Probability of Shoulder Outcome (%):",
                "Probabilidad de lesión de hombro (%):",
            ),
        }
        self.summary.probability_title.setText(captions[item.kind][int(spanish)])
        damage, probability = item.cumulative_damage, item.probability_percent
        self.summary.show_values(
            "—"
            if damage is None
            else f"{damage:.{self.precision.damage}f}".replace(
                ".", self.convention.value
            ),
            "—"
            if probability is None
            else f"{probability:.{self.precision.probability}f}".replace(
                ".", self.convention.value
            ),
            None if damage is None else job_damage_color(item.kind, damage),
        )
        if self.direct_values is not None:
            field = self.direct_values.fields[item.kind]
            style = self.summary.total_value.styleSheet()
            field.setStyleSheet(
                "QLineEdit { " + style + " min-height: 30px; padding: 0 6px; "
                "border: 1px solid #9EB0BE; } "
                "QLineEdit:focus { border: 2px solid #08A9B5; }"
            )
        for (_, label), value in zip(
            self.summary.rows, (damage, probability), strict=True
        ):
            label.setToolTip("" if value is None else str(value))

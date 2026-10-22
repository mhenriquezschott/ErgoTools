"""Reviewed original result cards, updated from typed current assessment results.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Callable, Mapping
from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from ergotools.application.assessments.evaluation import (
    AssessmentEvaluation,
    EvaluationStatus,
)
from ergotools.application.gauge_preferences import GaugeMarkerSettings
from ergotools.application.historical_results import HistoricalAssessmentResult
from ergotools.application.settings import Language
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    assessment_kind,
)
from ergotools.domain.assessments.duet_summary import DuetSummary
from ergotools.domain.assessments.lifft import LifftTaskResult
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.assessments.lifft_summary import LifftSummary
from ergotools.domain.assessments.tst import TstTaskResult
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.assessments.tst_summary import TstSummary
from ergotools.domain.display_precision import DisplayPrecision
from ergotools.domain.risk import classify_probability
from ergotools.presentation.desktop.historical_result_display import (
    historical_damage_color,
)
from ergotools.presentation.desktop.result_scales import DamageScale, RiskGauge
from ergotools.presentation.desktop.theme.duet_summary import display_duet_summary
from ergotools.presentation.desktop.theme.lifft_summary import display_lifft_summary
from ergotools.presentation.desktop.theme.risk import RISK_APPEARANCES
from ergotools.presentation.desktop.theme.tst_summary import display_tst_summary
from ergotools.presentation.desktop.workspace_text import workspace_text


class ResultsSidebar(QFrame):
    """Own original cards only; never parse another widget or read storage."""

    def __init__(
        self,
        *,
        parent: QWidget,
        icons: Mapping[str, QIcon] | None = None,
        gauge_markers: GaugeMarkerSettings | None = None,
        change_gauge_markers: Callable[[GaugeMarkerSettings], None] | None = None,
    ) -> None:
        """Construct the reviewed setupResultsSidebar controls and sizes.

        Args:
            icons: Optional packaged icons for the shared interval prompt.
            gauge_markers: Initial personal marker preferences, or None for defaults.
            change_gauge_markers: Optional host persistence/apply callback; None keeps
                right-click changes local to this gauge.
            parent: Required Qt owner of the new control; ownership follows the parent
                widget lifetime.

        Returns:
            None.
        """
        super().__init__(parent)
        self.setObjectName("resultsSidebar")
        self.setMinimumWidth(230)
        self.setMaximumWidth(260)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(5)
        risk_card = QFrame()
        risk_card.setObjectName("summaryCard")
        risk_card.setFixedHeight(235)
        risk_layout = QVBoxLayout(risk_card)
        risk_layout.setContentsMargins(10, 10, 10, 10)
        risk_layout.setSpacing(4)
        risk_header_widget = QWidget()
        self.risk_header_widget = risk_header_widget
        risk_header_widget.setFixedHeight(42)
        risk_header = QGridLayout(risk_header_widget)
        risk_header.setContentsMargins(0, 0, 0, 0)
        risk_header.setHorizontalSpacing(4)
        risk_header.setVerticalSpacing(0)
        self.individual_risk_title = QLabel("Individual LiFFT")
        self.individual_risk_title.setObjectName("summaryTitle")
        self.individual_risk_title.setToolTip(
            "Estimated individual probability for the adverse outcome "
            "calculated by the active ergonomic tool."
        )
        self.risk_level_title = QLabel("Risk Level")
        self.risk_level_title.setObjectName("summaryTitle")
        self.risk_severity_label = QLabel("Low")
        self.risk_severity_label.setObjectName("riskSeverity")
        self.risk_severity_label.setMinimumWidth(0)
        self.risk_severity_label.setAlignment(
            Qt.AlignmentFlag(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
        )
        risk_header.addWidget(self.individual_risk_title, 0, 0, 1, 2)
        risk_header.addWidget(self.risk_level_title, 1, 0)
        risk_header.addWidget(self.risk_severity_label, 1, 1)
        risk_header.setColumnStretch(0, 1)
        self.risk_gauge = RiskGauge(
            gauge_markers, change_gauge_markers, dialog_icons=icons
        )
        risk_layout.addWidget(risk_header_widget)
        risk_layout.addWidget(self.risk_gauge)
        risk_layout.addStretch(1)
        layout.addWidget(risk_card)
        damage_card = QFrame()
        damage_card.setObjectName("summaryCard")
        damage_layout = QVBoxLayout(damage_card)
        damage_layout.setContentsMargins(8, 6, 8, 6)
        damage_layout.setSpacing(4)
        damage_title = QLabel("Cumulative damage")
        damage_title.setObjectName("summaryTitle")
        damage_title.setToolTip(
            "Combined cumulative damage contribution from the entered tasks."
        )
        self.damage_value_label = QLabel("0.0000")
        self.damage_value_label.setObjectName("metricValue")
        self.damage_progress = DamageScale()
        self.damage_progress.setToolTip(
            "Cumulative damage scale: 0 at the left, 1 at the midpoint, "
            "and values above 2 capped at >2."
        )
        damage_layout.addWidget(damage_title)
        damage_layout.addWidget(self.damage_value_label)
        damage_layout.addWidget(self.damage_progress)
        layout.addWidget(damage_card)
        metrics_card = QFrame()
        metrics_card.setObjectName("summaryCard")
        metrics_layout = QGridLayout(metrics_card)
        metrics_layout.setContentsMargins(8, 6, 8, 6)
        metrics_layout.setHorizontalSpacing(6)
        metrics_layout.setVerticalSpacing(4)
        metrics_title = QLabel("Key metrics")
        metrics_title.setObjectName("summaryTitle")
        metrics_title.setToolTip(
            "A live summary of the task data entered for the active tool."
        )
        metrics_layout.addWidget(metrics_title, 0, 0, 1, 2)
        self.metric_labels: dict[str, QLabel] = {}
        for row, (key, label) in enumerate(
            (
                ("tasks", "Tasks"),
                ("repetitions", "Repetitions"),
                ("average_load", "Average load"),
                ("max_moment", "Max moment"),
            ),
            start=1,
        ):
            metrics_layout.addWidget(QLabel(label), row, 0)
            value = QLabel("0")
            value.setAlignment(Qt.AlignmentFlag.AlignRight)
            value.setObjectName("metricSmallValue")
            metrics_layout.addWidget(value, row, 1)
            self.metric_labels[key] = value
        layout.addWidget(metrics_card)
        status_card = QFrame()
        self.status_card = status_card
        status_card.setObjectName("summaryCard")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(8, 6, 8, 6)
        status_layout.setSpacing(3)
        status_title = QLabel("Status")
        status_title.setObjectName("summaryTitle")
        status_title.setToolTip(
            "Indicates whether the active assessment contains "
            "data that can be evaluated."
        )
        self.assessment_status_label = QLabel("Ready")
        self.assessment_status_label.setObjectName("readyStatus")
        self.assessment_status_detail = QLabel("Select a context and enter task data.")
        self.assessment_status_detail.setObjectName("supportingText")
        self.assessment_status_detail.setWordWrap(True)
        status_layout.addWidget(status_title)
        status_layout.addWidget(self.assessment_status_label)
        status_layout.addWidget(self.assessment_status_detail)
        layout.addWidget(status_card)
        layout.addStretch()
        self.precision = DisplayPrecision()
        self._damage_tip = self.damage_progress.toolTip()
        self._labels = tuple(
            (label, label.text(), label.toolTip())
            for label in self.findChildren(QLabel)
            if label
            not in (
                self.risk_severity_label,
                self.damage_value_label,
                self.assessment_status_label,
                self.assessment_status_detail,
                *self.metric_labels.values(),
            )
        )

    def update_result(
        self,
        source: AssessmentDraft | None,
        result: AssessmentEvaluation | None,
        language: Language,
        *,
        empty_kind: AssessmentKind = AssessmentKind.LIFFT,
        historical: HistoricalAssessmentResult | None = None,
        precision: DisplayPrecision | None = None,
    ) -> None:
        """Replace all cards atomically from current canonical inputs and results.

        The caller passes only an evaluator.current(active) result or matching saved
        result cache, never both. Unknown risk clears animation immediately. PARTIAL
        outputs retain the incomplete status. Metrics follow reference counting/rounding
        and use recorded source units.

        Args:
            source: Current canonical assessment inputs, or None with no selected
                assessment; supplied results must match these inputs.
            result: Current source-bound evaluation, including partial status, or None
                without current results.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            precision: Project-saved display decimals; scientific values/colors are
                unchanged.
            empty_kind: Tool whose captions remain visible when no assessment source is
                active.
            historical: Matching saved result cache, or None; caller supplies it only
                without a current evaluation.

        Returns:
            None.
        """
        precision = precision or DisplayPrecision()
        self.precision = precision
        self.risk_gauge.decimal_places = precision.probability
        text = partial(workspace_text, language=language)
        for label, caption, tip in self._labels:
            label.setText(text(caption))
            label.setToolTip(text(tip))
        self.damage_progress.setToolTip(text(self._damage_tip))
        self.risk_gauge.marker_language = language
        self.risk_gauge.outcome_text = text("Probability of high-risk\njob")
        kind = assessment_kind(source) if source is not None else empty_kind
        self.individual_risk_title.setText(
            text(
                "Individual Shoulder"
                if kind is AssessmentKind.TST
                else "Individual DUET"
                if kind is AssessmentKind.DUET
                else "Individual LiFFT"
            )
        )
        if kind is AssessmentKind.DUET:
            self.risk_gauge.outcome_text = text(
                "Probability of distal upper\nextremity outcome"
            )
        if kind is AssessmentKind.TST:
            self.risk_gauge.outcome_text = text("Probability of shoulder\noutcome")
        self.risk_gauge.update()
        self.damage_value_label.setText("—")
        self.damage_value_label.setStyleSheet("")
        self.risk_severity_label.setText(
            "● " + ("No disp." if language is Language.SPANISH else "Not available")
        )
        self.risk_severity_label.setToolTip(text("Not available"))
        self.risk_severity_label.setStyleSheet("color: #6F7E88; font-weight: 700;")
        self.assessment_status_label.setText(text("Incomplete"))
        self.assessment_status_detail.setText(text("Enter context and task data."))
        summary = result.summary if result is not None else None
        if historical is None and not isinstance(
            summary, (LifftSummary, DuetSummary, TstSummary)
        ):
            self.risk_gauge.clear()
            self.damage_progress.clear()
        if isinstance(summary, (LifftSummary, DuetSummary, TstSummary)):
            display = (
                display_lifft_summary(summary)
                if isinstance(summary, LifftSummary)
                else display_duet_summary(summary)
                if isinstance(summary, DuetSummary)
                else display_tst_summary(summary)
            )
            color = QColor(display.color or "#D9E1E6")
            damage = summary.total_damage
            self.damage_progress.set_value(damage, color.name())
            self.damage_value_label.setText(
                ">2.0" if damage > 2 else f"{damage:.{self.precision.damage}f}"
            )
            luminance = (
                0.2126 * color.redF() + 0.7152 * color.greenF() + 0.0722 * color.blueF()
            )
            foreground = "#102A43" if luminance > 0.58 else "#FFFFFF"
            self.damage_value_label.setStyleSheet(
                f"color: {foreground}; background: {color.name()}; "
                f"border: 1px solid {color.darker(115).name()}; "
                "border-radius: 4px; padding: 7px 10px; font-size: 20px; "
                "font-weight: 700;"
            )
            if summary.probability is not None:
                percent = round(summary.probability * 100, 1)
                gauge_value = (
                    0.0
                    if percent < 5
                    else 100.0
                    if percent > 90
                    else summary.probability * 100
                )
                appearance = RISK_APPEARANCES[
                    classify_probability(
                        0.0 if percent < 5 else 100.0 if percent > 90 else percent
                    )
                ]
                self.risk_gauge.set_value(gauge_value, color.name())
                severity = appearance.english_label.removesuffix(" Risk")
                self.risk_severity_label.setText("● " + text(severity))
                self.risk_severity_label.setStyleSheet(
                    f"color: {appearance.color_hex}; font-weight: 700;"
                )
            else:
                self.risk_gauge.clear()
            complete = (
                result is not None
                and result.status is EvaluationStatus.COMPLETE
                and summary.probability is not None
            )
            self.assessment_status_label.setText(
                text("Ready" if complete else "Incomplete")
            )
            self.assessment_status_detail.setText(
                text(
                    "Assessment data is available."
                    if complete
                    else "Results include completed rows only."
                )
            )
        elif result is not None and result.status is EvaluationStatus.REVIEW_REQUIRED:
            self.assessment_status_label.setText(text("Review required"))
            self.assessment_status_detail.setText(text("Calculation requires review."))
        elif source is None:
            self.assessment_status_detail.setText(
                text("Select a context and enter task data.")
            )
        ready = (
            result is not None
            and result.status is EvaluationStatus.COMPLETE
            and isinstance(summary, (LifftSummary, DuetSummary, TstSummary))
            and summary.probability is not None
        )
        self.assessment_status_label.setProperty("ready", ready)
        style = self.assessment_status_label.style()
        assert style is not None
        style.unpolish(self.assessment_status_label)
        style.polish(self.assessment_status_label)
        tasks = source.tasks if source is not None else ()
        repetitions = [
            t.repetitions
            for t in tasks
            if t.repetitions is not None and t.repetitions > 0
        ]
        loads = (
            [t.load for t in source.tasks if t.load is not None]
            if isinstance(source, (LifftDraft, TstDraft))
            else []
        )
        moments = (
            [
                t.displayed_moment
                for t in result.task_results
                if isinstance(t, (LifftTaskResult, TstTaskResult))
            ]
            if isinstance(summary, (LifftSummary, DuetSummary, TstSummary))
            and result is not None
            else []
        )
        values = {
            "tasks": str(len(repetitions)),
            "repetitions": f"{sum(int(r) for r in repetitions):,}",
            "average_load": f"{sum(loads) / len(loads):.{precision.inputs}f}"
            if loads
            else "-",
            "max_moment": f"{max(moments):.{precision.moment}f}" if moments else "-",
        }
        for key, value in values.items():
            self.metric_labels[key].setText(value)
        if historical is not None:
            self.update_historical(historical, language)

    def update_historical(
        self, result: HistoricalAssessmentResult, language: Language
    ) -> None:
        """Display the matching saved result cache in existing cards.

        Display the matching saved result cache in existing cards without creating a
        fresh evaluation.

        Called from update_result without resetting an unchanged gauge target. No
        evaluator result, freshness flag or scientific approval is created by this
        display.

        Args:
            result: Matching saved result cache in recorded source units; not a second
                calculation or migration archive.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.

        Returns:
            None.
        """
        self.risk_gauge.marker_language = language
        text = partial(workspace_text, language=language)
        damage, percent = result.damage, result.probability_percent
        color_hex = historical_damage_color(result)
        if damage is None:
            self.damage_progress.clear()
        if percent is None:
            self.risk_gauge.clear()
        if damage is not None and color_hex is not None:
            color = QColor(color_hex)
            self.damage_value_label.setText(
                ">2.0" if damage > 2 else f"{damage:.{self.precision.damage}f}"
            )
            luminance = (
                0.2126 * color.redF() + 0.7152 * color.greenF() + 0.0722 * color.blueF()
            )
            foreground = "#102A43" if luminance > 0.58 else "#FFFFFF"
            self.damage_value_label.setStyleSheet(
                f"color: {foreground}; background: {color.name()}; "
                f"border: 1px solid {color.darker(115).name()}; "
                "border-radius: 4px; padding: 7px 10px; font-size: 20px; "
                "font-weight: 700;"
            )
            self.damage_progress.set_value(damage, color_hex)
        if percent is not None:
            appearance = RISK_APPEARANCES[classify_probability(percent)]
            bounded = round(percent, 1)
            bounded = 0.0 if bounded < 5 else 100.0 if bounded > 90 else percent
            self.risk_gauge.set_value(bounded, color_hex or appearance.color_hex)
            self.risk_severity_label.setText(
                "● " + text(appearance.english_label.removesuffix(" Risk"))
            )
            self.risk_severity_label.setStyleSheet(
                f"color: {appearance.color_hex}; font-weight: 700;"
            )
        self.assessment_status_label.setText(
            "Registrado" if language is Language.SPANISH else "Recorded"
        )
        self.assessment_status_detail.setText(
            "Resultado original guardado; no recalculado."
            if language is Language.SPANISH
            else "Original saved result; not recalculated."
        )
        if result.calculation_status is not None:
            self.assessment_status_label.setText(
                "Guardado" if language is Language.SPANISH else "Saved"
            )
            self.assessment_status_detail.setText(
                (
                    "Cálculo parcial guardado."
                    if language is Language.SPANISH
                    else "Saved partial calculation."
                )
                if result.calculation_status is EvaluationStatus.PARTIAL
                else (
                    "Cálculo guardado."
                    if language is Language.SPANISH
                    else "Saved calculation."
                )
            )
        moments = [task.moment for task in result.tasks if task.moment is not None]
        self.metric_labels["max_moment"].setText(
            f"{max(moments):.{self.precision.moment}f}" if moments else "-"
        )

"""Original PLOT summary figures with owned Matplotlib objects and localized text.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from enum import StrEnum

from matplotlib import colormaps
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Patch

from ergotools.application.plot_summaries import PlotSummary, ToolRiskGroup
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.risk import RiskBand, classify_probability
from ergotools.presentation.desktop.theme.duet_colors import duet_damage_color
from ergotools.presentation.desktop.theme.lifft_colors import lifft_damage_color
from ergotools.presentation.desktop.theme.tst_colors import tst_damage_color


class PlotChart(StrEnum):
    """Original three worker selections and the separate placed-job risk view."""

    # Group the worker chart by ergonomic tool.
    TOOL = "tool"
    # Group the worker chart by saved sex metadata.
    SEX = "sex"
    # Group the worker chart by the original age bands.
    AGE = "age"
    # Display the separate placed-job risk chart.
    JOB = "job"


def _text(english: str, spanish: str, language: Language) -> str:
    """Resolve this component's UI wording without translating saved user values.

    Args:
        english: English UI text; saved user values are never translated by this helper.
        spanish: Spanish UI text corresponding to the English caption.
        language: UI language only; does not reinterpret saved names, numeric inputs or
            units.

    Returns:
        Localized UI wording according to this component's catalog/fallback contract.
    """
    return spanish if language is Language.SPANISH else english


def _tool(kind: AssessmentKind) -> str:
    """Map the typed tool identity to its unchanged branded chart caption.

    Args:
        kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
            captions are not keys.

    Returns:
        Unchanged branded tool caption: LiFFT, DUET or ST.
    """
    return {
        AssessmentKind.LIFFT: "LiFFT",
        AssessmentKind.DUET: "DUET",
        AssessmentKind.TST: "ST",
    }[kind]


def _bars(
    axis: Axes,
    groups: tuple[ToolRiskGroup, ...],
    positions: tuple[float, ...],
    *,
    width: float,
    color: str | tuple[float, ...],
    label: str | None = None,
    alpha: float = 0.75,
) -> None:
    # Missing groups have no bar/error-bar; their tick/legend identity is retained.
    """Draw only groups with observed risk using saved percentage means.

    Draw only groups with observed risk using saved percentage means and
    population-standard-deviation error bars.

    Args:
        axis: Owned Matplotlib axes to draw into; no global pyplot state is used.
        groups: Saved grouped risk observations; absent evidence is not rendered as a
            zero bar.
        positions: Bar positions on the chart's categorical axis in group order.
        width: Dimensionless width in chart categorical-axis units.
        color: Original chart color name or normalized RGB(A) components.
        label: Visible label/legend caption; None omits an optional chart series label.
        alpha: Bar opacity from zero (transparent) to one (opaque).

    Returns:
        None.
    """
    observed = tuple(
        (position, group.risk)
        for position, group in zip(positions, groups, strict=True)
        if group.risk.mean_percent is not None
    )
    axis.bar(
        [p for p, _ in observed],
        [risk.mean_percent for _, risk in observed if risk.mean_percent is not None],
        width,
        yerr=[risk.deviation_percent for _, risk in observed],
        label=label,
        color=color,
        edgecolor="#111111",
        linewidth=0.8,
        alpha=alpha,
        capsize=3,
    )


def summary_figure(
    summary: PlotSummary,
    chart: PlotChart,
    *,
    language: Language = Language.ENGLISH,
    tool: AssessmentKind = AssessmentKind.LIFFT,
) -> Figure:
    """Create a source-sized figure without pyplot globals, I/O or Qt ownership.

    Chart values are percentages with one population standard deviation. Missing
    evidence draws no zero-risk bar. Source series colors, widths, axes, fonts and
    initial size are retained. The composed Qt host owns canvas, settings and viewer.

    Args:
        summary: Immutable aggregate saved-risk observations used to draw the selected
            chart.
        chart: Typed chart grouping/mode; does not change source assessments or filters.
        language: UI language only; does not reinterpret saved names, numeric inputs or
            units.
        tool: Selected ergonomic tool whose saved risk evidence is presented.

    Returns:
        Fresh owned source-sized figure; caller owns its Qt canvas/export lifetime.
    """
    figure = Figure(figsize=(3.1, 2.3), facecolor="white")
    axis = figure.add_subplot()
    no_subjects = (
        summary.jobs.placements == 0
        if chart is PlotChart.JOB
        else summary.workers.total == 0
    )
    if no_subjects:
        message = _text(
            "No jobs results match\nthe current filters."
            if chart is PlotChart.JOB
            else "No workers results match\nthe current filters.",
            "Ningún trabajo coincide\ncon los filtros actuales."
            if chart is PlotChart.JOB
            else "Ningún trabajador coincide\ncon los filtros actuales.",
            language,
        )
        axis.text(
            0.5, 0.5, message, ha="center", va="center", color="#526777", fontsize=9
        )
        axis.set_axis_off()
        figure.tight_layout(pad=0.6)
        return figure
    if chart is PlotChart.JOB:
        rows = tuple(row for row in summary.placed_jobs if row.risk_percent is not None)
        colors = tuple(
            "#D9E1E6"
            if row.damage is None
            else (
                lifft_damage_color(row.damage)
                if tool is AssessmentKind.LIFFT
                else duet_damage_color(row.damage)
                if tool is AssessmentKind.DUET
                else tst_damage_color(row.damage)
            )
            for row in rows
        )
        axis.barh(
            range(len(rows)),
            [row.risk_percent for row in rows if row.risk_percent is not None],
            color=colors,
            edgecolor="black",
            linewidth=0.8,
        )
        axis.set_yticks(list(range(len(rows))))
        axis.set_yticklabels(
            [f"{row.job_id} ({row.placement_count})" for row in rows], fontsize=6.5
        )
        axis.invert_yaxis()
        axis.set_xlim(0, 100)
        axis.set_xlabel(
            _text("Job risk (%)", "Riesgo del trabajo (%)", language),
            fontsize=8,
            fontweight="bold",
        )
        axis.set_title(
            _text("Job Risk by Placed Job", "Riesgo por trabajo ubicado", language),
            fontsize=9,
            fontweight="bold",
        )
        if not rows:
            _empty(
                axis,
                _text(
                    "No Job risk value for this tool",
                    "Sin valores actuales para esta herramienta",
                    language,
                ),
            )
    else:
        axis.set_ylim(0, 100)
        axis.set_ylabel(
            _text("Avg. Risk (%)", "Riesgo medio (%)", language),
            fontsize=8,
            fontweight="bold",
        )
        if chart is PlotChart.TOOL:
            colors_by_band = {
                RiskBand.LOW: "#19B83F",
                RiskBand.MODERATE: "#F5C400",
                RiskBand.MODERATE_HIGH: "#FF8A19",
                RiskBand.HIGH: "#FF3B30",
            }
            for index, group in enumerate(summary.tools):
                if group.risk.mean_percent is not None:
                    _bars(
                        axis,
                        (group,),
                        (float(index),),
                        width=0.5,
                        color=colors_by_band[
                            classify_probability(group.risk.mean_percent)
                        ],
                    )
            labels = [_tool(kind) for kind in AssessmentKind]
            axis.set_xlabel(
                _text("Tool Type", "Herramienta", language),
                fontsize=8,
                fontweight="bold",
            )
            title = _text(
                "Total Worker Risk Distribution by Tool",
                "Riesgo de trabajadores por herramienta",
                language,
            )
            available = any(group.risk.count for group in summary.tools)
        elif chart is PlotChart.SEX:
            for index, (sex, spanish) in enumerate(
                (("Male", "Hombre"), ("Female", "Mujer"))
            ):
                groups = tuple(group for group in summary.sexes if group.group == sex)
                _bars(
                    axis,
                    groups,
                    tuple(i + (-0.15 if index == 0 else 0.15) for i in range(3)),
                    width=0.3,
                    label=_text(sex, spanish, language),
                    color=colormaps["Set2"](index + 1),
                )
            labels = [_tool(kind) for kind in AssessmentKind]
            axis.set_xlabel(
                _text("Tool Type", "Herramienta", language),
                fontsize=8,
                fontweight="bold",
            )
            title = _text(
                "Worker Risk Distribution by Gender & Tool",
                "Riesgo por sexo y herramienta",
                language,
            )
            available = any(group.risk.count for group in summary.sexes)
            axis.legend(
                handles=[
                    Patch(
                        facecolor=colormaps["Set2"](index + 1),
                        edgecolor="#111111",
                        linewidth=0.8,
                        alpha=0.75,
                        label=_text(sex, spanish, language),
                    )
                    for index, (sex, spanish) in enumerate(
                        (("Male", "Hombre"), ("Female", "Mujer"))
                    )
                ],
                fontsize=7,
                loc="upper right",
                frameon=True,
            )
        else:
            labels = list(
                dict.fromkeys(
                    group.group for group in summary.ages if group.group is not None
                )
            )
            for index, kind in enumerate(AssessmentKind):
                groups = tuple(group for group in summary.ages if group.kind is kind)
                _bars(
                    axis,
                    groups,
                    tuple(i + (index - 1) * 0.25 for i in range(len(labels))),
                    width=0.25,
                    label=_tool(kind),
                    color=colormaps["Set2"](index),
                )
            axis.set_xlabel(
                _text("Age Range", "Rango de edad", language),
                fontsize=8,
                fontweight="bold",
            )
            title = _text(
                "Worker Risk Distribution by Age & Tool",
                "Riesgo por edad y herramienta",
                language,
            )
            available = any(group.risk.count for group in summary.ages)
            axis.legend(
                handles=[
                    Patch(
                        facecolor=colormaps["Set2"](index),
                        edgecolor="#111111",
                        linewidth=0.8,
                        alpha=0.75,
                        label=_tool(kind),
                    )
                    for index, kind in enumerate(AssessmentKind)
                ],
                fontsize=7,
                loc="upper right",
                frameon=True,
            )
        axis.set_xticks(list(range(len(labels))))
        axis.set_xticklabels(labels, fontsize=7)
        axis.set_title(title, fontsize=7, fontweight="bold")
        if not available:
            _empty(
                axis,
                _text(
                    "No available worker risk results",
                    "Sin resultados de riesgo disponibles",
                    language,
                ),
            )
    # Source default graph settings hide grid and use compact padding.
    axis.grid(False)
    figure.tight_layout(pad=0.6)
    return figure


def _empty(axis: Axes, message: str) -> None:
    """Draw a centered unavailable-data message in the owned chart axes.

    Draw a centered unavailable-data message in the owned chart axes without creating a
    zero-risk series.

    Args:
        axis: Owned Matplotlib axes to draw into; no global pyplot state is used.
        message: Literal user-facing notification/error content.

    Returns:
        None.
    """
    axis.text(
        0.5,
        0.5,
        message,
        ha="center",
        va="center",
        transform=axis.transAxes,
        fontsize=8,
        color="#526777",
        wrap=True,
    )

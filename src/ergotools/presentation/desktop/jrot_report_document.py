"""Localized, paginated JROT report content for Qt preview and PDF output.

Presentation adapter. HTML is escaped literal data, not a browser or executable
content. Qt's document engine repeats table headers and paginates long studies;
small studies follow the team's two-page supervisor/detail report structure.
"""

from collections.abc import Sequence
from html import escape
from statistics import pstdev

from PyQt5.QtGui import QColor, QFont, QTextDocument
from PyQt5.QtWidgets import QWidget

from ergotools.application.rotation_report import RotationReport, relative_index_change
from ergotools.domain.language import Language
from ergotools.domain.risk import RiskBand, classify_probability
from ergotools.domain.rotation import RotationSolveStatus, WorkerRotation
from ergotools.domain.rotation_scenario import complete_rotation_rows
from ergotools.presentation.desktop.jrot_result_table import tool_caption
from ergotools.presentation.desktop.table_presentation import table_text_color
from ergotools.presentation.desktop.theme.risk import RISK_APPEARANCES


class ReportContent:
    """Compose one report from immutable evidence and an explicit UI language."""

    def __init__(self, report: RotationReport, language: Language) -> None:
        """Retain report evidence without reading a repository or altering results.

        Args:
            report: Validated same-run snapshot.
            language: English/Spanish captions; user labels remain literal.

        Returns:
            None; creating content never accepts a solver preview.
        """
        self.report = report
        self.spanish = language is Language.SPANISH
        self.run = report.run
        self.targets = {t.key: t for t in self.run.inputs.targets}
        self.names = {c.target_key: c.job_name for c in self.run.coefficients}

    def text(self, english: str, spanish: str) -> str:
        """Choose owned captions without translating project or worker names.

        Args:
            english: English wording.
            spanish: Equivalent Spanish wording.

        Returns:
            Caption for the report language.
        """
        return spanish if self.spanish else english

    def number(self, value: float | None, *, signed: bool = False) -> str:
        """Format a display value while preserving absent evidence.

        Args:
            value: Finite index, difference or relative percent, or no value.
            signed: Include a plus sign for positive changes.

        Returns:
            Two display decimals or an em dash; stored values remain unrounded.
        """
        if value is None:
            return "—"
        return f"{value:+.2f}" if signed else f"{value:.2f}"

    def score(self, value: float | None) -> str:
        """Color an index using existing application bands and contrast policy.

        Args:
            value: Worker statistic or Job probability in percentage points.

        Returns:
            Escaped display text inside a colored inline table cell.
        """
        if value is None:
            return "—"
        color = RISK_APPEARANCES[classify_probability(value)].color_hex
        ink = table_text_color(QColor(color)).name()
        return (
            f'<span style="background-color:{color};color:{ink};">'
            f"&nbsp;<b>{self.number(value)}</b>&nbsp;</span>"
        )

    def table(self, headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
        """Build a repeatable-header table from already escaped cell fragments.

        Args:
            headers: Trusted caption fragments, optionally with line breaks.
            rows: Escaped literal data or owned formatted score fragments.

        Returns:
            Qt-supported table HTML with light borders and alternate row fills.
        """
        head = "".join(f"<th>{h}</th>" for h in headers)
        body = "".join(
            '<tr bgcolor="'
            + ("#FFFFFF" if i % 2 == 0 else "#F1F6F8")
            + '">'
            + "".join(f'<td align="center" valign="middle">{v}</td>' for v in row)
            + "</tr>"
            for i, row in enumerate(rows)
        )
        return (
            '<table width="100%" cellspacing="0" cellpadding="3" border="1" '
            'style="border-color:#CCD9E2;"><thead><tr bgcolor="#E6F0F5">'
            + head
            + "</tr></thead>"
            + body
            + "</table>"
        )

    def target(self, key: str) -> str:
        """Keep placement-specific targets distinguishable in every matrix.

        Args:
            key: Exact target identity from the frozen run.

        Returns:
            Escaped Job ID and optional placement number, never an invented Station.
        """
        t = self.targets[key]
        return escape(t.job_id + (f" / #{t.placement_id}" if t.placement_id else ""))

    def clock(self, offset: int) -> str:
        """Format a local clock without losing overnight day offsets.

        Args:
            offset: Relative minute offset from the recorded rotation origin.

        Returns:
            24-hour clock with an explicit next-day suffix when applicable.
        """
        minute = (self.run.inputs.start_minute or 0) + offset
        return f"{minute // 60 % 24:02}:{minute % 60:02}" + (
            f" (+{minute // 1440})" if minute >= 1440 else ""
        )

    def schedule(self, rows: tuple[WorkerRotation, ...] | None) -> str:
        """Render complete matrices in readable block bands for larger horizons.

        Args:
            rows: Recorded starting or result arrangement; None stays absent.

        Returns:
            One or more tables; no default assignments or missing scores are invented.
        """
        if rows is None:
            return (
                "<p>"
                + self.text(
                    "No starting schedule was entered; before values are unavailable.",
                    "No hay horario inicial; no se dispone de valores previos.",
                )
                + "</p>"
            )
        timing = self.run.inputs.timing
        assert timing is not None
        blocks = timing.blocks()
        result = []
        for start in range(0, len(blocks), 4):
            indices = range(start, min(start + 4, len(blocks)))
            headers = [self.text("Worker", "Trabajador")]
            headers.extend(
                self.text("Block ", "Bloque ")
                + str(i + 1)
                + f"<br>{timing.block_minutes[i]} min<br>"
                + "<br>".join(
                    self.clock(p.start) + "-" + self.clock(p.end)
                    for p in blocks[i].pieces
                )
                for i in indices
            )
            body = [
                [escape(label), *(self.target(row.target_keys[i]) for i in indices)]
                for label, row in zip(self.run.worker_labels, rows, strict=True)
            ]
            result.append(self.table(headers, body))
        return "<br>".join(result)

    def html(self) -> str:
        """Compose supervisor overview followed by professional comparison details.

        Args:
            None.

        Returns:
            Complete escaped HTML; long tables may extend beyond two PDF pages.
        """
        r, run = self.report, self.run
        timing = run.inputs.timing
        assert timing is not None
        line = run.inputs.line
        location = (
            " / ".join((line.plant_name, line.section_name, line.line_name))
            if line
            else self.text("All Jobs", "Todos los trabajos")
        )
        state = (
            self.text(
                "PREVIEW · result not kept", "VISTA PREVIA · resultado no conservado"
            )
            if r.preview
            else self.text(
                "Retained optimization result", "Resultado optimizado conservado"
            )
        )
        if not r.current:
            state += self.text(
                " · STALE: recorded inputs differ from current data",
                " · SIN VIGENCIA: los datos guardados difieren de los actuales",
            )
        state_color = "#8A4000" if r.preview or not r.current else "#0B3D60"
        state_html = f'<b style="color:{state_color};">' + escape(state) + "</b>"
        before = (
            run.inputs.baseline
            if run.inputs.baseline is not None
            else run.inputs.proposed
        )
        start_title = (
            self.text("Current rotation", "Rotación actual")
            if run.inputs.baseline is not None
            else self.text("Starting proposal", "Propuesta inicial")
        )
        sections = [
            "<h1>JROT | "
            + self.text("Rotation report", "Informe de rotación")
            + "</h1>",
            "<p><b>"
            + escape(r.project_title)
            + " · "
            + escape(r.rotation_name)
            + "</b><br>"
            + escape(location)
            + " · "
            + self.text("Shift ", "Turno ")
            + escape(run.inputs.shift_id or "—")
            + " · "
            + str(run.inputs.planned_date)
            + "<br>"
            + state_html
            + "</p>",
            "<p>"
            + f"{len(run.inputs.workers)} "
            + self.text("workers", "trabajadores")
            + " · "
            + f"{len(run.inputs.targets)} "
            + self.text("Job positions", "posiciones de trabajo")
            + " · "
            + f"{len(timing.block_minutes)} "
            + self.text("work blocks", "bloques de trabajo")
            + f" · {timing.productive_minutes} min "
            + self.text("work", "trabajo")
            + f" · {(timing.shift_minutes - timing.productive_minutes)} min "
            + self.text("breaks", "pausas")
            + f" · {timing.averaging_minutes} min "
            + self.text("index basis", "base del índice")
            + "</p>",
            "<h2>01 "
            + self.text("Current / suggested schedules", "Horarios actual / sugerido")
            + "</h2>",
        ]
        first = self.schedule(
            complete_rotation_rows(before) if before is not None else None
        )
        after = self.schedule(run.arrangement)
        # Portrait pages use full-width matrices, preserving readable clock/name text.
        suggested_heading = (
            '<h3 style="page-break-before:always;">'
            if len(run.inputs.workers) > 6 or len(timing.block_minutes) > 4
            else "<h3>"
        )
        sections.extend(
            [
                "<h3>" + start_title + "</h3>",
                first,
                suggested_heading
                + self.text("Suggested rotation", "Rotación sugerida")
                + "</h3>",
                after,
            ]
        )
        sections.append(
            "<p>"
            + " · ".join(
                self.target(t.key) + ": " + escape(self.names[t.key])
                for t in run.inputs.targets
            )
            + "</p>"
        )
        sections.extend(
            [
                "<h2>02 "
                + self.text("Key results", "Resultados principales")
                + "</h2>",
                self.key_results(),
                "<h2>03 " + self.text("Recommendation", "Recomendación") + "</h2>",
                self.recommendation(),
            ]
        )
        sections.extend(
            [
                '<h1 style="page-break-before:always;">JROT | '
                + self.text("Comparison and detail", "Comparación y detalle")
                + "</h1>",
                "<p><b>" + escape(r.rotation_name) + "</b> · " + state_html + "</p>",
                "<h2>04 "
                + self.text("Statistical comparison", "Comparación estadística")
                + "</h2>",
                self.statistics(),
                "<h2>05 "
                + self.text("Worker-level comparison", "Comparación por trabajador")
                + "</h2>",
                self.workers(),
                "<h2>06 "
                + self.text(
                    "Warnings and recommendations", "Advertencias y recomendaciones"
                )
                + "</h2>",
                self.warnings(),
            ]
        )
        sections.append(
            "<p>"
            + self.text(
                (
                    "Scores are time-weighted Job-risk indices, not individual injury"
                    " probabilities. Changes are After minus Before in percentage "
                    "points (p.p.). Relative changes divide that difference by "
                    "Before; a zero starting value has no relative percentage. SD is "
                    "population standard deviation. Rotation changes assignments, not"
                    " intrinsic Job hazards; breaks imply no physiological recovery."
                ),
                (
                    "Los valores son índices de riesgo ponderados por tiempo, no "
                    "probabilidades individuales de lesión. Los cambios son Después "
                    "menos Antes en puntos porcentuales (p.p.). El cambio relativo "
                    "divide esa diferencia por Antes; una base cero no tiene "
                    "porcentaje relativo. DE es la desviación estándar poblacional. "
                    "La rotación cambia asignaciones, no los peligros del trabajo; "
                    "las pausas no implican recuperación fisiológica."
                ),
            )
            + "</p>"
        )
        status = (
            self.text(
                "Feasible candidate; optimality not proved",
                "Propuesta factible; optimalidad no demostrada",
            )
            if RotationSolveStatus.FEASIBLE in run.stages
            else self.text(
                "Optimal under configured gap and tolerances",
                "Óptimo con la brecha y tolerancias configuradas",
            )
        )
        sections.append(
            "<p>"
            + escape(status)
            + " · "
            + self.text("Calculated ", "Calculado ")
            + run.completed_at.strftime("%Y-%m-%d %H:%M UTC")
            + "</p>"
        )
        return (
            (
                "<html><head><style>body "
                "{font-family:Arial;font-size:11pt;color:#151B20;} h1 "
                "{font-size:19pt;color:#0B3D60;margin-bottom:8px;} h2 "
                "{font-size:13pt;color:#0B3D60;margin-top:12px;margin-bottom:6px;}"
                " h3 {font-size:11pt;color:#0B3D60;} p "
                "{margin-top:5px;margin-bottom:7px;text-align:justify;} "
                "td,th {font-size:10pt;} th "
                "{color:#0B3D60;} </style></head><body>"
            )
            + "".join(sections)
            + "</body></html>"
        )

    def key_results(self) -> str:
        """Compare worker means/maxima and distinguish point versus relative changes.

        Args:
            None.

        Returns:
            Summary table with explicit absent-before and zero-denominator handling.
        """
        rows = []
        for c in self.report.comparisons:
            b = c.before
            delta = c.after.worst - b.worst if b else None
            relative = relative_index_change(b.worst, c.after.worst) if b else None
            rows.append(
                [
                    tool_caption(c.kind.value),
                    self.score(b.mean if b else None)
                    + " → "
                    + self.score(c.after.mean),
                    self.score(b.worst if b else None)
                    + " → "
                    + self.score(c.after.worst),
                    self.number(delta, signed=True)
                    + " p.p.<br>"
                    + (
                        self.number(relative, signed=True) + "%"
                        if relative is not None
                        else "—"
                    ),
                ]
            )
        return self.table(
            [
                self.text("Tool", "Herramienta"),
                self.text(
                    "Mean worker index<br>Before → After",
                    "Índice medio<br>Antes → Después",
                ),
                self.text(
                    "Maximum worker index<br>Before → After",
                    "Índice máximo<br>Antes → Después",
                ),
                self.text(
                    "Maximum change<br>points / relative %",
                    "Cambio del máximo<br>puntos / % relativo",
                ),
            ],
            rows,
        )

    def statistics(self) -> str:
        """Reuse unrounded same-context distributions for population statistics.

        Args:
            None.

        Returns:
            Per-tool mean, maximum, population SD and range before/after table.
        """
        rows = []
        for c in self.report.comparisons:
            b, a = c.before, c.after
            rows.append(
                [
                    tool_caption(c.kind.value),
                    self.score(b.mean if b else None) + " → " + self.score(a.mean),
                    self.score(b.worst if b else None) + " → " + self.score(a.worst),
                    self.number(pstdev(b.values) if b else None)
                    + " → "
                    + self.number(pstdev(a.values)),
                    self.number(b.spread if b else None)
                    + " → "
                    + self.number(a.spread),
                ]
            )
        return self.table(
            [
                self.text("Tool", "Herramienta"),
                self.text("Mean", "Media"),
                self.text("Maximum", "Máximo"),
                self.text("Population SD", "DE poblacional"),
                self.text("Range", "Rango"),
            ],
            rows,
        )

    def workers(self) -> str:
        """Show increases as well as decreases for every analyzed tool and worker.

        Args:
            None.

        Returns:
            Worker-order comparison table and per-row review notes.
        """
        rows = []
        for i, label in enumerate(self.run.worker_labels):
            values, increases = [], []
            for c in self.report.comparisons:
                before = c.before.values[i] if c.before else None
                after = c.after.values[i]
                change = after - before if before is not None else None
                values.append(
                    self.score(before)
                    + " → "
                    + self.score(after)
                    + "<br>("
                    + self.number(change, signed=True)
                    + " p.p.)"
                )
                if change is not None and change > 1e-8:
                    increases.append(tool_caption(c.kind.value))
            note = (
                self.text("Increases: ", "Aumenta: ") + ", ".join(increases)
                if increases
                else "—"
            )
            rows.append([escape(label), *values, note])
        return self.table(
            [
                self.text("Worker", "Trabajador"),
                *(tool_caption(c.kind.value) for c in self.report.comparisons),
                self.text("Review note", "Nota de revisión"),
            ],
            rows,
        )

    def recommendation(self) -> str:
        """Interpret actual improvements without promising benefits for every worker.

        Args:
            None.

        Returns:
            Concise conditional interpretation and monitoring advice.
        """
        improved = [
            tool_caption(c.kind.value)
            for c in self.report.comparisons
            if c.before and c.after.spread < c.before.spread - 1e-8
        ]
        message = (
            self.text(
                "Exposure indices are more evenly distributed for: ",
                "Los índices se distribuyen más uniformemente para: ",
            )
            + ", ".join(improved)
            + "."
            if improved
            else self.text(
                (
                    "Review the maximum, spread and individual worker changes "
                    "together; improved balance is not guaranteed for every study."
                ),
                (
                    "Revise el máximo, la variabilidad y los cambios individuales "
                    "juntos; no se garantiza mejor equilibrio en cada estudio."
                ),
            )
        )
        return (
            "<p>"
            + message
            + " "
            + self.text(
                (
                    "Rotation redistributes work; it does not remove Job hazards. "
                    "Review remaining High Jobs, monitor worker feedback and reassess"
                    " when conditions change."
                ),
                (
                    "La rotación redistribuye el trabajo; no elimina sus peligros. "
                    "Revise los trabajos de riesgo alto, escuche a los trabajadores y"
                    " reevalúe cuando cambien las condiciones."
                ),
            )
            + "</p>"
        )

    def warnings(self) -> str:
        """Identify intrinsic High Jobs from the selected frozen coefficients.

        Args:
            None.

        Returns:
            Job/tool warnings or a no-High notice, followed by practical advice.
        """
        rows = []
        for c in self.run.coefficients:
            value = c.measurement.probability_percent
            if value is not None and classify_probability(value) is RiskBand.HIGH:
                rows.append(
                    [
                        self.target(c.target_key) + " · " + escape(c.job_name),
                        tool_caption(c.measurement.kind.value),
                        self.score(value),
                    ]
                )
        table = (
            self.table(
                [
                    self.text("High-risk Job", "Trabajo de riesgo alto"),
                    self.text("Tool", "Herramienta"),
                    self.text("Recorded probability (%)", "Probabilidad guardada (%)"),
                ],
                rows,
            )
            if rows
            else "<p>"
            + self.text(
                "No selected Job exceeds the High threshold in the analyzed tools.",
                (
                    "Ningún trabajo seleccionado supera el umbral alto actual en las "
                    "herramientas analizadas."
                ),
            )
            + "</p>"
        )
        timing = self.run.inputs.timing
        assert timing is not None
        breaks = "; ".join(
            escape(b.name or self.text("Break", "Pausa"))
            + ": "
            + self.clock(b.interval.start)
            + "-"
            + self.clock(b.interval.end)
            for b in timing.breaks
        )
        return (
            table
            + "<p>"
            + self.text(
                (
                    "High means above 50% in a selected tool. Consider reducing "
                    "repetition, force, load or awkward postures at the identified "
                    "Jobs. No compliance certification is implied."
                ),
                (
                    "Alto significa más de 50% en una herramienta seleccionada. "
                    "Considere reducir repetición, fuerza, carga o posturas forzadas "
                    "en los trabajos indicados. No se certifica cumplimiento "
                    "normativo."
                ),
            )
            + "</p>"
            + (
                "<p>" + self.text("Breaks: ", "Pausas: ") + breaks + "</p>"
                if breaks
                else ""
            )
        )


def report_document(
    report: RotationReport, language: Language, parent: QWidget | None = None
) -> QTextDocument:
    """Create a Qt document used unchanged for preview and PDF publication.

    Args:
        report: Immutable validated report snapshot.
        language: Caption language; names and numeric values stay literal.
        parent: Optional QObject owner for deterministic dialog lifetime.

    Returns:
        Unpaginated document; Qt print support fits its actual target page dimensions.
    """
    document = QTextDocument(parent)
    document.setDefaultFont(QFont("Arial", 11))
    document.setDocumentMargin(0)
    document.setHtml(ReportContent(report, language).html())
    document.setMetaInformation(
        QTextDocument.MetaInformation.DocumentTitle, "JROT - " + report.rotation_name
    )
    return document

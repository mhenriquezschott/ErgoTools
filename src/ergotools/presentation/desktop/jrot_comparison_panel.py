"""Guided retained-run comparisons over immutable optimization evidence.

Presentation layer. Reads frozen previews or retained evidence; no solver or catalog
writer. Keep/rework intent stays with the guided owner and shared history.
"""

from dataclasses import replace
from statistics import pstdev
from typing import TYPE_CHECKING

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.rotation_scenarios import run_is_current
from ergotools.domain.risk import classify_probability
from ergotools.domain.rotation import RotationSolveStatus
from ergotools.domain.rotation_comparison import ToolComparison, compare_rotation_run
from ergotools.domain.rotation_scenario import ROTATION_RUN_MODEL_VERSION, RotationRun
from ergotools.presentation.desktop.assessment_tool_tabs import (
    AssessmentResultTabs,
    assessment_tool_icon,
)
from ergotools.presentation.desktop.jrot_result_table import (
    JrotResultTable,
    tool_caption,
)
from ergotools.presentation.desktop.jrot_table_style import style_rotation_table
from ergotools.presentation.desktop.table_presentation import (
    AdaptiveTableWidget,
    table_text_color,
)
from ergotools.presentation.desktop.theme.risk import RISK_APPEARANCES
from ergotools.presentation.desktop.workflow_action_style import (
    stacked_action,
)

if TYPE_CHECKING:
    from ergotools.presentation.desktop.jrot_dialog import JrotDialog


class JrotComparisonPanel(QWidget):
    """Frozen before/after cards, tool statistics and optional schedule details."""

    def __init__(self, root: "JrotDialog") -> None:
        """Compose read-only comparisons and explicit Keep/rework actions.

        Args:
            root: Borrowed guided project and history lifetime owner.

        Returns:
            None; opening never creates a run or changes Job measurements.
        """
        super().__init__()
        self.root = root
        self.signature: tuple[object, ...] = ()
        self.run: RotationRun | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.notice = QLabel()
        self.notice.setWordWrap(True)
        layout.addWidget(self.notice)
        self.cards = QWidget()
        self.cards.setObjectName("rotationResultCards")
        self.cards.setStyleSheet(
            "QWidget#rotationResultCards {background:#F4F7F9;border:0;} "
            "QGroupBox#rotationToolResult {background:white;border:1px solid "
            "#BCC9D3;border-radius:7px;margin-top:0;padding-top:0;} "
            "QGroupBox#rotationToolResult::title {color:#0B326C;font-"
            "weight:bold;}"
        )
        self.cards_layout = QHBoxLayout(self.cards)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(14)
        layout.addWidget(self.cards)
        self.high_notice = QLabel()
        self.high_notice.setWordWrap(True)
        self.high_notice_group = QGroupBox(
            root.text("High Risk Notice", "Aviso de riesgo alto")
        )
        self.high_notice_group.setMinimumWidth(260)
        self.high_notice_group.setMaximumWidth(330)
        high_layout = QVBoxLayout(self.high_notice_group)
        high_layout.addWidget(self.high_notice)
        body = QHBoxLayout()
        self.tabs = AssessmentResultTabs()
        self.tabs.setIconSize(QSize(24, 24))
        body.addWidget(self.tabs, 1)
        body.addWidget(self.high_notice_group, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(body, 1)
        actions = QHBoxLayout()
        self.keep_button = stacked_action(
            root.text("Keep optimization result", "Conservar resultado optimizado"),
            root.solve.keep_result,
            root.icons["keep_optimization_result"],
        )
        self.keep_button.setIcon(root.icons.get("keep_optimization_result", QIcon()))
        self.keep_button.setToolTip(
            root.text(
                "Keep this preview as the result. The original baseline stays "
                "unchanged; Main Save writes the project.",
                "Conservar esta vista como resultado. La base original queda "
                "intacta; Guardar escribe el proyecto.",
            )
        )
        self.keep_button.hide()
        actions.addWidget(self.keep_button)
        self.rework_button = stacked_action(
            root.text("Create rotation from result…", "Crear rotación con resultado…"),
            lambda: root.rework_run(False),
            root.icons["rework_rotation"],
        )
        self.rework_button.setIcon(root.icons.get("rework_rotation", QIcon()))
        self.rework_button.setToolTip(
            root.text(
                "Create a separate rotation using this result as its starting "
                "schedule. This rotation and its original baseline are kept.",
                "Crear otra rotación usando este resultado como horario "
                "inicial. Esta rotación y su base original se conservan.",
            )
        )
        self.replace_button = stacked_action(
            root.text("Replace original baseline…", "Reemplazar base original…"),
            lambda: root.rework_run(True),
            root.icons["replace_baseline"],
        )
        self.replace_button.setIcon(root.icons.get("replace_baseline", QIcon()))
        self.replace_button.setToolTip(
            root.text(
                "Only this action replaces the original baseline, after "
                "confirmation. Running or keeping an optimization never "
                "changes it.",
                "Solo esta acción reemplaza la base original, con "
                "confirmación. Optimizar o conservar un resultado no la "
                "cambia.",
            )
        )
        self.report_button = stacked_action(
            root.text("Save report", "Guardar informe"),
            lambda: None,
            root.icons["export"],
        )
        self.report_button.setIcon(root.icons["export"])
        self.report_button.setEnabled(False)
        self.report_button.setToolTip(
            root.text(
                "Report contents and export formats await the team's specification.",
                "El contenido y formato del informe esperan la "
                "especificación del equipo.",
            )
        )
        for button in (
            self.rework_button,
            self.replace_button,
            self.report_button,
        ):
            actions.addWidget(button)
        actions.addStretch(1)
        layout.addLayout(actions)
        note = QLabel(
            root.text(
                "Worker values are time-weighted Job-risk indices. "
                "Negative change means "
                "a lower index, not an individual injury-probability reduction. Fully "
                "staffed schedules keep the same population mean for "
                "the frozen context.",
                "Los valores son índices de riesgo ponderados por tiempo. Un cambio "
                "negativo indica un índice menor, no una reducción de probabilidad "
                "individual. La media poblacional permanece igual en este contexto.",
            )
        )
        note.setWordWrap(True)
        layout.addWidget(note)

    def refresh(self) -> None:
        """Choose a fresh preview or retained run without mixing current source values.

        Args:
            None.

        Returns:
            None; stale and unsupported evidence remains explicitly read-only.
        """
        owner = self.root
        if owner.workspace.editing is not owner.owner:
            self.clear_tabs()
            self.run = None
            self.signature = ()
            for button in (
                self.rework_button,
                self.replace_button,
            ):
                button.setEnabled(False)
            self.notice.setText(
                owner.text(
                    "The project changed. Close and reopen this window.",
                    "El proyecto cambió. Cierre y vuelva a abrir esta ventana.",
                )
            )
            return
        record = owner.scenario
        preview = bool(
            owner.solve.preview is not None
            and owner.solve.run is not None
            and owner.solve.fresh()
        )
        run = owner.solve.run if preview else record.run if record else None
        self.keep_button.setVisible(preview)
        self.keep_button.setEnabled(preview and not owner.planning_busy())
        current = False
        if record is not None and run is not None:
            w = owner.workspace
            current = run_is_current(
                replace(record, run=run) if preview else record,
                w.read_hierarchy().hierarchy,
                w.read_jobs().jobs,
                w.read_job_risk().risk,
                owner.repository.load_rotation_scenarios(),
            )
        rework = bool(
            record
            and record.run
            and record.run.contract_version == ROTATION_RUN_MODEL_VERSION
            and not owner.planning_busy()
            and owner.solve.preview is None
        )
        self.rework_button.setEnabled(rework)
        self.replace_button.setEnabled(rework)
        signature = (record.scenario_id if record else None, run, preview, current)
        if signature == self.signature:
            return
        self.signature, self.run = signature, run
        self.clear_tabs()
        if run is None:
            self.notice.setText(
                owner.text(
                    "No optimized result yet. Generate or enter a starting proposal if "
                    "needed, then run optimization. No before/after "
                    "values are invented.",
                    "Todavía no hay resultado optimizado. Genere o "
                    "ingrese una propuesta "
                    "si hace falta y luego optimice. No se inventan "
                    "valores comparativos.",
                )
            )
            return
        state = (
            owner.text(
                "Preview · not kept yet · original baseline unchanged",
                "Vista previa · aún no conservada · base original intacta",
            )
            if preview
            else owner.text(
                "Retained optimization · original baseline is separate",
                "Optimización conservada · la base original es independiente",
            )
        )
        if not current:
            state += owner.text(
                " · STALE relative to current inputs or sources; "
                "showing recorded values",
                " · SIN VIGENCIA respecto a datos actuales; se "
                "muestran valores guardados",
            )
        analyzed = ", ".join(tool_caption(k.value) for k in run.inputs.tools)
        self.notice.setText(
            state
            + self.root.text(" · Optimized using: ", " · Optimizado con: ")
            + analyzed
            + " · "
            + run.completed_at.strftime("%Y-%m-%d %H:%M UTC")
        )
        line = run.inputs.line
        scope = (
            " / ".join((line.plant_name, line.section_name, line.line_name))
            if line
            else "—"
        )
        timing = run.inputs.timing
        basis = str(timing.averaging_minutes) if timing else "—"
        self.notice.setText(
            self.notice.text()
            + "\n"
            + self.root.text("Analysis setup: ", "Configuración analizada: ")
            + (
                self.root.text("Workplace", "Lugar de trabajo")
                if run.inputs.scope
                else self.root.text("All Jobs", "Todos los trabajos")
            )
            + " · "
            + scope
            + self.root.text(" · Shift ", " · Turno ")
            + (run.inputs.shift_id or "—")
            + self.root.text(" · Index basis: ", " · Base del índice: ")
            + basis
            + " min"
        )
        status = (
            self.root.text(
                "Feasible candidate; optimality not proved",
                "Propuesta factible; optimalidad no demostrada",
            )
            if RotationSolveStatus.FEASIBLE in run.stages
            else self.root.text(
                "Solver reports optimal under configured gap/tolerances",
                "Óptimo reportado con la brecha/tolerancias configuradas",
            )
        )
        self.notice.setText(self.notice.text() + " · " + status)
        self.notice.setToolTip(
            run.backend.value.upper()
            + " · "
            + ", ".join(
                f"Stage {i + 1}: {status.value}" for i, status in enumerate(run.stages)
            )
            + "\n"
            + str(dict(run.settings))
            + "\n"
            + run.completed_at.isoformat()
        )

        try:
            comparisons = compare_rotation_run(run)
        except ValueError as error:
            self.notice.setText(self.notice.text() + "\n" + str(error))
            # Unknown models retain exact matrices but receive no recalculated index.
            for kind in run.inputs.tools:
                self.tabs.addTab(
                    self.schedule(run, kind.value, None),
                    assessment_tool_icon(owner.icons, kind),
                    tool_caption(kind.value),
                )
            return
        self.show_cards(run, comparisons)
        for comparison in comparisons:
            self.tabs.addTab(
                self.tool_page(run, comparison),
                assessment_tool_icon(owner.icons, comparison.kind),
                tool_caption(comparison.kind.value),
            )

    def clear_tabs(self) -> None:
        """Release replaced read-only tables and summary cards.

        Args:
            None.

        Returns:
            None; data stays unchanged and obsolete widgets are scheduled for deletion.
        """
        self.high_notice.clear()
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        while self.tabs.count():
            widget = self.tabs.widget(0)
            self.tabs.removeTab(0)
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

    def schedule(
        self,
        run: RotationRun,
        kind: str,
        scores: tuple[float, ...] | None,
        *,
        before: bool = False,
    ) -> QWidget:
        """Build one frozen starting/result matrix or an explicit missing-state label.

        Args:
            run: Immutable labels, timeline and coefficients.
            kind: Analyzed tool value.
            scores: Independently evaluated indices, or None for unsupported models.
            before: True selects the saved baseline or proposal.

        Returns:
            Read-only matrix, or a missing-starting-schedule notice.
        """
        from ergotools.domain.rotation_scenario import complete_rotation_rows

        rows = (
            run.inputs.baseline
            if run.inputs.baseline is not None
            else run.inputs.proposed
        )
        if not before:
            rows = run.arrangement
        if rows is None:
            label = QLabel(
                self.root.text(
                    "No observed baseline or starting proposal was entered.",
                    "No se ingresó una base observada ni propuesta inicial.",
                )
            )
            label.setWordWrap(True)
            label.setStyleSheet("font-size:12px;font-weight:normal;color:#304652;")
            return label
        return JrotResultTable(
            run.inputs,
            complete_rotation_rows(rows),
            {c.target_key: c.job_name for c in run.coefficients},
            run.worker_labels,
            {
                c.target_key: c.measurement.probability_percent
                for c in run.coefficients
                if c.measurement.kind.value == kind
                and c.measurement.probability_percent is not None
            },
            scores,
            self.root.language,
            compact=True,
        )

    def show_cards(
        self, run: RotationRun, comparisons: tuple[ToolComparison, ...]
    ) -> None:
        """Show maximum worker indices and intrinsic High Jobs from frozen evidence.

        Args:
            run: Exact retained optimization; no current catalog values are used.
            comparisons: Same-solution tool distributions.

        Returns:
            None; absent baselines remain absent and risk colors use existing bands.
        """
        for comparison in comparisons:
            names = {
                "lifft": self.root.text("Low back", "Zona lumbar"),
                "duet": self.root.text("Hand / wrist", "Mano / muñeca"),
                "tst": self.root.text("Shoulder", "Hombro"),
            }
            group = QGroupBox(
                tool_caption(comparison.kind.value)
                + " · "
                + names[comparison.kind.value]
            )
            group.setObjectName("rotationToolResult")
            font = group.font()
            font.setBold(True)
            font.setPointSize(12)
            group.setFont(font)
            title = group.title()
            group.setTitle("")
            box = QVBoxLayout(group)
            heading = QHBoxLayout()
            icon = QLabel()
            icon.setPixmap(
                assessment_tool_icon(self.root.icons, comparison.kind).pixmap(26, 26)
            )
            heading.addWidget(icon)
            tool_label = QLabel(title)
            tool_label.setStyleSheet("font-size:16px;font-weight:bold;color:#0B326C;")
            heading.addWidget(tool_label, 1)
            box.addLayout(heading)
            label = QLabel(
                self.root.text(
                    "Maximum worker schedule average", "Máximo promedio por trabajador"
                )
            )
            label.setWordWrap(True)
            label.setStyleSheet("font-size:12px;font-weight:normal;color:#304652;")
            box.addWidget(label)
            values = QHBoxLayout()
            for position, (caption, summary) in enumerate(
                (
                    (self.root.text("Before", "Antes"), comparison.before),
                    (self.root.text("After", "Después"), comparison.after),
                )
            ):
                if position:
                    arrow = QLabel()
                    arrow.setPixmap(self.root.icons["next"].pixmap(24, 24))
                    arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    arrow.setStyleSheet("background:transparent;")
                    values.addWidget(arrow)
                value = QLabel(
                    caption + "\n" + (f"{summary.worst:.2f}%" if summary else "—")
                )
                value.setAlignment(Qt.AlignmentFlag.AlignCenter)
                color = (
                    RISK_APPEARANCES[classify_probability(summary.worst)].color_hex
                    if summary
                    else "#EAF1F5"
                )
                value.setStyleSheet(
                    f"background:{color};color:{table_text_color(QColor(color)).name()};padding:9px;border-radius:4px;font-weight:bold;font-size:14px;"
                )
                values.addWidget(value, 1)
            box.addLayout(values)
            self.cards_layout.addWidget(group, 1)
        high = tuple(
            dict.fromkeys(
                c.job_name
                for c in run.coefficients
                if c.measurement.probability_percent is not None
                and classify_probability(c.measurement.probability_percent).value
                == "high"
            )
        )
        # Classification is the shared existing threshold policy, not a new cutoff.
        if high:
            self.high_notice.setText(
                self.root.text("High-risk Jobs: ", "Trabajos de alto riesgo: ")
                + ", ".join(high)
                + self.root.text(
                    ". These Jobs remain above the current High threshold in "
                    "at least one analyzed tool. Review task design and "
                    "engineering controls; rotation alone does not reduce "
                    "intrinsic Job risk.",
                    ". Superan el límite alto en alguna herramienta analizada."
                    " Revise el diseño de tareas y controles de ingeniería; "
                    "rotar no reduce el riesgo intrínseco.",
                )
            )
            self.high_notice.setStyleSheet(
                "color:#A52C23;background:#FFF0ED;padding:6px;"
            )
        else:
            self.high_notice.setText(
                self.root.text(
                    "No High-risk Jobs in the analyzed tool values.",
                    "Sin trabajos de alto riesgo en los valores analizados.",
                )
            )
            self.high_notice.setStyleSheet("")

    def tool_page(self, run: RotationRun, comparison: ToolComparison) -> QWidget:
        """Present summary statistics with optional schedule and worker detail tabs.

        Args:
            run: Immutable solved context shared by all tools.
            comparison: Exact same-context distributions.

        Returns:
            Owned read-only page; reviewing details never runs the optimizer.
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        table = AdaptiveTableWidget()
        table.setRowCount(4)
        table.setColumnCount(4)
        table.setObjectName("comparisonStatistics")
        style_rotation_table(table)
        table.setHorizontalHeaderLabels(
            [
                self.root.text("Statistic", "Estadística"),
                self.root.text("Before", "Antes"),
                self.root.text("After", "Después"),
                self.root.text("Change (p.p.)", "Cambio (p.p.)"),
            ]
        )
        before = comparison.before
        summaries = (before, comparison.after)
        metrics = tuple(
            None
            if summary is None
            else (summary.mean, summary.worst, pstdev(summary.values), summary.spread)
            for summary in summaries
        )
        labels = (
            self.root.text("Mean", "Media"),
            self.root.text("Maximum", "Máximo"),
            self.root.text(
                "Population standard deviation", "Desviación estándar poblacional"
            ),
            self.root.text("Range", "Amplitud"),
        )
        for row, label in enumerate(labels):
            a = metrics[0][row] if metrics[0] is not None else None
            b = metrics[1][row] if metrics[1] is not None else None
            values = (
                label,
                "—" if a is None else f"{a:.2f}",
                "—" if b is None else f"{b:.2f}",
                "—" if a is None or b is None else f"{b - a:+.2f}",
            )
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setToolTip(text)
                if column:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, column, item)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = table.horizontalHeader()
        assert header is not None
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setFixedHeight(310)
        layout.addWidget(table)
        toggle = QToolButton()
        toggle.setText(
            self.root.text("Show schedule details", "Mostrar detalles de la rotación")
        )
        toggle.setCheckable(True)
        toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        toggle.setArrowType(Qt.ArrowType.RightArrow)
        toggle.setToolTip(
            self.root.text(
                "Expand or collapse the schedule details immediately below.",
                "Desplegar u ocultar los detalles justo debajo.",
            )
        )
        layout.addWidget(toggle, 0, Qt.AlignmentFlag.AlignLeft)
        details = QTabWidget()
        details.addTab(
            self.worker_table(run, comparison),
            self.root.text("Worker indices", "Índices de trabajadores"),
        )
        for is_before in (True, False):
            scores = (
                before.values
                if is_before and before
                else None
                if is_before
                else comparison.after.values
            )
            details.addTab(
                self.schedule(run, comparison.kind.value, scores, before=is_before),
                self.root.text("Before", "Antes")
                if is_before
                else self.root.text("After", "Después"),
            )
        details.hide()
        details.setMinimumHeight(240)

        def disclose(checked: bool) -> None:
            """Keep the summary anchored while revealing details directly below.

            Args:
                checked: True shows the associated schedule and worker tabs.

            Returns:
                None; only this page's presentation changes.
            """
            toggle.setArrowType(
                Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow
            )
            toggle.setText(
                self.root.text(
                    "Hide schedule details", "Ocultar detalles de la rotación"
                )
                if checked
                else self.root.text(
                    "Show schedule details", "Mostrar detalles de la rotación"
                )
            )
            details.setVisible(checked)

        toggle.toggled.connect(disclose)
        layout.addWidget(details)
        layout.addStretch(1)
        return page

    def worker_table(
        self, run: RotationRun, comparison: ToolComparison
    ) -> QTableWidget:
        """Render exact matched worker indices and signed percentage-point changes.

        Args:
            run: Frozen worker identity/label order.
            comparison: Same-context numeric distributions.

        Returns:
            Read-only numeric table; absent before/delta cells stay missing.
        """
        table = AdaptiveTableWidget()
        table.setRowCount(len(run.worker_labels))
        table.setColumnCount(4)
        style_rotation_table(table)
        table.setHorizontalHeaderLabels(
            [
                self.root.text("Worker", "Trabajador"),
                self.root.text("Before", "Antes"),
                self.root.text("After", "Después"),
                self.root.text("Change (p.p.)", "Cambio (p.p.)"),
            ]
        )
        changes = comparison.changes
        for index, label in enumerate(run.worker_labels):
            before = comparison.before.values[index] if comparison.before else None
            delta = changes[index] if changes else None
            for column, value in enumerate(
                (
                    label,
                    "—" if before is None else f"{before:.2f}",
                    f"{comparison.after.values[index]:.2f}",
                    "—" if delta is None else f"{delta:+.2f}",
                )
            ):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                if column:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                numeric = (
                    before
                    if column == 1
                    else comparison.after.values[index]
                    if column == 2
                    else None
                )
                if numeric is not None:
                    item.setBackground(
                        QColor(
                            RISK_APPEARANCES[classify_probability(numeric)].color_hex
                        )
                    )
                table.setItem(index, column, item)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.resizeColumnsToContents()
        header = table.horizontalHeader()
        assert header is not None
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        for column in range(1, 4):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
        return table

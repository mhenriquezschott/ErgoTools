"""Owned bounded guided solve, truthful preview and explicit guarded retention.

Presentation layer. Only immutable planning values and a replaceable solver port
enter QThread. All project reads/writes, confirmations and accepted history remain
on the GUI thread. Cancel suppresses results and waits; running native solvers are
never terminated.
"""

import logging
from dataclasses import replace
from threading import Event
from typing import TYPE_CHECKING

from PyQt5.QtCore import QElapsedTimer, QObject, QSize, Qt, QThread, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QProgressDialog,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.rotation_optimization import (
    RotationPlanningOptimizer,
)
from ergotools.application.rotation_planning import (
    PreparedRotationPlan,
    accepted_rotation_run,
    prepare_rotation_plan,
)
from ergotools.application.rotation_scenarios import apply_rotation_run, run_is_current
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation import (
    RotationBackend,
    RotationSolution,
    RotationSolveStatus,
)
from ergotools.domain.rotation_comparison import compare_rotation_run
from ergotools.domain.rotation_scenario import RotationInputs, RotationRun
from ergotools.presentation.desktop.assessment_tool_tabs import (
    AssessmentResultTabs,
    assessment_tool_icon,
    assessment_tool_title,
)
from ergotools.presentation.desktop.jrot_result_table import (
    JrotResultTable,
    tool_caption,
)
from ergotools.presentation.desktop.workflow_action_style import (
    set_action_icon,
)

if TYPE_CHECKING:
    from ergotools.presentation.desktop.jrot_dialog import JrotDialog

# Keep operational failures visible while preserving accepted source/project data.
_LOG = logging.getLogger(__name__)


class PlanningThread(QThread):
    """Bounded solver worker with immutable input and no project access."""

    def __init__(
        self,
        prepared: PreparedRotationPlan,
        optimizer: RotationPlanningOptimizer,
        parent: QObject,
    ) -> None:
        """Capture solver input and independent cancellation intention.

        Args:
            prepared: Exact detached planning values.
            optimizer: Approved backend adapter through the pure application port.
            parent: GUI lifetime owner; no parent methods are called in run.

        Returns:
            None; no solve begins until start is called by the controller.
        """
        super().__init__(parent)
        self.prepared, self.optimizer = prepared, optimizer
        self.cancelled = Event()
        self.solution: RotationSolution | None = None
        self.error: str | None = None

    def run(self) -> None:
        """Solve and validate detached results without project access.

        Args:
            None.

        Returns:
            None; cancelled results are never published to the GUI controller.
        """
        try:
            problem = self.prepared.problem
            result = self.optimizer.solve(problem, self.cancelled.is_set)
            problem.validate_schedule(result.schedule)
            backend = RotationBackend.HIGHS
            if (
                result.backend is not backend
                or len(result.stages) != (1 if problem.generation else 2)
                or any(not isinstance(s, RotationSolveStatus) for s in result.stages)
            ):
                raise ValueError("Invalid planning solver evidence.")
            if not self.cancelled.is_set():
                self.solution = result
        except Exception as error:
            _LOG.exception("Guided planning solve failed")
            self.error = str(error)


class JrotPlanningController(QObject):
    """Own bounded previews, explicit result retention and proposal confirmation."""

    def __init__(
        self, root: "JrotDialog", optimizer: RotationPlanningOptimizer | None
    ) -> None:
        """Attach real planning controls while keeping normal JROT composition separate.

        Args:
            root: Guided owner of the project/scenario and shared history.
            optimizer: Injected real/controlled planner; None disables solve
            commands.

        Returns:
            None; opening creates no proposal, risk value or accepted run.
        """
        super().__init__(root)
        self.root, self.optimizer = root, optimizer
        self.worker: PlanningThread | None = None
        self.prepared: PreparedRotationPlan | None = None
        self.preview: RotationSolution | None = None
        self.run: RotationRun | None = None
        self.displayed_run: RotationRun | None = None
        self.close_requested = False
        self.entry_generation = False
        self.entry_origin: RotationInputs | None = None
        self.wait_dialog: QProgressDialog | None = None
        self.panel = QWidget()
        layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(0, 0, 0, 0)
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        actions = QHBoxLayout()
        actions.addWidget(
            QLabel(root.text("Time limit per pass (s)", "Límite por pasada (s)"))
        )
        self.limit = QSpinBox()
        self.limit.setRange(1, 3600)
        self.limit.setValue(60)
        actions.addWidget(self.limit)
        self.start_button = root.button(
            root.text("Run optimization", "Optimizar"), lambda: self.start(False)
        )
        self.cancel_button = root.button(
            root.text("Cancel optimization", "Cancelar optimización"), self.cancel
        )
        self.discard_button = root.button(
            root.text("Discard preview", "Descartar vista previa"),
            self.discard,
        )
        set_action_icon(self.start_button, root.icons["optimize_all_tools"], 36)
        set_action_icon(self.cancel_button, root.icons["cancel"], 28)
        set_action_icon(self.discard_button, root.icons["discard_preview"], 28)
        for b in (
            self.start_button,
            self.cancel_button,
            self.discard_button,
        ):
            actions.addWidget(b)
        actions.addStretch(1)
        layout.addLayout(actions)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)
        self.tool_heading = QLabel()
        self.tool_heading.setStyleSheet("font-weight:bold;font-size:16px;padding:4px;")
        heading_row = QHBoxLayout()
        self.tool_heading_icon = QLabel()
        self.tool_heading_icon.setFixedSize(36, 36)
        heading_row.addWidget(self.tool_heading_icon)
        heading_row.addWidget(self.tool_heading, 1)
        layout.addLayout(heading_row)
        self.tabs = AssessmentResultTabs()
        self.tabs.setIconSize(QSize(24, 24))
        self.tabs.currentChanged.connect(self.update_tool_heading)
        layout.addWidget(self.tabs, 1)
        self.keep_button = root.button(
            root.text("Keep optimization result", "Conservar resultado optimizado"),
            self.keep_result,
        )
        self.keep_button.setIcon(root.icons.get("keep_optimization_result", QIcon()))
        set_action_icon(self.keep_button, root.icons["keep_optimization_result"], 36)
        layout.addWidget(self.keep_button)
        self.note = QLabel(
            root.text(
                "Worker scores are time-weighted Job-risk indices, not "
                "individual injury probabilities. Breaks imply no "
                "physiological recovery. Keep optimization result retains the result "
                "without changing the original baseline; Main Save stores it.",
                "Los puntajes son índices de riesgo de trabajos ponderados "
                "por tiempo, no probabilidades individuales. Los descansos "
                "no suponen recuperación fisiológica. Conservar resultado mantiene la "
                "base original; Guardar lo almacena.",
            )
        )
        self.note.setWordWrap(True)
        layout.addWidget(self.note)
        self.elapsed = QElapsedTimer()
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.tick)
        self.refresh()

    @property
    def busy(self) -> bool:
        """Retain lifetime ownership until the bounded thread completion is processed.

        Args:
            None.

        Returns:
            True during solving/cancellation, including
            finished-but-not-yet-released threads.
        """
        return self.worker is not None

    def refresh(self) -> None:
        """Project command availability without accepting data or claiming feasibility.

        Args:
            None.

        Returns:
            None; preparation validates actual readiness when a solve is requested.
        """
        if self.root.workspace.editing is not self.root.owner:
            self.preview = None
            self.run = None
            self.prepared = None
            self.clear_matrices()
            for button in (
                self.start_button,
                self.keep_button,
                self.discard_button,
            ):
                button.setEnabled(False)
            self.status.setText(
                self.root.text(
                    "The project changed. Close and reopen this window.",
                    "El proyecto cambió. Cierre y vuelva a abrir esta ventana.",
                )
            )
            return
        record = self.root.scenario
        self.start_button.setIcon(
            self.root.icons[
                "optimize_selected_tool"
                if record and len(record.inputs.tools) == 1
                else "optimize_all_tools"
            ]
        )
        retained_run_changed = (
            self.preview is None
            and self.run is not None
            and (record is None or record.run != self.run)
        )
        if (
            not self.busy
            and self.prepared is not None
            and (retained_run_changed or not self.fresh())
        ):
            self.preview = None
            self.run = None
            self.prepared = None
            self.clear_matrices()
        available = self.optimizer is not None and record is not None and not self.busy
        self.start_button.setEnabled(available)
        self.cancel_button.setEnabled(
            self.busy and self.worker is not None and not self.worker.cancelled.is_set()
        )
        self.limit.setEnabled(not self.busy)
        self.keep_button.setToolTip(
            self.root.text(
                "Keep the result without changing the original baseline. Main "
                "Save writes the project.",
                "Conservar el resultado sin cambiar la base original. Guardar "
                "escribe el proyecto.",
            )
        )
        self.keep_button.setVisible(self.preview is not None)
        self.discard_button.setVisible(self.preview is not None)
        self.keep_button.setEnabled(self.preview is not None and not self.busy)
        self.discard_button.setEnabled(self.preview is not None and not self.busy)
        if not self.busy and self.preview is None:
            if record is not None and record.run is not None:
                self.show_saved_run(record.run)
            else:
                self.clear_matrices()
                self.status.setText(
                    self.root.text(
                        "No optimization result yet. Review the starting assignments "
                        "in step 04 and tool values in step 05, then optimize here.",
                        "Sin resultado de optimización. Revise las asignaciones del "
                        "paso 04 y los valores del 05; luego optimice aquí.",
                    )
                )

    def clear_matrices(self) -> None:
        """Release displayed result widgets before a new or retired solve context.

        Args:
            None.

        Returns:
            None; project inputs and accepted runs remain unchanged.
        """
        self.displayed_run = None
        while self.tabs.count():
            widget = self.tabs.widget(0)
            self.tabs.removeTab(0)
            if widget is not None:
                widget.deleteLater()

    def prepare(self, generation: bool) -> PreparedRotationPlan:
        """Freeze real current catalogs on the GUI thread before starting a worker.

        Args:
            generation: True requests feasibility without an observed baseline.

        Returns:
            Independently validated exact immutable solver context.

        Raises:
            ValueError: No scenario or complete usable planning context exists.
        """
        current = self.root.current()
        if current is None:
            raise ValueError("Create/select a rotation first.")
        if generation:
            current = replace(
                current, inputs=replace(current.inputs, baseline=None, proposed=None)
            )
        workspace = self.root.workspace
        return prepare_rotation_plan(
            current,
            self.root.repository.load_rotation_scenarios(),
            workspace.read_hierarchy().hierarchy,
            workspace.read_jobs().jobs,
            workspace.read_job_risk().risk,
            workspace.load_task_definitions(),
            generation=generation,
            time_limit_seconds=float(self.limit.value()),
        )

    def start(self, generation: bool = False) -> None:
        """Start a bounded preview, or generate assignments directly in the entry page.

        Args:
            generation: True generates starting assignments in step 04 only,
                using explicit confirmation for replacement; False optimizes in 07.

        Returns:
            None; invalid inputs stay available and produce a visible diagnostic.
        """
        if self.busy or self.optimizer is None or not self.root.prepare():
            return
        try:
            prepared = self.prepare(generation)
        except Exception as error:
            self.root.show_error(error)
            return
        self.entry_generation = generation
        origin = self.root.current()
        self.entry_origin = origin.inputs if self.entry_generation and origin else None
        self.root.go(3 if generation else 6)
        self.clear_matrices()
        self.prepared = prepared
        self.preview = None
        self.run = None
        self.worker = PlanningThread(prepared, self.optimizer, self)
        self.worker.finished.connect(self.finished)
        self.root.error.clear()
        self.elapsed.start()
        self.progress.show()
        self.timer.start()
        self.root.pages.setEnabled(False)
        self.root.drawer.setEnabled(False)
        self.root.scenarios.setEnabled(False)
        # Keep Cancel usable while other pages are locked.
        self.root.pages.setEnabled(True)
        for i in range(self.root.pages.count()):
            page = self.root.pages.widget(i)
            if page is not None and (self.entry_generation or i != 6):
                page.setEnabled(False)
        for b in self.root.findChildren(
            QPushButton, options=Qt.FindChildOption.FindDirectChildrenOnly
        ):
            b.setEnabled(b.text() == self.root.text("Close", "Cerrar"))
        self.tick()
        self.refresh()
        self.root.history.refresh()
        if self.entry_generation:
            self.wait_dialog = QProgressDialog(
                self.root.text(
                    "Generating feasible starting assignments…",
                    "Generando asignaciones iniciales factibles…",
                ),
                self.root.text("Cancel", "Cancelar"),
                0,
                0,
                self.root,
            )
            self.wait_dialog.setWindowTitle(
                self.root.text("Generate initial proposal", "Generar propuesta inicial")
            )
            self.wait_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.wait_dialog.canceled.connect(self.cancel)
            self.wait_dialog.show()
        self.worker.start()

    def tick(self) -> None:
        """Display elapsed time without claiming a completion percentage.

        Args:
            None.

        Returns:
            None; native backend stages retain their independently bounded budgets.
        """
        if self.worker is not None:
            cancelled = self.worker.cancelled.is_set()
            self.status.setText(
                self.root.text(
                    "Cancellation requested; waiting for bounded solver"
                    if cancelled
                    else "Optimizing the rotation",
                    "Cancelación solicitada; esperando al cálculo acotado"
                    if cancelled
                    else "Calculando con el optimizador requerido",
                )
                + f" · {self.elapsed.elapsed() / 1000:.1f} s"
            )

    def cancel(self) -> None:
        """Cancel publication while allowing the bounded solver to finish.

        Args:
            None.

        Returns:
            None; the window stays alive until its bounded worker exits.
        """
        if self.worker is not None:
            self.worker.cancelled.set()
            self.tick()
            self.refresh()

    def request_close(self) -> bool:
        """Defer native/keyboard closure until the owned thread finishes safely.

        Args:
            None.

        Returns:
            True closes now; False records close/cancel intention and retains
            ownership.
        """
        if not self.busy:
            return True
        self.close_requested = True
        self.cancel()
        return False

    def fresh(self) -> bool:
        """Recheck the scenario, source values and neighboring runs.

        Args:
            None.

        Returns:
            False for any retired input or unavailable/stale source; names alone may
            change.
        """
        if self.prepared is None:
            return False
        try:
            record = self.root.current()
            if record is None or record.scenario_id != self.prepared.scenario_id:
                return False
            if self.entry_generation and record.inputs != self.entry_origin:
                return False
            if (
                self.prepare(self.prepared.problem.generation).problem
                != self.prepared.problem
            ):
                return False
            if self.run is not None:
                w = self.root.workspace
                return run_is_current(
                    replace(record, run=self.run),
                    w.read_hierarchy().hierarchy,
                    w.read_jobs().jobs,
                    w.read_job_risk().risk,
                    self.root.repository.load_rotation_scenarios(),
                )
            return True
        except (ValueError, RuntimeError):
            return False

    def finished(self) -> None:
        """Present a validated preview or populate requested entry assignments.

        Args:
            None.

        Returns:
            None; keeping a preview is explicit; Main Save publishes the file.
        """
        worker = self.worker
        if worker is None:
            return
        worker.wait()
        self.worker = None
        self.timer.stop()
        self.progress.hide()
        if self.wait_dialog is not None:
            self.wait_dialog.blockSignals(True)
            self.wait_dialog.close()
            self.wait_dialog.deleteLater()
            self.wait_dialog = None
        for i in range(self.root.pages.count()):
            page = self.root.pages.widget(i)
            if page is not None:
                page.setEnabled(True)
        self.root.drawer.setEnabled(True)
        self.root.scenarios.setEnabled(True)
        for b in self.root.findChildren(
            QPushButton, options=Qt.FindChildOption.FindDirectChildrenOnly
        ):
            b.setEnabled(True)
        try:
            if worker.cancelled.is_set():
                self.status.setText(
                    self.root.text(
                        "Cancelled. No result applied.",
                        "Cancelado. No se aplicaron resultados.",
                    )
                )
            elif worker.solution is None:
                self.root.show_error(worker.error or "No feasible incumbent returned.")
                self.status.setText(worker.error or "No result.")
            else:
                assert self.prepared is not None
                if not self.prepared.problem.generation:
                    self.run = accepted_rotation_run(self.prepared, worker.solution)
                if not self.fresh():
                    self.run = None
                    self.root.show_error(
                        self.root.text(
                            "Inputs or source context changed. Run again.",
                            "Los datos o su contexto cambiaron. Calcule nuevamente.",
                        )
                    )
                    self.status.setText(
                        self.root.text(
                            "Result retired. Run again.",
                            "Resultado sin vigencia. Calcule nuevamente.",
                        )
                    )
                else:
                    self.preview = worker.solution
                    if self.entry_generation:
                        self.keep_result()
                    else:
                        self.render()
        except Exception as error:
            _LOG.exception("Unable to present guided solve")
            self.root.show_error(error)
            self.status.setText(str(error))
        finally:
            worker.deleteLater()
            self.root.project_page()
            self.root.history.refresh()
            self.start_button.setEnabled(
                self.optimizer is not None and self.root.scenario is not None
            )
            self.cancel_button.setEnabled(False)
            self.limit.setEnabled(True)
            self.keep_button.setVisible(self.preview is not None)
            self.discard_button.setVisible(self.preview is not None)
            self.keep_button.setEnabled(self.preview is not None)
            self.discard_button.setEnabled(self.preview is not None)
        if self.preview is None:
            termination = self.status.text()
            self.refresh()
            self.status.setText(termination + " · " + self.status.text())
        if self.close_requested:
            self.close_requested = False
            self.root.accept()

    def render(self) -> None:
        """Show analyzed-tool tabs from the same returned schedule, without re-solving.

        Args:
            None.

        Returns:
            None; missing generation coefficients display a dash rather than zero.
        """
        assert self.prepared is not None and self.preview is not None
        self.clear_matrices()
        problem = self.prepared.problem
        for kind in problem.inputs.tools:
            risks = {
                r.target_key: r.probability_percent
                for r in problem.risks
                if r.kind is kind
            }
            scores = (
                problem.scores(self.preview.schedule, kind)
                if len(risks) == len(problem.target_keys)
                else None
            )
            self.tabs.addTab(
                JrotResultTable(
                    problem.inputs,
                    self.preview.schedule,
                    dict(self.prepared.job_labels),
                    self.prepared.worker_labels,
                    risks,
                    scores,
                    self.root.language,
                ),
                assessment_tool_icon(self.root.icons, kind),
                tool_caption(kind.value),
            )
        self.update_tool_heading()
        self.status.setText(
            self.root.text(
                "Optimization preview · Maximum exposure first, "
                "then balanced distribution. "
                "Keep the result to retain it without changing the baseline.",
                "Vista de optimización · Primero la exposición máxima, "
                "luego el equilibrio. "
                "Conserve el resultado sin cambiar la base.",
            )
            + self.feasibility_notice(self.preview.stages)
        )

    def update_tool_heading(self) -> None:
        """Show the selected matrix's full tool name without changing the solution.

        Args:
            None.

        Returns:
            None; short matrix tabs and their packaged tool icons remain unchanged.
        """
        index = self.tabs.currentIndex()
        caption = self.tabs.tabText(index) if index >= 0 else ""
        kinds = {
            "LiFFT": AssessmentKind.LIFFT,
            "DUET": AssessmentKind.DUET,
            "ST": AssessmentKind.TST,
        }
        kind = kinds.get(caption)
        self.tool_heading.setText(assessment_tool_title(kind) if kind else "")
        self.tool_heading.setVisible(kind is not None)
        self.tool_heading_icon.setVisible(kind is not None)
        if kind is not None:
            self.tool_heading_icon.setPixmap(
                assessment_tool_icon(self.root.icons, kind).pixmap(32, 32)
            )

    def feasibility_notice(self, stages: tuple[RotationSolveStatus, ...]) -> str:
        """Describe bounded feasible completion without presenting engine internals.

        Args:
            stages: Recorded success status of each actual optimization pass.

        Returns:
            A caution only when a pass found a feasible, unproven best result.
        """
        return (
            self.root.text(
                " Further improvement may be possible within a longer time limit.",
                " Un límite de tiempo mayor podría mejorar el resultado.",
            )
            if RotationSolveStatus.FEASIBLE in stages
            else ""
        )

    def discard(self) -> None:
        """Discard only the unapplied result and restore retained accepted evidence.

        Args:
            None.

        Returns:
            None; accepted Job edits, prior runs, history and Save state remain intact.
        """
        if self.busy:
            return
        self.preview = None
        self.run = None
        self.prepared = None
        self.clear_matrices()
        self.refresh()
        self.root.project_page()

    def show_saved_run(self, run: RotationRun) -> None:
        """Reopen frozen accepted matrices without solving or mixing current Job values.

        Args:
            run: Exact accepted evidence, possibly stale or an unsupported older model.

        Returns:
            None; unsupported models show schedules but no newly interpreted indices.
        """
        if self.displayed_run != run:
            self.clear_matrices()
            try:
                comparisons = {c.kind: c for c in compare_rotation_run(run)}
            except ValueError:
                comparisons = {}
            for kind in run.inputs.tools:
                risks = {
                    c.target_key: c.measurement.probability_percent
                    for c in run.coefficients
                    if c.measurement.kind is kind
                    and c.measurement.probability_percent is not None
                }
                scores = comparisons[kind].after.values if kind in comparisons else None
                self.tabs.addTab(
                    JrotResultTable(
                        run.inputs,
                        run.arrangement,
                        {c.target_key: c.job_name for c in run.coefficients},
                        run.worker_labels,
                        risks,
                        scores,
                        self.root.language,
                    ),
                    assessment_tool_icon(self.root.icons, kind),
                    tool_caption(kind.value),
                )
            self.displayed_run = run
        record = self.root.current()
        w = self.root.workspace
        current = record is not None and run_is_current(
            record,
            w.read_hierarchy().hierarchy,
            w.read_jobs().jobs,
            w.read_job_risk().risk,
            self.root.repository.load_rotation_scenarios(),
        )
        self.update_tool_heading()
        self.status.setText(
            self.root.text(
                "Kept optimization result", "Resultado optimizado conservado"
            )
            + (
                ""
                if current
                else self.root.text(
                    " · Setup has changed; showing the recorded result",
                    " · La configuración cambió; se muestra el resultado guardado",
                )
            )
            + (
                self.root.text(
                    " · Run again to balance the remaining workers",
                    " · Optimice de nuevo para equilibrar a los demás trabajadores",
                )
                if len(run.stages) == 1
                else ""
            )
            + self.feasibility_notice(run.stages)
        )

    def keep_result(self) -> None:
        """Explicitly keep an optimization, or accept a generated starting proposal.

        Args:
            None.

        Returns:
            None; rejected/cancelled/stale previews never overwrite project data.
        """
        if (
            self.preview is None
            or self.prepared is None
            or self.busy
            or not self.root.prepare()
        ):
            return
        try:
            if not self.fresh():
                raise ValueError("Planning inputs changed; run again before applying.")
            current = self.root.current()
            assert current is not None
            if self.prepared.problem.generation:
                observed = self.entry_generation and current.inputs.baseline is not None
                if observed and not self.root.confirm(
                    self.root.text(
                        "Replace the baseline assignments in step 04 with "
                        "generated starting assignments? This is a feasible "
                        "example, not an observed or risk-optimized schedule. "
                        "The kept result remains as recorded evidence and may "
                        "become stale. Undo restores the baseline.",
                        "¿Reemplazar las asignaciones de base del paso 04 por "
                        "asignaciones factibles? No son una observación ni una "
                        "optimización. El resultado conservado permanece como "
                        "evidencia y puede perder vigencia. Deshacer restaura "
                        "la base.",
                    )
                ):
                    self.discard()
                    return
                if (
                    not observed
                    and current.inputs.proposed is not None
                    and not self.root.confirm(
                        self.root.text(
                            "Replace the entered proposal? Undo restores it.",
                            "¿Reemplazar la propuesta ingresada? Deshacer la restaura.",
                        )
                    )
                ):
                    self.discard()
                    return
                candidate = replace(
                    current,
                    inputs=(
                        replace(current.inputs, baseline=self.preview.schedule)
                        if observed
                        else replace(current.inputs, proposed=self.preview.schedule)
                    ),
                )
            else:
                assert self.run is not None
                if current.run is not None and not self.root.confirm(
                    self.root.text(
                        "Keep this new optimization instead of the previously "
                        "retained result? The original baseline will not "
                        "change. Undo restores the previous result.",
                        "¿Conservar esta optimización en lugar del resultado "
                        "anterior? La base original no cambiará. Deshacer "
                        "restaura el resultado anterior.",
                    )
                ):
                    return
                w = self.root.workspace
                candidate = apply_rotation_run(
                    current,
                    self.prepared.problem.inputs,
                    self.run,
                    w.read_hierarchy().hierarchy,
                    w.read_jobs().jobs,
                    w.read_job_risk().risk,
                    self.root.repository.load_rotation_scenarios(),
                )
            if not self.fresh():
                raise ValueError("Planning target changed during confirmation.")
            generated = self.prepared.problem.generation
            self.root.repository.replace_rotation_scenario(current, candidate)
            self.preview = None
            self.run = candidate.run
            self.root.reload()
            self.status.setText(
                self.root.text(
                    "Starting assignments updated. Main Save stores them.",
                    "Asignaciones iniciales actualizadas. Guardar las almacena.",
                )
                if generated
                else self.root.text(
                    "Result kept. Original baseline unchanged. Main Save stores it.",
                    "Resultado conservado. Base original intacta. Guardar lo almacena.",
                )
            )
        except Exception as error:
            _LOG.exception("Guided planning retention failed")
            self.preview = None
            self.run = None
            self.root.show_error(error)

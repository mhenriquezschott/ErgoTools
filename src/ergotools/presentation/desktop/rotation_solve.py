"""Owned background CBC/HiGHS solve and original overlay/result/transfer workflow.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

import logging
from dataclasses import replace
from threading import Event
from typing import TYPE_CHECKING

from PyQt5.QtCore import QObject, Qt, QThread, QTimer
from PyQt5.QtWidgets import QLabel, QProgressBar, QWidget

from ergotools.application.rotation_optimization import RotationOptimizer
from ergotools.application.rotation_preparation import prepare_rotation_problem
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation import (
    RotationBackend,
    RotationProblem,
    RotationSolution,
    RotationSolveStatus,
)
from ergotools.domain.rotation_scheme import RotationMode, RotationScheme
from ergotools.presentation.desktop.rotation_comparison import RotationComparisonDialog
from ergotools.presentation.desktop.rotation_result_table import render_rotation_result

if TYPE_CHECKING:
    from ergotools.presentation.desktop.rotation_dialog import RotationDialog

# Module-scoped diagnostic logger for owned rotation command/solver failures.
_LOGGER = logging.getLogger(__name__)


class _SolveThread(QThread):
    """Carry immutable input and a solver port only; no view or repository access."""

    def __init__(
        self,
        optimizer: RotationOptimizer,
        problem: RotationProblem,
        kind: AssessmentKind,
        parent: QObject,
        *,
        all_tools: bool = False,
    ) -> None:
        """Capture immutable solver input and cancellation intent.

        Capture immutable solver input and cancellation intent without accessing widgets
        or project storage on the worker thread.

        Args:
            optimizer: Injected CBC/HiGHS solver capability; None keeps solve actions
                unavailable.
            problem: Immutable validated rotation problem passed to the owned solver
                thread.
            kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
                captions are not keys.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.
            all_tools: True selects HiGHS multi-tool optimization; False selects CBC
                single-tool optimization.

        Returns:
            None.
        """
        super().__init__(parent)
        self.optimizer = optimizer
        self.problem = problem
        self.kind = kind
        self.all_tools = all_tools
        self.cancelled = Event()
        self.solution: RotationSolution | None = None
        self.failed = False

    def run(self) -> None:
        """Solve on this thread; publish only after an independent result check.

        Args:
            None.

        Returns:
            None.
        """
        try:
            solution = (
                self.optimizer.optimize_all_tools(self.problem)
                if self.all_tools
                else self.optimizer.optimize_single_tool(self.problem, self.kind)
            )
            self.problem.validate_schedule(solution.schedule)
            if (
                solution.backend
                is not (
                    RotationBackend.HIGHS if self.all_tools else RotationBackend.CBC
                )
                or len(solution.stages) != (2 if self.all_tools else 1)
                or any(
                    not isinstance(stage, RotationSolveStatus)
                    for stage in solution.stages
                )
            ):
                raise ValueError("Invalid rotation solver evidence.")
            if not self.cancelled.is_set():
                self.solution = solution
        except Exception:
            _LOGGER.exception("JROT solve failed")
            self.failed = True


class RotationSolveController(QObject):
    """Keep the modal form alive and blocked until its bounded solver exits.

    Cancel suppresses publication; it never terminates the solver thread. Closing is
    deferred until finished, when joining is safe. All widgets and persistence stay on
    the GUI thread, and optimization itself performs no writes.
    """

    def __init__(self, view: "RotationDialog", optimizer: RotationOptimizer) -> None:
        """Wire selected-tool actions to the existing original form controls.

        Args:
            view: Owning integrated window whose controls and existing command policy
                are reused.
            optimizer: Injected CBC/HiGHS solver capability; None keeps solve actions
                unavailable.

        Returns:
            None.
        """
        super().__init__(view)
        self.view = view
        self.optimizer = optimizer
        self.worker: _SolveThread | None = None
        self.preview: RotationScheme | None = None
        self.applied_kind: AssessmentKind | None = None
        self.applied_mode: RotationMode | None = None
        self.comparison: RotationComparisonDialog | None = None
        self._input: RotationScheme | None = None
        self._close_requested = False
        self.overlay = QWidget(view)
        self.overlay.setObjectName("jrotSolveOverlay")
        self.overlay.setStyleSheet(
            "QWidget#jrotSolveOverlay { background-color: rgba(0, 0, 0, 100); }"
        )
        self.label = QLabel(self.overlay)
        self.label.setStyleSheet(
            "color: white; font-size: 16pt; font-weight: bold; background: transparent;"
        )
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress = QProgressBar(self.overlay)
        self.progress.setRange(0, 100)
        self.progress.setStyleSheet(
            "QProgressBar { border: 2px solid grey; border-radius: 5px; "
            "text-align: center; background-color: white; } "
            "QProgressBar::chunk { background-color: #72ff00; width: 1px; }"
        )
        self.cancel_button = view.button(view.text("Cancel", "Cancelar"), "cancel")
        self.cancel_button.setParent(self.overlay)
        self.cancel_button.clicked.connect(self.cancel)
        self.overlay.hide()
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self._tick)
        self._ticks = 0
        view.optimize_button.clicked.connect(self.start)
        view.optimize_all_button.clicked.connect(self.start_all)
        view.compare_button.clicked.connect(self.compare)
        view.optimize_all_button.setToolTip(
            view.text(
                "Optimize all three tools using HiGHS.",
                "Optimizar las tres herramientas con HiGHS.",
            )
        )
        view.compare_button.setToolTip(
            view.text(
                "Evaluate the optimized schedule using the other tools.",
                "Evaluar la rotación optimizada con las otras herramientas.",
            )
        )
        view.transfer_button.clicked.connect(self.transfer)
        view.optimize_button.setToolTip(
            view.text(
                "Optimize the selected tool using CBC.",
                "Optimizar la herramienta seleccionada con CBC.",
            )
        )
        view.transfer_button.setToolTip(
            view.text(
                "Replace the current rotation with the optimized assignment.",
                "Reemplazar la rotación actual por la asignación optimizada.",
            )
        )
        self.refresh_states()

    @property
    def busy(self) -> bool:
        """Report ownership until the finished callback releases the thread.

        Args:
            None.

        Returns:
            True until the owned worker's finished callback releases it, even after
            cancellation intent.
        """
        return self.worker is not None

    def refresh_states(self) -> None:
        """Enable solving only for a complete grid with selected-tool evidence.

        Args:
            None.

        Returns:
            None.
        """
        eligible = self._eligible((self.view.kind,))
        all_eligible = self._eligible(tuple(AssessmentKind))
        self.view.optimize_button.setEnabled(eligible)
        self.view.optimize_all_button.setEnabled(all_eligible)
        self.view.transfer_button.setEnabled(self.preview is not None and not self.busy)
        self.view.compare_button.setEnabled(self.preview is not None and all_eligible)

    def _eligible(self, kinds: tuple[AssessmentKind, ...]) -> bool:
        """Check complete grid and requested-tool evidence.

        Check complete grid and requested-tool evidence without starting a solver or
        changing the draft.

        Args:
            kinds: Required typed tool set whose evidence must be complete before
                solving.

        Returns:
            True only when the complete current grid supplies validated evidence for
            every requested tool.
        """
        grid = self.view.grid
        if grid is None or not grid.rowCount() or self.busy:
            return False
        try:
            scheme = grid.current_scheme("_preview", scope=self.view.scope)
            prepare_rotation_problem(scheme, grid.pool, kinds, time_limit_seconds=60)
        except ValueError:
            return False
        return True

    def _close_comparison(self) -> None:
        """Close and release the owned comparison preview.

        Close and release the owned comparison preview before clearing or replacing its
        result.

        Args:
            None.

        Returns:
            None.
        """
        if self.comparison is not None:
            self.comparison.close()
            self.comparison.deleteLater()
            self.comparison = None

    def clear_result(self, *, clear_provenance: bool = True) -> None:
        """Clear the preview; a tool repaint can retain applied provenance.

        Args:
            clear_provenance: True also drops previously applied solver provenance;
                False retains it for a tool repaint.

        Returns:
            None.
        """
        self._close_comparison()
        self.preview = None
        if clear_provenance:
            self.applied_kind = None
            self.applied_mode = None
        table = self.view.optimized_table
        table.clear()
        table.setRowCount(0)
        table.setColumnCount(0)
        self.refresh_states()

    def start(self) -> None:
        """Start the selected-tool CBC run over immutable input.

        Args:
            None.

        Returns:
            None.
        """
        self._start(all_tools=False)

    def start_all(self) -> None:
        """Start the original two-stage HiGHS all-tool workflow.

        Args:
            None.

        Returns:
            None.
        """
        self._start(all_tools=True)

    def _start(self, *, all_tools: bool) -> None:
        """Validate the requested tool set and time limit.

        Validate the requested tool set and time limit, capture immutable solver input
        and block the modal form until its owned worker actually finishes.

        Args:
            all_tools: True selects HiGHS multi-tool optimization; False selects CBC
                single-tool optimization.

        Returns:
            None.
        """
        if self.busy:
            return
        grid = self.view.grid
        assert grid is not None
        if not self.view.time_limit_input.hasAcceptableInput():
            self.view._message(
                self.view.text(
                    "Enter an optimization limit from 1 to 180 minutes.",
                    "Ingrese un límite de optimización de 1 a 180 minutos.",
                ),
                error=True,
            )
            return
        try:
            source = grid.current_scheme("_preview", scope=self.view.scope)
            problem = prepare_rotation_problem(
                source,
                grid.pool,
                tuple(AssessmentKind) if all_tools else (self.view.kind,),
                time_limit_seconds=int(self.view.time_limit_input.text()) * 60,
            )
        except ValueError:
            self.view._message(
                self.view.text(
                    "Complete the rotation and required Job risk data "
                    "before optimizing.",
                    "Complete la rotación y los datos de riesgo antes de optimizar.",
                ),
                error=True,
            )
            return
        self.clear_result(clear_provenance=False)
        self._input = source
        self._close_requested = False
        self._ticks = 0
        thread = _SolveThread(
            self.optimizer, problem, self.view.kind, self, all_tools=all_tools
        )
        self.worker = thread
        thread.finished.connect(self._finished)
        self.view.setup_group.setEnabled(False)
        self.view.splitter.setEnabled(False)
        self.view.close_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress.setValue(0)
        self.resize_overlay()
        self.overlay.show()
        self.overlay.raise_()
        self.overlay.setFocus()
        self.timer.start()
        self._tick()
        self.refresh_states()
        if self.view.history_actions is not None:
            self.view.history_actions.refresh()
        thread.start()

    def resize_overlay(self) -> None:
        """Cover the local form and keep the source-centered controls on resize.

        Args:
            None.

        Returns:
            None.
        """
        self.overlay.setGeometry(self.view.rect())
        x = self.overlay.width() // 2
        y = self.overlay.height() // 2
        self.label.setGeometry(x - 300, y - 60, 600, 50)
        self.progress.setGeometry(x - 150, y, 300, 20)
        self.cancel_button.setGeometry(x - 50, y + 40, 100, 32)

    def _tick(self) -> None:
        """Update the owned solve overlay.

        Project elapsed solve progress or cancellation wording into the original overlay
        without reading repositories.

        Args:
            None.

        Returns:
            None.
        """
        thread = self.worker
        if thread is None:
            return
        self._ticks += 1
        if thread.cancelled.is_set():
            self.label.setText(
                self.view.text(
                    "Cancelling: waiting for solver",
                    "Cancelando: esperando al solucionador",
                )
            )
        else:
            message = (
                self.view.text(
                    "Optimizing Rotation for All Tools",
                    "Optimizando todas las herramientas",
                )
                if thread.all_tools
                else self.view.text("Optimizing Rotation", "Optimizando rotación")
            )
            self.label.setText(message + "." * (self._ticks % 4))
        # This is elapsed budget, not backend-reported scientific/solver progress.
        self.progress.setValue(
            min(
                99,
                int(
                    self._ticks
                    * 0.5
                    / (
                        thread.problem.time_limit_seconds
                        * (2 if thread.all_tools else 1)
                    )
                    * 100
                ),
            )
        )

    def cancel(self) -> None:
        """Discard this run's eventual result while retaining worker ownership.

        Args:
            None.

        Returns:
            None.
        """
        if self.worker is not None:
            self.worker.cancelled.set()
            self.cancel_button.setEnabled(False)
            self._tick()

    def request_close(self) -> bool:
        """Defer modal rejection while busy; return whether closure must wait.

        Args:
            None.

        Returns:
            True when closure must wait for the owned worker; False when it may proceed
            immediately.
        """
        if not self.busy:
            self._close_comparison()
            return False
        self._close_requested = True
        self.cancel()
        return True

    def _finished(self) -> None:
        """Join the finished owned worker, release its Qt resources, restore controls.

        Join the finished owned worker, release its Qt resources, restore controls and
        publish only an uncancelled validated result; honor deferred close afterward.

        Args:
            None.

        Returns:
            None.
        """
        thread = self.worker
        assert thread is not None
        thread.wait()  # Backend returned before finished; join final thread cleanup.
        cancelled = thread.cancelled.is_set()
        solution = thread.solution
        failed = thread.failed
        kind = thread.kind
        all_tools = thread.all_tools
        self.worker = None
        thread.deleteLater()
        self.timer.stop()
        self.overlay.hide()
        self.view.setup_group.setEnabled(True)
        self.view.splitter.setEnabled(True)
        self.view.close_button.setEnabled(True)
        if not cancelled and solution is not None:
            assert self._input is not None and self.view.grid is not None
            candidate = replace(
                self._input,
                current=solution.schedule,
                mode=RotationMode.ALL_TOOLS if all_tools else RotationMode.SINGLE_TOOL,
                primary_kind=None if all_tools else kind,
            )
            if all_tools:
                self._show_comparison(self._input, candidate, all_tools=True)
            else:
                self.preview = candidate
                render_rotation_result(
                    self.view.optimized_table,
                    candidate,
                    self.view.grid.pool,
                    kind,
                    self.view.language,
                )
        self.view._states()
        self.refresh_states()
        if self._close_requested:
            self.view.reject()
        elif not cancelled and failed:
            self.view._message(
                self.view.text(
                    "Optimization failed. The current rotation was not changed.",
                    "La optimización falló. La rotación actual no cambió.",
                ),
                error=True,
            )

    def transfer(self) -> None:
        """Apply the preview's exact links without an implicit database save.

        Args:
            None.

        Returns:
            None.
        """
        if self.preview is None or self.busy:
            return
        assert self.view.grid is not None
        self._close_comparison()
        self.view.grid.load_scheme(self.preview)
        self.view._manual_edit = False
        self.applied_kind = self.preview.primary_kind
        self.applied_mode = self.preview.mode
        self.view.record_history()
        self.refresh_states()

    def prepare_save(self, scheme: RotationScheme) -> RotationScheme:
        """Attach optimization provenance only after Use as Current, never preview.

        Args:
            scheme: Immutable complete saved or proposed rotation scheme with exact
                evidence links.

        Returns:
            Scheme with explicitly applied optimization provenance, or the unchanged
            manual scheme if no preview was applied.
        """
        return (
            replace(scheme, mode=self.applied_mode, primary_kind=self.applied_kind)
            if self.applied_mode is not None
            else scheme
        )

    def compare(self) -> None:
        """Open the original other-tools comparison for the visible result.

        Args:
            None.

        Returns:
            None.
        """
        if self.preview is None or not self._eligible(tuple(AssessmentKind)):
            return
        assert self.view.grid is not None
        current = self.view.grid.current_scheme("_preview", scope=self.view.scope)
        self._show_comparison(current, self.preview, all_tools=False)

    def _show_comparison(
        self,
        current: RotationScheme,
        optimized: RotationScheme,
        *,
        all_tools: bool,
    ) -> None:
        """Replace the owned comparison window over frozen current/optimized schedules.

        Replace the owned comparison window over frozen current/optimized schedules and
        connect one explicit Apply action.

        Args:
            current: Complete frozen current schedule used for comparison.
            optimized: Validated frozen optimized schedule with exact pool/Job
                links.
            all_tools: True selects HiGHS multi-tool optimization; False selects CBC
                single-tool optimization.

        Returns:
            None.
        """
        assert self.view.grid is not None
        self._close_comparison()
        comparison = RotationComparisonDialog(
            current,
            optimized,
            self.view.grid.pool,
            self.view.icons,
            selected_kind=self.view.kind,
            all_tools=all_tools,
            language=self.view.language,
            parent=self.view,
        )
        self.comparison = comparison
        if all_tools:
            comparison.apply_requested.connect(lambda: self._apply_all(optimized))
        comparison.show()

    def _apply_all(self, optimized: RotationScheme) -> None:
        """Publish the accepted all-tool preview into the original result table.

        Publish the accepted all-tool preview into the original result table, apply its
        exact links locally and release the comparison window.

        Args:
            optimized: Validated frozen optimized schedule with exact pool/Job
                links.

        Returns:
            None.
        """
        assert self.view.grid is not None
        self.preview = optimized
        render_rotation_result(
            self.view.optimized_table,
            optimized,
            self.view.grid.pool,
            self.view.kind,
            self.view.language,
        )
        self.transfer()
        self._close_comparison()

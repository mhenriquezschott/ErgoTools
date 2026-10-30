"""Main LiFFT presenter binding for the shared assessment editor.

Presentation layer. AssessmentTaskGrid owns controls, rows, headers and scrolling;
AssessmentEditorSection owns totals/action composition. This adapter projects display
units, retains pending text and passes edits/results through the established presenter.
It owns no SQL, scientific formula, independent grid layout or separate history stack.
"""

from collections.abc import Callable, Mapping
from typing import cast

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.settings import Language
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.lifft import LifftTaskResult
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.lifft_summary import LifftSummary
from ergotools.domain.assessments.validation import DraftError
from ergotools.domain.display_precision import DisplayPrecision
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.assessment_editor_section import (
    AssessmentActionRow,
    AssessmentEditorSection,
)
from ergotools.presentation.desktop.assessment_task_grid import (
    AssessmentCellEdit,
    AssessmentTaskGrid,
)
from ergotools.presentation.desktop.historical_result_display import (
    historical_damage_color,
    historical_number,
    show_historical_rows,
)
from ergotools.presentation.desktop.lifft_presenter import LifftPresenter
from ergotools.presentation.desktop.precision_editor import PrecisionLineEdit
from ergotools.presentation.desktop.theme.lifft_summary import display_lifft_summary
from ergotools.presentation.desktop.theme.main_workspace import MAIN_WORKSPACE_STYLE
from ergotools.presentation.desktop.tool_result_summary import ToolResultSummary
from ergotools.presentation.edit_context import EditContext

# English reference LiFFT captions mapped to Spanish; dimensional units are supplied by
# the bound context.
_TEXT = {
    "Task #": ("Tarea #"),
    "Lever Arm": ("Brazo de Palanca"),
    "Load": ("Carga"),
    "Moment": ("Momento"),
    "Repetitions (per work day)": ("Repeticiones (por jornada laboral)"),
    "Damage (cumulative)": ("Daño (acumulado)"),
    "% Total (damage)": ("% Total (daño)"),
    "Clear assessment": ("Limpiar evaluación"),
    "Calculate": ("Calcular"),
    "Total Cumulative Damage:": ("Daño Acumulado Total:"),
    "Probability of High Risk Job * (%):": (
        "Probabilidad de Trabajo de Alto Riesgo * (%):"
    ),
    "Clear the active tool's task inputs and calculated results.": (
        "Borre los datos y resultados calculados de la herramienta activa."
    ),
    "Calculate risk results from the task data currently shown.": (
        "Calcule el riesgo con los datos de tareas mostrados."
    ),
    "Enter the lower-back lever arm for this lifting task.": (
        "Ingrese el brazo de palanca lumbar de esta tarea de levantamiento."
    ),
    "Enter the load handled during this lifting task.": (
        "Ingrese la carga manipulada en esta tarea de levantamiento."
    ),
    "Enter repetitions performed during one work day.": (
        "Ingrese las repeticiones realizadas en una jornada laboral."
    ),
    "Task row number.": ("Número de fila de la tarea."),
    "Horizontal distance between the load and the lower back.": (
        "Distancia horizontal entre la carga y la zona lumbar."
    ),
    "Load handled during this task.": ("Carga manipulada durante esta tarea."),
    "Calculated lower-back moment.": ("Momento lumbar calculado."),
    "Task repetitions during one work day.": ("Repeticiones de la tarea por jornada."),
    "Calculated cumulative damage for this task.": (
        "Daño acumulado calculado de la tarea."
    ),
    "This task's percentage of total cumulative damage.": (
        "Porcentaje de esta tarea en el daño acumulado total."
    ),
}
# Original task-column explanations in displayed column order, independent of source
# calculations.
_HEADER_TIPS = (
    "Task row number.",
    "Horizontal distance between the load and the lower back.",
    "Load handled during this task.",
    "Calculated lower-back moment.",
    "Task repetitions during one work day.",
    "Calculated cumulative damage for this task.",
    "This task's percentage of total cumulative damage.",
)
# Original editable task-field explanations in arm/load/repetition order.
_INPUT_TIPS = (
    "Enter the lower-back lever arm for this lifting task.",
    "Enter the load handled during this lifting task.",
    "Enter repetitions performed during one work day.",
)


class LifftTaskPanel(QWidget):
    """Original editable task grid with event-driven headers and injected services."""

    # Emitted only after a changed cell has completed validation/acceptance.
    input_committed = pyqtSignal()

    def __init__(
        self,
        presenter: LifftPresenter,
        icons: Mapping[str, QIcon],
        *,
        calculate: Callable[[], None],
        clear: Callable[[], None],
        invalidate: Callable[[], None],
        parent: QWidget | None = None,
    ) -> None:
        """Construct reference controls without opening files or changing source.

        Args:
            presenter: Injected tool/workplace coordinator; owns parsing and source
                commands, not these widgets.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            calculate: Callback running the host's explicit Calculate action.
            clear: Host-owned confirmation and scoped reversible assessment clearing.
            invalidate: Callback refreshing host results and shared-history actions
                when input becomes pending or a completed cell is accepted.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        self.presenter = presenter
        self._invalidate = invalidate
        self.context: EditContext | None = None
        self.pending = False
        self.language = Language.ENGLISH
        self.inputs: list[
            tuple[PrecisionLineEdit, PrecisionLineEdit, PrecisionLineEdit]
        ] = []
        self.outputs: list[tuple[QLabel, QLabel, QLabel]] = []
        self.task_ids: tuple[str, ...] = ()
        self.selected_task_id: str | None = None
        self.setStyleSheet(MAIN_WORKSPACE_STYLE)
        layout = QVBoxLayout(self)
        self.task_grid = AssessmentTaskGrid(
            self.language,
            self.presenter.convention,
            kind=AssessmentKind.LIFFT,
            worker_layout=True,
        )
        self.header_widget = self.task_grid.header_widget
        self.header_grid = self.task_grid.header_grid
        self.headers = self.task_grid.headers
        self.header = self.task_grid.header
        self.body_scroll = self.task_grid.body_scroll
        self.frame = self.task_grid.frame
        self.grid = self.task_grid.grid
        self.task_grid.input_edited.connect(self._mark_pending)
        self.task_grid.cell_finished.connect(self._complete_cell)
        self.task_grid.task_focused.connect(self._select_task)
        self.summary = ToolResultSummary()
        self.total_title = self.summary.total_title
        self.total_value = self.summary.total_value
        self.probability_title = self.summary.probability_title
        self.probability_value = self.summary.probability_value
        self.action_row = AssessmentActionRow(icons, tasks=True)
        self.clear_button = self.action_row.clear_button
        self.calculate_button = self.action_row.calculate_button
        assert self.action_row.add_task_button is not None
        assert self.action_row.remove_task_button is not None
        self.add_task_button = self.action_row.add_task_button
        self.remove_task_button = self.action_row.remove_task_button
        self.clear_button.clicked.connect(clear)
        self.calculate_button.clicked.connect(calculate)
        self.editor_section = AssessmentEditorSection(
            self.task_grid, self.summary, self.action_row
        )
        layout.addWidget(self.editor_section, 1)

    def _text(self, text: str) -> str:
        """Resolve this component's UI wording without translating saved user values.

        Args:
            text: Literal control text or user input; interpretation follows this
                method's stated policy.

        Returns:
            Localized UI wording according to this component's catalog/fallback
            contract.
        """
        return _TEXT[text] if self.language is Language.SPANISH else text

    def load_source(self, context: EditContext | None, language: Language) -> None:
        """Load committed projected input; no programmatic load triggers an edit.

        Args:
            context: Exact source/display interpretation captured when the grid was
                bound; None clears the view.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.

        Returns:
            None.
        """
        # Discard only projection-local completion signals before retiring fields;
        # callers resolve drafts before intentional navigation or bulk acceptance.
        self.pending = False
        self.context = context
        self.language = language
        self.pending = False
        precision = (
            self.presenter.workspace.project_metadata.precision
            if self.presenter.workspace.project_metadata
            else DisplayPrecision()
        )
        self.task_grid.language = self.language
        self.task_grid.convention = (
            context.convention if context else self.presenter.convention
        )
        self.task_grid.precision = precision
        self.task_grid.system = self.presenter.system
        rows = context.view.tasks if context else ()
        projected = (
            LifftDraft(
                context.view.system if context else self.presenter.system,
                tuple(
                    LifftTask(t.task_id, t.lever_arm, t.load, t.repetitions)
                    for t in rows
                ),
            )
            if context
            else None
        )
        self.task_grid.load_source(projected)
        self.headers = self.task_grid.headers
        self.task_ids = tuple(t.task_id for t in projected.tasks) if projected else ()
        if self.selected_task_id not in self.task_ids:
            self.selected_task_id = self.task_ids[0] if self.task_ids else None
        self.hidden_headers = tuple(self.task_grid.hidden_headers)
        self.inputs = [
            (
                cast(PrecisionLineEdit, row[0]),
                cast(PrecisionLineEdit, row[1]),
                cast(PrecisionLineEdit, row[2]),
            )
            for row in self.task_grid.inputs
        ]
        self.outputs = [
            cast(tuple[QLabel, QLabel, QLabel], row) for row in self.task_grid.outputs
        ]
        for inputs in self.inputs:
            for control, tip in zip(inputs, _INPUT_TIPS, strict=True):
                control.setToolTip(self._text(tip))
        system = context.view.system if context else self.presenter.system
        units = (
            ("in", "lb", "ft.lb")
            if system is MeasurementSystem.IMPERIAL
            else ("cm", "N", "N.m")
        )
        source = self.presenter.source()
        moment_unit = (
            "ft.lb"
            if source is None or source.system is MeasurementSystem.IMPERIAL
            else "N.m"
        )
        titles = (
            "Task #",
            "Lever Arm",
            "Load",
            "Moment",
            "Repetitions (per work day)",
            "Damage (cumulative)",
            "% Total (damage)",
        )
        for column, (label, title, tip) in enumerate(
            zip(self.headers, titles, _HEADER_TIPS, strict=True)
        ):
            text = self._text(title)
            if 1 <= column <= 3:
                text += f" ({moment_unit if column == 3 else units[column - 1]})"
            label.setText(text)
            self.hidden_headers[column].setText(text)
            label.setToolTip(self._text(tip))
        self.clear_button.setText(self._text("Clear assessment"))
        self.calculate_button.setText(self._text("Calculate"))
        for button, tip in (
            (
                self.clear_button,
                "Clear the active tool's task inputs and calculated results.",
            ),
            (
                self.calculate_button,
                "Calculate risk results from the task data currently shown.",
            ),
        ):
            button.setToolTip(self._text(tip))
        self.total_title.setText(self._text("Total Cumulative Damage:"))
        self.probability_title.setText(
            self._text("Probability of High Risk Job * (%):")
        )
        self.setEnabled(context is not None)
        self.show_result()
        self.task_grid.refresh_geometry()

    def _complete_cell(self, edit: AssessmentCellEdit) -> None:
        """Bind shared-grid completion to the existing presenter cell command.

        Args:
            edit: Exact completed display token and identity; the presenter retains
                parsing from the complete retained input projection.

        Returns:
            None; parsing, source conversion, validation and history stay in the host.
        """
        fields = self.task_grid.input_fields
        if edit.field in ("direction", "omni_res_scale"):
            self._mark_pending()
        self.commit_cell(edit.task_id, fields.index(edit.field) + 1)

    def _select_task(self, task_id: str) -> None:
        """Retain main-window row selection from the reusable grid's focus signal.

        Args:
            task_id: Stable currently displayed task identity.

        Returns:
            None; selecting a row does not modify source or history.
        """
        self.selected_task_id = task_id

    def _mark_pending(self) -> None:
        """Mark edited task text as pending and clear obsolete calculation display.

        Args:
            None.

        Returns:
            None.
        """
        self.pending = True
        self.presenter.evaluator.clear()
        self.show_result()
        self._invalidate()

    def input_rows(self) -> tuple[tuple[str, str, str, str], ...]:
        """Read widget values once without accepting edits or changing history.

        Args:
            None.

        Returns:
            Stable task identities and current displayed values in task order.
        """
        return tuple(
            (
                identity,
                editors[0].source_text(),
                editors[1].source_text(),
                editors[2].source_text(),
            )
            for identity, editors in zip(self.task_ids, self.inputs, strict=True)
        )

    def pending_change(self) -> bool | None:
        """Inspect valid pending input without committing or truncating Redo.

        Args:
            None.

        Returns:
            True for a valid changed source, including started incomplete tasks;
            False for no-op edits or no active source; None for invalid text or
            stale bindings, which must not be consumed by project replay.
        """
        if not self.pending or self.context is None:
            return False
        try:
            return (
                self.presenter.parse_grid(self.context, self.input_rows())
                != self.presenter.source()
            )
        except DraftError:
            return None

    def commit_cell(self, task_id: str, column: int) -> None:
        """Complete one input on focus departure, Enter or a selector change.

        Args:
            task_id: Stable task identity captured by the input's signal connection.
            column: One-based position in input_rows, excluding the task identity.

        Returns:
            None. Valid changed input is one existing source/history command, without
            rebuilding widgets. input_committed lets the host calculate; unfinished
            cells remain local. Invalid/stale input stays editable; projection loads
            disable completion before retiring focused controls.

        Raises:
            ValueError: Active source belongs to another tool or widget rows violate
                their typed projection contract; unexpected programmer errors surface.
        """
        if not self.pending or self.context is None:
            return
        try:
            changed = self.presenter.commit_grid(
                self.context, self.input_rows(), cell=(task_id, column)
            )
        except DraftError:
            return
        if changed:
            self.context = self.presenter.bind()
        self.pending = self.pending_change() is not False
        self.show_result()
        self._invalidate()
        if changed and not self.pending:
            self.input_committed.emit()

    def commit_inputs(self) -> bool:
        """Commit all text once; invalid input stays visible and source stays intact.

        Args:
            None.

        Returns:
            True when pending input changed the source; False when there is nothing to
            commit or values are unchanged.
        """
        if not self.pending or self.context is None:
            return False
        rows = self.input_rows()
        changed = self.presenter.commit_grid(self.context, rows)
        self.pending = False
        return changed

    def show_result(self) -> None:
        """Render only current complete results; clear stale row colors and totals.

        Args:
            None.

        Returns:
            None.
        """
        precision = (
            self.presenter.workspace.project_metadata.precision
            if self.presenter.workspace.project_metadata
            else DisplayPrecision()
        )
        self.summary.show_values("0.0", "0.0", None)
        for outputs in self.outputs:
            for label in outputs:
                label.setText("0.0")
                label.setStyleSheet("")
        result = self.presenter.evaluator.current(self.presenter.workspace.active)
        if result is None:
            historical = (
                None if self.pending else self.presenter.workspace.historical_result()
            )
            if historical is not None:
                show_historical_rows(self.outputs, historical, precision)
                self.summary.show_values(
                    historical_number(historical.damage, precision.damage),
                    historical_number(
                        historical.probability_percent, precision.probability
                    ),
                    historical_damage_color(historical),
                )
            return
        if not isinstance(result.summary, LifftSummary):
            return
        display = display_lifft_summary(result.summary, precision)
        self.summary.show_values(
            display.damage_text, display.probability_text, display.color
        )
        for outputs, task, share, color in zip(
            self.outputs,
            result.task_results,
            display.contribution_texts,
            display.task_colors,
            strict=True,
        ):
            assert isinstance(task, LifftTaskResult)
            outputs[0].setText(f"{task.displayed_moment:.{precision.moment}f}")
            outputs[1].setText(f"{task.cumulative_damage:.{precision.damage}f}")
            outputs[2].setText(share)
            if color:
                outputs[1].setStyleSheet("background-color: " + color)

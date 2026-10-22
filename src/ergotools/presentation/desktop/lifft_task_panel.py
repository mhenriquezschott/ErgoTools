"""Reviewed original seven-column LiFFT task controls for the integrated layout.

Ported from reference main.py setupLiFFTTab, sticky-header helpers and styling. Own only
widgets/pending text; the injected presenter owns edits and evaluation.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Callable, Mapping
from functools import partial

from PyQt5.QtCore import QEvent, QObject, QSize, Qt, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.settings import Language
from ergotools.domain.assessments.lifft import LifftTaskResult
from ergotools.domain.assessments.lifft_summary import LifftSummary
from ergotools.domain.assessments.validation import DraftError
from ergotools.domain.display_precision import DisplayPrecision
from ergotools.domain.model_units import MeasurementSystem
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
    "Open the task-data grid view for the active tool.": (
        "Abra la cuadrícula de datos de tareas de la herramienta activa."
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

    def __init__(
        self,
        presenter: LifftPresenter,
        icons: Mapping[str, QIcon],
        *,
        calculate: Callable[[], None],
        clear: Callable[[], None],
        select_context: Callable[[], None],
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
            select_context: Callback browsing saved assessments for the active
                worker/tool, without changing their workplace ownership.
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
        self._input_tasks: dict[QObject, str] = {}
        self._sync_scheduled = False
        self.setStyleSheet(MAIN_WORKSPACE_STYLE)
        layout = QVBoxLayout(self)
        self.header_widget = QWidget()
        self.header_grid = QGridLayout(self.header_widget)
        self.headers = tuple(QLabel() for _ in range(7))
        font = self.font()
        font.setBold(True)
        for column, label in enumerate(self.headers):
            label.setFont(font)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setWordWrap(True)
            label.setFixedHeight(42)
            self.header_grid.addWidget(label, 0, column)
        self.header = QScrollArea()
        self.header.setObjectName("stickyHeaderScroll")
        self.header_widget.setObjectName("stickyHeader")
        self.header.setFrameShape(QFrame.NoFrame)
        self.header.setWidgetResizable(False)
        self.header.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.header.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.header.setFixedHeight(42)
        self.header.setWidget(self.header_widget)
        layout.addWidget(self.header)
        self.body_scroll = QScrollArea()
        self.body_scroll.setWidgetResizable(True)
        self.frame = QFrame()
        frame_layout = QVBoxLayout(self.frame)
        self.grid = QGridLayout()
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        frame_layout.addLayout(self.grid)
        frame_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)
        self.body_scroll.setWidget(self.frame)
        body_bar = self.body_scroll.horizontalScrollBar()
        header_bar = self.header.horizontalScrollBar()
        assert body_bar is not None and header_bar is not None
        body_bar.valueChanged.connect(header_bar.setValue)
        viewport = self.body_scroll.viewport()
        assert viewport is not None
        viewport.installEventFilter(self)
        layout.addWidget(self.body_scroll, 1)
        self.summary = ToolResultSummary()
        self.total_title = self.summary.total_title
        self.total_value = self.summary.total_value
        self.probability_title = self.summary.probability_title
        self.probability_value = self.summary.probability_value
        layout.addLayout(self.summary)
        buttons = QHBoxLayout()
        self.clear_button = QPushButton()
        self.clear_button.setObjectName("clearAssessmentButton")
        self.clear_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.clear_button.setMinimumHeight(40)
        self.clear_button.setIcon(icons["delete"])
        self.clear_button.setIconSize(QSize(26, 26))
        self.clear_button.clicked.connect(clear)
        # Share the available width equally around the fixed-size chooser.
        buttons.addWidget(self.clear_button, 1)
        self.context_button = QPushButton()
        self.context_button.setIcon(icons["body_view"])
        self.context_button.setIconSize(QSize(30, 30))
        self.context_button.setFixedSize(40, 40)
        self.context_button.clicked.connect(select_context)
        buttons.addWidget(self.context_button)
        self.calculate_button = QPushButton()
        self.calculate_button.setObjectName("calculateButton")
        self.calculate_button.setMinimumHeight(40)
        self.calculate_button.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred
        )
        self.calculate_button.setIcon(icons["calculate_light"])
        self.calculate_button.setIconSize(QSize(28, 28))
        self.calculate_button.clicked.connect(calculate)
        buttons.addWidget(self.calculate_button, 1)
        layout.addLayout(buttons)

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
        # Retiring focused controls otherwise advance focus through the replacement
        # rows and make QScrollArea reveal the final task during Undo/Redo.
        focus = QApplication.focusWidget()
        if focus is not None and self.frame.isAncestorOf(focus):
            focus.clearFocus()
        self.context = context
        self.language = language
        self.pending = False
        self.inputs.clear()
        self._input_tasks.clear()
        self.outputs.clear()
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.hide()
                    widget.deleteLater()
        self.hidden_headers = tuple(QLabel() for _ in range(7))
        for column, label in enumerate(self.hidden_headers):
            label.setFont(self.headers[column].font())
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFixedHeight(0)
            self.grid.addWidget(label, 0, column)
        rows = context.view.tasks if context is not None else ()
        self.task_ids = tuple(t.task_id for t in rows)
        if self.selected_task_id not in self.task_ids:
            self.selected_task_id = self.task_ids[0] if self.task_ids else None
        for row, task in enumerate(rows):
            label = QLabel(str(row + 1))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(label, row + 1, 0)
            precision = (
                self.presenter.workspace.project_metadata.precision
                if self.presenter.workspace.project_metadata
                else DisplayPrecision()
            )
            assert context is not None
            assert context is not None
            inputs = (
                PrecisionLineEdit(task.lever_arm, context.convention, precision.inputs),
                PrecisionLineEdit(task.load, context.convention, precision.inputs),
                PrecisionLineEdit(task.repetitions, context.convention, 0),
            )
            for column, _field, editor, tip in zip(
                (1, 2, 4),
                ("lever_arm", "load", "repetitions"),
                inputs,
                _INPUT_TIPS,
                strict=True,
            ):
                assert context is not None
                # Compact text keeps exact unchanged values in PrecisionLineEdit.
                editor.setCursorPosition(0)
                editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
                editor.setToolTip(self._text(tip))
                editor.textEdited.connect(self._mark_pending)
                editor.editingFinished.connect(
                    partial(self.commit_cell, task.task_id, inputs.index(editor) + 1)
                )
                self._input_tasks[editor] = task.task_id
                editor.installEventFilter(self)
                self.grid.addWidget(editor, row + 1, column)
            self.inputs.append(inputs)
            outputs = (QLabel("0.0"), QLabel("0.0"), QLabel("0.0"))
            for column, output in zip((3, 5, 6), outputs, strict=True):
                output.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.grid.addWidget(output, row + 1, column)
            self.outputs.append(outputs)
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
            (self.context_button, "Open the task-data grid view for the active tool."),
        ):
            button.setToolTip(self._text(tip))
        self.total_title.setText(self._text("Total Cumulative Damage:"))
        self.probability_title.setText(
            self._text("Probability of High Risk Job * (%):")
        )
        self.setEnabled(context is not None)
        self.context_button.setEnabled(
            self.presenter.workspace.supports_assignment_history
        )
        self.show_result()
        self._schedule_sync()

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
            rebuilding widgets or saving/calculating. Other unfinished cells remain
            local. Invalid/stale completion is retained for correction; projection
            loads disable completion before retiring focused controls.

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

    def _schedule_sync(self) -> None:
        """Queue one sticky-header geometry synchronization.

        Queue one sticky-header geometry synchronization after the current Qt layout
        pass.

        Args:
            None.

        Returns:
            None.
        """
        if not self._sync_scheduled:
            self._sync_scheduled = True
            QTimer.singleShot(0, self._sync_header)

    def _sync_header(self) -> None:
        """Align fixed header labels to actual task-column widths.

        Align fixed header labels to actual task-column widths and scrollbar geometry.

        Header/body horizontal scrolling remains synchronized; no space padding or
        periodic refresh is used.

        Args:
            None.

        Returns:
            None.
        """
        self._sync_scheduled = False
        viewport = self.body_scroll.viewport()
        assert viewport is not None
        self.grid.activate()
        for column, label in enumerate(self.headers):
            item = self.grid.itemAtPosition(1, column)
            if item is not None and item.widget() is not None:
                widget = item.widget()
                assert widget is not None
                label.setFixedWidth(widget.width())
        header_viewport = self.header.viewport()
        assert header_viewport is not None
        margins = self.grid.contentsMargins()
        self.header_grid.setContentsMargins(
            margins.left(),
            margins.top(),
            margins.right() + header_viewport.width() - viewport.width(),
            margins.bottom(),
        )
        self.header_grid.setHorizontalSpacing(self.grid.horizontalSpacing())
        bar = self.body_scroll.horizontalScrollBar()
        assert bar is not None
        self.header_widget.setFixedWidth(header_viewport.width() + bar.maximum())
        self.header_widget.setFixedHeight(42)
        self.header_grid.activate()
        # Qt stylesheet polishing can replace fixed minima set during construction.
        for button in (
            self.clear_button,
            self.context_button,
            self.calculate_button,
        ):
            button.setFixedHeight(40)
        self.summary.align_to(self.outputs[0][1] if self.outputs else None, self)

    def eventFilter(self, watched: QObject | None, event: QEvent | None) -> bool:  # noqa: N802 - Qt override
        """Synchronize geometry after a viewport resize; no periodic refresh timer.

        Args:
            watched: QObject receiving the event; may be None in direct defensive calls.
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            True only when this filter explicitly consumes the event; otherwise the
            normal Qt base-filter result.
        """
        if (
            watched is not None
            and event is not None
            and event.type() == QEvent.Type.FocusIn
        ):
            self.selected_task_id = self._input_tasks.get(
                watched, self.selected_task_id
            )
        if event is not None and event.type() == QEvent.Type.Resize:
            self._schedule_sync()
        return super().eventFilter(watched, event)

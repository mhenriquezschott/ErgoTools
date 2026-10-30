"""Main DUET presenter binding for the shared assessment editor.

Presentation layer. The shared grid builds native inputs, fixed headers and scrolling;
the shared section composes totals/actions. This adapter retains DUET pending text,
selector acceptance, presenter validation and exact result display. No repository,
calculator implementation, duplicated task layout or separate history lives here.
"""

from collections.abc import Callable, Mapping
from typing import cast

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QComboBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.settings import Language
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.duet_summary import DuetSummary
from ergotools.domain.assessments.validation import DraftError, InputIssue
from ergotools.domain.display_precision import DisplayPrecision
from ergotools.presentation.desktop.assessment_controls import (
    OMNI_RATINGS,
)
from ergotools.presentation.desktop.assessment_editor_section import (
    AssessmentActionRow,
    AssessmentEditorSection,
)
from ergotools.presentation.desktop.assessment_task_grid import (
    AssessmentCellEdit,
    AssessmentTaskGrid,
)
from ergotools.presentation.desktop.duet_presenter import DuetEditContext, DuetPresenter
from ergotools.presentation.desktop.historical_result_display import (
    historical_damage_color,
    historical_number,
    show_historical_rows,
)
from ergotools.presentation.desktop.precision_editor import PrecisionLineEdit
from ergotools.presentation.desktop.theme.duet_summary import display_duet_summary
from ergotools.presentation.desktop.theme.main_workspace import MAIN_WORKSPACE_STYLE
from ergotools.presentation.desktop.tool_result_summary import ToolResultSummary

# Original task-column ordering with English/Spanish captions; units are supplied
# separately.
_HEADERS = (
    ("Task #", "Tarea #"),
    ("OMNI-Res Scale", "Escala OMNI-Res"),
    ("Repetitions (per work day)", "Repeticiones (por jornada laboral)"),
    ("Damage (cumulative)", "Daño (acumulado)"),
    ("% Total (damage)", "% Total (daño)"),
)
# Original dimensionless OMNI-Res scale 0-10 captions; blank entries intentionally match
# the reference.


class DuetTaskPanel(QWidget):
    """Own DUET widgets and pending input; the presenter owns source and history."""

    # Emitted only after a changed cell has completed validation/acceptance.
    input_committed = pyqtSignal()

    def __init__(
        self,
        presenter: DuetPresenter,
        icons: Mapping[str, QIcon],
        *,
        report_issue: Callable[[InputIssue], None],
        changed: Callable[[], None],
        clear: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Construct the reviewed original grid; do not open files or edit source.

        Args:
            presenter: Injected tool/workplace coordinator; owns parsing and source
                commands, not these widgets.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            report_issue: Callback displaying a typed validation issue while preserving
                the entered text.
            changed: Callback notifying the host after local edits/result state change.
            clear: Host-owned confirmation/clear callback; None uses the isolated
                panel source command, with confirmation owned by its caller.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        self.presenter = presenter
        self._report_issue = report_issue
        self._changed = changed
        self.language = Language.ENGLISH
        self.context: DuetEditContext | None = None
        self.pending = False
        self.inputs: list[tuple[QComboBox, PrecisionLineEdit]] = []
        self.outputs: list[tuple[QLabel, QLabel]] = []
        self.task_ids: tuple[str, ...] = ()
        self.setStyleSheet(MAIN_WORKSPACE_STYLE)
        layout = QVBoxLayout(self)
        self.task_grid = AssessmentTaskGrid(
            self.language,
            self.presenter.convention,
            kind=AssessmentKind.DUET,
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
        self.summary = ToolResultSummary()
        self.action_row = AssessmentActionRow(icons, tasks=True)
        self.clear_button = self.action_row.clear_button
        self.calculate_button = self.action_row.calculate_button
        assert self.action_row.add_task_button is not None
        assert self.action_row.remove_task_button is not None
        self.add_task_button = self.action_row.add_task_button
        self.remove_task_button = self.action_row.remove_task_button
        self.clear_button.clicked.connect(clear or self.clear_inputs)
        self.calculate_button.clicked.connect(self.calculate)
        self.editor_section = AssessmentEditorSection(
            self.task_grid, self.summary, self.action_row
        )
        layout.addWidget(self.editor_section, 1)
        self.translate()

    def translate(self) -> None:
        """Translate captions and rating descriptions without altering pending input.

        Args:
            None.

        Returns:
            None.
        """
        language = int(self.language is Language.SPANISH)
        for label, texts in zip(self.headers, _HEADERS, strict=True):
            label.setText(texts[language])
            label.setToolTip(texts[language])
        for combo, editor in self.inputs:
            combo.blockSignals(True)
            for index, texts in enumerate(OMNI_RATINGS):
                combo.setItemText(index, f"{index}: {texts[language]}")
            combo.blockSignals(False)
            combo.setToolTip(_HEADERS[1][language])
            editor.setToolTip(_HEADERS[2][language])
        self.clear_button.setText(("Clear assessment", "Limpiar evaluación")[language])
        self.calculate_button.setText(("Calculate", "Calcular")[language])
        self.clear_button.setToolTip(
            (
                "Clear DUET inputs and calculated results.",
                "Borre los datos y resultados DUET.",
            )[language]
        )
        self.calculate_button.setToolTip(
            (
                "Calculate DUET risk from the shown tasks.",
                "Calcule el riesgo DUET con las tareas mostradas.",
            )[language]
        )
        self.task_grid.refresh_geometry()

    def load_source(self, context: DuetEditContext | None) -> None:
        """Load a committed snapshot without triggering edits or recursive signals.

        Args:
            context: Exact source/display interpretation captured when the grid was
                bound; None clears the view.

        Returns:
            None.
        """
        # Discard only projection-local completion signals before retiring fields;
        # callers resolve drafts before intentional navigation or bulk acceptance.
        self.pending = False
        self.context = context
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
        projected = self.presenter.source() if context else None
        self.task_grid.load_source(projected)
        self.headers = self.task_grid.headers
        self.task_ids = tuple(t.task_id for t in projected.tasks) if projected else ()
        self.inputs = [
            (cast(QComboBox, row[0]), cast(PrecisionLineEdit, row[1]))
            for row in self.task_grid.inputs
        ]
        self.outputs = [
            cast(tuple[QLabel, QLabel], row) for row in self.task_grid.outputs
        ]
        self.setEnabled(context is not None)
        self.translate()
        self.show_result()

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
        self._changed()

    def input_rows(self) -> tuple[tuple[str, int | None, str], ...]:
        """Read widget values once without accepting edits or changing history.

        Args:
            None.

        Returns:
            Stable task identities and current displayed values in task order.
        """
        return tuple(
            (
                identity,
                combo.currentIndex() if combo.currentIndex() >= 0 else None,
                editor.source_text(),
            )
            for identity, (combo, editor) in zip(
                self.task_ids, self.inputs, strict=True
            )
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
        self._changed()
        if changed and not self.pending:
            self.input_committed.emit()

    def commit_inputs(self) -> bool:
        """Commit all inputs atomically; errors leave entered text and source intact.

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

    def calculate(self) -> None:
        """Commit and evaluate once; report rejected input without discarding it.

        Args:
            None.

        Returns:
            None.
        """
        try:
            if self.commit_inputs():
                self.context = self.presenter.bind()
            self.presenter.calculate()
        except DraftError as error:
            self._report_issue(error.issue)
            return
        self.show_result()
        self._changed()

    def clear_inputs(self) -> None:
        """Clear pending text using the reversible source command; caller owns consent.

        Args:
            None.

        Returns:
            None.
        """
        self.presenter.reset_grid()
        self.load_source(self.presenter.bind())
        self._changed()

    def show_result(self) -> None:
        """Apply current typed DUET row results or clear previous text and colors.

        Args:
            None.

        Returns:
            None.
        """
        self.summary.total_title.setText(
            "Daño Acumulado Total:"
            if self.language is Language.SPANISH
            else "Total Cumulative Damage:"
        )
        self.summary.probability_title.setText(
            "Probabilidad de Trastorno de Extremidad Superior Distal (%):"
            if self.language is Language.SPANISH
            else "Probability of Distal Upper Extremity Outcome (%):"
        )
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
        if not isinstance(result.summary, DuetSummary):
            return
        display = display_duet_summary(result.summary, precision)
        self.summary.show_values(
            display.damage_text, display.probability_text, display.color
        )
        for outputs, damage, share, color in zip(
            self.outputs,
            display.task_damage_texts,
            display.contribution_texts,
            display.task_colors,
            strict=True,
        ):
            outputs[0].setText(damage)
            outputs[1].setText(share)
            if color:
                outputs[0].setStyleSheet("background-color: " + color)

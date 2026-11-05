"""Job source binding for the reusable assessment task grid.

Presentation layer. The shared grid owns all controls, layout, headers and scrolling.
This adapter validates completed Job cells and emits immutable Job source replacements;
the host still owns calculation, project history and saving. Read-only copy previews
use the same grid without accepting edits. No SQL, calculator or separate history here.
"""

from collections.abc import Callable
from dataclasses import replace

from PyQt5.QtCore import QLocale, pyqtSignal
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QComboBox

from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.assessments.tst import TstDirection
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.job_risk import JobTaskResult
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.assessment_task_actions import AssessmentTaskActions
from ergotools.presentation.desktop.assessment_task_grid import (
    AssessmentCellEdit,
    AssessmentTaskGrid,
)
from ergotools.presentation.desktop.precision_editor import PrecisionLineEdit
from ergotools.presentation.numeric_input import parse_input_number


class JobTaskEditor(AssessmentTaskGrid):
    """Accept Job edits while reusing all assessment-grid presentation.

    Attributes:
        source_edited: Numeric/selector source edits; shared actions use the guarded
            callback to report actual persistence acceptance.
    """

    source_edited = pyqtSignal(object)
    # Optional explicit binding; standalone read-only grids have no project callbacks.
    task_actions: AssessmentTaskActions | None = None
    # Guarded host acceptance for shared actions; ordinary numeric signals remain.
    _accept_edit: Callable[[AssessmentDraft, str], bool] | None = None

    def configure_task_actions(
        self,
        workspace: ProjectWorkspace[AssessmentDraft],
        *,
        accept: Callable[[AssessmentDraft, str], bool],
    ) -> None:
        """Attach source/catalog acceptance without introducing another history stack.

        Args:
            workspace: Borrowed active project owner used by the Job Management host.
            accept: Source/operation acceptance reporting host persistence success.

        Returns:
            None; configuration creates no task definitions or project data.
        """
        self._accept_edit = accept
        self.task_actions = AssessmentTaskActions(
            self,
            source=lambda: self.source,
            accept=self._accept_shared_source,
            accept_paste=workspace.accept_task_paste,
            definitions=workspace.load_task_definitions,
            replace_definitions=workspace.replace_task_definitions,
            before_action=self.accept_pending,
            system=self._input_system,
            convention=lambda: self.convention,
        )
        self.task_actions.bind_catalog(workspace.editing)

    def _input_system(self) -> MeasurementSystem:
        """Return actual visible Job arm/load units for clipboard confirmation.

        Args:
            None.

        Returns:
            Recorded dimensional source units, otherwise the empty-grid unit choice.
        """
        return (
            self.source.system
            if isinstance(self.source, (LifftDraft, TstDraft))
            else self.system
        )

    def _accept_shared_source(
        self,
        expected: AssessmentDraft,
        replacement: AssessmentDraft,
        label: str,
        rebuild: bool,
    ) -> bool:
        """Accept a prepared source through the guarded calculation/history host.

        Args:
            expected: Exact canonical source captured before preparation.
            replacement: Complete validated same-tool source in recorded units.
            label: Operation identity; the Job host owns its shared edit boundary.
            rebuild: True when a clipboard batch may add rows.

        Returns:
            True only when a current source changed; stale previews do nothing.
        """
        if self.source != expected or replacement == expected:
            return False
        if self._accept_edit is None or not self._accept_edit(replacement, label):
            return False
        if rebuild:
            self.load_source(replacement, self.result_rows)
        else:
            self.source = replacement
        return True

    def load_source(
        self,
        source: AssessmentDraft | None,
        results: tuple[JobTaskResult, ...] = (),
    ) -> None:
        """Bind exact Job values and install their established numeric validation.

        Args:
            source: Independent Job or read-only copy source; None clears the grid.
            results: Exact matching outputs, never recalculated here.

        Returns:
            None; input construction never accepts edits or creates history.
        """
        if self.task_actions is not None:
            self.task_definitions = self.task_actions.definitions()
        super().load_source(source, results)
        for row in self.inputs:
            for control in row:
                if isinstance(control, PrecisionLineEdit):
                    validator = QDoubleValidator(0, 1e12, 12, control)
                    locale = QLocale(
                        "de_DE"
                        if self.convention is DecimalConvention.COMMA
                        else "en_US"
                    )
                    locale.setNumberOptions(QLocale.RejectGroupSeparator)
                    validator.setLocale(locale)
                    control.setValidator(validator)
        if not self.property("jobCellBinding"):
            self.cell_finished.connect(self._accept_cell)
            self.setProperty("jobCellBinding", True)

    def _accept_cell(self, edit: AssessmentCellEdit) -> None:
        """Route a completed shared-grid cell through Job source acceptance.

        Args:
            edit: Exact task/field/value intent emitted by the shared grid; the binding
                retains its numeric validator and source-text parsing policy.

        Returns:
            None; invalid or unchanged text retains the established no-edit behavior.
        """
        if self.source is None:
            return
        task_id, field = edit.task_id, edit.field
        row = next(
            i
            for i in range(len(self.source.tasks))
            if self.source.tasks[i].task_id == task_id
        )
        fields = self.input_fields
        control = self.inputs[row][fields.index(field)]
        if isinstance(control, PrecisionLineEdit):
            self._number_changed(row, field, control)
        else:
            self._selector_changed(row, field, control)

    def _number_changed(self, row: int, field: str, editor: PrecisionLineEdit) -> None:
        """Accept one valid completed input without sweeping unfinished sibling cells.

        Args:
            row: Stable current zero-based task position.
            field: Numeric source field owned by this editor.
            editor: Exact precision-preserving editor finishing its cell.

        Returns:
            None; invalid text stays visible and emits no accepted source/history edit.
        """
        source = self.source
        if (
            self.read_only
            or source is None
            or (not editor.hasAcceptableInput() and editor.text().strip())
        ):
            return
        value = parse_input_number(
            editor.source_text(), self.convention, field, source.tasks[row].task_id
        )
        if isinstance(source, DuetDraft):
            tasks = list(source.tasks)
            tasks[row] = replace(tasks[row], repetitions=value)
            updated: AssessmentDraft = replace(source, tasks=tuple(tasks))
        elif isinstance(source, LifftDraft):
            items = list(source.tasks)
            task = items[row]
            items[row] = (
                replace(task, repetitions=value)
                if field == "repetitions"
                else replace(task, lever_arm=value)
                if field == "lever_arm"
                else replace(task, load=value)
            )
            updated = replace(source, tasks=tuple(items))
        else:
            shoulders = list(source.tasks)
            task_st = shoulders[row]
            shoulders[row] = (
                replace(task_st, repetitions=value)
                if field == "repetitions"
                else replace(task_st, lever_arm=value)
                if field == "lever_arm"
                else replace(task_st, load=value)
            )
            updated = replace(source, tasks=tuple(shoulders))
        self._emit_source(updated)

    def _selector_changed(self, row: int, field: str, combo: QComboBox) -> None:
        """Accept only the selected scale/direction, preserving all other source fields.

        Args:
            row: Current zero-based task position.
            field: Selector identity, used to distinguish stored enum/scales.
            combo: Native selector carrying literal typed item data.

        Returns:
            None; unchanged choices produce no source/history edit.
        """
        source = self.source
        if self.read_only:
            return
        if field == "omni_res_scale" and isinstance(source, DuetDraft):
            tasks = list(source.tasks)
            tasks[row] = replace(tasks[row], omni_res_scale=int(combo.currentData()))
            self._emit_source(replace(source, tasks=tuple(tasks)))
        elif isinstance(source, TstDraft):
            shoulders = list(source.tasks)
            shoulders[row] = replace(
                shoulders[row], direction=TstDirection(combo.currentData())
            )
            self._emit_source(replace(source, tasks=tuple(shoulders)))

    def _emit_source(self, source: AssessmentDraft) -> None:
        """Update the local baseline before notifying its persistence-owning parent.

        Args:
            source: Validated replacement source for one completed cell.

        Returns:
            None; no-op edits never add history entries.
        """
        if source != self.source:
            self.source = source
            self.source_edited.emit(source)

    def accept_pending(self) -> bool:
        """Accept each valid unfinished numeric cell before a parent action.

        Args:
            None.

        Returns:
            False when any numeric editor is invalid, retaining its text for correction.
            Each valid changed cell remains its own shared history action.
        """
        if self.task_actions is not None:
            self.task_actions.finish_names()
        for row, controls in enumerate(self.inputs):
            fields = self.input_fields
            for field, control in zip(fields, controls, strict=True):
                if isinstance(control, PrecisionLineEdit):
                    if control.text().strip() and not control.hasAcceptableInput():
                        control.setFocus()
                        return False
                    self._number_changed(row, field, control)
        return True

    def has_pending(self) -> bool:
        """Detect unfinished numeric changes without accepting or rounding them.

        Args:
            None.

        Returns:
            True when an editor differs from the current source, including invalid text
            that must be corrected before shared history can replay.
        """
        if self.task_actions is not None and self.task_actions.pending_names():
            return True
        source = self.source
        if source is None:
            return False
        for row, controls in enumerate(self.inputs):
            fields = self.input_fields
            for field, control in zip(fields, controls, strict=True):
                if isinstance(control, PrecisionLineEdit):
                    if control.text().strip() and not control.hasAcceptableInput():
                        return True
                    value = parse_input_number(
                        control.source_text(),
                        self.convention,
                        field,
                        source.tasks[row].task_id,
                    )
                    if value != getattr(source.tasks[row], field):
                        return True
        return False

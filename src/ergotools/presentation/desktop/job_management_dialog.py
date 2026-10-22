"""Job details and a single current LiFFT/DUET/ST risk set with compact calculators.

Presentation layer. Preserve Job browsing/workplace controls while replacing the
profile/evidence workflow. Sources/results, direct edits and copied worker tasks use
existing workspace transactions and shared history. One main Save publishes; no SQL,
scientific formulas, ownership linking or nested calculator window occurs here.
"""

import logging
from collections.abc import Callable, Mapping
from dataclasses import replace

from PyQt5.QtCore import QEvent, QLocale, QSignalBlocker, QSize, Qt
from PyQt5.QtGui import QCloseEvent, QIcon
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.job_calculation import (
    blank_job_source,
    calculate_job_measurement,
    resize_job_source,
)
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.settings import Language
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    task_has_data,
)
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.job_catalog import Job
from ergotools.domain.job_risk import JobRiskMeasurement, JobRiskValues
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.job_assessment_dialog import JobAssessmentDialog
from ergotools.presentation.desktop.job_risk_table import JobRiskTable
from ergotools.presentation.desktop.job_task_editor import JobTaskEditor
from ergotools.presentation.desktop.job_workplace_host import JobWorkplaceHost
from ergotools.presentation.desktop.project_history_actions import ProjectHistoryActions
from ergotools.presentation.desktop.text import (
    job_management_error,
    job_management_text,
)
from ergotools.presentation.desktop.theme.job_management import JOB_MANAGEMENT_STYLE


class JobManagementDialog(QDialog):
    """Own current Job forms and project-history adapters, never a local Undo stack."""

    def __init__(
        self,
        workspace: ProjectWorkspace[AssessmentDraft],
        icons: Mapping[str, QIcon],
        system: MeasurementSystem,
        *,
        language: Language = Language.ENGLISH,
        convention: DecimalConvention = DecimalConvention.POINT,
        selected_job: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Bind Job editing to explicit project/unit/language owners.

        Args:
            workspace: Borrowed open project with current risk persistence capability.
            icons: Existing processed application assets.
            system: Default units for new calculator sources; copied units are retained.
            language: UI language, independent of numeric conventions.
            convention: Application decimal separator for every editable numeric field.
            selected_job: Existing exact Job identity to initially select, or None.
            parent: Owning main window; this modal does not own the workspace.

        Returns:
            None; construction creates no Job, risk values or calculator task source.
        """
        super().__init__(parent)
        self._workspace = workspace
        self._icons = icons
        self._system = system
        self._language = language
        self._convention = convention
        self._accepting_job = True
        self._busy = False
        self._loaded_job_id: str | None = None
        self._job_baseline: tuple[str, ...] = ()
        self._values = JobRiskValues("draft")
        self.project_history: ProjectHistoryActions | None = None
        self._jobs = workspace.read_jobs()
        self._risk = workspace.read_job_risk()
        self._workplaces = JobWorkplaceHost(workspace, icons, parent=self)
        self._preferred_shift: str | None = None
        if language is Language.SPANISH:
            self.setLocale(QLocale("es_CL"))
        self.setObjectName("jobWindow")
        self.setWindowTitle(self._text("Job Management"))
        self.setWindowIcon(icons["job_management"])
        self.setStyleSheet(JOB_MANAGEMENT_STYLE)
        self._collapsed_height = 680
        self.setMinimumSize(1040, 620)
        self.resize(1200, self._collapsed_height)
        self._setup_ui()
        self._translate_controls()
        self._reload_jobs(selected_job)
        self._accepting_job = False
        if workspace.editing is not None:
            self.save_button.hide()
            self.project_history = ProjectHistoryActions(
                self,
                workspace.editing,
                icons,
                language,
                prepare=self.accept_pending_job,
                restored=self.restore_project_jobs,
                pending=self._pending_label,
            )
            self.title_row.addStretch(1)
            self.title_row.addWidget(self.project_history.undo_button)
            self.title_row.addWidget(self.project_history.redo_button)
            self.job_name_input.textEdited.connect(self.project_history.refresh)
            self.job_description_input.textChanged.connect(self.project_history.refresh)
            self.risk_table.pending_input_changed.connect(self.project_history.refresh)
            self._watch_task_edits()

    def tr_text(self, english: str, spanish: str) -> str:
        """Select UI wording without interpreting stored user values.

        Args:
            english: English control/help text.
            spanish: Spanish control/help text.

        Returns:
            Current interface wording, never a stored identity.
        """
        return spanish if self._language is Language.SPANISH else english

    def _translate_controls(self) -> None:
        """Translate the existing Job details/browser labels in place.

        Args:
            None.

        Returns:
            None; numeric conventions and literal Job fields remain unchanged.
        """
        for label in self.findChildren(QLabel):
            label.setText(self._text(label.text()))
        for button in self.findChildren(QPushButton):
            button.setText(self._text(button.text()))
            button.setToolTip(self._text(button.toolTip()))
        self.job_id_combo.setToolTip(self._text(self.job_id_combo.toolTip()))
        self.job_name_input.setToolTip(self._text(self.job_name_input.toolTip()))
        self.job_description_input.setPlaceholderText(
            self._text("Optional job description")
        )

    def _job_values(self) -> tuple[str, ...]:
        """Read exact visible metadata/direct values without creating records.

        Args:
            None.

        Returns:
            Form tokens for pending-change detection; source grids have their own cell
            baseline and remain independent of rounded output displays.
        """
        return (
            self.job_id_combo.currentText(),
            self.job_name_input.text(),
            self.job_description_input.toPlainText(),
            *(
                self.risk_table._cell(row, col).text()
                for row in range(3)
                for col in (1, 2)
            ),
        )

    def _pending_label(self) -> str | None:
        """Expose pending metadata/input edits to the same shared project cursor.

        Args:
            None.

        Returns:
            A stable action label for valid unfinished work, otherwise None.
        """
        if self._accepting_job or not self.job_id_combo.currentText().strip():
            return None
        return (
            "save_job_details"
            if self._job_values() != self._job_baseline
            or self.risk_table.has_pending()
            or any(editor.has_pending() for editor in self.editors.values())
            else None
        )

    def _accept_from_signal(self) -> None:
        """Accept completed existing Job metadata without rebuilding task widgets.

        Args:
            None.

        Returns:
            None; invalid input remains available with a localized diagnostic.
        """
        if not self._accepting_job and self._loaded_job_id is not None:
            self.accept_pending_job()

    def eventFilter(self, watched: object, event: QEvent | None) -> bool:  # noqa: N802 — Qt override
        """Accept description edits on focus departure without a separate Save.

        Args:
            watched: Qt sender; only the owned description editor is handled.
            event: Native focus/other event forwarded by Qt.

        Returns:
            False; native text editing and focus behavior remain intact.
        """
        if (
            watched is self.job_description_input
            and event is not None
            and event.type() == QEvent.Type.FocusOut
        ):
            self._accept_from_signal()
        return False

    def accept_pending_job(self) -> bool:
        """Accept valid cells and metadata privately; only main Save publishes them.

        Args:
            None.

        Returns:
            True for accepted/unchanged forms; False retains invalid entries for retry.
            Each already completed task cell has its own shared history step.
        """
        if self._accepting_job:
            return True
        if not self.risk_table.accept_pending():
            return False
        for editor in self.editors.values():
            if not editor.accept_pending():
                return False
        if not self.job_id_combo.currentText().strip():
            has_tasks = any(
                item.source is not None
                and any(task_has_data(task) for task in item.source.tasks)
                for item in self._values.measurements
            )
            if self._job_values() != self._job_baseline or has_tasks:
                self.job_id_combo.setFocus()
                self._warning(
                    self._text("Validation Error"),
                    self.tr_text(
                        "Enter a Job ID before accepting these values.",
                        "Ingrese un ID del trabajo antes de aceptar estos valores.",
                    ),
                )
                return False
            return True
        if self._job_values() == self._job_baseline:
            return True
        self._accepting_job = True
        try:
            self._save_form()
            return True
        except (ValueError, OSError, RuntimeError) as error:
            self._warning(
                self._text("Validation Error"),
                job_management_error(str(error), self._language),
            )
            return False
        finally:
            self._accepting_job = False

    def _save_form(self) -> None:
        """Write one accepted form through existing guarded workspace operations.

        Args:
            None.

        Returns:
            None; refresh issued authorities while leaving live task widgets intact.
        """
        identity = self.job_id_combo.currentText().strip()
        existing = next(
            (job for job in self._jobs.jobs.jobs if job.job_id == identity), None
        )
        job = (
            replace(
                existing,
                name=self.job_name_input.text(),
                description=self.job_description_input.toPlainText(),
            )
            if existing is not None
            else Job(
                identity,
                self.job_name_input.text(),
                description=self.job_description_input.toPlainText(),
            )
        )
        values = JobRiskValues(identity, self.risk_table.measurements())
        self._jobs, self._risk = self._workspace.save_job_details(
            self._jobs, self._risk, job, values
        )
        self._values = self._risk.risk.for_job(identity)
        self._loaded_job_id = identity
        if self.job_id_combo.findText(identity) < 0:
            with QSignalBlocker(self.job_id_combo):
                self.job_id_combo.addItem(identity)
                self.job_id_combo.setCurrentIndex(self.job_id_combo.findText(identity))
        self._job_baseline = self._job_values()
        self._navigation(True)
        self._workplace_count()
        if self.project_history is not None:
            self.project_history.refresh()

    def restore_project_jobs(self) -> None:
        """Rebind current Job sources/results after shared project Undo/Redo.

        Args:
            None.

        Returns:
            None; retain selected tool/expanded calculator and surviving Job identity.
        """
        self._accepting_job = True
        try:
            selected = self._loaded_job_id
            self._jobs = self._workspace.read_jobs()
            self._risk = self._workspace.read_job_risk()
            self._reload_jobs(selected)
        finally:
            self._accepting_job = False

    def _reload_jobs(self, selected_job: str | None = None) -> None:
        """Rebuild Job identities from accepted values under a signal guard.

        Args:
            selected_job: Preferred surviving Job identity, or None for the first Job.

        Returns:
            None; no accepted source is recalculated or replaced.
        """
        previous = self._accepting_job
        self._accepting_job = True
        try:
            with QSignalBlocker(self.job_id_combo):
                self.job_id_combo.clear()
                self.job_id_combo.addItems([job.job_id for job in self._jobs.jobs.jobs])
                index = self.job_id_combo.findText(selected_job or "")
                self.job_id_combo.setCurrentIndex(index if index >= 0 else 0)
            self._show_job()
        finally:
            self._accepting_job = previous

    def _show_job(self) -> None:
        """Project one real Job or an empty form without manufacturing risk records.

        Args:
            None.

        Returns:
            None; calculator inputs are rebound only during navigation/replay.
        """
        identity = self.job_id_combo.currentText()
        job = next(
            (item for item in self._jobs.jobs.jobs if item.job_id == identity), None
        )
        self._loaded_job_id = job.job_id if job else None
        self.job_name_input.setText(job.name if job else "")
        self.job_description_input.setPlainText((job.description or "") if job else "")
        self._values = (
            self._risk.risk.for_job(identity) if identity else JobRiskValues("draft")
        )
        self.risk_table.load(self._values.measurements)
        for kind, editor in self.editors.items():
            item = next((m for m in self._values.measurements if m.kind is kind), None)
            editor.load_source(
                item.source if item else None, item.task_results if item else ()
            )
        self._watch_task_edits()
        self._tool_changed()
        self._identity_availability()
        self._navigation(job is not None)
        self._workplace_count()
        self._job_baseline = self._job_values()

    @property
    def selected_job_id(self) -> str | None:
        """Expose only real loaded Job identity for main-window selection memory.

        Args:
            None.

        Returns:
            Existing exact Job ID, or None for an unaccepted new form.
        """
        return (
            self._loaded_job_id
            if self.job_id_combo.currentText() == self._loaded_job_id
            else None
        )

    def _watch_task_edits(self, kind: AssessmentKind | None = None) -> None:
        """Refresh shared Undo availability while typing in each newly bound input.

        Args:
            kind: Rebound tool, or None for all tools during initial window setup.

        Returns:
            None; only new controls are connected, preventing duplicate subscriptions.
        """
        if self.project_history is None:
            return
        for tool, editor in self.editors.items():
            if kind is not None and tool is not kind:
                continue
            for controls in editor.inputs:
                for field in controls:
                    if isinstance(field, QLineEdit) and not field.property(
                        "jobHistoryWatched"
                    ):
                        field.textEdited.connect(self.project_history.refresh)
                        field.setProperty("jobHistoryWatched", True)

    def _kind(self) -> AssessmentKind:
        """Resolve the selected calculator tab using stable tool order.

        Args:
            None.

        Returns:
            LiFFT, DUET or ST enum, never a translated tab caption.
        """
        return (AssessmentKind.LIFFT, AssessmentKind.DUET, AssessmentKind.TST)[
            self.tool_tabs.currentIndex()
        ]

    def _measurement(self, kind: AssessmentKind) -> JobRiskMeasurement:
        """Return current form state for one tool, preserving missing-versus-zero.

        Args:
            kind: Exact tool identity.

        Returns:
            Existing form measurement or a nonpersisted empty tool value.
        """
        return next(
            (m for m in self._values.measurements if m.kind is kind),
            JobRiskMeasurement(kind),
        )

    def _identity_availability(self) -> None:
        """Enable risk entry only after a real proposed Job identity is present.

        Args:
            None.

        Returns:
            None; existing values remain intact if an ID is cleared, and acceptance
            requires restoring an ID rather than silently discarding entered tasks.
        """
        enabled = bool(self.job_id_combo.currentText().strip())
        self.risk_table.setEnabled(enabled)
        self.calculator_toggle.setEnabled(enabled)
        self.calculator_area.setEnabled(enabled)

    def _calculator_visibility_changed(self, expanded: bool) -> None:
        """Give expanded task controls room and restore the prior compact Job height.

        Args:
            expanded: Explicit calculator disclosure state chosen by the user.

        Returns:
            None; preserve width, task data and history while keeping summary/bottom
            controls fully visible. Collapsed details do not leave a large empty pane.
        """
        if expanded:
            self._collapsed_height = self.height()
            self.calculator_area.setVisible(True)
            self.setMinimumHeight(860)
            self.resize(self.width(), max(920, self.height()))
        else:
            self.calculator_area.setVisible(False)
            self.setMinimumHeight(620)
            self.resize(self.width(), max(620, self._collapsed_height))

    def _tool_changed(self) -> None:
        """Project mode/task capacity without saving or creating default task sources.

        Args:
            None.

        Returns:
            None; only explicitly selected calculation mode creates one blank task.
        """
        item = self._measurement(self._kind())
        with QSignalBlocker(self.mode_combo):
            self.mode_combo.setCurrentIndex(1 if item.source is not None else 0)
        count = len(item.source.tasks) if item.source is not None else 0
        self.tool_status.setText(
            self.tr_text(
                (
                    "Tasks: {count}. Inputs retain their recorded units; "
                    "calculated values are read-only in the summary."
                ),
                (
                    "Tareas: {count}. Se conservan las unidades originales; los "
                    "valores calculados son de solo lectura en el resumen."
                ),
            ).format(count=count)
        )
        self.add_task_button.setEnabled(0 < count < 100)
        self.remove_task_button.setEnabled(count > 1)
        self.calculate_button.setEnabled(count > 0)

    def _set_measurement(
        self, item: JobRiskMeasurement, *, rebind: bool = True
    ) -> None:
        """Accept one tool mutation while preserving other tools and worker sources.

        Args:
            item: Proposed source/current output for one tool.
            rebind: False for a completed cell, keeping sibling widgets and native Undo.

        Returns:
            None; the workspace owns one atomic shared project history action.
        """
        values = tuple(m for m in self._values.measurements if m.kind is not item.kind)
        self._values = JobRiskValues(
            self.job_id_combo.currentText().strip() or "draft", (*values, item)
        )
        self.risk_table.load(self._values.measurements)
        if rebind:
            self.editors[item.kind].load_source(item.source, item.task_results)
            self._watch_task_edits(item.kind)
        self.editors[item.kind].show_results(item.task_results)
        self._tool_changed()
        if self.job_id_combo.currentText().strip():
            self._save_form()

    def _source_changed(self, kind: AssessmentKind, source: object) -> None:
        """Invalidate the selected tool's output for one accepted task input change.

        Args:
            kind: Explicit edited tool identity.
            source: Immutable source emitted by the owned numeric/selector grid.

        Returns:
            None; other tools and unrelated unfinished inputs are not swept into it.
        """
        if isinstance(source, (LifftDraft, DuetDraft, TstDraft)):
            self._run(
                lambda: self._set_measurement(
                    JobRiskMeasurement(
                        kind, unit=self._measurement(kind).unit, source=source
                    ),
                    rebind=False,
                )
            )

    def _manual_changed(self) -> None:
        """Accept one completed direct risk edit through the same shared history.

        Args:
            None.

        Returns:
            None; invalid table input remains visible for correction/retry.
        """
        if not self._accepting_job and self.job_id_combo.currentText().strip():
            self._run(self._save_form)

    def _mode_changed(self) -> None:
        """Switch source method explicitly; retained tasks require discard consent.

        Args:
            None.

        Returns:
            None; Cancel restores the prior mode and all existing tasks/results.
        """
        if self._accepting_job:
            return
        item = self._measurement(self._kind())
        if self.mode_combo.currentIndex() == 1 and item.source is None:
            if (
                item.complete
                and self._question(
                    self._text("Confirm Deletion"),
                    self.tr_text(
                        "Start task calculation and replace this tool's direct values? "
                        "Undo can restore them.",
                        "¿Calcular con tareas y reemplazar los valores directos? "
                        "Deshacer permite restaurarlos.",
                    ),
                )
                != QMessageBox.Yes
            ):
                self._tool_changed()
                return
            self._run(
                lambda: self._set_measurement(
                    JobRiskMeasurement(
                        item.kind, source=blank_job_source(item.kind, self._system)
                    )
                )
            )
        elif self.mode_combo.currentIndex() == 0 and item.source is not None:
            if (
                self._question(
                    self._text("Confirm Deletion"),
                    self.tr_text(
                        (
                            "Use direct values and remove this tool's stored tasks? "
                            "Undo "
                            "can restore them."
                        ),
                        (
                            "¿Usar valores directos y quitar las tareas guardadas? "
                            "Deshacer permite restaurarlas."
                        ),
                    ),
                )
                != QMessageBox.Yes
            ):
                self._tool_changed()
                return
            self._run(
                lambda: self._set_measurement(
                    replace(item, source=None, task_results=())
                )
            )

    def add_task(self) -> None:
        """Append one blank task, preserving existing inputs and invalidating outputs.

        Args:
            None.

        Returns:
            None; task capacity is limited to 100 independently per Job/tool.
        """
        if not self.accept_pending_job():
            return
        item = self._measurement(self._kind())
        source = item.source
        if source is not None:
            self._run(
                lambda: self._set_measurement(
                    replace(
                        item,
                        source=resize_job_source(source),
                        cumulative_damage=None,
                        probability_percent=None,
                        task_results=(),
                    )
                )
            )

    def remove_task(self) -> None:
        """Remove the selected task after warning when it contains entered values.

        Args:
            None.

        Returns:
            None; at least one task remains, and shared Undo restores removed data.
        """
        if not self.accept_pending_job():
            return
        item = self._measurement(self._kind())
        source = item.source
        row = self.editors[item.kind].currentRow()
        if source is None or len(source.tasks) <= 1 or row < 0:
            return
        if (
            task_has_data(source.tasks[row])
            and self._question(
                self._text("Confirm Deletion"),
                self.tr_text(
                    "Remove the selected task and its inputs? Undo can restore it.",
                    (
                        "¿Quitar la tarea seleccionada y sus datos? Deshacer permite "
                        "restaurarla."
                    ),
                ),
            )
            != QMessageBox.Yes
        ):
            return
        self._run(
            lambda: self._set_measurement(
                replace(
                    item,
                    source=resize_job_source(source, remove=row),
                    cumulative_damage=None,
                    probability_percent=None,
                    task_results=(),
                )
            )
        )

    def clear_tool(self) -> None:
        """Clear only the selected tool after consent, retaining the other two tools.

        Args:
            None.

        Returns:
            None; calculation mode returns to one blank task; shared Undo restores all.
        """
        item = self._measurement(self._kind())
        if (
            self._question(
                self._text("Confirm Deletion"),
                self.tr_text(
                    "Clear this tool's tasks and values? Undo can restore them.",
                    (
                        "¿Limpiar las tareas y valores de esta herramienta? Deshacer "
                        "permite restaurarlos."
                    ),
                ),
            )
            != QMessageBox.Yes
        ):
            return
        source = (
            blank_job_source(
                item.kind,
                item.source.system
                if isinstance(item.source, (LifftDraft, TstDraft))
                else self._system,
            )
            if item.source is not None
            else None
        )
        self._run(
            lambda: self._set_measurement(JobRiskMeasurement(item.kind, source=source))
        )

    def calculate_tool(self) -> None:
        """Calculate only the selected tool through the shared scientific evaluator.

        Args:
            None.

        Returns:
            None; incomplete/invalid input cannot publish fabricated risk values.
        """
        if not self.accept_pending_job():
            return
        item = self._measurement(self._kind())
        source = item.source
        if source is not None:
            self._run(
                lambda: self._set_measurement(
                    calculate_job_measurement(
                        self._jobs.jobs.project_id,
                        self.job_id_combo.currentText().strip(),
                        source,
                        self._system,
                    ),
                    rebind=False,
                )
            )

    def copy_worker_assessment(self) -> None:
        """Copy exact tasks/results from a selected worker without creating a link.

        Args:
            None.

        Returns:
            None; Cancel preserves the Job; one accepted copy is one shared Undo action.
        """
        if not self.accept_pending_job() or not self.job_id_combo.currentText().strip():
            return
        dialog = JobAssessmentDialog(
            self._workspace,
            self._kind(),
            self._icons,
            self._language,
            self,
            convention=self._convention,
        )
        try:
            if dialog.exec() != QDialog.Accepted or dialog.selected is None:
                return
            previous = self._measurement(self._kind())
            if (previous.complete or previous.source is not None) and self._question(
                self._text("Confirm Deletion"),
                self.tr_text(
                    (
                        "Replace this tool's tasks and values with the selected "
                        "worker calculation? Undo can restore the previous data."
                    ),
                    (
                        "¿Reemplazar las tareas y valores con el cálculo del "
                        "trabajador? Deshacer permite restaurar los datos anteriores."
                    ),
                ),
            ) != QMessageBox.Yes:
                return
            self._jobs = self._workspace.read_jobs()
            self._risk = self._workspace.read_job_risk()
            selected = dialog.selected
            self._run(lambda: self._set_measurement(selected))
            self.calculator_toggle.setChecked(True)
        finally:
            dialog.close()
            dialog.deleteLater()
            self._jobs = self._workspace.read_jobs()
            self._risk = self._workspace.read_job_risk()

    def _workplace_count(self) -> None:
        """Count active placements for a real Job, independently of risk completeness.

        Args:
            None.

        Returns:
            None; an accepted Job may be placed before any tool has calculated values.
        """
        identity = self.job_id_combo.currentText().strip()
        count = sum(
            p.active and p.job_id == identity for p in self._jobs.jobs.placements
        )
        self.workplaces_button.setText(
            self._text("Workplaces ({count})").format(count=count)
        )
        self.workplaces_button.setEnabled(bool(identity))

    def new_job(self) -> None:
        """Accept the current form and prepare another Job without an extra Save.

        Args:
            None.

        Returns:
            None; empty defaults alone do not insert records.
        """
        if not self.accept_pending_job():
            return
        self._accepting_job = True
        try:
            with QSignalBlocker(self.job_id_combo):
                self.job_id_combo.setCurrentIndex(-1)
                self.job_id_combo.setEditText("")
            self._show_job()
            self.job_id_combo.setFocus()
        finally:
            self._accepting_job = False

    def save_job(self) -> None:
        """Accept current form through the diagnostic Save/normal private write path.

        Args:
            None.

        Returns:
            None; the integrated Save button is hidden and only main Save publishes.
        """
        self._run(self._save_form)

    def discard_changes(self) -> None:
        """Discard only unaccepted form text, preserving already shared accepted edits.

        Args:
            None.

        Returns:
            None; accepted operations are reverted using the shared Undo controls.
        """
        self._accepting_job = True
        try:
            self._show_job()
        finally:
            self._accepting_job = False

    def _setup_ui(self) -> None:
        """Retain the reference panel hierarchy, controls, margins and spacing.

        Args:
            None.

        Returns:
            None.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        title = QLabel("Job Management")
        title.setObjectName("dialogTitle")
        intro = QLabel(
            "Enter a Job ID, then define current risks. Main Save writes the project."
        )
        intro.setObjectName("supportingText")
        self.title_row = QHBoxLayout()
        self.title_row.addWidget(title)
        layout.addLayout(self.title_row)
        layout.addWidget(intro)
        content = QHBoxLayout()
        content.setSpacing(14)
        browser_panel = QFrame()
        browser_panel.setObjectName("workspacePanel")
        browser_panel.setMinimumWidth(280)
        browser_panel.setMaximumWidth(340)
        browser_layout = QVBoxLayout(browser_panel)
        browser_layout.setContentsMargins(14, 12, 14, 12)
        browser_layout.setSpacing(9)
        browser_title = QLabel("Jobs")
        browser_title.setObjectName("panelTitle")
        browser_layout.addWidget(browser_title)
        browser_layout.addWidget(QLabel("Job ID"))
        self.job_id_combo = QComboBox()
        self.job_id_combo.setEditable(True)
        self.job_id_combo.setToolTip(
            "Select an existing job or enter an ID for a new job."
        )
        browser_layout.addWidget(self.job_id_combo)
        navigation = QHBoxLayout()
        navigation.setSpacing(6)
        nav_specs = (
            ("first_button", "first.png", self.first_job, "First job"),
            ("previous_button", "previous.png", self.previous_job, "Previous job"),
            ("next_button", "next.png", self.next_job, "Next job"),
            ("last_button", "last.png", self.last_job, "Last job"),
        )
        for attr, icon, callback, tooltip in nav_specs:
            button = QPushButton()
            button.setIcon(self._icons[icon.removesuffix(".png")])
            button.setIconSize(QSize(24, 24))
            button.setToolTip(tooltip)
            button.clicked.connect(callback)
            setattr(self, attr, button)
            navigation.addWidget(button)
        browser_layout.addLayout(navigation)
        self.search_button = QPushButton("Search")
        self.search_button.setIcon(self._icons["search"])
        self.search_button.clicked.connect(self.search_job)
        browser_layout.addWidget(self.search_button)
        browser_layout.addStretch(1)
        content.addWidget(browser_panel)
        details_panel = QFrame()
        details_panel.setObjectName("workspacePanel")
        details_layout = QVBoxLayout(details_panel)
        details_layout.setContentsMargins(16, 12, 16, 14)
        details_layout.setSpacing(10)
        details_header = QHBoxLayout()
        details_title = QLabel("Job details")
        details_title.setObjectName("panelTitle")
        self.workplaces_button = QPushButton("Workplaces (0)")
        self.workplaces_button.setIcon(self._icons["plant"])
        self.workplaces_button.setIconSize(QSize(22, 22))
        self.workplaces_button.setToolTip(
            "Assign this Job to one or more workplace contexts."
        )
        self.workplaces_button.clicked.connect(self.open_workplaces)
        details_header.addWidget(details_title)
        details_header.addStretch(1)
        details_header.addWidget(self.workplaces_button)
        details_layout.addLayout(details_header)
        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(9)
        form_layout.addWidget(QLabel("Job name"), 0, 0)
        self.job_name_input = QLineEdit()
        self.job_name_input.setToolTip("Enter a descriptive name for this job.")
        form_layout.addWidget(self.job_name_input, 0, 1)
        form_layout.addWidget(QLabel("Description"), 1, 0, Qt.AlignmentFlag.AlignTop)
        self.job_description_input = QTextEdit()
        self.job_description_input.setMaximumHeight(70)
        self.job_description_input.setPlaceholderText("Optional job description")
        form_layout.addWidget(self.job_description_input, 1, 1)
        form_layout.setColumnStretch(1, 1)
        details_layout.addLayout(form_layout)
        self.risk_table = JobRiskTable(
            self._system, language=self._language, convention=self._convention
        )
        self.risk_table.setFixedHeight(162)
        details_layout.addWidget(self.risk_table)
        self.calculator_toggle = QPushButton(
            self.tr_text("Calculate or copy tool values", "Calcular o copiar valores")
        )
        self.calculator_toggle.setCheckable(True)
        self.calculator_toggle.setIcon(self._icons["job_management"])
        details_layout.addWidget(self.calculator_toggle)
        self.calculator_area = QWidget()
        calc_layout = QVBoxLayout(self.calculator_area)
        calc_layout.setContentsMargins(0, 0, 0, 0)
        self.tool_tabs = QTabWidget()
        self.tool_tabs.setObjectName("jobToolTabs")
        self.editors: dict[AssessmentKind, JobTaskEditor] = {}
        for kind, label in (
            (AssessmentKind.LIFFT, "LiFFT"),
            (AssessmentKind.DUET, "DUET"),
            (AssessmentKind.TST, "ST"),
        ):
            editor = JobTaskEditor(self._language, self._convention)
            editor.source_edited.connect(
                lambda source, k=kind: self._source_changed(k, source)
            )
            self.editors[kind] = editor
            self.tool_tabs.addTab(editor, label)
        calc_layout.addWidget(self.tool_tabs)
        self.tool_status = QLabel()
        self.tool_status.setWordWrap(True)
        calc_layout.addWidget(self.tool_status)
        actions = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(
            [
                self.tr_text("Direct values", "Valores directos"),
                self.tr_text("Task calculation", "Cálculo con tareas"),
            ]
        )
        actions.addWidget(self.mode_combo)
        self.add_task_button = QPushButton("+")
        self.add_task_button.setFixedWidth(38)
        self.add_task_button.setToolTip(
            self.tr_text("Add a task (maximum 100)", "Agregar tarea (máximo 100)")
        )
        self.remove_task_button = QPushButton("-")
        self.remove_task_button.setFixedWidth(38)
        self.remove_task_button.setToolTip(
            self.tr_text("Remove selected task", "Quitar tarea seleccionada")
        )
        self.clear_tool_button = QPushButton(
            self.tr_text("Clear tool", "Limpiar herramienta")
        )
        self.clear_tool_button.setIcon(self._icons["delete"])
        self.calculate_button = QPushButton(self.tr_text("Calculate", "Calcular"))
        self.calculate_button.setIcon(self._icons["calculate_light"])
        self.calculate_button.setStyleSheet("background: #087E91; color: white;")
        for button in (
            self.add_task_button,
            self.remove_task_button,
            self.clear_tool_button,
            self.calculate_button,
        ):
            actions.addWidget(
                button,
                1 if button in (self.clear_tool_button, self.calculate_button) else 0,
            )
        calc_layout.addLayout(actions)
        details_layout.addWidget(self.calculator_area, 1)
        self.calculator_area.setVisible(False)
        self.calculator_toggle.toggled.connect(self._calculator_visibility_changed)
        self.copy_assessment_button = QPushButton(
            self.tr_text("Use worker assessment…", "Usar evaluación de trabajador…")
        )
        self.copy_assessment_button.setIcon(self._icons["worker"])
        calc_layout.addWidget(self.copy_assessment_button)
        details_layout.addStretch(1)
        content.addWidget(details_panel, 1)
        layout.addLayout(content, 1)
        self.job_id_combo.currentIndexChanged.connect(self.load_job)
        identity_editor = self.job_id_combo.lineEdit()
        assert identity_editor is not None
        identity_editor.textChanged.connect(self._identity_availability)
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        for attr, text, icon, callback, name in (
            ("new_button", "Add Job", "new", self.new_job, ""),
            (
                "save_button",
                "Save changes",
                "save",
                self.save_job,
                "primaryOutlineButton",
            ),
            ("delete_button", "Delete", "delete", self.delete_job, "dangerButton"),
            ("cancel_button", "Discard changes", "undo", self.discard_changes, ""),
            ("close_button", "Close", "close", self.close_dialog, ""),
        ):
            button = QPushButton(self._text(text))
            button.setIcon(self._icons[icon])
            if name:
                button.setObjectName(name)
            button.clicked.connect(callback)
            setattr(self, attr, button)
            button_layout.addWidget(button)
        layout.addLayout(button_layout)
        self.risk_table.measurements_changed.connect(self._manual_changed)
        self.tool_tabs.currentChanged.connect(self._tool_changed)
        self.mode_combo.currentIndexChanged.connect(self._mode_changed)
        self.add_task_button.clicked.connect(self.add_task)
        self.remove_task_button.clicked.connect(self.remove_task)
        self.clear_tool_button.clicked.connect(self.clear_tool)
        self.calculate_button.clicked.connect(self.calculate_tool)
        self.copy_assessment_button.clicked.connect(self.copy_worker_assessment)
        self.job_name_input.editingFinished.connect(self._accept_from_signal)
        self.job_description_input.installEventFilter(self)

    def reject(self) -> None:
        """Accept valid session edits on Escape without writing the project file.

        Args:
            None.

        Returns:
            None; invalid text retains the dialog for correction or Discard changes.
        """
        if self.accept_pending_job():
            super().reject()

    def closeEvent(self, event: QCloseEvent | None) -> None:  # noqa: N802 — Qt override
        """Retain valid Job edits on native close.

        Args:
            event: Native close request; None is ignored defensively.

        Returns:
            None; failed acceptance preserves visible values and leaves the form open.
        """
        if event is None:
            return
        if not self.accept_pending_job():
            event.ignore()
            return
        super().closeEvent(event)

    def load_job(self) -> None:
        """Select stored details once, without reloading SQL or saving form edits.

        Args:
            None.

        Returns:
            None.
        """
        target = self.job_id_combo.currentText()
        if (
            self._workspace.editing is not None
            and not self._accepting_job
            and self._loaded_job_id
        ):
            with QSignalBlocker(self.job_id_combo):
                self.job_id_combo.setEditText(self._loaded_job_id)
            if not self.accept_pending_job():
                return
            with QSignalBlocker(self.job_id_combo):
                self.job_id_combo.setCurrentIndex(self.job_id_combo.findText(target))
        previous = self._accepting_job
        self._accepting_job = True
        try:
            self._show_job()
        finally:
            self._accepting_job = previous

    def _run(self, action: Callable[[], None]) -> None:
        """Invoke one explicit operation and display expected failures.

        Invoke one explicit operation and display expected failures while retaining the
        current form for correction or retry.

        Args:
            action: Host or local operation invoked once through the owning error
                boundary.

        Returns:
            None.
        """
        if self._busy:
            return
        self._busy = True
        try:
            action()
        except ValueError as error:
            self._warning(
                self._text("Validation Error"),
                job_management_error(str(error), self._language),
            )
        except Exception as error:
            # Qt event handlers must contain adapter failures and leave edits visible.
            logging.getLogger(__name__).warning(
                "Job action failed: %s", type(error).__name__
            )
            self._warning(
                self._text("Job Management"),
                self._text(
                    "The operation failed. Your form entries remain available. "
                    "Please try again."
                ),
            )
        finally:
            self._busy = False

    def _navigation(self, enabled: bool) -> None:
        """Update job-navigation and deletion availability.

        Update job-navigation and deletion availability for the currently loaded
        saved-job state.

        Args:
            enabled: Whether the associated controls should accept user interaction.

        Returns:
            None.
        """
        for button in (
            self.first_button,
            self.previous_button,
            self.next_button,
            self.last_button,
            self.search_button,
        ):
            button.setEnabled(enabled)
        self.delete_button.setEnabled(enabled)

    def open_workplaces(self) -> None:
        """Run the existing modal workplace editor while retaining unsaved form text.

        Args:
            None.

        Returns:
            None.
        """
        if not self.accept_pending_job():
            return

        def action() -> None:
            """Own the workplace edit and refresh committed placement catalogs/counts.

            Own the workplace edit and refresh committed placement catalogs/counts
            without accepting unsaved job form text.

            Args:
                None.

            Returns:
                None.
            """
            try:
                result = self._workplaces.edit(
                    self.job_id_combo.currentText(),
                    language=self._language,
                    preferred_shift=self._preferred_shift,
                )
                if result is not None:
                    self._preferred_shift = result.preferred_shift
            finally:
                # Even Cancel loads fresh workspace snapshots; retain the visible edits.
                self._jobs = self._workspace.read_jobs()
                self._risk = self._workspace.read_job_risk()
                self._workplace_count()

        self._run(action)

    def first_job(self) -> None:
        """Select the first job using the existing combo signal.

        Args:
            None.

        Returns:
            None.
        """
        if self.job_id_combo.count():
            self.job_id_combo.setCurrentIndex(0)

    def previous_job(self) -> None:
        """Select the previous job without wrapping.

        Args:
            None.

        Returns:
            None.
        """
        if self.job_id_combo.currentIndex() > 0:
            self.job_id_combo.setCurrentIndex(self.job_id_combo.currentIndex() - 1)

    def next_job(self) -> None:
        """Select the next job without wrapping.

        Args:
            None.

        Returns:
            None.
        """
        if self.job_id_combo.currentIndex() < self.job_id_combo.count() - 1:
            self.job_id_combo.setCurrentIndex(self.job_id_combo.currentIndex() + 1)

    def last_job(self) -> None:
        """Select the last job using the existing combo signal.

        Args:
            None.

        Returns:
            None.
        """
        if self.job_id_combo.count():
            self.job_id_combo.setCurrentIndex(self.job_id_combo.count() - 1)

    def delete_job(self) -> None:
        """Confirm deletion of the selected saved job; retain the form on failure.

        Args:
            None.

        Returns:
            None.
        """

        def action() -> None:
            """Require an unchanged saved job identity, confirm deletion.

            Require an unchanged saved job identity, confirm deletion, and reload
            catalogs only after the protected delete succeeds.

            Args:
                None.

            Returns:
                None.

            Raises:
                ValueError: Select an existing job before deleting.
            """
            index = self.job_id_combo.currentIndex()
            job_id = self.job_id_combo.currentText().strip()
            if index < 0 or job_id != self.job_id_combo.itemText(index):
                raise ValueError("Select an existing job before deleting.")
            reply = self._question(
                self._text("Confirm Deletion"),
                self._text("Are you sure you want to delete this job?"),
            )
            if reply != QMessageBox.Yes:
                return
            self._jobs, self._risk = self._workspace.delete_job(
                self._jobs, self._risk, job_id
            )
            self._reload_jobs()
            self._information(
                self._text("Success"),
                self._text("Job '{job_id}' has been deleted successfully.").format(
                    job_id=job_id
                ),
            )

        self._run(action)

    def search_job(self) -> None:
        """Use the original fixed-size exact-ID search dialog over loaded jobs.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(self._text("Search Job"))
        dialog.setFixedSize(400, 150)
        layout = QVBoxLayout(dialog)
        row = QHBoxLayout()
        row.addWidget(QLabel(self._text("Search by Job ID:")))
        field = QLineEdit()
        row.addWidget(field)
        layout.addLayout(row)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        for standard, icon in (
            (QDialogButtonBox.Ok, "search"),
            (QDialogButtonBox.Cancel, "close"),
        ):
            button = buttons.button(standard)
            assert button is not None
            button.setIcon(self._icons[icon])
        if self._language is Language.SPANISH:
            for standard, label in (
                (QDialogButtonBox.Ok, "OK"),
                (QDialogButtonBox.Cancel, "Cancel"),
            ):
                button = buttons.button(standard)
                assert button is not None
                button.setText(self._text(label))
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        try:
            if dialog.exec() == QDialog.Accepted:
                index = self.job_id_combo.findText(field.text().strip())
                if index >= 0:
                    self.job_id_combo.setCurrentIndex(index)
                else:
                    self._information(
                        self._text("No Match"),
                        self._text("No job found with the given criteria."),
                    )
        finally:
            dialog.deleteLater()

    def close_dialog(self) -> None:
        """Close through validation, retaining accepted integrated Job edits.

        Args:
            None.

        Returns:
            None.
        """
        self.close()

    def _text(self, source: str) -> str:
        """Resolve this component's UI wording without translating saved user values.

        Args:
            source: English reference UI wording or earlier project path, as stated by
                this operation; user values are retained literally.

        Returns:
            Localized UI wording according to this component's catalog/fallback
            contract.
        """
        return job_management_text(source, self._language)

    def _message(
        self,
        title: str,
        body: str,
        icon: QMessageBox.Icon,
        *,
        question: bool = False,
    ) -> int:
        # Localize framework buttons locally; do not change another window's locale.
        """Execute an owned localized message dialog and release its Qt resources.

        Execute an owned localized message dialog and release its Qt resources after the
        user responds.

        Args:
            title: Localized message/window title; never used as a stored identifier.
            body: Literal message content shown by the owned styled dialog.
            icon: Qt message severity icon.
            question: True presents Yes/No consent; False presents an informational
                acknowledgement.

        Returns:
            Qt standard-button/result integer chosen by the user; the temporary message
            instance is released.
        """
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(body)
        box.setIcon(icon)
        labels: tuple[tuple[QMessageBox.StandardButton, str], ...]
        if question:
            box.setStandardButtons(
                QMessageBox.StandardButtons(QMessageBox.Yes) | QMessageBox.No
            )
            labels = ((QMessageBox.Yes, "Yes"), (QMessageBox.No, "No"))
        else:
            box.setStandardButtons(QMessageBox.Ok)
            labels = ((QMessageBox.Ok, "OK"),)
        for standard, label in labels:
            button = box.button(standard)
            assert button is not None
            button.setText(self._text(label))
        try:
            return box.exec()
        finally:
            box.deleteLater()

    def _question(self, title: str, body: str) -> int:
        """Present original English or owned Spanish Yes/No job-management consent.

        Args:
            title: Localized message/window title; never used as a stored identifier.
            body: Literal message content shown by the owned styled dialog.

        Returns:
            Qt Yes/No result integer; the caller decides whether to execute the
            confirmed command.
        """
        if self._language is Language.ENGLISH:
            return int(
                QMessageBox.question(
                    self, title, body, QMessageBox.Yes | QMessageBox.No
                )
            )
        return self._message(title, body, QMessageBox.Question, question=True)

    def _information(self, title: str, body: str) -> None:
        """Show localized job-management information.

        Present original English or owned Spanish informational job-management feedback.

        Args:
            title: Localized message/window title; never used as a stored identifier.
            body: Literal message content shown by the owned styled dialog.

        Returns:
            None.
        """
        if self._language is Language.ENGLISH:
            QMessageBox.information(self, title, body)
        else:
            self._message(title, body, QMessageBox.Information)

    def _warning(self, title: str, body: str) -> None:
        """Present original English or owned Spanish validation/write-failure feedback.

        Present original English or owned Spanish validation/write-failure feedback
        without closing the editor.

        Args:
            title: Localized message/window title; never used as a stored identifier.
            body: Literal message content shown by the owned styled dialog.

        Returns:
            None.
        """
        if self._language is Language.ENGLISH:
            QMessageBox.warning(self, title, body)
        else:
            self._message(title, body, QMessageBox.Warning)

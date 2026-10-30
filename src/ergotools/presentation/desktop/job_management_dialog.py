"""Task-first Job workspace with optional direct results and shared project history.

Presentation layer. Preserve Job browsing/workplace controls while replacing the
profile/evidence workflow. Sources/results, direct edits and copied worker tasks use
existing workspace transactions and shared history. One main Save publishes; no SQL,
scientific formulas, ownership linking or nested calculator window occurs here.
"""

import logging
from collections.abc import Callable, Mapping
from dataclasses import replace

from PyQt5 import sip
from PyQt5.QtCore import QEvent, QLocale, QSignalBlocker, QSize, Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QIcon
from PyQt5.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.gauge_preferences import GaugeMarkerSettings
from ergotools.application.job_calculation import (
    auto_calculate_job_measurement,
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
from ergotools.presentation.desktop.assessment_editor_section import (
    AssessmentActionRow,
    AssessmentEditorSection,
)
from ergotools.presentation.desktop.job_assessment_dialog import (
    JobAssessmentDialog,
    JobCopyDialog,
)
from ergotools.presentation.desktop.job_direct_values import JobDirectValues
from ergotools.presentation.desktop.job_result_panel import (
    JobCalculationSummary,
    JobResultPanel,
)
from ergotools.presentation.desktop.job_task_editor import JobTaskEditor
from ergotools.presentation.desktop.job_workplace_host import JobWorkplaceHost
from ergotools.presentation.desktop.project_history_actions import ProjectHistoryActions
from ergotools.presentation.desktop.secondary_history_controls import (
    add_history_buttons,
)
from ergotools.presentation.desktop.text import (
    job_management_error,
    job_management_text,
)
from ergotools.presentation.desktop.theme.job_management import (
    JOB_INPUT_MODE_STYLE,
    JOB_MANAGEMENT_STYLE,
)
from ergotools.presentation.desktop.theme.main_workspace import MAIN_WORKSPACE_STYLE

# Reversible session-only tool selection; no database preference or separate stack.
_TOOL_EDITOR_KEY = "jobs.tool"
# Session-only selected Job identity; navigation never makes project data dirty.
_JOB_EDITOR_KEY = "jobs.selection"


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
        gauge_markers: GaugeMarkerSettings | None = None,
        change_gauge_markers: Callable[[GaugeMarkerSettings], None] | None = None,
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
            gauge_markers: Personal gauge appearance, independent of project data.
            change_gauge_markers: Personal-preference owner callback, or local preview.
            parent: Owning main window; this modal does not own the workspace.

        Returns:
            None; construction persists no Job, risk values or task source.
        """
        super().__init__(parent)
        self._workspace = workspace
        self._icons = icons
        self._system = system
        self._language = language
        self._convention = convention
        self._gauge_markers = gauge_markers
        self._change_gauge_markers = change_gauge_markers
        self._direct_tools: set[AssessmentKind] = set()
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
        self.setMinimumSize(1260, 830)
        self.resize(1620, 940)
        self._setup_ui()
        self._translate_controls()
        self._install_tooltips()
        if workspace.editing is not None:
            retained = workspace.editing.editor(_TOOL_EDITOR_KEY)
            if isinstance(retained, int) and 0 <= retained < 3:
                with QSignalBlocker(self.tool_tabs):
                    self.tool_tabs.setCurrentIndex(retained)
            workspace.editing.seed_editor(
                _TOOL_EDITOR_KEY, self.tool_tabs.currentIndex()
            )
        self._reload_jobs(selected_job)
        if workspace.editing is not None:
            workspace.editing.project_editor(_JOB_EDITOR_KEY, self._loaded_job_id)
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
            add_history_buttons(
                self.title_row,
                self.project_history.undo_button,
                self.project_history.redo_button,
            )
            for button in (
                self.project_history.undo_button,
                self.project_history.redo_button,
            ):
                button.setFixedSize(70, 70)
                button.setIconSize(QSize(34, 34))
            self.job_name_input.textEdited.connect(self.project_history.refresh)
            self.job_description_input.textChanged.connect(self.project_history.refresh)
            self.direct_values.pending_input_changed.connect(
                self.project_history.refresh
            )
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

    def _update_gauge_markers(self, settings: GaugeMarkerSettings) -> None:
        """Apply personal marker options only after the preference owner accepts them.

        Args:
            settings: Validated shared gauge visibility/interval preferences.

        Returns:
            None; failures retain appearance without changing project history.
        """

        def apply() -> None:
            """Persist through the injected owner before repainting the Job gauge.

            Args:
                None.

            Returns:
                None; errors propagate to the dialog's existing action boundary.
            """
            if self._change_gauge_markers is not None:
                self._change_gauge_markers(settings)
            self.result_panel.risk_gauge.set_marker_settings(settings)

        self._run(apply)

    def _install_tooltips(self) -> None:
        """Describe Job actions and editable metadata without replacing action tooltips.

        Args:
            None.

        Returns:
            None; tooltips carry no history, validation or persistence behavior.
        """
        for control, english, spanish in (
            (
                self.close_button,
                "Close and retain valid edits; use the main Save to store the project.",
                "Cerrar conservando cambios válidos; Guardar almacena el proyecto.",
            ),
            (
                self.save_button,
                "Accept this Job's valid edits.",
                "Aceptar los cambios válidos del trabajo.",
            ),
            (
                self.search_button,
                "Find a Job by ID or name.",
                "Buscar trabajo por ID o nombre.",
            ),
            (
                self.job_description_input,
                "Optional description of this Job.",
                "Descripción opcional del trabajo.",
            ),
            (
                self.new_button,
                "Start a new Job; valid edits to the current Job are retained.",
                "Crear trabajo; se conservan los cambios válidos del trabajo actual.",
            ),
            (
                self.delete_button,
                "Delete this Job after confirmation; referenced Jobs are protected.",
                "Eliminar con confirmación; los trabajos referenciados están "
                "protegidos.",
            ),
            (
                self.copy_assessment_button,
                "Copy all or selected tasks from a worker assessment; the source "
                "stays unchanged.",
                "Copiar tareas de una evaluación de trabajador sin modificar el "
                "origen.",
            ),
            (
                self.copy_job_button,
                "Choose another Job and copy all or selected tasks for this tool.",
                "Elegir otro trabajo y copiar tareas de esta herramienta.",
            ),
            (
                self.clear_tool_button,
                "Clear this tool's tasks and result; Undo restores them.",
                "Vaciar tareas y resultado de esta herramienta; Deshacer los restaura.",
            ),
            (
                self.calculate_button,
                "Recalculate the current tool from all entered tasks.",
                "Recalcular esta herramienta con todas las tareas ingresadas.",
            ),
        ):
            control.setToolTip(self.tr_text(english, spanish))

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
            *(field.text() for field in self.direct_values.fields.values()),
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
            or self.direct_values.has_pending()
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
        if not self.direct_values.accept_pending():
            for kind, error in self.direct_values.errors.items():
                if error.text():
                    with QSignalBlocker(self.tool_tabs):
                        self.tool_tabs.setCurrentIndex(list(AssessmentKind).index(kind))
                    self._tool_changed()
                    self.direct_values.fields[kind].setFocus()
                    break
            return False
        for kind, editor in self.editors.items():
            if not editor.accept_pending():
                with QSignalBlocker(self.tool_tabs):
                    self.tool_tabs.setCurrentIndex(list(AssessmentKind).index(kind))
                self._tool_changed()
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
        values = JobRiskValues(identity, self.direct_values.measurements())
        self._jobs, self._risk = self._workspace.save_job_details(
            self._jobs, self._risk, job, values
        )
        self._values = self._risk.risk.for_job(identity)
        self._tool_changed()
        self._loaded_job_id = identity
        self._update_assessment_heading()
        if self._workspace.editing is not None:
            self._workspace.editing.project_editor(_JOB_EDITOR_KEY, identity)
        if self.job_id_combo.findText(identity) < 0:
            with QSignalBlocker(self.job_id_combo):
                self.job_id_combo.addItem(identity)
                self.job_id_combo.setCurrentIndex(self.job_id_combo.findText(identity))
        self._job_baseline = self._job_values()
        self._navigation(True)
        self._workplace_count()
        self._refresh_copy_jobs()
        if self.project_history is not None:
            self.project_history.refresh()

    def restore_project_jobs(self) -> None:
        """Rebind current Job sources/results after shared project Undo/Redo.

        Args:
            None.

        Returns:
            None; restore the recorded tool/Job, falling back for a missing Job.
        """
        self._accepting_job = True
        try:
            selected = self._loaded_job_id
            editing = self._workspace.editing
            retained = editing.editor(_TOOL_EDITOR_KEY) if editing is not None else None
            selection = editing.editor(_JOB_EDITOR_KEY) if editing is not None else None
            if isinstance(selection, str):
                selected = selection
            if isinstance(retained, int) and 0 <= retained < 3:
                with QSignalBlocker(self.tool_tabs):
                    self.tool_tabs.setCurrentIndex(retained)
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
        self._direct_tools.clear()
        self.direct_values.load(self._values.measurements)
        for kind in self.editors:
            self._load_tool_editor(kind)
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
        self._update_assessment_heading()
        enabled = bool(self.job_id_combo.currentText().strip())
        self.direct_values.setEnabled(enabled)
        self.assessment_area.setEnabled(enabled)
        self.copy_assessment_button.setEnabled(enabled)
        self._refresh_copy_jobs()

    def _update_assessment_heading(self) -> None:
        """Identify the visible Job in its task heading without accepting any edit.

        Args:
            None.

        Returns:
            None; long literal names wrap, and pending metadata/history stay unchanged.
        """
        title = self.tr_text("Tasks & assessment", "Tareas y evaluación")
        identity = self.job_id_combo.currentText().strip()
        if identity:
            title += ": " + identity
            name = self.job_name_input.text().strip()
            if name:
                title += " - " + name
        self.assessment_heading.setText(title)
        self.assessment_heading.setToolTip(title)

    def _load_tool_editor(self, kind: AssessmentKind) -> None:
        """Display retained tasks, one unsaved starter row, or an empty direct tool.

        Args:
            kind: Exact tool whose editor is rebound after navigation or replay.

        Returns:
            None; opening an empty tool never inserts a source or history action.
        """
        item = self._measurement(kind)
        editor = self.editors[kind]
        if item.source is not None:
            editor.load_source(item.source, item.task_results)
        else:
            editor.load_source(
                blank_job_source(kind, self._system)
                if not item.complete and kind not in self._direct_tools
                else None
            )

    def _select_tool(self, index: int) -> None:
        """Accept pending inputs, then record the selected tool as a clean view action.

        Args:
            index: Newly requested LiFFT/DUET/ST tab index.

        Returns:
            None; invalid input stays on its tool instead of becoming hidden.
        """
        if not self._accepting_job and not self.accept_pending_job():
            return
        self._tool_changed()
        editing = self._workspace.editing
        if not self._accepting_job and editing is not None:
            editing.set_editor(_TOOL_EDITOR_KEY, index, "job.tool")

    def _tool_changed(self) -> None:
        """Project mode/task capacity without saving or creating default task sources.

        Args:
            None.

        Returns:
            None; an empty task-input tool shows its unsaved one-row starter preview.
        """
        kind = self._kind()
        item = self._measurement(kind)
        task_mode = item.source is not None or (
            not item.complete and kind not in self._direct_tools
        )
        mode_button = self.input_modes.button(1 if task_mode else 0)
        assert mode_button is not None
        mode_button.setChecked(True)
        self.direct_values.select_kind(kind)
        self.calculation_summary.set_direct_mode(not task_mode)
        source = item.source or (self.editors[kind].source if task_mode else None)
        count = len(source.tasks) if source is not None else 0
        self.tool_status.setText(
            self.tr_text(
                "{count} task(s) · Results update when input is complete."
                if task_mode
                else "Direct result · No task inputs recorded for this tool.",
                "{count} tarea(s) · Resultados al completar los datos."
                if task_mode
                else "Resultado directo · Sin tareas registradas.",
            ).format(count=count)
        )
        self.add_task_button.setEnabled(task_mode and count < 100)
        self.remove_task_button.setEnabled(task_mode and count > 0)
        self.calculate_button.setEnabled(task_mode and count > 0)
        self.result_panel.show_measurement(item)
        self.calculation_summary.show_measurement(item)
        QTimer.singleShot(0, self._align_results)

    def _align_results(self) -> None:
        """Align summary values with the active grid's Damage column after layout.

        Args:
            None.

        Returns:
            None; resize, tab selection and horizontal scrolling add no history action.
        """
        if sip.isdeleted(self.calculation_summary):
            return
        editor = self.editors[self._kind()]
        target = editor.headers[-2]
        self.calculation_summary.summary.align_to(target, self.assessment_area)
        self.direct_values.setFixedWidth(target.width())

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
        self.direct_values.load(self._values.measurements)
        if rebind:
            self._load_tool_editor(item.kind)
            self._watch_task_edits(item.kind)
        self.editors[item.kind].show_results(item.task_results)
        self._tool_changed()
        if self.job_id_combo.currentText().strip():
            self._save_form()

    def _source_changed(self, kind: AssessmentKind, source: object) -> None:
        """Accept task input and its automatic result as one shared history action.

        Args:
            kind: Explicit edited tool identity.
            source: Immutable source emitted by the owned numeric/selector grid.

        Returns:
            None; other tools and unrelated unfinished inputs are not swept into it.
        """
        if isinstance(source, (LifftDraft, DuetDraft, TstDraft)):
            self._run(
                lambda: self._set_measurement(
                    auto_calculate_job_measurement(
                        self._jobs.jobs.project_id,
                        self.job_id_combo.currentText().strip() or "draft",
                        source,
                        self._system,
                    ),
                    rebind=False,
                )
            )

    def _preview_direct_result(self, kind: object, value: object) -> None:
        """Project current direct typing into the single summary without accepting it.

        Args:
            kind: Tool identity emitted by the guarded direct input stack.
            value: Valid transient measurement, or None for absent/invalid input.

        Returns:
            None; pending text retains native undo and only editing completion commits.
        """
        if isinstance(kind, AssessmentKind) and kind == self._kind():
            item = (
                value
                if isinstance(value, JobRiskMeasurement)
                else JobRiskMeasurement(kind)
            )
            self.calculation_summary.show_measurement(item)

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
        if self.input_modes.checkedId() == 1 and item.source is None:
            self._direct_tools.discard(item.kind)
            if not item.complete:
                self._load_tool_editor(item.kind)
                self._watch_task_edits(item.kind)
                self._tool_changed()
                return
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
            self._run(lambda: self._set_measurement(JobRiskMeasurement(item.kind)))
        elif self.input_modes.checkedId() == 0 and item.source is not None:
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
            self._direct_tools.add(item.kind)
            self._run(
                lambda: self._set_measurement(
                    replace(item, source=None, task_results=())
                )
            )
        elif self.input_modes.checkedId() == 0:
            self._direct_tools.add(item.kind)
            self._load_tool_editor(item.kind)
            self._tool_changed()

    def add_task(self) -> None:
        """Append one task row, preserving existing inputs and invalidating outputs.

        Args:
            None.

        Returns:
            None; task capacity is limited to 100 independently per Job/tool.
        """
        if not self.accept_pending_job():
            return
        item = self._measurement(self._kind())
        source = item.source or self.editors[item.kind].source
        self._run(
            lambda: self._set_measurement(
                replace(
                    item,
                    source=(
                        resize_job_source(source)
                        if source is not None
                        else blank_job_source(item.kind, self._system)
                    ),
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
            None; removing the last stored task shows a starter; Undo restores data.
        """
        if not self.accept_pending_job():
            return
        item = self._measurement(self._kind())
        source = item.source
        row = self.editors[item.kind].selected_task_index
        if source is None or row < 0:
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
                    source=resize_job_source(source, remove=row)
                    if len(source.tasks) > 1
                    else None,
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
            None; task mode returns to one blank starter row; shared Undo restores all.
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
        self._run(lambda: self._set_measurement(JobRiskMeasurement(item.kind)))

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
        source = item.source or self.editors[item.kind].source
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
        finally:
            dialog.close()
            dialog.deleteLater()
            self._jobs = self._workspace.read_jobs()
            self._risk = self._workspace.read_job_risk()

    def _refresh_copy_jobs(self) -> None:
        """Enable explicit Job-source browsing when another real Job exists.

        Args:
            None.

        Returns:
            None; no source selector or implicit copy is kept in the main Job window.
        """
        identity = self.job_id_combo.currentText().strip()
        self.copy_job_button.setEnabled(
            bool(identity)
            and any(job.job_id != identity for job in self._jobs.jobs.jobs)
        )

    def copy_job_values(self) -> None:
        """Choose another Job's tool values, then confirm one independent copy.

        Args:
            None.

        Returns:
            None; Cancel leaves values intact. Existing project history owns mutation.
        """
        if not self.accept_pending_job():
            return
        picker = JobCopyDialog(
            self._workspace,
            self._kind(),
            self._icons,
            self._language,
            self.job_id_combo.currentText().strip(),
            self,
            convention=self._convention,
        )
        try:
            if picker.exec() != QDialog.Accepted or picker.selected is None:
                return
            item = picker.selected
            previous = self._measurement(self._kind())
            if (
                previous.complete
                or (
                    previous.source is not None
                    and any(task_has_data(t) for t in previous.source.tasks)
                )
            ) and self._question(
                self._text("Confirm Deletion"),
                self.tr_text(
                    "Replace this tool's tasks and results with the selected "
                    "Job values? Undo can restore them.",
                    "¿Reemplazar las tareas y resultados con los valores "
                    "seleccionados? Deshacer permite restaurarlos.",
                ),
            ) != QMessageBox.Yes:
                return
            self._jobs = self._workspace.read_jobs()
            self._risk = self._workspace.read_job_risk()
            self._run(lambda: self._set_measurement(item))
        finally:
            picker.close()
            picker.deleteLater()
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

    def _setup_ui(self) -> None:
        """Build Job navigation, task-first tool editors and one shared result card.

        Args:
            None.

        Returns:
            None.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        title = QLabel("Job Management")
        title.setObjectName("jobManagementTitle")
        intro = QLabel(
            self.tr_text(
                "Select a Job to review its tasks, calculate risk or "
                "reuse existing assessments.",
                "Seleccione un trabajo para revisar tareas, calcular "
                "riesgos o reutilizar evaluaciones.",
            )
        )
        intro.setObjectName("supportingText")
        self.title_row = QHBoxLayout()
        self.title_row.addWidget(title)
        metadata = self._workspace.project_metadata
        self.project_badge = QLabel(
            self.tr_text("Project: ", "Proyecto: ")
            + (metadata.title if metadata else "—")
        )
        self.project_badge.setObjectName("jobProjectBadge")
        self.project_badge.setWordWrap(True)
        self.project_badge.setMaximumWidth(650)
        self.project_badge.setToolTip(
            self._workspace.location or self.project_badge.text()
        )
        self.title_row.addWidget(self.project_badge)
        layout.addLayout(self.title_row)
        layout.addWidget(intro)
        content = QHBoxLayout()
        content.setSpacing(14)
        browser_panel = QFrame()
        browser_panel.setObjectName("workspacePanel")
        browser_panel.setMinimumWidth(235)
        browser_panel.setMaximumWidth(260)
        browser_layout = QVBoxLayout(browser_panel)
        browser_layout.setContentsMargins(14, 12, 14, 12)
        browser_layout.setSpacing(9)
        browser_title = QLabel("Jobs")
        browser_title.setObjectName("panelTitle")
        browser_layout.addWidget(browser_title)
        identity_group = QGroupBox(self.tr_text("Job details", "Datos del trabajo"))
        browser_layout.addWidget(identity_group)
        identity_layout = QVBoxLayout(identity_group)
        identity_layout.addWidget(QLabel("Job ID"))
        self.job_id_combo = QComboBox()
        self.job_id_combo.setEditable(True)
        self.job_id_combo.setToolTip(
            "Select an existing job or enter an ID for a new job."
        )
        identity_layout.addWidget(self.job_id_combo)
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
        identity_layout.addLayout(navigation)
        self.search_button = QPushButton("Search")
        self.search_button.setIcon(self._icons["search"])
        self.search_button.clicked.connect(self.search_job)
        identity_layout.addWidget(self.search_button)
        identity_layout.addWidget(QLabel(self._text("Job name")))
        self.job_name_input = QLineEdit()
        self.job_name_input.setToolTip("Enter a descriptive name for this job.")
        identity_layout.addWidget(self.job_name_input)
        identity_layout.addWidget(QLabel(self._text("Description")))
        self.job_description_input = QTextEdit()
        self.job_description_input.setMaximumHeight(90)
        identity_layout.addWidget(self.job_description_input)
        job_actions = QHBoxLayout()
        self.new_button = QPushButton(self.tr_text("Add Job", "Agregar"))
        self.new_button.setIcon(self._icons["new"])
        self.new_button.clicked.connect(self.new_job)
        self.delete_button = QPushButton(self._text("Delete"))
        self.delete_button.setIcon(self._icons["delete"])
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.clicked.connect(self.delete_job)
        job_actions.addWidget(self.new_button)
        job_actions.addWidget(self.delete_button)
        identity_layout.addLayout(job_actions)
        workplaces_group = QGroupBox(
            self.tr_text("Workplace assignments", "Asignaciones de lugar")
        )
        browser_layout.addWidget(workplaces_group)
        workplaces_layout = QVBoxLayout(workplaces_group)
        self.workplaces_button = QPushButton("Workplaces (0)")
        self.workplaces_button.setIcon(self._icons["plant"])
        self.workplaces_button.setToolTip(
            "Assign this Job to one or more workplace contexts."
        )
        self.workplaces_button.clicked.connect(self.open_workplaces)
        workplaces_layout.addWidget(self.workplaces_button)
        browser_layout.addStretch(1)
        reuse_group = QGroupBox(
            self.tr_text("Reuse assessment values", "Reutilizar evaluaciones")
        )
        reuse_layout = QVBoxLayout(reuse_group)
        browser_layout.addWidget(reuse_group)
        self.copy_assessment_button = QPushButton(
            self.tr_text("Copy from worker…", "Copiar de trabajador…")
        )
        self.copy_assessment_button.setIcon(self._icons["worker"])
        reuse_layout.addWidget(self.copy_assessment_button)
        self.copy_job_button = QPushButton(
            self.tr_text("Copy from Job", "Copiar de trabajo")
        )
        self.copy_job_button.setIcon(self._icons["job_management"])
        self.copy_job_button.clicked.connect(self.copy_job_values)
        reuse_layout.addWidget(self.copy_job_button)
        copy_note = QLabel(
            self.tr_text(
                "Copies can be edited independently.",
                "Las copias se pueden editar de forma independiente.",
            )
        )
        copy_note.setWordWrap(True)
        copy_note.setObjectName("supportingText")
        reuse_layout.addWidget(copy_note)
        content.addWidget(browser_panel)
        self.assessment_area = QFrame()
        self.assessment_area.setObjectName("workspacePanel")
        self.assessment_area.setStyleSheet(MAIN_WORKSPACE_STYLE)
        details_layout = QVBoxLayout(self.assessment_area)
        details_layout.setContentsMargins(14, 14, 14, 14)
        details_layout.setSpacing(10)
        method_row = QHBoxLayout()
        self.assessment_heading = QLabel()
        self.assessment_heading.setObjectName("jobAssessmentHeading")
        self.assessment_heading.setTextFormat(Qt.TextFormat.PlainText)
        self.assessment_heading.setWordWrap(True)
        self.assessment_heading.setMinimumWidth(0)
        self.assessment_heading.setSizePolicy(
            QSizePolicy.Ignored, QSizePolicy.Preferred
        )
        method_row.addWidget(self.assessment_heading, 1)
        self.input_modes = QButtonGroup(self)
        method_buttons = QHBoxLayout()
        method_buttons.setSpacing(0)
        for identity, english, spanish in (
            (1, "Task inputs", "Datos de tareas"),
            (0, "Direct result", "Resultado directo"),
        ):
            button = QPushButton(self.tr_text(english, spanish))
            button.setObjectName("jobInputModeButton")
            button.setStyleSheet(JOB_INPUT_MODE_STYLE)
            button.setMinimumWidth(
                button.fontMetrics().horizontalAdvance(button.text()) + 36
            )
            button.setToolTip(
                self.tr_text(
                    "Enter task inputs; results update after each completed valid edit."
                    if identity
                    else "Enter cumulative damage directly; probability is derived.",
                    "Ingrese tareas; resultados automáticos al completar datos válidos."
                    if identity
                    else "Ingrese el daño acumulado; la probabilidad se deriva.",
                )
            )
            button.setCheckable(True)
            self.input_modes.addButton(button, identity)
            method_buttons.addWidget(button)
        method_row.addLayout(method_buttons)
        details_layout.addLayout(method_row)
        self.tool_tabs = QTabWidget()
        self.tool_tabs.setObjectName("assessmentTabs")
        self.editors: dict[AssessmentKind, JobTaskEditor] = {}
        for kind, label in (
            (AssessmentKind.LIFFT, "LiFFT"),
            (AssessmentKind.DUET, "DUET"),
            (AssessmentKind.TST, "ST"),
        ):
            editor = JobTaskEditor(
                self._language,
                self._convention,
                kind=kind,
                system=self._system,
                precision=(
                    self._workspace.project_metadata.precision
                    if self._workspace.project_metadata
                    else None
                ),
            )
            editor.geometry_changed.connect(self._align_results)
            editor.source_edited.connect(
                lambda source, k=kind: self._source_changed(k, source)
            )
            self.editors[kind] = editor
            icon = "shoulder" if kind is AssessmentKind.TST else kind.value
            caption = {
                AssessmentKind.LIFFT: "Lifting Fatigue Failure Tool (LiFFT)",
                AssessmentKind.DUET: "Distal Upper Extremity Tool (DUET)",
                AssessmentKind.TST: "The Shoulder Tool (ST)",
            }[kind]
            index = self.tool_tabs.addTab(editor, self._icons[icon], caption)
            self.tool_tabs.setTabToolTip(
                index,
                self.tr_text(
                    "Shoulder Tool (ST)" if label == "ST" else label,
                    "Herramienta de hombro (ST)" if label == "ST" else label,
                ),
            )
        self.tool_tabs.setIconSize(QSize(36, 36))
        tab_bar = self.tool_tabs.tabBar()
        assert tab_bar is not None
        tab_bar.setElideMode(Qt.TextElideMode.ElideNone)
        tab_bar.setUsesScrollButtons(True)
        tab_bar.setExpanding(False)
        self.direct_values = JobDirectValues(
            self._system, self._language, self._convention
        )
        self.tool_status = QLabel()
        self.tool_status.setObjectName("supportingText")
        self.tool_status.setWordWrap(True)
        self.add_task_button = QPushButton(self.tr_text("+ Task", "+ Tarea"))
        self.add_task_button.setToolTip(
            self.tr_text("Add a task (maximum 100)", "Agregar tarea (máximo 100)")
        )
        self.remove_task_button = QPushButton(self.tr_text("- Task", "- Tarea"))
        self.remove_task_button.setToolTip(
            self.tr_text("Remove selected task", "Quitar tarea seleccionada")
        )
        self.calculation_summary = JobCalculationSummary(
            self._language,
            self._convention,
            self._workspace.project_metadata.precision
            if self._workspace.project_metadata
            else None,
        )
        self.calculation_summary.bind_direct_values(self.direct_values)
        self.direct_values.preview_changed.connect(self._preview_direct_result)
        self.assessment_actions = AssessmentActionRow(
            self._icons, middle=(self.add_task_button, self.remove_task_button)
        )
        self.clear_tool_button = self.assessment_actions.clear_button
        self.clear_tool_button.setText(
            self.tr_text("Clear assessment", "Limpiar evaluación")
        )
        self.calculate_button = self.assessment_actions.calculate_button
        self.calculate_button.setText(self.tr_text("Calculate", "Calcular"))
        self.editor_section = AssessmentEditorSection(
            self.tool_tabs,
            self.calculation_summary,
            self.assessment_actions,
            status=self.tool_status,
            spacing=10,
        )
        details_layout.addWidget(self.editor_section, 1)
        content.addWidget(self.assessment_area, 1)
        self.result_panel = JobResultPanel(
            self._language,
            self._convention,
            self._icons,
            self._gauge_markers,
            self._update_gauge_markers,
            parent=self,
            precision=self._workspace.project_metadata.precision
            if self._workspace.project_metadata
            else None,
        )
        self.result_panel.setMinimumHeight(self.result_panel.minimumSizeHint().height())
        result_scroll = QScrollArea()
        result_scroll.setFrameShape(QFrame.NoFrame)
        result_scroll.setWidgetResizable(True)
        result_scroll.setMinimumWidth(310)
        result_scroll.setMaximumWidth(325)
        result_scroll.setWidget(self.result_panel)
        content.addWidget(result_scroll)
        layout.addLayout(content, 1)
        self.job_name_input.textChanged.connect(self._update_assessment_heading)
        self.job_id_combo.currentIndexChanged.connect(self.load_job)
        identity_editor = self.job_id_combo.lineEdit()
        assert identity_editor is not None
        identity_editor.textChanged.connect(self._identity_availability)
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        for attr, text, icon, callback, name in (
            (
                "save_button",
                "Save changes",
                "save",
                self.save_job,
                "primaryOutlineButton",
            ),
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
        self.direct_values.measurements_changed.connect(self._manual_changed)
        self.tool_tabs.currentChanged.connect(self._select_tool)
        self.input_modes.idClicked.connect(self._mode_changed)
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
            None; invalid text retains the dialog for correction or native text Undo.
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
        """Accept pending edits, then record Job navigation on the shared clean cursor.

        Args:
            None.

        Returns:
            None; dropdown, arrows and search share one reversible view operation.
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

        editing = self._workspace.editing
        if not previous and editing is not None and self._loaded_job_id is not None:
            editing.set_editor(_JOB_EDITOR_KEY, self._loaded_job_id, "job.selection")

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
            if self._workspace.editing is not None:
                self._workspace.editing.project_editor(
                    _JOB_EDITOR_KEY, self._loaded_job_id
                )
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

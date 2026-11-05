"""Integrated guided Job assessment host over the production shared controls.

Presentation layer. Reuse JobTaskEditor, names/clipboard, totals, direct entry and the
main gauge/legend. This host accepts one completed edit through the existing workspace
Job service; it owns no calculator, SQL, save button or separate history stack.
"""

import logging
from collections.abc import Callable, Mapping
from functools import partial

from PyQt5 import sip
from PyQt5.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QButtonGroup,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.assessment_task_rows import remove_assessment_rows
from ergotools.application.gauge_preferences import GaugeMarkerSettings
from ergotools.application.job_calculation import (
    auto_calculate_job_measurement,
    blank_job_source,
    calculate_job_measurement,
    resize_job_source,
)
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    task_has_content,
)
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.job_risk import JobRiskMeasurement, JobRiskValues
from ergotools.domain.language import Language
from ergotools.presentation.desktop.assessment_action_icons import (
    assessment_action_icon,
)
from ergotools.presentation.desktop.assessment_editor_section import (
    AssessmentActionRow,
    AssessmentEditorSection,
)
from ergotools.presentation.desktop.assessment_tool_tabs import AssessmentToolTabs
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
from ergotools.presentation.desktop.theme.job_management import JOB_INPUT_MODE_STYLE
from ergotools.presentation.desktop.theme.main_workspace import MAIN_WORKSPACE_STYLE

# Surface operational failures at the owned widget boundary; never report failed
# writes as accepted.
_LOG = logging.getLogger(__name__)


class JrotJobPanel(QWidget):
    """Accept current Job/tool inputs while preserving exact unrelated project data.

    Attributes:
        changed: Accepted Job data changed; the host may refresh readiness/progress.
        tool_selected: Clean tool-view navigation, independent of analysis tool
            selection.
        pending_changed: Availability of still-focused data changed without acceptance.
        mode_selected: Immutable blank-direct view choices for shared history.
    """

    changed = pyqtSignal()
    tool_selected = pyqtSignal(object)
    pending_changed = pyqtSignal()
    mode_selected = pyqtSignal(object)

    def __init__(
        self,
        workspace: ProjectWorkspace[AssessmentDraft],
        icons: Mapping[str, QIcon],
        language: Language,
        parent: QWidget,
        convention: DecimalConvention = DecimalConvention.POINT,
        markers: GaugeMarkerSettings | None = None,
        change_markers: Callable[[GaugeMarkerSettings], None] | None = None,
    ) -> None:
        """Compose the actual shared calculator controls without creating Job sources.

        Args:
            workspace: Borrowed current integrated project and shared history owner.
            icons: Packaged tool/copy/calculation icons.
            language: Static interface language; source names/units remain literal.
            parent: Guided page owning Job selection and closing behavior.
            convention: Application numeric entry/display preference.
            markers: Shared personal gauge marker appearance.
            change_markers: Personal settings owner; never a project data write.

        Returns:
            None; blank one-task grids are preview-only until an explicit edit.

        Raises:
            ValueError: No integrated project/history owner is available.
        """
        super().__init__(parent)
        self.workspace, self.icons, self.language = workspace, icons, language
        self._owner = workspace.editing
        metadata = workspace.project_metadata
        if metadata is None or self._owner is None:
            raise ValueError("Open a project before editing guided Job inputs.")
        self.project_id = metadata.project_id
        self.system = metadata.default_units
        self.convention = convention
        self._tool_index = 0
        self.job_id: str | None = None
        self.values = JobRiskValues("unbound")
        self._loading = False
        self._direct: set[tuple[str, AssessmentKind]] = set()
        self._pending: JobRiskMeasurement | None = None
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.central = QWidget()
        self.central.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )
        self.central.setStyleSheet(MAIN_WORKSPACE_STYLE)
        layout = QVBoxLayout(self.central)
        layout.setContentsMargins(0, 0, 0, 0)
        methods = QHBoxLayout()
        self.heading = QLabel()
        self.heading.setWordWrap(True)
        methods.addWidget(self.heading, 1)
        self.modes = QButtonGroup(self)
        for key, en, es in [
            (1, "Task inputs", "Datos de tareas"),
            (0, "Direct result", "Resultado directo"),
        ]:
            button = QPushButton(self.text(en, es))
            button.setToolTip(button.text())
            button.setCheckable(True)
            button.setAutoDefault(False)
            button.setStyleSheet(JOB_INPUT_MODE_STYLE)
            button.setIcon(icons["task_inputs"] if key else icons["direct_result"])
            button.setIconSize(QSize(24, 24))
            button.setMinimumWidth(
                button.fontMetrics().horizontalAdvance(button.text()) + 64
            )
            self.modes.addButton(button, key)
            methods.addWidget(button)
        layout.addLayout(methods)
        self.tabs = AssessmentToolTabs()
        self.tabs.setObjectName("assessmentTabs")
        self.tabs.setIconSize(QSize(32, 32))
        tab_bar = self.tabs.tabBar()
        assert tab_bar is not None
        tab_bar.setElideMode(Qt.TextElideMode.ElideNone)
        tab_bar.setUsesScrollButtons(True)
        tab_bar.setExpanding(False)
        self.editors: dict[AssessmentKind, JobTaskEditor] = {}
        for kind, caption in [
            (AssessmentKind.LIFFT, "Lifting Fatigue Failure Tool (LiFFT)"),
            (AssessmentKind.DUET, "Distal Upper Extremity Tool (DUET)"),
            (AssessmentKind.TST, "The Shoulder Tool (ST)"),
        ]:
            editor = JobTaskEditor(
                language,
                self.convention,
                icons=icons,
                kind=kind,
                system=self.system,
                precision=metadata.precision,
            )
            editor.configure_task_actions(
                workspace, accept=partial(self.accept_source_change, kind)
            )
            editor.source_edited.connect(partial(self.source_changed, kind))
            editor.input_edited.connect(self.pending_changed.emit)
            editor.geometry_changed.connect(self.align_results)
            self.editors[kind] = editor
            self.tabs.addTab(
                editor,
                icons["shoulder" if kind is AssessmentKind.TST else kind.value],
                caption,
            )
        self.direct_values = JobDirectValues(self.system, language, self.convention)
        self.summary = JobCalculationSummary(
            language, self.convention, metadata.precision
        )
        self.summary.bind_direct_values(self.direct_values)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.add_task = QPushButton(self.text("+ Task", "+ Tarea"))
        self.remove_task = QPushButton(self.text("- Task", "- Tarea"))
        self.add_task.setToolTip(
            self.text("Append a task, up to 100", "Agregar una tarea, hasta 100")
        )
        self.add_task.setIcon(assessment_action_icon("add_task"))
        self.remove_task.setIcon(assessment_action_icon("remove_task"))
        self.remove_task.setToolTip(
            self.text(
                "Remove selected task rows", "Quitar filas de tareas seleccionadas"
            )
        )
        self.assessment_actions = AssessmentActionRow(
            icons, middle=(self.add_task, self.remove_task)
        )
        self.assessment_actions.clear_button.setText(
            self.text("Clear assessment", "Limpiar evaluación")
        )
        self.assessment_actions.calculate_button.setText(
            self.text("Calculate", "Calcular")
        )
        self.section = AssessmentEditorSection(
            self.tabs, self.summary, self.assessment_actions, status=self.status
        )
        layout.addWidget(self.section, 1)
        reuse = QHBoxLayout()
        for caption, worker in [
            (self.text("Copy worker assessment…", "Copiar evaluación…"), True),
            (self.text("Copy from Job…", "Copiar de trabajo…"), False),
        ]:
            button = QPushButton(caption)
            button.setAutoDefault(False)
            button.setIcon(icons["worker" if worker else "job_management"])
            button.setIconSize(QSize(28, 28))
            button.setMinimumHeight(42)
            button.clicked.connect(partial(self.copy_values, worker))
            reuse.addWidget(button)
        reuse.addStretch(1)
        layout.addLayout(reuse)
        root.addWidget(self.central, 1)
        self.results = JobResultPanel(
            language,
            self.convention,
            icons,
            markers,
            change_markers,
            parent=self,
            precision=metadata.precision,
        )
        result_scroll = QScrollArea()
        result_scroll.setWidgetResizable(True)
        result_scroll.setFixedWidth(315)
        result_scroll.setWidget(self.results)
        root.addWidget(result_scroll)
        self.error = QLabel()
        self.error.setWordWrap(True)
        self.error.setStyleSheet("color:#AD302B;")
        layout.addWidget(self.error)
        self.tabs.currentChanged.connect(self.tab_changed)
        self.modes.idClicked.connect(self.mode_changed)
        self.add_task.clicked.connect(partial(self.resize_tasks, False))
        self.remove_task.clicked.connect(partial(self.resize_tasks, True))
        self.assessment_actions.calculate_button.clicked.connect(self.calculate)
        self.assessment_actions.clear_button.clicked.connect(self.clear)
        self.direct_values.measurements_changed.connect(self.direct_changed)
        self.direct_values.pending_input_changed.connect(self.pending_changed.emit)
        self.direct_values.preview_changed.connect(self.preview_direct)
        self.bind(None)

    def text(self, english: str, spanish: str) -> str:
        """Choose captions without translating or changing source data.

        Args:
            english: English caption.
            spanish: Spanish caption.

        Returns:
            Current-language text.
        """
        return spanish if self.language is Language.SPANISH else english

    def kind(self) -> AssessmentKind:
        """Read the current display tool independently of optimization subset.

        Args:
            None.

        Returns:
            Stable tool enum in the shared tab order.
        """
        return tuple(AssessmentKind)[max(0, self.tabs.currentIndex())]

    def measurement(self, kind: AssessmentKind) -> JobRiskMeasurement:
        """Read one current value, keeping unavailable output distinct from zero.

        Args:
            kind: Current tool identity.

        Returns:
            Saved measurement or a typed empty display value.
        """
        return next(
            (m for m in self.values.measurements if m.kind is kind),
            JobRiskMeasurement(kind),
        )

    def bind(self, job_id: str | None) -> None:
        """Project accepted/restored data; hosts prepare pending text before navigation.

        Args:
            job_id: Exact existing Job identity, or None for an empty selection.

        Returns:
            None; starter tasks stay local and are never saved by binding.
        """
        self._loading = True
        try:
            self.job_id = job_id
            self._pending = None
            self.error.clear()
            jobs = self.workspace.read_jobs().jobs
            risks = self.workspace.read_job_risk().risk
            job = next((j for j in jobs.jobs if j.job_id == job_id), None)
            self.setEnabled(job is not None)
            self.values = (
                risks.for_job(job_id)
                if job_id is not None and job is not None
                else JobRiskValues("unbound")
            )
            self.heading.setText(
                (job.job_id + " · " + job.name)
                if job
                else self.text("Choose a Job", "Elija un trabajo")
            )
            for kind, editor in self.editors.items():
                item = self.measurement(kind)
                direct = item.source is None and (
                    item.complete or (job_id or "", kind) in self._direct
                )
                if direct:
                    self._direct.add((job_id or "", kind))
                else:
                    self._direct.discard((job_id or "", kind))
                editor.load_source(
                    None
                    if direct
                    else item.source or blank_job_source(kind, self.system),
                    item.task_results,
                )
            self.direct_values.load(self.values.measurements)
            self.refresh_result()
        finally:
            self._loading = False

    def refresh_result(self) -> None:
        """Update totals/gauge/legend without accepting or rebuilding cells.

        Args:
            None.

        Returns:
            None; queued alignment follows the shared Damage column geometry.
        """
        kind = self.kind()
        item = self.measurement(kind)
        direct = (self.job_id or "", kind) in self._direct
        button = self.modes.button(0 if direct else 1)
        if button is not None:
            button.setChecked(True)
        self.direct_values.select_kind(kind)
        self.summary.set_direct_mode(direct)
        self.summary.show_measurement(item)
        self.results.show_measurement(item)
        source = self.editors[kind].source
        self.add_task.setEnabled(
            not direct and source is not None and len(source.tasks) < 100
        )
        self.remove_task.setEnabled(
            not direct and self.editors[kind].source is not None
        )
        self.assessment_actions.calculate_button.setEnabled(not direct)
        self.status.setText(
            self.text(
                "Direct result · no task inputs", "Resultado directo · sin tareas"
            )
            if direct
            else self.text(
                "Complete inputs calculate automatically. These are shared "
                "project Job values.",
                "Los datos completos se calculan automáticamente. Son valores de "
                "trabajos del proyecto.",
            )
        )
        QTimer.singleShot(0, self.align_results)

    def align_results(self) -> None:
        """Use the same shared column alignment as Main and Job Management.

        Args:
            None.

        Returns:
            None; resize and horizontal scrolling do not create project edits.
        """
        if sip.isdeleted(self.summary):
            return
        target = self.editors[self.kind()].headers[-2]
        self.summary.summary.align_to(target, self.central)
        self.direct_values.setFixedWidth(target.width())

    def persist(self, item: JobRiskMeasurement, *, rebind: bool = False) -> bool:
        """Accept one guarded current Job/tool edit, retaining unfinished siblings.

        Args:
            item: Complete proposed source/result or deliberately cleared tool value.
            rebind: True only for structural actions, never an ordinary completed cell.

        Returns:
            True on acceptance; failed input stays pending and correction remains
            possible.
        """
        if self.job_id is None or self.workspace.editing is not self._owner:
            return False
        self._pending = item
        try:
            jobs, risk = self.workspace.read_jobs(), self.workspace.read_job_risk()
            if risk.risk.for_job(self.job_id) != self.values:
                raise ValueError(
                    self.text(
                        "Job values changed; reload before editing.",
                        "Los valores cambiaron; vuelva a cargar.",
                    )
                )
            job = next(j for j in jobs.jobs.jobs if j.job_id == self.job_id)
            values = JobRiskValues(
                self.job_id,
                (
                    *(m for m in self.values.measurements if m.kind is not item.kind),
                    item,
                ),
            )
            _, saved = self.workspace.save_job_details(jobs, risk, job, values)
            self.values = saved.risk.for_job(self.job_id)
            self._pending = None
            self.error.clear()
            if rebind:
                self.bind(self.job_id)
            else:
                self.direct_values.load(self.values.measurements)
                self.editors[item.kind].show_results(item.task_results)
                self.refresh_result()
            self.changed.emit()
            return True
        except Exception as error:
            _LOG.exception("Guided Job edit failed")
            self.error.setText(str(error))
            return False

    def source_changed(self, kind: AssessmentKind, source: object) -> None:
        """Receive a Qt source edit while the guarded callback reports acceptance.

        Args:
            kind: Exact tool associated with the emitting editor.
            source: Proposed source; non-assessment objects are rejected by the host.

        Returns:
            None; native signal dispatch keeps its standard void contract.
        """
        self.accept_source_change(kind, source)

    def accept_source_change(
        self, kind: AssessmentKind, source: object, label: str = ""
    ) -> bool:
        """Accept the shared grid's completed immutable cell/name/paste edit.

        Args:
            kind: Bound tool identity.
            source: Source DTO emitted by the existing guarded grid.
            label: Shared operation identity; the workspace groups Paste atomically.

        Returns:
            True on acceptance; False for obsolete targets or rejected persistence.
        """
        if self._loading or self.job_id is None:
            return False
        if isinstance(source, (LifftDraft, DuetDraft, TstDraft)):
            return self.persist(
                auto_calculate_job_measurement(
                    self.project_id, self.job_id, source, self.system
                )
            )

        return False

    def preview_direct(self, kind: object, item: object) -> None:
        """Show valid direct typing in the one existing colored summary.

        Args:
            kind: Explicit direct-editor model identity.
            item: Transient valid measurement or None.

        Returns:
            None; no history or source acceptance occurs in preview.
        """
        if kind is self.kind():
            self.summary.show_measurement(
                item
                if isinstance(item, JobRiskMeasurement)
                else JobRiskMeasurement(self.kind())
            )

    def direct_changed(self) -> None:
        """Accept the one completed direct tool field through the shared Job service.

        Args:
            None.

        Returns:
            None; missing values remain absent, and other tools remain exact.
        """
        if self._loading:
            return
        item = next(
            (m for m in self.direct_values.measurements() if m.kind is self.kind()),
            JobRiskMeasurement(self.kind()),
        )
        self.persist(item)

    def tab_changed(self, _index: int) -> None:
        """Publish a display-tool choice without changing the analysis subset.

        Args:
            _index: Native new tab index.

        Returns:
            None; the root owns chronological view navigation.
        """
        if self._loading:
            return
        self.tabs.blockSignals(True)
        self.tabs.setCurrentIndex(self._tool_index)
        self.tabs.blockSignals(False)
        if not self.prepare():
            return
        self.tabs.blockSignals(True)
        self.tabs.setCurrentIndex(_index)
        self.tabs.blockSignals(False)
        self._tool_index = _index
        self.refresh_result()
        self.tool_selected.emit(self.kind())

    def set_source_modes(self, modes: tuple[tuple[str, AssessmentKind], ...]) -> None:
        """Project retained blank-direct choices before binding restored Job data.

        Args:
            modes: Explicit Job/tool view choices from the shared immutable view.

        Returns:
            None; bind subsequently gives accepted sources precedence over stale flags.
        """
        self._direct = set(modes)

    def show_kind(self, kind: AssessmentKind) -> None:
        """Project a restored tool tab without recording another navigation edit.

        Args:
            kind: Accepted view state from the shared project history.

        Returns:
            None; current pending input must be prepared by the owner first.
        """
        self.tabs.blockSignals(True)
        self._tool_index = tuple(AssessmentKind).index(kind)
        self.tabs.setCurrentIndex(self._tool_index)
        self.tabs.blockSignals(False)
        self.refresh_result()

    def confirm(self, message: str) -> bool:
        """Obtain No-default consent before explicitly removing entered tasks/results.

        Args:
            message: Localized exact consequence.

        Returns:
            True only for explicit Yes.
        """
        return bool(
            QMessageBox.question(
                self,
                self.text("Confirm change", "Confirmar cambio"),
                message,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            == QMessageBox.Yes
        )

    def _binding(self) -> tuple[str | None, AssessmentKind, JobRiskValues]:
        """Capture the exact calculator target before an owned prompt or source picker.

        Args:
            None.

        Returns:
            Job, tool and accepted values; none of these identities come from captions.
        """
        return self.job_id, self.kind(), self.values

    def _check_binding(
        self, expected: tuple[str | None, AssessmentKind, JobRiskValues]
    ) -> bool:
        """Reject a prompt completion whose original target was rebound or retired.

        Args:
            expected: Target captured before entering a nested native event loop.

        Returns:
            True only for the same existing Job/tool/value and project session.
        """
        valid = (
            expected[0] is not None
            and self.workspace.editing is self._owner
            and self._binding() == expected
        )
        if not valid:
            self.error.setText(
                self.text(
                    "The Job/tool changed; retry the action.",
                    "El trabajo/herramienta cambió; repita la acción.",
                )
            )
        return valid

    def mode_changed(self, mode: int) -> None:
        """Switch source method with reversible explicit replacement of stored content.

        Args:
            mode: One for tasks, zero for direct output.

        Returns:
            None; cancelled changes restore the current mode. Blank method choices are
            clean views; stored-content replacement groups data and method in one edit.
        """
        if self._loading or not self.prepare():
            self.refresh_result()
            return
        binding = self._binding()
        kind = self.kind()
        if bool(mode) == ((self.job_id or "", kind) not in self._direct):
            self.refresh_result()
            return
        item = self.measurement(kind)
        if (item.source is not None or item.complete) and not self.confirm(
            self.text(
                "Replace this tool's stored tasks/result? Undo restores them.",
                "¿Reemplazar las tareas/resultado? Deshacer los restaura.",
            )
        ):
            self.refresh_result()
            return
        if not self._check_binding(binding):
            return
        owner = self._owner
        if owner is None or self.workspace.editing is not owner:
            return
        previous_modes = set(self._direct)
        key = (self.job_id or "", kind)
        if mode:
            self._direct.discard(key)
        else:
            self._direct.add(key)
        if item.source is None and not item.complete:
            self.bind(self.job_id)
            self.mode_selected.emit(tuple(sorted(self._direct)))
            return
        candidate = (
            auto_calculate_job_measurement(
                self.project_id,
                self.job_id or "",
                blank_job_source(kind, self.system),
                self.system,
            )
            if mode
            else JobRiskMeasurement(kind)
        )
        with owner.stage():
            if not self.persist(candidate, rebind=True):
                # A failed structural command retains the accepted source and can be
                # retried explicitly; there is no newly typed cell to discard here.
                self._direct = previous_modes
                self._pending = None
                self.refresh_result()
                return
            self.mode_selected.emit(tuple(sorted(self._direct)))
        owner.record("save_job_details")

    def resize_tasks(self, remove: bool) -> None:
        """Append one task or remove selected rows through shared calculation/history.

        Args:
            remove: True removes selected rows; False appends one, up to 100.

        Returns:
            None; populated removal needs consent and shared Undo restores it.
        """
        if not self.prepare():
            return
        binding = self._binding()
        editor = self.editors[self.kind()]
        source = editor.source
        if source is None:
            return
        rows = editor.selected_task_rows() if remove else ()
        if remove and not rows:
            return
        if (
            remove
            and any(task_has_content(source.tasks[row]) for row in rows)
            and not self.confirm(
                self.text(
                    f"Remove {len(rows)} selected task(s) and their data?",
                    f"¿Quitar {len(rows)} tarea(s) seleccionada(s) y sus datos?",
                )
            )
        ):
            return
        if not self._check_binding(binding):
            return
        if remove and len(rows) == len(source.tasks):
            self.persist(JobRiskMeasurement(self.kind()), rebind=True)
            return
        try:
            changed = (
                remove_assessment_rows(source, rows)
                if remove
                else resize_job_source(source)
            )
            item = auto_calculate_job_measurement(
                self.project_id,
                self.job_id or "",
                changed,
                self.system,
            )
            self.persist(item, rebind=True)
        except ValueError as error:
            self.error.setText(str(error))

    def calculate(self) -> None:
        """Run the unchanged calculator explicitly after accepting valid pending cells.

        Args:
            None.

        Returns:
            None; the resulting current Job value uses shared project history/Save.
        """
        if not self.prepare() or self.job_id is None:
            return
        source = self.editors[self.kind()].source
        if source is None:
            return
        try:
            self.persist(
                calculate_job_measurement(
                    self.project_id,
                    self.job_id,
                    source,
                    self.system,
                )
            )
        except ValueError as error:
            self.error.setText(str(error))

    def clear(self) -> None:
        """Clear only the selected Job/tool after explicit confirmation.

        Args:
            None.

        Returns:
            None; other Jobs/tools and worker assessments stay unchanged.
        """
        if not self.prepare():
            return
        binding = self._binding()
        if not self.confirm(
            self.text(
                "Clear this Job/tool assessment?",
                "¿Limpiar esta evaluación del trabajo?",
            )
        ):
            return
        if self._check_binding(binding):
            self.persist(JobRiskMeasurement(binding[1]), rebind=True)

    def copy_values(self, worker: bool) -> None:
        """Reuse the existing read-only source picker and optional task subset copy.

        Args:
            worker: True chooses a worker context; False chooses another Job.

        Returns:
            None; accepted copies are independent data, never links to the source.
        """
        if not self.prepare() or self.job_id is None:
            return
        binding = self._binding()
        dialog = (
            JobAssessmentDialog(
                self.workspace, self.kind(), self.icons, self.language, self
            )
            if worker
            else JobCopyDialog(
                self.workspace,
                self.kind(),
                self.icons,
                self.language,
                self.job_id,
                self,
            )
        )
        try:
            if dialog.exec() == QDialog.Accepted and dialog.selected is not None:
                if not self._check_binding(binding):
                    return
                if (
                    self.measurement(self.kind()).source is not None
                    or self.measurement(self.kind()).complete
                ) and not self.confirm(
                    self.text(
                        "Replace this tool with the selected independent copy?",
                        "¿Reemplazar con la copia independiente seleccionada?",
                    )
                ):
                    return
                if not self._check_binding(binding):
                    return
                item = dialog.selected
                if item.source is None:
                    self._direct.add((self.job_id, item.kind))
                else:
                    self._direct.discard((self.job_id, item.kind))
                self.persist(item, rebind=True)
        finally:
            dialog.deleteLater()

    def has_pending(self) -> bool:
        """Expose unfinished input to the root's shared history/close preparation.

        Args:
            None.

        Returns:
            True for unfinished numeric/name/direct tokens or a failed guarded write.
        """
        return (
            self._pending is not None
            or self.direct_values.has_pending()
            or any(e.has_pending() for e in self.editors.values())
        )

    def prepare(self) -> bool:
        """Complete valid cells before navigation without dropping invalid text.

        Args:
            None.

        Returns:
            False retains correction input; True leaves all accepted data in the
            project.
        """
        if self._pending is not None and not self.persist(self._pending):
            return False
        return self.direct_values.accept_pending() and all(
            e.accept_pending() for e in self.editors.values()
        )

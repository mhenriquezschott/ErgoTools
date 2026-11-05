"""Guided saved rotation entry over shared project services and calculator controls.

Presentation layer. The normal JROT entry edits real scenario and shared Job data
privately; Main Save publishes accepted changes. Weighted optimization, hard rules,
No-path proposals and frozen comparisons use the same portable project services.
No sample data, substitute solver or compatibility decoding is introduced here.
"""

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import date
from functools import partial
from uuid import uuid4

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QCloseEvent, QColor, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.gauge_preferences import GaugeMarkerSettings
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.rotation_entry import (
    RotationEntryChange,
    choose_observed_rotation,
    reclock_rotation_inputs,
    reshape_rotation_inputs,
    reshape_timed_rotation_inputs,
    rotation_entry_issues,
    rotation_entry_targets,
    scope_rotation_inputs,
    set_rotation_cell,
)
from ergotools.application.rotation_optimization import RotationPlanningOptimizer
from ergotools.application.rotation_planning import (
    capture_rotation_boundary,
    neighbors_are_current,
)
from ergotools.application.rotation_scenarios import (
    create_scenario,
    duplicate_scenario,
    opening_scenario,
    own_run_is_current,
)
from ergotools.application.rotation_timing import ShiftClock, clock_minute, shift_clock
from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    task_has_data,
)
from ergotools.domain.assessments.duet import DuetTask
from ergotools.domain.assessments.lifft_draft import LifftTask
from ergotools.domain.assessments.tst import TstTask
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.language import Language
from ergotools.domain.risk import classify_probability
from ergotools.domain.rotation import RotationRisk
from ergotools.domain.rotation_comparison import starting_indices
from ergotools.domain.rotation_planning import rotation_interval
from ergotools.domain.rotation_scenario import (
    ROTATION_RUN_MODEL_VERSION,
    RotationDraftRow,
    RotationInputs,
    RotationScenario,
)
from ergotools.domain.rotation_scheme import RotationTarget, RotationWorkerLink
from ergotools.domain.rotation_timing import RotationTiming, equal_timing
from ergotools.domain.work_hierarchy import LineKey
from ergotools.presentation.desktop.assessment_editor_preferences import (
    AssessmentEditorPreferences,
)
from ergotools.presentation.desktop.assessment_tool_tabs import assessment_tool_icon
from ergotools.presentation.desktop.job_management_dialog import JobManagementDialog
from ergotools.presentation.desktop.jrot_catalog_picker import (
    JrotCatalogChoice,
    JrotCatalogPicker,
)
from ergotools.presentation.desktop.jrot_comparison_panel import JrotComparisonPanel
from ergotools.presentation.desktop.jrot_job_panel import JrotJobPanel
from ergotools.presentation.desktop.jrot_neighbor_section import JrotNeighborSection
from ergotools.presentation.desktop.jrot_planning_controller import (
    JrotPlanningController,
)
from ergotools.presentation.desktop.jrot_result_table import tool_caption
from ergotools.presentation.desktop.jrot_rules_dialog import JrotRulesDialog
from ergotools.presentation.desktop.jrot_table_style import style_rotation_table
from ergotools.presentation.desktop.multiline_edit import MultilineEdit
from ergotools.presentation.desktop.optional_date_edit import OptionalDateEdit
from ergotools.presentation.desktop.optional_time_edit import OptionalTimeEdit
from ergotools.presentation.desktop.organization_dialog import OrganizationDialog
from ergotools.presentation.desktop.project_history_actions import ProjectHistoryActions
from ergotools.presentation.desktop.rotation_block_headers import RotationBlockHeaders
from ergotools.presentation.desktop.rotation_timeline import RotationTimeline
from ergotools.presentation.desktop.rotation_timing_dialog import RotationTimingDialog
from ergotools.presentation.desktop.secondary_history_controls import (
    add_history_buttons,
)
from ergotools.presentation.desktop.table_presentation import (
    AdaptiveTableWidget,
    numeric_display,
)
from ergotools.presentation.desktop.theme.dialogs import apply_dialog_theme
from ergotools.presentation.desktop.theme.job_results import job_damage_color
from ergotools.presentation.desktop.theme.risk import RISK_APPEARANCES
from ergotools.presentation.desktop.worker_management_dialog import (
    WorkerManagementDialog,
)
from ergotools.presentation.desktop.workflow_action_style import (
    page_heading_icon,
    set_action_icon,
)
from ergotools.presentation.desktop.workflow_drawer import WorkflowDrawer
from ergotools.presentation.desktop.workplace_scope_picker import WorkplaceScopePicker

# Log operational failures at the GUI boundary and keep the input available for
# correction.
_LOG = logging.getLogger(__name__)
# Project-local chronological view, separate from saved scientific scenario inputs.
_VIEW_KEY = "jrot.guided.view"
# Consecutive production page names, distinct from historical wireframe numbering.
# Same semantic glyphs for drawer navigation and light page headings.
_STEP_ICON_KEYS = (
    "shift",
    "job_management",
    "worker_management",
    "apply_rotation",
    "calculate_light",
    "view",
    "optimize_all_tools",
    "compare_rotation",
)
# Consecutive production page captions, independent of historical wireframe numbering.
_STEPS = (
    ("Rotation setup", "Configurar rotación"),
    ("Jobs", "Trabajos"),
    ("Workers", "Trabajadores"),
    ("Current assignments", "Asignaciones actuales"),
    ("Tasks & validation", "Tareas y validación"),
    ("Review inputs", "Revisar datos"),
    ("Optimization", "Optimización"),
    ("Comparison & report", "Comparación e informe"),
)


@dataclass(frozen=True, slots=True)
class JrotView:
    """Immutable shared-history projection; no widget or scientific state is retained.

    Attributes:
        scenario_id: Exact viewed record, or None for unaccepted creation.
        page: Zero-based sequential page.
        job_id: Exact Job currently displayed in the shared calculator.
        kind: Displayed tool, independent of analysis-tool selection.
        direct_modes: Local blank-direct choices; accepted sources override stale flags.
    """

    scenario_id: str | None = None
    page: int = 0
    job_id: str | None = None
    kind: AssessmentKind = AssessmentKind.LIFFT
    direct_modes: tuple[tuple[str, AssessmentKind], ...] = ()


class JrotDialog(QDialog):
    """Edit independent named rotations using the one current project/history owner."""

    def __init__(
        self,
        workspace: ProjectWorkspace[AssessmentDraft],
        icons: Mapping[str, QIcon],
        *,
        language: Language = Language.ENGLISH,
        convention: DecimalConvention = DecimalConvention.POINT,
        parent: QWidget | None = None,
        optimizer: RotationPlanningOptimizer | None = None,
        editor_preferences: AssessmentEditorPreferences | None = None,
        markers: GaugeMarkerSettings | None = None,
        change_markers: Callable[[GaugeMarkerSettings], None] | None = None,
    ) -> None:
        """Compose guided real-data entry without creating records merely on opening.

        Args:
            workspace: Open integrated project; owns private data, history and Save.
            icons: Current packaged icons, never assets from the reference checkout.
            language: Owned captions; literal project data is not translated.
            convention: Personal numeric entry/display preference.
            parent: Main window owning the modal lifecycle.
            editor_preferences: Shared column/import defaults and read-only file reader.
            optimizer: Production planner with immutable inputs and explicit Keep.
            markers: Shared personal gauge marker options.
            change_markers: Personal settings callback; independent of project
            history.

        Returns:
            None; a kept selection opens 08 collapsed; unsolved/empty opens 01 expanded.

        Raises:
            ValueError: No project editing session/metadata is available.
        """
        super().__init__(parent)
        metadata, owner = workspace.project_metadata, workspace.editing
        if metadata is None or owner is None:
            raise ValueError("Open a project before opening guided rotation entry.")
        self.editor_preferences = editor_preferences
        self.workspace, self.icons, self.language = workspace, icons, language
        self.metadata, self.owner, self.convention = metadata, owner, convention
        self.gauge_markers, self._change_markers = markers, change_markers
        self.repository = workspace.rotation_scenarios()
        records = self.repository.load_rotation_scenarios()
        remembered = owner.editor(_VIEW_KEY)
        remembered_selection = (
            remembered.scenario_id
            if isinstance(remembered, JrotView) and remembered.scenario_id is not None
            else self.repository.last_rotation_selection()
        )
        chosen = opening_scenario(records, remembered_selection)
        self.view = JrotView(
            chosen.scenario_id if chosen else None,
            page=7 if chosen and chosen.run else 0,
        )
        # Restore the remembered rotation, then show its kept evidence or setup.
        # Later in-window navigation remains on the shared chronological cursor.
        owner.project_editor(_VIEW_KEY, self.view)
        self.scenario: RotationScenario | None = None
        self._loading = False
        self._generation = 0
        self.setWindowTitle(
            self.text(
                "Job Rotation Optimization Tool (JROT)",
                "Herramienta de optimización de rotación (JROT)",
            )
        )
        self.resize(1720, 1000)
        self.setMinimumSize(1480, 880)
        apply_dialog_theme(self)
        self.setStyleSheet(
            self.styleSheet() + "\nQWidget#jrotPage { background:#F4F7F9; } "
            "QPushButton#observedChoice:checked { background:#087E91; "
            "color:white; border-color:#087E91; }"
        )
        root = QVBoxLayout(self)
        title = QHBoxLayout()
        self.title_icon = QLabel()
        self.title_icon.setFixedSize(40, 40)
        self.title_icon.setPixmap(icons["jrot"].pixmap(QSize(40, 40)))
        self.title_icon.setToolTip(
            self.text("Job rotation optimization", "Optimización de rotación")
        )
        title.addWidget(self.title_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        heading = QLabel(
            self.text(
                "Job Rotation Optimization", "Optimización de rotación de trabajos"
            )
        )
        heading.setStyleSheet("font-size:24px;font-weight:700;color:#0B326C;")
        title.addWidget(heading, 1)
        self.history = ProjectHistoryActions(
            self,
            owner,
            icons,
            language,
            prepare=self.prepare,
            restored=self.reload,
            blocked=lambda: (
                self.planning_busy()
                or QApplication.activeModalWidget() not in (None, self)
            ),
            pending=self.pending_action,
        )
        add_history_buttons(title, self.history.undo_button, self.history.redo_button)
        root.addLayout(title)
        project = QLabel(self.text("Project: ", "Proyecto: ") + metadata.title)
        root.addWidget(project)
        selection = QHBoxLayout()
        selection.addWidget(QLabel(self.text("Rotation", "Rotación")))
        self.scenarios = QComboBox()
        self.scenarios.setToolTip(
            self.text(
                "Choose a saved rotation to review or edit. New rotation opens an "
                "unsaved setup; its name is entered in step 01.",
                "Elija una rotación guardada para revisar o editar. Nueva rotación "
                "abre una configuración sin crear; su nombre se ingresa en el paso "
                "01.",
            )
        )
        self.scenarios.setMinimumContentsLength(24)
        selection.addWidget(self.scenarios, 1)
        for en, es, callback in [
            ("New rotation", "Nueva rotación", self.new_rotation),
            ("Duplicate…", "Duplicar…", self.duplicate),
            ("Delete…", "Eliminar…", self.delete_rotation),
        ]:
            button = self.button(self.text(en, es), callback)
            if en == "Duplicate…":
                button.setIcon(self.icons.get("duplicate_rotation", QIcon()))
                button.setIconSize(QSize(28, 28))
            selection.addWidget(button)
        root.addLayout(selection)
        self.creation_notice = self.notice(
            self.text(
                "Create a named rotation in step 1 to edit its data. "
                "You can review any page.",
                "Cree una rotación en el paso 1 para editarla. "
                "Puede revisar cualquier paso.",
            ),
            root,
        )
        body = QHBoxLayout()
        self.drawer = WorkflowDrawer(
            tuple(
                f"{i:02d}  {self.text(*captions)}"
                for i, captions in enumerate(_STEPS, 1)
            ),
            self.go,
            icons=tuple(icons[key] for key in _STEP_ICON_KEYS),
            language=language,
            hint=self.text(
                "Review any step. Main Save stores accepted changes.",
                "Revise cualquier paso. Guardar publica los cambios aceptados.",
            ),
        )
        body.addWidget(self.drawer)
        self.pages = QStackedWidget()
        self.page_layouts: list[QVBoxLayout] = []
        for i, captions in enumerate(_STEPS, 1):
            page = QWidget()
            page.setObjectName("jrotPage")
            layout = QVBoxLayout(page)
            layout.setContentsMargins(12, 10, 12, 10)
            label = QLabel(f"{i:02d} / {self.text(*captions)}")
            label.setStyleSheet("font-size:21px;font-weight:700;color:#0B326C;")
            heading_row = QHBoxLayout()
            heading_icon = QLabel()
            heading_icon.setPixmap(
                page_heading_icon(icons[_STEP_ICON_KEYS[i - 1]]).pixmap(40, 40)
            )
            heading_icon.setObjectName(f"stepIcon{i}")
            heading_icon.setFixedSize(44, 44)
            heading_row.addWidget(heading_icon)
            heading_row.addWidget(label, 1)
            layout.addLayout(heading_row)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(page)
            self.pages.addWidget(scroll)
            self.page_layouts.append(layout)
        body.addWidget(self.pages, 1)
        root.addLayout(body, 1)
        self.build_setup()
        self.build_catalogs()
        self.matrix = AdaptiveTableWidget()
        style_rotation_table(self.matrix)
        self.matrix_headers = RotationBlockHeaders(self.matrix)
        self.matrix.setAlternatingRowColors(True)
        self.matrix_notice = self.notice(
            self.text(
                "Enter the observed schedule. Blank cells stay unentered. No "
                "schedule is inferred.",
                "Ingrese la rotación de base. Las celdas vacías siguen sin completar.",
            ),
            self.page_layouts[3],
        )
        self.page_layouts[3].addWidget(self.matrix, 1)
        proposal_actions = QHBoxLayout()
        proposal_actions.addWidget(
            self.button(
                self.text("Generate initial proposal…", "Generar propuesta inicial…"),
                self.generate_proposal,
            )
        )
        proposal_actions.addWidget(
            self.button(
                self.text("Clear assignments", "Quitar asignaciones"),
                self.clear_assignments,
            )
        )
        proposal_actions.addStretch(1)
        self.page_layouts[3].addLayout(proposal_actions)
        assessment = QHBoxLayout()
        self.job_list = QListWidget()
        job_column = QWidget()
        job_column.setMinimumWidth(200)
        job_column.setMaximumWidth(260)
        job_layout = QVBoxLayout(job_column)
        job_layout.setContentsMargins(0, 0, 0, 0)
        job_layout.addWidget(self.job_list, 1)
        self.job_readiness = QLabel()
        self.job_readiness.setWordWrap(True)
        self.job_readiness.setStyleSheet(
            "background:#FFF3D6;color:#704700;border:1px solid #DBB660;border-"
            "radius:5px;padding:9px;font-weight:600;"
        )
        self.job_readiness.setMaximumHeight(180)
        job_layout.addWidget(self.job_readiness)
        assessment.addWidget(job_column)
        self.job_panel = JrotJobPanel(
            workspace, icons, language, self, convention, markers, self.save_markers
        )
        assessment.addWidget(self.job_panel, 1)
        self.page_layouts[4].addLayout(assessment, 1)
        self.job_list.currentRowChanged.connect(self.job_selected)
        self.job_panel.changed.connect(self.job_changed)
        self.job_panel.tool_selected.connect(self.tool_selected)
        self.job_panel.mode_selected.connect(self.source_mode_selected)
        self.job_panel.pending_changed.connect(self.history.refresh)
        self.build_review()
        self.solve = JrotPlanningController(self, optimizer)
        self.page_layouts[6].addWidget(self.solve.panel, 1)
        self.comparison = JrotComparisonPanel(self)
        self.page_layouts[7].addWidget(self.comparison, 1)
        self.error = QLabel()
        self.error.setWordWrap(True)
        self.error.setStyleSheet("color:#AD302B;")
        root.addWidget(self.error)
        footer = QHBoxLayout()
        self.back = self.button(self.text("Back", "Atrás"), partial(self.relative, -1))
        set_action_icon(self.back, self.icons["previous"])
        footer.addWidget(self.back)
        self.page_caption = QLabel()
        footer.addWidget(self.page_caption, 1)
        footer.addWidget(self.button(self.text("Close", "Cerrar"), self.accept))
        self.next = self.button(
            self.text("Continue", "Continuar"), partial(self.relative, 1)
        )
        set_action_icon(self.next, self.icons["next"])
        self.next.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.next.setObjectName("primary")
        footer.addWidget(self.next)
        root.addLayout(footer)
        self.scenarios.currentIndexChanged.connect(self.scenario_selected)
        self.reload()
        owner.seed_editor(_VIEW_KEY, self.view)
        self.drawer.pin.setChecked(chosen is None or chosen.run is None)

    def text(self, english: str, spanish: str) -> str:
        """Choose interface text without changing any project labels.

        Args:
            english: English caption.
            spanish: Spanish caption.

        Returns:
            Caption for the window's language.
        """
        return spanish if self.language is Language.SPANISH else english

    def button(self, text: str, callback: Callable[[], None]) -> QPushButton:
        """Build an owned action that cannot become an accidental Enter default.

        Args:
            text: Visible purpose, also its accessible tooltip.
            callback: Owner-thread operation.

        Returns:
            Button adopted by its containing layout.
        """
        button = QPushButton(text)
        for operation, name in (
            (self.generate_proposal, "generate_proposal"),
            (self.clear_assignments, "clear_assignments"),
            (self.edit_rules, "worker_restrictions"),
            (self.new_rotation, "new"),
            (self.delete_rotation, "delete"),
            (self.duplicate, "duplicate_rotation"),
            (self.create_rotation, "new"),
            (self.choose_scope, "plant"),
            (self.open_organization, "plant"),
            (self.use_shift_timing, "apply_timing"),
            (self.edit_timing, "edit_timing"),
            (self.choose_jobs, "job_management"),
            (self.choose_workers, "worker"),
            (self.open_jobs, "job_management"),
            (self.open_workers, "worker_management"),
            (self.accept, "close"),
        ):
            if callback == operation:
                set_action_icon(button, self.icons.get(name, QIcon()))
        button.setAutoDefault(False)
        button.setToolTip(text)
        button.clicked.connect(callback)
        return button

    def notice(self, text: str, layout: QVBoxLayout) -> QLabel:
        """Add a readable common-palette explanation to a page.

        Args:
            text: Localized explanation; not a saved data field.
            layout: Owning page layout.

        Returns:
            Wrapping notice for later projection when appropriate.
        """
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(
            "background:#EAF7F8;color:#0B326C;padding:10px;border:1px solid "
            "#B8DDE3;border-radius:4px;"
        )
        layout.addWidget(label)
        return label

    def build_setup(self) -> None:
        """Compose explicit metadata, workplace and copied timing acceptance controls.

        Args:
            None.

        Returns:
            None; previews never create records or copy source Shift timings.
        """
        layout = self.page_layouts[0]
        group = QGroupBox(self.text("Rotation details", "Detalles de la rotación"))
        form = QFormLayout(group)
        self.name = QLineEdit()
        self.name.setToolTip(
            self.text(
                "Name of the rotation selected above. Editing this field renames "
                "that same rotation.",
                "Nombre de la rotación seleccionada arriba. Editar este campo "
                "cambia el nombre de esa misma rotación.",
            )
        )
        self.day = OptionalDateEdit(self.text("Not set", "Sin definir"))
        self.day.setToolTip(
            self.text(
                "Choose the local rotation start date from the "
                "calendar, or type a complete date.",
                "Elija la fecha local de inicio en el "
                "calendario o ingrese una fecha completa.",
            )
        )
        self.description = MultilineEdit()
        form.addRow(self.text("Rotation name", "Nombre de la rotación"), self.name)
        form.addRow(
            self.text("Planned start date", "Fecha prevista de inicio"), self.day
        )
        form.addRow(self.text("Description", "Descripción"), self.description)
        self.create_button = self.button(
            self.text("Create rotation", "Crear rotación"), self.create_rotation
        )
        form.addRow(self.create_button)
        layout.addWidget(group)
        self.name.textEdited.connect(self.history.refresh)
        self.description.textEdited.connect(self.history.refresh)
        self.name.editingFinished.connect(self.metadata_finished)
        self.description.editingFinished.connect(self.metadata_finished)
        self.day.value_changed.connect(self.metadata_finished)
        self.setup_controls = QGroupBox(
            self.text("Workplace, Shift and boundaries", "Lugar, turno y límites")
        )
        setup = QVBoxLayout(self.setup_controls)
        self.scope_label = QLabel()
        self.scope_label.setWordWrap(True)
        setup.addWidget(self.scope_label)
        actions = QHBoxLayout()
        actions.addWidget(
            self.button(
                self.text("Choose Line and Shift…", "Elegir línea y turno…"),
                self.choose_scope,
            )
        )
        self.workplace = QCheckBox(
            self.text(
                "Use station-specific Job placements in this Line / Shift",
                "Usar ubicaciones de trabajos de esta línea / turno",
            )
        )
        self.workplace.setToolTip(
            self.text(
                "Checked: station-specific placements are separate rotation "
                "positions within this Line/Shift. Unchecked: choose each Job once"
                " globally, regardless of station.",
                "Marcado: las ubicaciones en estaciones son posiciones "
                "independientes de esta línea/turno. Sin marcar: cada trabajo se "
                "elige una vez, sin depender de la estación.",
            )
        )
        self.workplace.clicked.connect(self.scope_mode_changed)
        actions.addWidget(self.workplace)
        actions.addWidget(
            self.button(
                self.text("Organization…", "Organización…"), self.open_organization
            )
        )
        setup.addLayout(actions)
        clock = QHBoxLayout()
        self.clock_label = QLabel()
        self.clock_label.setWordWrap(True)
        clock.addWidget(self.clock_label, 1)
        clock.addWidget(
            self.button(
                self.text("Use Shift timing", "Usar tiempos del turno"),
                self.use_shift_timing,
            )
        )
        clock.addWidget(
            self.button(
                self.text("Edit rotation timing…", "Editar tiempos de la rotación…"),
                self.edit_timing,
            )
        )
        setup.addLayout(clock)
        clocks = QHBoxLayout()
        self.start_time = OptionalTimeEdit(self.text("Not set", "Sin definir"))
        self.end_time = OptionalTimeEdit(self.text("Not set", "Sin definir"))
        for control in (self.start_time, self.end_time):
            control.setToolTip(
                self.text(
                    "24-hour HH:mm. An end at or before the start "
                    "belongs to the following day. Edits affect "
                    "this rotation copy, not the recurring Shift.",
                    "Formato HH:mm de 24 horas. Un término igual o "
                    "anterior al inicio corresponde al día "
                    "siguiente. Se modifica esta rotación, no el "
                    "turno recurrente.",
                )
            )
        for label, field in [
            (self.text("Rotation start", "Inicio de rotación"), self.start_time),
            (self.text("Rotation end", "Término de rotación"), self.end_time),
        ]:
            clocks.addWidget(QLabel(label))
            field.setMaximumWidth(140)
            field.setToolTip(
                self.text(
                    "24-hour clock; end at/before start means next day.",
                    "Hora de 24 h; término igual/anterior indica el día siguiente.",
                )
            )
            field.value_changed.connect(self.history.refresh)
            field.editingFinished.connect(self.clocks_finished)
            clocks.addWidget(field)
        clocks.addStretch(1)
        clocks.addWidget(
            QLabel(
                self.text(
                    "Independent copy · recurring Shift unchanged",
                    "Copia independiente · el turno no cambia",
                )
            )
        )
        setup.addLayout(clocks)
        self.timeline = RotationTimeline(language=self.language)
        self.timeline.timing_changed.connect(self.timeline_changed)
        setup.addWidget(self.timeline)
        layout.addWidget(self.setup_controls)
        self.observation = QGroupBox(
            self.text(
                "Do you have an existing rotation to use as the baseline?",
                "¿Tiene una rotación existente para usar como base?",
            )
        )
        row = QHBoxLayout(self.observation)
        row.addStretch(1)
        self.observed = QButtonGroup(self)
        for flag, en, es in [
            (
                1,
                "Yes · enter baseline assignments",
                "Sí · ingresar asignaciones de base",
            ),
            (0, "No · create a proposal", "No · crear una propuesta"),
        ]:
            button = self.button(
                self.text(en, es), partial(self.choose_observed, bool(flag))
            )
            button.setCheckable(True)
            button.setObjectName("observedChoice")
            button.setMinimumHeight(48)
            set_action_icon(
                button, self.icons["apply_rotation" if flag else "generate_proposal"]
            )
            self.observed.addButton(button, flag)
            row.addWidget(button)
        row.addStretch(1)
        layout.addWidget(self.observation)
        layout.addStretch(1)

    def build_catalogs(self) -> None:
        """Compose catalog-backed selection with no inferred workers or Jobs.

        Args:
            None.

        Returns:
            None; data is accepted only by explicit picker confirmation.
        """
        self.jobs_table = AdaptiveTableWidget()
        self.workers_table = AdaptiveTableWidget()
        for index, table, caption, callback, manage, manage_caption in [
            (
                1,
                self.jobs_table,
                self.text("Select Jobs…", "Seleccionar trabajos…"),
                self.choose_jobs,
                self.open_jobs,
                self.text("Create / edit Jobs…", "Crear / editar trabajos…"),
            ),
            (
                2,
                self.workers_table,
                self.text("Select workers…", "Seleccionar trabajadores…"),
                self.choose_workers,
                self.open_workers,
                self.text("Create / edit workers…", "Crear / editar trabajadores…"),
            ),
        ]:
            actions = QHBoxLayout()
            actions.addWidget(self.button(caption, callback))
            if manage is not None:
                actions.addWidget(self.button(manage_caption, manage))
            actions.addStretch(1)
            self.page_layouts[index].addLayout(actions)
            table.setAlternatingRowColors(True)
            self.page_layouts[index].addWidget(table, 1)
        self.rules_label = self.notice("", self.page_layouts[2])
        rule_actions = QHBoxLayout()
        rule_actions.addWidget(
            self.button(
                self.text("Worker restrictions…", "Restricciones de trabajadores…"),
                self.edit_rules,
            )
        )
        self.page_layouts[2].addLayout(rule_actions)
        self.neighbors = JrotNeighborSection(
            self.language, self.choose_neighbor, self.clear_neighbor, icons=self.icons
        )
        self.page_layouts[2].addWidget(self.neighbors)

    def build_review(self) -> None:
        """Compose selected-tool readiness and literal current Job risk summaries.

        Args:
            None.

        Returns:
            None; exposures and optimization outcomes are never fabricated.
        """
        row = QHBoxLayout()
        row.addWidget(QLabel(self.text("Analyze using", "Analizar con")))
        strip = QHBoxLayout()
        strip.setSpacing(0)
        self.tools: dict[AssessmentKind, QToolButton] = {}
        for kind in AssessmentKind:
            check = QToolButton()
            check.setText(tool_caption(kind.value))
            check.setCheckable(True)
            check.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            check.setObjectName("jrotAnalysisTool")
            check.setIcon(assessment_tool_icon(self.icons, kind))
            check.setIconSize(QSize(24, 24))
            check.setFixedSize(104, 36)
            check.setToolTip(
                self.text(
                    (
                        "Include this tool in the optimization. Select one, two or all "
                        "three tools."
                    ),
                    "Incluir esta herramienta en la optimización. "
                    "Elija una, dos o las tres.",
                )
            )
            check.setStyleSheet(
                "QToolButton#jrotAnalysisTool {padding:2px 8px;color:#304652;"
                "background:white;border:1px solid #AFC0CB;border-radius:0;"
                "font-weight:600;} QToolButton#jrotAnalysisTool:hover "
                "{background:#EAF7F8;} QToolButton#jrotAnalysisTool:checked "
                "{color:#087E91;background:#DDF3F5;border-color:#08A9B5;}"
            )
            check.clicked.connect(self.tools_changed)
            self.tools[kind] = check
            strip.addWidget(check)
        row.addLayout(strip)
        row.addStretch(1)
        self.page_layouts[5].addLayout(row)
        self.readiness = self.notice("", self.page_layouts[5])
        self.risk_tabs = QTabWidget()
        self.risk_tabs.setIconSize(QSize(24, 24))
        self.summary_tabs = QTabWidget()
        self.start_notice = QLabel()
        self.start_notice.setWordWrap(True)
        self.start_table = AdaptiveTableWidget()
        start_page = QWidget()
        start_layout = QVBoxLayout(start_page)
        start_layout.addWidget(self.start_notice)
        start_layout.addWidget(self.start_table, 1)
        self.summary_tabs.addTab(
            start_page,
            self.text("Worker schedule averages", "Promedios de trabajadores"),
        )
        self.summary_tabs.addTab(
            self.risk_tabs, self.text("Job risk values", "Riesgos de trabajos")
        )
        self.page_layouts[5].addWidget(self.summary_tabs, 1)
        self.notice(
            self.text(
                "These are current Job risks. The optimization preview uses"
                " copied productive block durations. Worker indices come "
                "from the entered schedule and current Job values.",
                "Estos son riesgos actuales de trabajos. La optimización "
                "usa duraciones productivas copiadas. Los índices usan "
                "la rotación ingresada y riesgos actuales de trabajos.",
            ),
            self.page_layouts[5],
        )

    def current(self) -> RotationScenario | None:
        """Read the exact current scenario through the borrowed project capability.

        Args:
            None.

        Returns:
            Current accepted state, or None if uncreated/deleted.

        Raises:
            RuntimeError: This dialog's project session was replaced.
        """
        if self.workspace.editing is not self.owner:
            raise RuntimeError("The project changed; close and reopen this window.")
        return next(
            (
                s
                for s in self.repository.load_rotation_scenarios()
                if s.scenario_id == self.view.scenario_id
            ),
            None,
        )

    def show_error(self, error: Exception | str) -> None:
        """Retain input and surface failures without claiming an accepted operation.

        Args:
            error: User-correctable validation or owned operational failure.

        Returns:
            None; no history or persistence action occurs here.
        """
        self.error.setText(str(error))

    def confirm(self, text: str) -> bool:
        """Use the common No-default warning policy for destructive acceptance.

        Args:
            text: Exact consequence requiring consent.

        Returns:
            True only for explicit Yes.
        """
        return bool(
            QMessageBox.question(
                self,
                self.text("Confirm change", "Confirmar cambio"),
                text,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            == QMessageBox.Yes
        )

    def edit_inputs(
        self, expected: RotationScenario, change: RotationEntryChange
    ) -> bool:
        """Accept one expected-state edit after warning for removed matrix entries.

        Args:
            expected: Exact accepted scenario that produced this proposal.
            change: Complete independent candidate and explicit lost-cell list.

        Returns:
            True on acceptance; cancelled/failed edits preserve prior data.
        """
        if (change.lost_cells or change.lost_rules) and not self.confirm(
            self.text(
                "This change removes entered schedule cells: ",
                "Este cambio elimina celdas ingresadas: ",
            )
            + str(len(change.lost_cells))
            + self.text("; removed restrictions: ", "; restricciones eliminadas: ")
            + str(len(change.lost_rules))
            + self.text(
                ". Continue? Undo restores them.",
                ". ¿Continuar? Deshacer las restaura.",
            )
        ):
            return False
        try:
            if self.current() != expected:
                raise ValueError(
                    self.text(
                        "The rotation changed. Reload before editing.",
                        "La rotación cambió. Vuelva a cargar.",
                    )
                )
            self.repository.replace_rotation_scenario(
                expected, replace(expected, inputs=change.inputs)
            )
            self.scenario = self.current()
            self.error.clear()
            return True
        except Exception as error:
            _LOG.exception("Guided scenario edit failed")
            self.show_error(error)
            return False

    def metadata_finished(self) -> None:
        """Accept a completed metadata field; creation remains explicit and cancellable.

        Args:
            None.

        Returns:
            None; invalid name/date stays visible for correction.
        """
        if self._loading or self.scenario is None:
            return
        try:
            current = self.current()
            if current != self.scenario or current is None:
                raise ValueError("Rotation metadata changed; reload before editing.")
            day = (
                date.fromisoformat(self.day.date_text())
                if self.day.date_text()
                else None
            )
            candidate = replace(
                current,
                name=self.name.text(),
                description=self.description.text() or None,
                inputs=replace(current.inputs, planned_date=day),
            )
            self.repository.replace_rotation_scenario(current, candidate)
            self.scenario = candidate
            self.error.clear()
            self.refresh_names()
        except Exception as error:
            self.show_error(error)
        self.history.refresh()

    def pending_action(self) -> str | None:
        """Expose pending accepted-record data to the one shared history adapter.

        Args:
            None.

        Returns:
            Action identity for unfinished metadata/calculator data, otherwise None.
        """
        if not hasattr(self, "job_panel") or self.scenario is None:
            return None
        if self.job_panel.has_pending():
            return "save_job_details"
        current = self.scenario
        return (
            "replace_rotation_scenario"
            if (
                self.clock_pending()
                or self.name.text() != current.name
                or (self.description.text() or None) != current.description
                or (self.day.date_text() or None)
                != (
                    current.inputs.planned_date.isoformat()
                    if current.inputs.planned_date
                    else None
                )
            )
            else None
        )

    def prepare(self) -> bool:
        """Finish valid pending cells without losing invalid text.

        Args:
            None.

        Returns:
            False leaves correction in place; True means no unaccepted record edits
            remain.
        """
        if not hasattr(self, "job_panel"):
            return True
        if not self.job_panel.prepare():
            return False
        if self.scenario is not None and self.pending_action() is not None:
            self.metadata_finished()
            if self.clock_pending():
                self.clocks_finished()
        return self.pending_action() is None

    def refresh_names(self) -> None:
        """Project names/IDs without accepting a selection or scientific change.

        Args:
            None.

        Returns:
            None; duplicate display names retain distinct exact IDs.
        """
        self.scenarios.blockSignals(True)
        self.scenarios.clear()
        self.scenarios.addItem(
            self.text(
                "Not created yet — enter a name in step 01",
                "Sin crear — ingrese un nombre en el paso 01",
            ),
            None,
        )
        records = self.repository.load_rotation_scenarios()
        for record in records:
            label = record.name
            if record.inputs.planned_date is not None:
                label += " · " + record.inputs.planned_date.isoformat()
            if (
                sum(
                    other.name == record.name
                    and other.inputs.planned_date == record.inputs.planned_date
                    for other in records
                )
                > 1
            ):
                label += " · " + record.scenario_id
            self.scenarios.addItem(label, record.scenario_id)
            self.scenarios.setItemData(
                self.scenarios.count() - 1,
                record.name + "\nID: " + record.scenario_id,
                Qt.ItemDataRole.ToolTipRole,
            )
        self.scenarios.setCurrentIndex(
            max(0, self.scenarios.findData(self.view.scenario_id))
        )
        self.scenarios.blockSignals(False)

    def reload(self) -> None:
        """Project accepted/replayed state with callbacks blocked and no inferred data.

        Args:
            None.

        Returns:
            None; restored data and view use the same chronological project state.
        """
        self._loading = True
        try:
            retained = self.owner.editor(_VIEW_KEY)
            if isinstance(retained, JrotView):
                self.view = retained
            self.scenario = self.current()
            if self.scenario is None and self.view.scenario_id is not None:
                chosen = opening_scenario(
                    self.repository.load_rotation_scenarios(),
                    self.repository.last_rotation_selection(),
                )
                self.view = replace(
                    self.view,
                    scenario_id=chosen.scenario_id if chosen else None,
                    page=0,
                    job_id=None,
                )
                self.scenario = chosen
            self._generation += 1
            record = self.scenario
            inputs = record.inputs if record else RotationInputs()
            self.name.setText(record.name if record else "")
            self.description.setText(record.description or "" if record else "")
            self.day.set_value(
                inputs.planned_date.isoformat()
                if inputs.planned_date
                else (date.today().isoformat() if record is None else None)
            )
            self.create_button.setVisible(record is None)
            self.creation_notice.setVisible(record is None)
            self.setup_controls.setEnabled(record is not None)
            self.observation.setEnabled(record is not None)
            self.scope_label.setText(
                " / ".join(
                    (
                        inputs.line.plant_name,
                        inputs.line.section_name,
                        inputs.line.line_name,
                    )
                )
                if inputs.line
                else self.text(
                    "All Jobs · no Line selected",
                    "Todos los trabajos · sin línea seleccionada",
                )
            )
            self.scope_label.setText(
                self.scope_label.text()
                + " · "
                + self.text("Shift: ", "Turno: ")
                + (inputs.shift_id or "—")
            )
            self.workplace.setChecked(bool(inputs.scope))
            button = self.observed.button(int(inputs.baseline is not None))
            if button is not None:
                button.setChecked(True)
            self.project_timing(inputs)
            self.refresh_names()
            self.refresh_catalogs(inputs)
            self.refresh_matrix(inputs)
            self.refresh_job_list(inputs)
            self.job_panel.set_source_modes(self.view.direct_modes)
            self.job_panel.show_kind(self.view.kind)
            self.job_panel.bind(self.view.job_id)
            self.refresh_review(inputs)
            self.solve.refresh()
            self.project_page()
            self.owner.project_editor(_VIEW_KEY, self.view)
        except Exception as error:
            _LOG.exception("Guided scenario reload failed")
            self.show_error(error)
        finally:
            self._loading = False

    def project_page(self) -> None:
        """Display the accepted page/rail without recording an edit.

        Args:
            None.

        Returns:
            None; every review page remains accessible even when entry is incomplete.
        """
        self.pages.setCurrentIndex(self.view.page)
        self.comparison.refresh()
        for index, button in enumerate(self.drawer.buttons):
            button.setChecked(index == self.view.page)
        self.back.setEnabled(self.view.page > 0)
        self.next.setEnabled(self.view.page < len(_STEPS) - 1)
        keep = (
            self.view.page == 6
            and self.solve.preview is not None
            and self.solve.run is not None
        )
        self.next.setText(
            self.text("Keep result & compare", "Conservar y comparar")
            if keep
            else self.text("Continue", "Continuar")
        )
        self.page_caption.setText(
            f"{self.view.page + 1} / {len(_STEPS)} · "
            + self.text(
                "Main Save stores accepted changes",
                "Guardar publica los cambios aceptados",
            )
        )

    def record_view(self, view: JrotView) -> None:
        """Record a clean navigation step in shared chronological project history.

        Args:
            view: Immutable desired selection/page/tool state.

        Returns:
            None; clean page navigation does not rewrite scientific inputs.
        """
        self.view = view
        self.owner.set_editor(_VIEW_KEY, view, "jrot.view")
        self.project_page()

    def go(self, page: int) -> None:
        """Review any numbered page after preparing valid pending data.

        Args:
            page: Offered zero-based page, including currently incomplete later
            pages.

        Returns:
            None; invalid input stays visible rather than being silently discarded.
        """
        if (
            self._loading
            or self.planning_busy()
            or not 0 <= page < len(_STEPS)
            or not self.prepare()
        ):
            return
        self.record_view(replace(self.view, page=page))
        self.solve.refresh()
        if self.scenario is not None:
            self.refresh_review(self.scenario.inputs)

    def relative(self, delta: int) -> None:
        """Move Back/Continue using the same free navigation as the sidebar.

        Args:
            delta: Signed page increment.

        Returns:
            None; no completion gate is imposed merely to review a page.
        """
        if (
            delta > 0
            and self.view.page == 6
            and self.solve.preview is not None
            and self.solve.run is not None
        ):
            self.solve.keep_result()
            if self.solve.preview is not None:
                return
        self.go(self.view.page + delta)

    def select_record(self, record: RotationScenario | None) -> None:
        """Group saved selection and its projected view into one chronological action.

        Args:
            record: Existing selected rotation, or None for an unaccepted creation form.

        Returns:
            None; kept results open 08 collapsed, unsolved records 01 expanded;
            selecting the empty form creates no record.
        """
        scenario_id = record.scenario_id if record else None
        with self.owner.stage():
            self.repository.select_rotation_scenario(scenario_id)
            self.view = JrotView(scenario_id, page=7 if record and record.run else 0)
            self.owner.set_editor(_VIEW_KEY, self.view, "jrot.view")
        self.owner.record("select_rotation_scenario")
        self.reload()
        self.drawer.pin.setChecked(record is None or record.run is None)

    def scenario_selected(self, _index: int) -> None:
        """Prepare current edits before choosing an exact existing scenario ID.

        Args:
            _index: Native combo index; ID comes from item data, never its caption.

        Returns:
            None; failed pending input restores the prior visible selection.
        """
        if self._loading:
            return
        key = self.scenarios.currentData()
        if not self.prepare():
            self.refresh_names()
            return
        record = next(
            (
                s
                for s in self.repository.load_rotation_scenarios()
                if s.scenario_id == key
            ),
            None,
        )
        self.select_record(record)

    def new_rotation(self) -> None:
        """Open explicit creation after retaining accepted edits to the current plan.

        Args:
            None.

        Returns:
            None; the form itself owns no saved identity until Create is accepted.
        """
        if self.prepare():
            self.select_record(None)

    def create_rotation(self) -> None:
        """Accept required name/date and a generated stable scenario identity once.

        Args:
            None.

        Returns:
            None; validation failure keeps the creation form unchanged.
        """
        if self.scenario is not None:
            return
        try:
            record = create_scenario(
                self.metadata.project_id,
                uuid4().hex,
                self.name.text(),
                date.fromisoformat(self.day.date_text()),
            )
            record = replace(record, description=self.description.text() or None)
            with self.owner.stage():
                self.repository.replace_rotation_scenario(None, record)
                self.view = JrotView(record.scenario_id)
                self.owner.set_editor(_VIEW_KEY, self.view, "jrot.view")
            self.owner.record("replace_rotation_scenario")
            self.reload()
        except Exception as error:
            self.show_error(error)

    def duplicate(self) -> None:
        """Create an independent named copy without replacing the source or its run.

        Args:
            None.

        Returns:
            None; explicit consent names the independent copy and preserves unknown
            dates.
        """
        if not self.prepare() or self.scenario is None:
            return
        original = self.scenario
        from PyQt5.QtWidgets import QInputDialog

        name, accepted = QInputDialog.getText(
            self,
            self.text("Duplicate rotation", "Duplicar rotación"),
            self.text("Name for independent copy", "Nombre de la copia independiente"),
            text=self.scenario.name + self.text(" · copy", " · copia"),
        )
        if not accepted:
            return
        try:
            if self.current() != original:
                raise ValueError("The selected rotation changed; retry duplication.")
            day = original.inputs.planned_date
            if day is None:
                raise ValueError(
                    self.text(
                        "Set a planned date before duplicating this older rotation.",
                        "Defina una fecha antes de duplicar esta rotación anterior.",
                    )
                )
            record = duplicate_scenario(original, uuid4().hex, name, day)
            with self.owner.stage():
                self.repository.replace_rotation_scenario(None, record)
                self.view = JrotView(record.scenario_id)
                self.owner.set_editor(_VIEW_KEY, self.view, "jrot.view")
            self.owner.record("replace_rotation_scenario")
            self.reload()
        except Exception as error:
            self.show_error(error)

    def delete_rotation(self) -> None:
        """Delete only the selected plan after explicit consent, with shared replay.

        Args:
            None.

        Returns:
            None; unrelated Jobs, source assessments and other scenarios remain exact.
        """
        if not self.prepare() or self.scenario is None:
            return
        original = self.scenario
        if not self.confirm(
            self.text(
                "Delete this rotation and its retained run? Undo restores it.",
                "¿Eliminar esta rotación y su resultado? Deshacer los restaura.",
            )
        ):
            return
        try:
            if self.current() != original:
                raise ValueError("The selected rotation changed; retry deletion.")
            with self.owner.stage():
                self.repository.replace_rotation_scenario(original, None)
                self.view = JrotView()
                self.owner.set_editor(_VIEW_KEY, self.view, "jrot.view")
            self.owner.record("replace_rotation_scenario")
            self.reload()
        except Exception as error:
            self.show_error(error)

    def choose_observed(self, observed: bool) -> None:
        """Accept explicit Yes/No independently of subsequent participant entry.

        Args:
            observed: True means an entered, possibly still empty observation exists.

        Returns:
            None; switching to No warns before removing entered baseline cells.
        """
        if self.prepare() and self.scenario is not None:
            self.edit_inputs(
                self.scenario, choose_observed_rotation(self.scenario.inputs, observed)
            )
            self.reload()

    def choose_scope(self) -> None:
        """Select a real Line and Shift through the shared read-only hierarchy picker.

        Args:
            None.

        Returns:
            None; no organizational defaults or permanent assignments are created.
        """
        if not self.prepare() or self.scenario is None:
            return
        record = self.scenario
        inputs = record.inputs
        hierarchy = self.workspace.read_hierarchy().hierarchy
        records = {
            r.keys[0]: dict(r.attributes)
            for r in hierarchy.organization
            if r.kind.value == "Shift"
        }
        shifts = tuple(
            (
                key,
                str(records[key].get("description") or "") if key in records else "",
                str(records[key].get("start_time") or "") if key in records else "",
                str(records[key].get("end_time") or "") if key in records else "",
            )
            for key in hierarchy.work.shifts
        )
        line = inputs.line
        path = (line.plant_name, line.section_name, line.line_name) if line else ()
        dialog = WorkplaceScopePicker(
            hierarchy,
            self.icons,
            shifts,
            path,
            inputs.shift_id or "",
            self,
            language=self.language,
            lines_only=True,
        )
        try:
            if dialog.exec() == QDialog.Accepted:
                chosen = (
                    LineKey(*dialog.path)
                    if dialog.path is not None and len(dialog.path) == 3
                    else None
                )
                change = scope_rotation_inputs(
                    inputs,
                    hierarchy,
                    self.workspace.read_jobs().jobs,
                    chosen,
                    dialog.shift_id,
                    bool(inputs.scope),
                )
                self.edit_inputs(record, change)
                self.reload()
        except Exception as error:
            self.show_error(error)
        finally:
            dialog.deleteLater()

    def scope_mode_changed(self) -> None:
        """Apply scope without silently retaining unavailable targets.

        Args:
            None.

        Returns:
            None; invalid scope and cancelled loss restore the previous controls.
        """
        if self._loading or not self.prepare() or self.scenario is None:
            return
        try:
            inputs = self.scenario.inputs
            change = scope_rotation_inputs(
                inputs,
                self.workspace.read_hierarchy().hierarchy,
                self.workspace.read_jobs().jobs,
                inputs.line,
                inputs.shift_id,
                self.workplace.isChecked(),
            )
            self.edit_inputs(self.scenario, change)
            self.reload()
        except Exception as error:
            self.workplace.setChecked(bool(self.scenario.inputs.scope))
            self.show_error(error)

    def clock_pending(self) -> bool:
        """Detect clock edits without accepting partial or inferred time.

        Args:
            None.

        Returns:
            True when either visible clock differs from the accepted independent copy.
        """
        if self.scenario is None:
            return False
        inputs = self.scenario.inputs
        clock = (
            ShiftClock(inputs.start_minute, inputs.timing.shift_minutes)
            if inputs.timing is not None and inputs.start_minute is not None
            else None
        )
        expected = (
            (clock.label(0)[:5], clock.label(clock.span_minutes)[:5])
            if clock
            else ("", "")
        )
        return (self.start_time.clock_text(), self.end_time.clock_text()) != expected

    def project_timing(self, inputs: RotationInputs) -> None:
        """Project clocks/timeline without resetting other pending forms.

        Args:
            inputs: Current independent clock/timing pair or explicitly absent pair.

        Returns:
            None; other pending metadata and calculator tokens are retained.
        """
        loading = self._loading
        self._loading = True
        try:
            self.timeline.setVisible(inputs.timing is not None)
            if inputs.timing is not None and inputs.start_minute is not None:
                clock = ShiftClock(inputs.start_minute, inputs.timing.shift_minutes)
                self.start_time.set_value(clock.label(0)[:5])
                self.end_time.set_value(clock.label(clock.span_minutes)[:5])
                self.timeline.set_timing(inputs.timing, clock)
                self.clock_label.setText(
                    f"{clock.label(0)} → {clock.label(clock.span_minutes)} · "
                    + str(len(inputs.timing.block_minutes))
                    + self.text(" blocks · ", " bloques · ")
                    + str(inputs.timing.productive_minutes)
                    + self.text(" productive min", " min productivos")
                )
            else:
                self.start_time.set_value(None)
                self.end_time.set_value(None)
                self.clock_label.setText(
                    self.text(
                        "Rotation timing has not been copied or entered.",
                        "Los tiempos de esta rotación no están definidos.",
                    )
                )
        finally:
            self._loading = loading

    def clocks_finished(self) -> None:
        """Accept a complete clock pair while retaining unfinished text.

        Args:
            None.

        Returns:
            None; Shift clocks/templates are never modified by this acceptance.
        """
        if self._loading or self.scenario is None or not self.clock_pending():
            return
        try:
            record = self.scenario
            start, end = self.start_time.clock_text(), self.end_time.clock_text()
            if not start and not end:
                if not self.confirm(
                    self.text(
                        "Clear this rotation's clock and timing?",
                        "¿Quitar horas y tiempos de esta rotación?",
                    )
                ):
                    self.project_timing(record.inputs)
                    return
                change = reshape_rotation_inputs(
                    record.inputs, timing=None, start_minute=None, replace_timing=True
                )
            else:
                change = reclock_rotation_inputs(
                    record.inputs, clock_minute(start), clock_minute(end)
                )
            if self.edit_inputs(record, change):
                self.project_timing(change.inputs)
                self._generation += 1
                self.refresh_matrix(change.inputs)
                self.refresh_review(change.inputs)
        except ValueError as error:
            self.show_error(error)
        self.history.refresh()

    def use_shift_timing(self) -> None:
        """Explicitly copy Shift timing or an equal-block proposal.

        Args:
            None.

        Returns:
            None; future Shift template edits cannot reinterpret this independent copy.
        """
        if not self.prepare() or self.scenario is None:
            return
        record = self.scenario
        try:
            key = record.inputs.shift_id
            if key is None:
                raise ValueError(
                    self.text("Choose a Shift first.", "Seleccione un turno primero.")
                )
            clock = shift_clock(self.workspace.read_hierarchy().hierarchy, key)
            template = next(
                (t for t in self.workspace.load_shift_timings() if t.shift_id == key),
                None,
            )
            timing = (
                template.timing
                if template
                else equal_timing(clock.span_minutes, min(4, clock.span_minutes))
            )
            if record.inputs.timing is not None and not self.confirm(
                self.text(
                    "Replace the copied timing with this Shift's current timing?",
                    "¿Reemplazar la copia de tiempos por los del turno actual?",
                )
            ):
                return
            change = reshape_rotation_inputs(
                record.inputs,
                timing=timing,
                replace_timing=True,
                start_minute=clock.start_minute,
            )
            self.edit_inputs(record, change)
            self.reload()
        except Exception as error:
            self.show_error(error)

    def timing_target(
        self, scenario_id: str
    ) -> tuple[ShiftClock, RotationTiming | None]:
        """Read copied timing under exact scenario ownership.

        Args:
            scenario_id: Stable identity captured before opening the timing editor.

        Returns:
            Independent copied clock/model, or the selected Shift clock as a preview.

        Raises:
            ValueError: The record or a complete source clock is unavailable.
            RuntimeError: The original project editing session was replaced.
        """
        if self.view.scenario_id != scenario_id:
            raise ValueError("The timing target is no longer selected.")
        record = self.current()
        if record is None:
            raise ValueError("The timing target no longer exists.")
        inputs = record.inputs
        if inputs.timing is not None and inputs.start_minute is not None:
            return ShiftClock(
                inputs.start_minute, inputs.timing.shift_minutes
            ), inputs.timing
        if inputs.shift_id is None:
            raise ValueError(
                self.text(
                    "Choose a Shift with complete clocks first.",
                    "Seleccione un turno con horas completas.",
                )
            )
        return shift_clock(
            self.workspace.read_hierarchy().hierarchy, inputs.shift_id
        ), None

    def write_timing(
        self,
        scenario_id: str,
        expected: RotationTiming | None,
        candidate: RotationTiming | None,
    ) -> bool:
        """Accept one copied timing proposal; source Shift templates are never written.

        Args:
            scenario_id: Captured exact target identity.
            expected: Last timing shown by the reusable editor.
            candidate: Complete replacement, or an explicitly cleared copy.

        Returns:
            False rejects stale/lost-cell consent; True accepts one shared project edit.

        Raises:
            ValueError: Target ownership or expected copied timing changed.
            RuntimeError: The original project editing session was replaced.
        """
        clock, current = self.timing_target(scenario_id)
        record = self.current()
        if record is None or current != expected:
            raise ValueError("Rotation timing changed; reload before editing.")
        return self.edit_inputs(
            record,
            reshape_timed_rotation_inputs(
                record.inputs,
                candidate,
                clock.start_minute if candidate is not None else None,
            ),
        )

    def edit_timing(self) -> None:
        """Open the reusable timeline/table editor on this scenario's independent copy.

        Args:
            None.

        Returns:
            None; shared Undo/Redo remains synchronized with the main project.
        """
        if not self.prepare() or self.scenario is None:
            return
        key = self.scenario.scenario_id
        try:
            self.timing_target(key)
            dialog = RotationTimingDialog(
                self.workspace,
                self.scenario.inputs.shift_id or "",
                self.icons,
                self.language,
                self,
                read_target=partial(self.timing_target, key),
                write_target=partial(self.write_timing, key),
                target_label=self.scenario.name,
            )
            try:
                dialog.exec()
            finally:
                dialog.deleteLater()
                self.reload()
        except Exception as error:
            self.show_error(error)

    def timeline_changed(self, timing: object) -> None:
        """Accept one completed timeline gesture as one scenario edit.

        Args:
            timing: Shared widget's typed complete proposed timing.

        Returns:
            None; cancelled/stale gestures restore the accepted projection.
        """
        if (
            isinstance(timing, RotationTiming)
            and self.prepare()
            and self.scenario is not None
        ):
            inputs = self.scenario.inputs
            self.edit_inputs(
                self.scenario,
                reshape_timed_rotation_inputs(inputs, timing, inputs.start_minute),
            )
            self.reload()

    def choose_jobs(self) -> None:
        """Offer real global Jobs or exact scoped placements with current result colors.

        Args:
            None.

        Returns:
            None; offered names are descriptive and opaque keys retain identity.
        """
        if not self.prepare() or self.scenario is None:
            return
        record = self.scenario
        inputs = record.inputs
        jobs = self.workspace.read_jobs().jobs
        risks = self.workspace.read_job_risk().risk
        names = {j.job_id: j.name for j in jobs.jobs}
        placements = {p.placement_id: p for p in jobs.placements}
        targets = rotation_entry_targets(inputs, jobs)
        choices = []
        for target in targets:
            measurements = {
                m.kind: m for m in risks.for_job(target.job_id).measurements
            }
            values, colors = [], []
            for kind in AssessmentKind:
                item = measurements.get(kind)
                value = item.probability_percent if item is not None else None
                values.append(f"{value:.1f}%" if value is not None else "—")
                colors.append(
                    RISK_APPEARANCES[classify_probability(value)].color_hex
                    if value is not None
                    else None
                )
            place = (
                placements.get(target.placement_id)
                if target.placement_id is not None
                else None
            )
            context = place.workplace if place else None
            path = (
                (
                    context.plant_name,
                    context.section_name,
                    context.line_name,
                    context.station_id,
                    context.shift_id,
                )
                if context
                else ()
            )
            choices.append(
                JrotCatalogChoice(
                    target.key,
                    (target.job_id, names[target.job_id], *values),
                    path,
                    (None, None, *colors),
                )
            )
        dialog = JrotCatalogPicker(
            self.text("Select Jobs", "Seleccionar trabajos"),
            ("Job ID", self.text("Job", "Trabajo"), "LiFFT", "DUET", "ST"),
            tuple(choices),
            tuple(t.key for t in inputs.targets),
            self.language,
            self,
            icons=self.icons,
            entity_icon="job_management",
        )
        try:
            if dialog.exec() == QDialog.Accepted:
                change = reshape_rotation_inputs(
                    inputs,
                    targets=tuple(t for t in targets if t.key in dialog.selected),
                )
                self.edit_inputs(record, change)
                self.reload()
        finally:
            dialog.deleteLater()

    def choose_workers(self) -> None:
        """Select existing workers without creating permanent assignment records.

        Args:
            None.

        Returns:
            None; removed nonempty schedule cells require consent before acceptance.
        """
        if not self.prepare() or self.scenario is None:
            return
        record = self.scenario
        hierarchy = self.workspace.read_hierarchy().hierarchy
        locations = self.worker_locations()
        line = record.inputs.line
        choices = tuple(
            JrotCatalogChoice(
                w.worker_id,
                (
                    w.worker_id,
                    w.last_name or "",
                    w.first_name or "",
                    w.details.sex or "" if w.details else "",
                    self.worker_age(w.details.birth_date if w.details else None),
                    self.worker_location_text(w.worker_id, locations),
                ),
                in_scope=line is None
                or any(
                    (c.plant_name, c.section_name, c.line_name)
                    == (line.plant_name, line.section_name, line.line_name)
                    for c in locations.get(w.worker_id, ())
                ),
            )
            for w in hierarchy.work.workers
        )
        dialog = JrotCatalogPicker(
            self.text("Select workers", "Seleccionar trabajadores"),
            (
                "ID",
                self.text("Last name", "Apellido"),
                self.text("First name", "Nombre"),
                self.text("Sex", "Sexo"),
                self.text("Age", "Edad"),
                self.text("Assigned workplaces", "Lugares asignados"),
            ),
            choices,
            tuple(w.worker_id for w in record.inputs.workers),
            self.language,
            self,
            icons=self.icons,
            entity_icon="worker",
            scope_label=" / ".join((line.plant_name, line.section_name, line.line_name))
            if line
            else None,
        )
        try:
            if dialog.exec() == QDialog.Accepted:
                old = {w.worker_id: w for w in record.inputs.workers}
                workers = tuple(
                    old.get(key, RotationWorkerLink(key)) for key in dialog.selected
                )
                self.edit_inputs(
                    record,
                    reshape_rotation_inputs(record.inputs, workers=workers),
                )
                self.reload()
        finally:
            dialog.deleteLater()

    def table(
        self,
        table: QTableWidget,
        headers: tuple[str, ...],
        rows: tuple[tuple[str, ...], ...],
    ) -> None:
        """Project a read-only summary with full headings and native overflow scrolling.

        Args:
            table: Owned target table.
            headers: Literal display column headings.
            rows: Already formatted display values, never edit authorities.

        Returns:
            None; no controls infer or write values from these summaries.
        """
        style_rotation_table(table)
        table.clear()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(list(headers))
        table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(Qt.ItemFlags(Qt.ItemFlag.ItemIsEnabled))
                item.setToolTip(headers[column] + ": " + value)
                if numeric_display(value):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                table.setItem(row, column, item)
        header = table.horizontalHeader()
        assert header is not None
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(False)
        if isinstance(table, AdaptiveTableWidget):
            header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            if table is self.jobs_table:
                table.set_column_weights(
                    (0, 2, 3, 2, 2, 2), (80, 160, 240, 110, 110, 110)
                )
            elif table is self.workers_table:
                table.set_column_weights((0, 2, 3, 1, 1), (80, 170, 260, 100, 140))
            elif table is not self.start_table and len(headers) == 4:
                table.set_column_weights((0, 3, 2, 2), (90, 260, 160, 160))
            else:
                minima = tuple(
                    max(110, table.columnWidth(c)) if c == 0 else 130
                    for c in range(len(headers))
                )
                table.set_column_weights(tuple(1 for _ in headers), minima)
        else:
            for column in range(1, len(headers)):
                header.setSectionResizeMode(column, QHeaderView.Stretch)

    def target_caption(self, target: RotationTarget) -> str:
        """Resolve a human-readable physical position without exposing an opaque key.

        Args:
            target: Exact global Job or placement identity.

        Returns:
            Full hierarchy/Shift path, or the localized global Job scope caption.
        """
        placement = next(
            (
                p
                for p in self.workspace.read_jobs().jobs.placements
                if p.placement_id == target.placement_id
            ),
            None,
        )
        if placement is None:
            return self.text("Global Job", "Trabajo global")
        c = placement.workplace
        return " / ".join(
            (
                c.plant_name,
                c.section_name,
                c.line_name,
                c.station_id,
                self.text("Shift ", "Turno ") + c.shift_id,
            )
        )

    def refresh_catalogs(self, inputs: RotationInputs) -> None:
        """Display exact selected positions/workers without modifying their catalogs.

        Args:
            inputs: Accepted current scenario inputs or an empty creation projection.

        Returns:
            None; repeated placements remain distinct positions.
        """
        jobs = {j.job_id: j.name for j in self.workspace.read_jobs().jobs.jobs}
        risk = self.workspace.read_job_risk().risk
        self.table(
            self.jobs_table,
            (
                "Job ID",
                self.text("Job", "Trabajo"),
                self.text("Workplace", "Lugar de trabajo"),
                "LiFFT",
                "DUET",
                "ST",
            ),
            tuple(
                (
                    t.job_id,
                    jobs.get(t.job_id, "—"),
                    self.target_caption(t),
                    *(
                        f"{m.probability_percent:.1f}%"
                        if m is not None and m.probability_percent is not None
                        else "—"
                        for kind in AssessmentKind
                        for m in [
                            next(
                                (
                                    m
                                    for m in risk.for_job(t.job_id).measurements
                                    if m.kind is kind
                                ),
                                None,
                            )
                        ]
                    ),
                )
                for t in inputs.targets
            ),
        )
        for row, target in enumerate(inputs.targets):
            values = {
                m.kind: m.probability_percent
                for m in risk.for_job(target.job_id).measurements
            }
            for column, kind in enumerate(AssessmentKind, 3):
                value = values.get(kind)
                item = self.jobs_table.item(row, column)
                if item is not None and value is not None:
                    item.setBackground(
                        QColor(RISK_APPEARANCES[classify_probability(value)].color_hex)
                    )
        workers = {
            w.worker_id: w
            for w in self.workspace.read_hierarchy().hierarchy.work.workers
        }
        locations = self.worker_locations()
        details = {key: worker.details for key, worker in workers.items()}
        self.table(
            self.workers_table,
            (
                "ID",
                self.text("Worker", "Trabajador"),
                self.text("Assigned workplaces", "Lugares asignados"),
                self.text("Sex", "Sexo"),
                self.text("Age", "Edad"),
            ),
            tuple(
                (
                    w.worker_id,
                    " ".join(
                        (
                            workers[w.worker_id].first_name or "",
                            workers[w.worker_id].last_name or "",
                        )
                    )
                    if w.worker_id in workers
                    else "—",
                    self.worker_location_text(w.worker_id, locations),
                    detail.sex or "—"
                    if (detail := details.get(w.worker_id)) is not None
                    else "—",
                    self.worker_age(
                        detail.birth_date
                        if (detail := details.get(w.worker_id)) is not None
                        else None
                    ),
                )
                for w in inputs.workers
            ),
        )

    @staticmethod
    def worker_age(birth_date: str | None) -> str:
        """Project completed calendar years without changing the saved birth date.

        Args:
            birth_date: Canonical optional ISO birth date from the worker catalog.

        Returns:
            Age in completed years today, or a dash when birth date is absent.
        """
        if birth_date is None:
            return "—"
        born, today = date.fromisoformat(birth_date), date.today()
        return str(
            today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        )

    def worker_locations(self) -> dict[str, tuple[WorkplaceContext, ...]]:
        """Read active workplace assignments without inferring any rotation membership.

        Args:
            None.

        Returns:
            Worker IDs mapped to their distinct existing physical workplace owners.
        """
        locations: dict[str, tuple[WorkplaceContext, ...]] = {}
        for assignment in self.workspace.read_jobs().jobs.assignments:
            place = assignment.worker.workplace
            key = assignment.worker.worker_id
            if (
                assignment.active
                and place is not None
                and place not in locations.get(key, ())
            ):
                locations[key] = (*locations.get(key, ()), place)
        return locations

    def worker_location_text(
        self, worker: str, locations: Mapping[str, tuple[WorkplaceContext, ...]]
    ) -> str:
        """Format full existing association paths for summaries, search and tooltips.

        Args:
            worker: Literal worker identity.
            locations: Detached active workplace associations.

        Returns:
            Semicolon-separated ancestry/Shift paths or an explicit unassigned caption.
        """
        return "; ".join(
            " / ".join(
                (
                    c.plant_name,
                    c.section_name,
                    c.line_name,
                    c.station_id,
                    self.text("Shift ", "Turno ") + c.shift_id,
                )
            )
            for c in locations.get(worker, ())
        ) or self.text("No workplace assignment", "Sin lugar asignado")

    def refresh_matrix(self, inputs: RotationInputs) -> None:
        """Project only entered cells; each combo accepts exactly its edited cell.

        Args:
            inputs: Current observed/proposed draft and exact positions.

        Returns:
            None; untouched empty widgets never become default assignments.
        """
        observed = inputs.baseline is not None
        self.matrix_notice.setText(
            self.text(
                "Baseline assignments · edit cells, clear or generate a new "
                "starting schedule",
                "Asignaciones de base: edite, quite o genere otro horario inicial",
            )
            if observed
            else self.text(
                "No baseline entered. Optional proposal cells can be entered; "
                "use Generate initial proposal to create one.",
                "Sin base ingresada. Puede ingresar una propuesta; "
                "use Generar propuesta inicial para crearla.",
            )
        )
        horizon = (
            len(inputs.timing.block_minutes)
            if inputs.timing
            else next(
                (
                    len(rows[0].target_keys)
                    for rows in (inputs.baseline, inputs.proposed)
                    if rows
                ),
                1,
            )
        )
        self.matrix.clear()
        self.matrix.setColumnCount(horizon + 1)
        self.matrix.setHorizontalHeaderLabels(
            [
                self.text("Worker", "Trabajador"),
                *(
                    self.text(f"Block {i + 1}", f"Bloque {i + 1}")
                    + (
                        f"\n{inputs.timing.block_minutes[i]} min"
                        if inputs.timing
                        else ""
                    )
                    for i in range(horizon)
                ),
            ]
        )
        self.matrix.setRowCount(len(inputs.workers))
        names = {j.job_id: j.name for j in self.workspace.read_jobs().jobs.jobs}
        rows = {
            r.worker_id: r.target_keys
            for r in (inputs.baseline if observed else inputs.proposed) or ()
        }
        generation = self._generation
        workers = {
            w.worker_id: w
            for w in self.workspace.read_hierarchy().hierarchy.work.workers
        }
        for row, worker in enumerate(inputs.workers):
            person = workers.get(worker.worker_id)
            caption = worker.worker_id + (
                " · " + " ".join((person.first_name or "", person.last_name or ""))
                if person
                else ""
            )
            item = QTableWidgetItem(caption)
            item.setToolTip(caption)
            item.setFlags(Qt.ItemFlags(Qt.ItemFlag.ItemIsEnabled))
            self.matrix.setItem(row, 0, item)
            for block in range(horizon):
                combo = QComboBox()
                combo.addItem(self.text("Not entered", "Sin ingresar"), None)
                for target in inputs.targets:
                    combo.addItem(
                        target.job_id
                        + " · "
                        + names.get(target.job_id, "")
                        + (
                            f" · #{target.placement_id}"
                            if target.placement_id is not None
                            else ""
                        ),
                        target.key,
                    )
                keys = rows.get(worker.worker_id, ())
                key = keys[block] if block < len(keys) else None
                combo.setCurrentIndex(max(0, combo.findData(key)))
                combo.setToolTip(
                    caption
                    + " · "
                    + self.text(f"Block {block + 1}", f"Bloque {block + 1}")
                )
                combo.currentIndexChanged.connect(
                    partial(
                        self.matrix_changed,
                        generation,
                        self.view.scenario_id,
                        worker.worker_id,
                        block,
                        combo,
                    )
                )
                self.matrix.setCellWidget(row, block + 1, combo)
        header = self.matrix.horizontalHeader()
        assert header is not None
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(160)
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.matrix_headers.bind(inputs, horizon)

    def matrix_changed(
        self,
        generation: int,
        scenario_id: str | None,
        worker: str,
        block: int,
        combo: QComboBox,
        _index: int,
    ) -> None:
        """Accept one cell under current projection/session ownership.

        Args:
            generation: Projection epoch that created this cell editor.
            scenario_id: Exact record that owns it.
            worker: Existing participating worker ID.
            block: Zero-based block index.
            combo: Sender holding the exact offered position identity.
            _index: Native display index; it is never used as a position identity.

        Returns:
            None; retired widgets cannot overwrite a different record or restored state.
        """
        if (
            self._loading
            or generation != self._generation
            or scenario_id != self.view.scenario_id
        ):
            return
        try:
            current = self.current()
            if current is not None:
                if current != self.scenario:
                    raise ValueError(
                        self.text(
                            "The rotation changed; reload before editing.",
                            "La rotación cambió; vuelva a cargar.",
                        )
                    )
                changed = set_rotation_cell(
                    current.inputs, worker, block, combo.currentData()
                )
                if not self.edit_inputs(current, RotationEntryChange(changed)):
                    self.reload()
        except (ValueError, RuntimeError) as error:
            self.reload()
            self.show_error(error)

    def refresh_job_list(self, inputs: RotationInputs) -> None:
        """Project one calculator entry per exact unique selected Job.

        Args:
            inputs: Exact selected positions; repeated placements share Job values.

        Returns:
            None; projection does not copy, clear or recalculate Job values.
        """
        self.job_list.blockSignals(True)
        self.job_list.clear()
        names = {j.job_id: j.name for j in self.workspace.read_jobs().jobs.jobs}
        ids = tuple(dict.fromkeys(t.job_id for t in inputs.targets))
        for job_key in ids:
            measurements = (
                self.workspace.read_job_risk().risk.for_job(job_key).measurements
            )
            ready = sum(
                any(m.kind is kind and m.complete for m in measurements)
                for kind in inputs.tools
            )
            self.job_list.addItem(
                job_key
                + " · "
                + names.get(job_key, "")
                + f"\n{ready}/{len(inputs.tools)} "
                + self.text("tools ready", "herramientas listas")
            )
            item = self.job_list.item(self.job_list.count() - 1)
            assert item is not None
            item.setData(Qt.ItemDataRole.UserRole, job_key)
            item.setToolTip(item.text() + "\n" + self.job_issues(job_key, inputs))
        key = self.view.job_id if self.view.job_id in ids else next(iter(ids), None)
        self.view = replace(self.view, job_id=key)
        self.job_list.setCurrentRow(ids.index(key) if key else -1)
        self.job_list.blockSignals(False)
        self.job_readiness.setText(self.job_issues(key, inputs) if key else "")
        self.job_readiness.setToolTip(self.job_readiness.text())

    def job_issues(self, job_id: str, inputs: RotationInputs) -> str:
        """Describe incomplete selected-tool inputs without re-evaluating science.

        Args:
            job_id: Existing selected Job identity.
            inputs: Current analyzed tools.

        Returns:
            Localized first incomplete task per tool, or a readiness confirmation.
        """
        measurements = self.workspace.read_job_risk().risk.for_job(job_id).measurements
        issues = []
        fields = {
            "lever_arm": self.text("lever arm", "brazo de palanca"),
            "load": self.text("load", "carga"),
            "repetitions": self.text("repetitions", "repeticiones"),
            "omni_res_scale": "OMNI-Res",
            "direction": self.text("direction", "dirección"),
        }
        for kind in inputs.tools:
            measurement = next((m for m in measurements if m.kind is kind), None)
            if measurement is not None and measurement.complete:
                continue
            name = {
                AssessmentKind.LIFFT: "LiFFT",
                AssessmentKind.DUET: "DUET",
                AssessmentKind.TST: "ST",
            }[kind]
            detail = self.text(
                "enter task inputs or a direct result",
                "ingrese tareas o un resultado directo",
            )
            if measurement is not None and measurement.source is not None:
                tasks: tuple[LifftTask | DuetTask | TstTask, ...] = (
                    measurement.source.tasks
                )
                entered = tuple(
                    (i, t) for i, t in enumerate(tasks, 1) if task_has_data(t)
                )
                if entered:
                    detail = self.text(
                        "review inputs and calculate", "revise los datos y calcule"
                    )
                    for index, task in entered:
                        missing = tuple(
                            caption
                            for field, caption in fields.items()
                            if hasattr(task, field) and getattr(task, field) is None
                        )
                        if missing:
                            detail = (
                                self.text("Task ", "Tarea ")
                                + str(index)
                                + ": "
                                + ", ".join(missing)
                            )
                            break
            issues.append(name + " · " + detail)
        return (
            self.text("Still needed:\n", "Falta completar:\n") + "\n".join(issues)
            if issues
            else self.text(
                "Ready for the selected tools.",
                "Listo para las herramientas seleccionadas.",
            )
        )

    def job_selected(self, row: int) -> None:
        """Prepare pending input before selecting another shared Job calculator.

        Args:
            row: Native selected list row.

        Returns:
            None; a failed pending edit restores the previous Job selection.
        """
        if self._loading:
            return
        item = self.job_list.item(row)
        if not self.prepare():
            self._loading = True
            if self.scenario:
                self.refresh_job_list(self.scenario.inputs)
            self._loading = False
            return
        key = item.data(Qt.ItemDataRole.UserRole) if item else None
        self.record_view(replace(self.view, job_id=key))
        self.job_panel.bind(key)
        if self.scenario is not None:
            self.job_readiness.setText(
                self.job_issues(key, self.scenario.inputs) if key else ""
            )
            self.job_readiness.setToolTip(self.job_readiness.text())

    def tool_selected(self, kind: object) -> None:
        """Record calculator display-tool navigation without changing analysis tools.

        Args:
            kind: Shared panel's selected tool enum.

        Returns:
            None; one view entry can be replayed through Main or any secondary window.
        """
        if not self._loading and isinstance(kind, AssessmentKind):
            self.record_view(replace(self.view, kind=kind))

    def source_mode_selected(
        self, modes: tuple[tuple[str, AssessmentKind], ...]
    ) -> None:
        """Record blank-direct view choices, grouping destructive mode edits with data.

        Args:
            modes: Immutable explicit Job/tool view flags from the shared panel.

        Returns:
            None; the panel's staged data operation owns any combined history record.
        """
        if not self._loading:
            self.record_view(replace(self.view, direct_modes=modes))

    def save_markers(self, settings: GaugeMarkerSettings) -> None:
        """Forward personal gauge changes and synchronize both reused Job surfaces.

        Args:
            settings: Accepted application appearance options, never scenario data.

        Returns:
            None; no project history or native file write is introduced.

        Raises:
            OSError: Personal preference publication fails; previous options remain.
            ValueError: Personal settings are malformed or unsupported.
        """
        if self._change_markers is not None:
            self._change_markers(settings)
        self.gauge_markers = settings
        self.job_panel.results.risk_gauge.set_marker_settings(settings)

    def job_changed(self) -> None:
        """Refresh coefficient readiness while leaving the current task controls intact.

        Args:
            None.

        Returns:
            None; no rebind discards the user's focus or unfinished sibling cells.
        """
        if self.scenario is not None:
            self.refresh_catalogs(self.scenario.inputs)
            self.refresh_review(self.scenario.inputs)
            self.refresh_job_list(self.scenario.inputs)
            self.solve.refresh()

    def tools_changed(self) -> None:
        """Accept a nonempty analysis subset without changing calculator display tabs.

        Args:
            None.

        Returns:
            None; all seven nonempty subsets use the separate real planning controller.
        """
        if self._loading or not self.prepare() or self.scenario is None:
            return
        tools = tuple(k for k, c in self.tools.items() if c.isChecked())
        if tools:
            self.edit_inputs(
                self.scenario,
                RotationEntryChange(replace(self.scenario.inputs, tools=tools)),
            )
        self.refresh_review(self.scenario.inputs)
        self.refresh_job_list(self.scenario.inputs)

    def refresh_review(self, inputs: RotationInputs) -> None:
        """Show per-Job values and missing-input diagnostics.

        Args:
            inputs: Current accepted independent scenario inputs.

        Returns:
            None; unavailable measurements remain visibly absent.
        """
        risks = self.workspace.read_job_risk().risk
        issues = rotation_entry_issues(inputs, risks)
        labels = {
            "date": self.text("planned date", "fecha prevista"),
            "timing": self.text("copied timing", "tiempos copiados"),
            "participants": self.text(
                "one worker per selected Job", "un trabajador por trabajo seleccionado"
            ),
            "jobs": self.text("selected Jobs", "trabajos seleccionados"),
            "staffing": self.text(
                "one worker per Job in every observed block",
                "un trabajador por trabajo en cada bloque observado",
            ),
            "schedule": self.text(
                "complete baseline cells", "celdas de base completas"
            ),
            "coefficients": self.text(
                "complete selected-tool Job values",
                "valores completos de las herramientas seleccionadas",
            ),
        }
        self.readiness.setText(
            self.text("Input check — still needed: ", "Revisión de datos — falta: ")
            + ", ".join(labels[i] for i in issues)
            if issues
            else self.text(
                "Input check — Basic entry is complete. The planner validates hard"
                " rules "
                "and boundary freshness before solving.",
                "Revisión de datos — Los datos básicos están completos. El "
                "optimizador valida "
                "restricciones y límites antes de calcular.",
            )
        )
        for kind, check in self.tools.items():
            check.setChecked(kind in inputs.tools)
        old = self.risk_tabs.currentIndex()
        while self.risk_tabs.count():
            widget = self.risk_tabs.widget(0)
            self.risk_tabs.removeTab(0)
            if widget is not None:
                widget.deleteLater()
        for kind in inputs.tools:
            table = AdaptiveTableWidget()
            rows = []
            values: list[float | None] = []
            damages: list[float | None] = []
            for target in inputs.targets:
                item = next(
                    (
                        m
                        for m in risks.for_job(target.job_id).measurements
                        if m.kind is kind
                    ),
                    None,
                )
                probability = item.probability_percent if item else None
                rows.append(
                    (
                        target.job_id,
                        self.target_caption(target),
                        f"{item.cumulative_damage:.6g}"
                        if item and item.cumulative_damage is not None
                        else "—",
                        f"{probability:.1f}%" if probability is not None else "—",
                    )
                )
                values.append(probability)
                damages.append(item.cumulative_damage if item else None)
            self.table(
                table,
                (
                    self.text("Job", "Trabajo"),
                    self.text("Workplace", "Lugar de trabajo"),
                    self.text("Damage", "Daño"),
                    self.text("Probability", "Probabilidad"),
                ),
                tuple(rows),
            )
            for row, value in enumerate(values):
                damage_cell = table.item(row, 2)
                if damage_cell is not None:
                    damage_cell.setBackground(
                        QColor(job_damage_color(kind, damages[row]))
                    )
                cell = table.item(row, 3)
                if cell is not None and value is not None:
                    cell.setBackground(
                        QColor(RISK_APPEARANCES[classify_probability(value)].color_hex)
                    )
            self.risk_tabs.addTab(
                table,
                assessment_tool_icon(self.icons, kind),
                {
                    AssessmentKind.LIFFT: "LiFFT",
                    AssessmentKind.DUET: "DUET",
                    AssessmentKind.TST: "ST",
                }[kind],
            )
        if hasattr(self, "rules_label"):
            self.rules_label.setText(
                self.text(
                    "Active worker restrictions: ",
                    "Restricciones de trabajadores activas: ",
                )
                + str(len(inputs.rules))
            )
            self.neighbors.project(
                inputs,
                {
                    record.scenario_id: record.name
                    for record in self.repository.load_rotation_scenarios()
                },
            )
        self.risk_tabs.setCurrentIndex(min(max(0, old), self.risk_tabs.count() - 1))
        self.refresh_starting_indices(inputs)

    def refresh_starting_indices(self, inputs: RotationInputs) -> None:
        """Show current entered schedule indices without inventing absent worker data.

        Args:
            inputs: Current scenario timing, participants and baseline/proposal.

        Returns:
            None; incomplete schedules/tools remain explicitly unavailable.
        """
        risks = self.workspace.read_job_risk().risk
        values = tuple(
            RotationRisk(t.key, m.kind, m.probability_percent)
            for t in inputs.targets
            for m in risks.for_job(t.job_id).measurements
            if m.kind in inputs.tools and m.probability_percent is not None
        )
        columns: list[tuple[float, ...] | None] = []
        for kind in inputs.tools:
            try:
                summary = starting_indices(inputs, values, kind)
                columns.append(summary.values if summary else None)
            except ValueError:
                columns.append(None)
        workers = {
            w.worker_id: w
            for w in self.workspace.read_hierarchy().hierarchy.work.workers
        }
        rows = tuple(
            (
                w.worker_id
                + " · "
                + (workers[w.worker_id].first_name or "")
                + " "
                + (workers[w.worker_id].last_name or ""),
                *(
                    "—" if values is None else f"{values[index]:.2f}"
                    for values in columns
                ),
            )
            for index, w in enumerate(inputs.workers)
            if w.worker_id in workers
        )
        self.table(
            self.start_table,
            (
                self.text("Worker", "Trabajador"),
                *(
                    {
                        AssessmentKind.LIFFT: "LiFFT",
                        AssessmentKind.DUET: "DUET",
                        AssessmentKind.TST: "ST",
                    }[k]
                    for k in inputs.tools
                ),
            ),
            rows,
        )
        header = self.start_table.horizontalHeader()
        assert header is not None
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(80)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        for column in range(1, len(inputs.tools) + 1):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
        for column, column_values in enumerate(columns, 1):
            if column_values is not None:
                for row, value in enumerate(column_values):
                    item = self.start_table.item(row, column)
                    if item is not None:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        item.setBackground(
                            QColor(
                                RISK_APPEARANCES[classify_probability(value)].color_hex
                            )
                        )
        caption = (
            self.text("Baseline", "Base de referencia")
            if inputs.baseline is not None
            else self.text("Starting proposal", "Propuesta inicial")
        )
        self.start_notice.setText(
            caption
            + self.text(
                " · Current Job values and copied timing. "
                "Missing/incomplete values are —. "
                "These are schedule indices, not the worker's individual assessments.",
                " · Riesgos actuales y tiempos copiados. Valores incompletos: —. "
                "Son índices de la rotación, no evaluaciones "
                "individuales del trabajador.",
            )
        )

    def rework_run(self, replace_current: bool) -> None:
        """Promote an accepted result once, preferring a new independent named rotation.

        Args:
            replace_current: True requests a confirmed in-place baseline change.

        Returns:
            None; the source run stays frozen and Main Save owns publication.
        """
        if self.planning_busy() or not self.prepare() or self.scenario is None:
            return
        if self.solve.preview is not None:
            self.show_error(
                self.text(
                    "Keep or discard the optimization preview before reworking a "
                    "saved result.",
                    "Conserve o descarte la vista de optimización antes de rehacer un "
                    "resultado guardado.",
                )
            )
            return
        source = self.scenario
        if (
            source.run is None
            or source.run.contract_version != ROTATION_RUN_MODEL_VERSION
        ):
            self.show_error(
                self.text(
                    "Select a supported accepted result first.",
                    "Seleccione un resultado aceptado compatible.",
                )
            )
            return
        from PyQt5.QtWidgets import QInputDialog

        if replace_current:
            if not self.confirm(
                self.text(
                    "Replace this rotation's editable baseline with its "
                    "accepted result? "
                    "The original baseline stays in the old run until "
                    "that run is replaced. "
                    "Create a new rotation to keep both permanently; Undo"
                    " restores changes. "
                    "Current shared Job values will be used for the next solve.",
                    "¿Reemplazar la base editable por el resultado guardado? La base "
                    "original queda en el resultado hasta reemplazarlo. Cree una nueva "
                    "rotación para conservar ambas; Deshacer restaura "
                    "cambios. El cálculo "
                    "usará los riesgos actuales compartidos de trabajos.",
                )
            ):
                return
            name = source.name
        else:
            name, accepted = QInputDialog.getText(
                self,
                self.text("Rework as a new rotation", "Rehacer como nueva rotación"),
                self.text(
                    "New name; recorded setup is copied, current Job values are used",
                    "Nombre nuevo; se copia la configuración y se usan "
                    "riesgos actuales",
                ),
                text=source.name + self.text(" · rework", " · revisión"),
            )
            if not accepted:
                return
        try:
            if self.current() != source:
                raise ValueError(
                    "The selected saved rotation changed; retry reworking it."
                )
            assert source.run.inputs.planned_date is not None
            copy = duplicate_scenario(
                source,
                uuid4().hex,
                name,
                source.run.inputs.planned_date,
                use_optimized_baseline=True,
            )
            copy.inputs.validate_references(
                self.workspace.read_hierarchy().hierarchy,
                self.workspace.read_jobs().jobs,
            )
            if replace_current:
                self.repository.replace_rotation_scenario(
                    source, replace(source, inputs=copy.inputs)
                )
            else:
                with self.owner.stage():
                    self.repository.replace_rotation_scenario(None, copy)
                    self.view = JrotView(copy.scenario_id)
                    self.owner.set_editor(_VIEW_KEY, self.view, "jrot.view")
                self.owner.record("replace_rotation_scenario")
            self.reload()
        except Exception as error:
            self.show_error(error)

    def planning_busy(self) -> bool:
        """Guard data/history/navigation while an owned bounded planner is active.

        Args:
            None.

        Returns:
            True until the worker lifetime has safely completed.
        """
        return hasattr(self, "solve") and self.solve.busy

    def generate_proposal(self) -> None:
        """Generate feasible starting assignments for the displayed schedule.

        Args:
            None.

        Returns:
            None; replacement requires consent and stays in step 04 with shared Undo.
        """
        self.solve.start(True)

    def clear_assignments(self) -> None:
        """Clear the displayed baseline or proposal after explicit replacement consent.

        Args:
            None.

        Returns:
            None; Yes-path intent and the prior frozen run survive; Undo restores cells.
        """
        if not self.prepare() or self.scenario is None:
            return
        record = self.scenario
        observed = record.inputs.baseline is not None
        rows = record.inputs.baseline if observed else record.inputs.proposed
        if not rows or not any(k is not None for r in rows for k in r.target_keys):
            return
        if not self.confirm(
            self.text(
                "Clear these starting assignments? This changes the baseline shown in "
                "step 04, not the previously kept result. "
                "Undo restores the assignments."
                if observed
                else "Clear this entered proposal? Undo restores it.",
                "¿Quitar estas asignaciones iniciales? Cambia la base del paso 04, "
                "no el resultado conservado. Deshacer restaura las asignaciones."
                if observed
                else "¿Quitar esta propuesta? Deshacer la restaura.",
            )
        ):
            return
        blank = tuple(
            RotationDraftRow(r.worker_id, (None,) * len(r.target_keys)) for r in rows
        )
        inputs = (
            replace(record.inputs, baseline=blank)
            if observed
            else replace(record.inputs, proposed=None)
        )
        self.edit_inputs(record, RotationEntryChange(inputs))
        self.reload()

    def edit_rules(self) -> None:
        """Prepare one per-worker hard-rule proposal using exact selected positions.

        Args:
            None.

        Returns:
            None; removed restrictions require consent and accepted changes share
            history.
        """
        if self.planning_busy() or not self.prepare() or self.scenario is None:
            return
        record = self.scenario
        jobs = {j.job_id: j.name for j in self.workspace.read_jobs().jobs.jobs}
        labels = {
            t.key: t.job_id
            + " · "
            + jobs[t.job_id]
            + (" · " + self.target_caption(t) if t.placement_id is not None else "")
            for t in record.inputs.targets
        }
        worker_labels = {
            worker.worker_id: worker.worker_id
            + " · "
            + " ".join(part for part in (worker.first_name, worker.last_name) if part)
            for worker in self.workspace.read_hierarchy().hierarchy.work.workers
        }
        dialog = JrotRulesDialog(
            record.inputs,
            labels,
            self.icons,
            self.language,
            self,
            worker_labels=worker_labels,
        )
        try:
            if dialog.exec() == QDialog.Accepted:
                removed = tuple(
                    r for r in record.inputs.rules if r not in dialog.selected
                )
                self.edit_inputs(
                    record,
                    RotationEntryChange(
                        replace(record.inputs, rules=dialog.selected),
                        lost_rules=removed,
                    ),
                )
                self.reload()
        finally:
            dialog.deleteLater()

    def clear_neighbor(self, previous: bool) -> None:
        """Remove a neighbor link while retaining boundary-check intentions.

        Args:
            previous: True clears the previous run, False the following run.

        Returns:
            None; no rule is silently relaxed and Main Save remains the publication
            owner.
        """
        if self.planning_busy() or not self.prepare() or self.scenario is None:
            return
        inputs = self.scenario.inputs
        candidate = (
            replace(inputs, previous=None)
            if previous
            else replace(inputs, following=None)
        )
        self.edit_inputs(self.scenario, RotationEntryChange(candidate))
        self.reload()

    def choose_neighbor(self, previous: bool) -> None:
        """Select an accepted neighboring run without inferring adjacency.

        Args:
            previous: True captures its last block; False its first block.

        Returns:
            None; source freshness and temporal compatibility are checked before
            saving.
        """
        if self.planning_busy() or not self.prepare() or self.scenario is None:
            return
        record = self.scenario
        h, j, r = (
            self.workspace.read_hierarchy().hierarchy,
            self.workspace.read_jobs().jobs,
            self.workspace.read_job_risk().risk,
        )
        sources = tuple(
            s
            for s in self.repository.load_rotation_scenarios()
            if s.scenario_id != record.scenario_id and own_run_is_current(s, h, j, r)
        )
        choices = tuple(
            JrotCatalogChoice(
                s.scenario_id,
                (
                    s.name,
                    s.inputs.planned_date.isoformat() if s.inputs.planned_date else "—",
                    ", ".join(tool_caption(k.value) for k in s.inputs.tools),
                ),
            )
            for s in sources
        )
        dialog = JrotCatalogPicker(
            self.text(
                "Select preceding rotation result"
                if previous
                else "Select following rotation result",
                "Seleccionar resultado de rotación anterior"
                if previous
                else "Seleccionar resultado de rotación siguiente",
            ),
            (
                self.text("Rotation", "Rotación"),
                self.text("Date", "Fecha"),
                self.text("Tools", "Herramientas"),
            ),
            choices,
            (),
            self.language,
            self,
            icons=self.icons,
            entity_icon="jrot",
        )
        try:
            if dialog.exec() != QDialog.Accepted:
                return
            if len(dialog.selected) != 1:
                raise ValueError("Select exactly one accepted neighboring run.")
            source = next(s for s in sources if s.scenario_id == dialog.selected[0])
            boundary = capture_rotation_boundary(source, previous=previous)
            candidate = (
                replace(record.inputs, previous=boundary)
                if previous
                else replace(record.inputs, following=boundary)
            )
            if not neighbors_are_current(
                replace(record, inputs=candidate),
                self.repository.load_rotation_scenarios(),
                h,
                j,
                r,
            ):
                raise ValueError(
                    "Selected neighbor changed; choose its current accepted run."
                )
            if candidate.timing is not None and candidate.start_minute is not None:
                start, end = rotation_interval(candidate)
                if boundary.end > start if previous else boundary.start < end:
                    raise ValueError(
                        "Neighbor overlaps or has the wrong temporal order."
                    )
            # Complete preparation also validates requested worker/tool boundaries.
            self.edit_inputs(record, RotationEntryChange(candidate))
            self.reload()
        except ValueError as error:
            self.show_error(error)
        finally:
            dialog.deleteLater()

    def open_jobs(self) -> None:
        """Reuse Job management for catalog creation and placement edits.

        Args:
            None.

        Returns:
            None; selected scenario positions remain explicit and are not auto-filled.
        """
        if not self.prepare():
            return
        dialog = JobManagementDialog(
            self.workspace,
            self.icons,
            self.metadata.default_units,
            language=self.language,
            convention=self.convention,
            selected_job=self.view.job_id,
            gauge_markers=self.gauge_markers,
            change_gauge_markers=self.save_markers,
            parent=self,
        )
        if self.editor_preferences is not None:
            self.editor_preferences.bind(dialog)
        try:
            dialog.exec()
        finally:
            dialog.deleteLater()
            self.reload()

    def open_workers(self) -> None:
        """Open the shared worker editor without silently changing participants.

        Args:
            None.

        Returns:
            None; edits retain shared history and Main Save, then refresh catalogs.
        """
        if not self.prepare():
            return
        dialog = WorkerManagementDialog(
            self.workspace,
            self.icons,
            self.metadata.default_units,
            language=self.language,
            parent=self,
        )
        try:
            dialog.exec()
        finally:
            dialog.deleteLater()
            self.reload()

    def open_organization(self) -> None:
        """Reuse the maintained organization editor without inferring a scenario scope.

        Args:
            None.

        Returns:
            None; organization edits retain their ordinary shared history/Save behavior.
        """
        if not self.prepare():
            return
        dialog = OrganizationDialog(
            self.workspace, self.icons, language=self.language, parent=self
        )
        try:
            dialog.exec()
        finally:
            dialog.deleteLater()
            self.reload()

    def prepare_close(self) -> bool:
        """Resolve pending records and confirm discarding an unaccepted creation form.

        Args:
            None.

        Returns:
            True permits closure; accepted project edits are always retained.
        """
        return (
            self.solve.request_close()
            and self.prepare()
            and self.resolve_result_preview()
            and (
                self.scenario is not None
                or not (self.name.text().strip() or self.description.text().strip())
                or self.confirm(
                    self.text(
                        "Discard this uncreated rotation form?",
                        "¿Descartar este formulario de rotación sin crear?",
                    )
                )
            )
        )

    def resolve_result_preview(self) -> bool:
        """Offer explicit Keep/Discard/Cancel before closing an unretained result.

        Args:
            None.

        Returns:
            False keeps the window open; True retains or deliberately discards the
            preview. Keeping never promotes the optimized arrangement to a baseline.
        """
        if self.solve.preview is None:
            return True
        answer = QMessageBox.question(
            self,
            self.text("Keep result before closing?", "¿Conservar antes de cerrar?"),
            self.text(
                "Keep this result with the rotation? The original baseline "
                "will not change. Main Save stores kept changes. No discards "
                "only this preview.",
                "¿Conservar este resultado en la rotación? La base original no"
                " cambia. Guardar almacena los cambios. No descarta solo esta "
                "vista previa.",
            ),
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes,
        )
        if answer == QMessageBox.Cancel:
            return False
        if answer == QMessageBox.Yes:
            self.solve.keep_result()
            return self.solve.preview is None
        self.solve.discard()
        return True

    def accept(self) -> None:
        """Close only after pending accepted-record input is validated and retained.

        Args:
            None.

        Returns:
            None; accepted project edits remain private until Main Save.
        """
        if self.prepare_close():
            super().accept()

    def reject(self) -> None:
        """Apply the same preparation for Escape/Close without rolling back other edits.

        Args:
            None.

        Returns:
            None; failed pending input keeps the window open for correction.
        """
        if self.prepare_close():
            super().reject()

    def closeEvent(self, event: QCloseEvent | None) -> None:  # noqa: N802 - Qt override
        """Guard native close using the ordinary pending-input policy.

        Args:
            event: Native close request, or None for compatibility callers.

        Returns:
            None; refused closure preserves the widget/input lifetime.
        """
        if self.prepare_close():
            if event is not None:
                event.accept()
        elif event is not None:
            event.ignore()

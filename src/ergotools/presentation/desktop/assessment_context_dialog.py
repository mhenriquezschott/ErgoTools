"""Reference-shaped classified-assignment chooser with injected selection services.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Mapping

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.settings import Language
from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.presentation.assessment_selection import (
    AssessmentSelection,
    AssessmentSelector,
    SelectionCatalog,
)
from ergotools.presentation.assignment_options import (
    ClassifiedAssignment as ClassifiedAssignment,
)
from ergotools.presentation.assignment_selection import (
    AssignmentCatalog,
    AssignmentRequest,
    AssignmentSelector,
)
from ergotools.presentation.desktop.style import WORKSPACE_STYLE

# Original context-dialog palette and object-name styling; CSS values are visual
# reference data.
_CONTEXT_STYLE = """
QDialog#assessmentWorkplaceDialog { background: #F4F7F9; color: #1B2933;
    font: 12px "Segoe UI"; }
QLabel#dialogTitle { color: #0B326C; font-size: 20px; font-weight: 700; }
QLabel#supportingText { color: #405462; font-size: 12px; }
QPushButton#primaryOutlineButton { border: 2px solid #08A9B5; }
QTreeWidget { background: white; color: #1B2933; border: 1px solid #BCC9D3;
    border-radius: 5px; alternate-background-color: #F7FAFB; }
QTreeWidget::item { min-height: 29px; padding: 2px 5px; }
QTreeWidget::item:selected { background: #087E91; color: white; }
QTreeWidget::branch:selected { background: #087E91; }
QHeaderView::section { background: #EAF2F6; color: #0B326C; border: 0;
    border-bottom: 1px solid #BCC9D3; padding: 7px; font-weight: 700; }
"""


class AssessmentContextDialog(QDialog):
    """Choose a classified context; return prepared intent without saving or switching.

    The host supplies packaged icons and resolves pending widget text before preparing a
    selection. After acceptance it resolves dirty intent, then uses the selector; source
    edits require preparing a fresh request. No operational database or parent-window
    lookup is hidden in this component. A separate button sets selected_standalone
    when enabled, recording accepted unassigned navigation intent. Persisted
    ownership never changes here. Existing/missing labels and Open/Create button text
    expose the exact selected tool's intent; the main host owns creation after consent.
    """

    def __init__(
        self,
        selector: AssessmentSelector | AssignmentSelector,
        catalog: SelectionCatalog | AssignmentCatalog,
        worker_id: str,
        kind: AssessmentKind,
        assignments: tuple[ClassifiedAssignment, ...],
        icons: Mapping[str, QIcon],
        *,
        current: WorkplaceContext | None = None,
        shifts: tuple[str, ...] | None = None,
        saved_assignments: frozenset[int] | None = None,
        allow_standalone: bool = False,
        language: Language = Language.ENGLISH,
        parent: QWidget | None = None,
    ) -> None:
        """Build the reference tree/filter/button layout from immutable inputs.

        Args:
            selector: Injected selection service that prepares exact context ownership
                before activation.
            catalog: Immutable loaded catalog used for selection; no caption-based
                identity inference.
            worker_id: Exact stored worker identifier; captions and surname sorting are
                not identities.
            kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
                captions are not keys.
            assignments: Saved classified assignments eligible for this worker and tool.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            current: Currently committed workplace, or None when no assignment is
                selected.
            shifts: Explicit saved shift identifiers; assignment selection requires this
                catalog.
            saved_assignments: Current saved owners for the active tool; None retains
                the diagnostic three-column tree; otherwise show existing/missing state
                and label acceptance Open/Create assessment for the selected tool.
            allow_standalone: Offer an unassigned worker/tool view. Disabled for
                association and legacy pickers, which require a real assignment.
            language: Interface language only; user workplace and Job values stay
                literal.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.

        Raises:
            ValueError: Multiple eligible assignments for one workplace. Assignment
        """
        super().__init__(parent)
        self.allow_standalone = allow_standalone
        self.selected_standalone = False
        self.standalone_button: QPushButton | None = None
        self.language = language
        self._saved_assignments = saved_assignments
        self.selector = selector
        self.catalog = catalog
        self.worker_id = worker_id
        self.kind = kind
        self.icons = icons
        self.selected: AssessmentSelection | AssignmentRequest | None = None
        self.selected_assignment: ClassifiedAssignment | None = None
        self._current = current
        if isinstance(selector, AssignmentSelector) and isinstance(
            catalog, AssignmentCatalog
        ):
            project_id = catalog.snapshot.jobs.project_id
            assignments = selector.options(catalog, worker_id)
            if shifts is None:
                raise ValueError("Assignment dialogs require explicit project shifts.")
            available_shifts = shifts
        elif isinstance(selector, AssessmentSelector) and isinstance(
            catalog, SelectionCatalog
        ):
            project_id = catalog.snapshot.hierarchy.work.project_id
            available_shifts = catalog.snapshot.hierarchy.work.shifts
        else:
            raise ValueError("Selector and catalog capabilities must match.")
        self._assignments = tuple(
            item
            for item in assignments
            if item.assignment.worker.project_id == project_id
            and item.assignment.worker.worker_id == worker_id
            and item.assignment.active
            and item.assignment.placement_active
        )
        owners = [item.assignment.worker for item in self._assignments]
        if len(set(owners)) != len(owners):
            raise ValueError("Multiple eligible assignments for one workplace.")
        tool = {
            AssessmentKind.LIFFT: "LiFFT",
            AssessmentKind.DUET: "DUET",
            AssessmentKind.TST: "ST",
        }[kind]
        self.setObjectName("assessmentWorkplaceDialog")
        self.setWindowTitle("Assessment Context")
        self.setMinimumSize(700, 540)
        self.setStyleSheet(WORKSPACE_STYLE + _CONTEXT_STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        title = QLabel("Assessment context")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        description = QLabel(
            f"Worker: {worker_id} · Tool: {tool}. "
            "Select a workplace to open its assessment or create one if missing; "
            "a Job is optional."
        )
        description.setObjectName("supportingText")
        description.setWordWrap(True)
        layout.addWidget(description)
        shift_row = QHBoxLayout()
        shift_row.setContentsMargins(0, 0, 0, 0)
        shift_row.addWidget(QLabel("Shift"))
        self.shift = QComboBox()
        self.shift.setToolTip("Filter this worker's workplace assignments by shift.")
        self.shift.addItems(sorted(available_shifts))
        if current is not None:
            self.shift.setCurrentText(current.shift_id)
        shift_row.addWidget(self.shift, 1)
        layout.addLayout(shift_row)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(4 if saved_assignments is not None else 3)
        self.tree.setHeaderLabels(
            ["Workplace hierarchy", "Type", "Job"]
            + (["Assessment"] if saved_assignments is not None else [])
        )
        self.tree.setColumnWidth(0, 340)
        self.tree.setColumnWidth(1, 140)
        if saved_assignments is not None:
            header = self.tree.header()
            assert header is not None
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            for column in (1, 2, 3):
                header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
        self.tree.setToolTip("Expand the hierarchy and select a workplace assignment.")
        layout.addWidget(self.tree, 1)
        self.summary = QLabel("Select a workplace assignment from the hierarchy.")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        use = self.buttons.button(QDialogButtonBox.Ok)
        assert use is not None
        self.use = use
        self.use.setText("Use assessment context")
        self.use.setObjectName("primaryOutlineButton")
        self.use.setIcon(icons["job_management"])
        self.use.setIconSize(QSize(24, 24))
        cancel = self.buttons.button(QDialogButtonBox.Cancel)
        assert cancel is not None
        cancel.setIcon(icons["cancel"])
        cancel.setIconSize(QSize(22, 22))
        footer = QHBoxLayout()
        if allow_standalone:
            self.standalone_button = QPushButton(
                "Evaluación independiente"
                if language is Language.SPANISH
                else "Standalone assessment"
            )
            self.standalone_button.setIcon(icons["worker"])
            self.standalone_button.setIconSize(QSize(24, 24))
            self.standalone_button.setMinimumHeight(38)
            self.standalone_button.setToolTip(
                "Ver la evaluación de este trabajador sin asociación a un lugar."
                if language is Language.SPANISH
                else "View this worker's assessment without a workplace association."
            )
            self.standalone_button.clicked.connect(self._accept_standalone)
            footer.addWidget(self.standalone_button)
        footer.addStretch(1)
        footer.addWidget(self.buttons)
        layout.addLayout(footer)
        self.tree.currentItemChanged.connect(self._selection_changed)
        self.tree.itemDoubleClicked.connect(self._accept_selection)
        self.shift.currentTextChanged.connect(self._populate)
        self.buttons.accepted.connect(self._accept_selection)
        self.buttons.rejected.connect(self.reject)
        self._populate()
        if language is Language.SPANISH:
            self.setWindowTitle("Contexto de evaluación")
            title.setText("Contexto de evaluación")
            description.setText(
                f"Trabajador: {worker_id} · Herramienta: {tool}. "
                "Seleccione un lugar para abrir su evaluación o crear una "
                "si no existe; "
                "el trabajo es opcional."
            )
            self.tree.setHeaderLabels(
                ["Jerarquía del lugar", "Tipo", "Trabajo"]
                + (["Evaluación"] if saved_assignments is not None else [])
            )
            if saved_assignments is None:
                self.use.setText("Usar contexto de evaluación")
            cancel.setText("Cancelar")
            self.shift.setToolTip("Filtrar las asignaciones del trabajador por turno.")
            self.tree.setToolTip(
                "Expanda la jerarquía y seleccione una asignación de lugar."
            )
            shift_item = shift_row.itemAt(0)
            assert shift_item is not None
            shift_label = shift_item.widget()
            if isinstance(shift_label, QLabel):
                shift_label.setText("Turno")

    def _populate(self) -> None:
        """Rebuild the exact assignment tree for the selected shift.

        Rebuild the exact assignment tree for the selected shift, reveal the committed
        context and disable empty selection.

        Args:
            None.

        Returns:
            None.
        """
        self.selected_standalone = False
        self.tree.clear()
        self.selected = None
        self.selected_assignment = None
        self.use.setEnabled(False)
        if self._saved_assignments is not None:
            self.use.setText(
                "Crear evaluación"
                if self.language is Language.SPANISH
                else "Create assessment"
            )
        self.summary.setText(
            "Seleccione una asignación de lugar en la jerarquía."
            if self.language is Language.SPANISH
            else "Select a workplace assignment from the hierarchy."
        )
        nodes: dict[tuple[str, ...], QTreeWidgetItem] = {}
        selected_item = None
        count = 0
        for option in self._assignments:
            place = option.assignment.worker.workplace
            if place.shift_id != self.shift.currentText():
                continue
            count += 1
            parent = None
            path: tuple[str, ...] = ()
            for label, value in (
                ("Plant", place.plant_name),
                ("Section", place.section_name),
                ("Line", place.line_name),
            ):
                path = (*path, value)
                if path not in nodes:
                    caption = (
                        {"Plant": "Planta", "Section": "Sección", "Line": "Línea"}[
                            label
                        ]
                        if self.language is Language.SPANISH
                        else label
                    )
                    item = QTreeWidgetItem([value, caption])
                    item.setIcon(0, self.icons[label.lower()])
                    item.setToolTip(0, f"{caption}: {value}")
                    if parent is None:
                        self.tree.addTopLevelItem(item)
                    else:
                        parent.addChild(item)
                    nodes[path] = item
                parent = nodes[path]
            assert parent is not None
            state = (
                (
                    "Saved"
                    if option.assignment.assignment_id in self._saved_assignments
                    else "Not created"
                )
                if self._saved_assignments is not None
                else ""
            )
            if self.language is Language.SPANISH:
                state = {"Saved": "Guardada", "Not created": "Sin crear"}.get(
                    state, state
                )
            leaf = QTreeWidgetItem(
                [
                    place.station_id,
                    "Asignación" if self.language is Language.SPANISH else "Assignment",
                    option.job_id or "—",
                    state,
                ]
            )
            leaf.setIcon(0, self.icons["station"])
            leaf.setData(0, Qt.ItemDataRole.UserRole, option)
            leaf.setToolTip(
                0,
                "Seleccione este lugar y turno de evaluación."
                if self.language is Language.SPANISH
                else "Select this workplace and shift assessment context.",
            )
            leaf.setToolTip(2, option.job_name or option.job_id or "—")
            parent.addChild(leaf)
            if place == self._current:
                selected_item = leaf
        self.tree.collapseAll()
        if selected_item is not None:
            ancestor = selected_item.parent()
            while ancestor is not None:
                ancestor.setExpanded(True)
                ancestor = ancestor.parent()
            self.tree.setCurrentItem(selected_item)
            self.tree.scrollToItem(selected_item)
        elif count == 0:
            self.summary.setText(
                (
                    "El trabajador no tiene asignaciones de lugar "
                    "para el turno seleccionado."
                )
                if self.language is Language.SPANISH
                else (
                    "This worker has no workplace assignments for the selected shift."
                )
            )

    def _selection_changed(self) -> None:
        """Read typed leaf ownership.

        Read typed leaf ownership and update the complete workplace/job summary and
        acceptance interlock. Standalone navigation is a separate footer action, never
        a hierarchy node.

        Args:
            None.

        Returns:
            None.
        """
        item = self.tree.currentItem()
        option = item.data(0, Qt.ItemDataRole.UserRole) if item is not None else None
        self.selected_assignment = (
            option if isinstance(option, ClassifiedAssignment) else None
        )
        self.selected_standalone = False
        self.use.setEnabled(self.selected_assignment is not None)
        if self._saved_assignments is not None:
            exists = (
                self.selected_assignment is not None
                and self.selected_assignment.assignment.assignment_id
                in self._saved_assignments
            )
            self.use.setText(
                ("Abrir evaluación" if exists else "Crear evaluación")
                if self.language is Language.SPANISH
                else ("Open assessment" if exists else "Create assessment")
            )
        if self.selected_assignment is None:
            self.summary.setText(
                "Seleccione una asignación de lugar en la jerarquía."
                if self.language is Language.SPANISH
                else "Select a workplace assignment from the hierarchy."
            )
            return
        place = self.selected_assignment.assignment.worker.workplace
        job = self.selected_assignment.job_id or "—"
        if self.selected_assignment.job_name:
            job += " | " + self.selected_assignment.job_name
        self.summary.setText(
            "  >  ".join(
                (
                    place.plant_name,
                    place.section_name,
                    place.line_name,
                    place.station_id,
                    place.shift_id,
                )
            )
            + ("  |  Trabajo: " if self.language is Language.SPANISH else "  |  Job: ")
            + job
        )

    def _accept_standalone(self) -> None:
        """Accept unassigned navigation without manufacturing a hierarchy entry.

        Args:
            None.

        Returns:
            None. When offered, clear workplace selection and return standalone intent;
            the host retains ownership of unsaved-edit consent and document navigation.
            Association-only dialogs cannot accept this action.
        """
        if not self.allow_standalone:
            return
        self.selected = None
        self.selected_assignment = None
        self.selected_standalone = True
        self.accept()

    def _accept_selection(self) -> None:
        """Prepare the exact selected ownership request and accept only.

        Prepare the exact selected ownership request and accept only while it remains
        eligible; stale selections stay open with a diagnostic. The separate standalone
        action uses the same host-owned pending-edit resolution after acceptance.

        Args:
            None.

        Returns:
            None.
        """
        if self.selected_assignment is None:
            return
        try:
            if isinstance(self.selector, AssignmentSelector) and isinstance(
                self.catalog, AssignmentCatalog
            ):
                self.selected = self.selector.prepare(
                    self.catalog,
                    self.worker_id,
                    self.selected_assignment.assignment.assignment_id,
                    self.kind,
                )
            else:
                assert isinstance(self.selector, AssessmentSelector)
                assert isinstance(self.catalog, SelectionCatalog)
                self.selected = self.selector.prepare(
                    self.catalog,
                    self.worker_id,
                    self.selected_assignment.assignment.worker.workplace,
                    self.kind,
                )
        except (ValueError, KeyError):
            self.selected = None
            self.use.setEnabled(False)
            self.summary.setText(
                "La selección ya no está disponible. Abra de nuevo este diálogo."
                if self.language is Language.SPANISH
                else "The selection is no longer available. Reopen the context dialog."
            )
            return
        self.accept()

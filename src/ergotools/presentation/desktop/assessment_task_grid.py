"""Shared LiFFT/DUET/ST grid for main assessments, Jobs and read-only copy previews.

Presentation layer. Sticky headers, column order, numeric inputs, descriptive
selectors and read-only outputs follow the main assessment UI. Completed cells emit
task/field identities; hosts own parsing, canonical source edits, calculation,
persistence and shared history.
A read-only instance previews copied sources without emitting edits.
"""

from collections.abc import Mapping
from contextlib import ExitStack
from dataclasses import dataclass
from functools import partial
from itertools import pairwise
from typing import TYPE_CHECKING
from weakref import ReferenceType, ref

from PyQt5 import sip
from PyQt5.QtCore import (
    QEvent,
    QObject,
    QPoint,
    QSignalBlocker,
    QSize,
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt5.QtGui import QIcon, QKeyEvent, QKeySequence, QMouseEvent
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
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

from ergotools.application.assessment_columns import (
    AssessmentColumns,
    assessment_column_keys,
)
from ergotools.application.settings import Language
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    task_has_data,
)
from ergotools.domain.assessments.duet_draft import DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.display_precision import DisplayPrecision
from ergotools.domain.job_risk import JobTaskResult
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.task_catalog import TaskDefinition
from ergotools.presentation.desktop.assessment_action_icons import (
    assessment_action_icon,
)
from ergotools.presentation.desktop.assessment_controls import (
    assessment_number,
    assessment_selector,
)
from ergotools.presentation.desktop.precision_editor import PrecisionLineEdit
from ergotools.presentation.desktop.theme.job_results import job_damage_color
from ergotools.presentation.desktop.theme.main_workspace import MAIN_WORKSPACE_STYLE

if TYPE_CHECKING:
    from ergotools.presentation.desktop.assessment_editor_preferences import (
        AssessmentEditorPreferences,
    )


@dataclass(frozen=True, slots=True)
class AssessmentCellEdit:
    """Completed display-cell intent, independent of source acceptance and units.

    Attributes:
        task_id: Stable task identity from the currently displayed projection.
        field: Canonical field name; hosts keep their existing conversion/validation.
        value: Exact numeric text token or selector item data, never a rounded float.
    """

    task_id: str
    field: str
    value: str | int | None


class AssessmentTaskGrid(QWidget):
    """Render one assessment tool without accepting input into project state.

    Attributes:
        cell_finished: Emits immutable task/field/value intent when a cell completes.
        input_edited: Emits numeric typing notifications; never accepts source edits.
        task_focused: Emits task ID on row focus or click.
        geometry_changed: Signals settled columns or horizontal scrolling.
        task_selection_changed: Emits checked IDs for read-only copy previews.
        task_checks: Copy checkboxes indexed by stable source task identity.
    """

    cell_finished = pyqtSignal(object)
    input_edited = pyqtSignal()
    task_focused = pyqtSignal(str)
    geometry_changed = pyqtSignal()
    task_selection_changed = pyqtSignal(object)
    task_name_finished = pyqtSignal(str, object, object)

    def __init__(
        self,
        language: Language,
        convention: DecimalConvention,
        parent: QWidget | None = None,
        *,
        icons: Mapping[str, QIcon] | None = None,
        kind: AssessmentKind = AssessmentKind.LIFFT,
        precision: DisplayPrecision | None = None,
        system: MeasurementSystem = MeasurementSystem.METRIC,
        read_only: bool = False,
        selectable: bool = False,
        compact: bool = False,
        worker_layout: bool = False,
    ) -> None:
        """Construct an empty main-style grid with no manufactured task rows.

        Args:
            icons: Injected packaged action glyphs; no asset lookup or source writes.
            language: Static label/selector language.
            convention: Explicit display/input decimal mark.
            parent: Qt owner of the grid.
            kind: Tool identifying columns even when no source exists.
            precision: Project display policy; unchanged source precision is preserved.
            system: Empty-grid unit labels; recorded sources retain their own units.
            read_only: True permits browsing but never source edits or signals.
            selectable: Add task-copy checkboxes; selection never edits task values.
            compact: Read-only embedded preview density; ordinary editing is unchanged.
            worker_layout: Retain the established main-panel column geometry.

        Returns:
            None; no source, task, calculation or history action is created.
        """
        super().__init__(parent)
        self.icons = icons or {}
        self.language = language
        self.convention = convention
        self.kind = kind
        self.precision = precision or DisplayPrecision()
        self.read_only = read_only
        self.selectable = selectable
        self.compact = compact
        self.worker_layout = worker_layout
        self.task_checks: dict[str, QCheckBox] = {}
        self.task_definitions: tuple[TaskDefinition, ...] = ()
        self.task_names: list[QComboBox | QLabel] = []
        self.system = system
        self.source: AssessmentDraft | None = None
        self._focus_task_id: str | None = None
        self.inputs: list[list[PrecisionLineEdit | QComboBox]] = []
        self.outputs: list[tuple[QLabel, ...]] = []
        self.editor_preferences: AssessmentEditorPreferences | None = None
        self.selected_task_index = -1
        self.selected_input_field = "task_name"
        self._cell_anchor: tuple[int, str] | None = None
        self._cell_end: tuple[int, str] | None = None
        self._selected_rows: set[int] = set()
        self._row_anchor: int | None = None
        self._sync_pending = False
        self._column_profiles: tuple[AssessmentColumns, ...] = ()
        self._column_dimensions: list[tuple[int, int]] = []
        self._generation = 0
        self.setStyleSheet(
            MAIN_WORKSPACE_STYLE + ' QLineEdit[taskRangeSelected="true"], '
            'QComboBox[taskRangeSelected="true"] '
            "{ background:#DDF3F5; border:1px solid #00AEBE; } "
            + (
                "QWidget { font-size: 11px; } "
                "QLineEdit, QComboBox { min-height: 20px; max-height: 20px; "
                "padding: 0 3px; border: 0; background: transparent; } "
                "QLabel, QCheckBox { padding: 0; margin: 0; min-height: 0; }"
                if compact
                else ""
            )
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.actions_widget = QWidget()
        task_actions = QHBoxLayout(self.actions_widget)
        task_actions.setContentsMargins(0, 0 if compact else 8, 0, 0)
        self.task_names_button = QPushButton()
        self.task_names_button.setIcon(self.icons.get("task_names", QIcon()))
        self.task_names_button.setIconSize(QSize(26, 26))
        self.copy_cells_button = QPushButton()
        self.paste_cells_button = QPushButton()
        self.copy_cells_button.setIcon(assessment_action_icon("copy"))
        self.paste_cells_button.setIcon(assessment_action_icon("paste"))
        self.import_settings_button = QPushButton()
        self.import_settings_button.setIcon(assessment_action_icon("import"))
        self.import_settings_button.setFixedWidth(34)
        self.import_settings_button.setToolTip(
            "Import CSV/TSV/Excel and configure paste settings."
        )
        task_actions.addWidget(self.task_names_button)
        task_actions.addStretch(1)
        task_actions.addWidget(self.copy_cells_button)
        task_actions.addWidget(self.paste_cells_button)
        task_actions.addWidget(self.import_settings_button)
        self.actions_widget.setVisible(not read_only)
        layout.addWidget(self.actions_widget)
        self.header_widget = QWidget()
        self.header_widget.setObjectName("stickyHeader")
        self.header_grid = QGridLayout(self.header_widget)
        self.header = QScrollArea()
        self.header.setObjectName("stickyHeaderScroll")
        self.header.setFrameShape(QFrame.NoFrame)
        self.header.setFixedHeight(44 if compact else 42)
        self.header.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.header.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.header.setWidget(self.header_widget)
        layout.addWidget(self.header)
        self.body_scroll = QScrollArea()
        self.body_scroll.setWidgetResizable(True)
        self.frame = QFrame()
        frame_layout = QVBoxLayout(self.frame)
        if compact:
            frame_layout.setContentsMargins(2, 2, 2, 2)
        elif worker_layout and kind is AssessmentKind.TST:
            frame_layout.setContentsMargins(0, 0, 0, 0)
            self.frame.setMinimumWidth(0)
            self.frame.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
            self.body_scroll.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
        frame_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)
        self.grid = QGridLayout()
        if compact:
            self.grid.setHorizontalSpacing(3)
            self.grid.setVerticalSpacing(2)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        if worker_layout and kind is AssessmentKind.TST:
            self.grid.setContentsMargins(6, 0, 6, 0)
        frame_layout.addLayout(self.grid)
        self.body_scroll.setWidget(self.frame)
        viewport = self.body_scroll.viewport()
        assert viewport is not None
        viewport.installEventFilter(self)
        self.frame.installEventFilter(self)
        body_bar = self.body_scroll.horizontalScrollBar()
        header_bar = self.header.horizontalScrollBar()
        assert body_bar is not None and header_bar is not None
        vertical_bar = self.body_scroll.verticalScrollBar()
        assert vertical_bar is not None
        vertical_bar.rangeChanged.connect(
            lambda _minimum, _maximum: self.refresh_geometry()
        )
        body_bar.valueChanged.connect(header_bar.setValue)
        body_bar.valueChanged.connect(self.geometry_changed)
        layout.addWidget(self.body_scroll, 1)
        self.load_source(None)

    @property
    def task_count(self) -> int:
        """Return the visible source capacity without manufacturing empty tasks.

        Args:
            None.

        Returns:
            Zero without a source, otherwise the exact number of retained task rows.
        """
        return len(self.inputs)

    @property
    def input_fields(self) -> tuple[str, ...]:
        """Return the ordered input identities shared with host acceptance adapters.

        Args:
            None.

        Returns:
            Stable field names in control/input-row order, excluding derived outputs.
        """
        if self.kind is AssessmentKind.DUET:
            return ("omni_res_scale", "repetitions")
        if self.kind is AssessmentKind.TST:
            return ("direction", "lever_arm", "load", "repetitions")
        return ("lever_arm", "load", "repetitions")

    @property
    def geometry_pending(self) -> bool:
        """Expose whether column alignment is awaiting its next native event turn.

        Args:
            None.

        Returns:
            True only while a coalesced geometry update is queued; no timer polling.
        """
        return self._sync_pending

    def select_task(self, row: int) -> None:
        """Remember the row targeted by Remove without changing source values.

        Args:
            row: Zero-based task position; out-of-range requests clear selection.

        Returns:
            None; focus and editing remain with the native input widget.
        """
        self.selected_task_index = row if 0 <= row < self.task_count else -1

        if self.source is not None and self.selected_task_index >= 0:
            self.task_focused.emit(self.source.tasks[self.selected_task_index].task_id)

    def load_source(
        self,
        source: AssessmentDraft | None,
        results: tuple[JobTaskResult, ...] = (),
    ) -> None:
        """Rebuild controls after selection/replay, preserving exact source quantities.

        Args:
            source: Explicit task source, or None for an empty tool/direct result.
            results: Matching output rows; absent results show unavailable labels.

        Returns:
            None; construction never accepts input or adds history actions.
        """
        self._generation += 1
        generation = self._generation
        focus = QApplication.focusWidget()
        if focus is not None and self.frame.isAncestorOf(focus):
            focus.clearFocus()
        self._focus_task_id = None
        if (tuple(t.task_id for t in self.source.tasks) if self.source else ()) != (
            tuple(t.task_id for t in source.tasks) if source else ()
        ):
            self._cell_anchor, self._cell_end = None, None
            self._selected_rows.clear()
            self._row_anchor = None
        self.source = source
        self.copy_cells_button.setEnabled(source is not None)
        self.paste_cells_button.setEnabled(source is not None)
        self.import_settings_button.setEnabled(source is not None)
        self.inputs = []
        self.outputs = []
        self.task_checks = {}
        self.task_names = []
        for grid in (self.grid, self.header_grid):
            while grid.count():
                item = grid.takeAt(0)
                widget = item.widget() if item is not None else None
                if widget is not None:
                    widget.hide()
                    widget.deleteLater()
        spanish = self.language is Language.SPANISH
        self.task_names_button.setText(
            "Nombres de tareas…" if spanish else "Task names…"
        )
        self.copy_cells_button.setText("Copiar celdas" if spanish else "Copy cells")
        self.import_settings_button.setToolTip(
            "Importar CSV/TSV/Excel y configurar el pegado."
            if self.language is Language.SPANISH
            else "Import CSV/TSV/Excel and configure paste settings."
        )
        self.paste_cells_button.setText("Pegar" if spanish else "Paste")
        self.task_names_button.setToolTip(
            "Agregar o renombrar nombres reutilizables."
            if spanish
            else "Add or rename reusable project task names."
        )
        self.copy_cells_button.setToolTip(
            "Mayús+clic selecciona un rango de entradas. Copiar celdas copia ese "
            "rango, o todas las entradas si no hay un rango seleccionado."
            if spanish
            else "Shift+click another input to select a range; Copy cells copies that "
            "range, or all inputs when no range is selected."
        )
        self.paste_cells_button.setToolTip(
            "Pegar con las preferencias guardadas; revisar datos incompatibles."
            if spanish
            else "Paste with saved defaults; review incompatible data."
        )
        imperial = (
            source.system if isinstance(source, (LifftDraft, TstDraft)) else self.system
        ) is MeasurementSystem.IMPERIAL
        captions = {
            "task_number": "Task #",
            "task_name": "Task name",
            "omni_res_scale": "OMNI-Res Scale",
            "direction": "Type of Task",
            "lever_arm": "Lever Arm",
            "load": "Load",
            "moment": "Moment",
            "repetitions": "Repetitions (per work day)",
            "damage": "Damage (cumulative)",
            "share": "% Total (damage)",
        }
        keys = assessment_column_keys(self.kind)
        titles = [captions[key] for key in keys]
        translated = {
            "Task #": "Tarea #",
            "Task name": "Nombre de tarea",
            "OMNI-Res Scale": "Escala OMNI-Res",
            "Type of Task": "Tipo de tarea",
            "Lever Arm": "Brazo de Palanca",
            "Load": "Carga",
            "Moment": "Momento",
            "Repetitions (per work day)": "Repeticiones (por jornada laboral)",
            "Damage (cumulative)": "Daño (acumulado)",
            "% Total (damage)": "% Total (daño)",
        }
        self._column_dimensions = []
        self.headers: list[QLabel] = []
        self.hidden_headers: list[QLabel] = []
        for column, title in enumerate(titles):
            caption = translated[title] if spanish else title
            if title in ("Lever Arm", "Load", "Moment"):
                unit = (
                    ("in" if imperial else "cm")
                    if title == "Lever Arm"
                    else ("lb" if imperial else "N")
                    if title == "Load"
                    else ("ft.lb" if imperial else "N.m")
                )
                caption += " (" + unit + ")"
            label = QLabel(caption)
            label.setToolTip(caption)
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            font = label.font()
            font.setBold(True)
            label.setFont(font)
            label.setFixedHeight(44 if self.compact else 42)
            self.header_grid.addWidget(label, 0, column)
            self.headers.append(label)
            width = (
                45
                if column == 0
                else 250
                if title == "OMNI-Res Scale"
                else (205 if spanish else 170)
                if title == "Type of Task"
                else 130
                if title == "Repetitions (per work day)"
                else 90
            )
            if self.compact:
                width = 80 if column == 0 else min(width, 135)
            if self.worker_layout:
                if self.kind is AssessmentKind.DUET:
                    width = (48, 180, 250, 220, 150, 105)[column]
                    stretch = (0, 2, 4, 3, 2, 1)[column]
                elif self.kind is AssessmentKind.TST:
                    width = (55, 180, 190, 95, 58, 80, 145, 115, 85)[column]
                    stretch = (0, 2, 3, 2, 1, 0, 3, 2, 0)[column]
                else:
                    width, stretch = 0, (0 if column == 0 else 1)
            else:
                stretch = 0 if column == 0 else 1
            if title == "Task name":
                width, stretch = (105 if self.compact else 135), 0
            self._column_dimensions.append((width, stretch))
            self.grid.setColumnMinimumWidth(column, width)
            self.grid.setColumnStretch(column, stretch)
            hidden = QLabel()
            self.hidden_headers.append(hidden)
            hidden.setFixedHeight(0)
            self.grid.addWidget(hidden, 0, column)
        fields = self.input_fields
        input_columns = tuple(keys.index(field) for field in fields)
        output_keys = (
            ("damage", "share")
            if self.kind is AssessmentKind.DUET
            else ("moment", "damage", "share")
        )
        output_columns = tuple(keys.index(key) for key in output_keys)
        for row, task in enumerate(source.tasks if source else ()):
            assert isinstance(task, (LifftTask, DuetTask, TstTask))
            number: QLabel | QCheckBox
            if self.selectable:
                check = QCheckBox(str(row + 1))
                check.setChecked(True)
                check.toggled.connect(self._selection_changed)
                self.task_checks[task.task_id] = check
                check.setToolTip(
                    ("Copy task " if not spanish else "Copiar tarea ") + str(row + 1)
                )
                number = check
            else:
                number = QLabel(str(row + 1))
                number.setAlignment(Qt.AlignmentFlag.AlignCenter)
            number.setProperty("jobTaskRow", row)
            number.setProperty("taskRowHeader", not self.selectable)
            if not self.read_only:
                number.setToolTip(
                    "Click: select row · Shift: range · Ctrl: add/remove row"
                    if not spanish
                    else "Clic: fila · Mayús: rango · Ctrl: añadir/quitar fila"
                )
            number.installEventFilter(self)
            self.grid.addWidget(number, row + 1, 0)
            current_name = next(
                (
                    d.name
                    for d in self.task_definitions
                    if d.definition_id == task.task_definition_id
                ),
                task.task_name or "",
            )
            name_control: QComboBox | QLabel
            if self.read_only:
                name_control = QLabel(current_name)
                name_control.setWordWrap(True)
            else:
                name_control = QComboBox()
                name_control.setEditable(True)
                name_control.setInsertPolicy(QComboBox.NoInsert)
                name_control.setSizeAdjustPolicy(
                    QComboBox.AdjustToMinimumContentsLengthWithIcon
                )
                name_control.setMinimumContentsLength(9)
                name_control.addItem("", None)
                for definition in sorted(
                    self.task_definitions,
                    key=lambda d: (d.name.casefold(), d.definition_id),
                ):
                    name_control.addItem(definition.name, definition.definition_id)
                    name_control.setItemData(
                        name_control.count() - 1,
                        definition.description or definition.definition_id,
                        Qt.ItemDataRole.ToolTipRole,
                    )
                index = name_control.findData(task.task_definition_id)
                name_control.setCurrentIndex(max(0, index))
                name_control.setEditText(current_name)
                line = name_control.lineEdit()
                assert line is not None
                callback = partial(
                    _complete_task_name,
                    ref(self),
                    ref(name_control),
                    generation,
                    task.task_id,
                )
                name_control.activated.connect(callback)
                line.editingFinished.connect(callback)
                line.setProperty("jobTaskRow", row)
                line.setProperty("jobTaskField", "task_name")
                line.installEventFilter(self)
                line.textEdited.connect(self.input_edited)
            name_control.setToolTip(
                current_name
                or (
                    "Type a task name or select a reusable name."
                    if not spanish
                    else "Escriba o seleccione un nombre de tarea."
                )
            )
            name_control.setProperty("jobTaskRow", row)
            name_control.setProperty("jobTaskField", "task_name")
            name_control.installEventFilter(self)
            self.grid.addWidget(name_control, row + 1, 1)
            self.task_names.append(name_control)
            controls: list[PrecisionLineEdit | QComboBox] = []
            for field, column in zip(fields, input_columns, strict=True):
                value = getattr(task, field)
                if field in ("direction", "omni_res_scale"):
                    control = assessment_selector(self.kind, value, self.language)
                    control.setEnabled(not self.read_only)
                    control.currentIndexChanged.connect(
                        partial(
                            _complete_grid_cell,
                            ref(self),
                            ref(control),
                            generation,
                            task.task_id,
                            field,
                        )
                    )
                else:
                    control = assessment_number(
                        value,
                        self.convention,
                        0 if field == "repetitions" else self.precision.inputs,
                    )
                    if self.worker_layout and self.kind is AssessmentKind.DUET:
                        control.setMaximumWidth(280)
                    control.textEdited.connect(self.input_edited)
                    control.setReadOnly(self.read_only)
                    control.editingFinished.connect(
                        partial(
                            _complete_grid_cell,
                            ref(self),
                            ref(control),
                            generation,
                            task.task_id,
                            field,
                        )
                    )
                control.setToolTip(self.headers[column].text())
                control.setProperty("jobTaskRow", row)
                control.setProperty("jobTaskField", field)
                control.installEventFilter(self)
                controls.append(control)
                self.grid.addWidget(control, row + 1, column)
            self.inputs.append(controls)
            outputs = tuple(QLabel() for _ in output_columns)
            for label, column in zip(outputs, output_columns, strict=True):
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.grid.addWidget(label, row + 1, column)
            self.outputs.append(outputs)
        if self.kind is AssessmentKind.TST:
            # Preserve the main ST workflow: all direction selectors, then numbers.
            order: list[QWidget] = [row[0] for row in self.inputs]
            order.extend(field for row in self.inputs for field in row[1:])
            for first, second in pairwise(order):
                QWidget.setTabOrder(first, second)
        self.select_task(min(max(0, self.selected_task_index), self.task_count - 1))
        self.show_results(results)
        self._apply_column_visibility()
        self._paint_cell_selection()
        self.refresh_geometry()

    def set_column_preferences(self, profiles: tuple[AssessmentColumns, ...]) -> None:
        """Apply personal optional-column visibility without rebinding any source.

        Args:
            profiles: Validated independent per-tool visibility preferences.

        Returns:
            None; hidden controls retain values, precision, identities and pending text.
        """
        self._column_profiles = profiles
        self._apply_column_visibility()
        self._paint_cell_selection()
        self.refresh_geometry()

    def _apply_column_visibility(self) -> None:
        """Collapse optional columns, retaining required inputs and copy selectors.

        Args:
            None.

        Returns:
            None; visibility emits no completed-cell intent or project-history command.
        """
        if not self._column_dimensions:
            return
        profile = next(
            (p for p in self._column_profiles if p.kind is self.kind),
            AssessmentColumns(self.kind),
        )
        hidden = set(profile.hidden)
        with ExitStack() as signals:
            for index, key in enumerate(assessment_column_keys(self.kind)):
                visible = key not in hidden or (self.selectable and index == 0)
                width, stretch = self._column_dimensions[index]
                self.grid.setColumnMinimumWidth(index, width if visible else 0)
                self.grid.setColumnStretch(index, stretch if visible else 0)
                self.headers[index].setVisible(visible)
                for item_index in range(self.grid.count()):
                    _row, column, _rows, _columns = self.grid.getItemPosition(
                        item_index
                    )
                    if column != index:
                        continue
                    item = self.grid.itemAt(item_index)
                    control = item.widget() if item is not None else None
                    if control is not None:
                        signals.enter_context(QSignalBlocker(control))
                        if isinstance(control, QComboBox) and control.lineEdit():
                            signals.enter_context(QSignalBlocker(control.lineEdit()))
                        control.setVisible(visible)
            self.task_names_button.setVisible(
                not self.read_only and "task_name" not in hidden
            )

    def show_results(self, results: tuple[JobTaskResult, ...]) -> None:
        """Project the matching outputs with main-panel precision and damage colors.

        Args:
            results: Exact current source outputs; empty after an input edit.

        Returns:
            None; labels clear immediately without rebuilding input controls/history.
        """
        self.result_rows = results
        for row, outputs in enumerate(self.outputs):
            item = results[row] if row < len(results) else None
            values = (
                []
                if self.kind is AssessmentKind.DUET
                else [(item.moment if item else None, self.precision.moment)]
            ) + [
                (item.damage if item else None, self.precision.damage),
                (item.share_percent if item else None, self.precision.contribution),
            ]
            for column, (label, (value, digits)) in enumerate(
                zip(outputs, values, strict=True)
            ):
                label.setText(
                    "—"
                    if value is None
                    else f"{value:.{digits}f}".replace(".", self.convention.value)
                )
                label.setToolTip("" if value is None else str(value))
                color = (
                    job_damage_color(self.kind, value)
                    if value is not None
                    and column == len(outputs) - 2
                    and self.source is not None
                    and task_has_data(self.source.tasks[row])
                    else None
                )
                label.setStyleSheet(
                    "" if color is None else f"background: {color}; border-radius: 4px;"
                )

    def focus_task(self, row: int) -> None:
        """Reveal a newly added task after queued row/header geometry has settled.

        Args:
            row: Source row to focus; invalid rows are ignored.

        Returns:
            None; only presentation changes. Any subsequent source bind cancels the
            request; a hidden grid never receives deferred focus.
        """
        if self.source is not None and 0 <= row < len(self.source.tasks):
            self._focus_task_id = self.source.tasks[row].task_id
            self.refresh_geometry()

    def refresh_geometry(self) -> None:
        """Coalesce native resize events into one sticky-header alignment pass.

        Args:
            None.

        Returns:
            None; no source or input changes occur.
        """
        if not sip.isdeleted(self) and not self._sync_pending:
            self._sync_pending = True
            QTimer.singleShot(0, self._sync_header)

    def _sync_header(self) -> None:
        """Align sticky labels with actual grid cells, including horizontal scrolling.

        Args:
            None.

        Returns:
            None; headers remain independent of task scroll position.
        """
        self._sync_pending = False
        if sip.isdeleted(self):
            return
        self.grid.activate()
        if self.worker_layout:
            viewport = self.body_scroll.viewport()
            header_viewport = self.header.viewport()
            assert viewport is not None and header_viewport is not None
            for column, label in enumerate(self.headers):
                item = self.grid.itemAtPosition(1 if self.inputs else 0, column)
                widget = item.widget() if item is not None else None
                if widget is not None and not label.isHidden():
                    label.setFixedWidth(widget.width())
            margins = self.grid.contentsMargins()
            self.header_grid.setContentsMargins(
                margins.left(),
                margins.top(),
                margins.right() + header_viewport.width() - viewport.width(),
                margins.bottom(),
            )
            bar = self.body_scroll.horizontalScrollBar()
            assert bar is not None
            self.header_widget.setFixedSize(header_viewport.width() + bar.maximum(), 42)
        else:
            inset = 2 if self.compact else 9
            self.header_grid.setContentsMargins(inset, 0, inset, 0)
            for column, label in enumerate(self.headers):
                if not label.isHidden():
                    label.setFixedWidth(self.grid.cellRect(0, column).width())
            self.header_widget.setFixedSize(
                self.frame.width(), 44 if self.compact else 42
            )
        self.header_grid.setHorizontalSpacing(self.grid.horizontalSpacing())
        self.header_grid.activate()
        self.geometry_changed.emit()
        if self._focus_task_id is not None:
            QTimer.singleShot(0, self._reveal_task)

    def _reveal_task(self) -> None:
        """Reveal pending input after row geometry and scroll range become available.

        Args:
            None.

        Returns:
            None; source replacement cancels requests. Hidden tools never steal focus.
            A request remains pending until the input is inside the actual viewport.
        """
        if sip.isdeleted(self):
            return
        identity = self._focus_task_id
        if identity is None or self.source is None:
            return
        if not self.isVisible():
            self._focus_task_id = None
            return
        for row in range(len(self.source.tasks)):
            if self.source.tasks[row].task_id == identity and self.inputs[row]:
                control = self.inputs[row][0]
                self.select_task(row)
                self.body_scroll.ensureWidgetVisible(control, 0, 12)
                control.setFocus()
                viewport = self.body_scroll.viewport()
                assert viewport is not None
                center = control.mapTo(
                    viewport, QPoint(control.width() // 2, control.height() // 2)
                )
                if viewport.rect().contains(center):
                    self._focus_task_id = None
                break

    def selected_task_rows(self, fallback: int | None = None) -> tuple[int, ...]:
        """Read selected row headers or the rows touched by a cell-range selection.

        Args:
            fallback: Host's established single-row policy when nothing is selected;
                None uses the focused row. Main may retain its last-row default.

        Returns:
            Ordered distinct zero-based rows, or empty without a valid source row.
        """
        if self._selected_rows:
            return tuple(sorted(r for r in self._selected_rows if r < self.task_count))
        area = self.selected_cell_range()
        if area is not None:
            return area[0]
        row = self.selected_task_index if fallback is None else fallback
        return (row,) if 0 <= row < self.task_count else ()

    def selected_cell_range(self) -> tuple[tuple[int, ...], tuple[str, ...]] | None:
        """Read the explicit rectangular copy range among visible editable columns.

        Args:
            None.

        Returns:
            Row indices and canonical input fields, or None for ordinary editing.
            Derived outputs and hidden optional columns never enter the range.
        """
        if not self.inputs:
            return None
        fields = tuple(
            field
            for field, control in zip(
                ("task_name", *self.input_fields),
                (self.task_names[0], *self.inputs[0]),
                strict=True,
            )
            if not control.isHidden()
        )
        if self._selected_rows:
            return tuple(sorted(self._selected_rows)), fields
        if self._cell_anchor is None or self._cell_end is None:
            return None
        (first, left), (last, right) = self._cell_anchor, self._cell_end
        if (
            left not in fields
            or right not in fields
            or max(first, last) >= self.task_count
        ):
            return None
        low, high = sorted((fields.index(left), fields.index(right)))
        return tuple(range(min(first, last), max(first, last) + 1)), fields[
            low : high + 1
        ]

    def _paint_cell_selection(self) -> None:
        """Highlight the exact copy range without altering native values or focus.

        Args:
            None.

        Returns:
            None; the Copy caption describes selected cells, or ordinary full-grid copy.
        """
        selection = self.selected_cell_range()
        rows, fields = selection if selection is not None else ((), ())
        for index, inputs in enumerate(self.inputs):
            number_item = self.grid.itemAtPosition(index + 1, 0)
            number = number_item.widget() if number_item is not None else None
            if number is not None and not self.read_only:
                number.setStyleSheet(
                    "background:#DDF2F4;color:#087E91;font-weight:bold;"
                    "border:1px solid #08A9B5;border-radius:3px;"
                    if index in rows
                    else ""
                )
            for field, control in zip(
                ("task_name", *self.input_fields),
                (self.task_names[index], *inputs),
                strict=True,
            ):
                selected = index in self._selected_rows or (
                    index in rows and field in fields
                )
                widgets = [control]
                if isinstance(control, QComboBox) and control.isEditable():
                    line = control.lineEdit()
                    if line is not None:
                        widgets.append(line)
                for widget in widgets:
                    if bool(widget.property("taskRangeSelected")) == selected:
                        continue
                    widget.setProperty("taskRangeSelected", selected)
                    style = widget.style()
                    if style is not None:
                        style.unpolish(widget)
                        style.polish(widget)
                    widget.update()
        count = len(rows) * len(fields)
        self.copy_cells_button.setText(
            (
                f"Copiar {count} celdas"
                if self.language is Language.SPANISH
                else f"Copy {count} cells"
            )
            if count
            else (
                "Copiar celdas" if self.language is Language.SPANISH else "Copy cells"
            )
        )

    def eventFilter(self, watched: QObject | None, event: QEvent | None) -> bool:  # noqa: N802 - Qt override
        """Track geometry/focus and handle explicit copy-range gestures.

        Args:
            watched: Native child input, task label, frame or viewport.
            event: Focus/mouse/resize notification; never rewritten.

        Returns:
            True only for explicit range selection/copy/cancellation or structured
            paste; ordinary editing, text Undo and popup operation stay native.
        """
        if isinstance(event, QKeyEvent) and event.type() == QEvent.Type.KeyPress:
            if self.selected_cell_range() is not None and event.matches(
                QKeySequence.Copy
            ):
                self.copy_cells_button.click()
                return True
            if event.key() == Qt.Key.Key_Escape and (
                self._cell_end is not None or self._selected_rows
            ):
                self._cell_end = None
                self._selected_rows.clear()
                self._paint_cell_selection()
                return True
        if (
            isinstance(watched, QWidget)
            and isinstance(event, QMouseEvent)
            and event.type() == QEvent.Type.MouseButtonPress
            and event.button() == Qt.MouseButton.LeftButton
            and not self.read_only
        ):
            row, field = (
                watched.property("jobTaskRow"),
                watched.property("jobTaskField"),
            )
            if isinstance(row, int) and watched.property("taskRowHeader"):
                if (
                    event.modifiers() & Qt.KeyboardModifier.ShiftModifier
                    and self._row_anchor is not None
                ):
                    self._selected_rows = set(
                        range(
                            min(row, self._row_anchor), max(row, self._row_anchor) + 1
                        )
                    )
                elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    self._selected_rows.symmetric_difference_update({row})
                    self._row_anchor = row
                else:
                    self._selected_rows = {row}
                    self._row_anchor = row
                self._cell_anchor = self._cell_end = None
                self.select_task(row)
                self._paint_cell_selection()
                return True
            if isinstance(row, int) and isinstance(field, str):
                self._selected_rows.clear()
                if (
                    event.modifiers() & Qt.KeyboardModifier.ShiftModifier
                    and self._cell_anchor is not None
                ):
                    self._cell_end = row, field
                    self._paint_cell_selection()
                    return True
                self._cell_anchor, self._cell_end = (row, field), None
                self._paint_cell_selection()
        if (
            isinstance(event, QKeyEvent)
            and event.type() == QEvent.Type.KeyPress
            and event.matches(QKeySequence.Paste)
            and not self.read_only
        ):
            clipboard = QApplication.clipboard()
            if clipboard is not None and (
                any(mark in clipboard.text() for mark in ("\t", "\n", "\r"))
                or (
                    self.selected_input_field != "task_name"
                    and (
                        ";" in clipboard.text()
                        or "|" in clipboard.text()
                        or clipboard.text().count(",") > 1
                    )
                )
            ):
                self.paste_cells_button.click()
                return True
        if event is not None:
            if event.type() == QEvent.Type.Resize:
                self.refresh_geometry()
            if isinstance(watched, QWidget) and event.type() in (
                QEvent.Type.FocusIn,
                QEvent.Type.MouseButtonPress,
            ):
                field = watched.property("jobTaskField")
                if isinstance(field, str):
                    self.selected_input_field = field
                row = watched.property("jobTaskRow")
                if isinstance(row, int):
                    self.select_task(row)
        return False

    def selected_task_ids(self) -> tuple[str, ...]:
        """Return checked source identities in their original order.

        Args:
            None.

        Returns:
            Checked task IDs; empty outside a selectable source preview.
        """
        return tuple(
            key for key, check in self.task_checks.items() if check.isChecked()
        )

    def set_task_selection(self, identities: tuple[str, ...]) -> None:
        """Change copy selection only, keeping every source/output read-only.

        Args:
            identities: Desired existing task identities; unlisted rows are unchecked.

        Returns:
            None; emit one selection notification and no source edit/history action.
        """
        for identity, check in self.task_checks.items():
            with QSignalBlocker(check):
                check.setChecked(identity in identities)
        self._selection_changed()

    def _selection_changed(self) -> None:
        """Notify the copy host after checkbox changes without accepting source edits.

        Args:
            None.

        Returns:
            None; selection belongs to the copy dialog, never project data.
        """
        self.task_selection_changed.emit(self.selected_task_ids())

    def _finish_cell(
        self,
        generation: int,
        task_id: str,
        field: str,
        control: PrecisionLineEdit | QComboBox,
    ) -> None:
        """Notify a completed native input without parsing or mutating its source.

        Args:
            generation: Projection generation captured when the widget was created.
            task_id: Exact task identity captured at construction, never a row lookup.
            field: Stable numeric or selector field name for the owning adapter.
            control: Completing native control, carrying exact text or selector data.

        Returns:
            None; read-only previews never emit accepted-cell notifications.
        """
        if (
            not sip.isdeleted(self)
            and not self.read_only
            and self.source is not None
            and generation == self._generation
        ):
            value = (
                control.source_text()
                if isinstance(control, PrecisionLineEdit)
                else control.currentData()
            )
            self.cell_finished.emit(AssessmentCellEdit(task_id, field, value))


def _complete_grid_cell(
    grid_ref: ReferenceType[AssessmentTaskGrid],
    control_ref: ReferenceType[PrecisionLineEdit | QComboBox],
    generation: int,
    task_id: str,
    field: str,
    _index: int | None = None,
) -> None:
    """Route native completion without retaining a grid/control reference cycle.

    Args:
        grid_ref: Weak grid owner; cleared before Python/native widget teardown.
        control_ref: Weak emitting input; never keeps a retired widget alive.
        generation: Exact projection generation captured when connecting this cell.
        task_id: Stable task identity from that same projection.
        field: Stable numeric/selector field name.
        _index: Ignored Qt selector index; typed item data is read by the live grid.

    Returns:
        None; collected/deleted owners and inputs cannot emit another edit intent.
    """
    grid, control = grid_ref(), control_ref()
    if (
        grid is not None
        and control is not None
        and not sip.isdeleted(grid)
        and not sip.isdeleted(control)
    ):
        grid._finish_cell(generation, task_id, field, control)


def _complete_task_name(
    grid_ref: ReferenceType[AssessmentTaskGrid],
    control_ref: ReferenceType[QComboBox],
    generation: int,
    task_id: str,
    _index: int | None = None,
) -> None:
    """Emit one literal/local or explicitly selected reusable name for a live row.

    Args:
        grid_ref: Weak shared-grid owner; never retains a closed editor.
        control_ref: Weak editable name selector from that projection.
        generation: Projection identity preventing retired focus events from editing.
        task_id: Stable source row, never the reusable definition identity.
        _index: Ignored native activation index; current typed item data is inspected.

    Returns:
        None; source acceptance, references and history remain with the host adapter.
    """
    grid, control = grid_ref(), control_ref()
    if (
        grid is None
        or control is None
        or sip.isdeleted(grid)
        or sip.isdeleted(control)
        or grid.read_only
        or generation != grid._generation
    ):
        return
    name = control.currentText() if control.currentText().strip() else None
    identity = control.currentData()
    definition = next(
        (d for d in grid.task_definitions if d.definition_id == identity), None
    )
    if definition is None or definition.name != name:
        identity = None
    grid.task_name_finished.emit(task_id, name, identity)

"""Shared LiFFT/DUET/ST grid for main assessments, Jobs and read-only copy previews.

Presentation layer. Sticky headers, column order, numeric inputs, descriptive
selectors and read-only outputs follow the main assessment UI. Completed cells emit
task/field identities; hosts own parsing, canonical source edits, calculation,
persistence and shared history.
A read-only instance previews copied sources without emitting edits.
"""

from dataclasses import dataclass
from functools import partial
from itertools import pairwise
from weakref import ReferenceType, ref

from PyQt5 import sip
from PyQt5.QtCore import (
    QEvent,
    QObject,
    QPoint,
    QSignalBlocker,
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QLabel,
    QLayout,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
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
from ergotools.presentation.desktop.assessment_controls import (
    assessment_number,
    assessment_selector,
)
from ergotools.presentation.desktop.precision_editor import PrecisionLineEdit
from ergotools.presentation.desktop.theme.job_results import job_damage_color
from ergotools.presentation.desktop.theme.main_workspace import MAIN_WORKSPACE_STYLE


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

    def __init__(
        self,
        language: Language,
        convention: DecimalConvention,
        parent: QWidget | None = None,
        *,
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
        self.language = language
        self.convention = convention
        self.kind = kind
        self.precision = precision or DisplayPrecision()
        self.read_only = read_only
        self.selectable = selectable
        self.compact = compact
        self.worker_layout = worker_layout
        self.task_checks: dict[str, QCheckBox] = {}
        self.system = system
        self.source: AssessmentDraft | None = None
        self._focus_task_id: str | None = None
        self.inputs: list[list[PrecisionLineEdit | QComboBox]] = []
        self.outputs: list[tuple[QLabel, ...]] = []
        self.selected_task_index = -1
        self._sync_pending = False
        self._generation = 0
        self.setStyleSheet(
            MAIN_WORKSPACE_STYLE
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
        self.source = source
        self.inputs = []
        self.outputs = []
        self.task_checks = {}
        for grid in (self.grid, self.header_grid):
            while grid.count():
                item = grid.takeAt(0)
                widget = item.widget() if item is not None else None
                if widget is not None:
                    widget.hide()
                    widget.deleteLater()
        spanish = self.language is Language.SPANISH
        imperial = (
            source.system if isinstance(source, (LifftDraft, TstDraft)) else self.system
        ) is MeasurementSystem.IMPERIAL
        titles = (
            [
                "Task #",
                "OMNI-Res Scale",
                "Repetitions (per work day)",
                "Damage (cumulative)",
                "% Total (damage)",
            ]
            if self.kind is AssessmentKind.DUET
            else [
                "Task #",
                *(["Type of Task"] if self.kind is AssessmentKind.TST else []),
                "Lever Arm",
                "Load",
                "Moment",
                "Repetitions (per work day)",
                "Damage (cumulative)",
                "% Total (damage)",
            ]
        )
        translated = {
            "Task #": "Tarea #",
            "OMNI-Res Scale": "Escala OMNI-Res",
            "Type of Task": "Tipo de tarea",
            "Lever Arm": "Brazo de Palanca",
            "Load": "Carga",
            "Moment": "Momento",
            "Repetitions (per work day)": "Repeticiones (por jornada laboral)",
            "Damage (cumulative)": "Daño (acumulado)",
            "% Total (damage)": "% Total (daño)",
        }
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
                else 170
                if title == "Type of Task"
                else 130
                if title == "Repetitions (per work day)"
                else 90
            )
            if self.compact:
                width = 80 if column == 0 else min(width, 135)
            if self.worker_layout:
                if self.kind is AssessmentKind.DUET:
                    width = (48, 250, 220, 150, 105)[column]
                    stretch = (0, 4, 3, 2, 1)[column]
                elif self.kind is AssessmentKind.TST:
                    width = (55, 190, 95, 58, 80, 145, 115, 85)[column]
                    stretch = (0, 3, 2, 1, 0, 3, 2, 0)[column]
                else:
                    width, stretch = 0, 0
            else:
                stretch = 0 if column == 0 else 1
            self.grid.setColumnMinimumWidth(column, width)
            self.grid.setColumnStretch(column, stretch)
            hidden = QLabel()
            self.hidden_headers.append(hidden)
            hidden.setFixedHeight(0)
            self.grid.addWidget(hidden, 0, column)
        fields = self.input_fields
        input_columns = (
            (1, 2)
            if self.kind is AssessmentKind.DUET
            else (1, 2, 3, 5)
            if self.kind is AssessmentKind.TST
            else (1, 2, 4)
        )
        output_columns = (
            (3, 4)
            if self.kind is AssessmentKind.DUET
            else (4, 6, 7)
            if self.kind is AssessmentKind.TST
            else (3, 5, 6)
        )
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
            number.installEventFilter(self)
            self.grid.addWidget(number, row + 1, 0)
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
        self.refresh_geometry()

    def show_results(self, results: tuple[JobTaskResult, ...]) -> None:
        """Project the matching outputs with main-panel precision and damage colors.

        Args:
            results: Exact current source outputs; empty after an input edit.

        Returns:
            None; labels clear immediately without rebuilding input controls/history.
        """
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
                if widget is not None:
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

    def eventFilter(self, watched: QObject | None, event: QEvent | None) -> bool:  # noqa: N802 - Qt override
        """Track selected tasks and header geometry without intercepting native input.

        Args:
            watched: Native child input, task label, frame or viewport.
            event: Focus/mouse/resize notification; never rewritten.

        Returns:
            False; keyboard editing, text Undo and popup operation stay native.
        """
        if event is not None:
            if event.type() == QEvent.Type.Resize:
                self.refresh_geometry()
            if isinstance(watched, QWidget) and event.type() in (
                QEvent.Type.FocusIn,
                QEvent.Type.MouseButtonPress,
            ):
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

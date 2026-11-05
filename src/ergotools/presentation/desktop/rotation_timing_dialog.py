"""Reusable Shift timing editor using shared project history and the sole Main Save.

Presentation layer. Ordinary controls and a timeline edit the same complete minute
model. Valid edits are accepted privately; unfinished break rows stay local and cannot
partially write. Opening alone creates no template. The optimizer is not called.
Expected-state ports edit one Shift template or one independent scenario copy.
"""

import logging
from collections.abc import Callable, Mapping
from dataclasses import replace
from functools import partial
from itertools import pairwise

from PyQt5.QtCore import QSignalBlocker, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.rotation_segments import (
    TimingSegment,
    from_timing_segments,
    redistribute_timing_segments,
    remove_timing_segment,
    segment_position,
    timing_segments,
)
from ergotools.application.rotation_timing import ShiftClock, shift_clock
from ergotools.application.rotation_timing_actions import (
    change_timing_break,
    edit_contiguous_breaks,
    remove_work_block,
    separate_work_blocks,
    split_work_block,
)
from ergotools.application.settings import Language
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.rotation_timing import (
    MinuteInterval,
    RotationTiming,
    TimedBreak,
    equal_minutes,
    equal_timing,
)
from ergotools.presentation.desktop.optional_time_edit import OptionalTimeEdit
from ergotools.presentation.desktop.project_history_actions import ProjectHistoryActions
from ergotools.presentation.desktop.rotation_timeline import RotationTimeline
from ergotools.presentation.desktop.secondary_history_controls import (
    add_history_buttons,
)
from ergotools.presentation.desktop.theme.dialogs import apply_dialog_theme
from ergotools.presentation.desktop.timing_tool_icons import timing_tool_icon

# Operational failures are logged at the owned Qt boundary; no silent rollback/success.
_LOG = logging.getLogger(__name__)
# Known domain corrections; literal Shift/break names remain untranslated.
_ERRORS = {
    "Remove the break before joining these work blocks.": (
        "Quite el descanso antes de unir estos bloques."
    ),
    "Separate interrupted blocks before joining them.": (
        "Separe los bloques interrumpidos antes de unirlos."
    ),
    "Split inside a work block, not inside a break.": (
        "Divida dentro de un bloque de trabajo, no de un descanso."
    ),
    "Split inside a work block, away from an existing boundary.": (
        "Divida dentro del bloque, lejos de un límite existente."
    ),
    "Choose a boundary between two work blocks to join.": (
        "Elija un límite entre dos bloques para unirlos."
    ),
    "Select a work block first.": ("Seleccione primero un bloque de trabajo."),
    "Keep at least one work block; draw a break to remove work time.": (
        "Conserve un bloque de trabajo; dibuje un descanso para quitar "
        "tiempo de trabajo."
    ),
    "Choose a positive break interval.": (
        "Elija un intervalo positivo para el descanso."
    ),
    "Select a break first.": ("Seleccione primero un descanso."),
    "Join only touching breaks; work between breaks must remain work.": (
        "Una solo descansos contiguos; el trabajo intermedio debe conservarse."
    ),
    "Clock offset must be inside the shift.": ("La hora debe estar dentro del turno."),
    "Enter a complete 24-hour clock as HH:mm.": (
        "Ingrese una hora completa en formato HH:mm."
    ),
    "Use positive whole-minute intervals inside the shift.": (
        "Use intervalos positivos de minutos dentro del turno."
    ),
    "Breaks must be ordered, inside the shift and not overlap.": (
        "Los descansos deben estar dentro del turno y no superponerse."
    ),
    "Positive block durations must cover all productive minutes.": (
        "Los bloques deben cubrir todos los minutos productivos. Ajuste "
        "el último bloque o use bloques iguales."
    ),
    "The shift must contain productive time.": (
        "El turno debe incluir tiempo productivo."
    ),
    "Block count cannot exceed productive minutes.": (
        "La cantidad de bloques no puede superar los minutos productivos."
    ),
    "Keep at least one productive minute in each neighboring block.": (
        "Conserve al menos un minuto productivo en cada bloque vecino."
    ),
    "Select an existing Shift.": ("Seleccione un turno existente."),
    "Set Shift start and end times before defining rotation timing.": (
        "Defina las horas de inicio y término del turno antes de sus "
        "tiempos de rotación."
    ),
}


class RotationTimingDialog(QDialog):
    """Edit one Shift's relative template; opening never creates a project record."""

    def __init__(
        self,
        workspace: ProjectWorkspace[AssessmentDraft],
        shift_id: str,
        icons: Mapping[str, QIcon],
        language: Language = Language.ENGLISH,
        parent: QWidget | None = None,
        *,
        read_target: Callable[[], tuple[ShiftClock, RotationTiming | None]]
        | None = None,
        write_target: Callable[[RotationTiming | None, RotationTiming | None], bool]
        | None = None,
        target_label: str | None = None,
    ) -> None:
        """Bind one project/Shift and construct the reusable timed editor.

        Args:
            workspace: Borrowed current private project with shared history.
            shift_id: Existing Shift with complete start/end clocks.
            icons: Packaged application icons for shared history/actions.
            language: English/Spanish captions; clock values remain 24-hour.
            parent: Modal owner retaining the organization form.
            read_target: Optional scenario reader, paired with write_target.
            write_target: Optional guarded scenario acceptor; False means cancelled.
            target_label: Literal rotation label instead of a Shift template caption.

        Returns:
            None; initial equal-block preview is not persisted.

        Raises:
            ValueError: Shift clocks are missing/invalid.
            RuntimeError: Project has no shared editing owner.
        """
        super().__init__(parent)
        self.workspace, self.shift_id, self.language = workspace, shift_id, language
        if (read_target is None) != (write_target is None):
            raise ValueError("Timing target requires both read and write callbacks.")
        self._read_target, self._write_target = read_target, write_target
        self._target_label = target_label
        self._editing = workspace.editing
        if self._editing is None:
            raise RuntimeError("Timing editor requires a project editing session.")
        self.clock = (
            read_target()[0]
            if read_target is not None
            else shift_clock(workspace.read_hierarchy().hierarchy, shift_id)
        )
        self._model = equal_timing(
            self.clock.span_minutes, min(4, self.clock.span_minutes)
        )
        self._saved: RotationTiming | None = None
        self._loading = True
        self._draft_pending = False
        self._pending_duration: int | None = None
        self._pending_block_clock: tuple[int, str] | None = None
        self._pending_break_duration: int | None = None
        self.block_clocks: list[tuple[OptionalTimeEdit, OptionalTimeEdit]] = []
        self.break_spins: list[QSpinBox] = []
        self._owner_missing = False
        self._break_generation = 0
        self._block_generation = 0
        self.break_rows: list[tuple[QLineEdit, OptionalTimeEdit, OptionalTimeEdit]] = []
        self.block_spins: list[QSpinBox] = []
        self.setWindowTitle(
            self.text("Rotation timing", "Tiempos de la rotación")
            if read_target is not None
            else self.text("Shift rotation timing", "Tiempos de rotación del turno")
        )
        self.setWindowIcon(icons["shift"])
        self.resize(1240, 860)
        self.setMinimumSize(1080, 790)
        apply_dialog_theme(self)
        self.setStyleSheet(
            # Preserve native spin frames/arrows, as in Organization time controls.
            # Other owned controls retain the common dialog palette and typography.
            self.styleSheet().replace("QDialog QAbstractSpinBox", "QDialog QComboBox")
            + (
                "QHeaderView::section {background:#EDF3F6;color:#0B326C;"
                "border:0;padding:6px;font-weight:600;}"
                "QAbstractSpinBox QLineEdit {border:0;padding:0;}"
            )
        )
        layout = QVBoxLayout(self)
        title_row = QHBoxLayout()
        title = QLabel(
            self.text("Rotation timing", "Tiempos de rotación")
            + " · "
            + (target_label or shift_id)
        )
        title.setStyleSheet("font-size:20px;font-weight:700;color:#0B326C;")
        title_row.addWidget(title)
        title_row.addStretch(1)
        self.history = ProjectHistoryActions(
            self,
            self._editing,
            icons,
            language,
            prepare=self.prepare,
            restored=self.reload,
            pending=self.pending_action,
        )
        add_history_buttons(
            title_row, self.history.undo_button, self.history.redo_button
        )
        layout.addLayout(title_row)
        self.clock_label = QLabel()
        layout.addWidget(self.clock_label)
        notice = QLabel(
            self.text(
                "Independent rotation timing; the recurring Shift stays unchanged."
                if read_target is not None
                else "Reusable Shift timing; rotations use independent copies.",
                "Tiempos propios de la rotación; el turno habitual no cambia."
                if read_target is not None
                else "Plantilla de turno; cada rotación usa una copia independiente.",
            )
        )
        notice.setWordWrap(True)
        notice.setStyleSheet("color:#526E82;")
        layout.addWidget(notice)

        self.timeline = RotationTimeline(language=language)
        self.timeline.setAccessibleName(
            self.text("Work blocks and breaks", "Bloques de trabajo y descansos")
        )
        self.timeline.setToolTip(
            self.text(
                (
                    "Drag a boundary to redistribute work; "
                    "Escape cancels a drag. Arrow keys adjust"
                    " the selected boundary."
                ),
                (
                    "Arrastre un límite para redistribuir "
                    "trabajo; Escape cancela. Las flechas "
                    "ajustan el límite seleccionado."
                ),
            )
        )
        self.timeline.timing_changed.connect(self.gesture_finished)
        self.timeline.selection_changed.connect(self.select_timeline_segment)
        self.timeline.operation_error.connect(self.show_error)
        self.timeline.tool_changed.connect(self.sync_tool)
        tools = QHBoxLayout()
        self.timeline_tools: dict[str, QPushButton] = {}
        self.tool_group = QButtonGroup(self)
        self.tool_group.setExclusive(True)
        for key, captions in (
            ("select", ("Select", "Seleccionar")),
            ("split", ("Split block", "Dividir bloque")),
            ("draw_break", ("Draw break", "Dibujar descanso")),
            ("move", ("Move / resize", "Mover / ajustar")),
            ("join", ("Join", "Unir")),
            ("remove", ("Remove", "Quitar")),
        ):
            button = QPushButton(self.text(*captions))
            button.setIcon(timing_tool_icon(key))
            button.setIconSize(QSize(22, 22))
            button.setCheckable(True)
            button.setAutoDefault(False)
            button.setStyleSheet(
                "QPushButton:checked {background:#DDF2F4;border:1px solid #08A9B5;}"
            )
            button.clicked.connect(partial(self.choose_tool, key))
            self.tool_group.addButton(button)
            self.timeline_tools[key] = button
            tools.addWidget(button)
        tools.addStretch(1)
        tools.addWidget(QLabel(self.text("Snap (min)", "Ajuste (min)")))
        self.snap = QSpinBox()
        self.snap.setRange(1, 60)
        self.snap.setMinimumHeight(32)
        self.snap.setValue(5)
        self.snap.setToolTip(
            self.text(
                "Pointer and arrow-key time increment; manual "
                "clocks retain exact minutes.",
                "Incremento para puntero y flechas; las horas "
                "manuales conservan minutos exactos.",
            )
        )
        self.snap.valueChanged.connect(self.snap_changed)
        tools.addWidget(self.snap)
        layout.addLayout(tools)
        layout.addWidget(self.timeline)
        self.tool_hint = QLabel()
        self.tool_hint.setWordWrap(True)
        layout.addWidget(self.tool_hint)
        self.sync_tool("select")
        options = QHBoxLayout()
        self.equal_button = QPushButton(self.text("Equal blocks", "Bloques iguales"))
        self.unequal_button = QPushButton(
            self.text("Unequal blocks", "Bloques distintos")
        )
        for button in (self.equal_button, self.unequal_button):
            button.setCheckable(True)
            button.setStyleSheet(
                "QPushButton:checked "
                "{background:#DDF2F4;color:#008DA8;border:1px"
                " solid #08A9B5;}"
            )
            options.addWidget(button)
        self.equal_button.setToolTip(
            self.text(
                "As equal as whole minutes allow; remainder minutes "
                "go to earlier blocks.",
                "Tan iguales como permiten los minutos enteros; "
                "los minutos restantes van a los primeros bloques.",
            )
        )
        self.equal_button.clicked.connect(self.mode_equal)
        self.unequal_button.clicked.connect(self.mode_unequal)
        count_pair = QHBoxLayout()
        count_pair.setSpacing(5)
        count_label = QLabel(self.text("Count", "Cantidad"))
        count_label.setFixedWidth(
            count_label.fontMetrics().horizontalAdvance(count_label.text()) + 4
        )
        count_pair.addWidget(count_label)
        self.count = QSpinBox()
        self.count.setRange(1, self.clock.span_minutes)
        self.count.setKeyboardTracking(False)
        self.count.setMinimumHeight(32)
        self.count.setToolTip(
            self.text(
                "Changing count redistributes productive minutes equally.",
                "Cambiar la cantidad redistribuye por igual los minutos productivos.",
            )
        )
        self.count.valueChanged.connect(self.count_changed)
        self.count.setFixedWidth(80)
        count_pair.addWidget(self.count)
        options.addLayout(count_pair)
        self.subtract = QCheckBox(
            self.text(
                "Exclude breaks from the time used for averages",
                "Excluir descansos del tiempo usado para promedios",
            )
        )
        self.subtract.setToolTip(
            self.text(
                (
                    "Breaks never contain work. This option "
                    "changes the averaging denominator, not "
                    "Job risk or recovery."
                ),
                (
                    "Los descansos nunca contienen trabajo. "
                    "Cambia el divisor del promedio, no el "
                    "riesgo del trabajo ni la recuperación."
                ),
            )
        )
        self.subtract.toggled.connect(self.form_finished)
        layout.addWidget(self.subtract)
        self.body = QWidget()
        columns = QHBoxLayout(self.body)
        columns.setContentsMargins(0, 0, 0, 0)
        pause_group = QGroupBox(self.text("Breaks", "Descansos"))
        pause_layout = QVBoxLayout(pause_group)
        self.break_table = QTableWidget(0, 4)
        self.break_table.setHorizontalHeaderLabels(
            [
                self.text("Name (optional)", "Nombre (opcional)"),
                self.text("Start", "Inicio"),
                self.text("End", "Término"),
                self.text("Minutes", "Minutos"),
            ]
        )
        break_header = self.break_table.horizontalHeader()
        assert break_header is not None
        break_header.setSectionResizeMode(0, QHeaderView.Stretch)
        for index in (1, 2, 3):
            self.break_table.setColumnWidth(index, 90)
        self.break_table.setToolTip(
            self.text(
                (
                    "24-hour clocks within the Shift. Breaks "
                    "are shown chronologically; overnight "
                    "clocks are supported."
                ),
                (
                    "Horas de 24 h dentro del turno. Los "
                    "descansos se ordenan cronológicamente; "
                    "se admiten turnos nocturnos."
                ),
            )
        )
        pause_layout.addWidget(self.break_table)
        pause_actions = QHBoxLayout()
        self.add_break_button = QPushButton(self.text("+ Break", "+ Descanso"))
        self.remove_break_button = QPushButton(self.text("- Break", "- Descanso"))
        self.add_break_button.setToolTip(
            self.text(
                "Add a reversible 15-minute pause in selected work; "
                "its clocks remain editable.",
                "Añadir un descanso de 15 minutos en el trabajo seleccionado; "
                "edite sus horas.",
            )
        )
        self.remove_break_button.setToolTip(
            self.text(
                "Remove the break; adjacent segments expand into its time.",
                "Quitar el descanso seleccionado y unir el trabajo vecino.",
            )
        )
        self.add_break_button.clicked.connect(self.add_break)
        self.remove_break_button.clicked.connect(self.remove_break)
        self.remove_break_button.setEnabled(False)
        pause_actions.addWidget(self.add_break_button)
        pause_actions.addWidget(self.remove_break_button)
        pause_actions.addStretch(1)
        pause_layout.insertLayout(0, pause_actions)
        break_options = QHBoxLayout()
        self.equal_break_button = QPushButton(
            self.text("Equal breaks", "Descansos iguales")
        )
        self.unequal_break_button = QPushButton(
            self.text("Unequal breaks", "Descansos distintos")
        )
        for button in (self.equal_break_button, self.unequal_break_button):
            button.setCheckable(True)
            button.setAutoDefault(False)
            button.setStyleSheet(self.equal_button.styleSheet())
            break_options.addWidget(button)
        self.equal_break_button.setToolTip(
            self.text(
                "Divide the existing total break time equally, preserving names.",
                "Repartir por igual el tiempo total de descanso, conservando nombres.",
            )
        )
        self.unequal_break_button.setToolTip(
            self.text(
                "Edit individual break durations without redistributing other "
                "intervals.",
                "Editar duraciones individuales sin redistribuir otros intervalos.",
            )
        )
        self.equal_break_button.clicked.connect(self.mode_equal_breaks)
        self.unequal_break_button.clicked.connect(self.mode_unequal_breaks)
        break_count_pair = QHBoxLayout()
        break_count_pair.setSpacing(5)
        break_count_label = QLabel(self.text("Count", "Cantidad"))
        break_count_label.setFixedWidth(
            break_count_label.fontMetrics().horizontalAdvance(break_count_label.text())
            + 4
        )
        break_count_pair.addWidget(break_count_label)
        self.break_count = QSpinBox()
        self.break_count.setRange(0, self.clock.span_minutes - 1)
        self.break_count.setFixedWidth(80)
        self.break_count.setMinimumHeight(32)
        self.break_count.setKeyboardTracking(False)
        self.break_count.setToolTip(
            self.text(
                "Change the number of breaks; review redistribution before accepting.",
                "Cambiar la cantidad de descansos; revise la redistribución antes "
                "de aceptar.",
            )
        )
        self.break_count.valueChanged.connect(self.break_count_changed)
        break_count_pair.addWidget(self.break_count)
        break_options.addLayout(break_count_pair)
        pause_layout.insertLayout(1, break_options)

        block_group = QGroupBox(self.text("Work blocks", "Bloques de trabajo"))
        block_layout = QVBoxLayout(block_group)
        block_layout.addLayout(options)
        self.block_table = QTableWidget(0, 5)
        self.block_table.setHorizontalHeaderLabels(
            [
                self.text("Block", "Bloque"),
                self.text("Start", "Inicio"),
                self.text("End", "Término"),
                self.text("Minutes", "Minutos"),
                self.text("Work interval", "Intervalo de trabajo"),
            ]
        )
        self.block_table.setEditTriggers(QTableWidget.NoEditTriggers)
        row_header = self.block_table.verticalHeader()
        assert row_header is not None
        row_header.hide()
        block_header = self.block_table.horizontalHeader()
        assert block_header is not None
        block_header.setSectionResizeMode(4, QHeaderView.Stretch)
        for index, width in ((0, 64), (1, 90), (2, 90), (3, 80)):
            self.block_table.setColumnWidth(index, width)
        self.block_table.setToolTip(
            self.text(
                (
                    "Unequal mode: edit a duration or drag "
                    "its boundary. Only neighboring budgets "
                    "change; one block may span a break."
                ),
                (
                    "Modo distinto: edite minutos o arrastre "
                    "un límite. Solo cambian bloques vecinos;"
                    " un bloque puede cruzar un descanso."
                ),
            )
        )
        block_actions = QHBoxLayout()
        self.add_block_button = QPushButton(self.text("+ Block", "+ Bloque"))
        self.remove_block_button = QPushButton(self.text("- Block", "- Bloque"))
        self.add_block_button.setToolTip(
            self.text(
                "Split the selected block in half, keeping the other durations.",
                "Dividir el bloque seleccionado por la mitad sin cambiar los demás.",
            )
        )
        self.remove_block_button.setToolTip(
            self.text(
                "Join the selected block to a neighbor; no work minutes are deleted.",
                "Unir el bloque con un vecino sin borrar minutos de trabajo.",
            )
        )
        self.add_block_button.clicked.connect(self.add_block)
        self.remove_block_button.clicked.connect(self.remove_block)
        block_actions.addWidget(self.add_block_button)
        block_actions.addWidget(self.remove_block_button)
        block_actions.addStretch(1)
        block_layout.insertLayout(0, block_actions)
        block_layout.addWidget(self.block_table)
        columns.addWidget(block_group, 1)
        columns.addWidget(pause_group, 1)
        layout.addWidget(self.body, 1)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setStyleSheet("background:#EAF7F8;color:#0B326C;padding:8px;")
        layout.addWidget(self.summary)
        self.error = QLabel()
        self.error.setStyleSheet("color:#AD302B;")
        self.error.setWordWrap(True)
        layout.addWidget(self.error)
        footer = QHBoxLayout()
        self.clear_button = QPushButton(
            self.text("Clear timing", "Quitar tiempos")
            if read_target is not None
            else self.text("Clear template", "Quitar plantilla")
        )
        self.clear_button.clicked.connect(self.clear_template)
        footer.addWidget(self.clear_button)
        footer.addWidget(
            QLabel(
                self.text(
                    "Accepted edits use the main project Save.",
                    "Los cambios aceptados usan Guardar del proyecto.",
                )
            )
        )
        footer.addStretch(1)
        self.use_button = QPushButton(
            self.text("Use this timing", "Usar estos tiempos")
        )
        self.use_button.clicked.connect(self.use_timing)
        footer.addWidget(self.use_button)
        self.close_button = QPushButton(self.text("Close", "Cerrar"))
        self.close_button.clicked.connect(self.accept)
        footer.addWidget(self.close_button)
        layout.addLayout(footer)
        for button in (
            self.equal_button,
            self.unequal_button,
            self.add_break_button,
            self.remove_break_button,
            self.add_block_button,
            self.remove_block_button,
            self.clear_button,
            self.use_button,
            self.close_button,
        ):
            button.setAutoDefault(False)
            button.setDefault(False)
        self.block_table.currentCellChanged.connect(
            lambda row, _col, _old, _oldcol: self.select_table_segment("block", row)
        )
        self.break_table.currentCellChanged.connect(
            lambda row, _col, _old, _oldcol: self.select_table_segment("break", row)
        )
        for control, name in (
            (self.add_break_button, "add_break"),
            (self.remove_break_button, "remove_break"),
            (self.add_block_button, "add_work_block"),
            (self.remove_block_button, "remove_work_block"),
            (self.equal_button, "equal_work_blocks"),
            (self.unequal_button, "unequal_work_blocks"),
            (self.equal_break_button, "equal_breaks"),
            (self.unequal_break_button, "unequal_breaks"),
            (self.use_button, "apply_timing"),
            (self.clear_button, "clear_timing"),
            (self.close_button, "close"),
        ):
            control.setIcon(icons.get(name, QIcon()))
            control.setIconSize(QSize(32, 32))
        for mode_button in (
            self.equal_button,
            self.unequal_button,
            self.equal_break_button,
            self.unequal_break_button,
        ):
            mode_button.setIconSize(QSize(48, 48))
        self.use_button.setIconSize(QSize(40, 40))
        self.reload()

    def text(self, english: str, spanish: str) -> str:
        """Resolve captions without changing clock, Shift or break identities.

        Args:
            english: English interface text.
            spanish: Spanish interface text.

        Returns:
            Current-language caption.
        """
        return spanish if self.language is Language.SPANISH else english

    def show_error(self, error: ValueError | str) -> None:
        """Retain unfinished intent and explain why no template was accepted.

        Args:
            error: Known domain validation or owned operational guidance.

        Returns:
            None; accepted project data and the last valid timeline remain intact.
        """
        message = str(error)
        self.error.setText(
            _ERRORS.get(message, message)
            if self.language is Language.SPANISH
            else message
        )

    def reload(self) -> None:
        """Restore current project timing after history, without saving defaults.

        Args:
            None.

        Returns:
            None; a removed owner disables data entry while leaving Redo/Close usable.
        """
        self._loading = True
        try:
            if self.workspace.editing is not self._editing:
                raise ValueError(
                    self.text(
                        "The original project is no longer open.",
                        "El proyecto original ya no está abierto.",
                    )
                )
            if self._read_target is not None:
                self.clock, self._saved = self._read_target()
            else:
                self.clock = shift_clock(
                    self.workspace.read_hierarchy().hierarchy, self.shift_id
                )
                self._saved = next(
                    (
                        t.timing
                        for t in self.workspace.load_shift_timings()
                        if t.shift_id == self.shift_id
                    ),
                    None,
                )
            self._model = (
                separate_work_blocks(self._saved)
                if self._saved
                else equal_timing(
                    self.clock.span_minutes, min(4, self.clock.span_minutes)
                )
            )
            self._owner_missing = False
            self.clear_pending()
            self.error.clear()
            self._project(force=True)
            if self._saved is not None and self._saved != self._model:
                self.show_error(
                    self.text(
                        "Preview: interrupted work is shown as separate blocks. "
                        "Use this timing to accept; opening alone changes nothing.",
                        "Vista previa: el trabajo interrumpido aparece separado. "
                        "Use estos tiempos para aceptar; abrir no modifica datos.",
                    )
                )
        except ValueError as error:
            self._owner_missing = True
            self.show_error(error)
        finally:
            self._loading = False
            for widget in (
                self.body,
                self.timeline,
                self.equal_button,
                self.unequal_button,
                self.equal_break_button,
                self.unequal_break_button,
                self.break_count,
                self.count,
                self.subtract,
                self.snap,
                *self.timeline_tools.values(),
            ):
                widget.setEnabled(not self._owner_missing)
            self.use_button.setEnabled(
                not self._owner_missing and self._saved != self._model
            )
            self.clear_button.setEnabled(
                not self._owner_missing and self._saved is not None
            )
            self.history.refresh()

    def _project(self, *, force: bool = False) -> None:
        """Project accepted timing without replacing ordinary completed-cell widgets.

        Args:
            force: True retires both tables after history/ownership restoration.

        Returns:
            None; signal guards preserve exact edit chronology and keyboard focus.
        """
        previous = self._loading
        self._loading = True
        try:
            self.count.setMaximum(self.clock.span_minutes)
            self.count.setValue(len(self._model.block_minutes))
            self.break_count.setValue(len(self._model.breaks))
            self.equal_button.setChecked(self._model.equal_blocks)
            self.unequal_button.setChecked(not self._model.equal_blocks)
            lengths = tuple(
                b.interval.end - b.interval.start for b in self._model.breaks
            )
            equal_breaks = bool(lengths) and lengths == equal_minutes(
                sum(lengths), len(lengths)
            )
            self.equal_break_button.setChecked(equal_breaks)
            self.unequal_break_button.setChecked(not equal_breaks)
            self.subtract.setChecked(self._model.subtract_breaks)
            self.clock_label.setText(
                self.text("Shift", "Turno")
                + f": {self.clock.label(0)} - "
                + f"{self.clock.label(self.clock.span_minutes)} · "
                + self.text(
                    "(+1) means next day. Breaks are relative to Shift start.",
                    (
                        "(+1) indica el día siguiente. "
                        "Descansos relativos al inicio del "
                        "turno."
                    ),
                )
            )
            if force or len(self.break_rows) != len(self._model.breaks):
                self._break_generation += 1
                self.break_rows.clear()
                self.break_spins.clear()
                self.break_table.setRowCount(0)
                for _ in self._model.breaks:
                    self._append_break()
            for pause_row, ((name, start, end), pause) in enumerate(
                zip(self.break_rows, self._model.breaks, strict=True)
            ):
                name.setText(pause.name or "")
                start.set_value(self.clock.label(pause.interval.start)[:5])
                end.set_value(self.clock.label(pause.interval.end)[:5])
                self.break_spins[pause_row].setValue(
                    pause.interval.end - pause.interval.start
                )
                self.break_spins[pause_row].setProperty(
                    "acceptedDuration", pause.interval.end - pause.interval.start
                )
                self.break_spins[pause_row].setEnabled(True)
            if force or len(self.block_spins) != len(self._model.block_minutes):
                self._block_generation += 1
                self.block_spins.clear()
                self.block_clocks.clear()
                self.block_table.setRowCount(len(self._model.block_minutes))
                for row in range(len(self._model.block_minutes)):
                    spin = QSpinBox()
                    spin.setRange(1, self.clock.span_minutes)
                    spin.setKeyboardTracking(False)
                    spin.valueChanged.connect(
                        partial(self.mark_duration_pending, self._block_generation, row)
                    )
                    spin.editingFinished.connect(
                        partial(self.duration_finished, self._block_generation, row)
                    )
                    self.block_table.setCellWidget(row, 3, spin)
                    self.block_spins.append(spin)
                    start = OptionalTimeEdit(self.text("Not set", "Sin definir"))
                    end = OptionalTimeEdit(self.text("Not set", "Sin definir"))
                    self.block_clocks.append((start, end))
                    for column, edge, control in ((1, "start", start), (2, "end", end)):
                        self.block_table.setCellWidget(row, column, control)
                        control.value_changed.connect(
                            partial(
                                self.mark_block_clock, self._block_generation, row, edge
                            )
                        )
                        control.editingFinished.connect(
                            partial(
                                self.block_clock_finished,
                                self._block_generation,
                                row,
                                edge,
                            )
                        )
                        control.setToolTip(
                            self.text(
                                "24-hour boundary; first start and last end are"
                                " fixed by the shift. Unequal mode edits "
                                "neighboring work budgets.",
                                "Límite de 24 h; inicio y término del turno son"
                                " fijos. El modo distinto ajusta bloques "
                                "vecinos.",
                            )
                        )
                    for column in (0, 4):
                        self.block_table.setItem(row, column, QTableWidgetItem())
                    self.block_table.setRowHeight(row, 40)
            blocks = self._model.blocks()
            for row, block in enumerate(blocks):
                self.block_spins[row].setValue(self._model.block_minutes[row])
                start_clock, end_clock = self.block_clocks[row]
                start_clock.set_value(self.clock.label(block.pieces[0].start)[:5])
                end_clock.set_value(self.clock.label(block.pieces[-1].end)[:5])
                segments = timing_segments(self._model)
                position = segment_position(self._model, "work", row)
                start_clock.setEnabled(position > 0)
                end_clock.setEnabled(position < len(segments) - 1)
                self.block_spins[row].setEnabled(len(segments) > 1)
                self.block_spins[row].setProperty(
                    "acceptedDuration", self._model.block_minutes[row]
                )
                for control in (start_clock, end_clock, self.block_spins[row]):
                    control.setToolTip(
                        self.text(
                            "Resize neighboring segments; Shift endpoints stay fixed.",
                            "Ajustar vecinos; los extremos del turno son fijos.",
                        )
                    )
                pieces = "\n".join(
                    f"{self.clock.label(p.start)}-{self.clock.label(p.end)}"
                    for p in block.pieces
                )
                self.block_table.setRowHeight(row, max(40, 18 * len(block.pieces) + 8))
                for column, text in (
                    (0, str(row + 1)),
                    (4, pieces),
                ):
                    item = self.block_table.item(row, column)
                    assert item is not None
                    item.setText(text)
                    item.setToolTip(text)
            self.timeline.set_timing(self._model, self.clock)
            pause_minutes = self._model.shift_minutes - self._model.productive_minutes
            self.summary.setText(
                self.text(
                    f"{self._model.shift_minutes} min shift · "
                    f"{pause_minutes} min breaks · "
                    f"{self._model.productive_minutes} min work · "
                    f"{self._model.averaging_minutes} min used for averages. "
                    "No work is assigned during breaks.",
                    f"{self._model.shift_minutes} min de turno · "
                    f"{pause_minutes} min de descansos · "
                    f"{self._model.productive_minutes} min de trabajo · "
                    f"{self._model.averaging_minutes} min para promedios. "
                    "No se asigna trabajo durante descansos.",
                )
            )
            self.use_button.setEnabled(self._saved != self._model)
            self.clear_button.setEnabled(self._saved is not None)
            self.remove_break_button.setEnabled(bool(self.break_rows))
            self.remove_block_button.setEnabled(len(self.block_spins) > 1)
        finally:
            self._loading = previous

    def _append_break(self) -> None:
        """Append an initially unspecified break row without inferring a pause.

        Args:
            None.

        Returns:
            None; no project data is created by the empty row.
        """
        row = self.break_table.rowCount()
        self.break_table.setRowCount(row + 1)
        name = QLineEdit()
        start = OptionalTimeEdit(self.text("Not set", "Sin definir"))
        end = OptionalTimeEdit(self.text("Not set", "Sin definir"))
        for column, control in enumerate((name, start, end)):
            self.break_table.setCellWidget(row, column, control)
            control.setToolTip(
                self.text(
                    "Enter both break clocks before accepting this row.",
                    "Ingrese ambas horas para aceptar este descanso.",
                )
            )
            if isinstance(control, OptionalTimeEdit):
                control.value_changed.connect(
                    partial(self.mark_break_pending, self._break_generation)
                )
            else:
                control.textEdited.connect(
                    partial(self.mark_break_pending, self._break_generation)
                )
            control.editingFinished.connect(
                partial(self.break_finished, self._break_generation)
            )
        self.break_table.setRowHeight(row, 40)
        self.break_rows.append((name, start, end))
        spin = QSpinBox()
        spin.setRange(1, self.clock.span_minutes)
        spin.setKeyboardTracking(False)
        spin.setValue(15)
        spin.setEnabled(False)
        spin.setToolTip(
            self.text(
                "Edit break duration after setting its start and end clocks.",
                "Edite la duración después de definir ambas horas.",
            )
        )
        spin.valueChanged.connect(
            partial(self.mark_break_duration, self._break_generation, spin)
        )
        spin.editingFinished.connect(
            partial(self.break_duration_finished, self._break_generation, spin)
        )
        self.break_table.setCellWidget(row, 3, spin)
        self.break_spins.append(spin)
        self.remove_break_button.setEnabled(True)

    def _read_form(self, omit_break: int | None = None) -> RotationTiming:
        """Prepare every pending clock/duration against one complete accepted model.

        Args:
            omit_break: Explicitly deleted pending row, otherwise keep all rows.

        Returns:
            Complete validated timing. Independent valid field edits are retained
            together; no event may silently discard another field's invalid input.

        Raises:
            ValueError: Clocks, overlapping breaks, conflicting boundary intents or
                positive productive coverage are invalid.
        """
        pauses = []
        for row, (name, start, end) in enumerate(self.break_rows):
            if row == omit_break:
                continue
            if (
                not start.clock_text()
                or not end.clock_text()
                or not start.is_acceptable()
                or not end.is_acceptable()
            ):
                raise ValueError(
                    self.text(
                        "Enter both valid break clocks, or remove the unfinished row.",
                        "Ingrese ambas horas válidas o quite la fila incompleta.",
                    )
                )
            first = self.clock.offset(start.clock_text())
            last = self.clock.offset(end.clock_text(), end=True)
            if self.break_spins[row].isEnabled():
                previous_duration = self.break_spins[row].property("acceptedDuration")
                if self.break_spins[row].value() != previous_duration:
                    last = first + self.break_spins[row].value()
            pauses.append(
                TimedBreak(
                    MinuteInterval(first, last),
                    name.text() if name.text().strip() else None,
                )
            )
        values = timing_segments(self._model)
        points = [0]
        for segment in values:
            points.append(points[-1] + segment.minutes)
        intents: dict[int, int] = {}
        durations: list[tuple[int, int]] = []
        forms = [
            ("work", row, start, end, self.block_spins[row])
            for row, (start, end) in enumerate(self.block_clocks)
        ]
        for kind, row, start, end, spin in forms:
            position = segment_position(self._model, kind, row)
            for boundary, field, terminal in (
                (position, start, False),
                (position + 1, end, True),
            ):
                if field.clock_text() == self.clock.label(points[boundary])[:5]:
                    continue
                if not field.is_acceptable() or not field.clock_text():
                    raise ValueError("Enter a complete 24-hour clock as HH:mm.")
                value = self.clock.offset(field.clock_text(), end=terminal)
                if boundary in intents and intents[boundary] != value:
                    raise ValueError(
                        "Match the pending clock and duration for this boundary."
                    )
                intents[boundary] = value
            if spin.value() != values[position].minutes:
                durations.append((position, spin.value()))
        for position, duration in durations:
            boundary = position + 1 if position + 1 < len(points) - 1 else position
            value = (
                intents.get(position, points[position]) + duration
                if boundary == position + 1
                else intents.get(position + 1, points[position + 1]) - duration
            )
            if boundary in intents and intents[boundary] != value:
                raise ValueError(
                    "Match the pending clock and duration for this boundary."
                )
            intents[boundary] = value
        for boundary, value in intents.items():
            if boundary in (0, len(values)) and value != points[boundary]:
                raise ValueError(
                    "Shift endpoints stay fixed; edit the Shift duration separately."
                )
            points[boundary] = value
        rebuilt = tuple(
            TimingSegment(segment.kind, last - first, segment.name)
            for segment, (first, last) in zip(values, pairwise(points), strict=True)
        )
        candidate = from_timing_segments(
            rebuilt,
            subtract_breaks=self.subtract.isChecked(),
            equal_work=self._model.equal_blocks,
        )
        if len(pauses) == len(self._model.breaks):
            updated = tuple(
                pause if pause != old else candidate.breaks[index]
                for index, (pause, old) in enumerate(
                    zip(pauses, self._model.breaks, strict=True)
                )
            )
        else:
            updated = tuple(pauses)
        if updated != candidate.breaks:
            candidate = edit_contiguous_breaks(
                candidate, tuple(sorted(updated, key=lambda p: p.interval.start))
            )
        return candidate

    def _commit(self, candidate: RotationTiming, *, force: bool) -> bool:
        """Accept one validated proposal while guarding original project ownership.

        Args:
            candidate: Complete relative timing, not a partially parsed form.
            force: True explicitly accepts even the initial unmodified preview.

        Returns:
            True after exact acceptance/no-op; False retains the editor on failure.
        """
        candidate = separate_work_blocks(candidate)
        try:
            if self.workspace.editing is not self._editing or self._owner_missing:
                raise ValueError(
                    self.text(
                        "The original Shift is no longer available.",
                        "El turno original ya no está disponible.",
                    )
                )
            if candidate == self._model and self._saved is None and not force:
                self.clear_pending()
                return True
            if self._write_target is not None:
                if not self._write_target(self._saved, candidate):
                    self.clear_pending()
                    self._project(force=True)
                    self.history.refresh()
                    return False
            else:
                self.workspace.replace_shift_timing(
                    self.shift_id, self._saved, candidate
                )
            self._saved = self._model = candidate
            self.clear_pending()
            self.error.clear()
            self._project()
            self.history.refresh()
            return True
        except Exception as error:
            _LOG.exception("Unable to accept Shift timing")
            self.show_error(
                error
                if isinstance(error, ValueError)
                else self.text(
                    "Timing could not be accepted; your input is kept.",
                    "No se aceptaron los tiempos; se conservan sus entradas.",
                )
            )
            return False

    def form_finished(self, _checked: bool = False) -> None:
        """Accept one complete option edit; incomplete rows never write partially.

        Args:
            _checked: Native checkbox argument; values are read from owned controls.

        Returns:
            None; valid accepted edits share the project history.
        """
        if self._loading:
            return
        self._draft_pending = True
        if self._pending_duration is not None:
            self.show_error(
                self.text(
                    "Complete the pending duration first.",
                    "Complete primero la duración pendiente.",
                )
            )
            return
        self._accept_form(force=True)

    def _accept_form(self, *, force: bool = False) -> bool:
        """Validate pending form intent before atomic project acceptance.

        Args:
            force: Explicitly accept the unchanged initial preview when True.

        Returns:
            True for valid acceptance; False leaves all pending cells available.
        """
        if self._pending_block_clock is not None:
            return self.accept_block_clock(*self._pending_block_clock)
        if self._pending_break_duration is not None:
            return self.accept_break_duration(self._pending_break_duration)
        if self._pending_duration is not None:
            return self.accept_duration(self._pending_duration)
        try:
            return self._commit(self._read_form(), force=force)
        except ValueError as error:
            self.show_error(error)
            self.history.refresh()
            return False

    def mark_break_pending(self, generation: int, _text: str = "") -> None:
        """Advertise real clock/name typing without accepting an unfinished cell.

        Args:
            generation: Exact current break-table generation.
            _text: Optional native text-edit token; source is read only at completion.

        Returns:
            None; toolbar replay can now prepare the focused input coherently.
        """
        if not self._loading and generation == self._break_generation:
            self._draft_pending = True
            self.history.refresh()

    def mark_duration_pending(self, generation: int, row: int, _value: int) -> None:
        """Retain a work-duration draft until its neighboring segments validate.

        Args:
            generation: Exact current block-table generation.
            row: Source duration currently edited.
            _value: Native integer token; authoritative validation occurs at completion.

        Returns:
            None; invalid durations cannot be swept away by Close or shared replay.
        """
        if not self._loading and generation == self._block_generation:
            self._pending_duration = row
            self._draft_pending = True
            self.history.refresh()

    def break_finished(self, generation: int) -> None:
        """Ignore retired break focus events and accept current complete rows.

        Args:
            generation: Exact table generation captured when this control was created.

        Returns:
            None; obsolete callbacks never read or edit replacement rows.
        """
        if generation == self._break_generation:
            self.form_finished()

    def add_break(self) -> None:
        """Create a valid short pause in selected work as one reversible edit.

        Args:
            None.

        Returns:
            None; a proposed fifteen-minute pause is shortened for small blocks.
            Its clocks/name remain editable; no unfinished blank row traps Undo.
        """
        if not self.prepare():
            return
        row = self.block_table.currentRow()
        blocks = self._model.blocks()
        chosen = (
            blocks[row].pieces[0]
            if 0 <= row < len(blocks)
            else max(
                (p for b in blocks for p in b.pieces), key=lambda p: p.end - p.start
            )
        )
        length = min(15, chosen.end - chosen.start - 2)
        if length < 1:
            self.show_error(
                self.text(
                    "Choose a work block with at least three minutes.",
                    "Elija un bloque de al menos tres minutos.",
                )
            )
            return
        start = chosen.start + (chosen.end - chosen.start - length) // 2
        self.gesture_finished(
            change_timing_break(
                self._model, None, TimedBreak(MinuteInterval(start, start + length))
            )
        )

    def remove_break(self) -> None:
        """Remove the selected pending/saved break and prepare complete remaining work.

        Args:
            None.

        Returns:
            None; a successful timing replacement is reversible in shared history.
        """
        row = self.break_table.currentRow()
        if row < 0:
            row = len(self.break_rows) - 1
        if row < 0:
            return
        if self._draft_pending:
            try:
                self._commit(self._read_form(omit_break=row), force=True)
            except ValueError as error:
                self.show_error(error)
            return
        if self._model.breaks:
            self.gesture_finished(remove_timing_segment(self._model, "break", row))

    def duration_finished(self, generation: int, row: int) -> None:
        """Commit one completed duration from this exact live block projection.

        Args:
            generation: Table generation captured by the source editor.
            row: Edited duration; last-block edits move its preceding boundary.

        Returns:
            None; failed input remains pending and does not partially write.
        """
        if not self._loading and generation == self._block_generation:
            self._pending_duration = row
            self._draft_pending = True
            self.accept_duration(row)

    def accept_duration(self, row: int) -> bool:
        """Accept a completed duration through the common full-form validator.

        Args:
            row: Current live block row, retained by its generation-checked callback.

        Returns:
            True for complete acceptance; False preserves all invalid pending fields.
        """
        if not 0 <= row < len(self.block_spins):
            return False
        try:
            return self._commit(self._read_form(), force=True)
        except ValueError as error:
            self.show_error(error)
            return False

    def gesture_finished(self, value: object) -> None:
        """Accept one timeline gesture as one shared history action.

        Args:
            value: Complete RotationTiming emitted after release/keyboard nudge.

        Returns:
            None; rejected gestures restore the last accepted timeline.
        """
        if isinstance(value, RotationTiming) and not self._draft_pending:
            if (
                len(value.block_minutes) < len(self._model.block_minutes)
                and value.productive_minutes < self._model.productive_minutes
            ):
                difference = self._model.productive_minutes - value.productive_minutes
                question = self.text(
                    f"Removing this work extends neighboring breaks by {difference} "
                    f"minutes. Continue? Undo restores the layout.",
                    f"Quitar este trabajo amplía descansos vecinos en {difference} "
                    f"minutos. ¿Continuar? Deshacer restaura el diseño.",
                )
                if (
                    QMessageBox.question(
                        self,
                        self.text("Extend neighbors", "Extender vecinos"),
                        question,
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No,
                    )
                    != QMessageBox.Yes
                ):
                    self.timeline.set_timing(self._model, self.clock)
                    return
            if not self._commit(value, force=True):
                self.timeline.set_timing(self._model, self.clock)
        else:
            self.timeline.set_timing(self._model, self.clock)
            self.show_error(
                self.text(
                    "Complete the pending table input first.",
                    "Complete primero las entradas pendientes.",
                )
            )

    def count_changed(self, count: int) -> None:
        """Confirm explicit equal redistribution after a bulk block-count edit.

        Args:
            count: Requested positive number of work blocks.

        Returns:
            None; rejected redistribution restores the accepted count and clocks.
        """
        if self._loading:
            return
        with QSignalBlocker(self.count):
            self.count.setValue(len(self._model.block_minutes))
        if self.prepare():
            if self._model.equal_blocks and not self._model.breaks:
                self._commit(
                    redistribute_timing_segments(
                        self._model,
                        work_count=count,
                        break_count=0,
                        equal_work=True,
                        equal_breaks=False,
                    ),
                    force=True,
                )
            else:
                self.redistribute(count)

    def redistribute(self, count: int) -> None:
        """Review coordinated equal work redistribution without deleting pauses.

        Args:
            count: Explicit requested number of positive work blocks.

        Returns:
            None; rejection retains accepted clocks and counts.
        """
        self.redistribute_review(
            count, len(self._model.breaks), True, self.equal_break_button.isChecked()
        )

    def redistribute_review(
        self, work_count: int, break_count: int, equal_work: bool, equal_breaks: bool
    ) -> None:
        """Prepare and confirm coupled count/equality edits as one shared action.

        Args:
            work_count: Positive work count.
            break_count: Nonnegative break count.
            equal_work: Equalize total productive time.
            equal_breaks: Equalize total pause time, preserving names where retained.

        Returns:
            None; invalid budgets or declined review preserve the accepted model.
        """
        total = self._model.shift_minutes - self._model.productive_minutes
        if break_count and total < break_count:
            total, accepted = QInputDialog.getInt(
                self,
                self.text("Total break time", "Tiempo total de descanso"),
                self.text(
                    "Total minutes for all breaks",
                    "Minutos totales para todos los descansos",
                ),
                max(15, break_count),
                break_count,
                self._model.shift_minutes - 1,
            )
            if not accepted:
                self._project()
                return
        try:
            proposal = redistribute_timing_segments(
                self._model,
                work_count=work_count,
                break_count=break_count,
                equal_work=equal_work,
                equal_breaks=equal_breaks,
                break_minutes=total,
            )
        except ValueError as error:
            self._project()
            self.show_error(error)
            return
        message = self.text(
            "Redistribute these segments and adjust their clock positions? "
            "Equal breaks share the existing total break time; work and "
            "breaks keep the full Shift covered. Undo restores the previous layout.",
            "¿Redistribuir los tramos y ajustar sus horas? "
            "Los descansos iguales reparten "
            "el tiempo total existente. Trabajo y descansos cubren todo el "
            "turno. Deshacer restaura el diseño.",
        )
        if break_count < len(self._model.breaks):
            removed = [
                p.name or str(i + 1)
                for i, p in enumerate(self._model.breaks)
                if i >= break_count
            ]
            message += self.text(
                " Removed break names: ", " Nombres de descanso eliminados: "
            ) + ", ".join(removed)
        if break_count > max(0, work_count - 1):
            message += self.text(
                " Some breaks will be adjacent; no work blocks are added "
                "automatically.",
                " Algunos descansos quedarán juntos; no se añaden bloques "
                "automáticamente.",
            )
        if (
            QMessageBox.question(
                self,
                self.text("Redistribute timing", "Redistribuir tiempos"),
                message,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            == QMessageBox.Yes
        ):
            self._commit(proposal, force=True)
        else:
            self._project()

    def break_count_changed(self, count: int) -> None:
        """Review a pause-count change while retaining the existing pause budget.

        Args:
            count: Requested zero or positive break count.

        Returns:
            None; no direct spin edit can silently remove names or change budgets.
        """
        if self._loading:
            return
        with QSignalBlocker(self.break_count):
            self.break_count.setValue(len(self._model.breaks))
        if self.prepare():
            self.redistribute_review(
                len(self._model.block_minutes), count, self._model.equal_blocks, True
            )

    def mode_equal_breaks(self) -> None:
        """Review equal pause durations while preserving total pause time and work mode.

        Args:
            None.

        Returns:
            None; clocks may move only after confirmation.
        """
        if self.prepare() and self._model.breaks:
            self.redistribute_review(
                len(self._model.block_minutes),
                len(self._model.breaks),
                self._model.equal_blocks,
                True,
            )
        else:
            self._project()

    def mode_unequal_breaks(self) -> None:
        """Allow direct custom pause editing without changing accepted durations.

        Args:
            None.

        Returns:
            None; equality is re-evaluated from data after each accepted edit.
        """
        self.equal_break_button.setChecked(False)
        self.unequal_break_button.setChecked(True)

    def mode_equal(self) -> None:
        """Confirm canonical equal work and duration-preserving break relocation.

        Args:
            None.

        Returns:
            None; the accepted layout stays unchanged if confirmation is declined.
        """
        with QSignalBlocker(self.equal_button), QSignalBlocker(self.unequal_button):
            self.equal_button.setChecked(self._model.equal_blocks)
            self.unequal_button.setChecked(not self._model.equal_blocks)
        if self.prepare() and not self._model.equal_blocks:
            self.redistribute(len(self._model.block_minutes))

    def mode_unequal(self) -> None:
        """Permit manual work boundaries without redistributing any current time.

        Args:
            None.

        Returns:
            None; only the explicit mode changes through existing shared history.
        """
        with QSignalBlocker(self.equal_button), QSignalBlocker(self.unequal_button):
            self.equal_button.setChecked(self._model.equal_blocks)
            self.unequal_button.setChecked(not self._model.equal_blocks)
        if self.prepare():
            self._commit(replace(self._model, equal_blocks=False), force=True)

    def snap_changed(self, minutes: int) -> None:
        """Change pointer/keyboard snapping as session-only view state.

        Args:
            minutes: Positive whole-minute gesture increment.

        Returns:
            None; no template/history/preference write occurs.
        """
        self.timeline.snap_minutes = minutes

    def use_timing(self) -> None:
        """Explicitly retain the initial valid preview without requiring a fake edit.

        Args:
            None.

        Returns:
            None; one accepted creation enables Clear and shared Undo.
        """
        self._accept_form(force=True)

    def clear_template(self) -> None:
        """Explicitly remove this reusable template after No-default confirmation.

        Args:
            None.

        Returns:
            None; existing rotations remain unchanged and shared Undo restores timing.
        """
        if self._saved is None or not self.prepare():
            return
        if (
            QMessageBox.question(
                self,
                self.text("Clear timing template", "Quitar plantilla"),
                self.text(
                    (
                        "Clear this rotation's copied timing? Undo restores it."
                        if self._write_target is not None
                        else "Remove this Shift timing template? "
                        "Existing rotations stay unchanged; Undo "
                        "restores the template."
                    ),
                    (
                        "¿Quitar los tiempos copiados de esta rotación? Deshacer "
                        "los restaura."
                        if self._write_target is not None
                        else "¿Quitar la plantilla del turno? Las "
                        "rotaciones existentes no cambian; "
                        "Deshacer restaura la plantilla."
                    ),
                ),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            != QMessageBox.Yes
        ):
            return
        try:
            if self._write_target is not None:
                if not self._write_target(self._saved, None):
                    return
            else:
                self.workspace.replace_shift_timing(self.shift_id, self._saved, None)
            self.reload()
        except Exception:
            _LOG.exception("Unable to clear Shift timing")
            self.show_error(
                self.text(
                    "The template could not be cleared.",
                    "No se pudo quitar la plantilla.",
                )
            )

    def pending_action(self) -> str | None:
        """Advertise unaccepted input to the shared history controls without writing.

        Args:
            None.

        Returns:
            Stable edit label only while real pending input exists.
        """
        return (
            (
                "replace_rotation_scenario"
                if self._write_target is not None
                else "replace_shift_timing"
            )
            if self._draft_pending
            else None
        )

    def prepare(self) -> bool:
        """Commit pending fields before replay/close, never an open preview.

        Args:
            None.

        Returns:
            True if replay/close may proceed; False retains invalid unfinished input.
        """
        if self._owner_missing:
            return True
        self.count.interpretText()
        self.break_count.interpretText()
        for row, spin in enumerate(self.break_spins):
            if spin.isEnabled():
                spin.interpretText()
                if spin.value() != spin.property("acceptedDuration"):
                    self._pending_break_duration = row
                    self._draft_pending = True
                    break
        for row, spin in enumerate(self.block_spins):
            spin.interpretText()
            if spin.value() != self._model.block_minutes[row]:
                self._pending_duration = row
                self._draft_pending = True
                break
        if self._pending_block_clock is not None:
            return self.accept_block_clock(*self._pending_block_clock)
        if self._pending_break_duration is not None:
            return self.accept_break_duration(self._pending_break_duration)
        if self._pending_duration is not None:
            return self.accept_duration(self._pending_duration)
        if not self._draft_pending:
            return True
        return self._accept_form()

    def accept(self) -> None:
        """Close after accepting valid pending cells; Main Save remains authoritative.

        Args:
            None.

        Returns:
            None; invalid input keeps the editor open with correction guidance.
        """
        if self.prepare():
            super().accept()

    def reject(self) -> None:
        """Allow cancelling only unaccepted input without discarding project edits.

        Args:
            None.

        Returns:
            None; accepted history is retained, and No preserves unfinished input.
        """
        if (
            self.prepare()
            or QMessageBox.question(
                self,
                self.text("Unfinished timing input", "Entrada de tiempos incompleta"),
                self.text(
                    (
                        "Discard only the unaccepted input and "
                        "close? Accepted edits remain in the "
                        "project."
                    ),
                    (
                        "¿Descartar solo las entradas no "
                        "aceptadas y cerrar? Los cambios "
                        "aceptados permanecen en el proyecto."
                    ),
                ),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            == QMessageBox.Yes
        ):
            super().reject()

    def tool_description(self, tool: str) -> str:
        """Explain the selected visual operation and its non-destructive work semantics.

        Args:
            tool: Supported persistent timeline tool.

        Returns:
            Localized action instructions; manual fields use the same validation.
        """
        descriptions = {
            "select": (
                "Select a segment; drag a work boundary. Escape"
                " returns to this cursor. Navy: work; grey: "
                "breaks.",
                "Seleccione un tramo o arrastre un límite. "
                "Escape vuelve a este cursor. Azul: trabajo; "
                "gris: descansos.",
            ),
            "split": (
                "Click inside work to split that block at the snapped time.",
                "Haga clic dentro del trabajo para dividir el bloque en esa hora.",
            ),
            "draw_break": (
                "Drag across work to draw a break; click to add"
                " 15 minutes. Blocks cover the remaining work.",
                "Arrastre sobre trabajo para crear un descanso;"
                " un clic añade 15 minutos. Los bloques cubren "
                "el trabajo restante.",
            ),
            "move": (
                "Drag work or a break to move it; cross another segment to reorder. "
                "Drag any interior boundary to resize its neighbors.",
                "Arrastre trabajo o descanso para mover o reordenar. "
                "Arrastre límites interiores para ajustar los vecinos.",
            ),
            "join": (
                "Click a work boundary to join neighbors, or a "
                "break to join a touching break.",
                "Haga clic en un límite para unir bloques, o en"
                " un descanso para unir otro contiguo.",
            ),
            "remove": (
                "Remove a segment; its immediate neighbors expand to cover the time. "
                "Delete also removes the selection.",
                "Quite un tramo y extienda sus vecinos para cubrir su tiempo. "
                "Supr también quita la selección.",
            ),
        }
        return self.text(*descriptions[tool])

    def choose_tool(self, tool: str) -> None:
        """Change only the timeline cursor/mode, leaving pending table inputs intact.

        Args:
            tool: Explicit toolbar action.

        Returns:
            None; switching modes is not a saved timing edit.
        """
        self.timeline.set_tool(tool)

    def sync_tool(self, tool: str) -> None:
        """Synchronize checked buttons and contextual guidance after Escape or clicks.

        Args:
            tool: Current timeline tool.

        Returns:
            None; window-only tool state is never persisted.
        """
        for key, button in self.timeline_tools.items():
            button.setChecked(key == tool)
            button.setToolTip(self.tool_description(key))
        self.tool_hint.setText(self.tool_description(tool))

    def select_timeline_segment(self, kind: str, row: int) -> None:
        """Select the corresponding manual row without moving keyboard focus.

        Args:
            kind: block or break.
            row: Chronological zero-based accepted segment.

        Returns:
            None; selection is visual and creates no history command.
        """
        if not self._loading:
            table = self.block_table if kind == "block" else self.break_table
            with QSignalBlocker(table):
                table.setCurrentCell(row, 0)

    def select_table_segment(self, kind: str, row: int) -> None:
        """Reflect a valid table selection in the shared timeline highlight.

        Args:
            kind: block or break.
            row: Native current row; unaccepted break rows remain unselected.

        Returns:
            None; current accepted timing is unchanged.
        """
        count = len(
            self._model.block_minutes if kind == "block" else self._model.breaks
        )
        if not self._loading and 0 <= row < count:
            self.timeline.select_segment(kind, row)

    def add_block(self) -> None:
        """Split the selected work budget in half without redistributing other blocks.

        Args:
            None.

        Returns:
            None; one valid proposal uses the normal shared timing/history port.
        """
        if not self.prepare():
            return
        row = max(0, self.block_table.currentRow())
        block = self._model.blocks()[row]
        remaining = self._model.block_minutes[row] // 2
        if remaining < 1:
            self.show_error(
                self.text(
                    "A one-minute block cannot be split.",
                    "No se puede dividir un bloque de un minuto.",
                )
            )
            return
        for piece in block.pieces:
            length = piece.end - piece.start
            if remaining < length:
                self.gesture_finished(
                    split_work_block(self._model, piece.start + remaining)
                )
                return
            remaining -= length
            if remaining == 0:
                self.gesture_finished(split_work_block(self._model, piece.end))
                return

    def remove_block(self) -> None:
        """Remove a selected block and extend its immediate neighboring segments.

        Args:
            None.

        Returns:
            None; any scenario lost-cell confirmation remains owned by its host.
        """
        if not self.prepare():
            return
        row = self.block_table.currentRow()
        try:
            self.gesture_finished(
                remove_work_block(
                    self._model, row if row >= 0 else len(self._model.block_minutes) - 1
                )
            )
        except ValueError as error:
            self.show_error(error)

    def mark_block_clock(self, generation: int, row: int, edge: str) -> None:
        """Track a live start/end clock independently of unaccepted durations.

        Args:
            generation: Exact table projection generation.
            row: Current block index.
            edge: start or end.

        Returns:
            None; partial native clock input cannot be lost on replay/close.
        """
        if not self._loading and generation == self._block_generation:
            self._pending_block_clock = row, edge
            self._draft_pending = True
            self.history.refresh()

    def block_clock_finished(self, generation: int, row: int, edge: str) -> None:
        """Accept a complete native clock only from this current table projection.

        Args:
            generation: Captured source projection generation.
            row: Current block index.
            edge: start or end.

        Returns:
            None; obsolete focus callbacks cannot edit a replacement block.
        """
        if not self._loading and generation == self._block_generation:
            self.accept_block_clock(row, edge)

    def accept_block_clock(self, row: int, edge: str) -> bool:
        """Accept a native clock without dropping pending changes in other fields.

        Args:
            row: Current live work-block row.
            edge: start or end; first start and last end remain fixed.

        Returns:
            True on one complete acceptance; False keeps the correction form intact.
        """
        boundary = row if edge == "start" else row + 1
        if edge not in ("start", "end") or not 0 < boundary < len(
            self._model.block_minutes
        ):
            return False
        try:
            return self._commit(self._read_form(), force=True)
        except ValueError as error:
            self.show_error(error)
            return False

    def mark_break_duration(
        self, generation: int, control: QSpinBox, _value: int
    ) -> None:
        """Track a live break duration by control identity after row removals.

        Args:
            generation: Current break projection generation.
            control: Exact owned duration editor, not a potentially shifted row index.
            _value: Native token; validation reads the current complete form.

        Returns:
            None; pending values stay local until completion.
        """
        if (
            not self._loading
            and generation == self._break_generation
            and control in self.break_spins
        ):
            self._pending_break_duration = self.break_spins.index(control)
            self._draft_pending = True
            self.history.refresh()

    def break_duration_finished(self, generation: int, control: QSpinBox) -> None:
        """Complete the current break duration through the same clock/model pathway.

        Args:
            generation: Exact current table generation.
            control: Exact still-owned duration editor.

        Returns:
            None; retired cells never acquire another break's identity.
        """
        if (
            not self._loading
            and generation == self._break_generation
            and control in self.break_spins
        ):
            self.accept_break_duration(self.break_spins.index(control))

    def accept_break_duration(self, row: int) -> bool:
        """Accept a break's duration through the same whole-form clock model.

        Args:
            row: Current chronological break row.

        Returns:
            True on exact complete acceptance; False retains every pending correction.
        """
        if not 0 <= row < len(self.break_spins):
            return False
        try:
            return self._commit(self._read_form(), force=True)
        except ValueError as error:
            self.show_error(error)
            return False

    def clear_pending(self) -> None:
        """Retire every field-intent flag after accepted projection or explicit cancel.

        Args:
            None.

        Returns:
            None; invalid unaccepted input retains flags until corrected or discarded.
        """
        self._draft_pending = False
        self._pending_duration = None
        self._pending_block_clock = None
        self._pending_break_duration = None

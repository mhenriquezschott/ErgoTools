"""Original ST eight-column controls, separated from SQL and scientific models.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Callable, Mapping
from functools import partial
from itertools import pairwise

from PyQt5.QtCore import QEvent, QObject, QSize, Qt, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.settings import Language
from ergotools.domain.assessments.tst import TstDirection
from ergotools.domain.assessments.tst_summary import TstSummary
from ergotools.domain.assessments.validation import DraftError, InputIssue
from ergotools.domain.display_precision import DisplayPrecision
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.historical_result_display import (
    historical_damage_color,
    historical_number,
    show_historical_rows,
)
from ergotools.presentation.desktop.precision_editor import PrecisionLineEdit
from ergotools.presentation.desktop.theme.main_workspace import MAIN_WORKSPACE_STYLE
from ergotools.presentation.desktop.theme.tst_summary import display_tst_summary
from ergotools.presentation.desktop.tool_result_summary import ToolResultSummary
from ergotools.presentation.desktop.tst_presenter import TstPresenter
from ergotools.presentation.edit_context import EditContext

# Original task-column ordering with English/Spanish captions; units are supplied
# separately.
_HEADERS = (
    ("Task #", "Tarea #"),
    ("Type of Task", "Tipo de tarea"),
    ("Lever Arm", "Brazo de Palanca"),
    ("Load", "Carga"),
    ("Moment", "Momento"),
    ("Repetitions (per work day)", "Repeticiones (por jornada laboral)"),
    ("Damage (cumulative)", "Daño (acumulado)"),
    ("% Total (damage)", "% Total (daño)"),
)
# Original ST selector order and typed item identities; formula mapping stays in the
# application/domain boundary.
_DIRECTIONS = (
    (TstDirection.HANDLING_LOADS, "Handling Loads", "Manipulación de cargas"),
    (TstDirection.DOWNWARD, "Push or Pull Downward", "Empujar o Tirar hacia abajo"),
    (
        TstDirection.HORIZONTAL,
        "Horizontal Push or Pull",
        "Empuje o Tirón Horizontal",
    ),
)


class TstTaskPanel(QWidget):
    """Own ST widgets and pending input; the presenter owns source and history."""

    def __init__(
        self,
        presenter: TstPresenter,
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
        self.context: EditContext | None = None
        self.pending = False
        self.inputs: list[
            tuple[QComboBox, PrecisionLineEdit, PrecisionLineEdit, PrecisionLineEdit]
        ] = []
        self.outputs: list[tuple[QLabel, QLabel, QLabel]] = []
        self.task_ids: tuple[str, ...] = ()
        self._sync_scheduled = False
        self.setStyleSheet(MAIN_WORKSPACE_STYLE)
        layout = QVBoxLayout(self)
        self.header_widget = QWidget()
        self.header_grid = QGridLayout(self.header_widget)
        self.headers = tuple(QLabel() for _ in range(8))
        font = self.font()
        font.setBold(True)
        for column, label in enumerate(self.headers):
            label.setFont(font)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setWordWrap(True)
            label.setFixedHeight(42)
            self.header_grid.addWidget(label, 0, column)
        self.header = QScrollArea()
        self.header.setObjectName("stickyHeaderScroll")
        self.header_widget.setObjectName("stickyHeader")
        self.header.setFrameShape(QFrame.NoFrame)
        self.header.setWidgetResizable(False)
        self.header.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.header.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.header.setFixedHeight(42)
        self.header.setWidget(self.header_widget)
        layout.addWidget(self.header)
        self.body_scroll = QScrollArea()
        self.body_scroll.setWidgetResizable(True)
        self.body_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.frame = QFrame()
        self.frame.setMinimumWidth(0)
        self.frame.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        self.grid = QGridLayout()
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.grid.setContentsMargins(6, 0, 6, 0)
        for column, (stretch, width) in enumerate(
            zip(
                (0, 3, 2, 1, 0, 3, 2, 0),
                (55, 190, 95, 58, 80, 145, 115, 85),
                strict=True,
            )
        ):
            self.grid.setColumnStretch(column, stretch)
            self.grid.setColumnMinimumWidth(column, width)
        frame_layout.addLayout(self.grid)
        frame_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)
        self.body_scroll.setWidget(self.frame)
        # The content can resize after its viewport during row rebuild/translation.
        self.frame.installEventFilter(self)
        bar = self.body_scroll.horizontalScrollBar()
        header_bar = self.header.horizontalScrollBar()
        assert bar is not None and header_bar is not None
        bar.valueChanged.connect(header_bar.setValue)
        viewport = self.body_scroll.viewport()
        assert viewport is not None
        viewport.installEventFilter(self)
        layout.addWidget(self.body_scroll, 1)
        self.summary = ToolResultSummary()
        layout.addLayout(self.summary)
        buttons = QHBoxLayout()
        self.clear_button = QPushButton()
        self.clear_button.setObjectName("clearAssessmentButton")
        self.clear_button.setIcon(icons["delete"])
        self.clear_button.setIconSize(QSize(26, 26))
        self.clear_button.clicked.connect(clear or self.clear_inputs)
        self.context_button = QPushButton()
        self.context_button.setIcon(icons["body_view"])
        self.context_button.setFixedSize(40, 40)
        self.context_button.setIconSize(QSize(30, 30))
        self.context_button.setEnabled(False)
        self.calculate_button = QPushButton()
        self.calculate_button.setObjectName("calculateButton")
        self.calculate_button.setIcon(icons["calculate_light"])
        self.calculate_button.setIconSize(QSize(28, 28))
        self.calculate_button.clicked.connect(self.calculate)
        for button in (
            self.clear_button,
            self.context_button,
            self.calculate_button,
        ):
            button.setMinimumHeight(40)
            if button in (self.clear_button, self.calculate_button):
                button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            # Equal action widths keep the fixed-size chooser centered.
            buttons.addWidget(
                button, 1 if button in (self.clear_button, self.calculate_button) else 0
            )
        layout.addLayout(buttons)
        self.translate()

    def translate(self) -> None:
        """Translate captions and rating descriptions without altering pending input.

        Args:
            None.

        Returns:
            None.
        """
        language = int(self.language is Language.SPANISH)
        system = self.context.view.system if self.context else self.presenter.system
        units = (
            ("in", "lb", "ft.lb")
            if system is MeasurementSystem.IMPERIAL
            else ("cm", "N", "N.m")
        )
        # Inputs may be projected; calculated/recorded moments stay in source units.
        source = self.presenter.source()
        result_system = source.system if source is not None else system
        moment_unit = "ft.lb" if result_system is MeasurementSystem.IMPERIAL else "N.m"
        for column, (label, texts) in enumerate(
            zip(self.headers, _HEADERS, strict=True)
        ):
            text = texts[language]
            if column in (2, 3, 4):
                text += f" ({moment_unit if column == 4 else units[column - 2]})"
            label.setText(text)
            label.setToolTip(text)
        for combo, arm, load, repetitions in self.inputs:
            combo.blockSignals(True)
            for index, direction in enumerate(_DIRECTIONS):
                combo.setItemText(index, direction[1 + language])
            combo.blockSignals(False)
            combo.setToolTip(_HEADERS[1][language])
            for editor, column in ((arm, 2), (load, 3), (repetitions, 5)):
                editor.setToolTip(self.headers[column].text())
        self.clear_button.setText(("Clear assessment", "Limpiar evaluación")[language])
        self.calculate_button.setText(("Calculate", "Calcular")[language])
        self.clear_button.setToolTip(
            (
                "Clear ST inputs and calculated results.",
                "Borre los datos y resultados ST.",
            )[language]
        )
        self.calculate_button.setToolTip(
            (
                "Validate ST inputs; calculation remains subject to scientific review.",
                "Valide las entradas ST; el cálculo requiere revisión científica.",
            )[language]
        )
        self.context_button.setToolTip(
            (
                "Open the task-data grid view for the active tool.",
                "Abra la cuadrícula de tareas de la herramienta activa.",
            )[language]
        )
        self._schedule_sync()

    def load_source(self, context: EditContext | None) -> None:
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
        # Retiring focused controls otherwise advance focus through the replacement
        # rows and make QScrollArea reveal the final task during Undo/Redo.
        focus = QApplication.focusWidget()
        if focus is not None and self.frame.isAncestorOf(focus):
            focus.clearFocus()
        self.context = context
        self.pending = False
        self.inputs.clear()
        self.outputs.clear()
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item is not None and item.widget() is not None:
                widget = item.widget()
                assert widget is not None
                widget.hide()
                widget.deleteLater()
        for column in range(8):
            hidden_header = QLabel()
            hidden_header.setFixedHeight(0)
            hidden_header.setMinimumWidth(0)
            hidden_header.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self.grid.addWidget(hidden_header, 0, column)
            hidden_header.installEventFilter(self)
        tasks = context.view.tasks if context is not None else ()
        self.task_ids = tuple(t.task_id for t in tasks)
        for row, task in enumerate(tasks, 1):
            label = QLabel(str(row))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(label, row, 0)
            combo = QComboBox()
            combo.setItemDelegate(QStyledItemDelegate(combo))
            view = combo.view()
            assert view is not None
            view.setStyleSheet(
                "QAbstractItemView { background: white; color: #1B2933; outline: 0; }"
                "QAbstractItemView::item { min-height: 28px; padding: 2px 7px; }"
                "QAbstractItemView::item:selected, QAbstractItemView::item:hover "
                "{ background: #087E91; color: white; }"
            )
            combo.setMinimumWidth(0)
            combo.setMaximumWidth(220)
            combo.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            # Keep visible choices; the draft owns its explicit calculator convention.
            for direction, title, _ in _DIRECTIONS:
                combo.addItem(title, direction.value)
            combo.setCurrentIndex(
                combo.findData(task.direction.value) if task.direction else -1
            )
            combo.currentIndexChanged.connect(
                partial(self._selector_changed, task.task_id)
            )
            self.grid.addWidget(combo, row, 1)
            precision = (
                self.presenter.workspace.project_metadata.precision
                if self.presenter.workspace.project_metadata
                else DisplayPrecision()
            )
            assert context is not None
            editors = (
                PrecisionLineEdit(task.lever_arm, context.convention, precision.inputs),
                PrecisionLineEdit(task.load, context.convention, precision.inputs),
                PrecisionLineEdit(task.repetitions, context.convention, 0),
            )
            assert context is not None
            for column, _field, editor in zip(
                (2, 3, 5), ("lever_arm", "load", "repetitions"), editors, strict=True
            ):
                editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
                # Compact text keeps exact unchanged values in PrecisionLineEdit.
                editor.setCursorPosition(0)
                editor.textEdited.connect(self._mark_pending)
                editor.editingFinished.connect(
                    partial(self.commit_cell, task.task_id, editors.index(editor) + 2)
                )
                self.grid.addWidget(editor, row, column)
            self.inputs.append((combo, *editors))
            outputs = (QLabel("0.0"), QLabel("0.0"), QLabel("0.0"))
            for column, output in zip((4, 6, 7), outputs, strict=True):
                output.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.grid.addWidget(output, row, column)
            self.outputs.append(outputs)
            if row == 1:
                for widget in (label, combo, *editors, *outputs):
                    widget.installEventFilter(self)
        # Original setupTSTTab creates all direction selectors before the numeric
        # editors. Preserve that keyboard workflow independently of row creation.
        tab_order: list[QWidget] = [row[0] for row in self.inputs]
        tab_order.extend(editor for row in self.inputs for editor in row[1:])
        for previous, following in pairwise(tab_order):
            QWidget.setTabOrder(previous, following)
        self.setEnabled(context is not None)
        self.translate()
        self.show_result()

    def _selector_changed(self, task_id: str, index: int) -> None:
        """Accept one rating/direction choice as its own chronological edit.

        Args:
            task_id: Stable identity captured when this selector was constructed.
            index: Qt selection index; the typed value is read through input_rows.

        Returns:
            None; unrelated unfinished numeric text stays visible and unaccepted.
        """
        self._mark_pending()
        self.commit_cell(task_id, 1)

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

    def input_rows(self) -> tuple[tuple[str, TstDirection | None, str, str, str], ...]:
        """Read widget values once without accepting edits or changing history.

        Args:
            None.

        Returns:
            Stable task identities and current displayed values in task order.
        """
        return tuple(
            (
                identity,
                self._direction(combo),
                arm.source_text(),
                load.source_text(),
                repetitions.source_text(),
            )
            for identity, (combo, arm, load, repetitions) in zip(
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
            rebuilding widgets or saving/calculating. Other unfinished cells remain
            local. Invalid/stale completion is retained for correction; projection
            loads disable completion before retiring focused controls.

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

    @staticmethod
    def _direction(combo: QComboBox) -> TstDirection | None:
        """Read the direction selector's typed item data.

        Read the direction selector's typed item data; absence stays incomplete rather
        than becoming a default direction.

        Args:
            combo: Direction selector whose opaque item data determines the stored ST
                direction.

        Returns:
            Typed original ST direction stored in combo item data, or None when the
            selector is incomplete.
        """
        value = combo.currentData()
        return TstDirection(value) if isinstance(value, str) else None

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
            result = self.presenter.calculate()
            if result is not None and result.issues:
                self._report_issue(result.issues[0])
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
        """Replace outputs from exact current results; clear missing/stale styling.

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
            "Probabilidad de Trastorno del Hombro (%):"
            if self.language is Language.SPANISH
            else "Probability of Shoulder Outcome (%):"
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
        if not isinstance(result.summary, TstSummary):
            return
        display = display_tst_summary(result.summary, precision)
        self.summary.show_values(
            display.damage_text, display.probability_text, display.color
        )
        for outputs, moment, damage, share, color in zip(
            self.outputs,
            display.task_moment_texts,
            display.task_damage_texts,
            display.contribution_texts,
            display.task_colors,
            strict=True,
        ):
            for label, value in zip(outputs, (moment, damage, share), strict=True):
                label.setText(value)
            if color is not None:
                outputs[1].setStyleSheet("background-color: " + color)

    def _schedule_sync(self) -> None:
        """Queue one sticky-header geometry synchronization.

        Queue one sticky-header geometry synchronization after the current Qt layout
        pass.

        Args:
            None.

        Returns:
            None.
        """
        if not self._sync_scheduled:
            self._sync_scheduled = True
            QTimer.singleShot(0, self._sync_header)

    def _sync_header(self) -> None:
        """Align fixed header labels to actual task-column widths.

        Align fixed header labels to actual task-column widths and scrollbar geometry.

        Header/body horizontal scrolling remains synchronized; no space padding or
        periodic refresh is used.

        Args:
            None.

        Returns:
            None.
        """
        self._sync_scheduled = False
        self.grid.activate()
        viewport = self.body_scroll.viewport()
        header_viewport = self.header.viewport()
        assert viewport is not None and header_viewport is not None
        for column, label in enumerate(self.headers):
            item = self.grid.itemAtPosition(1 if self.inputs else 0, column)
            if item is not None and item.widget() is not None:
                widget = item.widget()
                assert widget is not None
                label.setFixedWidth(widget.width())
        margins = self.grid.contentsMargins()
        self.header_grid.setContentsMargins(
            margins.left(),
            margins.top(),
            margins.right() + header_viewport.width() - viewport.width(),
            margins.bottom(),
        )
        self.header_grid.setHorizontalSpacing(self.grid.horizontalSpacing())
        bar = self.body_scroll.horizontalScrollBar()
        assert bar is not None
        self.header_widget.setFixedSize(header_viewport.width() + bar.maximum(), 42)
        self.header_grid.activate()
        for button in (
            self.clear_button,
            self.context_button,
            self.calculate_button,
        ):
            button.setFixedHeight(40)

        self.summary.align_to(self.outputs[0][1] if self.outputs else None, self)

    def eventFilter(self, watched: QObject | None, event: QEvent | None) -> bool:  # noqa: N802 - Qt override
        """Update sticky headers when the viewport or its task content resizes.

        Args:
            watched: QObject receiving the event; may be None in direct defensive calls.
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            True only when this filter explicitly consumes the event; otherwise the
            normal Qt base-filter result.
        """
        if event is not None and event.type() == QEvent.Type.Resize:
            self._schedule_sync()
        return super().eventFilter(watched, event)

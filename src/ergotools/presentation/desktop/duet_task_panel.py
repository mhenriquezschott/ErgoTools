"""Original DUET five-column controls, separated from SQL and scientific models.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Callable, Mapping
from functools import partial

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
from ergotools.domain.assessments.duet_summary import DuetSummary
from ergotools.domain.assessments.validation import DraftError, InputIssue
from ergotools.domain.display_precision import DisplayPrecision
from ergotools.presentation.desktop.duet_presenter import DuetEditContext, DuetPresenter
from ergotools.presentation.desktop.historical_result_display import (
    historical_damage_color,
    historical_number,
    show_historical_rows,
)
from ergotools.presentation.desktop.precision_editor import PrecisionLineEdit
from ergotools.presentation.desktop.theme.duet_summary import display_duet_summary
from ergotools.presentation.desktop.theme.main_workspace import MAIN_WORKSPACE_STYLE
from ergotools.presentation.desktop.tool_result_summary import ToolResultSummary

# Original task-column ordering with English/Spanish captions; units are supplied
# separately.
_HEADERS = (
    ("Task #", "Tarea #"),
    ("OMNI-Res Scale", "Escala OMNI-Res"),
    ("Repetitions (per work day)", "Repeticiones (por jornada laboral)"),
    ("Damage (cumulative)", "Daño (acumulado)"),
    ("% Total (damage)", "% Total (daño)"),
)
# Original dimensionless OMNI-Res scale 0-10 captions; blank entries intentionally match
# the reference.
_RATINGS = (
    ("Extremely Easy", "Extremadamente fácil"),
    ("", ""),
    ("Easy", "Fácil"),
    ("", ""),
    ("Somewhat Easy", "Algo fácil"),
    ("", ""),
    ("Somewhat Hard", "Algo difícil"),
    ("", ""),
    ("Hard", "Difícil"),
    ("", ""),
    ("Extremely Hard", "Extremadamente difícil"),
)


class DuetTaskPanel(QWidget):
    """Own DUET widgets and pending input; the presenter owns source and history."""

    def __init__(
        self,
        presenter: DuetPresenter,
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
        self.context: DuetEditContext | None = None
        self.pending = False
        self.inputs: list[tuple[QComboBox, PrecisionLineEdit]] = []
        self.outputs: list[tuple[QLabel, QLabel]] = []
        self.task_ids: tuple[str, ...] = ()
        self._sync_scheduled = False
        self.setStyleSheet(MAIN_WORKSPACE_STYLE)
        layout = QVBoxLayout(self)
        self.header_widget = QWidget()
        self.header_grid = QGridLayout(self.header_widget)
        self.headers = tuple(QLabel() for _ in range(5))
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
        self.frame = QFrame()
        frame_layout = QVBoxLayout(self.frame)
        self.grid = QGridLayout()
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        for column, (stretch, width) in enumerate(
            zip((0, 4, 3, 2, 1), (48, 250, 220, 150, 105), strict=True)
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
        for label, texts in zip(self.headers, _HEADERS, strict=True):
            label.setText(texts[language])
            label.setToolTip(texts[language])
        for combo, editor in self.inputs:
            combo.blockSignals(True)
            for index, texts in enumerate(_RATINGS):
                combo.setItemText(index, f"{index}: {texts[language]}")
            combo.blockSignals(False)
            combo.setToolTip(_HEADERS[1][language])
            editor.setToolTip(_HEADERS[2][language])
        self.clear_button.setText(("Clear assessment", "Limpiar evaluación")[language])
        self.calculate_button.setText(("Calculate", "Calcular")[language])
        self.clear_button.setToolTip(
            (
                "Clear DUET inputs and calculated results.",
                "Borre los datos y resultados DUET.",
            )[language]
        )
        self.calculate_button.setToolTip(
            (
                "Calculate DUET risk from the shown tasks.",
                "Calcule el riesgo DUET con las tareas mostradas.",
            )[language]
        )
        self.context_button.setToolTip(
            (
                "Open the task-data grid view for the active tool.",
                "Abra la cuadrícula de tareas de la herramienta activa.",
            )[language]
        )
        self._schedule_sync()

    def load_source(self, context: DuetEditContext | None) -> None:
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
        for column in range(5):
            hidden_header = QLabel()
            hidden_header.setFixedHeight(0)
            hidden_header.setMinimumWidth(0)
            hidden_header.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self.grid.addWidget(hidden_header, 0, column)
        source = self.presenter.source() if context is not None else None
        tasks = source.tasks if source is not None else ()
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
            combo.setMinimumWidth(250)
            combo.setSizeAdjustPolicy(
                QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
            )
            combo.setMinimumContentsLength(19)
            combo.addItems(
                [f"{index}: {texts[0]}" for index, texts in enumerate(_RATINGS)]
            )
            combo.setCurrentIndex(
                task.omni_res_scale if task.omni_res_scale is not None else -1
            )
            assert context is not None
            editor = PrecisionLineEdit(task.repetitions, context.convention, 0)
            editor.setMaximumWidth(280)
            editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
            assert context is not None
            combo.currentIndexChanged.connect(
                partial(self._selector_changed, task.task_id)
            )
            # Compact text keeps exact unchanged values in PrecisionLineEdit.
            editor.setCursorPosition(0)
            editor.textEdited.connect(self._mark_pending)
            editor.editingFinished.connect(partial(self.commit_cell, task.task_id, 2))
            self.grid.addWidget(combo, row, 1)
            self.grid.addWidget(editor, row, 2)
            self.inputs.append((combo, editor))
            outputs = (QLabel("0.0"), QLabel("0.0"))
            for column, output in zip((3, 4), outputs, strict=True):
                output.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.grid.addWidget(output, row, column)
            self.outputs.append(outputs)
            if row == 1:
                # Rebuilt controls receive their real widths after layout activation.
                for widget in (label, combo, editor, *outputs):
                    widget.installEventFilter(self)
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

    def input_rows(self) -> tuple[tuple[str, int | None, str], ...]:
        """Read widget values once without accepting edits or changing history.

        Args:
            None.

        Returns:
            Stable task identities and current displayed values in task order.
        """
        return tuple(
            (
                identity,
                combo.currentIndex() if combo.currentIndex() >= 0 else None,
                editor.source_text(),
            )
            for identity, (combo, editor) in zip(
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
            self.presenter.calculate()
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
        """Apply current typed DUET row results or clear previous text and colors.

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
            "Probabilidad de Trastorno de Extremidad Superior Distal (%):"
            if self.language is Language.SPANISH
            else "Probability of Distal Upper Extremity Outcome (%):"
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
        if not isinstance(result.summary, DuetSummary):
            return
        display = display_duet_summary(result.summary, precision)
        self.summary.show_values(
            display.damage_text, display.probability_text, display.color
        )
        for outputs, damage, share, color in zip(
            self.outputs,
            display.task_damage_texts,
            display.contribution_texts,
            display.task_colors,
            strict=True,
        ):
            outputs[0].setText(damage)
            outputs[1].setText(share)
            if color:
                outputs[0].setStyleSheet("background-color: " + color)

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
            item = self.grid.itemAtPosition(1, column)
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

        self.summary.align_to(self.outputs[0][0] if self.outputs else None, self)

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

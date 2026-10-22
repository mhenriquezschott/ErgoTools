"""Compact Job task input grid, independent of avatar and main assessment widgets.

Presentation layer. Reuse domain tasks and application calculator operations; this
widget only projects/edit inputs. Each completed numeric cell or selector emits one
immutable source edit without rebuilding sibling controls. Parent owns persistence,
shared history, clear/remove confirmation and calculation. No SQL or formulas.
"""

from dataclasses import replace

from PyQt5.QtCore import QEvent, QLocale, Qt, pyqtSignal
from PyQt5.QtGui import QDoubleValidator, QResizeEvent
from PyQt5.QtWidgets import (
    QComboBox,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from ergotools.application.settings import Language
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.job_risk import JobTaskResult
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.precision_editor import PrecisionLineEdit
from ergotools.presentation.numeric_input import parse_input_number


class JobTaskEditor(QTableWidget):
    """Own only displayed source inputs; each accepted cell emits its exact source."""

    source_edited = pyqtSignal(object)

    def __init__(
        self,
        language: Language,
        convention: DecimalConvention,
        parent: QWidget | None = None,
    ) -> None:
        """Create an empty task table with an explicit language/decimal policy.

        Args:
            language: UI wording, never the numeric convention or source units.
            convention: Application decimal mark for validators and exact text parsing.
            parent: Widget owner; the containing Job editor retains lifetime.

        Returns:
            None; no task source or history action is created.
        """
        super().__init__(parent)
        self.language = language
        self.convention = convention
        self.source: AssessmentDraft | None = None
        self._fitting_columns = False
        self.inputs: list[list[PrecisionLineEdit | QComboBox]] = []
        self.setMinimumHeight(160)
        self.setMaximumHeight(340)
        header = self.horizontalHeader()
        assert header is not None
        header.setSectionResizeMode(QHeaderView.Fixed)
        vertical = self.verticalHeader()
        assert vertical is not None
        vertical.setDefaultSectionSize(42)

    def load_source(
        self, source: AssessmentDraft | None, results: tuple[JobTaskResult, ...] = ()
    ) -> None:
        """Rebind an explicit source after selection/replay, never inside cell edits.

        Args:
            source: Exact Job/tool tasks, or None for direct entry.
            results: Matching exact calculated rows, empty before calculation.

        Returns:
            None; existing source values and their full precision remain untouched.
        """
        self.source = source
        self.inputs = []
        self.clear()
        if source is None:
            self.setRowCount(0)
            self.setColumnCount(0)
            return
        spanish = self.language is Language.SPANISH
        imperial = (
            not isinstance(source, DuetDraft)
            and source.system is MeasurementSystem.IMPERIAL
        )
        headers = (
            ["OMNI-RES", "Repeticiones" if spanish else "Repetitions"]
            if isinstance(source, DuetDraft)
            else [
                *(
                    ["Tipo de tarea" if spanish else "Task type"]
                    if isinstance(source, TstDraft)
                    else []
                ),
                ("Brazo de palanca" if spanish else "Lever arm")
                + (" (in)" if imperial else " (cm)"),
                ("Carga" if spanish else "Load") + (" (lbf)" if imperial else " (N)"),
                "Repeticiones" if spanish else "Repetitions",
            ]
        )
        headers.extend(
            (
                []
                if isinstance(source, DuetDraft)
                else [
                    ("Momento" if spanish else "Moment")
                    + (" (ft.lb)" if imperial else " (N.m)")
                ]
            )
            + [
                "Daño" if spanish else "Damage",
                "Aporte (%)" if spanish else "Share (%)",
            ]
        )
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.setRowCount(len(source.tasks))
        for row, task in enumerate(source.tasks):
            assert isinstance(task, (LifftTask, DuetTask, TstTask))
            controls: list[PrecisionLineEdit | QComboBox] = []
            fields = (
                ("omni_res_scale", "repetitions")
                if isinstance(task, DuetTask)
                else (
                    ("direction", "lever_arm", "load", "repetitions")
                    if isinstance(task, TstTask)
                    else ("lever_arm", "load", "repetitions")
                )
            )
            for column, field in enumerate(fields):
                if field in ("direction", "omni_res_scale"):
                    combo = QComboBox()
                    if field == "direction":
                        for code, en, es in (
                            ("0", "Handling loads", "Manipulación de cargas"),
                            (
                                "1",
                                "Push or pull downward",
                                "Empujar o tirar hacia abajo",
                            ),
                            (
                                "2",
                                "Horizontal push or pull",
                                "Empuje o tirón horizontal",
                            ),
                        ):
                            combo.addItem(es if spanish else en, code)
                        assert isinstance(task, TstTask)
                        combo.setCurrentIndex(
                            combo.findData(
                                task.direction.value if task.direction else None
                            )
                        )
                    else:
                        for scale in range(11):
                            combo.addItem(str(scale), scale)
                        assert isinstance(task, DuetTask)
                        combo.setCurrentIndex(combo.findData(task.omni_res_scale))
                    combo.currentIndexChanged.connect(
                        lambda index, r=row, f=field, c=combo: self._selector_changed(
                            r, f, c
                        )
                    )
                    controls.append(combo)
                    combo.setProperty("jobTaskRow", row)
                    combo.setProperty("jobTaskColumn", column)
                    combo.installEventFilter(self)
                    self.setCellWidget(row, column, combo)
                else:
                    value = (
                        task.repetitions
                        if field == "repetitions"
                        else task.lever_arm
                        if field == "lever_arm"
                        and isinstance(task, (LifftTask, TstTask))
                        else task.load
                        if isinstance(task, (LifftTask, TstTask))
                        else None
                    )
                    editor = PrecisionLineEdit(
                        value, self.convention, 0 if field == "repetitions" else 4
                    )
                    validator = QDoubleValidator(0, 1e12, 12, editor)
                    locale = QLocale(
                        "de_DE"
                        if self.convention is DecimalConvention.COMMA
                        else "en_US"
                    )
                    locale.setNumberOptions(QLocale.RejectGroupSeparator)
                    validator.setLocale(locale)
                    editor.setValidator(validator)
                    editor.editingFinished.connect(
                        lambda r=row, f=field, e=editor: self._number_changed(r, f, e)
                    )
                    controls.append(editor)
                    editor.setProperty("jobTaskRow", row)
                    editor.setProperty("jobTaskColumn", column)
                    editor.installEventFilter(self)
                    self.setCellWidget(row, column, editor)
            self.inputs.append(controls)
        self.show_results(results)

    def eventFilter(self, watched: object, event: QEvent | None) -> bool:  # noqa: N802 - Qt override
        """Keep selected task aligned with native input focus before Remove is used.

        Args:
            watched: Owned numeric/selector child; unrelated objects are ignored.
            event: Native focus notification forwarded unchanged.

        Returns:
            False; native typing, selector popups and keyboard traversal remain intact.
        """
        if (
            isinstance(watched, QWidget)
            and event is not None
            and event.type() == QEvent.Type.FocusIn
        ):
            row, column = (
                watched.property("jobTaskRow"),
                watched.property("jobTaskColumn"),
            )
            if isinstance(row, int) and isinstance(column, int):
                self.setCurrentCell(row, column)
        return False

    def show_results(self, results: tuple[JobTaskResult, ...]) -> None:
        """Display retained per-task outputs or clear stale outputs without a rebind.

        Args:
            results: Exact matching calculated rows, empty after any source edit.

        Returns:
            None; scientific quantities retain full precision in storage/tooltips while
            visible cells use compact numbers and the application decimal convention.
            Numeric input widgets and focus/native typing history remain intact.
        """
        if self.source is None:
            return
        for row, controls in enumerate(self.inputs):
            result = results[row] if row < len(results) else None
            values = (
                [result.moment if result else None]
                if not isinstance(self.source, DuetDraft)
                else []
            ) + [
                result.damage if result else None,
                result.share_percent if result else None,
            ]
            for offset, value in enumerate(values):
                text = (
                    "—"
                    if value is None
                    else f"{value:.6g}".replace(".", self.convention.value)
                )
                cell = QTableWidgetItem(text)
                flags = Qt.ItemFlags(Qt.ItemFlag.ItemIsEnabled)
                flags |= Qt.ItemFlag.ItemIsSelectable
                cell.setFlags(flags)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setToolTip(
                    ""
                    if value is None
                    else str(value).replace(".", self.convention.value)
                )
                self.setItem(row, len(controls) + offset, cell)
        self._fit_columns()

    def resizeEvent(self, event: QResizeEvent | None) -> None:  # noqa: N802 - Qt override
        """Refit complete headers and source controls to the available task viewport.

        Args:
            event: Native resize event forwarded to the standard table implementation.

        Returns:
            None; resizing never changes tasks, calculations or project history.
        """
        if event is not None:
            super().resizeEvent(event)
        self._fit_columns()

    def _fit_columns(self) -> None:
        """Fit full labels/choices, distributing spare width without clipping minima.

        Args:
            None.

        Returns:
            None; horizontal scrolling occurs only when intrinsic widths exceed the
            viewport. Native selector arrows/padding and complete headers are included.
            Reentrant viewport changes cannot recurse into another sizing pass.
        """
        if self._fitting_columns or not self.columnCount():
            return
        self._fitting_columns = True
        try:
            viewport = self.viewport()
            header = self.horizontalHeader()
            assert viewport is not None and header is not None
            metrics = header.fontMetrics()
            widths = []
            for column in range(self.columnCount()):
                label = self.horizontalHeaderItem(column)
                width = max(
                    75, metrics.horizontalAdvance(label.text() if label else "") + 26
                )
                for row in range(self.rowCount()):
                    widget = self.cellWidget(row, column)
                    if isinstance(widget, QComboBox):
                        width = max(width, widget.sizeHint().width())
                    elif isinstance(widget, PrecisionLineEdit):
                        width = max(
                            width,
                            widget.fontMetrics().horizontalAdvance(widget.text()) + 30,
                            90,
                        )
                    else:
                        cell = self.item(row, column)
                        if cell is not None:
                            width = max(
                                width, metrics.horizontalAdvance(cell.text()) + 24
                            )
                widths.append(width)
            spare = max(0, viewport.width() - sum(widths))
            for column, width in enumerate(widths):
                extra, remainder = divmod(spare, len(widths))
                self.setColumnWidth(column, width + extra + (column < remainder))
        finally:
            self._fitting_columns = False

    def _number_changed(self, row: int, field: str, editor: PrecisionLineEdit) -> None:
        """Accept one valid completed input without sweeping unfinished sibling cells.

        Args:
            row: Stable current zero-based task position.
            field: Numeric source field owned by this editor.
            editor: Exact precision-preserving editor finishing its cell.

        Returns:
            None; invalid text stays visible and emits no accepted source/history edit.
        """
        source = self.source
        if source is None or (
            not editor.hasAcceptableInput() and editor.text().strip()
        ):
            return
        value = parse_input_number(
            editor.source_text(), self.convention, field, source.tasks[row].task_id
        )
        if isinstance(source, DuetDraft):
            tasks = list(source.tasks)
            tasks[row] = replace(tasks[row], repetitions=value)
            updated: AssessmentDraft = replace(source, tasks=tuple(tasks))
        elif isinstance(source, LifftDraft):
            items = list(source.tasks)
            task = items[row]
            items[row] = (
                replace(task, repetitions=value)
                if field == "repetitions"
                else replace(task, lever_arm=value)
                if field == "lever_arm"
                else replace(task, load=value)
            )
            updated = replace(source, tasks=tuple(items))
        else:
            shoulders = list(source.tasks)
            task_st = shoulders[row]
            shoulders[row] = (
                replace(task_st, repetitions=value)
                if field == "repetitions"
                else replace(task_st, lever_arm=value)
                if field == "lever_arm"
                else replace(task_st, load=value)
            )
            updated = replace(source, tasks=tuple(shoulders))
        self._emit_source(updated)

    def _selector_changed(self, row: int, field: str, combo: QComboBox) -> None:
        """Accept only the selected scale/direction, preserving all other source fields.

        Args:
            row: Current zero-based task position.
            field: Selector identity, used to distinguish stored enum/scales.
            combo: Native selector carrying literal typed item data.

        Returns:
            None; unchanged choices produce no source/history edit.
        """
        source = self.source
        if field == "omni_res_scale" and isinstance(source, DuetDraft):
            tasks = list(source.tasks)
            tasks[row] = replace(tasks[row], omni_res_scale=int(combo.currentData()))
            self._emit_source(replace(source, tasks=tuple(tasks)))
        elif isinstance(source, TstDraft):
            shoulders = list(source.tasks)
            shoulders[row] = replace(
                shoulders[row], direction=TstDirection(combo.currentData())
            )
            self._emit_source(replace(source, tasks=tuple(shoulders)))

    def _emit_source(self, source: AssessmentDraft) -> None:
        """Update the local baseline before notifying its persistence-owning parent.

        Args:
            source: Validated replacement source for one completed cell.

        Returns:
            None; no-op edits never add history entries.
        """
        if source != self.source:
            self.source = source
            self.source_edited.emit(source)

    def accept_pending(self) -> bool:
        """Accept each valid unfinished numeric cell before a parent action.

        Args:
            None.

        Returns:
            False when any numeric editor is invalid, retaining its text for correction.
            Each valid changed cell remains its own shared history action.
        """
        for row, controls in enumerate(self.inputs):
            fields = (
                ("omni_res_scale", "repetitions")
                if isinstance(self.source, DuetDraft)
                else ("direction", "lever_arm", "load", "repetitions")
                if isinstance(self.source, TstDraft)
                else ("lever_arm", "load", "repetitions")
            )
            for field, control in zip(fields, controls, strict=True):
                if isinstance(control, PrecisionLineEdit):
                    if control.text().strip() and not control.hasAcceptableInput():
                        control.setFocus()
                        return False
                    self._number_changed(row, field, control)
        return True

    def has_pending(self) -> bool:
        """Detect unfinished numeric changes without accepting or rounding them.

        Args:
            None.

        Returns:
            True when an editor differs from the current source, including invalid text
            that must be corrected before shared history can replay.
        """
        source = self.source
        if source is None:
            return False
        for row, controls in enumerate(self.inputs):
            fields = (
                ("omni_res_scale", "repetitions")
                if isinstance(source, DuetDraft)
                else ("direction", "lever_arm", "load", "repetitions")
                if isinstance(source, TstDraft)
                else ("lever_arm", "load", "repetitions")
            )
            for field, control in zip(fields, controls, strict=True):
                if isinstance(control, PrecisionLineEdit):
                    if control.text().strip() and not control.hasAcceptableInput():
                        return True
                    value = parse_input_number(
                        control.source_text(),
                        self.convention,
                        field,
                        source.tasks[row].task_id,
                    )
                    if value != getattr(source.tasks[row], field):
                        return True
        return False

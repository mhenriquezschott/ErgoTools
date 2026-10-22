"""Original Job Management measurement table, with explicit typed form values.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

import math
from collections.abc import Iterable

from PyQt5 import sip
from PyQt5.QtCore import QLocale, QModelIndex, QSignalBlocker, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QDoubleValidator
from PyQt5.QtWidgets import (
    QAbstractItemDelegate,
    QHeaderView,
    QLineEdit,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from ergotools.application.settings import Language
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.duet import (
    probability_from_damage as duet_probability,
)
from ergotools.domain.assessments.lifft import (
    probability_from_damage as lifft_probability,
)
from ergotools.domain.assessments.tst import probability_from_damage as tst_probability
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.job_risk import JobRiskMeasurement
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.text import desktop_text
from ergotools.presentation.desktop.theme.duet_colors import duet_damage_color
from ergotools.presentation.desktop.theme.lifft_colors import lifft_damage_color
from ergotools.presentation.desktop.theme.tst_colors import tst_damage_color

# Original job measurement row order: LiFFT, DUET and Shoulder Tool.
_KINDS = (AssessmentKind.LIFFT, AssessmentKind.DUET, AssessmentKind.TST)
# Original per-tool damage-to-probability functions in measurement row order; displayed
# results are percent.
_PROBABILITIES = (lifft_probability, duet_probability, tst_probability)
# Original per-tool continuous damage palettes in measurement row order.
_COLORS = (lifft_damage_color, duet_damage_color, tst_damage_color)

# Exact table/header rules from the original Job Management stylesheet.
_STYLE = """
QTableWidget { background: white; alternate-background-color: #F5F8FA;
 border: 1px solid #CAD5DD; gridline-color: #D5DEE5;
 selection-background-color: #087E91; selection-color: white; }
QHeaderView::section { background: #EAF1F5; color: #0B326C; border: 0;
 border-right: 1px solid #CAD5DD; border-bottom: 1px solid #CAD5DD;
 padding: 7px; font-weight: 700; }
"""


class _DamageDelegate(QStyledItemDelegate):
    """Restrict direct damage editing to finite nonnegative localized numeric text."""

    def createEditor(  # noqa: N802 - Qt override
        self, parent: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget:
        """Create the existing table editor with its owning decimal convention.

        Args:
            parent: Qt-owned editor container.
            option: Standard Qt cell geometry/style, retained by the view.
            index: Damage cell being edited; outputs have no edit flag.

        Returns:
            Native line editor with a locale-specific nonnegative numeric validator.
        """
        editor = QLineEdit(parent)
        table = self.parent()
        assert isinstance(table, JobRiskTable)
        validator = QDoubleValidator(0, 1e300, 15, editor)
        locale = QLocale(
            "de_DE" if table.convention is DecimalConvention.COMMA else "en_US"
        )
        locale.setNumberOptions(QLocale.RejectGroupSeparator)
        validator.setLocale(locale)
        editor.setValidator(validator)
        editor.textEdited.connect(table.pending_input_changed)
        return editor


class JobRiskTable(QTableWidget):
    """Edit damage and derive displayed probability once per user change.

    Preserve the original three rows, three columns, row height and stretch rules. No
    database or parent-window lookup occurs. Loading saved values emits no form-edit
    notification and never recalculates recorded probabilities.
    """

    measurements_changed = pyqtSignal()
    pending_input_changed = pyqtSignal()

    def __init__(
        self,
        system: MeasurementSystem,
        *,
        language: Language = Language.ENGLISH,
        convention: DecimalConvention = DecimalConvention.POINT,
        parent: QWidget | None = None,
    ) -> None:
        """Build the reference table with empty editable rows and explicit units.

        Args:
            system: Measurement display policy; conversions preserve canonical
                source/body units.
            convention: Application decimal separator, independent of UI language.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(3, 3, parent)
        self.system = system
        self.language = language
        self.convention = convention
        self._saved: dict[AssessmentKind, JobRiskMeasurement] = {}
        self._editable = True
        self.setStyleSheet(_STYLE)
        self.setHorizontalHeaderLabels(
            [
                desktop_text(key, language)
                for key in (
                    "job_tool",
                    "job_damage_header",
                    "job_probability_header",
                )
            ]
        )
        for column in range(3):
            header_item = self.horizontalHeaderItem(column)
            assert header_item is not None
            font = header_item.font()
            font.setBold(True)
            header_item.setFont(font)
            header_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        for row, label in enumerate(("LiFFT", "DUET", "ST")):
            for column in range(3):
                cell = QTableWidgetItem(label if column == 0 else "")
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if column == 0:
                    cell.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    font = cell.font()
                    font.setBold(True)
                    cell.setFont(font)
                self.setItem(row, column, cell)
        vertical = self.verticalHeader()
        header = self.horizontalHeader()
        assert vertical is not None and header is not None
        vertical.setDefaultSectionSize(35)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.load(())
        self.setItemDelegateForColumn(1, _DamageDelegate(self))
        self.cellChanged.connect(self._damage_changed)

    def has_pending(self) -> bool:
        """Expose a live delegate's unfinished text to shared history availability.

        Args:
            None.

        Returns:
            True when a visible damage editor has intentionally modified its text.
        """
        return any(
            editor.isVisible() and editor.isModified()
            for editor in self.findChildren(QLineEdit)
        )

    def accept_pending(self) -> bool:
        """Commit a valid native damage editor before Close, copy or shared replay.

        Args:
            None.

        Returns:
            False for invalid unfinished input; True after accepting each valid cell.
            Each commit follows the ordinary measurements_changed path exactly once.
        """
        for editor in self.findChildren(QLineEdit):
            if not editor.isVisible():
                continue
            if editor.text().strip() and not editor.hasAcceptableInput():
                editor.setFocus()
                return False
            self.commitData(editor)
            if not sip.isdeleted(editor):
                self.closeEditor(editor, QAbstractItemDelegate.EndEditHint.NoHint)
        return True

    def _cell(self, row: int, column: int) -> QTableWidgetItem:
        """Require the existing cell at the requested zero-based table location.

        Args:
            row: Zero-based task/worker table row.
            column: Zero-based table/tree column; derived columns remain protected where
                specified.

        Returns:
            Borrowed existing table cell at the validated zero-based coordinates.
        """
        cell = self.item(row, column)
        assert cell is not None
        return cell

    def load(self, measurements: Iterable[JobRiskMeasurement]) -> None:
        """Display compact values, retaining exact quantities and task sources.

        Direct editable damage retains its full entered precision; calculated/read-only
        quantities use compact formatting. Reject duplicate tools before changing the
        display. Empty values retain the
        original neutral color; populated values use the reference palette.

        Args:
            measurements: Saved per-tool values, preserving sources, units and missing
                versus zero values.

        Returns:
            None.

        Raises:
            ValueError: Duplicate measurement tool.
        """
        values = tuple(measurements)
        saved = {item.kind: item for item in values}
        if len(saved) != len(values):
            raise ValueError("Duplicate measurement tool.")
        with QSignalBlocker(self):
            for row, kind in enumerate(_KINDS):
                measurement = saved.get(kind)
                damage = measurement.cumulative_damage if measurement else None
                probability = measurement.probability_percent if measurement else None
                for column, value, decimals in ((1, damage, 4), (2, probability, 1)):
                    text = (
                        ""
                        if value is None
                        else (
                            str(value)
                            if column == 1
                            and measurement is not None
                            and measurement.source is None
                            else f"{value:.{decimals}f}"
                        ).replace(".", self.convention.value)
                    )
                    cell = self._cell(row, column)
                    cell.setText(text)
                    cell.setData(Qt.ItemDataRole.UserRole, (value, text))
                self._color(row, "#D9E1E6" if damage is None else _COLORS[row](damage))
            self._saved = saved
            self.set_editable(self._editable)

    def set_editable(self, editable: bool) -> None:
        """Permit direct damage edits; calculated-source rows remain read-only.

        Args:
            editable: True permits input edits; False preserves selection/copying of
                read-only values.

        Returns:
            None.
        """
        self._editable = editable
        for row in range(3):
            for column in (1, 2):
                flags = Qt.ItemFlags(Qt.ItemFlag.ItemIsEnabled)
                flags |= Qt.ItemFlag.ItemIsSelectable
                if (
                    editable
                    and column == 1
                    and self._saved.get(
                        _KINDS[row], JobRiskMeasurement(_KINDS[row])
                    ).source
                    is None
                ):
                    flags |= Qt.ItemFlag.ItemIsEditable
                with QSignalBlocker(self):
                    self._cell(row, column).setFlags(flags)

    def _color(self, row: int, color: str) -> None:
        """Apply the tool-specific continuous damage color.

        Apply the tool-specific continuous damage color to both current risk output
        cells.

        Args:
            row: Zero-based task/worker table row.
            color: Original CSS/Qt palette color, or None to clear unavailable-result
                styling.

        Returns:
            None.
        """
        for column in (1, 2):
            self._cell(row, column).setBackground(QColor(color))

    def _damage_changed(self, row: int, column: int) -> None:
        """Recalculate displayed probability only after an editable damage-cell change.

        Recalculate displayed probability only after an editable damage-cell change;
        invalid/empty input clears stale probability/color before one notification.

        Args:
            row: Zero-based task/worker table row.
            column: Zero-based table/tree column; derived columns remain protected where
                specified.

        Returns:
            None.
        """
        if column != 1 or not self._editable:
            return
        retained = self._saved.get(_KINDS[row])
        if retained is not None and retained.source is not None:
            self.load(self._saved.values())
            return
        with QSignalBlocker(self):
            try:
                damage = float(
                    self._cell(row, 1).text().replace(self.convention.value, ".")
                )
                if not math.isfinite(damage) or damage < 0:
                    raise ValueError("Invalid damage.")
                probability = (
                    round(_PROBABILITIES[row](damage) * 100, 1) if damage else 0.0
                )
                self._cell(row, 2).setData(Qt.ItemDataRole.UserRole, None)
                self._cell(row, 2).setText(
                    str(probability).replace(".", self.convention.value)
                )
                self._color(row, _COLORS[row](damage) if damage else "#ffffff")
            except (ValueError, OverflowError):
                # Invalid/cleared damage must not leave an old valid-looking result.
                self._cell(row, 2).setData(Qt.ItemDataRole.UserRole, None)
                self._cell(row, 2).setText("")
                self._color(row, "#D9E1E6")
        self.measurements_changed.emit()

    def _quantity(self, row: int, column: int) -> float:
        """Read an unchanged exact value or parse the intentionally edited token.

        Args:
            row: Tool row in the three-row summary.
            column: Damage or probability column.

        Returns:
            Full saved precision when its rounded display is unchanged; otherwise the
            new explicit localized numeric input. Display rounding is never storage.

        Raises:
            ValueError: The entered text is not a numeric quantity.
        """
        cell = self._cell(row, column)
        retained = cell.data(Qt.ItemDataRole.UserRole)
        if isinstance(retained, tuple) and retained[1] == cell.text():
            value = retained[0]
            if isinstance(value, (int, float)):
                return value
        return float(cell.text().replace(self.convention.value, "."))

    def measurements(self) -> tuple[JobRiskMeasurement, ...]:
        """Read exact validated current values without committing or converting units.

        Raise ValueError for nonnumeric, incomplete, negative or nonfinite values.
        Retain sources and units; new direct rows use the injected system. Fully
        empty direct rows are omitted; uncalculated source rows retain their tasks.

        Args:
            None.

        Returns:
            Nonempty validated tool measurements in original order, retaining saved
            sources/units; completely empty direct rows are omitted.

        Raises:
            ValueError: The supplied ownership, enum or value violates the operation's
                validated contract.
        """
        result = []
        for row, kind in enumerate(_KINDS):
            calculated = self._saved.get(kind)
            if calculated is not None and calculated.source is not None:
                result.append(calculated)
                continue
            texts = (
                self._cell(row, 1).text().strip(),
                self._cell(row, 2).text().strip(),
            )
            if not any(texts):
                saved_empty = self._saved.get(kind)
                if saved_empty is not None and saved_empty.source is not None:
                    result.append(saved_empty)
                continue
            try:
                damage, probability = (self._quantity(row, column) for column in (1, 2))
                saved = self._saved.get(kind)
                result.append(
                    JobRiskMeasurement(
                        kind,
                        damage,
                        probability,
                        saved.unit if saved is not None else self.system.value.title(),
                        saved.source if saved is not None else None,
                        saved.task_results if saved is not None else (),
                    )
                )
            except ValueError as error:
                raise ValueError(
                    desktop_text("job_invalid_measurement", self.language)
                ) from error
        return tuple(result)

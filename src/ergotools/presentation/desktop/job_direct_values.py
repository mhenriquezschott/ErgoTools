"""Optional per-tool direct Job entry without a three-tool summary table.

Presentation layer. Own localized numeric fields and exact retained measurements.
Delegate probability conversion to the existing scientific functions. Completed
fields notify the Job dialog; that host alone owns persistence and shared history.
Loading, selection and display formatting never recalculate stored measurements.
"""

from collections.abc import Iterable

from PyQt5.QtCore import QLocale, QSignalBlocker, Qt, pyqtSignal
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QLabel, QLineEdit, QStackedWidget, QVBoxLayout, QWidget

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
from ergotools.presentation.numeric_input import parse_input_number

# Existing tool-specific damage-to-probability models; outputs are fractions.
_PROBABILITIES = {
    AssessmentKind.LIFFT: lifft_probability,
    AssessmentKind.DUET: duet_probability,
    AssessmentKind.TST: tst_probability,
}


class JobDirectValues(QStackedWidget):
    """Own exact direct damage fields embedded in the colored summary value cell.

    Attributes:
        preview_changed: Emits tool identity and current valid measurement or None.
        measurements_changed: Signals a completed edit for shared project acceptance.
        pending_input_changed: Refreshes availability without accepting typing.
    """

    preview_changed = pyqtSignal(object, object)
    measurements_changed = pyqtSignal()
    pending_input_changed = pyqtSignal()

    def __init__(
        self,
        system: MeasurementSystem,
        language: Language,
        convention: DecimalConvention,
    ) -> None:
        """Build guarded direct-entry fields without creating measurements.

        Args:
            system: Default units recorded for newly entered direct results.
            language: English/Spanish labels, independent of numeric parsing.
            convention: Explicit decimal separator; grouping is rejected.

        Returns:
            None; fields emit only on an explicitly completed valid edit.
        """
        super().__init__()
        self.system = system
        self.language = language
        self.convention = convention
        self.fields: dict[AssessmentKind, QLineEdit] = {}
        self.errors: dict[AssessmentKind, QLabel] = {}
        self._saved: dict[AssessmentKind, JobRiskMeasurement] = {}
        self._accepted: dict[AssessmentKind, str] = {}
        for kind in AssessmentKind:
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setSpacing(2)
            layout.setContentsMargins(0, 0, 0, 0)
            field = QLineEdit()
            field.setPlaceholderText("0.0000")
            field.setToolTip(
                "Enter finite, nonnegative cumulative damage; probability is derived."
                if language is Language.ENGLISH
                else "Daño acumulado finito no negativo; probabilidad derivada."
            )
            validator = QDoubleValidator(0, 1e300, 15, field)
            locale = QLocale(
                "de_DE" if convention is DecimalConvention.COMMA else "en_US"
            )
            locale.setNumberOptions(QLocale.RejectGroupSeparator)
            validator.setLocale(locale)
            field.setValidator(validator)
            field.setMinimumWidth(0)
            field.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error = QLabel()
            error.setWordWrap(True)
            error.setObjectName("inputError")
            layout.addWidget(field)
            layout.addWidget(error)
            self.addWidget(page)
            self.fields[kind] = field
            self.errors[kind] = error
            field.textEdited.connect(self.pending_input_changed)
            field.textChanged.connect(lambda _text, k=kind: self._preview(k))
            field.editingFinished.connect(lambda k=kind: self._finish_edit(k))
        self.load(())

    def select_kind(self, kind: AssessmentKind) -> None:
        """Select a tool page without accepting or modifying its inputs.

        Args:
            kind: Stable selected tool identity.

        Returns:
            None.
        """
        self.setCurrentIndex(list(AssessmentKind).index(kind))

    def load(self, measurements: Iterable[JobRiskMeasurement]) -> None:
        """Bind exact current values without emitting edit notifications.

        Args:
            measurements: At most one source/result per tool; stored precision retained.

        Returns:
            None; calculated sources are protected against direct editing.

        Raises:
            ValueError: Duplicate tool measurements were supplied.
        """
        values = tuple(measurements)
        saved = {item.kind: item for item in values}
        if len(saved) != len(values):
            raise ValueError("Duplicate measurement tool.")
        self._saved = saved
        for kind, field in self.fields.items():
            item = saved.get(kind)
            damage = item.cumulative_damage if item else None
            text = (
                ""
                if damage is None
                else str(damage).replace(".", self.convention.value)
            )
            with QSignalBlocker(field):
                field.setText(text)
                field.setReadOnly(item is not None and item.source is not None)
            self._accepted[kind] = text
            self._preview(kind)

    def _value(self, kind: AssessmentKind) -> JobRiskMeasurement | None:
        """Read retained precision or derive one deliberately changed direct value.

        Args:
            kind: Exact tool whose field is inspected.

        Returns:
            Current measurement, or None for an empty direct field.

        Raises:
            ValueError: Damage is invalid, negative, nonfinite or out of range.
        """
        saved = self._saved.get(kind)
        text = self.fields[kind].text().strip()
        if saved is not None:
            original = (
                ""
                if saved.cumulative_damage is None
                else str(saved.cumulative_damage).replace(".", self.convention.value)
            )
            if saved.source is not None or text == original:
                return saved
        if not text:
            return None
        damage = parse_input_number(text, self.convention, "damage", kind.value)
        assert damage is not None
        if damage < 0:
            raise ValueError("Damage must be nonnegative.")
        probability = round(_PROBABILITIES[kind](damage) * 100, 1) if damage else 0.0
        return JobRiskMeasurement(
            kind,
            damage,
            probability,
            saved.unit if saved else self.system.value.title(),
        )

    def _preview(self, kind: AssessmentKind) -> None:
        """Clear stale output immediately when direct text becomes invalid.

        Args:
            kind: Tool whose direct input changed.

        Returns:
            None; preview alone does not persist or append history.
        """
        try:
            item = self._value(kind)
            self.errors[kind].clear()
            self.errors[kind].hide()
        except (ValueError, OverflowError):
            item = None
            self.errors[kind].show()
            self.errors[kind].setText(
                "Ingrese un daño finito no negativo."
                if self.language is Language.SPANISH
                else "Enter a finite, nonnegative damage value."
            )
        self.preview_changed.emit(kind, item)

    def _finish_edit(self, kind: AssessmentKind) -> None:
        """Adapt native editing completion to the guarded commit operation.

        Args:
            kind: Stable tool identity captured by the owned field's signal.

        Returns:
            None; invalid text remains available for correction.
        """
        self._commit(kind)

    def _commit(self, kind: AssessmentKind) -> bool:
        """Publish one completed valid direct field through the host's history path.

        Args:
            kind: Tool whose field completed editing.

        Returns:
            True for unchanged/valid text; False retains invalid input and focus.
        """
        field = self.fields[kind]
        try:
            self._value(kind)
        except (ValueError, OverflowError):
            self._preview(kind)
            field.setFocus()
            return False
        if field.text() != self._accepted[kind]:
            self._accepted[kind] = field.text()
            self.measurements_changed.emit()
        return True

    def has_pending(self) -> bool:
        """Inspect direct text without committing or fabricating history.

        Args:
            None.

        Returns:
            True when any field differs from its completed baseline.
        """
        return any(
            field.text() != self._accepted[kind] for kind, field in self.fields.items()
        )

    def accept_pending(self) -> bool:
        """Complete valid direct inputs before navigation, Close or project replay.

        Args:
            None.

        Returns:
            False at the first invalid field; otherwise True after individual commits.
        """
        return all(self._commit(kind) for kind in AssessmentKind)

    def measurements(self) -> tuple[JobRiskMeasurement, ...]:
        """Read all exact source/results, omitting empty direct values.

        Args:
            None.

        Returns:
            Measurements in stable LiFFT/DUET/ST order.

        Raises:
            ValueError: A direct damage token is invalid.
        """
        return tuple(
            item for kind in AssessmentKind if (item := self._value(kind)) is not None
        )

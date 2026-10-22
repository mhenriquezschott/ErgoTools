"""Real Qt form edits, stored evidence preservation and signal behavior.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QSignalSpy
from PyQt5.QtWidgets import QApplication, QTableWidgetItem

from ergotools.application.settings import Language
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_risk import JobRiskMeasurement
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.job_risk_table import JobRiskTable

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


def cell(table: JobRiskTable, row: int, column: int) -> QTableWidgetItem:
    """Return a required original table cell.

    Args:
        table: Owned risk table or explicit SQL table identity selected for fault
            injection.
        row: Zero-based task/risk table row selected for actual user editing.
        column: Zero-based visible column or explicit SQL column identity selected by
            the regression.

    Returns:
        Required existing borrowed Qt risk-table cell at the supplied zero-based
        coordinates.
    """
    result = table.item(row, column)
    assert result is not None
    return result


def test_load_preserves_values_and_edit_emits_once() -> None:
    """Loading retains recorded probability/unit/notes and causes no edit signals.

    Args:
        None.

    Returns:
        None.
    """
    table = JobRiskTable(MeasurementSystem.METRIC)
    try:
        original = JobRiskMeasurement(AssessmentKind.LIFFT, 1, 42, "Imperial")
        changed = QSignalSpy(table.measurements_changed)
        table.load((original,))
        assert table.measurements() == (original,)
        assert len(changed) == 0
        cell(table, 0, 1).setText("0")
        assert len(changed) == 1
        assert table.measurements() == (
            JobRiskMeasurement(AssessmentKind.LIFFT, 0, 0, "Imperial"),
        )
        assert cell(table, 0, 2).background().color().name() == "#ffffff"
        cell(table, 0, 1).setText("1")
        assert cell(table, 0, 2).text() == "84.9"
        assert len(changed) == 2
        with pytest.raises(ValueError, match="Duplicate"):
            table.load((original, original))
        assert cell(table, 0, 1).text() == "1"
    finally:
        table.close()


@pytest.mark.parametrize("text", ("", "bad", "nan", "inf", "-1"))
def test_invalid_damage_cannot_reuse_previous_probability(text: str) -> None:
    """Cleared/invalid cells remove an old result and neutralize both colors.

    Args:
        text: Literal typed/control input, including invalid/incomplete cases where
            specified.

    Returns:
        None.
    """
    table = JobRiskTable(MeasurementSystem.IMPERIAL)
    try:
        cell(table, 1, 1).setText("1")
        assert cell(table, 1, 2).text()
        cell(table, 1, 1).setText(text)
        assert cell(table, 1, 2).text() == ""
        assert cell(table, 1, 1).background().color().name() == "#d9e1e6"
        if text:
            with pytest.raises(ValueError, match="finite"):
                table.measurements()
        else:
            assert table.measurements() == ()
    finally:
        table.close()


def test_approved_flags_localization_and_new_row_units() -> None:
    """Approved values remain selectable; new rows receive explicit system labels.

    Args:
        None.

    Returns:
        None.
    """
    table = JobRiskTable(MeasurementSystem.METRIC, language=Language.SPANISH)
    try:
        cell(table, 2, 1).setText("1")
        assert table.measurements()[0].unit == "Metric"
        table.set_editable(False)
        for row in range(3):
            for column in (1, 2):
                flags = cell(table, row, column).flags()
                assert not flags & Qt.ItemFlag.ItemIsEditable
                assert flags & Qt.ItemFlag.ItemIsSelectable
        header = table.horizontalHeaderItem(1)
        assert header is not None and header.text() == "Daño acumulado\ntotal"
        table.set_editable(True)
        assert cell(table, 0, 1).flags() & Qt.ItemFlag.ItemIsEditable
        assert not cell(table, 0, 2).flags() & Qt.ItemFlag.ItemIsEditable
    finally:
        table.close()


def test_direct_damage_stays_exact_and_intentional_rounding_is_an_edit() -> None:
    """Editable direct values never hide precision behind a rounded input token.

    Args:
        None.

    Returns:
        None; an intentionally rounded replacement becomes the new numeric value.
    """
    original = JobRiskMeasurement(
        AssessmentKind.LIFFT, 0.123456789, 80.123456789, "Metric"
    )
    table = JobRiskTable(MeasurementSystem.METRIC)
    try:
        table.load((original,))
        assert cell(table, 0, 1).text() == "0.123456789"
        assert table.measurements() == (original,)
        cell(table, 0, 1).setText("0.1235")
        assert table.measurements()[0].cumulative_damage == 0.1235
        assert (
            table.measurements()[0].probability_percent != original.probability_percent
        )
    finally:
        table.close()

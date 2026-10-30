"""Optional Job direct entry preserves precision and commits complete fields only.

Test layer. Exercise the actual localized inputs and notifications without a
database. Source-bearing values stay read-only; invalid text cannot reuse output.
"""

import pytest
from PyQt5.QtTest import QSignalSpy
from PyQt5.QtWidgets import QApplication

from ergotools.application.job_calculation import calculate_job_measurement
from ergotools.application.settings import Language
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.job_risk import JobRiskMeasurement
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.job_direct_values import JobDirectValues

# Keep native controls alive for the module's independent widget checks.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("convention", list(DecimalConvention))
def test_exact_direct_values_and_completed_edits(convention: DecimalConvention) -> None:
    """Loading preserves saved probability; one completed edit derives it once.

    Args:
        convention: Explicit point/comma parsing independent of language.

    Returns:
        None; zero and absence remain distinct and unchanged precision is retained.
    """
    view = JobDirectValues(MeasurementSystem.METRIC, Language.ENGLISH, convention)
    original = JobRiskMeasurement(
        AssessmentKind.LIFFT, 0.123456789, 80.123456789, "Imperial"
    )
    changed = QSignalSpy(view.measurements_changed)
    view.load((original,))
    assert view.measurements() == (original,)
    assert not changed
    field = view.fields[AssessmentKind.LIFFT]
    field.setText("0" + convention.value + "001")
    assert view.has_pending() and not changed
    field.editingFinished.emit()
    assert len(changed) == 1
    assert view.measurements()[0].cumulative_damage == 0.001
    assert view.measurements()[0].probability_percent == 20.6
    assert view.measurements()[0].unit == "Imperial"
    field.editingFinished.emit()
    assert len(changed) == 1
    field.setText("0")
    assert view.accept_pending()
    assert view.measurements()[0].probability_percent == 0
    field.clear()
    assert view.accept_pending()
    assert not view.measurements()
    with pytest.raises(ValueError, match="Duplicate"):
        view.load((original, original))
    view.close()


@pytest.mark.parametrize("token", ("bad", "nan", "inf", "-1", "1e400", "1,000"))
def test_invalid_direct_input_clears_preview_and_blocks_completion(token: str) -> None:
    """Invalid tokens cannot leave the previous valid-looking probability visible.

    Args:
        token: Malformed, negative, grouped or overflowing entered text.

    Returns:
        None; invalid text remains editable and produces no accepted notification.
    """
    view = JobDirectValues(
        MeasurementSystem.METRIC, Language.ENGLISH, DecimalConvention.POINT
    )
    view.load((JobRiskMeasurement(AssessmentKind.LIFFT, 0.1, 50),))
    changed = QSignalSpy(view.measurements_changed)
    field = view.fields[AssessmentKind.LIFFT]
    preview = QSignalSpy(view.preview_changed)
    field.setText(token)
    assert preview[-1] == [AssessmentKind.LIFFT, None]
    assert not view.accept_pending()
    assert not changed
    assert view.errors[AssessmentKind.LIFFT].text()
    with pytest.raises(ValueError):
        view.measurements()
    view.close()


def test_calculated_sources_are_read_only_and_exact() -> None:
    """A calculated result cannot be overwritten through the optional direct field.

    Args:
        None.

    Returns:
        None; selecting tools and reading values cannot change the retained source.
    """
    view = JobDirectValues(
        MeasurementSystem.METRIC, Language.SPANISH, DecimalConvention.COMMA
    )
    source = LifftDraft(MeasurementSystem.METRIC, (LifftTask("t", 30, 49, 100),))
    original = calculate_job_measurement("p", "j", source, MeasurementSystem.METRIC)
    view.load((original,))
    assert view.fields[AssessmentKind.LIFFT].isReadOnly()
    view.select_kind(AssessmentKind.DUET)
    assert view.currentIndex() == 1
    assert view.measurements() == (original,)
    view.close()

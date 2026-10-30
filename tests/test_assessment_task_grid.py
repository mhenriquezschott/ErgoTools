"""Shared-grid ownership, replacement and read-only preview contracts.

Test layer. Controls run without repositories, presenters or calculators. Completing
cells reports identities without accepting data. Integration suites cover Main/Job
units, results, saving and shared history through their existing adapters.
"""

from dataclasses import replace
from unittest.mock import patch

import pytest
from PyQt5 import sip
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QComboBox

from ergotools.application.job_calculation import blank_job_source
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.assessment_task_grid import (
    AssessmentCellEdit,
    AssessmentTaskGrid,
)
from ergotools.presentation.desktop.precision_editor import PrecisionLineEdit

# Retain Qt for pure presentation-contract tests; no operational project is opened.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("kind", list(AssessmentKind))
@pytest.mark.parametrize("worker_layout", (False, True))
def test_completed_cells_report_identity_without_accepting_source(
    kind: AssessmentKind, worker_layout: bool
) -> None:
    """Both layouts emit exact cell identities and leave acceptance to their host.

    Args:
        kind: All three tools and their distinct numeric/selector columns.
        worker_layout: Main geometry or Job geometry on the same reusable component.

    Returns:
        None; selectors and numeric completion create no source replacement themselves.
    """
    source = blank_job_source(kind, MeasurementSystem.METRIC)
    grid = AssessmentTaskGrid(
        Language.ENGLISH,
        DecimalConvention.POINT,
        kind=kind,
        worker_layout=worker_layout,
    )
    finished: list[AssessmentCellEdit] = []
    grid.cell_finished.connect(finished.append)
    try:
        grid.load_source(source)
        number = grid.inputs[0][-1]
        assert isinstance(number, PrecisionLineEdit)
        number.setText("123")
        number.editingFinished.emit()
        assert finished == [
            AssessmentCellEdit(source.tasks[0].task_id, "repetitions", "123")
        ]
        assert source.tasks[0].repetitions is None
        assert grid.source is source
        if kind is not AssessmentKind.LIFFT:
            selector = grid.inputs[0][0]
            assert isinstance(selector, QComboBox)
            selector.setCurrentIndex(1)
            assert finished[-1] == AssessmentCellEdit(
                source.tasks[0].task_id,
                "omni_res_scale" if kind is AssessmentKind.DUET else "direction",
                selector.currentData(),
            )
        assert grid.source is source
    finally:
        grid.close()
        grid.deleteLater()
        _APP.processEvents()


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_retired_controls_cannot_complete_against_replacement_source(
    kind: AssessmentKind,
) -> None:
    """Delayed events from replaced controls cannot acquire the new task identity.

    Args:
        kind: Each ergonomic input layout, including rating/direction selectors.

    Returns:
        None; only the new projection can report subsequent cell completion.
    """
    first = blank_job_source(kind, MeasurementSystem.METRIC)
    second = replace(first, tasks=(replace(first.tasks[0], task_id="replacement"),))
    grid = AssessmentTaskGrid(Language.ENGLISH, DecimalConvention.POINT, kind=kind)
    finished: list[AssessmentCellEdit] = []
    grid.cell_finished.connect(finished.append)
    try:
        grid.load_source(first)
        old_number = grid.inputs[0][-1]
        assert isinstance(old_number, PrecisionLineEdit)
        old_selector = grid.inputs[0][0]
        grid.load_source(second)
        old_number.editingFinished.emit()
        if isinstance(old_selector, QComboBox):
            old_selector.setCurrentIndex(1)
        assert finished == []
        current = grid.inputs[0][-1]
        assert isinstance(current, PrecisionLineEdit)
        current.editingFinished.emit()
        assert finished == [AssessmentCellEdit("replacement", "repetitions", "")]
    finally:
        grid.close()
        grid.deleteLater()
        _APP.processEvents()


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_read_only_selection_never_emits_task_edits(kind: AssessmentKind) -> None:
    """Compact preview selection stays independent of scientific input acceptance.

    Args:
        kind: Each tool in its compact copy-preview presentation.

    Returns:
        None; copy checkboxes operate while source controls remain read-only.
    """
    source = blank_job_source(kind, MeasurementSystem.METRIC)
    grid = AssessmentTaskGrid(
        Language.SPANISH,
        DecimalConvention.COMMA,
        kind=kind,
        read_only=True,
        selectable=True,
        compact=True,
    )
    finished: list[AssessmentCellEdit] = []
    grid.cell_finished.connect(finished.append)
    try:
        grid.load_source(source)
        number = grid.inputs[0][-1]
        assert isinstance(number, PrecisionLineEdit) and number.isReadOnly()
        number.editingFinished.emit()
        grid.set_task_selection(())
        assert grid.selected_task_ids() == ()
        grid.set_task_selection((source.tasks[0].task_id,))
        assert grid.selected_task_ids() == (source.tasks[0].task_id,)
        assert finished == [] and grid.source is source
    finally:
        grid.close()
        grid.deleteLater()
        _APP.processEvents()


def test_queued_geometry_respects_destroyed_widget_lifetime() -> None:
    """A queued layout callback cannot access children after native widget deletion.

    Args:
        None.

    Returns:
        None; no exception escapes a Qt callback after the grid is destroyed.
    """
    grid = AssessmentTaskGrid(Language.ENGLISH, DecimalConvention.POINT)
    grid.refresh_geometry()
    sip.delete(grid)
    with patch("sys.excepthook") as errors:
        QTest.qWait(10)
    errors.assert_not_called()

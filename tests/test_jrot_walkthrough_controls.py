"""Guided picker filters, readable tables and visible shared-grid copy ranges.

Test layer. Native controls use detached catalogs or disposable projects; no maintained
fixture or personal preference is changed. Scientific values use the existing formatter.
"""

import csv
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QDialog

from ergotools.application.assessment_clipboard import (
    assessment_clipboard_text,
    assessment_input_fields,
    prepare_assessment_paste,
)
from ergotools.application.job_calculation import blank_job_source
from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.assessment_task_actions import AssessmentTaskActions
from ergotools.presentation.desktop.assessment_task_grid import AssessmentTaskGrid
from ergotools.presentation.desktop.jrot_catalog_picker import (
    JrotCatalogChoice,
    JrotCatalogPicker,
)
from tests.test_jrot_guided_ui import dispose, populated_dialog

# Native ownership must remain alive through deferred child teardown.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("language", list(Language))
def test_worker_line_alphabet_search_preserve_hidden_checks(language: Language) -> None:
    """Line scope is a local filter; hidden selections stay explicit and reversible.

    Args:
        language: Both maintained picker languages.

    Returns:
        None; filtered All/None never changes hidden checks or source records.
    """
    parent = QDialog()
    choices = (
        JrotCatalogChoice("W01", ("W01", "Ruiz", "Ana", "Packing / Line A")),
        JrotCatalogChoice("W02", ("W02", "Silva", "Bruno", "Assembly"), in_scope=False),
        JrotCatalogChoice(
            "W03", ("W03", "Vega", "Carla", "No assignment"), in_scope=False
        ),
    )
    picker = JrotCatalogPicker(
        "Workers",
        ("ID", "Last name", "First name", "Workplace"),
        choices,
        ("W01", "W02"),
        language,
        parent,
        icons=load_icons(),
        entity_icon="worker",
        scope_label="Plant / Packing / Line A",
    )
    try:
        picker.show()
        _APP.processEvents()
        assert picker.tree.visualItemRect(picker.nodes["W01"]).height() >= 36
        assert not picker.nodes["W01"].isHidden()
        assert picker.nodes["W02"].isHidden()
        assert "2" in picker.count_label.text() and "1" in picker.count_label.text()
        assert not picker.alphabet.buttons["S"].isEnabled()
        picker.scope_filter.setCurrentIndex(1)
        assert picker.alphabet.buttons["S"].isEnabled()
        picker.alphabet.buttons["S"].click()
        assert picker.nodes["W01"].isHidden() and not picker.nodes["W02"].isHidden()
        picker.check_visible(False)
        assert picker.nodes["W01"].checkState(0) == Qt.Checked
        picker.alphabet.buttons["All"].click()
        picker.search.setText("Carla")
        picker.check_visible(True)
        picker.accept_selection()
        assert picker.selected == ("W01", "W03")
        assert picker.tree.header().font().bold()
        assert picker.tree.header().height() >= 42
        assert picker.tree.columnWidth(0) >= 80
    finally:
        picker.close()
        parent.deleteLater()
        _APP.processEvents()


@pytest.mark.parametrize("kind", list(AssessmentKind))
@pytest.mark.parametrize("worker_layout", [False, True])
def test_shift_click_highlights_and_copies_exact_visible_input_rectangle(
    kind: AssessmentKind, worker_layout: bool
) -> None:
    """Shared Main/Job layouts copy only explicit selected inputs without data edits.

    Args:
        kind: All three tool schemas, including numeric and selector controls.
        worker_layout: Main layout or the Job/JROT instance of the same grid.

    Returns:
        None; precision, source identity, native text copy and Escape remain intact.
    """
    source = blank_job_source(kind, MeasurementSystem.METRIC)
    fields = assessment_input_fields(source)
    rows = (
        (("Trim", "2", "100"), ("Pack", "4", "200"))
        if kind is AssessmentKind.DUET
        else (
            ("Trim", "Handling Load", "30.123456789", "49.05", "100"),
            ("Pack", "Horizontal Push/Pull", "20", "10", "200"),
        )
        if kind is AssessmentKind.TST
        else (("Trim", "30.123456789", "49.05", "100"), ("Pack", "20", "10", "200"))
    )
    source = prepare_assessment_paste(source, rows, fields)
    grid = AssessmentTaskGrid(
        Language.ENGLISH,
        DecimalConvention.POINT,
        kind=kind,
        worker_layout=worker_layout,
    )
    controller = AssessmentTaskActions(
        grid,
        source=lambda: source,
        accept=lambda *_args: False,
        accept_paste=lambda *_args: False,
        definitions=lambda: (),
        replace_definitions=lambda *_args: None,
        before_action=lambda: True,
        system=lambda: MeasurementSystem.METRIC,
        convention=lambda: DecimalConvention.POINT,
    )
    try:
        grid.resize(1300, 500)
        grid.load_source(source)
        grid.show()
        _APP.processEvents()
        first = grid.inputs[0][1 if kind is not AssessmentKind.LIFFT else 0]
        last = grid.inputs[1][-1]
        QTest.mouseClick(first, Qt.LeftButton)
        QTest.mouseClick(last, Qt.LeftButton, Qt.ShiftModifier)
        selection = grid.selected_cell_range()
        assert selection is not None and selection[0] == (0, 1)
        assert first.property("taskRangeSelected") is True
        assert last.property("taskRangeSelected") is True
        assert grid.task_names[0].property("taskRangeSelected") is not True
        QTest.keyClick(first, Qt.Key_C, Qt.ControlModifier)
        clip = QApplication.clipboard().text()
        copied = list(csv.reader(StringIO(clip), delimiter="\t"))
        assert len(copied) == 3 and len(copied[0]) == len(selection[1])
        assert "Task name" not in copied[0]
        if kind is not AssessmentKind.DUET:
            assert copied[1][0] == "30.123456789"
        assert grid.source == source
        grid.load_source(source)
        assert grid.selected_cell_range() == selection
        QTest.keyClick(grid.inputs[0][-1], Qt.Key_Escape)
        assert grid.selected_cell_range() is None
        controller.copy()
        assert QApplication.clipboard().text() == assessment_clipboard_text(
            source, (), DecimalConvention.POINT, MeasurementSystem.METRIC
        )
        text = grid.inputs[0][-1]
        text.setFocus()
        text.selectAll()
        QTest.keyClick(text, Qt.Key_C, Qt.ControlModifier)
        assert QApplication.clipboard().text() == text.text()
    finally:
        grid.close()
        grid.deleteLater()
        _APP.processEvents()


@pytest.mark.parametrize("language", list(Language))
def test_guided_worker_manager_and_full_block_headers(
    tmp_path: Path, language: Language
) -> None:
    """Step 03 opens the existing editor and setup names refer to one selected record.

    Args:
        tmp_path: Private native project only.
        language: Both current guided interface languages.

    Returns:
        None; visiting worker management never invents participating workers.
    """
    dialog = populated_dialog(tmp_path, language)
    try:
        before = dialog.current()
        with patch(
            "ergotools.presentation.desktop.jrot_dialog.WorkerManagementDialog"
        ) as factory:
            dialog.open_workers()
            factory.return_value.exec.assert_called_once()
        assert dialog.current() == before
        assert "01" in dialog.scenarios.itemText(0)
        assert dialog.name.text() == before.name
        heading = dialog.matrix.horizontalHeaderItem(1).text()
        assert heading.startswith(
            "Block " if language is Language.ENGLISH else "Bloque "
        )
        assert dialog.matrix.horizontalHeader().font().bold()
        assert dialog.matrix.rowHeight(0) >= 36
        assert dialog.jobs_table.columnCount() == 6
        assert dialog.workers_table.columnCount() == 5
    finally:
        dispose(dialog)


def test_job_summary_uses_exact_risk_and_refreshes_after_calculation(
    tmp_path: Path,
) -> None:
    """Rounded display text cannot move a Job across a risk-band boundary.

    Args:
        tmp_path: Private guided project; no maintained Job values are replaced.

    Returns:
        None; the new summary refreshes when source results change without rebinding
        active calculator controls or deriving a color from rounded text.
    """
    from ergotools.domain.job_risk import JobRiskMeasurement, JobRiskValues
    from ergotools.domain.risk import classify_probability
    from ergotools.presentation.desktop.theme.risk import RISK_APPEARANCES

    dialog = populated_dialog(tmp_path)
    try:
        job = dialog.workspace.read_jobs().jobs.jobs[0]
        probability = 25.000001
        dialog.workspace.save_job_details(
            dialog.workspace.read_jobs(),
            dialog.workspace.read_job_risk(),
            job,
            JobRiskValues(
                job.job_id, (JobRiskMeasurement(AssessmentKind.LIFFT, 1, probability),)
            ),
        )
        dialog.job_changed()
        cell = dialog.jobs_table.item(0, 3)
        assert cell.text() == "25.0%"
        assert (
            cell.background().color().name().upper()
            == RISK_APPEARANCES[classify_probability(probability)].color_hex.upper()
        )
    finally:
        dispose(dialog)

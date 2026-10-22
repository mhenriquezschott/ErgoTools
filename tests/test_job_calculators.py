"""Native Job mini-calculators, independent worker copies and shared project replay.

Test layer. Drive the owned controls against private native projects; assert exact
sources/results before and after the sole durable Save. No reference/user file isedited.
"""

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.saved_results import calculate_saved_result
from ergotools.application.session import DocumentKey
from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.job_assessment_dialog import JobAssessmentDialog
from ergotools.presentation.desktop.job_management_dialog import JobManagementDialog
from tests.test_unified_project_save import editing_workspace
from tests.test_workplace_assignment_workflow import open_private, seed_workplace_source

# Retain Qt lifetime until every owned test dialog is closed.
_APP = QApplication.instance() or QApplication([])


def enter_job(dialog: JobManagementDialog) -> None:
    """Accept a real Job without inventing required risk data.

    Args:
        dialog: Native Job window borrowing a private project session.

    Returns:
        None; Job metadata becomes one accepted shared-history edit.
    """
    dialog.new_job()
    dialog.job_id_combo.setEditText("J1")
    dialog.job_name_input.setText("Assembly")
    assert dialog.accept_pending_job()


@pytest.mark.parametrize("kind", list(AssessmentKind))
@pytest.mark.parametrize("units", list(MeasurementSystem))
def test_calculator_inputs_calculate_clear_and_save(
    tmp_path: Path, kind: AssessmentKind, units: MeasurementSystem
) -> None:
    """Each mini-tool uses normal science, keeps inputs and needs only main Save.

    Args:
        tmp_path: Disposable project/preference directory.
        kind: Each ergonomic tool.
        units: Explicit metric/imperial input interpretation.

    Returns:
        None; exact sources/results and clearing/replay survive native reopen.
    """
    workspace = editing_workspace(tmp_path)
    path = Path(workspace.location)
    before = path.read_bytes()
    dialog = JobManagementDialog(workspace, load_icons(), units)
    try:
        enter_job(dialog)
        dialog.calculator_toggle.setChecked(True)
        dialog.tool_tabs.setCurrentIndex(list(AssessmentKind).index(kind))
        dialog.mode_combo.setCurrentIndex(1)
        editor = dialog.editors[kind]
        fields = editor.inputs[0]
        if kind is AssessmentKind.DUET:
            fields[0].setCurrentIndex(fields[0].findData(6))
            fields[1].setText("100")
            fields[1].editingFinished.emit()
        else:
            numeric = fields[1:] if kind is AssessmentKind.TST else fields
            for field, value in zip(numeric, ("30", "49.05", "100"), strict=True):
                field.setText(value)
                field.editingFinished.emit()
        source = dialog._measurement(kind).source
        assert source is not None
        assert not dialog._measurement(kind).complete
        expected = calculate_saved_result(
            DocumentKey(dialog._jobs.jobs.project_id, "oracle"), source, units
        )
        dialog.calculate_tool()
        calculated = dialog._measurement(kind)
        assert calculated.source == source and calculated.complete
        assert calculated.cumulative_damage == expected.damage
        assert calculated.probability_percent == expected.probability_percent
        assert [
            (r.moment, r.damage, r.share_percent) for r in calculated.task_results
        ] == [(r.moment, r.damage, r.share_percent) for r in expected.tasks]
        row = list(AssessmentKind).index(kind)
        assert not dialog.risk_table.item(row, 1).flags() & Qt.ItemIsEditable
        assert path.read_bytes() == before
        with patch.object(dialog, "_question", return_value=QMessageBox.No):
            dialog.clear_tool()
        assert dialog._measurement(kind) == calculated
        with patch.object(dialog, "_question", return_value=QMessageBox.Yes):
            dialog.clear_tool()
        assert not dialog._measurement(kind).complete
        assert len(dialog._measurement(kind).source.tasks) == 1
        assert workspace.editing.replay(redo=False)
        assert dialog._measurement(kind) == calculated
        assert workspace.editing.replay(redo=True)
        assert not dialog._measurement(kind).complete
        assert workspace.editing.replay(redo=False)
        dialog.close()
        assert workspace.save()
        with AssessmentProjectFile.open(path) as reopened:
            assert reopened.load_job_risk().for_job("J1").measurements == (calculated,)
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_numeric_cells_replay_individually_and_repeatedly(tmp_path: Path) -> None:
    """Lever arm and load are separate steps across repeated Undo/edit/Redo cycles.

    Args:
        tmp_path: Disposable project directory.

    Returns:
        None; expanding/removing rows retains source identities and entered data.
    """
    workspace = editing_workspace(tmp_path)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:
        enter_job(dialog)
        dialog.calculator_toggle.setChecked(True)
        dialog.mode_combo.setCurrentIndex(1)
        for _ in range(2):
            fields = dialog.editors[AssessmentKind.LIFFT].inputs[0]
            fields[0].setText("50")
            fields[0].editingFinished.emit()
            fields[1].setText("60")
            fields[1].editingFinished.emit()
            assert workspace.editing.replay(redo=False)
            task = dialog._measurement(AssessmentKind.LIFFT).source.tasks[0]
            assert task.lever_arm == 50 and task.load is None
            assert workspace.editing.replay(redo=False)
            task = dialog._measurement(AssessmentKind.LIFFT).source.tasks[0]
            assert task.lever_arm is None and task.load is None
            assert workspace.editing.replay(redo=True)
            assert workspace.editing.replay(redo=True)
            assert workspace.editing.replay(redo=False)
            assert workspace.editing.replay(redo=False)
        fields = dialog.editors[AssessmentKind.LIFFT].inputs[0]
        fields[0].setText("30")
        fields[0].editingFinished.emit()
        retained = dialog._measurement(AssessmentKind.LIFFT).source.tasks[0]
        dialog.add_task()
        assert dialog._measurement(AssessmentKind.LIFFT).source.tasks[0] == retained
        dialog.editors[AssessmentKind.LIFFT].setCurrentCell(0, 0)
        with patch.object(dialog, "_question", return_value=QMessageBox.No):
            dialog.remove_task()
        assert len(dialog._measurement(AssessmentKind.LIFFT).source.tasks) == 2
        with patch.object(dialog, "_question", return_value=QMessageBox.Yes):
            dialog.remove_task()
        assert len(dialog._measurement(AssessmentKind.LIFFT).source.tasks) == 1
        assert workspace.editing.replay(redo=False)
        assert dialog._measurement(AssessmentKind.LIFFT).source.tasks[0] == retained
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("kind", list(AssessmentKind))
@pytest.mark.parametrize("assigned", (False, True, "job"))
def test_worker_copy_retains_tasks_results_and_independent_ownership(
    tmp_path: Path, kind: AssessmentKind, assigned: bool | str
) -> None:
    """The actual picker copies exact source/output without worker navigation or links.

    Args:
        tmp_path: Disposable native project directory.
        kind: Each supported worker calculator.
        assigned: Standalone, unclassified workplace and Job-assigned source variants.

    Returns:
        None; later Job task edits leave worker inputs, outputs and ownership unchanged.
    """
    path = seed_workplace_source(tmp_path, kind)
    if assigned:
        with AssessmentProjectFile.open(path) as project:
            workplace = project.load_hierarchy().work.available_workplaces()[0]
            placement_id = None
            if assigned == "job":
                from ergotools.domain.job_catalog import Job, JobCatalog, JobPlacement

                project.save_jobs(
                    JobCatalog(
                        project.metadata.project_id,
                        (Job("J-Source", "Source Job"),),
                        (JobPlacement(1, "J-Source", workplace),),
                    )
                )
                placement_id = 1
            project.associate_assessment_at_workplace(
                "source",
                workplace,
                placement_id,
                effective_date=date(2026, 10, 20),
            )
    workspace = open_private(path)
    active = workspace.active
    source = workspace.assessment_source("source")
    expected = workspace.job_measurement_from_assessment("source")
    original_history = workspace.read_history().history
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:
        enter_job(dialog)
        dialog.tool_tabs.setCurrentIndex(list(AssessmentKind).index(kind))

        def use_source() -> None:
            """Select the only eligible worker source in the owned modal picker.

            Args:
                None.

            Returns:
                None; the dialog accepts without performing any calculation.
            """
            picker = _APP.activeModalWidget()
            assert isinstance(picker, JobAssessmentDialog)
            assert picker.table.rowCount() == 1
            assert ("Standalone" in picker.table.item(0, 1).text()) == (
                not bool(assigned)
            )
            if assigned == "job":
                assert "J-Source - Source Job" in picker.table.item(0, 1).text()
            elif assigned:
                assert "No Job" in picker.table.item(0, 1).text()
            picker.table.selectRow(0)
            picker.use_button.click()

        QTimer.singleShot(0, use_source)
        with patch(
            "ergotools.application.job_calculation.calculate_saved_result",
            side_effect=AssertionError("Copy must not calculate"),
        ):
            dialog.copy_worker_assessment()
        assert dialog._measurement(kind) == expected
        assert workspace.active is active
        assert workspace.assessment_source("source") == source
        assert workspace.read_history().history == original_history
        # Refresh controller authorities after an explicit independent history read.
        dialog._jobs = workspace.read_jobs()
        dialog._risk = workspace.read_job_risk()
        dialog.add_task()
        assert not dialog._measurement(kind).complete
        assert workspace.assessment_source("source") == source
        assert workspace.job_measurement_from_assessment("source") == expected
        assert workspace.editing.replay(redo=False)
        assert dialog._measurement(kind) == expected
        dialog.close()
        assert workspace.save()
        with AssessmentProjectFile.open(path) as reopened:
            assert reopened.load_job_risk().for_job("J1").measurements == (expected,)
            assert reopened.load_history() == original_history
            assert (
                reopened.load(DocumentKey(reopened.metadata.project_id, "source"))
                == source
            )
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("convention", list(DecimalConvention))
def test_locale_display_preserves_exact_outputs_and_replacement_cancel(
    tmp_path: Path, language: Language, convention: DecimalConvention
) -> None:
    """Rounded summaries preserve exact copied output; cancellation retains all tasks.

    Args:
        tmp_path: Disposable project directory.
        language: English or Spanish wording.
        convention: Independent application decimal mark.

    Returns:
        None; metadata acceptance does not round copied scientific values.
    """
    workspace = open_private(seed_workplace_source(tmp_path, AssessmentKind.LIFFT))
    expected = workspace.job_measurement_from_assessment("source")
    dialog = JobManagementDialog(
        workspace,
        load_icons(),
        MeasurementSystem.METRIC,
        language=language,
        convention=convention,
    )
    try:
        enter_job(dialog)
        dialog._set_measurement(expected)
        original = dialog._measurement(AssessmentKind.LIFFT)
        text = dialog.risk_table.item(0, 2).text()
        assert text == f"{expected.probability_percent:.1f}".replace(
            ".", convention.value
        )
        dialog.job_name_input.setText("Renamed")
        assert dialog.accept_pending_job()
        assert dialog._measurement(AssessmentKind.LIFFT) == original
        with patch.object(dialog, "_question", return_value=QMessageBox.No):
            dialog.mode_combo.setCurrentIndex(0)
        assert dialog._measurement(AssessmentKind.LIFFT) == original
        with patch.object(dialog, "_question", return_value=QMessageBox.Yes):
            dialog.mode_combo.setCurrentIndex(0)
        assert dialog._measurement(AssessmentKind.LIFFT).source is None
        assert workspace.editing.replay(redo=False)
        assert dialog._measurement(AssessmentKind.LIFFT) == original
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("kind", list(AssessmentKind))
@pytest.mark.parametrize("convention", list(DecimalConvention))
def test_fractional_repetitions_survive_copy_focus_and_edit(
    tmp_path: Path, kind: AssessmentKind, convention: DecimalConvention
) -> None:
    """Unchanged rounded repetition text never truncates an exact copied quantity.

    Args:
        tmp_path: Disposable native project directory.
        kind: Each compact calculator.
        convention: Explicit point/comma numeric policy.

    Returns:
        None; new fractional input follows the existing model's float semantics.
    """
    from dataclasses import replace

    from ergotools.application.job_calculation import calculate_job_measurement
    from tests.test_optional_assessment_context import source_for

    workspace = editing_workspace(tmp_path)
    dialog = JobManagementDialog(
        workspace, load_icons(), MeasurementSystem.METRIC, convention=convention
    )
    try:
        enter_job(dialog)
        dialog.tool_tabs.setCurrentIndex(list(AssessmentKind).index(kind))
        source = source_for(kind)
        source = replace(source, tasks=(replace(source.tasks[0], repetitions=100.5),))
        expected = calculate_job_measurement(
            dialog._jobs.jobs.project_id, "J1", source, MeasurementSystem.METRIC
        )
        dialog._set_measurement(expected)
        field = dialog.editors[kind].inputs[0][-1]
        field.editingFinished.emit()
        assert dialog.accept_pending_job()
        assert dialog._measurement(kind) == expected
        field.setText("100.25".replace(".", convention.value))
        field.editingFinished.emit()
        changed = dialog._measurement(kind)
        assert changed.source.tasks[0].repetitions == 100.25
        assert not changed.complete and not changed.task_results
        assert workspace.editing.replay(redo=False)
        assert dialog._measurement(kind) == expected
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_reopened_task_edit_enables_shared_undo_before_focus_leaves(
    tmp_path: Path,
) -> None:
    """A reopened calculator's first keystrokes expose the same pending Undo action.

    Args:
        tmp_path: Disposable project and settings directory.

    Returns:
        None; per-cell acceptance and replay restore the original calculated values.
    """
    from PyQt5.QtTest import QTest

    from ergotools.domain.job_catalog import Job
    from ergotools.domain.job_risk import JobRiskValues

    path = seed_workplace_source(tmp_path, AssessmentKind.LIFFT)
    with AssessmentProjectFile.open(path) as project:
        from ergotools.application.job_calculation import job_measurement_from_result
        from ergotools.application.saved_results import stored_result

        key = DocumentKey(project.metadata.project_id, "source")
        source = project.load(key)
        expected = job_measurement_from_result(
            source, stored_result(project, key, source)
        )
        project.save_job_details(
            project.load_jobs(),
            project.load_job_risk(),
            Job("J1", "Assembly"),
            JobRiskValues("J1", (expected,)),
        )
    workspace = open_private(path)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:
        dialog.show()
        _APP.setActiveWindow(dialog)
        dialog.calculator_toggle.setChecked(True)
        _APP.processEvents()
        assert _APP.activeWindow() is dialog
        assert not dialog.project_history.undo_button.isEnabled()
        field = dialog.editors[AssessmentKind.LIFFT].inputs[0][0]
        field.setFocus()
        field.selectAll()
        QTest.keyClicks(field, "50")
        assert dialog.project_history.undo_button.isEnabled()
        assert dialog.accept_pending_job()
        assert workspace.editing.replay(redo=False)
        assert dialog._measurement(AssessmentKind.LIFFT) == expected
        dialog.add_task()
        editor = dialog.editors[AssessmentKind.LIFFT]
        second = editor.inputs[1][0]
        second.setFocus()
        _APP.processEvents()
        assert editor.currentRow() == 1
        dialog.remove_task()
        assert (
            dialog._measurement(AssessmentKind.LIFFT).source.tasks
            == expected.source.tasks
        )
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_direct_damage_delegate_exposes_pending_undo_and_commits_once(
    tmp_path: Path,
) -> None:
    """Typing into a direct damage cell enables Undo before the native editor closes.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; accepting and undoing the cell restores the previous exact current value.
    """
    from PyQt5.QtTest import QTest
    from PyQt5.QtWidgets import QLineEdit

    from ergotools.domain.job_catalog import Job
    from ergotools.domain.job_risk import JobRiskMeasurement, JobRiskValues

    path = seed_workplace_source(tmp_path, AssessmentKind.LIFFT)
    original = JobRiskMeasurement(AssessmentKind.LIFFT, 0.1, 50, "Metric")
    with AssessmentProjectFile.open(path) as project:
        project.save_job_details(
            project.load_jobs(),
            project.load_job_risk(),
            Job("J1", "Assembly"),
            JobRiskValues("J1", (original,)),
        )
    workspace = open_private(path)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:
        dialog.show()
        _APP.processEvents()
        assert not dialog.project_history.undo_button.isEnabled()
        cell = dialog.risk_table.item(0, 1)
        dialog.risk_table.editItem(cell)
        _APP.processEvents()
        field = dialog.risk_table.findChild(QLineEdit)
        assert field is not None
        field.selectAll()
        QTest.keyClicks(field, "0.2")
        assert dialog.project_history.undo_button.isEnabled()
        assert dialog.accept_pending_job()
        assert dialog._measurement(AssessmentKind.LIFFT).cumulative_damage == 0.2
        assert workspace.editing.replay(redo=False)
        assert dialog._measurement(AssessmentKind.LIFFT) == original
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_missing_job_id_never_discards_entered_task_data(tmp_path: Path) -> None:
    """A missing Job ID cannot silently discard entered task data.

    Args:
        tmp_path: Disposable project directory.

    Returns:
        None; correction restores acceptance with the original exact task source.
    """
    workspace = editing_workspace(tmp_path)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:
        assert not dialog.risk_table.isEnabled()
        assert not dialog.calculator_toggle.isEnabled()
        enter_job(dialog)
        dialog.calculator_toggle.setChecked(True)
        dialog.mode_combo.setCurrentIndex(1)
        field = dialog.editors[AssessmentKind.LIFFT].inputs[0][0]
        field.setText("30")
        field.editingFinished.emit()
        retained = dialog._measurement(AssessmentKind.LIFFT).source
        dialog.job_id_combo.setEditText("")
        with patch.object(dialog, "_warning") as warning:
            assert not dialog.accept_pending_job()
            warning.assert_called_once()
        assert dialog._measurement(AssessmentKind.LIFFT).source == retained
        dialog.job_id_combo.setEditText("J1")
        assert dialog.accept_pending_job()
        assert dialog._measurement(AssessmentKind.LIFFT).source == retained
    finally:
        dialog.job_id_combo.setEditText("J1")
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)

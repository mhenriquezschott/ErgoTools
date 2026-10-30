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
        dialog.tool_tabs.setCurrentIndex(list(AssessmentKind).index(kind))
        dialog.input_modes.button(1).click()
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
        assert dialog._measurement(kind).complete
        expected = calculate_saved_result(
            DocumentKey(dialog._jobs.jobs.project_id, "oracle"), source, units
        )
        automatically_calculated = dialog._measurement(kind)
        revision = workspace.editing.history.revision
        dialog.calculate_tool()
        assert workspace.editing.history.revision == revision
        assert dialog._measurement(kind) == automatically_calculated
        calculated = dialog._measurement(kind)
        assert calculated.source == source and calculated.complete
        assert calculated.cumulative_damage == expected.damage
        assert calculated.probability_percent == expected.probability_percent
        assert [
            (r.moment, r.damage, r.share_percent) for r in calculated.task_results
        ] == [(r.moment, r.damage, r.share_percent) for r in expected.tasks]
        assert dialog.direct_values.fields[kind].isReadOnly()
        assert path.read_bytes() == before
        with patch.object(dialog, "_question", return_value=QMessageBox.No):
            dialog.clear_tool()
        assert dialog._measurement(kind) == calculated
        with patch.object(dialog, "_question", return_value=QMessageBox.Yes):
            dialog.clear_tool()
        assert not dialog._measurement(kind).complete
        assert dialog._measurement(kind).source is None
        assert dialog.editors[kind].task_count == 1
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
        dialog.input_modes.button(1).click()
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
            assert dialog._measurement(AssessmentKind.LIFFT).source is None
            preview = dialog.editors[AssessmentKind.LIFFT].source.tasks[0]
            assert preview.lever_arm is None and preview.load is None
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
        dialog.editors[AssessmentKind.LIFFT].select_task(0)
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
            candidate = picker.tree.currentItem().data(0, Qt.ItemDataRole.UserRole)
            assert candidate.identity == "source"
            assert ("Standalone assessment" in candidate.path) == (not bool(assigned))
            if assigned == "job":
                assert candidate.job == "J-Source · Source Job"
            elif assigned:
                assert candidate.job == "No Job"
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
        text = dialog.calculation_summary.summary.probability_value.text().removesuffix(
            "%"
        )
        assert text == f"{expected.probability_percent:.1f}".replace(
            ".", convention.value
        )
        dialog.job_name_input.setText("Renamed")
        assert dialog.accept_pending_job()
        assert dialog._measurement(AssessmentKind.LIFFT) == original
        with patch.object(dialog, "_question", return_value=QMessageBox.No):
            dialog.input_modes.button(0).click()
        assert dialog._measurement(AssessmentKind.LIFFT) == original
        with patch.object(dialog, "_question", return_value=QMessageBox.Yes):
            dialog.input_modes.button(0).click()
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
        assert changed == calculate_job_measurement(
            dialog._jobs.jobs.project_id, "J1", changed.source, MeasurementSystem.METRIC
        )
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
        assert editor.selected_task_index == 1
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
        cell = dialog.direct_values.fields[AssessmentKind.LIFFT]
        field = cell
        field.setFocus()
        _APP.processEvents()
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
        assert not dialog.direct_values.isEnabled()
        assert not dialog.assessment_area.isEnabled()
        enter_job(dialog)
        dialog.input_modes.button(1).click()
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


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_direct_to_tasks_starts_one_row_without_losing_cancelled_values(
    tmp_path: Path, kind: AssessmentKind
) -> None:
    """Direct-result replacement shows one starter and replays the original value.

    Args:
        tmp_path: Disposable native project directory.
        kind: Each Job tool, independent of other tool sources.

    Returns:
        None; Cancel preserves direct values; confirmed replacement and edits replay.
    """
    workspace = editing_workspace(tmp_path)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:
        enter_job(dialog)
        dialog.tool_tabs.setCurrentIndex(list(AssessmentKind).index(kind))
        dialog.input_modes.button(0).click()
        field = dialog.direct_values.fields[kind]
        field.setText("0.01")
        field.editingFinished.emit()
        original = dialog._measurement(kind)
        assert original.complete and original.source is None
        with patch.object(dialog, "_question", return_value=QMessageBox.No):
            dialog.input_modes.button(1).click()
        assert dialog._measurement(kind) == original
        assert dialog.input_modes.checkedId() == 0
        assert dialog.editors[kind].task_count == 0
        with patch.object(dialog, "_question", return_value=QMessageBox.Yes):
            dialog.input_modes.button(1).click()
        assert dialog.input_modes.checkedId() == 1
        assert dialog.editors[kind].task_count == 1
        assert not dialog._measurement(kind).complete
        assert workspace.editing.replay(redo=False)
        assert dialog._measurement(kind) == original
        assert dialog.editors[kind].task_count == 0
        assert workspace.editing.replay(redo=True)
        assert dialog.editors[kind].task_count == 1
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)

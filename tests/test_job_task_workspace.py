"""Task-first Job browsing, copied sources, selected-tool results and shared replay.

Test layer. Use private native projects and real presentation controls. Opening an
empty tool is read-only; explicit copied inputs/results remain independent and use
the existing main Save rather than a new storage path.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.gauge_preferences import GaugeMarkerSettings
from ergotools.application.job_calculation import calculate_job_measurement
from ergotools.application.settings import Language
from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.job_assessment_dialog import JobCopyDialog
from ergotools.presentation.desktop.job_management_dialog import JobManagementDialog
from tests.test_job_calculators import enter_job
from tests.test_unified_project_save import editing_workspace

# Retain one native application while private Job dialogs are constructed and closed.
_APP = QApplication.instance() or QApplication([])


def test_viewing_missing_tools_only_records_clean_navigation(tmp_path: Path) -> None:
    """Empty tool templates remain presentation state until an actual edit occurs.

    Args:
        tmp_path: Disposable project and preferences directory.

    Returns:
        None; the starter row creates no measurement or dirty edit from viewing tools.
    """
    workspace = editing_workspace(tmp_path)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:
        enter_job(dialog)
        assert workspace.save()
        before = Path(workspace.location).read_bytes()
        history = workspace.editing.history.revision
        for index, kind in enumerate(AssessmentKind):
            dialog.tool_tabs.setCurrentIndex(index)
            assert dialog.input_modes.checkedId() == 1
            assert dialog.editors[kind].task_count == 1
            assert dialog._measurement(kind).source is None
            assert not dialog.result_panel.risk_gauge.has_value
            dialog.input_modes.button(0).click()
            assert dialog.editors[kind].task_count == 0
            dialog.input_modes.button(1).click()
            assert dialog.editors[kind].task_count == 1
        assert dialog.accept_pending_job()
        assert not dialog.direct_values.measurements()
        assert workspace.editing.history.revision > history
        assert not workspace.editing.is_dirty
        assert Path(workspace.location).read_bytes() == before
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_copy_job_inputs_results_independence_replay_and_save(tmp_path: Path) -> None:
    """An explicit Job copy preserves exact values and is one reversible operation.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; later destination edits cannot change the original Job's tasks/results.
    """
    workspace = editing_workspace(tmp_path)
    path = Path(workspace.location)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:

        def select_job_copy() -> None:
            """Choose J1 through the real modal without writing its source data.

            Args:
                None.

            Returns:
                None; destination owns any subsequent replacement confirmation.
            """
            picker = QApplication.activeModalWidget()
            assert isinstance(picker, JobCopyDialog)
            picker.source_combo.setCurrentIndex(picker.source_combo.findData("J1"))
            picker.use_button.click()

        enter_job(dialog)
        source = LifftDraft(MeasurementSystem.METRIC, (LifftTask("t", 30, 49, 100),))
        original = calculate_job_measurement(
            dialog._jobs.jobs.project_id, "J1", source, MeasurementSystem.METRIC
        )
        dialog._set_measurement(original)
        dialog.new_job()
        dialog.job_id_combo.setEditText("J2")
        dialog.job_name_input.setText("Pallet loading")
        assert dialog.accept_pending_job()
        QTimer.singleShot(0, select_job_copy)
        with patch.object(
            dialog, "_warning", side_effect=AssertionError("Unexpected copy failure")
        ):
            dialog.copy_job_button.click()
        assert dialog._measurement(AssessmentKind.LIFFT) == original
        assert dialog.input_modes.checkedId() == 1
        assert (
            dialog.result_panel.risk_gauge.target_value == original.probability_percent
        )
        assert dialog.result_panel.damage_progress.has_value
        assert dialog.calculation_summary.summary.total_value.toolTip() == str(
            original.cumulative_damage
        )
        assert workspace.editing.replay(redo=False)
        assert dialog._measurement(AssessmentKind.LIFFT).source is None
        assert not dialog.result_panel.risk_gauge.has_value
        assert workspace.editing.replay(redo=True)
        assert dialog._measurement(AssessmentKind.LIFFT) == original
        field = dialog.editors[AssessmentKind.LIFFT].inputs[0][0]
        field.setText("45")
        field.editingFinished.emit()
        updated = dialog._measurement(AssessmentKind.LIFFT)
        assert updated.complete and updated != original
        assert (
            dialog.result_panel.risk_gauge.target_value == updated.probability_percent
        )
        assert (
            dialog.result_panel.damage_progress.target_value
            == updated.cumulative_damage
        )
        assert dialog.calculation_summary.summary.total_value.toolTip() == str(
            updated.cumulative_damage
        )
        assert workspace.read_job_risk().risk.for_job("J1").measurements == (original,)
        assert workspace.editing.replay(redo=False)
        assert dialog._measurement(AssessmentKind.LIFFT) == original
        QTimer.singleShot(0, select_job_copy)
        with patch.object(dialog, "_question", return_value=QMessageBox.No):
            dialog.copy_job_values()
        assert dialog._measurement(AssessmentKind.LIFFT) == original
        dialog.close()
        assert workspace.save()
        with AssessmentProjectFile.open(path) as project:
            risks = project.load_job_risk()
            assert risks.for_job("J1").measurements == (original,)
            assert risks.for_job("J2").measurements == (original,)
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_invalid_direct_input_stays_visible_on_tool_navigation(tmp_path: Path) -> None:
    """A failed tab change exposes the invalid field instead of hiding the error.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; correcting the field permits navigation and preserves entered values.
    """
    workspace = editing_workspace(tmp_path)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:
        enter_job(dialog)
        dialog.input_modes.button(0).click()
        field = dialog.direct_values.fields[AssessmentKind.LIFFT]
        field.setText("bad")
        dialog.tool_tabs.setCurrentIndex(1)
        assert dialog.tool_tabs.currentIndex() == 0
        assert field.text() == "bad"
        assert dialog.direct_values.errors[AssessmentKind.LIFFT].text()
        field.setText("0.001")
        dialog.tool_tabs.setCurrentIndex(1)
        assert dialog.tool_tabs.currentIndex() == 1
        assert dialog._measurement(AssessmentKind.LIFFT).cumulative_damage == 0.001
    finally:
        dialog.direct_values.fields[AssessmentKind.LIFFT].setText("0.001")
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_job_gauge_uses_personal_preferences_without_project_history(
    tmp_path: Path,
) -> None:
    """Marker changes update this shared gauge only after the preference owner accepts.

    Args:
        tmp_path: Disposable project directory; no personal settings are written.

    Returns:
        None; failed preference writes leave appearance and project history unchanged.
    """
    workspace = editing_workspace(tmp_path)
    observed: list[GaugeMarkerSettings] = []
    dialog = JobManagementDialog(
        workspace,
        load_icons(),
        MeasurementSystem.METRIC,
        change_gauge_markers=observed.append,
    )
    try:
        revision = workspace.editing.history.revision
        settings = GaugeMarkerSettings(interval=5)
        dialog._update_gauge_markers(settings)
        assert observed == [settings]
        assert dialog.result_panel.risk_gauge.marker_settings == settings
        assert workspace.editing.history.revision == revision
        with (
            patch.object(dialog, "_change_gauge_markers", side_effect=OSError("test")),
            patch.object(dialog, "_warning") as warning,
        ):
            dialog._update_gauge_markers(GaugeMarkerSettings(interval=20))
            warning.assert_called_once()
        assert dialog.result_panel.risk_gauge.marker_settings == settings
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_first_and_last_task_are_separate_reversible_job_actions(
    tmp_path: Path,
) -> None:
    """Starter rows are unsaved; adding/removing stored tasks replays exact results.

    Args:
        tmp_path: Private project directory; operational fixtures are never changed.

    Returns:
        None; creating, editing and removing the final row share project history.
    """
    workspace = editing_workspace(tmp_path)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:
        enter_job(dialog)
        assert dialog.editors[AssessmentKind.LIFFT].task_count == 1
        assert dialog._measurement(AssessmentKind.LIFFT).source is None
        assert dialog.add_task_button.isEnabled()
        dialog.add_task_button.click()
        assert dialog.editors[AssessmentKind.LIFFT].task_count == 2
        assert workspace.editing.replay(redo=False)
        assert dialog.editors[AssessmentKind.LIFFT].task_count == 1
        assert workspace.editing.replay(redo=True)
        dialog.editors[AssessmentKind.LIFFT].select_task(1)
        dialog.remove_task_button.click()
        fields = dialog.editors[AssessmentKind.LIFFT].inputs[0]
        for control, value in zip(fields, ("30", "49", "100"), strict=True):
            control.setText(value)
            control.editingFinished.emit()
        dialog.calculate_button.click()
        calculated = dialog._measurement(AssessmentKind.LIFFT)
        assert calculated.complete
        with patch.object(dialog, "_question", return_value=QMessageBox.Yes):
            dialog.remove_task_button.click()
        assert dialog.editors[AssessmentKind.LIFFT].task_count == 1
        assert not dialog.result_panel.risk_gauge.has_value
        assert workspace.editing.replay(redo=False)
        assert dialog._measurement(AssessmentKind.LIFFT) == calculated
        assert dialog.project_history.undo_action.iconText() == "Undo"
        assert dialog.project_history.undo_button.text() == "Undo"
        assert workspace.editing.replay(redo=True)
        assert dialog.editors[AssessmentKind.LIFFT].task_count == 1
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_job_tool_tabs_share_chronological_navigation_history(tmp_path: Path) -> None:
    """Job tool selection replays like main assessment selection without dirty data.

    Args:
        tmp_path: Private project directory.

    Returns:
        None; a tab change and a data edit remain distinct ordered Undo/Redo steps.
    """
    from PyQt5.QtCore import Qt
    from PyQt5.QtTest import QTest

    workspace = editing_workspace(tmp_path)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:
        enter_job(dialog)
        assert workspace.save()
        original = Path(workspace.location).read_bytes()
        dialog.show()
        _APP.setActiveWindow(dialog)
        _APP.processEvents()
        dialog.tool_tabs.setCurrentIndex(1)
        assert not workspace.editing.is_dirty
        QTest.mouseClick(dialog.project_history.undo_button, Qt.MouseButton.LeftButton)
        assert dialog.tool_tabs.currentIndex() == 0
        QTest.mouseClick(dialog.project_history.redo_button, Qt.MouseButton.LeftButton)
        assert dialog.tool_tabs.currentIndex() == 1
        dialog.add_task_button.click()
        assert dialog.editors[AssessmentKind.DUET].task_count == 2
        QTest.mouseClick(dialog.project_history.undo_button, Qt.MouseButton.LeftButton)
        assert dialog.editors[AssessmentKind.DUET].task_count == 1
        assert dialog.tool_tabs.currentIndex() == 1
        QTest.mouseClick(dialog.project_history.undo_button, Qt.MouseButton.LeftButton)
        assert dialog.tool_tabs.currentIndex() == 0
        assert not workspace.editing.is_dirty
        assert Path(workspace.location).read_bytes() == original
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_job_layout_aligns_damage_and_matches_main_titles(tmp_path: Path) -> None:
    """Native geometry keeps totals under Damage and row controls between actions.

    Args:
        tmp_path: Private project directory.

    Returns:
        None; all tools share full captions and alignment after tab/resize passes.
    """
    workspace = editing_workspace(tmp_path)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:
        enter_job(dialog)
        dialog.resize(1620, 940)
        dialog.show()
        captions = (
            "Lifting Fatigue Failure Tool (LiFFT)",
            "Distal Upper Extremity Tool (DUET)",
            "The Shoulder Tool (ST)",
        )
        for index, kind in enumerate(AssessmentKind):
            dialog.tool_tabs.setCurrentIndex(index)
            _APP.processEvents()
            _APP.processEvents()
            assert dialog.tool_tabs.tabText(index) == captions[index]
            damage = dialog.editors[kind].headers[-2]
            value = dialog.calculation_summary.summary.total_value
            area = dialog.assessment_area
            assert (
                abs(
                    value.mapTo(area, value.rect().topLeft()).x()
                    - damage.mapTo(area, damage.rect().topLeft()).x()
                )
                <= 2
            )
            assert value.width() == damage.width()
        assert dialog.clear_tool_button.x() < dialog.add_task_button.x()
        assert dialog.add_task_button.x() < dialog.remove_task_button.x()
        assert dialog.remove_task_button.x() < dialog.calculate_button.x()
        undo, redo = (
            dialog.project_history.undo_button,
            dialog.project_history.redo_button,
        )
        assert redo.x() - undo.geometry().right() <= 2
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_direct_input_uses_single_colored_summary_and_shared_history(
    tmp_path: Path,
) -> None:
    """Edit damage in its visible result cell and replay the accepted value exactly.

    Args:
        tmp_path: Disposable project/preferences directory.

    Returns:
        None; no duplicate form is visible and typing preview never accepts data.
    """
    from PyQt5.QtCore import Qt
    from PyQt5.QtTest import QTest

    workspace = editing_workspace(tmp_path)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:
        enter_job(dialog)
        dialog.show()
        dialog.activateWindow()
        dialog.input_modes.button(0).click()
        _APP.processEvents()
        summary = dialog.calculation_summary.summary
        field = dialog.direct_values.fields[AssessmentKind.LIFFT]
        assert field.isVisible()
        assert summary.total_value.isHidden()
        assert dialog.direct_values.parentWidget() is dialog.calculation_summary
        assert summary.itemAtPosition(0, 1).widget() is summary.total_value
        field.setFocus()
        QTest.keyClicks(field, "0.001")
        _APP.processEvents()
        assert dialog._measurement(AssessmentKind.LIFFT).cumulative_damage is None
        assert summary.probability_value.text() != "—"
        assert "background: #" in field.styleSheet()
        dialog.tool_status.setFocus()
        field.editingFinished.emit()
        assert dialog._measurement(AssessmentKind.LIFFT).cumulative_damage == 0.001
        history = dialog.project_history
        assert history is not None
        QTest.mouseClick(history.undo_button, Qt.MouseButton.LeftButton)
        assert dialog._measurement(AssessmentKind.LIFFT).cumulative_damage is None
        QTest.mouseClick(history.redo_button, Qt.MouseButton.LeftButton)
        assert dialog._measurement(AssessmentKind.LIFFT).cumulative_damage == 0.001
        field = dialog.direct_values.fields[AssessmentKind.LIFFT]
        field.setText("bad")
        assert summary.probability_value.text() == "—"
        field.setText("0.001")
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("language", list(Language))
def test_saved_job_selection_enables_clean_shared_replay(
    tmp_path: Path, language: Language
) -> None:
    """Dropdown/arrows replay selected Jobs after reopen, separately from pending edits.

    Args:
        tmp_path: Disposable native project; live projects are never written.
        language: Both localized history labels and native window projections.

    Returns:
        None; selections remain clean and replay matching details without file writes.
    """
    workspace = editing_workspace(tmp_path)
    seed = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    enter_job(seed)
    seed.new_job()
    seed.job_id_combo.setEditText("J2")
    seed.job_name_input.setText("Pallet loading")
    assert seed.accept_pending_job()
    seed.close()
    assert workspace.save()
    path = Path(workspace.location)
    workspace.close(choice=CloseChoice.DISCARD)
    workspace.switch(str(path), None)
    before = path.read_bytes()
    dialog = JobManagementDialog(
        workspace, load_icons(), MeasurementSystem.METRIC, language=language
    )
    try:
        dialog.show()
        _APP.setActiveWindow(dialog)
        _APP.processEvents()
        history = dialog.project_history
        assert history is not None
        assert dialog.selected_job_id == "J1"
        heading = (
            "Tasks & assessment"
            if language is Language.ENGLISH
            else "Tareas y evaluación"
        )
        assert dialog.assessment_heading.text() == heading + ": J1 - Assembly"
        assert not history.undo_action.isEnabled()
        dialog.job_id_combo.setFocus()
        QTest.keyClick(dialog.job_id_combo, Qt.Key.Key_Down)
        assert dialog.selected_job_id == "J2"
        assert dialog.job_name_input.text() == "Pallet loading"
        assert dialog.assessment_heading.text() == heading + ": J2 - Pallet loading"
        assert history.undo_action.isEnabled()
        assert not workspace.editing.is_dirty
        for _ in range(2):
            QTest.mouseClick(history.undo_button, Qt.MouseButton.LeftButton)
            assert dialog.selected_job_id == "J1"
            assert dialog.job_name_input.text() == "Assembly"
            assert dialog.assessment_heading.text() == heading + ": J1 - Assembly"
            assert not history.undo_action.isEnabled()
            QTest.mouseClick(history.redo_button, Qt.MouseButton.LeftButton)
            assert dialog.selected_job_id == "J2"
        dialog.first_job()
        assert dialog.selected_job_id == "J1"
        QTest.mouseClick(history.undo_button, Qt.MouseButton.LeftButton)
        assert dialog.selected_job_id == "J2"
        QTest.mouseClick(history.redo_button, Qt.MouseButton.LeftButton)
        assert dialog.selected_job_id == "J1"
        dialog.job_name_input.setText("Edited assembly")
        assert dialog.assessment_heading.text() == heading + ": J1 - Edited assembly"
        dialog.next_job()
        assert dialog.selected_job_id == "J2"
        QTest.mouseClick(history.undo_button, Qt.MouseButton.LeftButton)
        assert dialog.selected_job_id == "J1"
        assert dialog.job_name_input.text() == "Edited assembly"
        QTest.mouseClick(history.undo_button, Qt.MouseButton.LeftButton)
        assert dialog.selected_job_id == "J1"
        assert dialog.job_name_input.text() == "Assembly"
        assert not workspace.editing.is_dirty
        assert path.read_bytes() == before
        dialog.next_job()
        with (
            patch.object(dialog, "_question", return_value=QMessageBox.Yes),
            patch.object(dialog, "_information"),
        ):
            dialog.delete_job()
        assert dialog.selected_job_id == "J1"
        assert workspace.editing.replay(redo=False)
        assert dialog.selected_job_id == "J2"
        assert workspace.editing.replay(redo=True)
        assert dialog.selected_job_id == "J1"
        assert path.read_bytes() == before
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)

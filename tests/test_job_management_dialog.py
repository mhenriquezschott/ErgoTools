"""Integrated original Job Management controls over synthetic real projects.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import os
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QDialog, QLineEdit, QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.bootstrap import create_job_management_demo, load_icons
from ergotools.domain.assessments.document import AssessmentDraft, AssessmentKind
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.settings_store import JsonSettingsStore
from ergotools.presentation.desktop.job_management_dialog import JobManagementDialog
from ergotools.presentation.desktop.job_workplace_dialog import JobWorkplaceDialog
from tests.test_workspace_job_risk import workspace_at

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


def enter_new(dialog: JobManagementDialog, identity: str = "assembly") -> None:
    """Enter one complete job form through visible controls.

    Args:
        dialog: Live modal/form under test; the caller owns its lifetime and event-loop
            scheduling.
        identity: Exact saved worker/task/scheme identity or deliberately malformed
            boundary value.

    Returns:
        None.
    """
    dialog.new_button.click()
    dialog.job_id_combo.setEditText(identity)
    dialog.job_name_input.setText("Assembly")
    dialog.input_modes.button(0).click()
    cell = dialog.direct_values.fields[AssessmentKind.LIFFT]
    assert cell is not None
    cell.setText("1")
    cell.editingFinished.emit()


def test_create_current_values_and_reopen(tmp_path: Path) -> None:
    """One Job/tool value stays editable without profile creation or approval steps.

    Args:
        tmp_path: Disposable project and settings directory.

    Returns:
        None; reopening restores the same single current value set.
    """
    workspace = workspace_at(tmp_path)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.IMPERIAL)
    try:
        enter_new(dialog)
        dialog.save_button.click()
        assert dialog.selected_job_id == "assembly"
        assert not hasattr(dialog, "profile_combo")
        dialog.direct_values.fields[AssessmentKind.LIFFT].setText("2")
        dialog.save_button.click()
        with AssessmentProjectFile.open(tmp_path / "project.sqlite") as project:
            current = project.load_job_risk().for_job("assembly")
            assert len(current.measurements) == 1
            assert current.measurements[0].cumulative_damage == 2
        assert not hasattr(dialog, "cancel_button")
        assert dialog.direct_values.measurements() == current.measurements
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_failed_save_keeps_visible_entries_for_retry(tmp_path: Path) -> None:
    """Invalid direct values and failed writes preserve text for explicit correction.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; a successful retry publishes the intended current values only.
    """
    workspace = workspace_at(tmp_path)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.IMPERIAL)
    try:
        enter_new(dialog)
        with patch.object(dialog, "_warning"):
            cell = dialog.direct_values.fields[AssessmentKind.LIFFT]
            cell.setText("invalid")
            assert not dialog.accept_pending_job()
            assert dialog.direct_values.errors[AssessmentKind.LIFFT].text()
            with patch.object(
                AssessmentProjectFile, "save_job_details", side_effect=OSError("disk")
            ):
                cell.setText("2")
                assert dialog.job_name_input.text() == "Assembly"
            dialog.save_button.click()
            assert dialog.direct_values.measurements()[0].cumulative_damage == 2
    finally:
        dialog.direct_values.fields[AssessmentKind.LIFFT].setText("2")
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_nested_workplace_save_preserves_form_and_next_save(tmp_path: Path) -> None:
    """Actual nested modal assignment updates counts without discarding form text.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = workspace_at(tmp_path)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.IMPERIAL)
    try:
        with patch.object(QMessageBox, "information"):
            enter_new(dialog)
            dialog.save_button.click()
            dialog.job_name_input.setText("Local unsaved name")
            seen = []

            def assign() -> None:
                """Save the chosen workplace in the real modal.

                Check and Save the last exact station in the actual owned workplace
                modal while retaining the outer unsaved form.

                Args:
                    None.

                Returns:
                    None.
                """
                child = QApplication.activeModalWidget()
                if isinstance(child, JobWorkplaceDialog):
                    seen.append(True)
                    leaf = list(child.items())[-1]
                    leaf.setCheckState(0, Qt.CheckState.Checked)
                    child.save_button.click()

            QTimer.singleShot(0, assign)
            dialog.workplaces_button.click()
            assert seen == [True]
            assert dialog.workplaces_button.text() == "Workplaces (1)"
            assert dialog.job_name_input.text() == "Local unsaved name"
            dialog.save_button.click()
            with AssessmentProjectFile.open(tmp_path / "project.sqlite") as project:
                assert project.load_jobs().jobs[-1].name == "Local unsaved name"
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_navigation_search_and_modal_execution(tmp_path: Path) -> None:
    """Navigation follows the original order and exact-ID modal search selects once.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = workspace_at(tmp_path)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.IMPERIAL)
    try:
        dialog.last_button.click()
        assert dialog.job_id_combo.currentText() == "k"
        dialog.previous_button.click()
        assert dialog.job_id_combo.currentText() == "j"
        dialog.next_button.click()
        dialog.first_button.click()
        assert dialog.job_id_combo.currentText() == "j"
        enter_new(dialog)
        assert not hasattr(dialog, "cancel_button")
        assert dialog.job_id_combo.currentText() == "assembly"

        def search() -> None:
            """Enter exact job ID k into the original search modal and accept it.

            Args:
                None.

            Returns:
                None.
            """
            child = QApplication.activeModalWidget()
            if isinstance(child, QDialog):
                field = child.findChild(QLineEdit)
                assert field is not None
                field.setText("k")
                child.accept()

        QTimer.singleShot(0, search)
        dialog.search_button.click()
        assert dialog.job_id_combo.currentText() == "k"
        modal = []

        def close() -> None:
            """Record that the original job form owns the active modal.

            Record that the original job form owns the active modal before clicking its
            Close action.

            Args:
                None.

            Returns:
                None.
            """
            modal.append(QApplication.activeModalWidget() is dialog)
            dialog.close_button.click()

        QTimer.singleShot(0, close)
        dialog.exec()
        assert modal == [True]
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_empty_demo_creates_exclusively_and_saves_first_job(tmp_path: Path) -> None:
    """The runnable demo starts empty and never replaces an existing project.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "demo.ergprj"
    create_job_management_demo(path)
    with pytest.raises(FileExistsError):
        create_job_management_demo(path)
    workspace: ProjectWorkspace[AssessmentDraft] = ProjectWorkspace(
        lambda location: AssessmentProjectFile.open(Path(location)),
        JsonSettingsStore(tmp_path / "settings.json"),
    )
    workspace.switch(str(path), "assessment")
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.IMPERIAL)
    try:
        assert dialog.job_id_combo.count() == 0
        assert not dialog.workplaces_button.isEnabled()
        assert not hasattr(dialog, "cancel_button")
        with patch.object(QMessageBox, "information"):
            enter_new(dialog)
            dialog.save_button.click()
        assert dialog.job_id_combo.count() == 1
        assert dialog.workplaces_button.isEnabled()
        with (
            patch.object(QMessageBox, "question", return_value=QMessageBox.Yes),
            patch.object(QMessageBox, "information"),
        ):
            dialog.delete_button.click()
        assert dialog.job_id_combo.count() == 0
        assert dialog.job_name_input.text() == ""
        assert not dialog.delete_button.isEnabled()
        assert not dialog.workplaces_button.isEnabled()
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_preview_launcher_closes_owned_project(tmp_path: Path) -> None:
    """Run the actual modal launcher and reopen its synthetic project afterward.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    from ergotools.bootstrap import run_job_management

    path = tmp_path / "demo.ergprj"
    create_job_management_demo(path)
    seen = []

    def close_preview() -> None:
        """Record the launched Job Management title.

        Record the launched Job Management title and close its actual owned modal so
        repository cleanup can be asserted.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        if isinstance(dialog, JobManagementDialog):
            seen.append(dialog.windowTitle())
            dialog.close_button.click()

    QTimer.singleShot(0, close_preview)
    assert run_job_management(path, tmp_path / "settings.json") == 0
    assert seen == ["Job Management"]
    with AssessmentProjectFile.open(path) as reopened:
        assert reopened.load_jobs().jobs == ()


def test_delete_confirmation_retains_history_and_selected_form(tmp_path: Path) -> None:
    """Cancel does nothing; confirmed deletion selects a survivor; history blocks j.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = workspace_at(tmp_path)
    dialog = JobManagementDialog(
        workspace, load_icons(), MeasurementSystem.IMPERIAL, selected_job="k"
    )
    try:
        with patch.object(QMessageBox, "question", return_value=QMessageBox.No):
            dialog.delete_button.click()
        assert dialog.job_id_combo.currentText() == "k"
        with (
            patch.object(QMessageBox, "question", return_value=QMessageBox.Yes),
            patch.object(QMessageBox, "information"),
        ):
            dialog.delete_button.click()
        assert dialog.job_id_combo.currentText() == "j"
        assert not dialog.direct_values.measurements()
        with (
            patch.object(QMessageBox, "question", return_value=QMessageBox.Yes),
            patch.object(QMessageBox, "warning") as warning,
        ):
            dialog.delete_button.click()
            assert "referenced by an assessment" in warning.call_args.args[2]
        assert dialog.job_id_combo.currentText() == "j"
        assert dialog.delete_button.isEnabled()
        with (
            patch.object(QMessageBox, "question") as question,
            patch.object(QMessageBox, "warning"),
        ):
            dialog.job_id_combo.setEditText("another-id")
            dialog.delete_button.click()
            question.assert_not_called()
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)

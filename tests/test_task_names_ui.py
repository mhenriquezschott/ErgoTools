"""Native shared-grid task-name/paste editing with main and Job project history.

Test layer. Real controls use disposable projects. Modal previews are driven through
owned callbacks; warnings and canceled previews must never mutate project data.
"""

from pathlib import Path

import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QComboBox, QDialog

from ergotools.application.assessment_clipboard import (
    assessment_input_fields,
    prepare_assessment_paste,
)
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.task_catalog import TaskDefinition
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.assessment_paste_dialog import (
    AssessmentPasteDialog,
    clipboard_field,
)
from ergotools.presentation.desktop.job_management_dialog import JobManagementDialog
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_job_calculators import enter_job
from tests.test_task_count_integration import window as window
from tests.test_task_input_history import reopen_grid
from tests.test_unified_project_save import editing_workspace

# Keep native widgets alive through timer delivery; no operational project is opened.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("index", [0, 1, 2])
@pytest.mark.parametrize("language", list(Language))
def test_main_name_input_save_and_repeated_history(
    window: LifftWindow, tmp_path: Path, index: int, language: Language
) -> None:
    """One name cell is one repeatable source edit with unchanged numerical results.

    Args:
        window: Existing native fixture; it owns cleanup and only private files.
        tmp_path: Disposable source/settings directory.
        index: LiFFT, DUET or ST assessment panel.
        language: Both maintained UI languages.

    Returns:
        None; Enter, replay, pending Save and independent reopen preserve names.
    """
    original = reopen_grid(window, tmp_path, index, MeasurementSystem.METRIC, language)
    workspace = window.presenter.workspace
    panel = window.secondary_panel() or window.task_panel
    assert (
        panel is not None
        and workspace.active is not None
        and workspace.editing is not None
    )
    initial_result = workspace.historical_result()
    for name in ("Trimming", "Cutting"):
        control = panel.task_grid.task_names[0]
        assert isinstance(control, QComboBox)
        line = control.lineEdit()
        assert line is not None
        line.setFocus()
        line.selectAll()
        revision = workspace.editing.history.revision
        QTest.keyClicks(line, name)
        QTest.keyClick(line, Qt.Key_Return)
        assert workspace.active.state.tasks[0].task_name == name
        assert workspace.editing.history.revision > revision
        assert workspace.editing.replay(redo=False)
        assert workspace.active.state == original
        assert workspace.editing.history.undo_label_key is None
        assert workspace.editing.replay(redo=True)
        assert workspace.active.state.tasks[0].task_name == name
        assert workspace.editing.replay(redo=False)
    # Saving while the name editor still owns focus must accept the final token.
    control = panel.task_grid.task_names[0]
    assert isinstance(control, QComboBox)
    line = control.lineEdit()
    assert line is not None
    line.setFocus()
    QTest.keyClicks(line, "Pressing")
    window.save_project()
    assert workspace.active.state.tasks[0].task_name == "Pressing"
    assert workspace.historical_result().damage == initial_result.damage
    assert (
        workspace.historical_result().probability_percent
        == initial_result.probability_percent
    )
    with AssessmentProjectFile.open(Path(workspace.location)) as reopened:
        assert reopened.load(workspace.active.document).tasks[0].task_name == "Pressing"


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_job_name_and_multirow_paste_are_independent_undoable_operations(
    tmp_path: Path, kind: AssessmentKind
) -> None:
    """Job name cells and complete paste batches replay without losing inputs/results.

    Args:
        tmp_path: Disposable complete-project/settings directory.
        kind: Every tool uses the same shared task actions.

    Returns:
        None; source/results/task capacity survive history and durable Save/reopen.
    """
    workspace = editing_workspace(tmp_path)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:
        enter_job(dialog)
        dialog.tool_tabs.setCurrentIndex(list(AssessmentKind).index(kind))
        editor = dialog.editors[kind]
        expected = editor.source
        assert expected is not None and editor.task_actions is not None
        control = editor.task_names[0]
        assert isinstance(control, QComboBox)
        control.setEditText("Trimming")
        control.lineEdit().editingFinished.emit()
        named = dialog._measurement(kind).source
        assert named is not None and named.tasks[0].task_name == "Trimming"
        assert workspace.editing.replay(redo=False)
        assert editor.source.tasks[0].task_name is None
        assert workspace.editing.replay(redo=True)
        named = editor.source
        rows = (
            (("Cutting", "6", "100"), ("Pressing", "2", "200"))
            if kind is AssessmentKind.DUET
            else (
                (
                    ("Cutting", "0", "30", "49.05", "100"),
                    ("Pressing", "2", "20", "10", "200"),
                )
                if kind is AssessmentKind.TST
                else (
                    ("Cutting", "30", "49.05", "100"),
                    ("Pressing", "20", "10", "200"),
                )
            )
        )
        replacement = prepare_assessment_paste(
            named, rows, assessment_input_fields(named)
        )
        revision = workspace.editing.history.revision
        assert editor._accept_shared_source(
            named, replacement, "assessment.paste", True
        )
        pasted = dialog._measurement(kind)
        assert pasted.source == replacement and pasted.complete
        assert editor.task_count == 2 and len(editor.task_names) == 2
        assert workspace.editing.history.revision == revision + 1
        assert workspace.editing.replay(redo=False)
        assert editor.source == named and editor.task_count == 1
        assert workspace.editing.replay(redo=True)
        assert dialog._measurement(kind) == pasted
        assert workspace.save()
        with AssessmentProjectFile.open(Path(workspace.location)) as reopened:
            assert reopened.load_job_risk().for_job("J1").measurements == (pasted,)
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_reusable_definition_refresh_does_not_mutate_measurements(
    window: LifftWindow, tmp_path: Path
) -> None:
    """An explicit definition choice links only its name; global rename retains inputs.

    Args:
        window: Borrowed integrated native fixture.
        tmp_path: Disposable source/settings directory.

    Returns:
        None; rename and local name override are reversible independent operations.
    """
    reopen_grid(window, tmp_path, 0, MeasurementSystem.METRIC, Language.ENGLISH)
    workspace = window.presenter.workspace
    panel = window.task_panel
    definition = TaskDefinition("trimming", "Trimming")
    workspace.replace_task_definitions((), (definition,))
    panel.task_actions.refresh_names()
    control = panel.task_grid.task_names[0]
    assert isinstance(control, QComboBox)
    control.setCurrentIndex(control.findData("trimming"))
    control.activated.emit(control.currentIndex())
    linked = workspace.active.state
    assert linked.tasks[0].task_definition_id == "trimming"
    renamed = TaskDefinition("trimming", "Trimming thin material")
    workspace.replace_task_definitions((definition,), (renamed,))
    panel.task_actions.refresh_names()
    assert control.currentText() == renamed.name
    assert workspace.active.state == linked
    control.setEditText("One-off local task")
    control.lineEdit().editingFinished.emit()
    assert workspace.active.state.tasks[0].task_definition_id is None
    assert workspace.active.state.tasks[0].lever_arm == linked.tasks[0].lever_arm
    assert workspace.editing.replay(redo=False)
    assert workspace.active.state == linked
    assert workspace.load_task_definitions() == (renamed,)
    assert panel.task_grid.task_names[0].currentText() == renamed.name
    assert workspace.editing.replay(redo=False)
    assert workspace.load_task_definitions() == (definition,)
    assert panel.task_grid.task_names[0].currentText() == definition.name
    assert workspace.active.state == linked
    assert workspace.editing.replay(redo=True)
    assert panel.task_grid.task_names[0].currentText() == renamed.name


def test_paste_preview_header_units_mapping_and_cancel() -> None:
    """Preview detects real headers/units without misreading activity names as headers.

    Args:
        None.

    Returns:
        None; no project exists, and cancellation never produces a replacement.
    """
    from ergotools.application.job_calculation import blank_job_source
    from ergotools.domain.decimal_convention import DecimalConvention

    source = blank_job_source(AssessmentKind.LIFFT, MeasurementSystem.METRIC)
    dialog = AssessmentPasteDialog(
        source,
        "Task name\tLever arm (in)\tLoad (lbf)\tRepetitions\nCutting\t12\t10\t100",
        Language.ENGLISH,
        DecimalConvention.POINT,
        MeasurementSystem.METRIC,
        0,
    )
    try:
        assert dialog.header_option.isChecked()
        assert dialog.units.currentData() is MeasurementSystem.IMPERIAL
        dialog.prepare()
        assert dialog.result() == QDialog.Accepted
        assert dialog.replacement.tasks[0].task_name == "Cutting"
        assert dialog.replacement.tasks[0].lever_arm == 30.48
    finally:
        dialog.close()
    assert clipboard_field("Load boxes") is None
    assert clipboard_field("Task name") == "task_name"
    canceled = AssessmentPasteDialog(
        source,
        "Loading boxes\t30\t49\t100",
        Language.ENGLISH,
        DecimalConvention.POINT,
        MeasurementSystem.METRIC,
        0,
    )
    try:
        assert not canceled.header_option.isChecked()
        canceled.reject()
        assert canceled.replacement is None
    finally:
        canceled.close()


@pytest.mark.parametrize("index", [0, 1, 2])
def test_main_spreadsheet_preview_paste_cancel_and_single_undo(
    window: LifftWindow,
    tmp_path: Path,
    index: int,
) -> None:
    """The real Paste action previews/cancels or records an entire rectangle once.

    Args:
        window: Borrowed integrated fixture with shared project history.
        tmp_path: Disposable native source directory.
        index: Each assessment tool and its editable spreadsheet columns.

    Returns:
        None; modal cancellation leaves the source exact and Paste is one replay step.
    """
    original = reopen_grid(
        window, tmp_path, index, MeasurementSystem.METRIC, Language.ENGLISH
    )
    workspace = window.presenter.workspace
    panel = window.secondary_panel() or window.task_panel
    assert panel is not None
    headers = (
        "Task name\tLever arm (cm)\tLoad (N)\tRepetitions"
        if index == 0
        else "Task name\tOMNI-Res scale\tRepetitions"
        if index == 1
        else "Task name\tTask type\tLever arm (cm)\tLoad (N)\tRepetitions"
    )
    cells = (
        "Cutting\t30\t49.05\t120\nPressing\t20\t10\t150"
        if index == 0
        else "Cutting\t6\t120\nPressing\t2\t150"
        if index == 1
        else "Cutting\t0\t30\t49.05\t120\nPressing\t2\t20\t10\t150"
    )
    _APP.clipboard().setText(headers + "\n" + cells)
    failures = []

    def cancel_preview() -> None:
        """Cancel the owned native modal without changing inputs or source history.

        Args:
            None.

        Returns:
            None; callback failures are reported after modal exit rather than hidden.
        """
        dialog = _APP.activeModalWidget()
        if not isinstance(dialog, AssessmentPasteDialog):
            failures.append("Expected assessment paste preview")
            return
        dialog.reject()

    QTimer.singleShot(0, cancel_preview)
    panel.task_grid.paste_cells_button.click()
    assert not failures and workspace.active.state == original
    assert workspace.editing.history.undo_label_key is None

    def accept_preview() -> None:
        """Validate then accept the exact clipboard snapshot from its native preview.

        Args:
            None.

        Returns:
            None; a failed preparation closes the modal and reports the UI error.
        """
        dialog = _APP.activeModalWidget()
        if not isinstance(dialog, AssessmentPasteDialog):
            failures.append("Expected assessment paste preview")
            return
        dialog.prepare()
        if dialog.result() != QDialog.Accepted:
            failures.append(dialog.error.text())
            dialog.reject()

    QTimer.singleShot(0, accept_preview)
    panel.task_grid.paste_cells_button.click()
    assert not failures
    pasted = workspace.active.state
    assert pasted.tasks[0].task_name == "Cutting"
    assert pasted.tasks[1].task_name == "Pressing"
    assert pasted.tasks[1].repetitions == 150
    assert workspace.editing.replay(redo=False)
    assert workspace.active.state == original
    assert workspace.editing.history.undo_label_key is None
    assert workspace.editing.replay(redo=True)
    assert workspace.active.state == pasted


@pytest.mark.parametrize(
    "headers",
    [
        "Task name\tLever arm (cm)\tLoad (lbf)",
        "Task name\tLever arm (m)\tLoad (N)",
        "Task name\tLever arm (cm)\tLoad (kg)",
    ],
)
def test_ambiguous_or_unsupported_paste_units_do_not_apply(headers: str) -> None:
    """Mixed systems, unsupported dimensions and mass cannot silently become force.

    Args:
        headers: Explicit incompatible dimensional source columns.

    Returns:
        None; the native preview stays unaccepted with a useful validation message.
    """
    from ergotools.application.job_calculation import blank_job_source
    from ergotools.domain.decimal_convention import DecimalConvention

    source = blank_job_source(AssessmentKind.LIFFT, MeasurementSystem.METRIC)
    dialog = AssessmentPasteDialog(
        source,
        headers + "\nCutting\t30\t10",
        Language.ENGLISH,
        DecimalConvention.POINT,
        MeasurementSystem.METRIC,
        0,
    )
    try:
        dialog.prepare()
        assert dialog.result() != QDialog.Accepted
        assert dialog.error.text()
        assert dialog.replacement is None
    finally:
        dialog.close()

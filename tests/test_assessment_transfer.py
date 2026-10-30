"""Atomic saved-tool transfer and original-modal integration.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QCheckBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.session import DocumentKey
from ergotools.domain.assessment_transfer import TransferRequest
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.work_catalog import WorkerEntry
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.assessment_store import AssessmentSqliteStore
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.worker_transfer_dialog import WorkerTransferDialog
from tests.test_saved_tool_data import KINDS
from tests.test_saved_tool_data import window as window


def add_destination(window: LifftWindow) -> None:
    """Add one synthetic worker with no assessments, leaving all existing data.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    workspace = window.presenter.workspace
    snapshot = workspace.read_hierarchy()
    hierarchy = snapshot.hierarchy
    workspace.replace_hierarchy(
        snapshot,
        replace(
            hierarchy,
            work=replace(
                hierarchy.work, workers=(*hierarchy.work.workers, WorkerEntry("y"))
            ),
        ),
    )
    workspace.save()
    window.refresh_navigation()


def request(window: LifftWindow, move: bool = False) -> TransferRequest:
    """Select all source current tools and a new exact owner at the same station.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        move: True tests Move; False tests Copy while retaining the source assessment.

    Returns:
        Complete exact all-tool transfer request for the synthetic destination; no write
        occurs by constructing it.
    """
    workspace = window.presenter.workspace
    hierarchy = workspace.read_hierarchy().hierarchy
    source = workspace.read_jobs().jobs.assignments[0].worker
    return TransferRequest(
        1, hierarchy.work.worker_context("y", source.workplace), KINDS, move
    )


@pytest.mark.parametrize("move", [False, True])
def test_all_tool_copy_move_preserves_older_history_and_catalogs(
    window: LifftWindow, move: bool
) -> None:
    """One transaction copies exact sources; Move removes only selected current ones.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        move: True tests Move; False tests Copy while retaining the source assessment.

    Returns:
        None.
    """
    add_destination(window)
    workspace = window.presenter.workspace
    req = request(window, move)
    jobs, history = workspace.read_jobs(), workspace.read_history()
    with AssessmentProjectFile.open(Path(workspace.location)) as project:
        original = {
            e.document_id: project.load(
                next(
                    a.document
                    for a in project.list_assessments()
                    if a.document.document_id == e.document_id
                )
            )
            for e in history.history.entries
        }
        risk = project.load_job_risk()
    active = workspace.active
    ids = {kind: f"new-{kind}" for kind in KINDS}
    assert workspace.transfer_assessments(jobs, history, req, ids).completed
    assert workspace.active is (None if move else active)
    assert workspace.has_unsaved_changes
    workspace.save()
    with AssessmentProjectFile.open(Path(workspace.location)) as project:
        saved = project.load_history()
        target = next(
            a for a in project.load_jobs().assignments if a.worker.worker_id == "y"
        )
        for kind in KINDS:
            entry = saved.current_for(target.assignment_id, kind)
            assert entry.document_id == ids[kind]
            key = next(
                a.document
                for a in project.list_assessments()
                if a.document.document_id == ids[kind]
            )
            assert project.load(key) == original[f"{kind}-1"]
            assert (saved.current_for(1, kind) is None) is move
        # The fixture's older noncurrent LiFFT remains, as do all other owners.
        assert any(e.assignment_id == 2 for e in saved.entries)
        assert project.load_job_risk() == risk
        assert len(saved.entries) == len(history.history.entries) + (0 if move else 3)


def test_conflict_and_mid_write_failure_roll_back_all_selected_tools(
    window: LifftWindow,
) -> None:
    """A later tool failure rolls back earlier inserts and any new assignment.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    add_destination(window)
    workspace = window.presenter.workspace
    req = request(window)
    jobs, history = workspace.read_jobs(), workspace.read_history()
    ids = {kind: f"new-{kind}" for kind in KINDS}
    conflict = replace(req, destination=replace(req.destination, worker_id="x"))
    with pytest.raises(ValueError):
        workspace.transfer_assessments(jobs, history, conflict, ids)
    insert = AssessmentSqliteStore.insert_in_transaction
    calls = 0

    def fail_second(
        store: AssessmentSqliteStore, key: DocumentKey, state: AssessmentDraft
    ) -> None:
        """Fail the second selected source insert.

        Inject a failure on the second source insert so the test can assert complete
        selected-tool transfer rollback.

        Args:
            store: Injected test-owned storage adapter receiving the controlled
                write/read callback.
            key: Exact project/document identity for the source/result under test.
            state: Immutable draft snapshot being validated, loaded or persisted by this
                test callback.

        Returns:
            None.

        Raises:
            OSError: The controlled adapter/resource/publication failure is injected by
                this scenario.
        """
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("second tool failed")
        insert(store, key, state)

    with (
        patch.object(AssessmentSqliteStore, "insert_in_transaction", fail_second),
        pytest.raises(OSError),
    ):
        workspace.transfer_assessments(jobs, history, req, ids)
    with AssessmentProjectFile.open(Path(workspace.location)) as project:
        assert project.load_jobs() == jobs.jobs
        assert project.load_history() == history.history
    assert workspace.transfer_assessments(jobs, history, req, ids).completed


def select_y(dialog: WorkerTransferDialog) -> None:
    """Select exact destination through the original worker table.

    Args:
        dialog: Live modal/form under test; the caller owns its lifetime and event-loop
            scheduling.

    Returns:
        None.

    Raises:
        AssertionError: The deliberately rejected boundary/routing condition occurs, or
            the expected synthetic modal data are unavailable.
    """
    for row in range(dialog.worker_table.rowCount()):
        if dialog.worker_table.item(row, 0).data(Qt.ItemDataRole.UserRole) == "y":
            dialog.worker_table.selectRow(row)
            return
    raise AssertionError("Synthetic destination missing.")


@pytest.mark.parametrize("mode", ["cancel", "copy", "move"])
def test_actual_modal_pending_copy_and_move_dirty_cancel(
    window: LifftWindow,
    mode: str,
) -> None:
    """Main Transfer opens the original form; Copy and Cancel keep invalid text.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        mode: Parametrized workflow mode selecting the stated copy/move/cancel or
            display scenario.

    Returns:
        None.
    """
    add_destination(window)
    workspace = window.presenter.workspace
    field = window.task_panel.inputs[0][2]
    field.setText("bad")
    field.textEdited.emit("bad")
    active = workspace.active

    def act() -> None:
        """Drive the real destination selection, optionally stage a dirty Move.

        Drive the real destination selection, optionally stage a dirty Move and assert
        cancelled dirty consent does not complete it.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, WorkerTransferDialog)
        select_y(dialog)
        if mode == "cancel":
            dialog.reject()
        else:
            if mode == "move":
                field.setText("350")
                field.textEdited.emit("350")
                dialog.move_radio.setChecked(True)
            dialog.perform_transfer()
            assert dialog.completed

    with (
        patch.object(WorkerTransferDialog, "confirm_transfer", return_value=True),
        patch.object(WorkerTransferDialog, "show_success"),
        patch.object(WorkerTransferDialog, "show_failure") as errors,
        patch.object(window, "dirty_choice", return_value=CloseChoice.CANCEL),
    ):
        QTimer.singleShot(0, act)
        window.main_navigation.buttons["transfer"].click()
    errors.assert_not_called()
    if mode == "move":
        assert workspace.active is not active
        assert window.assessment_navigation.view.worker_id == "y"
        assert workspace.active.state.tasks[0].repetitions == 350
    else:
        assert workspace.active is active
    if mode != "move":
        assert field.text() == "bad"
    with AssessmentProjectFile.open(Path(workspace.location)) as project:
        has_destination = any(
            a.worker.worker_id == "y" for a in project.load_jobs().assignments
        )
        assert not has_destination
    assert any(
        a.worker.worker_id == "y" for a in workspace.read_jobs().jobs.assignments
    ) is (mode != "cancel")
    if mode == "move":
        window.save_project()
        with AssessmentProjectFile.open(Path(workspace.location)) as project:
            assert any(
                a.worker.worker_id == "y" for a in project.load_jobs().assignments
            )


def test_filters_clear_destination_and_tool_selection_disables_transfer(
    window: LifftWindow,
) -> None:
    """No hidden worker/tool/station selection can pass the form's interlocks.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    add_destination(window)
    workspace = window.presenter.workspace
    dialog = WorkerTransferDialog(
        workspace,
        1,
        window.icons,
        lambda _: None,
        language=window.language,
        parent=window,
    )
    try:
        select_y(dialog)
        assert dialog.transfer_button.isEnabled()
        dialog.worker_search.setText("no such worker")
        assert dialog.worker_table.rowCount() == 0
        assert not dialog.transfer_button.isEnabled()
        dialog.worker_search.clear()
        select_y(dialog)
        for row in range(dialog.tool_table.rowCount()):
            dialog.tool_table.cellWidget(row, 0).findChild(QCheckBox).setChecked(False)
        assert not dialog.transfer_button.isEnabled()
    finally:
        dialog.close()


def test_actual_modal_move_save_keeps_older_sources_and_opens_destination(
    window: LifftWindow,
) -> None:
    """Confirmed Move retains valid input privately until the sole main Save.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    add_destination(window)
    workspace = window.presenter.workspace
    field = window.task_panel.inputs[0][2]
    field.setText("350")
    field.textEdited.emit("350")

    def act() -> None:
        """Drive the real Move controls.

        Drive the real Move controls and assert explicit Save consent completes the
        exact selected transfer.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, WorkerTransferDialog)
        select_y(dialog)
        dialog.move_radio.setChecked(True)
        dialog.perform_transfer()
        assert dialog.completed

    with (
        patch.object(WorkerTransferDialog, "confirm_transfer", return_value=True),
        patch.object(WorkerTransferDialog, "show_success"),
        patch.object(WorkerTransferDialog, "show_failure") as errors,
        patch.object(window, "dirty_choice", return_value=CloseChoice.SAVE),
    ):
        QTimer.singleShot(0, act)
        window.main_navigation.buttons["transfer"].click()
    errors.assert_not_called()
    assert window.assessment_navigation.view.worker_id == "y"
    assert workspace.active.state.tasks[0].repetitions == 350
    with AssessmentProjectFile.open(Path(workspace.location)) as saved:
        assert all(a.worker.worker_id != "y" for a in saved.load_jobs().assignments)
    window.save_project()
    with AssessmentProjectFile.open(Path(workspace.location)) as project:
        target = next(
            a for a in project.load_jobs().assignments if a.worker.worker_id == "y"
        )
        entry = project.load_history().current_for(target.assignment_id, KINDS[0])
        copied = project.load(
            DocumentKey(project.metadata.project_id, entry.document_id)
        )
        assert copied.tasks[0].repetitions == 350
        assert any(e.assignment_id == 2 for e in project.load_history().entries)

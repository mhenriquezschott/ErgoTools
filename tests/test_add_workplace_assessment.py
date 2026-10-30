"""Explicit blank workplace creation/replacement through the shared hierarchy picker.

Tests use disposable projects and public workspace editing paths. Consent, atomic
ownership/source/result changes, cache invalidation and empty Save/reopen are covered.
"""

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtWidgets import QDialog, QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.session import DocumentKey
from ergotools.bootstrap import create_window
from ergotools.domain.assessments.document import AssessmentDraft, AssessmentKind
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.assessment_store import AssessmentSqliteStore
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.workplace_assignment_dialog import (
    WorkplaceAssignmentDialog,
)
from tests.test_assessment_navigation import add_night_context
from tests.test_history_persistence import STATION
from tests.test_main_navigation import window as window
from tests.test_worker_assessment_defaults import seed_defaults


def accept_workplace(dialog: WorkplaceAssignmentDialog) -> int:
    """Accept the first actual station/shift through the existing picker API.

    Args:
        dialog: Real picker constructed by the host for the current worker/tool.

    Returns:
        Accepted dialog code after a real hierarchy leaf and saved shift are selected.
    """
    station = next(iter(dialog._stations))
    dialog.select_workplace(station.at_shift(dialog.shift.itemData(0)))
    dialog.accept_selection()
    return QDialog.Accepted


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_add_blank_assessment_creates_owner_and_survives_empty_save(
    tmp_path: Path, kind: AssessmentKind
) -> None:
    """A worker needs no prior assignment; all tools save empty and remain undoable.

    Args:
        tmp_path: Disposable native project and personal preferences directory.
        kind: Each tool gets one independently owned blank 15-task source.

    Returns:
        None; other sources and public bytes stay unchanged until Save.
    """
    path = tmp_path / "create.ergprj"
    seed_defaults(path)
    original = path.read_bytes()
    host = create_window(tmp_path / "settings.json", original_navigation=True)
    try:
        host.open_project_location(str(path))
        host.assessment_tabs.setCurrentIndex(list(AssessmentKind).index(kind))
        host.navigate_worker("W03")
        workspace = host.presenter.workspace
        before = workspace.read_history().history
        with patch.object(WorkplaceAssignmentDialog, "exec", accept_workplace):
            host.main_navigation.location_browser.add_button.click()
        view = host.assessment_navigation.view
        assert view.saved and view.kind is kind and view.worker_id == "W03"
        assert view.assignment_id is not None and view.workplace is not None
        entry = workspace.read_history().history.current_for(view.assignment_id, kind)
        assert entry.document_id == view.document_id
        source = workspace.active.state
        assert len(source.tasks) == 15
        assert all(task.repetitions is None for task in source.tasks)
        assert workspace.saved_assessment_result(entry.document_id) is None
        assert len(workspace.read_history().history.entries) == len(before.entries) + 1
        assert path.read_bytes() == original
        host.save_project()
        assert not workspace.has_unsaved_changes
        with AssessmentProjectFile.open(path) as project:
            assert project.load(DocumentKey("defaults", entry.document_id)) == source
            assert project.load_history().current_for(view.assignment_id, kind) == entry
            assert (
                project.load_saved_result(DocumentKey("defaults", entry.document_id))
                is None
            )
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            # Replay any selection step before the atomic creation step.
            for _ in range(3):
                if not any(
                    e.document_id == entry.document_id
                    for e in workspace.read_history().history.entries
                ):
                    break
                host.history_actions.replay(redo=False)
            assert workspace.read_history().history == before
            for _ in range(3):
                if any(
                    e.document_id == entry.document_id
                    for e in workspace.read_history().history.entries
                ):
                    break
                host.history_actions.replay(redo=True)
            assert any(e == entry for e in workspace.read_history().history.entries)
    finally:
        host.presenter.workspace.close(choice=CloseChoice.DISCARD)
        host.close()
        host.deleteLater()


def test_replace_consent_keeps_identity_and_undo_restores_exact_result(
    window: LifftWindow,
) -> None:
    """No leaves existing data intact; Yes clears only the selected owner/tool.

    Args:
        window: Disposable integrated LiFFT project with two assessed workers.

    Returns:
        None; cached source reloads; Undo/Redo restores exact inputs/results.
    """
    window.task_panel.calculate_button.click()
    window.save_project()
    ws = window.presenter.workspace
    original = ws.active.state
    key = ws.active.document
    result = ws.saved_assessment_result(key.document_id)
    assert result is not None
    history = ws.read_history().history
    other = next(e for e in history.entries if e.document_id != key.document_id)
    other_source = ws.assessment_source(other.document_id)
    with patch.object(WorkplaceAssignmentDialog, "exec", return_value=QDialog.Rejected):
        window.add_workplace_assessment()
    assert ws.active.state == original and ws.read_history().history == history
    with patch.object(WorkplaceAssignmentDialog, "exec", accept_workplace):
        with patch.object(QMessageBox, "question", return_value=QMessageBox.No) as ask:
            window.add_workplace_assessment()
        assert ask.call_count == 1 and ask.call_args.args[-1] == QMessageBox.No
        assert ws.active.state == original
        assert ws.saved_assessment_result(key.document_id) == result
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            window.add_workplace_assessment()
    assert ws.active.document == key and len(ws.active.state.tasks) == 15
    assert ws.active.state != original
    assert ws.saved_assessment_result(key.document_id) is None
    assert ws.read_history().history == history
    assert ws.assessment_source(other.document_id) == other_source
    window.history_actions.replay(redo=False)
    assert ws.active.state == original
    assert ws.saved_assessment_result(key.document_id) == result
    window.history_actions.replay(redo=True)
    assert len(ws.active.state.tasks) == 15
    assert ws.saved_assessment_result(key.document_id) is None


def test_destination_guard_and_late_failure_roll_back_every_record(
    window: LifftWindow,
) -> None:
    """Unconfirmed replacement and late insertion failure leave no orphan assignment.

    Args:
        window: Disposable native project with an unassigned worker y.

    Returns:
        None; catalog, ownership, source and active document retain their exact state.
    """
    ws = window.presenter.workspace
    jobs, history, active = ws.read_jobs().jobs, ws.read_history().history, ws.active
    placement = jobs.assignments[0].placement_id
    with pytest.raises(ValueError, match="destination changed"):
        ws.add_workplace_assessment(
            "w",
            STATION.at_shift("Day"),
            placement,
            "new",
            window._blank_kind(AssessmentKind.LIFFT),
            effective_date=date.today(),
        )
    with (
        patch.object(
            AssessmentSqliteStore,
            "insert_in_transaction",
            side_effect=OSError("late source failure"),
        ),
        pytest.raises(OSError, match="late source failure"),
    ):
        ws.add_workplace_assessment(
            "y",
            STATION.at_shift("Day"),
            None,
            "new",
            window._blank_kind(AssessmentKind.LIFFT),
            effective_date=date.today(),
        )
    assert ws.read_jobs().jobs == jobs and ws.read_history().history == history
    assert ws.active is active


@pytest.mark.parametrize("accept", [False, True])
def test_add_preserves_same_job_creation_consent(
    window: LifftWindow,
    accept: bool,
) -> None:
    """The new Add path retains the established same-Job warning across locations.

    Args:
        window: Disposable project with day data and an empty night assignment.
        accept: Explicit Yes/No consent before creating the night source.

    Returns:
        None; No preserves exact history/view and Yes creates only the requested tool.
    """
    add_night_context(window, saved=False)
    ws = window.presenter.workspace
    before = ws.read_history().history
    original = ws.active.document

    def night(dialog: WorkplaceAssignmentDialog) -> int:
        """Select an existing unassessed night owner through the shared hierarchy.

        Args:
            dialog: Real reuse-existing workplace picker.

        Returns:
            Accepted complete station/shift intent, without any repository mutation.
        """
        dialog.select_workplace(STATION.at_shift("Night"))
        dialog.accept_selection()
        return QDialog.Accepted

    with (
        patch.object(WorkplaceAssignmentDialog, "exec", night),
        patch.object(
            QMessageBox,
            "question",
            return_value=QMessageBox.Yes if accept else QMessageBox.No,
        ) as ask,
    ):
        window.add_workplace_assessment()
    assert ask.call_count == 1 and "Job j" in ask.call_args.args[2]
    assert len(ws.read_history().history.entries) == len(before.entries) + int(accept)
    if not accept:
        assert ws.active.document == original and ws.read_history().history == before
    else:
        assert window.assessment_navigation.view.workplace.shift_id == "Night"
        assert len(ws.active.state.tasks) == 15


def test_replacement_late_source_failure_restores_source_and_result(
    window: LifftWindow,
) -> None:
    """A failure after source SQL runs rolls back both old inputs and saved outputs.

    Args:
        window: Disposable integrated LiFFT assessment and private editing adapter.

    Returns:
        None; source, exact result, catalog and active session remain intact.
    """
    window.task_panel.calculate_button.click()
    window.save_project()
    ws = window.presenter.workspace
    source, key = ws.active.state, ws.active.document
    result = ws.saved_assessment_result(key.document_id)
    history, jobs = ws.read_history().history, ws.read_jobs().jobs
    original_save = AssessmentSqliteStore.save_in_transaction

    def fail_after_save(
        store: AssessmentSqliteStore,
        document: DocumentKey,
        state: AssessmentDraft,
    ) -> None:
        """Inject failure after the real source write inside the owning transaction.

        Args:
            store: Borrowed source adapter sharing the native transaction.
            document: Target assessment identity.
            state: Proposed blank replacement source.

        Returns:
            None; injected exception always prevents completion.

        Raises:
            OSError: Deliberate late replacement failure for rollback verification.
        """
        original_save(store, document, state)
        raise OSError("late replacement failure")

    owner = next(a for a in jobs.assignments if a.worker.worker_id == "w")
    with (
        patch.object(AssessmentSqliteStore, "save_in_transaction", fail_after_save),
        pytest.raises(OSError, match="late replacement failure"),
    ):
        ws.add_workplace_assessment(
            "w",
            owner.worker.workplace,
            owner.placement_id,
            "unused-new-id",
            window._blank_kind(AssessmentKind.LIFFT),
            effective_date=date.today(),
            expected_document_id=key.document_id,
        )
    assert ws.active.state == source and ws.assessment_source(key.document_id) == source
    assert ws.saved_assessment_result(key.document_id) == result
    assert ws.read_history().history == history and ws.read_jobs().jobs == jobs

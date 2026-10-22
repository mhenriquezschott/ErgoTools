"""Single project Save, shared worker replay and durable failure boundaries.

Tests use genuinely empty native16 projects in pytest-owned directories. User
fixtures and the reference application are never opened for writing. Real SQLite
reopen assertions distinguish private accepted edits from durable publication.
"""

from contextlib import closing
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtWidgets import QApplication, QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.session import DocumentKey
from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.work_catalog import WorkerEntry
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.settings_store import JsonSettingsStore
from ergotools.presentation.desktop.worker_management_dialog import (
    WorkerManagementDialog,
)

# Retain the one Qt application required by real worker form controls.
_APP = QApplication.instance() or QApplication([])


def editing_workspace(tmp_path: Path) -> ProjectWorkspace[AssessmentDraft]:
    """Create an empty native project and open its integrated private session.

    Args:
        tmp_path: Disposable project/settings directory owned by pytest.

    Returns:
        Open workspace owned by the caller, with no workers or assessment placeholder.
    """
    path = tmp_path / "workflow.ergprj"
    with AssessmentProjectFile.create_empty(
        path, ProjectMetadata("workflow", "Workflow", MeasurementSystem.METRIC)
    ):
        pass
    workspace: ProjectWorkspace[AssessmentDraft] = ProjectWorkspace(
        lambda location: AssessmentProjectFile.open(Path(location)),
        JsonSettingsStore(tmp_path / "settings.json"),
        unified_saving=True,
    )
    workspace.switch(str(path), None)
    return workspace


def test_four_workers_close_shared_undo_redo_and_single_save(tmp_path: Path) -> None:
    """Four accepted workers stay private and replay individually across closing.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; reopens verify the durable database before and after the sole Save.
    """
    workspace = editing_workspace(tmp_path)
    path = Path(workspace.location)
    before = path.read_bytes()
    dialog = WorkerManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:
        assert dialog.save_button.isHidden()
        for index in range(1, 5):
            dialog.worker_id_combo.setEditText(f"W0{index}")
            dialog.first_name_input.setText(f"Worker {index}")
            dialog.new_button.click()
        dialog.close()
        assert path.read_bytes() == before
        editing = workspace.editing
        assert editing is not None and editing.is_dirty
        assert editing.removals(redo=False) == frozenset({("worker", "W04")})
        assert editing.replay(redo=False)
        assert [
            w.worker_id for w in workspace.read_hierarchy().hierarchy.work.workers
        ] == ["W01", "W02", "W03"]
        assert editing.removals(redo=False) == frozenset({("worker", "W03")})
        assert editing.replay(redo=False)
        assert editing.replay(redo=True)
        assert [
            w.worker_id for w in workspace.read_hierarchy().hierarchy.work.workers
        ] == ["W01", "W02", "W03"]
        assert workspace.active is None
        assert workspace.save()
        assert not workspace.has_unsaved_changes
        with AssessmentProjectFile.open(path) as saved:
            assert [w.worker_id for w in saved.load_hierarchy().work.workers] == [
                "W01",
                "W02",
                "W03",
            ]
            assert saved.list_assessments() == ()
        assert editing.replay(redo=True)
        assert workspace.has_unsaved_changes
        workspace.close(choice=CloseChoice.DISCARD)
        with AssessmentProjectFile.open(path) as saved:
            assert len(saved.load_hierarchy().work.workers) == 3
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_worker_navigation_accepts_edits_and_invalid_close_keeps_form(
    tmp_path: Path,
) -> None:
    """Worker edits survive navigation, while invalid text cannot vanish on close.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; only the main project Save publishes accepted details.
    """
    workspace = editing_workspace(tmp_path)
    dialog = WorkerManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:
        dialog.worker_id_combo.setEditText("W01")
        dialog.first_name_input.setText("Ana")
        dialog.new_button.click()
        dialog.worker_id_combo.setEditText("W02")
        dialog.first_name_input.setText("Bruno")
        assert dialog.accept_pending_worker()
        dialog.worker_id_combo.setCurrentIndex(dialog.worker_id_combo.findText("W01"))
        dialog.weight_input.setText("65")
        dialog.worker_id_combo.setCurrentIndex(dialog.worker_id_combo.findText("W02"))
        worker = next(
            w for w in dialog._hierarchy.hierarchy.work.workers if w.worker_id == "W01"
        )
        assert worker.details.weight_kg == 65
        dialog.weight_input.setText("invalid")
        assert not dialog.accept_pending_worker()
        assert dialog.weight_input.text() == "invalid"
        dialog.cancel_worker()
        assert dialog.accept_pending_worker()
    finally:
        dialog.cancel_worker()
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_failed_save_keeps_file_and_drafts_for_retry(tmp_path: Path) -> None:
    """Failed publication never marks private edits clean or damages the old file.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; retry publishes the same retained worker without duplicate records.
    """
    workspace = editing_workspace(tmp_path)
    path = Path(workspace.location)
    before = path.read_bytes()
    try:
        hierarchy = workspace.read_hierarchy()
        workspace.replace_hierarchy(
            hierarchy,
            replace(
                hierarchy.hierarchy,
                work=replace(hierarchy.hierarchy.work, workers=(WorkerEntry("W01"),)),
            ),
        )
        editing = workspace.editing
        assert editing is not None
        with (
            patch.object(
                editing.repository, "commit_editing", side_effect=OSError("read only")
            ),
            pytest.raises(OSError, match="read only"),
        ):
            workspace.save()
        assert workspace.has_unsaved_changes
        assert path.read_bytes() == before
        assert workspace.save()
        assert not workspace.has_unsaved_changes
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_worker_window_uses_same_history_and_cancelled_removal_keeps_cursor(
    tmp_path: Path,
) -> None:
    """Local buttons replay the global project and cancellation consumes nothing.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; restoration prompts are absent and removed worker details return intact.
    """
    workspace = editing_workspace(tmp_path)
    dialog = WorkerManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:
        dialog.worker_id_combo.setEditText("W01")
        dialog.first_name_input.setText("Ana")
        dialog.new_button.click()
        history = dialog.project_history
        assert history is not None
        dialog.setFocus()
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Cancel):
            history.replay(redo=False)
        assert len(dialog._hierarchy.hierarchy.work.workers) == 1
        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.Yes
        ) as consent:
            history.replay(redo=False)
            assert consent.call_count == 1
            assert not dialog._hierarchy.hierarchy.work.workers
            history.replay(redo=True)
            assert consent.call_count == 1
        assert dialog.first_name_input.text() == "Ana"
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_organization_and_job_close_accept_into_one_project_save(
    tmp_path: Path,
) -> None:
    """Organization and Job dialogs retain edits with no local Save controls.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; both editors publish together only through workspace Save.
    """
    from ergotools.presentation.desktop.job_management_dialog import JobManagementDialog
    from ergotools.presentation.desktop.organization_dialog import OrganizationDialog

    workspace = editing_workspace(tmp_path)
    path = Path(workspace.location)
    before = path.read_bytes()
    organization = OrganizationDialog(workspace, load_icons())
    try:
        assert organization.save_button.isHidden()
        organization.editors["name"].setText("P01")
        organization.close()
        jobs = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
        try:
            assert jobs.save_button.isHidden()
            jobs.job_id_combo.setEditText("J01")
            jobs.job_name_input.setText("Packing")
            jobs.risk_table.item(0, 1).setText("0")
            jobs.close()
        finally:
            jobs.deleteLater()
        assert workspace.read_hierarchy().hierarchy.plants == ("P01",)
        assert [job.job_id for job in workspace.read_jobs().jobs.jobs] == ["J01"]
        assert path.read_bytes() == before
        assert workspace.save()
        with AssessmentProjectFile.open(path) as saved:
            assert saved.load_hierarchy().plants == ("P01",)
            assert saved.load_jobs().jobs[0].name == "Packing"
    finally:
        organization.deleteLater()
        workspace.close(choice=CloseChoice.DISCARD)


def test_main_and_worker_buttons_share_the_same_four_worker_history(
    tmp_path: Path,
) -> None:
    """Closing worker management creates no extra Undo step in the main window.

    Args:
        tmp_path: Disposable native project and personal settings directory.

    Returns:
        None; main Undo removes only W04 and reopening worker management sees W03.
    """
    from PyQt5.QtWidgets import QDialog

    from ergotools.bootstrap import create_window

    initial = editing_workspace(tmp_path)
    location = initial.location
    initial.close(choice=CloseChoice.DISCARD)
    view = create_window(tmp_path / "main_settings.json", original_navigation=True)
    view.open_project_location(location)

    def enter_workers(dialog: WorkerManagementDialog) -> int:
        """Accept four complete workers through the production modal boundary.

        Args:
            dialog: Main-window-owned worker editor over the same project session.

        Returns:
            Accepted Qt modal result after four individual additions.
        """
        for index in range(1, 5):
            dialog.worker_id_combo.setEditText(f"W0{index}")
            dialog.first_name_input.setText(f"Worker {index}")
            dialog.new_button.click()
        return QDialog.Accepted

    try:
        with patch.object(WorkerManagementDialog, "exec", enter_workers):
            view.open_worker_management()
        actions = view.history_actions
        assert actions is not None
        actions.refresh()
        view.setFocus()
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            actions.replay(redo=False)
        assert [
            w.worker_id
            for w in view.presenter.workspace.read_hierarchy().hierarchy.work.workers
        ] == ["W01", "W02", "W03"]
        dialog = WorkerManagementDialog(
            view.presenter.workspace, load_icons(), MeasurementSystem.METRIC
        )
        try:
            assert len(dialog._hierarchy.hierarchy.work.workers) == 3
            assert dialog.project_history.editing is actions.shared.editing
        finally:
            dialog.close()
    finally:
        view.presenter.workspace.close(choice=CloseChoice.DISCARD)
        view.close()
        view.deleteLater()


def test_save_as_includes_private_edits_while_backup_excludes_them(
    tmp_path: Path,
) -> None:
    """Save As publishes accepted content; Backup preserves the last durable baseline.

    Args:
        tmp_path: Disposable native destinations and settings directory.

    Returns:
        None; neither operation silently overwrites the original project file.
    """
    workspace = editing_workspace(tmp_path)
    original = Path(workspace.location)
    before = original.read_bytes()
    try:
        hierarchy = workspace.read_hierarchy()
        workspace.replace_hierarchy(
            hierarchy,
            replace(
                hierarchy.hierarchy,
                work=replace(hierarchy.hierarchy.work, workers=(WorkerEntry("W01"),)),
            ),
        )
        backup = tmp_path / "backup.ergprj"
        assert workspace.backup(str(backup)).completed
        with AssessmentProjectFile.open(backup) as saved:
            assert not saved.load_hierarchy().work.workers
        assert workspace.has_unsaved_changes
        copied = tmp_path / "working_copy.ergprj"
        assert workspace.save_as(str(copied)).completed
        assert original.read_bytes() == before
        with AssessmentProjectFile.open(copied) as saved:
            assert saved.load_hierarchy().work.workers == (WorkerEntry("W01"),)
        assert not workspace.has_unsaved_changes
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_real_sqlite_publication_failure_is_atomic_and_retryable(
    tmp_path: Path,
) -> None:
    """A read-only destination rejects the complete Save without losing private data.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; removing the injected SQLite read-only restriction permits exact retry.
    """
    import sqlite3

    workspace = editing_workspace(tmp_path)
    path = Path(workspace.location)
    before = path.read_bytes()
    try:
        hierarchy = workspace.read_hierarchy()
        workspace.replace_hierarchy(
            hierarchy,
            replace(
                hierarchy.hierarchy,
                work=replace(hierarchy.hierarchy.work, workers=(WorkerEntry("W01"),)),
            ),
        )
        repository = workspace.editing.repository
        assert isinstance(repository, AssessmentProjectFile)
        destination = repository._durable_connection
        assert destination is not None
        with closing(
            sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        ) as read_only:
            repository._durable_connection = read_only
            try:
                with pytest.raises(sqlite3.OperationalError):
                    workspace.save()
                assert path.read_bytes() == before and workspace.has_unsaved_changes
            finally:
                repository._durable_connection = destination
        assert workspace.save()
        assert not workspace.has_unsaved_changes
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_management_rich_text_undo_stays_local(tmp_path: Path) -> None:
    """Typing Undo in Job notes must never remove the previously accepted Job.

    Args:
        tmp_path: Disposable native project and preference directory.

    Returns:
        None; global history and record membership remain unchanged during text Undo.
    """
    from PyQt5.QtCore import Qt
    from PyQt5.QtTest import QTest

    from ergotools.presentation.desktop.job_management_dialog import JobManagementDialog

    workspace = editing_workspace(tmp_path)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:
        dialog.job_id_combo.setEditText("J01")
        dialog.job_name_input.setText("Packing")
        dialog.risk_table.item(0, 1).setText("0")
        assert dialog.accept_pending_job()
        editing = workspace.editing
        revision = editing.history.revision
        dialog.show()
        dialog.activateWindow()
        dialog.job_description_input.setFocus()
        _APP.processEvents()
        QTest.keyClicks(dialog.job_description_input, "temporary notes")
        with patch.object(QMessageBox, "question") as consent:
            QTest.keyClick(dialog.job_description_input, Qt.Key_Z, Qt.ControlModifier)
            consent.assert_not_called()
        assert dialog.job_description_input.toPlainText() == ""
        assert editing.history.revision == revision
        assert dialog._jobs.jobs.jobs[0].job_id == "J01"
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_shared_history_subscriptions_detach_during_native_teardown(
    tmp_path: Path,
) -> None:
    """Retired project windows tolerate callbacks and garbage collection.

    Args:
        tmp_path: Disposable project and personal settings directory.

    Returns:
        None; Qt/Python teardown must emit no unhandled callback exception.
    """
    import gc

    from PyQt5.QtCore import QCoreApplication, QEvent

    workspace = editing_workspace(tmp_path)
    dialog = WorkerManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    editing = workspace.editing
    dialog.close()
    dialog.deleteLater()
    workspace.close(choice=CloseChoice.DISCARD)
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _APP.processEvents()
    gc.collect()
    editing.notify()


def test_multi_source_staging_failure_rolls_back_and_keeps_both_drafts(
    tmp_path: Path,
) -> None:
    """Failure on a second tab cannot leave the first accepted secretly clean.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; both exact edited states survive rollback and an ordinary Save retry.
    """
    from ergotools.application.assessments.lifft_commands import AddLifftTask
    from ergotools.application.assessments.project_edits import LifftProjectEdit
    from ergotools.domain.assessment_history import AssignmentAssessment
    from ergotools.domain.assessments.document import AssessmentKind
    from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask

    workspace = editing_workspace(tmp_path)
    try:
        hierarchy = workspace.read_hierarchy()
        workspace.replace_hierarchy(
            hierarchy,
            replace(
                hierarchy.hierarchy,
                work=replace(
                    hierarchy.hierarchy.work,
                    workers=(WorkerEntry("W01"), WorkerEntry("W02")),
                ),
            ),
        )
        for identity, worker in (("a", "W01"), ("b", "W02")):
            assert workspace.create_assignment_assessment(
                AssignmentAssessment(
                    identity, None, AssessmentKind.LIFFT, worker_id=worker
                ),
                LifftDraft(MeasurementSystem.METRIC),
            ).completed
        workspace.browse_document("a")
        first = workspace.active
        first.execute(
            LifftProjectEdit(
                AddLifftTask(first.document, LifftTask("ta", 20, 20, 100), 0)
            )
        )
        workspace.browse_document("b")
        second = workspace.active
        second.execute(
            LifftProjectEdit(
                AddLifftTask(second.document, LifftTask("tb", 30, 40, 200), 0)
            )
        )
        editing = workspace.editing
        checkpoint = editing.repository.editing_checkpoint()
        assert not workspace.resolve_browse(CloseChoice.CANCEL)
        assert editing.repository.editing_checkpoint() == checkpoint
        assert first.is_dirty and second.is_dirty
        original = AssessmentProjectFile.save
        calls = 0

        def fail_second(
            repository: AssessmentProjectFile,
            document: DocumentKey,
            state: AssessmentDraft,
        ) -> None:
            """Fail only the second source write inside the private acceptance group.

            Args:
                repository: Borrowed native project receiving each source write.
                document: Existing source key passed unchanged to the real adapter.
                state: Immutable source passed unchanged to the real adapter.

            Returns:
                None after the first real write; later failure propagates to rollback.

            Raises:
                OSError: Controlled second-source acceptance failure.
            """
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("second source failed")
            original(repository, document, state)

        with (
            patch.object(AssessmentProjectFile, "save", fail_second),
            pytest.raises(OSError, match="second source"),
        ):
            workspace.stage_assessments()
        assert editing.repository.editing_checkpoint() == checkpoint
        assert first.is_dirty and second.is_dirty and workspace.has_unsaved_changes
        assert first.state.tasks[0].repetitions == 100
        assert second.state.tasks[0].repetitions == 200
        assert workspace.save()
        with AssessmentProjectFile.open(Path(workspace.location)) as saved:
            assert saved.load(first.document).tasks[0].repetitions == 100
            assert saved.load(second.document).tasks[0].repetitions == 200
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_project_editing_initialization_tolerates_reentrant_readers(
    tmp_path: Path,
) -> None:
    """Focus/finalizer readers cannot start a second partially initialized session.

    Args:
        tmp_path: Disposable native project and personal settings directory.

    Returns:
        None; the outer activation completes once and remains clean/saveable.
    """
    path = tmp_path / "reentrant.ergprj"
    with AssessmentProjectFile.create_empty(
        path, ProjectMetadata("reentrant", "Reentrant", MeasurementSystem.METRIC)
    ):
        pass
    workspace = ProjectWorkspace(
        lambda location: AssessmentProjectFile.open(Path(location)),
        JsonSettingsStore(tmp_path / "settings.json"),
        unified_saving=True,
    )
    original = AssessmentProjectFile.begin_editing
    observations = []

    def begin(repository: AssessmentProjectFile, changed: object) -> None:
        """Inject the same nested read as Qt focus notifications during allocation.

        Args:
            repository: Native repository being detached to private memory.
            changed: Exact application callback forwarded without replacement.

        Returns:
            None; nested readers observe construction rather than duplicating it.
        """
        original(repository, changed)
        observations.append(workspace.editing)

    try:
        workspace.switch(str(path), None)
        with patch.object(AssessmentProjectFile, "begin_editing", begin):
            editing = workspace.editing
        assert editing is not None and observations == [None]
        assert workspace.editing is editing and not workspace.has_unsaved_changes
        assert workspace.save()
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("language_code", ("en", "es"))
@pytest.mark.parametrize("system", list(MeasurementSystem))
def test_existing_worker_weight_undo_is_available_before_closing(
    tmp_path: Path, language_code: str, system: MeasurementSystem
) -> None:
    """A completed existing-worker edit can Undo/Redo in the still-open form.

    Args:
        tmp_path: Disposable native project and personal settings directory.
        language_code: English/Spanish history controls over the same canonical data.
        system: Display system; entered 85 means kilograms or pounds respectively.

    Returns:
        None; mouse replay restores exact prior mass without a project-file write,
        and only the main Save publishes the redone edit.
    """
    from PyQt5.QtCore import Qt
    from PyQt5.QtTest import QTest

    from ergotools.domain.language import Language
    from ergotools.domain.worker_details import WorkerDetails, store_body_measurement

    workspace = editing_workspace(tmp_path)
    path = Path(workspace.location)
    snapshot = workspace.read_hierarchy()
    workspace.replace_hierarchy(
        snapshot,
        replace(
            snapshot.hierarchy,
            work=replace(
                snapshot.hierarchy.work,
                workers=(
                    WorkerEntry("W04", "Diego", details=WorkerDetails(weight_kg=65)),
                ),
            ),
        ),
    )
    workspace.save()
    workspace.close(choice=CloseChoice.DISCARD)
    workspace.switch(str(path), None)
    before = path.read_bytes()
    dialog = WorkerManagementDialog(
        workspace, load_icons(), system, language=Language(language_code)
    )
    try:
        dialog.show()
        dialog.activateWindow()
        dialog.optional_toggle.click()
        _APP.processEvents()
        history = dialog.project_history
        assert history is not None and not history.undo_button.isEnabled()
        field = dialog.weight_input
        field.setFocus()
        field.selectAll()
        QTest.keyClicks(field, "85")
        _APP.processEvents()
        assert field.text() == "85"
        assert history.undo_button.isEnabled()
        assert not history.redo_button.isEnabled()
        assert not workspace.has_unsaved_changes  # Still an unaccepted form draft.
        with patch.object(QMessageBox, "question") as removal:
            QTest.mouseClick(history.undo_button, Qt.LeftButton)
            removal.assert_not_called()
        assert dialog.isVisible()
        assert (
            next(
                w
                for w in workspace.read_hierarchy().hierarchy.work.workers
                if w.worker_id == "W04"
            ).details.weight_kg
            == 65
        )
        assert not history.undo_button.isEnabled() and history.redo_button.isEnabled()
        QTest.mouseClick(history.redo_button, Qt.LeftButton)
        expected = store_body_measurement(85, system, mass=True)
        assert next(
            w
            for w in workspace.read_hierarchy().hierarchy.work.workers
            if w.worker_id == "W04"
        ).details.weight_kg == pytest.approx(expected)
        assert dialog.isVisible() and workspace.has_unsaved_changes
        assert path.read_bytes() == before
        dialog.close()
        assert path.read_bytes() == before
        workspace.save()
        with AssessmentProjectFile.open(path) as saved:
            assert saved.load_hierarchy().work.workers[0].details.weight_kg == (
                pytest.approx(expected)
            )
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("language_code", ("en", "es"))
def test_pending_worker_weight_keeps_native_typing_and_redo_branch(
    tmp_path: Path, language_code: str
) -> None:
    """Pending typing cannot consume shared Redo or create a worker history step.

    Args:
        tmp_path: Disposable native project directory.
        language_code: English or Spanish worker form and history controls.

    Returns:
        None; invalid text stays unaccepted, native typing Undo/Redo stays local,
        and clearing a pending edit re-enables the untouched shared Redo branch.
    """
    from PyQt5.QtCore import Qt
    from PyQt5.QtTest import QTest

    from ergotools.domain.language import Language
    from ergotools.domain.worker_details import WorkerDetails

    workspace = editing_workspace(tmp_path)
    snapshot = workspace.read_hierarchy()
    workspace.replace_hierarchy(
        snapshot,
        replace(
            snapshot.hierarchy,
            work=replace(
                snapshot.hierarchy.work,
                workers=(
                    WorkerEntry("W04", "Diego", details=WorkerDetails(weight_kg=65)),
                ),
            ),
        ),
    )
    workspace.save()
    path = Path(workspace.location)
    workspace.close(choice=CloseChoice.DISCARD)
    workspace.switch(str(path), None)
    before = path.read_bytes()
    dialog = WorkerManagementDialog(
        workspace,
        load_icons(),
        MeasurementSystem.METRIC,
        language=Language(language_code),
    )
    try:
        dialog.show()
        dialog.activateWindow()
        dialog.optional_toggle.click()
        _APP.processEvents()
        history = dialog.project_history
        editing = workspace.editing
        initial_revision = editing.history.revision
        field = dialog.weight_input
        field.setFocus()
        field.selectAll()
        QTest.keyClicks(field, "85")
        assert history.undo_button.isEnabled()
        with patch.object(QMessageBox, "question") as removal:
            QTest.keyClick(field, Qt.Key_Z, Qt.ControlModifier)
            assert field.text() == "65"
            QTest.keyClick(field, Qt.Key_Z, Qt.ControlModifier | Qt.ShiftModifier)
            assert field.text() == "85"
            removal.assert_not_called()
        assert editing.history.revision == initial_revision
        QTest.mouseClick(history.undo_button, Qt.LeftButton)
        assert field.text() == "65" and history.redo_button.isEnabled()
        shared_redo = editing.history.redo_label_key
        field.setFocus()
        field.selectAll()
        QTest.keyClicks(field, "90")
        assert not history.redo_button.isEnabled()
        assert editing.history.redo_label_key == shared_redo
        QTest.keyClick(field, Qt.Key_Z, Qt.ControlModifier)
        assert field.text() == "65" and history.redo_button.isEnabled()
        field.setText("invalid")
        assert dialog.pending_worker_action() is None
        assert not workspace.has_unsaved_changes and path.read_bytes() == before
        field.setText("65")
        assert editing.history.redo_label_key == shared_redo
        assert history.redo_button.isEnabled()
    finally:
        dialog.weight_input.setText("65")
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)

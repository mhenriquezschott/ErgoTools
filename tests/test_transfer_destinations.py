"""Standalone/workplace transfer destinations, consent, atomic replacement and replay.

Every write targets a synthetic temporary project. Distinct inputs/results prove
replacement and rollback preserve exact values, historical owners and unselected tools.
Native UI tests drive the real destination tree and confirmation boundary.
"""

import sqlite3
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.saved_results import calculate_saved_result
from ergotools.application.session import DocumentKey
from ergotools.bootstrap import create_window
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessment_transfer import StandaloneDestination, TransferRequest
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_catalog import JobCatalog, WorkerJobAssignment
from ergotools.domain.language import Language
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.saved_result_store import SavedResultStore
from ergotools.presentation.desktop.worker_search_dialog import WorkerSearchDialog
from ergotools.presentation.desktop.worker_transfer_dialog import WorkerTransferDialog
from tests.test_optional_assessment_context import source_for
from tests.test_workplace_assignment_workflow import (
    STATION,
    open_private,
    seed_workplace_source,
)


def seed_destination(
    tmp_path: Path,
    kind: AssessmentKind,
    assigned: bool,
    standalone: bool,
    occupied: bool,
) -> Path:
    """Prepare distinct source/target, historical and unselected-tool observations.

    Args:
        tmp_path: Private native fixture directory.
        kind: Tool copied or moved.
        assigned: Attach the source to A's station when True.
        standalone: Target B's standalone tool rather than station owner 2.
        occupied: Store an existing destination tool requiring replacement consent.

    Returns:
        Closed project path; all results are calculated with approved existing formulas.
    """
    path = seed_workplace_source(tmp_path, kind)
    with AssessmentProjectFile.open(path) as project:
        work = project.load_hierarchy().work
        jobs = JobCatalog(
            work.project_id,
            assignments=(
                WorkerJobAssignment(
                    1, work.worker_context("A", STATION.at_shift("1")), None
                ),
                WorkerJobAssignment(
                    2, work.worker_context("B", STATION.at_shift("1")), None
                ),
                WorkerJobAssignment(
                    3,
                    work.worker_context("B", STATION.at_shift("1")),
                    None,
                    active=False,
                ),
            ),
        )
        project.save_jobs(jobs)
        if assigned:
            project.associate_assessment("source", 1)
        source = source_for(kind)
        different = replace(source, tasks=(replace(source.tasks[0], repetitions=777),))
        other = next(k for k in AssessmentKind if k is not kind)
        for identity, owner, tool, state in (
            ("historical", 3, kind, different),
            ("other-tool", None, other, source_for(other)),
            *(
                ([("target", None if standalone else 2, kind, different)])
                if occupied
                else []
            ),
        ):
            project.create_historical_assessment(
                AssignmentAssessment(identity, owner, tool, "B"),
                state,
                result=calculate_saved_result(
                    DocumentKey(work.project_id, identity),
                    state,
                    project.metadata.default_units,
                ),
            )
    return path


@pytest.mark.parametrize("kind", list(AssessmentKind))
@pytest.mark.parametrize("assigned", (False, True))
@pytest.mark.parametrize("standalone", (False, True))
@pytest.mark.parametrize("occupied", (False, True))
@pytest.mark.parametrize("move", (False, True))
def test_transfer_destination_matrix_exact_replay_and_save(
    tmp_path: Path,
    kind: AssessmentKind,
    assigned: bool,
    standalone: bool,
    occupied: bool,
    move: bool,
) -> None:
    """All source/target modes preserve results, consent, history and durable ownership.

    Args:
        tmp_path: Private native project directory.
        kind: LiFFT, DUET and ST independently.
        assigned: Assigned source or standalone source.
        standalone: Standalone target or active workplace target.
        occupied: Existing target requires consent; historical data stays separate.
        move: Move removes selected source only; Copy retains it.

    Returns:
        None; one Undo restores the exact prior project and Redo/Save reopens correctly.
    """
    path = seed_destination(tmp_path, kind, assigned, standalone, occupied)
    original = path.read_bytes()
    ws = open_private(path)
    try:
        jobs, history = ws.read_jobs().jobs, ws.read_history().history
        source, result = ws.active.state, ws.historical_result()
        work = ws.read_hierarchy().hierarchy.work
        destination = (
            StandaloneDestination(work.project_id, "B")
            if standalone
            else work.worker_context("B", STATION.at_shift("1"))
        )
        request = TransferRequest(
            1 if assigned else None, destination, (kind,), move, "A"
        )
        if occupied:
            with pytest.raises(ValueError, match="already contains"):
                ws.transfer_assessments(
                    ws.read_jobs(), ws.read_history(), request, {kind: "copied"}
                )
            assert ws.read_history().history == history
        request = replace(request, replace_existing=occupied)
        assert ws.transfer_assessments(
            ws.read_jobs(), ws.read_history(), request, {kind: "copied"}
        ).completed
        after = ws.read_history().history
        assert ws.read_jobs().jobs == jobs
        assert ws.assessment_source("copied") == source
        assert ws.saved_assessment_result("copied") == result
        assert any(e.document_id == "source" for e in after.entries) is not move
        assert not any(e.document_id == "target" for e in after.entries)
        assert any(e.document_id == "historical" for e in after.entries)
        assert any(e.document_id == "other-tool" for e in after.entries)
        copied = next(e for e in after.entries if e.document_id == "copied")
        assert copied.worker_id == "B" and copied.assignment_id == (
            None if standalone else 2
        )
        assert path.read_bytes() == original
        assert ws.editing.replay(redo=False)
        assert ws.read_history().history == history
        assert ws.assessment_source("source") == source
        assert ws.saved_assessment_result("source") == result
        assert ws.editing.replay(redo=True)
        assert ws.read_history().history == after
        assert ws.save()
        with AssessmentProjectFile.open(path) as saved:
            assert saved.load_history() == after and saved.load_jobs() == jobs
            assert (
                saved.load_saved_result(DocumentKey(work.project_id, "copied"))
                == result
            )
    finally:
        ws.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("kind", list(AssessmentKind))
@pytest.mark.parametrize("move", (False, True))
def test_assigned_to_own_new_standalone(
    tmp_path: Path, kind: AssessmentKind, move: bool
) -> None:
    """A worker's assigned data may create its own missing standalone assessment.

    Args:
        tmp_path: Disposable native project directory.
        kind: Each tool's exact values must survive.
        move: Copy retains assignment source; Move removes only that tool's source.

    Returns:
        None; no additional workplace assignment is manufactured.
    """
    path = seed_destination(tmp_path, kind, True, True, False)
    ws = open_private(path)
    try:
        jobs = ws.read_jobs().jobs
        result = ws.historical_result()
        request = TransferRequest(
            1, StandaloneDestination(jobs.project_id, "A"), (kind,), move
        )
        assert ws.transfer_assessments(
            ws.read_jobs(), ws.read_history(), request, {kind: "own"}
        ).completed
        assert ws.read_jobs().jobs == jobs
        assert ws.read_history().history.standalone_for("A", kind).document_id == "own"
        assert ws.saved_assessment_result("own") == result
    finally:
        ws.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("assigned", (False, True))
def test_identical_destination_rejected_even_with_replace(
    tmp_path: Path, assigned: bool
) -> None:
    """Self-transfer cannot be authorized by replacement consent or Copy/Move mode.

    Args:
        tmp_path: Disposable native project directory.
        assigned: Same workplace or same standalone source/target.

    Returns:
        None; failed requests preserve the source and all saved ownership.
    """
    kind = AssessmentKind.LIFFT
    path = seed_destination(tmp_path, kind, assigned, True, False)
    ws = open_private(path)
    try:
        before = ws.read_history().history
        destination = (
            ws.read_hierarchy().hierarchy.work.worker_context(
                "A", STATION.at_shift("1")
            )
            if assigned
            else StandaloneDestination(before.project_id, "A")
        )
        for move in (False, True):
            with pytest.raises(ValueError, match="identical"):
                ws.transfer_assessments(
                    ws.read_jobs(),
                    ws.read_history(),
                    TransferRequest(
                        1 if assigned else None, destination, (kind,), move, "A", True
                    ),
                    {kind: "same"},
                )
            assert ws.read_history().history == before
    finally:
        ws.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("standalone", (False, True))
def test_replacement_write_failure_restores_original_target(
    tmp_path: Path, standalone: bool
) -> None:
    """A failure after destination deletion rolls back source, target and sole results.

    Args:
        tmp_path: Private native project directory.
        standalone: Existing standalone or workplace destination.

    Returns:
        None; no partial removal/replacement is visible after the failed transaction.
    """
    kind = AssessmentKind.LIFFT
    path = seed_destination(tmp_path, kind, True, standalone, True)
    ws = open_private(path)
    try:
        before = ws.read_history().history
        target_result = ws.saved_assessment_result("target")
        destination = (
            StandaloneDestination(before.project_id, "B")
            if standalone
            else ws.read_hierarchy().hierarchy.work.worker_context(
                "B", STATION.at_shift("1")
            )
        )
        with (
            patch.object(
                SavedResultStore,
                "write",
                side_effect=sqlite3.OperationalError("write failed"),
            ),
            pytest.raises(sqlite3.OperationalError),
        ):
            ws.transfer_assessments(
                ws.read_jobs(),
                ws.read_history(),
                TransferRequest(1, destination, (kind,), True, replace_existing=True),
                {kind: "failed"},
            )
        assert ws.read_history().history == before
        assert ws.saved_assessment_result("target") == target_result
        assert ws.active.document.document_id == "source"
    finally:
        ws.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("move", (False, True))
def test_native_standalone_selection_replace_cancel_confirm_and_self_block(
    tmp_path: Path, language: Language, move: bool
) -> None:
    """The real destination tree exposes standalone values and replacement warnings.

    Args:
        tmp_path: Disposable native project and preferences.
        language: English/Spanish UI values retain exact typed ownership.
        move: Exercise both Copy and Move confirmation/replay.

    Returns:
        None; Cancel writes nothing, confirmed transfer replaces only the chosen target.
    """
    path = seed_destination(tmp_path, AssessmentKind.LIFFT, False, True, True)
    w = create_window(
        tmp_path / "ui.json", original_controls=True, original_navigation=True
    )
    dialog = None
    try:
        w.open_project_location(str(path))
        ws = w.presenter.workspace
        before = ws.read_history().history
        dialog = WorkerTransferDialog(
            ws,
            None,
            w.icons,
            lambda request: CloseChoice.SAVE,
            source_worker_id="A",
            language=language,
            parent=w,
        )
        dialog.show()
        dialog.move_radio.setChecked(move)
        dialog.workplace_tree.setCurrentItem(dialog.standalone_item)
        for row in range(dialog.worker_table.rowCount()):
            if dialog.worker_table.item(row, 0).text() == "A":
                dialog.worker_table.selectRow(row)
        QTest.qWait(20)
        assert (
            not dialog.shift_combo.isEnabled()
            and not dialog.transfer_button.isEnabled()
        )
        for row in range(dialog.worker_table.rowCount()):
            if dialog.worker_table.item(row, 0).text() == "B":
                dialog.worker_table.selectRow(row)
        assert dialog.transfer_button.isEnabled()
        assert "%" in dialog.standalone_item.text(2)
        assert (
            "replaced" if language is Language.ENGLISH else "reemplazarán"
        ) in dialog.preview_label.text()
        with patch.object(dialog, "confirm_transfer", return_value=False):
            dialog.transfer_button.click()
        assert not dialog.completed and ws.read_history().history == before
        with (
            patch.object(dialog, "confirm_transfer", return_value=True),
            patch.object(dialog, "show_success"),
        ):
            dialog.transfer_button.click()
        assert dialog.completed
        assert not any(
            e.document_id == "target" for e in ws.read_history().history.entries
        )
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            w.history_actions.replay(redo=False)
        assert ws.read_history().history == before
        assert ws.active.document.document_id == "source"
        # Canonical Find keeps standalone first, while All remains its initial scope.
        from datetime import date

        from ergotools.presentation.desktop.worker_search_dialog import (
            search_assessments,
        )

        rows = search_assessments(
            ws.read_hierarchy().hierarchy,
            ws.read_jobs().jobs,
            ws.read_history().history,
            AssessmentKind.LIFFT,
            year=date.today().year,
        )
        find = WorkerSearchDialog(
            rows,
            ws.read_hierarchy().hierarchy,
            AssessmentKind.LIFFT,
            w.icons,
            language=language,
            parent=w,
        )
        assert find.workplace_tree.topLevelItem(0).data(0, Qt.UserRole) == (
            "",
            "",
            "",
            "",
        )
        assert find.workplace_tree.topLevelItem(1).data(0, Qt.UserRole) == ()
        find.close()
        find.deleteLater()
    finally:
        if dialog is not None:
            dialog.close()
            dialog.deleteLater()
        w.presenter.workspace.close(choice=CloseChoice.DISCARD)
        w.close()
        w.deleteLater()


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_replacement_drops_retained_destination_session(
    tmp_path: Path, kind: AssessmentKind
) -> None:
    """Revisiting a replaced target loads copied inputs instead of its retired session.

    Args:
        tmp_path: Private synthetic native project directory.
        kind: Tool-specific retained sessions share the invalidation boundary.

    Returns:
        None; Copy replaces B independently and shared Undo restores its prior values.
    """
    path = seed_destination(tmp_path, kind, False, True, True)
    ws = open_private(path)
    try:
        source = ws.active.state
        ws.browse_document("target")
        previous = ws.active.state
        assert source != previous
        ws.browse_document("source")
        request = TransferRequest(
            None,
            StandaloneDestination(ws.read_jobs().jobs.project_id, "B"),
            (kind,),
            source_worker_id="A",
            replace_existing=True,
        )
        ws.transfer_assessments(
            ws.read_jobs(), ws.read_history(), request, {kind: "copied"}
        )
        ws.browse_document("copied")
        assert ws.active.state == source
        assert ws.editing.replay(redo=False)
        ws.browse_document("target")
        assert ws.active.state == previous
    finally:
        ws.close(choice=CloseChoice.DISCARD)


def test_standalone_destination_works_without_workplace_or_shift(
    tmp_path: Path,
) -> None:
    """Independent-only projects need no dummy organization to transfer assessments.

    Args:
        tmp_path: Disposable native project and UI preferences directory.

    Returns:
        None; standalone Copy creates B's source without any organization records.
    """
    from ergotools.domain.work_catalog import WorkCatalog, WorkerEntry
    from ergotools.domain.work_hierarchy import WorkHierarchy
    from tests.test_optional_assessment_context import META

    path = tmp_path / "independent.ergprj"
    with AssessmentProjectFile.create_empty(path, META) as project:
        project.save_hierarchy(
            WorkHierarchy(
                WorkCatalog(
                    META.project_id, (WorkerEntry("A"), WorkerEntry("B")), (), ()
                )
            )
        )
        project.create_historical_assessment(
            AssignmentAssessment("source", None, AssessmentKind.LIFFT, "A"),
            source_for(AssessmentKind.LIFFT),
        )
    w = create_window(tmp_path / "ui.json", original_navigation=True)
    dialog = None
    try:
        w.open_project_location(str(path))
        ws = w.presenter.workspace
        dialog = WorkerTransferDialog(
            ws,
            None,
            w.icons,
            lambda request: CloseChoice.SAVE,
            source_worker_id="A",
            language=Language.ENGLISH,
            parent=w,
        )
        dialog.workplace_tree.setCurrentItem(dialog.standalone_item)
        for row in range(dialog.worker_table.rowCount()):
            if dialog.worker_table.item(row, 0).text() == "B":
                dialog.worker_table.selectRow(row)
        assert not dialog.shift_combo.count() and dialog.transfer_button.isEnabled()
        assert "will be created" in dialog.preview_label.text()
        with (
            patch.object(dialog, "confirm_transfer", return_value=True),
            patch.object(dialog, "show_success"),
        ):
            dialog.perform_transfer()
        assert dialog.completed
        assert ws.read_history().history.standalone_for("B", AssessmentKind.LIFFT)
        assert not ws.read_jobs().jobs.assignments
    finally:
        if dialog is not None:
            dialog.close()
            dialog.deleteLater()
        w.presenter.workspace.close(choice=CloseChoice.DISCARD)
        w.close()
        w.deleteLater()


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_main_move_opens_standalone_target_and_undo_restores_source(
    tmp_path: Path, kind: AssessmentKind
) -> None:
    """Moving the displayed assessment leaves the user viewing its new exact owner.

    Args:
        tmp_path: Disposable native project and application preferences directory.
        kind: Each tool's current result and source selection remain coherent.

    Returns:
        None; Move opens B's standalone, and one Undo restores A's assigned source.
    """
    path = seed_destination(tmp_path, kind, True, True, True)
    w = create_window(
        tmp_path / "ui.json", original_controls=True, original_navigation=True
    )
    try:
        w.open_project_location(str(path))
        w.assessment_tabs.setCurrentIndex(list(AssessmentKind).index(kind))
        w.navigate_worker("A")
        ws = w.presenter.workspace
        source, result = ws.active.state, ws.historical_result()

        def choose(dialog: WorkerTransferDialog) -> int:
            """Drive Move to B's saved standalone through the existing modal host.

            Args:
                dialog: Real owned Transfer window; confirmation is patched separately.

            Returns:
                Accepted only after its actual transaction completes.
            """
            dialog.move_radio.setChecked(True)
            dialog.workplace_tree.setCurrentItem(dialog.standalone_item)
            for row in range(dialog.worker_table.rowCount()):
                if dialog.worker_table.item(row, 0).text() == "B":
                    dialog.worker_table.selectRow(row)
            dialog.perform_transfer()
            assert dialog.completed
            return 1

        with (
            patch.object(WorkerTransferDialog, "exec", choose),
            patch.object(WorkerTransferDialog, "confirm_transfer", return_value=True),
            patch.object(WorkerTransferDialog, "show_success"),
        ):
            w.main_navigation.buttons["transfer"].click()
        assert w.assessment_navigation.view.worker_id == "B"
        assert w.assessment_navigation.view.workplace is None
        assert ws.active.state == source and ws.historical_result() == result
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            w.history_actions.replay(redo=False)
        assert w.assessment_navigation.view.worker_id == "A"
        assert w.assessment_navigation.view.assignment_id == 1
        assert ws.active.state == source and ws.historical_result() == result
    finally:
        w.presenter.workspace.close(choice=CloseChoice.DISCARD)
        w.close()
        w.deleteLater()


@pytest.mark.parametrize("move", (False, True))
def test_mixed_tool_replacement_late_failure_and_retry(
    tmp_path: Path, move: bool
) -> None:
    """Mixed existing/new targets roll back together, preserving unselected tool data.

    Args:
        tmp_path: Disposable native project directory.
        move: Both Copy and Move retain every source if the second result write fails.

    Returns:
        None; retry succeeds with exact selected results and B's unselected DUET intact.
    """
    path = seed_destination(tmp_path, AssessmentKind.LIFFT, True, True, True)
    with AssessmentProjectFile.open(path) as project:
        for kind in (AssessmentKind.DUET, AssessmentKind.TST):
            state = source_for(kind)
            identity = "source-" + kind.value
            project.create_historical_assessment(
                AssignmentAssessment(identity, 1, kind, "A"),
                state,
                result=calculate_saved_result(
                    DocumentKey(project.metadata.project_id, identity),
                    state,
                    project.metadata.default_units,
                ),
            )
    ws = open_private(path)
    try:
        before = ws.read_history().history
        saved = {
            e.document_id: ws.saved_assessment_result(e.document_id)
            for e in before.entries
        }
        kinds = (AssessmentKind.LIFFT, AssessmentKind.TST)
        ids = {kind: "copy-" + kind.value for kind in kinds}
        request = TransferRequest(
            1,
            StandaloneDestination(before.project_id, "B"),
            kinds,
            move,
            replace_existing=True,
        )
        original_write = SavedResultStore.write
        calls = 0

        def fail_second(
            store: SavedResultStore, key: DocumentKey, payload: str
        ) -> None:
            """Write the first result, then fail the second inside the transaction.

            Args:
                store: Existing transaction-owned result adapter.
                key: Exact newly allocated copied source identity.
                payload: Serialized source-bound saved calculation.

            Returns:
                None for the first write.

            Raises:
                sqlite3.OperationalError: Simulated second result write failure.
            """
            nonlocal calls
            calls += 1
            if calls == 2:
                raise sqlite3.OperationalError("second result failed")
            original_write(store, key, payload)

        with (
            patch.object(SavedResultStore, "write", fail_second),
            pytest.raises(sqlite3.OperationalError),
        ):
            ws.transfer_assessments(ws.read_jobs(), ws.read_history(), request, ids)
        assert calls == 2 and ws.read_history().history == before
        assert {
            e.document_id: ws.saved_assessment_result(e.document_id)
            for e in before.entries
        } == saved
        assert ws.transfer_assessments(
            ws.read_jobs(), ws.read_history(), request, ids
        ).completed
        assert ws.saved_assessment_result(ids[AssessmentKind.LIFFT]) == saved["source"]
        assert (
            ws.saved_assessment_result(ids[AssessmentKind.TST]) == saved["source-tst"]
        )
        assert ws.saved_assessment_result("other-tool") == saved["other-tool"]
        assert ws.saved_assessment_result("source-duet") == saved["source-duet"]
    finally:
        ws.close(choice=CloseChoice.DISCARD)

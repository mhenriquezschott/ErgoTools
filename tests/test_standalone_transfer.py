"""Standalone sources use the existing Transfer Copy/Move workflow and transaction.

All projects are disposable. Exact results, ownership, shared history and main Save
are checked for all three tools; no production fixture is written.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QTreeWidgetItem

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.bootstrap import create_window
from ergotools.domain.assessment_transfer import TransferRequest
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.worker_transfer_dialog import WorkerTransferDialog
from tests.test_workplace_assignment_workflow import (
    STATION,
    open_private,
    seed_workplace_source,
)


@pytest.mark.parametrize("kind", list(AssessmentKind))
@pytest.mark.parametrize("move", [False, True])
def test_standalone_copy_move_exact_results_replay_save(
    tmp_path: Path, kind: AssessmentKind, move: bool
) -> None:
    """Transfer one tool to the same worker's station without a preliminary association.

    Args:
        tmp_path: Private native project directory.
        kind: All three ergonomic models retain their exact source-bound outputs.
        move: Copy retains standalone ownership; Move removes only its source.

    Returns:
        None; one history step restores both owners and main Save persists the data.
    """
    path = seed_workplace_source(tmp_path, kind)
    before = path.read_bytes()
    workspace = open_private(path)
    try:
        result = workspace.historical_result()
        work = workspace.read_hierarchy().hierarchy.work
        request = TransferRequest(
            None, work.worker_context("A", STATION.at_shift("1")), (kind,), move, "A"
        )
        assert workspace.transfer_assessments(
            workspace.read_jobs(), workspace.read_history(), request, {kind: "copy"}
        ).completed
        history = workspace.read_history().history
        assert (history.standalone_for("A", kind) is None) == move
        assert history.current_for(1, kind).document_id == "copy"
        assert workspace.saved_assessment_result("copy") == result
        assert path.read_bytes() == before
        assert workspace.editing.replay(redo=False)
        assert len(workspace.read_history().history.entries) == 1
        assert not workspace.read_jobs().jobs.assignments
        assert workspace.editing.replay(redo=True)
        assert workspace.save()
        with AssessmentProjectFile.open(path) as saved:
            assert saved.load_history() == history
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("move", [False, True])
def test_main_transfer_supports_standalone_source_and_user_operation(
    tmp_path: Path, move: bool
) -> None:
    """The sole toolbar Transfer opens standalone data and honors Copy/Move selection.

    Args:
        tmp_path: Private project/preferences directory.
        move: Explicit selection made in the existing Transfer operation panel.

    Returns:
        None; no duplicate copy button exists; Transfer routes the chosen operation.
    """
    path = seed_workplace_source(tmp_path, AssessmentKind.LIFFT)
    window = create_window(
        tmp_path / "ui.json", original_navigation=True, enable_vtk=False
    )
    window.open_project_location(str(path))
    workspace = window.presenter.workspace

    def choose(dialog: WorkerTransferDialog) -> int:
        """Drive the existing three-panel form with exact tree/table identities.

        Args:
            dialog: The real Transfer modal; source is the standalone worker A.

        Returns:
            Accepted only after the normal transaction succeeds.
        """
        assert dialog.source_assignment_id is None and dialog.source_worker_id == "A"
        assert "Standalone" in dialog.source_path_label.text()
        for row in range(dialog.worker_table.rowCount()):
            if dialog.worker_table.item(row, 0).data(Qt.ItemDataRole.UserRole) == "A":
                dialog.worker_table.selectRow(row)
        nodes = list(
            dialog.workplace_tree.findItems(
                "ST01", Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive, 0
            )
        )
        assert nodes and isinstance(nodes[0], QTreeWidgetItem)
        dialog.workplace_tree.setCurrentItem(nodes[0])
        dialog.shift_combo.setCurrentText("1")
        (dialog.move_radio if move else dialog.copy_radio).setChecked(True)
        assert dialog.transfer_button.isEnabled()
        dialog.transfer_button.click()
        assert dialog.completed
        return QDialog.Accepted

    try:
        assert "copy_workplaces" not in window.main_navigation.buttons
        with (
            patch.object(WorkerTransferDialog, "exec", choose),
            patch.object(WorkerTransferDialog, "confirm_transfer", return_value=True),
            patch.object(WorkerTransferDialog, "show_success"),
        ):
            window.main_navigation.buttons["transfer"].click()
        history = workspace.read_history().history
        assert (history.standalone_for("A", AssessmentKind.LIFFT) is None) == move
        assert history.current_for(1, AssessmentKind.LIFFT) is not None
    finally:
        workspace.close(choice=CloseChoice.DISCARD)
        window.close()
        window.deleteLater()


def test_standalone_move_keeps_other_workers_and_unselected_tools(
    tmp_path: Path,
) -> None:
    """None assignment ownership never conflates workers or removes an unselected tool.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; only A's LiFFT source moves, leaving A's DUET and B's LiFFT intact.
    """
    from ergotools.domain.assessment_history import AssignmentAssessment
    from tests.test_optional_assessment_context import source_for

    path = seed_workplace_source(tmp_path, AssessmentKind.LIFFT)
    with AssessmentProjectFile.open(path) as project:
        for document_id, worker, kind in (
            ("b-lifft", "B", AssessmentKind.LIFFT),
            ("a-duet", "A", AssessmentKind.DUET),
        ):
            project.create_historical_assessment(
                AssignmentAssessment(document_id, None, kind, worker), source_for(kind)
            )
    workspace = open_private(path)
    try:
        work = workspace.read_hierarchy().hierarchy.work
        request = TransferRequest(
            None,
            work.worker_context("A", STATION.at_shift("1")),
            (AssessmentKind.LIFFT,),
            True,
            "A",
        )
        workspace.transfer_assessments(
            workspace.read_jobs(),
            workspace.read_history(),
            request,
            {AssessmentKind.LIFFT: "moved"},
        )
        history = workspace.read_history().history
        assert history.standalone_for("A", AssessmentKind.DUET).document_id == "a-duet"
        assert (
            history.standalone_for("B", AssessmentKind.LIFFT).document_id == "b-lifft"
        )
        assert history.standalone_for("A", AssessmentKind.LIFFT) is None
    finally:
        workspace.close(choice=CloseChoice.DISCARD)

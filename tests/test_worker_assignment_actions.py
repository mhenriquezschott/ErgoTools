"""Worker assignment changes/removal through immutable services and real Qt forms.

Test layer: synthetic catalogs and disposable native projects verify history protection,
placement eligibility, cancellation, failed commits and localized row actions. No
operational/reference project is written and no solver model is changed.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtWidgets import QApplication, QMessageBox, QPushButton

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.job_assignment import change_worker_assignment
from ergotools.application.settings import Language
from ergotools.bootstrap import load_icons
from ergotools.domain.job_catalog import JobPlacement, WorkerJobAssignment
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.worker_management_dialog import (
    WorkerManagementDialog,
)
from ergotools.presentation.desktop.workplace_assignment_dialog import (
    WorkplaceAssignmentDialog,
)
from tests.test_history_persistence import ENTRY, SOURCE
from tests.test_job_classification import CATALOG, OWNER, TODAY
from tests.test_workspace_job_risk import workspace_at

# Retain the approved Qt application throughout form creation and owned teardown.
_APP = QApplication.instance() or QApplication([])


def test_change_remove_preserve_historical_owner() -> None:
    """Changing and ending active rows never reclassifies historical assessment owners.

    Args:
        None.

    Returns:
        None; assert exact original ownership/metadata, active successor and closure.
    """
    changed = change_worker_assignment(
        CATALOG, "w", 1, 2, effective_date=TODAY, new_assignment_id=2
    )
    previous, successor = changed.jobs.assignments
    assert previous.worker == OWNER and previous.placement_id == 1
    assert previous.notes == "original" and not previous.active
    assert successor.active and successor.placement_id == 2
    removed = change_worker_assignment(
        changed.jobs, "w", 2, None, effective_date=TODAY, new_assignment_id=3
    )
    assert not any(a.active for a in removed.jobs.assignments)
    assert len(removed.jobs.assignments) == 2
    assert CATALOG.assignments[0].active


@pytest.mark.parametrize(
    "worker,identity,placement",
    [("other", 1, 2), ("w", 9, 2), ("w", 1, 99), ("w", 1, True)],
)
def test_invalid_assignment_change_is_atomic(
    worker: str, identity: int, placement: int
) -> None:
    """Reject foreign identities and unavailable/untyped destinations without mutation.

    Args:
        worker: Requested owner, possibly foreign.
        identity: Requested source assignment identity, possibly absent.
        placement: Requested destination identity, possibly absent or boolean.

    Returns:
        None; the source catalog remains active and unchanged after rejection.
    """
    with pytest.raises(ValueError):
        change_worker_assignment(
            CATALOG,
            worker,
            identity,
            placement,
            effective_date=TODAY,
            new_assignment_id=2,
        )
    assert CATALOG.assignments[0].active


def test_change_can_move_workplace_but_never_overwrite_existing_assignment() -> None:
    """Allow an eligible new station/shift and reject occupied destinations and no-ops.

    Args:
        None.

    Returns:
        None; assert exact destination, original ownership and duplicate protection.
    """
    place = replace(OWNER.workplace, shift_id="Night")
    catalog = replace(
        CATALOG, placements=(*CATALOG.placements, JobPlacement(3, "k", place))
    )
    changed = change_worker_assignment(
        catalog, "w", 1, 3, effective_date=TODAY, new_assignment_id=2
    )
    assert changed.jobs.assignments[-1].worker.workplace == place
    occupied = replace(
        catalog,
        assignments=(
            *catalog.assignments,
            WorkerJobAssignment(2, replace(OWNER, workplace=place), 3),
        ),
    )
    with pytest.raises(ValueError, match="already has"):
        change_worker_assignment(
            occupied, "w", 1, 3, effective_date=TODAY, new_assignment_id=3
        )
    assert (
        change_worker_assignment(
            CATALOG, "w", 1, 1, effective_date=TODAY, new_assignment_id=2
        ).jobs
        is CATALOG
    )


@pytest.mark.parametrize("language", list(Language))
def test_row_actions_change_remove_and_reopen(
    tmp_path: Path, language: Language
) -> None:
    """Commit real row actions while preserving worker drafts and saved assessment data.

    Args:
        tmp_path: Pytest-owned directory for a synthetic native project and settings.
        language: Initial supported UI language used for captions and confirmations.

    Returns:
        None; cancellation, error, change/removal and reopen retain historical sources.
    """
    workspace = workspace_at(tmp_path)
    jobs = workspace.read_jobs()
    placement = jobs.jobs.placements[0]
    dialog = WorkerManagementDialog(
        workspace, load_icons(), MeasurementSystem.METRIC, language=language
    )
    try:
        identity = jobs.jobs.assignments[0].assignment_id
        dialog.first_name_input.setText("Unsaved name")
        assert dialog.assignment_table.columnCount() == 7
        actions = dialog.assignment_table.cellWidget(0, 6).findChildren(QPushButton)
        assert len(actions) == 2 and all(b.accessibleName() for b in actions)
        with patch.object(
            WorkplaceAssignmentDialog,
            "exec",
            return_value=WorkplaceAssignmentDialog.Rejected,
        ):
            actions[0].click()
        assert dialog._jobs.jobs == jobs.jobs
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.No):
            actions[1].click()
        assert dialog._jobs.jobs == jobs.jobs
        combo = dialog.assignment_table.cellWidget(0, 5)
        combo.setCurrentIndex(combo.findData(2))
        with pytest.raises(ValueError, match="Save dropdown"):
            dialog.edit_worker_assignment(identity, remove=True)
        combo.setCurrentIndex(combo.findData(placement.placement_id))

        def choose(picker: WorkplaceAssignmentDialog) -> int:
            """Accept the actual placement picker contract for another eligible job.

            Args:
                picker: Dialog built by the row action with active placement rows.

            Returns:
                Accepted Qt result with an explicit eligible destination identity.
            """
            assert picker.heading.text() == dialog._text("Change assignment")
            assert len(picker._jobs.placements) == 2
            picker.selected_placement_id = 2
            return WorkplaceAssignmentDialog.Accepted

        with patch.object(WorkplaceAssignmentDialog, "exec", choose):
            actions[0].click()
        assert dialog.first_name_input.text() == "Unsaved name"
        active = next(a for a in dialog._jobs.jobs.assignments if a.active)
        assert active.placement_id == 2 and active.assignment_id != identity
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.Yes):
            dialog.assignment_table.cellWidget(0, 6).findChildren(QPushButton)[
                1
            ].click()
        assert dialog.assignment_table.rowCount() == 0
        assert dialog.first_name_input.text() == "Unsaved name"
        assert dialog.add_assignment_button.isEnabled()
        with AssessmentProjectFile.open(tmp_path / "project.sqlite") as project:
            assert project.load_history().entries == (ENTRY,)
            assert project.load(workspace.active.document) == SOURCE
            assert not any(a.active for a in project.load_jobs().assignments)
            assert (
                project.load_jobs().assignments[0].placement_id
                == placement.placement_id
            )
    finally:
        dialog.close()
        dialog.deleteLater()
        workspace.close(choice=CloseChoice.DISCARD)

"""Real worker/Job subset-copy dialogs preserve sources and share main Save/history.

Presentation integration tests use private native projects with exact calculated inputs.
No operational project or reference data is modified.
"""

from pathlib import Path

import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.job_calculation import calculate_job_measurement
from ergotools.application.saved_results import calculate_saved_result
from ergotools.application.session import DocumentKey
from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.job_assessment_dialog import (
    JobAssessmentDialog,
    JobCopyDialog,
)
from ergotools.presentation.desktop.job_management_dialog import JobManagementDialog
from tests.test_job_calculators import enter_job
from tests.test_workplace_assignment_workflow import open_private, seed_workplace_source

# Retain a native application for every owned modal/dialog in this module.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("worker", (True, False))
def test_selected_tasks_copy_from_both_sources_replay_and_reopen(
    tmp_path: Path,
    worker: bool,
) -> None:
    """Explicit subset Copy preserves source values and publishes only selected inputs.

    Args:
        tmp_path: Disposable native project directory.
        worker: Choose a worker assessment or another Job as the copy source.

    Returns:
        None; subset results, source independence, Undo/Redo and reopen remain exact.
    """
    path = seed_workplace_source(tmp_path, AssessmentKind.LIFFT)
    source = LifftDraft(
        MeasurementSystem.METRIC,
        (LifftTask("a", 30, 49, 100), LifftTask("b", 40, 60, 300)),
    )
    with AssessmentProjectFile.open(path) as project:
        key = DocumentKey(project.metadata.project_id, "source")
        project.save_result(key, calculate_saved_result(key, source, source.system))
    workspace = open_private(path)
    worker_before = workspace.assessment_source("source")
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:
        enter_job(dialog)
        project_id = dialog._jobs.jobs.project_id
        full = calculate_job_measurement(project_id, "J2", source, source.system)
        if not worker:
            dialog.new_job()
            dialog.job_id_combo.setEditText("J2")
            dialog.job_name_input.setText("Source Job")
            assert dialog.accept_pending_job()
            dialog._set_measurement(full)
            dialog.job_id_combo.setCurrentIndex(dialog.job_id_combo.findText("J1"))

        def select_subset() -> None:
            """Choose only task b through the real embedded read-only preview.

            Args:
                None.

            Returns:
                None; explicit Copy owns the sole subset calculation.
            """
            picker = QApplication.activeModalWidget()
            assert isinstance(picker, JobAssessmentDialog if worker else JobCopyDialog)
            node = picker.tree.currentItem()
            node.setExpanded(True)
            identity = "source" if worker else "J2"
            details = picker.task_details[identity]
            details.grid.set_task_selection(("b",))
            assert details.grid.inputs[0][0].isReadOnly()
            picker.use_button.click()

        QTimer.singleShot(0, select_subset)
        if worker:
            dialog.copy_worker_assessment()
        else:
            dialog.copy_job_values()
        expected = calculate_job_measurement(
            project_id,
            "J1",
            LifftDraft(source.system, (source.tasks[1],)),
            source.system,
        )
        assert dialog._measurement(AssessmentKind.LIFFT) == expected
        assert workspace.assessment_source("source") == worker_before
        if not worker:
            assert workspace.read_job_risk().risk.for_job("J2").measurements == (full,)
        assert workspace.editing.replay(redo=False)
        assert dialog._measurement(AssessmentKind.LIFFT).source is None
        assert workspace.editing.replay(redo=True)
        assert dialog._measurement(AssessmentKind.LIFFT) == expected
        dialog.close()
        assert workspace.save()
        with AssessmentProjectFile.open(path) as project:
            assert project.load_job_risk().for_job("J1").measurements == (expected,)
            assert project.load(key) == source
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)

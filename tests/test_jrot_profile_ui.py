import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox, QTableWidgetItem

from job_risk_repository import job_profiles
from job_window import JobWindow, JobWorkplaceDialog
from main import ErgoTools
from rotation_layout import RotationLayoutWindow
from worker_window import WorkerWindow


app = QApplication.instance() or QApplication([])
messages = []
QMessageBox.information = staticmethod(lambda *args, **kwargs: QMessageBox.Ok)
QMessageBox.critical = staticmethod(lambda *args, **kwargs: QMessageBox.Ok)
QMessageBox.question = staticmethod(lambda *args, **kwargs: QMessageBox.Yes)


def capture_warning(parent, title, message, *args, **kwargs):
    messages.append((title, message))
    return QMessageBox.Ok


QMessageBox.warning = staticmethod(capture_warning)

with tempfile.TemporaryDirectory() as temporary_directory:
    temporary_root = Path(temporary_directory)
    project_path = temporary_root / "ErgoTools_IntegratedTest.ergprj"
    shutil.copy2(ROOT / "tests" / project_path.name, project_path)
    shutil.copytree(
        ROOT / "tests" / "ErgoTools_IntegratedTest_data",
        temporary_root / "ErgoTools_IntegratedTest_data",
    )
    shutil.copytree(
        ROOT / "tests" / "ErgoTools_IntegratedTest_images",
        temporary_root / "ErgoTools_IntegratedTest_images",
    )

    parent = ErgoTools(disable_vtk=True)
    parent.openFilePath(str(project_path))
    parent.editJobName = "Job-S003"

    job_window = JobWindow(parent)
    job_index = job_window.job_id_combo.findText("Job-S003")
    assert job_index >= 0
    job_window.job_id_combo.setCurrentIndex(job_index)
    job_window.loadJobDetails()
    app.processEvents()

    selected = job_window.selectedProfile()
    assert selected["status"] == "approved"
    assert selected["is_current"] == 1
    assert not bool(job_window.risk_table.item(0, 1).flags() & Qt.ItemIsEditable)
    assert job_window.risk_table.item(0, 1).background().color().name() == "#9dff00"

    with sqlite3.connect(parent.projectdatabasePath) as connection:
        initial_profile_count = len(job_profiles(connection, "Job-S003"))

    job_window.newProfileVersion()
    draft = job_window.selectedProfile()
    assert draft["status"] == "draft"
    assert bool(job_window.risk_table.item(0, 1).flags() & Qt.ItemIsEditable)
    job_window.profile_name_input.setText("Observed validation sample")
    job_window.profile_source_combo.setCurrentIndex(
        job_window.profile_source_combo.findData("study")
    )
    job_window.profile_reference_input.setText("UI-SMOKE-2026")
    job_window.approveSelectedProfile()
    app.processEvents()

    approved = job_window.selectedProfile()
    assert approved["status"] == "approved"
    assert approved["is_current"] == 1
    with sqlite3.connect(parent.projectdatabasePath) as connection:
        profiles = job_profiles(connection, "Job-S003")
        assert len(profiles) == initial_profile_count + 1
        assert profiles[0]["name"] == "Observed validation sample"

        current_profile_id = profiles[0]["id"]
        connection.execute(
            "DELETE FROM JobRiskMeasurement WHERE profile_id = ? AND tool_id = 'DUET'",
            (current_profile_id,),
        )
        connection.commit()

    workplace_dialog = JobWorkplaceDialog(
        "Job-S003", parent.projectdatabasePath, job_window
    )
    leaves = [
        item for item in workplace_dialog.iterWorkplaceItems()
        if item.childCount() == 0
    ]
    assert len(leaves) > 1
    assert workplace_dialog.shift_combo.count() > 0
    assert all(
        item.text(2) != "Shift" for item in workplace_dialog.iterWorkplaceItems()
    )
    leaves[0].setCheckState(0, Qt.Checked)
    leaves[1].setCheckState(0, Qt.Checked)
    workplace_dialog.resize(840, 590)
    workplace_dialog.show()
    app.processEvents()
    workplace_dialog.grab().save("/tmp/job_workplace_assignments.png")
    workplace_dialog.saveAssignments()
    with sqlite3.connect(parent.projectdatabasePath) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM JobPlacement WHERE job_id='Job-S003' AND active=1"
        ).fetchone()[0] == 2
        worker_assignment = connection.execute(
            """
            SELECT assignment.worker_id, assignment.id, placement.id
            FROM WorkerAssignment AS assignment
            JOIN JobPlacement AS placement
              ON placement.workplace_context_id = assignment.workplace_context_id
            WHERE placement.job_id = 'Job-S003' AND placement.active = 1
            ORDER BY assignment.worker_id
            LIMIT 1
            """
        ).fetchone()
    assert worker_assignment is not None

    worker_id, assignment_id, placement_id = worker_assignment
    parent.workerComboBox.setCurrentText(worker_id)
    worker_window = WorkerWindow(parent)
    worker_index = worker_window.worker_id_combo.findText(worker_id)
    assert worker_index >= 0
    worker_window.worker_id_combo.setCurrentIndex(worker_index)
    worker_window.loadWorkerDetails()
    worker_window.tabWidget.setCurrentWidget(worker_window.assignments_tab)
    matching_combo = None
    for row in range(worker_window.assignment_table.rowCount()):
        combo = worker_window.assignment_table.cellWidget(row, 5)
        if int(combo.property("assignmentId")) == assignment_id:
            matching_combo = combo
            break
    assert matching_combo is not None
    placement_index = matching_combo.findData(placement_id)
    assert placement_index >= 0
    matching_combo.setCurrentIndex(placement_index)
    worker_window.resize(worker_window.minimumSize())
    worker_window.show()
    app.processEvents()
    assert worker_window.tabWidget.tabBar().count() == 5
    assert worker_window.tabWidget.tabBar().isTabVisible(0)
    assert worker_window.tabWidget.tabBar().isTabVisible(1)
    assert all(
        not worker_window.tabWidget.tabBar().isTabVisible(index)
        for index in range(2, worker_window.tabWidget.count())
    )
    assert matching_combo.view().sizeHintForColumn(0) > 0
    worker_window.grab().save("/tmp/worker_job_assignments.png")
    worker_window.saveWorker()
    with sqlite3.connect(parent.projectdatabasePath) as connection:
        assert connection.execute(
            "SELECT job_placement_id FROM WorkerAssignment WHERE id = ?",
            (assignment_id,),
        ).fetchone()[0] == placement_id

    job_window.newJob()
    job_window.job_id_combo.setEditText("UI-New-Job")
    job_window.job_name_input.setText("UI evidence check")
    job_window.risk_table.item(0, 1).setText("0.0003")
    job_window.profile_name_input.setText("Initial expert estimate")
    job_window.profile_reference_input.setText("EXPERT-UI-2026")
    job_window.profile_methodology_input.setPlainText("Expert consensus")
    job_window.profile_sample_size.setValue(3)
    job_window.saveJob()
    with sqlite3.connect(parent.projectdatabasePath) as connection:
        initial_profile = job_profiles(connection, "UI-New-Job")[0]
        assert initial_profile["status"] == "approved"
        assert initial_profile["is_current"] == 1
        assert initial_profile["name"] == "Initial expert estimate"
        assert initial_profile["source_reference"] == "EXPERT-UI-2026"
        assert initial_profile["methodology"] == "Expert consensus"
        assert initial_profile["sample_size"] == 3

    rotation_window = RotationLayoutWindow(parent)
    rotation_window.timeblocks_combo.setCurrentText("2")
    rotation_window.rotation_table.setRowCount(1)
    rotation_window.rotation_table.setColumnCount(3)
    rotation_window.rotation_table.setItem(0, 1, QTableWidgetItem("Job-S003\n13.2%"))
    rotation_window.rotation_table.setItem(0, 2, QTableWidgetItem("Job-S003\n13.2%"))

    assert rotation_window.validateOptimizationRiskData(("LiFFT",))
    messages.clear()
    assert not rotation_window.validateOptimizationRiskData(("LiFFT", "DUET", "ST"))
    assert messages[-1][0] == "Missing Job Risk Data"
    assert "Job-S003 - DUET" in messages[-1][1]
    assert "measurement is not available" in messages[-1][1]

    job_window.resize(job_window.minimumSize())
    job_window.show()
    app.processEvents()
    assert job_window.profile_tabs.height() >= 200
    assert job_window.risk_table.height() >= 150
    job_window.grab().save("/tmp/job_profile_ui_smoke.png")

    rotation_window.close()
    worker_window.close()
    job_window.close()
    parent.close()

print("JROT profile UI checks passed")

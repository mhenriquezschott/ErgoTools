import os
import shutil
import sqlite3
import sys
import tempfile
import time
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
from rotation_repository import available_scope_contexts
from rotation_scope_dialog import RotationScopeDialog
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
    rotation_window._loaded_scheme = None
    rotation_window._refreshRotationPool()
    rotation_window.workersnumber_combo.setCurrentText("1")
    rotation_window.timeblocks_combo.setCurrentText("2")
    rotation_window._renderCurrentPool()
    worker_id = next(iter(rotation_window._rotation_workers))
    rotation_window.rotation_table.setItem(0, 0, QTableWidgetItem(worker_id))
    rotation_window.rotation_table.setItem(0, 1, QTableWidgetItem("Job-S003"))
    rotation_window.rotation_table.setItem(0, 2, QTableWidgetItem("Job-S003"))
    rotation_window.handleCellChanged(0, 1)

    assert rotation_window.validateOptimizationRiskData(("LiFFT",))
    messages.clear()
    assert not rotation_window.validateOptimizationRiskData(("LiFFT", "DUET", "ST"))
    assert messages[-1][0] == "Missing Job Risk Data"
    assert "Job-S003 - DUET" in messages[-1][1]
    assert "measurement is not available" in messages[-1][1]

    rotation_window.onOptimizeClicked()
    deadline = time.monotonic() + 10
    while rotation_window.optimization_thread.isRunning() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()
    assert not rotation_window.optimization_thread.isRunning()
    assert rotation_window.optimized_table.rowCount() == 1
    assert "Profile v" in rotation_window.optimized_table.item(0, 1).toolTip()

    rotation_window.resize(rotation_window.minimumSize())
    rotation_window.show()
    app.processEvents()
    rotation_window.grab().save("/tmp/jrot_organization_scope.png")

    scope_dialog = RotationScopeDialog(parent.projectdatabasePath, parent=rotation_window)
    assert scope_dialog.shift_combo.count() > 0
    assert scope_dialog.tree.topLevelItemCount() > 0
    scope_dialog.show()
    app.processEvents()
    scope_dialog.grab().save("/tmp/jrot_scope_dialog.png")
    scope_dialog.close()

    with sqlite3.connect(parent.projectdatabasePath) as connection:
        selected_contexts = [
            context["id"] for context in available_scope_contexts(connection)[:3]
        ]
    rotation_window._pending_scope_context_ids = selected_contexts
    rotation_window.workplace_scope_button.setChecked(True)
    rotation_window.applyfilterButtonClicked()
    app.processEvents()
    assert rotation_window._scope_context_ids == selected_contexts
    assert rotation_window._rotation_targets
    assert rotation_window._rotation_workers
    rotation_window.grab().save("/tmp/jrot_workplace_scope.png")

    scoped_worker_id = next(iter(rotation_window._rotation_workers))
    scoped_target_label = next(iter(rotation_window._rotation_targets))
    rotation_window.rotation_table.setItem(0, 0, QTableWidgetItem(scoped_worker_id))
    for column in range(1, 3):
        rotation_window.rotation_table.setItem(
            0, column, QTableWidgetItem(scoped_target_label)
        )
    rotation_window.rotation_combo.setEditText("UI-Scoped-Rotation")
    rotation_window.saveRotationScheme()
    with sqlite3.connect(parent.projectdatabasePath) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM RotationSchemeScope WHERE scheme_id = ?",
            ("UI-Scoped-Rotation",),
        ).fetchone()[0] == len(selected_contexts)
        saved = connection.execute(
            """
            SELECT target.job_placement_id, target.job_risk_profile_id,
                   assignment.worker_assignment_id
            FROM RotationAssignment AS assignment
            JOIN RotationTarget AS target
              ON target.id = assignment.rotation_target_id
            WHERE assignment.scheme_id = ?
            """,
            ("UI-Scoped-Rotation",),
        ).fetchall()
        assert len(saved) == 2
        assert all(all(value is not None for value in row) for row in saved)
    rotation_window.loadRotationDetails()
    assert rotation_window._loaded_scheme["id"] == "UI-Scoped-Rotation"
    assert rotation_window._scope_context_ids == selected_contexts

    complete_target_label = next(
        label
        for label, measurements in rotation_window._rotation_measurements.items()
        if {"LiFFT", "DUET", "ST"}.issubset(measurements)
    )
    for column in range(1, 3):
        rotation_window.rotation_table.setItem(
            0, column, QTableWidgetItem(complete_target_label)
        )
    rotation_window.handleCellChanged(0, 1)
    assert rotation_window.validateOptimizationRiskData(("LiFFT", "DUET", "ST"))

    rotation_window.onOptimizeAllClicked()
    deadline = time.monotonic() + 20
    while rotation_window.optimizeall_thread.isRunning() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()
    assert not rotation_window.optimizeall_thread.isRunning()
    assert rotation_window.compare_all_window.isVisible()
    rotation_window.compare_all_window.grab().save("/tmp/jrot_all_tools_comparison.png")
    rotation_window.compare_all_window.transferToMainWindow()
    app.processEvents()
    assert rotation_window._optimization_mode == "all_tools"
    assert "Profile v" in rotation_window.rotation_table.item(0, 1).toolTip()
    rotation_window.saveRotationScheme()
    with sqlite3.connect(parent.projectdatabasePath) as connection:
        saved_mode, primary_tool = connection.execute(
            "SELECT optimization_mode, primary_tool_id "
            "FROM RotationScheme WHERE id = ?",
            ("UI-Scoped-Rotation",),
        ).fetchone()
        assert saved_mode == "all_tools"
        assert primary_tool is None

    rotation_window.onOptimizeClicked()
    deadline = time.monotonic() + 10
    while rotation_window.optimization_thread.isRunning() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()
    assert not rotation_window.optimization_thread.isRunning()
    rotation_window.onCompareClicked()
    app.processEvents()
    assert rotation_window.compare_window.isVisible()
    rotation_window.compare_window.grab().save("/tmp/jrot_selected_tool_comparison.png")

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

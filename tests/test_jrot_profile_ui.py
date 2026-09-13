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
from job_window import JobWindow
from main import ErgoTools
from rotation_layout import RotationLayoutWindow


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
    parent.job_combo.setCurrentText("Job-S003")

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
        assert len(profiles) == 2
        assert profiles[0]["name"] == "Observed validation sample"

        current_profile_id = profiles[0]["id"]
        connection.execute(
            "DELETE FROM JobRiskMeasurement WHERE profile_id = ? AND tool_id = 'DUET'",
            (current_profile_id,),
        )
        connection.commit()

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
    job_window.close()
    parent.close()

print("JROT profile UI checks passed")

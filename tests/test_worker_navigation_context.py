import os
import shutil
import sys
import tempfile


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
sys.path.insert(0, os.path.abspath("src"))

from PyQt5.QtWidgets import QApplication, QMessageBox

from main import ErgoTools


app = QApplication.instance() or QApplication([])
QMessageBox.information = staticmethod(lambda *args, **kwargs: QMessageBox.Ok)
QMessageBox.warning = staticmethod(lambda *args, **kwargs: QMessageBox.Ok)
QMessageBox.critical = staticmethod(lambda *args, **kwargs: QMessageBox.Ok)
QMessageBox.question = staticmethod(lambda *args, **kwargs: QMessageBox.No)


def worker_index(window, worker_id):
    return next(
        index for index in range(window.workerComboBox.count())
        if window.workerComboBox.itemText(index).split(" ", 1)[0] == worker_id
    )


def invoke_from_nested_signal_path(callback, depth=8):
    if depth:
        return invoke_from_nested_signal_path(callback, depth - 1)
    return callback()


def test_worker_navigation_keeps_exact_assessment_context():
    with tempfile.TemporaryDirectory() as project_root:
        project_path = os.path.join(project_root, "ErgoTools_IntegratedTest.ergprj")
        shutil.copy2("tests/ErgoTools_IntegratedTest.ergprj", project_path)
        shutil.copytree(
            "tests/ErgoTools_IntegratedTest_data",
            os.path.join(project_root, "ErgoTools_IntegratedTest_data"),
        )

        window = ErgoTools(disable_vtk=True)
        window.openFilePath(project_path)
        window.tabWidget.setCurrentIndex(0)
        assert window.setAssessmentWorkplaceContext(
            ("Default", "Default", "Default", "ST04", "1")
        )

        window.workerComboBox.setCurrentIndex(worker_index(window, "SSN004"))
        assert window.numericLabelValue(window.lifft_probability_value_label) == 13.2

        invoke_from_nested_signal_path(
            lambda: window.workerComboBox.setCurrentIndex(worker_index(window, "V001"))
        )
        assert window.station_combo.currentText() == "ST04"
        assert window.context_summary_labels[3].text() == "Station: ST04"
        assert not window._assessment_record_exists_by_tool["LiFFT"]
        assert window.lifft_lever_arm_inputs[0].text() == ""
        assert window.numericLabelValue(window.lifft_probability_value_label) == 0.0
        assert window.assessment_status_detail.text() == "No assessment saved here."
        window.close()


if __name__ == "__main__":
    test_worker_navigation_keeps_exact_assessment_context()
    print("worker navigation assessment context: ok")

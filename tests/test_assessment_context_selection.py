import os
import shutil
import sqlite3
import sys
import tempfile


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
sys.path.insert(0, os.path.abspath("src"))

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox

import main as main_module
from main import ErgoTools, WorkerSearchDialog


app = QApplication.instance() or QApplication([])
QMessageBox.information = staticmethod(lambda *args, **kwargs: QMessageBox.Ok)
QMessageBox.warning = staticmethod(lambda *args, **kwargs: QMessageBox.Ok)
QMessageBox.critical = staticmethod(lambda *args, **kwargs: QMessageBox.Ok)


def worker_index(window, worker_id):
    return next(
        index for index in range(window.workerComboBox.count())
        if window.workerComboBox.itemText(index).split(" ", 1)[0] == worker_id
    )


def test_saved_assessment_search_and_context_selection():
    with tempfile.TemporaryDirectory() as project_root:
        project_path = os.path.join(project_root, "test3.ergprj")
        shutil.copy2("tests/test3.ergprj", project_path)
        shutil.copytree("tests/test3_data", os.path.join(project_root, "test3_data"))
        shutil.copytree("tests/test3_images", os.path.join(project_root, "test3_images"))

        window = ErgoTools(disable_vtk=True)
        window.openFilePath(project_path)
        window.tabWidget.setCurrentIndex(0)
        window.workerComboBox.setCurrentIndex(worker_index(window, "SSN001"))

        default_context = ("Default", "Default", "Default", "Default", "1")
        renew_context = (
            "TheRenewPlant", "TheRenewSection", "TheRenewLine", "TheRenewStation", "1"
        )
        assert window.setAssessmentWorkplaceContext(default_context)
        assert window.numericLabelValue(window.lifft_probability_value_label) == 40.8

        dialog = WorkerSearchDialog(window)
        matching_rows = []
        for row in range(dialog.table.rowCount()):
            item = dialog.table.item(row, 0)
            context = tuple(item.data(Qt.UserRole + 1))
            if item.data(Qt.UserRole) == "SSN001" and context == renew_context:
                matching_rows.append(row)
        assert len(matching_rows) == 1
        dialog.table.selectRow(matching_rows[0])
        app.processEvents()
        assert dialog.selected_worker_id == "SSN001"
        assert tuple(dialog.selected_assessment_context) == renew_context
        dialog.resize(1080, 650)
        dialog.show()
        app.processEvents()
        dialog.grab().save("/tmp/find_assessment_context.png")

        assert window.setAssessmentWorkplaceContext(default_context)
        window.workerComboBox.setCurrentIndex(worker_index(window, "SSN002"))

        class SelectedAssessmentDialog:
            selected_worker_id = "SSN001"
            selected_assessment_context = renew_context

            def __init__(self, parent):
                pass

            def exec_(self):
                return SelectedAssessmentDialog.Accepted

            Accepted = 1

        original_dialog = main_module.WorkerSearchDialog
        main_module.WorkerSearchDialog = SelectedAssessmentDialog
        try:
            window.searchWorkerClicked()
        finally:
            main_module.WorkerSearchDialog = original_dialog

        assert window.workerComboBox.currentText().split(" ", 1)[0] == "SSN001"
        assert [label.text() for label in window.context_summary_labels] == [
            "Plant: TheRenewPlant",
            "Section: TheRenewSection",
            "Line: TheRenewLine",
            "Station: TheRenewStation",
            "Shift: 1",
        ]
        assert window.numericLabelValue(window.lifft_probability_value_label) == 84.0
        assert window._assessment_record_exists_by_tool["LiFFT"]
        window.resize(1550, 1015)
        window.show()
        app.processEvents()
        window.grab().save("/tmp/main_saved_assessment_context.png")

        window.workerComboBox.setCurrentIndex(worker_index(window, "SSN002"))
        assert window.numericLabelValue(window.lifft_probability_value_label) == 0.0
        assert not window._assessment_record_exists_by_tool["LiFFT"]
        assert window.assessment_status_detail.text() == "No assessment saved here."
        app.processEvents()
        window.grab().save("/tmp/main_missing_assessment_context.png")

        with sqlite3.connect(window.projectdatabasePath) as connection:
            for tab_index, tool_id, tool_name in (
                (0, "LiFFT", "LiFFT"),
                (1, "DUET", "DUET"),
                (2, "ST", "Shoulder"),
            ):
                window.tabWidget.setCurrentIndex(tab_index)
                tool_dialog = WorkerSearchDialog(window)
                expected = connection.execute(
                    """SELECT COUNT(*) FROM (
                           SELECT DISTINCT worker_id, plant_name, section_name,
                                           line_name, station_id, shift_id
                           FROM WorkerStationShiftErgoTool WHERE tool_id = ?
                       )""",
                    (tool_id,),
                ).fetchone()[0]
                assert tool_dialog.active_tool_id == tool_id
                assert tool_dialog.active_tool_name == tool_name
                assert tool_dialog.table.rowCount() == expected
                suffix = "assessment" if expected == 1 else "assessments"
                assert tool_dialog.result_count.text() == f"{expected} {suffix}"
                tool_dialog.close()

        dialog.close()
        window.close()


if __name__ == "__main__":
    test_saved_assessment_search_and_context_selection()
    print("assessment context selection: ok")

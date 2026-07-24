import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
sys.path.insert(0, os.path.abspath("src"))

from PyQt5.QtCore import QDate, QPoint, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QLabel, QMessageBox, QToolButton

from main import ErgoTools
from organization_window import OrganizationWindow
from worker_window import WorkerWindow


app = QApplication.instance() or QApplication([])
QMessageBox.information = staticmethod(lambda *args, **kwargs: QMessageBox.Ok)
QMessageBox.warning = staticmethod(lambda *args, **kwargs: QMessageBox.Ok)
QMessageBox.critical = staticmethod(lambda *args, **kwargs: QMessageBox.Ok)

parent = ErgoTools(disable_vtk=True)
parent.openFilePath(os.path.abspath("tests/test3.ergprj"))

parent.tabWidget.setCurrentIndex(0)
parent.lifft_repetitions_inputs[0].setText("10")
parent.lifft_total_damage_value_label.setText("2.1000")
parent.lifft_probability_value_label.setText("50.1")
parent.lifft_total_risk_color = "#FF3B30"
parent.refreshAssessmentSummary()
assert parent.damage_value_label.text() == ">2.0"
assert parent.damage_progress.target_value == 2.0
assert parent.risk_severity_label.text().endswith("High")
assert parent.individual_risk_title.text() == "Individual LiFFT"
assert parent.risk_level_title.text() == "Risk Level"
assert "background: #" in parent.damage_value_label.styleSheet()
assert parent.body_risk_title.text() == "LiFFT Individual Risk Score"
assert parent.project_header_label.text().startswith("Current Project: ")
assert parent.footer_context_label.text().startswith("Current Project: ")
assert parent.statusBar().currentMessage() == "Status: Ready - Assessment data is available."

parent.tabWidget.blockSignals(True)
parent.tabWidget.setCurrentIndex(1)
parent.tabWidget.blockSignals(False)
for field in parent.duet_repetitions_inputs:
    field.clear()
parent.duet_total_damage_value_label.setText("0.0")
parent.duet_probability_value_label.setText("0.0")
parent.duet_total_risk_color = "none"
parent.refreshAssessmentSummary()
assert parent.risk_severity_label.text() == "● Not available"
assert parent.statusBar().currentMessage() == "Status: Incomplete - Enter context and task data."
assert parent.individual_risk_title.text() == "Individual DUET"
assert parent.risk_level_title.text() == "Risk Level"
assert parent.risk_gauge.target_value == 0.0
assert "#d9e1e6" in parent.damage_value_label.styleSheet().lower()
assert "#d9e1e6" in parent.duet_total_damage_value_label.styleSheet().lower()
assert "#d9e1e6" in parent.duet_probability_value_label.styleSheet().lower()
assert parent.body_risk_title.text() == "DUET Individual Risk Score"

parent.tabWidget.blockSignals(True)
parent.tabWidget.setCurrentIndex(2)
parent.tabWidget.blockSignals(False)
parent.tst_repetitions_inputs[0].setText("100")
parent.tst_total_damage_value_label.setText("0.0001")
parent.tst_probability_value_label.setText("5.5")
parent.tst_total_risk_color = "#19B83F"
parent.refreshAssessmentSummary()
parent.any_tst_input_changed = False
parent.resize(1550, 1015)
parent.show()
app.processEvents()
assert parent.individual_risk_title.text() == "Individual Shoulder"
assert parent.risk_level_title.text() == "Risk Level"
assert parent.risk_severity_label.text().endswith("Low")
parent.grab().save("/tmp/main_shoulder_ready.png")
assert parent.individual_risk_title.geometry().right() <= parent.risk_header_widget.contentsRect().right()
assert parent.risk_level_title.geometry().right() <= parent.risk_severity_label.geometry().left()

parent.tst_repetitions_inputs[0].clear()
parent.tst_total_risk_color = "none"
parent.refreshAssessmentSummary()
parent.any_tst_input_changed = False
app.processEvents()
assert parent.risk_severity_label.text() == "● Not available"
parent.grab().save("/tmp/main_shoulder_unavailable.png")
assert parent.risk_level_title.geometry().right() <= parent.risk_severity_label.geometry().left()
status_detail_bottom = parent.assessment_status_detail.mapTo(
    parent.status_card, parent.assessment_status_detail.rect().bottomLeft()
).y()
assert status_detail_bottom <= parent.status_card.contentsRect().bottom()
status_text_height = parent.assessment_status_detail.fontMetrics().boundingRect(
    0, 0, parent.assessment_status_detail.width(), 1000,
    Qt.TextWordWrap, parent.assessment_status_detail.text()
).height()
assert status_text_height <= parent.assessment_status_detail.height()

parent.tabWidget.blockSignals(True)
parent.tabWidget.setCurrentIndex(0)
parent.tabWidget.blockSignals(False)
parent.any_lifft_input_changed = False
parent.any_duet_input_changed = False
parent.resize(1550, 1015)
parent.show()
app.processEvents()
QTest.qWait(800)
app.processEvents()
parent.refreshAssessmentSummary()
parent.grab().save("/tmp/main_damage_over_two.png")
parent.tabWidget.blockSignals(True)
parent.tabWidget.setCurrentIndex(1)
parent.tabWidget.blockSignals(False)
parent.refreshAssessmentSummary()
app.processEvents()
parent.grab().save("/tmp/main_missing_analysis.png")
parent.tabWidget.blockSignals(True)
parent.tabWidget.setCurrentIndex(0)
parent.tabWidget.blockSignals(False)
parent.refreshAssessmentSummary()
assert parent.toolbar.iconSize().width() == 38
assert parent.toolbar.iconSize().height() == 38
assert parent.toolbar.height() == 90
assert parent.toolbar.parentWidget().height() == 112
assert all(button.height() == 75 for button in parent.toolbar.findChildren(QToolButton) if button.text())
brand_logo = parent.findChild(QLabel, "brandLogo")
assert brand_logo is not None
assert brand_logo.pixmap() is not None and not brand_logo.pixmap().isNull()
assert brand_logo.width() >= 80 and brand_logo.height() >= 80
workplace_separators = parent.findChildren(QLabel, "contextArrow")
assert len(workplace_separators) == 4
assert all(label.pixmap() is not None and not label.pixmap().isNull() for label in workplace_separators)


class CameraDirectorProbe:
    def __init__(self):
        self.active_tool = 0
        self.animated_tools = []

    def animateTo(self, index):
        self.animated_tools.append(index)
        self.active_tool = index

    def applyFullBody(self):
        pass


parent.camera_director = CameraDirectorProbe()
parent.vtk_enabled = True
parent.isAnimationAllowed = True
parent.onTabChange(0)
assert parent.camera_director.animated_tools == []
parent.onTabChange(1)
assert parent.camera_director.animated_tools == []
parent.onToolTabClicked(1)
assert parent.camera_director.animated_tools == [1]
parent.camera_director.active_tool = parent.tabWidget.currentIndex()
parent.camera_director.animated_tools.clear()
parent.nextButtonClicked()
app.processEvents()
assert parent.camera_director.animated_tools == []
parent.setMainWorkerAlphabetFilter("A")
app.processEvents()
assert parent.camera_director.animated_tools == []

# Returning a result from PLOT is an explicit tool change and should focus the
# corresponding body region even though the tab is selected programmatically.
parent.camera_director.active_tool = 0
parent.camera_director.animated_tools.clear()
parent.editWorkerID = "Default"
parent.editPlantName = "Default"
parent.editSectionName = "Default"
parent.editLineName = "Default"
parent.editStationName = "Default"
parent.editShiftName = "1"
parent.editToolID = "DUET"
parent.editUnit = "Metric"
parent.loadEditVarsToUI()
app.processEvents()
assert parent.tabWidget.currentIndex() == 1
assert parent.camera_director.animated_tools == [1]
parent.vtk_enabled = False

worker = WorkerWindow(parent)
worker.resize(1400, 800)
worker.show()
worker.optional_toggle.setChecked(True)
app.processEvents()
worker.grab().save("/tmp/worker_revised_fields.png")

form_labels = [label.text() for label in worker.findChildren(QLabel)]
for removed_label in ("Address", "City", "Country", "State/Region", "Postal Code", "Email"):
    assert removed_label not in form_labels
assert any(label in form_labels for label in ("Height (in)", "Height (cm)"))
assert any(label in form_labels for label in ("Weight (lb)", "Weight (kg)"))
assert "Date of hiring" in form_labels
assert "Date of birth" in form_labels
assert worker.dob_input.calendarPopup()
worker.dob_input.setDate(QDate.currentDate().addYears(-20).addDays(1))
assert worker.age_label.text() == "19 years"
QTest.mouseClick(
    worker.dob_input,
    Qt.LeftButton,
    pos=QPoint(worker.dob_input.width() - 10, worker.dob_input.height() // 2),
)
app.processEvents()
worker.dob_input.calendarWidget().grab().save("/tmp/worker_birth_calendar.png")

organization = OrganizationWindow(parent)
organization.resize(1180, 780)
organization.show()
app.processEvents()
organization.grab().save("/tmp/organization_add_element.png")
assert organization.add_child_button.text() == "Add element"

print({"organization_action": organization.add_child_button.text(), "worker_optional_fields": [
    label for label in form_labels if label.startswith(("Height", "Weight")) or label == "Date of hiring"
]})

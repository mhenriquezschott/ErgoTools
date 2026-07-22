import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
sys.path.insert(0, os.path.abspath("src"))

from PyQt5.QtCore import QDate, QPoint, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QLabel, QMessageBox

from main import ErgoTools
from organization_window import OrganizationWindow
from worker_window import WorkerWindow


app = QApplication.instance() or QApplication([])
QMessageBox.information = staticmethod(lambda *args, **kwargs: QMessageBox.Ok)
QMessageBox.warning = staticmethod(lambda *args, **kwargs: QMessageBox.Ok)

parent = ErgoTools(disable_vtk=True)
parent.openFilePath(os.path.abspath("tests/test3.ergprj"))

parent.tabWidget.setCurrentIndex(0)
parent.lifft_total_damage_value_label.setText("2.1000")
parent.lifft_probability_value_label.setText("50.1")
parent.refreshAssessmentSummary()
assert parent.damage_value_label.text() == ">2.0"
assert parent.damage_progress.target_value == 2.0
assert parent.risk_severity_label.text().endswith("High")
assert "background: #" in parent.damage_value_label.styleSheet()
parent.resize(1550, 1015)
parent.show()
app.processEvents()
parent.grab().save("/tmp/main_damage_over_two.png")
brand_logo = parent.findChild(QLabel, "brandLogo")
assert brand_logo is not None
assert brand_logo.pixmap() is not None and not brand_logo.pixmap().isNull()


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

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
sys.path.insert(0, os.path.abspath("src"))

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

organization = OrganizationWindow(parent)
organization.resize(1180, 780)
organization.show()
app.processEvents()
organization.grab().save("/tmp/organization_add_element.png")
assert organization.add_child_button.text() == "Add element"

print({"organization_action": organization.add_child_button.text(), "worker_optional_fields": [
    label for label in form_labels if label.startswith(("Height", "Weight")) or label == "Date of hiring"
]})

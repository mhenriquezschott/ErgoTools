import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
sys.path.insert(0, os.path.abspath("src"))

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

from main import ErgoTools
from plant_layout import PlantLayoutWindow


app = QApplication.instance() or QApplication([])
QMessageBox.information = staticmethod(lambda *args, **kwargs: QMessageBox.Ok)
QMessageBox.warning = staticmethod(lambda *args, **kwargs: QMessageBox.Ok)
QMessageBox.critical = staticmethod(lambda *args, **kwargs: QMessageBox.Ok)

parent = ErgoTools(disable_vtk=True)
parent.openFilePath(os.path.abspath("tests/test3.ergprj"))
window = PlantLayoutWindow(parent)

assert window.minimumWidth() <= 1300
assert window.minimumHeight() <= 900
assert window.maximumWidth() > window.minimumWidth()
assert window.layout() is not None

window.resize(1390, 940)
window.show()
for _ in range(12):
    app.processEvents()
window.grab().save("/tmp/plot_responsive_default.png")
default_canvas_size = window.plantlayout_image.viewport().size()
assert window.minimumSizeHint().width() <= 1390
assert window.minimumSizeHint().height() <= 940
assert window.summaryplot_canvas.geometry().bottom() < window.summaryplot_combo.geometry().top()
for option in (
    window.option1a_option, window.option1b_option,
    window.option1c_radio, window.option1d_radio,
):
    assert option.width() >= option.sizeHint().width()
for metric in (
    window.summaryresult1_label, window.summaryresult2_label,
    window.summaryresult3_label, window.summaryresult4_label,
):
    assert metric.width() >= metric.sizeHint().width()

window.resize(1800, 1080)
for _ in range(8):
    app.processEvents()
window.grab().save("/tmp/plot_responsive_large.png")
large_canvas_size = window.plantlayout_image.viewport().size()

assert large_canvas_size.width() > default_canvas_size.width()
assert large_canvas_size.height() > default_canvas_size.height()
assert window.workerComboBox.count() > 0
assert window.summaryplot_combo.count() > 0
assert window.plantlayout_image.scene() is window.plantlayout_scene
assert all(not button.icon().isNull() for button in (
    window.grtool1_button, window.grtool2_button, window.grtool3_button,
    window.grtool4_button, window.grtool5_button, window.grtool6_button,
    window.grtool7_button, window.grtool8_button, window.grtool9_button,
))

initial_worker_index = window.workerComboBox.currentIndex()
window.nextInfoButtonClicked()
app.processEvents()
assert window.workerComboBox.currentIndex() != initial_worker_index
window.agefrom_edit.setText("30")
window.workerfilter_group.setChecked(True)
window.clearfilterButtonClicked()
assert window.agefrom_edit.text() == ""
assert not window.workerfilter_group.isChecked()

window.resize(1300, 900)
for _ in range(8):
    app.processEvents()
window.grab().save("/tmp/plot_responsive_minimum.png")
assert window.plantlayout_image.viewport().width() >= 500
assert window.plantlayout_image.viewport().height() >= 300

empty_parent = ErgoTools(disable_vtk=True)
empty_window = PlantLayoutWindow(empty_parent)
empty_window.resize(1390, 940)
empty_window.show()
for _ in range(4):
    app.processEvents()
empty_window.grab().save("/tmp/plot_responsive_empty.png")
assert empty_window.layout() is not None
assert empty_window.plantlayout_image.scene() is empty_window.plantlayout_scene

print({
    "default_canvas": (default_canvas_size.width(), default_canvas_size.height()),
    "large_canvas": (large_canvas_size.width(), large_canvas_size.height()),
    "workers": window.workerComboBox.count(),
    "summary_plots": window.summaryplot_combo.count(),
})

QTimer.singleShot(0, app.quit)
app.exec_()

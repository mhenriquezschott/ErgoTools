import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
sys.path.insert(0, os.path.abspath("src"))

from PyQt5.QtCore import QPoint, QTimer, Qt
from PyQt5.QtGui import QImage
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

from main import ErgoTools
from plant_layout import (
    PlantLayoutWindow, PlotGraphSettingsDialog, PlotHighlightDetailsDialog,
    PlotWorkerPickerDialog, PlotWorkplaceFilterDialog,
)


app = QApplication.instance() or QApplication([])
QMessageBox.information = staticmethod(lambda *args, **kwargs: QMessageBox.Ok)
QMessageBox.warning = staticmethod(lambda *args, **kwargs: QMessageBox.Ok)
QMessageBox.critical = staticmethod(lambda *args, **kwargs: QMessageBox.Ok)

parent = ErgoTools(disable_vtk=True)
parent.openFilePath(os.path.abspath("tests/test3.ergprj"))
window = PlantLayoutWindow(parent)

assert window.minimumWidth() <= 1300
assert window.minimumHeight() <= 1045
assert window.maximumWidth() > window.minimumWidth()
assert window.layout() is not None

window.resize(1460, 1060)
window.show()
for _ in range(12):
    app.processEvents()
QTest.qWait(800)
window.grab().save("/tmp/plot_responsive_default.png")
default_canvas_size = window.plantlayout_image.viewport().size()
assert window.minimumSizeHint().width() <= 1460
assert window.minimumSizeHint().height() <= 1060
assert default_canvas_size.width() >= 960
assert default_canvas_size.height() >= 575
assert window.summaryplot_canvas.geometry().bottom() <= window.summaryplot_combo.geometry().top()
assert window.otheroptionsfilter_group.isHidden()
assert window.shiftfilter_group.isHidden()
assert window.toolsfiltersettings_button.isHidden()
assert set(window.plot_tool_buttons) == {"LiFFT", "DUET", "ST"}
assert window.summaryplot_combo.count() == 3
assert window.plot_tool_buttons["LiFFT"].isChecked()
assert window.outcome_group.title() == "LiFFT Tool Outcome"
assert len(window.findChildren(type(window.genderflt_label), "workplaceScopeType")) == 5
for label in (
    window.genderflt_label, window.ageflt_label,
    window.weightftl_label, window.heightflt_label,
):
    assert label.objectName() == "demographicFieldTitle"
for button in window.plot_tool_buttons.values():
    bottom_right = button.mapTo(window.toolfilter_group, button.rect().bottomRight())
    assert bottom_right.y() <= window.toolfilter_group.contentsRect().bottom()
assert not window.agefrom_edit.isVisible()
assert not window.xview_input.isVisible()
assert window.workplace_button.isVisible()
assert window.workplace_button.height() == 52
assert window.workplace_button.text().replace("\n", " ") == "Choose Workplace"
assert window.workplace_button.iconSize().width() == 34
assert window.workplace_button.iconSize().height() == 34
assert window.workplace_scope_values["Plant"].text() == "Default"
assert window.workplace_scope_values["Section"].text() == "All"
assert not window.grtool8_button.isVisible()
assert sum(button.isVisible() for button in (
    window.grtool1_button, window.grtool2_button, window.grtool3_button,
    window.grtool4_button, window.grtool5_button, window.grtool6_button,
    window.grtool7_button, window.grtool8_button, window.grtool9_button,
)) == 8
for icon_name in (
    "zoomplus.png", "zoomminus.png", "actualsize.png",
    "captureimage.png", "opacitytransparency.png",
):
    image = QImage(os.path.join("assets", "ui-icons", icon_name))
    assert image.size().width() == 256 and image.size().height() == 256
    assert image.hasAlphaChannel()
assert abs(window.toolfilter_group.geometry().top() - window.plantfilter_group.geometry().top()) <= 1
assert window.toolfilter_group.geometry().right() < window.plantfilter_group.geometry().left()
workplace_dialog = PlotWorkplaceFilterDialog(window)
workplace_dialog.show()
app.processEvents()
workplace_dialog.grab().save("/tmp/plot_workplace_filter.png")
assert workplace_dialog.tree.topLevelItemCount() > 0
assert tuple(workplace_dialog.tree.topLevelItem(0).data(0, Qt.UserRole)) == ("Default",)
assert all(
    tuple(workplace_dialog.tree.topLevelItem(i).data(0, Qt.UserRole)) != ("__ALL__",)
    for i in range(workplace_dialog.tree.topLevelItemCount())
)
assert all(not workplace_dialog.tree.topLevelItem(i).isExpanded()
           for i in range(workplace_dialog.tree.topLevelItemCount()))
assert "Plant: Default" in workplace_dialog.path_label.text()
assert "Section: All" in workplace_dialog.path_label.text()
assert "Shift: 1" in workplace_dialog.path_label.text()
workplace_dialog.close()
window.applyWorkplaceScope(("Default", "Default", "Default", "ST02"), "1")
assert "ST02" in window.workplace_summary_label.text()
window.applyfilterButtonClicked()
assert window.workerComboBox.count() > 0
specific_workplace_workers = window.workerComboBox.count()
window.restoreDefaultPlantScope()
window.applyfilterButtonClicked()
assert window.workerComboBox.count() >= specific_workplace_workers
assert "Plant: Default" in window.workplace_summary_label.text()
assert "Section: All" in window.workplace_summary_label.text()
assert "Line: All" in window.workplace_summary_label.text()
assert "Station: All" in window.workplace_summary_label.text()
assert "Shift: 1" in window.workplace_summary_label.text()
assert "\nShift: 1" in window.workplace_summary_label.text()
for metric in (
    window.summaryresult1_label, window.summaryresult2_label,
    window.summaryresult3_label, window.summaryresult4_label,
):
    assert metric.width() >= metric.sizeHint().width()

window.resize(1800, 1280)
for _ in range(8):
    app.processEvents()
window.grab().save("/tmp/plot_responsive_large.png")
large_canvas_size = window.plantlayout_image.viewport().size()

assert large_canvas_size.width() > default_canvas_size.width()
assert large_canvas_size.height() > default_canvas_size.height()
assert window.workerComboBox.count() > 0
assert "Section:" not in window.workerComboBox.currentText()
assert window.worker_assignment_label.text()
assert window.summaryplot_combo.count() > 0
assert window.plot_risk_gauge.target_value >= 0.0
assert window.summarysettings_button.text() == "Graph Settings"
graph_settings = PlotGraphSettingsDialog(window.graph_settings, window)
graph_settings.show()
app.processEvents()
graph_settings.grab().save("/tmp/plot_graph_settings.png")
assert graph_settings.save_plot_button.text() == "Save plot"
saved_plot_path = "/tmp/plot_saved_summary.png"
original_save_dialog = QFileDialog.getSaveFileName
QFileDialog.getSaveFileName = staticmethod(lambda *_args, **_kwargs: (saved_plot_path, "PNG image (*.png)"))
graph_settings.savePlot()
QFileDialog.getSaveFileName = original_save_dialog
assert os.path.exists(saved_plot_path) and os.path.getsize(saved_plot_path) > 0
assert not graph_settings.y_axis_max.isEnabled()
graph_settings.y_axis_mode.setCurrentIndex(graph_settings.y_axis_mode.findData("custom"))
graph_settings.y_axis_max.setValue(75.0)
graph_settings.show_grid.setChecked(True)
graph_settings.show_bar_values.setChecked(True)
updated_graph_settings = graph_settings.settings()
assert updated_graph_settings["y_axis_mode"] == "custom"
assert updated_graph_settings["y_axis_max"] == 75.0
assert updated_graph_settings["show_grid"]
assert updated_graph_settings["show_bar_values"]
graph_settings.close()
window.graph_settings = updated_graph_settings
window.onSummaryPlotChanged()
app.processEvents()
assert tuple(round(value, 1) for value in window.current_plot_figure.axes[0].get_ylim()) == (0.0, 75.0)
assert any(line.get_visible() for line in window.current_plot_figure.axes[0].get_ygridlines())
assert window.current_plot_figure.axes[0].texts
window.graph_settings = window.defaultGraphSettings()
window.onSummaryPlotChanged()
for chart_index in range(min(4, window.summaryplot_combo.count())):
    window.summaryplot_combo.setCurrentIndex(chart_index)
    app.processEvents()
    assert window.summaryplot_canvas.figure.canvas is window.summaryplot_canvas
    assert "What this shows:" in window.plot_description_label.text()
    assert window.plot_compare_label.text().startswith(("<b>Compare:</b>", "<b>Scale:</b>"))
window.summaryplot_canvas.grab().save("/tmp/plot_summary_after_switching.png")
worker_picker = PlotWorkerPickerDialog(window.workerstationshifttool_dataset, window)
worker_picker.show()
app.processEvents()
assert worker_picker.results.topLevelItemCount() == window.workerComboBox.count()
assert worker_picker.workplace_tree.topLevelItemCount() == 1
assert worker_picker.workplace_tree.topLevelItem(0).text(0) == "Default"
assert worker_picker.select_button.text() == "Select Worker"
assert not worker_picker.select_button.icon().isNull()
worker_picker.search_input.setText("ST02")
app.processEvents()
assert 0 < worker_picker.results.topLevelItemCount() < window.workerComboBox.count()
worker_picker.grab().save("/tmp/plot_worker_picker.png")
worker_picker.close()
assert window.plantlayout_image.scene() is window.plantlayout_scene
assert all(not button.icon().isNull() for button in (
    window.grtool1_button, window.grtool2_button, window.grtool3_button,
    window.grtool4_button, window.grtool5_button, window.grtool6_button,
    window.grtool7_button, window.grtool8_button, window.grtool9_button,
))

window.details_tabs.setCurrentWidget(window.workerinfo_group)
for _ in range(4):
    app.processEvents()
window.grab().save("/tmp/plot_worker_tab.png")
assert window.details_tabs.tabText(0) == "Tools Overview"
assert window.details_tabs.tabText(1) == "Worker Overview"
assert window.details_tabs.tabBar().tabRect(1).right() <= window.details_tabs.tabBar().width()
assert window.details_tabs.tabBar().font().pointSize() >= 12
assert window.details_tabs.tabIcon(0).actualSize(window.details_tabs.iconSize()) == window.details_tabs.iconSize()
assert window.details_tabs.tabIcon(1).actualSize(window.details_tabs.iconSize()) == window.details_tabs.iconSize()
assert window.worker_marker_preview.isVisible()
assert window.worker_marker_preview.size().width() == 108
assert window.worker_marker_preview.size().height() == 108
assert window.worker_marker_preview.gender in ("male", "female")
male_index = next((
    index for index, row in enumerate(window.workerstationshifttool_dataset)
    if str(row.get("gender", "")).casefold() == "male"
), -1)
if male_index >= 0:
    window.workerComboBox.setCurrentIndex(male_index)
    app.processEvents()
    assert window.worker_marker_preview.gender == "male"
    window.grab().save("/tmp/plot_worker_tab_male.png")
for control in (
    window.workerComboBox, window.orderInfo_button, window.searchInfo_button,
    window.xinfo_input, window.yinfo_input, window.scaleinfo_input,
    window.firstinfo_button, window.previousinfo_button,
    window.nextinfo_button, window.lastinfo_button,
    window.saveinfo_button, window.saveallinfo_button,
):
    assert control.isVisible()
    control_bottom_right = control.mapTo(window.workerinfo_group, control.rect().bottomRight())
    assert control_bottom_right.x() <= window.workerinfo_group.contentsRect().right()
    assert control_bottom_right.y() <= window.workerinfo_group.contentsRect().bottom()
window.details_tabs.setCurrentWidget(window.summary_group)

initial_worker_index = window.workerComboBox.currentIndex()
window.nextInfoButtonClicked()
app.processEvents()
assert window.workerComboBox.currentIndex() != initial_worker_index
window.agefrom_edit.setValue(30)
collapsed_canvas_top = window.plantlayout_image.mapTo(window, QPoint(0, 0)).y()
window.workerfilter_group.setChecked(True)
app.processEvents()
assert window.agefrom_edit.isVisible()
for button in window.plot_tool_buttons.values():
    bottom_right = button.mapTo(window.toolfilter_group, button.rect().bottomRight())
    assert bottom_right.y() <= window.toolfilter_group.contentsRect().bottom()
expanded_canvas_top = window.plantlayout_image.mapTo(window, QPoint(0, 0)).y()
assert expanded_canvas_top > collapsed_canvas_top
window.grab().save("/tmp/plot_responsive_filters_expanded.png")
window.selectPlotTool("DUET")
app.processEvents()
assert window.outcome_group.title() == "LiFFT Tool Outcome"
window.applyfilterButtonClicked()
app.processEvents()
assert window.outcome_group.title() == "DUET Tool Outcome"
window.selectPlotTool("ST")
app.processEvents()
assert window.outcome_group.title() == "DUET Tool Outcome"
window.applyfilterButtonClicked()
app.processEvents()
assert window.outcome_group.title() == "Shoulder Tool Outcome"
window.selectPlotTool("LiFFT")
app.processEvents()
assert window.outcome_group.title() == "Shoulder Tool Outcome"
window.applyfilterButtonClicked()
app.processEvents()
assert window.outcome_group.title() == "LiFFT Tool Outcome"
window.clearfilterButtonClicked()
assert window.agefrom_edit.value() == window.agefrom_edit.minimum()
assert not window.workerfilter_group.isChecked()

assert window.highlight_details
assert window.outcomemore_button.isVisible()
assert ": ST" not in window.outcomeresult1_label.text()
highlight_dialog = PlotHighlightDetailsDialog(window.highlight_details, window)
highlight_dialog.show()
app.processEvents()
highlight_dialog.grab().save("/tmp/plot_highlight_details.png")
assert highlight_dialog.table.topLevelItemCount() == len(window.highlight_details)
for column in range(highlight_dialog.table.columnCount()):
    assert highlight_dialog.table.columnWidth(column) >= highlight_dialog.table.fontMetrics().horizontalAdvance(
        highlight_dialog.table.headerItem().text(column)
    )
highlight_dialog.close()

window.resize(1300, 1100)
for _ in range(8):
    app.processEvents()
window.grab().save("/tmp/plot_responsive_minimum.png")
assert window.plantlayout_image.viewport().width() >= 500
assert window.plantlayout_image.viewport().height() >= 300

empty_parent = ErgoTools(disable_vtk=True)
empty_window = PlantLayoutWindow(empty_parent)
empty_window.resize(1460, 1060)
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

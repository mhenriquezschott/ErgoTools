"""PLOT graph workflows, independent viewer ownership and explicit export.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest
from matplotlib.figure import Figure
from PIL import Image
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

from ergotools.application.plot_results import saved_plot_results
from ergotools.bootstrap import load_icons
from ergotools.domain.language import Language
from ergotools.domain.plot_filters import PlotFilterSelection, PlotRiskView
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.plot_figure_export import export_plot
from ergotools.presentation.desktop.plot_figure_viewer import PlotFigureViewer
from ergotools.presentation.desktop.plot_graph_dialog import PlotGraphDialog
from ergotools.presentation.desktop.plot_graph_settings import (
    PlotAxisMode,
    PlotGraphSettings,
    style_summary_figure,
)
from ergotools.presentation.desktop.plot_marker_layer import PlotMarkerLayer
from ergotools.presentation.desktop.plot_tools_overview import PlotToolsOverview
from tests.test_plot_markers import canvas_with_map, positions_for
from tests.test_plot_results import SCOPE
from tests.test_plot_results import project as project

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("language", list(Language))
def test_saved_summary_selection_previews_and_modal_settings(
    project: AssessmentProjectFile, tmp_path: Path, language: Language
) -> None:
    """Only applied settings/saved data redraw; Close and visual drafts stay local.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    positions_for(project)
    canvas = canvas_with_map(tmp_path)
    writer = Mock(wraps=project.save_plot_positions)
    layer = PlotMarkerLayer(
        canvas, project.load_jobs(), writer, Mock(), current_year=2026
    )
    panel = PlotToolsOverview(layer, load_icons(), language=language)
    panel.resize(420, 700)
    panel.show()
    _APP.processEvents()
    assert not panel.settings_button.isEnabled()
    panel.open_settings()
    panel.open_viewer()
    results = saved_plot_results(project, PlotFilterSelection(SCOPE), current_year=2026)
    layer.set_results(results)
    assert panel.summary.workers.total == 2 and panel.settings_button.isEnabled()
    panel.chart_combo.setCurrentIndex(1)
    assert panel.canvas.figure.axes[0].get_legend() is not None
    figure = panel.canvas.figure
    layer.preview_worker(replace(results.positions.marker(1), enabled=False))
    assert panel.canvas.figure is figure and panel.summary.workers.total == 2
    assert writer.call_count == 0
    assert layer.save_workers(tuple(layer.worker_drafts.values()))
    assert writer.call_count == 1 and panel.summary.workers.total == 1
    figure = panel.canvas.figure
    errors = []

    def cancel() -> None:
        """Edit and Reset local graph settings, assert original defaults, then Close.

        Edit and Reset local graph settings, assert original defaults, then Close
        without applying; return callback failures to pytest.

        Args:
            None.

        Returns:
            None.
        """
        try:
            dialog = QApplication.activeModalWidget()
            assert isinstance(dialog, PlotGraphDialog)
            dialog.axis_mode.setCurrentIndex(2)
            assert dialog.axis_maximum.isEnabled()
            dialog.axis_maximum.setValue(80)
            dialog.text_scale.setValue(140)
            QTest.mouseClick(dialog.reset_button, Qt.MouseButton.LeftButton)
            assert dialog.settings() == PlotGraphSettings()
            QTest.mouseClick(dialog.close_button, Qt.MouseButton.LeftButton)
        except BaseException as error:
            errors.append(error)
            QApplication.activeModalWidget().reject()

    QTimer.singleShot(0, cancel)
    panel.open_settings()
    assert not errors and panel.canvas.figure is figure

    def apply() -> None:
        """Change explicit axis/text/title/legend/grid/value settings.

        Change explicit axis/text/title/legend/grid/value settings and click the actual
        Apply button once.

        Args:
            None.

        Returns:
            None.
        """
        try:
            dialog = QApplication.activeModalWidget()
            dialog.axis_mode.setCurrentIndex(2)
            dialog.axis_maximum.setValue(80)
            dialog.text_scale.setValue(120)
            dialog.show_title.setChecked(False)
            dialog.show_legend.setChecked(False)
            dialog.show_grid.setChecked(True)
            dialog.show_bar_values.setChecked(True)
            QTest.mouseClick(dialog.apply_button, Qt.MouseButton.LeftButton)
        except BaseException as error:
            errors.append(error)
            QApplication.activeModalWidget().reject()

    QTimer.singleShot(0, apply)
    panel.open_settings()
    assert not errors and panel.canvas.figure is not figure
    axis = panel.canvas.figure.axes[0]
    assert axis.get_ylim() == (0, 80) and not axis.title.get_visible()
    assert not axis.get_legend().get_visible()
    assert any(line.get_visible() for line in axis.get_ygridlines())
    assert axis.texts
    size = axis.title.get_fontsize()
    panel.draw_current()
    assert panel.canvas.figure.axes[0].title.get_fontsize() == size
    panel.settings = replace(panel.settings, show_title=True, text_scale=140)
    panel.resize(330, 600)
    panel.draw_current()
    _APP.processEvents()
    panel.canvas.draw()
    title = panel.canvas.figure.axes[0].title
    bounds = title.get_window_extent(panel.canvas.get_renderer())
    assert bounds.x0 >= 0 and bounds.x1 <= panel.canvas.width()

    applied = layer.results
    layer.set_results(
        replace(
            applied, selection=replace(applied.selection, risk_view=PlotRiskView.JOB)
        )
    )
    assert panel.chart_combo.isHidden() and panel.chart_combo.currentIndex() == 1
    assert panel.canvas.figure.axes[0].get_xlim() == (0, 80)
    layer.set_results(
        replace(
            applied,
            selection=replace(applied.selection, risk_view=PlotRiskView.COMPARISON),
        )
    )
    assert not panel.chart_combo.isHidden() and panel.chart_combo.currentIndex() == 1
    panel.resize(330, 600)
    _APP.processEvents()
    panel.canvas.draw()
    axis = panel.canvas.figure.axes[0]
    bounds = axis.yaxis.label.get_window_extent(panel.canvas.get_renderer())
    assert bounds.x0 >= 0 and bounds.x1 <= panel.canvas.width()
    layer.clear()
    assert panel.summary is None and not panel.settings_button.isEnabled()
    assert not panel.canvas.figure.axes[0].patches
    panel.close()
    canvas.close()


@pytest.mark.parametrize("language", list(Language))
def test_expanded_viewer_click_owns_figure_and_navigation(
    project: AssessmentProjectFile, tmp_path: Path, language: Language
) -> None:
    """An actual chart click opens an independent figure and preserves its parent.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    canvas = canvas_with_map(tmp_path)
    layer = PlotMarkerLayer(
        canvas, project.load_jobs(), Mock(), Mock(), current_year=2026
    )
    panel = PlotToolsOverview(layer, load_icons(), language=language)
    panel.resize(420, 700)
    panel.show()
    layer.set_results(
        saved_plot_results(project, PlotFilterSelection(SCOPE), current_year=2026)
    )
    _APP.processEvents()
    figure = panel.canvas.figure
    original_size = tuple(figure.get_size_inches())
    errors = []
    visited = []

    def view() -> None:
        """Assert the expanded viewer owns a distinct 900x650 figure.

        Assert the expanded viewer owns a distinct 900x650 figure, exercise real
        Pan/Zoom/Home and close it after recording failures.

        Args:
            None.

        Returns:
            None.
        """
        try:
            dialog = QApplication.activeModalWidget()
            assert isinstance(dialog, PlotFigureViewer)
            visited.append(dialog)
            assert dialog.figure is not figure and figure.canvas is panel.canvas
            assert (dialog.width(), dialog.height()) == (900, 650)
            dialog.toolbar.pan()
            assert dialog.toolbar.mode
            dialog.toolbar.pan()
            dialog.toolbar.zoom()
            assert dialog.toolbar.mode
            dialog.toolbar.zoom()
            dialog.toolbar.home()
        except BaseException as error:
            errors.append(error)
        finally:
            modal = QApplication.activeModalWidget()
            if modal is not None:
                modal.close()

    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(view)
    timer.start(0)
    QTest.mouseClick(
        panel.canvas, Qt.MouseButton.LeftButton, pos=panel.canvas.rect().center()
    )
    timer.stop()
    assert not errors and len(visited) == 1
    assert panel.canvas.figure is figure and figure.canvas is panel.canvas
    assert tuple(figure.get_size_inches()) == original_size and figure.axes
    panel.close()
    canvas.close()


def test_explicit_export_formats_cancel_and_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Real exports keep source DPI/formats; cancel and failure never accept edits.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        monkeypatch: Pytest patch fixture; environment/adapter substitutions are
            restored after the test.

    Returns:
        None.
    """
    figure = Figure(figsize=(3.1, 2.3))
    figure.add_subplot().bar([1], [25])
    dialog = PlotGraphDialog(PlotGraphSettings(), load_icons(), Mock())
    info, error = Mock(), Mock()
    monkeypatch.setattr(QMessageBox, "information", info)
    monkeypatch.setattr(QMessageBox, "critical", error)
    for filter_name, suffix in (
        ("PNG", ".png"),
        ("JPEG", ".jpg"),
        ("SVG", ".svg"),
        ("PDF", ".pdf"),
    ):
        path = tmp_path / filter_name
        monkeypatch.setattr(
            QFileDialog, "getSaveFileName", Mock(return_value=(str(path), filter_name))
        )
        assert export_plot(figure, dialog, Language.ENGLISH, "Graph title")
        output = path.with_suffix(suffix)
        assert output.stat().st_size > 100
        if suffix == ".png":
            with Image.open(output) as image:
                assert image.info["dpi"][0] == pytest.approx(300, abs=0.01)
        if suffix == ".svg":
            assert "<svg" in output.read_text()
        if suffix == ".pdf":
            assert output.read_bytes().startswith(b"%PDF")
    assert info.call_count == 4 and not error.called
    chooser = Mock(return_value=("", ""))
    monkeypatch.setattr(QFileDialog, "getSaveFileName", chooser)
    assert not export_plot(figure, dialog, Language.SPANISH, "title", expanded=True)
    assert "Todos los archivos" in chooser.call_args.args[3]
    assert not export_plot(figure, dialog, Language.SPANISH, "***")
    assert chooser.call_args.args[2] == "plot-summary.png"
    missing = tmp_path / "missing" / "plot.png"
    chooser.return_value = (str(missing), "PNG")
    assert not export_plot(figure, dialog, Language.SPANISH, "title", expanded=True)
    assert error.call_count == 1 and not missing.exists()
    assert dialog.result() == 0 and dialog.settings() == PlotGraphSettings()
    viewer = PlotFigureViewer(figure, load_icons())
    path = tmp_path / "viewer.jpg"
    chooser.return_value = (str(path), "JPEG")
    viewer.save_plot()
    assert path.exists() and info.call_count == 4
    viewer.close()
    dialog.close()


def test_settings_validation_and_missing_figure() -> None:
    """Programmatic settings preserve the native control contract and empty safety.

    Args:
        None.

    Returns:
        None.
    """
    for changes in (
        {"axis_maximum": float("nan")},
        {"axis_maximum": 0},
        {"text_scale": 141},
        {"show_title": 1},
        {"axis_mode": "other"},
    ):
        with pytest.raises(ValueError, match="Unsupported"):
            PlotGraphSettings(**changes)
    style_summary_figure(Figure(), PlotGraphSettings())
    figure = Figure()
    axis = figure.add_subplot()
    axis.bar([1], [20])
    style_summary_figure(figure, PlotGraphSettings(axis_mode=PlotAxisMode.RISK))
    assert axis.get_ylim() == (0, 100)
    figure.clear()


def test_settings_save_exports_applied_chart_with_modal_owner(
    project: AssessmentProjectFile,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Saving a local draft exports applied settings and keeps modal ownership.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        monkeypatch: Pytest patch fixture; environment/adapter substitutions are
            restored after the test.

    Returns:
        None.
    """
    canvas = canvas_with_map(tmp_path)
    layer = PlotMarkerLayer(
        canvas, project.load_jobs(), Mock(), Mock(), current_year=2026
    )
    panel = PlotToolsOverview(layer, load_icons())
    layer.set_results(
        saved_plot_results(project, PlotFilterSelection(SCOPE), current_year=2026)
    )
    before = panel.canvas.figure
    before_settings = panel.settings
    chooser = Mock(return_value=(str(tmp_path / "applied.svg"), "SVG"))
    monkeypatch.setattr(QFileDialog, "getSaveFileName", chooser)
    monkeypatch.setattr(QMessageBox, "information", Mock())
    errors = []

    def save() -> None:
        """Edit unaccepted graph settings, trigger Save.

        Edit unaccepted graph settings, trigger Save and assert export uses the
        unchanged applied chart and actual modal owner.

        Args:
            None.

        Returns:
            None.
        """
        try:
            dialog = QApplication.activeModalWidget()
            dialog.show_title.setChecked(False)
            dialog.axis_mode.setCurrentIndex(2)
            dialog.axis_maximum.setValue(5)
            QTest.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
            assert chooser.call_args.args[0] is dialog
            assert dialog.isVisible() and panel.canvas.figure is before
            assert panel.settings is before_settings
            assert before.axes[0].title.get_visible()
        except BaseException as error:
            errors.append(error)
        finally:
            QApplication.activeModalWidget().reject()

    QTimer.singleShot(0, save)
    panel.open_settings()
    assert not errors and (tmp_path / "applied.svg").exists()
    assert panel.settings is before_settings
    panel.close()
    canvas.close()

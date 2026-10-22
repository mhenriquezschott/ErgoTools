"""Original PLOT host Apply, tabs, saved handoff and explicit close ownership.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest
from PIL import Image
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QMenuBar, QMessageBox, QToolBar

from ergotools.bootstrap import load_icons
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.plot_filters import PlotRiskView
from ergotools.domain.plot_positions import WorkerAssignmentMarker
from ergotools.domain.plot_scope import PlotScope
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.plant_image_import import import_plant_image
from ergotools.presentation.desktop.plot_window import PlotWindow
from tests.test_plot_markers import positions_for
from tests.test_plot_results import project as project

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


def host(
    project: AssessmentProjectFile, tmp_path: Path, **kwargs: object
) -> PlotWindow:
    """Seed a map explicitly before exercising read-only host workflows.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        kwargs: Explicit constructor overrides forwarded to the synthetic dialog/host.

    Returns:
        Live owned PLOT window over the supplied temporary repository and explicitly
        seeded image; caller closes it.
    """
    image_path = tmp_path / "map.png"
    Image.new("RGB", (640, 400), "white").save(image_path)
    project.save_plant_image("P", import_plant_image(image_path))
    project.save_plot_positions(positions_for(project))
    window = PlotWindow(
        project,
        project,
        project,
        lambda path: import_plant_image(Path(path)),
        load_icons(),
        current_year=2026,
        **kwargs,
    )
    window.show()
    _APP.processEvents()
    return window


def answer_close(window: PlotWindow, button: QMessageBox.StandardButton) -> bool:
    """Answer the actual owned modal and assert it was entered.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        button: Qt standard consent button activated by the scheduled modal driver.

    Returns:
        Actual close-acceptance outcome after asserting the scheduled native consent
        dialog was entered.
    """
    visited = []
    timer = QTimer(window)
    timer.setSingleShot(True)

    def answer() -> None:
        """Record the actual unsaved-PLOT consent text.

        Record the actual unsaved-PLOT consent text and click the caller-selected native
        standard button.

        Args:
            None.

        Returns:
            None.
        """
        box = _APP.activeModalWidget()
        assert isinstance(box, QMessageBox)
        visited.append(box.text())
        control = box.button(button)
        assert control is not None
        QTest.mouseClick(control, Qt.MouseButton.LeftButton)

    timer.timeout.connect(answer)
    timer.start(0)
    accepted = window.close()
    timer.stop()
    assert visited
    return accepted


@pytest.mark.parametrize("language", tuple(Language))
def test_host_original_regions_modes_resize_and_no_implicit_writes(
    project: AssessmentProjectFile, tmp_path: Path, language: Language
) -> None:
    """Compose EN/ES saved regions without clipped rail/chart or image scrollbars.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None; demographics disclosure preserves full toolbar/chart space and both
        gauges retain their full arc radius at minimum and enlarged window sizes.
    """
    window = host(
        project, tmp_path, language=language, system=MeasurementSystem.IMPERIAL
    )
    snapshot = project.load_plot_positions(), project.read("P")
    assert window.filters.workplace.scope is not None
    assert window.layer.results is not None and window.layer.results.workers
    assert window.outcome.summary is not None and window.tools.summary is not None
    assert (
        window.tabs.count() == 2 and window.overviews.currentWidget() is window.workers
    )
    for mode in (PlotRiskView.COMPARISON, PlotRiskView.JOB, PlotRiskView.INDIVIDUAL):
        QTest.mouseClick(window.filters.risk_buttons[mode], Qt.MouseButton.LeftButton)
        _APP.processEvents()
        assert window.layer.results.selection.risk_view is mode
        assert window.overviews.currentWidget() is (
            window.jobs if mode is PlotRiskView.JOB else window.workers
        )
    item = window.layer.items[("worker", 1)]
    window.layer.select(item)
    assert window.tabs.currentIndex() == 1
    window.filters.risk_buttons[PlotRiskView.COMPARISON].click()
    window.tabs.setCurrentIndex(0)
    assert not window.findChildren(QMenuBar) and not window.findChildren(QToolBar)
    for size in ((1300, 1045), (1800, 1200)):
        window.resize(*size)
        _APP.processEvents()
        for widget in (window.filters, window.splitter, window.outcome):
            assert window.rect().contains(widget.geometry())
        assert window.map_panel.canvas.width() > 800
        assert window.tabs.width() >= 390
        for expanded in (True, False):
            window.filters.demographics.setChecked(expanded)
            _APP.processEvents()
            _APP.processEvents()
            rail = window.map_panel.rail
            for button in window.map_panel.buttons.values():
                assert rail.rect().contains(button.geometry())
            assert window.tools.canvas.height() >= 250
            assert (
                window.tools.canvas.geometry().bottom()
                < window.tools.chart_combo.geometry().top()
            )
            assert (
                window.map_panel.canvas.horizontalScrollBarPolicy()
                == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            assert (
                window.map_panel.canvas.verticalScrollBarPolicy()
                == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            for gauge in (window.outcome.individual_gauge, window.outcome.job_gauge):
                assert gauge.width() >= 210 and gauge.height() >= 144
                assert gauge.parentWidget().rect().contains(gauge.geometry())
            assert (
                window.history_actions.redo_button.geometry().right()
                > window.title.geometry().right()
            )
    window.workers.locate()
    assert window.workers.timer.isActive()
    assert window.close() and not window.workers.timer.isActive()
    assert (project.load_plot_positions(), project.read("P")) == snapshot
    window.deleteLater()


def test_host_pending_marker_apply_cancel_and_close_discard(
    project: AssessmentProjectFile, tmp_path: Path
) -> None:
    """Pending map intent survives Cancel; closing never saves it.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    window = host(project, tmp_path)
    snapshot = project.load_plot_positions()
    before = window.layer.results
    window.layer.preview_worker(WorkerAssignmentMarker(1, visible=False))
    window.map_panel.show_error = Mock()
    QTest.mouseClick(
        window.filters.risk_buttons[PlotRiskView.JOB], Qt.MouseButton.LeftButton
    )
    assert window.layer.results is before
    assert window.filters.risk_view is PlotRiskView.INDIVIDUAL
    window.map_panel.show_error.assert_called_once()
    assert not answer_close(window, QMessageBox.StandardButton.No)
    assert window.isVisible() and window.layer.pending
    assert answer_close(window, QMessageBox.StandardButton.Yes)
    assert project.load_plot_positions() == snapshot
    window.deleteLater()


def test_host_read_failure_and_empty_scope_retain_saved_identity(
    project: AssessmentProjectFile, tmp_path: Path
) -> None:
    """Failed Apply retains results; an empty plant clears the regions.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    window = host(project, tmp_path)
    before = window.layer.results
    real = window.repository
    window.repository = Mock(wraps=real)
    window.repository.load_job_risk.side_effect = OSError("fixture read failure")
    window.map_panel.show_error = Mock()
    QTest.mouseClick(window.filters.apply_button, Qt.MouseButton.LeftButton)
    assert window.layer.results is before
    window.map_panel.show_error.assert_called_once()
    window.repository = real
    assert window.filters.workplace.set_scope(PlotScope((("Empty",),)))
    QTest.mouseClick(window.filters.apply_button, Qt.MouseButton.LeftButton)
    assert window.layer.results is not None and not window.layer.results.workers
    assert not window.layer.items
    assert window.map_panel.canvas.loaded_layout.image is None
    assert window.close()
    window.deleteLater()


def test_host_handoff_rejection_exception_image_consent_and_success(
    project: AssessmentProjectFile, tmp_path: Path
) -> None:
    """Accepted handoff closes; rejection retains image preview and data.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    load = Mock(return_value=False)
    window = host(project, tmp_path, load_assessment=load)
    snapshot = project.load_plot_positions(), project.read("P")
    assert not window.layer.load_worker(1) and window.isVisible()
    assert load.call_args.args[0].assignment_id == 1
    load.side_effect = OSError("fixture editor rejection")
    window.layer.show_error = Mock()
    assert not window.layer.load_worker(1) and window.isVisible()
    window.layer.show_error.assert_called_once()
    load.side_effect = None
    load.return_value = True
    window.map_panel.pending_image = import_plant_image(tmp_path / "map.png")
    window.confirm_close = Mock(return_value=False)
    count = load.call_count
    assert not window.layer.load_worker(1) and load.call_count == count
    assert window.map_panel.pending_image is not None and window.isVisible()
    window.confirm_close.return_value = True
    assert window.layer.load_worker(1) and not window.isVisible()
    window.confirm_close.assert_called_with()
    assert (project.load_plot_positions(), project.read("P")) == snapshot
    window.deleteLater()

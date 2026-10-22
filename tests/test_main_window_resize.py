"""Main-window enlargement preserves task geometry, source and native framing.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.bootstrap import create_window
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.presentation.desktop.lifft_window import LifftWindow

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


def test_enlargement_preserves_pending_input_and_column_alignment(
    tmp_path: Path,
) -> None:
    """Both grids retain edits and aligned headers as adjacent controls grow.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    window = create_window(tmp_path / "settings.json", original_navigation=True)
    workspace = window.presenter.workspace
    workspace.create(
        str(tmp_path / "sizing.ergprj"),
        ProjectMetadata("p", "Sizing", MeasurementSystem.IMPERIAL),
        "lifft",
        LifftDraft(MeasurementSystem.IMPERIAL, (LifftTask("l", 12, 20, 100),)),
    )
    window.refresh()
    window.show()
    _APP.processEvents()
    try:
        assert window.minimumWidth() == 1550 and window.minimumHeight() == 1015
        assert window.maximumWidth() > 2100 and window.maximumHeight() > 1600
        for duet in (False, True):
            if duet:
                workspace.create_assessment(
                    "duet",
                    DuetDraft(tuple(DuetTask(str(i), 6, 100) for i in range(15))),
                    choice=CloseChoice.DISCARD,
                )
                window.resize(2100, 1300)
                window.language = Language.SPANISH
                window.translate()
                window.refresh()
                QTest.qWait(30)
            panel = window.duet_panel if duet else window.task_panel
            field = panel.inputs[0][1]
            field.setText("pending")
            field.textEdited.emit("pending")
            before = workspace.active.state
            if duet:
                window.translate()
                window.refresh()
                QTest.qWait(30)
                panel = window.duet_panel
                for column, header in enumerate(panel.headers):
                    assert (
                        header.width()
                        == panel.grid.itemAtPosition(1, column).widget().width()
                    )
                field = panel.inputs[0][1]
                field.setText("pending")
                field.textEdited.emit("pending")
            widths = []
            for width, height in (
                (1550, 1015),
                (1920, 1200),
                (2100, 1300),
                (1550, 1015),
            ):
                window.resize(width, height)
                QTest.qWait(30)
                assert (window.width(), window.height()) == (width, height)
                widths.append(panel.body_scroll.width())
                assert field.text() == "pending" and panel.pending
                assert workspace.active.state is before
                for column, header in enumerate(panel.headers):
                    assert (
                        header.width()
                        == panel.grid.itemAtPosition(1, column).widget().width()
                    )
                for widget in (
                    window.body_panel,
                    window.results_sidebar,
                    window.main_navigation.context_frame,
                    panel.calculate_button,
                    panel.clear_button,
                ):
                    assert window.rect().contains(
                        widget.mapTo(window, widget.rect().bottomRight())
                    )
            assert widths[1] > widths[0] and widths[2] > widths[1]
            assert widths[3] == widths[0]
            # Explicit clearing precedes a source change; resizing never commits.
            if duet:
                with patch.object(
                    LifftWindow, "confirm_clear_assessment", return_value=True
                ):
                    panel.clear_button.click()
            else:
                with patch.object(
                    LifftWindow, "confirm_clear_assessment", return_value=True
                ):
                    window.clear_assessment()
    finally:
        workspace.close(choice=CloseChoice.DISCARD)
        window.close()
        _APP.processEvents()


@pytest.mark.skipif(
    _APP.platformName() == "offscreen", reason="Native OpenGL display required."
)
def test_tall_viewport_fits_full_avatar_and_preserves_user_zoom(tmp_path: Path) -> None:
    """Aspect changes retain camera pose, relative zoom and full-body fit.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    window = create_window(
        tmp_path / "native.json", original_navigation=True, enable_vtk=True
    )
    window.show()
    _APP.processEvents()
    engine = window._body_renderer
    try:
        engine.set_animation_enabled(False)
        engine.reset_view()
        camera = engine.renderer.GetActiveCamera()
        pose = camera.GetPosition()
        baseline = camera.GetParallelScale()
        engine.zoom_view()
        zoomed = camera.GetParallelScale()
        for width, height in ((1920, 1200), (1550, 1300), (2100, 1300)):
            window.resize(width, height)
            _APP.processEvents()
            assert camera.GetPosition() == pose
            assert camera.GetParallelScale() == pytest.approx(
                zoomed * engine._aspect_factor
            )
        window.resize(1550, 1015)
        _APP.processEvents()
        assert camera.GetParallelScale() == pytest.approx(baseline / 1.15)
        window.resize(1550, 1300)
        _APP.processEvents()
        engine.set_animation_enabled(False)
        engine.reset_view()
        bounds = engine.actors["human"].GetBounds()
        # Project all eight world-space bounds corners into the actual framebuffer.
        for x in bounds[:2]:
            for y in bounds[2:4]:
                for z in bounds[4:]:
                    engine.renderer.SetWorldPoint(x, y, z, 1)
                    engine.renderer.WorldToDisplay()
                    px, py, _ = engine.renderer.GetDisplayPoint()
                    assert 0 <= px <= engine.widget.width()
                    assert 0 <= py <= engine.widget.height()
    finally:
        window.close()
        _APP.processEvents()

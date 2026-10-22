"""Native VTK regression checks on the approved desktop baseline.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtWidgets import QApplication, QWidget

from ergotools.application.contracts.body_renderer import (
    BodyRegion,
    BodyViewState,
    RgbColor,
)
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.bootstrap import create_window
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.resources import read_asset
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.rendering.vtk_body_renderer import VtkBodyRenderer

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])
pytestmark = pytest.mark.skipif(
    _APP.platformName() == "offscreen",
    reason="VTK Qt/OpenGL integration requires a native display.",
)


@pytest.fixture
def window(tmp_path: Path) -> Iterator[LifftWindow]:
    """Own a native integrated window with a synthetic imperial assessment.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Yields:
        Live synthetic integrated window; fixture cleanup closes the window and releases
        its temporary project after the test.
    """
    view = create_window(
        tmp_path / "settings.json", original_navigation=True, enable_vtk=True
    )
    view.presenter.workspace.create(
        str(tmp_path / "avatar.ergprj"),
        ProjectMetadata("p", "Avatar", MeasurementSystem.IMPERIAL),
        "lifft",
        LifftDraft(MeasurementSystem.IMPERIAL, (LifftTask("a", 12, 20, 100),)),
    )
    view.refresh()
    view.show()
    _APP.processEvents()
    yield view
    view.presenter.workspace.close(choice=CloseChoice.DISCARD)
    view.close()
    _APP.processEvents()


def renderer(window: LifftWindow) -> VtkBodyRenderer:
    """Get the real renderer attached by the application composition root.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        Borrowed real VtkBodyRenderer created by bootstrap for this window; window owns
        native disposal.
    """
    result = window._body_renderer
    assert isinstance(result, VtkBodyRenderer)
    return result


def test_packaged_meshes_camera_and_layout(window: LifftWindow) -> None:
    """All eight meshes decode and the original torso shot fits its viewport.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    engine = renderer(window)
    assert len(engine.actors) == 8
    assert all(
        a.GetMapper().GetInput().GetNumberOfPoints() > 0 for a in engine.actors.values()
    )
    assert engine.actors["human"].GetVisibility()
    assert not engine.actors["back"].GetVisibility()
    camera = engine.renderer.GetActiveCamera()
    shot = engine.shots[BodyRegion.LOW_BACK]
    assert camera.GetPosition() == pytest.approx(shot.position)
    assert camera.GetParallelScale() == pytest.approx(shot.parallel_scale)
    assert camera.GetParallelProjection()
    assert engine.widget.width() >= 250
    assert engine.widget.height() >= 315
    assert all(
        b.isEnabled() and not b.icon().isNull() for b in window.body_panel.view_buttons
    )


def test_calculation_edit_and_clear_overlay(window: LifftWindow) -> None:
    """Calculated risk colors the back; invalid edits and clearing hide it.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    engine = renderer(window)
    window.task_panel.calculate_button.click()
    back = engine.actors["back"]
    assert back.GetVisibility()
    assert back.GetProperty().GetColor() == pytest.approx((165 / 255, 1, 0))
    cell = window.task_panel.inputs[0][1]
    cell.setText("bad")
    cell.textEdited.emit("bad")
    assert not back.GetVisibility()
    cell.setText("20")
    cell.textEdited.emit("20")
    window.task_panel.calculate_button.click()
    assert back.GetVisibility()
    with patch.object(LifftWindow, "confirm_clear_assessment", return_value=True):
        window.task_panel.clear_button.click()
    assert not back.GetVisibility()


def test_buttons_and_duplicate_states_preserve_camera(window: LifftWindow) -> None:
    """Controls use original steps; value updates retain the user's camera.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    engine = renderer(window)
    camera = engine.renderer.GetActiveCamera()
    before = camera.GetPosition()
    window.body_panel.view_buttons[0].click()
    assert camera.GetPosition() != before
    rotated = camera.GetPosition()
    scale = camera.GetParallelScale()
    window.body_panel.view_buttons[1].click()
    assert camera.GetParallelScale() == pytest.approx(scale / 1.15)
    rendered = []
    engine.render_window.AddObserver("EndEvent", lambda *_: rendered.append(True))
    state = BodyViewState(BodyRegion.LOW_BACK, RgbColor(1, 0, 0))
    engine.set_state(state)
    assert len(rendered) == 1
    engine.set_state(state)
    assert len(rendered) == 1
    assert camera.GetPosition() == rotated
    engine.set_animation_enabled(False)
    window.body_panel.view_buttons[2].click()
    shot = engine.shots[BodyRegion.FULL_BODY]
    assert camera.GetPosition() == pytest.approx(shot.position)
    assert camera.GetParallelScale() == pytest.approx(shot.parallel_scale)


def test_region_switches_clear_other_patches(window: LifftWindow) -> None:
    """Future tool views receive their reviewed region shots and patch groups.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    engine = renderer(window)
    for region, keys in (
        (
            BodyRegion.DISTAL_UPPER_EXTREMITIES,
            {"left_arm", "left_hand", "right_arm", "right_hand"},
        ),
        (BodyRegion.SHOULDERS, {"left_shoulder", "right_shoulder"}),
        (BodyRegion.FULL_BODY, set()),
    ):
        engine.set_state(BodyViewState(region, RgbColor(1, 0, 0)))
        assert {
            k for k, a in engine.actors.items() if k != "human" and a.GetVisibility()
        } == keys
        assert engine.renderer.GetActiveCamera().GetPosition() == pytest.approx(
            engine.shots[region].position
        )


def test_cancelled_close_retains_renderer(
    window: LifftWindow, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A modal close cancellation keeps a usable scene; accepted close finalizes.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        monkeypatch: Pytest patch fixture; environment/adapter substitutions are
            restored after the test.

    Returns:
        None.
    """
    engine = renderer(window)
    cell = window.task_panel.inputs[0][1]
    cell.setText("21")
    cell.textEdited.emit("21")
    monkeypatch.setattr(window, "dirty_choice", lambda: CloseChoice.CANCEL)
    assert not window.close()
    assert not engine._closed
    engine.rotate_view()
    monkeypatch.setattr(window, "dirty_choice", lambda: CloseChoice.DISCARD)
    assert window.close()
    assert engine._closed
    engine.close()
    engine.rotate_view()
    engine.zoom_view()
    engine.reset_view()
    engine.set_state(BodyViewState(BodyRegion.LOW_BACK, None))
    assert not engine.actors


def test_model_loading_is_independent_of_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Resources decode from a foreign directory and read errors propagate.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        monkeypatch: Pytest patch fixture; environment/adapter substitutions are
            restored after the test.

    Returns:
        None.
    """
    monkeypatch.chdir(tmp_path)
    parent = QWidget()
    engine = VtkBodyRenderer(parent, lambda name: read_asset(f"models/{name}"))
    assert len(engine.actors) == 8
    engine.set_state(BodyViewState(BodyRegion.SHOULDERS, None))
    assert engine.renderer.GetActiveCamera().GetPosition() == pytest.approx(
        engine.shots[BodyRegion.SHOULDERS].position
    )
    engine.close()

    def fail_read(_name: str) -> bytes:
        """Inject an explicit missing packaged-model read error.

        Inject an explicit missing packaged-model read error before a usable native
        renderer can be published.

        Args:
            _name: Packaged model resource name; this injected reader fails deliberately
                without reading any file.

        Returns:
            No value: deliberately raises the missing-resource OSError before any native
                model can be decoded.

        Raises:
            OSError: The controlled adapter/resource/publication failure is injected by
                this scenario.
        """
        raise OSError("missing asset")

    with pytest.raises(OSError, match="missing asset"):
        VtkBodyRenderer(parent, fail_read)
    with pytest.raises(ValueError, match="no decoded points"):
        VtkBodyRenderer(parent, lambda _name: b"solid empty\nendsolid empty\n")
    parent.close()
    _APP.processEvents()


def test_simultaneous_overlays_clear_missing_regions(window: LifftWindow) -> None:
    """Independent region colors survive focus changes and missing data clears patches.

    Args:
        window: Fixture-owned live VTK window with the packaged anatomical meshes.

    Returns:
        None; verify actual backend actor visibility and exact RGB channels.
    """
    engine = renderer(window)
    overlays = (
        (BodyRegion.LOW_BACK, RgbColor(1, 1, 0)),
        (BodyRegion.DISTAL_UPPER_EXTREMITIES, RgbColor(1, 0, 0)),
        (BodyRegion.SHOULDERS, RgbColor(0, 1, 0)),
    )
    for focus in (BodyRegion.LOW_BACK, BodyRegion.SHOULDERS):
        engine.set_state(BodyViewState(focus, None, overlays))
        visible = [
            actor
            for key, actor in engine.actors.items()
            if key != "human" and actor.GetVisibility()
        ]
        assert len(visible) >= 5
        assert {actor.GetProperty().GetColor() for actor in visible} == {
            (1.0, 1.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        }
    engine.set_state(BodyViewState(BodyRegion.LOW_BACK))
    assert all(
        not actor.GetVisibility()
        for key, actor in engine.actors.items()
        if key != "human"
    )

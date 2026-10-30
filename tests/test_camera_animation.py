"""Original camera animation, owned View preference and explicit user tab selection.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

from ergotools.application.contracts.body_renderer import BodyRegion, BodyViewState
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.bootstrap import create_window
from ergotools.infrastructure.settings_store import JsonSettingsStore
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.rendering.vtk_body_renderer import VtkBodyRenderer
from tests import test_saved_tool_data as fixture


@pytest.fixture
def window(tmp_path: Path) -> Iterator[LifftWindow]:
    """Use all three saved tools with the approved native renderer.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Yields:
        Live synthetic integrated window; fixture cleanup closes the window and releases
        its temporary project after the test.
    """
    original = fixture.create_window
    with patch.object(
        fixture,
        "create_window",
        side_effect=lambda *args, **kwargs: original(*args, **kwargs, enable_vtk=True),
    ):
        generator = fixture.window.__wrapped__(tmp_path)
        view = next(generator)
    yield view
    next(generator, None)


def click(window: LifftWindow, index: int) -> None:
    """Select the real original tab with a mouse, preserving normal source policy.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        index: Zero-based selected input/row/case index used by the parametrized
            regression.

    Returns:
        None.
    """
    tabs = window.assessment_tabs.tabBar()
    QTest.mouseClick(tabs, Qt.MouseButton.LeftButton, pos=tabs.tabRect(index).center())


def test_only_accepted_mouse_selection_animates(window: LifftWindow) -> None:
    """Accepted clicks animate while tool switching retains edited drafts.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    engine = window._body_renderer
    assert isinstance(engine, VtkBodyRenderer)
    window.assessment_tabs.setCurrentIndex(1)
    assert not engine._timer.isActive()
    before = engine.renderer.GetActiveCamera().GetPosition()
    click(window, 2)
    assert engine._timer.isActive()
    assert engine.renderer.GetActiveCamera().GetPosition() == before
    engine._stop_animation()
    engine.reset_view()
    field = window.tst_panel.inputs[0][-1]
    field.setText("350")
    field.textEdited.emit("350")
    before = engine.renderer.GetActiveCamera().GetPosition()
    with patch.object(window, "dirty_choice", return_value=CloseChoice.CANCEL):
        click(window, 0)
    assert not window.tst_active and engine._timer.isActive()
    assert engine.renderer.GetActiveCamera().GetPosition() == before
    assert engine._selection_region is None
    click(window, 2)
    assert window.tst_panel.inputs[0][-1].text() == "350"


def test_reference_segment_boundaries_and_final_pose(window: LifftWindow) -> None:
    """Original stage durations finish at the exact target with one render per tick.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    engine = window._body_renderer
    click(window, 1)
    engine._timer.stop()
    assert [segment[2] for segment in engine._segments] == [190, 420, 120]
    renders = []
    engine.render_window.AddObserver("EndEvent", lambda *_: renders.append(True))
    engine._advance_animation(190)
    camera = engine.renderer.GetActiveCamera()
    assert camera.GetPosition() == pytest.approx(
        engine.shots[BodyRegion.FULL_BODY].position
    )
    approach = engine._segments[1][1]
    engine._advance_animation(420)
    assert camera.GetPosition() == pytest.approx(approach.position)
    engine._advance_animation(120)
    target = engine.shots[BodyRegion.DISTAL_UPPER_EXTREMITIES]
    assert camera.GetPosition() == pytest.approx(target.position)
    assert camera.GetParallelScale() == pytest.approx(
        target.parallel_scale * engine._aspect_factor
    )
    assert len(renders) == 3 and not engine._segments


@pytest.mark.parametrize(
    "operation", ["rotate_view", "zoom_view", "reset_view", "close"]
)
def test_camera_control_or_close_cancels_transition(
    window: LifftWindow, operation: str
) -> None:
    """Manual control and close cannot be overwritten by a pending timer frame.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        operation: Named parametrized command/capability whose success/failure boundary
            is exercised.

    Returns:
        None.
    """
    engine = window._body_renderer
    click(window, 1)
    assert engine._timer.isActive()
    getattr(engine, operation)()
    assert not engine._timer.isActive() and not engine._segments
    camera = engine.renderer.GetActiveCamera()
    position = camera.GetPosition()
    engine._tick()
    assert camera.GetPosition() == position


def test_view_toggle_failure_restart_and_pending_preservation(
    window: LifftWindow,
) -> None:
    """View retains invalid text; save failure restores the checked state.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    engine = window._body_renderer
    field = window.task_panel.inputs[0][2]
    field.setText("bad")
    field.textEdited.emit("bad")
    active = window.presenter.workspace.active
    state = active.state
    action = window._assessment_menu.camera_animation
    settings = window._settings_store.load()
    with patch.object(JsonSettingsStore, "save", side_effect=OSError("failed")):
        action.trigger()
    assert action.isChecked() and window._settings_store.load() == settings
    action.trigger()
    assert not action.isChecked() and not engine._animation_enabled
    assert engine.renderer.GetActiveCamera().GetPosition() == pytest.approx(
        engine.shots[BodyRegion.FULL_BODY].position
    )
    assert field.text() == "bad" and active.state is state
    restored = create_window(
        window._settings_store._path, original_navigation=True, enable_vtk=True
    )
    try:
        assert not restored._assessment_menu.camera_animation.isChecked()
        assert not restored._body_renderer._animation_enabled
    finally:
        restored.close()
    action.trigger()
    assert action.isChecked() and engine._animation_enabled
    assert field.text() == "bad" and active.state is state
    assert (
        window._settings_store.load().decimal_convention == settings.decimal_convention
    )


def test_disabled_focus_keeps_full_body_through_region_changes(
    window: LifftWindow,
) -> None:
    """Disabled focus retains full-body framing and preserves manual zoom.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    engine = window._body_renderer
    engine.set_animation_enabled(False)
    click(window, 1)
    assert not engine._timer.isActive()
    assert engine.renderer.GetActiveCamera().GetPosition() == pytest.approx(
        engine.shots[BodyRegion.FULL_BODY].position
    )
    engine.zoom_view()
    scale = engine.renderer.GetActiveCamera().GetParallelScale()
    engine.set_state(BodyViewState(BodyRegion.DISTAL_UPPER_EXTREMITIES))
    assert engine.renderer.GetActiveCamera().GetParallelScale() == scale


def test_version_two_camera_default_and_boolean_validation(tmp_path: Path) -> None:
    """Old comma preferences load read-only; invalid new policy is never coerced.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    import json

    from ergotools.application.settings import UserSettings
    from ergotools.domain.decimal_convention import DecimalConvention
    from ergotools.infrastructure.settings_store import SettingsFormatError

    path = tmp_path / "settings.json"
    old = dict(
        format="ergotools.user-settings",
        version=2,
        language="es",
        default_units="metric",
        recent_documents=["old"],
        decimal_convention=",",
    )
    path.write_text(json.dumps(old))
    original = path.read_bytes()
    store = JsonSettingsStore(path)
    loaded = store.load()
    assert loaded.animated_body_region_focus is True
    assert loaded.decimal_convention is DecimalConvention.COMMA
    assert path.read_bytes() == original
    store.save(loaded)
    payload = json.loads(path.read_text())
    assert payload["version"] == 7
    for invalid in (0, "true", None):
        payload["animated_body_region_focus"] = invalid
        path.write_text(json.dumps(payload))
        with pytest.raises(SettingsFormatError):
            store.load()
        with pytest.raises(ValueError):
            UserSettings(animated_body_region_focus=invalid)

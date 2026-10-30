"""Exercise owned toolbar history and simple VTK anatomical tool selection.

Test layer: disposable projects and the approved Qt/VTK baseline. No operational
project, source calculation, reference asset or environment is modified.
"""

from pathlib import Path

import pytest
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QImage
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication
from vtkmodules.vtkRenderingCore import vtkPropPicker

from ergotools.application.contracts.body_renderer import BodyRegion
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.bootstrap import create_window
from ergotools.infrastructure.resources import read_asset
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_saved_tool_data import window as window


def test_redo_is_exact_static_mirror() -> None:
    """Require the saved Redo asset to preserve every mirrored Undo pixel.

    Args:
        None.

    Returns:
        None; compare decoded pixels, canvas size and alpha rather than PNG encoding.
    """
    undo = QImage.fromData(read_asset("icons/undo.png"))
    redo = QImage.fromData(read_asset("icons/redo.png"))
    assert not redo.isNull() and redo == undo.mirrored(True, False)


def test_main_toolbar_shares_history_and_keeps_settings_help_in_menus(
    window: LifftWindow,
) -> None:
    """Route visible buttons through existing source history without saving.

    Args:
        window: Fixture-owned integrated classified three-tool assessment window.

    Returns:
        None; assert action order, exact Undo/Redo and retained menu access.
    """
    navigation = window.main_navigation
    menu = window._assessment_menu
    assert navigation is not None and menu is not None
    actions = navigation.toolbar.actions()
    assert actions[:2] == [navigation.toolbar_actions[k] for k in ("undo", "redo")]
    assert navigation.toolbar_actions["settings"] not in actions
    assert navigation.toolbar_actions["help"] not in actions
    assert menu.preferences.isEnabled() and menu.user_guide.isEnabled()
    active = window.presenter.workspace.active
    before = active.state
    window.add_task()
    changed = active.state
    assert changed != before
    window.setFocus()
    window.history_actions.refresh()
    undo = navigation.toolbar.widgetForAction(navigation.toolbar_actions["undo"])
    redo = navigation.toolbar.widgetForAction(navigation.toolbar_actions["redo"])
    assert undo.isEnabled() and not redo.isEnabled()
    QTest.mouseClick(undo, Qt.MouseButton.LeftButton)
    assert active.state is before and redo.isEnabled()
    QTest.mouseClick(redo, Qt.MouseButton.LeftButton)
    assert active.state is changed


def actor_point(
    engine: object, key: str, *, release_offset: QPoint | None = None
) -> QPoint:
    """Locate an exposed colored actor pixel using its small projected bounds.

    Args:
        engine: Borrowed native VTK adapter from the fixture window.
        key: Existing mesh identity whose visible surface must be selectable.
        release_offset: Optional held-click movement; verify its release pixel stays
            on this actor, so mesh-edge crossings do not invalidate the gesture.

    Returns:
        Widget pixel coordinate selecting that exact frontmost actor at press and
        optional offset release. No renderer/camera state is changed.

    Raises:
        AssertionError: The native viewport fails to settle, or no exposed gesture
            endpoints exist in the bounded projected mesh area.
    """
    # Qt can deliver a deferred layout/VTK resize after the first processEvents().
    # Pick only after two stable frame intervals, then verify both gesture endpoints.
    stable = 0
    previous = None
    for _ in range(10):
        QTest.qWait(20)
        geometry = (
            engine.widget.size(),
            engine.render_window.GetSize(),
            engine.renderer.GetActiveCamera().GetParallelScale(),
        )
        stable = stable + 1 if geometry == previous else 0
        if stable == 2:
            break
        previous = geometry
    else:
        raise AssertionError("Native viewport did not settle before actor picking")
    actor = engine.actors[key]
    bounds = actor.GetBounds()
    points = []
    for x in bounds[:2]:
        for y in bounds[2:4]:
            for z in bounds[4:6]:
                engine.renderer.SetWorldPoint(x, y, z, 1)
                engine.renderer.WorldToDisplay()
                points.append(engine.renderer.GetDisplayPoint())
    width, height = engine.render_window.GetSize()
    left, right = min(v[0] for v in points), max(v[0] for v in points)
    bottom, top = min(v[1] for v in points), max(v[1] for v in points)
    picker = vtkPropPicker()
    for a in range(1, 10):
        for b in range(1, 10):
            x, y = left + (right - left) * a / 10, bottom + (top - bottom) * b / 10
            point = QPoint(
                round(x * engine.widget.width() / width),
                round((height - 1 - y) * engine.widget.height() / height),
            )
            # Both integer Qt endpoints must hit the intended frontmost region.
            # A one-pixel drift from an edge can correctly land on neutral anatomy.
            targets = (
                (point,) if release_offset is None else (point, point + release_offset)
            )
            for target in targets:
                picker.Pick(
                    target.x() * width / engine.widget.width(),
                    height - 1 - target.y() * height / engine.widget.height(),
                    0,
                    engine.renderer,
                )
                if picker.GetActor() != actor:
                    break
            else:
                return point
    raise AssertionError(f"No exposed picking point for {key}")


def test_native_colored_region_clicks_drag_and_animation(
    window: LifftWindow,
    tmp_path: Path,
) -> None:
    """Pick real mesh actors; reuse tool/context navigation and optional animation.

    Args:
        window: Fixture-owned classified project with all three tools available.
        tmp_path: Disposable settings directory; reference projects stay untouched.

    Returns:
        None; assert exact source preservation, no drag selection, neutral no-op,
        three tool mappings and enabled/disabled camera animation.
    """
    view = create_window(
        tmp_path / "native.json", original_navigation=True, enable_vtk=True
    )
    app = QApplication.instance()
    try:
        view.open_project_location(window.presenter.workspace.location)
        view.select_tool(0)
        view.task_panel.calculate_button.click()
        view.show()
        app.processEvents()
        engine = view._body_renderer
        engine.set_animation_enabled(False)
        calls = []

        def selected(region: BodyRegion) -> None:
            """Record and route a picked anatomical region through the host.

            Args:
                region: Typed available anatomical region selected by VTK.

            Returns:
                None; retain ordinary host validation and tool-selection policy.
            """
            calls.append(region)
            view.select_body_region(region)

        engine.set_region_selected(selected)
        for key, region, index in (
            ("left_arm", BodyRegion.DISTAL_UPPER_EXTREMITIES, 1),
            ("left_shoulder", BodyRegion.SHOULDERS, 2),
            ("back", BodyRegion.LOW_BACK, 0),
        ):
            point = actor_point(engine, key)
            QTest.mouseClick(engine.widget, Qt.MouseButton.LeftButton, pos=point)
            app.processEvents()
            assert calls[-1] is region
            assert view.assessment_tabs.currentIndex() == index
            assert not engine._timer.isActive()
        before = tuple(calls)
        camera = engine.renderer.GetActiveCamera()
        neutral_pose = (camera.GetPosition(), camera.GetViewUp())
        QTest.mousePress(engine.widget, Qt.MouseButton.LeftButton, pos=QPoint(1, 1))
        QTest.qWait(100)
        QTest.mouseRelease(engine.widget, Qt.MouseButton.LeftButton, pos=QPoint(1, 1))
        app.processEvents()
        assert tuple(calls) == before
        assert (camera.GetPosition(), camera.GetViewUp()) == neutral_pose
        point = actor_point(engine, "left_arm")
        QTest.mousePress(engine.widget, Qt.MouseButton.LeftButton, pos=point)
        QTest.mouseMove(engine.widget, point + QPoint(20, 0))
        QTest.qWait(100)
        assert (camera.GetPosition(), camera.GetViewUp()) != neutral_pose
        QTest.mouseRelease(
            engine.widget, Qt.MouseButton.LeftButton, pos=point + QPoint(20, 0)
        )
        app.processEvents()
        assert tuple(calls) == before
        released_pose = (camera.GetPosition(), camera.GetViewUp())
        QTest.qWait(100)
        assert (camera.GetPosition(), camera.GetViewUp()) == released_pose
        engine.set_animation_enabled(True)
        source = view.presenter.workspace.active.state
        view.select_body_region(BodyRegion.SHOULDERS)
        assert view.assessment_tabs.currentIndex() == 2 and engine._timer.isActive()
        view.select_body_region(BodyRegion.LOW_BACK)
        assert view.presenter.workspace.active.state is source
        engine.close()
        engine.pick_region(0, 0)
        assert tuple(calls) == before
    finally:
        view.presenter.workspace.close(choice=CloseChoice.DISCARD)
        view.close()
        app.processEvents()


@pytest.mark.parametrize("animated", [False, True])
def test_realistic_click_hold_does_not_rotate_before_tool_selection(
    window: LifftWindow,
    tmp_path: Path,
    animated: bool,
) -> None:
    """A normal held click with tiny hand motion must not start VTK camera rotation.

    Args:
        window: Fixture-owned classified three-tool project.
        tmp_path: Disposable native-window settings directory.
        animated: Existing camera-focus preference to test in both states.

    Returns:
        None; assert stable camera during the click, correct selection on release,
        final framing, and no delayed VTK rotation after focus animation completes.
    """
    view = create_window(
        tmp_path / "hold.json", original_navigation=True, enable_vtk=True
    )
    app = QApplication.instance()
    try:
        view.open_project_location(window.presenter.workspace.location)
        view.select_tool(0)
        view.task_panel.calculate_button.click()
        view.show()
        app.processEvents()
        engine = view._body_renderer
        engine.set_animation_enabled(animated)
        point = actor_point(engine, "left_arm", release_offset=QPoint(1, 0))
        camera = engine.renderer.GetActiveCamera()
        original = (camera.GetPosition(), camera.GetFocalPoint(), camera.GetViewUp())
        QTest.mousePress(engine.widget, Qt.MouseButton.LeftButton, pos=point)
        QTest.qWait(160)
        QTest.mouseMove(engine.widget, point + QPoint(1, 0))
        QTest.qWait(160)
        assert (
            camera.GetPosition(),
            camera.GetFocalPoint(),
            camera.GetViewUp(),
        ) == original
        QTest.mouseRelease(
            engine.widget, Qt.MouseButton.LeftButton, pos=point + QPoint(1, 0)
        )
        app.processEvents()
        assert view.assessment_tabs.currentIndex() == 1
        QTest.qWait(900)
        shot = engine.shots[
            BodyRegion.DISTAL_UPPER_EXTREMITIES if animated else BodyRegion.FULL_BODY
        ]
        assert camera.GetPosition() == pytest.approx(shot.position)
        assert camera.GetViewUp() == pytest.approx(shot.view_up)
        settled = (camera.GetPosition(), camera.GetFocalPoint(), camera.GetViewUp())
        QTest.qWait(160)
        assert (
            camera.GetPosition(),
            camera.GetFocalPoint(),
            camera.GetViewUp(),
        ) == settled
    finally:
        view.presenter.workspace.close(choice=CloseChoice.DISCARD)
        view.close()
        app.processEvents()

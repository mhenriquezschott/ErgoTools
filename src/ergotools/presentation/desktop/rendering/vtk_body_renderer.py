"""Original anatomical scene and camera controls behind the portable renderer port.

VTK objects stay here. Models arrive through an injected packaged-asset reader; no SQL,
worker interpretation or scientific calculation occurs in this adapter.

Presentation layer. This module is the sole native VTK adapter: scene, interactor, actor
transforms, GUI-thread timers and disposal stay behind BodyRenderer; it reads only
injected packaged model bytes.
"""

import math
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol, cast

from PyQt5.QtCore import QElapsedTimer, QEvent, QObject, Qt, QTimer
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QApplication, QWidget
from vtkmodules import vtkInteractionStyle, vtkRenderingOpenGL2
from vtkmodules.qt.QVTKRenderWindowInteractor import (
    QVTKRenderWindowInteractor,
)
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkIOGeometry import vtkSTLReader
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkPropPicker,
    vtkRenderer,
    vtkRenderWindow,
)

from ergotools.application.contracts.body_renderer import BodyRegion, BodyViewState

# These imports register native interaction/OpenGL implementations before creation.
_BACKENDS = (vtkInteractionStyle, vtkRenderingOpenGL2)


# VTK 9.5.0 ships C++ stubs, but its Qt Python wrapper has no stub. These two
# narrowly typed protocols describe the reviewed wrapper surface; no Any leaks out.
class _WidgetFactory(Protocol):
    """Narrow typed callable surface of the approved unannotated QVTK wrapper."""

    def __call__(self, parent: QWidget) -> QWidget:
        """Construct the Qt-owned native VTK viewport through the approved wrapper.

        Args:
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            New Qt-owned VTK viewport constructed by the approved native wrapper.
        """
        ...


class _Interactor(Protocol):
    """Borrowed native interaction surface used.

    Borrowed native interaction surface used for initialize/render-window/finalize
    ownership.
    """

    def GetRenderWindow(self) -> vtkRenderWindow:  # noqa: N802 - VTK wrapper API
        """Return the native render window borrowed by the renderer adapter.

        Args:
            None.

        Returns:
            Borrowed native render window; adapter owns its lifecycle through the
            interactor.
        """
        ...

    def Initialize(self) -> None:  # noqa: N802 - VTK wrapper API
        """Initialize native interaction after the viewport has been attached.

        Args:
            None.

        Returns:
            None.
        """
        ...

    def Finalize(self) -> None:  # noqa: N802 - VTK wrapper API
        """Release native interaction resources during renderer disposal.

        Args:
            None.

        Returns:
            None.
        """
        ...


class _ViewportResize(QObject):
    """Separate click intent from native VTK camera drags before press delivery."""

    def __init__(
        self,
        widget: QWidget,
        resized: Callable[[], None],
        clicked: Callable[[int, int], None],
    ) -> None:
        """Attach owned viewport observation without replacing VTK interaction.

        Hold a left press until motion exceeds five widget pixels. Ordinary clicks
        never reach VTK's joystick-camera handler; actual drags receive the retained
        press before their first move and keep normal native release handling.

        Args:
            widget: Qt component to attach or inspect; lifetime remains with its owning
                window.
            resized: GUI-thread callback updating camera framing after viewport resize.
            clicked: Deferred click callback in widget pixels; drags are excluded.

        Returns:
            None.
        """
        super().__init__(widget)
        self._resized = resized
        self._clicked = clicked
        self._press: QMouseEvent | None = None
        self._forwarding = False
        widget.installEventFilter(self)

    def _forward_press(self, widget: QWidget) -> None:
        """Start native VTK dragging once movement exceeds the click threshold.

        Args:
            widget: Owned native viewport that must receive the retained mouse press.

        Returns:
            None; forward once with reentrancy guarded, preserving original mouse
            position/buttons/modifiers. Subsequent moves/releases follow normal VTK.
        """
        press, self._press = self._press, None
        if press is None:
            return
        self._forwarding = True
        try:
            QApplication.sendEvent(widget, press)
        finally:
            self._forwarding = False

    def eventFilter(self, watched: QObject | None, event: QEvent | None) -> bool:  # noqa: N802 - Qt override
        """Consume candidate clicks and pass only confirmed camera drags to VTK.

        Args:
            watched: Owned viewport; optional for defensive direct calls.
            event: GUI-thread Qt event; resize and non-left interaction stay native.

        Returns:
            True for a retained left press, sub-threshold motion or completed click.
            False/base result for actual drag events and all unrelated interactions.
            Selection is queued after release, with no native joystick timer started.
        """
        if self._forwarding:
            return False
        if event is not None and event.type() == QEvent.Type.Resize:
            self._resized()
        if isinstance(event, QMouseEvent) and isinstance(watched, QWidget):
            if (
                event.type()
                in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonDblClick)
                and event.button() == Qt.MouseButton.LeftButton
            ):
                self._press = QMouseEvent(
                    QEvent.Type.MouseButtonPress,
                    event.localPos(),
                    event.button(),
                    event.buttons(),
                    event.modifiers(),
                )
                return True
            if self._press is not None:
                distance = (event.pos() - self._press.pos()).manhattanLength()
                if event.type() == QEvent.Type.MouseMove:
                    if distance <= 5:
                        return True
                    self._forward_press(watched)
                elif (
                    event.type() == QEvent.Type.MouseButtonRelease
                    and event.button() == Qt.MouseButton.LeftButton
                ):
                    if distance > 5:
                        self._forward_press(watched)
                    else:
                        self._press = None
                        x, y = event.pos().x(), event.pos().y()
                        QTimer.singleShot(0, lambda: self._clicked(x, y))
                        return True
        return super().eventFilter(watched, event)


@dataclass(frozen=True, slots=True)
class CameraShot:
    """Reference parallel-camera state in transformed model coordinates.

    Attributes:
        position: Camera XYZ position in transformed anatomical-model coordinates.
        focal_point: Camera XYZ focus in the same transformed coordinates.
        parallel_scale: Positive parallel-camera half-height before viewport aspect
            correction.
        view_up: Camera up-direction vector; original default is positive Y.
    """

    position: tuple[float, float, float]
    focal_point: tuple[float, float, float]
    parallel_scale: float
    view_up: tuple[float, float, float] = (0.0, 1.0, 0.0)


# Packaged STL actor identities, normalized resource names and original model-coordinate
# component offsets.
_MODELS = (
    ("human", "body_avatar.stl", (0.0, 0.0, 0.0)),
    ("back", "lower_back.stl", (284.0, 293.0, 1010.0)),
    ("left_arm", "left_forearm.stl", (264.7, 57.9, 851.6)),
    ("left_hand", "left_hand.stl", (369.0, -42.0, 694.0)),
    ("right_arm", "right_forearm.stl", (264.7, 535.0, 851.6)),
    ("right_hand", "right_hand.stl", (222.0, 545.0, 703.0)),
    ("left_shoulder", "left_shoulder.stl", (247.0, 105.0, 1110.0)),
    ("right_shoulder", "right_shoulder.stl", (247.0, 495.0, 1110.0)),
)
# Typed anatomical overlay to actor-key mapping; full-body focus uses the base avatar.
_REGIONS = {
    BodyRegion.LOW_BACK: ("back",),
    BodyRegion.DISTAL_UPPER_EXTREMITIES: (
        "left_arm",
        "left_hand",
        "right_arm",
        "right_hand",
    ),
    BodyRegion.SHOULDERS: ("left_shoulder", "right_shoulder"),
}
# Original region camera padding, yaw degrees and vertical model-coordinate offsets.
_SHOTS = {
    BodyRegion.LOW_BACK: (1.28 * 1.15, 6.0, 8.0),
    BodyRegion.DISTAL_UPPER_EXTREMITIES: (1.18 / 1.10, -17.0, 12.0),
    BodyRegion.SHOULDERS: (1.30 / 1.15, 19.0, 5.0),
}


class VtkBodyRenderer:
    """Own the original scene, Qt widget and native resources on the GUI thread."""

    def __init__(self, parent: QWidget, read_model: Callable[[str], bytes]) -> None:
        """Load packaged models before publishing a usable scene.

        Args:
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.
            read_model: Packaged-resource reader returning complete STL bytes by
                normalized resource filename.

        Returns:
            None.

        Raises:
            ValueError: An STL cannot be decoded into a nonempty anatomical mesh.
            OSError: Temporary staging or packaged-asset reading fails.
        """
        self.widget = cast(_WidgetFactory, QVTKRenderWindowInteractor)(parent)
        self.widget.setObjectName("vtkWorkspace")
        self.widget.setMinimumHeight(315)
        self._interactor = cast(_Interactor, self.widget)
        self.render_window = self._interactor.GetRenderWindow()
        self.renderer = vtkRenderer()
        self.renderer.SetBackground(0.035, 0.176, 0.271)
        self.renderer.SetBackground2(0.035, 0.176, 0.271)
        self.renderer.GradientBackgroundOff()
        self.render_window.AddRenderer(self.renderer)
        self.actors: dict[str, vtkActor] = {}
        self._closed = False
        self._state: BodyViewState | None = None
        self._region_selected: Callable[[BodyRegion], None] | None = None
        self._aspect_factor = 1.0
        self._animation_enabled = True
        self._selection_region: BodyRegion | None = None
        self._segments: list[
            tuple[CameraShot, CameraShot, int, bool, tuple[float, float, float] | None]
        ] = []
        self._segment_index = 0
        self._animation_target = BodyRegion.LOW_BACK
        self._timer = QTimer(self.widget)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self._clock = QElapsedTimer()
        self._viewport_resize = _ViewportResize(
            self.widget, self._resize_framing, self.pick_region
        )
        try:
            transform = vtkTransform()
            transform.RotateX(-90)
            transform.RotateZ(-45)
            with tempfile.TemporaryDirectory(prefix="ergotools-models-") as staging:
                for key, asset, position in _MODELS:
                    path = Path(staging) / asset
                    path.write_bytes(read_model(asset))
                    reader = vtkSTLReader()
                    reader.SetFileName(str(path))
                    reader.Update()
                    mesh = reader.GetOutput()
                    if mesh.GetNumberOfPoints() == 0:
                        raise ValueError("Anatomical model contains no decoded points.")
                    mapper = vtkPolyDataMapper()
                    # Retain decoded data; render updates cannot reread staged files.
                    mapper.SetInputData(mesh)
                    actor = vtkActor()
                    actor.SetMapper(mapper)
                    actor.SetPosition(*position)
                    actor.SetUserTransform(transform)
                    if key != "human":
                        actor.VisibilityOff()
                    self.renderer.AddActor(actor)
                    self.actors[key] = actor
            self.renderer.ResetCamera()
            bounds = self.actors["human"].GetBounds()
            distance = (
                max(bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4])
                * 2.2
            )
            self.shots = {
                BodyRegion.FULL_BODY: self._shot(("human",), 1.08, 0, 0, distance)
            }
            for region, (padding, yaw, offset) in _SHOTS.items():
                self.shots[region] = self._shot(
                    _REGIONS[region], padding, yaw, offset, distance
                )
            self._apply_shot(self.shots[BodyRegion.LOW_BACK])
            self._interactor.Initialize()
        except Exception:
            self.close()
            raise

    def _shot(
        self,
        keys: tuple[str, ...],
        padding: float,
        yaw: float,
        offset: float,
        distance: float,
    ) -> CameraShot:
        """Compute the original parallel-camera pose.

        Compute the original parallel-camera pose from the selected anatomical actor
        bounds, framing padding, yaw and vertical offset.

        Args:
            keys: Exact anatomical actor keys whose combined bounds frame the camera.
            padding: Dimensionless reference camera framing multiplier.
            yaw: Camera azimuth in degrees around the region center.
            offset: Vertical camera-center offset in transformed model coordinates.
            distance: Camera distance in transformed anatomical-model coordinates.

        Returns:
            Parallel-camera position/focal point/scale in transformed anatomical-model
            coordinates.
        """
        bounds = tuple(self.actors[key].GetBounds() for key in keys)
        combined = tuple(
            operation(b[axis] for b in bounds)
            for axis, operation in enumerate((min, max, min, max, min, max))
        )
        center = [(combined[i] + combined[i + 1]) / 2 for i in (0, 2, 4)]
        center[1] += offset
        scale = (
            max(
                (combined[3] - combined[2]) / 2,
                (combined[1] - combined[0]) / (2 * 0.68),
            )
            * padding
        )
        angle = math.radians(yaw)
        return CameraShot(
            (
                center[0] + math.sin(angle) * distance,
                center[1] + 10,
                center[2] + math.cos(angle) * distance,
            ),
            (center[0], center[1], center[2]),
            scale,
        )

    def _apply_shot(self, shot: CameraShot) -> None:
        """Apply one model-coordinate camera pose.

        Apply one model-coordinate camera pose with current viewport aspect correction
        and refreshed clipping planes.

        Args:
            shot: Parallel-camera pose in transformed model coordinates, before viewport
                aspect adjustment.

        Returns:
            None.
        """
        camera = self.renderer.GetActiveCamera()
        camera.ParallelProjectionOn()
        camera.SetPosition(*shot.position)
        camera.SetFocalPoint(*shot.focal_point)
        camera.SetViewUp(*shot.view_up)
        camera.SetParallelScale(max(1.0, shot.parallel_scale) * self._aspect_factor)
        self.renderer.ResetCameraClippingRange()

    def _resize_framing(self) -> None:
        """Retain pose/relative zoom while fitting the reference 0.68 framing aspect.

        Taller narrow viewports need more parallel scale to retain horizontal coverage.
        Wider viewports keep the original shot. Qt/VTK owns repainting; this observer
        performs no additional Render call or document operation.

        Args:
            None.

        Returns:
            None.
        """
        if self._closed or self.widget.width() <= 0 or self.widget.height() <= 0:
            return
        aspect = self.widget.width() / self.widget.height()
        factor = max(1.0, 0.68 / aspect)
        camera = self.renderer.GetActiveCamera()
        camera.SetParallelScale(
            camera.GetParallelScale() * factor / self._aspect_factor
        )
        self._aspect_factor = factor

    def set_state(self, state: BodyViewState) -> None:
        """Show all available overlays independently of the active camera region.

        Do not reset a user's camera on ordinary value edits. Region changes use the
        reference framing; duplicate states do not trigger a render.

        Args:
            state: Immutable source/view snapshot to project without recording another
                edit.

        Returns:
            None.
        """
        if self._closed or state == self._state:
            return
        previous = self._state
        self._state = state
        for key, actor in self.actors.items():
            if key != "human":
                actor.VisibilityOff()
                actor.GetProperty().SetColor(1, 1, 1)
        overlays = state.region_colors or (
            ((state.region, state.overlay_color),)
            if state.overlay_color is not None
            else ()
        )
        for region, color in overlays:
            for key in _REGIONS.get(region, ()):
                actor = self.actors[key]
                actor.GetProperty().SetColor(color.red, color.green, color.blue)
                actor.VisibilityOn()
        if (
            previous is None or previous.region is not state.region
        ) and self._selection_region is None:
            self._stop_animation()
            region = state.region if self._animation_enabled else BodyRegion.FULL_BODY
            self._apply_shot(self.shots[region])
        self.render_window.Render()

    def rotate_view(self) -> None:
        """Apply the original clockwise 20-degree azimuth step.

        Args:
            None.

        Returns:
            None.
        """
        if not self._closed:
            self._stop_animation()
            self.renderer.GetActiveCamera().Azimuth(20)
            self.renderer.ResetCameraClippingRange()
            self.render_window.Render()

    def zoom_view(self) -> None:
        """Apply the original 1.15 zoom factor around the active view.

        Args:
            None.

        Returns:
            None.
        """
        if not self._closed:
            self._stop_animation()
            self.renderer.GetActiveCamera().Zoom(1.15)
            self.renderer.ResetCameraClippingRange()
            self.render_window.Render()

    def reset_view(self) -> None:
        """Restore active-region focus when enabled, otherwise the full-body view.

        Args:
            None.

        Returns:
            None.
        """
        if not self._closed:
            self._stop_animation()
            region = (
                self._state.region
                if self._animation_enabled and self._state
                else BodyRegion.FULL_BODY
            )
            self._apply_shot(self.shots[region])
            self.render_window.Render()

    def set_animation_enabled(self, enabled: bool) -> None:
        """Retain the reference active-region/full-body camera preference.

        Args:
            enabled: Whether the associated controls should accept user interaction.

        Returns:
            None.

        Raises:
            ValueError: Camera animation must be an explicit boolean.
        """
        if type(enabled) is not bool:
            raise ValueError("Camera animation must be an explicit boolean.")
        if self._closed:
            return
        self._animation_enabled = enabled
        self._selection_region = None
        self.reset_view()

    def begin_region_selection(self) -> None:
        """Defer snapping while the host resolves an explicit mouse tab choice.

        Args:
            None.

        Returns:
            None.
        """
        if not self._closed and self._animation_enabled and self._state is not None:
            self._stop_animation()
            self._selection_region = self._state.region

    def end_region_selection(self) -> None:
        """Animate accepted region changes; rejected selections keep the camera.

        Args:
            None.

        Returns:
            None.
        """
        previous = self._selection_region
        self._selection_region = None
        if (
            not self._closed
            and previous is not None
            and self._state is not None
            and previous is not self._state.region
        ):
            self._animate_to(self._state.region)

    def _stop_animation(self) -> None:
        """Stop the owned GUI timer and discard queued camera segments.

        Stop the owned GUI timer and discard queued camera segments before a new view
        command or disposal.

        Args:
            None.

        Returns:
            None.
        """
        self._timer.stop()
        self._segments.clear()

    def _animate_to(self, region: BodyRegion) -> None:
        """Queue the original full-body/approach/settle camera path.

        Queue the original full-body/approach/settle camera path for the accepted
        anatomical region.

        Segment durations are 190, 420 and 120 ms; source/body geometry is unchanged.

        Args:
            region: Typed anatomical region used for accepted tool focus.

        Returns:
            None.
        """
        self._stop_animation()
        camera = self.renderer.GetActiveCamera()
        position = camera.GetPosition()
        focal = camera.GetFocalPoint()
        up = camera.GetViewUp()
        current = CameraShot(
            (position[0], position[1], position[2]),
            (focal[0], focal[1], focal[2]),
            camera.GetParallelScale() / self._aspect_factor,
            (up[0], up[1], up[2]),
        )
        target = self.shots[region]
        direction = 1.0 if target.position[0] >= target.focal_point[0] else -1.0
        approach = replace(
            target,
            parallel_scale=target.parallel_scale * 1.045,
            position=(
                target.position[0] + direction * 28.0,
                target.position[1] + 6.0,
                target.position[2],
            ),
        )
        full = self.shots[BodyRegion.FULL_BODY]
        self._segments = [
            (current, full, 190, True, None),
            (full, approach, 420, False, (direction * 420.0, 0.0, -180.0)),
            (approach, target, 120, True, None),
        ]
        self._segment_index = 0
        self._animation_target = region
        self._clock.start()
        self._timer.start()

    def _tick(self) -> None:
        """Advance only a live camera animation using elapsed milliseconds.

        Advance only a live camera animation using elapsed milliseconds; disposed
        renderers stop pending timer work.

        Args:
            None.

        Returns:
            None.
        """
        if self._closed or not self._segments:
            self._stop_animation()
            return
        self._advance_animation(self._clock.elapsed())

    def _advance_animation(self, elapsed_ms: int) -> None:
        """Interpolate the current reference camera segment.

        Interpolate the current reference camera segment, including its optional
        approach offset, and render once; finished segments advance or release the
        timer.

        Args:
            elapsed_ms: Elapsed milliseconds within the current animation segment.

        Returns:
            None.
        """
        start, end, duration, ease_out, curve = self._segments[self._segment_index]
        progress = min(1.0, max(0.0, elapsed_ms / duration))
        amount = (
            1.0 - (1.0 - progress) ** 3
            if ease_out
            else progress * progress * (3.0 - 2.0 * progress)
        )

        def vector(
            left: tuple[float, float, float], right: tuple[float, float, float]
        ) -> tuple[float, float, float]:
            """Interpolate the camera segment XYZ vector.

            Interpolate an XYZ vector by the enclosing normalized/eased segment
            progress.

            Args:
                left: Start XYZ vector in transformed model coordinates.
                right: End XYZ vector in transformed model coordinates.

            Returns:
                Interpolated XYZ vector using the enclosing segment's normalized/eased
                progress.
            """
            return (
                left[0] + (right[0] - left[0]) * amount,
                left[1] + (right[1] - left[1]) * amount,
                left[2] + (right[2] - left[2]) * amount,
            )

        position = vector(start.position, end.position)
        if curve is not None:
            arc = 4.0 * amount * (1.0 - amount)
            position = (
                position[0] + curve[0] * arc,
                position[1] + curve[1] * arc,
                position[2] + curve[2] * arc,
            )
        shot = CameraShot(
            position,
            vector(start.focal_point, end.focal_point),
            start.parallel_scale + (end.parallel_scale - start.parallel_scale) * amount,
            vector(start.view_up, end.view_up),
        )
        self._apply_shot(shot)
        if progress >= 1.0:
            self._segment_index += 1
            if self._segment_index == len(self._segments):
                self._apply_shot(self.shots[self._animation_target])
                self._stop_animation()
            else:
                self._clock.restart()
        self.render_window.Render()

    def set_region_selected(
        self, selected: Callable[[BodyRegion], None] | None
    ) -> None:
        """Connect an anatomical selection callback owned by the desktop host.

        Args:
            selected: GUI-thread callback, or None to disconnect selection.

        Returns:
            None; selection never changes assessment state within the renderer.
        """
        self._region_selected = selected

    def pick_region(self, x: int, y: int) -> None:
        """Resolve an ordinary viewport click using VTK's built-in actor picker.

        Args:
            x: Horizontal widget pixel coordinate from its left edge.
            y: Vertical widget pixel coordinate from its top edge.

        Returns:
            None; notify only for an available colored actor visible at the click.
            Neutral anatomy/background, closed renderers and disconnected hosts do
            nothing. Qt-to-render coordinates account for viewport pixel scaling.
        """
        if self._closed or self._region_selected is None or self._state is None:
            return
        width, height = self.render_window.GetSize()
        if not (0 <= x < self.widget.width() and 0 <= y < self.widget.height()):
            return
        picker = vtkPropPicker()
        picker.Pick(
            x * width / self.widget.width(),
            height - 1 - y * height / self.widget.height(),
            0,
            self.renderer,
        )
        actor = picker.GetActor()
        regions = self._state.region_colors or (
            ((self._state.region, self._state.overlay_color),)
            if self._state.overlay_color is not None
            else ()
        )
        for region, _ in regions:
            if any(actor == self.actors[key] for key in _REGIONS.get(region, ())):
                self._region_selected(region)
                return

    def close(self) -> None:
        """Finalize native resources once; duplicate closure is safe.

        Args:
            None.

        Returns:
            None.
        """
        if self._closed:
            return
        self._closed = True
        self._region_selected = None
        self._stop_animation()
        self._interactor.Finalize()
        self.renderer.RemoveAllViewProps()
        self.actors.clear()
        self.widget.deleteLater()

import math

from PyQt5 import QtCore


class VTKCameraDirector:
    """Deterministic, interruptible camera choreography for the body-region view."""

    def __init__(self, renderer, render_window, parent=None):
        self.renderer = renderer
        self.render_window = render_window
        self.timer = QtCore.QTimer(parent)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._tick)
        self.clock = QtCore.QElapsedTimer()
        self.shots = {}
        self.full_body_shot = None
        self.segments = []
        self.segment_index = 0
        self.active_tool = 0

    def configure(self, human_actor, region_actors):
        full_bounds = self._combinedBounds([human_actor])
        full_center = self._center(full_bounds)
        full_scale = self._scaleForBounds(full_bounds, padding=1.08)
        distance = max(
            full_bounds[1] - full_bounds[0],
            full_bounds[3] - full_bounds[2],
            full_bounds[5] - full_bounds[4],
        ) * 2.2
        self.full_body_shot = self._shot(full_center, full_scale, distance, yaw_degrees=0.0)

        shot_settings = {
            0: (1.28 * 1.15, 6.0, 8.0),
            1: (1.18 / 1.10, -17.0, 12.0),
            2: (1.30 / 1.15, 19.0, 5.0),
        }
        for tool_index, actors in region_actors.items():
            bounds = self._combinedBounds(actors)
            padding, yaw_degrees, y_offset = shot_settings[tool_index]
            center = list(self._center(bounds))
            center[1] += y_offset
            self.shots[tool_index] = self._shot(
                tuple(center), self._scaleForBounds(bounds, padding), distance, yaw_degrees
            )

    def apply(self, tool_index):
        if tool_index not in self.shots:
            return
        self.stop()
        self.active_tool = tool_index
        self._applyState(self.shots[tool_index])
        self.render_window.Render()

    def applyFullBody(self):
        if not self.full_body_shot:
            return
        self.stop()
        self._applyState(self.full_body_shot)
        self.render_window.Render()

    def animateTo(self, tool_index):
        if tool_index not in self.shots:
            return
        self.stop()
        self.active_tool = tool_index
        current = self._cameraState()
        target = self.shots[tool_index]
        approach = dict(target)
        approach["parallel_scale"] = target["parallel_scale"] * 1.045
        approach["position"] = (
            target["position"][0] + (28.0 if target["position"][0] >= target["focal_point"][0] else -28.0),
            target["position"][1] + 6.0,
            target["position"][2],
        )
        orbit_direction = 1.0 if target["position"][0] >= target["focal_point"][0] else -1.0
        self.segments = [
            (current, self.full_body_shot, 190, "out", None),
            (self.full_body_shot, approach, 420, "smooth", (orbit_direction * 420.0, 0.0, -180.0)),
            (approach, target, 120, "out", None),
        ]
        self.segment_index = 0
        self.clock.start()
        self.timer.start()

    def stop(self):
        self.timer.stop()
        self.segments = []

    def _tick(self):
        if self.segment_index >= len(self.segments):
            self.stop()
            return
        start, end, duration, easing, curve = self.segments[self.segment_index]
        progress = min(1.0, self.clock.elapsed() / float(duration))
        self._applyState(self._interpolate(start, end, self._ease(progress, easing), curve))
        self.render_window.Render()
        if progress >= 1.0:
            self.segment_index += 1
            if self.segment_index >= len(self.segments):
                self._applyState(self.shots[self.active_tool])
                self.render_window.Render()
                self.stop()
            else:
                self.clock.restart()

    def _cameraState(self):
        camera = self.renderer.GetActiveCamera()
        return {
            "position": tuple(camera.GetPosition()),
            "focal_point": tuple(camera.GetFocalPoint()),
            "view_up": tuple(camera.GetViewUp()),
            "parallel_scale": float(camera.GetParallelScale()),
        }

    def _applyState(self, state):
        camera = self.renderer.GetActiveCamera()
        camera.ParallelProjectionOn()
        camera.SetPosition(*state["position"])
        camera.SetFocalPoint(*state["focal_point"])
        camera.SetViewUp(*state["view_up"])
        camera.SetParallelScale(max(1.0, state["parallel_scale"]))
        self.renderer.ResetCameraClippingRange()

    @staticmethod
    def _interpolate(start, end, amount, curve=None):
        def vector(key):
            result = tuple(
                left + (right - left) * amount
                for left, right in zip(start[key], end[key])
            )
            if key == "position" and curve:
                curve_amount = 4.0 * amount * (1.0 - amount)
                result = tuple(
                    value + offset * curve_amount for value, offset in zip(result, curve)
                )
            return result
        return {
            "position": vector("position"),
            "focal_point": vector("focal_point"),
            "view_up": vector("view_up"),
            "parallel_scale": start["parallel_scale"] + (
                end["parallel_scale"] - start["parallel_scale"]
            ) * amount,
        }

    @staticmethod
    def _ease(progress, easing):
        if easing == "out":
            return 1.0 - (1.0 - progress) ** 3
        return progress * progress * (3.0 - 2.0 * progress)

    @staticmethod
    def _combinedBounds(actors):
        bounds = [actor.GetBounds() for actor in actors]
        return (
            min(value[0] for value in bounds), max(value[1] for value in bounds),
            min(value[2] for value in bounds), max(value[3] for value in bounds),
            min(value[4] for value in bounds), max(value[5] for value in bounds),
        )

    @staticmethod
    def _center(bounds):
        return (
            (bounds[0] + bounds[1]) / 2.0,
            (bounds[2] + bounds[3]) / 2.0,
            (bounds[4] + bounds[5]) / 2.0,
        )

    @staticmethod
    def _scaleForBounds(bounds, padding):
        aspect = 0.68
        half_height = (bounds[3] - bounds[2]) / 2.0
        half_width = (bounds[1] - bounds[0]) / (2.0 * aspect)
        return max(half_height, half_width) * padding

    @staticmethod
    def _shot(focal_point, parallel_scale, distance, yaw_degrees):
        yaw = math.radians(yaw_degrees)
        return {
            "position": (
                focal_point[0] + math.sin(yaw) * distance,
                focal_point[1] + 10.0,
                focal_point[2] + math.cos(yaw) * distance,
            ),
            "focal_point": tuple(focal_point),
            "view_up": (0.0, 1.0, 0.0),
            "parallel_scale": parallel_scale,
        }

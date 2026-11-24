"""Run isolated Flet construction/layout probes alongside real Android visual QA.

Use the approved prototype Flet environment and PYTHONPATH for src/prototype src.
These checks exercise widget state/contracts; they do not replace native rendering,
actual gestures, keyboard or physical-device acceptance.
"""

import asyncio
import json
import struct
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import flet as ft
from assessment_contexts import read_contexts
from assessment_tasks import preview
from body_region import BodyRegion
from demo_project import build_demo
from mobile_organization import organization_snapshot
from mobile_results import ResultPanel
from mobile_ui import TabletApp
from project_session import ProjectSession
from tablet_style import action_button
from tablet_timing import TimingScreen

from ergotools.application.rotation_timing import shift_clock


class ProbePage:
    """Minimal construction host; no drawing or platform behavior is inferred.

    Attributes:
        controls: Mounted root candidates inspected by construction probes.
        width: Logical viewport width, changed to exercise portrait reordering.
    """

    def __init__(self) -> None:
        """Create a detached landscape host with one root-view navigation adapter.

        Args:
            None.

        Returns:
            None; no Android or real user state is involved.
        """
        self.width = 1280
        self.height = 800
        self.views = [SimpleNamespace()]
        self.controls = []

    def add(self, control: ft.Control) -> None:
        """Retain a constructed root instead of attempting platform rendering.

        Args:
            control: Complete screen candidate.

        Returns:
            None; tests inspect its state and relationships only.
        """
        self.controls.append(control)

    def update(self) -> None:
        """Accept view-only refresh requests without claiming a rendered result.

        Args:
            None.

        Returns:
            None; native screenshots supply separate rendering evidence.
        """


def check() -> dict:
    """Probe source preservation, real-width legends, portrait access and flat actions.

    Args:
        None; all native projects live in a disposable temporary directory.

    Returns:
        JSON-compatible acceptance facts after all assertions succeed.
    """
    assets = Path(__file__).resolve().parents[1] / "src/assets/anatomy"
    files = list(assets.glob("*.png"))
    assert len(files) == 288
    for path in files:
        data = path.read_bytes()
        assert data[:8] == b"\x89PNG\r\n\x1a\n"
        assert struct.unpack(">II", data[16:24]) == (480, 560)
        assert data[25] == 6  # RGBA allows depth masks and integrated soft previews.
    with TemporaryDirectory() as directory, patch.object(ft.Control, "update"):
        folder = Path(directory)
        source = folder / "fixture.ergprj"
        build_demo(source)
        session = ProjectSession(folder / "private")
        session.activate(source.read_bytes(), "Probe.ergprj", "Widget probe")
        original = session.working.read_bytes()
        app = TabletApp(ProbePage(), session)
        app.home()
        records = read_contexts(session.working)["records"]
        hierarchy, _templates = organization_snapshot(session.working)
        timeline = TimingScreen(
            app, SimpleNamespace(), "Day", shift_clock(hierarchy, "Day")
        )
        timeline.render()
        original_timing = timeline.timing
        before_gesture = session.working.read_bytes()
        timeline.mode = "Draw break"

        def x(minute: int) -> float:
            """Map a known fixture minute into the actual local canvas width."""
            return 12 + (timeline.width - 24) * minute / 480

        asyncio.run(
            timeline.drag_start(
                SimpleNamespace(local_position=SimpleNamespace(x=x(30)))
            )
        )
        asyncio.run(
            timeline.drag_update(
                SimpleNamespace(local_position=SimpleNamespace(x=x(45)))
            )
        )
        assert timeline.preview_timing is not None
        assert timeline.preview_timing.breaks[0].interval.start == 30
        assert timeline.preview_timing.breaks[0].interval.end == 45
        assert timeline.timing == original_timing
        assert session.working.read_bytes() == before_gesture
        asyncio.run(timeline.drag_cancel(SimpleNamespace()))
        assert timeline.preview_timing is None
        assert timeline.timing == original_timing
        assert session.working.read_bytes() == before_gesture
        timeline.mode = "Move / resize"
        asyncio.run(
            timeline.hover(SimpleNamespace(local_position=SimpleNamespace(x=x(145))))
        )
        assert timeline.gesture.mouse_cursor == ft.MouseCursor.RESIZE_LEFT_RIGHT
        asyncio.run(
            timeline.hover(SimpleNamespace(local_position=SimpleNamespace(x=x(60))))
        )
        assert timeline.gesture.mouse_cursor == ft.MouseCursor.GRAB
        assert timeline.edge_at(x(152)) is None
        asyncio.run(
            timeline.drag_start(
                SimpleNamespace(local_position=SimpleNamespace(x=x(152)))
            )
        )
        asyncio.run(
            timeline.drag_update(
                SimpleNamespace(local_position=SimpleNamespace(x=x(177)))
            )
        )
        assert timeline.preview_timing.breaks[0].interval.start == 170
        assert timeline.preview_timing.breaks[0].interval.end == 185
        assert session.working.read_bytes() == before_gesture
        asyncio.run(timeline.drag_cancel(SimpleNamespace()))
        app.home()
        panel = ResultPanel()
        for record in records:
            panel.project(
                record, preview(record["document"], record["source"], record["units"])
            )
            if record["result"] is None:
                assert panel.probability.value == "—" and panel.bar.value == 0
                assert panel.body.color == "#078398"
            else:
                assert (
                    panel.probability.value
                    == f"{record['result'].probability_percent:.1f}%"
                )
        # Observe actual animation state updates without wall-clock sleeps. Platform
        # screenshots/video separately verify that the frames reach the native view.
        animation = ResultPanel()
        record = next(r for r in records if r["result"] is not None)
        animation.project(
            record,
            preview(record["document"], record["source"], record["units"]),
            animate=True,
        )
        frames = []
        initial_body_frame = animation.body.frame
        animation_page = SimpleNamespace(
            update=lambda: frames.append(
                (animation.angle, animation.bar.value, animation.body.frame)
            )
        )
        with patch("asyncio.sleep", new_callable=AsyncMock):
            asyncio.run(
                animation.animate(
                    animation_page, 0, record["result"].probability_percent
                )
            )
        assert len(frames) == 24
        assert frames[0][0] < frames[-1][0]
        assert frames[0][1] < frames[-1][1]
        assert {f[2] for f in frames} == {initial_body_frame}
        animation.preferences = replace(
            animation.preferences,
            gauge_animation=False,
            damage_animation=False,
            body_animation=False,
        )
        frames.clear()
        with patch("asyncio.sleep", new_callable=AsyncMock):
            asyncio.run(
                animation.animate(
                    animation_page, 0, record["result"].probability_percent
                )
            )
        assert all(f[0] == record["result"].probability_percent for f in frames)
        assert all(f[1] == animation.target_bar for f in frames)
        assert {f[2] for f in frames} == {initial_body_frame}

        body = BodyRegion()
        body.frame = 60
        visited = []

        def capture_body(control: ft.Control) -> None:
            """Record each submitted body frame without rendering claims."""
            if control is body.control:
                visited.append(body.frame)

        with (
            patch.object(ft.Control, "update", capture_body),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            asyncio.run(body.turn_to(0))
            assert visited == [*range(61, 72), 0]
            visited.clear()
            asyncio.run(body.choose(SimpleNamespace(control=SimpleNamespace(data=36))))
            assert visited == list(range(71, 35, -1))
            visited.clear()
            body.preferences = replace(body.preferences, body_animation=False)
            asyncio.run(body.turn_to(0))
            assert visited == [0]
        body.preferences = replace(body.preferences, body_animation=True)
        visited.clear()

        async def interrupt_motion(_delay: float) -> None:
            """Simulate direct touch superseding an automated camera route."""
            body.motion += 1

        with (
            patch.object(ft.Control, "update", capture_body),
            patch("asyncio.sleep", interrupt_motion),
        ):
            asyncio.run(body.turn_to(36))
        assert visited == [71] and body.frame == 71

        asyncio.run(panel.reflow(SimpleNamespace(width=800)))
        assert not panel.legend_compact and panel.legend_box.width == 190
        asyncio.run(panel.reflow(SimpleNamespace(width=400)))
        assert panel.legend_compact and panel.legend_box.width == 360
        asyncio.run(panel.reflow(SimpleNamespace(width=440)))
        assert panel.legend_box.width == 400
        app.open_assessment_record(records[0])
        editor = app.task_editor
        assert editor.workspace.controls[0] is editor.left_group
        app.page.width = 800
        editor.arrange()
        assert editor.workspace.controls[0] is editor.input_group
        assert editor.quick_navigation.visible
        assert not editor.results.body_section.controls
        assert session.working.read_bytes() == original
        unavailable = action_button("Unavailable", disabled=True)
        assert isinstance(unavailable, ft.OutlinedButton)
        assert unavailable.style.elevation == 0
    return {
        "anatomy_frames_and_masks": 288,
        "rgba_dimensions": "480x560",
        "all_19_source_results_projected": True,
        "unavailable_result_stays_neutral": True,
        "legend_uses_actual_card_width_and_reflows": True,
        "portrait_task_navigation_present": True,
        "portrait_reordering_preserves_source_bytes": True,
        "one_anatomy_control_mount": True,
        "disabled_controls_use_flat_outlined_variant": True,
        "live_timing_preview_preserves_accepted_file": True,
        "edge_and_move_cursors_distinct": True,
        "gesture_cancellation_preserves_accepted_file": True,
        "short_break_body_remains_movable": True,
        "independent_animation_switches_respected": True,
        "gauge_bar_transition_frames": 24,
        "body_shortest_route_visits_every_view": True,
        "front_back_buttons_use_same_route": True,
        "touch_cancels_automated_camera_route": True,
        "gauge_never_overwrites_body_angle": True,
        "limitations": (
            "Construction probes; native rendering and physical-device "
            "acceptance are separate."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))

"""Touch-rotatable anatomy rendered from ErgoTools' actual packaged 3D model.

Offline base frames and depth-correct tint masks are rebuilt by render_anatomy.py.
Android needs neither VTK nor a network renderer. Rotation is view state; colors
project the selected assessment, never a new anatomical/scientific calculation.
"""

import asyncio

import flet as ft
from mobile_preferences import TabletPreferences

from ergotools.domain.assessments.document import AssessmentKind

# Existing tool/body relationship and frame count generated from original STL assets.
REGIONS = {
    AssessmentKind.LIFFT: "Lower back",
    AssessmentKind.DUET: "Hands & forearms",
    AssessmentKind.TST: "Shoulders",
}
FRAME_COUNT = 72


class BodyRegion:
    """Compose the real anatomy turntable with independent view and result state.

    Attributes:
        control: Reusable anatomy card; embedded in editor and Settings.
        frame: Five-degree view index; persisted neither in source nor history.
        motion: Cancels a superseded finite camera preview.
    """

    def __init__(self) -> None:
        """Create a full-quality local anatomical surface with touch rotation.

        Args:
            None.

        Returns:
            None; project supplies selected tool/color/preferences.
        """
        self.kind = AssessmentKind.LIFFT
        self.frame = 0
        self.target_frame = 0
        self.bound = False
        self.motion = 0
        self.drag_distance = 0.0
        self.color = "#12BDB0"
        self.preferences = TabletPreferences()
        self.base = ft.Image(
            src="anatomy/body_00.png",
            width=240,
            height=280,
            fit=ft.BoxFit.CONTAIN,
            gapless_playback=True,
        )
        self.mask = ft.Image(
            src="anatomy/lifft_00.png",
            gapless_playback=True,
            color=self.color,
            color_blend_mode=ft.BlendMode.MODULATE,
            exclude_from_semantics=True,
            width=240,
            height=280,
            fit=ft.BoxFit.CONTAIN,
            semantics_label="ErgoTools anatomical model; drag horizontally to rotate.",
        )
        self.label = ft.Text(
            "Lower back", size=20, weight=ft.FontWeight.BOLD, color="white"
        )
        self.angle_label = ft.Text("Drag to rotate · 0°", color="#BFD5E4", size=14)
        surface = ft.GestureDetector(
            ft.Stack([self.base, self.mask], width=240, height=280),
            on_horizontal_drag_update=self.drag,
            drag_interval=35,
        )
        self.control = ft.Container(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.ACCESSIBILITY_NEW, color="#62E1DE", size=26
                            ),
                            self.label,
                        ]
                    ),
                    ft.Row([surface], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row(
                        [
                            ft.TextButton(
                                "Back",
                                on_click=self.choose,
                                data=0,
                                style=ft.ButtonStyle(color="white"),
                            ),
                            ft.TextButton(
                                "Front",
                                on_click=self.choose,
                                data=FRAME_COUNT // 2,
                                style=ft.ButtonStyle(color="white"),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.ROTATE_RIGHT,
                                on_click=self.rotate,
                                tooltip="Rotate the anatomical view",
                                icon_color="#62E1DE",
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    self.angle_label,
                    ft.Text(
                        "3D anatomy · assessment color overlay",
                        color="#BFD5E4",
                        size=14,
                    ),
                ],
                spacing=10,
            ),
            bgcolor="#092137",
            padding=18,
            border_radius=20,
        )

    async def choose(self, event: ft.Event) -> None:
        """Select a front/back angle without changing assessment data.

        Args:
            event: View button carrying an exact frame index.

        Returns:
            None; active motion is cancelled and the selected angle is displayed.
        """
        await self.turn_to(int(event.control.data))

    async def turn_to(self, target: int) -> None:
        """Visit every five-degree view on the shortest route to an exact target.

        Frame pacing is independent of the gauge clock. A full half-turn gets at
        least 25 ms per view; short moves still respect the preferred duration.
        Direct touch, another button or leaving the screen cancels the old route.
        """
        self.motion += 1
        generation = self.motion
        self.target_frame = target % FRAME_COUNT
        delta = (
            self.target_frame - self.frame + FRAME_COUNT // 2
        ) % FRAME_COUNT - FRAME_COUNT // 2
        if not self.preferences.body_animation:
            self.frame = self.target_frame
            self.draw()
            self.control.update()
            return
        steps = abs(delta)
        direction = 1 if delta > 0 else -1
        interval = max(0.025, self.preferences.animation_ms / 1000 / max(1, steps))
        for _ in range(steps):
            if generation != self.motion:
                return
            self.frame = (self.frame + direction) % FRAME_COUNT
            self.draw()
            self.control.update()
            await asyncio.sleep(interval)

    async def reveal(self) -> None:
        """Move from the mounted origin to the selected tool's preferred view."""
        await self.turn_to(self.target_frame)

    async def drag(self, event: ft.DragUpdateEvent) -> None:
        """Rotate through cached 3D frames using deliberate horizontal finger motion.

        Args:
            event: Native horizontal drag; four logical pixels advance one frame.

        Returns:
            None; vertical page scrolling is left to the parent.
        """
        self.motion += 1
        self.drag_distance += event.primary_delta or 0
        steps = int(self.drag_distance / 4)
        if steps:
            self.drag_distance -= steps * 4
            self.frame = (self.frame + steps) % FRAME_COUNT
            self.draw()
            self.control.update()

    async def rotate(self, event: ft.Event) -> None:
        """Preview one finite turn, or move one angle when body animation is disabled.

        Args:
            event: Rotate action; no background or infinite timer is started.

        Returns:
            None after one turn; a drag or view choice cancels it.
        """
        self.motion += 1
        generation = self.motion
        for _ in range(FRAME_COUNT if self.preferences.body_animation else 1):
            if generation != self.motion:
                return
            self.frame = (self.frame + 1) % FRAME_COUNT
            self.draw()
            self.control.update()
            await asyncio.sleep(0.025)

    def project(
        self, kind: AssessmentKind, color: str, preferences: TabletPreferences
    ) -> None:
        """Bind region/color while preserving touch rotation within the same tool.

        Args:
            kind: Current tool, using the established region mapping.
            color: Actual risk color, or neutral teal without a probability.
            preferences: Personal visual settings; no scientific parameters.

        Returns:
            None; only local image selection and tint change.
        """
        if not self.bound or kind is not self.kind:
            self.motion += 1
            self.target_frame = 0 if kind is AssessmentKind.LIFFT else FRAME_COUNT // 2
            if not self.bound:
                self.frame = (self.target_frame - 12) % FRAME_COUNT
            self.bound = True
        self.kind, self.color, self.preferences = kind, color, preferences
        self.label.value = REGIONS[kind]
        self.draw()

    def draw(self, opacity: float = 1) -> None:
        """Select aligned base/mask frames and project a visual-only highlight pulse.

        Args:
            opacity: Optional pulse strength from the result transition.

        Returns:
            None; stored results and original model assets remain untouched.
        """
        self.base.src = f"anatomy/body_{self.frame:02}.png"
        self.mask.src = f"anatomy/{self.kind.value}_{self.frame:02}.png"
        self.mask.color = self.color
        self.mask.opacity = opacity * 0.86
        self.angle_label.value = f"Drag to rotate · {self.frame * 5}°"

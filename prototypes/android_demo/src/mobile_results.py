"""Reusable mobile assessment result surface with animated gauge and damage bar.

Formatting and animation never change stored numerical precision. Risk categories
come from the shared domain thresholds; absent probability stays absent.
"""

import asyncio
import math

import flet as ft
import flet.canvas as cv
from assessment_tools import tool_name
from body_region import BodyRegion
from mobile_preferences import TabletPreferences

from ergotools.domain.assessments.document import assessment_kind
from ergotools.domain.risk import classify_probability

# Shared four-band palette; continuous numbers remain unchanged by display clipping.
BANDS = {
    "low": ("Low risk", "#16B83E"),
    "moderate": ("Moderate risk", "#F3C800"),
    "moderate_high": ("Moderate high risk", "#FF8C16"),
    "high": ("High risk", "#FF3934"),
}


class ResultPanel:
    """Own a stable gauge/result card updated without rebuilding focused input controls.

    Attributes:
        control: Embeddable result card.
        probability: Formatted risk text, distinct from its original floating result.
        canvas: Custom shared-style mobile gauge.
        generation: Cancels an older animation when a newer edit/calculation arrives.
    """

    def __init__(self) -> None:
        """Create uncalculated result widgets with visible scale and risk legend.

        Args:
            None.

        Returns:
            None; caller projects an actual persisted or freshly accepted result.
        """
        self.on_mounted = None
        self.generation = 0
        self.embedded_body = True
        self.preferences = TabletPreferences()
        self.body = BodyRegion()
        self.body_section = ft.ExpansionTile(
            title=ft.Text(
                "3D body region", size=17, weight=ft.FontWeight.W_600, color="#0B3D60"
            ),
            controls=[self.body.control],
        )
        self.angle = 0.0
        self.canvas = cv.Canvas(width=320, height=230)
        self.probability = ft.Text(
            "—",
            size=44,
            weight=ft.FontWeight.BOLD,
            color="#0B3D60",
            text_align=ft.TextAlign.CENTER,
            left=34,
            right=34,
            top=174,
        )
        self.damage = ft.Text("—", size=30, weight=ft.FontWeight.BOLD, color="#0B3D60")
        self.band = ft.Text(
            "Not calculated", size=16, weight=ft.FontWeight.BOLD, color="#53687A"
        )
        self.status = ft.Text("Enter task inputs.", size=15, color="#344F63")
        self.bar = ft.ProgressBar(
            value=0, bar_height=22, color="#078398", bgcolor="#DDE8EF", border_radius=11
        )
        self.title = ft.Text(
            "Assessment result", size=22, weight=ft.FontWeight.BOLD, color="#0B3D60"
        )
        legend = ft.Column(
            [
                ft.Text(
                    "Risk ranges", size=17, weight=ft.FontWeight.BOLD, color="#0B3D60"
                ),
                *[
                    ft.Row(
                        [
                            ft.Container(
                                width=12, height=12, bgcolor=color, border_radius=6
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        label,
                                        size=15,
                                        weight=ft.FontWeight.W_600,
                                        color="#193F56",
                                    ),
                                    ft.Text(interval, size=14, color="#405D70"),
                                ],
                                spacing=2,
                            ),
                        ],
                        spacing=10,
                    )
                    for (label, color), interval in zip(
                        BANDS.values(),
                        ("0-25%", ">25-37.5%", ">37.5-50%", ">50%"),
                        strict=True,
                    )
                ],
            ],
            spacing=14,
        )
        self.legend_box = ft.Container(legend, width=190)
        self.legend_compact = None
        self.legend_width = 0
        gauge = ft.Container(
            ft.Stack([self.canvas, self.probability], width=320, height=230),
            width=320,
            alignment=ft.Alignment.CENTER,
        )
        self.visual = ft.Row(
            [gauge, self.legend_box],
            wrap=True,
            spacing=18,
            run_spacing=12,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        self.legend_below = ft.Container()
        self.control = ft.Container(
            ft.Column(
                [
                    ft.Row(
                        [self.title, self.band],
                        wrap=True,
                        spacing=10,
                        run_spacing=8,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text("Probability of high-risk job", size=15, color="#344F63"),
                    self.visual,
                    ft.Divider(color="#E1EAF0"),
                    ft.Row(
                        [
                            ft.Text(
                                "Cumulative damage",
                                size=17,
                                weight=ft.FontWeight.W_600,
                                color="#0B3D60",
                            ),
                            self.damage,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        wrap=True,
                    ),
                    self.bar,
                    ft.Row(
                        [
                            ft.Text("0", color="#405D70"),
                            ft.Text("1", color="#405D70"),
                            ft.Text("2+", color="#405D70"),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(
                        "0-2 scale · small positive values retain a visible marker.",
                        size=13,
                        color="#405D70",
                    ),
                    ft.Container(
                        self.status, padding=12, bgcolor="#EDF6F8", border_radius=10
                    ),
                    self.legend_below,
                    self.body_section,
                ],
                spacing=14,
            ),
            padding=20,
            bgcolor="white",
            border_radius=20,
            border=ft.Border.all(1, "#E0EAF0"),
            on_size_change=self.reflow,
        )

    async def reflow(self, event: ft.LayoutSizeChangeEvent) -> None:
        """Use available card width, not screen width, to place a readable legend.

        Args:
            event: Actual containing result-card size after orientation/layout changes.

        Returns:
            None; a narrow card uses compact rows, a wide card places ranges beside it.
        """
        compact = event.width < 590
        if compact == self.legend_compact and abs(event.width - self.legend_width) < 2:
            return
        self.legend_width = event.width
        self.legend_compact = compact
        intervals = ("0-25%", ">25-37.5%", ">37.5-50%", ">50%")
        rows = [
            ft.Text("Risk ranges", size=16, weight=ft.FontWeight.W_600, color="#0B3D60")
        ]
        for (label, color), interval in zip(BANDS.values(), intervals, strict=True):
            parts = [ft.Container(width=10, height=10, bgcolor=color, border_radius=5)]
            if compact:
                parts.extend(
                    [
                        ft.Text(label, size=14, color="#294C63", expand=True),
                        ft.Text(interval, size=14, color="#405D70"),
                    ]
                )
            else:
                parts.append(
                    ft.Column(
                        [
                            ft.Text(
                                label,
                                size=15,
                                weight=ft.FontWeight.W_600,
                                color="#294C63",
                            ),
                            ft.Text(interval, size=14, color="#405D70"),
                        ],
                        spacing=2,
                    )
                )
            rows.append(ft.Row(parts, spacing=10))
        if compact:
            self.visual.controls = self.visual.controls[:1]
            self.legend_below.content = self.legend_box
        else:
            self.legend_below.content = None
            if len(self.visual.controls) == 1:
                self.visual.controls.append(self.legend_box)
        self.legend_box.width = max(260, event.width - 40) if compact else 190
        self.legend_box.content = ft.Column(rows, spacing=8 if compact else 14)
        self.control.update()
        if self.on_mounted is not None:
            callback, self.on_mounted = self.on_mounted, None
            await callback()

    def draw(self, risk: float | None) -> None:
        """Draw the gauge scale and an optional needle without implying missing is zero.

        Args:
            risk: Displayed probability percentage, clipped only for needle geometry.

        Returns:
            None; the formatted result remains full-precision independent storage.
        """
        arcs = []
        start = math.pi
        for fraction, color in (
            (0.25, "#16B83E"),
            (0.125, "#F3C800"),
            (0.125, "#FF8C16"),
            (0.5, "#FF3934"),
        ):
            arcs.append(
                cv.Arc(
                    42,
                    57,
                    236,
                    236,
                    start_angle=start,
                    sweep_angle=math.pi * fraction,
                    paint=ft.Paint(
                        color=color, stroke_width=26, style=ft.PaintingStyle.STROKE
                    ),
                )
            )
            start += math.pi * fraction
        if self.preferences.tick_interval:
            for value in range(0, 101, self.preferences.tick_interval):
                angle = math.pi + math.pi * value / 100
                arcs.append(
                    cv.Line(
                        160 + 100 * math.cos(angle),
                        175 + 100 * math.sin(angle),
                        160 + 112 * math.cos(angle),
                        175 + 112 * math.sin(angle),
                        paint=ft.Paint(color="#FFFFFF", stroke_width=2),
                    )
                )
        if self.preferences.range_labels:
            for value in (25, 37.5, 50):
                angle = math.pi + math.pi * value / 100
                arcs.append(
                    cv.Text(
                        160 + 145 * math.cos(angle) - 12,
                        175 + 145 * math.sin(angle) - 10,
                        f"{value:g}",
                        style=ft.TextStyle(
                            size=14, color="#294C63", weight=ft.FontWeight.W_600
                        ),
                    )
                )
        if self.preferences.scale_labels:
            arcs.extend(
                [
                    cv.Text(27, 193, "0", style=ft.TextStyle(size=14, color="#294C63")),
                    cv.Text(
                        268, 193, "100", style=ft.TextStyle(size=14, color="#294C63")
                    ),
                ]
            )
        if risk is not None:
            angle = math.pi + math.pi * max(0, min(100, risk)) / 100
            arcs.append(
                cv.Line(
                    160,
                    175,
                    160 + 99 * math.cos(angle),
                    175 + 99 * math.sin(angle),
                    paint=ft.Paint(color="#244D68", stroke_width=4),
                )
            )
            arcs.append(cv.Circle(160, 175, 6, paint=ft.Paint(color="#244D68")))
        self.canvas.shapes = arcs

    def project(
        self, selected: dict, readiness: dict, *, animate: bool = False
    ) -> None:
        """Project a real source-bound result and explicit partial/invalid readiness.

        Args:
            selected: Native document/source/result projection.
            readiness: Core grid evaluation status and plain-language missing fields.
            animate: Retain current geometry for the following animation callback.

        Returns:
            None; animation is scheduled separately after the widgets are mounted.
        """
        self.title.value = f"{tool_name(selected['source'])} assessment result"
        result = selected["result"]
        risk = result.probability_percent if result else None
        self.probability.value = f"{risk:.1f}%" if risk is not None else "—"
        self.damage.value = f"{result.damage:.5f}" if result else "—"
        label, color = (
            BANDS[classify_probability(risk).value]
            if risk is not None
            else ("Not available", "#687D8B")
        )
        self.band.value = label
        self.band.color = color
        partial = (
            result
            and result.calculation_status
            and result.calculation_status.value == "partial"
        )
        self.status.value = ("Partial result · " if partial else "") + readiness[
            "message"
        ]
        self.status.color = (
            "#A65000"
            if partial or readiness["status"] in ("invalid_input", "calculation_failed")
            else "#0B3D60"
        )
        self.body_section.visible = self.preferences.body_visible and self.embedded_body
        self.body.project(
            assessment_kind(selected["source"]),
            color if risk is not None else "#078398",
            self.preferences,
        )
        self.bar.color = color
        self.target_bar = (
            min(1, max(0.012, result.damage / 2)) if result and result.damage > 0 else 0
        )
        if not animate:
            self.generation += 1
            self.angle = risk or 0
            self.bar.value = self.target_bar
            self.draw(risk)
        elif risk is not None:
            self.draw(self.angle)

    async def animate(self, page: ft.Page, start: float, end: float | None) -> None:
        """Animate current result only, canceling stale frames after a newer edit.

        Args:
            page: Mounted mobile page for frame updates.
            start: Previous displayed needle position.
            end: New probability; None removes the needle.

        Returns:
            None after a short nonblocking animation; stored values never change.
        """
        self.generation += 1
        generation = self.generation
        if end is None:
            self.draw(None)
            self.bar.value = self.target_bar
            self.body.draw()
            page.update()
            return
        start_bar = self.bar.value or 0
        for frame in range(1, 25):
            if generation != self.generation:
                return
            fraction = 1 - (1 - frame / 24) ** 3
            self.angle = (
                start + (end - start) * fraction
                if self.preferences.gauge_animation
                else end
            )
            self.draw(self.angle)
            self.bar.value = (
                start_bar + (self.target_bar - start_bar) * fraction
                if self.preferences.damage_animation
                else self.target_bar
            )
            # Camera movement belongs to BodyRegion's cancellable route, not
            # to the needle easing fraction; neither can snap the other back.
            page.update()
            await asyncio.sleep(self.preferences.animation_ms / 24000)
        self.angle = end

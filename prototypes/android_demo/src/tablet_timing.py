"""Touch shift timeline with real shared block/break commands and project history.

Selection/gesture previews are local. Each completed valid edit is one native project
change; global Undo/Redo and Save remain authoritative. No new timing mathematics,
rotation data or database schema is introduced by this frontend.
"""

from dataclasses import replace
from datetime import time
from typing import TYPE_CHECKING

import flet as ft
from tablet_style import action_button

if TYPE_CHECKING:
    from mobile_ui import TabletApp
    from tablet_organization import OrganizationScreen
import flet.canvas as cv
from mobile_organization import accept_timing, organization_snapshot

from ergotools.application.rotation_segments import (
    move_timing_segment,
    redistribute_timing_segments,
    remove_timing_segment,
    resize_timing_boundary,
    timing_segments,
)
from ergotools.application.rotation_timing import ShiftClock, shift_clock
from ergotools.application.rotation_timing_actions import (
    change_timing_break,
    draw_timing_break,
    separate_work_blocks,
    split_work_block,
)
from ergotools.domain.rotation_timing import (
    MinuteInterval,
    RotationTiming,
    TimedBreak,
    equal_timing,
)


class TimingScreen:
    """Compose timeline, selected interval controls and equally prominent work/breaks.

    Attributes:
        saved: Exact last native timing, or None before first accepted edit.
        selected: Chronological segment index; never a persisted identity.
        mode: Explicit touch operation, independently highlighted in the toolbar.
    """

    def __init__(
        self,
        app: "TabletApp",
        parent: "OrganizationScreen",
        shift_id: str,
        clock: ShiftClock,
    ) -> None:
        """Bind a real recurring shift and retain the organization return target.

        Args:
            app: Tablet shell with shared project history.
            parent: Organization browser to restore on Back.
            shift_id: Exact existing shift owner.
            clock: Validated recurring clock from the shared application service.

        Returns:
            None; merely opening an absent timing does not create one.
        """
        self.app, self.parent, self.shift_id, self.clock = app, parent, shift_id, clock
        self.mode = "Select"
        self.selected = 0
        self.message = ""
        self.pointer = None
        self.gesture_start = None
        self.preview_timing = None
        self.width = min(1100, (app.page.width or 800) - 100)
        self.canvas = cv.Canvas(width=self.width, height=160)

    def refresh(self) -> None:
        """Reload native timing; absent templates use an uncommitted visual default.

        Args:
            None.

        Returns:
            None; default four equal blocks are not stored until an edit is accepted.
        """
        hierarchy, templates = organization_snapshot(self.app.session.working)
        self.clock = shift_clock(hierarchy, self.shift_id)
        self.preview_timing = None
        self.saved = next(
            (t.timing for t in templates if t.shift_id == self.shift_id), None
        )
        self.timing = separate_work_blocks(
            self.saved or equal_timing(self.clock.span_minutes, 4)
        )
        self.segments = timing_segments(self.timing)
        self.selected = min(self.selected, len(self.segments) - 1)

    def bounds(self) -> list[tuple[int, int]]:
        """Project chronological intervals for hit testing and labels.

        Args:
            None.

        Returns:
            Positive half-open shift-relative interval pairs.
        """
        result = []
        cursor = 0
        for segment in self.segments:
            result.append((cursor, cursor + segment.minutes))
            cursor += segment.minutes
        return result

    def draw(self) -> None:
        """Paint a transient drag proposal without changing the accepted timing."""
        timing, segments = self.timing, self.segments
        if self.preview_timing is not None:
            self.timing = self.preview_timing
            self.segments = timing_segments(self.preview_timing)
        try:
            self.draw_segments()
        finally:
            self.timing, self.segments = timing, segments

    def draw_segments(self) -> None:
        """Draw legible work/break segments, selection and exact clock information.

        Args:
            None.

        Returns:
            None; selected borders and the gesture marker carry no stored state.
        """
        shapes = []
        work = 0
        pause = 0
        for i, (segment, (start, end)) in enumerate(
            zip(self.segments, self.bounds(), strict=True)
        ):
            x = 12 + (self.width - 24) * start / self.timing.shift_minutes
            width = (self.width - 24) * (end - start) / self.timing.shift_minutes
            if segment.kind == "work":
                work += 1
                label = f"Block {work}"
                color = "#0B456B"
                text = "white"
            else:
                pause += 1
                label = segment.name or f"Break {pause}"
                color = "#F7D790"
                text = "#503900"
            shapes.append(
                cv.Rect(
                    x,
                    26,
                    max(2, width - 2),
                    78,
                    border_radius=6,
                    paint=ft.Paint(color=color),
                )
            )
            if i == self.selected:
                shapes.append(
                    cv.Rect(
                        x,
                        26,
                        max(2, width - 2),
                        78,
                        border_radius=6,
                        paint=ft.Paint(
                            color="#02B9BA",
                            stroke_width=3,
                            style=ft.PaintingStyle.STROKE,
                        ),
                    )
                )
            if segment.kind == "break" and width <= 85 and width > 16:
                for offset in (-4, 4):
                    shapes.append(
                        cv.Line(
                            x + width / 2 + offset,
                            52,
                            x + width / 2 + offset,
                            77,
                            paint=ft.Paint(color="#755316", stroke_width=2),
                        )
                    )
            if width > 85:
                shapes.extend(
                    [
                        cv.Text(
                            x + 10,
                            42,
                            label,
                            style=ft.TextStyle(
                                size=15, weight=ft.FontWeight.BOLD, color=text
                            ),
                        ),
                        cv.Text(
                            x + 10,
                            68,
                            f"{segment.minutes} min",
                            style=ft.TextStyle(size=14, color=text),
                        ),
                    ]
                )
            shapes.append(
                cv.Line(x, 108, x, 115, paint=ft.Paint(color="#7591A3", stroke_width=1))
            )
            if width > 105:
                shapes.append(
                    cv.Text(
                        x,
                        124,
                        self.clock.label(start),
                        style=ft.TextStyle(size=13, color="#294C63"),
                    )
                )
        shapes.append(
            cv.Text(
                self.width - 55,
                124,
                self.clock.label(self.timing.shift_minutes).split()[0],
                style=ft.TextStyle(size=13, color="#294C63"),
            )
        )
        if self.mode == "Move / resize":
            for _, end in self.bounds()[:-1]:
                x = 12 + (self.width - 24) * end / self.timing.shift_minutes
                shapes.extend(
                    [
                        cv.Line(
                            x,
                            23,
                            x,
                            107,
                            paint=ft.Paint(color="#00A5AF", stroke_width=2),
                        ),
                        cv.Circle(x, 26, 6, paint=ft.Paint(color="#00A5AF")),
                    ]
                )
        if self.pointer is not None:
            x = 12 + (self.width - 24) * self.pointer / self.timing.shift_minutes
            shapes.extend(
                [
                    cv.Line(
                        x, 10, x, 116, paint=ft.Paint(color="#008D9B", stroke_width=2)
                    ),
                    cv.Text(
                        max(0, min(self.width - 100, x - 28)),
                        140,
                        self.clock.label(self.pointer),
                        style=ft.TextStyle(
                            size=14, color="#006F7E", weight=ft.FontWeight.BOLD
                        ),
                    ),
                ]
            )
        self.canvas.shapes = shapes

    def minute(self, x: float) -> int:
        """Snap a touch point to a five-minute position inside this actual shift.

        Args:
            x: Local timeline coordinate, in logical pixels.

        Returns:
            Clamped relative minute suitable for shared command validation.
        """
        return max(
            0,
            min(
                self.timing.shift_minutes,
                round((x - 12) / (self.width - 24) * self.timing.shift_minutes / 5) * 5,
            ),
        )

    async def commit(self, timing: RotationTiming, label: str) -> None:
        """Accept one exact completed edit; failed commands keep the prior native file.

        Args:
            timing: Validated shared-domain proposal.
            label: Plain-language history label.

        Returns:
            None; native failures remain visible on this screen.
        """
        try:
            self.app.session.change(
                label,
                lambda: accept_timing(
                    self.app.session.working, self.shift_id, self.saved, timing
                ),
            )
            self.message = label
            self.app.message.value = ""
            self.render()
        except (ValueError, OSError) as error:
            await self.app.notify(str(error), error=True)

    async def tap(self, event: ft.TapEvent) -> None:
        """Select, split, remove or insert a pause according to the visible tool mode.

        Args:
            event: Local finger position on the actual timeline.

        Returns:
            None; destructive removals require explicit consent.
        """
        minute = self.minute(event.local_position.x)
        self.selected = next(
            (i for i, (a, b) in enumerate(self.bounds()) if a <= minute < b),
            len(self.segments) - 1,
        )
        self.pointer = minute
        try:
            if self.mode == "Split":
                await self.commit(
                    split_work_block(self.timing, minute), "Split work block"
                )
            elif self.mode == "Draw break":
                await self.commit(
                    draw_timing_break(
                        self.timing, minute, min(minute + 15, self.timing.shift_minutes)
                    ),
                    "Add timing break",
                )
            elif self.mode == "Remove":
                await self.remove(None)
            else:
                self.render()
        except ValueError as error:
            await self.app.notify(str(error), error=True)

    def edge_at(self, x: float) -> int | None:
        """Hit-test edges in unsnapped pixels, leaving short segments a move area.

        A fixed broad radius made every point of a short break count as an edge.
        Limit each handle to a fraction of its narrower neighbor and choose the
        closest candidate. Snapping applies to times, never to cursor hit testing.
        """
        bounds = self.bounds()
        candidates = []
        scale = (self.width - 24) / self.timing.shift_minutes
        for index, (start, end) in enumerate(bounds[:-1]):
            neighbor = bounds[index + 1]
            radius = max(
                3, min(10, min(end - start, neighbor[1] - neighbor[0]) * scale * 0.22)
            )
            distance = abs(x - (12 + end * scale))
            if distance <= radius:
                candidates.append((distance, index + 1))
        return min(candidates)[1] if candidates else None

    async def drag_start(self, event: ft.DragDownEvent) -> None:
        """Capture the press before Android touch slop delays drag recognition."""
        self.gesture_start = self.minute(event.local_position.x)
        self.pointer = self.gesture_start
        self.preview_timing = None
        self.origin = self.timing
        self.selected = next(
            (
                i
                for i, (a, b) in enumerate(self.bounds())
                if a <= self.gesture_start < b
            ),
            len(self.segments) - 1,
        )
        self.edge = self.edge_at(event.local_position.x)

    def drag_proposal(self) -> RotationTiming:
        """Build the same pure-core proposal used for live preview and release.

        Coordinates are measured against the press snapshot, so repeated events
        never compound offsets or write intermediate database/history entries.
        """
        if self.mode == "Draw break":
            start, end = sorted((self.gesture_start, self.pointer))
            return draw_timing_break(self.origin, start, end)
        if self.mode == "Move / resize":
            if self.edge:
                return resize_timing_boundary(self.origin, self.edge, self.pointer)
            segment = self.segments[self.selected]
            index = sum(s.kind == segment.kind for s in self.segments[: self.selected])
            start = self.bounds()[self.selected][0] + self.pointer - self.gesture_start
            return move_timing_segment(self.origin, segment.kind, index, start)
        return self.origin

    async def hover(self, event: ft.HoverEvent) -> None:
        """Show edge resize versus body move affordances for mouse/stylus users."""
        near_edge = self.edge_at(event.local_position.x) is not None
        cursor = (
            (ft.MouseCursor.RESIZE_LEFT_RIGHT if near_edge else ft.MouseCursor.GRAB)
            if self.mode == "Move / resize"
            else (
                ft.MouseCursor.PRECISE
                if self.mode in ("Draw break", "Split")
                else ft.MouseCursor.CLICK
            )
        )
        if self.gesture.mouse_cursor != cursor:
            self.gesture.mouse_cursor = cursor
            self.gesture.update()

    async def drag_update(self, event: ft.DragUpdateEvent) -> None:
        """Preview valid segment geometry continuously; no source writes occur."""
        self.pointer = self.minute(event.local_position.x)
        if self.gesture_start is not None:
            try:
                self.preview_timing = self.drag_proposal()
            except ValueError:
                self.preview_timing = None
        if self.mode == "Move / resize":
            self.gesture.mouse_cursor = (
                ft.MouseCursor.RESIZE_LEFT_RIGHT
                if self.edge
                else ft.MouseCursor.GRABBING
            )
            self.gesture.update()
        self.draw()
        self.canvas.update()

    async def drag_cancel(self, event: ft.Event) -> None:
        """Discard an interrupted touch preview without accepting any timing edit."""
        self.preview_timing = None
        self.gesture_start = None
        self.draw()
        self.canvas.update()

    async def drag_end(self, event: ft.DragEndEvent) -> None:
        """Accept one completed valid edit, discarding the transient visual proposal."""
        if self.gesture_start is None or self.pointer is None:
            return
        try:
            proposal = self.drag_proposal()
            self.preview_timing = None
            if proposal != self.origin:
                await self.commit(
                    proposal,
                    "Draw timing break"
                    if self.mode == "Draw break"
                    else "Move / resize timing",
                )
        except ValueError as error:
            await self.app.notify(str(error), error=True)
        finally:
            self.gesture_start = None
            self.preview_timing = None
            self.draw()
            self.canvas.update()

    async def remove(self, event: ft.Event | None) -> None:
        """Confirm removal and let the shared core redistribute the freed interval."""
        segment = self.segments[self.selected]
        index = sum(s.kind == segment.kind for s in self.segments[: self.selected])
        if (
            await self.app.choice(
                "Remove selected interval?",
                "Neighboring work or breaks expand to cover its "
                "time. Undo can restore it.",
                ["Cancel", "Remove"],
            )
            != "Remove"
        ):
            return
        try:
            await self.commit(
                remove_timing_segment(self.timing, segment.kind, index),
                "Remove timing interval",
            )
        except ValueError as error:
            await self.app.notify(str(error), error=True)

    async def redistribute(
        self,
        work_delta: int = 0,
        break_delta: int = 0,
        *,
        equal_work: bool = False,
        equal_breaks: bool = False,
    ) -> None:
        """Confirm count/equality changes while preserving the other duration budget."""
        try:
            count = len(self.timing.breaks) + break_delta
            total = sum(b.interval.end - b.interval.start for b in self.timing.breaks)
            if break_delta > 0:
                total += 15
            proposal = redistribute_timing_segments(
                self.timing,
                work_count=len(self.timing.block_minutes) + work_delta,
                break_count=count,
                equal_work=equal_work or self.timing.equal_blocks,
                equal_breaks=equal_breaks,
                break_minutes=0 if count == 0 else total,
            )
            if (
                await self.app.choice(
                    "Adjust timing?",
                    "Work blocks or breaks may move. Break names "
                    "are retained; equality redistributes their "
                    "existing duration. Undo restores the previous arrangement.",
                    ["Cancel", "Adjust timing"],
                )
                == "Adjust timing"
            ):
                await self.commit(
                    proposal,
                    "Add timing work block"
                    if work_delta > 0
                    else "Add timing break"
                    if break_delta > 0
                    else "Equalize timing layout",
                )
        except ValueError as error:
            await self.app.notify(str(error), error=True)

    def render(self) -> None:
        """Show a responsive timeline, precise selected interval and parallel controls.

        Args:
            None.

        Returns:
            None; drafts without an accepted edit remain absent from the database.
        """
        self.refresh()
        self.draw()

        async def mode(event: ft.Event) -> None:
            """Select a persistent touch tool without changing project data."""
            self.mode = event.control.data
            self.render()

        async def change(event: ft.Event) -> None:
            """Coordinate counts and equality; removal restores time."""
            work_delta, break_delta = event.control.data[:2]
            if work_delta < 0 or break_delta < 0:
                kind = "work" if work_delta < 0 else "break"
                index = sum(s.kind == kind for s in self.segments) - 1
                if (
                    await self.app.choice(
                        "Remove last interval?",
                        "Neighboring intervals will cover its time; Undo restores it.",
                        ["Cancel", "Remove"],
                    )
                    == "Remove"
                ):
                    await self.commit(
                        remove_timing_segment(self.timing, kind, index),
                        "Remove timing interval",
                    )
                return
            await self.redistribute(
                *event.control.data[:2],
                equal_work=event.control.data[2],
                equal_breaks=event.control.data[3],
            )

        async def basis(event: ft.Event) -> None:
            """Change only the stored averaging-basis policy, not working minutes."""
            await self.commit(
                replace(self.timing, subtract_breaks=event.control.value),
                "Change timing basis",
            )

        async def close(event: ft.Event) -> None:
            """Return to the shift cards, retaining accepted project edits."""
            self.app.timing_screen = None
            self.parent.shifts = True
            self.parent.render()

        segment = self.segments[self.selected]
        start, end = self.bounds()[self.selected]
        name = ft.TextField(
            label="Break name (optional)",
            value=segment.name or "",
            visible=segment.kind == "break",
        )

        def clock_field(label: str, value: str) -> ft.TextField:
            """Use Android's 24-hour clock picker rather than unrestricted time text."""
            field = ft.TextField(label=label, value=value, read_only=True, width=200)

            async def choose(event: ft.Event) -> None:
                """Open a native dial/input picker without accepting a project edit."""

                async def accepted(event: ft.Event) -> None:
                    """Keep the selected HH:mm in this interval draft until Apply."""
                    field.value = event.control.value.strftime("%H:%M")
                    field.update()

                self.app.page.show_dialog(
                    ft.TimePicker(
                        value=time.fromisoformat(field.value),
                        hour_format=ft.TimePickerHourFormat.H24,
                        on_change=accepted,
                        help_text=label,
                    )
                )

            field.suffix = ft.IconButton(
                icon=ft.Icons.SCHEDULE, on_click=choose, tooltip="Choose 24-hour time"
            )
            return field

        start_field = clock_field(
            "Start · 24-hour time", self.clock.label(start).split()[0]
        )
        end_field = clock_field("End · 24-hour time", self.clock.label(end).split()[0])

        async def precise(event: ft.Event) -> None:
            """Validate exact clocks using the same overnight-aware shift convention."""
            try:
                first = self.clock.offset(start_field.value.strip())
                last = self.clock.offset(end_field.value.strip(), end=True)
                if segment.kind == "break":
                    index = sum(
                        s.kind == "break" for s in self.segments[: self.selected]
                    )
                    proposal = change_timing_break(
                        self.timing,
                        index,
                        TimedBreak(
                            MinuteInterval(first, last), name.value.strip() or None
                        ),
                    )
                else:
                    proposal = self.timing
                    if first != start:
                        proposal = resize_timing_boundary(
                            proposal, self.selected, first
                        )
                    if last != end:
                        proposal = resize_timing_boundary(
                            proposal, self.selected + 1, last
                        )
                await self.commit(proposal, "Edit timing interval")
            except ValueError as error:
                await self.app.notify(str(error), error=True)

        controls = []
        for title, icon in (
            ("Select", ft.Icons.NEAR_ME_OUTLINED),
            ("Split", ft.Icons.CONTENT_CUT),
            ("Draw break", ft.Icons.PAUSE),
            ("Move / resize", ft.Icons.OPEN_WITH),
            ("Remove", ft.Icons.DELETE_OUTLINE),
        ):
            controls.append(
                action_button(
                    title,
                    icon=icon,
                    data=title,
                    on_click=mode,
                    height=48,
                    bgcolor="#DDF2F4" if self.mode == title else "white",
                    color="#0B3D60",
                )
            )

        def group(title: str, icon: str, kind: str) -> ft.Container:
            """Build matching touch controls for work and breaks, with.

            truthful totals.
            """
            work = kind == "work"
            count = len(self.timing.block_minutes) if work else len(self.timing.breaks)
            minutes = (
                self.timing.productive_minutes
                if work
                else self.timing.shift_minutes - self.timing.productive_minutes
            )
            return self.app.card(
                [
                    ft.Row(
                        [
                            ft.Icon(icon, color="#078398"),
                            self.app.heading(title),
                            ft.Text(
                                f"{count} · {minutes} min", color="#405D70", size=16
                            ),
                        ]
                    ),
                    ft.Row(
                        [
                            action_button(
                                "Add",
                                icon=ft.Icons.ADD,
                                data=(1, 0, False, False)
                                if work
                                else (0, 1, False, False),
                                on_click=change,
                                height=48,
                            ),
                            action_button(
                                "Remove last",
                                icon=ft.Icons.REMOVE,
                                data=(-1, 0, False, False)
                                if work
                                else (0, -1, False, False),
                                on_click=change,
                                height=48,
                                disabled=count <= (1 if work else 0),
                            ),
                            action_button(
                                "Make equal",
                                icon=ft.Icons.BALANCE,
                                data=(0, 0, work, not work),
                                on_click=change,
                                height=48,
                                disabled=count < 2,
                            ),
                        ],
                        wrap=True,
                    ),
                ],
                col={"xs": 12, "lg": 6},
            )

        async def create_template(event: ft.Event) -> None:
            """Accept the displayed default only by explicit user action."""
            await self.commit(self.timing, "Create shift timing")

        async def clear_template(event: ft.Event) -> None:
            """Clear only this reusable template after explicit loss confirmation."""
            if (
                await self.app.choice(
                    "Clear shift timing?",
                    "The work blocks and breaks for this shift will be removed. "
                    "Existing rotation copies stay unchanged; "
                    "Undo restores the template.",
                    ["Cancel", "Clear timing"],
                )
                == "Clear timing"
            ):
                self.app.session.change(
                    "Clear shift timing",
                    lambda: accept_timing(
                        self.app.session.working, self.shift_id, self.saved, None
                    ),
                )
                self.render()

        async def fit_canvas(event: ft.LayoutSizeChangeEvent) -> None:
            """Fit drawing and touch mapping to this timeline card."""
            width = max(260, event.width - 40)
            if abs(width - self.width) > 2:
                self.width = width
                self.canvas.width = width
                self.draw()
                self.canvas.update()

        chips = []
        work_index = 0
        break_index = 0
        for position, item in enumerate(self.segments):
            if item.kind == "work":
                work_index += 1
                label = f"Block {work_index} · {item.minutes} min"
            else:
                break_index += 1
                label = f"Break {break_index} · {item.minutes} min"

            async def select_interval(
                event: ft.Event, position: int = position
            ) -> None:
                """Select even a very short interval with a full-size touch target."""
                self.selected = position
                self.pointer = self.bounds()[position][0]
                self.render()

            chips.append(
                action_button(
                    label,
                    icon=ft.Icons.VIEW_WEEK_OUTLINED
                    if item.kind == "work"
                    else ft.Icons.COFFEE_OUTLINED,
                    data=position,
                    on_click=select_interval,
                    height=48,
                    bgcolor="#DCF4F4"
                    if position == self.selected
                    else "#FFF4D9"
                    if item.kind == "break"
                    else "white",
                    tooltip=item.name or label,
                )
            )
        name.width = float("inf")
        inspector = self.app.card(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.TOUCH_APP_OUTLINED, color="#078398"),
                        ft.Text(
                            "Selected interval",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color="#0B3D60",
                        ),
                    ]
                ),
                ft.Text(
                    segment.name
                    or ("Work block" if segment.kind == "work" else "Break"),
                    size=21,
                    weight=ft.FontWeight.BOLD,
                    color="#0B3D60",
                ),
                ft.Text(
                    f"{self.clock.label(start)} → {self.clock.label(end)} · "
                    f"{segment.minutes} min",
                    size=16,
                    color="#067D8D",
                ),
                ft.Row([start_field, end_field], wrap=True),
                name,
                ft.Row(
                    [
                        self.app.button(
                            "Apply interval", ft.Icons.CHECK, precise, primary=True
                        ),
                        self.app.button(
                            "Remove selected", ft.Icons.DELETE_OUTLINE, self.remove
                        ),
                    ],
                    wrap=True,
                    spacing=8,
                ),
            ],
            col={"xs": 12, "lg": 4},
        )
        self.gesture = ft.GestureDetector(
            self.canvas,
            on_tap_up=self.tap,
            on_horizontal_drag_down=self.drag_start,
            on_horizontal_drag_update=self.drag_update,
            on_horizontal_drag_end=self.drag_end,
            on_horizontal_drag_cancel=self.drag_cancel,
            on_hover=self.hover,
            mouse_cursor=ft.MouseCursor.PRECISE
            if self.mode in ("Draw break", "Split")
            else ft.MouseCursor.GRAB
            if self.mode == "Move / resize"
            else ft.MouseCursor.CLICK,
            drag_interval=16,
        )
        self.timeline_host = self.app.card(
            [
                ft.Row(controls, wrap=True, spacing=8, run_spacing=8),
                self.gesture,
                ft.Row(chips, wrap=True, spacing=8, run_spacing=8),
                ft.Text(
                    "Tap a bar or interval button. Drag in Move / resize mode; "
                    "use Draw break to mark a pause.",
                    size=14,
                    color="#405D70",
                ),
                ft.Text(
                    self.message, size=14, color="#067D8D", visible=bool(self.message)
                ),
            ],
            col={"xs": 12, "lg": 8},
        )
        self.timeline_host.on_size_change = fit_canvas
        break_total = self.timing.shift_minutes - self.timing.productive_minutes
        self.app.show(
            "Blocks & breaks",
            [
                ft.Row(
                    [
                        self.app.heading(self.shift_id),
                        ft.Text(
                            f"{self.clock.label(0)} → "
                            f"{self.clock.label(self.timing.shift_minutes)}",
                            size=18,
                            color="#405D70",
                        ),
                        ft.Container(
                            ft.Text(
                                "Live timing"
                                if self.saved
                                else "Preview · not yet stored",
                                color="#067D8D",
                                size=14,
                                weight=ft.FontWeight.W_600,
                            ),
                            padding=10,
                            bgcolor="#E7F5F7",
                            border_radius=10,
                        ),
                        action_button(
                            "Create this timing",
                            icon=ft.Icons.ADD,
                            on_click=create_template,
                            height=48,
                            visible=self.saved is None,
                        ),
                    ],
                    wrap=True,
                ),
                ft.ResponsiveRow(
                    [self.timeline_host, inspector], spacing=16, run_spacing=16
                ),
                ft.ResponsiveRow(
                    [
                        group("Work blocks", ft.Icons.VIEW_WEEK_OUTLINED, "work"),
                        group("Breaks", ft.Icons.COFFEE_OUTLINED, "break"),
                    ],
                    spacing=16,
                    run_spacing=16,
                ),
                ft.Row(
                    [
                        ft.Switch(
                            label="Exclude breaks from averaging time",
                            value=self.timing.subtract_breaks,
                            on_change=basis,
                        ),
                        ft.Text(
                            f"{self.timing.productive_minutes} min work · "
                            f"{break_total}"
                            " "
                            f"min breaks · {self.timing.averaging_minutes} min basis",
                            color="#405D70",
                        ),
                    ],
                    wrap=True,
                ),
                ft.Row(
                    [
                        self.app.button("Back to shifts", ft.Icons.ARROW_BACK, close),
                        action_button(
                            "Clear timing",
                            icon=ft.Icons.DELETE_SWEEP_OUTLINED,
                            on_click=clear_template,
                            height=48,
                            visible=self.saved is not None,
                        ),
                    ],
                    wrap=True,
                ),
            ],
        )

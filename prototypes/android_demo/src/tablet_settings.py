"""Personal touch display settings with the actual result/body widgets as live previews.

Draft controls never enter the project timeline. Apply atomically stores only personal
JSON; Cancel restores the previous screen and its accepted native assessment data.
"""

import asyncio
from dataclasses import replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mobile_ui import TabletApp

import flet as ft
from assessment_contexts import read_contexts
from assessment_tasks import preview
from assessment_tools import TOOLS
from body_region import FRAME_COUNT
from mobile_preferences import KINDS
from mobile_results import ResultPanel

from ergotools.domain.assessments.document import AssessmentKind


class TabletSettings:
    """Own one temporary settings draft and the screen that opened it.

    Attributes:
        draft: Immutable personal configuration updated by controls.
        result: Reused result widget with actual current source when available.
        origin: Existing controller to restore after Apply/Cancel.
    """

    def __init__(self, app: "TabletApp") -> None:
        """Capture accepted screen state without changing project bytes/history.

        Args:
            app: Mobile composition root, with pending input already flushed.

        Returns:
            None; render explicitly mounts controls.
        """
        self.app = app
        self.draft = app.preferences
        self.origin = (
            app.task_editor
            or app.assessment_browser
            or app.worker_browser
            or app.timing_screen
            or app.organization_screen
        )
        self.result = ResultPanel()
        self.result.body_section.expanded = True
        self.kind = app.selected_tool
        self.selected = None
        if app.session.active:
            records = read_contexts(app.session.working)["records"]
            self.selected = (
                app.task_editor.selected
                if app.task_editor and app.task_editor.selected["result"]
                else next(
                    (
                        r
                        for r in records
                        if r["owner"].kind is self.kind and r["result"]
                    ),
                    None,
                )
            )
        self.task_preview = ft.Column()

    def refresh(self) -> None:
        """Project the draft into real widgets, retaining required-input explanations.

        Args:
            None.

        Returns:
            None; no calculations or native writes are performed.
        """
        self.result.preferences = self.draft
        if self.selected:
            self.result.project(
                self.selected,
                preview(
                    self.selected["document"],
                    self.selected["source"],
                    self.selected["units"],
                ),
            )
            self.result.title.value = (
                f"Preview · {self.selected['worker'].worker_id} · "
                f"{TOOLS[self.kind][0]} result"
            )
        else:
            self.result.title.value = "Illustrative display preview · 40%"
            self.result.probability.value = "40.0%"
            self.result.damage.value = "0.80000"
            self.result.band.value = "Display example only"
            self.result.target_bar = 0.4
            self.result.bar.value = 0.4
            self.result.draw(40)
            self.result.body.project(self.kind, "#FF8C16", self.draft)
        self.result.body_section.visible = self.draft.body_visible
        numeric = [("Repetitions / work day", "100")]
        if self.kind is AssessmentKind.DUET:
            numeric.insert(0, ("OMNI-Res effort rating", "3"))
        else:
            numeric = [("Lever arm (cm)", "30.0"), ("Load (N)", "49.0"), *numeric]
        if self.kind is AssessmentKind.TST:
            numeric.insert(0, ("Force direction", "Handling"))
        self.task_preview.controls = [
            ft.Text(
                "Live layout preview · illustrative task", weight=ft.FontWeight.BOLD
            ),
            ft.Text("Task 1"),
            ft.TextField(
                label="Task name (optional)",
                value="Packing",
                read_only=True,
                visible=self.draft.names_for(self.kind),
            ),
            ft.ResponsiveRow(
                [
                    ft.TextField(
                        label=label,
                        value=value,
                        read_only=True,
                        col={"xs": 12, "sm": 4},
                    )
                    for label, value in numeric
                ]
            ),
            ft.Text(
                "Derived task results appear here after calculation.",
                visible=self.draft.details_for(self.kind),
            ),
            ft.Text(
                "Required inputs stay visible. Hidden names and results are retained.",
                size=14,
            ),
        ]

    def switch(self, title: str, field: str) -> ft.Switch:
        """Bind one personal boolean to draft projection rather than project mutation.

        Args:
            title: Descriptive control label.
            field: Validated boolean preference attribute.

        Returns:
            Touch switch with its own explicit change callback.
        """

        async def changed(event: ft.Event) -> None:
            """Repaint preview after a switch; Apply remains explicit."""
            self.draft = replace(self.draft, **{field: event.control.value})
            self.refresh()
            self.app.page.update()

        return ft.Switch(
            label=title, value=getattr(self.draft, field), on_change=changed
        )

    def render(self) -> None:
        """Show grouped controls and previews without a misleading project Save toolbar.

        Args:
            None.

        Returns:
            None; settings are reachable without an open project.
        """

        async def interval(event: ft.Event) -> None:
            """Accept one supported tick spacing in the draft."""
            self.draft = replace(self.draft, tick_interval=int(event.control.value))
            self.refresh()
            self.app.page.update()

        async def duration(event: ft.Event) -> None:
            """Set bounded visual animation duration without a scientific edit."""
            self.draft = replace(self.draft, animation_ms=int(event.control.value))
            self.refresh()
            self.app.page.update()

        async def tool(event: ft.Event) -> None:
            """Switch per-tool optional visibility controls and preview."""
            self.kind = KINDS[int(event.control.value)]
            self.selected = None
            if self.app.session.active:
                self.selected = next(
                    (
                        r
                        for r in read_contexts(self.app.session.working)["records"]
                        if r["owner"].kind is self.kind and r["result"]
                    ),
                    None,
                )
            self.render()

        async def flag(event: ft.Event) -> None:
            """Keep each tool's optional flags independent and immutable."""
            key = event.control.data
            flags = list(getattr(self.draft, key))
            flags[KINDS.index(self.kind)] = event.control.value
            self.draft = replace(self.draft, **{key: tuple(flags)})
            self.refresh()
            self.app.page.update()

        self.refresh()
        self.result.control.col = {"xs": 12, "lg": 6}
        self.app.show(
            "Tablet settings",
            [
                ft.Text(
                    "Personal display preferences · Apply keeps these settings across "
                    "restarts. Projects are unchanged.",
                    size=16,
                ),
                ft.ResponsiveRow(
                    [
                        self.app.card(
                            [
                                self.app.heading("Gauge and animations"),
                                ft.Dropdown(
                                    label="Gauge tick interval",
                                    value=str(self.draft.tick_interval),
                                    options=[
                                        ft.DropdownOption(
                                            str(v),
                                            "No interval ticks" if not v else f"{v}%",
                                        )
                                        for v in (0, 5, 10, 20)
                                    ],
                                    on_select=interval,
                                ),
                                self.switch("Show risk-range labels", "range_labels"),
                                self.switch(
                                    "Show scale limits (0 / 100)", "scale_labels"
                                ),
                                self.switch("Animate gauge needle", "gauge_animation"),
                                self.switch(
                                    "Animate cumulative-damage bar", "damage_animation"
                                ),
                                self.switch(
                                    "Animate body-region motion", "body_animation"
                                ),
                                ft.Dropdown(
                                    label="Animation duration",
                                    value=str(self.draft.animation_ms),
                                    options=[
                                        ft.DropdownOption(str(v), f"{v} ms")
                                        for v in sorted(
                                            {
                                                100,
                                                240,
                                                500,
                                                1000,
                                                self.draft.animation_ms,
                                            }
                                        )
                                    ],
                                    on_select=duration,
                                ),
                                self.switch(
                                    "Offer body-region illustration", "body_visible"
                                ),
                                self.app.button(
                                    "Preview animations",
                                    ft.Icons.PLAY_ARROW,
                                    self.animate,
                                ),
                            ],
                            col={"xs": 12, "lg": 6},
                        ),
                        self.result.control,
                    ]
                ),
                self.app.card(
                    [
                        self.app.heading("Task display"),
                        ft.Dropdown(
                            label="Tool",
                            value=str(KINDS.index(self.kind)),
                            options=[
                                ft.DropdownOption(
                                    str(i),
                                    TOOLS[k][0],
                                )
                                for i, k in enumerate(KINDS)
                            ],
                            on_select=tool,
                        ),
                        ft.Switch(
                            label="Show optional task names",
                            value=self.draft.names_for(self.kind),
                            data="task_names",
                            on_change=flag,
                        ),
                        ft.Switch(
                            label="Show derived task details",
                            value=self.draft.details_for(self.kind),
                            data="task_details",
                            on_change=flag,
                        ),
                        self.task_preview,
                    ]
                ),
                ft.Row(
                    [
                        self.app.button("Cancel", ft.Icons.CLOSE, self.cancel),
                        self.app.button(
                            "Apply settings", ft.Icons.CHECK, self.apply, primary=True
                        ),
                    ],
                    wrap=True,
                ),
            ],
            project_actions=False,
        )
        self.app.active_result_panel = self.result

    async def animate(self, event: ft.Event) -> None:
        """Run one finite cancellable preview using the selected settings.

        Args:
            event: Preview action; source results stay unchanged.

        Returns:
            None when the visual transition finishes.
        """
        end = self.selected["result"].probability_percent if self.selected else 40
        self.result.bar.value = 0
        await asyncio.gather(
            self.result.animate(self.app.page, 0, end),
            self.result.body.turn_to((self.result.body.frame + 12) % FRAME_COUNT),
        )

    def leave(self) -> None:
        """Cancel any preview and restore the accepted originating screen.

        Args:
            None.

        Returns:
            None; project identity cannot change inside Settings.
        """
        self.result.generation += 1
        self.app.settings_screen = None
        if self.origin:
            from context_browser import AssessmentBrowser
            from task_editor import TaskEditor

            self.app.task_editor = (
                self.origin if isinstance(self.origin, TaskEditor) else None
            )
            self.app.assessment_browser = (
                self.origin if isinstance(self.origin, AssessmentBrowser) else None
            )
            from worker_browser import WorkerBrowser

            self.app.worker_browser = (
                self.origin if isinstance(self.origin, WorkerBrowser) else None
            )
            self.origin.render()
        else:
            self.app.home()

    async def cancel(self, event: ft.Event) -> None:
        """Discard draft only; Android Back uses this same operation."""
        self.leave()

    async def apply(self, event: ft.Event) -> None:
        """Publish preferences first; retain the draft on write error."""
        try:
            self.app.preference_store.save(self.draft)
            self.app.preferences = self.draft
            self.leave()
        except OSError as error:
            await self.app.notify(f"Could not save settings: {error}", error=True)

"""Touch assessment task list/detail editor, sharing project Save/history with workers.

The list offers explicit multi-selection and clipboard TSV input-only interchange.
Completed fields auto-calculate through the core; incomplete/invalid sources remain
editable and never retain a stale prior result. No desktop UI implementation changes.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace
from typing import TYPE_CHECKING
from unicodedata import normalize

import flet as ft
from assessment_tasks import (
    MAX_TASKS,
    blank_task,
    persist_source,
    preview,
    remove_tasks,
    task_form_values,
    task_from_form,
    tasks_from_tsv,
    tasks_to_tsv,
)
from assessment_tools import (
    DIRECTION_LABELS,
    OMNI_LABELS,
    TOOLS,
    input_fields,
    numeric_fields,
    source_units,
    task_summary,
    tool_name,
)
from mobile_results import ResultPanel
from mobile_workers import BODY_INPUT_PATTERN
from touch_alphabet import alphabet

from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    assessment_kind,
    task_has_content,
    task_has_data,
)
from ergotools.domain.assessments.duet import (
    probability_from_damage as duet_probability,
)
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft import probability_from_damage
from ergotools.domain.assessments.tst import probability_from_damage as st_probability
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.risk import classify_probability
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile

if TYPE_CHECKING:
    from mobile_ui import TabletApp


class TaskEditor:
    """Own selected task/checkbox state without storing view selection in source rows.

    Attributes:
        app: Project shell providing Save, history and native workspace.
        selected: Exact source-bound document projection.
        active_id: Stable row identity shown in the input panel.
        checked: Explicit multi-selection for clipboard/removal.
        pending: Temporary field text not yet accepted by native storage.
    """

    def __init__(self, app: TabletApp, selected: dict) -> None:
        """Start editing all rows of the existing worker assessment.

        Args:
            app: Mobile project shell.
            selected: Complete tool source, units and ownership; never truncated.

        Returns:
            None; source is not changed by simply opening the editor.
        """
        self.app, self.selected = app, selected
        self.active_id = (
            selected["source"].tasks[0].task_id if selected["source"].tasks else None
        )
        self.checked = set()
        self.pending = False
        self.values = {}
        self.results = ResultPanel()
        self.task_list = ft.Column(spacing=6)
        self.inputs = ft.Column(spacing=14)
        self.readiness = ft.Text(size=16, color="#0B3D60")
        self.details_expanded = False

    @property
    def draft(self) -> AssessmentDraft:
        """Return the current immutable complete source.

        Args:
            None.

        Returns:
            Current tool draft, including blank unused rows.
        """
        return self.selected["source"]

    def render(self) -> None:
        """Compose responsive task/editor/results cards with a fixed project toolbar.

        Args:
            None.

        Returns:
            None; task list state and explicit checkbox selection stay intact.
        """
        if self.results.legend_compact is None:
            self.results.on_mounted = self.animate_entry
        ids = {t.task_id for t in self.draft.tasks}
        self.checked.intersection_update(ids)
        if self.active_id not in ids:
            self.active_id = self.draft.tasks[0].task_id if self.draft.tasks else None
        worker = self.selected["worker"]
        self.results.control.col = {"xs": 12, "lg": 4}
        self.workspace = ft.ResponsiveRow(
            [
                self.app.card(
                    [
                        self.app.heading("Tasks"),
                        ft.Row(
                            [
                                self.app.button(
                                    "+ Task",
                                    ft.Icons.ADD_CIRCLE_OUTLINE,
                                    self.add,
                                    disabled=len(self.draft.tasks) >= MAX_TASKS,
                                ),
                                self.app.button(
                                    "- Task",
                                    ft.Icons.REMOVE_CIRCLE_OUTLINE,
                                    self.remove,
                                ),
                            ],
                            wrap=True,
                        ),
                        ft.Row(
                            [
                                ft.TextButton("Select all", on_click=self.select_all),
                                ft.TextButton("Select none", on_click=self.select_none),
                            ],
                            wrap=True,
                        ),
                        self.task_list,
                        ft.Row(
                            [
                                self.app.button(
                                    "Copy selected", ft.Icons.COPY, self.copy
                                ),
                                self.app.button(
                                    "Paste tasks…",
                                    ft.Icons.CONTENT_PASTE,
                                    self.paste,
                                ),
                            ],
                            wrap=True,
                        ),
                    ],
                    col={"xs": 12, "lg": 3},
                ),
                self.app.card(
                    [
                        self.inputs,
                        ft.Row(
                            [
                                self.app.button(
                                    "Clear assessment",
                                    ft.Icons.DELETE_SWEEP,
                                    self.clear,
                                ),
                                self.app.button(
                                    "Calculate",
                                    ft.Icons.CALCULATE,
                                    self.calculate,
                                    primary=True,
                                ),
                            ],
                            wrap=True,
                        ),
                    ],
                    col={"xs": 12, "lg": 5},
                ),
                self.results.control,
            ],
            spacing=16,
            run_spacing=16,
        )
        self.results.embedded_body = False
        self.results.body_section.controls = []
        self.body_disclosure = ft.ExpansionTile(
            title=ft.Text("3D anatomy", weight=ft.FontWeight.W_600, color="#0B3D60"),
            leading=ft.Icon(ft.Icons.ACCESSIBILITY_NEW, color="#078398"),
            controls=[self.results.body.control],
            expanded=(self.app.page.width or 1280) >= 1000,
            visible=self.app.preferences.body_visible,
        )
        self.task_group = self.workspace.controls[0]
        self.task_group.col = 12
        self.left_group = ft.Column(
            [self.body_disclosure, self.task_group], spacing=16, col={"xs": 12, "lg": 3}
        )
        self.input_group = self.workspace.controls[1]
        self.arrange()
        self.app.show(
            f"{worker.worker_id} · {worker.first_name or ''} {worker.last_name or ''}",
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(
                                    self.selected["context"], size=16, color="#078398"
                                ),
                                ft.Text(
                                    self.selected["job"],
                                    size=14,
                                    color="#53687A",
                                    visible=self.selected["job"] != "No Job assigned"
                                    or self.selected["workplace"] is not None,
                                ),
                            ],
                            width=min(560, (self.app.page.width or 800) - 40),
                        ),
                        ft.Row(
                            [
                                ft.Image(
                                    src=TOOLS[assessment_kind(self.draft)][2],
                                    width=30,
                                    height=30,
                                ),
                                ft.Text(
                                    TOOLS[assessment_kind(self.draft)][1],
                                    size=18,
                                    weight=ft.FontWeight.W_600,
                                    color="#0B3D60",
                                ),
                            ],
                            wrap=True,
                        ),
                    ],
                    wrap=True,
                    spacing=24,
                ),
                ft.Row(
                    [
                        self.app.tool_choices(assessment_kind(self.draft)),
                        self.app.button(
                            "Assessments",
                            ft.Icons.ACCOUNT_TREE_OUTLINED,
                            self.app.browse_assessments,
                        ),
                        self.app.button(
                            "Copy / Move…",
                            ft.Icons.CONTENT_COPY,
                            self.app.reuse_assessment,
                        ),
                    ],
                    wrap=True,
                ),
                self.workspace,
                ft.Container(
                    self.readiness, padding=14, bgcolor="#E7F5F7", border_radius=8
                ),
                ft.Text(
                    "Inputs calculate when you finish a"
                    " field. Project Save retains all "
                    "accepted task and result changes.",
                    size=15,
                ),
            ],
        )
        self.fill_list()
        self.fill_inputs()
        self.update_results(animate=True)
        self.app.active_result_panel = self.results
        self.app.page.update()

    async def animate_entry(self) -> None:
        """Reveal results after native layout, honoring personal animation switches.

        A short delay lets the first visible frame precede the transition. Leaving
        the editor cancels it through the shell's active-result identity.
        """
        await asyncio.sleep(0.12)
        if self.app.active_result_panel is not self.results:
            return
        result = self.selected["result"]
        await asyncio.gather(
            self.results.animate(
                self.app.page, 0, result.probability_percent if result else None
            ),
            self.results.body.reveal(),
        )

    def arrange(self) -> None:
        """Prioritize input/results on portrait and anatomy/navigation on landscape.

        Args:
            None; current mounted controls retain pending text and selected task IDs.

        Returns:
            None; only placement changes, never field values or native data.
        """
        portrait = (self.app.page.width or 1280) < 1000
        if hasattr(self, "quick_navigation"):
            self.quick_navigation.visible = portrait
        self.workspace.controls = (
            [self.input_group, self.results.control, self.left_group]
            if portrait
            else [self.left_group, self.input_group, self.results.control]
        )

    def fill_list(self) -> None:
        """Refresh task summaries without replacing a focused numeric field.

        Args:
            None.

        Returns:
            None; row numbers are display-only and update after deletion.
        """
        rows = []
        result = self.selected["result"]
        for index, task in enumerate(self.draft.tasks):

            async def checked(event: ft.Event, identity: str = task.task_id) -> None:
                """Change multi-selection without editing assessment data.

                Args:
                    event: Checkbox with selected state.
                    identity: Stable row identity captured from this task.

                Returns:
                    None; selection changes never dirty the project.
                """
                self.checked.add(
                    identity
                ) if event.control.value else self.checked.discard(identity)

            suffix = (
                "Empty task"
                if not task_has_data(task)
                else "Incomplete task"
                if any(getattr(task, key) is None for key in input_fields(self.draft))
                else (task_summary(self.draft, task))
            )
            row_result = (
                result.tasks[index] if result and index < len(result.tasks) else None
            )
            color = "#0B3D60"
            if row_result and row_result.damage is not None and row_result.damage > 0:
                probability = {
                    AssessmentKind.LIFFT: probability_from_damage,
                    AssessmentKind.DUET: duet_probability,
                    AssessmentKind.TST: st_probability,
                }[assessment_kind(self.draft)]
                band = classify_probability(probability(row_result.damage) * 100).value
                color = {
                    "low": "#087B2D",
                    "moderate": "#806100",
                    "moderate_high": "#A74B00",
                    "high": "#C32323",
                }[band]
            rows.append(
                ft.Row(
                    [
                        ft.Checkbox(
                            value=task.task_id in self.checked,
                            tooltip=f"Select task {index + 1}",
                            on_change=checked,
                        ),
                        ft.Container(
                            ft.ListTile(
                                title=ft.Text(
                                    f"{index + 1}. {task.task_name or 'Unnamed task'}"
                                    if self.app.preferences.names_for(
                                        assessment_kind(self.draft)
                                    )
                                    else f"Task {index + 1}",
                                    weight=ft.FontWeight.BOLD,
                                ),
                                subtitle=ft.Text(suffix, color=color),
                                selected=task.task_id == self.active_id,
                                selected_tile_color="#DDF2F4",
                                data=task.task_id,
                                on_click=self.choose,
                                min_height=64,
                            ),
                            expand=True,
                        ),
                    ],
                    spacing=0,
                )
            )
        self.task_list.controls = [
            ft.Text(
                f"{len(self.draft.tasks)} / 100 tasks · "
                "select checkboxes to copy or remove"
            ),
            ft.Container(
                ft.Column(
                    rows or [ft.Text("No tasks. Tap + Task to start.")],
                    scroll=ft.ScrollMode.AUTO,
                ),
                height=min(288, max(85, len(rows) * 72)),
            ),
        ]

    def fill_inputs(self) -> None:
        """Display editable task inputs with current source units and reusable names.

        Args:
            None.

        Returns:
            None; name/number/moment/damage are clearly separate concepts.
        """
        task = next((t for t in self.draft.tasks if t.task_id == self.active_id), None)
        if task is None:
            self.inputs.controls = [ft.Text("Add a task to enter inputs.")]
            return
        index = self.draft.tasks.index(task) + 1
        self.values = task_form_values(task)
        self.original_values = dict(self.values)
        arm, load = (
            ("cm", "N") if source_units(self.draft).value == "metric" else ("in", "lbf")
        )
        self.inputs.controls = [
            self.app.heading(f"Task {index} inputs"),
            ft.TextField(
                visible=self.app.preferences.names_for(assessment_kind(self.draft)),
                label="Task name (optional)",
                value=self.values["task_name"],
                data="task_name",
                on_change=self.changed,
                on_blur=self.finished,
                on_submit=self.finished,
            ),
            self.app.button(
                "Use an existing task name…", ft.Icons.LIST_ALT, self.use_name
            ),
            ft.ResponsiveRow(
                [
                    ft.TextField(
                        label=label,
                        value=self.values[key],
                        data=key,
                        keyboard_type=ft.KeyboardType.NUMBER,
                        input_filter=ft.InputFilter(
                            regex_string=BODY_INPUT_PATTERN, allow=True
                        ),
                        col={"xs": 12, "sm": 4},
                        on_change=self.changed,
                        on_blur=self.finished,
                        on_submit=self.finished,
                    )
                    for key, label in (
                        (
                            key,
                            {
                                "lever_arm": f"Lever arm ({arm})",
                                "load": f"Load ({load})",
                                "repetitions": "Repetitions / day",
                            }[key],
                        )
                        for key in numeric_fields(self.draft)
                    )
                ],
                spacing=12,
                run_spacing=12,
            ),
            ft.Text(
                "OMNI-Res is an effort rating from 0 to 10, not a physical unit."
                if isinstance(self.draft, DuetDraft)
                else (
                    "Load is force, not body weight. "
                    "Optional task names are reusable across the project."
                ),
                size=14,
            ),
            ft.Row(
                [
                    self.app.button(
                        "Previous task",
                        ft.Icons.CHEVRON_LEFT,
                        self.previous,
                        disabled=index == 1,
                    ),
                    self.app.button(
                        "Next task",
                        ft.Icons.CHEVRON_RIGHT,
                        self.next,
                        disabled=index == len(self.draft.tasks),
                    ),
                ],
                wrap=True,
            ),
        ]
        if isinstance(self.draft, (DuetDraft, TstDraft)):
            key = "omni_res_scale" if isinstance(self.draft, DuetDraft) else "direction"
            options = (
                [
                    (str(i), f"{i}: {label}".rstrip(": "))
                    for i, label in enumerate(OMNI_LABELS)
                ]
                if key == "omni_res_scale"
                else [(d.value, label) for d, label in DIRECTION_LABELS]
            )
            self.inputs.controls.insert(
                3,
                ft.Dropdown(
                    label="OMNI-Res effort rating"
                    if key == "omni_res_scale"
                    else "Force direction",
                    value=self.values[key] or None,
                    options=[
                        ft.DropdownOption("", "Not entered"),
                        *[ft.DropdownOption(value, label) for value, label in options],
                    ],
                    data=key,
                    on_select=self.selector_changed,
                    tooltip="Select the effort rating."
                    if key == "omni_res_scale"
                    else (
                        "Direction labels and saved convention "
                        "match the desktop assessment."
                    ),
                ),
            )
        self.inputs.controls[2].visible = self.app.preferences.names_for(
            assessment_kind(self.draft)
        )

        async def choose_task(event: ft.Event) -> None:
            """Choose a stable task from the compact portrait navigator."""
            try:
                self.flush()
                self.active_id = event.control.value
                self.fill_inputs()
                self.fill_list()
                self.update_results()
                self.app.page.update()
            except ValueError as error:
                await self.app.notify(str(error), error=True)

        async def show_anatomy(event: ft.Event) -> None:
            """Open a full-quality touch anatomy sheet without moving the input form."""
            from body_region import BodyRegion

            body = BodyRegion()
            body.project(
                assessment_kind(self.draft),
                self.results.body.color,
                self.app.preferences,
            )

            async def close(event: ft.Event) -> None:
                """Stop preview motion before closing this view-only sheet."""
                body.motion += 1
                self.app.page.pop_dialog()

            async def dismissed(event: ft.Event) -> None:
                """Cancel motion when Android Back dismisses the anatomy sheet."""
                body.motion += 1

            self.app.page.show_dialog(
                ft.AlertDialog(
                    title=self.app.heading("3D anatomy"),
                    content=ft.Container(body.control, width=320),
                    scrollable=True,
                    on_dismiss=dismissed,
                    actions=[self.app.button("Close", ft.Icons.CLOSE, close)],
                )
            )

        self.quick_navigation = ft.Row(
            [
                ft.Dropdown(
                    label="Task",
                    value=self.active_id,
                    width=220,
                    options=[
                        ft.DropdownOption(
                            t.task_id,
                            f"{i + 1} · {t.task_name or 'Unnamed'}"
                            if self.app.preferences.names_for(
                                assessment_kind(self.draft)
                            )
                            else f"Task {i + 1}",
                        )
                        for i, t in enumerate(self.draft.tasks)
                    ],
                    on_select=choose_task,
                ),
                self.app.button(
                    "3D anatomy",
                    ft.Icons.ACCESSIBILITY_NEW,
                    show_anatomy,
                    disabled=not self.app.preferences.body_visible,
                ),
            ],
            wrap=True,
            visible=(self.app.page.width or 1280) < 1000,
        )
        self.inputs.controls.insert(1, self.quick_navigation)

        self.pending = False

    async def selector_changed(self, event: ft.Event) -> None:
        """Accept a discrete rating/direction as one calculated history step.

        Args:
            event: Typed choice represented by its original source code.

        Returns:
            None; numeric fields and source convention remain unchanged.
        """
        await self.changed(event)
        await self.finished(event)

    def update_results(self, *, animate: bool = False) -> None:
        """Update source-bound aggregate/per-task outputs and readiness in place.

        Args:
            animate: Retain geometry for a following short animation.

        Returns:
            None; incomplete and invalid results remain visibly distinct from ready.
        """
        readiness = preview(
            self.selected["document"], self.draft, self.selected["units"]
        )
        if self.selected["result"] is None and readiness["result"] is not None:
            readiness["message"] = (
                "Inputs ready. Press Calculate; no saved calculation exists yet."
            )
        self.readiness.value = readiness["message"]
        self.results.preferences = self.app.preferences
        self.results.project(self.selected, readiness, animate=animate)
        result = self.selected["result"]
        task = next((t for t in self.draft.tasks if t.task_id == self.active_id), None)
        if task and result:
            row = result.tasks[self.draft.tasks.index(task)]
            unit = "N.m" if source_units(self.draft).value == "metric" else "ft.lbf"
            moment = (
                f"Moment: {row.moment:g} {unit} · " if row.moment is not None else ""
            )
            detail = (
                f"{moment}Damage: {row.damage:.5f} · "
                f"Share of total: {row.share_percent:.1f}%"
                if row.damage is not None
                else "No current result for this task."
            )
        else:
            detail = (
                "No current calculated task result. "
                "Complete numeric inputs to calculate."
            )
        metric_controls = [ft.Text(detail, size=15, color="#405D70")]
        if task and result and row.damage is not None:
            pairs = [
                ("Task damage", f"{row.damage:.5f}"),
                ("Contribution", f"{row.share_percent:.1f}%"),
            ]
            if row.moment is not None:
                pairs.insert(0, (f"Moment ({unit})", f"{row.moment:g}"))
            metric_controls = [
                ft.Container(
                    ft.Column(
                        [
                            ft.Text(label, size=12, color="#405D70"),
                            ft.Text(
                                value,
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color="#0B3D60",
                            ),
                        ],
                        spacing=4,
                    ),
                    padding=10,
                    bgcolor="#F1F6F9",
                    border_radius=10,
                )
                for label, value in pairs
            ]
        if hasattr(self, "task_detail") and self.task_detail in self.inputs.controls:
            self.task_detail.controls = metric_controls
        else:
            self.task_detail = ft.Row(metric_controls, wrap=True, spacing=8)
            self.inputs.controls.append(self.task_detail)
        self.task_detail.visible = self.app.preferences.details_for(
            assessment_kind(self.draft)
        )

    def flush(
        self, label: str = "Edit assessment inputs", *, animate: bool = False
    ) -> None:
        """Accept one completed field and automatically refresh the same result source.

        Args:
            label: Shared history label, including names for catalog-changing edits.
            animate: Prepare result geometry for the field-completion animation.

        Returns:
            None; invalid text stays editable without modifying the native project.
        """
        if not self.pending:
            return
        task = next(t for t in self.draft.tasks if t.task_id == self.active_id)
        next_task = task_from_form(task, self.values, self.original_values)
        draft = replace(
            self.draft,
            tasks=tuple(
                next_task if t.task_id == task.task_id else t for t in self.draft.tasks
            ),
        )
        if draft != self.draft:
            self.selected = self.app.session.change(
                label,
                lambda: persist_source(self.app.session.working, self.selected, draft),
            )
        self.pending = False
        self.original_values = dict(self.values)
        self.fill_list()
        self.update_results(animate=animate)
        self.app.update_project_actions()

    async def changed(self, event: ft.Event) -> None:
        """Retain transient input and remove stale result claims until acceptance.

        Args:
            event: Selected input field change.

        Returns:
            None; field completion groups typing into one undo step.
        """
        self.values[event.control.data] = event.control.value or ""
        self.results.generation += 1
        self.pending = True
        self.results.status.value = "Inputs changed · finish the field to recalculate."
        self.results.probability.value = "—"
        self.results.damage.value = "—"
        self.results.draw(None)
        self.results.band.value = "Inputs changed"
        self.results.band.color = "#687D8B"
        self.results.bar.value = 0
        self.results.body.project(
            assessment_kind(self.draft), "#078398", self.app.preferences
        )
        self.readiness.value = "Finish the current field to validate and recalculate."
        if hasattr(self, "task_detail"):
            self.task_detail.controls = [
                ft.Text(
                    "Inputs changed · finish the field to calculate.",
                    size=15,
                    color="#405D70",
                )
            ]
        self.app.save_button.disabled = False
        self.app.save_state.value = "Unsaved task input"
        self.app.page.update()

    async def finished(self, event: ft.Event) -> None:
        """Accept the field, then animate only the latest accepted calculation.

        Args:
            event: Field blur or keyboard submit.

        Returns:
            None; parsing errors remain in the visible form.
        """
        try:
            start = self.results.angle
            self.flush(
                "Edit task name"
                if event.control.data == "task_name"
                else f"Edit {tool_name(self.draft)} · {event.control.data}",
                animate=True,
            )
            result = self.selected["result"]
            await self.results.animate(
                self.app.page, start, result.probability_percent if result else None
            )
        except Exception as error:
            await self.app.notify(f"Review task input: {error}", error=True)

    async def choose(self, event: ft.Event) -> None:
        """Switch one displayed task while preserving the checkbox selection.

        Args:
            event: Task list row with stable identity.

        Returns:
            None; invalid field text prevents silent loss during navigation.
        """
        try:
            self.flush()
            self.active_id = event.control.data
            self.fill_list()
            self.fill_inputs()
            self.update_results()
            self.app.page.update()
        except Exception as error:
            await self.app.notify(str(error), error=True)

    async def add(self, event: ft.Event) -> None:
        """Append one empty task as one project history action, up to 100 rows.

        Args:
            event: Add task button.

        Returns:
            None; existing task identities/data/results remain intact.
        """
        try:
            self.flush()
            if len(self.draft.tasks) >= MAX_TASKS:
                raise ValueError("Maximum 100 tasks reached.")
            task = blank_task(assessment_kind(self.draft))
            draft = replace(self.draft, tasks=(*self.draft.tasks, task))
            self.selected = self.app.session.change(
                "Add task",
                lambda: persist_source(self.app.session.working, self.selected, draft),
            )
            self.active_id = task.task_id
            self.render()
        except Exception as error:
            await self.app.notify(str(error), error=True)

    async def remove(self, event: ft.Event) -> None:
        """Remove checked tasks, or the active task, with content-loss confirmation.

        Args:
            event: Remove task button.

        Returns:
            None; deleting all tasks leaves one blank reusable assessment row.
        """
        try:
            self.flush()
            ids = self.checked or {self.active_id}
            rows = [t for t in self.draft.tasks if t.task_id in ids]
            if not rows:
                return
            if any(task_has_content(t) for t in rows) and (
                await self.app.choice(
                    "Remove selected tasks",
                    f"Remove {len(rows)} selected task(s)? "
                    "This includes their inputs and names. "
                    "Undo can restore them.",
                    ["Cancel", "Remove tasks"],
                )
                != "Remove tasks"
            ):
                return
            draft = remove_tasks(self.draft, ids)
            self.selected = self.app.session.change(
                "Remove tasks",
                lambda: persist_source(self.app.session.working, self.selected, draft),
            )
            self.checked.clear()
            self.render()
        except Exception as error:
            await self.app.notify(str(error), error=True)

    async def clear(self, event: ft.Event) -> None:
        """Clear only this assessment, preserving its task count and ownership.

        Args:
            event: Clear assessment button.

        Returns:
            None; catalog task names remain available for later reuse.
        """
        try:
            self.flush()
            if (
                await self.app.choice(
                    f"Clear {tool_name(self.draft)} assessment",
                    f"Clear inputs and results for {len(self.draft.tasks)} "
                    f"{'task' if len(self.draft.tasks) == 1 else 'tasks'}? "
                    "Other assessments are unchanged.",
                    ["Cancel", "Clear assessment"],
                )
                != "Clear assessment"
            ):
                return
            tasks = tuple(
                replace(
                    t,
                    **{
                        key: (
                            0
                            if key == "omni_res_scale"
                            else DIRECTION_LABELS[0][0]
                            if key == "direction"
                            else None
                        )
                        for key in input_fields(self.draft)
                    },
                    task_name=None,
                    task_definition_id=None,
                )
                for t in self.draft.tasks
            ) or (blank_task(assessment_kind(self.draft)),)
            self.selected = self.app.session.change(
                f"Clear {tool_name(self.draft)}",
                lambda: persist_source(
                    self.app.session.working,
                    self.selected,
                    replace(self.draft, tasks=tasks),
                ),
            )
            self.checked.clear()
            self.render()
        except Exception as error:
            await self.app.notify(str(error), error=True)

    async def calculate(self, event: ft.Event) -> None:
        """Explicitly verify/recalculate the current source using the same auto policy.

        Args:
            event: Calculate button.

        Returns:
            None; calculation does not publish project Save.
        """
        try:
            self.flush()
            self.selected = self.app.session.change(
                f"Calculate {tool_name(self.draft)}",
                lambda: persist_source(
                    self.app.session.working, self.selected, self.draft
                ),
            )
            self.update_results()
            self.app.update_project_actions()
        except Exception as error:
            await self.app.notify(str(error), error=True)

    async def select_all(self, event: ft.Event) -> None:
        """Check all tasks for one batch copy/removal operation.

        Args:
            event: Select all button.

        Returns:
            None; no native data changes.
        """
        self.checked = {t.task_id for t in self.draft.tasks}
        self.fill_list()
        self.app.page.update()

    async def select_none(self, event: ft.Event) -> None:
        """Clear multi-selection while keeping the active editing task.

        Args:
            event: Select none button.

        Returns:
            None.
        """
        self.checked.clear()
        self.fill_list()
        self.app.page.update()

    async def copy(self, event: ft.Event) -> None:
        """Copy checked or active task inputs to Android's actual clipboard as TSV.

        Args:
            event: Copy selected button.

        Returns:
            None; calculated output columns never enter clipboard input data.
        """
        try:
            self.flush()
            ids = self.checked or {self.active_id}
            rows = tuple(t for t in self.draft.tasks if t.task_id in ids)
            await ft.Clipboard().set(tasks_to_tsv(rows, assessment_kind(self.draft)))
            units = (
                "unitless DUET ratings"
                if isinstance(self.draft, DuetDraft)
                else source_units(self.draft).value + " source units"
            )
            await self.app.notify(
                f"Copied {len(rows)} task(s). Clipboard inputs use {units}."
            )
        except Exception as error:
            await self.app.notify(str(error), error=True)

    async def paste(self, event: ft.Event) -> None:
        """Preview/edit TSV input before appending independent task rows in one action.

        Args:
            event: Paste tasks button.

        Returns:
            None; canceled/invalid paste leaves all source/catalog data unchanged.
        """
        try:
            self.flush()
        except Exception as error:
            await self.app.notify(str(error), error=True)
            return
        text = ft.TextField(
            label="Task rows (tab-separated, no header)",
            value=await ft.Clipboard().get() or "",
            multiline=True,
            min_lines=4,
            max_lines=9,
            width=650,
        )
        feedback = ft.Text("", color="#B3261E")

        async def apply(event: ft.Event) -> None:
            """Validate the entire pasted rectangle before a compound native acceptance.

            Args:
                event: Append tasks action.

            Returns:
                None; invalid rows stay in the dialog for correction.
            """
            try:
                rows = tasks_from_tsv(text.value or "", assessment_kind(self.draft))
                current = self.draft.tasks
                if len(current) == 1 and not task_has_content(current[0]):
                    current = ()
                if len(current) + len(rows) > MAX_TASKS:
                    raise ValueError("Pasting would exceed 100 tasks.")
                self.selected = self.app.session.change(
                    "Paste tasks",
                    lambda: persist_source(
                        self.app.session.working,
                        self.selected,
                        replace(self.draft, tasks=(*current, *rows)),
                    ),
                )
                self.active_id = rows[0].task_id
                self.checked = {r.task_id for r in rows}
                self.app.page.pop_dialog()
                self.render()
            except Exception as error:
                feedback.value = str(error)
                self.app.page.update()

        async def cancel(event: ft.Event) -> None:
            """Cancel without accepting source or reusable-name changes.

            Args:
                event: Cancel paste action.

            Returns:
                None.
            """
            self.app.page.pop_dialog()

        self.app.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=self.app.heading("Paste task inputs"),
                content=ft.Column(
                    [
                        ft.Text(
                            (
                                "Units: dimensionless OMNI-Res and repetitions. "
                                if isinstance(self.draft, DuetDraft)
                                else f"Units: {source_units(self.draft).value}. "
                            )
                            + f"Columns: optional task name, "
                            f"{', '.join(input_fields(self.draft))}. "
                            + (
                                "ST direction: 0 Handling Loads, "
                                "1 Downward, 2 Horizontal. "
                                if isinstance(self.draft, TstDraft)
                                else ""
                            )
                            + "Appends rows; a single empty task is replaced."
                        ),
                        text,
                        feedback,
                    ],
                    width=700,
                    height=360,
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=cancel),
                    ft.TextButton("Paste tasks", on_click=apply),
                ],
            )
        )

    async def use_name(self, event: ft.Event) -> None:
        """Offer searchable reusable project names without changing numeric inputs.

        Args:
            event: Existing name button.

        Returns:
            None; name selection is one undoable source/catalog operation.
        """
        try:
            self.flush()
        except Exception as error:
            await self.app.notify(str(error), error=True)
            return
        with AssessmentProjectFile.open(self.app.session.working) as project:
            names = sorted(
                project.load_task_definitions(), key=lambda d: d.name.casefold()
            )
        listing = ft.Column(scroll=ft.ScrollMode.AUTO, height=260)
        initials = ft.Column()
        letter = "All"
        query_value = ""

        async def choose_letter(value: str) -> None:
            """Filter reusable names using the same touch alphabet as worker browsing.

            Args:
                value: Enabled initial or All.

            Returns:
                None; choosing an initial never edits project data.
            """
            nonlocal letter
            letter = value
            filter_names(query_value)
            self.app.page.update()

        async def select(event: ft.Event) -> None:
            """Use a selected definition's literal name for the active task.

            Args:
                event: Name button carrying the catalog name.

            Returns:
                None; task definition is bound by the native acceptance adapter.
            """
            self.app.page.pop_dialog()
            self.values["task_name"] = event.control.data
            self.pending = True
            self.flush("Edit task name")
            self.fill_inputs()
            self.update_results()
            self.app.page.update()

        def filter_names(query: str) -> None:
            """Refresh available name choices without closing the picker.

            Args:
                query: Case-insensitive name substring.

            Returns:
                None.
            """
            offered = [d for d in names if query.casefold() in d.name.casefold()]
            initials.controls = [
                alphabet(
                    {normalize("NFKD", d.name).upper()[0] for d in offered},
                    letter,
                    choose_letter,
                    all_label="All task names",
                    group_label="Task names",
                )
            ]
            listing.controls = [
                ft.TextButton(d.name, data=d.name, on_click=select)
                for d in offered
                if letter == "All"
                or normalize("NFKD", d.name).upper().startswith(letter)
            ] or [ft.Text("No matching task names yet.")]

        async def search(event: ft.Event) -> None:
            """Filter reusable name choices from the current query.

            Args:
                event: Search input change.

            Returns:
                None.
            """
            nonlocal query_value, letter
            query_value = event.control.value or ""
            letter = "All"
            filter_names(query_value)
            self.app.page.update()

        async def close(event: ft.Event) -> None:
            """Close without changing the current task name.

            Args:
                event: Close button.

            Returns:
                None.
            """
            self.app.page.pop_dialog()

        filter_names("")
        self.app.page.show_dialog(
            ft.AlertDialog(
                title=self.app.heading("Reusable task names"),
                content=ft.Column(
                    [
                        ft.TextField(label="Search task names", on_change=search),
                        initials,
                        listing,
                    ],
                    tight=True,
                ),
                actions=[ft.TextButton("Close", on_click=close)],
            )
        )

    async def move(self, step: int) -> None:
        """Navigate the task list without changing checkbox selection.

        Args:
            step: -1 for previous or +1 for next.

        Returns:
            None; incomplete drafts are accepted before navigation.
        """
        try:
            self.flush()
            index = next(
                i for i, t in enumerate(self.draft.tasks) if t.task_id == self.active_id
            )
            self.active_id = self.draft.tasks[
                max(0, min(len(self.draft.tasks) - 1, index + step))
            ].task_id
            self.fill_list()
            self.fill_inputs()
            self.update_results()
            self.app.page.update()
        except Exception as error:
            await self.app.notify(str(error), error=True)

    async def previous(self, event: ft.Event) -> None:
        """Select the previous task.

        Args:
            event: Previous task tap.

        Returns:
            None.
        """
        await self.move(-1)

    async def next(self, event: ft.Event) -> None:
        """Select the next task.

        Args:
            event: Next task tap.

        Returns:
            None.
        """
        await self.move(1)

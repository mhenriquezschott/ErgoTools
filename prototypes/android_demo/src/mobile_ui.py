"""Touch-first M01 project shell, using Android's native document selectors.

Home, worker overview and all three task editors share one project toolbar.
Save publishes the tablet copy; Save As exports complete bytes using SAF. Imported
external documents remain unchanged, a distinction stated beside the controls.
"""

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path

import flet as ft
from assessment_contexts import create_assessment, read_contexts, workplace_label
from assessment_tools import TOOLS
from body_region import FRAME_COUNT
from context_browser import AssessmentBrowser
from mobile_assessment import assessment
from mobile_preferences import PreferenceStore
from project_session import ProjectSession
from tablet_settings import TabletSettings
from tablet_style import action_button
from task_editor import TaskEditor
from worker_browser import WorkerBrowser

from ergotools.domain.assessments.document import AssessmentKind, assessment_kind

# Software palette, independent of risk thresholds in the domain calculators.
NAVY = "#0B3D60"
TEAL = "#078398"
WHITE = "#FFFFFF"
RED = "#B3261E"


class TabletApp:
    """Compose project navigation and one-task continuation without saving implicitly.

    Attributes:
        page: Current Flet surface.
        session: Private workspace and recent saved-project catalog.
        task_editor: Current shared mobile task editor, or None outside assessment.
        worker_browser: Current worker catalog form, or None outside Workers.
    """

    def __init__(self, page: ft.Page, session: ProjectSession) -> None:
        """Bind UI state without altering a restored native project.

        Args:
            page: Active Android page.
            session: Existing private project lifecycle adapter.

        Returns:
            None; home rendering is explicit.
        """
        self.page, self.session = page, session
        self.preference_store = PreferenceStore(session.folder)
        self.preferences = self.preference_store.load()
        self.settings_screen = None
        self.organization_screen = None
        self.timing_screen = None
        self.task_editor = None
        self.assessment_browser = None
        self.last_assessment_browser = None
        self.selected_tool = AssessmentKind.LIFFT
        self.message = ft.Text("", color=NAVY, size=16)
        self.save_button = None
        self.save_state = None
        self.worker_browser = None
        self.scroll_offset = 0
        self.screen = "Project home"
        self.active_result_panel = None
        page.views[0].can_pop = False
        page.views[0].on_confirm_pop = self.back
        page.on_resize = self.resized

    async def resized(self, event: ft.Event) -> None:
        """Keep timeline touch coordinates aligned after tablet orientation changes.

        Args:
            event: Page viewport resize; source inputs remain untouched.

        Returns:
            None; responsive rows handle other cards without rebuilding focused forms.
        """
        if self.task_editor:
            self.task_editor.arrange()
            self.task_editor.workspace.update()
        if self.timing_screen:
            surface = self.timing_screen
            surface.width = min(1100, (self.page.width or 800) - 100)
            surface.canvas.width = surface.width
            surface.draw()
            surface.canvas.update()

    def button(
        self,
        text: str,
        icon: str,
        handler: Callable[[ft.Event], Awaitable[object]],
        *,
        primary: bool = False,
        disabled: bool = False,
    ) -> ft.OutlinedButton:
        """Build a consistent touch target with icon and explanatory text.

        Args:
            text: User-visible action.
            icon: Existing Material icon identifier supplied by Flet.
            handler: Async action callback.
            primary: Teal emphasis for the main action.
            disabled: Whether the action currently lacks a valid project/target.

        Returns:
            A button with a 48-logical-pixel minimum height.
        """
        return action_button(
            text,
            icon=icon,
            on_click=handler,
            height=48,
            disabled=disabled,
            bgcolor=TEAL if primary else None,
            color=None if disabled else WHITE if primary else NAVY,
            style=ft.ButtonStyle(
                elevation=0,
                shape=ft.RoundedRectangleBorder(radius=12),
                icon_color=WHITE if primary else None,
            ),
        )

    def card(self, controls: list, *, col: int | dict[str, int] = 12) -> ft.Container:
        """Group related content in a responsive white surface.

        Args:
            controls: Ordered controls in the card.
            col: Column span or responsive breakpoint-to-span mapping.

        Returns:
            Padded card, never a fixed-height content clip.
        """
        return ft.Container(
            ft.Column(controls, spacing=16),
            padding=20,
            width=float("inf"),
            bgcolor=WHITE,
            border_radius=14,
            col=col,
        )

    def heading(self, text: str) -> ft.Text:
        """Format a navy heading without shrinking body text.

        Args:
            text: Section title.

        Returns:
            Consistent bold heading.
        """
        return ft.Text(text, size=23, weight=ft.FontWeight.BOLD, color=NAVY)

    def show(self, title: str, controls: list, *, project_actions: bool = True) -> None:
        """Render a scrollable screen with project-level save and navigation.

        Args:
            title: Current screen title.
            controls: Screen-specific cards, rows and instructions.
            project_actions: Hide project mutations while a settings draft is open.

        Returns:
            None; native data is read only by the explicit controller operations.
        """
        if self.active_result_panel:
            self.active_result_panel.generation += 1
            self.active_result_panel.body.motion += 1
            self.active_result_panel = None
        self.screen = title
        active = self.session.active
        dirty = bool(active and active["dirty"]) or bool(
            self.task_editor and self.task_editor.pending
        )
        self.save_state = ft.Text(
            "Unsaved changes"
            if dirty
            else "Saved on tablet"
            if active
            else "No project",
            color="#FFDE8A" if dirty else "#BCD5E5",
            size=14,
        )
        self.save_button = self.button(
            "Save", ft.Icons.SAVE_OUTLINED, self.save, disabled=not dirty
        )
        history = self.session.history
        self.undo_button = self.button(
            "Undo",
            ft.Icons.UNDO,
            self.undo,
            disabled=not history or history.undo_label_key is None,
        )
        self.redo_button = self.button(
            "Redo",
            ft.Icons.REDO,
            self.redo,
            disabled=not history or history.redo_label_key is None,
        )
        toolbar = ft.Row(
            [
                self.undo_button,
                self.redo_button,
                self.save_button,
                ft.PopupMenuButton(
                    icon=ft.Icons.MORE_VERT,
                    tooltip="Project actions",
                    items=[
                        ft.PopupMenuItem(
                            content=ft.Text("Open project…"),
                            icon=ft.Icons.FOLDER_OPEN,
                            on_click=self.open_file,
                        ),
                        ft.PopupMenuItem(
                            content=ft.Text("Create project"),
                            icon=ft.Icons.NOTE_ADD,
                            on_click=self.new_dialog,
                        ),
                        ft.PopupMenuItem(
                            content=ft.Text("Save As…"),
                            icon=ft.Icons.SAVE_AS,
                            on_click=self.save_as,
                        ),
                    ],
                ),
                self.button("Settings", ft.Icons.SETTINGS_OUTLINED, self.settings),
            ],
            wrap=True,
            spacing=8,
            run_spacing=8,
            visible=project_actions,
        )
        header = ft.Container(
            ft.Row(
                [
                    ft.Image(src="icon.png", width=34, height=34),
                    ft.Text(
                        "ErgoTools", size=21, weight=ft.FontWeight.BOLD, color="white"
                    ),
                    ft.Text(
                        active["name"] if active else "Worker assessments",
                        size=14,
                        color="#D5E7F2",
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        expand=True,
                        tooltip=active["name"] if active else None,
                    ),
                    self.save_state,
                    ft.IconButton(
                        icon=ft.Icons.HOME_OUTLINED,
                        icon_color="white",
                        tooltip="Workspace",
                        on_click=self.go_home,
                        visible=title != "Project home",
                    ),
                ],
                spacing=12,
            ),
            padding=ft.Padding(20, 8, 20, 8),
            bgcolor=NAVY,
        )
        self.message.visible = bool(self.message.value)
        self.scroller = ft.Column(
            [self.message, *controls],
            spacing=18,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            on_scroll=self.record_scroll,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        self.page.controls.clear()
        self.page.add(
            ft.SafeArea(
                ft.Column(
                    [
                        header,
                        ft.Container(
                            ft.Row(
                                [
                                    self.heading(
                                        "Workspace"
                                        if title == "Project home"
                                        else title
                                    ),
                                    toolbar,
                                ],
                                wrap=True,
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                run_spacing=10,
                            ),
                            padding=ft.Padding(20, 8, 20, 8),
                        ),
                        ft.Container(
                            self.scroller,
                            padding=ft.Padding(20, 8, 20, 20),
                            expand=True,
                        ),
                    ],
                    spacing=0,
                    expand=True,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
                expand=True,
            )
        )

    async def notify(self, text: str, *, error: bool = False) -> None:
        """Display actionable feedback in the persistent screen message area.

        Args:
            text: Outcome, cancellation or error explanation.
            error: Use error color for a failed operation.

        Returns:
            None; does not replace the current page or fields.
        """
        self.message.value, self.message.color = text, RED if error else NAVY
        self.message.visible = True
        if error:
            self.page.show_dialog(
                ft.SnackBar(ft.Text(text, color=WHITE), bgcolor=RED, duration=6000)
            )
        self.page.update()

    def home(self) -> None:
        """Show project overview, explicit sample entry and saved recent projects.

        Args:
            None.

        Returns:
            None; first launch stays at home without creating fake user data.
        """
        from tablet_home import home_content

        self.worker_browser = None
        self.task_editor = None
        self.assessment_browser = None
        self.organization_screen = None
        self.timing_screen = None
        self.message.value = ""
        self.show("Project home", home_content(self))

    async def choice(self, title: str, text: str, choices: list[str]) -> str:
        """Await an explicit modal decision; dismissal never authorizes data loss.

        Args:
            title: Decision heading.
            text: Consequences in plain language.
            choices: Named actions, including a safe cancel when appropriate.

        Returns:
            Exact chosen label; barrier and back dismissal are disabled.
        """
        answer = asyncio.get_running_loop().create_future()

        async def decide(event: ft.Event) -> None:
            """Resolve one modal choice and remove its dialog.

            Args:
                event: Action button, whose data is the selected label.

            Returns:
                None; future resolves once.
            """
            self.page.pop_dialog()
            if not answer.done():
                answer.set_result(event.control.data)

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=self.heading(title),
                content=ft.Text(text, size=17),
                actions=[ft.TextButton(c, data=c, on_click=decide) for c in choices],
            )
        )
        return await answer

    async def guard(self) -> bool:
        """Protect a switch/close with Save, Discard or Cancel.

        Args:
            None.

        Returns:
            True only when navigation may proceed without silent edit loss.
        """
        if self.worker_browser and not await self.worker_browser.leave():
            return False
        if not (self.task_editor and self.task_editor.pending) and not (
            self.session.active and self.session.active["dirty"]
        ):
            return True
        decision = await self.choice(
            "Unsaved project changes",
            "Save changes on this tablet before leaving this "
            "project? Discard restores the last saved "
            "version. Cancel keeps editing.",
            ["Cancel", "Discard", "Save"],
        )
        if decision == "Cancel":
            return False
        if decision == "Save":
            return await self.save(None)
        self.session.discard()
        if self.task_editor:
            self.task_editor.pending = False
        return True

    def flush(self) -> None:
        """Accept pending mobile form fields into the private project timeline.

        Args:
            None.

        Returns:
            None; invalid text stays editable and cannot silently replace saved data.
        """
        if self.worker_browser:
            self.worker_browser.flush()
        if self.task_editor:
            self.task_editor.flush()

    async def save(self, event: ft.Event | None) -> bool:
        """Publish accepted edits to the managed tablet project, not an external URI.

        Args:
            event: Project Save gesture, or None from unsaved-change protection.

        Returns:
            Whether save succeeded; validation/I/O errors remain visible.
        """
        try:
            self.flush()
            self.session.save()
            self.save_button.disabled = True
            self.save_state.value, self.save_state.color = "Saved on this tablet", WHITE
            self.update_project_actions()
            await self.notify(
                "Project saved on this tablet. Use Save As… for an external file."
            )
            return True
        except Exception as error:
            await self.notify(f"Could not save: {error}", error=True)
            return False

    async def save_as(self, event: ft.Event | None) -> None:
        """Export complete native bytes through the Android system save dialog.

        Args:
            event: Save As gesture.

        Returns:
            None; cancellation leaves unsaved status and active identity unchanged.
        """
        try:
            self.flush()
            destination = await ft.FilePicker().save_file(
                file_name=self.session.active["name"],
                src_bytes=self.session.working.read_bytes(),
            )
            if not destination:
                await self.notify("Save As cancelled. No saved copy was changed.")
                return
            name = Path(destination).name
            if not name.lower().endswith(".ergprj"):
                name = self.session.active["name"]
            self.session.save(name=name, new_copy=True)
            self.home()
            await self.notify(
                "Project file saved using Android file picker. "
                "This tablet copy is also available in Recent projects."
            )
        except Exception as error:
            await self.notify(f"Could not export project: {error}", error=True)

    async def open_file(self, event: ft.Event | None) -> None:
        """Read picker bytes and validate before replacing the active workspace.

        Args:
            event: Open gesture.

        Returns:
            None; canceled/invalid/unsupported files never replace the current project.
        """
        if not await self.guard():
            return
        try:
            files = await ft.FilePicker().pick_files(
                with_data=True, allow_multiple=False
            )
            if not files:
                await self.notify("Open cancelled.")
                return
            selected = files[0]
            if not selected.name.lower().endswith(".ergprj"):
                raise ValueError("Choose a native .ergprj project file.")
            data = selected.bytes or (
                Path(selected.path).read_bytes() if selected.path else None
            )
            if not data:
                raise ValueError("The selected file is empty or could not be read.")
            self.session.activate(data, selected.name, f"Imported from {selected.name}")
            self.home()
            await self.notify(
                "Project opened as a tablet copy. Save to keep it in Recent projects."
                if self.session.active["dirty"]
                else "Project opened. Its matching saved tablet copy was restored."
            )
        except Exception as error:
            await self.notify(f"Could not open project: {error}", error=True)

    async def new_dialog(self, event: ft.Event | None) -> None:
        """Collect project name and measurement system before creating an empty file.

        Args:
            event: Create-project gesture.

        Returns:
            None; cancel does not create a project.
        """
        if not await self.guard():
            return
        name = ft.TextField(label="Project name", autofocus=True, width=440)
        units = ft.Dropdown(
            label="Measurement system",
            value="metric",
            options=[
                ft.DropdownOption("metric", "Metric · cm / N"),
                ft.DropdownOption("imperial", "Imperial · in / lbf"),
            ],
        )
        error_text = ft.Text("", color=RED)

        async def create(event: ft.Event) -> None:
            """Validate form and activate an unsaved empty native project.

            Args:
                event: Create button tap.

            Returns:
                None; invalid fields remain in the dialog.
            """
            try:
                self.session.create(name.value or "", units.value)
                self.page.pop_dialog()
                self.home()
            except Exception as error:
                error_text.value = str(error)
                self.page.update()

        async def cancel(event: ft.Event) -> None:
            """Dismiss without changing the current workspace.

            Args:
                event: Cancel tap.

            Returns:
                None.
            """
            self.page.pop_dialog()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=self.heading("Create project"),
                content=ft.Column(
                    [
                        name,
                        units,
                        ft.Text(
                            "Starts empty. The project is not saved until you"
                            " press Save."
                        ),
                        error_text,
                    ],
                    tight=True,
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=cancel),
                    ft.TextButton("Create", on_click=create),
                ],
            )
        )

    async def organization(self, event: ft.Event | None) -> None:
        """Open organization management after accepting current valid inputs.

        Args:
            event: Organization navigation action.

        Returns:
            None; subsequent accepted edits use project history and Save.
        """
        from tablet_organization import OrganizationScreen

        if self.worker_browser and not await self.worker_browser.leave():
            return
        try:
            self.flush()
            self.task_editor = self.worker_browser = self.assessment_browser = None
            self.organization_screen = OrganizationScreen(self)
            self.organization_screen.render()
        except Exception as error:
            await self.notify(f"Could not open Organization: {error}", error=True)

    async def settings(self, event: ft.Event | None) -> None:
        """Open personal settings after accepting inputs; projects cannot change there.

        Args:
            event: Settings action from any screen.

        Returns:
            None; invalid pending inputs keep their editor visible.
        """
        try:
            if self.worker_browser and not await self.worker_browser.leave():
                return
            self.flush()
            if self.task_editor:
                self.task_editor.results.generation += 1
            self.settings_screen = TabletSettings(self)
            self.task_editor = self.worker_browser = self.assessment_browser = None
            self.settings_screen.render()
        except Exception as error:
            await self.notify(f"Could not open Settings: {error}", error=True)

    async def complete_demo(self, event: ft.Event | None) -> None:
        """Generate a fresh owned demo only after protecting the current project.

        Args:
            event: Explicit complete-demo action.

        Returns:
            None; generation failures preserve the current project and clean temp data.
        """
        from tempfile import TemporaryDirectory

        from demo_project import build_demo

        if not await self.guard():
            return
        try:
            with TemporaryDirectory(dir=self.session.folder) as folder:
                path = Path(folder) / "complete_demo.ergprj"
                build_demo(path)
                self.session.activate(
                    path.read_bytes(),
                    "Tablet worker-assessment demo.ergprj",
                    "Fictional complete demo",
                )
            self.home()
        except Exception as error:
            await self.notify(f"Could not prepare demo: {error}", error=True)

    async def sample(self, event: ft.Event | None) -> None:
        """Create an explicitly requested fictional one-worker example.

        Args:
            event: Explore sample gesture.

        Returns:
            None; example remains unsaved until the project Save action.
        """
        if await self.guard():
            self.session.create("Tablet assessment sample", sample=True)
            self.home()

    async def close_project(self, event: ft.Event | None) -> None:
        """Close the project after protecting unsaved changes.

        Args:
            event: Close-project tap.

        Returns:
            None; saved recent entries remain available.
        """
        if await self.guard():
            self.session.state["active"] = None
            self.session.persist()
            self.session.reset_history()
            self.home()

    async def go_home(self, event: ft.Event | None) -> None:
        """Return home within the same project, retaining accepted draft changes.

        Args:
            event: Home gesture.

        Returns:
            None; invalid text stays in the editor with an error instead of vanishing.
        """
        try:
            if self.settings_screen:
                self.settings_screen.result.generation += 1
                self.settings_screen = None
            if self.worker_browser and not await self.worker_browser.leave():
                return
            self.flush()
            self.home()
        except Exception as error:
            await self.notify(f"Review the inputs: {error}", error=True)

    async def workers(self, event: ft.Event | None) -> None:
        """Open the touch worker browser sharing project Save and history.

        Args:
            event: Workers gesture.

        Returns:
            None; native worker editing is delegated to its mobile adapter.
        """
        self.task_editor = None
        self.assessment_browser = None
        self.worker_browser = WorkerBrowser(self)
        self.worker_browser.render()

    def tool_choices(self, selected: AssessmentKind, *, home: bool = False) -> ft.Row:
        """Create consistent branded touch choices without creating assessments on Home.

        Args:
            selected: Highlighted tool, independent of scientific source units.
            home: Choose a tool only; the explicit Open action then opens/creates it.

        Returns:
            Wrapping tool row with copied software icons and accessible labels.
        """

        async def choose(event: ft.Event) -> None:
            """Flush current inputs before selecting another tool without losing edits.

            Args:
                event: Tool button carrying its stable model key.

            Returns:
                None; cancellation leaves the current editor/tool selected.
            """
            try:
                self.flush()
                previous = self.selected_tool
                self.selected_tool = AssessmentKind(event.control.data)
                if home:
                    self.home()
                else:
                    await self.continue_assessment(None)
                    if self.task_editor:
                        self.selected_tool = assessment_kind(self.task_editor.draft)
                    else:
                        self.selected_tool = previous
            except Exception as error:
                await self.notify(str(error), error=True)

        return ft.Row(
            [
                action_button(
                    ft.Row(
                        [
                            ft.Image(src=icon, width=30, height=30),
                            ft.Text(name, size=16, weight=ft.FontWeight.BOLD),
                        ],
                        tight=True,
                    ),
                    data=kind.value,
                    tooltip=title,
                    on_click=choose,
                    height=50,
                    bgcolor="#DDF2F4" if kind is selected else "white",
                    color=NAVY,
                )
                for kind, (name, title, icon) in TOOLS.items()
            ],
            wrap=True,
            spacing=10,
        )

    async def continue_assessment(self, event: ft.Event | None) -> None:
        """Open existing worker tool data or explicitly create its standalone source.

        Args:
            event: Home assessment gesture.

        Returns:
            None; exactly one standalone worker/tool source is allowed by storage.
        """
        try:
            worker_id = self.session.active.get("selected_worker")
            if not worker_id:
                from mobile_workers import load_workers

                workers, _ = load_workers(self.session.working)
                if not workers:
                    await self.notify("Add a worker before starting an assessment.")
                    return
                worker_id = workers[0].worker_id
                self.session.active["selected_worker"] = worker_id
                self.session.persist()
            workplace = None
            previous = self.task_editor.selected if self.task_editor else None
            if previous and previous["worker"].worker_id == worker_id:
                workplace = previous["workplace"]
                selected = next(
                    (
                        r
                        for r in read_contexts(self.session.working)["records"]
                        if r["worker"].worker_id == worker_id
                        and r["owner"].kind is self.selected_tool
                        and r["owner"].assignment_id == previous["owner"].assignment_id
                    ),
                    None,
                )
                if selected is None and not previous["active"]:
                    await self.notify(
                        "No assessment for this tool in the closed assignment. "
                        "Choose another saved context in Assessments."
                    )
                    return
            else:
                selected = assessment(
                    self.session.working, worker_id, kind=self.selected_tool
                )
            if selected is None:
                if (
                    await self.choice(
                        f"Start {TOOLS[self.selected_tool][0]} assessment",
                        f"Create {TOOLS[self.selected_tool][0]} for {worker_id} "
                        f"at {workplace_label(workplace)}, with one empty task?",
                        ["Cancel", "Start assessment"],
                    )
                    != "Start assessment"
                ):
                    return
                identity = self.session.change(
                    "Add assessment",
                    lambda: create_assessment(
                        self.session.working, worker_id, self.selected_tool, workplace
                    ),
                )
                selected = assessment(
                    self.session.working, worker_id, identity, self.selected_tool
                )
            self.open_assessment_record(selected)
        except Exception as error:
            await self.notify(f"Could not open assessment: {error}", error=True)

    def open_assessment_record(self, selected: dict) -> None:
        """Open one exact saved context without confusing it with a calculation filter.

        Args:
            selected: Complete source/owner/result projection from the context adapter.

        Returns:
            None; selection changes only private worker view state, not native data.
        """
        self.session.active["selected_worker"] = selected["worker"].worker_id
        self.session.persist()
        self.selected_tool = assessment_kind(selected["source"])
        self.worker_browser = None
        if self.assessment_browser:
            self.last_assessment_browser = self.assessment_browser
        self.assessment_browser = None
        previous_body = self.task_editor.results.body if self.task_editor else None
        self.task_editor = TaskEditor(self, selected)
        if previous_body is not None:
            body = self.task_editor.results.body
            body.frame, body.kind = previous_body.frame, previous_body.kind
            body.bound = True
            body.target_frame = (
                0 if self.selected_tool is AssessmentKind.LIFFT else FRAME_COUNT // 2
            )
        self.task_editor.render()

    async def browse_assessments(self, event: ft.Event | None) -> None:
        """Open the relevant-only worker/tool hierarchy after accepting pending input.

        Args:
            event: Home or task-editor Assessments action.

        Returns:
            None; invalid text prevents silent loss during navigation.
        """
        try:
            if self.worker_browser and not await self.worker_browser.leave():
                return
            self.flush()
            self.task_editor = None
            self.worker_browser = None
            previous = self.last_assessment_browser
            self.assessment_browser = (
                previous
                if previous
                and previous.catalog_id == self.session.active.get("id")
                and previous.worker_id == self.session.active.get("selected_worker")
                and previous.kind is self.selected_tool
                else AssessmentBrowser(self)
            )
            self.last_assessment_browser = self.assessment_browser
            self.assessment_browser.render()
        except Exception as error:
            await self.notify(str(error), error=True)

    async def reuse_assessment(self, event: ft.Event) -> None:
        """Reuse current inputs/results through the shared exact destination picker.

        Args:
            event: Task editor Copy/Move action.

        Returns:
            None; source stays unchanged until an explicit successful transfer.
        """
        try:
            await event.control.focus()
            self.flush()
            await AssessmentBrowser(self).transfer(self.task_editor.selected)
        except Exception as error:
            await self.notify(str(error), error=True)

    async def back(self, event: ft.Event) -> None:
        """Route Android Back home first, then protect project edits before exit.

        Args:
            event: Native root-view pop confirmation.

        Returns:
            None; denied saves and Cancel keep the app open.
        """
        if self.screen != "Project home":
            await event.control.confirm_pop(False)
            if self.settings_screen:
                self.settings_screen.leave()
            elif self.timing_screen:
                parent = self.timing_screen.parent
                self.timing_screen = None
                parent.shifts = True
                parent.render()
            else:
                await self.go_home(None)
        else:
            await event.control.confirm_pop(await self.guard())

    def update_project_actions(self) -> None:
        """Synchronize Save/Undo/Redo without replacing focused fields or filters.

        Args:
            None.

        Returns:
            None; only project-level action state is updated.
        """
        history = self.session.history
        self.save_button.disabled = not (
            self.session.active and self.session.active["dirty"]
        )
        self.save_state.value = (
            "Unsaved changes"
            if not self.save_button.disabled
            else "Saved on this tablet"
        )
        self.undo_button.disabled = not history or history.undo_label_key is None
        self.redo_button.disabled = not history or history.redo_label_key is None
        self.undo_button.tooltip = (
            f"Undo: {history.undo_label_key}"
            if history and history.undo_label_key
            else "No earlier changes"
        )
        self.redo_button.tooltip = (
            f"Redo: {history.redo_label_key}"
            if history and history.redo_label_key
            else "No changes to redo"
        )
        self.page.update()

    async def replay(self, *, redo: bool) -> None:
        """Replay one shared change with confirmation when workers are removed/restored.

        Args:
            redo: Forward replay instead of Undo.

        Returns:
            None; canceled/rejected operations retain the project and form.
        """
        try:
            if self.worker_browser and not await self.worker_browser.leave():
                return
            self.flush()
            history = self.session.history
            label = history.redo_label_key if redo else history.undo_label_key
            if not label:
                return
            if label.startswith(
                (
                    "Add organization",
                    "Delete organization",
                    "Remove timing",
                    "Add timing",
                    "Clear shift timing",
                    "Draw timing",
                    "Create shift timing",
                    "Add worker",
                    "Add assessment",
                    "Delete assessment",
                    "Replace assessment",
                    "Copy assessment",
                    "Move assessment",
                    "Delete worker",
                    "Create LiFFT",
                    "Create DUET",
                    "Create ST",
                    "Remove tasks",
                    "Paste tasks",
                    "Clear LiFFT",
                    "Clear DUET",
                    "Clear ST",
                    "Edit task name",
                )
            ):
                decision = await self.choice(
                    "Confirm history change",
                    f"{'Redo' if redo else 'Undo'}: {label}. "
                    "This can remove or restore "
                    "records, task inputs and reusable "
                    "names. Continue?",
                    ["Cancel", "Continue"],
                )
                if decision != "Continue":
                    return
            scroll = self.scroll_offset
            self.session.replay(redo=redo)
            if self.timing_screen:
                self.timing_screen.render()
            elif self.organization_screen:
                self.organization_screen.render()
            elif self.assessment_browser:
                self.assessment_browser.render()
                await self.scroller.scroll_to(offset=scroll, duration=0)
            elif self.worker_browser:
                self.worker_browser.render()
                await self.scroller.scroll_to(offset=scroll, duration=0)
            elif self.task_editor:
                previous = self.task_editor
                selected = assessment(
                    self.session.working,
                    self.session.active.get("selected_worker"),
                    previous.selected["document"].document_id,
                    kind=assessment_kind(previous.draft),
                )
                if selected:
                    previous.selected = selected
                    previous.pending = False
                    previous.results.generation += 1
                    previous.render()
                    await self.scroller.scroll_to(offset=scroll, duration=0)
                else:
                    self.home()
            else:
                self.home()
            self.update_project_actions()
            await self.notify(f"{'Redone' if redo else 'Undone'}: {label}")
        except Exception as error:
            await self.notify(f"Could not replay change: {error}", error=True)

    async def undo(self, event: ft.Event) -> None:
        """Undo the latest accepted project change from any mobile screen.

        Args:
            event: Shared Undo button gesture.

        Returns:
            None.
        """
        await event.control.focus()
        await self.replay(redo=False)

    async def redo(self, event: ft.Event) -> None:
        """Redo the next retained project change from any mobile screen.

        Args:
            event: Shared Redo button gesture.

        Returns:
            None.
        """
        await event.control.focus()
        await self.replay(redo=True)

    async def record_scroll(self, event: ft.OnScrollEvent) -> None:
        """Retain body scroll during worker history replay without moving the toolbar.

        Args:
            event: Active subpage scroll metrics.

        Returns:
            None; scrolling is presentation state, not a project mutation.
        """
        self.scroll_offset = event.pixels

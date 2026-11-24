"""Mobile worker browser and live detail form, composed with the shared app toolbar.

Search, alphabet and ID/name ordering retain stable worker selection. Existing edits
are accepted at field completion, without a second Save. Add is a single deliberate
creation action. Calendar controls store ISO dates; body units follow the project.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

import flet as ft
from mobile_workers import (
    BODY_INPUT_PATTERN,
    age,
    delete_worker,
    filter_workers,
    form_values,
    initial,
    load_workers,
    make_worker,
    put_worker,
)
from touch_alphabet import alphabet

from ergotools.domain.work_catalog import WorkerEntry
from ergotools.domain.worker_details import WorkerDetails

if TYPE_CHECKING:
    from mobile_ui import TabletApp


class WorkerBrowser:
    """Own transient worker filtering/form state within one TabletApp instance.

    Attributes:
        app: Host shell; provides shared Save/history, messages and cards.
        selected_id: Stable worker selection, never a list index.
        current: Expected source entry used for stale-edit protection.
        values: Complete visible form in display units; ISO dates remain optional.
        creating: Whether the form is collecting one new worker.
    """

    def __init__(self, app: TabletApp) -> None:
        """Start an unfiltered browser without creating any worker data.

        Args:
            app: TabletApp composition owner, independent of core domain/storage.

        Returns:
            None; rendering and all writes remain explicit.
        """
        self.app = app
        self.query, self.letter, self.by_id = "", "All", False
        self.selected_id = app.session.active.get("selected_worker")
        self.current = None
        self.values = {}
        self.original = {}
        self.creating = False
        self.form_dirty = False
        self.details_expanded = False
        self.all_workers, self.system = load_workers(app.session.working)
        self.list_panel = ft.Column(spacing=8)
        self.detail_panel = ft.Column(spacing=12)
        self.age_text = ft.Text()

    def render(self, *, reload_form: bool = True) -> None:
        """Refresh the two-column/stacked browser while retaining current filters.

        Args:
            reload_form: Reload accepted selected values after history or navigation.

        Returns:
            None; portrait stacks controls instead of shrinking touch targets.
        """
        self.all_workers, self.system = load_workers(self.app.session.working)
        if self.selected_id not in {w.worker_id for w in self.all_workers}:
            self.selected_id = (
                self.all_workers[0].worker_id if self.all_workers else None
            )
        self.app.session.active["selected_worker"] = self.selected_id
        self.app.session.persist()
        if reload_form:
            self.load_form()
        search = ft.TextField(
            label="Search worker ID or name",
            value=self.query,
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.search_changed,
            on_submit=self.search_changed,
        )
        left = self.app.card(
            [
                self.app.heading("Find a worker"),
                self.app.button(
                    "Add worker", ft.Icons.PERSON_ADD, self.new_worker, primary=True
                ),
                search,
                self.app.button(
                    "Order: ID" if self.by_id else "Order: last name",
                    ft.Icons.SORT_BY_ALPHA,
                    self.order_changed,
                ),
                ft.Text("Swipe the alphabet to browse last-name initials.", size=14),
                self.list_panel,
            ],
            col={"xs": 12, "lg": 4},
        )
        right = self.app.card([self.detail_panel], col={"xs": 12, "lg": 8})
        self.app.show(
            "Workers",
            [
                ft.Text(
                    "Edit a field, then move to the next "
                    "one to accept it. Project Save stores "
                    "all accepted changes. Undo/Redo is "
                    "shared with the rest of the project.",
                    size=16,
                ),
                ft.ResponsiveRow([left, right], spacing=16, run_spacing=16),
            ],
        )
        self.refresh_list()
        self.refresh_form()

    def load_form(self) -> None:
        """Load the selected worker without altering literal or canonical values.

        Args:
            None.

        Returns:
            None; absent worker leaves an empty selection until Add is pressed.
        """
        self.creating = False
        self.current = next(
            (w for w in self.all_workers if w.worker_id == self.selected_id), None
        )
        self.values = form_values(self.current, self.system) if self.current else {}
        self.original = dict(self.values)
        self.form_dirty = False

    def refresh_list(self) -> None:
        """Rebuild searchable selection controls without recreating the focused field.

        Args:
            None.

        Returns:
            None; only the browser list region changes on search input.
        """
        offered = filter_workers(self.all_workers, self.query, by_id=self.by_id)
        visible = filter_workers(
            self.all_workers, self.query, self.letter, by_id=self.by_id
        )
        self.list_panel.controls = [
            alphabet({initial(w) for w in offered}, self.letter, self.letter_changed),
            ft.Text(f"{len(visible)} of {len(self.all_workers)} workers", size=15),
        ]
        rows = []
        for worker in visible:
            years = age(worker)
            details = worker.details
            subtitle = (
                " · ".join(
                    p
                    for p in (
                        (details.sex if details else None),
                        f"Age {years}" if years is not None else None,
                    )
                    if p
                )
                or "No demographic details"
            )
            rows.append(
                ft.ListTile(
                    title=ft.Text(
                        f"{worker.worker_id} · {worker.first_name or ''} "
                        f"{worker.last_name or ''}",
                        weight=ft.FontWeight.BOLD,
                    ),
                    subtitle=ft.Text(subtitle),
                    leading=ft.Icon(ft.Icons.PERSON),
                    selected=worker.worker_id == self.selected_id,
                    selected_tile_color="#DDF2F4",
                    min_height=70,
                    data=worker.worker_id,
                    on_click=self.select_worker,
                )
            )
        if not rows:
            rows = [
                ft.Text(
                    "No workers yet. Tap Add worker to create the first one."
                    if not self.all_workers
                    else "No matching workers. Clear the search or choose All."
                )
            ]
        self.list_panel.controls.append(
            ft.Container(
                ft.Column(rows, scroll=ft.ScrollMode.AUTO),
                height=min(300, max(90, len(visible) * 78)),
            )
        )
        self.list_panel.controls.append(
            ft.Row(
                [
                    self.app.button(
                        "Previous",
                        ft.Icons.CHEVRON_LEFT,
                        self.previous,
                        disabled=not visible
                        or self.selected_id == visible[0].worker_id,
                    ),
                    self.app.button(
                        "Next",
                        ft.Icons.CHEVRON_RIGHT,
                        self.next,
                        disabled=not visible
                        or self.selected_id == visible[-1].worker_id,
                    ),
                ],
                wrap=True,
            )
        )
        self.app.page.update()

    def field(self, key: str, label: str, *, numeric: bool = False) -> ft.TextField:
        """Create one optional text/body field with per-field acceptance.

        Args:
            key: Canonical worker/form field name.
            label: Visible label including body units when appropriate.
            numeric: Request decimal keyboard and restrict body input characters.

        Returns:
            Touch field preserving original display text until edited.
        """
        return ft.TextField(
            label=label,
            value=self.values.get(key, ""),
            data=key,
            read_only=key == "worker_id" and not self.creating,
            keyboard_type=ft.KeyboardType.NUMBER if numeric else ft.KeyboardType.TEXT,
            input_filter=ft.InputFilter(regex_string=BODY_INPUT_PATTERN, allow=True)
            if numeric
            else None,
            on_change=self.form_changed,
            on_blur=self.field_finished,
            on_submit=self.field_finished,
            col={"xs": 12, "sm": 6},
        )

    def calendar_row(self, key: str, label: str) -> ft.Row:
        """Present an optional calendar date with an explicit clear action.

        Args:
            key: birth_date or hiring_date.
            label: User-facing date meaning.

        Returns:
            Calendar button and clear target; no default date is silently saved.
        """

        async def pick(event: ft.Event) -> None:
            """Open a date selector at the saved date or appropriate recent year.

            Args:
                event: Calendar button tap.

            Returns:
                None; canceled dates leave the form unchanged.
            """
            today = date.today()
            fallback = (
                date(today.year - 18, today.month, min(today.day, 28))
                if key == "birth_date"
                else today
            )
            current = (
                date.fromisoformat(self.values[key])
                if self.values.get(key)
                else fallback
            )

            async def accepted(event: ft.Event) -> None:
                """Accept the chosen calendar date as one undoable field edit.

                Args:
                    event: DatePicker change; its value is a datetime.

                Returns:
                    None; validation messages stay in the worker form.
                """
                self.values[key] = event.control.value.date().isoformat()
                self.form_dirty = True
                if not self.creating:
                    await self.commit(key)
                self.refresh_form()
                self.app.page.update()

            self.app.page.show_dialog(
                ft.DatePicker(
                    value=datetime.combine(current, datetime.min.time()),
                    first_date=datetime(1900, 1, 1),
                    last_date=datetime.combine(today, datetime.min.time()),
                    on_change=accepted,
                    help_text=label,
                )
            )

        async def clear(event: ft.Event) -> None:
            """Remove only this optional date without touching the other details.

            Args:
                event: Clear-date button.

            Returns:
                None; existing-worker changes join the shared history.
            """
            self.values[key] = ""
            self.form_dirty = True
            if not self.creating:
                await self.commit(key)
            self.refresh_form()
            self.app.page.update()

        text = (
            date.fromisoformat(self.values[key]).strftime("%d %b %Y")
            if self.values.get(key)
            else "Not set"
        )
        return ft.Row(
            [
                self.app.button(f"{label}: {text}", ft.Icons.CALENDAR_MONTH, pick),
                self.app.button(
                    "Clear", ft.Icons.CLEAR, clear, disabled=not self.values.get(key)
                ),
            ],
            wrap=True,
        )

    def refresh_form(self) -> None:
        """Compose identity, demographics and optional employment/contact groups.

        Args:
            None.

        Returns:
            None; controls are rebuilt only after selection/calendar/history changes.
        """
        if not self.current and not self.creating:
            self.detail_panel.controls = [
                self.app.heading("Worker details"),
                ft.Text("Choose a worker or tap Add worker to start."),
            ]
            self.app.page.update()
            return
        birth = self.values.get("birth_date") or None
        preview_age = age(
            WorkerEntry("preview", details=WorkerDetails(birth_date=birth))
        )
        self.age_text = ft.Text(
            f"Age: {preview_age}" if preview_age is not None else "Age: —",
            color="#0B3D60",
            size=17,
        )
        height_unit, weight_unit = (
            ("cm", "kg") if self.system.value == "metric" else ("in", "lb")
        )
        controls = [
            self.app.heading(
                "Add worker"
                if self.creating
                else f"{self.current.worker_id} · Worker details"
            ),
            ft.Text(
                "Worker ID is required; all other "
                "details are optional. Existing IDs "
                "stay fixed to preserve assessment "
                "associations."
            ),
            ft.ResponsiveRow(
                [
                    self.field("worker_id", "Worker ID"),
                    self.field("first_name", "First name"),
                    self.field("last_name", "Last name"),
                ],
                spacing=12,
                run_spacing=12,
            ),
            self.app.heading("Demographics"),
            ft.Dropdown(
                label="Sex",
                value=self.values.get("sex", ""),
                options=[
                    ft.DropdownOption("", "Not provided"),
                    ft.DropdownOption("Female", "Female"),
                    ft.DropdownOption("Male", "Male"),
                ],
                on_select=self.sex_changed,
            ),
            self.calendar_row("birth_date", "Date of birth"),
            self.age_text,
            ft.ResponsiveRow(
                [
                    self.field("height_cm", f"Height ({height_unit})", numeric=True),
                    self.field("weight_kg", f"Weight ({weight_unit})", numeric=True),
                ],
                spacing=12,
                run_spacing=12,
            ),
            ft.ExpansionTile(
                title=ft.Text(
                    "Employment and contact details", weight=ft.FontWeight.BOLD
                ),
                controls=[
                    self.calendar_row("hiring_date", "Date of hiring"),
                    ft.ResponsiveRow(
                        [
                            self.field(k, label)
                            for k, label in [
                                ("address", "Address"),
                                ("city", "City"),
                                ("region", "Region / state"),
                                ("country", "Country"),
                                ("postal_code", "Postal code"),
                                ("email", "Email"),
                            ]
                        ],
                        spacing=12,
                        run_spacing=12,
                    ),
                ],
                maintain_state=True,
                expanded=self.details_expanded,
                on_change=self.details_toggled,
            ),
            ft.Row(
                [
                    self.app.button(
                        "Add worker", ft.Icons.PERSON_ADD, self.add, primary=True
                    ),
                    self.app.button("Cancel", ft.Icons.CLOSE, self.cancel_add),
                ],
                wrap=True,
            )
            if self.creating
            else self.app.button("Delete worker", ft.Icons.PERSON_REMOVE, self.remove),
        ]
        self.detail_panel.controls = controls
        self.app.page.update()

    async def details_toggled(self, event: ft.Event) -> None:
        """Retain optional-section disclosure through worker edits and history replay.

        Args:
            event: ExpansionTile change, whose expanded flag reflects the new state.

        Returns:
            None; disclosure is browser state and does not dirty the project.
        """
        self.details_expanded = event.control.expanded

    async def form_changed(self, event: ft.Event) -> None:
        """Keep temporary typed text until field completion; do not create per-key undo.

        Args:
            event: Text field with data identifying its form key.

        Returns:
            None; project Save remains available for existing-worker field edits.
        """
        self.values[event.control.data] = event.control.value or ""
        self.form_dirty = self.values != self.original
        if not self.creating and self.form_dirty:
            self.app.save_button.disabled = False
            self.app.save_state.value = "Unsaved worker input"
            self.app.page.update()

    def flush(self, field: str = "details") -> None:
        """Validate and accept one completed existing-worker form change.

        Args:
            field: Field label for the common project Undo tooltip.

        Returns:
            None; invalid form values remain editable and saved files stay unchanged.
        """
        if self.creating:
            if any(self.values.values()):
                raise ValueError(
                    "Tap Add worker to accept the new record, "
                    "or Cancel to discard its form."
                )
            return
        if not self.form_dirty:
            return
        worker = make_worker(self.values, self.system, self.current)
        expected = self.current
        self.app.session.change(
            f"Edit worker · {field}",
            lambda: put_worker(self.app.session.working, worker, expected=expected),
        )
        self.current = worker
        self.original = dict(self.values)
        self.form_dirty = False
        self.all_workers, self.system = load_workers(self.app.session.working)

    async def commit(self, field: str) -> bool:
        """Accept worker values and synchronize project save/history controls.

        Args:
            field: Completed field name.

        Returns:
            Success flag; validation errors are visible instead of closing the form.
        """
        try:
            self.flush(field)
            self.refresh_list()
            self.app.update_project_actions()
            return True
        except Exception as error:
            await self.app.notify(f"Review worker details: {error}", error=True)
            return False

    async def field_finished(self, event: ft.Event) -> None:
        """Commit a completed text field as a single project history entry.

        Args:
            event: Text field blur/submit event.

        Returns:
            None; creation remains explicit until Add worker.
        """
        if not self.creating:
            await self.commit(event.control.data)

    async def sex_changed(self, event: ft.Event) -> None:
        """Accept categorical changes immediately instead of waiting for a text blur.

        Args:
            event: Sex selection.

        Returns:
            None; one change joins the same project history as other worker fields.
        """
        self.values["sex"] = event.control.value or ""
        self.form_dirty = True
        if not self.creating:
            await self.commit("sex")

    async def leave(self) -> bool:
        """Protect an unfinished creation form and validate pending existing edits.

        Args:
            None.

        Returns:
            Whether navigation can proceed; Cancel or invalid input retains the form.
        """
        if self.creating and any(self.values.values()):
            choice = await self.app.choice(
                "Worker not added",
                "Add this worker before leaving? "
                "Discard closes this form without "
                "adding it.",
                ["Cancel", "Discard", "Add worker"],
            )
            if choice == "Cancel":
                return False
            if choice == "Add worker":
                return await self.add(None)
            self.creating = False
            self.form_dirty = False
            return True
        if self.creating:
            return True
        return await self.commit("details")

    async def select_worker(self, event: ft.Event) -> None:
        """Select a stable worker after protecting the current form.

        Args:
            event: Worker list row holding its ID.

        Returns:
            None; canceled navigation preserves the selected record.
        """
        if await self.leave():
            self.selected_id = event.control.data
            self.app.session.active["selected_worker"] = self.selected_id
            self.app.session.persist()
            self.load_form()
            self.refresh_form()
            self.refresh_list()

    async def new_worker(self, event: ft.Event) -> None:
        """Open an empty creation form without inventing a worker or default DOB.

        Args:
            event: Add worker gesture.

        Returns:
            None; an ID is stored only on the form's Add action.
        """
        if await self.leave():
            self.creating = True
            self.current = None
            self.values = form_values(WorkerEntry("new"), self.system)
            self.values["worker_id"] = ""
            self.original = dict(self.values)
            self.form_dirty = False
            self.refresh_form()

    async def add(self, event: ft.Event | None) -> bool:
        """Accept one creation as one undoable project operation.

        Args:
            event: Explicit Add action, or None from leave protection.

        Returns:
            Success; duplicate/invalid values remain in the form.
        """
        try:
            worker = make_worker(self.values, self.system)
            self.app.session.change(
                f"Add worker · {worker.worker_id}",
                lambda: put_worker(self.app.session.working, worker),
            )
            self.selected_id = worker.worker_id
            self.creating = False
            self.render()
            await self.app.notify("Worker added. Use project Save to retain changes.")
            return True
        except Exception as error:
            await self.app.notify(f"Could not add worker: {error}", error=True)
            return False

    async def cancel_add(self, event: ft.Event) -> None:
        """Close the unadded worker form after an explicit discard decision.

        Args:
            event: Cancel creation gesture.

        Returns:
            None; no native worker was created.
        """
        if (
            not any(self.values.values())
            or await self.app.choice(
                "Cancel new worker",
                "Discard this unadded worker form?",
                ["Keep editing", "Discard"],
            )
            == "Discard"
        ):
            self.load_form()
            self.refresh_form()

    async def remove(self, event: ft.Event) -> None:
        """Delete only after naming the worker and warning about the operation.

        Args:
            event: Delete worker tap.

        Returns:
            None; protected associations are refused by the native adapter.
        """
        if not await self.commit("details"):
            return
        worker = self.current
        if (
            await self.app.choice(
                "Delete worker",
                f"Delete {worker.worker_id} · {worker.first_name or ''} "
                f"{worker.last_name or ''}? This can be undone. "
                "Workers with assessments or workplace "
                "associations cannot be deleted here.",
                ["Cancel", "Delete worker"],
            )
            != "Delete worker"
        ):
            return
        try:
            self.app.session.change(
                f"Delete worker · {worker.worker_id}",
                lambda: delete_worker(self.app.session.working, worker.worker_id),
            )
            self.render()
            await self.app.notify(
                "Worker deleted from the working project. Undo can restore it."
            )
        except Exception as error:
            await self.app.notify(str(error), error=True)

    async def search_changed(self, event: ft.Event) -> None:
        """Filter only the list while keeping the current form and keyboard intact.

        Args:
            event: Search field change.

        Returns:
            None; an empty result never deletes or silently changes the worker.
        """
        self.query = event.control.value or ""
        self.letter = "All"
        self.refresh_list()

    async def letter_changed(self, letter: str) -> None:
        """Filter by an offered initial without hiding the worker edit form.

        Args:
            letter: All or an enabled last-name initial.

        Returns:
            None; selection stays explicit.
        """
        self.letter = letter
        self.refresh_list()

    async def order_changed(self, event: ft.Event) -> None:
        """Toggle ID/last-name ordering without writing project data.

        Args:
            event: Order button tap.

        Returns:
            None; browser filters and form stay available.
        """
        self.by_id = not self.by_id
        self.render(reload_form=False)

    async def navigate(self, step: int) -> None:
        """Navigate the currently filtered catalog by one stable selection.

        Args:
            step: -1 for previous, +1 for next.

        Returns:
            None; boundaries stay on the current record.
        """
        visible = filter_workers(
            self.all_workers, self.query, self.letter, by_id=self.by_id
        )
        if not visible or not await self.leave():
            return
        index = next(
            (i for i, w in enumerate(visible) if w.worker_id == self.selected_id), 0
        )
        self.selected_id = visible[
            max(0, min(len(visible) - 1, index + step))
        ].worker_id
        self.app.session.active["selected_worker"] = self.selected_id
        self.app.session.persist()
        self.load_form()
        self.refresh_form()
        self.refresh_list()

    async def previous(self, event: ft.Event) -> None:
        """Navigate to the previous visible worker.

        Args:
            event: Previous button tap.

        Returns:
            None.
        """
        await self.navigate(-1)

    async def next(self, event: ft.Event) -> None:
        """Navigate to the next visible worker.

        Args:
            event: Next button tap.

        Returns:
            None.
        """
        await self.navigate(1)

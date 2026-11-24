"""Touch organization browser and typed metadata forms with reusable native timing.

Hierarchy cards expose parent/child structure instead of a compressed desktop tree.
Explicit Apply accepts form changes into the shared project timeline; Main Save
retains them. Native date pickers and hour/minute choices avoid free-form clocks.
"""

from datetime import datetime
from typing import TYPE_CHECKING

import flet as ft
from tablet_style import action_button

if TYPE_CHECKING:
    from mobile_ui import TabletApp
from mobile_organization import (
    accept_record,
    organization_snapshot,
    record_from_form,
    remove_record,
)
from mobile_workers import BODY_INPUT_PATTERN

from ergotools.application.organization_management import organization_keys
from ergotools.application.rotation_timing import shift_clock
from ergotools.domain.organization_record import (
    ORGANIZATION_FIELDS,
    OrganizationKind,
    OrganizationRecord,
)

# Existing hierarchy kind ordering, not a new persisted organization taxonomy.
LEVELS = (
    OrganizationKind.PLANT,
    OrganizationKind.SECTION,
    OrganizationKind.LINE,
    OrganizationKind.STATION,
)
ICONS = {
    OrganizationKind.PLANT: ft.Icons.FACTORY_OUTLINED,
    OrganizationKind.SECTION: ft.Icons.GRID_VIEW,
    OrganizationKind.LINE: ft.Icons.ACCOUNT_TREE_OUTLINED,
    OrganizationKind.STATION: ft.Icons.LOCATION_ON_OUTLINED,
    OrganizationKind.SHIFT: ft.Icons.SCHEDULE,
}


class OrganizationScreen:
    """Own browser selection/disclosure while native projects own all accepted data.

    Attributes:
        app: Mobile shell supplying shared history, status and Save.
        shifts: Whether independent shifts rather than physical locations are shown.
    """

    def __init__(self, app: "TabletApp") -> None:
        """Start at physical locations without creating default organization data.

        Args:
            app: Tablet shell with an active native project.

        Returns:
            None; render explicitly reads the current hierarchy.
        """
        self.app = app
        self.shifts = False
        self.expanded = set()

    def render(self) -> None:
        """Show hierarchy or shift cards with clear edit/add/timing actions.

        Args:
            None.

        Returns:
            None; all rendered hierarchy data is read-only until an explicit form Apply.
        """
        self.hierarchy, self.templates = organization_snapshot(self.app.session.working)

        async def tab(event: ft.Event) -> None:
            """Switch catalog page without changing any stored data."""
            self.shifts = event.control.data
            self.render()

        cards = []
        if self.shifts:
            for identity in self.hierarchy.work.shifts:
                record = next(
                    (
                        r
                        for r in self.hierarchy.organization
                        if r.kind is OrganizationKind.SHIFT and r.keys == (identity,)
                    ),
                    OrganizationRecord(OrganizationKind.SHIFT, (identity,)),
                )
                attributes = dict(record.attributes)
                timing = next(
                    (t.timing for t in self.templates if t.shift_id == identity), None
                )

                async def edit(
                    event: ft.Event, record: OrganizationRecord = record
                ) -> None:
                    """Edit this exact independent shift definition."""
                    self.form(record)

                async def timing_action(
                    event: ft.Event, identity: str = identity
                ) -> None:
                    """Open timing only with complete shift clocks."""
                    try:
                        clock = shift_clock(self.hierarchy, identity)
                        from tablet_timing import TimingScreen

                        self.app.timing_screen = TimingScreen(
                            self.app, self, identity, clock
                        )
                        self.app.timing_screen.render()
                    except ValueError as error:
                        await self.app.notify(str(error), error=True)

                break_total = (
                    timing.shift_minutes - timing.productive_minutes if timing else 0
                )
                cards.append(
                    self.app.card(
                        [
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.SCHEDULE, size=28, color="#078398"
                                    ),
                                    self.app.heading(identity),
                                ]
                            ),
                            ft.Text(
                                f"{attributes.get('start_time') or 'Start not set'} "
                                f"→ {attributes.get('end_time') or 'End not set'}",
                                size=22,
                                weight=ft.FontWeight.W_600,
                                color="#0B3D60",
                            ),
                            ft.Text(
                                attributes.get("description")
                                or "Recurring shift definition",
                                size=15,
                                color="#405D70",
                            ),
                            ft.Container(
                                ft.Text(
                                    f"{len(timing.block_minutes)} work blocks · "
                                    f"{break_total}"
                                    " "
                                    f"min breaks"
                                    if timing
                                    else "Timing not configured",
                                    weight=ft.FontWeight.W_600,
                                    color="#078398",
                                ),
                                padding=12,
                                bgcolor="#EAF6F7",
                                border_radius=10,
                            ),
                            ft.Row(
                                [
                                    self.app.button(
                                        "Edit shift", ft.Icons.EDIT_OUTLINED, edit
                                    ),
                                    self.app.button(
                                        "Blocks & breaks"
                                        if timing
                                        else "Set up blocks & breaks",
                                        ft.Icons.VIEW_TIMELINE_OUTLINED,
                                        timing_action,
                                        primary=True,
                                    ),
                                ],
                                wrap=True,
                            ),
                        ],
                        col={"xs": 12, "lg": 6},
                    )
                )
            listing = ft.ResponsiveRow(cards, spacing=16, run_spacing=16)
        else:

            def branch(
                kind: OrganizationKind, keys: tuple[str, ...]
            ) -> ft.ExpansionTile:
                """Project scoped nodes and retain expanded paths."""

                async def edit(event: ft.Event) -> None:
                    """Open the existing metadata form for this exact node."""
                    self.form(
                        next(
                            (
                                r
                                for r in self.hierarchy.organization
                                if r.kind is kind and r.keys == keys
                            ),
                            OrganizationRecord(kind, keys),
                        )
                    )

                async def add(event: ft.Event) -> None:
                    """Create one child in the selected existing parent."""
                    self.form(
                        OrganizationRecord(
                            LEVELS[LEVELS.index(kind) + 1], (*keys, "New")
                        ),
                        creating=True,
                    )

                actions = [self.app.button("Details", ft.Icons.EDIT_OUTLINED, edit)]
                if kind is not OrganizationKind.STATION:
                    actions.append(
                        self.app.button(
                            "Add " + LEVELS[LEVELS.index(kind) + 1].value.lower(),
                            ft.Icons.ADD,
                            add,
                        )
                    )
                children = []
                if kind is not OrganizationKind.STATION:
                    next_kind = LEVELS[LEVELS.index(kind) + 1]
                    children = [
                        branch(next_kind, child)
                        for child in organization_keys(self.hierarchy, next_kind)
                        if child[:-1] == keys
                    ]

                async def disclosure(event: ft.Event) -> None:
                    """Retain disclosure through edits and replay."""
                    self.expanded.add(
                        keys
                    ) if event.control.expanded else self.expanded.discard(keys)

                return ft.ExpansionTile(
                    title=ft.Text(
                        keys[-1], size=19, weight=ft.FontWeight.W_600, color="#0B3D60"
                    ),
                    subtitle=ft.Text(kind.value, color="#405D70"),
                    leading=ft.Icon(ICONS[kind], color="#078398", size=26),
                    expanded=keys in self.expanded,
                    on_change=disclosure,
                    bgcolor="#EAF6F8",
                    collapsed_bgcolor="white",
                    tile_padding=ft.Padding(16, 8, 16, 8),
                    controls_padding=ft.Padding(18, 6, 12, 12),
                    shape=ft.RoundedRectangleBorder(radius=14),
                    collapsed_shape=ft.RoundedRectangleBorder(radius=14),
                    controls=[ft.Row(actions, wrap=True), *children],
                )

            listing = ft.Container(
                ft.Column(
                    [
                        branch(OrganizationKind.PLANT, (name,))
                        for name in self.hierarchy.plants
                    ]
                    or [ft.Text("No locations yet. Add a plant to begin.")]
                ),
                max_width=900,
            )

        if not self.shifts:
            listing.col = {"xs": 12, "lg": 8}
            summary = self.app.card(
                [
                    self.app.heading("Structure at a glance"),
                    *[
                        ft.Row(
                            [
                                ft.Icon(ICONS[kind], color="#078398", size=25),
                                ft.Text(
                                    kind.value + "s",
                                    size=16,
                                    color="#405D70",
                                    expand=True,
                                ),
                                ft.Text(
                                    str(len(organization_keys(self.hierarchy, kind))),
                                    size=26,
                                    weight=ft.FontWeight.BOLD,
                                    color="#0B3D60",
                                ),
                            ]
                        )
                        for kind in (*LEVELS, OrganizationKind.SHIFT)
                    ],
                    ft.Divider(color="#E0EAF0"),
                    ft.Text(
                        "Expand a location to see its children, "
                        "edit details or add a new place.",
                        size=15,
                        color="#405D70",
                    ),
                ],
                col={"xs": 12, "lg": 4},
            )
            listing = ft.ResponsiveRow([listing, summary], spacing=16, run_spacing=16)

        async def create(event: ft.Event) -> None:
            """Start one new top-level plant or independent shift form."""
            kind = OrganizationKind.SHIFT if self.shifts else OrganizationKind.PLANT
            self.form(OrganizationRecord(kind, ("New",)), creating=True)

        self.app.show(
            "Organization & shifts",
            [
                ft.Text(
                    "Define where work happens and when people work. "
                    "Accepted edits use project Undo/Redo and Save.",
                    size=16,
                    color="#405D70",
                ),
                ft.Row(
                    [
                        action_button(
                            "Locations",
                            icon=ft.Icons.FACTORY_OUTLINED,
                            data=False,
                            on_click=tab,
                            height=48,
                            bgcolor="#DDF2F4" if not self.shifts else "white",
                        ),
                        action_button(
                            "Shifts",
                            icon=ft.Icons.SCHEDULE,
                            data=True,
                            on_click=tab,
                            height=48,
                            bgcolor="#DDF2F4" if self.shifts else "white",
                        ),
                        self.app.button(
                            "Add shift" if self.shifts else "Add plant",
                            ft.Icons.ADD,
                            create,
                        ),
                    ],
                    wrap=True,
                ),
                listing,
                ft.Text(
                    "Edits are included in Project Save.",
                    size=14,
                    color="#405D70",
                    tooltip=(
                        "Native guards protect referenced workplaces. "
                        "Reusable Shift timing does not change saved rotation copies."
                    ),
                ),
            ],
        )

    def form(self, record: OrganizationRecord, *, creating: bool = False) -> None:
        """Present typed metadata in an owned, scrollable form with safe cancellation.

        Args:
            record: Existing immutable descriptive record or a new parent's template.
            creating: New identifiers are editable; existing identities cannot rename.

        Returns:
            None; Apply publishes one guarded native mutation or reports a failure.
        """
        expected = self.hierarchy
        identifier = ft.TextField(
            label=record.kind.value + " name / ID",
            value="" if creating else record.keys[-1],
            read_only=not creating,
        )
        fields = {}
        attributes = dict(record.attributes)
        controls = [identifier]
        for key, field_type in ORGANIZATION_FIELDS[record.kind.value]:
            value = attributes.get(key)
            if key in ("start_time", "end_time"):
                hour, minute = (
                    str(value).split(":")
                    if value
                    else ("08" if key == "start_time" else "16", "00")
                    if creating
                    else (None, None)
                )
                first = ft.Dropdown(
                    label=key.replace("_", " ").title() + " · hour",
                    value=hour,
                    options=[
                        ft.DropdownOption("", "Not set"),
                        *[ft.DropdownOption(f"{i:02d}") for i in range(24)],
                    ],
                    width=210,
                )
                last = ft.Dropdown(
                    label="Minute",
                    value=minute,
                    options=[
                        ft.DropdownOption("", "Not set"),
                        *[ft.DropdownOption(f"{i:02d}") for i in range(60)],
                    ],
                    width=160,
                )
                fields[key] = (first, last)
                controls.append(ft.Row([first, ft.Text(":", size=24), last], wrap=True))
            elif field_type == "date":
                field = ft.TextField(
                    label=key.replace("_", " ").title(),
                    value=value or "",
                    read_only=True,
                    expand=True,
                )

                async def choose_date(
                    event: ft.Event, field: ft.TextField = field
                ) -> None:
                    """Use the native calendar and retain canonical ISO text."""

                    async def accepted(event: ft.Event) -> None:
                        """Project the selected date into this draft."""
                        field.value = event.control.value.date().isoformat()
                        field.update()

                    self.app.page.show_dialog(
                        ft.DatePicker(
                            first_date=datetime(1900, 1, 1),
                            last_date=datetime(2100, 12, 31),
                            on_change=accepted,
                        )
                    )

                fields[key] = field
                controls.append(
                    ft.Row(
                        [
                            field,
                            ft.IconButton(
                                icon=ft.Icons.CALENDAR_MONTH,
                                on_click=choose_date,
                                tooltip="Choose a date",
                            ),
                        ]
                    )
                )
            else:
                field = ft.TextField(
                    label=key.replace("_", " ").title(),
                    value="" if value is None else str(value),
                    multiline=field_type == "text",
                    min_lines=2 if field_type == "text" else 1,
                    input_filter=ft.InputFilter(
                        regex_string=BODY_INPUT_PATTERN, allow=True
                    )
                    if field_type == "number"
                    else None,
                    keyboard_type=ft.KeyboardType.NUMBER
                    if field_type == "number"
                    else ft.KeyboardType.TEXT,
                )
                fields[key] = field
                controls.append(field)
        primary = []
        optional = []
        for (key, _), control in zip(
            ORGANIZATION_FIELDS[record.kind.value], controls[1:], strict=True
        ):
            (
                primary
                if key
                in {
                    "description",
                    "start_time",
                    "end_time",
                    "opening_date",
                    "creation_date",
                }
                else optional
            ).append(control)
        controls = [
            identifier,
            ft.Text(
                " / ".join(record.keys[:-1])
                or "Project-wide " + record.kind.value.lower(),
                size=14,
                color="#405D70",
            ),
            *primary,
        ]
        if optional:
            controls.append(
                ft.ExpansionTile(title=ft.Text("Additional details"), controls=optional)
            )
        status = ft.Text(
            "Apply accepts the form; Project Save stores it.", color="#405D70"
        )
        reset = ft.Checkbox(
            label="Reset existing timing if shift duration changes", value=False
        )
        if record.kind is OrganizationKind.SHIFT:
            controls.extend(
                [
                    ft.Text(
                        "24-hour time. End at/before start means the following day.",
                        color="#405D70",
                    ),
                    reset,
                ]
            )

        async def apply(event: ft.Event) -> None:
            """Validate typed metadata and accept it as one project history command."""
            try:
                values = {}
                for key, _ in ORGANIZATION_FIELDS[record.kind.value]:
                    field = fields[key]
                    if isinstance(field, tuple):
                        if bool(field[0].value) != bool(field[1].value):
                            raise ValueError(
                                "Set both hour and minute, or leave both unset."
                            )
                        values[key] = (
                            f"{field[0].value}:{field[1].value}"
                            if field[0].value
                            else ""
                        )
                    else:
                        values[key] = field.value or ""
                replacement = record_from_form(record, identifier.value, values)
                if (
                    reset.value
                    and await self.app.choice(
                        "Reset shift timing?",
                        "The existing blocks and breaks will be cleared "
                        "if their duration no longer matches.",
                        ["Cancel", "Reset if needed"],
                    )
                    != "Reset if needed"
                ):
                    return
                self.app.session.change(
                    "Add organization" if creating else "Edit organization",
                    lambda: accept_record(
                        self.app.session.working,
                        expected,
                        replacement,
                        creating=creating,
                        reset_timing=reset.value,
                    ),
                )
                self.app.page.pop_dialog()
                self.render()
            except (ValueError, OSError) as error:
                status.value = str(error)
                status.color = "#B3261E"
                status.update()

        async def cancel(event: ft.Event) -> None:
            """Close the uncommitted form without modifying any project data."""
            self.app.page.pop_dialog()

        async def remove(event: ft.Event) -> None:
            """Confirm deletion; native guards protect references."""
            if (
                await self.app.choice(
                    "Delete " + record.kind.value + "?",
                    "Unreferenced children will also be removed. "
                    "Referenced assignments and assessments are protected.",
                    ["Cancel", "Delete"],
                )
                != "Delete"
            ):
                return
            try:
                self.app.session.change(
                    "Delete organization",
                    lambda: remove_record(
                        self.app.session.working, expected, record.kind, record.keys
                    ),
                )
                self.app.page.pop_dialog()
                self.render()
            except (ValueError, OSError) as error:
                status.value = str(error)
                status.color = "#B3261E"
                status.update()

        actions = [
            self.app.button("Cancel", ft.Icons.CLOSE, cancel),
            self.app.button("Apply", ft.Icons.CHECK, apply, primary=True),
        ]
        if not creating:
            actions.insert(
                0, self.app.button("Delete", ft.Icons.DELETE_OUTLINE, remove)
            )
        self.app.page.show_dialog(
            ft.AlertDialog(
                title=self.app.heading(
                    ("Add " if creating else "Edit ") + record.kind.value
                ),
                content=ft.Container(
                    ft.Column(
                        [*controls, status],
                        scroll=ft.ScrollMode.AUTO,
                        spacing=16,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                    width=min(650, (self.app.page.width or 800) - 100),
                    height=min(620, (self.app.page.height or 800) - 220),
                ),
                actions=actions,
            )
        )

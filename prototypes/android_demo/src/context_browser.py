"""Touch assessment browser and reusable workplace destination picker.

Uses real hierarchy/ownership, search/alphabet, explicit current-tool context cards,
risk colors and project history. This frontend edits no organization or Job metadata.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

import flet as ft
from assessment_contexts import (
    create_assessment,
    delete_assessment,
    destination_record,
    read_contexts,
    transfer_assessment,
    workplace_label,
)
from assessment_tools import TOOLS
from mobile_results import BANDS
from mobile_workers import filter_workers, initial
from tablet_style import action_button
from touch_alphabet import alphabet

from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.risk import classify_probability

if TYPE_CHECKING:
    from mobile_ui import TabletApp


def risk_badge(record: dict | None) -> ft.Container:
    """Display saved probability/status with domain colors; absence is never zero risk.

    Args:
        record: Exact source/result projection, or an unoccupied destination.

    Returns:
        Compact readable badge for both browser cards and destination leaves.
    """
    result = record["result"] if record else None
    probability = result.probability_percent if result else None
    color = (
        BANDS[classify_probability(probability).value][1]
        if probability is not None
        else "#E7EEF3"
    )
    label = (
        f"{probability:.1f}%"
        if probability is not None
        else "No probability"
        if result
        else "Not calculated"
        if record
        else "No assessment"
    )
    if result and result.calculation_status.value == "partial":
        label += " · Partial"
    return ft.Container(
        ft.Text(label, color="#111111", weight=ft.FontWeight.BOLD, size=15),
        bgcolor=color,
        padding=8,
        border_radius=6,
    )


def hierarchy_tree(
    items: list[tuple[tuple[str, ...], ft.Control]],
    expanded: set[tuple[str, ...]],
    depth: int = 0,
    prefix: tuple[str, ...] = (),
) -> list[ft.Control]:
    """Group leaves into one reusable, expandable Plant/Section/Line/Station tree.

    Args:
        items: Exact label path and already composed leaf, in display order.
        expanded: Caller-owned expanded paths, retained across refresh/history replay.
        depth: Recursive path level.
        prefix: Full parent path; duplicate station names remain distinct.

    Returns:
        Native touch expansion controls, no global or database view state.
    """
    leaves = [control for path, control in items if len(path) == depth]
    names = sorted(
        {path[depth] for path, _ in items if len(path) > depth}, key=str.casefold
    )
    icons = (
        ft.Icons.FACTORY_OUTLINED,
        ft.Icons.ACCOUNT_TREE_OUTLINED,
        ft.Icons.LINEAR_SCALE,
        ft.Icons.LOCATION_ON_OUTLINED,
    )
    for name in names:
        key = (*prefix, name)
        children = [
            (path, c) for path, c in items if len(path) > depth and path[depth] == name
        ]

        async def toggle(event: ft.Event, identity: tuple[str, ...] = key) -> None:
            """Retain disclosure state without recording data history.

            Args:
                event: Expansion control with current expanded value.
                identity: Exact full parent path captured for this node.

            Returns:
                None; controls outside this node remain in place.
            """
            if event.control.expanded:
                expanded.add(identity)
            else:
                expanded.discard(identity)

        leaves.append(
            ft.ExpansionTile(
                title=ft.Text(name, weight=ft.FontWeight.BOLD, color="#0B3D60"),
                leading=ft.Icon(icons[min(depth, 3)], color="#078398"),
                controls=hierarchy_tree(children, expanded, depth + 1, key),
                expanded=key in expanded,
                maintain_state=True,
                on_change=toggle,
                controls_padding=ft.Padding(14, 0, 4, 8),
            )
        )
    return leaves


class DestinationPicker:
    """Read-only real worker/station/shift picker, shared by Add and Copy/Move.

    Attributes:
        app: Owning project shell/history.
        worker_id: Exact selected destination worker.
        kind: Tool whose existing destination risk is displayed.
        callback: Async action receiving destination and its exact shown record.
    """

    def __init__(
        self,
        app: TabletApp,
        worker_id: str,
        kind: AssessmentKind,
        callback: Callable[
            [str, WorkplaceContext | None, dict | None], Awaitable[None]
        ],
        *,
        source: dict | None = None,
    ) -> None:
        """Load one detached picker catalog without creating records or assignments.

        Args:
            app: Current tablet project.
            worker_id: Initial destination worker.
            kind: Current tool only.
            callback: Confirm/accept operation owned by caller.
            source: Transfer source; an identical destination is disabled.

        Returns:
            None; show() opens the composed picker.
        """
        self.app, self.worker_id, self.kind, self.callback, self.source = (
            app,
            worker_id,
            kind,
            callback,
            source,
        )
        self.catalog = read_contexts(app.session.working)
        self.query, self.letter = "", "All"
        self.expanded = set()
        self.shift = next(iter(self.catalog["hierarchy"].work.shifts), None)
        self.tree = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, height=310)
        self.workers = ft.Dropdown(
            label="Destination worker", width=420, on_select=self.change_worker
        )
        self.initials = ft.Column()
        self.feedback = ft.Text(
            "Choose standalone or expand the hierarchy and select a station.",
            color="#0B3D60",
        )

    async def change_worker(self, event: ft.Event) -> None:
        """Refresh destination badges when the worker changes.

        Args:
            event: Worker dropdown carrying exact ID.

        Returns:
            None; no data is transferred yet.
        """
        self.worker_id = event.control.value
        self.fill()
        self.app.page.update()

    async def search(self, event: ft.Event) -> None:
        """Search workers without closing or recreating the active text field.

        Args:
            event: ID/name search text.

        Returns:
            None; selection stays when offered, otherwise explicitly changes.
        """
        self.query, self.letter = event.control.value or "", "All"
        self.fill()
        self.app.page.update()

    async def choose_letter(self, letter: str) -> None:
        """Filter destination workers using the shared touch alphabet.

        Args:
            letter: Available normalized last-name initial or All.

        Returns:
            None.
        """
        self.letter = letter
        self.fill()
        self.app.page.update()

    async def change_shift(self, event: ft.Event) -> None:
        """Refresh station availability/risk for the selected real shift.

        Args:
            event: Project shift dropdown.

        Returns:
            None; standalone destinations have no shift.
        """
        self.shift = event.control.value
        self.fill()
        self.app.page.update()

    def leaf(self, workplace: WorkplaceContext | None) -> ft.Control:
        """Compose a destination action with existing value and explicit self-blocking.

        Args:
            workplace: Exact selected shift/station, or standalone.

        Returns:
            Wrapping action row, never a synthetic workplace ID.
        """
        existing = destination_record(
            self.catalog, self.worker_id, self.kind, workplace
        )
        same = (
            self.source is not None
            and self.source["worker"].worker_id == self.worker_id
            and self.source["workplace"] == workplace
        )

        async def select(event: ft.Event) -> None:
            """Pass the exact shown record into the caller's confirmation/mutation.

            Args:
                event: Destination action.

            Returns:
                None; errors remain visible in the picker.
            """
            try:
                await event.control.focus()
                await self.callback(self.worker_id, workplace, existing)
            except Exception as error:
                self.feedback.value = str(error)
                self.feedback.color = "#B3261E"
                self.app.page.update()

        label = (
            "Standalone assessment"
            if workplace is None
            else f"Select {workplace.station_id} · Shift {workplace.shift_id}"
        )
        return ft.Container(
            ft.Row(
                [
                    action_button(
                        label,
                        icon=ft.Icons.PERSON_OUTLINE
                        if workplace is None
                        else ft.Icons.LOCATION_ON_OUTLINED,
                        disabled=same,
                        tooltip="Source and destination are the same."
                        if same
                        else workplace_label(workplace),
                        on_click=select,
                        height=48,
                    ),
                    risk_badge(existing),
                    ft.Text(
                        "Current source"
                        if same
                        else f"{len(existing['source'].tasks)} tasks · "
                        f"{existing['job']}"
                        if existing
                        else "New empty destination",
                        size=14,
                    ),
                ],
                wrap=True,
            ),
            padding=6,
            bgcolor="#F3F7FA",
            border_radius=8,
        )

    def fill(self) -> None:
        """Project worker filtering and the real location tree for the current shift.

        Args:
            None.

        Returns:
            None; expanded paths survive worker/shift updates.
        """
        work = self.catalog["hierarchy"].work
        offered = filter_workers(work.workers, self.query, self.letter)
        searched = filter_workers(work.workers, self.query)
        self.initials.controls = [
            alphabet({initial(w) for w in searched}, self.letter, self.choose_letter)
        ]
        if self.worker_id not in {w.worker_id for w in offered}:
            self.worker_id = offered[0].worker_id if offered else None
        self.workers.options = [
            ft.DropdownOption(
                w.worker_id, f"{w.worker_id} · {w.first_name or ''} {w.last_name or ''}"
            )
            for w in offered
        ]
        self.workers.value = self.worker_id
        if self.worker_id is None:
            self.tree.controls = [ft.Text("No workers match this search.")]
            return
        items = []
        if self.shift:
            for station in work.stations:
                path = (station.plant_name, station.section_name, station.line_name)
                items.append((path, self.leaf(station.at_shift(self.shift))))
        self.tree.controls = [self.leaf(None), *hierarchy_tree(items, self.expanded)]
        if not work.stations or not work.shifts:
            self.tree.controls.append(
                ft.Text(
                    "No station/shift destinations. Add organization data on "
                    "desktop, then open the project here."
                )
            )

    def show(self) -> None:
        """Open a bounded picker with live target badges and Cancel.

        Args:
            None.

        Returns:
            None; selection requires explicit caller confirmation where destructive.
        """

        async def close(event: ft.Event) -> None:
            """Cancel the destination picker without changing project data.

            Args:
                event: Cancel action.

            Returns:
                None.
            """
            self.app.page.pop_dialog()

        self.fill()
        self.app.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=self.app.heading(f"{TOOLS[self.kind][0]} · Choose destination"),
                content=ft.Column(
                    [
                        ft.TextField(
                            label="Search destination worker ID or name",
                            width=800,
                            on_change=self.search,
                        ),
                        self.initials,
                        ft.Row(
                            [
                                self.workers,
                                ft.Dropdown(
                                    label="Workplace shift",
                                    width=220,
                                    value=self.shift,
                                    options=[
                                        ft.DropdownOption(s, s)
                                        for s in self.catalog["hierarchy"].work.shifts
                                    ],
                                    on_select=self.change_shift,
                                    disabled=self.shift is None,
                                ),
                            ],
                            wrap=True,
                        ),
                        self.tree,
                        self.feedback,
                    ],
                    width=800,
                    height=570,
                    scroll=ft.ScrollMode.AUTO,
                ),
                actions=[ft.TextButton("Cancel", on_click=close)],
            )
        )


class AssessmentBrowser:
    """Show current worker/tool's saved standalone and workplace assessments.

    Attributes:
        app: Project shell providing Save/history.
        worker_id: Exact current worker, independent of context selection.
        kind: Current tool; other tool results are not mixed into this list.
        expanded: Hierarchy disclosure state retained across refresh/Undo.
    """

    def __init__(self, app: TabletApp) -> None:
        """Bind browser view state without writing native data.

        Args:
            app: Current project shell.

        Returns:
            None; render loads current catalogs.
        """
        self.app = app
        self.catalog_id = app.session.active.get("id")
        self.worker_id = app.session.active.get("selected_worker")
        self.kind = app.selected_tool
        self.query, self.letter = "", "All"
        self.expanded = set()
        self.listing, self.filters = ft.Column(spacing=12), ft.Column(spacing=10)

    def render(self) -> None:
        """Rebuild after data/history changes, keeping filters and disclosure.

        Args:
            None.

        Returns:
            None; project toolbar remains fixed while the body scrolls.
        """
        self.catalog = read_contexts(self.app.session.working)
        self.app.show(
            "Assessments",
            [
                self.app.heading("Choose the assessment to view"),
                ft.Text(
                    "Choose a saved assessment to view or edit. "
                    "Standalone and workplace assessments are independent."
                ),
                ft.TextField(
                    label="Search worker ID or name",
                    value=self.query,
                    on_change=self.search,
                ),
                self.filters,
                self.listing,
            ],
        )
        self.fill()
        self.app.page.update()

    async def search(self, event: ft.Event) -> None:
        """Filter available workers while keeping the focused search control.

        Args:
            event: ID/name input.

        Returns:
            None.
        """
        self.query, self.letter = event.control.value or "", "All"
        self.fill()
        self.app.page.update()

    async def choose_letter(self, letter: str) -> None:
        """Select a last-name initial using the reusable touch control.

        Args:
            letter: Available initial or All.

        Returns:
            None.
        """
        self.letter = letter
        self.fill()
        self.app.page.update()

    async def select_worker(self, event: ft.Event) -> None:
        """Select an exact worker and remember it for task editing.

        Args:
            event: Worker dropdown.

        Returns:
            None; selection is view state, not a data edit.
        """
        self.worker_id = event.control.value
        self.app.session.active["selected_worker"] = self.worker_id
        self.app.session.persist()
        self.fill()
        self.app.page.update()

    async def select_tool(self, event: ft.Event) -> None:
        """Browse another tool without manufacturing or modifying an assessment.

        Args:
            event: Selected native model ID.

        Returns:
            None.
        """
        self.kind = AssessmentKind(event.control.value)
        self.app.selected_tool = self.kind
        self.fill()
        self.app.page.update()

    def card(self, record: dict) -> ft.Control:
        """Show exact context, result, task count and clearly separated record actions.

        Args:
            record: Saved worker/tool source projection.

        Returns:
            Wrapping card; long ancestry never establishes identity.
        """

        async def open_record(event: ft.Event) -> None:
            """Open this exact assessment, keeping its worker and tool synchronized.

            Args:
                event: Open action.

            Returns:
                None.
            """
            self.app.open_assessment_record(record)

        async def remove(event: ft.Event) -> None:
            """Confirm deletion of this source only and refresh context counts.

            Args:
                event: Delete assessment action.

            Returns:
                None; cancellation leaves every source/result unchanged.
            """
            await event.control.focus()
            if (
                await self.app.choice(
                    "Delete assessment",
                    f"Delete {TOOLS[self.kind][0]} for "
                    f"{record['worker'].worker_id} at {record['context']}? "
                    "Inputs and results will be removed; the workplace assignment "
                    "and other tools remain. Undo can restore it.",
                    ["Cancel", "Delete assessment"],
                )
                != "Delete assessment"
            ):
                return
            try:
                self.app.session.change(
                    "Delete assessment",
                    lambda: delete_assessment(self.app.session.working, record),
                )
                self.render()
                self.app.update_project_actions()
            except Exception as error:
                await self.app.notify(str(error), error=True)

        async def transfer(event: ft.Event) -> None:
            """Open the shared destination picker for this exact saved source.

            Args:
                event: Copy/Move action.

            Returns:
                None.
            """
            await event.control.focus()
            await self.transfer(record)

        return self.app.card(
            [
                ft.Text(
                    record["context"],
                    size=17,
                    weight=ft.FontWeight.BOLD,
                    color="#0B3D60",
                ),
                ft.Row(
                    [
                        risk_badge(record),
                        ft.Text(
                            f"{len(record['source'].tasks)} tasks · {record['job']}"
                        ),
                    ],
                    wrap=True,
                ),
                ft.Row(
                    [
                        self.app.button(
                            "Open assessment",
                            ft.Icons.OPEN_IN_NEW,
                            open_record,
                            primary=True,
                        ),
                        self.app.button(
                            "Copy / Move…", ft.Icons.CONTENT_COPY, transfer
                        ),
                        self.app.button(
                            "Delete assessment", ft.Icons.DELETE_OUTLINE, remove
                        ),
                    ],
                    wrap=True,
                ),
            ]
        )

    def fill(self) -> None:
        """Refresh worker/tool controls and relevant-only saved hierarchy leaves.

        Args:
            None.

        Returns:
            None; empty and standalone-only workers remain explicit.
        """
        work = self.catalog["hierarchy"].work
        offered = filter_workers(work.workers, self.query, self.letter)
        if self.worker_id not in {w.worker_id for w in offered}:
            self.worker_id = offered[0].worker_id if offered else None
        self.filters.controls = [
            alphabet(
                {initial(w) for w in filter_workers(work.workers, self.query)},
                self.letter,
                self.choose_letter,
            ),
            ft.Row(
                [
                    ft.Dropdown(
                        label="Worker",
                        value=self.worker_id,
                        options=[
                            ft.DropdownOption(
                                w.worker_id,
                                f"{w.worker_id} · {w.first_name or ''} "
                                f"{w.last_name or ''}",
                            )
                            for w in offered
                        ],
                        on_select=self.select_worker,
                        width=420,
                    ),
                    ft.Dropdown(
                        label="Assessment tool",
                        value=self.kind.value,
                        options=[
                            ft.DropdownOption(
                                k.value,
                                n[1],
                                content=ft.Row(
                                    [
                                        ft.Image(src=n[2], width=28, height=28),
                                        ft.Text(n[0], size=16),
                                    ],
                                    tight=True,
                                ),
                            )
                            for k, n in TOOLS.items()
                        ],
                        on_select=self.select_tool,
                        width=390,
                    ),
                    self.app.button(
                        "Add assessment…", ft.Icons.ADD_LOCATION_ALT_OUTLINED, self.add
                    ),
                ],
                wrap=True,
            ),
        ]
        records = [
            r
            for r in self.catalog["records"]
            if r["worker"].worker_id == self.worker_id and r["owner"].kind is self.kind
        ]
        standalone = [self.card(r) for r in records if r["workplace"] is None]
        items = [
            (
                (
                    r["workplace"].plant_name,
                    r["workplace"].section_name,
                    r["workplace"].line_name,
                    r["workplace"].station_id,
                ),
                self.card(r),
            )
            for r in records
            if r["workplace"] is not None
        ]
        self.listing.controls = [
            ft.Text(
                f"{len(records)} saved {TOOLS[self.kind][0]} assessment(s)",
                weight=ft.FontWeight.BOLD,
            ),
            *standalone,
            *hierarchy_tree(items, self.expanded),
        ]
        if records and not standalone:
            self.listing.controls.insert(
                1,
                ft.Text(
                    "No standalone assessment for this worker/tool.",
                    size=15,
                    color="#53687A",
                ),
            )
        if not records:
            self.listing.controls.append(
                ft.Text(
                    "No assessment for this worker/tool. Add one here, or start "
                    "a standalone assessment from Home."
                )
            )

    async def add(self, event: ft.Event) -> None:
        """Choose a destination and explicitly confirm existing-data replacement.

        Args:
            event: Add assessment action.

        Returns:
            None; successful creation opens the exact new empty assessment.
        """
        await event.control.focus()

        async def selected(
            worker_id: str, workplace: WorkplaceContext | None, existing: dict | None
        ) -> None:
            """Accept a chosen destination after any required replacement consent.

            Args:
                worker_id: Exact selected worker.
                workplace: Real station/shift or standalone.
                existing: Exact target shown, or unoccupied destination.

            Returns:
                None; cancellation leaves the destination picker available.
            """
            if (
                existing
                and await self.app.choice(
                    "Replace assessment",
                    f"{worker_id} · {workplace_label(workplace)} already has "
                    f"{TOOLS[self.kind][0]} data "
                    f"({len(existing['source'].tasks)} tasks). "
                    "Replace it with one empty task? Undo can restore it.",
                    ["Cancel", "Replace assessment"],
                )
                != "Replace assessment"
            ):
                return
            identity = self.app.session.change(
                "Replace assessment" if existing else "Add assessment",
                lambda: create_assessment(
                    self.app.session.working,
                    worker_id,
                    self.kind,
                    workplace,
                    expected=existing,
                ),
            )
            self.app.page.pop_dialog()
            self.app.open_assessment_record(
                next(
                    r
                    for r in read_contexts(self.app.session.working)["records"]
                    if r["document"].document_id == identity
                )
            )

        DestinationPicker(self.app, self.worker_id, self.kind, selected).show()

    async def transfer(self, source: dict) -> None:
        """Choose Copy/Move then a target with explicit destructive consent.

        Args:
            source: Exact current-tool source with input/result snapshot.

        Returns:
            None; only this tool is transferred, never every tool implicitly.
        """
        mode = await self.app.choice(
            "Reuse assessment",
            f"{source['worker'].worker_id} · {source['context']} · "
            f"{TOOLS[source['owner'].kind][0]}. Copy keeps the original; "
            "Move removes it after the destination is written. "
            "Only this tool is included.",
            ["Cancel", "Copy assessment", "Move assessment"],
        )
        if mode == "Cancel":
            return
        move = mode == "Move assessment"

        async def selected(
            worker_id: str, workplace: WorkplaceContext | None, existing: dict | None
        ) -> None:
            """Confirm affected data, run one atomic transfer, then open its new owner.

            Args:
                worker_id: Exact selected destination worker.
                workplace: Station/shift or standalone destination.
                existing: Existing destination whose replacement needs approval.

            Returns:
                None; failures leave source and destination unchanged.
            """
            if existing or move:
                text = (
                    f"{'Move' if move else 'Copy'} "
                    f"{TOOLS[source['owner'].kind][0]} to {worker_id} · "
                    f"{workplace_label(workplace)}? "
                )
                text += (
                    "Existing destination inputs/results will be replaced. "
                    if existing
                    else ""
                )
                text += (
                    "The source assessment will be removed. "
                    if move
                    else "The source stays independent. "
                )
                if (
                    await self.app.choice(
                        "Confirm assessment transfer",
                        text + "Undo can restore the previous data.",
                        ["Cancel", "Transfer assessment"],
                    )
                    != "Transfer assessment"
                ):
                    return
            identity = self.app.session.change(
                "Move assessment" if move else "Copy assessment",
                lambda: transfer_assessment(
                    self.app.session.working,
                    source,
                    worker_id,
                    workplace,
                    move=move,
                    expected=existing,
                ),
            )
            self.app.page.pop_dialog()
            self.app.open_assessment_record(
                next(
                    r
                    for r in read_contexts(self.app.session.working)["records"]
                    if r["document"].document_id == identity
                )
            )

        DestinationPicker(
            self.app,
            source["worker"].worker_id,
            source["owner"].kind,
            selected,
            source=source,
        ).show()

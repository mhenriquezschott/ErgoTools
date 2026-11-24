"""Tablet workspace overview with source-bound assessment previews and clear actions.

Cards preview exact saved records; they never calculate, manufacture assessment data
or mutate a project. Large/tall layouts share the same responsive content hierarchy.
"""

from typing import TYPE_CHECKING

import flet as ft

if TYPE_CHECKING:
    from mobile_ui import TabletApp
from assessment_contexts import read_contexts
from assessment_tools import TOOLS
from mobile_results import BANDS
from project_session import project_info

from ergotools.domain.risk import classify_probability


def assessment_preview(app: "TabletApp", record: dict) -> ft.Container:
    """Present one real worker/context/result before the user opens its task editor.

    Args:
        app: Tablet composition root, providing shared controls/navigation.
        record: Exact native ownership/source/result projection.

    Returns:
        Touch card with a decorative anatomical preview and explicit saved-state text.
    """
    kind = record["owner"].kind
    result = record["result"]
    risk = result.probability_percent if result else None
    label, color = (
        BANDS[classify_probability(risk).value]
        if risk is not None
        else ("Not calculated", "#53687A")
    )
    worker = record["worker"]

    async def open_record(event: ft.Event) -> None:
        """Open this exact source; preview selection never reassigns ownership."""
        app.open_assessment_record(record)

    art = ft.Stack(
        [
            ft.Image(
                src="anatomy/body_00.png",
                width=180,
                height=210,
                fit=ft.BoxFit.COVER,
                opacity=0.24,
            ),
            ft.Image(
                src=f"anatomy/{kind.value}_00.png",
                width=180,
                height=210,
                color=color,
                color_blend_mode=ft.BlendMode.SRC_IN,
                opacity=0.65,
            ),
        ],
        width=180,
        height=210,
        right=0,
        top=0,
    )
    text = ft.Container(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Image(src=TOOLS[kind][2], width=28, height=28),
                        ft.Text(
                            TOOLS[kind][0],
                            weight=ft.FontWeight.BOLD,
                            size=17,
                            color="#0B3D60",
                        ),
                        ft.Text(
                            "Open",
                            size=14,
                            color="#067D8D",
                            weight=ft.FontWeight.W_600,
                        ),
                        ft.Icon(ft.Icons.ARROW_FORWARD, size=18, color="#067D8D"),
                    ]
                ),
                ft.Text(
                    f"{worker.worker_id} · {worker.first_name or ''} "
                    f"{worker.last_name or ''}",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color="#0B3D60",
                ),
                ft.Text(
                    record["context"],
                    size=14,
                    color="#405D70",
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    tooltip=record["context"],
                ),
                ft.Row(
                    [
                        ft.Container(
                            ft.Text(
                                f"{risk:.1f}%" if risk is not None else "—",
                                weight=ft.FontWeight.BOLD,
                                size=23,
                                color="#092C43",
                            ),
                            padding=ft.Padding(12, 6, 12, 6),
                            bgcolor=color if risk is not None else "#E6EDF2",
                            border_radius=10,
                        ),
                        ft.Text(
                            label, size=14, color="#294C63", weight=ft.FontWeight.W_600
                        ),
                    ],
                    wrap=True,
                ),
                ft.Text(
                    "Saved calculation"
                    if result
                    else "Draft · inputs can be completed later",
                    size=13,
                    color="#405D70",
                ),
            ],
            spacing=10,
        ),
        padding=18,
        right=76,
        left=0,
        top=0,
    )
    return ft.Container(
        ft.Stack([art, text], height=270),
        on_click=open_record,
        ink=True,
        tooltip="Open this saved assessment",
        bgcolor="#F1F7FA",
        border=ft.Border.all(1, "#DBE7EF"),
        border_radius=18,
        col={"xs": 12, "md": 6},
    )


def home_content(app: "TabletApp") -> list:
    """Build the current workspace, first-launch entry and recent-project disclosure.

    Args:
        app: Tablet shell; state and data remain read-only during composition.

    Returns:
        Responsive cards arranged by primary task rather than storage implementation.
    """
    controls = []
    if app.preference_store.warning:
        controls.append(ft.Text(app.preference_store.warning, color="#B3261E"))
    if app.session.active:
        info = project_info(app.session.working)
        records = read_contexts(app.session.working)["records"]
        chosen = app.session.active.get("selected_worker")
        offered = sorted(
            records,
            key=lambda r: (
                r["worker"].worker_id != chosen,
                r["owner"].kind is not app.selected_tool,
                r["workplace"] is not None,
                r["worker"].worker_id,
            ),
        )
        # Show different workers where possible, keeping the first preferred record.
        previews = []
        seen = set()
        for record in offered:
            if record["worker"].worker_id not in seen:
                previews.append(record)
                seen.add(record["worker"].worker_id)
            if len(previews) == 2:
                break
        controls.append(
            ft.Container(
                ft.Column(
                    [
                        ft.Text(
                            "YOUR WORKSPACE",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color="#067D8D",
                        ),
                        ft.Text(
                            info["title"],
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color="#0B3D60",
                        ),
                        ft.Text(
                            f"{info['workers']} workers  ·  {info['assessments']} "
                            f"assessments  ·  {info['units'].title()}",
                            size=16,
                            color="#405D70",
                        ),
                    ],
                    spacing=6,
                ),
                padding=ft.Padding(2, 6, 2, 8),
            )
        )
        left = app.card(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.ASSIGNMENT_OUTLINED, color="#078398"),
                        app.heading("Assessment desk"),
                    ]
                ),
                ft.Text(
                    "Preview a saved assessment or browse every worker and workplace.",
                    size=15,
                    color="#405D70",
                ),
                ft.Row(
                    [
                        app.button(
                            "Browse assessments",
                            ft.Icons.ACCOUNT_TREE_OUTLINED,
                            app.browse_assessments,
                            primary=True,
                        ),
                        app.button(
                            "Start / continue",
                            ft.Icons.PLAY_ARROW,
                            app.continue_assessment,
                            disabled=not info["workers"],
                        ),
                    ],
                    wrap=True,
                ),
                app.tool_choices(app.selected_tool, home=True),
                ft.ResponsiveRow(
                    [assessment_preview(app, r) for r in previews],
                    spacing=12,
                    run_spacing=12,
                ),
            ],
            col={"xs": 12, "lg": 8},
        )
        right = app.card(
            [
                app.heading("Manage project"),
                ft.Text(
                    "People, places and the time they work.", size=15, color="#405D70"
                ),
                app.button("Workers", ft.Icons.PEOPLE_OUTLINE, app.workers),
                app.button(
                    "Organization & shifts",
                    ft.Icons.ACCOUNT_TREE_OUTLINED,
                    app.organization,
                ),
                ft.Divider(color="#E0EAF0"),
                app.button("Open project…", ft.Icons.FOLDER_OPEN, app.open_file),
                app.button(
                    "Create project", ft.Icons.NOTE_ADD_OUTLINED, app.new_dialog
                ),
                app.button("Save As…", ft.Icons.SAVE_AS_OUTLINED, app.save_as),
                app.button("Close project", ft.Icons.CLOSE, app.close_project),
            ],
            col={"xs": 12, "lg": 4},
        )
        controls.append(ft.ResponsiveRow([left, right], spacing=18, run_spacing=18))
    else:
        controls.append(
            app.card(
                [
                    ft.Text(
                        "A clear view of work and risk.",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        color="#0B3D60",
                    ),
                    ft.Text(
                        "Assess lifting, upper-extremity effort and "
                        "shoulder tasks. Begin with your project, or "
                        "explore a complete example.",
                        size=18,
                        color="#405D70",
                    ),
                    ft.Row(
                        [
                            app.button(
                                "Open project…",
                                ft.Icons.FOLDER_OPEN,
                                app.open_file,
                                primary=True,
                            ),
                            app.button(
                                "Create project",
                                ft.Icons.NOTE_ADD_OUTLINED,
                                app.new_dialog,
                            ),
                            app.button(
                                "Open complete demo",
                                ft.Icons.SCIENCE_OUTLINED,
                                app.complete_demo,
                            ),
                        ],
                        wrap=True,
                    ),
                ]
            )
        )
    recents = []
    for item in app.session.state["recent"]:

        async def choose(event: ft.Event, identity: str = item["id"]) -> None:
            """Protect pending changes before restoring this exact private project."""
            if await app.guard():
                try:
                    app.session.open_recent(identity)
                    app.home()
                except Exception as error:
                    await app.notify(f"Could not open project: {error}", error=True)

        recents.append(
            ft.ListTile(
                leading=ft.Icon(ft.Icons.FOLDER_OUTLINED, color="#078398"),
                title=ft.Text(item["name"], weight=ft.FontWeight.W_600),
                subtitle=ft.Text(
                    item.get("origin", "Tablet project"),
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                on_click=choose,
                min_height=72,
            )
        )
    controls.append(
        ft.ExpansionTile(
            title=ft.Text("Recent projects", size=18, weight=ft.FontWeight.W_600),
            leading=ft.Icon(ft.Icons.HISTORY),
            controls=recents or [ft.Text("Your saved tablet projects appear here.")],
        )
    )
    if app.session.active:
        controls.append(
            ft.ExpansionTile(
                title=ft.Text("Example projects", size=18, weight=ft.FontWeight.W_600),
                leading=ft.Icon(ft.Icons.SCIENCE_OUTLINED),
                controls=[
                    ft.Text(
                        "Open a fresh example; existing work is protected "
                        "before switching."
                    ),
                    app.button(
                        "Open complete demo",
                        ft.Icons.SCIENCE_OUTLINED,
                        app.complete_demo,
                    ),
                ],
            )
        )
    return controls

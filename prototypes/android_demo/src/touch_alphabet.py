"""Reusable tablet alphabet navigation with touch-sized, horizontally swipable chips.

Only initials present in the offered catalog are enabled. The bar preserves Spanish
literal names while the caller supplies normalized initials. No hover-only behavior
is required on Android; tooltips support pointer use in the emulator.
"""

import string
from collections.abc import Awaitable, Callable

import flet as ft


def alphabet(
    available: set[str],
    selected: str,
    on_select: Callable[[str], Awaitable[None]],
    *,
    all_label: str = "All workers",
    group_label: str = "Last names",
) -> ft.Row:
    """Build a reusable scrolling initial selector without tiny compressed letters.

    Args:
        available: Normalized Latin initials in the currently searched catalog.
        selected: Active initial or All.
        on_select: Async browser action; caller retains its catalog and selection.
        all_label: Tooltip for the unfiltered choice in this catalog.
        group_label: Tooltip noun for enabled initials, such as task names.

    Returns:
        One swipable row with 44-logical-pixel targets and disabled empty letters.
    """

    async def choose(event: ft.Event) -> None:
        """Forward the tapped initial to the owning browser.

        Args:
            event: Button whose data holds the literal initial.

        Returns:
            None; filtering never mutates project data.
        """
        await on_select(event.control.data)

    return ft.Row(
        [
            ft.TextButton(
                letter,
                data=letter,
                width=54 if letter == "All" else 44,
                height=44,
                disabled=letter != "All" and letter not in available,
                tooltip=all_label
                if letter == "All"
                else f"{group_label} starting with {letter}",
                on_click=choose,
                style=ft.ButtonStyle(
                    bgcolor="#0B3D60" if letter == selected else "#F3F7FA",
                    color={
                        ft.ControlState.DEFAULT: "white"
                        if letter == selected
                        else "#0B3D60",
                        ft.ControlState.DISABLED: "#BCC8D1",
                    },
                ),
            )
            for letter in ("All", *string.ascii_uppercase)
        ],
        scroll=ft.ScrollMode.AUTO,
        spacing=3,
    )

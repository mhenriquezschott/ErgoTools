"""Small shared Android visual tokens: quiet secondary actions, clear primary actions.

Only presentation state is affected. Disabled controls intentionally recede without
elevation; touch targets remain at least 48 logical pixels in the host controls.
"""

from collections.abc import Callable

import flet as ft


def secondary_button_style() -> ft.ButtonStyle:
    """Return one flat accessible style for shared and directly composed buttons.

    Args:
        None.

    Returns:
        Fresh immutable-by-convention style with separate disabled colors.
    """
    return ft.ButtonStyle(
        elevation=0,
        bgcolor={
            ft.ControlState.DEFAULT: "#FFFFFF",
            ft.ControlState.DISABLED: "#F1F5F8",
        },
        color={ft.ControlState.DEFAULT: "#0B3D60", ft.ControlState.DISABLED: "#7B8E9C"},
        icon_color={
            ft.ControlState.DEFAULT: "#0B3D60",
            ft.ControlState.DISABLED: "#7B8E9C",
        },
        side={
            ft.ControlState.DEFAULT: ft.BorderSide(1, "#D9E4EC"),
            ft.ControlState.DISABLED: ft.BorderSide(1, "#E6EDF2"),
        },
        shape=ft.RoundedRectangleBorder(radius=12),
        padding=ft.Padding(16, 10, 16, 10),
    )


def action_button(
    content: str | ft.Control,
    *,
    icon: str | ft.IconData | None = None,
    on_click: Callable[[ft.Event], object] | None = None,
    height: int = 48,
    disabled: bool = False,
    visible: bool = True,
    tooltip: str | None = None,
    style: ft.ButtonStyle | None = None,
    bgcolor: str | None = None,
    color: str | None = None,
    data: object = None,
) -> ft.OutlinedButton:
    """Compose a genuinely flat Material action instead of an elevated-button variant.

    Args:
        content: Text or accessible control label.
        icon: Existing app/Material icon beside that label.
        on_click: Host-owned synchronous or asynchronous event callback.
        height: Logical touch-target height, normally 48 pixels.
        disabled: Unavailable actions retain quiet, shadow-free styling.
        visible: Whether the host offers this action in the current state.
        tooltip: Optional specific explanation of purpose.
        style: Explicit host overrides, merged with the shared defaults.
        bgcolor: Optional selected/primary surface, preserving disabled semantics.
        color: Optional enabled foreground; primary controls use white.
        data: Detached handler identity; never persisted by this component.

    Returns:
        OutlinedButton with no elevation, including colored primary/selected surfaces.
    """
    combined = secondary_button_style()
    if style:
        for name in style.__dataclass_fields__:
            value = getattr(style, name)
            if value is not None:
                setattr(combined, name, value)
    if bgcolor:
        combined.bgcolor = {
            ft.ControlState.DEFAULT: bgcolor,
            ft.ControlState.DISABLED: "#F1F5F8",
        }
        combined.side = {
            ft.ControlState.DEFAULT: ft.BorderSide(1, bgcolor),
            ft.ControlState.DISABLED: ft.BorderSide(1, "#E6EDF2"),
        }
    if color:
        combined.color = {
            ft.ControlState.DEFAULT: color,
            ft.ControlState.DISABLED: "#7B8E9C",
        }
        combined.icon_color = {
            ft.ControlState.DEFAULT: color,
            ft.ControlState.DISABLED: "#7B8E9C",
        }
    combined.elevation = 0
    return ft.OutlinedButton(
        content,
        icon=icon,
        on_click=on_click,
        height=height,
        disabled=disabled,
        visible=visible,
        tooltip=tooltip,
        style=combined,
        data=data,
    )

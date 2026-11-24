"""Android tablet worker-assessment demo entry point.

Native project lifecycle, workers, three tools, context reuse and personal settings
are composed in a touch frontend; formulas/storage remain shared with the desktop.
"""

import asyncio
import json
import os
import traceback
from pathlib import Path

import flet as ft
from demo_service import compatibility_probe
from mobile_ui import TabletApp
from project_session import ProjectSession
from tablet_style import secondary_button_style


async def main(page: ft.Page) -> None:
    """Start a recoverable tablet project workspace with visible startup failures.

    Args:
        page: Flet Android surface, including system document picker services.

    Returns:
        None; all native connections are scoped to adapter operations.
    """
    folder = Path(
        os.environ.get(
            "FLET_APP_STORAGE_DATA", str(Path.home() / ".ergotools-tablet-test")
        )
    )
    folder.mkdir(parents=True, exist_ok=True)
    page.title = "ErgoTools"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(
        color_scheme_seed="#078398",
        button_theme=ft.ButtonTheme(style=secondary_button_style()),
    )
    page.bgcolor = "#F3F7FA"
    page.padding = 0
    try:
        session = ProjectSession(folder)
        app = TabletApp(page, session)
        app.home()
        # Keep the existing reproducible runtime probe off the first-frame path.
        probe = await asyncio.to_thread(compatibility_probe, folder)
        print(
            json.dumps({"event": "ergotools_android_ready", "probe": probe}), flush=True
        )
    except Exception as error:
        detail = traceback.format_exc()
        (folder / "startup_error.txt").write_text(detail)
        page.add(
            ft.SafeArea(
                ft.Column(
                    [
                        ft.Text("Unable to open ErgoTools", size=24),
                        ft.Text(str(error)),
                        ft.Text(detail, selectable=True),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                ),
                expand=True,
            )
        )
        print(detail, flush=True)


if __name__ == "__main__":
    ft.run(main)

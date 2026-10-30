"""Checkout launcher platform defaults and unchanged argument forwarding.

Tooling tests substitute a disposable interpreter executable. No GUI, dependency
installation or operational project is involved; native OS acceptance is separate.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("platform", (None, "xcb", "wayland", "offscreen"))
def test_linux_launcher_defaults_to_xcb_and_respects_explicit_backend(
    tmp_path: Path,
    platform: str | None,
) -> None:
    """Only default/XCB launches remove the redundant Wayland session warning input.

    Args:
        tmp_path: Disposable checkout/interpreter directory.
        platform: Explicit Qt override, or None for the launcher's Linux default.

    Returns:
        None; arguments retain spaces and the correct per-process environment arrives.
    """
    root = tmp_path / "checkout with spaces"
    (root / "tools").mkdir(parents=True)
    (root / ".venv/bin").mkdir(parents=True)
    shutil.copy2("tools/run.sh", root / "tools/run.sh")
    executable = root / ".venv/bin/python"
    executable.write_text(
        "#!/usr/bin/env python3\nimport os,sys,json\n"
        "print(json.dumps([sys.argv[1:],os.getenv('QT_QPA_PLATFORM'),"
        "os.getenv('XDG_SESSION_TYPE')]))\n"
    )
    executable.chmod(0o755)
    environment = dict(os.environ, XDG_SESSION_TYPE="wayland")
    if platform is None:
        environment.pop("QT_QPA_PLATFORM", None)
    else:
        environment["QT_QPA_PLATFORM"] = platform
    result = subprocess.run(
        [
            "bash",
            str(root / "tools/run.sh"),
            "a project.ergprj",
            "--settings",
            "my settings.json",
        ],
        env=environment,
        text=True,
        capture_output=True,
        check=True,
    )
    arguments, backend, session = json.loads(result.stdout)
    assert arguments == [
        "-m",
        "ergotools.launcher",
        "a project.ergprj",
        "--settings",
        "my settings.json",
    ]
    assert backend == (platform or "xcb")
    assert session == (None if platform in (None, "xcb") else "wayland")

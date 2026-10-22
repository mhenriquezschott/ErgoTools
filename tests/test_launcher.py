"""Installed integrated entry point never depends on the launch directory.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from ergotools.launcher import main


@pytest.mark.parametrize(
    "arguments", [[], ["--disable-vtk"], ["a project with spaces.ergprj"]]
)
def test_launch_uses_integrated_ui_and_user_config(
    tmp_path: Path, arguments: list[str]
) -> None:
    """Integrated rendering is default and explicit diagnostic options pass through.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        arguments: Explicit test command-line arguments passed without a shell.

    Returns:
        None.
    """
    with (
        patch(
            "ergotools.bootstrap.QStandardPaths.writableLocation",
            return_value=str(tmp_path),
        ),
        patch("ergotools.launcher.desktop_main", return_value=7) as desktop,
    ):
        assert main(arguments) == 7
    desktop.assert_called_once_with(
        [
            "--integrated-preview",
            *arguments,
            "--settings",
            str(tmp_path / "settings.json"),
        ]
    )
    assert not (tmp_path / "settings.json").exists()


@pytest.mark.parametrize(
    "arguments", [["--settings", "custom.json"], ["--settings=custom.json"]]
)
def test_explicit_settings_are_preserved(arguments: list[str]) -> None:
    """Retain explicit settings and caller arguments.

    Args:
        arguments: Explicit test command-line arguments passed without a shell.

    Returns:
        None.
    """
    before = list(arguments)
    with patch("ergotools.launcher.desktop_main", return_value=0) as desktop:
        main(arguments)
    assert arguments == before
    desktop.assert_called_once_with(["--integrated-preview", *arguments])


def test_unavailable_config_path_fails_before_launch() -> None:
    """Fail without creating preferences beside projects.

    Args:
        None.

    Returns:
        None.
    """
    with (
        patch("ergotools.bootstrap.QStandardPaths.writableLocation", return_value=""),
        patch("ergotools.launcher.desktop_main") as desktop,
        pytest.raises(OSError, match="configuration directory"),
    ):
        main([])
    desktop.assert_not_called()

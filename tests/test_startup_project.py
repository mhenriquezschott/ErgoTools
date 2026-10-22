"""Positional startup paths share Open, cancellation and recent-history policy.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from collections.abc import Callable
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.bootstrap import main
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_saved_tool_data import window as window


@pytest.mark.parametrize("case", ["open", "missing"])
def test_startup_project_uses_real_open_and_recent_history(
    window: LifftWindow, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    """Relative spaced paths open after show; errors never add recents.

    Startup owns theme installation; those setup calls are isolated from the mocked
    QApplication. Real theme behavior is covered by the owned-dialog/widget tests.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        monkeypatch: Pytest patch fixture; environment/adapter substitutions are
            restored after the test.
        case: Frozen reference case or parametrized scenario whose expected outcome is
            asserted here.

    Returns:
        None.
    """
    workspace = window.presenter.workspace
    source = Path(workspace.location)
    target = tmp_path / "project with spaces.ergprj"
    workspace.backup(str(target))
    workspace.close(choice=CloseChoice.DISCARD)
    window.refresh()
    store = window._settings_store
    assert store is not None
    store.save(store.load().clear_recent())
    if case == "missing":
        target.unlink()
        label = ""
    else:
        label = window.document_options(str(target), window.language)[0][1]
    monkeypatch.chdir(tmp_path)
    scheduled: list[Callable[[], None]] = []

    def schedule(delay: int, callback: Callable[[], None]) -> None:
        """Assert startup Open is queued with zero delay and retain its callback.

        Assert startup Open is queued with zero delay and retain its callback for the
        controlled GUI loop.

        Args:
            delay: Requested startup callback delay in milliseconds; this scenario
                requires zero.
            callback: Scheduled startup operation retained and executed once by the
                controlled event loop.

        Returns:
            None.
        """
        assert delay == 0
        scheduled.append(callback)

    def event_loop() -> int:
        """Assert the real main window is shown.

        Assert the real main window is shown before executing the one queued
        project-open operation.

        Args:
            None.

        Returns:
            Zero (successful controlled event-loop exit) after executing the one
            scheduled startup Open.
        """
        assert window.isVisible() and len(scheduled) == 1
        scheduled[0]()
        return 0

    app = Mock()
    app.exec.side_effect = event_loop
    with (
        patch("ergotools.bootstrap.QApplication", return_value=app),
        patch("ergotools.bootstrap.install_menu_icon_style") as menu_style,
        patch("ergotools.bootstrap.install_dialog_theme") as dialog_theme,
        patch("ergotools.bootstrap.create_window", return_value=window),
        patch("ergotools.bootstrap.QTimer.singleShot", side_effect=schedule),
        patch.object(window, "choose_item", return_value=(label, case == "open")),
    ):
        assert main(["--integrated-preview", str(target.relative_to(tmp_path))]) == 0
    menu_style.assert_called_once_with(app)
    dialog_theme.assert_called_once_with(app)
    if case == "open":
        assert window.assessment_navigation.view.worker_id == "w"
        assert workspace.location == str(target)
        assert workspace.active is not None
        assert store.load().recent_documents == (str(target),)
        window.refresh_recent_projects()
        assert window._assessment_menu.recent.actions()[0].data() == str(target)
    else:
        assert workspace.location is None and workspace.active is None
        assert store.load().recent_documents == ()
        if case == "missing":
            assert window.message.text() == window.text("error")
    assert source.exists()


@pytest.mark.parametrize("option", ["--job-management-demo", "--job-management"])
def test_startup_rejects_conflicting_diagnostic_target(option: str) -> None:
    """Reject ambiguous projects before creating a GUI or opening either file.

    Args:
        option: Named parametrized command/setting whose acceptance policy is asserted.

    Returns:
        None.
    """
    arguments = ["normal.ergprj", option]
    if option == "--job-management":
        arguments.append("diagnostic.ergprj")
    with patch("ergotools.bootstrap.QApplication") as app, pytest.raises(SystemExit):
        main(arguments)
    app.assert_not_called()

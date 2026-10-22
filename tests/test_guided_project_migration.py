"""Focused M2 desktop consent, failure and first-save lifecycle regressions.

Tests use disposable native/original fixtures and the approved Qt environment. Real
dialog buttons exercise cancellation and errors; process-backed cases verify temporary
ownership, failed first Save and no converter access on native reopen. No operational
project or reference checkout is modified.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import shlex
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QDialog, QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.infrastructure.project_migration import ExternalProjectMigration
from ergotools.infrastructure.settings_store import JsonSettingsStore
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.project_migration_dialog import (
    ProjectMigrationDialog,
)
from tests.test_desktop_legacy_open import accept_migration as accept_migration
from tests.test_legacy_catalogs import legacy_catalog as legacy_catalog
from tests.test_legacy_plot import mapped as mapped
from tests.test_legacy_reconciliation import old_source as old_source
from tests.test_legacy_rotations import rotated as rotated
from tests.test_main_navigation import window as window


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("action", ["migrate", "cancel", "failure", "dirty-cancel"])
def test_guided_buttons_and_failure(
    window: LifftWindow,
    language: Language,
    action: str,
) -> None:
    """Use actual modal buttons to exercise consent, rejection and visible errors.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.
        action: Injected operation or named action selected for reentrancy/dirty-consent
            testing.

    Returns:
        None.
    """
    calls = []

    def convert() -> bool:
        """Record one explicit attempt and simulate its process outcome.

        Args:
            None.

        Returns:
            Controlled external conversion outcome selected by the test; no unconsented
            retry is performed.

        Raises:
            FileNotFoundError: The explicit controlled error named by this
                fault-injection callback is reached.
        """
        calls.append(action)
        if action == "failure":
            raise FileNotFoundError("missing migration utility")
        return action != "dirty-cancel"

    dialog = ProjectMigrationDialog(
        language, "python tool.py input --output new.ergprj", convert, parent=window
    )

    def click() -> None:
        """Activate the real button and dismiss a visible failure afterwards.

        Args:
            None.

        Returns:
            None.
        """
        if action == "cancel":
            dialog.cancel_button.click()
        else:
            dialog.migrate_button.click()
            if action == "failure":
                assert dialog.error.isVisible()
                assert "missing migration utility" in dialog.error.text()
                assert not dialog.migrate_button.isEnabled()
                dialog.cancel_button.click()

    QTimer.singleShot(0, click)
    assert dialog.exec() == (
        QDialog.Accepted if action == "migrate" else QDialog.Rejected
    )
    assert calls == ([] if action == "cancel" else [action])
    assert dialog.command.isReadOnly() and dialog.command.toPlainText()
    assert (
        "actualizar" if language is Language.SPANISH else "upgrade"
    ) in dialog.windowTitle()
    dialog.deleteLater()


def test_command_guidance_quotes_literal_paths() -> None:
    """CLI guidance reconstructs the exact arguments used without a shell.

    Args:
        None.

    Returns:
        None.
    """
    adapter = ExternalProjectMigration(("/tool path/python", "/tool path/migrate.py"))
    source = "/project's folder/source $(literal).ergprj"
    destination = "/new folder/output.ergprj"
    assert shlex.split(adapter.command_line(source, destination)) == [
        *adapter.command,
        source,
        "--output",
        destination,
    ]


@pytest.mark.usefixtures("accept_migration")
def test_first_save_failure_and_clean_converted_close_consent(
    window: LifftWindow,
    mapped: Path,
    old_source: Path,
    rotated: Path,
    tmp_path: Path,
) -> None:
    """Retain unsaved conversion after cancelled/conflicting Save and close Cancel.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.
        old_source: Disposable original-format fixture containing unversioned LiFFT rows
            and exact saved ownership.
        rotated: Disposable original-format fixture containing frozen
            JROT/profile/assignment links.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    assert mapped == old_source == rotated
    with patch.object(
        window, "choose_item", side_effect=lambda _, __, ids: (ids[0], True)
    ):
        window.open_project_location(str(mapped))
    backing = Path(window.presenter.workspace.location)
    assert (
        window._is_unsaved_project() and not window.presenter.workspace.active.is_dirty
    )
    with patch.object(window, "choose_file", return_value=""):
        window.save_project()
    assert window._is_unsaved_project() and backing.exists()
    existing = tmp_path / "existing.ergprj"
    existing.write_bytes(b"preserve")
    with patch.object(window, "choose_file", return_value=str(existing)):
        window.save_project()
    assert existing.read_bytes() == b"preserve" and backing.exists()

    def cancel_close() -> None:
        """Cancel the actual dirty-consent dialog even though assessment is clean.

        Args:
            None.

        Returns:
            None.
        """
        dialog = window.findChild(QMessageBox)
        assert dialog is not None
        button = next(b for b in dialog.buttons() if b.text() == window.text("cancel"))
        button.click()

    QTimer.singleShot(0, cancel_close)
    window.close_project()
    assert window._is_unsaved_project() and backing.exists()
    assert (
        str(backing)
        not in JsonSettingsStore(tmp_path / "settings.json").load().recent_documents
    )
    with patch.object(window, "dirty_choice", return_value=CloseChoice.DISCARD):
        window.close_project()
    assert not backing.exists()


@pytest.mark.usefixtures("accept_migration")
def test_failed_first_save_keeps_temporary_project(
    window: LifftWindow,
    mapped: Path,
    old_source: Path,
    rotated: Path,
    tmp_path: Path,
) -> None:
    """A publication error retains the converted data for retry instead of losing it.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.
        old_source: Disposable original-format fixture containing unversioned LiFFT rows
            and exact saved ownership.
        rotated: Disposable original-format fixture containing frozen
            JROT/profile/assignment links.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    assert mapped == old_source == rotated
    with patch.object(
        window, "choose_item", side_effect=lambda _, __, ids: (ids[0], True)
    ):
        window.open_project_location(str(mapped))
    workspace = window.presenter.workspace
    active, location = workspace.active, workspace.location
    destination = tmp_path / "failed-save.ergprj"
    with (
        patch.object(window, "choose_file", return_value=str(destination)),
        patch.object(window, "choose_project_details", return_value=("Converted", "")),
        patch.object(workspace, "save_as", side_effect=OSError("disk full")),
        pytest.raises(OSError, match="disk full"),
    ):
        window.save_project()
    assert workspace.active is active and workspace.location == location
    assert Path(location).exists() and window._is_unsaved_project()
    assert not destination.exists()

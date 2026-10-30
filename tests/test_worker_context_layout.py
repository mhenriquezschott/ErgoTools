"""Worker/context layout and project-local disclosure persistence contracts.

Test layer. Real widgets and disposable native databases distinguish accepted private
preferences from Main Save. Existing scientific sources/results stay untouched.
"""

import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QPoint
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.domain.display_precision import DisplayPrecision
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.lifft_store import StoreFormatError
from ergotools.infrastructure.project_preferences_store import (
    read_context_expanded,
    write_display_settings,
)
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_main_navigation import window as window
from tests.test_unified_project_save import editing_workspace


@pytest.mark.parametrize("language", list(Language))
def test_worker_layout_disclosure_and_shared_history(
    window: LifftWindow, language: Language
) -> None:
    """Compact navigation stays beside the selector; nested disclosure retains sources.

    Args:
        window: Integrated disposable project with classified workers.
        language: Both supported UI languages must fit the existing window width.

    Returns:
        None; Undo/Redo restores disclosure without warning or modifying task data.
    """
    window.languages.setCurrentIndex(list(Language).index(language))
    window.resize(1550, 1015)
    app = QApplication.instance()
    assert app is not None
    app.processEvents()
    nav = window.main_navigation
    assert nav is not None and "refresh" not in nav.buttons
    assert not hasattr(nav, "context_toggle")
    browser = nav.location_browser
    assert not nav.context_frame.isVisible()  # New/unset projects start collapsed.
    nav.context_disclosure.click()
    QTest.qWait(230)
    assert browser.isVisible() and browser.isEnabled()
    assert not hasattr(nav, "follow_worker_button")
    controls = [
        nav.order_button,
        *nav.nav_buttons,
        nav.buttons["workers"],
        nav.buttons["search"],
        nav.buttons["transfer"],
        nav.standalone_button,
    ]
    positions = [button.mapTo(window, QPoint()).x() for button in controls]
    assert positions == sorted(positions)
    assert all(button.height() == 36 and button.isVisible() for button in controls)
    assert nav.context_disclosure.height() == 28
    assert (
        nav.context_disclosure.mapTo(window, QPoint()).y()
        > nav.standalone_button.mapTo(window, QPoint()).y()
    )
    top = nav.workers.mapTo(window, nav.workers.rect().center()).y()
    assert all(
        button.mapTo(window, button.rect().center()).y() == top for button in controls
    )
    assert (
        nav.context_frame.mapTo(window, QPoint()).y()
        > nav.alphabet.mapTo(window, QPoint()).y()
    )
    before = window.presenter.workspace.active.state
    document = window.presenter.workspace.active.document
    body_top = window.body_panel.mapTo(window, QPoint()).y()
    actions = window.history_actions
    assert actions is not None
    nav.context_disclosure.setChecked(False)
    QTest.qWait(230)
    assert not nav.context_frame.isVisible()
    app.processEvents()
    assert window.body_panel.mapTo(window, QPoint()).y() < body_top
    with patch.object(
        QMessageBox, "question", side_effect=AssertionError("unexpected warning")
    ):
        actions.replay(redo=False)
        assert nav.context_frame.isVisible()
        actions.replay(redo=True)
        assert not nav.context_frame.isVisible()
    assert window.presenter.workspace.active.state == before
    assert window.presenter.workspace.active.document == document


@pytest.mark.parametrize("expanded", [False, True])
def test_disclosure_save_reopen_and_display_update(
    tmp_path: Path, expanded: bool
) -> None:
    """Disclosure is private until Main Save and survives precision changes/reopen.

    Args:
        tmp_path: Disposable native project and personal settings directory.
        expanded: Both explicit states, including False distinct from old defaults.

    Returns:
        None; project bytes stay unchanged before Save and reopening is read-only.
    """
    workspace = editing_workspace(tmp_path)
    path = Path(workspace.location)
    original = path.read_bytes()
    try:
        metadata = workspace.project_metadata
        assert metadata is not None and metadata.assessment_context_expanded is None
        workspace.update_display_settings(
            replace(metadata, assessment_context_expanded=expanded)
        )
        assert workspace.has_unsaved_changes and path.read_bytes() == original
        metadata = workspace.project_metadata
        workspace.update_display_settings(
            replace(metadata, precision=DisplayPrecision(inputs=2))
        )
        assert workspace.save()
        assert not workspace.has_unsaved_changes
    finally:
        workspace.close(choice=CloseChoice.DISCARD)
    saved = path.read_bytes()
    with AssessmentProjectFile.open(path) as project:
        assert project.metadata.assessment_context_expanded is expanded
        assert project.metadata.precision.inputs == 2
    assert path.read_bytes() == saved


def test_disclosure_save_as_and_backup_keep_distinct_baselines(tmp_path: Path) -> None:
    """Backup retains durable intent; Save As includes the private changed choice.

    Args:
        tmp_path: Disposable native original, backup and Save As destinations.

    Returns:
        None; original stays unchanged and copied metadata includes explicit False.
    """
    workspace = editing_workspace(tmp_path)
    original = Path(workspace.location).read_bytes()
    try:
        workspace.update_display_settings(
            replace(workspace.project_metadata, assessment_context_expanded=False)
        )
        backup, copied = tmp_path / "backup.ergprj", tmp_path / "copy.ergprj"
        assert workspace.backup(str(backup)).completed
        with AssessmentProjectFile.open(backup) as project:
            assert project.metadata.assessment_context_expanded is None
        assert workspace.save_as(str(copied)).completed
        with AssessmentProjectFile.open(copied) as project:
            assert project.metadata.assessment_context_expanded is False
        assert (tmp_path / "workflow.ergprj").read_bytes() == original
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_old_settings_read_only_and_invalid_disclosure_rejected() -> None:
    """Optional column is lazy and strict; invalid write intent changes no record.

    Args:
        None.

    Returns:
        None; old precision-only tables retain their exact SQL until explicit choice.
    """
    with closing(sqlite3.connect(":memory:")) as connection:
        assert read_context_expanded(connection) is None
        assert connection.execute("SELECT name FROM sqlite_master").fetchall() == []
        write_display_settings(connection, DisplayPrecision())
        schema = connection.execute("SELECT sql FROM sqlite_master").fetchall()
        assert read_context_expanded(connection) is None
        assert connection.execute("SELECT sql FROM sqlite_master").fetchall() == schema
        with pytest.raises(ValueError, match="disclosure"):
            write_display_settings(connection, DisplayPrecision(), "yes")
        assert connection.execute("SELECT sql FROM sqlite_master").fetchall() == schema
        write_display_settings(connection, DisplayPrecision(), False)
        assert read_context_expanded(connection) is False
        write_display_settings(connection, DisplayPrecision(), True)
        assert read_context_expanded(connection) is True
        write_display_settings(connection, DisplayPrecision(), None)
        assert read_context_expanded(connection) is None
        connection.execute("PRAGMA ignore_check_constraints = ON")
        connection.execute("UPDATE project_display_settings SET context_expanded = 2")
        with pytest.raises(StoreFormatError, match="disclosure"):
            read_context_expanded(connection)
        connection.execute("DELETE FROM project_display_settings")
        with pytest.raises(StoreFormatError, match="disclosure"):
            read_context_expanded(connection)


@pytest.mark.parametrize("index", range(3))
def test_disclosure_preserves_invalid_pending_tool_text(
    window: LifftWindow, index: int
) -> None:
    """Toggling the browser never validates/discards the active tool's unfinished input.

    Args:
        window: Disposable integrated assessment window.
        index: LiFFT, DUET and ST use the same non-destructive disclosure contract.

    Returns:
        None; input widget identity/text and accepted scientific state stay intact.
    """
    window.assessment_tabs.setCurrentIndex(index)
    panel = window.task_panel if index == 0 else window.secondary_panel()
    field = panel.inputs[0][0 if index == 0 else 1]
    before = window.presenter.workspace.active.state
    field.setText("bad")
    field.textEdited.emit("bad")
    nav = window.main_navigation
    nav.context_disclosure.setChecked(not nav.context_disclosure.isChecked())
    assert field.text() == "bad"
    assert window.presenter.workspace.active.state == before
    assert (window.task_panel if index == 0 else window.secondary_panel()) is panel


def test_disclosure_failure_restores_visibility(window: LifftWindow) -> None:
    """Failed preference acceptance rolls the chevron/panel back to accepted intent.

    Args:
        window: Integrated project with an initially collapsed organization path.

    Returns:
        None; an adapter error never creates a contradictory checked/visible state.
    """
    nav = window.main_navigation
    assert not nav.context_disclosure.isChecked()
    with patch.object(
        window.presenter.workspace,
        "update_display_settings",
        side_effect=OSError("test failure"),
    ):
        nav.context_disclosure.click()
    assert not nav.context_disclosure.isChecked() and not nav.context_frame.isVisible()
    assert (
        window.presenter.workspace.project_metadata.assessment_context_expanded is None
    )


@pytest.mark.parametrize("expanded", [False, True])
def test_main_save_reopen_restores_disclosure(
    window: LifftWindow, expanded: bool
) -> None:
    """Actual Main Save and project Open restore either explicit disclosure state.

    Args:
        window: Integrated disposable project with real organization and assessments.
        expanded: Both expanded and collapsed states persist independently of defaults.

    Returns:
        None; reopening restores the chevron and panel together without dirtying data.
    """
    nav = window.main_navigation
    nav.context_disclosure.setChecked(not expanded)
    nav.context_disclosure.setChecked(expanded)
    window.save_project()
    path = window.presenter.workspace.location
    window.presenter.workspace.close(choice=CloseChoice.DISCARD)
    window.open_project_location(path)
    assert nav.context_disclosure.isChecked() is expanded
    assert nav.context_frame.isVisible() is expanded
    assert not window.presenter.workspace.has_unsaved_changes


def test_closed_project_disables_and_collapses_disclosure(window: LifftWindow) -> None:
    """Closing a project removes its optional context even when it was expanded.

    Args:
        window: Integrated disposable project with organization and saved sources.

    Returns:
        None; no project-dependent disclosure remains actionable in the empty window.
    """
    window.presenter.workspace.close(choice=CloseChoice.DISCARD)
    window.refresh()
    nav = window.main_navigation
    assert not nav.context_disclosure.isEnabled()
    assert not nav.context_disclosure.isChecked()
    assert not nav.context_frame.isVisible()


@pytest.mark.parametrize("expanded", [False, True])
def test_context_moves_only_after_preference_acceptance(
    window: LifftWindow, expanded: bool
) -> None:
    """An accepted browser preference changes only after its private edit completes.

    Args:
        window: Disposable integrated project with native layout and shared history.
        expanded: Expansion and collapse both avoid an early move during persistence.

    Returns:
        None; geometry stays fixed during acceptance, then animates to the new state.
    """
    nav = window.main_navigation
    nav.context_disclosure.setChecked(not expanded)
    QTest.qWait(230)
    app = QApplication.instance()
    assert app is not None
    app.processEvents()
    old_geometry = window.body_panel.geometry()
    original = window.presenter.workspace.update_display_settings

    def accept(metadata: ProjectMetadata) -> None:
        """Assert no intermediate layout while the existing preference port runs.

        Args:
            metadata: Original validated metadata forwarded without modification.

        Returns:
            None after the real private project mutation completes.
        """
        assert nav.context_frame.isVisible() is not expanded
        assert window.body_panel.geometry() == old_geometry
        original(metadata)
        assert nav.context_frame.isVisible() is not expanded
        assert window.body_panel.geometry() == old_geometry

    with patch.object(
        window.presenter.workspace, "update_display_settings", side_effect=accept
    ) as update:
        nav.context_disclosure.click()
    update.assert_called_once()
    QTest.qWait(230)
    assert nav.context_frame.isVisible() is expanded
    assert window.body_panel.geometry() != old_geometry
    assert window.updatesEnabled()


@pytest.mark.parametrize("ancestor", [False, True])
def test_context_projection_preserves_outer_update_suspension(
    window: LifftWindow, ancestor: bool
) -> None:
    """Nested host layout batches retain ownership of their disabled update state.

    Args:
        window: Disposable integrated window with nested context content.
        ancestor: Suspend the main window instead of the root to check inherited state.

    Returns:
        None; disclosure projection neither enables nor permanently disables children.
    """
    nav = window.main_navigation
    root = nav.context_frame.parentWidget()
    assert root is not None
    owner = window if ancestor else root
    owner.setUpdatesEnabled(False)
    try:
        nav.update_context_visibility("project", Language.ENGLISH, False)
        assert not nav.context_frame.isVisible()
        assert not root.updatesEnabled()
        nav.update_context_visibility("project", Language.ENGLISH, True)
        assert nav.location_browser.isVisible()
        assert not root.updatesEnabled()
    finally:
        owner.setUpdatesEnabled(True)
    assert root.updatesEnabled()


def test_disclosure_keeps_static_rows_fixed_without_repopulating(
    window: LifftWindow,
) -> None:
    """Disclosure only animates the lower browser; alphabet/status stay in place.

    Args:
        window: Disposable integrated native Qt window with saved workplace data.

    Returns:
        None; selectors are not rebuilt, row positions stay fixed and Undo/Save enable.
    """
    nav = window.main_navigation
    frames: list[tuple[int, int]] = []

    def record(_value: object) -> None:
        """Observe upper-row positions during the lower browser's height animation.

        Args:
            _value: Qt animated height; source data is not inspected or mutated.

        Returns:
            None; append positions in main-window coordinates.
        """
        frames.append(
            (
                nav.alphabet.mapTo(window, QPoint()).y(),
                nav.location_browser.summary.mapTo(window, QPoint()).y(),
            )
        )

    nav.context_frame.animation.valueChanged.connect(record)
    with patch.object(nav, "_populate", side_effect=AssertionError("selector rebuild")):
        nav.context_disclosure.click()
        QTest.qWait(230)
    assert len(frames) > 2 and len(set(frames)) == 1
    assert nav.toolbar_actions["undo"].isEnabled()
    assert nav.toolbar_actions["save"].isEnabled()
    assert "Modified" in nav.project_label.text()
    assert nav.alphabet.height() == 28
    gap = nav.alphabet.mapTo(window, QPoint()).y() - (
        nav.workers.mapTo(window, QPoint()).y() + nav.workers.height()
    )
    assert 0 <= gap <= 4

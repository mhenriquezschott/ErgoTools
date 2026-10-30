"""Recent-project and Close menu workflows use existing lifecycle/settings policy.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import shutil
from html import escape
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.settings_store import JsonSettingsStore
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_saved_tool_data import KINDS
from tests.test_saved_tool_data import window as window


@pytest.mark.parametrize("index", [0, 1, 2])
def test_close_invalid_cancel_save_reopen_discard(
    window: LifftWindow, index: int
) -> None:
    """Close respects invalid input, Cancel, Save and Discard.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        index: Zero-based selected input/row/case index used by the parametrized
            regression.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(index)
    workspace = window.presenter.workspace
    active = workspace.active
    path = Path(workspace.location)
    panel = window.task_panel if index == 0 else window.secondary_panel()
    field = panel.inputs[0][2 if index == 0 else -1]
    field.setText("bad")
    field.textEdited.emit("bad")
    close = window._assessment_menu.close_project_action
    with patch.object(window, "dirty_choice") as choice:
        close.trigger()
    choice.assert_not_called()
    assert workspace.active is active and field.text() == "bad"
    field.setText("350")
    field.textEdited.emit("350")
    with patch.object(window, "dirty_choice", return_value=CloseChoice.CANCEL):
        close.trigger()
    assert workspace.active is active and workspace.has_unsaved_changes
    with patch.object(window, "dirty_choice", return_value=CloseChoice.SAVE):
        close.trigger()
    assert (
        workspace.active is None and workspace.location is None and window.isVisible()
    )
    assert not close.isEnabled() and not window.results_sidebar.risk_gauge.has_value
    with AssessmentProjectFile.open(path) as project:
        assert project.load(active.document).tasks[0].repetitions == 350
    with patch.object(
        window,
        "choose_item",
        return_value=(
            next(
                label
                for identity, label in window.document_options(
                    str(path), window.language
                )
                if identity == f"{KINDS[index]}-1"
            ),
            True,
        ),
    ):
        window.open_recent_project(str(path))
    window.assessment_tabs.setCurrentIndex(index)
    assert workspace.active.state.tasks[0].repetitions == 350 and close.isEnabled()
    panel = window.task_panel if index == 0 else window.secondary_panel()
    field = panel.inputs[0][2 if index == 0 else -1]
    field.setText("999")
    field.textEdited.emit("999")
    with patch.object(window, "dirty_choice", return_value=CloseChoice.DISCARD):
        close.trigger()
    with AssessmentProjectFile.open(path) as project:
        assert project.load(active.document).tasks[0].repetitions == 350


def test_recent_listing_clear_failure_and_pending_preservation(
    window: LifftWindow,
) -> None:
    """Listing opens no project; clear failure retains history and editor text.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    store = window._settings_store
    before = store.load()
    active = window.presenter.workspace.active
    field = window.task_panel.inputs[0][2]
    field.setText("bad")
    field.textEdited.emit("bad")
    with patch.object(
        AssessmentProjectFile,
        "open",
        side_effect=AssertionError("listing opened project"),
    ):
        window.refresh_recent_projects()
    menu = window._assessment_menu
    assert menu.recent.actions()[0].data() == before.recent_documents[0]
    with patch.object(
        JsonSettingsStore, "save", side_effect=OSError("injected failure")
    ):
        menu.clear_recent_action.trigger()
    assert (
        store.load() == before
        and window.presenter.workspace.active is active
        and field.text() == "bad"
    )
    menu.clear_recent_action.trigger()
    after = store.load()
    assert (
        after.recent_documents == ()
        and after.language is before.language
        and after.default_units is before.default_units
    )
    assert (
        field.text() == "bad"
        and window.task_panel.pending
        and not menu.clear_recent_action.isEnabled()
    )


def test_recent_cancel_failed_open_and_explicit_success(
    window: LifftWindow, tmp_path: Path
) -> None:
    """Cancelled/corrupt targets retain source; success adopts the chosen tool.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = window.presenter.workspace
    active = workspace.active
    location = workspace.location
    target = tmp_path / "copied.ergprj"
    shutil.copyfile(location, target)
    store = window._settings_store
    store.save(store.load().remember(str(target)))
    window.refresh_recent_projects()
    action = window._assessment_menu.recent.actions()[0]
    target.write_bytes(b"not a project")
    action.trigger()
    assert workspace.active is active and workspace.location == location
    shutil.copyfile(location, target)
    with patch.object(
        window,
        "choose_item",
        return_value=(
            next(
                label
                for identity, label in window.document_options(
                    str(target), window.language
                )
                if identity == "duet-1"
            ),
            True,
        ),
    ):
        action.trigger()
    assert (
        workspace.location == str(target)
        and workspace.active.document.document_id == "lifft-1"
    )
    assert store.load().recent_documents[0] == str(target)


def test_missing_recent_no_and_yes_forget_only_entry(
    window: LifftWindow, tmp_path: Path
) -> None:
    """Missing files offer forgetting with default No; never alter the open project.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    missing = str(tmp_path / "missing.ergprj")
    store = window._settings_store
    store.save(store.load().remember(missing))
    window.refresh_recent_projects()
    active = window.presenter.workspace.active
    before = store.load()
    with patch(
        "ergotools.presentation.desktop.lifft_window.QMessageBox.question",
        return_value=QMessageBox.No,
    ) as question:
        window._assessment_menu.recent.actions()[0].trigger()
    assert question.call_args.args[-1] == QMessageBox.No and store.load() == before
    with (
        patch(
            "ergotools.presentation.desktop.lifft_window.QMessageBox.question",
            return_value=QMessageBox.Yes,
        ),
        patch.object(
            JsonSettingsStore, "save", side_effect=OSError("injected failure")
        ),
    ):
        window._assessment_menu.recent.actions()[0].trigger()
    assert store.load() == before and window.presenter.workspace.active is active
    with patch(
        "ergotools.presentation.desktop.lifft_window.QMessageBox.question",
        return_value=QMessageBox.Yes,
    ):
        window._assessment_menu.recent.actions()[0].trigger()
    assert (
        missing not in store.load().recent_documents
        and window.presenter.workspace.active is active
    )


def test_closed_project_translation_fits_summary_labels(window: LifftWindow) -> None:
    """Empty output lists must not leave translated labels at the old width.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    with patch.object(window, "dirty_choice", return_value=CloseChoice.DISCARD):
        window._assessment_menu.close_project_action.trigger()
    for language in (Language.SPANISH, Language.ENGLISH):
        window.language = language
        window.translate()
        QTest.qWait(30)
        assert not window.task_panel.outputs
        for label in (
            window.task_panel.total_title,
            window.task_panel.probability_title,
        ):
            assert label.width() >= label.sizeHint().width()


@pytest.mark.parametrize("language", [Language.ENGLISH, Language.SPANISH])
@pytest.mark.parametrize("accepted", [True, False])
def test_open_project_folder_os_boundary_preserves_pending_input(
    window: LifftWindow, tmp_path: Path, language: Language, accepted: bool
) -> None:
    """Folder menu delegates Unicode paths without accepting drafts or saving data.

    Args:
        window: Disposable integrated project with real Project menu.
        tmp_path: Private path containing spaces, accents and a URL-special character.
        language: English or Spanish menu and launch-failure wording.
        accepted: Desktop service accepts or rejects the external file-manager launch.

    Returns:
        None; the URL target, localized menu/error, unchanged file/source/history and
        invalid pending text are checked. This mocked boundary is not an OS UI test.
    """
    workspace = window.presenter.workspace
    folder = tmp_path / "Proyecto Ána # 1"
    folder.mkdir()
    destination = folder / "workflow.ergprj"
    shutil.copyfile(workspace.location, destination)
    key = workspace.active.document
    workspace.close(choice=CloseChoice.DISCARD)
    workspace.switch(str(destination), key.document_id)
    window.language = language
    window.refresh()
    window.translate()
    field = window.task_panel.inputs[0][2]
    field.setText("bad")
    field.textEdited.emit("bad")
    state = workspace.active.state
    editing = workspace.editing
    revision = editing.history.revision
    before_file = destination.read_bytes()
    action = window._assessment_menu.open_project_folder
    assert action.isEnabled()
    assert action.text() == (
        "Abrir carpeta del proyecto"
        if language is Language.SPANISH
        else "Open project folder"
    )
    with (
        patch(
            "ergotools.presentation.desktop.lifft_window.QDesktopServices.openUrl",
            return_value=accepted,
        ) as launch,
        patch.object(QMessageBox, "warning") as warning,
    ):
        action.trigger()
    launch.assert_called_once()
    url = launch.call_args.args[0]
    assert url.isLocalFile() and Path(url.toLocalFile()) == folder
    assert warning.call_count == (0 if accepted else 1)
    if not accepted:
        assert warning.call_args.args[1] == (
            "Carpeta del proyecto" if language is Language.SPANISH else "Project folder"
        )
    assert workspace.active.state == state
    assert editing.history.revision == revision
    assert destination.read_bytes() == before_file
    assert field.text() == "bad" and window.task_panel.pending


@pytest.mark.parametrize("language", [Language.ENGLISH, Language.SPANISH])
def test_open_project_folder_disabled_without_saved_project(
    window: LifftWindow, language: Language
) -> None:
    """Closed and pre-first-Save temporary projects expose no backing directory.

    Args:
        window: Disposable integrated Project menu and lifecycle.
        language: English or Spanish menu state.

    Returns:
        None; even direct host invocation cannot open a temporary or absent project.
    """
    workspace = window.presenter.workspace
    workspace.close(choice=CloseChoice.DISCARD)
    window.language = language
    window.refresh()
    action = window._assessment_menu.open_project_folder
    with patch(
        "ergotools.presentation.desktop.lifft_window.QDesktopServices.openUrl"
    ) as launch:
        assert not action.isEnabled()
        window.open_project_folder()
        window.new_project()
        assert window._is_unsaved_project()
        assert not action.isEnabled()
        window.open_project_folder()
        launch.assert_not_called()


@pytest.mark.parametrize("language", list(Language))
def test_recent_shows_complete_paths_and_opens_exact_duplicate_filename_location(
    window: LifftWindow, language: Language
) -> None:
    """Same filenames in distinct directories stay identifiable and route exactly.

    Args:
        window: Disposable integrated window; no actual project is opened by this test.
        language: Menu translation must not alter stored/displayed path identities.

    Returns:
        None; literal ampersands and HTML-like path characters remain safe captions.
    """
    paths = (
        "/home/demo/Factory A/workflow.ergprj",
        "/home/demo/Factory B/workflow.ergprj",
        "/home/demo/R&D <archive>/workflow.ergprj",
        r"C:\Projects\Données & tests\workflow.ergprj",
    )
    menu = window._assessment_menu
    menu.translate(language)
    menu.set_recent(paths)
    assert menu.recent.toolTipsVisible()
    actions = menu.recent.actions()[: len(paths)]
    with patch.object(menu, "_open_recent") as open_recent:
        for number, (action, path) in enumerate(zip(actions, paths, strict=True), 1):
            assert action.text() == f"{number}. " + path.replace("&", "&&")
            assert action.data() == path
            assert action.toolTip() == "<qt>" + escape(path) + "</qt>"
            action.trigger()
            open_recent.assert_called_with(path)
        assert open_recent.call_count == len(paths)

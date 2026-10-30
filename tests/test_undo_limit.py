"""Bound shared project replay through personal settings without changing saved data.

Immutable session cases cover pruning, revision identity and clean markers. Native
settings/task controls verify Apply/Cancel, per-user persistence and shared action
boundaries. All projects/preferences are disposable; owner/reference files stay intact.
"""

import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.application.settings import Language, UserSettings
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.settings_store import (
    JsonSettingsStore,
    SettingsFormatError,
)
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.preferences_dialog import PreferencesDialog
from tests.test_saved_tool_data import window as window
from tests.test_session import Draft, MemoryStore, Rename
from tests.test_task_input_history import reopen_grid
from tests.test_unified_project_save import editing_workspace


@pytest.mark.parametrize("limit", [1, 25, 50])
def test_bounded_history_keeps_exact_steps_and_revision_ids(limit: int) -> None:
    """Overflow retains exactly the budget; replay, clean markers and branches survive.

    Args:
        limit: Owner-supported minimum, default or maximum operation budget.

    Returns:
        None; eviction neither renumbers revisions nor makes unsaved data clean.
    """
    key = DocumentKey("p", "d")
    session = DocumentSession(key, Draft("0"), persisted=True)
    session.set_history_limit(limit)
    for number in range(1, 71):
        session.execute(Rename(key, str(number)))
    revision = session.revision
    session.set_history_limit(limit)
    assert session.revision == revision and session.is_dirty
    for number in range(69, 69 - limit, -1):
        assert session.undo() and session.state.title == str(number)
    assert not session.undo()
    assert not session.execute(Rename(key, session.state.title))
    assert session.redo_label_key is not None
    for number in range(71 - limit, 71):
        assert session.redo() and session.state.title == str(number)
    assert not session.redo()
    session.save(MemoryStore())
    assert not session.is_dirty
    assert session.undo() and session.is_dirty
    assert session.redo() and not session.is_dirty
    assert session.undo()
    assert session.execute(Rename(key, "branch"))
    assert session.revision > revision and session.redo_label_key is None


def test_shrink_while_undone_preserves_current_and_prioritizes_undo() -> None:
    """Pruning cannot move data; nearest Undo has priority over excess Redo.

    Args:
        None.

    Returns:
        None; increasing capacity cannot recover discarded snapshots.
    """
    key = DocumentKey("p", "d")
    session = DocumentSession(key, Draft("0"), persisted=True)
    for number in range(1, 11):
        session.execute(Rename(key, str(number)))
    for _ in range(3):
        session.undo()
    before = session.state
    revision = session.revision
    session.set_history_limit(3)
    assert session.state is before and session.revision == revision
    assert not session.redo()
    for value in ("6", "5", "4"):
        assert session.undo() and session.state.title == value
    assert not session.undo()
    session.set_history_limit(50)
    assert not session.undo()
    for _ in range(3):
        assert session.redo()
    assert session.state is before
    session.undo()
    session.undo()
    session.set_history_limit(1)
    assert session.state.title == "5" and not session.redo()
    assert session.undo() and session.state.title == "4"


@pytest.mark.parametrize("value", [0, -1, True, 2.5, "25"])
def test_core_invalid_budget_and_reentrant_save_are_atomic(value: object) -> None:
    """Invalid/reentrant changes preserve the complete existing replay path.

    Args:
        value: Deliberately invalid generic command budget.

    Returns:
        None; neither rejected preference mutation nor failed Save consumes history.
    """
    key = DocumentKey("p", "d")
    session = DocumentSession(key, Draft("0"), persisted=True)
    session.execute(Rename(key, "1"))
    with pytest.raises(ValueError):
        session.set_history_limit(value)
    store = MemoryStore()
    with (
        patch.object(
            store, "save", side_effect=lambda *_: session.set_history_limit(1)
        ),
        pytest.raises(RuntimeError),
    ):
        session.save(store)
    assert session.is_dirty and session.state.title == "1"
    assert session.undo() and session.state.title == "0"


@pytest.mark.parametrize("version", range(1, 6))
def test_previous_settings_formats_default_to_25(tmp_path: Path, version: int) -> None:
    """Older personal settings remain readable without touching any project.

    Args:
        tmp_path: Disposable settings directory.
        version: Existing accepted preference schema before the new Undo field.

    Returns:
        None; old values survive and loading does not rewrite the settings file.
    """
    path = tmp_path / "settings.json"
    store = JsonSettingsStore(path)
    store.save(UserSettings(language=Language.SPANISH, undo_limit=50))
    data = json.loads(path.read_text())
    data["version"] = version
    for field, introduced in (
        ("animated_risk_gauge", 7),
        ("animated_cumulative_damage", 7),
        ("undo_limit", 6),
        ("gauge_markers", 5),
        ("assessment_contexts", 4),
        ("animated_body_region_focus", 3),
        ("decimal_convention", 2),
    ):
        if version < introduced:
            data.pop(field)
    path.write_text(json.dumps(data))
    before = path.read_bytes()
    loaded = store.load()
    assert loaded.undo_limit == 25 and loaded.language is Language.SPANISH
    assert path.read_bytes() == before
    store.save(replace(loaded, undo_limit=1))
    assert store.load().undo_limit == 1
    assert json.loads(path.read_text())["version"] == 7


@pytest.mark.parametrize("value", [0, 51, -1, True, 1.5, "25", None])
def test_invalid_application_preference_is_rejected(
    tmp_path: Path, value: object
) -> None:
    """Typed and serialized application limits enforce integer 1 through 50.

    Args:
        tmp_path: Disposable settings destination.
        value: Invalid typed/serialized value, including bool and null.

    Returns:
        None; damaged settings are rejected without rewriting user preferences.
    """
    with pytest.raises(ValueError):
        UserSettings(undo_limit=value)
    path = tmp_path / "settings.json"
    store = JsonSettingsStore(path)
    assert store.load().undo_limit == 25 and not path.exists()
    store.save(UserSettings())
    data = json.loads(path.read_text())
    data["undo_limit"] = value
    path.write_text(json.dumps(data))
    before = path.read_bytes()
    with pytest.raises(SettingsFormatError):
        store.load()
    assert path.read_bytes() == before


@pytest.mark.parametrize("limit", [1, 25, 50])
def test_project_initial_budget_and_dirty_baseline(tmp_path: Path, limit: int) -> None:
    """Each newly opened project uses personal policy; pruning does not alter dirt.

    Args:
        tmp_path: Disposable native project and settings directory.
        limit: Minimum, default or maximum budget loaded at project activation.

    Returns:
        None; complete private snapshots and Save baseline remain independent of cap.
    """
    workspace = editing_workspace(tmp_path)
    try:
        settings = JsonSettingsStore(tmp_path / "settings.json")
        settings.save(replace(settings.load(), undo_limit=limit))
        location = workspace.location
        workspace.close(choice=CloseChoice.DISCARD)
        workspace.switch(location, None)
        editing = workspace.editing
        assert editing is not None
        for value in range(limit + 2):
            editing.set_editor("probe", value, "assessment.view")
        assert not workspace.has_unsaved_changes
        for _ in range(limit):
            assert editing.history.undo()
        assert not editing.history.undo()
        before = editing.history.state
        editing.set_undo_limit(1)
        assert editing.history.state is before and not workspace.has_unsaved_changes
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("index", range(3))
@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("limit", [1, 25])
def test_settings_apply_cancel_and_shared_task_boundaries(
    window: LifftWindow, tmp_path: Path, index: int, language: Language, limit: int
) -> None:
    """Actual Settings changes the shared budget immediately, retaining Save baseline.

    Args:
        window: Real integrated window borrowing shared project history.
        tmp_path: Disposable project directory.
        index: LiFFT, DUET or ST active tab.
        language: English or Spanish controls.
        limit: Small bounded depth exercised by every actual input/history widget.

    Returns:
        None; Cancel is inert, Apply persists globally, exact Undo/Redo boundaries
        update actions, and project reopen starts a fresh history with retained policy.
    """
    reopen_grid(window, tmp_path, index, MeasurementSystem.METRIC, language)
    workspace = window.presenter.workspace
    path = Path(workspace.location)
    durable = path.read_bytes()
    store = window._settings_store
    before = workspace.editing.history.state

    def choose(cancel: bool) -> None:
        """Set the owned General control and accept or cancel the actual modal.

        Args:
            cancel: True rejects the draft preference; False applies it.

        Returns:
            None; range and initial persisted value are inspected in the real dialog.
        """
        modal = QApplication.activeModalWidget()
        assert isinstance(modal, PreferencesDialog)
        assert modal.undo_limit.minimum() == 1 and modal.undo_limit.maximum() == 50
        assert modal.undo_limit.value() == 25
        modal.undo_limit.setValue(limit)
        (modal.cancel_button if cancel else modal.apply_button).click()

    for cancel in (True, False):
        QTimer.singleShot(0, lambda cancel=cancel: choose(cancel))
        window._assessment_menu.preferences.trigger()
        assert workspace.editing.history.state == before
        assert path.read_bytes() == durable and not workspace.has_unsaved_changes
        assert store.load().undo_limit == (25 if cancel else limit)
    for count in range(101, 103 + limit):
        panel = window.secondary_panel() or window.task_panel
        field = panel.inputs[0][-1]
        field.setText(str(count))
        field.textEdited.emit(str(count))
        field.editingFinished.emit()
    window.setFocus()
    actions = window.main_navigation.toolbar_actions
    for expected in range(101 + limit, 101, -1):
        assert actions["undo"].isEnabled()
        actions["undo"].trigger()
        assert workspace.active.state.tasks[0].repetitions == expected
    assert not actions["undo"].isEnabled()
    assert workspace.has_unsaved_changes and actions["save"].isEnabled()
    for _ in range(limit):
        assert actions["redo"].isEnabled()
        actions["redo"].trigger()
    assert not actions["redo"].isEnabled()
    assert path.read_bytes() == durable
    window.save_project()
    assert not workspace.has_unsaved_changes
    key = workspace.active.document
    workspace.close(choice=CloseChoice.DISCARD)
    workspace.switch(str(path), key.document_id)
    window.refresh()
    assert store.load().undo_limit == limit
    assert not actions["undo"].isEnabled() and not actions["save"].isEnabled()

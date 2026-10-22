"""Scoped Clear assessment workflows and explicit backend deletion integrity.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.session import DocumentKey
from ergotools.application.settings import Language
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessments.document import AssessmentDraft, AssessmentKind
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.assessments.tst import TstDirection
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.style import WORKSPACE_STYLE
from tests.test_saved_tool_data import KINDS
from tests.test_saved_tool_data import window as window


def test_storage_delete_rolls_back_source_and_history(window: LifftWindow) -> None:
    """Failure between owner/source writes rolls back the complete transaction.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    path = Path(window.presenter.workspace.location)
    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            "CREATE TRIGGER reject_source_delete BEFORE DELETE ON draft_documents "
            "BEGIN SELECT RAISE(ABORT, 'injected'); END"
        )
        connection.commit()
    with AssessmentProjectFile.open(path) as project:
        history = project.load_history()
        key = DocumentKey("p", "lifft-1")
        source = project.load(key)
        with pytest.raises(sqlite3.IntegrityError):
            project.delete_historical_assessment(history, "lifft-1")
        assert project.load_history() == history and project.load(key) == source
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("DROP TRIGGER reject_source_delete")
        connection.commit()


def test_storage_compacts_positions_rejects_stale_and_retains_last_project(
    window: LifftWindow,
) -> None:
    """Permit future insertion and empty projects without version promotion.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    path = Path(window.presenter.workspace.location)
    with AssessmentProjectFile.open(path) as project:
        old = project.load_history()
        current = project.delete_historical_assessment(old, "lifft-1")
        with pytest.raises(ValueError):
            project.delete_historical_assessment(old, "duet-1")
        with pytest.raises(KeyError):
            project.delete_historical_assessment(current, "missing")
        project.create_historical_assessment(
            AssignmentAssessment(
                "replacement",
                1,
                KINDS[0],
                worker_id=next(
                    a.worker.worker_id
                    for a in project.load_jobs().assignments
                    if a.assignment_id == 1
                ),
            ),
            LifftDraft(project.metadata.default_units),
        )
        current = project.load_history()
        for entry in tuple(current.entries):
            current = project.delete_historical_assessment(current, entry.document_id)
        assert current.entries == () and project.list_assessments() == ()
        assert project.load_jobs().assignments
    with AssessmentProjectFile.open(path) as project:
        assert project.load_history().entries == ()


def prepare_clear_window(
    window: LifftWindow,
    index: int,
    language: Language,
    system: MeasurementSystem,
    standalone: bool,
    count: int,
) -> None:
    """Save and reopen a calculated exact owner with a custom-sized task grid.

    Args:
        window: Borrowed real integrated window over temporary native data.
        index: LiFFT, DUET or ST tab index.
        language: English or Spanish controls and confirmation.
        system: Metric or imperial display/input units.
        standalone: True selects independent worker ownership; False keeps assignment1.
        count: Existing task count whose rows/identities must survive clearing.

    Returns:
        None; the caller receives a fresh shared history with all other saved sources.
    """
    window.language = language
    window.presenter.system = system
    window.translate()
    window.assessment_tabs.setCurrentIndex(index)
    if standalone:
        window.assessment_navigation.select(
            "w",
            KINDS[index],
            lambda: window._blank_kind(KINDS[index]),
            workplace=None,
            keep=True,
            explicit=True,
        )
    presenter = (window.presenter, window.duet_presenter, window.tst_presenter)[index]
    presenter.set_task_count(count)
    window.refresh()
    panel = window.secondary_panel() or window.task_panel
    fields = panel.inputs[0]
    if index == 1:
        fields[0].setCurrentIndex(6)
        numeric = fields[1:]
        values = ("100",)
    elif index == 2:
        fields[0].setCurrentIndex(2)
        numeric = fields[1:]
        values = ("30", "49.05", "100")
    else:
        numeric = fields
        values = ("30", "49.05", "100")
    for field, value in zip(numeric, values, strict=True):
        field.setText(value)
        field.textEdited.emit(value)
    panel.calculate_button.click()
    window.save_project()
    workspace = window.presenter.workspace
    key = workspace.active.document
    path = workspace.location
    workspace.close(choice=CloseChoice.DISCARD)
    workspace.switch(path, key.document_id)
    window.refresh()
    window.setFocus()


def private_assessment_values(
    window: LifftWindow,
) -> dict[DocumentKey, tuple[object, object]]:
    """Read all private source/result pairs through the existing owned adapter.

    Args:
        window: Integrated temporary native workspace whose private state is inspected.

    Returns:
        Exact immutable source/result pairs by document; no Save or calculation occurs.
    """
    project = window.presenter.workspace._project
    return {
        entry.document: (
            project.load(entry.document),
            project.load_saved_result(entry.document),
        )
        for entry in project.list_assessments()
    }


def choose_clear(window: LifftWindow, accept: bool) -> None:
    """Inspect and resolve the actual themed confirmation for this active owner.

    Args:
        window: Main window owning the real confirmation modal.
        accept: True explicitly clears; False chooses the default Cancel action.

    Returns:
        None; context, localized captions, theme and safe default are asserted.
    """
    modal = QApplication.activeModalWidget()
    assert isinstance(modal, QMessageBox)
    spanish = window.language is Language.SPANISH
    caption = "Limpiar evaluación" if spanish else "Clear assessment"
    assert caption in modal.windowTitle()
    assert ("LiFFT", "DUET", "ST")[
        (AssessmentKind.LIFFT, AssessmentKind.DUET, AssessmentKind.TST).index(
            window.active_kind()
        )
    ] in modal.windowTitle()
    assert "w" in modal.text()
    assert modal.styleSheet() == WORKSPACE_STYLE
    assert modal.defaultButton() is modal.button(QMessageBox.Cancel)
    assert modal.button(QMessageBox.Yes).text() == caption
    modal.button(QMessageBox.Yes if accept else QMessageBox.Cancel).click()


def assert_clear_source(source: AssessmentDraft, count: int) -> None:
    """Check blank canonical fields and established DUET/ST selector defaults.

    Args:
        source: Actual active tool source after clearing.
        count: Required unchanged task count.

    Returns:
        None; numeric fields are missing, DUET ratings zero and ST Handling Loads.
    """
    assert len(source.tasks) == count
    for task in source.tasks:
        assert task.repetitions is None
        if isinstance(source, DuetDraft):
            assert task.omni_res_scale == 0
        else:
            assert task.lever_arm is None and task.load is None
        if isinstance(source, TstDraft):
            assert task.direction is TstDirection.HANDLING_LOADS


@pytest.mark.parametrize("index", range(3))
@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("system", list(MeasurementSystem))
@pytest.mark.parametrize("standalone", [False, True])
def test_clear_cancel_replay_save_and_cross_tool_isolation(
    window: LifftWindow,
    index: int,
    language: Language,
    system: MeasurementSystem,
    standalone: bool,
) -> None:
    """One confirmed Clear keeps the owner/grid and touches no other source/result.

    Args:
        window: Temporary integrated native project with multiple workers/assignments.
        index: LiFFT, DUET or ST source under test.
        language: English or Spanish controls.
        system: Metric or imperial display/input interpretation.
        standalone: Independent ownership or a real workplace/Job assignment.

    Returns:
        None; invalid-text Cancel is inert, Clear is one exact shared Undo/Redo step,
        Save/reopen keeps the blank owned grid, and other assessment data is untouched.
    """
    count = 15 if standalone else 7
    prepare_clear_window(window, index, language, system, standalone, count)
    workspace = window.presenter.workspace
    active = workspace.active
    key = active.document
    original = active.state
    original_result = workspace.historical_result()
    assert original_result is not None
    all_before = private_assessment_values(window)
    history = workspace.read_history().history
    view = window.assessment_navigation.view
    path = Path(workspace.location)
    durable = path.read_bytes()
    panel = window.secondary_panel() or window.task_panel
    assert not hasattr(panel, "delete_button") and not hasattr(panel, "reset_button")
    assert panel.clear_button.text() == (
        "Limpiar evaluación" if language is Language.SPANISH else "Clear assessment"
    )
    field = panel.inputs[0][-1]
    field.setText("invalid")
    field.textEdited.emit("invalid")
    before_revision = workspace.editing.history.revision
    QTimer.singleShot(0, lambda: choose_clear(window, False))
    panel.clear_button.click()
    assert field.text() == "invalid" and panel.pending
    assert (
        active.state is original
        and workspace.editing.history.revision == before_revision
    )
    assert private_assessment_values(window) == all_before
    QTimer.singleShot(0, lambda: choose_clear(window, True))
    panel.clear_button.click()
    assert workspace.active.document == key
    assert_clear_source(active.state, count)
    assert tuple(t.task_id for t in active.state.tasks) == tuple(
        t.task_id for t in original.tasks
    )
    if hasattr(original, "system"):
        assert active.state.system is original.system
    assert window.assessment_navigation.view.worker_id == view.worker_id
    assert window.assessment_navigation.view.assignment_id == view.assignment_id
    assert workspace.read_history().history == history
    assert workspace.historical_result() is None
    assert not panel.pending and not window.results_sidebar.risk_gauge.has_value
    assert len(panel.inputs) == count
    changed = private_assessment_values(window)
    assert {k: v for k, v in changed.items() if k != key} == {
        k: v for k, v in all_before.items() if k != key
    }
    assert changed[key][1] is None
    assert path.read_bytes() == durable
    assert workspace.editing.history.revision == before_revision + 1
    assert workspace.editing.history.undo_label_key == "assessment.clear"
    actions = window.main_navigation.toolbar_actions
    window.setFocus()
    actions["undo"].trigger()
    assert workspace.active.state == original
    assert workspace.historical_result() == original_result
    assert not workspace.has_unsaved_changes and not actions["save"].isEnabled()
    assert not actions["undo"].isEnabled()
    actions["redo"].trigger()
    assert_clear_source(workspace.active.state, count)
    assert workspace.has_unsaved_changes and actions["save"].isEnabled()
    actions["save"].trigger()
    with AssessmentProjectFile.open(path) as project:
        assert project.load_history() == history
        assert project.load_saved_result(key) is None
        assert project.load(key) == workspace.active.state
        for other, (source, result) in all_before.items():
            if other != key:
                assert project.load(other) == source
                assert project.load_saved_result(other) == result
    workspace.close(choice=CloseChoice.DISCARD)
    workspace.switch(str(path), key.document_id)
    window.refresh()
    assert_clear_source(workspace.active.state, count)
    assert len((window.secondary_panel() or window.task_panel).inputs) == count
    assert not actions["undo"].isEnabled() and not actions["save"].isEnabled()


@pytest.mark.parametrize("index", range(3))
@pytest.mark.parametrize("count", [1, 100])
def test_clear_preserves_task_count_boundaries(
    window: LifftWindow, index: int, count: int
) -> None:
    """Minimum/maximum owned grids retain their exact IDs and size through Clear.

    Args:
        window: Temporary integrated native project.
        index: LiFFT, DUET or ST active model.
        count: Owner-supported minimum or maximum task slots.

    Returns:
        None; one Undo restores the original source at both count boundaries.
    """
    prepare_clear_window(
        window, index, Language.ENGLISH, MeasurementSystem.METRIC, False, count
    )
    workspace = window.presenter.workspace
    original = workspace.active.state
    QTimer.singleShot(0, lambda: choose_clear(window, True))
    (window.secondary_panel() or window.task_panel).clear_button.click()
    assert_clear_source(workspace.active.state, count)
    assert tuple(t.task_id for t in workspace.active.state.tasks) == tuple(
        t.task_id for t in original.tasks
    )
    window.setFocus()
    window.main_navigation.toolbar_actions["undo"].trigger()
    assert workspace.active.state == original


@pytest.mark.parametrize("index", range(3))
def test_repeated_blank_clear_preserves_redo(window: LifftWindow, index: int) -> None:
    """Clearing an already blank owned form does not consume history or truncate Redo.

    Args:
        window: Temporary integrated native project.
        index: Active tool whose numeric field and selector defaults are checked.

    Returns:
        None; unchanged clearing stays clean and the prior field edit remains redoable.
    """
    prepare_clear_window(
        window, index, Language.ENGLISH, MeasurementSystem.METRIC, False, 15
    )
    QTimer.singleShot(0, lambda: choose_clear(window, True))
    (window.secondary_panel() or window.task_panel).clear_button.click()
    window.save_project()
    panel = window.secondary_panel() or window.task_panel
    field = panel.inputs[0][-1]
    field.setText("150")
    field.textEdited.emit("150")
    field.editingFinished.emit()
    window.setFocus()
    actions = window.main_navigation.toolbar_actions
    actions["undo"].trigger()
    workspace = window.presenter.workspace
    revision = workspace.editing.history.revision
    assert actions["redo"].isEnabled() and not workspace.has_unsaved_changes
    QTimer.singleShot(0, lambda: choose_clear(window, True))
    (window.secondary_panel() or window.task_panel).clear_button.click()
    assert workspace.editing.history.revision == revision
    assert actions["redo"].isEnabled() and not workspace.has_unsaved_changes
    actions["redo"].trigger()
    assert workspace.active.state.tasks[0].repetitions == 150


@pytest.mark.parametrize("index", range(3))
def test_failed_main_save_keeps_clear_undoable(window: LifftWindow, index: int) -> None:
    """Publication failure retains the clear draft, saved file and exact Undo target.

    Args:
        window: Temporary integrated project and shared Save/history controls.
        index: LiFFT, DUET or ST source whose calculated baseline is retained.

    Returns:
        None; after failed Save, Undo still restores the complete saved assessment.
    """
    prepare_clear_window(
        window, index, Language.ENGLISH, MeasurementSystem.METRIC, False, 15
    )
    workspace = window.presenter.workspace
    original = workspace.active.state
    result = workspace.historical_result()
    path = Path(workspace.location)
    durable = path.read_bytes()
    QTimer.singleShot(0, lambda: choose_clear(window, True))
    (window.secondary_panel() or window.task_panel).clear_button.click()
    with (
        patch.object(
            workspace.editing.repository,
            "commit_editing",
            side_effect=OSError("read only"),
        ),
        pytest.raises(OSError, match="read only"),
    ):
        window.save_project()
    assert path.read_bytes() == durable and workspace.has_unsaved_changes
    assert_clear_source(workspace.active.state, 15)
    window.setFocus()
    window.main_navigation.toolbar_actions["undo"].trigger()
    assert workspace.active.state == original
    assert workspace.historical_result() == result
    assert not workspace.has_unsaved_changes


@pytest.mark.parametrize("label", ["", " ", "\n"])
def test_invalid_staging_label_cannot_mutate_project(
    window: LifftWindow, label: str
) -> None:
    """The shared explicit-action port rejects blank labels before touching sources.

    Args:
        window: Existing integrated source over private temporary data.
        label: Invalid empty/whitespace operation label.

    Returns:
        None; source, results, shared history and file all remain unchanged.
    """
    workspace = window.presenter.workspace
    before = private_assessment_values(window)
    revision = workspace.editing.history.revision
    with pytest.raises(ValueError, match="label"):
        workspace.stage_assessments(label=label)
    assert private_assessment_values(window) == before
    assert workspace.editing.history.revision == revision


def test_clear_without_project_never_opens_confirmation(window: LifftWindow) -> None:
    """The host safely ignores Clear when no assessment/project is active.

    Args:
        window: Borrowed main window, closed explicitly before the attempted action.

    Returns:
        None; no source, manufactured context or assessment is created.
    """
    window.presenter.workspace.close(choice=CloseChoice.DISCARD)
    window.refresh()
    with patch.object(window, "confirm_clear_assessment") as confirm:
        window.clear_assessment()
    confirm.assert_not_called()
    assert window.presenter.workspace.active is None
    assert not window.task_panel.clear_button.isEnabled()

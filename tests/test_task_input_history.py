"""Completed task cells are separate edits on the existing shared project cursor.

Real controls drive mouse, Tab and Enter completion, pending invalid siblings,
revisited fields, exact source/result replay and durable Save boundaries. All native
files are temporary; the owner/reference projects and dependency baseline are untouched.
"""

from pathlib import Path

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QComboBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.assessments.validation import DraftError
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_task_count_integration import window as window


def reopen_grid(
    window: LifftWindow,
    tmp_path: Path,
    index: int,
    system: MeasurementSystem,
    language: Language,
) -> AssessmentDraft:
    """Start with a saved/reopened fifteen-row source and one calculated first task.

    Args:
        window: Borrowed integrated window; the existing fixture owns final cleanup.
        tmp_path: Private native project destination.
        index: LiFFT, DUET or ST tab index.
        system: Metric or imperial source and display interpretation.
        language: Application language for actual controls and history labels.

    Returns:
        Exact initial immutable source, with no shared Undo available after reopening.
    """
    workspace = window.presenter.workspace
    workspace.close(choice=CloseChoice.DISCARD)
    source = (
        LifftDraft(system, (LifftTask("first", 30, 49.05, 100),)),
        DuetDraft((DuetTask("first", 6, 100),)),
        TstDraft(system, (TstTask("first", TstDirection.HORIZONTAL, 30, 49.05, 100),)),
    )[index]
    path = tmp_path / "cell-history.ergprj"
    workspace.create(
        str(path), ProjectMetadata("cells", "Cells", system), "assessment", source
    )
    window.language = language
    window.presenter.system = system
    window.assessment_tabs.setCurrentIndex(index)
    presenter = (window.presenter, window.duet_presenter, window.tst_presenter)[index]
    presenter.set_task_count(15)
    window.refresh()
    window.calculate()
    window.save_project()
    key = workspace.active.document
    original = workspace.active.state
    workspace.close(choice=CloseChoice.DISCARD)
    workspace.switch(str(path), key.document_id)
    window.refresh()
    window.activateWindow()
    QTest.qWait(20)
    assert workspace.editing.history.undo_label_key is None
    return original


@pytest.mark.parametrize("index", [0, 1, 2])
@pytest.mark.parametrize("system", list(MeasurementSystem))
@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("row", [0, 1])
@pytest.mark.parametrize("completion", ["tab", "enter", "mouse"])
def test_each_completed_input_is_one_shared_history_step(
    window: LifftWindow,
    tmp_path: Path,
    index: int,
    system: MeasurementSystem,
    language: Language,
    row: int,
    completion: str,
) -> None:
    """Every input reverses alone, across all tools, units and completion gestures.

    Args:
        window: Real main toolbar and existing integrated task controls.
        tmp_path: Disposable native file directory.
        index: LiFFT, DUET or ST tab; all numeric and selector columns are edited.
        system: Metric or imperial source/display interpretation.
        language: English or Spanish UI.
        row: Initially populated first task or blank second task.
        completion: Tab, Enter or mouse departure completes numeric input.

    Returns:
        None; exact intermediate source/results, actual widget projections, rebind
        lifetime, one command per input, full replay and unchanged disk are checked.
    """
    original = reopen_grid(window, tmp_path, index, system, language)
    workspace = window.presenter.workspace
    editing = workspace.editing
    original_result = workspace.historical_result()
    path = Path(workspace.location)
    durable = path.read_bytes()
    snapshots = [original]
    panel = window.secondary_panel() or window.task_panel
    for column in range(len(panel.inputs[row])):
        field = panel.inputs[row][column]
        field.setFocus()
        revision = editing.history.revision
        if isinstance(field, QComboBox):
            field.setCurrentIndex((field.currentIndex() + 1) % field.count())
        else:
            field.selectAll()
            QTest.keyClicks(field, str(50 + column * 10))
            if completion == "mouse":
                QTest.mouseClick(panel.inputs[(row + 1) % 15][-1], Qt.LeftButton)
            else:
                QTest.keyClick(
                    field, Qt.Key_Tab if completion == "tab" else Qt.Key_Return
                )
        assert editing.history.revision == revision + 1
        assert workspace.active.state != snapshots[-1]
        assert not panel.pending
        assert (
            "Modificado" if language is Language.SPANISH else "Modified"
        ) in window.main_navigation.project_label.text()
        assert panel.inputs[row][column] is field  # No signal-time widget rebuild.
        if completion == "enter" and not isinstance(field, QComboBox):
            assert field.hasFocus()
        snapshots.append(workspace.active.state)
    nav = window.main_navigation
    undo = nav.toolbar.widgetForAction(nav.toolbar_actions["undo"])
    redo = nav.toolbar.widgetForAction(nav.toolbar_actions["redo"])
    for expected in reversed(snapshots[:-1]):
        QTest.mouseClick(undo, Qt.LeftButton)
        assert workspace.active.state == expected
        panel = window.secondary_panel() or window.task_panel
        assert panel.presenter.parse_grid(panel.context, panel.input_rows()) == expected
        assert not panel.pending
        assert workspace.historical_result() == (
            original_result if expected == original else None
        )
        assert path.read_bytes() == durable
    assert not undo.isEnabled() and redo.isEnabled()
    for expected in snapshots[1:]:
        QTest.mouseClick(redo, Qt.LeftButton)
        assert workspace.active.state == expected
        panel = window.secondary_panel() or window.task_panel
        assert panel.presenter.parse_grid(panel.context, panel.input_rows()) == expected
        assert workspace.historical_result() is None
    assert not redo.isEnabled() and path.read_bytes() == durable
    key = workspace.active.document
    window.save_project()
    workspace.close(choice=CloseChoice.DISCARD)
    workspace.switch(str(path), key.document_id)
    assert workspace.active.state == snapshots[-1]


@pytest.mark.parametrize("index", [0, 1, 2])
@pytest.mark.parametrize("system", list(MeasurementSystem))
@pytest.mark.parametrize("language", list(Language))
def test_last_pending_cell_undo_then_revisit_same_field(
    window: LifftWindow,
    tmp_path: Path,
    index: int,
    system: MeasurementSystem,
    language: Language,
) -> None:
    """Arm 50 then Load 60 reverses 60 first; revisiting a field adds a fresh step.

    Args:
        window: Integrated controls with the shared mouse toolbar.
        tmp_path: Disposable saved project destination.
        index: All tools; DUET uses repetitions then its rating selector.
        system: Source/display unit interpretation.
        language: English or Spanish captions.

    Returns:
        None; the last numeric field is still being typed before Undo, and replay
        checks each intermediate source, rendered input and matching result.
    """
    original = reopen_grid(window, tmp_path, index, system, language)
    workspace = window.presenter.workspace
    result = workspace.historical_result()
    panel = window.secondary_panel() or window.task_panel
    first_column, second_column = ((0, 1), (1, 0), (1, 2))[index]
    first = panel.inputs[1][first_column]
    second = panel.inputs[1][second_column]
    first.setFocus()
    QTest.keyClicks(first, "50")
    second.setFocus()  # Completes only the first field, without rebuilding either.
    after_first = workspace.active.state
    assert after_first != original and panel.inputs[1][first_column] is first
    if isinstance(second, QComboBox):
        second.setCurrentIndex((second.currentIndex() + 1) % second.count())
    else:
        QTest.keyClicks(second, "60")
        assert panel.pending and workspace.active.state == after_first
    desired = panel.presenter.parse_grid(panel.context, panel.input_rows())
    nav = window.main_navigation
    undo = nav.toolbar.widgetForAction(nav.toolbar_actions["undo"])
    redo = nav.toolbar.widgetForAction(nav.toolbar_actions["redo"])
    for expected in (after_first, original):
        QTest.mouseClick(undo, Qt.LeftButton)
        assert workspace.active.state == expected
        panel = window.secondary_panel() or window.task_panel
        assert panel.presenter.parse_grid(panel.context, panel.input_rows()) == expected
    assert workspace.historical_result() == result
    for expected in (after_first, desired):
        QTest.mouseClick(redo, Qt.LeftButton)
        assert workspace.active.state == expected
    panel = window.secondary_panel() or window.task_panel
    first = panel.inputs[1][first_column]
    first.setFocus()
    first.selectAll()
    QTest.keyClicks(first, "80")
    QTest.keyClick(first, Qt.Key_Return)
    assert workspace.active.state != desired
    QTest.mouseClick(undo, Qt.LeftButton)
    assert workspace.active.state == desired  # Other field remains 60/rating choice.
    panel = window.secondary_panel() or window.task_panel
    assert panel.inputs[1][first_column].text() in ("50", "50.0", "50,0")


@pytest.mark.parametrize("index", [0, 1, 2])
@pytest.mark.parametrize("system", list(MeasurementSystem))
@pytest.mark.parametrize("language", list(Language))
def test_invalid_sibling_never_batches_other_completed_cells(
    window: LifftWindow,
    tmp_path: Path,
    index: int,
    system: MeasurementSystem,
    language: Language,
) -> None:
    """Valid siblings commit independently while invalid text stays local and visible.

    Args:
        window: Borrowed main window and real task widgets.
        tmp_path: Only native project destination.
        index: LiFFT, DUET or ST numeric/selector combination.
        system: Metric or imperial inputs.
        language: English or Spanish controls.

    Returns:
        None; source history stays granular through invalid-field correction, without
        accepting invalid text, dropping a valid edit or hiding the original result.
    """
    original = reopen_grid(window, tmp_path, index, system, language)
    workspace = window.presenter.workspace
    result = workspace.historical_result()
    panel = window.secondary_panel() or window.task_panel
    invalid_column, valid_column = ((0, 1), (1, 0), (1, 0))[index]
    invalid = panel.inputs[1][invalid_column]
    valid = panel.inputs[1][valid_column]
    invalid.setFocus()
    QTest.keyClicks(invalid, "bad")
    valid.setFocus()
    assert workspace.active.state == original
    revision = workspace.editing.history.revision
    if isinstance(valid, QComboBox):
        valid.setCurrentIndex((valid.currentIndex() + 1) % valid.count())
    else:
        QTest.keyClicks(valid, "60")
        QTest.keyClick(valid, Qt.Key_Return)
    accepted = workspace.active.state
    assert accepted != original
    assert workspace.editing.history.revision == revision + 1
    assert invalid.text() == "bad" and panel.pending
    assert panel.pending_change() is None
    invalid.setFocus()
    invalid.selectAll()
    QTest.keyClicks(invalid, "50")
    QTest.keyClick(invalid, Qt.Key_Return)
    assert workspace.editing.history.revision == revision + 2
    assert not panel.pending
    nav = window.main_navigation
    undo = nav.toolbar.widgetForAction(nav.toolbar_actions["undo"])
    for expected in (accepted, original):
        QTest.mouseClick(undo, Qt.LeftButton)
        assert workspace.active.state == expected
        panel = window.secondary_panel() or window.task_panel
        assert panel.presenter.parse_grid(panel.context, panel.input_rows()) == expected
    assert workspace.historical_result() == result


@pytest.mark.parametrize("index", [0, 1, 2])
def test_cell_coordinates_stale_context_and_noop_preserve_cursor(
    window: LifftWindow, tmp_path: Path, index: int
) -> None:
    """Cell acceptance retains identity/context guards and native typing/no-op policy.

    Args:
        window: Real task controls and existing project history.
        tmp_path: Private native project destination.
        index: Tool-specific coordinate and numeric field interpretation.

    Returns:
        None; invalid coordinates/stale callbacks cannot mutate source or history,
        native typing Undo remains local and unchanged completion adds no command.
    """
    original = reopen_grid(
        window, tmp_path, index, MeasurementSystem.METRIC, Language.ENGLISH
    )
    workspace = window.presenter.workspace
    panel = window.secondary_panel() or window.task_panel
    rows = panel.input_rows()
    context = panel.context
    for cell in (("missing", 1), (rows[0][0], 0), (rows[0][0], 99), (rows[0][0], True)):
        with pytest.raises(DraftError):
            panel.presenter.commit_grid(context, rows, cell=cell)
        assert workspace.active.state == original
        assert workspace.editing.history.undo_label_key is None
    field = panel.inputs[1][0 if index == 0 else -1]
    field.setFocus()
    QTest.keyClicks(field, "50")
    QTest.keyClick(field, Qt.Key_Z, Qt.ControlModifier)
    assert field.text() == "" and workspace.active.state == original
    QTest.keyClick(field, Qt.Key_Return)
    assert workspace.editing.history.undo_label_key is None
    assert not panel.pending
    QTest.keyClicks(field, "50")
    QTest.keyClick(field, Qt.Key_Return)
    accepted = workspace.active.state
    revision = workspace.editing.history.revision
    with pytest.raises(DraftError):
        panel.presenter.commit_grid(context, rows, cell=(rows[0][0], 1))
    assert workspace.active.state == accepted
    QTest.keyClick(field, Qt.Key_Return)  # Unchanged Enter creates no additional edit.
    assert workspace.editing.history.revision == revision


@pytest.mark.parametrize("index", [0, 2])
@pytest.mark.parametrize("source_system", list(MeasurementSystem))
def test_cell_completion_keeps_unedited_precision_across_display_units(
    window: LifftWindow,
    tmp_path: Path,
    index: int,
    source_system: MeasurementSystem,
) -> None:
    """One comma-decimal projected input never rounds an untouched source sibling.

    Args:
        window: Existing dimensional tool controls and shared project history.
        tmp_path: Only native project destination.
        index: LiFFT or ST; DUET has no dimensional input projection.
        source_system: Canonical metric or imperial data, displayed in the other system.

    Returns:
        None; unchanged 49.05 source load remains exact, entered arm/repetition edits
        undo separately and original source/result recover without calculation.
    """
    original = reopen_grid(window, tmp_path, index, source_system, Language.SPANISH)
    workspace = window.presenter.workspace
    result = workspace.historical_result()
    display = (
        MeasurementSystem.METRIC
        if source_system is MeasurementSystem.IMPERIAL
        else MeasurementSystem.IMPERIAL
    )
    window.presenter.system = display
    window.presenter.convention = DecimalConvention.COMMA
    window.refresh()
    panel = window.secondary_panel() or window.task_panel
    assert panel.context.view.system is display
    arm = panel.inputs[0][0 if index == 0 else 1]
    arm.setFocus()
    arm.selectAll()
    QTest.keyClicks(arm, "50,5")
    QTest.keyClick(arm, Qt.Key_Return)
    after_arm = workspace.active.state
    assert after_arm != original
    assert after_arm.tasks[0].load == original.tasks[0].load == 49.05
    assert after_arm.tasks[0].repetitions == original.tasks[0].repetitions
    repetitions = panel.inputs[0][-1]
    repetitions.setFocus()
    repetitions.selectAll()
    QTest.keyClicks(repetitions, "200")
    QTest.keyClick(repetitions, Qt.Key_Return)
    nav = window.main_navigation
    undo = nav.toolbar.widgetForAction(nav.toolbar_actions["undo"])
    for expected in (after_arm, original):
        QTest.mouseClick(undo, Qt.LeftButton)
        assert workspace.active.state == expected
        panel = window.secondary_panel() or window.task_panel
        assert panel.presenter.parse_grid(panel.context, panel.input_rows()) == expected
    assert workspace.historical_result() == result


@pytest.mark.parametrize("index", [0, 1, 2])
def test_programmatic_projection_does_not_complete_retiring_input(
    window: LifftWindow, tmp_path: Path, index: int
) -> None:
    """Retiring focused widgets during projection cannot create a source command.

    Args:
        window: Existing integrated source view and real task controls.
        tmp_path: Private native project destination.
        index: LiFFT, DUET or ST projection path.

    Returns:
        None; a deliberate programmatic reload discards only pending widget text,
        preserves the canonical source/result and cannot manufacture project history.
    """
    original = reopen_grid(
        window, tmp_path, index, MeasurementSystem.METRIC, Language.ENGLISH
    )
    workspace = window.presenter.workspace
    result = workspace.historical_result()
    panel = window.secondary_panel() or window.task_panel
    field = panel.inputs[1][0 if index == 0 else -1]
    field.setFocus()
    QTest.keyClicks(field, "50")
    assert panel.pending and workspace.editing.history.undo_label_key is None
    window.refresh()
    assert workspace.active.state == original
    assert workspace.historical_result() == result
    assert workspace.editing.history.undo_label_key is None
    panel = window.secondary_panel() or window.task_panel
    assert not panel.pending
    assert panel.inputs[1][0 if index == 0 else -1].text() == ""

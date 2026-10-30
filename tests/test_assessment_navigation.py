"""Owner-approved integrated context navigation, deferred Save and draft regression.

Test layer. Use synthetic classified projects and real main-window controls. No
reference inputs are written; each fixture owns its repository, preferences and Qt
lifetime. Assertions cover observable workflows rather than implementation structure.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtWidgets import QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.job_catalog import JobPlacement, WorkerJobAssignment
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_duet_task_panel import enter as enter_duet
from tests.test_history_persistence import STATION
from tests.test_lifft_task_panel import enter
from tests.test_main_navigation import window as window


def add_night_context(view: LifftWindow, *, saved: bool = True) -> None:
    """Add a second classified workplace for the same Job in a disposable project.

    Args:
        view: Fixture-owned integrated window; release its repository before writing.
        saved: True adds a saved night LiFFT assessment; False leaves a New context.

    Returns:
        None; reopen the original day assessment with fresh workspace snapshots.
    """
    workspace = view.presenter.workspace
    path = Path(workspace.location)
    workspace.close(choice=CloseChoice.DISCARD)
    with AssessmentProjectFile.open(path) as project:
        hierarchy = project.load_hierarchy()
        project.save_hierarchy(
            replace(hierarchy, work=replace(hierarchy.work, shifts=("Day", "Night")))
        )
        owner = hierarchy.work.worker_context("w", STATION.at_shift("Day"))
        owner = replace(owner, workplace=STATION.at_shift("Night"))
        jobs = project.load_jobs()
        project.save_jobs(
            replace(
                jobs,
                placements=(*jobs.placements, JobPlacement(3, "j", owner.workplace)),
                assignments=(*jobs.assignments, WorkerJobAssignment(3, owner, 3)),
            )
        )
        if saved:
            project.create_historical_assessment(
                AssignmentAssessment(
                    "night",
                    3,
                    AssessmentKind.LIFFT,
                    worker_id=next(
                        a.worker.worker_id
                        for a in project.load_jobs().assignments
                        if a.assignment_id == 3
                    ),
                ),
                LifftDraft(
                    MeasurementSystem.IMPERIAL, (LifftTask("night-task", 30, 20, 40),)
                ),
            )
    workspace.switch(str(path), "a")
    view.assessment_navigation.view = None
    view.refresh()


def test_open_has_no_assessment_picker(window: LifftWindow) -> None:
    """Opening selects an available LiFFT context without asking for a document.

    Args:
        window: Disposable integrated window with two workers holding saved data.

    Returns:
        None.
    """
    path = window.presenter.workspace.location
    window.presenter.workspace.close(choice=CloseChoice.DISCARD)
    with patch.object(
        window,
        "choose_item",
        side_effect=AssertionError("Unexpected assessment picker"),
    ):
        window.open_project_location(path)
    assert window.presenter.workspace.location == path
    assert window.main_navigation.workers.currentData() == "w"
    assert window.active_kind() is AssessmentKind.LIFFT
    assert window.active_source().tasks[0].lever_arm == 12


@pytest.mark.parametrize("enabled", [True, False])
def test_all_workers_remain_navigable(window: LifftWindow, enabled: bool) -> None:
    """First/next/last browse every worker even when the active tool has no data.

    Args:
        window: Disposable integrated window; worker y has no saved assessment.
        enabled: Browser preference must never restrict worker navigation.

    Returns:
        None.
    """
    window.main_navigation.context_disclosure.setChecked(enabled)
    nav = window.main_navigation
    nav.nav_buttons[2].click()
    assert nav.workers.currentData() == "x"
    nav.nav_buttons[2].click()
    assert nav.workers.currentData() == "y"
    assert window.assessment_navigation.view.saved is False
    assert window.results_sidebar.assessment_status_label.text() == "No assessment"
    assert window.assessment_navigation.view.workplace is None
    nav.nav_buttons[0].click()
    assert nav.workers.currentData() == "w"


def test_worker_navigation_uses_alphabetical_default_despite_remembered_context(
    window: LifftWindow,
) -> None:
    """Worker navigation ignores last-used context and chooses the first saved location.

    Args:
        window: Disposable integrated window and preference file.

    Returns:
        None.
    """
    add_night_context(window)
    browser = window.assessment_navigation
    browser.select(
        "w",
        AssessmentKind.LIFFT,
        window.blank_active_source,
        workplace=STATION.at_shift("Night"),
        explicit=True,
    )
    window.refresh()
    window.navigate_worker("x")
    window.navigate_worker("w")
    assert browser.view.workplace.shift_id == "Day"
    assert window.active_source().tasks[0].lever_arm == 12
    browser._memory.clear()
    window.navigate_worker("x")
    window.navigate_worker("w")
    assert browser.view.workplace.shift_id == "Day"
    window.main_navigation.context_disclosure.setChecked(False)
    before = browser.view
    assert browser.view == before
    window.navigate_worker("x")
    assert browser.view.workplace.shift_id == "Day"
    assert browser.view.saved
    window.main_navigation.context_disclosure.setChecked(True)
    assert browser.view.workplace.shift_id == "Day"


@pytest.mark.parametrize("save_as", [False, True])
def test_tool_drafts_survive_switching_and_save(
    window: LifftWindow, tmp_path: Path, save_as: bool
) -> None:
    """LiFFT and new DUET drafts survive tab switching and explicit Save/Save As.

    Args:
        window: Disposable classified main-window fixture.
        tmp_path: Pytest-owned copy destination.
        save_as: True exercises copy publication; False saves the current project.

    Returns:
        None.
    """
    workspace = window.presenter.workspace
    original_path = workspace.location
    enter(window, 0, 0, "17")
    with patch.object(
        window, "dirty_choice", side_effect=AssertionError("Tab switch requested Save")
    ):
        window.select_tool(1)
        assert window.active_kind() is AssessmentKind.DUET
        assert window.assessment_navigation.view.workplace == STATION.at_shift("Day")
        enter_duet(window.duet_panel, 0, "75")
        window.select_tool(0)
    assert window.task_panel.inputs[0][0].text() == "17.0"
    assert workspace.has_unsaved_changes
    assert len(workspace.read_history().history.entries) == 3
    with AssessmentProjectFile.open(Path(original_path)) as saved:
        assert len(saved.load_history().entries) == 2
    if save_as:
        destination = tmp_path / "all_tabs.ergprj"
        with (
            patch.object(window, "choose_file", return_value=str(destination)),
            patch.object(window, "choose_project_details", return_value=("Copy", "")),
        ):
            window.save_project_as()
        with AssessmentProjectFile.open(Path(original_path)) as original:
            assert len(original.load_history().entries) == 2
    else:
        window.save_project()
    assert not workspace.has_unsaved_changes
    history = workspace.read_history().history
    assert len(history.entries) == 3
    window.select_tool(1)
    assert window.duet_panel.inputs[0][1].text() == "75"
    with AssessmentProjectFile.open(Path(workspace.location)) as saved:
        duet = next(
            e for e in saved.load_history().entries if e.kind is AssessmentKind.DUET
        )
        assert (
            saved.load(replace(workspace.active.document, document_id=duet.document_id))
            .tasks[0]
            .repetitions
            == 75
        )


@pytest.mark.parametrize("accept", [False, True])
def test_same_job_warning_precedes_creation(window: LifftWindow, accept: bool) -> None:
    """Confirm same-Job creation; cancellation preserves drafts and saved data.

    Args:
        window: Disposable fixture with one saved day assessment.
        accept: Yes/No consent for a night assessment belonging to the same Job.

    Returns:
        None.
    """
    add_night_context(window, saved=False)
    browser = window.assessment_navigation
    browser.select(
        "w",
        AssessmentKind.LIFFT,
        window.blank_active_source,
        workplace=STATION.at_shift("Night"),
        explicit=True,
    )
    window.refresh()
    assert window.results_sidebar.assessment_status_label.text() == "New assessment"
    enter(window, 0, 0, "25")
    window.task_panel.commit_inputs()
    with patch.object(
        QMessageBox,
        "question",
        return_value=QMessageBox.Yes if accept else QMessageBox.No,
    ) as question:
        window.save_project()
    assert question.call_count == 1
    message = question.call_args.args[2]
    assert "Job j" in message and "Day" in message
    assert len(window.presenter.workspace.read_history().history.entries) == (
        3 if accept else 2
    )
    with AssessmentProjectFile.open(Path(window.presenter.workspace.location)) as saved:
        assert len(saved.load_history().entries) == (3 if accept else 2)
    assert window.presenter.workspace.has_unsaved_changes is not accept


@pytest.mark.parametrize("language", list(Language))
def test_context_picker_saved_new_labels_and_menu(
    window: LifftWindow, language: Language
) -> None:
    """Context tree states and setup menu use packaged actions and exact ownership.

    Args:
        window: Disposable integrated window with one existing and one missing context.
        language: English or Spanish, including the initially selected action caption.

    Returns:
        None.
    """
    from ergotools.presentation.assignment_selection import AssignmentSelector
    from ergotools.presentation.desktop.assessment_context_dialog import (
        AssessmentContextDialog,
    )

    add_night_context(window, saved=False)
    workspace = window.presenter.workspace
    selector = AssignmentSelector(workspace)
    dialog = AssessmentContextDialog(
        selector,
        selector.refresh(),
        "w",
        AssessmentKind.LIFFT,
        (),
        window.icons,
        shifts=("Day", "Night"),
        saved_assignments=frozenset({1}),
        current=STATION.at_shift("Day"),
        language=language,
        parent=window,
    )
    try:
        assert dialog.use.text() == (
            "Abrir evaluación" if language is Language.SPANISH else "Open assessment"
        )
        leaf = dialog.tree.topLevelItem(0).child(0).child(0).child(0)
        assert leaf.text(3) == ("Guardada" if language is Language.SPANISH else "Saved")
        dialog.tree.setCurrentItem(leaf)
        assert dialog.use.text() == (
            "Abrir evaluación" if language is Language.SPANISH else "Open assessment"
        )
        dialog.shift.setCurrentText("Night")
        leaf = dialog.tree.topLevelItem(0).child(0).child(0).child(0)
        assert leaf.text(3) == (
            "Sin crear" if language is Language.SPANISH else "Not created"
        )
        dialog.tree.setCurrentItem(leaf)
        assert dialog.selected_assignment.assignment.assignment_id == 3
        assert dialog.use.text() == (
            "Crear evaluación" if language is Language.SPANISH else "Create assessment"
        )
    finally:
        dialog.close()
    menu = window._assessment_menu
    assert menu.work_setup.title() == "Workplace"
    assert menu.organization.icon().isNull() is False
    assert menu.jobs.icon().isNull() is False
    assert (
        window.main_navigation.toolbar_actions["jobs"]
        in window.main_navigation.toolbar.actions()
    )
    window.language = Language.SPANISH
    window.translate()
    window.refresh_navigation()
    assert menu.work_setup.title() == "Lugar de trabajo"
    assert window.main_navigation.location_browser.title() == "Evaluación"


def test_worker_navigation_retains_the_old_worker_draft(window: LifftWindow) -> None:
    """Worker navigation retains edits and never requests a local Save or Discard.

    Args:
        window: Disposable integrated window with two classified workers.

    Returns:
        None.
    """
    enter(window, 0, 0, "99")
    with patch.object(window, "dirty_choice", return_value=CloseChoice.DISCARD):
        window.navigate_worker("x")
    window.navigate_worker("w")
    assert window.active_source().tasks[0].lever_arm == 99
    assert window.presenter.workspace.has_unsaved_changes


def test_first_save_rolls_back_source_owner_and_result(window: LifftWindow) -> None:
    """A failed result write retains accepted private inputs and permits one Save retry.

    Args:
        window: Disposable classified main-window fixture with no saved DUET data.

    Returns:
        None.
    """
    from ergotools.infrastructure.saved_result_store import SavedResultStore

    window.select_tool(1)
    enter_duet(window.duet_panel, 0, "75")
    window.history_actions.refresh()
    window.duet_panel.calculate_button.click()
    workspace = window.presenter.workspace
    active = workspace.active
    result = window.current_result_snapshot()
    assert result is not None and workspace.has_unsaved_changes
    with (
        patch.object(
            SavedResultStore, "write", side_effect=OSError("disk write failed")
        ),
        pytest.raises(OSError, match="disk write failed"),
    ):
        workspace.save(result)
    assert len(workspace.read_history().history.entries) == 3
    assert workspace.has_unsaved_changes
    with AssessmentProjectFile.open(Path(workspace.location)) as saved:
        assert len(saved.load_history().entries) == 2
    workspace.save(result)
    assert len(workspace.read_history().history.entries) == 3
    assert not active.is_dirty


def test_empty_project_workers_are_browsable(
    window: LifftWindow, tmp_path: Path
) -> None:
    """An assessment-free project opens without a picker or implicit source creation.

    Args:
        window: Disposable integrated main-window owner.
        tmp_path: Pytest-owned empty project destination.

    Returns:
        None; worker and tool navigation remain available without writing assessments.
    """
    workspace = window.presenter.workspace
    hierarchy = workspace.read_hierarchy().hierarchy
    jobs = workspace.read_jobs().jobs
    path = tmp_path / "empty_assessments.ergprj"
    with AssessmentProjectFile.create_with_job_risks(
        path, workspace.project_metadata
    ) as project:
        project.save_hierarchy(hierarchy)
        project.save_jobs(jobs)
    with patch.object(
        window, "choose_item", side_effect=AssertionError("Picker opened")
    ):
        window.open_project_location(str(path))
    assert workspace.location == str(path)
    assert window.main_navigation.workers.currentData() == "w"
    assert window.results_sidebar.assessment_status_label.text() == "No assessment"
    window.navigate_worker("y")
    window.select_tool(1)
    assert window.main_navigation.workers.currentData() == "y"
    assert window.active_kind() is AssessmentKind.DUET
    assert not workspace.read_history().history.entries
    assert not workspace.has_unsaved_changes


@pytest.mark.parametrize("accept", [False, True])
def test_context_create_preserves_same_job_warning(
    window: LifftWindow, accept: bool
) -> None:
    """Explicit context creation preserves existing same-Job consent and identity.

    Args:
        window: Disposable integrated window with a day assessment and an empty
            night assignment.
        accept: Whether to approve a separate assessment for the same Job elsewhere.

    Returns:
        None; No leaves the day view and owner count unchanged, while Yes creates only
        the selected night/tool assessment privately until main Save.
    """
    from PyQt5.QtWidgets import QDialog

    from ergotools.presentation.desktop.assessment_context_dialog import (
        AssessmentContextDialog,
    )

    add_night_context(window, saved=False)
    workspace = window.presenter.workspace
    original = workspace.active.document
    before = Path(workspace.location).read_bytes()

    def choose_night(dialog: AssessmentContextDialog) -> int:
        """Accept the missing night assessment through the explicit Create action.

        Args:
            dialog: Exact worker/tool picker owned by the main window.

        Returns:
            Accepted context intent; no mutation occurs inside the picker.
        """
        dialog.shift.setCurrentText("Night")
        leaf = dialog.tree.topLevelItem(0).child(0).child(0).child(0)
        dialog.tree.setCurrentItem(leaf)
        assert dialog.use.text() == "Create assessment"
        dialog.use.click()
        assert dialog.result() == QDialog.Accepted
        return dialog.result()

    with (
        patch.object(AssessmentContextDialog, "exec_", choose_night),
        patch.object(
            QMessageBox,
            "question",
            return_value=QMessageBox.Yes if accept else QMessageBox.No,
        ) as question,
    ):
        window.select_navigation_context()
    assert question.call_count == 1
    assert "Job j" in question.call_args.args[2]
    assert "Day" in question.call_args.args[2]
    assert len(workspace.read_history().history.entries) == (3 if accept else 2)
    assert (workspace.active.document == original) is not accept
    if accept:
        assert window.assessment_navigation.view.assignment_id == 3
        assert len(workspace.active.state.tasks) == 15
    assert Path(workspace.location).read_bytes() == before


def test_context_create_keeps_inputs_already_entered_in_that_preview(
    window: LifftWindow,
) -> None:
    """Explicit creation must not replace data already entered at the chosen context.

    Args:
        window: Disposable integrated window with an uncreated night assignment.

    Returns:
        None; staging reuses the entered source identity and value instead of inserting
        a second blank assessment for the same assignment/tool.
    """
    from ergotools.presentation.desktop.assessment_context_dialog import (
        AssessmentContextDialog,
    )

    add_night_context(window, saved=False)
    browser = window.assessment_navigation
    browser.select(
        "w",
        AssessmentKind.LIFFT,
        window.blank_active_source,
        workplace=STATION.at_shift("Night"),
        explicit=True,
    )
    window.refresh()
    identity = window.presenter.workspace.active.document.document_id
    enter(window, 0, 0, "25")
    window.task_panel.commit_inputs()

    def choose_current(dialog: AssessmentContextDialog) -> int:
        """Accept the exact current assignment after input acceptance has staged it.

        Args:
            dialog: Context chooser opened through the normal pending-input boundary.

        Returns:
            Accepted Open/Create intent; the existing entered source remains exact.
        """
        assert dialog.selected_assignment.assignment.assignment_id == 3
        dialog.use.click()
        return dialog.result()

    with (
        patch.object(AssessmentContextDialog, "exec_", choose_current),
        patch.object(QMessageBox, "question", return_value=QMessageBox.Yes),
    ):
        window.select_navigation_context()
    workspace = window.presenter.workspace
    assert workspace.active.document.document_id == identity
    assert workspace.active.state.tasks[0].lever_arm == 25
    assert (
        sum(
            e.assignment_id == 3 and e.kind is AssessmentKind.LIFFT
            for e in workspace.read_history().history.entries
        )
        == 1
    )

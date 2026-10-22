"""Worker edits retain context; assessment creation requires an explicit selection.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QCoreApplication, QEvent, Qt, QTimer
from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.session import DocumentKey
from ergotools.application.settings import Language
from ergotools.bootstrap import create_window
from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.assessment_context_dialog import (
    AssessmentContextDialog,
)
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.worker_management_dialog import (
    WorkerManagementDialog,
)
from ergotools.presentation.desktop.workplace_assignment_dialog import (
    WorkplaceAssignmentDialog,
)
from tests.test_optional_assessment_context import META
from tests.test_saved_tool_data import KINDS
from tests.test_saved_tool_data import window as window
from tests.test_workplace_assignment_workflow import STATION, seed_workplace_source


@pytest.mark.parametrize("index", [0, 1, 2])
def test_worker_modal_retains_edit_without_switching_assessment_before_main_save(
    window: LifftWindow, index: int
) -> None:
    """Closing the integrated modal retains edits and the previously active assessment.

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
    path = Path(workspace.location)
    before_hierarchy = workspace.read_hierarchy().hierarchy
    before_history = workspace.read_history().history
    before_jobs = workspace.read_jobs().jobs
    prior_document = workspace.active.document
    source = workspace.active.state
    closed = []

    def choose_placement() -> None:
        """Select the first real placement row and accept its exact opaque ownership.

        Args:
            None.

        Returns:
            None.
        """
        picker = QApplication.activeModalWidget()
        assert isinstance(picker, WorkplaceAssignmentDialog)
        placement = next(p for p in picker._jobs.placements if p.active)
        picker.select_workplace(placement.workplace, placement.placement_id)
        picker.accept_button.click()

    def choose_worker() -> None:
        """Select worker x and retain workplace edits without assessment intent.

        Select saved worker x, retain unsaved first-name text, add the exact placement
        and close while retaining the edit without changing the active assessment.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, WorkerManagementDialog)
        assert dialog.parent() is window
        dialog.worker_id_combo.setCurrentIndex(dialog.worker_id_combo.findText("x"))
        dialog.first_name_input.setText("Accepted worker edit")
        QTimer.singleShot(0, choose_placement)
        dialog.add_assignment_button.click()
        assert dialog.assignment_table.rowCount() == 1
        assert dialog.first_name_input.text() == "Accepted worker edit"
        closed.append(True)
        dialog.close_button.click()

    QTimer.singleShot(0, choose_worker)
    window.open_worker_management()
    assert closed == [True]
    assert workspace.active.document == prior_document
    assert window.active_kind() is KINDS[index]
    assert window._worker_selection == (workspace.location, "x")
    with AssessmentProjectFile.open(path) as project:
        assert project.load_hierarchy() == before_hierarchy
        assert project.load_history() == before_history
        assert project.load_jobs() == before_jobs
        assert project.load(prior_document) == source
    assert workspace.active.state == source
    accepted = workspace.read_hierarchy().hierarchy
    assert next(w for w in accepted.work.workers if w.worker_id == "x").first_name == (
        "Accepted worker edit"
    )
    window.save_project()
    with AssessmentProjectFile.open(path) as project:
        assert project.load_hierarchy() == accepted
        assert project.load_history() == before_history
        assert project.load_jobs() == before_jobs
        assert project.load(prior_document) == source


@pytest.mark.parametrize("kind", list(AssessmentKind))
@pytest.mark.parametrize("language", list(Language))
def test_multiple_workplaces_require_exact_context_creation(
    tmp_path: Path, kind: AssessmentKind, language: Language
) -> None:
    """Three assignment additions never choose which assessment should be created.

    Args:
        tmp_path: Disposable native project and preference directory.
        kind: LiFFT, DUET or ST, with an existing calculated standalone source.
        language: English or Spanish labels; stored identities remain literal.

    Returns:
        None; modal close, explicit creation, reopen and existing-context navigation
        preserve standalone inputs/results and create only the chosen assignment/tool.
    """
    path = seed_workplace_source(tmp_path, kind)
    view = create_window(
        tmp_path / "settings.json", original_navigation=True, enable_vtk=False
    )
    workspace = view.presenter.workspace
    workspace.switch(str(path), "source")
    view.language = language
    view.refresh()
    view.show()
    QApplication.processEvents()
    browser = view.assessment_navigation
    browser.select("A", kind, lambda: view._blank_kind(kind), explicit=True)
    view.refresh()
    before = path.read_bytes()
    with AssessmentProjectFile.open(path) as saved:
        original = saved.load(workspace.active.document)
        result = saved.load_saved_result(workspace.active.document)
    places = (
        STATION.at_shift("1"),
        replace(STATION, station_id="ST02").at_shift("1"),
        STATION.at_shift("2"),
    )

    def add_workplaces(dialog: WorkerManagementDialog) -> int:
        """Accept three distinct No Job workplaces in the real worker editor.

        Args:
            dialog: Worker Management owned by the integrated host.

        Returns:
            Accepted close result, without any assessment action or prompt.
        """
        assert dialog.worker_id_combo.currentText() == "A"
        for place in places:

            def select_place(
                picker: WorkplaceAssignmentDialog, workplace: WorkplaceContext = place
            ) -> int:
                """Choose the current exact workplace/shift without a Job.

                Args:
                    picker: Real nested workplace picker.
                    workplace: Bound loop choice, independent of later additions.

                Returns:
                    Accepted result carrying workplace intent only.
                """
                picker.select_workplace(workplace, None)
                picker.accept_button.click()
                return picker.result()

            with patch.object(WorkplaceAssignmentDialog, "exec", select_place):
                dialog.add_assignment_button.click()
        assert dialog.assignment_table.rowCount() == 3
        dialog.close_button.click()
        return dialog.result()

    try:
        with (
            patch.object(WorkerManagementDialog, "exec", add_workplaces),
            patch.object(
                QMessageBox,
                "question",
                side_effect=AssertionError(
                    "Closing workers must not ask about assessment"
                ),
            ),
        ):
            view.open_worker_management()
        assert workspace.active.document.document_id == "source"
        assert browser.view.workplace is None
        assert len(workspace.read_history().history.entries) == 1
        assignments = workspace.read_jobs().jobs.assignments
        assert len(assignments) == 3
        assert all(a.placement_id is None for a in assignments)
        assert path.read_bytes() == before
        view.save_project()
        with AssessmentProjectFile.open(path) as saved:
            assert saved.load_jobs().assignments == assignments
            assert len(saved.load_history().entries) == 1
            assert saved.load_saved_result(workspace.active.document) == result
        baseline = path.read_bytes()
        chosen = assignments[0]
        view._worker_selection = (workspace.location, "A")

        def select_context(dialog: AssessmentContextDialog) -> int:
            """Create the first assignment's assessment, never the last added one.

            Args:
                dialog: Exact worker/tool context picker.

            Returns:
                Explicit acceptance of Create/Open assessment for the first workplace.
            """
            dialog.shift.setCurrentText(chosen.worker.workplace.shift_id)
            leaf = dialog.tree.topLevelItem(0).child(0).child(0).child(0)
            assert (
                leaf.data(0, Qt.UserRole).assignment.assignment_id
                == chosen.assignment_id
            )
            dialog.tree.setCurrentItem(leaf)
            assert "A" in dialog.findChild(QLabel, "supportingText").text()
            dialog.use.click()
            return dialog.result()

        # Cancel is inert even after selecting a different workplace.
        with patch.object(
            AssessmentContextDialog, "exec_", return_value=QDialog.Rejected
        ):
            view.select_navigation_context()
        assert workspace.active.document.document_id == "source"
        assert path.read_bytes() == baseline
        with patch.object(AssessmentContextDialog, "exec_", select_context):
            view.select_navigation_context()
        entries = workspace.read_history().history.entries
        assert len(entries) == 2
        created = next(e for e in entries if e.assignment_id is not None)
        assert (created.assignment_id, created.worker_id, created.kind) == (
            chosen.assignment_id,
            "A",
            kind,
        )
        assert browser.view.assignment_id == chosen.assignment_id
        assert browser.view.saved
        assert len(workspace.active.state.tasks) == 15
        assert path.read_bytes() == baseline
        shared = view.history_actions.shared
        assert shared is not None
        view.activateWindow()
        view.setFocus()
        QApplication.processEvents()
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Cancel):
            shared.undo_action.trigger()
        assert workspace.read_history().history.entries == entries
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            shared.undo_action.trigger()
        assert len(workspace.read_history().history.entries) == 1
        assert len(workspace.read_jobs().jobs.assignments) == 3
        shared.redo_action.trigger()
        assert workspace.read_history().history.entries == entries
        view.save_project()
        with AssessmentProjectFile.open(path) as saved:
            assert saved.load_history().entries == entries
            key = DocumentKey(META.project_id, "source")
            assert saved.load(key) == original
            assert saved.load_saved_result(key) == result
            assert len(saved.load_jobs().assignments) == 3
        workspace.close(choice=CloseChoice.DISCARD)
        workspace.switch(str(path), "source")
        browser.view = None
        view.refresh()
        browser.select("A", kind, lambda: view._blank_kind(kind), explicit=True)
        view.refresh()
        with patch.object(AssessmentContextDialog, "exec_", select_context):
            view.select_navigation_context()
        assert workspace.active.document.document_id == created.document_id
        assert len(workspace.read_history().history.entries) == 2
    finally:
        workspace.close(choice=CloseChoice.DISCARD)
        view.close()
        view.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        QApplication.processEvents()

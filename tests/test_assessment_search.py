"""Original Search filtering and exact historical selection over real projects.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.worker_details import WorkerDetails
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.worker_search_dialog import (
    WorkerSearchDialog,
    search_assessments,
)
from tests.test_saved_tool_data import window as window


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_search_filters_and_exact_sorted_identity(
    window: LifftWindow, kind: AssessmentKind
) -> None:
    """Text, surname, ancestry and model filters intersect without losing owner IDs.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
            captions are not keys.

    Returns:
        None.
    """
    workspace = window.presenter.workspace
    hierarchy = workspace.read_hierarchy().hierarchy
    workers = tuple(
        replace(
            w,
            first_name="Ana",
            last_name="Álvarez" if w.worker_id == "w" else "Baker",
            details=WorkerDetails(birth_date="1990-12-31", sex="Female"),
        )
        for w in hierarchy.work.workers
    )
    hierarchy = replace(hierarchy, work=replace(hierarchy.work, workers=workers))
    rows = search_assessments(
        hierarchy,
        workspace.read_jobs().jobs,
        workspace.read_history().history,
        kind,
        year=2026,
    )
    assert len(rows) == 3 and all(
        row.selection.kind is kind and row.age == "36" for row in rows
    )
    dialog = WorkerSearchDialog(rows, hierarchy, kind, window.icons, parent=window)
    try:
        assert dialog.table.rowCount() == 3 and not dialog.use_button.isEnabled()
        dialog.accept_selection()
        assert dialog.result() == 0
        dialog.search_input.setText("aNa")
        assert dialog.table.rowCount() == 3
        dialog.set_alphabet("B")
        assert dialog.table.rowCount() == 1
        dialog.search_input.setText("not-present")
        assert dialog.table.rowCount() == 0 and not dialog.use_button.isEnabled()
        dialog.search_input.clear()
        dialog.set_alphabet("All")
        branch = dialog.workplace_tree.topLevelItem(1)
        dialog.workplace_tree.setCurrentItem(branch)
        assert dialog.table.rowCount() == 3
        dialog.active_workplace = ("absent",)
        dialog.apply_filters()
        assert dialog.table.rowCount() == 0
        dialog.active_workplace = ()
        dialog.apply_filters()
        dialog.table.sortItems(0, Qt.DescendingOrder)
        index = next(
            i
            for i in range(3)
            if dialog.table.item(i, 0).data(Qt.UserRole).assignment_id == 2
        )
        dialog.table.selectRow(index)
        assert dialog.selected.assignment_id == 2 and dialog.use_button.isEnabled()
        dialog.accept_selection()
        assert dialog.result() == dialog.Accepted
    finally:
        dialog.close()


@pytest.mark.parametrize("index", [0, 1, 2])
def test_main_search_cancel_and_load_dirty_policy(
    window: LifftWindow, index: int
) -> None:
    """Actual Search preserves invalid Cancel text and honors Save/Discard/Cancel.

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
    before = active.state
    panel = window.task_panel if index == 0 else window.secondary_panel()
    field = panel.inputs[0][2 if index == 0 else -1]
    field.setText("bad")
    field.textEdited.emit("bad")

    def dismiss() -> None:
        """Verify three real search rows and reject the modal.

        Verify three real search rows and reject the modal without accepting pending
        assessment text.

        Args:
            None.

        Returns:
            None.
        """
        modal = QApplication.activeModalWidget()
        assert isinstance(modal, WorkerSearchDialog)
        assert modal.table.rowCount() == 3
        modal.reject()

    QTimer.singleShot(50, dismiss)
    window.navigation_action(window.search_assessment)
    assert workspace.active is active and active.state is before
    assert field.text() == "bad" and panel.pending

    def select() -> None:
        """Select exact assignment 2 from sorted item data.

        Select exact assignment 2 from sorted item data and activate the original Use
        action.

        Args:
            None.

        Returns:
            None.
        """
        modal = QApplication.activeModalWidget()
        assert isinstance(modal, WorkerSearchDialog)
        row = next(
            i
            for i in range(3)
            if modal.table.item(i, 0).data(Qt.UserRole).assignment_id == 2
        )
        modal.table.selectRow(row)
        modal.use_button.click()

    field.setText("500")
    field.textEdited.emit("500")
    with patch.object(
        window,
        "dirty_choice",
        side_effect=AssertionError("Search must not request Save"),
    ):
        QTimer.singleShot(50, select)
        window.navigation_action(window.search_assessment)
    assert workspace.active.document.document_id == f"{list(AssessmentKind)[index]}-2"
    assert workspace.active.state.tasks[0].repetitions == 200
    with AssessmentProjectFile.open(Path(workspace.location)) as project:
        assert project.load(active.document).tasks[0].repetitions == 100
    window.save_project()
    with AssessmentProjectFile.open(Path(workspace.location)) as project:
        assert project.load(active.document).tasks[0].repetitions == 500

    def select_other_worker() -> None:
        """Select exact assignment 3 belonging to another saved worker.

        Select exact assignment 3 belonging to another saved worker through typed search
        item data.

        Args:
            None.

        Returns:
            None.
        """
        modal = QApplication.activeModalWidget()
        assert isinstance(modal, WorkerSearchDialog)
        row = next(
            i
            for i in range(modal.table.rowCount())
            if modal.table.item(i, 0).data(Qt.UserRole).assignment_id == 3
        )
        modal.table.selectRow(row)
        modal.use_button.click()

    with patch.object(window, "dirty_choice", return_value=CloseChoice.DISCARD):
        QTimer.singleShot(50, select_other_worker)
        window.navigation_action(window.search_assessment)
    assert workspace.active.document.document_id == f"{list(AssessmentKind)[index]}-3"
    assert window.main_navigation.workers.currentData() == "x"


@pytest.mark.parametrize("language", list(Language))
def test_search_empty_and_localized(window: LifftWindow, language: Language) -> None:
    """Empty results keep hierarchy navigation and a disabled accept interlock.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    dialog = WorkerSearchDialog(
        (),
        window.presenter.workspace.read_hierarchy().hierarchy,
        AssessmentKind.TST,
        window.icons,
        language=language,
        parent=window,
    )
    try:
        assert dialog.table.rowCount() == 0 and not dialog.use_button.isEnabled()
        assert dialog.alphabet_buttons["All"].isEnabled()
        assert not dialog.alphabet_buttons["Z"].isEnabled()
        assert ("Buscar" in dialog.windowTitle()) is (language is Language.SPANISH)
        assert dialog.minimumWidth() == 900 and dialog.minimumHeight() == 560
    finally:
        dialog.close()


def test_search_rejects_foreign_catalog(window: LifftWindow) -> None:
    """Cross-project snapshots fail before a dialog or source selection exists.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    workspace = window.presenter.workspace
    hierarchy = workspace.read_hierarchy().hierarchy
    with pytest.raises(ValueError, match="different projects"):
        search_assessments(
            replace(hierarchy, work=replace(hierarchy.work, project_id="foreign")),
            workspace.read_jobs().jobs,
            workspace.read_history().history,
            AssessmentKind.LIFFT,
            year=2026,
        )

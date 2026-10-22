"""Saved-tool modal filtering, identity and integrated dirty-source decisions.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QCoreApplication, QEvent, Qt, QTimer
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QApplication

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.bootstrap import create_window
from ergotools.domain.assessment_history import AssessmentHistory, AssignmentAssessment
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.job_catalog import WorkerJobAssignment
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.tool_data_dialog import ToolDataDialog
from ergotools.presentation.saved_tool_options import saved_tool_options
from tests.test_history_persistence import HIERARCHY, JOBS, META, OWNER

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])
# Original stable LiFFT/DUET/ST ordering used to verify cross-tool isolation and modal
# filtering.
KINDS = (AssessmentKind.LIFFT, AssessmentKind.DUET, AssessmentKind.TST)


@pytest.fixture
def window(tmp_path: Path) -> Iterator[LifftWindow]:
    """Two same-workplace owners and another worker expose identity/filter mistakes.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Yields:
        Live synthetic integrated window; fixture cleanup closes the window and releases
        its temporary project after the test.
    """
    path = tmp_path / "saved.ergprj"
    jobs = replace(
        JOBS,
        assignments=(
            *JOBS.assignments,
            WorkerJobAssignment(2, OWNER, 2, active=False),
            WorkerJobAssignment(3, replace(OWNER, worker_id="x"), 1),
        ),
    )
    with AssessmentProjectFile.create_with_job_risks(path, META) as project:
        project.save_hierarchy(HIERARCHY)
        project.save_jobs(jobs)
        for assignment in (1, 2, 3):
            for kind, source in (
                (
                    KINDS[0],
                    LifftDraft(
                        META.default_units, (LifftTask("l", 12, 20, assignment * 100),)
                    ),
                ),
                (KINDS[1], DuetDraft((DuetTask("d", 6, assignment * 100),))),
                (
                    KINDS[2],
                    TstDraft(
                        META.default_units,
                        (
                            TstTask(
                                "s", TstDirection.DOWNWARD, 12, 20, assignment * 100
                            ),
                        ),
                    ),
                ),
            ):
                project.create_historical_assessment(
                    AssignmentAssessment(
                        f"{kind}-{assignment}",
                        assignment,
                        kind,
                        worker_id=next(
                            a.worker.worker_id
                            for a in jobs.assignments
                            if a.assignment_id == assignment
                        ),
                    ),
                    source,
                )
        with pytest.raises(ValueError, match="assignment/tool"):
            project.create_historical_assessment(
                AssignmentAssessment(
                    "old",
                    1,
                    KINDS[0],
                    worker_id=next(
                        a.worker.worker_id
                        for a in jobs.assignments
                        if a.assignment_id == 1
                    ),
                ),
                LifftDraft(META.default_units),
            )
    view = create_window(tmp_path / "settings.json", original_navigation=True)
    view.presenter.workspace.switch(str(path), "lifft-1")
    view.refresh()
    view.show()
    _APP.processEvents()
    yield view
    view.presenter.workspace.close(choice=CloseChoice.DISCARD)
    view.close()
    # Dispose this fixture's widget tree and filesystem-model children before the
    # next test starts; Python cycle collection must not destroy them mid-event.
    view.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _APP.processEvents()


@pytest.mark.parametrize("index", [0, 1, 2])
def test_saved_grid_invalid_text_and_retained_project_edits(
    window: LifftWindow, index: int
) -> None:
    """Saved-data browsing protects text and retains valid edits until main Save.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        index: Zero-based selected input/row/case index used by the parametrized
            regression.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(index)
    panel = window.task_panel if index == 0 else window.secondary_panel()
    active = window.presenter.workspace.active
    before = active.state
    field = panel.inputs[0][-1]
    # LiFFT inputs append a read-only moment field; repetitions is index 2.
    if index == 0:
        field = panel.inputs[0][2]
    field.setText("bad")
    field.textEdited.emit("bad")
    assert panel.context_button.isEnabled()

    def close() -> None:
        """Verify exact saved assignment IDs 1/2 in the actual owned browser.

        Verify exact saved assignment IDs 1/2 in the actual owned browser and click
        Close without loading.

        Args:
            None.

        Returns:
            None.
        """
        modal = QApplication.activeModalWidget()
        assert isinstance(modal, ToolDataDialog) and modal.parent() is window
        assert modal.table.rowCount() == 2
        assert {
            modal.table.item(r, 0).data(Qt.UserRole).assignment_id for r in range(2)
        } == {1, 2}
        modal.close_button.click()

    QTimer.singleShot(0, close)
    panel.context_button.click()
    assert active.state is before and field.text() == "bad" and panel.pending

    def load() -> None:
        """Sort the actual browser, resolve exact assignment 2 from item data.

        Sort the actual browser, resolve exact assignment 2 from item data and click
        Load.

        Args:
            None.

        Returns:
            None.
        """
        modal = QApplication.activeModalWidget()
        assert isinstance(modal, ToolDataDialog)
        modal.table.sortItems(0, Qt.DescendingOrder)
        row = next(
            r
            for r in range(2)
            if modal.table.item(r, 0).data(Qt.UserRole).assignment_id == 2
        )
        modal.table.selectRow(row)
        modal.load_button.click()

    QTimer.singleShot(0, load)
    panel.context_button.click()
    assert window.presenter.workspace.active is active and field.text() == "bad"
    field.setText("500")
    field.textEdited.emit("500")
    with patch.object(window, "dirty_choice") as departure:
        QTimer.singleShot(0, load)
        panel.context_button.click()
    departure.assert_not_called()
    workspace = window.presenter.workspace
    assert workspace.active.document.document_id == f"{KINDS[index]}-2"
    assert workspace.active.state.tasks[0].repetitions == 200
    assert not window.results_sidebar.risk_gauge.has_value
    with AssessmentProjectFile.open(Path(workspace.location)) as project:
        assert project.load(active.document).tasks[0].repetitions == 100
    window.save_project()
    with AssessmentProjectFile.open(Path(workspace.location)) as project:
        assert project.load(active.document).tasks[0].repetitions == 500
        history = project.load_history()
        assert (
            history.current_for(1, KINDS[index]).document_id
            == active.document.document_id
        )
        assert (
            history.current_for(2, KINDS[index]).document_id
            == workspace.active.document.document_id
        )
    # Returning to the first owner retains the second edit without writing the file.
    panel = window.task_panel if index == 0 else window.secondary_panel()
    field = panel.inputs[0][2 if index == 0 else -1]
    field.setText("999")
    field.textEdited.emit("999")

    def return_first() -> None:
        """Resolve exact assignment 1 from sorted item data and click Load.

        Resolve exact assignment 1 from sorted item data and click Load to return to the
        original owner.

        Args:
            None.

        Returns:
            None.
        """
        modal = QApplication.activeModalWidget()
        row = next(
            r
            for r in range(2)
            if modal.table.item(r, 0).data(Qt.UserRole).assignment_id == 1
        )
        modal.table.selectRow(row)
        modal.load_button.click()

    with patch.object(window, "dirty_choice") as departure:
        QTimer.singleShot(0, return_first)
        panel.context_button.click()
    departure.assert_not_called()
    second = next(
        e.document
        for e in workspace.list_assessments()
        if e.document.document_id == f"{KINDS[index]}-2"
    )
    assert workspace.assessment_source(second.document_id).tasks[0].repetitions == 999
    assert workspace.active.state.tasks[0].repetitions == 500
    with AssessmentProjectFile.open(Path(workspace.location)) as project:
        assert project.load(second).tasks[0].repetitions == 200
        assert (
            next(
                e
                for e in project.list_assessments()
                if e.document.document_id == f"{KINDS[index]}-2"
            ).task_count
            == 1
        )


def test_empty_and_spanish_selection_warning(window: LifftWindow) -> None:
    """Empty browser rejects Load with the localized reference warning.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    dialog = ToolDataDialog((), language=Language.SPANISH, parent=window)
    with patch(
        "ergotools.presentation.desktop.tool_data_dialog.QMessageBox.warning"
    ) as warning:
        dialog.load_button.click()
    assert warning.call_args.args[1:] == (
        "Error de selección",
        "Seleccione una fila antes de continuar.",
    )
    assert dialog.selected is None and dialog.result() == 0
    assert dialog.table.horizontalHeaderItem(5).text() == "Herramienta"
    metrics = QFontMetrics(dialog.table.horizontalHeader().font())
    for column in range(6):
        text = dialog.table.horizontalHeaderItem(column).text()
        assert dialog.table.columnWidth(column) >= metrics.horizontalAdvance(text) + 24
    dialog.close()


def test_options_reject_foreign_history_and_omit_noncurrent(
    window: LifftWindow,
) -> None:
    """Filter current versions by worker/tool, retaining closed owners.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    workspace = window.presenter.workspace
    jobs = workspace.read_jobs().jobs
    history = workspace.read_history().history
    options = saved_tool_options(jobs, history, "w", KINDS[0])
    assert [o.assignment_id for o in options] == [1, 2]
    assert all(o.document_id != "old" for o in options)
    assert saved_tool_options(jobs, history, "missing", KINDS[0]) == ()
    with pytest.raises(ValueError):
        saved_tool_options(jobs, AssessmentHistory("foreign"), "w", KINDS[0])

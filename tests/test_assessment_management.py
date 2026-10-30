"""Canonical assessment discovery/deletion and reversible per-tool task controls.

Only synthetic private projects are used. Tests assert exact owner/data restoration,
current-tool scoping, preserved assignments and no writes before the main Save.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QCheckBox, QDialog, QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.bootstrap import create_window
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.worker_search_dialog import WorkerSearchDialog
from ergotools.presentation.desktop.worker_transfer_dialog import WorkerTransferDialog
from tests.test_worker_assessment_defaults import seed_defaults


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_main_task_buttons_change_only_active_tool_and_undo(
    tmp_path: Path,
    kind: AssessmentKind,
) -> None:
    """Add/remove retain the prefix and exact count history for every tool.

    Args:
        tmp_path: Disposable native project/settings directory.
        kind: Current tool with one saved standalone task and independent others.

    Returns:
        None; limits, data-loss consent and source Undo/Redo remain shared.
    """
    path = tmp_path / "tasks.ergprj"
    seed_defaults(path)
    before_bytes = path.read_bytes()
    w = create_window(
        tmp_path / "settings.json", original_controls=True, original_navigation=True
    )
    try:
        w.open_project_location(str(path))
        w.assessment_tabs.setCurrentIndex(list(AssessmentKind).index(kind))
        w.navigate_worker("W01")
        ws = w.presenter.workspace
        before = ws.active.state
        panel = w.task_panel if kind is AssessmentKind.LIFFT else w.secondary_panel()
        assert not hasattr(panel, "context_button")
        assert not panel.remove_task_button.isEnabled()
        panel.add_task_button.click()
        assert len(ws.active.state.tasks) == 2
        assert ws.active.state.tasks[0] == before.tasks[0]
        w.history_actions.replay(redo=False)
        assert ws.active.state == before
        w.history_actions.replay(redo=True)
        assert len(ws.active.state.tasks) == 2
        panel = w.task_panel if kind is AssessmentKind.LIFFT else w.secondary_panel()
        panel.remove_task_button.click()
        assert len(ws.active.state.tasks) == 1
        panel.add_task_button.click()
        panel = w.task_panel if kind is AssessmentKind.LIFFT else w.secondary_panel()
        field = panel.inputs[1][
            2
            if kind is AssessmentKind.LIFFT
            else 1
            if kind is AssessmentKind.DUET
            else -1
        ]
        field.setText("10")
        field.textEdited.emit("10")
        field.editingFinished.emit()
        assert ws.active.state.tasks[-1].repetitions == 10
        with patch.object(w, "confirm_task_reset", return_value=False) as confirm:
            panel.remove_task_button.click()
        confirm.assert_called_once()
        assert len(ws.active.state.tasks) == 2
        with patch.object(w, "confirm_task_reset", return_value=True):
            panel.remove_task_button.click()
        assert len(ws.active.state.tasks) == 1
        w.history_actions.replay(redo=False)
        assert len(ws.active.state.tasks) == 2
        assert ws.active.state.tasks[-1].repetitions == 10
        assert ws.read_history().history.standalone_for("W01", kind) is not None
        assert path.read_bytes() == before_bytes
    finally:
        w.presenter.workspace.close(choice=CloseChoice.DISCARD)
        w.close()
        w.deleteLater()


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_delete_picker_saved_only_confirm_cancel_and_single_undo(
    tmp_path: Path,
    kind: AssessmentKind,
) -> None:
    """Deletion of the current source updates browsing but retains workplace records.

    Args:
        tmp_path: Disposable native project/settings directory.
        kind: Each tool independently owns its standalone/workplace source.

    Returns:
        None; No preserves data and Yes removes only the exact selected source.
    """
    path = tmp_path / "delete.ergprj"
    seed_defaults(path)
    original_bytes = path.read_bytes()
    w = create_window(
        tmp_path / "settings.json", original_controls=True, original_navigation=True
    )
    try:
        w.open_project_location(str(path))
        w.assessment_tabs.setCurrentIndex(list(AssessmentKind).index(kind))
        w.navigate_worker("W01")
        ws = w.presenter.workspace
        doc, source = ws.active.document, ws.active.state
        history, jobs = ws.read_history().history, ws.read_jobs().jobs

        def choose(dialog: WorkerSearchDialog) -> int:
            """Accept an existing exact standalone row after inspecting scoped choices.

            Args:
                dialog: Saved-only picker created by the Delete action.

            Returns:
                Accepted exact selection; no mutation occurs inside the picker.
            """
            assert all(
                row.worker_id == "W01" and row.selection.kind is kind
                for row in dialog.rows
            )
            row = next(row for row in dialog.rows if row.document_id == doc.document_id)
            assert row.selection.assignment_id is None
            dialog.selected = row.selection
            return QDialog.Accepted

        with patch.object(WorkerSearchDialog, "exec_", choose):
            with patch.object(QMessageBox, "question", return_value=QMessageBox.No):
                w.main_navigation.location_browser.delete_button.click()
            assert ws.read_history().history == history and ws.active.state == source
            with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
                w.main_navigation.location_browser.delete_button.click()
        assert not any(
            e.document_id == doc.document_id for e in ws.read_history().history.entries
        )
        assert path.read_bytes() == original_bytes
        w.save_project()
        with AssessmentProjectFile.open(path) as reopened:
            assert not any(
                e.document_id == doc.document_id
                for e in reopened.load_history().entries
            )
            assert reopened.load_jobs() == jobs
        assert ws.read_jobs().jobs == jobs
        assert w.assessment_navigation.view.workplace is not None
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            w.history_actions.replay(redo=False)
        assert ws.read_history().history == history
        assert ws.active.document == doc and ws.active.state == source
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            w.history_actions.replay(redo=True)
        assert not any(
            e.document_id == doc.document_id for e in ws.read_history().history.entries
        )
    finally:
        w.presenter.workspace.close(choice=CloseChoice.DISCARD)
        w.close()
        w.deleteLater()


def test_added_task_is_revealed_after_layout_and_focus_cancels_on_switch(
    tmp_path: Path,
) -> None:
    """A long worker grid reveals its appended row without delayed cross-tool focus.

    Args:
        tmp_path: Private synthetic project/preferences directory.

    Returns:
        None; adding to a scrolled grid focuses the new input after layout settles.
    """
    path = tmp_path / "reveal.ergprj"
    seed_defaults(path)
    w = create_window(
        tmp_path / "settings.json", original_controls=True, original_navigation=True
    )
    try:
        w.open_project_location(str(path))
        w.resize(1550, 1015)
        w.show()
        w.activateWindow()
        QApplication.setActiveWindow(w)
        w.task_panel.task_grid.setMaximumHeight(300)
        w.presenter.set_task_count(40)
        w.refresh()
        QTest.qWait(60)
        w.task_panel.add_task_button.click()
        grid = w.task_panel.task_grid
        control = grid.inputs[40][0]
        for _ in range(50):
            QTest.qWait(10)
            if (
                QApplication.focusWidget() is control
                and grid.body_scroll.verticalScrollBar().value() > 0
            ):
                break
        assert QApplication.focusWidget() is control
        assert grid.body_scroll.verticalScrollBar().value() > 0, (
            w.size(),
            grid.size(),
            grid.frame.size(),
            control.pos(),
            grid.body_scroll.verticalScrollBar().maximum(),
        )
        grid.focus_task(0)
        w.assessment_tabs.setCurrentIndex(1)
        QTest.qWait(60)
        assert QApplication.focusWidget() not in grid.inputs[0]
    finally:
        w.presenter.workspace.close(choice=CloseChoice.DISCARD)
        w.close()
        w.deleteLater()


@pytest.mark.parametrize("language", list(Language))
def test_transfer_badges_follow_destination_worker_shift_and_tool_selection(
    tmp_path: Path, language: Language
) -> None:
    """Saved percentages and uncalculated destinations remain visibly distinct.

    Args:
        tmp_path: Disposable project/preferences directory.
        language: English/Spanish captions must retain exact ownership and values.

    Returns:
        None; occupied tools announce replacement and empty shifts enable Copy.
    """
    path = tmp_path / "badges.ergprj"
    seed_defaults(path)
    w = create_window(
        tmp_path / "settings.json", original_controls=True, original_navigation=True
    )
    dialog = None
    try:
        w.open_project_location(str(path))
        w.task_panel.calculate_button.click()
        ws = w.presenter.workspace
        source = ws.saved_assessment_result("standalone-lifft")
        assert source is not None
        dialog = WorkerTransferDialog(
            ws,
            None,
            w.icons,
            lambda request: CloseChoice.SAVE,
            source_worker_id="W01",
            language=language,
            parent=w,
        )
        dialog.show()
        QTest.qWait(40)
        lifft = next(
            row
            for row in range(dialog.tool_table.rowCount())
            if dialog.tool_table.item(row, 1).data(Qt.UserRole) is AssessmentKind.LIFFT
        )
        assert dialog.tool_table.item(lifft, 2).text() == (
            f"{source.probability_percent:.1f}%"
        )
        dialog.selected_worker_id = "W01"
        dialog.shift_combo.setCurrentText("Night")
        place = ws.read_jobs().jobs.assignments[0].worker.workplace
        key = (place.plant_name, place.section_name, place.line_name, place.station_id)
        item = dialog.workplace_nodes[key]
        dialog.workplace_tree.setCurrentItem(item)
        dialog.update_preview()
        column = 2 + dialog._available_kinds.index(AssessmentKind.LIFFT)
        assert item.text(column) == (
            "Sin calcular" if language is Language.SPANISH else "Not calculated"
        )
        assert dialog.transfer_button.isEnabled()
        assert (
            "replaced" if language is Language.ENGLISH else "reemplazarán"
        ) in dialog.preview_label.text()
        for row in range(dialog.tool_table.rowCount()):
            holder = dialog.tool_table.cellWidget(row, 0)
            holder.findChild(QCheckBox).setChecked(False)
        assert not dialog.transfer_button.isEnabled()
        dialog.tool_table.cellWidget(lifft, 0).findChild(QCheckBox).setChecked(True)
        dialog.shift_combo.setCurrentText("Day")
        assert item.text(column) == "—"
        assert dialog.transfer_button.isEnabled()
        dialog.selected_worker_id = "W02"
        dialog.update_preview()
        assert dialog.transfer_button.isEnabled()
    finally:
        if dialog is not None:
            dialog.close()
            dialog.deleteLater()
        w.presenter.workspace.close(choice=CloseChoice.DISCARD)
        w.close()
        w.deleteLater()


def test_delete_other_source_keeps_invalid_current_input(tmp_path: Path) -> None:
    """Deleting another saved context must not rebuild/discard current pending text.

    Args:
        tmp_path: Disposable native source and preferences directory.

    Returns:
        None; only the chosen workplace source disappears and all assignments remain.
    """
    path = tmp_path / "other.ergprj"
    seed_defaults(path)
    w = create_window(
        tmp_path / "settings.json", original_controls=True, original_navigation=True
    )
    try:
        w.open_project_location(str(path))
        ws = w.presenter.workspace
        before, jobs = ws.active, ws.read_jobs().jobs
        field = w.task_panel.inputs[0][0]
        field.setText("unfinished")
        field.textEdited.emit("unfinished")

        def choose(dialog: WorkerSearchDialog) -> int:
            """Choose an existing workplace source while standalone input stays pending.

            Args:
                dialog: Current-worker/tool saved-only deletion picker.

            Returns:
                Accepted exact workplace source intent.
            """
            dialog.selected = next(
                r.selection for r in dialog.rows if r.document_id == "workplace-lifft"
            )
            return QDialog.Accepted

        with (
            patch.object(WorkerSearchDialog, "exec_", choose),
            patch.object(QMessageBox, "question", return_value=QMessageBox.Yes),
        ):
            w.main_navigation.location_browser.delete_button.click()
        assert ws.active is before
        assert w.task_panel.inputs[0][0] is field and field.text() == "unfinished"
        assert w.task_panel.pending
        assert ws.read_jobs().jobs == jobs
        assert ws.read_history().history.standalone_for("W01", AssessmentKind.LIFFT)
        assert w.main_navigation.location_browser.combos[0].count() == 1
    finally:
        w.presenter.workspace.close(choice=CloseChoice.DISCARD)
        w.close()
        w.deleteLater()


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_find_opens_exact_standalone_from_workplace(
    tmp_path: Path, kind: AssessmentKind
) -> None:
    """Find exposes standalone context clearly and opens its exact worker/tool source.

    Args:
        tmp_path: Disposable native project/settings directory.
        kind: Active tool whose saved sources must stay separate from other tools.

    Returns:
        None; the selected source is unchanged and missing workers do not appear.
    """
    path = tmp_path / "find.ergprj"
    seed_defaults(path)
    w = create_window(
        tmp_path / "settings.json", original_controls=True, original_navigation=True
    )
    try:
        w.open_project_location(str(path))
        w.assessment_tabs.setCurrentIndex(list(AssessmentKind).index(kind))
        ws = w.presenter.workspace
        owner = ws.read_jobs().jobs.assignments[0]
        w.assessment_navigation.select(
            "W01",
            kind,
            lambda: w._blank_kind(kind),
            workplace=owner.worker.workplace,
            assignment_id=1,
            explicit=True,
        )
        w.refresh()

        def choose(dialog: WorkerSearchDialog) -> int:
            """Inspect enriched results and choose an exact standalone identity.

            Args:
                dialog: Canonical Find with current-tool risk values and saved sources.

            Returns:
                Accepted standalone result; no draft/ownership mutation.
            """
            assert all(
                r.selection.kind is kind and r.worker_id != "W03" for r in dialog.rows
            )
            assert dialog.table.columnCount() == 8
            assert any(
                "Standalone assessment" in dialog.table.item(i, 5).text()
                for i in range(dialog.table.rowCount())
            )
            dialog.selected = next(
                r.selection
                for r in dialog.rows
                if r.worker_id == "W01" and r.selection.assignment_id is None
            )
            return QDialog.Accepted

        with patch.object(WorkerSearchDialog, "exec_", choose):
            w.main_navigation.buttons["search"].click()
        assert ws.active.document.document_id == f"standalone-{kind.value}"
        assert w.assessment_navigation.view.workplace is None
    finally:
        w.presenter.workspace.close(choice=CloseChoice.DISCARD)
        w.close()
        w.deleteLater()

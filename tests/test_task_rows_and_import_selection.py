"""Nonadjacent row removal, exact Undo and reversible import-row filtering.

Only disposable projects and staged values are used. Shared-grid mouse selection is
exercised through real events, not private selection-state mutation.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QMessageBox, QTableWidgetSelectionRange

from ergotools.application.assessment_import import ImportProfile, prepare_import
from ergotools.application.assessment_task_rows import remove_assessment_rows
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.job_calculation import blank_job_source
from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentDraft, AssessmentKind
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.assessment_paste_dialog import AssessmentPasteDialog
from ergotools.presentation.desktop.assessment_task_grid import AssessmentTaskGrid
from ergotools.presentation.desktop.job_management_dialog import JobManagementDialog
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_assessment_import_ui import assessment_input_fields
from tests.test_job_calculators import enter_job
from tests.test_jrot_planning_ui import dispose, planning_dialog
from tests.test_saved_tool_data import window as window
from tests.test_task_names_ui import reopen_grid
from tests.test_unified_project_save import editing_workspace

# Retain the GUI owner for native header and modal probes.
_APP = QApplication.instance() or QApplication([])


def populated(source: AssessmentDraft) -> AssessmentDraft:
    """Fill four independently named valid tasks without rounded display values.

    Args:
        source: Tool and units template, borrowed without mutation.

    Returns:
        Four valid source tasks ready for one existing host acceptance operation.
    """
    fields = assessment_input_fields(source)
    rows = tuple(
        tuple(
            {
                "task_name": f"Task Ñ {number}",
                "lever_arm": "30",
                "load": "49.05",
                "repetitions": "100",
                "omni_res_scale": "4",
                "direction": "0",
            }[field]
            for field in fields
        )
        for number in range(1, 5)
    )
    from ergotools.domain.assessments.document import assessment_kind

    return prepare_import(
        source,
        rows,
        ImportProfile(assessment_kind(source), header=False, fields=fields),
        0,
    )


def select_separate_rows(grid: AssessmentTaskGrid) -> None:
    """Select first and third task headers using native Ctrl-click gestures.

    Args:
        grid: Four-row editable shared control.

    Returns:
        None; assertions verify exact nonadjacent row and copy selection.
    """
    first = grid.grid.itemAtPosition(1, 0).widget()
    third = grid.grid.itemAtPosition(3, 0).widget()
    QTest.mouseClick(first, Qt.MouseButton.LeftButton)
    QTest.mouseClick(
        third, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier
    )
    assert grid.selected_task_rows() == (0, 2)
    assert grid.selected_cell_range()[0] == (0, 2)


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_ordered_removal_keeps_exact_retained_ids_and_blank_starter(
    kind: AssessmentKind,
) -> None:
    """Nonadjacent deletion preserves exact data; all-row deletion leaves a starter.

    Args:
        kind: All three canonical task schemas.

    Returns:
        None; invalid row indices fail without altering the immutable source.
    """
    source = populated(blank_job_source(kind, MeasurementSystem.METRIC))
    result = remove_assessment_rows(source, (2, 0, 2))
    assert result.tasks == (source.tasks[1], source.tasks[3])
    assert len(remove_assessment_rows(source, (0, 1, 2, 3)).tasks) == 1
    for rows in ((), (-1,), (4,), (True,)):
        with pytest.raises(ValueError):
            remove_assessment_rows(source, rows)


@pytest.mark.parametrize("index", (0, 1, 2))
def test_main_multirow_cancel_remove_and_undo(
    window: LifftWindow, tmp_path: Path, index: int
) -> None:
    """Worker task removal warns once, respects Cancel and restores one exact batch.

    Args:
        window: Disposable integrated fixture.
        tmp_path: Private project and preferences folder.
        index: Each main tool tab.

    Returns:
        None; repeated remove/Undo works and retains the unselected rows.
    """
    reopen_grid(window, tmp_path, index, MeasurementSystem.METRIC, Language.ENGLISH)
    panel = window.secondary_panel() or window.task_panel
    original = window.active_source()
    source = populated(original)
    actions = panel.task_actions
    assert actions.accept_source(original, source, "assessment.paste", True)
    grid = panel.task_grid
    owner = window.presenter.workspace.editing
    for _ in range(2):
        select_separate_rows(grid)
        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.Cancel
        ) as ask:
            window.change_assessment_tasks(-1)
            assert ask.call_count == 1
        assert window.active_source() == source
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes) as ask:
            window.change_assessment_tasks(-1)
            assert ask.call_count == 1
        assert window.active_source().tasks == tuple(
            t for i, t in enumerate(source.tasks) if i not in (0, 2)
        )
        assert owner.replay(redo=False)
        assert window.active_source() == source


@pytest.mark.parametrize("kind", list(AssessmentKind))
@pytest.mark.parametrize("host", ("job", "jrot"))
def test_job_hosts_remove_selected_batch_and_undo(
    tmp_path: Path, kind: AssessmentKind, host: str
) -> None:
    """Both Job hosts share the grid and accept one reversible selected-row removal.

    Args:
        tmp_path: Disposable project directory.
        kind: Tool whose immutable tasks are edited.
        host: Dedicated Job Management or integrated JROT editor.

    Returns:
        None; exact source data is restored by one shared project Undo.
    """
    if host == "job":
        workspace = editing_workspace(tmp_path)
        dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
        enter_job(dialog)
        dialog.tool_tabs.setCurrentIndex(list(AssessmentKind).index(kind))
        editor = dialog.editors[kind]
    else:
        dialog = planning_dialog(tmp_path, Language.ENGLISH)
        workspace = dialog.workspace
        dialog.go(4)
        dialog.job_panel.tabs.setCurrentIndex(list(AssessmentKind).index(kind))
        with patch.object(dialog.job_panel, "confirm", return_value=True):
            dialog.job_panel.mode_changed(1)
        editor = dialog.job_panel.editors[kind]
    try:
        source = populated(editor.source)
        assert editor._accept_shared_source(
            editor.source, source, "assessment.paste", True
        )
        assert editor.source == source
        select_separate_rows(editor)
        if host == "job":
            with patch.object(dialog, "_question", return_value=QMessageBox.Yes) as ask:
                dialog.remove_task()
                assert ask.call_count == 1
        else:
            with patch.object(dialog.job_panel, "confirm", return_value=True) as ask:
                dialog.job_panel.resize_tasks(True)
                assert ask.call_count == 1
        assert editor.source.tasks == (source.tasks[1], source.tasks[3])
        assert workspace.editing.replay(redo=False)
        assert editor.source == source
    finally:
        if host == "jrot":
            dispose(dialog)
        else:
            dialog.close()
            workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("language", list(Language))
def test_import_extra_headers_notes_and_reversible_row_selection(
    language: Language,
) -> None:
    """Header selection and arbitrary excluded rows retain staged originals and mapping.

    Args:
        language: Both maintained interface languages.

    Returns:
        None; skipped invalid notes cannot enter tasks; restoring them revalidates.
    """
    source = blank_job_source(AssessmentKind.LIFFT, MeasurementSystem.METRIC)
    rows = (
        "Report\t\t\t",
        "Date\t\t\t",
        "Task name\tLever arm\tLoad\tRepetitions",
        "Packing Ñ\t30\t49.05\t100",
        "Note: check\tn/a\t?\t?",
        "Loading\t40\t98.1\t200",
    )
    dialog = AssessmentPasteDialog(
        source,
        "\n".join(rows),
        language,
        DecimalConvention.POINT,
        MeasurementSystem.METRIC,
        0,
    )
    try:
        panel = dialog.panel
        panel.header_option.setChecked(True)
        panel.header_row.setValue(3)
        assert tuple(combo.currentData() for combo in panel.mappings) == (
            "task_name",
            "lever_arm",
            "load",
            "repetitions",
        )
        staged = panel.rows
        # Visible row 4 is source row 5: two preceding rows, then task and note.
        row_header = panel.table.verticalHeader()
        QTest.mouseClick(
            row_header.viewport(),
            Qt.MouseButton.LeftButton,
            pos=QPoint(
                14,
                row_header.sectionViewportPosition(4) + row_header.sectionSize(4) // 2,
            ),
        )
        assert not panel.row_included(4)
        panel.prepare(accept=False)
        assert panel.replacement is not None, panel.error.text()
        assert [t.task_name for t in panel.replacement.tasks] == [
            "Packing Ñ",
            "Loading",
        ]
        assert panel.rows == staged
        mapping = panel.profile().fields
        panel.include_all_rows()
        panel.prepare(accept=False)
        assert panel.replacement is None
        assert panel.profile().fields == mapping
        # Bulk-skip disjoint selected rows, retaining the source numbers.
        panel.table.clearSelection()
        for row in (1, 2, 4):
            panel.table.setRangeSelected(
                QTableWidgetSelectionRange(row, 0, row, 3), True
            )
        panel.set_selected_rows(False)
        panel.prepare(accept=False)
        assert panel.replacement is not None, panel.error.text()
        assert panel.rows == staged
        panel.toggle_row(0)
        panel.prepare(accept=False)
        assert panel.replacement is None
        assert panel.rows == staged
    finally:
        dialog.panel.stop_validation()
        dialog.close()
        dialog.deleteLater()
        _APP.processEvents()

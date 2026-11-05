"""User-facing JROT layout, proposal placement and explicit-result regression checks.

Tests own temporary projects and native widgets. They verify observable interaction
contracts rather than introduce substitute scientific or persistence implementations.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QMessageBox, QStyleOptionViewItem

from ergotools.bootstrap import load_icons
from ergotools.domain.language import Language
from ergotools.domain.rotation_scenario import RotationDraftRow
from ergotools.domain.rotation_timing import MinuteInterval, TimedBreak, equal_timing
from ergotools.domain.task_catalog import TaskDefinition
from ergotools.presentation.desktop.jrot_dialog import JrotDialog
from ergotools.presentation.desktop.table_presentation import ReadableCellDelegate
from ergotools.presentation.desktop.task_name_dialog import TaskNameDialog
from tests.test_jrot_comparison_ui import solved_dialog
from tests.test_jrot_guided_ui import dispose
from tests.test_jrot_planning_ui import await_result, planning_dialog


def test_generation_from_assignments_stays_in_step_four(tmp_path: Path) -> None:
    """Generate fills proposal cells without skipping assessment/review steps.

    Args:
        tmp_path: Disposable project location.

    Returns:
        None; proposal generation is reversible and never creates an observed baseline.
    """
    root = planning_dialog(tmp_path, Language.ENGLISH)
    try:
        root.go(3)
        before = root.current()
        root.generate_proposal()
        assert root.pages.currentIndex() == 3
        for _ in range(1000):
            if not root.solve.busy:
                break
            QTest.qWait(10)
        assert not root.solve.busy and not root.error.text()
        assert root.pages.currentIndex() == 3
        assert root.current().inputs.proposed is not None
        assert root.current().inputs.baseline is None and root.current().run is None
        assert root.workspace.editing.replay(redo=False)
        root.reload()
        assert root.current() == before
        root.relative(1)
        assert root.pages.currentIndex() == 4
    finally:
        dispose(root)


def test_explicit_keep_close_cancel_and_baseline_are_independent(
    tmp_path: Path,
) -> None:
    """A pending rerun cannot replace evidence or baseline merely by completing.

    Args:
        tmp_path: Disposable native project.

    Returns:
        None; Cancel keeps the preview, deliberate Keep retains only the new result.
    """
    root = solved_dialog(tmp_path)
    try:
        before = root.current()
        root.solve.start()
        await_result(root)
        assert root.current() == before
        assert root.solve.preview is not None
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Cancel):
            assert not root.resolve_result_preview()
        assert root.current() == before and root.solve.preview is not None
        with patch.object(root, "confirm", return_value=True):
            root.relative(1)
        assert root.pages.currentIndex() == 7
        assert root.solve.preview is None
        assert root.current().inputs.baseline == before.inputs.baseline
        assert root.current().run.inputs.baseline == before.inputs.baseline
        assert root.current().run.arrangement != before.inputs.baseline
    finally:
        dispose(root)


def test_numeric_contrast_and_roomy_summary_layout(tmp_path: Path) -> None:
    """Dark fills get light text, numeric cells center and peer risks retain space.

    Args:
        tmp_path: Private guided project.

    Returns:
        None; repeated layout refresh does not grow rows indefinitely or add scrolling.
    """
    root = planning_dialog(tmp_path, Language.ENGLISH)
    try:
        root.go(1)
        QTest.qWait(30)
        table = root.jobs_table
        assert min(table.columnWidth(c) for c in (3, 4, 5)) >= 110
        assert table.rowHeight(0) >= 42
        first = table.rowHeight(0)
        table.schedule_fit()
        QTest.qWait(20)
        assert table.rowHeight(0) == first
        assert table.verticalScrollBar().maximum() == 0
        item = table.item(0, 3)
        item.setBackground(QColor("#FF3B30"))
        option = QStyleOptionViewItem()
        ReadableCellDelegate(table).initStyleOption(option, table.model().index(0, 3))
        assert option.palette.color(QPalette.Text).name() == "#fafcff"
        assert option.font.bold()
    finally:
        dispose(root)


def test_reopen_uses_remembered_rotation_and_collapses_drawer(
    tmp_path: Path,
) -> None:
    """Opening restores the remembered rotation at its kept comparison page.

    Args:
        tmp_path: Disposable project and shared editor state.

    Returns:
        None; read-only reopening chooses the remembered retained record and step 08.
    """
    original = solved_dialog(tmp_path)
    earlier = replace(original.current(), scenario_id="A", name="A retained rotation")
    original.repository.replace_rotation_scenario(None, earlier)
    original.go(4)
    original.accept()
    root = JrotDialog(original.workspace, load_icons())
    try:
        root.show()
        QTest.qWait(30)
        assert root.current().scenario_id == original.current().scenario_id
        assert root.pages.currentIndex() == 7
        assert not root.drawer.pin.isChecked()
    finally:
        original.deleteLater()
        dispose(root)


def test_task_names_use_shared_available_initials(tmp_path: Path) -> None:
    """The name catalog supports the same accent-aware alphabet and text intersection.

    Args:
        tmp_path: Disposable project catalog.

    Returns:
        None; filtering writes no definitions or measurements.
    """
    root = planning_dialog(tmp_path, Language.ENGLISH)
    names = (TaskDefinition("a", "Ángular lift"), TaskDefinition("b", "Box loading"))
    root.workspace.replace_task_definitions((), names)
    dialog = TaskNameDialog(root.workspace, load_icons(), Language.ENGLISH, root)
    try:
        assert dialog.alphabet.buttons["A"].isEnabled()
        assert not dialog.alphabet.buttons["Z"].isEnabled()
        dialog.alphabet.buttons["B"].click()
        rows = {
            dialog.table.topLevelItem(i).text(0): dialog.table.topLevelItem(i)
            for i in range(2)
        }
        assert rows["Ángular lift"].isHidden()
        assert not rows["Box loading"].isHidden()
        assert root.workspace.load_task_definitions() == names
    finally:
        dialog.close()
        dialog.deleteLater()
        dispose(root)


def test_clear_baseline_preserves_intent_run_and_undo(tmp_path: Path) -> None:
    """Clear edits displayed starting cells, not the frozen optimized evidence.

    Args:
        tmp_path: Disposable observed rotation with a retained real solver result.

    Returns:
        None; rejected clear is a no-op; clear and Undo preserve the frozen evidence.
    """
    root = solved_dialog(tmp_path)
    try:
        root.go(3)
        before = root.current()
        with patch.object(root, "confirm", return_value=False):
            root.clear_assignments()
        assert root.current() == before
        with patch.object(root, "confirm", return_value=True):
            root.clear_assignments()
        cleared = root.current()
        assert cleared.inputs.baseline is not None
        assert all(k is None for r in cleared.inputs.baseline for k in r.target_keys)
        assert cleared.run == before.run
        assert root.workspace.editing.replay(redo=False)
        root.reload()
        assert root.current() == before
    finally:
        dispose(root)


def test_baseline_generation_confirmation_and_history(tmp_path: Path) -> None:
    """A Yes-path baseline can be regenerated without deleting its kept optimization.

    Args:
        tmp_path: Temporary observed rotation and main project history.

    Returns:
        None; generation stays in 04, cancellation preserves data and Undo restores it.
    """
    root = solved_dialog(tmp_path)
    try:
        root.go(3)
        with patch.object(root, "confirm", return_value=True):
            root.clear_assignments()
        before = root.current()
        for accepted in (False, True):
            with patch.object(root, "confirm", return_value=accepted):
                root.generate_proposal()
                for _ in range(1000):
                    if not root.solve.busy:
                        break
                    QTest.qWait(10)
            assert not root.solve.busy and not root.error.text()
            assert root.pages.currentIndex() == 3
            assert root.current().run == before.run
            if not accepted:
                assert root.current() == before
            else:
                assert all(
                    k is not None
                    for r in root.current().inputs.baseline
                    for k in r.target_keys
                )
                assert root.current().inputs.proposed == before.inputs.proposed
                assert root.workspace.editing.replay(redo=False)
                root.reload()
                assert root.current() == before
    finally:
        dispose(root)


def test_clock_headers_adapt_without_changing_column_widths(tmp_path: Path) -> None:
    """Input and result headers expose exact clocks, then omit them on crowded views.

    Args:
        tmp_path: Disposable solved rotation.

    Returns:
        None; annotations use frozen timing without creating document edits.
    """
    root = solved_dialog(tmp_path)
    try:
        root.go(3)
        QTest.qWait(50)
        root.matrix_headers.refresh()
        text = root.matrix.horizontalHeaderItem(1).text()
        assert "08:00" in text and "12:00" in text
        before = root.current()
        root.go(6)
        table = root.solve.tabs.widget(0)
        table.block_headers.refresh()
        widths = tuple(table.columnWidth(c) for c in range(table.columnCount()))
        assert "08:00" in table.horizontalHeaderItem(1).text()
        table.block_headers.refresh()
        assert widths == tuple(table.columnWidth(c) for c in range(table.columnCount()))
        root.solve.tabs.removeTab(0)
        table.setParent(None)
        table.setMinimumSize(0, 0)
        table.resize(300, 300)
        table.show()
        QTest.qWait(30)
        table.block_headers.refresh()
        assert "08:00" not in table.horizontalHeaderItem(1).text()
        assert "08:00" in table.horizontalHeaderItem(1).toolTip()
        table.close()
        table.deleteLater()
        assert root.current() == before
    finally:
        dispose(root)


def test_baseline_generation_rejects_changed_starting_cells(tmp_path: Path) -> None:
    """A detached feasibility solve cannot overwrite a baseline changed while solving.

    Args:
        tmp_path: Private observed rotation and real bounded planner.

    Returns:
        None; exact origin checking covers cells omitted from the feasibility problem.
    """
    root = solved_dialog(tmp_path)
    try:
        root.go(3)
        root.generate_proposal()
        before = root.current()
        rows = tuple(
            RotationDraftRow(r.worker_id, (None,) * len(r.target_keys))
            for r in before.inputs.baseline
        )
        changed = replace(before, inputs=replace(before.inputs, baseline=rows))
        root.repository.replace_rotation_scenario(before, changed)
        for _ in range(1000):
            if not root.solve.busy:
                break
            QTest.qWait(10)
        assert not root.solve.busy and root.error.text()
        assert root.current() == changed
        assert root.solve.preview is None
    finally:
        dispose(root)


def test_clock_header_keeps_overnight_and_break_pieces(tmp_path: Path) -> None:
    """Overnight suffixes and interrupted historical blocks are never hidden as work.

    Args:
        tmp_path: Disposable layout host; source inputs are not accepted or saved.

    Returns:
        None; compact header tooltips preserve every exact productive clock piece.
    """
    root = planning_dialog(tmp_path, Language.ENGLISH)
    try:
        inputs = replace(
            root.current().inputs,
            start_minute=1320,
            timing=equal_timing(480, 2, (TimedBreak(MinuteInterval(120, 180)),)),
        )
        root.refresh_matrix(inputs)
        root.matrix_headers.refresh()
        interval = root.matrix.horizontalHeaderItem(1).toolTip()
        assert "22:00 - 00:00 (+1) / 01:00 (+1) - 02:30 (+1)" in interval
    finally:
        dispose(root)


def test_rotation_combo_distinguishes_kept_and_unsolved_records(tmp_path: Path) -> None:
    """Selecting kept evidence opens comparison; an unsolved record opens setup.

    Args:
        tmp_path: Disposable project containing solved and unsolved rotations.

    Returns:
        None; combo changes do not solve, erase evidence or generate starting cells.
    """
    root = solved_dialog(tmp_path)
    kept = root.current()
    pending = replace(kept, scenario_id="pending", name="Pending", run=None)
    root.repository.replace_rotation_scenario(None, pending)
    root.reload()
    try:
        with patch.object(root.solve.optimizer, "solve", side_effect=AssertionError):
            root.scenarios.setCurrentIndex(root.scenarios.findData(pending.scenario_id))
            QTest.qWait(20)
            assert root.current() == pending
            assert root.pages.currentIndex() == 0 and root.drawer.pin.isChecked()
            root.scenarios.setCurrentIndex(root.scenarios.findData(kept.scenario_id))
            QTest.qWait(20)
            assert root.current() == kept
            assert root.pages.currentIndex() == 7 and not root.drawer.pin.isChecked()
            assert root.comparison.run == kept.run
            assert not hasattr(root.solve, "generate_button")
    finally:
        dispose(root)

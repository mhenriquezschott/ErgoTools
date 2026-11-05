"""Actual guided comparison/rework/reopen controls on disposable native projects.

Real HiGHS output, frozen catalogs and shared project history underpin assertions;
viewing is never replaced by sample data, a second solver or a separate Save operation.
"""

from dataclasses import replace
from itertools import combinations
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QInputDialog, QTableWidget

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.rotation_entry import RotationEntryChange
from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.rotation import WorkerRotation
from ergotools.presentation.desktop.jrot_dialog import JrotDialog
from ergotools.presentation.desktop.jrot_result_table import JrotResultTable
from ergotools.presentation.desktop.plot_chart_canvas import PlotChartCanvas
from tests.test_jrot_guided_ui import dispose
from tests.test_jrot_planning_ui import WaitingPlanner, await_result, planning_dialog


def solved_dialog(tmp_path: Path, language: Language = Language.ENGLISH) -> JrotDialog:
    """Solve a real 0/100 observed baseline into an accepted balanced 50/50 schedule.

    Args:
        tmp_path: Disposable project and settings location.
        language: Owned English/Spanish captions.

    Returns:
        Open test-owned dialog; its run uses actual approved HiGHS stages.
    """
    dialog = planning_dialog(tmp_path, language)
    record = dialog.current()
    a, b = (t.key for t in record.inputs.targets)
    rows = (WorkerRotation("W1", (a, a)), WorkerRotation("W2", (b, b)))
    assert dialog.edit_inputs(
        record, RotationEntryChange(replace(record.inputs, baseline=rows))
    )
    dialog.reload()
    dialog.solve.start()
    await_result(dialog)
    dialog.solve.keep_result()
    assert dialog.current().run is not None, dialog.error.text()
    return dialog


@pytest.mark.parametrize("language", list(Language))
def test_comparison_uses_same_frozen_solution_and_readonly_views(
    tmp_path: Path,
    language: Language,
) -> None:
    """Comparison statistics and details display frozen evidence without another solve.

    Args:
        tmp_path: Private native project directory.
        language: Both caption languages.

    Returns:
        None; UI review leaves accepted source/run and saved file bytes unchanged.
    """
    dialog = solved_dialog(tmp_path, language)
    try:
        original = dialog.current()
        assert dialog.workspace.save()
        saved = Path(dialog.workspace.location).read_bytes()
        with patch.object(
            dialog.solve.optimizer, "solve", side_effect=AssertionError("view solved")
        ):
            dialog.go(7)
            for i in range(3):
                dialog.comparison.tabs.setCurrentIndex(i)
                QTest.qWait(5)
            assert dialog.comparison.tabs.count() == 3
            tables = dialog.comparison.findChildren(JrotResultTable)
            assert len(tables) == 6
            assert all(t.editTriggers() == t.EditTrigger.NoEditTriggers for t in tables)
            assert all(t.item(0, 3).text() in ("0.00", "50.00") for t in tables)
            assert not dialog.comparison.findChildren(PlotChartCanvas)
            statistics = dialog.comparison.findChildren(
                QTableWidget, "comparisonStatistics"
            )
            assert len(statistics) == 3
            for table in statistics:
                assert table.item(0, 1).text() == "50.00"
                assert table.item(0, 2).text() == "50.00"
                assert table.item(1, 1).text() == "100.00"
                assert table.item(1, 2).text() == "50.00"
                assert table.item(2, 1).text() == "50.00"
                assert table.item(2, 2).text() == "0.00"
        assert dialog.current() == original
        assert Path(dialog.workspace.location).read_bytes() == saved
        assert not dialog.comparison.report_button.isEnabled()
        assert dialog.comparison.rework_button.isEnabled()
    finally:
        dispose(dialog)


def test_job_edit_marks_saved_run_stale_without_recalculating_original_values(
    tmp_path: Path,
) -> None:
    """Current Job edits alter input review while frozen comparisons stay unchanged.

    Args:
        tmp_path: Disposable project.

    Returns:
        None; no original solve is silently displayed with today's coefficients.
    """
    dialog = solved_dialog(tmp_path)
    try:
        saved = dialog.current().run
        jobs, risks = dialog.workspace.read_jobs(), dialog.workspace.read_job_risk()
        old = risks.risk.for_job("J1")
        changed = replace(
            old,
            measurements=tuple(
                replace(m, probability_percent=20) for m in old.measurements
            ),
        )
        dialog.workspace.save_job_details(
            jobs, risks, next(j for j in jobs.jobs.jobs if j.job_id == "J1"), changed
        )
        dialog.reload()
        dialog.go(7)
        assert dialog.current().run == saved
        assert "STALE" in dialog.comparison.notice.text()
        assert dialog.comparison.run == saved
        for table in dialog.comparison.findChildren(JrotResultTable):
            assert table.item(0, 3).text() in ("0.00", "50.00")
        dialog.go(5)
        assert dialog.start_table.item(0, 1).text() == "20.00"
        assert dialog.solve.displayed_run == saved
    finally:
        dispose(dialog)


def test_duplicate_rework_preserves_original_and_replays_one_action(
    tmp_path: Path,
) -> None:
    """Default rework copies optimized baseline once without replacing the original.

    Args:
        tmp_path: Disposable native project.

    Returns:
        None; coherent undo/redo restores both identity selection and original evidence.
    """
    dialog = solved_dialog(tmp_path)
    try:
        original = dialog.current()
        jobs = dialog.workspace.read_job_risk().risk
        with patch.object(
            QInputDialog, "getText", return_value=("Packing revision", True)
        ):
            dialog.rework_run(False)
        new = dialog.current()
        assert new.scenario_id != original.scenario_id
        assert new.source_scenario_id == original.scenario_id
        assert new.inputs.baseline == original.run.arrangement
        assert new.inputs.proposed is None and new.run is None
        assert original in dialog.repository.load_rotation_scenarios()
        assert dialog.workspace.read_job_risk().risk == jobs
        assert dialog.workspace.editing.replay(redo=False)
        dialog.reload()
        assert dialog.current() == original
        assert dialog.repository.load_rotation_scenarios() == (original,)
        assert dialog.workspace.editing.replay(redo=True)
        dialog.reload()
        assert dialog.current() == new
        assert dialog.workspace.save()
    finally:
        dispose(dialog)


def test_explicit_baseline_replacement_has_cancel_and_exact_undo(
    tmp_path: Path,
) -> None:
    """Optional in-place rework requires consent and retains the old frozen run.

    Args:
        tmp_path: Disposable native project.

    Returns:
        None; declining changes nothing and accepted replacement remains reversible.
    """
    dialog = solved_dialog(tmp_path)
    try:
        before = dialog.current()
        with patch.object(dialog, "confirm", return_value=False):
            dialog.rework_run(True)
        assert dialog.current() == before
        with patch.object(dialog, "confirm", return_value=True):
            dialog.rework_run(True)
        replaced = dialog.current()
        assert replaced.scenario_id == before.scenario_id
        assert replaced.inputs.baseline == before.run.arrangement
        assert replaced.run == before.run
        assert not replaced.run_matches_inputs
        assert dialog.workspace.editing.replay(redo=False)
        dialog.reload()
        assert dialog.current() == before
    finally:
        dispose(dialog)


@pytest.mark.parametrize("version", [1, 99])
def test_unsupported_saved_model_is_visible_but_not_reinterpreted(
    tmp_path: Path, version: int
) -> None:
    """Old/future evidence displays exact matrices with missing weighted indices.

    Args:
        tmp_path: Private project.
        version: Unsupported positive run model.

    Returns:
        None; no compare, rework or Apply fabricates supported solver evidence.
    """
    dialog = solved_dialog(tmp_path)
    try:
        record = dialog.current()
        old = replace(record, run=replace(record.run, contract_version=version))
        dialog.repository.replace_rotation_scenario(record, old)
        dialog.reload()
        dialog.go(7)
        assert dialog.comparison.tabs.count() == 3
        assert not dialog.comparison.rework_button.isEnabled()
        for table in dialog.comparison.findChildren(JrotResultTable):
            assert table.item(0, 3).text() == "—"
        assert dialog.current() == old
    finally:
        dispose(dialog)


def test_cancelled_reoptimization_restores_saved_matrix_and_result(
    tmp_path: Path,
) -> None:
    """Cancellation retains accepted evidence in storage and on screen.

    Args:
        tmp_path: Disposable native project.

    Returns:
        None; a cancelled bounded worker never writes a replacement.
    """
    dialog = solved_dialog(tmp_path)
    planner = WaitingPlanner()
    dialog.solve.optimizer = planner
    try:
        before = dialog.current()
        dialog.solve.start()
        dialog.solve.cancel()
        planner.release.set()
        for _ in range(500):
            QTest.qWait(10)
            if not dialog.solve.busy:
                break
        assert not dialog.solve.busy
        assert dialog.current() == before
        assert dialog.solve.preview is None
        assert dialog.solve.displayed_run == before.run
        assert dialog.solve.tabs.count() == 3
        assert not dialog.solve.keep_button.isEnabled()
    finally:
        planner.release.set()
        dispose(dialog)


def test_reopen_selects_saved_result_and_keeps_project_clean(tmp_path: Path) -> None:
    """A fresh workspace opens its last accepted result without solving or writing.

    Args:
        tmp_path: Disposable native project and application settings.

    Returns:
        None; exact saved context and worker/tool matrices survive process-like reopen.
    """
    from ergotools.application.project_workspace import ProjectWorkspace
    from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
    from ergotools.infrastructure.settings_store import JsonSettingsStore

    original = solved_dialog(tmp_path)
    expected = original.current()
    earlier = replace(expected, scenario_id="A", name="A earlier retained rotation")
    original.repository.replace_rotation_scenario(None, earlier)
    original.repository.select_rotation_scenario(expected.scenario_id)
    assert original.workspace.save()
    location = Path(original.workspace.location)
    before = location.read_bytes()
    dispose(original)
    workspace = ProjectWorkspace(
        lambda name: AssessmentProjectFile.open(Path(name)),
        JsonSettingsStore(tmp_path / "reopen_preferences.json"),
        unified_saving=True,
    )
    workspace.switch(str(location), None)
    dialog = JrotDialog(workspace, load_icons())
    try:
        dialog.show()
        QTest.qWait(20)
        assert dialog.pages.currentIndex() == 7
        assert dialog.current() == expected
        assert dialog.comparison.run == expected.run
        assert dialog.solve.displayed_run == expected.run
        assert dialog.solve.tabs.count() == 3
        assert not workspace.has_unsaved_changes
        assert location.read_bytes() == before
    finally:
        dialog.accept()
        dialog.deleteLater()
        workspace.close(choice=CloseChoice.DISCARD)


def test_explicit_reoptimization_keep_preserves_baseline_and_undo_evidence(
    tmp_path: Path,
) -> None:
    """Explicit Keep replaces the result while preserving the original baseline.

    Args:
        tmp_path: Disposable project.

    Returns:
        None; explicit replacement is one edit and Undo restores old evidence exactly.
    """
    dialog = solved_dialog(tmp_path)
    try:
        before = dialog.current()
        jobs, risks = dialog.workspace.read_jobs(), dialog.workspace.read_job_risk()
        item = risks.risk.for_job("J1")
        item = replace(
            item,
            measurements=tuple(
                replace(m, probability_percent=20) for m in item.measurements
            ),
        )
        dialog.workspace.save_job_details(
            jobs, risks, next(j for j in jobs.jobs.jobs if j.job_id == "J1"), item
        )
        dialog.reload()
        dialog.solve.start()
        await_result(dialog)
        dialog.comparison.refresh()
        assert dialog.solve.run.coefficients != before.run.coefficients
        assert dialog.solve.preview is not None
        assert dialog.current() == before
        with patch.object(dialog, "confirm", return_value=False):
            dialog.solve.keep_result()
        assert dialog.current() == before
        with patch.object(dialog, "confirm", return_value=True):
            dialog.solve.keep_result()
        assert dialog.solve.preview is None
        after = dialog.current()
        assert after.run != before.run
        assert all(
            m.measurement.probability_percent == 20
            for m in after.run.coefficients
            if m.target_key == after.inputs.targets[0].key
        )
        assert dialog.workspace.editing.replay(redo=False)
        dialog.reload()
        assert dialog.current() == before
        assert "STALE" in dialog.comparison.notice.text()
        assert dialog.workspace.editing.replay(redo=True)
        dialog.reload()
        assert dialog.current() == after
    finally:
        dispose(dialog)


@pytest.mark.parametrize(
    "tools",
    [subset for count in (1, 2, 3) for subset in combinations(AssessmentKind, count)],
)
def test_selected_tools_have_exactly_their_analyzed_matrix_tabs(
    tmp_path: Path, tools: tuple[AssessmentKind, ...]
) -> None:
    """Every analyzed subset displays its own matrices without extra empty tabs.

    Args:
        tmp_path: Disposable native project.
        tools: Every nonempty supported scientific model subset.

    Returns:
        None; display selection does not imply a solve for unselected tools.
    """
    dialog = planning_dialog(tmp_path, Language.ENGLISH)
    try:
        record = dialog.current()
        assert dialog.edit_inputs(
            record, RotationEntryChange(replace(record.inputs, tools=tools))
        )
        dialog.reload()
        dialog.solve.start()
        await_result(dialog)
        dialog.solve.keep_result()
        dialog.go(7)
        assert dialog.comparison.tabs.count() == len(tools)
        assert dialog.solve.tabs.count() == len(tools)
        assert dialog.comparison.run.inputs.baseline is None
    finally:
        dispose(dialog)


def test_retired_workspace_cannot_publish_or_display_late_result(
    tmp_path: Path,
) -> None:
    """A replaced project session retires both preview and saved-result controls.

    Args:
        tmp_path: Disposable project.

    Returns:
        None; detached work may finish but gains no access to another project session.
    """
    dialog = solved_dialog(tmp_path)
    planner = WaitingPlanner()
    dialog.solve.optimizer = planner
    try:
        dialog.solve.start()
        dialog.workspace.close(choice=CloseChoice.DISCARD)
        planner.release.set()
        for _ in range(500):
            QTest.qWait(10)
            if not dialog.solve.busy:
                break
        assert not dialog.solve.busy
        assert dialog.solve.preview is None
        assert dialog.comparison.run is None
        assert not dialog.solve.start_button.isEnabled()
    finally:
        planner.release.set()
        dialog.deleteLater()
        QTest.qWait(10)


def test_step_four_generation_keeps_saved_evidence_separate(tmp_path: Path) -> None:
    """Step 04 changes only starting assignments and never replaces a kept run.

    Args:
        tmp_path: Disposable native project.

    Returns:
        None; generated proposals stay in 04 and Undo restores the prior inputs.
    """
    dialog = planning_dialog(tmp_path, Language.ENGLISH)
    try:
        dialog.solve.start()
        await_result(dialog)
        dialog.solve.keep_result()
        accepted = dialog.current()
        dialog.generate_proposal()
        await_result(dialog)
        assert dialog.pages.currentIndex() == 3
        assert dialog.solve.preview is None
        assert dialog.current().run == accepted.run
        assert dialog.current().inputs.proposed is not None
        assert dialog.workspace.editing.replay(redo=False)
        dialog.reload()
        assert dialog.current() == accepted
        dialog.go(7)
        assert dialog.comparison.run == accepted.run
        assert dialog.comparison.rework_button.isEnabled()
    finally:
        dispose(dialog)


def test_feasible_stage_is_not_presented_as_proved_optimal(tmp_path: Path) -> None:
    """A validated incumbent keeps its recorded qualified status on reopen/display.

    Args:
        tmp_path: Disposable native project with synthetic termination metadata.

    Returns:
        None; numeric correctness is tested separately with actual approved solvers.
    """
    from ergotools.domain.rotation import RotationSolveStatus

    dialog = solved_dialog(tmp_path)
    try:
        record = dialog.current()
        feasible = replace(
            record,
            run=replace(
                record.run,
                stages=(
                    RotationSolveStatus.FEASIBLE,
                    RotationSolveStatus.OPTIMAL,
                ),
            ),
        )
        dialog.repository.replace_rotation_scenario(record, feasible)
        dialog.reload()
        dialog.go(7)
        assert "optimality not proved" in dialog.comparison.notice.text()
        assert "Stage 1: feasible" in dialog.comparison.notice.toolTip()
    finally:
        dispose(dialog)


def test_input_review_gives_each_tool_equal_width(tmp_path: Path) -> None:
    """The three peer tool columns use available width without privileging ST.

    Args:
        tmp_path: Disposable project with a complete known baseline.

    Returns:
        None; worker labels retain content width and all numeric headers remain visible.
    """
    dialog = solved_dialog(tmp_path)
    try:
        dialog.go(5)
        dialog.summary_tabs.setCurrentIndex(0)
        QTest.qWait(20)
        widths = [dialog.start_table.columnWidth(i) for i in range(1, 4)]
        assert max(widths) - min(widths) <= 1
        assert min(widths) >= 80
    finally:
        dispose(dialog)

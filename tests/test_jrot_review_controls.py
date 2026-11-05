"""Owner walkthrough regressions for visible tools, optional links and coherent rules.

Native presentation tests use private projects and real shared history. No solver,
calculator or project format is replaced by a test-only implementation.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QMessageBox

from ergotools.application.rotation_entry import RotationEntryChange
from ergotools.application.rotation_planning import capture_rotation_boundary
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.rotation_constraints import NoAdjacentHigh
from ergotools.presentation.desktop.jrot_catalog_picker import JrotCatalogPicker
from ergotools.presentation.desktop.jrot_rules_dialog import JrotRulesDialog
from tests.test_jrot_comparison_ui import solved_dialog
from tests.test_jrot_guided_ui import dispose
from tests.test_jrot_planning_ui import planning_dialog


@pytest.mark.parametrize("language", list(Language))
def test_prominent_tool_choices_keep_subset_history_and_shared_icons(
    tmp_path: Path, language: Language
) -> None:
    """Compact tool controls still select a nonempty subset through shared Undo.

    Args:
        tmp_path: Disposable native project.
        language: Maintained interface language.

    Returns:
        None; icons are visible across calculator/review/result tabs, not new assets.
    """
    root = solved_dialog(tmp_path, language)
    try:
        root.go(5)
        before = root.current()
        for control in root.tools.values():
            assert not control.icon().isNull() and control.iconSize().height() >= 24
            assert control.width() == 104 and control.height() == 36
            assert control.toolTip()
        root.tools[AssessmentKind.DUET].click()
        assert root.current().inputs.tools == (AssessmentKind.LIFFT, AssessmentKind.TST)
        assert root.workspace.editing.replay(redo=False)
        root.reload()
        assert root.current() == before
        for tabs in (root.risk_tabs, root.solve.tabs, root.comparison.tabs):
            assert tabs.count() == 3
            assert all(not tabs.tabIcon(i).isNull() for i in range(3))
    finally:
        dispose(root)


@pytest.mark.parametrize("language", list(Language))
def test_optional_neighbor_disclosure_requests_and_hover_help(
    tmp_path: Path, language: Language
) -> None:
    """Links activate per boundary, while expanding and hover create no source edits.

    Args:
        tmp_path: Private editor state.
        language: Owned English/Spanish wording.

    Returns:
        None; disabled selection still explains when it becomes relevant.
    """
    root = planning_dialog(tmp_path, language)
    try:
        root.go(2)
        section = root.neighbors
        assert not section.toggle.isChecked() and section.disclosure.isHidden()
        assert not any(b.isEnabled() for b in section.choose_buttons.values())
        before = root.current()
        section.toggle.click()
        QTest.qWait(230)
        assert section.disclosure.isVisible()
        assert root.current() == before
        changed = replace(before.inputs, rules=(NoAdjacentHigh("W1", previous=True),))
        assert root.edit_inputs(before, RotationEntryChange(changed))
        root.reload()
        assert section.toggle.isChecked()
        assert section.choose_buttons[True].isEnabled()
        assert not section.choose_buttons[False].isEnabled()
        previous_text = section.explanation(True)
        root.activateWindow()
        root.raise_()
        QTest.qWait(20)
        section.choose_buttons[True].setFocus()
        QTest.qWait(10)
        assert section.help.text() == previous_text
        QTest.mouseMove(
            section.choose_buttons[False], section.choose_buttons[False].rect().center()
        )
        QTest.qWait(20)
        assert section.help.text() == section.explanation(False)
        assert root.current().inputs == changed
    finally:
        dispose(root)


@pytest.mark.parametrize("language", list(Language))
def test_fixed_and_excluded_jobs_prevent_contradictory_choices(
    tmp_path: Path, language: Language
) -> None:
    """Fixed Jobs cannot be excluded or duplicated and matching conflicts revert early.

    Args:
        tmp_path: Disposable worker/Job catalog.
        language: Both maintained UI languages.

    Returns:
        None; draft navigation/cancellation never changes the project source.
    """
    root = planning_dialog(tmp_path, language)
    before = root.current()
    a, b = (t.key for t in before.inputs.targets)
    dialog = JrotRulesDialog(
        before.inputs, {a: "J1", b: "J2"}, root.icons, language, root
    )
    try:
        fixed = dialog.controls["W1"][0]
        other = dialog.controls["W2"][0]
        fixed.setCurrentIndex(fixed.findData(a))
        assert not other.model().item(other.findData(a)).isEnabled()

        def choose_other() -> None:
            """Inspect the actual offered choices and exclude only the nonfixed Job.

            Args:
                None.

            Returns:
                None; the fixed Job is not offered as a contradictory exclusion.
            """
            picker = QApplication.activeModalWidget()
            assert isinstance(picker, JrotCatalogPicker)
            assert a not in picker.nodes and b in picker.nodes
            picker.nodes[b].setCheckState(0, Qt.CheckState.Checked)
            picker.accept_selection()

        QTimer.singleShot(0, choose_other)
        dialog.choose_exclusions("W1")
        assert dialog.excluded["W1"] == {b}
        assert not fixed.model().item(fixed.findData(b)).isEnabled()
        fixed.setCurrentIndex(0)
        # W1 can now only do J1: fixing W2 to J1 would break complete staffing.
        other.setCurrentIndex(other.findData(a))
        assert other.currentData() is None and dialog.guidance.text()
        assert root.current() == before
    finally:
        dialog.reject()
        dialog.deleteLater()
        dispose(root)


@pytest.mark.parametrize("language", list(Language))
def test_excluding_every_job_retains_previous_draft(
    tmp_path: Path, language: Language
) -> None:
    """Reject an exclusion set with no staffing solution before accepting it locally.

    Args:
        tmp_path: Private source project.
        language: Maintained captions.

    Returns:
        None; the prior set and source remain unchanged, with an explanatory warning.
    """
    root = planning_dialog(tmp_path, language)
    before = root.current()
    labels = {t.key: t.job_id for t in before.inputs.targets}
    dialog = JrotRulesDialog(before.inputs, labels, root.icons, language, root)
    try:

        def choose_all() -> None:
            """Offer the complete local exclusion set through the real nested picker.

            Args:
                None.

            Returns:
                None; the owner rejects impossible staffing after the picker returns.
            """
            picker = QApplication.activeModalWidget()
            picker.check_visible(True)
            picker.accept_selection()

        QTimer.singleShot(0, choose_all)
        with patch.object(QMessageBox, "warning") as warning:
            dialog.choose_exclusions("W1")
        warning.assert_called_once()
        assert dialog.excluded["W1"] == set()
        assert root.current() == before
    finally:
        dialog.reject()
        dialog.deleteLater()
        dispose(root)


def test_unused_neighbor_links_survive_disclosure_projection(tmp_path: Path) -> None:
    """Disabling a worker rule never silently removes a previously linked result.

    Args:
        tmp_path: Disposable retained real optimization.

    Returns:
        None; clearing remains an explicit host-owned action even with no active rule.
    """
    root = solved_dialog(tmp_path)
    try:
        before = root.current()
        boundary = capture_rotation_boundary(before, previous=True)
        inputs = replace(before.inputs, previous=boundary)
        root.neighbors.project(inputs, {before.scenario_id: "Named source rotation"})
        assert not root.neighbors.choose_buttons[True].isEnabled()
        assert root.neighbors.clear_buttons[True].isEnabled()
        assert "Named source rotation" in root.neighbors.links.text()
        assert root.current() == before
    finally:
        dispose(root)


@pytest.mark.parametrize("language", list(Language))
def test_rule_summary_tracks_local_choices_and_missing_neighbor_context(
    tmp_path: Path, language: Language
) -> None:
    """Keep counts and warnings synchronized without accepting local edits.

    Args:
        tmp_path: Disposable project with two selected workers and Jobs.
        language: Both maintained title, guidance and summary languages.

    Returns:
        None; fixed, excluded and checkbox changes update the bottom panel, clearing
        restores the unrestricted message, and Cancel leaves the rotation unchanged.
    """
    root = planning_dialog(tmp_path, language)
    before = root.current()
    labels = {t.key: t.job_id for t in before.inputs.targets}
    dialog = JrotRulesDialog(before.inputs, labels, root.icons, language, root)
    try:
        dialog.show()
        QTest.qWait(20)
        assert dialog.title.text() == dialog.windowTitle()
        assert all(label.isVisible() for label in dialog.summary_counts.values())
        assert dialog.summary_status.isVisible()
        assert all(
            label.parent() is dialog.table.cellWidget(row, 2)
            for row, label in enumerate(dialog.exclusion_summaries.values())
        )
        empty_status = dialog.summary_status.text()
        first = next(iter(dialog.controls))
        controls = dialog.controls[first]
        controls[0].setCurrentIndex(1)
        assert dialog.summary_counts["fixed"].text().startswith("<b>1</b>")
        dialog.clear_fixed()
        assert dialog.summary_counts["fixed"].text().startswith("<b>0</b>")
        dialog.excluded[first] = {before.inputs.targets[0].key}
        dialog.update_exclusion_label(first)
        dialog.refresh_fixed_choices()
        assert dialog.summary_counts["excluded"].text().startswith("<b>1</b>")
        dialog.clear_excluded()
        controls[2].setChecked(True)
        assert dialog.summary_counts["high"].text().startswith("<b>1</b>")
        controls[3].setChecked(True)
        assert "03" in dialog.summary_status.text()
        assert "previous" in dialog.summary_status.text() or (
            "anterior" in dialog.summary_status.text()
        )
        controls[4].setChecked(True)
        assert "following" in dialog.summary_status.text() or (
            "siguiente" in dialog.summary_status.text()
        )
        dialog.bulk_checks(3, False)
        assert dialog.summary_counts["high"].text().startswith("<b>0</b>")
        assert dialog.summary_status.text() == empty_status
        dialog.reject()
        assert root.current() == before
    finally:
        dialog.deleteLater()
        dispose(root)

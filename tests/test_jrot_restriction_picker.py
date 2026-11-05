"""Native exclusion routes and single-column catalog contracts on private projects.

These tests exercise the nested picker used by actual restriction buttons, including
fixed/excluded interaction, cancellation and accepted shared history.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QMessageBox

from ergotools.bootstrap import load_icons
from ergotools.domain.language import Language
from ergotools.domain.rotation_constraints import ExcludedPosition, FixedPosition
from ergotools.presentation.desktop.jrot_catalog_picker import (
    JrotCatalogChoice,
    JrotCatalogPicker,
)
from ergotools.presentation.desktop.jrot_rules_dialog import JrotRulesDialog
from tests.test_jrot_guided_ui import dispose
from tests.test_jrot_planning_ui import await_result, planning_dialog


@pytest.mark.parametrize("language", list(Language))
def test_fixed_then_exclusion_modal_accept_cancel_and_shared_history(
    tmp_path: Path, language: Language
) -> None:
    """Reproduce the reported fixed-Job then exclusion-button route without a crash.

    Args:
        tmp_path: Private project backing path.
        language: Maintained caption languages.

    Returns:
        None; accepted rules undo/redo together and cancelled selections stay local.
    """
    root = planning_dialog(tmp_path, language)
    before = root.current()
    a, b = (t.key for t in before.inputs.targets)
    try:

        def edit_rules() -> None:
            """Use real modal buttons and nested native events to select exclusions.

            Args:
                None.

            Returns:
                None; the parent form remains alive after either picker outcome.
            """
            modal = QApplication.activeModalWidget()
            assert isinstance(modal, JrotRulesDialog)
            fixed, excluded, high, previous, following = modal.controls["W1"]
            fixed.setCurrentIndex(fixed.findData(a))
            assert not previous.isEnabled() and not following.isEnabled()
            high.setChecked(True)
            assert previous.isEnabled() and following.isEnabled()
            assert all(
                c.toolTip() for c in (fixed, excluded, high, previous, following)
            )

            def choose() -> None:
                """Choose the other Job by its exact key and accept the nested picker.

                Args:
                    None.

                Returns:
                    None; source and destination forms use distinct owned lifetimes.
                """
                picker = QApplication.activeModalWidget()
                assert isinstance(picker, JrotCatalogPicker)
                assert picker.tree.columnCount() == 2
                picker.nodes[b].setCheckState(0, Qt.CheckState.Checked)
                picker.accept_selection()

            QTimer.singleShot(0, choose)
            excluded.click()
            assert modal.excluded["W1"] == {b}
            QTimer.singleShot(0, lambda: QApplication.activeModalWidget().reject())
            excluded.click()
            assert modal.excluded["W1"] == {b}
            # Contradictory fixed/excluded selection is reported and stays editable.
            modal.excluded["W1"].add(a)
            with patch.object(QMessageBox, "warning") as warning:
                modal.accept_rules()
            warning.assert_called_once()
            assert modal.isVisible()
            modal.excluded["W1"].remove(a)
            high.setChecked(False)
            modal.accept_rules()

        QTimer.singleShot(0, edit_rules)
        root.edit_rules()
        assert root.current().inputs.rules == (
            FixedPosition("W1", a),
            ExcludedPosition("W1", b),
        )
        accepted = root.current()
        assert root.workspace.editing.replay(redo=False)
        root.reload()
        assert root.current() == before
        assert root.workspace.editing.replay(redo=True)
        root.reload()
        assert root.current() == accepted
        root.solve.start()
        await_result(root)
        root.solve.keep_result()
        assert root.current().run is not None
        assert root.current().run.arrangement[0].target_keys == (a, a)
    finally:
        dispose(root)


def test_single_column_picker_and_mismatched_rows_have_explicit_contract() -> None:
    """A one-column catalog supports initials; malformed rows fail before native events.

    Args:
        None.

    Returns:
        None; no unavailable tuple index is accessed by filtering.
    """
    picker = JrotCatalogPicker(
        "Jobs",
        ("Name",),
        (JrotCatalogChoice("one", ("Álpha",)),),
        (),
        Language.ENGLISH,
        None,
        icons=load_icons(),
        entity_icon="job_management",
    )
    try:
        picker.select_letter("A")
        assert not picker.nodes["one"].isHidden()
        assert picker.initial(picker.choices[0]) == "A"
        assert picker.alphabet.buttons["A"].isEnabled()
        assert not picker.alphabet.buttons["Z"].isEnabled()
        with pytest.raises(ValueError, match="columns"):
            JrotCatalogPicker(
                "Bad",
                ("ID", "Name"),
                picker.choices,
                (),
                Language.ENGLISH,
                None,
                icons=load_icons(),
                entity_icon="job_management",
            )
    finally:
        picker.deleteLater()
        QTest.qWait(1)


def test_missing_task_diagnostic_and_centered_result_geometry(tmp_path: Path) -> None:
    """Missing inputs identify their task; result rows use spare height.

    Args:
        tmp_path: Disposable native project.

    Returns:
        None; diagnostics never turn missing inputs into numerical coefficients.
    """
    from ergotools.domain.assessments.document import AssessmentKind
    from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
    from ergotools.domain.job_risk import JobRiskMeasurement
    from ergotools.domain.model_units import MeasurementSystem

    root = planning_dialog(tmp_path, Language.ENGLISH)
    try:
        root.solve.start()
        await_result(root)
        root.solve.keep_result()
        table = root.solve.tabs.widget(0)
        root.resize(1700, 1100)
        root.show()
        QTest.qWait(20)
        assert table.verticalHeader().width() >= 44
        assert table.item(0, 1).textAlignment() == Qt.AlignmentFlag.AlignCenter
        assert table.item(0, 1).font().bold()
        assert table.verticalScrollBar().maximum() == 0
        assert all(table.rowHeight(i) >= 36 for i in range(table.rowCount()))
        jobs, risks = root.workspace.read_jobs(), root.workspace.read_job_risk()
        original = risks.risk.for_job("J1")
        missing = JobRiskMeasurement(
            AssessmentKind.LIFFT,
            unit="metric",
            source=LifftDraft(MeasurementSystem.METRIC, (LifftTask("1", 30, 49),)),
        )
        changed = replace(
            original,
            measurements=tuple(
                missing if m.kind is AssessmentKind.LIFFT else m
                for m in original.measurements
            ),
        )
        root.workspace.save_job_details(jobs, risks, jobs.jobs.jobs[0], changed)
        root.reload()
        assert "LiFFT · Task 1: repetitions" in root.job_readiness.text()
        root.go(5)
        assert "Input check" in root.readiness.text()
        assert "complete selected-tool Job values" in root.readiness.text()
    finally:
        dispose(root)

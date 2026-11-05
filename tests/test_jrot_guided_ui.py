"""Real guided entry, shared calculators/history and sole Main Save acceptance.

Native Qt tests use disposable projects. They exercise real controls rather than a
second data model or generated sample schedules; normal JROT/optimizer remain separate.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QComboBox, QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.rotation_scenarios import create_scenario
from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.rotation_timing import equal_timing
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.jrot_catalog_picker import JrotCatalogPicker
from ergotools.presentation.desktop.jrot_dialog import JrotDialog
from ergotools.presentation.desktop.rotation_timing_dialog import RotationTimingDialog
from tests.test_rotation_scenario_storage import scenario_workspace
from tests.test_rotation_scenarios import scenario_inputs

# Retain the native application for all owned dialogs and deferred geometry callbacks.
_APP = QApplication.instance() or QApplication([])


def populated_dialog(
    tmp_path: Path, language: Language = Language.ENGLISH
) -> JrotDialog:
    """Create a guided real project with participants/timing but no invented Job values.

    Args:
        tmp_path: Disposable project/preferences directory.
        language: Current owned interface captions.

    Returns:
        Shown dialog; caller closes the borrowed workspace explicitly after teardown.
    """
    workspace = scenario_workspace(tmp_path)
    inputs = scenario_inputs()
    record = replace(
        create_scenario("timing", "R1", "Morning packing", inputs.planned_date),
        inputs=inputs,
    )
    workspace.rotation_scenarios().replace_rotation_scenario(None, record)
    dialog = JrotDialog(workspace, load_icons(), language=language)
    dialog.show()
    QTest.qWait(50)
    assert not dialog.error.text()
    return dialog


def dispose(dialog: JrotDialog) -> None:
    """Release native callbacks before discarding the private synthetic project.

    Args:
        dialog: Test-owned guided window.

    Returns:
        None; no maintained project or personal preference is touched.
    """
    dialog.solve.discard()
    dialog.accept()
    dialog.deleteLater()
    dialog.workspace.close(choice=CloseChoice.DISCARD)
    _APP.processEvents()


@pytest.mark.parametrize("language", list(Language))
def test_empty_open_is_read_only_then_yes_choice_and_metadata_save(
    tmp_path: Path, language: Language
) -> None:
    """Opening/closing creates nothing; explicit name/date/Yes survive Main Save.

    Args:
        tmp_path: Disposable native file.
        language: Both maintained caption languages.

    Returns:
        None; arbitrary review pages require neither fake data nor a baseline.
    """
    workspace = scenario_workspace(tmp_path)
    path = Path(workspace.location)
    before = path.read_bytes()
    dialog = JrotDialog(workspace, load_icons(), language=language)
    try:
        assert not workspace.has_unsaved_changes
        assert workspace.rotation_scenarios().load_rotation_scenarios() == ()
        for page in reversed(range(8)):
            dialog.go(page)
            assert dialog.pages.currentIndex() == page
        assert not workspace.has_unsaved_changes
        dialog.go(0)
        dialog.name.setText("Morning packing")
        dialog.create_rotation()
        key = dialog.current().scenario_id
        dialog.observed.button(1).click()
        assert dialog.current().inputs.baseline == ()
        assert dialog.current().inputs.workers == ()
        assert path.read_bytes() == before
        assert workspace.save()
        with AssessmentProjectFile.open(path) as stored:
            assert stored.format_version == 24
            assert stored.load_rotation_scenarios()[0].inputs.baseline == ()
            assert stored.last_rotation_selection() == key
        assert dialog.history.editing is workspace.editing
        dialog.name.setText("")
        dialog.metadata_finished()
        assert dialog.error.text() and not dialog.prepare()
        dialog.name.setText("Renamed morning")
        assert dialog.prepare()
    finally:
        dispose(dialog)


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_shared_task_calculation_each_cell_replays_repeatedly(
    tmp_path: Path, kind: AssessmentKind
) -> None:
    """Every real tool calculates through the existing shared grid and project history.

    Args:
        tmp_path: Disposable project.
        kind: LiFFT, DUET or ST scientific model.

    Returns:
        None; clean navigation is separate from data and repeated replay stays usable.
    """
    dialog = populated_dialog(tmp_path)
    try:
        dialog.go(4)
        panel = dialog.job_panel
        panel.tabs.setCurrentIndex(list(AssessmentKind).index(kind))
        assert panel.measurement(kind).source is None
        editor = panel.editors[kind]
        values = (
            ("30", "49", "100")
            if kind is AssessmentKind.LIFFT
            else (("3", "100") if kind is AssessmentKind.DUET else ("30", "49", "100"))
        )
        fields = editor.inputs[0]
        if kind is AssessmentKind.DUET:
            fields[0].setCurrentIndex(fields[0].findData(6))
            fields[1].setText("100")
            fields[1].editingFinished.emit()
        else:
            numeric = fields[1:] if kind is AssessmentKind.TST else fields
            for control, value in zip(numeric, values, strict=True):
                control.setText(value)
                control.editingFinished.emit()
                assert not panel.error.text()
        item = panel.measurement(kind)
        assert item.complete and item.task_results
        assert panel.results.risk_gauge.has_value
        assert dialog.workspace.read_job_risk().risk.for_job("J1").measurements
        assert dialog.workspace.editing.replay(redo=False)
        dialog.reload()
        assert not dialog.job_panel.measurement(kind).complete
        assert dialog.workspace.editing.replay(redo=True)
        dialog.reload()
        assert dialog.job_panel.measurement(kind) == item
        for _ in range(2):
            cell = panel.editors[kind].inputs[0][-1]
            cell.setText("200")
            cell.editingFinished.emit()
            changed = panel.measurement(kind)
            assert changed.complete and changed != item
            assert dialog.workspace.editing.replay(redo=False)
            dialog.reload()
            assert panel.measurement(kind) == item
        assert not panel.error.text()
    finally:
        dispose(dialog)


def test_observed_matrix_cell_history_and_destructive_reshape_warning(
    tmp_path: Path,
) -> None:
    """Untouched matrix cells stay None; separate edits undo one-by-one.

    Args:
        tmp_path: Disposable project.

    Returns:
        None; rejected Yes/No data loss leaves the original observed matrix exact.
    """
    dialog = populated_dialog(tmp_path)
    try:
        dialog.choose_observed(True)
        dialog.go(3)
        first = dialog.matrix.cellWidget(0, 1)
        second = dialog.matrix.cellWidget(0, 2)
        assert isinstance(first, QComboBox) and isinstance(second, QComboBox)
        first.setCurrentIndex(1)
        one = dialog.current().inputs
        assert one.baseline[0].target_keys[0] is not None
        assert one.baseline[0].target_keys[1] is None
        second.setCurrentIndex(2)
        two = dialog.current().inputs
        assert two != one
        assert dialog.workspace.editing.replay(redo=False)
        dialog.reload()
        assert dialog.current().inputs == one
        assert dialog.workspace.editing.replay(redo=True)
        dialog.reload()
        assert dialog.current().inputs == two
        with patch.object(dialog, "confirm", return_value=False):
            dialog.choose_observed(False)
        assert dialog.current().inputs == two
        with patch.object(dialog, "confirm", return_value=True):
            dialog.choose_observed(False)
        assert dialog.current().inputs.baseline is None
        assert dialog.workspace.editing.replay(redo=False)
        dialog.reload()
        assert dialog.current().inputs == two
    finally:
        dispose(dialog)


def test_real_picker_acceptance_and_duplicate_delete_selection_replay(
    tmp_path: Path,
) -> None:
    """Catalog pickers and lifecycle actions use exact IDs and one coherent history.

    Args:
        tmp_path: Disposable project.

    Returns:
        None; no permanent assignment is created by selecting participants.
    """
    dialog = populated_dialog(tmp_path)
    try:

        def choose_all() -> None:
            """Accept all offered current records through the real modal picker.

            Args:
                None.

            Returns:
                None; no synthetic default is inserted into the source catalogs.
            """
            picker = QApplication.activeModalWidget()
            assert isinstance(picker, JrotCatalogPicker)
            picker.check_visible(True)
            picker.accept_selection()

        QTimer.singleShot(0, choose_all)
        dialog.choose_jobs()
        QTimer.singleShot(0, choose_all)
        dialog.choose_workers()
        assert len(dialog.current().inputs.targets) == 2
        assert dialog.workspace.read_jobs().jobs.assignments == ()
        original = dialog.current()
        with patch(
            "PyQt5.QtWidgets.QInputDialog.getText",
            return_value=("Independent copy", True),
        ):
            dialog.duplicate()
        copied = dialog.current()
        assert copied.source_scenario_id == original.scenario_id
        assert copied.run is None and copied.inputs == original.inputs
        with patch.object(dialog, "confirm", return_value=True):
            dialog.delete_rotation()
        assert dialog.current() is None
        assert dialog.workspace.editing.replay(redo=False)
        dialog.reload()
        assert dialog.current() == copied
        assert dialog.workspace.editing.replay(redo=True)
        dialog.reload()
        assert dialog.current() is None
    finally:
        dispose(dialog)


def test_copied_timing_editor_never_modifies_shift_template(tmp_path: Path) -> None:
    """Reusable editor callbacks edit only this rotation, including shared Undo/Redo.

    Args:
        tmp_path: Disposable current project.

    Returns:
        None; copied timing can diverge from its recurring Shift independently.
    """
    dialog = populated_dialog(tmp_path)
    try:
        original = dialog.current()
        templates = dialog.workspace.load_shift_timings()
        timing = RotationTimingDialog(
            dialog.workspace,
            "Day",
            load_icons(),
            parent=dialog,
            read_target=lambda: dialog.timing_target("R1"),
            write_target=lambda expected, candidate: dialog.write_timing(
                "R1", expected, candidate
            ),
            target_label="Morning packing",
        )
        try:
            timing.count.setValue(4)
            assert dialog.current().inputs.timing == equal_timing(480, 4)
            assert dialog.workspace.load_shift_timings() == templates
            assert timing.history.editing is dialog.workspace.editing
            assert dialog.workspace.editing.replay(redo=False)
            timing.reload()
            assert dialog.current() == original
            assert timing.count.value() == 2
            with patch.object(QMessageBox, "question", return_value=QMessageBox.No):
                timing.clear_template()
            assert dialog.current() == original
        finally:
            timing.accept()
            timing.deleteLater()
        dialog.reload()
    finally:
        dispose(dialog)


def test_copied_job_subset_and_named_paste_keep_source_independent(
    tmp_path: Path,
) -> None:
    """Source copy and shared paste retain exact independent tasks.

    Args:
        tmp_path: Disposable current Job/scenario project.

    Returns:
        None; source copy/paste are each reversible single accepted data operations.
    """
    from ergotools.application.assessment_clipboard import (
        assessment_input_fields,
        prepare_assessment_paste,
    )
    from ergotools.application.job_calculation import calculate_job_measurement
    from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
    from ergotools.domain.job_risk import JobRiskValues
    from ergotools.domain.model_units import MeasurementSystem
    from ergotools.presentation.desktop.job_assessment_dialog import JobCopyDialog

    dialog = populated_dialog(tmp_path)
    try:
        workspace = dialog.workspace
        source = LifftDraft(
            MeasurementSystem.METRIC,
            (LifftTask("one", 30, 49, 100), LifftTask("two", 20, 98, 200)),
        )
        item = calculate_job_measurement(
            "timing", "J2", source, MeasurementSystem.METRIC
        )
        jobs, risks = workspace.read_jobs(), workspace.read_job_risk()
        workspace.save_job_details(
            jobs,
            risks,
            next(j for j in jobs.jobs.jobs if j.job_id == "J2"),
            JobRiskValues("J2", (item,)),
        )
        dialog.go(4)

        def choose_source() -> None:
            """Choose one source task using the real read-only Job copy modal.

            Args:
                None.

            Returns:
                None; source tasks and values are never changed by the picker.
            """
            picker = QApplication.activeModalWidget()
            assert isinstance(picker, JobCopyDialog)
            picker.source_combo.setCurrentIndex(picker.source_combo.findData("J2"))
            picker.use_button.click()

        QTimer.singleShot(0, choose_source)
        dialog.job_panel.copy_values(False)
        assert dialog.job_panel.measurement(AssessmentKind.LIFFT) == item
        editor = dialog.job_panel.editors[AssessmentKind.LIFFT]
        copied = editor.source
        named = prepare_assessment_paste(
            copied, (("Inspect", "25", "50", "120"),), assessment_input_fields(copied)
        )
        assert editor._accept_shared_source(copied, named, "assessment.paste", True)
        assert dialog.job_panel.measurement(AssessmentKind.LIFFT).complete
        assert editor.source.tasks[0].task_name == "Inspect"
        assert workspace.read_job_risk().risk.for_job("J2").measurements == (item,)
        assert workspace.editing.replay(redo=False)
        dialog.reload()
        assert dialog.job_panel.measurement(AssessmentKind.LIFFT) == item
        assert workspace.save()
        with AssessmentProjectFile.open(Path(workspace.location)) as stored:
            assert stored.load_job_risk().for_job("J1").measurements == (item,)
    finally:
        dispose(dialog)


def test_direct_entry_pending_tab_and_failed_write_remain_correctable(
    tmp_path: Path,
) -> None:
    """A still-focused direct field belongs to its original tool during tab navigation.

    Args:
        tmp_path: Disposable real project.

    Returns:
        None; failed persistence retains intent and retry cannot silently clear input.
    """
    dialog = populated_dialog(tmp_path)
    try:
        panel = dialog.job_panel
        dialog.go(4)
        panel.modes.button(0).click()
        field = panel.direct_values.fields[AssessmentKind.LIFFT]
        field.setText("0.01")
        panel.tabs.setCurrentIndex(1)
        assert panel.measurement(AssessmentKind.LIFFT).complete
        assert not panel.measurement(AssessmentKind.DUET).complete
        panel.tabs.setCurrentIndex(0)
        field = panel.direct_values.fields[AssessmentKind.LIFFT]
        field.setText("0.02")
        with patch.object(
            dialog.workspace,
            "save_job_details",
            side_effect=OSError("injected write failure"),
        ):
            field.editingFinished.emit()
            assert not panel.prepare()
            assert panel.has_pending() and "injected" in panel.error.text()
        assert panel.prepare() and not panel.has_pending()
        assert panel.measurement(AssessmentKind.LIFFT).cumulative_damage == 0.02
        assert panel.measurement(AssessmentKind.DUET).source is None
    finally:
        dispose(dialog)


@pytest.mark.parametrize("mask", range(1, 8))
def test_analysis_subsets_and_display_tabs_are_independent(
    tmp_path: Path, mask: int
) -> None:
    """Every nonempty tool subset persists without inferring a displayed-tool objective.

    Args:
        tmp_path: Disposable scenario project.
        mask: Independent bit selection across the three tool identities.

    Returns:
        None; empty selection is refused and calculator display stays intact.
    """
    dialog = populated_dialog(tmp_path)
    try:
        kinds = tuple(AssessmentKind)
        wanted = tuple(kind for i, kind in enumerate(kinds) if mask & (1 << i))
        for kind, check in dialog.tools.items():
            check.setChecked(kind in wanted)
        dialog.tools_changed()
        assert dialog.current().inputs.tools == wanted
        dialog.job_panel.tabs.setCurrentIndex(2)
        assert dialog.current().inputs.tools == wanted
        assert dialog.view.kind is AssessmentKind.TST
        for check in dialog.tools.values():
            check.setChecked(False)
        dialog.tools_changed()
        assert dialog.current().inputs.tools == wanted
        assert tuple(k for k, c in dialog.tools.items() if c.isChecked()) == wanted
    finally:
        dispose(dialog)


def test_stale_matrix_and_task_widgets_cannot_edit_a_rebound_record(
    tmp_path: Path,
) -> None:
    """Retired projection signals cannot overwrite another Job or restored scenario.

    Args:
        tmp_path: Disposable guided project.

    Returns:
        None; exact expected state remains authoritative over late native callbacks.
    """
    dialog = populated_dialog(tmp_path)
    try:
        dialog.choose_observed(True)
        old = dialog.matrix.cellWidget(0, 1)
        generation = dialog._generation
        source = dialog.current()
        changed = replace(source, description="external accepted edit")
        dialog.repository.replace_rotation_scenario(source, changed)
        dialog.matrix_changed(generation, "R1", "W1", 0, old, 1)
        assert dialog.current() == changed
        assert dialog.error.text()
        dialog.go(4)
        panel = dialog.job_panel
        field = panel.editors[AssessmentKind.LIFFT].inputs[0][0]
        dialog.job_list.setCurrentRow(1)
        before = dialog.workspace.read_job_risk().risk
        field.setText("90")
        field.editingFinished.emit()
        assert dialog.workspace.read_job_risk().risk == before
        assert panel.job_id == "J2"
    finally:
        dispose(dialog)


def test_production_entry_does_not_require_developer_switch(
    tmp_path: Path,
) -> None:
    """Normal JROT opens guided composition without enabling Developer or Legacy.

    Args:
        tmp_path: Disposable project/preferences and Main window.

    Returns:
        None; no opening action writes a project or persists the Developer preference.
    """
    from ergotools.bootstrap import create_window

    workspace = scenario_workspace(tmp_path)
    path = Path(workspace.location)
    workspace.close(choice=CloseChoice.DISCARD)
    main = create_window(
        tmp_path / "main-settings.json",
        original_controls=True,
        original_navigation=True,
    )
    try:
        main.presenter.workspace.switch(str(path), None)
        main.refresh()
        before = path.read_bytes()
        with patch.object(JrotDialog, "exec", return_value=0) as opened:
            main.open_rotation()
            opened.assert_called_once()
            assert not main._developer_enabled and not main._legacy_enabled
        assert path.read_bytes() == before
        assert not main.presenter.workspace.has_unsaved_changes
        assert main._rotation_opener is not None
        assert main._guided_rotation_opener is not None
    finally:
        main.presenter.workspace.close(choice=CloseChoice.DISCARD)
        main.close()
        main.deleteLater()
        _APP.processEvents()


def test_guided_panel_inherits_personal_marker_preferences(tmp_path: Path) -> None:
    """Gauge appearance comes from application preferences, never scenario data.

    Args:
        tmp_path: Disposable scenario and personal settings.

    Returns:
        None; merely constructing the panel accepts no Job measurement or preference.
    """
    from ergotools.application.gauge_preferences import GaugeMarkerSettings

    workspace = scenario_workspace(tmp_path)
    settings = GaugeMarkerSettings(interval=20)
    dialog = JrotDialog(workspace, load_icons(), markers=settings)
    try:
        assert dialog.job_panel.results.risk_gauge.marker_settings == settings
        assert not workspace.has_unsaved_changes
    finally:
        dispose(dialog)


def test_blank_source_mode_is_clean_history_and_populated_switch_is_one_edit(
    tmp_path: Path,
) -> None:
    """Blank method choices are views; replacing entered data and method is atomic.

    Args:
        tmp_path: Disposable project/scenario with two real Jobs.

    Returns:
        None; Undo/Redo restores the displayed method together with exact accepted data.
    """
    dialog = populated_dialog(tmp_path)
    try:
        assert dialog.workspace.save()
        panel = dialog.job_panel
        panel.modes.button(0).click()
        assert panel.modes.checkedId() == 0 and not dialog.workspace.has_unsaved_changes
        assert dialog.workspace.editing.replay(redo=False)
        dialog.reload()
        assert panel.modes.checkedId() == 1
        assert dialog.workspace.editing.replay(redo=True)
        dialog.reload()
        assert panel.modes.checkedId() == 0
        field = panel.direct_values.fields[AssessmentKind.LIFFT]
        field.setText("0.01")
        field.editingFinished.emit()
        original = panel.measurement(AssessmentKind.LIFFT)
        revision = dialog.owner.history.revision
        with patch.object(panel, "confirm", return_value=True):
            panel.modes.button(1).click()
        assert (
            panel.modes.checkedId() == 1
            and panel.measurement(AssessmentKind.LIFFT).source is not None
        )
        assert dialog.owner.history.revision == revision + 1
        assert dialog.owner.replay(redo=False)
        dialog.reload()
        assert (
            panel.modes.checkedId() == 0
            and panel.measurement(AssessmentKind.LIFFT) == original
        )
        assert dialog.owner.replay(redo=True)
        dialog.reload()
        assert (
            panel.modes.checkedId() == 1
            and panel.editors[AssessmentKind.LIFFT].task_count == 1
        )
    finally:
        dispose(dialog)


def test_worker_source_subset_reuses_readonly_picker_and_keeps_original(
    tmp_path: Path,
) -> None:
    """The guided copy action retains selected worker tasks as independent Job data.

    Args:
        tmp_path: Disposable project with a real calculated standalone source.

    Returns:
        None; copying does not change worker ownership, units, inputs or saved outputs.
    """
    from datetime import date

    from ergotools.application.job_calculation import calculate_job_measurement
    from ergotools.domain.job_catalog import Job
    from ergotools.domain.job_risk import JobRiskValues
    from ergotools.domain.rotation_scheme import RotationTarget
    from ergotools.presentation.desktop.job_assessment_dialog import JobAssessmentDialog
    from tests.test_workplace_assignment_workflow import (
        open_private,
        seed_workplace_source,
    )

    path = seed_workplace_source(tmp_path, AssessmentKind.LIFFT)
    workspace = open_private(path)
    metadata = workspace.project_metadata
    source = workspace.assessment_source("source")
    expected = calculate_job_measurement(
        metadata.project_id, "target", source, metadata.default_units
    )
    jobs, risks = workspace.read_jobs(), workspace.read_job_risk()
    workspace.save_job_details(
        jobs, risks, Job("target", "Packing"), JobRiskValues("target")
    )
    record = create_scenario(metadata.project_id, "R1", "Copy test", date(2026, 11, 2))
    record = replace(
        record, inputs=replace(record.inputs, targets=(RotationTarget("target"),))
    )
    workspace.rotation_scenarios().replace_rotation_scenario(None, record)
    dialog = JrotDialog(workspace, load_icons())
    try:

        def choose_worker() -> None:
            """Inspect read-only tasks and copy the one populated source row.

            Args:
                None.

            Returns:
                None; the existing picker performs its normal source revalidation.
            """
            picker = QApplication.activeModalWidget()
            assert isinstance(picker, JobAssessmentDialog)
            node = picker.tree.currentItem()
            assert node is not None
            node.setExpanded(True)
            detail = picker.task_details["source"]
            assert detail.grid.inputs[0][0].isReadOnly()
            detail.grid.set_task_selection((source.tasks[0].task_id,))
            picker.use_button.click()

        QTimer.singleShot(0, choose_worker)
        dialog.job_panel.copy_values(True)
        assert dialog.job_panel.measurement(AssessmentKind.LIFFT) == expected
        assert workspace.assessment_source("source") == source
        assert workspace.editing.replay(redo=False)
        dialog.reload()
        assert dialog.job_panel.measurement(AssessmentKind.LIFFT).source is None
    finally:
        dispose(dialog)


def test_independent_rotation_clocks_replay_without_touching_shift(
    tmp_path: Path,
) -> None:
    """Both clocks must be valid; overnight edits never change recurring Shift metadata.

    Args:
        tmp_path: Disposable project with original 08:00-16:00 Shift clocks.

    Returns:
        None; source hierarchy stays exact and invalid tokens remain correctable.
    """
    dialog = populated_dialog(tmp_path)
    try:
        hierarchy = dialog.workspace.read_hierarchy().hierarchy
        original = dialog.current()
        dialog.start_time.set_value("22:00")
        dialog.end_time.set_value("06:00")
        dialog.clocks_finished()
        assert dialog.current().inputs.start_minute == 1320
        assert dialog.current().inputs.timing == original.inputs.timing
        assert dialog.workspace.read_hierarchy().hierarchy == hierarchy
        assert dialog.owner.replay(redo=False)
        dialog.reload()
        assert dialog.current() == original
        assert dialog.start_time.clock_text() == "08:00"
        dialog.start_time.set_value("bad clock")
        assert not dialog.prepare()
        assert dialog.start_time.clock_text() == "bad clock"
        assert dialog.current() == original
        dialog.start_time.set_value("08:00")
        assert dialog.prepare()
        dialog.name.setText("")
        dialog.start_time.set_value("09:00")
        dialog.end_time.set_value("17:00")
        dialog.clocks_finished()
        assert dialog.current().inputs.start_minute == 540
        assert dialog.name.text() == "" and not dialog.prepare()
        dialog.name.setText(original.name)
        assert dialog.prepare()
    finally:
        dispose(dialog)

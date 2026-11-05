"""Atomic paste/catalog registration through real worker, Job and guided editors.

Private projects verify one history action, reversible consent, durable reopening,
Unicode name reuse, mapping boundaries and failure rollback. No maintained file is used.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtWidgets import QApplication, QComboBox, QDialog, QMessageBox

from ergotools.application.assessment_clipboard import (
    assessment_input_fields,
    prepare_assessment_paste,
)
from ergotools.application.assessment_import import ImportProfile
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.job_calculation import blank_job_source, resize_job_source
from ergotools.application.task_catalog import (
    label_assessment_task,
    reusable_pasted_names,
)
from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentDraft, AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.task_catalog import TaskDefinition
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.settings_store import JsonSettingsStore
from ergotools.infrastructure.tabular_file_reader import SpreadsheetValueReader
from ergotools.presentation.desktop.assessment_editor_preferences import (
    AssessmentEditorPreferences,
)
from ergotools.presentation.desktop.assessment_paste_dialog import AssessmentPasteDialog
from ergotools.presentation.desktop.assessment_task_grid import AssessmentTaskGrid
from ergotools.presentation.desktop.job_management_dialog import JobManagementDialog
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_job_calculators import enter_job
from tests.test_jrot_planning_ui import dispose, planning_dialog
from tests.test_saved_tool_data import window as window
from tests.test_task_names_ui import reopen_grid
from tests.test_unified_project_save import editing_workspace

# Retain Qt lifetime while real history actions, dropdowns and clipboard are inspected.
_APP = QApplication.instance() or QApplication([])


def enter_name(grid: AssessmentTaskGrid, row: int, name: str) -> None:
    """Complete one actual editable name field before an independent paste action.

    Args:
        grid: Owned worker or Job grid.
        row: Existing zero-based task row.
        name: Literal typed name; this action does not create a reusable definition.

    Returns:
        None after the ordinary editingFinished host acceptance.
    """
    control = grid.task_names[row]
    assert isinstance(control, QComboBox)
    control.setEditText(name)
    control.lineEdit().editingFinished.emit()


def pasted_rows(kind: AssessmentKind) -> tuple[tuple[str, ...], ...]:
    """Return complete source inputs with repeated/new/existing Unicode names.

    Args:
        kind: Target tool determines numeric and selector columns.

    Returns:
        Four TSV-compatible task rows; three names normalize to the same new entry.
    """
    values = (
        ("4", "100")
        if kind is AssessmentKind.DUET
        else (
            ("Handling Load", "30", "49.05", "100")
            if kind is AssessmentKind.TST
            else ("30", "49.05", "100")
        )
    )
    return tuple(
        (name, *values) for name in ("Packing", "Corte Ñ", "Corte N\u0303", " corte ñ ")
    )


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_pure_name_plan_limits_scope_and_preserves_inputs(kind: AssessmentKind) -> None:
    """Deduplicate names without merging explicit identities or unrelated local labels.

    Args:
        kind: All tools retain their exact measurements and row identities.

    Returns:
        None; only mapped destination task IDs acquire reusable references.
    """
    original = blank_job_source(kind, MeasurementSystem.METRIC)
    source = prepare_assessment_paste(
        original, pasted_rows(kind), assessment_input_fields(original)
    )
    source = resize_job_source(source)
    local = source.tasks[-1]
    source = label_assessment_task(source, local.task_id, "Keep local", None)
    existing = (TaskDefinition("packing", "Packing"),)
    ids = frozenset(task.task_id for task in source.tasks[:-1])
    with patch("uuid.uuid4", side_effect=AssertionError("Uninjected identity")):
        linked, definitions = reusable_pasted_names(
            source, ids, existing, lambda: "new"
        )
    assert definitions == (TaskDefinition("new", "Corte Ñ"), *existing)
    assert [t.task_definition_id for t in linked.tasks] == [
        "packing",
        "new",
        "new",
        "new",
        None,
    ]
    assert linked.tasks[-1] == source.tasks[-1]
    for old, new in zip(source.tasks, linked.tasks, strict=True):
        assert replace(new, task_definition_id=old.task_definition_id) == old
    assert reusable_pasted_names(linked, ids, definitions, lambda: "unused") == (
        linked,
        definitions,
    )
    with pytest.raises(ValueError, match="no longer exist"):
        reusable_pasted_names(source, frozenset({"foreign"}), existing, lambda: "new")
    with pytest.raises(ValueError, match="already exists"):
        reusable_pasted_names(source, ids, existing, lambda: "packing")


@pytest.mark.parametrize("index", range(3))
def test_worker_paste_catalog_one_step_warning_and_reopen(
    window: LifftWindow, tmp_path: Path, index: int
) -> None:
    """Immediate dropdown reuse, one Undo with consent, exact Redo and Main Save.

    Args:
        window: Integrated native window with private settings/project.
        tmp_path: Test-owned file directory.
        index: Selected LiFFT/DUET/ST editor.

    Returns:
        None; existing definitions survive Undo; new IDs and results survive reopening.
    """
    reopen_grid(window, tmp_path, index, MeasurementSystem.METRIC, Language.ENGLISH)
    workspace = window.presenter.workspace
    known = (TaskDefinition("packing", "Packing"),)
    workspace.replace_task_definitions((), known)
    panel = window.secondary_panel() or window.task_panel
    original = window.active_source()
    kind = list(AssessmentKind)[index]
    service = window._assessment_editor_preferences
    service.save(
        ImportProfile(
            kind,
            header=False,
            fields=assessment_input_fields(original),
            configured=True,
        )
    )
    _APP.clipboard().setText("\n".join("\t".join(row) for row in pasted_rows(kind)))
    revision = workspace.editing.history.revision
    durable = Path(workspace.location).read_bytes()
    panel.task_grid.paste_cells_button.click()
    pasted = window.active_source()
    definitions = workspace.load_task_definitions()
    assert len(definitions) == 2 and workspace.editing.history.revision == revision + 1
    assert workspace.editing.history.undo_label_key == "assessment.paste"
    created = next(d for d in definitions if d.definition_id != "packing")
    assert created.name == "Corte Ñ"
    assert [t.task_definition_id for t in pasted.tasks[:4]] == [
        "packing",
        *([created.definition_id] * 3),
    ]
    choices = panel.task_grid.task_names[4]
    assert isinstance(choices, QComboBox)
    assert choices.findData(created.definition_id) >= 0
    assert Path(workspace.location).read_bytes() == durable
    panel.task_grid.selected_task_index = 0
    panel.task_grid.paste_cells_button.click()
    assert workspace.editing.history.revision == revision + 1
    assert workspace.load_task_definitions() == definitions
    window.setFocus()
    window.history_actions.refresh()
    history = window.history_actions.shared
    with patch.object(
        QMessageBox, "question", return_value=QMessageBox.Cancel
    ) as consent:
        history.replay(redo=False)
        assert consent.call_count == 1
    assert (
        window.active_source() == pasted
        and workspace.load_task_definitions() == definitions
    )
    with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes) as consent:
        history.replay(redo=False)
        assert consent.call_count == 1
        assert "paste" in consent.call_args.args[2].lower()
    assert (
        window.active_source() == original
        and workspace.load_task_definitions() == known
    )
    with patch.object(QMessageBox, "question") as consent:
        history.replay(redo=True)
        consent.assert_not_called()
    assert (
        window.active_source() == pasted
        and workspace.load_task_definitions() == definitions
    )
    assert workspace.save()
    with AssessmentProjectFile.open(Path(workspace.location)) as reopened:
        assert reopened.load_task_definitions() == definitions
        assert reopened.load(workspace.active.document) == pasted


@pytest.mark.parametrize("guided", (False, True))
@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_job_hosts_share_atomic_named_paste(
    tmp_path: Path, kind: AssessmentKind, guided: bool
) -> None:
    """Dedicated Jobs and guided JROT use the same catalog/input/calculation operation.

    Args:
        tmp_path: Private project and personal import preferences.
        kind: Every supported tool editor.
        guided: True uses the production guided JROT Job panel.

    Returns:
        None; one exact Undo/Redo covers catalog, source and calculated output.
    """
    planner = planning_dialog(tmp_path, Language.ENGLISH) if guided else None
    workspace = (
        planner.workspace if planner is not None else editing_workspace(tmp_path)
    )
    dialog = planner or JobManagementDialog(
        workspace, load_icons(), MeasurementSystem.METRIC
    )
    service = AssessmentEditorPreferences(
        JsonSettingsStore(tmp_path / "imports.json"), SpreadsheetValueReader()
    )
    service.bind(dialog)
    try:
        if planner is not None:
            planner.go(4)
            planner.job_panel.tabs.setCurrentIndex(list(AssessmentKind).index(kind))
            with patch.object(planner.job_panel, "confirm", return_value=True):
                planner.job_panel.mode_changed(1)
            editor = planner.job_panel.editors[kind]
        else:
            enter_job(dialog)
            dialog.tool_tabs.setCurrentIndex(list(AssessmentKind).index(kind))
            editor = dialog.editors[kind]
        enter_name(editor, 0, "Original local label")
        editor.task_actions.refresh_names()
        original = editor.source
        original_risk = workspace.read_job_risk().risk
        known = (TaskDefinition("packing", "Packing"),)
        workspace.replace_task_definitions((), known)
        revision = workspace.editing.history.revision
        service.save(
            ImportProfile(
                kind,
                header=False,
                fields=assessment_input_fields(original),
                configured=True,
            )
        )
        _APP.clipboard().setText("\n".join("\t".join(row) for row in pasted_rows(kind)))
        with patch.object(
            QMessageBox, "warning", return_value=QMessageBox.Ok
        ) as warning:
            editor.paste_cells_button.click()
        assert not warning.called, warning.call_args
        pasted = editor.source
        risk = workspace.read_job_risk().risk
        definitions = workspace.load_task_definitions()
        assert len(definitions) == 2
        assert workspace.editing.history.revision == revision + 1
        assert workspace.editing.history.undo_label_key == "assessment.paste"
        assert all(task.task_definition_id is not None for task in pasted.tasks)
        measurement = (
            next(m for m in planner.job_panel.values.measurements if m.kind is kind)
            if planner is not None
            else dialog._measurement(kind)
        )
        assert editor.result_rows == measurement.task_results
        assert all(outputs[-2].text() != "—" for outputs in editor.outputs)
        assert workspace.editing.replay(redo=False)
        assert workspace.load_task_definitions() == known
        assert (
            editor.source == original
            and workspace.read_job_risk().risk == original_risk
        )
        assert workspace.editing.replay(redo=True)
        assert workspace.load_task_definitions() == definitions
        assert editor.source == pasted and workspace.read_job_risk().risk == risk
        assert workspace.save()
        with AssessmentProjectFile.open(Path(workspace.location)) as reopened:
            assert reopened.load_task_definitions() == definitions
            assert reopened.load_job_risk() == risk
    finally:
        if planner is not None:
            dispose(planner)
        else:
            dialog.close()
            workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("failure", ("catalog", "source", "rejected"))
def test_failed_paste_rolls_back_catalog_source_and_redo(
    window: LifftWindow, tmp_path: Path, failure: str
) -> None:
    """Failures before/after source acceptance preserve existing data and Redo.

    Args:
        window: Integrated private worker editor with real automatic calculation.
        tmp_path: Private native project and preferences.
        failure: Catalog write failure, post-source exception or explicit rejection.

    Returns:
        None; no stray catalog definition, dirty revision or partially updated grid.
    """
    reopen_grid(window, tmp_path, 0, MeasurementSystem.METRIC, Language.ENGLISH)
    workspace = window.presenter.workspace
    actions = window.task_panel.task_actions
    enter_name(window.task_panel.task_grid, 0, "Redo must survive")
    assert workspace.editing.replay(redo=False)
    original = window.active_source()
    replacement = prepare_assessment_paste(
        original, pasted_rows(AssessmentKind.LIFFT), assessment_input_fields(original)
    )
    ids = frozenset(task.task_id for task in replacement.tasks[:4])
    before = workspace.editing.history.state
    revision = workspace.editing.history.revision
    redo = workspace.editing.history.redo_label_key
    durable = Path(workspace.location).read_bytes()

    def failing_accept(
        expected: AssessmentDraft, proposed: AssessmentDraft, label: str, rebuild: bool
    ) -> bool:
        """Fail after the real host has accepted inputs and automatic results.

        Args:
            expected: Exact current worker source.
            proposed: Prepared source with registered definition references.
            label: Shared paste action identity.
            rebuild: Shared grid reconstruction choice.

        Returns:
            False for an explicit rejected acceptance.

        Raises:
            OSError: Simulated failure after a successful source replacement.
        """
        assert actions.accept_source(expected, proposed, label, rebuild)
        workspace.stage_assessments()
        if failure == "source":
            raise OSError("source write failed")
        return False

    if failure == "catalog":
        with (
            patch.object(
                AssessmentProjectFile,
                "replace_task_definitions",
                side_effect=OSError("catalog write failed"),
            ),
            pytest.raises(OSError, match="catalog write"),
        ):
            workspace.accept_task_paste(original, replacement, ids, failing_accept)
    else:
        with pytest.raises((OSError, ValueError)):
            workspace.accept_task_paste(original, replacement, ids, failing_accept)
    assert workspace.load_task_definitions() == ()
    assert workspace.active.state == original
    assert window.task_panel.task_grid.source == original
    assert workspace.editing.history.state == before
    assert workspace.editing.history.revision == revision
    assert workspace.editing.history.redo_label_key == redo
    assert Path(workspace.location).read_bytes() == durable
    assert workspace.editing.replay(redo=True)
    assert workspace.active.state.tasks[0].task_name == "Redo must survive"


def test_unmapped_names_stay_local_and_paste_undo_still_warns(
    window: LifftWindow, tmp_path: Path
) -> None:
    """Numeric-only paste never registers unrelated names; Undo warns without new IDs.

    Args:
        window: Integrated private worker editor.
        tmp_path: Private file/preferences directory.

    Returns:
        None; mapped names register only inside the destination rectangle later.
    """
    reopen_grid(window, tmp_path, 0, MeasurementSystem.METRIC, Language.SPANISH)
    workspace = window.presenter.workspace
    actions = window.task_panel.task_actions
    enter_name(window.task_panel.task_grid, 0, "Local only")
    enter_name(window.task_panel.task_grid, 10, "Outside paste")
    actions.refresh_names()
    original = workspace.active.state
    service = window._assessment_editor_preferences
    service.save(
        ImportProfile(
            AssessmentKind.LIFFT, header=False, fields=("repetitions",), configured=True
        )
    )
    _APP.clipboard().setText("321")
    window.task_panel.task_grid.selected_task_index = 0
    window.task_panel.task_grid.paste_cells_button.click()
    assert workspace.load_task_definitions() == ()
    assert workspace.active.state.tasks[0].task_name == "Local only"
    window.setFocus()
    window.history_actions.refresh()
    with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes) as consent:
        window.history_actions.shared.replay(redo=False)
        assert consent.call_count == 1 and "pegado" in consent.call_args.args[2]
    assert workspace.active.state == original
    service.save(
        ImportProfile(
            AssessmentKind.LIFFT, header=False, fields=("task_name",), configured=True
        )
    )
    _APP.clipboard().setText("New mapped name")
    window.task_panel.task_grid.paste_cells_button.click()
    assert [d.name for d in workspace.load_task_definitions()] == ["New mapped name"]
    assert workspace.active.state.tasks[10].task_name == "Outside paste"
    assert workspace.active.state.tasks[10].task_definition_id is None


def test_job_persistence_failure_leaves_no_reusable_names(tmp_path: Path) -> None:
    """A real Job-host write failure cannot accept a catalog-only half-paste.

    Args:
        tmp_path: Private Job project/preferences.

    Returns:
        None; the shared rollback reloads prior source, values, catalog and revision.
    """
    workspace = editing_workspace(tmp_path)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:
        enter_job(dialog)
        editor = dialog.editors[AssessmentKind.LIFFT]
        enter_name(editor, 0, "Before")
        editor.task_actions.refresh_names()
        original = editor.source
        before = workspace.editing.history.state
        service = AssessmentEditorPreferences(
            JsonSettingsStore(tmp_path / "imports.json"), SpreadsheetValueReader()
        )
        service.bind(dialog)
        service.save(
            ImportProfile(
                AssessmentKind.LIFFT,
                header=False,
                fields=assessment_input_fields(original),
                configured=True,
            )
        )
        _APP.clipboard().setText(
            "\n".join("\t".join(row) for row in pasted_rows(AssessmentKind.LIFFT))
        )
        with (
            patch.object(
                workspace, "save_job_details", side_effect=OSError("disk error")
            ),
            patch.object(
                QMessageBox, "warning", return_value=QMessageBox.Ok
            ) as warning,
        ):
            editor.paste_cells_button.click()
        assert warning.called
        assert workspace.load_task_definitions() == () and editor.source == original
        assert workspace.editing.history.state == before
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("language", list(Language))
def test_import_cancel_and_skipped_rows_do_not_register_names(
    window: LifftWindow, tmp_path: Path, language: Language
) -> None:
    """The accepted import mapping registers only included names; Cancel is inert.

    Args:
        window: Integrated private worker editor.
        tmp_path: Test-owned project/settings directory.
        language: Both import presentation languages.

    Returns:
        None; preview staging does not create definitions or write source inputs.
    """
    reopen_grid(window, tmp_path, 0, MeasurementSystem.METRIC, language)
    workspace = window.presenter.workspace
    original = window.active_source()
    before = workspace.editing.history.state
    _APP.clipboard().setText(
        "Task name\tLever arm\tLoad\tRepetitions\n"
        "Selected Ñ\t30\t49.05\t100\n"
        "Skipped name\t30\t49.05\t200\n"
        "Other picked\t30\t49.05\t300"
    )
    actions = window.task_panel.task_actions
    with patch.object(AssessmentPasteDialog, "exec", return_value=QDialog.Rejected):
        actions.paste(configure=True)
    assert workspace.load_task_definitions() == ()
    assert (
        workspace.active.state == original and workspace.editing.history.state == before
    )

    def accept_preview(preview: AssessmentPasteDialog) -> int:
        """Exclude the middle source row before actual modal acceptance.

        Args:
            preview: Owned real shared import dialog.

        Returns:
            Its native Accepted result after successful preparation.
        """
        assert workspace.load_task_definitions() == ()
        preview.panel.toggle_row(2)
        preview.prepare()
        assert preview.result() == QDialog.Accepted
        assert workspace.load_task_definitions() == ()
        return preview.result()

    with patch.object(AssessmentPasteDialog, "exec", accept_preview):
        actions.paste(configure=True)
    assert {d.name for d in workspace.load_task_definitions()} == {
        "Selected Ñ",
        "Other picked",
    }
    assert [t.task_name for t in workspace.active.state.tasks[:2]] == [
        "Selected Ñ",
        "Other picked",
    ]
    assert workspace.editing.history.undo_label_key == "assessment.paste"
    assert workspace.editing.replay(redo=False)
    assert (
        workspace.load_task_definitions() == () and workspace.active.state == original
    )


def test_explicit_duplicate_identity_is_not_merged_by_paste() -> None:
    """Existing equal-name definitions remain distinct when a row is explicitly linked.

    Args:
        None.

    Returns:
        None; unlinked matching names choose a stable existing ID without creation.
    """
    source = blank_job_source(AssessmentKind.LIFFT, MeasurementSystem.METRIC)
    source = resize_job_source(source)
    source = label_assessment_task(source, source.tasks[0].task_id, "Packing", "b")
    source = label_assessment_task(source, source.tasks[1].task_id, "packing", None)
    definitions = (TaskDefinition("a", "Packing"), TaskDefinition("b", "Packing"))
    linked, catalog = reusable_pasted_names(
        source,
        frozenset(t.task_id for t in source.tasks),
        definitions,
        lambda: "unused",
    )
    assert catalog == definitions
    assert [t.task_definition_id for t in linked.tasks] == ["b", "a"]
    invalid = label_assessment_task(
        source, source.tasks[0].task_id, "Packing", "missing"
    )
    with pytest.raises(ValueError, match="unknown reusable"):
        reusable_pasted_names(
            invalid, frozenset({source.tasks[0].task_id}), definitions, lambda: "unused"
        )


@pytest.mark.parametrize("pending_name", (False, True))
def test_catalog_choices_follow_other_open_editor_without_losing_typing(
    window: LifftWindow, tmp_path: Path, pending_name: bool
) -> None:
    """A Job paste updates the worker choices, deferring safely around unfinished names.

    Args:
        window: Private Main window remaining open behind Job Management.
        tmp_path: Disposable project and settings.
        pending_name: Leave one worker name field unfinished during the Job paste.

    Returns:
        None; shared Undo/Redo updates both open grids without accepting unrelated text.
    """
    reopen_grid(window, tmp_path, 0, MeasurementSystem.METRIC, Language.ENGLISH)
    workspace = window.presenter.workspace
    grid = window.task_panel.task_grid
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    window._assessment_editor_preferences.bind(dialog)
    try:
        enter_job(dialog)
        editor = dialog.editors[AssessmentKind.LIFFT]
        if pending_name:
            control = grid.task_names[5]
            control.setEditText("Unfinished local name")
            control.lineEdit().textEdited.emit("Unfinished local name")
        service = window._assessment_editor_preferences
        service.save(
            ImportProfile(
                AssessmentKind.LIFFT,
                header=False,
                fields=assessment_input_fields(editor.source),
                configured=True,
            )
        )
        _APP.clipboard().setText("New shared name\t30\t49.05\t100")
        editor.paste_cells_button.click()
        definition = workspace.load_task_definitions()[0]
        if pending_name:
            assert grid.task_names[5].currentText() == "Unfinished local name"
            assert workspace.active.state.tasks[5].task_name is None
            grid.task_names[5].lineEdit().editingFinished.emit()
            assert workspace.active.state.tasks[5].task_name == "Unfinished local name"
        assert grid.task_names[6].findData(definition.definition_id) >= 0
        assert grid.task_names[6].currentText() == ""
        if pending_name:
            assert workspace.editing.replay(redo=False)
        assert workspace.editing.replay(redo=False)
        assert workspace.load_task_definitions() == ()
        assert grid.task_names[6].findData(definition.definition_id) < 0
        assert workspace.editing.replay(redo=True)
        assert grid.task_names[6].findData(definition.definition_id) >= 0
    finally:
        dialog.close()
        dialog.deleteLater()
        _APP.processEvents()


def test_catalog_listener_ignores_editor_destroyed_during_notification(
    tmp_path: Path,
) -> None:
    """A prior notification may close a grid before its queued weak callback runs.

    Args:
        tmp_path: Private empty project for the shared notification owner.

    Returns:
        None; destroyed widgets are never read, and the catalog listener detaches.
    """
    from PyQt5 import sip
    from PyQt5.QtCore import QCoreApplication, QEvent

    from ergotools.domain.decimal_convention import DecimalConvention
    from ergotools.presentation.desktop.assessment_task_actions import (
        AssessmentTaskActions,
    )

    workspace = editing_workspace(tmp_path)
    grid = AssessmentTaskGrid(
        Language.ENGLISH, DecimalConvention.POINT, icons=load_icons()
    )
    source = blank_job_source(AssessmentKind.LIFFT, MeasurementSystem.METRIC)
    grid.load_source(source)

    def close_grid() -> None:
        """Close the grid before later callbacks from the same listener snapshot.

        Args:
            None.

        Returns:
            None after actual Qt DeferredDelete processing.
        """
        grid.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    detach = workspace.editing.subscribe(close_grid)
    actions = AssessmentTaskActions(
        grid,
        source=lambda: source,
        accept=lambda expected, replacement, label, rebuild: False,
        accept_paste=workspace.accept_task_paste,
        definitions=workspace.load_task_definitions,
        replace_definitions=workspace.replace_task_definitions,
        before_action=lambda: True,
        system=lambda: MeasurementSystem.METRIC,
        convention=lambda: DecimalConvention.POINT,
    )
    actions.bind_catalog(workspace.editing)
    try:
        workspace.editing.notify()
        assert sip.isdeleted(grid) and not actions._catalog_cleanup
    finally:
        detach()
        workspace.close(choice=CloseChoice.DISCARD)

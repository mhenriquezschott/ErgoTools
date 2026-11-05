"""Shared staging/paste UI, source failures, persistent mappings and host history.

Native Qt tests operate only private workbooks/projects/preferences. Stage-only actions
must not edit assessments; successful import is one existing shared history operation.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from openpyxl import Workbook
from PyQt5.QtCore import QCoreApplication, QEvent, Qt
from PyQt5.QtWidgets import QApplication, QDialog, QTableWidgetSelectionRange

from ergotools.application.assessment_clipboard import assessment_input_fields
from ergotools.application.assessment_import import ImportProfile
from ergotools.application.job_calculation import blank_job_source
from ergotools.application.settings import UserSettings
from ergotools.bootstrap import create_window, load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.settings_store import JsonSettingsStore
from ergotools.infrastructure.tabular_file_reader import SpreadsheetValueReader
from ergotools.presentation.desktop.assessment_editor_preferences import (
    AssessmentEditorPreferences,
)
from ergotools.presentation.desktop.assessment_paste_dialog import AssessmentPasteDialog
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.preferences_dialog import PreferencesDialog
from tests.test_jrot_planning_ui import dispose, planning_dialog
from tests.test_saved_tool_data import window as window
from tests.test_task_names_ui import reopen_grid

# Retain native application lifetime across modal, timer and clipboard probes.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("kind", list(AssessmentKind))
@pytest.mark.parametrize("language", list(Language))
def test_staging_selection_edit_errors_and_cancel_are_independent(
    kind: AssessmentKind, language: Language
) -> None:
    """All tools share staged cells, correctable diagnostics and original identity.

    Args:
        kind: Each numeric/selector schema.
        language: English/Spanish presentation.

    Returns:
        None; no valid/invalid staging action mutates the captured source.
    """
    source = blank_job_source(kind, MeasurementSystem.METRIC)
    fields = assessment_input_fields(source)
    values = (
        ("Inspección Ñ", "4", "100")
        if kind is AssessmentKind.DUET
        else (
            ("Inspección Ñ", "Handling Load", "30", "49.05", "100")
            if kind is AssessmentKind.TST
            else ("Inspección Ñ", "30", "49.05", "100")
        )
    )
    data = "\t".join(values) + "\n" + "\t".join(values)
    profile = ImportProfile(kind, header=False, fields=fields, configured=True)
    dialog = AssessmentPasteDialog(
        source,
        data,
        language,
        DecimalConvention.POINT,
        MeasurementSystem.METRIC,
        0,
        profile=profile,
    )
    try:
        dialog.panel.prepare(accept=False)
        assert dialog.result() != QDialog.Accepted and dialog.replacement is not None
        assert source.tasks[0].repetitions is None
        last = len(fields) - 1
        dialog.table.item(2, last).setText("-10")
        dialog.panel.prepare(accept=False)
        assert dialog.replacement is None and dialog.error.text()
        assert dialog.table.item(2, last).background().color().name() == "#fde5e3"
        dialog.table.item(2, last).setText("200")
        dialog.panel.prepare(accept=False)
        assert dialog.replacement.tasks[1].repetitions == 200
        assert dialog.table.item(2, last).background().style() == Qt.BrushStyle.NoBrush
        dialog.table.clearSelection()
        dialog.table.setRangeSelected(QTableWidgetSelectionRange(2, 0, 2, last), True)
        dialog.panel.use_selection()
        dialog.prepare()
        assert dialog.result() == QDialog.Accepted
        assert (
            len(dialog.replacement.tasks) == 1
            and dialog.replacement.tasks[0].repetitions == 200
        )
        assert source.tasks[0].repetitions is None
    finally:
        dialog.reject()
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_file_sheet_range_and_failed_reload_cannot_apply_stale_preview(
    tmp_path: Path,
) -> None:
    """Worksheet switches and precise range reads are real; failed loads block Apply.

    Args:
        tmp_path: Private multi-sheet workbook and malformed file.

    Returns:
        None; source files and original destination remain unchanged.
    """
    path = tmp_path / "multi.xlsx"
    book = Workbook()
    book.active.title = "Notes"
    book.active["A1"] = "Do not import"
    page = book.create_sheet("Tareas Ñ")
    for col, value in zip(
        "BCDE", ("Task name", "Lever arm (cm)", "Load (N)", "Repetitions"), strict=True
    ):
        page[f"{col}4"] = value
    for col, value in zip("BCDE", ("Inspección", 30, 49.05, 100), strict=True):
        page[f"{col}5"] = value
    book.save(path)
    book.close()
    original = path.read_bytes()
    source = blank_job_source(AssessmentKind.LIFFT, MeasurementSystem.METRIC)
    dialog = AssessmentPasteDialog(
        source,
        "",
        Language.ENGLISH,
        DecimalConvention.POINT,
        MeasurementSystem.METRIC,
        0,
        file_reader=SpreadsheetValueReader(),
    )
    try:
        dialog.panel._path = str(path)
        dialog.panel.reload_file(True)
        assert dialog.panel.sheet.count() == 2
        dialog.panel.sheet.setCurrentText("Tareas Ñ")
        dialog.panel.sheet.activated.emit(1)
        assert dialog.panel.sheet.currentText() == "Tareas Ñ"
        dialog.panel.range_edit.setText("B4:E5")
        dialog.panel.load_range()
        dialog.panel.prepare(accept=False)
        assert dialog.replacement.tasks[0].task_name == "Inspección"
        assert path.read_bytes() == original
        dialog.panel.range_edit.setText("ZZ999:ZZ999")
        dialog.panel.load_range()
        dialog.prepare()
        assert dialog.result() != QDialog.Accepted and dialog.replacement is None
        dialog.panel.range_edit.setText("B4:E5")
        dialog.panel.load_range()
        dialog.prepare()
        assert dialog.result() == QDialog.Accepted
    finally:
        dialog.reject()
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        _APP.processEvents()


@pytest.mark.parametrize("language", list(Language))
def test_embedded_settings_share_panel_and_cancel_or_save_only_profiles(
    tmp_path: Path, language: Language
) -> None:
    """Settings embeds shared controls with independent tool drafts and no data writes.

    Args:
        tmp_path: Private personal settings path.
        language: Current interface language.

    Returns:
        None; Cancel leaves settings absent; accepted profiles omit source data.
    """
    owner = create_window(tmp_path / "settings.json", original_navigation=True)
    try:
        dialog = PreferencesDialog(
            language,
            MeasurementSystem.METRIC,
            load_icons(),
            parent=owner,
            import_reader=SpreadsheetValueReader(),
        )
        assert dialog.import_settings.profiles() == ()
        panel = dialog.import_settings._panels[AssessmentKind.LIFFT]
        panel.separator.setCurrentIndex(panel.separator.findData(";"))
        profiles = dialog.import_settings.profiles()
        assert len(profiles) == 1 and profiles[0].delimiter == ";"
        dialog.import_settings.tools.setCurrentIndex(1)
        duet = dialog.import_settings._panels[AssessmentKind.DUET]
        duet.encoding.setCurrentIndex(duet.encoding.findData("cp1252"))
        assert len(dialog.import_settings.profiles()) == 2
        dialog.reject()
        dialog.deleteLater()
        assert not (tmp_path / "settings.json").exists()
        store = JsonSettingsStore(tmp_path / "saved.json")
        store.save(replace(UserSettings(), import_profiles=profiles))
        assert store.load().import_profiles == profiles
    finally:
        owner.close()
        owner.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        _APP.processEvents()


@pytest.mark.parametrize("index", [0, 1, 2])
def test_main_paste_then_saved_fast_paste_share_one_step_and_restore_exact_inputs(
    window: LifftWindow, tmp_path: Path, index: int
) -> None:
    """Worker inputs use first-use review, then remembered fast paste and shared Undo.

    Args:
        window: Native private assessment fixture supplied by pytest.
        tmp_path: Private copied project/preference directory.
        index: LiFFT/DUET/ST main tool tab.

    Returns:
        None; two complete pastes undo separately and preserve existing source IDs.
    """
    reopen_grid(window, tmp_path, index, MeasurementSystem.METRIC, Language.ENGLISH)
    panel = window.secondary_panel() or window.task_panel
    source = window.active_source()
    kind = list(AssessmentKind)[index]
    values = (
        ("Inspección Ñ", "4", "100")
        if index == 1
        else (
            ("Inspección Ñ", "Handling Load", "30", "49.05", "100")
            if index == 2
            else ("Inspección Ñ", "30", "49.05", "100")
        )
    )
    profile = ImportProfile(
        kind, header=False, fields=assessment_input_fields(source), configured=True
    )
    window._assessment_editor_preferences.save(profile)
    _APP.clipboard().setText("\t".join(values))
    grid = panel.task_grid
    grid.selected_task_index = 0
    with patch.object(
        AssessmentPasteDialog,
        "exec",
        side_effect=AssertionError("configured paste reopened"),
    ):
        grid.paste_cells_button.click()
    first = window.active_source()
    assert (
        first.tasks[0].repetitions == 100 and first.tasks[0].task_name == "Inspección Ñ"
    )
    values = (*values[:-1], "200")
    _APP.clipboard().setText("\t".join(values))
    grid.paste_cells_button.click()
    second = window.active_source()
    assert second.tasks[0].repetitions == 200
    assert window.presenter.workspace.editing.replay(redo=False)
    assert window.active_source() == first
    assert window.presenter.workspace.editing.replay(redo=False)
    assert window.active_source() == source
    assert window.presenter.workspace.editing.replay(redo=True)
    assert window.active_source() == first


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_guided_job_import_uses_same_service_and_history(
    tmp_path: Path, kind: AssessmentKind
) -> None:
    """The guided Job calculator uses the shared paste service, not a second parser.

    Args:
        tmp_path: Private planning project and personal preferences.
        kind: Every tool's reusable editor.

    Returns:
        None; accepted copied inputs revert through the shared project history.
    """
    dialog = planning_dialog(tmp_path, Language.ENGLISH)
    service = AssessmentEditorPreferences(
        JsonSettingsStore(tmp_path / "import.json"), SpreadsheetValueReader()
    )
    service.bind(dialog)
    try:
        dialog.go(4)
        dialog.job_panel.tabs.setCurrentIndex(list(AssessmentKind).index(kind))
        with patch.object(dialog.job_panel, "confirm", return_value=True):
            dialog.job_panel.mode_changed(1)
        editor = dialog.job_panel.editors[kind]
        assert editor.editor_preferences is service
        original = editor.source
        fields = assessment_input_fields(original)
        values = (
            ("Copied job", "4", "100")
            if kind is AssessmentKind.DUET
            else (
                ("Copied job", "Handling Load", "30", "49.05", "100")
                if kind is AssessmentKind.TST
                else ("Copied job", "30", "49.05", "100")
            )
        )
        service.save(ImportProfile(kind, header=False, fields=fields, configured=True))
        _APP.clipboard().setText("\t".join(values))
        editor.paste_cells_button.click()
        assert editor.source.tasks[0].task_name == "Copied job"
        assert dialog.owner.replay(redo=False)
        dialog.reload()
        assert dialog.job_panel.editors[kind].source == original
    finally:
        dispose(dialog)


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_dedicated_job_window_paste_uses_same_service_and_undo(
    tmp_path: Path, kind: AssessmentKind
) -> None:
    """Dedicated Jobs share staging/preferences and exactly one accepted batch edit.

    Args:
        tmp_path: Private project and settings files.
        kind: LiFFT/DUET/ST dedicated Job tool tab.

    Returns:
        None; Undo restores the prior named source and source-bound calculation state.
    """
    from ergotools.application.document_lifecycle import CloseChoice
    from ergotools.presentation.desktop.job_management_dialog import JobManagementDialog
    from tests.test_job_calculators import enter_job
    from tests.test_unified_project_save import editing_workspace

    workspace = editing_workspace(tmp_path)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    service = AssessmentEditorPreferences(
        JsonSettingsStore(tmp_path / "imports.json"), SpreadsheetValueReader()
    )
    service.bind(dialog)
    try:
        enter_job(dialog)
        dialog.tool_tabs.setCurrentIndex(list(AssessmentKind).index(kind))
        editor = dialog.editors[kind]
        control = editor.task_names[0]
        control.setEditText("Existing source")
        control.lineEdit().editingFinished.emit()
        original = editor.source
        assert original is not None and editor.editor_preferences is service
        fields = assessment_input_fields(original)
        values = (
            ("Imported job", "4", "100")
            if kind is AssessmentKind.DUET
            else (
                ("Imported job", "Handling Load", "30", "49.05", "100")
                if kind is AssessmentKind.TST
                else ("Imported job", "30", "49.05", "100")
            )
        )
        service.save(ImportProfile(kind, header=False, fields=fields, configured=True))
        _APP.clipboard().setText("\t".join(values))
        editor.paste_cells_button.click()
        assert dialog._measurement(kind).complete
        assert editor.source.tasks[0].task_name == "Imported job"
        assert workspace.editing.replay(redo=False)
        assert editor.source == original
    finally:
        dialog.close()
        dialog.deleteLater()
        workspace.close(choice=CloseChoice.DISCARD)
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_settings_reopen_retains_custom_column_shape_and_skips_project_acceptance(
    window: LifftWindow,
) -> None:
    """Custom source-column profiles reopen correctly and personal Apply retains typing.

    Args:
        window: Native private worker/project fixture.

    Returns:
        None; a personal mapping change neither parses pending text nor dirties project.
    """
    profile = ImportProfile(
        AssessmentKind.LIFFT,
        fields=("load", None, "repetitions"),
        configured=True,
        header=False,
    )
    window._assessment_editor_preferences.save(profile)
    failures: list[BaseException] = []
    before = window.presenter.workspace.active.state
    dirty = window.presenter.workspace.has_unsaved_changes
    field = window.task_panel.inputs[0][2]
    field.setText("unfinished")
    field.textEdited.emit("unfinished")

    def choose() -> None:
        """Modify only personal import parsing through the actual owned Settings modal.

        Args:
            None.

        Returns:
            None; capture callback failures outside Qt's event boundary.
        """
        modal = QApplication.activeModalWidget()
        try:
            assert isinstance(modal, PreferencesDialog)
            panel = modal.import_settings._panels[AssessmentKind.LIFFT]
            assert panel.profile().fields == profile.fields
            assert len(panel.rows) == 1 and not any(panel.rows[0])
            panel.separator.setCurrentIndex(panel.separator.findData(";"))
            modal.accept()
        except BaseException as error:
            failures.append(error)
            if isinstance(modal, PreferencesDialog):
                modal.reject()

    from PyQt5.QtCore import QTimer

    with patch.object(
        window,
        "resolve_context_text",
        side_effect=AssertionError("personal import parsed project"),
    ):
        QTimer.singleShot(0, choose)
        window.open_preferences()
    assert not failures
    assert window.presenter.workspace.active.state == before
    assert window.presenter.workspace.has_unsaved_changes == dirty
    assert field.text() == "unfinished"
    saved = window._settings_store.load().import_profiles[0]
    assert saved.fields == profile.fields and saved.delimiter == ";"


def test_changed_source_or_format_must_be_previewed_before_apply() -> None:
    """Editing raw text or its separator cannot apply the previous parsed snapshot.

    Args:
        None.

    Returns:
        None; Apply remains rejected until explicit preview update resolves the source.
    """
    source = blank_job_source(AssessmentKind.LIFFT, MeasurementSystem.METRIC)
    dialog = AssessmentPasteDialog(
        source,
        "30;49.05;100",
        Language.SPANISH,
        DecimalConvention.POINT,
        MeasurementSystem.METRIC,
        0,
        start_field="lever_arm",
    )
    try:
        dialog.panel.prepare(accept=False)
        assert dialog.replacement is not None
        dialog.panel.source_text.setPlainText("45;98.1;200")
        dialog.prepare()
        assert dialog.result() != QDialog.Accepted and dialog.replacement is None
        dialog.panel.update_source()
        dialog.panel.prepare(accept=False)
        assert dialog.replacement.tasks[0].lever_arm == 45
        dialog.panel.separator.setCurrentIndex(dialog.panel.separator.findData("|"))
        dialog.prepare()
        assert dialog.result() != QDialog.Accepted and dialog.replacement is None
        dialog.panel.separator.setCurrentIndex(dialog.panel.separator.findData(";"))
        dialog.panel.update_source()
        dialog.prepare()
        assert dialog.result() == QDialog.Accepted
    finally:
        dialog.reject()
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_duplicate_mapping_is_correctable_and_does_not_block_new_sources(
    tmp_path: Path,
) -> None:
    """An invalid map remains correctable while a replacement source can be loaded.

    Args:
        tmp_path: Generated private text source.

    Returns:
        None; mapping errors never escape the native callback or apply data.
    """
    source = blank_job_source(AssessmentKind.LIFFT, MeasurementSystem.METRIC)
    dialog = AssessmentPasteDialog(
        source,
        "30;49;100",
        Language.ENGLISH,
        DecimalConvention.POINT,
        MeasurementSystem.METRIC,
        0,
        start_field="lever_arm",
        file_reader=SpreadsheetValueReader(),
    )
    try:
        dialog.panel.mappings[1].setCurrentIndex(
            dialog.panel.mappings[1].findData("lever_arm")
        )
        dialog.prepare()
        assert dialog.result() != QDialog.Accepted and dialog.error.text()
        path = tmp_path / "new.csv"
        path.write_text("Task name;Lever arm (cm);Load (N);Repetitions\nNew;30;49;100")
        dialog.panel._path = str(path)
        dialog.panel.reload_file(True)
        dialog.prepare()
        assert dialog.result() == QDialog.Accepted
        assert dialog.replacement.tasks[0].task_name == "New"
    finally:
        dialog.reject()
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_finished_preview_stops_validation_without_losing_accepted_values() -> None:
    """Closing a staging dialog retires queued work but retains its accepted result.

    Args:
        None.

    Returns:
        None; deferred validation cannot replace a committed immutable preview.
    """
    dialog = AssessmentPasteDialog(
        blank_job_source(AssessmentKind.DUET, MeasurementSystem.METRIC),
        "Task name\tOMNI-RES\tRepetitions\nPacking\t4\t100",
        Language.ENGLISH,
        DecimalConvention.POINT,
        MeasurementSystem.METRIC,
        0,
    )
    try:
        dialog.prepare()
        result = dialog.replacement
        assert result is not None and dialog.result() == QDialog.Accepted
        assert not dialog.panel.validation_timer.isActive()
        dialog.panel.queue_validation()
        _APP.processEvents()
        assert dialog.replacement is result
        assert not dialog.panel.validation_timer.isActive()
    finally:
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        _APP.processEvents()


@pytest.mark.parametrize("extension", ["xlsx", "xlsm"])
@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_sparse_calculator_workbook_imports_only_mapped_inputs(
    tmp_path: Path, extension: str, kind: AssessmentKind
) -> None:
    """Merged-sheet spacing compacts explicitly while derived columns stay ignored.

    Args:
        tmp_path: Private workbook directory.
        extension: Ordinary or macro-enabled package suffix; no code is executed.
        kind: Every supported calculator input schema.

    Returns:
        None; 35 logical tasks survive file/clipboard staging without formula values.
    """
    path = tmp_path / f"calculator.{extension}"
    book = Workbook()
    sheet = book.active
    sheet.title = "Inputs"
    fields = assessment_input_fields(blank_job_source(kind, MeasurementSystem.IMPERIAL))
    labels = {
        "task_name": "Task name",
        "lever_arm": "Lever arm (inch)",
        "load": "Load (lbs)",
        "direction": "Type of Task",
        "omni_res_scale": "OMNI-Res Scale",
        "repetitions": "Repetitions (per work day)",
    }
    values = {
        "task_name": "Packing Ñ",
        "lever_arm": "14",
        "load": "3.3",
        "direction": "Handling Load",
        "omni_res_scale": "2: Easy",
        "repetitions": "52",
    }
    for column, field in enumerate(fields, 1):
        sheet.cell(1, column, labels[field])
    sheet.cell(1, len(fields) + 1, "Damage (calculated)")
    for index in range(35):
        row = index * 3 + 2
        for column, field in enumerate(fields, 1):
            token = values[field]
            if kind is AssessmentKind.TST and index == 1 and field != "task_name":
                token = "Please select ..." if field == "direction" else ""
            sheet.cell(row, column, token)
            sheet.merge_cells(
                start_row=row, end_row=row + 2, start_column=column, end_column=column
            )
        sheet.cell(row, len(fields) + 1, "=999999")
    book.create_sheet("Instructions")
    book.save(path)
    book.close()
    original = path.read_bytes()
    source = blank_job_source(kind, MeasurementSystem.IMPERIAL)
    dialog = AssessmentPasteDialog(
        source,
        "",
        Language.ENGLISH,
        DecimalConvention.POINT,
        MeasurementSystem.IMPERIAL,
        0,
        file_reader=SpreadsheetValueReader(),
    )
    try:
        panel = dialog.panel
        panel._path = str(path)
        panel.range_edit.setText(f"A1:{chr(65 + len(fields))}106")
        panel.reload_file()
        assert panel.sheet.count() == 2 and not panel._source_error
        assert panel.mappings[-1].currentData() is None
        panel.exclude_empty_rows()
        panel.prepare(accept=False)
        assert panel.replacement is not None, panel.error.text()
        assert len(panel.replacement.tasks) == 35
        assert all(t.repetitions in (None, 52) for t in panel.replacement.tasks)
        assert panel.replacement.tasks[0].repetitions == 52
        assert all(t.task_name == "Packing Ñ" for t in panel.replacement.tasks)
        assert source.tasks[0].repetitions is None
        assert path.read_bytes() == original
    finally:
        dialog.close()
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        _APP.processEvents()


@pytest.mark.parametrize("kind", list(AssessmentKind))
@pytest.mark.parametrize("language", list(Language))
def test_background_validation_keeps_file_preview_position(
    tmp_path: Path, kind: AssessmentKind, language: Language
) -> None:
    """Keep row-review position during diagnostics; locate explicit errors.

    Args:
        tmp_path: Private long TSV file; its bytes must remain unchanged.
        kind: Each shared assessment input schema.
        language: Both native presentation languages.

    Returns:
        None; real checkbox clicks and bulk actions do not interrupt source review.
        Manual Validate still reveals the invalid first row without applying inputs.
    """
    from PyQt5.QtCore import QPoint
    from PyQt5.QtTest import QTest

    source = blank_job_source(kind, MeasurementSystem.METRIC)
    values = (
        ("Imported task", "4", "100")
        if kind is AssessmentKind.DUET
        else (
            ("Imported task", "Handling Load", "30", "49.05", "100")
            if kind is AssessmentKind.TST
            else ("Imported task", "30", "49.05", "100")
        )
    )
    # Ignored trailing columns require horizontal scrolling as in wide workbooks.
    fields = (*assessment_input_fields(source), *((None,) * 6))
    rows = [(*values[:-1], "invalid repetitions", *(("note",) * 6))]
    rows.extend((*values, *(("note",) * 6)) for _ in range(79))
    path = tmp_path / "long_source.tsv"
    path.write_text("\n".join("\t".join(row) for row in rows), encoding="utf-8")
    original = path.read_bytes()
    dialog = AssessmentPasteDialog(
        source,
        "",
        language,
        DecimalConvention.POINT,
        MeasurementSystem.METRIC,
        0,
        profile=ImportProfile(kind, header=False, fields=fields, configured=True),
        file_reader=SpreadsheetValueReader(),
    )
    try:
        panel = dialog.panel
        panel._path = str(path)
        panel.reload_file(True)
        dialog.show()
        QTest.qWait(350)
        assert panel.replacement is None and panel._invalid_cells
        table = panel.table
        table.setCurrentCell(65, 2)
        table.setRangeSelected(QTableWidgetSelectionRange(65, 2, 67, 3), True)
        table.scrollToItem(table.item(65, 2))
        vertical, horizontal = table.verticalScrollBar(), table.horizontalScrollBar()
        assert vertical is not None and horizontal is not None
        horizontal.setValue(horizontal.maximum())
        position = vertical.value(), horizontal.value()
        assert min(position) > 0
        selected = {(index.row(), index.column()) for index in table.selectedIndexes()}
        current = table.currentRow(), table.currentColumn()
        header = table.verticalHeader()
        assert header is not None
        for _ in range(2):
            QTest.mouseClick(
                header.viewport(),
                Qt.MouseButton.LeftButton,
                pos=QPoint(
                    14,
                    header.sectionViewportPosition(65) + header.sectionSize(65) // 2,
                ),
            )
            QTest.qWait(350)
            assert not panel.validation_timer.isActive()
            assert (vertical.value(), horizontal.value()) == position
            assert {(i.row(), i.column()) for i in table.selectedIndexes()} == selected
            assert (table.currentRow(), table.currentColumn()) == current
        panel.set_selected_rows(False)
        QTest.qWait(350)
        assert (vertical.value(), horizontal.value()) == position
        panel.include_all_rows()
        QTest.qWait(350)
        assert (vertical.value(), horizontal.value()) == position
        assert panel.replacement is None and panel._invalid_cells
        panel.validate_button.click()
        assert vertical.value() < position[0]
        assert dialog.result() != QDialog.Accepted
        assert path.read_bytes() == original and source.tasks[0].repetitions is None
    finally:
        dialog.panel.stop_validation()
        dialog.reject()
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        _APP.processEvents()

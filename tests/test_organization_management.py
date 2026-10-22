"""Original organization form and a complete synthetic management workflow.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import (
    QApplication,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QTreeWidgetItem,
)

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.organization_management import (
    delete_organization,
    save_organization,
)
from ergotools.application.settings import Language
from ergotools.bootstrap import create_window, load_icons
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.organization_record import OrganizationKind, OrganizationRecord
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.work_hierarchy_store import (
    decode_hierarchy,
    encode_hierarchy,
)
from ergotools.presentation.desktop.assessment_context_dialog import (
    AssessmentContextDialog,
)
from ergotools.presentation.desktop.job_management_dialog import JobManagementDialog
from ergotools.presentation.desktop.job_workplace_dialog import JobWorkplaceDialog
from ergotools.presentation.desktop.optional_date_edit import OptionalDateEdit
from ergotools.presentation.desktop.optional_duration_edit import OptionalDurationEdit
from ergotools.presentation.desktop.optional_time_edit import OptionalTimeEdit
from ergotools.presentation.desktop.organization_dialog import (
    ENTITY_FIELDS,
    OrganizationDialog,
)
from ergotools.presentation.desktop.organization_text import organization_text
from ergotools.presentation.desktop.worker_management_dialog import (
    WorkerManagementDialog,
)
from ergotools.presentation.desktop.workplace_assignment_dialog import (
    WorkplaceAssignmentDialog,
)
from tests.test_history_persistence import HIERARCHY
from tests.test_job_management_dialog import enter_new
from tests.test_unified_project_save import editing_workspace
from tests.test_workspace_job_risk import workspace_at

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


def enter_identifier(dialog: OrganizationDialog, identity: str) -> None:
    """Enter the one required identity through the visible form.

    Args:
        dialog: Live modal/form under test; the caller owns its lifetime and event-loop
            scheduling.
        identity: Exact saved worker/task/scheme identity or deliberately malformed
            boundary value.

    Returns:
        None.
    """
    first = next(iter(dialog.editors.values()))
    assert isinstance(first, QLineEdit)
    first.setText(identity)
    dialog.save_button.click()
    assert dialog.current_keys is not None and dialog.current_keys[-1] == identity


def test_empty_project_to_classified_assessment_via_forms(tmp_path: Path) -> None:
    """New project can reach a saved worker assessment through migrated controls.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    window = create_window(tmp_path / "settings.json")
    workspace = window.presenter.workspace
    path = tmp_path / "new.ergprj"
    workspace.create(
        str(path),
        ProjectMetadata("p", "Integration", MeasurementSystem.METRIC),
        "initial",
        LifftDraft(MeasurementSystem.METRIC),
    )
    window.refresh()
    dialog = OrganizationDialog(workspace, load_icons())
    try:
        enter_identifier(dialog, "Plant A")
        dialog.add_child_button.click()
        enter_identifier(dialog, "Section A")
        dialog.add_child_button.click()
        enter_identifier(dialog, "Line A")
        dialog.add_child_button.click()
        enter_identifier(dialog, "station-1")
        dialog.directory_tabs.setCurrentIndex(1)
        dialog.add_root_button.click()
        enter_identifier(dialog, "Day")
        dialog.close()
        jobs = JobManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
        enter_new(jobs)
        with patch.object(QMessageBox, "information"):
            jobs.save_button.click()

        def place_job() -> None:
            """Check the last exact station in the owned workplace modal.

            Check the last exact station in the owned workplace modal and click its
            explicit Save button.

            Args:
                None.

            Returns:
                None.
            """
            child = _APP.activeModalWidget()
            assert isinstance(child, JobWorkplaceDialog)
            leaf = list(child.items())[-1]
            leaf.setCheckState(0, Qt.CheckState.Checked)
            child.save_button.click()

        QTimer.singleShot(0, place_job)
        jobs.workplaces_button.click()
        jobs.close()

        def choose_placement() -> None:
            """Accept the first exact placement in the picker.

            Select and accept the first exact saved placement in the actual worker
            picker.

            Args:
                None.

            Returns:
                None.
            """
            picker = _APP.activeModalWidget()
            assert isinstance(picker, WorkplaceAssignmentDialog)
            placement = next(p for p in picker._jobs.placements if p.active)
            picker.select_workplace(placement.workplace, placement.placement_id)
            picker.accept_button.click()

        def create_worker() -> None:
            """Create saved worker worker-1/Ada through real controls.

            Create saved worker worker-1/Ada through real controls, schedule its
            placement chooser and close after assignment.

            Args:
                None.

            Returns:
                None.
            """
            workers = _APP.activeModalWidget()
            assert isinstance(workers, WorkerManagementDialog)
            workers.worker_id_combo.setEditText("worker-1")
            workers.first_name_input.setText("Ada")
            workers.save_button.click()
            QTimer.singleShot(0, choose_placement)
            workers.add_assignment_button.click()
            workers.close()

        with patch.object(
            QMessageBox,
            "question",
            side_effect=AssertionError("Unexpected close prompt"),
        ):
            QTimer.singleShot(0, create_worker)
            window.buttons["worker_management"].click()
        assert workspace.active.document.document_id == "initial"
        assert not workspace.read_history().history.entries

        def create_at_workplace() -> None:
            """Create explicitly at the newly added workplace in the diagnostic host.

            Args:
                None.

            Returns:
                None; the existing selection host owns the atomic creation transition.
            """
            context = _APP.activeModalWidget()
            assert isinstance(context, AssessmentContextDialog)
            leaf = context.tree.topLevelItem(0).child(0).child(0).child(0)
            context.tree.setCurrentItem(leaf)
            context.use.click()

        QTimer.singleShot(0, create_at_workplace)
        window.choose_assessment_context(worker_id="worker-1", create=True)
        document = workspace.active.document.document_id
        assert document != "initial"
        with AssessmentProjectFile.open(path) as project:
            assert project.format_version == 19
            assert project.load_hierarchy().plants == ("Plant A",)
            assert project.load_jobs().assignments[0].worker.worker_id == "worker-1"
            assert project.load_history().entries[0].document_id == document
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)
        window.close()


def test_metadata_save_cancel_reopen_and_sqlite_failure(tmp_path: Path) -> None:
    """Operational fields persist; a real failed catalog write retains form text.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = workspace_at(tmp_path)
    dialog = OrganizationDialog(workspace, load_icons(), language=Language.SPANISH)
    try:
        assert dialog.windowTitle() == "Gestión de la organización"
        dialog.select_keys(OrganizationKind.STATION, ("P", "S", "L", "1"))
        cycle = dialog.editors["cycle_time"]
        assert isinstance(cycle, QLineEdit)
        assert not dialog.editors["id"].isEnabled()
        cycle.setText("12,5")
        with (
            closing(sqlite3.connect(tmp_path / "project.sqlite")) as connection,
            connection,
        ):
            connection.execute(
                "CREATE TRIGGER fail_org BEFORE UPDATE ON work_catalog "
                "BEGIN SELECT RAISE(ABORT, 'failed'); END"
            )
        dialog.save_button.click()
        assert cycle.text() == "12,5"
        with AssessmentProjectFile.open(tmp_path / "project.sqlite") as project:
            assert not project.load_hierarchy().organization
        with (
            closing(sqlite3.connect(tmp_path / "project.sqlite")) as connection,
            connection,
        ):
            connection.execute("DROP TRIGGER fail_org")
        dialog.save_button.click()
        cycle = dialog.editors["cycle_time"]
        assert isinstance(cycle, QLineEdit)
        cycle.setText("discard")
        dialog.cancel_button.click()
        assert dialog.editors["cycle_time"].text() == "12.5"
        with AssessmentProjectFile.open(tmp_path / "project.sqlite") as project:
            record = project.load_hierarchy().organization[0]
            assert record.kind is OrganizationKind.STATION
            assert dict(record.attributes)["cycle_time"] == 12.5
        snapshot = workspace.read_hierarchy()
        replacement = delete_organization(
            snapshot.hierarchy, OrganizationKind.PLANT, ("P",)
        )
        with pytest.raises((ValueError, KeyError)):
            workspace.replace_hierarchy(snapshot, replacement)
        assert workspace.active.document.document_id == "a"
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_optional_fields_and_duplicate_identity(tmp_path: Path) -> None:
    """Required identifiers stay scoped; optional text/numbers are typed and saved.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = workspace_at(tmp_path)
    dialog = OrganizationDialog(workspace, load_icons())
    try:
        dialog.add_root_button.click()
        first = dialog.editors["name"]
        first.setText("P")
        dialog.save_button.click()
        assert dialog.new_mode
        assert first.text() == "P"
        first.setText("New plant")
        description = dialog.editors["description"]
        assert isinstance(description, QTextEdit)
        description.setPlainText("Saved description")
        dialog.save_button.click()
        assert (
            dict(dialog._snapshot.hierarchy.organization[-1].attributes)["description"]
            == "Saved description"
        )
        dialog.add_child_button.click()
        enter_identifier(dialog, "Empty section")
        parent = dialog._snapshot.hierarchy
        deleted = delete_organization(parent, OrganizationKind.PLANT, ("New plant",))
        assert all(r.keys[0] != "New plant" for r in deleted.organization)
        assert all(s.plant_name != "New plant" for s in deleted.sections)
        dialog.select_keys(OrganizationKind.PLANT, ("New plant",))

        def confirm() -> None:
            """Accept native Yes for the protected-delete test.

            Accept explicit native Yes consent so the outer test can verify protected
            deletion/optional details behavior.

            Args:
                None.

            Returns:
                None.
            """
            box = _APP.activeModalWidget()
            assert isinstance(box, QMessageBox)
            box.done(QMessageBox.Yes)

        QTimer.singleShot(0, confirm)
        dialog.delete_button.click()
        assert "New plant" not in dialog._snapshot.hierarchy.plants
        assert dialog.current_entity is None
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_payload_versions_and_invalid_metadata() -> None:
    """Old catalogs remain readable; orphan, unknown and nonfinite metadata fail.

    Args:
        None.

    Returns:
        None.
    """
    for version in (1, 2):
        payload = json.loads(encode_hierarchy(HIERARCHY))
        payload["version"] = version
        payload["hierarchy"].pop("organization")
        if version == 1:
            for worker in payload["hierarchy"]["work"]["workers"]:
                worker.pop("details")
        assert decode_hierarchy(json.dumps(payload)) == HIERARCHY
    for attributes in (
        (("area", float("nan")),),
        (("unknown", "value"),),
        (("area", True),),
    ):
        with pytest.raises(ValueError):
            OrganizationRecord(OrganizationKind.PLANT, ("P",), attributes)
    for fields in ENTITY_FIELDS.values():
        for _, label, _ in fields:
            assert organization_text(label, Language.SPANISH) != label


def organization_editing_dialog(
    tmp_path: Path,
    kind: OrganizationKind,
    language: Language = Language.ENGLISH,
) -> OrganizationDialog:
    """Open an existing record with empty shared history in a private native project.

    Args:
        tmp_path: Pytest-owned project/settings directory.
        kind: Existing organization level to show, including independent shifts.
        language: Localized control captions; stored values remain literal.

    Returns:
        Visible dialog borrowing a fresh workspace; caller must close both.
    """
    workspace = editing_workspace(tmp_path)
    snapshot = workspace.read_hierarchy()
    hierarchy = snapshot.hierarchy
    keys = {
        OrganizationKind.PLANT: ("Plant",),
        OrganizationKind.SECTION: ("Plant", "Section"),
        OrganizationKind.LINE: ("Plant", "Section", "Line"),
        OrganizationKind.STATION: ("Plant", "Section", "Line", "ST01"),
        OrganizationKind.SHIFT: ("1",),
    }
    for level in OrganizationKind:
        attributes = tuple(
            (
                name,
                "08:00"
                if name == "start_time"
                else "16:00"
                if name == "end_time"
                else None,
            )
            for name, _, _ in ENTITY_FIELDS[level.value][1:]
        )
        hierarchy = save_organization(
            hierarchy, OrganizationRecord(level, keys[level], attributes), creating=True
        )
    workspace.replace_hierarchy(snapshot, hierarchy)
    assert workspace.save()
    location = workspace.location
    workspace.close(choice=CloseChoice.DISCARD)
    workspace.switch(location, None)
    dialog = OrganizationDialog(workspace, load_icons(), language=language)
    if kind is OrganizationKind.SHIFT:
        dialog.directory_tabs.setCurrentIndex(1)
    dialog.select_keys(kind, keys[kind])
    dialog.optional_toggle.setChecked(True)
    dialog.show()
    _APP.processEvents()
    return dialog


@pytest.mark.parametrize(
    ("kind", "field", "value"),
    [
        (
            kind,
            name,
            "09:30"
            if editor_type == "time"
            else "12.5"
            if editor_type in ("number", "duration")
            else "2020-02-29"
            if editor_type == "date"
            else "Changed details",
        )
        for kind in OrganizationKind
        for name, _, editor_type in ENTITY_FIELDS[kind.value][1:]
    ],
)
def test_each_existing_organization_field_enables_shared_repeated_replay(
    tmp_path: Path, kind: OrganizationKind, field: str, value: str
) -> None:
    """Every optional field exposes pending Undo and replays through one shared cursor.

    Args:
        tmp_path: Disposable native project directory.
        kind: Plant/section/line/station/shift being edited.
        field: Real optional field, including multiline, numeric and time editors.
        value: Valid changed input in the control's own representation.

    Returns:
        None; mouse Undo/Redo restores exact hierarchy twice without durable writes.
    """
    dialog = organization_editing_dialog(tmp_path, kind)
    workspace = dialog._workspace
    path = Path(workspace.location)
    saved = path.read_bytes()
    baseline = workspace._hierarchy_repository().load_hierarchy()
    history = dialog.project_history
    assert history is not None
    try:
        assert not history.undo_button.isEnabled()
        for _ in range(2):
            editor = dialog.editors[field]
            if isinstance(editor, OptionalDurationEdit):
                editor.set_value(float(value))
            elif isinstance(editor, (OptionalTimeEdit, OptionalDateEdit)):
                editor.set_value(value)
            elif isinstance(editor, QTextEdit):
                editor.setPlainText(value)
            else:
                editor.setText(value)
            _APP.processEvents()
            assert history.undo_button.isEnabled()
            assert not history.redo_button.isEnabled()
            assert workspace._hierarchy_repository().load_hierarchy() == baseline
            QTest.mouseClick(history.undo_button, Qt.MouseButton.LeftButton)
            _APP.processEvents()
            assert workspace._hierarchy_repository().load_hierarchy() == baseline
            assert not history.undo_button.isEnabled(), dialog.note.text()
            assert history.redo_button.isEnabled()
            QTest.mouseClick(history.redo_button, Qt.MouseButton.LeftButton)
            _APP.processEvents()
            changed = workspace._hierarchy_repository().load_hierarchy()
            assert changed != baseline
            record = next(r for r in changed.organization if r.kind is kind)
            assert str(dict(record.attributes)[field]) == value
            QTest.mouseClick(history.undo_button, Qt.MouseButton.LeftButton)
            _APP.processEvents()
            assert workspace._hierarchy_repository().load_hierarchy() == baseline
        assert path.read_bytes() == saved
        assert not workspace.editing.is_dirty
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)
        dialog.deleteLater()


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("kind", [OrganizationKind.PLANT, OrganizationKind.SHIFT])
def test_standard_optional_clocks_format_keyboard_input_and_keep_boundaries(
    tmp_path: Path, language: Language, kind: OrganizationKind
) -> None:
    """Native segmented editors accept short keyboard clocks without losing absence.

    Args:
        tmp_path: Disposable native project directory.
        language: English or Spanish presentation.
        kind: Plant or Shift, both using the same standard time adapter.

    Returns:
        None; typing formatting, exact midnight, optional clearing and labels work.
    """
    dialog = organization_editing_dialog(tmp_path, kind, language)
    try:
        for name in ("start_time", "end_time"):
            editor = dialog.editors[name]
            assert isinstance(editor, OptionalTimeEdit)
            assert editor.displayFormat() == "HH:mm"
            assert "00:00-23:59" in editor.toolTip()
            label = dialog.optional_form.labelForField(editor)
            assert label is not None and "24 h, HH:mm" in label.text()
            for valid in ("00:00", "08:00", "12:30", "23:59"):
                editor.set_value(valid)
                assert editor.clock_text() == valid and editor.is_acceptable()
            for invalid in ("24:00", "12:60", "bad"):
                editor.set_value(invalid)
                assert not editor.is_acceptable()
                assert editor.clock_text() == invalid
            editor.clear()
            editor.setFocus()
            QTest.keyClicks(editor, "letters")
            assert editor.clock_text() == ""
            QTest.keyClicks(editor, "8:30")
            assert editor.clock_text() == "08:30"
            editor.selectAll()
            QTest.keyClick(editor, Qt.Key.Key_Delete)
            assert editor.clock_text() == ""
        dialog.cancel_edit()
        assert dialog.pending_entity_action() is None
    finally:
        dialog.close()
        dialog._workspace.close(choice=CloseChoice.DISCARD)
        dialog.deleteLater()


@pytest.mark.parametrize("value", ["24:00", "12:60", "08:0", "garbage"])
def test_invalid_shift_time_cannot_be_accepted_or_close_the_form(
    tmp_path: Path, value: str
) -> None:
    """Programmatic/loaded malformed times are retained for correction, never saved.

    Args:
        tmp_path: Disposable native project directory.
        value: Nonempty malformed clock value, bypassing interactive validation.

    Returns:
        None; rejection preserves the private hierarchy, saved file and draft text.
    """
    dialog = organization_editing_dialog(tmp_path, OrganizationKind.SHIFT)
    workspace = dialog._workspace
    baseline = workspace._hierarchy_repository().load_hierarchy()
    saved = Path(workspace.location).read_bytes()
    try:
        dialog.editors["start_time"].set_value(value)
        assert dialog.pending_entity_action() is None
        assert not dialog.accept_pending_entity()
        dialog.close()
        assert dialog.isVisible()
        assert dialog.editors["start_time"].text() == value
        assert "HH:mm" in dialog.note.text()
        assert workspace._hierarchy_repository().load_hierarchy() == baseline
        assert Path(workspace.location).read_bytes() == saved
        dialog.editors["start_time"].set_value("09:30")
        assert dialog.project_history.undo_button.isEnabled()
        assert dialog.accept_pending_entity(), dialog.note.text()
    finally:
        dialog.cancel_edit()
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)
        dialog.deleteLater()


def test_shift_overnight_and_blank_times_save_reopen_and_undo(tmp_path: Path) -> None:
    """Night shifts and unspecified times retain literal values through shared replay.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; only main Save publishes, and reopening retains the accepted clock data.
    """
    dialog = organization_editing_dialog(tmp_path, OrganizationKind.SHIFT)
    workspace = dialog._workspace
    path = Path(workspace.location)
    saved = path.read_bytes()
    history = dialog.project_history
    assert history is not None
    try:
        dialog.editors["start_time"].set_value("22:00")
        dialog.editors["end_time"].set_value("06:00")
        dialog.ends_next_day.setChecked(True)
        assert history.undo_button.isEnabled()
        assert dialog.accept_pending_entity(), dialog.note.text()
        overnight = workspace._hierarchy_repository().load_hierarchy()
        assert path.read_bytes() == saved
        dialog.editors["start_time"].clear()
        dialog.editors["end_time"].clear()
        assert history.undo_button.isEnabled()
        assert dialog.accept_pending_entity(), dialog.note.text()
        history.undo_button.setFocus()
        history.replay(redo=False)
        assert workspace._hierarchy_repository().load_hierarchy() == overnight
        assert dialog.editors["start_time"].text() == "22:00"
        assert dialog.editors["end_time"].text() == "06:00"
        history.replay(redo=True)
        assert dialog.editors["start_time"].clock_text() == ""
        assert dialog.editors["end_time"].clock_text() == ""
        assert workspace.save()
        with AssessmentProjectFile.open(path) as project:
            shift = next(
                r
                for r in project.load_hierarchy().organization
                if r.kind is OrganizationKind.SHIFT
            )
            assert dict(shift.attributes)["start_time"] is None
            assert dict(shift.attributes)["end_time"] is None
        dialog.editors["start_time"].set_value("00:00")
        dialog.editors["end_time"].set_value("23:59")
        dialog.close()
        assert workspace.save()
        workspace.close(choice=CloseChoice.DISCARD)
        workspace.switch(str(path), None)
        reopened = OrganizationDialog(
            workspace, load_icons(), initial_entity=OrganizationKind.SHIFT
        )
        try:
            assert reopened.editors["start_time"].text() == "00:00"
            assert reopened.editors["end_time"].text() == "23:59"
        finally:
            reopened.close()
            reopened.deleteLater()
    finally:
        dialog.deleteLater()
        workspace.close(choice=CloseChoice.DISCARD)


def test_organization_native_typing_undo_and_cancel_preserve_shared_history(
    tmp_path: Path,
) -> None:
    """Typing Undo stays local and Cancel drops the draft without a project command.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; valid typing exposes pending project Undo but keeps its cursor clean.
    """
    dialog = organization_editing_dialog(tmp_path, OrganizationKind.SHIFT)
    workspace = dialog._workspace
    history = dialog.project_history
    assert history is not None
    try:
        editor = dialog.editors["description"]
        assert isinstance(editor, QTextEdit)
        # Native XCB needs an active top-level before assigning field focus.
        dialog.activateWindow()
        _APP.setActiveWindow(dialog)
        _APP.processEvents()
        editor.setFocus()
        _APP.processEvents()
        assert _APP.focusWidget() is editor
        QTest.keyClicks(editor, "Changed shift")
        assert history.undo_button.isEnabled()
        history.replay(redo=False)
        assert editor.toPlainText() == ""
        assert not history.undo_button.isEnabled()
        assert not workspace.editing.is_dirty
        QTest.keyClicks(editor, "Another shift")
        dialog.cancel_button.click()
        assert dialog.editors["description"].toPlainText() == ""
        assert not history.undo_button.isEnabled()
        assert not workspace.editing.is_dirty
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)
        dialog.deleteLater()


def test_new_shift_invalid_time_blocks_creation_and_keeps_identity(
    tmp_path: Path,
) -> None:
    """Unfinished time cannot silently create a shift or discard its new-record form.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; correcting the same form creates one record, published by main Save.
    """
    workspace = editing_workspace(tmp_path)
    dialog = OrganizationDialog(
        workspace, load_icons(), initial_entity=OrganizationKind.SHIFT
    )
    try:
        dialog.editors["id"].setText("Night")
        dialog.editors["start_time"].set_value("22:")
        assert not dialog.accept_pending_entity()
        assert dialog.new_mode
        assert dialog.editors["id"].text() == "Night"
        assert not workspace._hierarchy_repository().load_hierarchy().work.shifts
        dialog.editors["start_time"].set_value("22:00")
        dialog.editors["end_time"].set_value("06:00")
        dialog.ends_next_day.setChecked(True)
        assert dialog.accept_pending_entity(), dialog.note.text()
        assert workspace._hierarchy_repository().load_hierarchy().work.shifts == (
            "Night",
        )
        assert workspace.save()
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)
        dialog.deleteLater()


def organization_location_items(
    dialog: OrganizationDialog,
) -> dict[tuple[str, ...], QTreeWidgetItem]:
    """Read current tree items by stable ancestry without expanding any branches.

    Args:
        dialog: Open organization form whose tree belongs to the caller.

    Returns:
        Fresh mapping including hidden descendants. Qt item references are valid only
        until the next operation rebuilds the tree; callers retain keys/flags instead.
    """
    root = dialog.location_tree.invisibleRootItem()
    assert root is not None
    stack = [root.child(index) for index in range(root.childCount())]
    items = {}
    while stack:
        item = stack.pop()
        if item is not None:
            _, keys = item.data(0, Qt.ItemDataRole.UserRole)
            items[keys] = item
            stack.extend(item.child(index) for index in range(item.childCount()))
    return items


@pytest.mark.parametrize("kind", list(OrganizationKind))
@pytest.mark.parametrize("expanded", [False, True])
@pytest.mark.parametrize("language", list(Language))
def test_organization_edit_replay_keeps_optional_details_and_tree(
    tmp_path: Path, kind: OrganizationKind, expanded: bool, language: Language
) -> None:
    """Record edits replay without changing the user's working detail/branch choices.

    Args:
        tmp_path: Disposable native project directory.
        kind: Existing location or independent shift level under test.
        expanded: User-selected Optional details state to preserve.
        language: English or Spanish presentation, independent of record keys.

    Returns:
        None; repeated exact source Undo/Redo keeps the same view and saved bytes.
    """
    dialog = organization_editing_dialog(tmp_path, kind, language)
    workspace = dialog._workspace
    history = dialog.project_history
    assert history is not None
    baseline = workspace._hierarchy_repository().load_hierarchy()
    saved = Path(workspace.location).read_bytes()
    selected = dialog.current_keys
    try:
        items = organization_location_items(dialog)
        items[("Plant",)].setExpanded(True)
        items[("Plant", "Section")].setExpanded(True)
        items[("Plant", "Section", "Line")].setExpanded(False)
        flags = {key: item.isExpanded() for key, item in items.items()}
        dialog.optional_toggle.setChecked(expanded)
        assert not history.undo_button.isEnabled()
        for _ in range(2):
            name = ENTITY_FIELDS[kind.value][1][0]
            editor = dialog.editors[name]
            if isinstance(editor, QTextEdit):
                editor.setPlainText("Changed details")
            else:
                editor.setText("Changed details")
            QTest.mouseClick(history.undo_button, Qt.MouseButton.LeftButton)
            _APP.processEvents()
            assert dialog.optional_toggle.isChecked() is expanded
            assert dialog.current_keys == selected
            assert workspace._hierarchy_repository().load_hierarchy() == baseline
            assert {
                key: item.isExpanded()
                for key, item in organization_location_items(dialog).items()
            } == flags
            QTest.mouseClick(history.redo_button, Qt.MouseButton.LeftButton)
            _APP.processEvents()
            assert dialog.optional_toggle.isChecked() is expanded
            assert {
                key: item.isExpanded()
                for key, item in organization_location_items(dialog).items()
            } == flags
            QTest.mouseClick(history.undo_button, Qt.MouseButton.LeftButton)
            _APP.processEvents()
        assert Path(workspace.location).read_bytes() == saved
        assert not workspace.editing.is_dirty
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)
        dialog.deleteLater()


@pytest.mark.parametrize("kind", list(OrganizationKind))
@pytest.mark.parametrize("expanded", [False, True])
@pytest.mark.parametrize("language", list(Language))
def test_organization_delete_subtree_replay_restores_expansion_and_selection(
    tmp_path: Path, kind: OrganizationKind, expanded: bool, language: Language
) -> None:
    """Deletion leaves other branches intact and Undo restores the removed working view.

    Args:
        tmp_path: Disposable native project directory.
        kind: Plant/section/line/station/shift removed through the actual control.
        expanded: User-selected Optional details state before deleting.
        language: English or Spanish control captions; keys remain literal.

    Returns:
        None; cancelled deletion is inert, confirmed Delete/Undo/Redo retain exact
        branches, ownership data, form state and the last saved project bytes.
    """
    dialog = organization_editing_dialog(tmp_path, kind, language)
    workspace = dialog._workspace
    history = dialog.project_history
    assert history is not None
    baseline = workspace._hierarchy_repository().load_hierarchy()
    saved = Path(workspace.location).read_bytes()
    selected = dialog.current_keys
    try:
        items = organization_location_items(dialog)
        for item in items.values():
            item.setExpanded(True)
        flags = {key: item.isExpanded() for key, item in items.items()}
        dialog.optional_toggle.setChecked(expanded)
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.No):
            dialog.delete_button.click()
        assert dialog.current_keys == selected
        assert dialog.optional_toggle.isChecked() is expanded
        assert workspace._hierarchy_repository().load_hierarchy() == baseline
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.Yes):
            dialog.delete_button.click()
        assert dialog.current_entity is None
        assert dialog.optional_toggle.isChecked() is expanded
        remaining = organization_location_items(dialog)
        assert {key: item.isExpanded() for key, item in remaining.items()} == {
            key: value for key, value in flags.items() if key in remaining
        }
        for _ in range(2):
            QTest.mouseClick(history.undo_button, Qt.MouseButton.LeftButton)
            _APP.processEvents()
            assert workspace._hierarchy_repository().load_hierarchy() == baseline
            assert dialog.current_entity is kind and dialog.current_keys == selected
            assert dialog.optional_toggle.isChecked() is expanded
            assert {
                key: item.isExpanded()
                for key, item in organization_location_items(dialog).items()
            } == flags
            with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
                QTest.mouseClick(history.redo_button, Qt.MouseButton.LeftButton)
            _APP.processEvents()
            assert dialog.current_entity is None
            assert dialog.optional_toggle.isChecked() is expanded
            assert {
                key: item.isExpanded()
                for key, item in organization_location_items(dialog).items()
            } == {key: value for key, value in flags.items() if key in remaining}
        assert Path(workspace.location).read_bytes() == saved
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)
        dialog.deleteLater()


def test_user_changed_branch_choices_after_delete_win_on_undo(tmp_path: Path) -> None:
    """A user collapse/expand after deletion remains the current preference on replay.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; hidden removed branches recover their remembered flags, surviving
        branches use the user's latest choice and view-only actions add no history.
    """
    dialog = organization_editing_dialog(tmp_path, OrganizationKind.LINE)
    workspace = dialog._workspace
    history = dialog.project_history
    assert history is not None
    try:
        dialog.location_tree.expandAll()
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.Yes):
            dialog.delete_button.click()
        items = organization_location_items(dialog)
        items[("Plant",)].setExpanded(False)
        dialog.optional_toggle.setChecked(False)
        QTest.mouseClick(history.undo_button, Qt.MouseButton.LeftButton)
        _APP.processEvents()
        items = organization_location_items(dialog)
        assert not items[("Plant",)].isExpanded()
        assert items[("Plant", "Section", "Line")].isExpanded()
        assert dialog.current_keys == ("Plant", "Section", "Line")
        assert not dialog.optional_toggle.isChecked()
        assert not workspace.editing.is_dirty
        assert not history.undo_button.isEnabled()
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)
        dialog.deleteLater()


def test_organization_delete_keeps_mixed_sibling_branches(tmp_path: Path) -> None:
    """Deleting one line does not open or collapse sibling/hidden descendant branches.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; exact mixed branch flags survive Delete and restoration of its subtree.
    """
    dialog = organization_editing_dialog(tmp_path, OrganizationKind.LINE)
    workspace = dialog._workspace
    history = dialog.project_history
    assert history is not None
    try:
        hierarchy = dialog._snapshot.hierarchy
        for kind, keys in (
            (OrganizationKind.SECTION, ("Plant", "Other")),
            (OrganizationKind.LINE, ("Plant", "Other", "Other line")),
            (OrganizationKind.STATION, ("Plant", "Other", "Other line", "ST02")),
        ):
            hierarchy = save_organization(
                hierarchy, OrganizationRecord(kind, keys), creating=True
            )
        dialog._snapshot = workspace.replace_hierarchy(dialog._snapshot, hierarchy)
        dialog.refresh_all()
        dialog.select_keys(OrganizationKind.LINE, ("Plant", "Section", "Line"))
        items = organization_location_items(dialog)
        items[("Plant",)].setExpanded(True)
        items[("Plant", "Section")].setExpanded(True)
        items[("Plant", "Section", "Line")].setExpanded(True)
        items[("Plant", "Other")].setExpanded(False)
        items[("Plant", "Other", "Other line")].setExpanded(True)
        flags = {key: item.isExpanded() for key, item in items.items()}
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.Yes):
            dialog.delete_button.click()
        remaining = organization_location_items(dialog)
        assert {key: item.isExpanded() for key, item in remaining.items()} == {
            key: value for key, value in flags.items() if key in remaining
        }
        QTest.mouseClick(history.undo_button, Qt.MouseButton.LeftButton)
        _APP.processEvents()
        assert {
            key: item.isExpanded()
            for key, item in organization_location_items(dialog).items()
        } == flags
        assert dialog.current_keys == ("Plant", "Section", "Line")
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)
        dialog.deleteLater()


def test_organization_new_selection_after_delete_is_kept_on_undo(
    tmp_path: Path,
) -> None:
    """Undo restores data without overriding a newer deliberate record selection.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; changing to Shift after a Line deletion remains selected during replay.
    """
    dialog = organization_editing_dialog(tmp_path, OrganizationKind.LINE)
    workspace = dialog._workspace
    history = dialog.project_history
    assert history is not None
    try:
        dialog.location_tree.expandAll()
        with patch.object(QMessageBox, "exec", return_value=QMessageBox.Yes):
            dialog.delete_button.click()
        dialog.directory_tabs.setCurrentIndex(1)
        dialog.select_keys(OrganizationKind.SHIFT, ("1",))
        dialog.optional_toggle.setChecked(True)
        QTest.mouseClick(history.undo_button, Qt.MouseButton.LeftButton)
        _APP.processEvents()
        assert dialog.current_entity is OrganizationKind.SHIFT
        assert dialog.current_keys == ("1",)
        assert dialog.directory_tabs.currentIndex() == 1
        assert dialog.optional_toggle.isChecked()
        assert ("Plant", "Section", "Line") in organization_location_items(dialog)
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)
        dialog.deleteLater()


def test_organization_view_choices_are_dialog_local_not_project_edits(
    tmp_path: Path,
) -> None:
    """Expansion changes add no Undo/dirty state and do not survive dialog teardown.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; a fresh dialog keeps its established collapsed initial layout.
    """
    dialog = organization_editing_dialog(tmp_path, OrganizationKind.LINE)
    workspace = dialog._workspace
    saved = Path(workspace.location).read_bytes()
    try:
        dialog.location_tree.expandAll()
        dialog.optional_toggle.setChecked(True)
        dialog.refresh_all()
        assert not workspace.editing.is_dirty
        assert not dialog.project_history.undo_button.isEnabled()
        dialog.close()
        reopened = OrganizationDialog(workspace, load_icons())
        try:
            assert not reopened.optional_toggle.isChecked()
            assert not any(
                item.isExpanded()
                for item in organization_location_items(reopened).values()
            )
            assert not workspace.editing.is_dirty
            assert Path(workspace.location).read_bytes() == saved
        finally:
            reopened.close()
            reopened.deleteLater()
    finally:
        dialog.deleteLater()
        workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize(
    ("start", "end", "next_day", "valid"),
    [
        ("08:00", "16:00", False, True),
        ("22:00", "06:00", True, True),
        ("23:30", "00:15", True, True),
        ("00:00", "23:59", False, True),
        ("08:00", "08:00", True, True),
        ("08:00", "06:00", False, False),
        ("08:00", "08:00", False, False),
        ("08:00", "16:00", True, False),
        (None, "16:00", False, True),
        ("08:00", None, False, True),
        (None, None, False, True),
    ],
)
def test_shift_day_intent_validation_keeps_private_and_saved_data_on_rejection(
    tmp_path: Path,
    language: Language,
    start: str | None,
    end: str | None,
    next_day: bool,
    valid: bool,
) -> None:
    """Explicit same-day/overnight intent validates without new project fields.

    Args:
        tmp_path: Disposable native project directory.
        language: English or Spanish control/error wording.
        start: Optional start clock, including midnight.
        end: Optional end clock, including an earlier overnight end.
        next_day: User's following-day choice, inferred only when opening saved data.
        valid: Whether this complete/optional clock pair has consistent day intent.

    Returns:
        None; invalid forms remain available; accepted forms retain clock-only data.
    """
    dialog = organization_editing_dialog(tmp_path, OrganizationKind.SHIFT, language)
    workspace = dialog._workspace
    baseline = workspace._hierarchy_repository().load_hierarchy()
    saved = Path(workspace.location).read_bytes()
    try:
        dialog.editors["start_time"].set_value(start)
        dialog.editors["end_time"].set_value(end)
        assert dialog.ends_next_day is not None
        dialog.ends_next_day.setChecked(next_day)
        assert dialog.ends_next_day.isEnabled() is bool(start and end)
        assert (dialog._shift_time_error() is None) is valid
        assert dialog.accept_pending_entity() is valid
        if not valid:
            assert workspace._hierarchy_repository().load_hierarchy() == baseline
            assert dialog.editors["start_time"].clock_text() == start
            assert dialog.editors["end_time"].clock_text() == end
            assert dialog.note.text()
        else:
            record = next(
                r
                for r in dialog._snapshot.hierarchy.organization
                if r.kind is OrganizationKind.SHIFT
            )
            assert dict(record.attributes)["start_time"] == start
            assert dict(record.attributes)["end_time"] == end
            assert "ends_next_day" not in dict(record.attributes)
        assert Path(workspace.location).read_bytes() == saved
    finally:
        dialog.cancel_edit()
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)
        dialog.deleteLater()


def test_overnight_shift_save_reopen_shared_undo_retains_view_and_clock_identity(
    tmp_path: Path,
) -> None:
    """Night shifts infer their saved day choice and replay to a day shift exactly.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; no new attribute, schema or calculation changes accompany the controls.
    """
    dialog = organization_editing_dialog(tmp_path, OrganizationKind.SHIFT)
    workspace = dialog._workspace
    history = dialog.project_history
    assert history is not None
    try:
        assert not dialog.ends_next_day.isChecked()
        dialog.editors["start_time"].set_value("22:00")
        dialog.editors["end_time"].set_value("06:00")
        assert dialog.pending_entity_action() is None
        dialog.ends_next_day.setChecked(True)
        assert history.undo_button.isEnabled()
        QTest.mouseClick(history.undo_button, Qt.MouseButton.LeftButton)
        _APP.processEvents()
        assert dialog.editors["start_time"].clock_text() == "08:00"
        assert not dialog.ends_next_day.isChecked()
        assert dialog.optional_toggle.isChecked()
        QTest.mouseClick(history.redo_button, Qt.MouseButton.LeftButton)
        _APP.processEvents()
        assert dialog.editors["start_time"].clock_text() == "22:00"
        assert dialog.ends_next_day.isChecked()
        assert dialog.optional_toggle.isChecked()
        dialog.close()
        assert workspace.save()
        location = workspace.location
        workspace.close(choice=CloseChoice.DISCARD)
        workspace.switch(location, None)
        reopened = OrganizationDialog(
            workspace, load_icons(), initial_entity=OrganizationKind.SHIFT
        )
        try:
            assert reopened.ends_next_day.isChecked()
            assert reopened.editors["start_time"].clock_text() == "22:00"
            assert reopened.editors["end_time"].clock_text() == "06:00"
            assert not workspace.editing.is_dirty
        finally:
            reopened.close()
            reopened.deleteLater()
    finally:
        dialog.deleteLater()
        workspace.close(choice=CloseChoice.DISCARD)


def test_focused_standard_clock_keeps_keyboard_history_local(tmp_path: Path) -> None:
    """Shared history recognizes the line editor inside a focused standard time widget.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; keyboard history inside a clock cannot replay the project cursor.
    """
    dialog = organization_editing_dialog(tmp_path, OrganizationKind.SHIFT)
    workspace = dialog._workspace
    history = dialog.project_history
    assert history is not None
    try:
        editor = dialog.editors["start_time"]
        assert isinstance(editor, OptionalTimeEdit)
        dialog.activateWindow()
        _APP.setActiveWindow(dialog)
        editor.setFocus()
        _APP.processEvents()
        assert _APP.focusWidget() is editor
        editor.setSelectedSection(editor.HourSection)
        QTest.keyClicks(editor, "09")
        assert history.undo_button.isEnabled()
        history.replay(redo=False)
        assert not workspace.editing.is_dirty
        assert dialog.current_keys == ("1",)
        assert dialog.editors["start_time"] is editor
        history.replay(redo=True)
        assert not workspace.editing.is_dirty
        dialog.cancel_edit()
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)
        dialog.deleteLater()

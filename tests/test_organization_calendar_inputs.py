"""Organization calendars, daily durations and removal of obsolete station fields.

Test layer. Drive actual Qt controls against disposable project copies and immutable
metadata. Verify absence separately from real dates/zero/full-day durations, canonical
persistence, rollback, and shared history without modifying maintained projects.
"""

from datetime import date
from pathlib import Path

import pytest
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.domain.organization_record import OrganizationKind, OrganizationRecord
from ergotools.presentation.desktop.optional_date_edit import OptionalDateEdit
from ergotools.presentation.desktop.optional_duration_edit import OptionalDurationEdit
from tests.test_organization_management import organization_editing_dialog

# Keep native controls owned until their Qt teardown has completed.
_APP = QApplication.instance() or QApplication([])
# The owner explicitly removed these station attributes, without replacement data.
REMOVED_STATION_FIELDS = (
    "task_description",
    "equipment_used",
    "ergonomic_risk_level",
    "performance_metric",
    "power_consumption",
    "materials_used",
)


@pytest.mark.parametrize("field", REMOVED_STATION_FIELDS)
def test_station_domain_rejects_removed_fields(field: str) -> None:
    """Disallow obsolete attributes even when their previous values were empty.

    Args:
        field: Exact field removed by the owner.

    Returns:
        None. No current domain record can retain this obsolete field.
    """
    with pytest.raises(ValueError, match="Unknown or duplicate"):
        OrganizationRecord(
            OrganizationKind.STATION, ("P", "S", "L", "ST"), ((field, None),)
        )


@pytest.mark.parametrize(
    ("kind", "field"),
    (
        (OrganizationKind.PLANT, "opening_date"),
        (OrganizationKind.SECTION, "creation_date"),
        (OrganizationKind.LINE, "creation_date"),
        (OrganizationKind.STATION, "creation_date"),
    ),
)
@pytest.mark.parametrize("value", ("2025-02-30", "20/01/2020", "2020-1-1", "nonsense"))
def test_domain_rejects_invalid_organization_dates(
    kind: OrganizationKind, field: str, value: str
) -> None:
    """Require real canonical dates instead of unrestricted date-like text.

    Args:
        kind: Organization level owning this date.
        field: Opening or creation date metadata name.
        value: Invalid or noncanonical prior free-text input.

    Returns:
        None. Invalid dates cannot enter storage through a new snapshot.
    """
    keys = {
        OrganizationKind.PLANT: ("P",),
        OrganizationKind.SECTION: ("P", "S"),
        OrganizationKind.LINE: ("P", "S", "L"),
        OrganizationKind.STATION: ("P", "S", "L", "ST"),
    }[kind]
    with pytest.raises(ValueError):
        OrganizationRecord(kind, keys, ((field, value),))


@pytest.mark.parametrize("value", (-1, 24.01, 25, float("nan"), float("inf"), 1.234))
def test_daily_duration_rejects_invalid_or_lossy_values(value: float) -> None:
    """Avoid clock wrapping or silent rounding of an unsupported duration.

    Args:
        value: Negative, over-day, nonfinite or subminute decimal hours.

    Returns:
        None. Domain and presentation enforce the same daily-minute contract.
    """
    with pytest.raises(ValueError):
        OrganizationRecord(
            OrganizationKind.PLANT, ("P",), (("operational_hours", value),)
        )
    editor = OptionalDurationEdit("Not set")
    try:
        with pytest.raises(ValueError):
            editor.set_value(value)
        assert editor.duration_text() == ""
    finally:
        editor.close()


def test_optional_calendar_today_selection_clear_and_keyboard() -> None:
    """A click on today's empty anchor is a real edit, unlike opening the popup.

    Args:
        None.

    Returns:
        None. ISO data and Python/Qt explicit setters retain all valid dates.
    """
    editor = OptionalDateEdit("Not set")
    editor.show()
    try:
        assert editor.date_text() == ""
        assert editor.date() == QDate.currentDate()
        editor.calendarWidget().clicked.emit(QDate.currentDate())
        assert editor.date_text() == QDate.currentDate().toString(Qt.ISODate)
        editor.setDate(date(2020, 2, 29))
        assert editor.date_text() == "2020-02-29"
        editor.setDate(QDate(1, 1, 1))
        assert editor.date_text() == "0001-01-01"
        editor.set_value("2020-02-29")
        editor.selectAll()
        QTest.keyClick(editor, Qt.Key_Delete)
        assert editor.date_text() == ""
        editor.stepBy(1)
        assert editor.date_text()
        editor.clear()
        editor.setReadOnly(True)
        editor.stepBy(1)
        assert editor.date_text() == ""
        with pytest.raises(ValueError):
            editor.set_value("wrong")
        assert editor.date_text() == ""
    finally:
        editor.close()


@pytest.mark.parametrize("value", (None, 0.0, 9.0, 9.5, 1 / 60, 24.0))
def test_optional_duration_keeps_minutes_zero_and_full_day(value: float | None) -> None:
    """Native hour/minute quantities retain decimal-hour storage without wrapping.

    Args:
        value: Optional valid daily duration, including zero and a full day.

    Returns:
        None. Both controls enforce bounds and clearing returns to absence.
    """
    editor = OptionalDurationEdit("Not set")
    try:
        editor.set_value(value)
        assert editor.duration_text() == ("" if value is None else str(value))
        assert editor.minutes.isEnabled() == (value is not None and value < 24)
        editor.hours.setValue(9)
        editor.minutes.setValue(30)
        assert editor.duration_text() == "9.5"
        editor.hours.setValue(24)
        assert editor.duration_text() == "24.0" and editor.minutes.value() == 0
        editor.hours.selectAll()
        QTest.keyClick(editor.hours, Qt.Key_Delete)
        assert editor.duration_text() == ""
        editor.set_value(9.5)
        editor.clear()
        assert editor.duration_text() == ""
    finally:
        editor.close()


@pytest.mark.parametrize(
    ("kind", "field"),
    (
        (OrganizationKind.PLANT, "opening_date"),
        (OrganizationKind.SECTION, "creation_date"),
        (OrganizationKind.LINE, "creation_date"),
        (OrganizationKind.STATION, "creation_date"),
    ),
)
def test_calendar_shared_history_save_and_reopen(
    tmp_path: Path, kind: OrganizationKind, field: str
) -> None:
    """Each calendar participates in private edits, shared replay and main Save.

    Args:
        tmp_path: Disposable project directory.
        kind: Exact location level selected in the real form.
        field: Calendar metadata belonging to that level.

    Returns:
        None. Undo restores absence, Redo restores the day, and durable Save retains it.
    """
    dialog = organization_editing_dialog(tmp_path, kind)
    workspace = dialog._workspace
    try:
        editor = dialog.editors[field]
        assert isinstance(editor, OptionalDateEdit)
        editor.setDate(QDate(2020, 2, 29))
        history = dialog.project_history
        assert history is not None and history.undo_button.isEnabled()
        QTest.mouseClick(history.undo_button, Qt.LeftButton)
        assert dialog.editors[field].date_text() == ""
        QTest.mouseClick(history.redo_button, Qt.LeftButton)
        assert dialog.editors[field].date_text() == "2020-02-29"
        dialog.close()
        assert workspace.save()
        location = workspace.location
        workspace.close(choice=CloseChoice.DISCARD)
        workspace.switch(location, None)
        record = next(
            item
            for item in workspace.read_hierarchy().hierarchy.organization
            if item.kind is kind
        )
        assert dict(record.attributes)[field] == "2020-02-29"
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_plant_shift_count_requires_real_usage_and_is_not_stored(
    tmp_path: Path,
) -> None:
    """Unused project Shift definitions do not inflate a Plant-specific usage count.

    Args:
        tmp_path: Disposable project and settings directory.

    Returns:
        None. Adding an unused shift leaves the count zero; no Plant count is saved.
    """
    dialog = organization_editing_dialog(tmp_path, OrganizationKind.PLANT)
    workspace = dialog._workspace
    try:
        assert dialog.plant_shift_count is not None
        assert dialog.plant_shift_count.text() == "0"
        jobs_snapshot = workspace.read_jobs()
        hierarchy_snapshot = dialog._snapshot
        assert workspace.plant_shift_count("Plant") == 0
        assert workspace.jobs_are_current(jobs_snapshot)
        assert workspace.hierarchy_is_current(hierarchy_snapshot)
        assert "number_of_shifts" not in dialog.editors
        dialog.start_new(OrganizationKind.SHIFT, [])
        dialog.editors["id"].setText("2")
        dialog.save_entity()
        dialog.select_keys(OrganizationKind.PLANT, ("Plant",))
        assert dialog.plant_shift_count.text() == "0"
        plant = next(
            record
            for record in dialog._snapshot.hierarchy.organization
            if record.kind is OrganizationKind.PLANT
        )
        assert "number_of_shifts" not in dict(plant.attributes)
        with pytest.raises(ValueError, match="Unknown or duplicate"):
            OrganizationRecord(
                OrganizationKind.PLANT, ("Plant",), (("number_of_shifts", 2),)
            )
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_empty_calendar_accepts_first_real_click_on_today() -> None:
    """Click the native calendar's already selected day without an unrelated edit.

    Args:
        None.

    Returns:
        None. Today's navigation anchor becomes provided on the first actual click.
    """
    from PyQt5.QtCore import QPoint
    from PyQt5.QtWidgets import QTableView

    editor = OptionalDateEdit("Not set")
    editor.resize(260, 36)
    editor.show()
    _APP.setActiveWindow(editor)
    try:
        QTest.mouseClick(
            editor, Qt.LeftButton, pos=QPoint(editor.width() - 10, editor.height() // 2)
        )
        _APP.processEvents()
        calendar = editor.calendarWidget()
        assert calendar is not None and calendar.isVisible()
        assert editor.date_text() == ""
        view = calendar.findChild(QTableView)
        assert view is not None and view.currentIndex().isValid()
        QTest.mouseClick(
            view.viewport(),
            Qt.LeftButton,
            pos=view.visualRect(view.currentIndex()).center(),
        )
        _APP.processEvents()
        assert editor.date_text() == QDate.currentDate().toString(Qt.ISODate)
    finally:
        editor.close()


@pytest.mark.parametrize("populated", (False, True))
def test_previous_organization_cleanup_changes_only_retired_metadata(
    tmp_path: Path, populated: bool
) -> None:
    """Remove old Station data and a stale Plant count without touching real results.

    Args:
        tmp_path: Disposable older native source and exclusive output directory.
        populated: Exercise both missing and explicitly retired entered values.

    Returns:
        None. All unrelated rows and source bytes survive conversion exactly.
    """
    import json
    import sqlite3
    from contextlib import closing

    from tools.project_migration.ergotools_migration.previous_project import (
        upgrade_previous_project,
    )

    original = Path("test_projects/native/comparative_risk_test.ergprj")
    source, output = tmp_path / "old.ergprj", tmp_path / "new.ergprj"
    with (
        closing(
            sqlite3.connect(original.resolve().as_uri() + "?mode=ro", uri=True)
        ) as old,
        closing(sqlite3.connect(source)) as working,
    ):
        old.backup(working)
        payload = json.loads(
            working.execute("SELECT payload FROM work_catalog").fetchone()[0]
        )
        for record in payload["hierarchy"]["organization"]:
            if record["kind"] == "Station":
                record["attributes"].extend(
                    (field, "Retired value" if populated else None)
                    for field in REMOVED_STATION_FIELDS
                )
            elif record["kind"] == "Plant":
                record["attributes"].append(
                    ("number_of_shifts", 88 if populated else None)
                )
        with working:
            working.execute("UPDATE project_metadata SET version=17")
            working.execute("UPDATE work_catalog SET payload=?", (json.dumps(payload),))
        tables = [
            row[0]
            for row in working.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            if row[0] not in ("project_metadata", "work_catalog")
        ]
        before = {
            table: working.execute(f'SELECT * FROM "{table}"').fetchall()
            for table in tables
        }
    source_bytes = source.read_bytes()
    with upgrade_previous_project(source, output) as native:
        assert native.format_version == 19
        for record in native.load_hierarchy().organization:
            if record.kind is OrganizationKind.STATION:
                assert not set(REMOVED_STATION_FIELDS).intersection(
                    dict(record.attributes)
                )
            if record.kind is OrganizationKind.PLANT:
                assert "number_of_shifts" not in dict(record.attributes)
    assert source.read_bytes() == source_bytes
    with closing(sqlite3.connect(output)) as converted:
        assert {
            table: converted.execute(f'SELECT * FROM "{table}"').fetchall()
            for table in tables
        } == before


def test_plant_shift_usage_deduplicates_active_links_and_separates_plants() -> None:
    """Count active Job/worker usage once per Plant/shift, including unclassified staff.

    Args:
        None.

    Returns:
        None. Inactive links and inactive Jobs do not establish current usage.
    """
    from ergotools.application.organization_management import plant_shift_count
    from ergotools.domain.assessments.context import WorkerContext, WorkplaceContext
    from ergotools.domain.job_catalog import (
        Job,
        JobCatalog,
        JobPlacement,
        WorkerJobAssignment,
    )

    first = WorkplaceContext("P", "S", "L", "A", "1")
    catalog = JobCatalog(
        "p",
        (Job("J", "Active"), Job("old", "Inactive", False)),
        (
            JobPlacement(1, "J", first),
            JobPlacement(2, "J", WorkplaceContext("P", "S", "L", "B", "1")),
            JobPlacement(3, "old", WorkplaceContext("P", "S", "L", "A", "4")),
            JobPlacement(4, "J", WorkplaceContext("P", "S", "L", "A", "5"), False),
            JobPlacement(5, "J", WorkplaceContext("Q", "S", "L", "A", "3")),
        ),
        (
            WorkerJobAssignment(1, WorkerContext("p", "W1", first), 1),
            WorkerJobAssignment(
                2,
                WorkerContext("p", "W2", WorkplaceContext("P", "S", "L", "A", "2")),
                None,
            ),
            WorkerJobAssignment(
                3,
                WorkerContext("p", "W3", WorkplaceContext("P", "S", "L", "A", "6")),
                None,
                False,
            ),
            WorkerJobAssignment(
                4,
                WorkerContext("p", "W4", WorkplaceContext("Q", "S", "L", "A", "7")),
                None,
            ),
        ),
    )
    assert plant_shift_count(catalog, "P") == 2
    assert plant_shift_count(catalog, "Q") == 2
    assert plant_shift_count(catalog, "Unknown") == 0


def test_plant_usage_count_refreshes_on_job_history_without_storing_cache(
    tmp_path: Path,
) -> None:
    """A Job workplace makes a shift in use; shared Undo removes that derived usage.

    Args:
        tmp_path: Disposable native workspace and organization form directory.

    Returns:
        None. Existing Job and hierarchy authority stays valid across count queries.
    """
    from dataclasses import replace
    from unittest.mock import patch

    from PyQt5.QtWidgets import QMessageBox

    from ergotools.domain.assessments.context import WorkplaceContext
    from ergotools.domain.job_catalog import Job, JobPlacement

    dialog = organization_editing_dialog(tmp_path, OrganizationKind.PLANT)
    workspace = dialog._workspace
    try:
        snapshot = workspace.read_jobs()
        jobs = replace(
            snapshot.jobs,
            jobs=(Job("J", "Job"),),
            placements=(
                JobPlacement(
                    1, "J", WorkplaceContext("Plant", "Section", "Line", "ST01", "1")
                ),
            ),
        )
        workspace.replace_jobs(snapshot, jobs)
        # Project the existing Job edit as when Organization opens after Job management.
        dialog.restore_project_entities()
        _APP.processEvents()
        assert workspace.plant_shift_count("Plant") == 1
        assert dialog.plant_shift_count.text() == "1"
        with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
            QTest.mouseClick(dialog.project_history.undo_button, Qt.LeftButton)
        _APP.processEvents()
        assert dialog.plant_shift_count.text() == "0"
        QTest.mouseClick(dialog.project_history.redo_button, Qt.LeftButton)
        _APP.processEvents()
        assert dialog.plant_shift_count.text() == "1"
        assert all(
            "number_of_shifts" not in dict(record.attributes)
            for record in dialog._snapshot.hierarchy.organization
        )
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)

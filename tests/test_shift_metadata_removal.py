"""Recurring shifts exclude dated incidents in UI, domain and native persistence.

Test layer. Obsolete catalogs are built only in pytest-owned copies. Conversion must
remove exactly the two rejected Shift attributes, preserve every other database row
and source/result byte, leave the input untouched and reject unrelated corruption.
"""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from ergotools.application.settings import Language
from ergotools.domain.organization_record import OrganizationKind, OrganizationRecord
from ergotools.infrastructure.project_migration import ExternalProjectMigration
from tests.test_organization_management import organization_editing_dialog
from tools.project_migration.ergotools_migration.previous_project import (
    remove_obsolete_organization_fields,
    upgrade_previous_project,
)

# These fields describe dated occurrences, not a recurring project-wide shift.
REMOVED_FIELDS = ("incidents_reported", "ergonomic_risk_events")


@pytest.mark.parametrize("field", REMOVED_FIELDS)
def test_recurring_shift_rejects_event_attributes(field: str) -> None:
    """Prohibit rejected metadata from entering a new domain snapshot.

    Args:
        field: One explicitly removed optional event field.

    Returns:
        None. Even an empty obsolete field is rejected rather than stored.
    """
    with pytest.raises(ValueError, match="Unknown or duplicate"):
        OrganizationRecord(OrganizationKind.SHIFT, ("1",), ((field, None),))


@pytest.mark.parametrize("language", (Language.ENGLISH, Language.SPANISH))
def test_shift_form_has_only_recurring_metadata(
    tmp_path: Path, language: Language
) -> None:
    """Keep clock, description and notes controls while removing both event editors.

    Args:
        tmp_path: Disposable project directory owned by pytest.
        language: Current English or Spanish organization form language.

    Returns:
        None. Both localized forms use the same reduced typed field contract.
    """
    dialog = organization_editing_dialog(tmp_path, OrganizationKind.SHIFT, language)
    try:
        assert not set(REMOVED_FIELDS).intersection(dialog.editors)
        assert {
            "description",
            "start_time",
            "end_time",
            "notes",
        } <= dialog.editors.keys()
    finally:
        dialog.close()
        dialog._workspace.close()


@pytest.mark.parametrize("version", (14, 15, 16, 17))
@pytest.mark.parametrize("value", (None, "Owner-requested removal"))
def test_previous_shift_event_removal_preserves_other_data(
    tmp_path: Path, version: int, value: str | None
) -> None:
    """Upgrade obsolete metadata without recalculation or unrelated SQL changes.

    Args:
        tmp_path: Disposable conversion source and destination directory.
        version: Earlier exact-result native metadata version.
        value: Empty or populated rejected value, both explicitly removed.

    Returns:
        None. The old source remains byte-identical; output opens directly and all
        unrelated rows, including tasks, results, images and schemes, remain exact.
    """
    fixture = Path("test_projects/native/comparative_risk_test.ergprj")
    source, destination = tmp_path / "old.ergprj", tmp_path / "new.ergprj"
    with (
        closing(
            sqlite3.connect(fixture.resolve().as_uri() + "?mode=ro", uri=True)
        ) as original,
        closing(sqlite3.connect(source)) as copy,
    ):
        original.backup(copy)
        with copy:
            copy.execute("UPDATE project_metadata SET version=?", (version,))
            payload = json.loads(
                copy.execute("SELECT payload FROM work_catalog").fetchone()[0]
            )
            for record in payload["hierarchy"]["organization"]:
                if record["kind"] == "Shift":
                    record["attributes"] = [
                        pair
                        for pair in record["attributes"]
                        if pair[0] not in REMOVED_FIELDS
                    ]
                    record["attributes"].extend(
                        (field, value) for field in REMOVED_FIELDS
                    )
            copy.execute("UPDATE work_catalog SET payload=?", (json.dumps(payload),))
        tables = [
            row[0]
            for row in copy.execute("SELECT name FROM sqlite_master WHERE type='table'")
            if row[0] not in ("project_metadata", "work_catalog")
        ]
        before = {
            table: copy.execute(f'SELECT * FROM "{table}"').fetchall()
            for table in tables
        }
    original_bytes = source.read_bytes()
    migration = ExternalProjectMigration()
    assert migration.requires_conversion(str(source))
    with upgrade_previous_project(source, destination) as project:
        assert project.format_version == 19
        assert all(
            not set(REMOVED_FIELDS).intersection(dict(record.attributes))
            for record in project.load_hierarchy().organization
        )
    assert source.read_bytes() == original_bytes
    assert not migration.requires_conversion(str(destination))
    with closing(sqlite3.connect(destination)) as converted:
        assert {
            table: converted.execute(f'SELECT * FROM "{table}"').fetchall()
            for table in tables
        } == before
        result = json.loads(
            converted.execute("SELECT payload FROM work_catalog").fetchone()[0]
        )
    expected = json.loads(json.dumps(payload))
    for record in expected["hierarchy"]["organization"]:
        if record["kind"] == "Shift":
            record["attributes"] = [
                pair for pair in record["attributes"] if pair[0] not in REMOVED_FIELDS
            ]
    assert result == expected


def test_shift_field_removal_requires_transaction_and_valid_catalog(
    tmp_path: Path,
) -> None:
    """Reject unrelated fields and missing transaction without partially editing SQL.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None. Caller rollback retains the complete previous catalog on failure.
    """
    source = Path("test_projects/native/comparative_risk_test.ergprj")
    with (
        closing(
            sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)
        ) as original,
        closing(sqlite3.connect(tmp_path / "copy.ergprj")) as connection,
    ):
        original.backup(connection)
        with pytest.raises(RuntimeError, match="transaction"):
            remove_obsolete_organization_fields(connection)
        payload = json.loads(
            connection.execute("SELECT payload FROM work_catalog").fetchone()[0]
        )
        shift = next(
            item
            for item in payload["hierarchy"]["organization"]
            if item["kind"] == "Shift"
        )
        shift["attributes"].extend(
            ((REMOVED_FIELDS[0], "remove"), ("unrelated_unknown_field", "retain error"))
        )
        with connection:
            connection.execute(
                "UPDATE work_catalog SET payload=?", (json.dumps(payload),)
            )
        before = connection.execute("SELECT payload FROM work_catalog").fetchone()
        with pytest.raises(ValueError, match="Unknown or duplicate"), connection:
            connection.execute("BEGIN IMMEDIATE")
            remove_obsolete_organization_fields(connection)
        assert (
            connection.execute("SELECT payload FROM work_catalog").fetchone() == before
        )

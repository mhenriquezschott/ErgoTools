"""Original XML, portable companion paths and strictly read-only source lifetime.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from tools.project_migration.ergotools_migration.legacy_project import (
    LegacyProject,
    read_legacy_descriptor,
)


@pytest.fixture
def legacy(tmp_path: Path) -> Path:
    """Build a tiny source schema with no dependency on the reference checkout.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        Disposable original descriptor path with a tiny companion schema; no reference
        checkout access is required.
    """
    (tmp_path / "data").mkdir()
    with (
        closing(sqlite3.connect(tmp_path / "data" / "source.db")) as connection,
        connection,
    ):
        connection.executescript(
            "PRAGMA user_version=8;"
            "CREATE TABLE Worker(id TEXT PRIMARY KEY, first_name TEXT);"
            "INSERT INTO Worker VALUES ('ñ',NULL),('w','Ada');"
        )
    path = tmp_path / "source.ergprj"
    path.write_text(
        "<ErgoProject><Name>Original ñ</Name><Description>Details</Description>"
        "<Date>2025-02-04</Date><Time>21:23:53</Time>"
        "<DataPath>data</DataPath><DatabaseName>source.db</DatabaseName>"
        "<DatabasePath>obsolete.db</DatabasePath><ImagesPath>images</ImagesPath>"
        "<Language>Spanish</Language><MeasurementSystem>Imperial</MeasurementSystem>"
        "</ErgoProject>",
        encoding="utf-8",
    )
    return path


def test_descriptor_read_snapshot_and_close(legacy: Path) -> None:
    """Use original DataPath/DatabaseName precedence; retain exact optional data.

    Args:
        legacy: Disposable original descriptor/database fixture built without importing
            the reference application.

    Returns:
        None.
    """
    descriptor = read_legacy_descriptor(legacy, "destination")
    assert descriptor.metadata.language is Language.SPANISH
    assert descriptor.metadata.default_units is MeasurementSystem.IMPERIAL
    assert descriptor.metadata.created_at.isoformat() == "2025-02-04T21:23:53"
    before = descriptor.database_path.read_bytes(), legacy.read_bytes()
    with LegacyProject(descriptor) as project:
        rows = project.rows("Worker", order=("id",))
        assert rows[0]["first_name"] == "Ada" and rows[1]["first_name"] is None
        with pytest.raises(TypeError):
            rows[0]["id"] = "changed"
        assert project.inventory().table_counts == (("Worker", 2),)
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            project._connection.execute("DELETE FROM Worker")
        for table, order in [("missing", ()), ("Worker", ("missing",))]:
            with pytest.raises(ValueError):
                project.rows(table, order=order)
    assert (descriptor.database_path.read_bytes(), legacy.read_bytes()) == before
    with pytest.raises(sqlite3.ProgrammingError):
        project.rows("Worker")


@pytest.mark.parametrize(
    "old,new",
    [
        ("ErgoProject", "Other"),
        ("<Name>", "<Name>duplicate</Name><Name>"),
        ("<DataPath>data", "<DataPath>../outside"),
        ("<DataPath>data", "<DataPath>C:\\outside"),
        ("<DatabaseName>source.db", "<DatabaseName>"),
        ("Imperial", "Unknown"),
        ("Spanish", "Unknown"),
        ("21:23:53", "invalid"),
    ],
)
def test_invalid_descriptor_is_not_guessed(legacy: Path, old: str, new: str) -> None:
    """Reject ambiguous identities, unknown defaults and nonportable paths.

    Args:
        legacy: Disposable original descriptor/database fixture built without importing
            the reference application.
        old: Original serialized/text value before the test-only mutation.
        new: Replacement serialized/text value for the test-only mutation.

    Returns:
        None.
    """
    legacy.write_text(legacy.read_text().replace(old, new))
    with pytest.raises(ValueError):
        read_legacy_descriptor(legacy, "p")


def test_windows_separators_missing_database_and_unsupported_schema(
    legacy: Path,
) -> None:
    """Do not create a missing SQLite file or run old-schema migrations.

    Args:
        legacy: Disposable original descriptor/database fixture built without importing
            the reference application.

    Returns:
        None.
    """
    legacy.write_text(
        legacy.read_text().replace("data</DataPath>", "data\\.</DataPath>")
    )
    descriptor = read_legacy_descriptor(legacy, "p")
    with closing(sqlite3.connect(descriptor.database_path)) as connection, connection:
        connection.execute("PRAGMA user_version=7")
    before = descriptor.database_path.read_bytes()
    with pytest.raises(ValueError, match="version 8"):
        LegacyProject(descriptor)
    assert descriptor.database_path.read_bytes() == before
    descriptor.database_path.unlink()
    with pytest.raises(sqlite3.OperationalError):
        LegacyProject(descriptor)
    assert not descriptor.database_path.exists()


def test_serialized_wal_evidence_uses_the_open_read_snapshot(legacy: Path) -> None:
    """Capture committed WAL pages and exclude later writes on another handle.

    Args:
        legacy: Disposable original descriptor/database fixture built without importing
            the reference application.

    Returns:
        None.
    """
    from tools.project_migration.ergotools_migration.legacy_evidence import (
        LegacyEvidence,
    )

    descriptor = read_legacy_descriptor(legacy, "p")
    with closing(sqlite3.connect(descriptor.database_path)) as writer:
        assert writer.execute("PRAGMA journal_mode=WAL").fetchone() == ("wal",)
        writer.execute("CREATE TABLE UnmappedEvidence(id INTEGER,raw BLOB)")
        writer.execute("INSERT INTO UnmappedEvidence VALUES (1,?)", (b"\x00\xff",))
        writer.commit()
        with LegacyProject(descriptor) as project:
            assert project.rows("UnmappedEvidence")[0]["raw"] == b"\x00\xff"
            writer.execute("INSERT INTO UnmappedEvidence VALUES (2,?)", (b"later",))
            writer.commit()
            snapshot = project.database_snapshot()
            evidence = LegacyEvidence(descriptor.original_xml, snapshot)
        assert evidence.database == snapshot
        # This decoding copy mirrors SQLite's documented deserialize limitation:
        # a WAL header needs sidecars. The archived bytes themselves stay exact.
        with closing(sqlite3.connect(":memory:")) as recovered:
            recovered.deserialize(snapshot[:18] + b"\x01\x01" + snapshot[20:])
            assert recovered.execute("SELECT * FROM UnmappedEvidence").fetchall() == [
                (1, b"\x00\xff")
            ]
        assert writer.execute("SELECT COUNT(*) FROM UnmappedEvidence").fetchone() == (
            2,
        )

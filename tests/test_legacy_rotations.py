"""Saved JROT exact frozen evidence, original modes and invalid-grid rejection.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from ergotools.domain.rotation_scheme import RotationMode
from tests.test_legacy_catalogs import legacy_catalog as legacy_catalog
from tools.project_migration.ergotools_migration.legacy_catalogs import (
    read_legacy_catalogs,
)
from tools.project_migration.ergotools_migration.legacy_project import (
    LegacyProject,
    read_legacy_descriptor,
)
from tools.project_migration.ergotools_migration.legacy_rotations import (
    read_legacy_rotations,
)


@pytest.fixture
def rotated(legacy_catalog: Path) -> Path:
    """Use a scoped closed assignment and retired exact risk version, not successors.

    Args:
        legacy_catalog: Disposable original-shape catalog fixture used only by the
            external converter tests.

    Returns:
        Disposable original descriptor path retaining exact scoped JROT, closed
        assignment and retired risk-version links.
    """
    path = read_legacy_descriptor(legacy_catalog, "p").database_path
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.executescript(
            "INSERT INTO RotationScheme(id,name,num_workers,num_timeblocks,"
            "optimization_mode,primary_tool_id,description) VALUES "
            "('R-ñ','Original',1,2,'single_tool','LiFFT','Notes');"
            "INSERT INTO RotationSchemeScope VALUES ('R-ñ',10);"
            "INSERT INTO RotationTarget VALUES (60,'R-ñ','j',20,40);"
            "INSERT INTO RotationAssignment VALUES "
            "('R-ñ',0,'w',30,60),('R-ñ',1,'w',30,60);"
        )
    return legacy_catalog


@pytest.mark.parametrize(
    "mode,primary", [("manual", None), ("single_tool", "LiFFT"), ("all_tools", None)]
)
def test_saved_modes_and_historical_links(
    rotated: Path, mode: str, primary: str | None
) -> None:
    """Retain arrangements and invalidate optimization based on superseded values.

    Args:
        rotated: Disposable original-format fixture containing frozen
            JROT/profile/assignment links.
        mode: Parametrized workflow mode selecting the stated copy/move/cancel or
            display scenario.
        primary: Explicit primary-tool provenance, or None for an unknown/manual source.

    Returns:
        None.
    """
    descriptor = read_legacy_descriptor(rotated, "p")
    with closing(sqlite3.connect(descriptor.database_path)) as connection, connection:
        connection.execute(
            "UPDATE RotationScheme SET optimization_mode=?,primary_tool_id=?",
            (mode, primary),
        )
    before = descriptor.database_path.read_bytes()
    with LegacyProject(descriptor) as project:
        result = read_legacy_rotations(project, read_legacy_catalogs(project))
    (scheme,) = result.schemes
    assert scheme.mode is RotationMode.MANUAL
    assert scheme.primary_kind is None
    assert scheme.workers[0].assignment_id == 30
    assert scheme.targets[0].job_id == "j" and scheme.targets[0].placement_id == 20
    assert scheme.current[0].target_keys == (scheme.targets[0].key,) * 2
    assert scheme.scope[0].station_id == "1" and scheme.description == "Notes"
    assert result.original_targets[0]["id"] == 60
    assert descriptor.database_path.read_bytes() == before


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM RotationAssignment WHERE block_index=1",
        "UPDATE RotationAssignment SET worker_assignment_id=31 WHERE block_index=1",
        "UPDATE RotationScheme SET primary_tool_id=NULL",
        "UPDATE RotationTarget SET job_id='missing' WHERE id=60",
    ],
)
def test_invalid_saved_rotation_is_not_repaired(rotated: Path, sql: str) -> None:
    """Reject holes, changing owners, false provenance and foreign Job references.

    Args:
        rotated: Disposable original-format fixture containing frozen
            JROT/profile/assignment links.
        sql: Explicit test-only SQL statement used for controlled schema/trigger
            corruption.

    Returns:
        None.
    """
    descriptor = read_legacy_descriptor(rotated, "p")
    with closing(sqlite3.connect(descriptor.database_path)) as connection, connection:
        connection.execute(sql)
    before = descriptor.database_path.read_bytes()
    with pytest.raises(ValueError), LegacyProject(descriptor) as project:
        read_legacy_rotations(project, read_legacy_catalogs(project))
    assert descriptor.database_path.read_bytes() == before

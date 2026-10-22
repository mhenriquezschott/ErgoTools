"""Old/versioned agreement, exact recovery ownership and blocking conflicts.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from tests.test_legacy_catalogs import legacy_catalog as legacy_catalog
from tools.project_migration.ergotools_migration.legacy_assessments import (
    read_legacy_assessments,
)
from tools.project_migration.ergotools_migration.legacy_catalogs import (
    read_legacy_catalogs,
)
from tools.project_migration.ergotools_migration.legacy_project import (
    LegacyProject,
    read_legacy_descriptor,
)
from tools.project_migration.ergotools_migration.legacy_reconciliation import (
    LegacyReconciliation,
    reconcile_legacy_assessments,
)


@pytest.fixture
def old_source(legacy_catalog: Path) -> Path:
    """Create one unversioned LiFFT record with two rows and an exact active owner.

    Args:
        legacy_catalog: Disposable original-shape catalog fixture used only by the
            external converter tests.

    Returns:
        Disposable original descriptor path with one unversioned LiFFT source and exact
        active ownership.
    """
    descriptor = read_legacy_descriptor(legacy_catalog, "p")
    with closing(sqlite3.connect(descriptor.database_path)) as connection, connection:
        connection.executescript(
            "INSERT INTO WorkerStationShiftErgoTool(worker_id,plant_name,section_name,"
            "line_name,station_id,shift_id,tool_id,unit,total_cumulative_damage,"
            "probability_outcome) VALUES "
            "('w','P','S','L','1','Day','LiFFT','Metric',0,0);"
            "INSERT INTO LifftResults(worker_id,plant_name,section_name,line_name,"
            "station_id,shift_id,tool_id,task_id,lever_arm,load,moment,repetitions,"
            "cumulative_damage,percentage_total) VALUES "
            "('w','P','S','L','1','Day','LiFFT',1,10,20,20,100,0,0),"
            "('w','P','S','L','1','Day','LiFFT',5,NULL,NULL,NULL,NULL,NULL,NULL);"
        )
    return legacy_catalog


def read_plan(path: Path) -> LegacyReconciliation:
    """Read on one source snapshot with the existing reviewed history/catalogs.

    Args:
        path: Disposable test file path; the caller controls creation and cleanup.

    Returns:
        Typed reconciliation plan read from one source snapshot, including exact
        recoverable ownership/conflicts.
    """
    with LegacyProject(read_legacy_descriptor(path, "p")) as project:
        catalogs = read_legacy_catalogs(project)
        return reconcile_legacy_assessments(
            project, catalogs, read_legacy_assessments(project, catalogs)
        )


def test_recover_exact_owner_and_deterministic_id(old_source: Path) -> None:
    """Recover missing history, without new ownership or zero-filling blank rows.

    Args:
        old_source: Disposable original-format fixture containing unversioned LiFFT rows
            and exact saved ownership.

    Returns:
        None.
    """
    path = read_legacy_descriptor(old_source, "p").database_path
    before = path.read_bytes()
    plan = read_plan(old_source)
    assert not plan.conflicts and plan.matched_summaries == 0
    (record,) = plan.recovered
    assert record.ownership.assignment_id == 31
    assert [t.task_id for t in record.source.tasks] == [
        "legacy-task-1",
        "legacy-task-5",
    ]
    assert record.source.tasks[1].lever_arm is None
    assert record.summary["probability_outcome"] == 0
    assert read_plan(old_source) == plan
    assert path.read_bytes() == before


def test_matching_history_is_not_imported_twice(old_source: Path) -> None:
    """Existing current source and evidence must match before old tables are ignored.

    Args:
        old_source: Disposable original-format fixture containing unversioned LiFFT rows
            and exact saved ownership.

    Returns:
        None.
    """
    path = read_legacy_descriptor(old_source, "p").database_path
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.executescript(
            "INSERT INTO IndividualAssessment(id,worker_assignment_id,tool_id,"
            "version,status,is_current,unit,total_cumulative_damage,probability_outcome)"
            " VALUES (50,31,'LiFFT',1,'complete',1,'Metric',0,0);"
            "INSERT INTO LiFFTAssessmentTask SELECT 50,task_id,lever_arm,load,moment,"
            "repetitions,cumulative_damage,percentage_total FROM LifftResults;"
        )
    plan = read_plan(old_source)
    assert not plan.recovered and not plan.conflicts and plan.matched_summaries == 1
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("UPDATE LiFFTAssessmentTask SET load=999 WHERE task_index=1")
    before = path.read_bytes()
    plan = read_plan(old_source)
    assert (
        not plan.recovered
        and plan.conflicts[0].reason == "Old/current evidence differs."
    )
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "sql,reason",
    [
        ("UPDATE WorkerAssignment SET active=0", "No unique active assignment."),
    ],
)
def test_no_inferred_ownership_or_discarded_orphans(
    old_source: Path, sql: str, reason: str
) -> None:
    """Incomplete/ambiguous source relationships block a complete conversion.

    Args:
        old_source: Disposable original-format fixture containing unversioned LiFFT rows
            and exact saved ownership.
        sql: Explicit test-only SQL statement used for controlled schema/trigger
            corruption.
        reason: Expected diagnostic fragment identifying why the malformed input is
            rejected.

    Returns:
        None.
    """
    path = read_legacy_descriptor(old_source, "p").database_path
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(sql)
    plan = read_plan(old_source)
    assert not plan.recovered and plan.conflicts[0].reason == reason


def test_orphan_old_tasks_fail_source_preflight(old_source: Path) -> None:
    """Source foreign-key validation blocks orphan tasks before reconciliation.

    Args:
        old_source: Disposable original-format fixture containing unversioned LiFFT rows
            and exact saved ownership.

    Returns:
        None.
    """
    path = read_legacy_descriptor(old_source, "p").database_path
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("DELETE FROM WorkerStationShiftErgoTool")
    before = path.read_bytes()
    with pytest.raises(ValueError, match="orphaned"):
        read_plan(old_source)
    assert path.read_bytes() == before

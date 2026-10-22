"""Exact legacy catalog links, lifecycle, absence and original measurement units.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
from collections.abc import Callable
from contextlib import closing
from pathlib import Path

import pytest

from ergotools.domain.assessments.document import AssessmentKind
from tools.project_migration.ergotools_migration.legacy_catalogs import (
    read_legacy_catalogs,
)
from tools.project_migration.ergotools_migration.legacy_project import (
    LegacyProject,
    read_legacy_descriptor,
)
from tools.project_migration.ergotools_migration.legacy_values import (
    legacy_flag,
    legacy_integer,
    legacy_kind,
    legacy_number,
    legacy_text,
)


@pytest.fixture
def legacy_catalog(tmp_path: Path) -> Path:
    """Seed a source-shaped schema with closed/current owners and risk versions.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        Disposable original descriptor path whose companion database contains exact
        synthetic closed/current catalogs.
    """
    path = tmp_path / "source.ergprj"
    path.write_text(
        "<ErgoProject><Name>Source ñ</Name><DataPath>data</DataPath>"
        "<DatabaseName>source.db</DatabaseName>"
        "<MeasurementSystem>Imperial</MeasurementSystem></ErgoProject>"
    )
    (tmp_path / "data").mkdir()
    with (
        closing(sqlite3.connect(tmp_path / "data/source.db")) as connection,
        connection,
    ):
        connection.executescript(
            (Path(__file__).parent / "fixtures/legacy_v8.sql").read_text()
        )
        connection.execute("PRAGMA foreign_keys=ON")
        connection.executescript(
            "INSERT INTO Worker(id,first_name,last_name,height,weight,year_of_birth,"
            "month_of_birth,day_of_birth) VALUES ('w','Ada','ñ',170,0,2000,2,29);"
            "INSERT INTO Worker(id) VALUES ('x');"
            "INSERT INTO Plant(name,description) VALUES ('P','Original plant');"
            "INSERT INTO Section(plant_name,name) VALUES ('P','S');"
            "INSERT INTO Line(plant_name,section_name,name) VALUES ('P','S','L');"
            "INSERT INTO Station(plant_name,section_name,line_name,id) "
            "VALUES ('P','S','L','1');"
            "INSERT INTO Shift(id) VALUES ('Day');"
            "INSERT INTO ErgoTool(id,name) VALUES "
            "('LiFFT','LiFFT'),('DUET','DUET'),('ST','ST');"
            "INSERT INTO WorkplaceContext VALUES (10,'P','S','L','1','Day');"
            "INSERT INTO Job(id,name,description,active) VALUES ('j','Original job',"
            "NULL,1);"
            "INSERT INTO JobPlacement(id,job_id,workplace_context_id,active) "
            "VALUES (20,'j',10,1);"
            "INSERT INTO WorkerAssignment(id,worker_id,workplace_context_id,"
            "job_placement_id,active,started_at,ended_at) "
            "VALUES (30,'w',10,20,0,'2024-01-01','2024-12-31'),"
            "(31,'w',10,NULL,1,'2025-01-01',NULL);"
            "INSERT INTO JobRiskProfile(id,job_id,name,version,status,is_current,"
            "source_type) VALUES (40,'j','Old',1,'retired',0,'expert'),"
            "(41,'j','Current',2,'approved',1,'imported');"
            "INSERT INTO JobRiskMeasurement(profile_id,tool_id,"
            "total_cumulative_damage,probability_outcome,unit) "
            "VALUES (40,'LiFFT',0,0,'Imperial'),(41,'LiFFT',.2,80,'Metric'),"
            "(41,'DUET',NULL,NULL,NULL);"
        )
    return path


def test_catalogs_keep_selected_values_links_units_and_absence(
    legacy_catalog: Path,
) -> None:
    """Declared project units normalize body values without relabeling risk units.

    Args:
        legacy_catalog: Disposable original-shape catalog fixture used only by the
            external converter tests.

    Returns:
        None.
    """
    descriptor = read_legacy_descriptor(legacy_catalog, "p")
    before = descriptor.database_path.read_bytes()
    with LegacyProject(descriptor) as project:
        result = read_legacy_catalogs(project)
    worker, missing = result.hierarchy.work.workers
    assert worker.details.birth_date == "2000-02-29"
    assert worker.details.height_cm == 170 * 2.54 and worker.details.weight_kg == 0
    assert missing.first_name is None and missing.details.height_cm is None
    assert result.jobs.assignments[0].assignment_id == 30
    assert not result.jobs.assignments[0].active
    assert result.jobs.assignments[0].placement_id == 20
    assert result.jobs.assignments[1].placement_id is None
    assert len(result.risks.values) == 1
    current = result.risks.for_job("j")
    measurements = {m.kind: m for m in current.measurements}
    assert measurements[AssessmentKind.LIFFT].unit == "Metric"
    assert measurements[AssessmentKind.DUET].probability_percent is None
    assert any(
        ("description", "Original plant") in record.attributes
        for record in result.hierarchy.organization
    )
    assert descriptor.database_path.read_bytes() == before


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE Worker SET month_of_birth=NULL WHERE id='w'",
        "UPDATE Worker SET gender='unknown' WHERE id='w'",
        "UPDATE JobRiskProfile SET is_current=1 WHERE id=40",
    ],
)
def test_invalid_source_catalogs_fail_without_repair(
    legacy_catalog: Path, sql: str
) -> None:
    """Reject incomplete dates, invalid metadata and ambiguous profile lifecycles.

    Args:
        legacy_catalog: Disposable original-shape catalog fixture used only by the
            external converter tests.
        sql: Explicit test-only SQL statement used for controlled schema/trigger
            corruption.

    Returns:
        None.
    """
    descriptor = read_legacy_descriptor(legacy_catalog, "p")
    with closing(sqlite3.connect(descriptor.database_path)) as connection, connection:
        connection.execute(sql)
    before = descriptor.database_path.read_bytes()
    with LegacyProject(descriptor) as project, pytest.raises(ValueError):
        read_legacy_catalogs(project)
    assert descriptor.database_path.read_bytes() == before


@pytest.mark.parametrize(
    "reader,value",
    [
        (legacy_integer, 1.5),
        (legacy_integer, True),
        (legacy_number, float("inf")),
        (legacy_number, "2"),
        (legacy_flag, 2),
        (legacy_kind, "shoulder"),
        (legacy_text, None),
    ],
)
def test_strict_legacy_boundaries(
    reader: Callable[[object], object], value: object
) -> None:
    """Malformed source storage cannot silently become a plausible domain value.

    Args:
        reader: Injected read operation under test; source/connection lifetime stays
            with the caller.
        value: Parametrized valid/invalid boundary value; expected acceptance is
            asserted before publication.

    Returns:
        None.
    """
    with pytest.raises(ValueError):
        reader(value)

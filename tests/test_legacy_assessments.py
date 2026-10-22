"""Historical source/evidence identity with no calculation or ST direction guessing.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.model_units import MeasurementSystem
from tests.test_legacy_catalogs import legacy_catalog as legacy_catalog
from tools.project_migration.ergotools_migration.legacy_assessments import (
    LegacyShoulderSource,
    read_legacy_assessments,
)
from tools.project_migration.ergotools_migration.legacy_catalogs import (
    read_legacy_catalogs,
)
from tools.project_migration.ergotools_migration.legacy_project import (
    LegacyProject,
    read_legacy_descriptor,
)


@pytest.fixture
def historical(legacy_catalog: Path) -> Path:
    """Retain a superseded closed-owner record and current three-tool sources.

    Args:
        legacy_catalog: Disposable original-shape catalog fixture used only by the
            external converter tests.

    Returns:
        Disposable original-format project path retaining superseded ownership and
        current three-tool source rows.
    """
    path = read_legacy_descriptor(legacy_catalog, "p").database_path
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.executescript(
            "INSERT INTO IndividualAssessment(id,worker_assignment_id,tool_id,version,"
            "status,is_current,unit,total_cumulative_damage,probability_outcome,notes) "
            "VALUES (50,30,'LiFFT',1,'superseded',0,'Metric',0,0,'old'),"
            "(51,31,'LiFFT',2,'complete',1,'Imperial',.25,80,'current'),"
            "(52,31,'DUET',1,'draft',1,NULL,NULL,NULL,NULL),"
            "(53,31,'ST',1,'complete',1,'Metric',.2,90,NULL);"
            "INSERT INTO LiFFTAssessmentTask(individual_assessment_id,task_index,"
            "lever_arm,load,moment,repetitions,cumulative_damage,percentage_total) "
            "VALUES (50,0,0,0,0,0,0,0),(51,2,12,20,20,100,.25,100),"
            "(51,5,NULL,NULL,NULL,NULL,NULL,NULL);"
            "INSERT INTO DUETAssessmentTask(individual_assessment_id,task_index,"
            "omni_res_scale,repetitions,cumulative_damage,percentage_total) "
            "VALUES (52,0,0,0,0,0),(52,1,NULL,'',NULL,NULL);"
            "INSERT INTO ShoulderAssessmentTask(individual_assessment_id,task_index,"
            "type_of_task,lever_arm,load,repetitions,moment,cumulative_damage) "
            "VALUES (53,0,0,10,20,100,20,.1),(53,1,1,10,20,100,20,.1),"
            "(53,2,2,'','','',20,0);"
        )
    return legacy_catalog


def test_history_sources_and_cached_evidence_are_distinct(historical: Path) -> None:
    """Preserve every row/index/unit/owner, without making old results fresh.

    Args:
        historical: Disposable source fixture with closed/current assignment versions;
            not a native compatibility mode.

    Returns:
        None.
    """
    descriptor = read_legacy_descriptor(historical, "p")
    before = descriptor.database_path.read_bytes()
    with LegacyProject(descriptor) as project:
        assessments = read_legacy_assessments(project, read_legacy_catalogs(project))
    old, current, duet, shoulder = assessments
    assert old.source_id == 50 and old.ownership.assignment_id == 30
    assert (
        isinstance(old.source, LifftDraft)
        and old.source.system is MeasurementSystem.METRIC
    )
    assert old.source.tasks[0].repetitions == 0 and old.probability_percent == 0
    assert isinstance(current.source, LifftDraft)
    assert current.source.system is MeasurementSystem.IMPERIAL
    assert [task.task_id for task in current.source.tasks] == [
        "legacy-task-2",
        "legacy-task-5",
    ]
    assert current.source.tasks[1].lever_arm is None
    assert current.task_evidence[0].moment == 20
    assert current.task_evidence[0].cumulative_damage == 0.25
    assert current.task_evidence[1].cumulative_damage is None
    assert current.notes == "current" and current.unit == "Imperial"
    assert isinstance(duet.source, DuetDraft)
    assert duet.source.tasks[0].omni_res_scale == 0
    assert (
        duet.source.tasks[1].omni_res_scale is None and duet.probability_percent is None
    )
    assert isinstance(shoulder.source, LegacyShoulderSource)
    assert [t.selector_index for t in shoulder.source.tasks] == [0, 1, 2]
    assert shoulder.source.tasks[2].lever_arm is None
    assert shoulder.original_tasks[2]["lever_arm"] == ""
    assert duet.source.tasks[1].repetitions is None
    assert duet.original_tasks[1]["repetitions"] == ""
    assert shoulder.task_evidence[2].cumulative_damage == 0
    assert descriptor.database_path.read_bytes() == before


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE IndividualAssessment SET unit=NULL WHERE id=51",
        "UPDATE ShoulderAssessmentTask SET type_of_task=3 WHERE task_index=1",
        "UPDATE DUETAssessmentTask SET repetitions='bad' WHERE task_index=1",
        "INSERT INTO DUETAssessmentTask(individual_assessment_id,task_index) "
        "VALUES (51,0)",
        "UPDATE IndividualAssessment SET worker_assignment_id=31,is_current=1 "
        "WHERE id=50",
    ],
)
def test_bad_history_is_rejected_without_normalizing(
    historical: Path, sql: str
) -> None:
    """Reject missing physical units, unknown ST selectors and wrong-model tasks.

    Args:
        historical: Disposable source fixture with closed/current assignment versions;
            not a native compatibility mode.
        sql: Explicit test-only SQL statement used for controlled schema/trigger
            corruption.

    Returns:
        None.
    """
    descriptor = read_legacy_descriptor(historical, "p")
    with closing(sqlite3.connect(descriptor.database_path)) as connection, connection:
        connection.execute(sql)
    before = descriptor.database_path.read_bytes()
    with LegacyProject(descriptor) as project, pytest.raises(ValueError):
        read_legacy_assessments(project, read_legacy_catalogs(project))
    assert descriptor.database_path.read_bytes() == before

"""Verify single-result precision, invalidation and recalculated native upgrades.

Regression tests own isolated native files. They compare persisted results with the
existing evaluator and known DUET values, exercise probabilities beyond gauge limits,
and prove obsolete duplicate tables cannot enter an upgraded project.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path

import pytest

from ergotools.application.assessments.evaluation import AssessmentEvaluator
from ergotools.application.saved_results import calculate_saved_result, result_snapshot
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.project_migration import ExternalProjectMigration
from ergotools.infrastructure.project_snapshot import ProjectSnapshot
from tests.test_project_snapshot import archived as archived
from tests.test_project_snapshot import legacy_catalog as legacy_catalog
from tests.test_project_snapshot import mapped as mapped
from tests.test_project_snapshot import old_source as old_source
from tests.test_project_snapshot import rotated as rotated
from tests.test_project_snapshot import snapshot as snapshot
from tools.project_migration.ergotools_migration.previous_project import (
    upgrade_previous_project,
)


@pytest.mark.parametrize("scale,repetitions", [(7, 2806), (0, 20), (10, 1_000_000)])
def test_save_keeps_calculator_precision_and_no_gauge_clipping(
    tmp_path: Path, scale: int, repetitions: int
) -> None:
    """Save/reopen/backup retain raw probability and the known 0.98249 damage.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        scale: Dimensionless OMNI-Res selector or explicit invalid boundary value.
        repetitions: Explicit daily repetition count used for the calculator/input
            regression.

    Returns:
        None.
    """
    source = DuetDraft((DuetTask("task", scale, repetitions),))
    key = DocumentKey("p", "d")
    outcome = AssessmentEvaluator().evaluate_duet_grid(DocumentSession(key, source))
    expected = result_snapshot(outcome, MeasurementSystem.IMPERIAL)
    assert expected is not None and outcome.summary is not None
    assert expected.damage == outcome.summary.total_damage
    assert expected.probability_percent == outcome.summary.probability * 100
    if scale == 7:
        assert expected.damage == 0.98249
        assert expected.damage != round(expected.damage, 4)
    else:
        assert expected.probability_percent < 5 or expected.probability_percent > 90
        assert expected.probability_percent not in (0, 100)
    path = tmp_path / "precision.ergprj"
    with AssessmentProjectFile.create_with_document(
        path, ProjectMetadata("p", "Precision", MeasurementSystem.IMPERIAL), "d", source
    ) as project:
        project.save_result(key, expected)
        project.save_result(key, expected)
        with project.snapshot(str(tmp_path / "backup.ergprj"), None, None) as backup:
            assert backup.load_saved_result(key) == expected
    with AssessmentProjectFile.open(path) as project:
        assert project.load_saved_result(key) == expected
        project.save(key, source)
        assert project.load_saved_result(key) == expected
        changed = replace(source, tasks=(replace(source.tasks[0], repetitions=17),))
        project.save(key, changed)
        assert project.load_saved_result(key) is None
        result = calculate_saved_result(key, changed, MeasurementSystem.IMPERIAL)
        assert result is not None
        project.save_result(key, result)
    with closing(sqlite3.connect(path)) as connection:
        (payload,) = connection.execute(
            "SELECT payload FROM saved_assessment_results"
        ).fetchone()
        assert json.loads(payload)["version"] == 3
        assert json.loads(payload)["damage"] == result.damage
        assert connection.execute(
            "SELECT count(*) FROM saved_assessment_results"
        ).fetchone() == (1,)
        assert not connection.execute(
            "SELECT 1 FROM sqlite_master WHERE name='recorded_assessment_results'"
        ).fetchone()


@pytest.mark.parametrize("version", [8, 11, 13])
def test_format13_upgrade_discards_duplicate_and_rounded_outputs(
    archived: ProjectSnapshot, tmp_path: Path, version: int
) -> None:
    """Prior native duplicates are discarded without reading their old payloads.

    Args:
        archived: Prior-format source/result fixture or scenario flag; current native
            output still has one authoritative result.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        version: Explicit historical/native test-format version used to exercise
            acceptance or rejection boundaries.

    Returns:
        None.
    """
    source = tmp_path / "format13.ergprj"
    with AssessmentProjectFile.create_from_snapshot(source, archived):
        pass
    with closing(sqlite3.connect(source)) as connection, connection:
        connection.execute("UPDATE project_metadata SET version=?", (version,))
        connection.execute("CREATE TABLE recorded_assessment_results(payload TEXT)")
        connection.execute(
            "INSERT INTO recorded_assessment_results VALUES ('obsolete')"
        )
        connection.execute(
            "UPDATE saved_assessment_results SET payload=?", ('{"version":1}',)
        )
    before = source.read_bytes()
    assert ExternalProjectMigration().requires_conversion(str(source))
    destination = tmp_path / "single.ergprj"
    with upgrade_previous_project(source, destination) as project:
        assert project.format_version == 19
        for item in archived.assessments:
            key = DocumentKey(project.metadata.project_id, item.ownership.document_id)
            assert project.load_saved_result(key) == calculate_saved_result(
                key, item.source, project.metadata.default_units
            )
    assert source.read_bytes() == before
    with closing(sqlite3.connect(destination)) as connection:
        assert not connection.execute(
            "SELECT name FROM sqlite_master WHERE name='recorded_assessment_results'"
        ).fetchone()


def test_invalid_inputs_cannot_manufacture_migrated_result() -> None:
    """Keep invalid input explicit rather than saving a zero-risk substitute.

    Args:
        None.

    Returns:
        None.
    """
    source = DuetDraft((DuetTask("invalid", 7, -1),))
    assert (
        calculate_saved_result(DocumentKey("p", "d"), source, MeasurementSystem.METRIC)
        is None
    )

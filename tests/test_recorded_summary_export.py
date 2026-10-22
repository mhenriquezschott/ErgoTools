"""Archived CSV fidelity and exact saved-source invalidation regressions.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from ergotools.application.assessment_export import saved_summary_rows
from ergotools.application.assessments.evaluation import (
    AssessmentEvaluator,
    EvaluationStatus,
)
from ergotools.application.saved_results import calculate_saved_result
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.presentation.summary_csv import SUMMARY_HEADERS, summary_csv_table
from tests.test_legacy_catalogs import legacy_catalog as legacy_catalog
from tests.test_legacy_reconciliation import old_source as old_source
from tools.project_migration.ergotools_migration.legacy_conversion import (
    convert_legacy_project,
)
from tools.project_migration.ergotools_migration.legacy_project import (
    read_legacy_descriptor,
)


@pytest.mark.parametrize(
    "damage,percent", [(0, 0), (None, None), (1.23456789, 123.456789)]
)
def test_recorded_export_keeps_absence_zero_precision_and_source_units(
    old_source: Path, tmp_path: Path, damage: float | None, percent: float | None
) -> None:
    """Migration ignores rounded/null/incorrect old outputs and recalculates inputs.

    Args:
        old_source: Disposable original-format fixture containing unversioned LiFFT rows
            and exact saved ownership.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        damage: Dimensionless damage boundary input (or deliberate invalid text) for the
            stated scenario.
        percent: Observed probability percentage or explicit invalid/absent boundary
            case.

    Returns:
        None.
    """
    descriptor = read_legacy_descriptor(old_source, "p")
    with closing(sqlite3.connect(descriptor.database_path)) as connection, connection:
        connection.execute(
            "UPDATE WorkerStationShiftErgoTool SET total_cumulative_damage=?, "
            "probability_outcome=?",
            (damage, percent),
        )
    before = descriptor.database_path.read_bytes()
    target = tmp_path / "converted.ergprj"
    with convert_legacy_project(old_source, target, "p") as project:
        with patch.object(
            AssessmentEvaluator,
            "evaluate_lifft_grid",
            side_effect=AssertionError("must not recalculate"),
        ):
            (row,) = saved_summary_rows(project, AssessmentKind.LIFFT)
        source = project.load(row.document)
        expected = calculate_saved_result(
            row.document, source, project.metadata.default_units
        )
        assert expected is not None
        assert row.status is expected.calculation_status
        assert row.total_damage == expected.damage
        assert row.recorded_probability_percent == expected.probability_percent
        assert project.load_saved_result(row.document) == expected
        table = summary_csv_table((row,), "fixed timestamp")
        fields = dict(zip(SUMMARY_HEADERS, table[1], strict=True))
        assert float(fields["Probability Outcome"]) == expected.probability_percent
        assert float(fields["Total Cumulative Damage"]) == expected.damage
        source = project.load(row.document)
        project.save(
            row.document,
            replace(
                source,
                tasks=(replace(source.tasks[0], repetitions=999), *source.tasks[1:]),
            ),
        )
        (edited,) = saved_summary_rows(project, AssessmentKind.LIFFT)
        assert edited.status is EvaluationStatus.COMPLETE
        assert edited.recorded_probability_percent is None
        assert edited.total_damage is not None and edited.total_damage != damage
        assert project.load_saved_result(row.document) is None
    assert descriptor.database_path.read_bytes() == before


@pytest.mark.parametrize("unit", ["Metric", None, ""])
def test_duet_recorded_units_override_project_default_without_changing_source(
    old_source: Path, tmp_path: Path, unit: str | None
) -> None:
    """Unit-independent DUET still exports its original per-assessment unit label.

    Args:
        old_source: Disposable original-format fixture containing unversioned LiFFT rows
            and exact saved ownership.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        unit: Recorded evidence unit label, or None for a deliberately missing/unknown
            unit case.

    Returns:
        None.
    """
    descriptor = read_legacy_descriptor(old_source, "p")
    with closing(sqlite3.connect(descriptor.database_path)) as connection, connection:
        connection.executescript(
            "DELETE FROM LifftResults;"
            "UPDATE WorkerStationShiftErgoTool SET tool_id='DUET', unit='Metric';"
            "INSERT INTO DuetResults (worker_id,plant_name,section_name,line_name,"
            "station_id,shift_id,tool_id,task_id,omni_res_scale,repetitions,"
            "cumulative_damage,percentage_total) VALUES "
            "('w','P','S','L','1','Day','DUET',1,2,100,0,0);"
        )
        connection.execute("UPDATE WorkerStationShiftErgoTool SET unit=?", (unit,))
    target = tmp_path / "duet-converted.ergprj"
    with convert_legacy_project(old_source, target, "p") as project:
        (row,) = saved_summary_rows(project, AssessmentKind.DUET)
        assert row.status is EvaluationStatus.COMPLETE
        assert row.units is project.metadata.default_units
        expected = calculate_saved_result(
            row.document, project.load(row.document), row.units
        )
        assert project.load_saved_result(row.document) == expected
        fields = dict(
            zip(SUMMARY_HEADERS, summary_csv_table((row,), "fixed")[1], strict=True)
        )
        assert fields["Unit"] == row.units.value.title()

"""Catalog validation scales without dropping saved-reference integrity checks.

Infrastructure tests use disposable native databases and observable SQL work, avoiding
machine-dependent timing assertions. They cover current and proposed catalog references.
"""

from dataclasses import replace
from pathlib import Path

import pytest

from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.rotation_scenario_serialization import encode_scenario
from tests.test_rotation_scenarios import scenario_catalogs, scenario_with_run


def test_catalog_read_queries_do_not_multiply_per_rotation(tmp_path: Path) -> None:
    """A fivefold catalog increase must not multiply nested hierarchy/Job SQL reads.

    Args:
        tmp_path: Private project directory.

    Returns:
        None; all 25 records and every frozen run are still returned exactly, and a
        corrupt reference in the final row remains rejected on the next fresh read.
    """
    hierarchy, jobs, _ = scenario_catalogs()
    with AssessmentProjectFile.create_empty(
        tmp_path / "scaling.ergprj",
        ProjectMetadata("timing", "Scaling", MeasurementSystem.METRIC),
    ) as project:
        project.save_hierarchy(hierarchy)
        project.save_jobs(jobs)
        source = scenario_with_run()
        records = tuple(
            replace(source, scenario_id=f"R{i:02}", name=f"Rotation {i:02}")
            for i in range(25)
        )
        sizes = []
        for index, record in enumerate(records, 1):
            project.replace_rotation_scenario(None, record)
            if index in (5, 25):
                statements: list[str] = []
                project._connection.set_trace_callback(statements.append)
                try:
                    assert project.load_rotation_scenarios() == records[:index]
                finally:
                    project._connection.set_trace_callback(None)
                sizes.append(sum(s.startswith("SELECT") for s in statements))
        assert 0 < sizes[0] <= sizes[1] <= 2 * sizes[0]
        broken = replace(
            records[-1], inputs=replace(records[-1].inputs, shift_id="missing")
        )
        with project._connection:
            project._connection.execute(
                "UPDATE rotation_schemes SET payload=? WHERE scheme_id=?",
                (encode_scenario(broken), broken.scenario_id),
            )
        with pytest.raises(ValueError):
            project.load_rotation_scenarios()

"""Explicit demo generation remains external to normal production JROT opening.

Preserve the former prototype fixture-quality regression after retiring its UI.
Only a disposable target is created; regeneration is exclusive and never overwrites it.
"""

from pathlib import Path

import pytest

from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from tools.create_jrot_demo_project import create_demo, demo_sources


def test_clean_fixture_quality_and_exclusive_regeneration(tmp_path: Path) -> None:
    """The clean meeting fixture has real source rows and no unexplained direct totals.

    Args:
        tmp_path: Private generator target; never overwrite the maintained demo.

    Returns:
        None; sources, demographics and scoped organization survive native reopen.
    """
    target = tmp_path / "new.ergprj"
    create_demo(target)
    baseline = target.read_bytes()
    with pytest.raises(FileExistsError):
        create_demo(target)
    assert target.read_bytes() == baseline
    with AssessmentProjectFile.open(target) as project:
        hierarchy, jobs, risks = (
            project.load_hierarchy(),
            project.load_jobs(),
            project.load_job_risk(),
        )
        assert (
            len(hierarchy.plants),
            len(hierarchy.sections),
            len(hierarchy.lines),
            len(hierarchy.work.stations),
        ) == (2, 4, 8, 24)
        assert hierarchy.work.shifts == ("Day", "Evening")
        assert len(jobs.jobs) == len(hierarchy.work.workers) == 6
        assert {w.worker_id for w in hierarchy.work.workers} == {
            f"W{i:02}" for i in range(1, 7)
        }
        assert all(
            w.first_name
            and w.last_name
            and w.details
            and w.details.sex
            and w.details.birth_date
            for w in hierarchy.work.workers
        )
        assert not project.load_history().entries
        for index, job in enumerate(jobs.jobs):
            values = risks.for_job(job.job_id)
            assert values is not None and len(values.measurements) == 3
            assert tuple(v.source for v in values.measurements) == demo_sources(
                job.job_id, index
            )
            assert all(
                v.complete
                and v.source is not None
                and len(v.source.tasks) == len(v.task_results) == 2
                for v in values.measurements
            )
        assert {p.workplace.shift_id for p in jobs.placements} == {"Day", "Evening"}
    assert target.read_bytes() == baseline

"""M05 native ownership, copy/move, stale consent and project-history contracts.

Use disposable native projects and real core transfer transactions. No desktop,
reference or maintained project is a migration/mutation target.
"""

from dataclasses import replace
from pathlib import Path

import pytest
from assessment_contexts import (
    create_assessment,
    delete_assessment,
    destination_record,
    read_contexts,
    transfer_assessment,
    workplace_label,
)
from assessment_tasks import persist_source, task_from_form
from mobile_assessment import assessment
from mobile_workers import put_worker
from project_session import ProjectSession

from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_catalog import Job, JobCatalog, JobPlacement
from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile


def setup_contexts(tmp_path: Path, kind: AssessmentKind) -> tuple:
    """Prepare two real plants with duplicate station labels and independent shifts.

    Args:
        tmp_path: Disposable session storage.
        kind: Tool under test, independently owned by W01.

    Returns:
        Session, complete source and exact first/second workplaces.
    """
    session = ProjectSession(tmp_path)
    session.create("Contexts", "metric")
    for identity in ("W01", "W02"):
        session.change(
            "Worker",
            lambda identity=identity: put_worker(
                session.working, WorkerEntry(identity)
            ),
        )
    with AssessmentProjectFile.open(session.working) as project:
        hierarchy = project.load_hierarchy()
        stations = (
            StationKey("Harbor Plant", "Packing", "Line A", "ST01"),
            StationKey("Riverside Plant", "Assembly", "Line B", "ST01"),
        )
        work = WorkCatalog(
            project.metadata.project_id,
            hierarchy.work.workers,
            stations,
            ("Day", "Night"),
        )
        project.save_hierarchy(
            WorkHierarchy(
                work,
                ("Harbor Plant", "Riverside Plant"),
                tuple(SectionKey(s.plant_name, s.section_name) for s in stations),
                tuple(
                    LineKey(s.plant_name, s.section_name, s.line_name) for s in stations
                ),
            )
        )
    session.reset_history()
    session.change(
        "Add assessment", lambda: create_assessment(session.working, "W01", kind, None)
    )
    selected = assessment(session.working, "W01", kind=kind)
    row = task_from_form(
        selected["source"].tasks[0],
        {
            "task_name": "Packing",
            "omni_res_scale": "6",
            "direction": "1",
            "lever_arm": "30",
            "load": "49",
            "repetitions": "100",
        },
        {},
    )
    selected = session.change(
        "Input",
        lambda: persist_source(
            session.working, selected, replace(selected["source"], tasks=(row,))
        ),
    )
    return (
        session,
        assessment(session.working, "W01", kind=kind),
        stations[0].at_shift("Day"),
        stations[1].at_shift("Night"),
    )


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_create_replace_delete_and_replay_preserve_other_contexts(
    tmp_path: Path, kind: AssessmentKind
) -> None:
    """Blank sources save independently; replacement/deletion requires exact intent.

    Args:
        tmp_path: Disposable working project.
        kind: Each independent tool.

    Returns:
        None; Undo restores exact source/result/ownership and leaves assignment intact.
    """
    session, standalone, first, second = setup_contexts(tmp_path, kind)
    identity = session.change(
        "Add assessment", lambda: create_assessment(session.working, "W01", kind, first)
    )
    created = assessment(session.working, "W01", identity, kind)
    assert len(created["source"].tasks) == 1 and created["result"] is None
    assert created["context"] == workplace_label(first)
    assert created["job"] == "No Job assigned"
    with pytest.raises(ValueError):
        create_assessment(session.working, "W01", kind, first)
    copy = session.change(
        "Copy assessment",
        lambda: transfer_assessment(
            session.working, standalone, "W01", first, expected=created
        ),
    )
    copied = assessment(session.working, "W01", copy, kind)
    exact = copied["source"], copied["result"]
    session.change(
        "Replace assessment",
        lambda: create_assessment(session.working, "W01", kind, first, expected=copied),
    )
    assert (
        destination_record(read_contexts(session.working), "W01", kind, first)["result"]
        is None
    )
    session.replay()
    restored = destination_record(read_contexts(session.working), "W01", kind, first)
    assert (restored["source"], restored["result"]) == exact
    session.change(
        "Delete assessment", lambda: delete_assessment(session.working, restored)
    )
    assert (
        destination_record(read_contexts(session.working), "W01", kind, first) is None
    )
    assert (
        assessment(session.working, "W01", kind=kind)["result"] == standalone["result"]
    )
    assert len(read_contexts(session.working)["jobs"].assignments) == 1
    session.replay()
    assert assessment(session.working, "W01", copy, kind)["result"] == exact[1]
    session.save()
    session.open_recent(session.active["id"])
    assert assessment(session.working, "W01", copy, kind)["result"] == exact[1]
    assert (
        first.station_id == second.station_id and first.plant_name != second.plant_name
    )


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_copy_move_all_context_directions_and_independent_edits(
    tmp_path: Path, kind: AssessmentKind
) -> None:
    """Transfer standalone↔workplace across workers/plants with exact unchanged results.

    Args:
        tmp_path: Owned native files.
        kind: Current tool only.

    Returns:
        None; same destination rejects; edits to copies never update their originals.
    """
    session, original, first, second = setup_contexts(tmp_path, kind)
    before = session.working.read_bytes()
    with pytest.raises(ValueError):
        transfer_assessment(session.working, original, "W01", None, expected=original)
    assert session.working.read_bytes() == before
    copied_id = session.change(
        "Copy assessment",
        lambda: transfer_assessment(session.working, original, "W02", first),
    )
    copied = assessment(session.working, "W02", copied_id, kind)
    assert (
        copied["source"] == original["source"]
        and copied["result"] == original["result"]
    )
    row = replace(copied["source"].tasks[0], repetitions=200)
    copied = session.change(
        "Input",
        lambda: persist_source(
            session.working, copied, replace(copied["source"], tasks=(row,))
        ),
    )
    assert copied["result"] != original["result"]
    assert assessment(session.working, "W01", kind=kind)["result"] == original["result"]
    moved_id = session.change(
        "Move assessment",
        lambda: transfer_assessment(session.working, copied, "W01", second, move=True),
    )
    assert assessment(session.working, "W02", copied_id, kind) is None
    moved = assessment(session.working, "W01", moved_id, kind)
    assert moved["result"] == copied["result"]
    target_id = session.change(
        "Copy assessment",
        lambda: transfer_assessment(session.working, moved, "W02", None),
    )
    target = assessment(session.working, "W02", target_id, kind)
    assert target["workplace"] is None and target["result"] == copied["result"]
    session.change(
        "Move assessment",
        lambda: transfer_assessment(
            session.working, moved, "W01", None, move=True, expected=original
        ),
    )
    assert assessment(session.working, "W01", moved_id, kind) is None
    assert assessment(session.working, "W01", kind=kind)["result"] == copied["result"]
    session.replay()
    assert (
        assessment(session.working, "W01", moved_id, kind)["result"] == copied["result"]
    )
    assert assessment(session.working, "W01", kind=kind)["result"] == original["result"]


def test_stale_source_destination_and_missing_membership_reject_without_writes(
    tmp_path: Path,
) -> None:
    """Reject stale/invalid consent rather than overwriting data after confirmation.

    Args:
        tmp_path: Disposable native workspace.

    Returns:
        None; failed operations retain exact original native bytes.
    """
    session, source, first, second = setup_contexts(tmp_path, AssessmentKind.LIFFT)
    target_id = transfer_assessment(session.working, source, "W02", None)
    target = assessment(session.working, "W02", target_id)
    changed = replace(
        target["source"], tasks=(replace(target["source"].tasks[0], repetitions=200),)
    )
    persist_source(session.working, target, changed)
    before = session.working.read_bytes()
    for operation in (
        lambda: delete_assessment(session.working, target),
        lambda: create_assessment(
            session.working, "W02", AssessmentKind.LIFFT, None, expected=target
        ),
        lambda: transfer_assessment(
            session.working, source, "W02", None, expected=target
        ),
        lambda: transfer_assessment(session.working, target, "W01", first),
        lambda: create_assessment(
            session.working, "missing", AssessmentKind.LIFFT, second
        ),
    ):
        with pytest.raises((ValueError, KeyError)):
            operation()
        assert session.working.read_bytes() == before


def test_optional_job_and_closed_contexts_preserved(tmp_path: Path) -> None:
    """Keep optional placement and closed history distinct from an active destination.

    Args:
        tmp_path: Private native fixture.

    Returns:
        None; exact document lookup can open closed history without creating versions.
    """
    session, _source, first, _second = setup_contexts(tmp_path, AssessmentKind.LIFFT)
    with AssessmentProjectFile.open(session.working) as project:
        project.save_jobs(
            JobCatalog(
                project.metadata.project_id,
                (Job("J01", "Box loading"),),
                (JobPlacement(1, "J01", first),),
            )
        )
    identity = create_assessment(session.working, "W01", AssessmentKind.LIFFT, first)
    with AssessmentProjectFile.open(session.working) as project:
        jobs = project.load_jobs()
        project.save_jobs(
            replace(jobs, assignments=(replace(jobs.assignments[0], placement_id=1),))
        )
    record = assessment(session.working, "W01", identity)
    assert record["job"] == "J01 · Box loading"
    create_assessment(
        session.working, "W01", AssessmentKind.LIFFT, first, expected=record
    )
    assert assessment(session.working, "W01", identity)["job"] == record["job"]
    with AssessmentProjectFile.open(session.working) as project:
        jobs = project.load_jobs()
        project.save_jobs(
            replace(jobs, assignments=(replace(jobs.assignments[0], active=False),))
        )
    closed = assessment(session.working, "W01", identity)
    assert not closed["active"] and "Closed assignment" in closed["context"]
    assert (
        destination_record(
            read_contexts(session.working), "W01", AssessmentKind.LIFFT, first
        )
        is None
    )
    assert assessment(session.working, "W01")["workplace"] is None


def test_transfer_publish_failure_rolls_back_complete_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed final publish cannot remove source or partially replace destination.

    Args:
        tmp_path: Disposable session/native files.
        monkeypatch: Controlled failing adapter publication boundary.

    Returns:
        None; bytes, chronology and exact source/result remain unchanged on failure.
    """
    session, source, first, _second = setup_contexts(tmp_path, AssessmentKind.LIFFT)
    identity = create_assessment(session.working, "W02", AssessmentKind.LIFFT, first)
    target = assessment(session.working, "W02", identity)
    before = session.working.read_bytes()
    label = session.history.undo_label_key

    def fail(project: AssessmentProjectFile) -> None:
        """Inject failure after the native in-memory transfer, before publication.

        Args:
            project: Owned repository whose persistent bytes must remain recoverable.

        Returns:
            None; always raises to emulate a failed write.

        Raises:
            OSError: Synthetic publication failure.
        """
        raise OSError("Synthetic publish failure")

    monkeypatch.setattr(AssessmentProjectFile, "commit_editing", fail)
    with pytest.raises(OSError, match="Synthetic publish failure"):
        session.change(
            "Move assessment",
            lambda: transfer_assessment(
                session.working, source, "W02", first, move=True, expected=target
            ),
        )
    assert session.working.read_bytes() == before
    assert session.history.undo_label_key == label
    assert assessment(session.working, "W01")["result"] == source["result"]
    assert assessment(session.working, "W02", identity)["source"] == target["source"]

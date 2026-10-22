"""CR006 exact Copy/Move observations, source binding and transaction rollback.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
import sqlite3
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from ergotools.application.assessment_export import saved_summary_rows
from ergotools.application.saved_results import stored_result
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessment_transfer import TransferRequest
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.work_catalog import WorkerEntry
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.draft_json import DocumentFormatError
from ergotools.infrastructure.saved_result_store import SavedResultStore
from ergotools.presentation.summary_csv import summary_csv_table
from tests.test_history_persistence import HIERARCHY, JOBS, META
from tests.test_legacy_assessments import historical as historical
from tests.test_legacy_catalogs import legacy_catalog as legacy_catalog
from tests.test_saved_results import SOURCES, calculate
from tools.project_migration.ergotools_migration.legacy_conversion import (
    convert_legacy_project,
)


def seed(
    path: Path, historical: Path, archived: bool, *, fresh_results: bool = True
) -> int:
    """Create a small synthetic project with either fresh or original results.

    Args:
        path: Disposable test file path; the caller controls creation and cleanup.
        historical: Disposable source fixture with closed/current assignment versions;
            not a native compatibility mode.
        archived: True converts the original-format fixture; False creates a fresh
            native project. Both branches produce current-format projects with one
            result per assessment.
        fresh_results: True stores matching recalculated fixture output; False preserves
            the scenario's absent/old output case.

    Returns:
        Assignment identity 31 for the converted original-format fixture or 1 for
        the fresh native fixture. The project is closed before returning.
    """
    if archived:
        with convert_legacy_project(historical, path, "p"):
            pass
        source_id = 31
    else:
        with AssessmentProjectFile.create_with_job_risks(path, META) as project:
            project.save_hierarchy(HIERARCHY)
            project.save_jobs(JOBS)
            for kind, source in zip(AssessmentKind, SOURCES, strict=True):
                entry = AssignmentAssessment(
                    kind.value,
                    1,
                    kind,
                    worker_id=next(
                        a.worker.worker_id
                        for a in project.load_jobs().assignments
                        if a.assignment_id == 1
                    ),
                )
                project.create_historical_assessment(entry, source)
                key = DocumentKey("p", entry.document_id)
                if fresh_results:
                    project.save_result(key, calculate(DocumentSession(key, source)))
        source_id = 1
    with AssessmentProjectFile.open(path) as project:
        hierarchy = project.load_hierarchy()
        project.save_hierarchy(
            replace(
                hierarchy,
                work=replace(
                    hierarchy.work, workers=(*hierarchy.work.workers, WorkerEntry("y"))
                ),
            )
        )
    return source_id


@pytest.mark.parametrize("archived", [False, True])
@pytest.mark.parametrize("move", [False, True])
def test_transfer_results_reopen_and_export_exactly(
    tmp_path: Path, historical: Path, archived: bool, move: bool
) -> None:
    """All three tools keep exact observations, including null legacy outputs.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        historical: Disposable source fixture with closed/current assignment versions;
            not a native compatibility mode.
        archived: Prior-format source/result fixture or scenario flag; current native
            output still has one authoritative result.
        move: True tests Move; False tests Copy while retaining the source assessment.

    Returns:
        None.
    """
    path = tmp_path / "transfer.ergprj"
    source_id = seed(path, historical, archived)
    with AssessmentProjectFile.open(path) as project:
        history, jobs = project.load_history(), project.load_jobs()
        source_owner = next(
            a.worker for a in jobs.assignments if a.assignment_id == source_id
        )
        destination_owner = replace(source_owner, worker_id="y")
        entries = {
            kind: history.current_for(source_id, kind) for kind in AssessmentKind
        }
        originals = {}
        for kind, entry in entries.items():
            key = DocumentKey("p", entry.document_id)
            source = project.load(key)
            originals[kind] = stored_result(project, key, source)
            assert originals[kind] is not None
        summaries = {
            kind: next(
                r
                for r in saved_summary_rows(project, kind)
                if r.assignment_id == source_id
            )
            for kind in AssessmentKind
        }
        ids = {kind: f"copied-{kind.value}" for kind in AssessmentKind}
        project.transfer_assessments(
            jobs,
            history,
            TransferRequest(source_id, destination_owner, tuple(AssessmentKind), move),
            ids,
        )
    with AssessmentProjectFile.open(path) as project:
        destination = next(
            a for a in project.load_jobs().assignments if a.worker.worker_id == "y"
        )
        for kind in AssessmentKind:
            key = DocumentKey("p", ids[kind])
            assert project.load_saved_result(key) == originals[kind]
            assert project.load(key) == originals[kind].source
            (row,) = (
                r
                for r in saved_summary_rows(project, kind)
                if r.assignment_id == destination.assignment_id
            )
            assert row == replace(
                summaries[kind],
                document=key,
                owner=destination_owner,
                assignment_id=destination.assignment_id,
                assignment_active=destination.active,
            )
            # Compare actual CSV result/unit/status columns independently of IDs.
            old_csv = summary_csv_table((summaries[kind],), "fixed")[1]
            new_csv = summary_csv_table((row,), "fixed")[1]
            assert new_csv[8:11] == old_csv[8:11] and new_csv[16:] == old_csv[16:]
            old_entry = project.load_history().current_for(source_id, kind)
            assert (old_entry is None) is move
            if not move:
                old_key = summaries[kind].document
                assert (
                    stored_result(project, old_key, project.load(old_key))
                    == originals[kind]
                )
        if archived:
            # The source fixture includes a superseded version on a closed owner.
            assert any(
                e.document_id == "legacy-assessment-50"
                for e in project.load_history().entries
            )


@pytest.mark.parametrize("archived", [False, True])
@pytest.mark.parametrize("move", [False, True])
def test_result_write_failure_rolls_back_whole_transfer(
    tmp_path: Path, historical: Path, move: bool, archived: bool
) -> None:
    """Second result failure restores first copy, new assignment and Move sources.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        historical: Disposable source fixture with closed/current assignment versions;
            not a native compatibility mode.
        move: True tests Move; False tests Copy while retaining the source assessment.
        archived: Prior-format source/result fixture or scenario flag; current native
            output still has one authoritative result.

    Returns:
        None.
    """
    path = tmp_path / "rollback.ergprj"
    source_id = seed(path, historical, archived)
    with AssessmentProjectFile.open(path) as project:
        jobs, history = project.load_jobs(), project.load_history()
        original_documents = project.list_assessments()
        owner = replace(
            next(a.worker for a in jobs.assignments if a.assignment_id == source_id),
            worker_id="y",
        )
        write = SavedResultStore.write
        calls = 0

        def fail_second(
            store: SavedResultStore, key: DocumentKey, payload: str
        ) -> None:
            """Fail the second selected result-cache write after the first succeeds.

            Fail the second selected result-cache write after the first succeeds,
            verifying complete source/result transfer rollback.

            Args:
                store: Injected test-owned storage adapter receiving the controlled
                    write/read callback.
                key: Exact project/document identity for the source/result under test.
                payload: Serialized result/source text forwarded to the controlled
                    storage callback.

            Returns:
                None.

            Raises:
                sqlite3.OperationalError: The deliberately injected SQLite
                    write/metadata failure is reached.
            """
            nonlocal calls
            calls += 1
            if calls == 2:
                raise sqlite3.OperationalError("second result failed")
            write(store, key, payload)

        with (
            patch.object(SavedResultStore, "write", fail_second),
            pytest.raises(sqlite3.OperationalError),
        ):
            project.transfer_assessments(
                jobs,
                history,
                TransferRequest(source_id, owner, tuple(AssessmentKind), move),
                {kind: f"copy-{kind.value}" for kind in AssessmentKind},
            )
        assert calls == 2
    with AssessmentProjectFile.open(path) as project:
        assert project.load_jobs() == jobs and project.load_history() == history
        assert project.list_assessments() == original_documents
        for entry in history.entries:
            key = DocumentKey("p", entry.document_id)
            assert stored_result(project, key, project.load(key)) is not None


@pytest.mark.parametrize("unit", [None, "", "Imperial", "original label"])
def test_recorded_codec_retains_absent_units_and_outputs(unit: str | None) -> None:
    """The native codec refuses obsolete result status and unit labels.

    Args:
        unit: Recorded evidence unit label, or None for a deliberately missing/unknown
            unit case.

    Returns:
        None.
    """
    fresh = calculate(DocumentSession(DocumentKey("p", "d"), SOURCES[0]))
    recorded = replace(fresh, calculation_status=None, unit_label=unit)
    with pytest.raises(DocumentFormatError):
        SavedResultStore.encode(recorded)


@pytest.mark.parametrize(
    "change",
    [
        {"status": None},
        {"units": 1},
        {"version": True},
        {"tasks": []},
        {"damage": float("inf")},
        {"percent": True},
    ],
)
def test_recorded_codec_rejects_invalid_or_fresh_provenance(
    change: dict[str, object],
) -> None:
    """The recorded envelope cannot bypass strict numeric/source/provenance checks.

    Args:
        change: Parametrized mutation applied to an isolated snapshot/source to exercise
            a rejection boundary.

    Returns:
        None.
    """
    fresh = calculate(DocumentSession(DocumentKey("p", "d"), SOURCES[0]))
    data = json.loads(SavedResultStore.encode(fresh))
    data.update(change)
    with pytest.raises(DocumentFormatError):
        SavedResultStore.decode(json.dumps(data))


@pytest.mark.parametrize("archived", [False, True])
def test_changed_source_does_not_copy_stale_result(
    tmp_path: Path, historical: Path, archived: bool
) -> None:
    """An input edit invalidates both fresh and archived source-bound observations.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        historical: Disposable source fixture with closed/current assignment versions;
            not a native compatibility mode.
        archived: Prior-format source/result fixture or scenario flag; current native
            output still has one authoritative result.

    Returns:
        None.
    """
    path = tmp_path / "stale.ergprj"
    source_id = seed(path, historical, archived)
    kind = AssessmentKind.LIFFT
    with AssessmentProjectFile.open(path) as project:
        jobs, history = project.load_jobs(), project.load_history()
        entry = history.current_for(source_id, kind)
        key = DocumentKey("p", entry.document_id)
        source = project.load(key)
        changed = replace(
            source, tasks=(replace(source.tasks[0], repetitions=987), *source.tasks[1:])
        )
        project.save(key, changed)
        owner = next(a.worker for a in jobs.assignments if a.assignment_id == source_id)
        project.transfer_assessments(
            jobs,
            history,
            TransferRequest(source_id, replace(owner, worker_id="y"), (kind,)),
            {kind: "copy"},
        )
    with AssessmentProjectFile.open(path) as project:
        assert project.load(DocumentKey("p", "copy")) == changed
        assert project.load_saved_result(DocumentKey("p", "copy")) is None


@pytest.mark.parametrize("move", [False, True])
def test_no_saved_result_stays_absent(
    tmp_path: Path, historical: Path, move: bool
) -> None:
    """Transfer does not calculate or create observations for unevaluated sources.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        historical: Disposable source fixture with closed/current assignment versions;
            not a native compatibility mode.
        move: True tests Move; False tests Copy while retaining the source assessment.

    Returns:
        None.
    """
    path = tmp_path / "absent.ergprj"
    source_id = seed(path, historical, False, fresh_results=False)
    with AssessmentProjectFile.open(path) as project:
        jobs, history = project.load_jobs(), project.load_history()
        owner = replace(jobs.assignments[0].worker, worker_id="y")
        project.transfer_assessments(
            jobs,
            history,
            TransferRequest(source_id, owner, tuple(AssessmentKind), move),
            {kind: f"copy-{kind.value}" for kind in AssessmentKind},
        )
    with AssessmentProjectFile.open(path) as project:
        for kind in AssessmentKind:
            key = DocumentKey("p", f"copy-{kind.value}")
            assert project.load_saved_result(key) is None
            assert project.load_saved_result(key) is None
            assert project.load(key).tasks


def test_recorded_copy_can_be_transferred_again_after_reopen(
    tmp_path: Path, historical: Path
) -> None:
    """A recorded-copy envelope remains transferable without its own archive ID.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        historical: Disposable source fixture with closed/current assignment versions;
            not a native compatibility mode.

    Returns:
        None.
    """
    path = tmp_path / "repeat.ergprj"
    source_id = seed(path, historical, True)
    originals = {}
    for worker_id in ("y", "x"):
        with AssessmentProjectFile.open(path) as project:
            jobs, history = project.load_jobs(), project.load_history()
            source = next(a for a in jobs.assignments if a.assignment_id == source_id)
            for kind in AssessmentKind:
                entry = history.current_for(source_id, kind)
                key = DocumentKey("p", entry.document_id)
                result = stored_result(project, key, project.load(key))
                if worker_id == "y":
                    originals[kind] = result
                else:
                    assert result == originals[kind]
            project.transfer_assessments(
                jobs,
                history,
                TransferRequest(
                    source_id,
                    replace(source.worker, worker_id=worker_id),
                    tuple(AssessmentKind),
                ),
                {kind: f"{worker_id}-{kind.value}" for kind in AssessmentKind},
            )
            source_id = next(
                a.assignment_id
                for a in project.load_jobs().assignments
                if a.worker.worker_id == worker_id
            )
    with AssessmentProjectFile.open(path) as project:
        for kind in AssessmentKind:
            assert (
                project.load_saved_result(DocumentKey("p", f"x-{kind.value}"))
                == originals[kind]
            )

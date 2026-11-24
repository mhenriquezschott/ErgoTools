"""Thin prototype adapter over unchanged ErgoTools calculation and SQLite services.

This module owns only a dedicated tablet-test project, not operational fixtures.
It imports no Qt, VTK, solver, Flet or network code. Connections are scoped to each
operation so Android callbacks never share a SQLite connection between threads.
"""

import json
import platform
import sqlite3
import sys
from pathlib import Path

from ergotools.application.assessments.evaluation import AssessmentEvaluator
from ergotools.application.saved_results import result_snapshot
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.work_catalog import WorkCatalog, WorkerEntry
from ergotools.domain.work_hierarchy import WorkHierarchy
from ergotools.domain.worker_details import WorkerDetails
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile

# Dedicated fictional project/worker IDs; never derived from a user's real project.
PROJECT_ID = "android-feasibility"
DOCUMENT_ID = "W01-lifft-standalone"


def source(arm: float = 30, load: float = 49, repetitions: float = 100) -> LifftDraft:
    """Build metric task inputs; delegates all scientific validation to the core.

    Args:
        arm: Lever arm in centimeters.
        load: Load as force in newtons.
        repetitions: Repetitions per work day.

    Returns:
        Immutable one-task source, with a literal optional task name.
    """
    return LifftDraft(
        MeasurementSystem.METRIC,
        (LifftTask("T01", arm, load, repetitions, task_name="Manual packing"),),
    )


def create_project(path: Path) -> None:
    """Create a current-format owned sample with one real standalone assessment.

    Args:
        path: Nonexistent test destination; its parent must exist.

    Returns:
        None; existing files are refused by the unchanged repository adapter.
    """
    metadata = ProjectMetadata(
        PROJECT_ID, "Tablet assessment test", MeasurementSystem.METRIC
    )
    worker = WorkerEntry(
        "W01", "Elena", "Muñoz", WorkerDetails("1991-06-15", "Female", 165, 65)
    )
    hierarchy = WorkHierarchy(WorkCatalog(PROJECT_ID, (worker,)))
    with AssessmentProjectFile.create_empty(path, metadata) as project:
        project.save_hierarchy(hierarchy)
        project.create_historical_assessment(
            AssignmentAssessment(DOCUMENT_ID, None, AssessmentKind.LIFFT, "W01"),
            source(),
        )


def calculate_and_save(path: Path, draft: LifftDraft) -> dict[str, object]:
    """Calculate and save through the existing application/result/storage contracts.

    Args:
        path: Dedicated existing tablet sample.
        draft: Complete input source from the mobile fields.

    Returns:
        Reloaded persisted values after closing and reopening the native repository.

    Raises:
        ValueError: The existing evaluator rejects the entered assessment.
    """
    document = DocumentKey(PROJECT_ID, DOCUMENT_ID)
    evaluation = AssessmentEvaluator().evaluate(DocumentSession(document, draft))
    result = result_snapshot(evaluation, MeasurementSystem.METRIC)
    if result is None:
        raise ValueError("Enter complete, valid nonnegative task inputs.")
    with AssessmentProjectFile.open(path) as project:
        project.begin_editing(lambda label: None)
        checkpoint = project.editing_checkpoint()
        project.restore_editing_checkpoint(checkpoint)
        project.save_result(document, result)
        project.commit_editing()
    return read_project(path)


def read_project(path: Path) -> dict[str, object]:
    """Read the exact source, demographics and persisted result without calculating.

    Args:
        path: Current-format test project readable by the existing desktop adapter.

    Returns:
        JSON-compatible inputs and outputs, with absent results represented by None.
    """
    document = DocumentKey(PROJECT_ID, DOCUMENT_ID)
    with AssessmentProjectFile.open(path) as project:
        draft = project.load(document)
        if not isinstance(draft, LifftDraft):
            raise ValueError("The tablet sample must contain a LiFFT assessment.")
        task = draft.tasks[0]
        result = project.load_saved_result(document)
        worker = project.load_hierarchy().work.workers[0]
        return {
            "worker": worker.worker_id,
            "name": f"{worker.first_name} {worker.last_name}",
            "arm_cm": task.lever_arm,
            "load_n": task.load,
            "repetitions": task.repetitions,
            "task_name": task.task_name,
            "damage": result.damage if result else None,
            "probability_percent": result.probability_percent if result else None,
        }


def compatibility_probe(folder: Path) -> dict[str, object]:
    """Produce a disposable same-core Android/desktop round-trip evidence file.

    Args:
        folder: App-private test storage, not a user-selected project directory.

    Returns:
        Reopened calculation with runtime evidence; also writes JSON beside its project.
    """
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "compatibility_probe.ergprj"
    path.unlink(missing_ok=True)
    create_project(path)
    saved = calculate_and_save(path, source())
    report = {
        "runtime": platform.system(),
        "python": sys.version,
        "sqlite": sqlite3.sqlite_version,
        "sqlite_serialize": hasattr(sqlite3.Connection, "serialize"),
        "sqlite_deserialize": hasattr(sqlite3.Connection, "deserialize"),
        "reopened": saved,
        "qt_imported": any(
            name.startswith(("PyQt", "vtk", "highspy")) for name in sys.modules
        ),
    }
    (folder / "compatibility_probe.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return report

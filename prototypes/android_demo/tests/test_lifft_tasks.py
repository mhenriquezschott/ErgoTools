"""M03 source/result/catalog round trips using real unchanged calculators and SQLite.

Cover independent worker ownership, task structure, precise known vectors, partial
rows, names/clipboard, compound Undo and source-bound stale/invalid protection.
"""

from dataclasses import replace
from pathlib import Path

import pytest
from assessment_tasks import (
    blank_task,
    create_standalone,
    persist_source,
    preview,
    remove_tasks,
    task_form_values,
    task_from_form,
    tasks_from_tsv,
    tasks_to_tsv,
)
from mobile_assessment import assessment
from mobile_workers import put_worker
from project_session import ProjectSession

from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.work_catalog import WorkerEntry
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile


def setup_project(
    tmp_path: Path, *, units: str = "metric"
) -> tuple[ProjectSession, dict]:
    """Create a private real worker/standalone document with the selected source units.

    Args:
        tmp_path: Owned test directory.
        units: Metric or imperial native project defaults.

    Returns:
        Mobile session and selected complete source projection.
    """
    session = ProjectSession(tmp_path)
    session.create("LiFFT test", units)
    session.change(
        "Add worker",
        lambda: put_worker(session.working, WorkerEntry("W01", "Ana", "Ruiz")),
    )
    session.change(
        "Create LiFFT assessment", lambda: create_standalone(session.working, "W01")
    )
    return session, assessment(session.working, "W01")


def test_creation_one_owner_per_worker_and_source_units(tmp_path: Path) -> None:
    """Standalone creation uses project defaults and never creates duplicate ownership.

    Args:
        tmp_path: Disposable native storage.

    Returns:
        None; other workers' data remains independent after repeated native reopen.
    """
    session, selected = setup_project(tmp_path, units="imperial")
    assert len(selected["source"].tasks) == 1
    assert selected["source"].system == MeasurementSystem.IMPERIAL
    before = session.working.read_bytes()
    with pytest.raises(ValueError):
        session.change("Duplicate", lambda: create_standalone(session.working, "W01"))
    assert session.working.read_bytes() == before
    session.change(
        "Add worker", lambda: put_worker(session.working, WorkerEntry("W02"))
    )
    session.change(
        "Create LiFFT assessment", lambda: create_standalone(session.working, "W02")
    )
    assert assessment(session.working, "W02")["document"] != selected["document"]
    assert assessment(session.working, "W01")["source"] == selected["source"]
    with pytest.raises(ValueError):
        create_standalone(session.working, "missing")


def test_multitask_known_numbers_blank_and_partial_rows(tmp_path: Path) -> None:
    """Known vectors retain exact totals; only started incomplete rows make partial.

    Args:
        tmp_path: Private project.

    Returns:
        None; total and row results remain source-bound through desktop native reopen.
    """
    session, selected = setup_project(tmp_path)
    tasks = (
        LifftTask("a", 30, 49, 100, task_name="Packing"),
        LifftTask("b", 30, 49, 100),
        blank_task(),
    )
    selected = session.change(
        "Paste tasks",
        lambda: persist_source(
            session.working, selected, replace(selected["source"], tasks=tasks)
        ),
    )
    assert selected["result"].damage == 0.0006
    assert selected["result"].probability_percent == 17.13696930240022
    assert selected["result"].calculation_status.value == "complete"
    assert selected["result"].tasks[0].share_percent == 50
    partial = replace(tasks[2], lever_arm=30)
    selected = session.change(
        "Edit",
        lambda: persist_source(
            session.working,
            selected,
            replace(selected["source"], tasks=(*selected["source"].tasks[:2], partial)),
        ),
    )
    assert selected["result"].damage == 0.0006
    assert selected["result"].calculation_status.value == "partial"
    assert "Task 3: load, repetitions" in selected["readiness"]["message"]
    session.save()
    reopened = assessment(session.working, "W01")
    assert (
        reopened["source"] == selected["source"]
        and reopened["result"] == selected["result"]
    )


def test_multiselect_removal_all_empty_and_undo_restore(tmp_path: Path) -> None:
    """Batch removal retains unaffected row identities; Undo restores exact full data.

    Args:
        tmp_path: Owned native file.

    Returns:
        None; deleting every row leaves one blank row instead of an unusable matrix.
    """
    session, selected = setup_project(tmp_path)
    tasks = tuple(
        LifftTask(str(i), 30, 49, 100, task_name=f"Task {i}") for i in range(4)
    )
    selected = session.change(
        "Paste tasks",
        lambda: persist_source(
            session.working, selected, replace(selected["source"], tasks=tasks)
        ),
    )
    before = selected
    selected = session.change(
        "Remove tasks",
        lambda: persist_source(
            session.working, selected, remove_tasks(selected["source"], {"1", "3"})
        ),
    )
    assert [t.task_id for t in selected["source"].tasks] == ["0", "2"]
    session.replay()
    assert assessment(session.working, "W01")["source"] == before["source"]
    session.replay(redo=True)
    selected = assessment(session.working, "W01")
    selected = session.change(
        "Remove tasks",
        lambda: persist_source(
            session.working, selected, remove_tasks(selected["source"], {"0", "2"})
        ),
    )
    assert len(selected["source"].tasks) == 1
    assert selected["source"].tasks[0].lever_arm is None and selected["result"] is None


def test_name_catalog_and_source_undo_as_one_compound_action(tmp_path: Path) -> None:
    """Pasted names become reusable with source/results and are removed by one Undo.

    Args:
        tmp_path: Owned app storage.

    Returns:
        None; redo restores exact name references/inputs/result without duplicates.
    """
    session, selected = setup_project(tmp_path)
    session.save()
    before = selected["source"]
    rows = tasks_from_tsv("Packing\t30\t49\t100\nPacking\t30\t49\t100")
    selected = session.change(
        "Paste tasks",
        lambda: persist_source(
            session.working, selected, replace(selected["source"], tasks=rows)
        ),
    )
    with AssessmentProjectFile.open(session.working) as native:
        defs = native.load_task_definitions()
        assert len(defs) == 1
        assert all(
            t.task_definition_id == defs[0].definition_id
            for t in selected["source"].tasks
        )
    session.replay()
    with AssessmentProjectFile.open(session.working) as native:
        assert native.load_task_definitions() == ()
        assert native.load(selected["document"]) == before
    session.replay(redo=True)
    with AssessmentProjectFile.open(session.working) as native:
        assert native.load_task_definitions() == defs
        assert native.load_saved_result(selected["document"]) == selected["result"]


def test_invalid_and_stale_inputs_cannot_keep_old_result(tmp_path: Path) -> None:
    """Invalid model values clear outputs; nonfinite/stale operations preserve the file.

    Args:
        tmp_path: Private native project.

    Returns:
        None; no prior summary is displayed as if bound to changed invalid inputs.
    """
    session, selected = setup_project(tmp_path)
    draft = replace(selected["source"], tasks=(LifftTask("a", 30, 49, 100),))
    selected = session.change(
        "Edit", lambda: persist_source(session.working, selected, draft)
    )
    assert selected["result"].probability_percent == 13.190999733969136
    invalid = replace(
        selected["source"], tasks=(replace(selected["source"].tasks[0], load=-1),)
    )
    prior = selected
    selected = session.change(
        "Edit", lambda: persist_source(session.working, selected, invalid)
    )
    assert (
        selected["result"] is None
        and selected["readiness"]["status"] == "invalid_input"
    )
    before = session.working.read_bytes()
    with pytest.raises(ValueError):
        session.change("Stale", lambda: persist_source(session.working, prior, draft))
    assert session.working.read_bytes() == before
    with pytest.raises(ValueError):
        tasks_from_tsv("Packing\tNaN\t49\t100")


def test_imperial_and_metric_sources_match_desktop_model(tmp_path: Path) -> None:
    """Use each source's original units and the characterized model conversion factors.

    Args:
        tmp_path: Separate private project folder for each unit system.

    Returns:
        None; both native files retain the correct source-unit declaration.
    """
    outputs = []
    for units, arm, load in (("metric", 30, 49), ("imperial", 30 / 2.54, 49 / 4.45)):
        session, selected = setup_project(tmp_path / units, units=units)
        selected = persist_source(
            session.working,
            selected,
            replace(selected["source"], tasks=(LifftTask("a", arm, load, 100),)),
        )
        outputs.append(selected["result"].probability_percent)
        assert assessment(session.working, "W01")["source"].system.value == units
    assert outputs == [13.190999733969136] * 2


def test_capacity_clipboard_precision_and_unused_names(tmp_path: Path) -> None:
    """TSV preserves literals/numeric precision and caps batch operations at 100 tasks.

    Args:
        tmp_path: Private native file.

    Returns:
        None; named-only tasks are unused and new copy rows have independent IDs.
    """
    session, selected = setup_project(tmp_path)
    source = (
        LifftTask("a", 30.1234567890123, 49, 100, task_name="Empaque ñ"),
        LifftTask("b", task_name="Named unused"),
    )
    copied = tasks_from_tsv(tasks_to_tsv(source))
    assert copied[0].lever_arm == source[0].lever_arm
    assert copied[0].task_name == "Empaque ñ" and copied[0].task_id != "a"
    draft = replace(
        selected["source"],
        tasks=tuple(LifftTask(str(i), 30, 49, 100) for i in range(100)),
    )
    selected = persist_source(session.working, selected, draft)
    assert len(assessment(session.working, "W01")["source"].tasks) == 100
    with pytest.raises(ValueError, match="100"):
        persist_source(
            session.working,
            selected,
            replace(draft, tasks=(*draft.tasks, blank_task())),
        )
    assert (
        preview(selected["document"], LifftDraft(draft.system, (copied[0], copied[1])))[
            "status"
        ]
        == "complete"
    )
    with pytest.raises(ValueError):
        tasks_from_tsv("bad\tcolumns")
    with pytest.raises(ValueError):
        tasks_from_tsv("\n\t\n")
    with pytest.raises(ValueError, match="100"):
        tasks_from_tsv("30\t49\t100\n" * 101)


def test_blank_and_zero_totals_do_not_invent_probability(tmp_path: Path) -> None:
    """Blank sources have no result; valid zero damage has no model probability.

    Args:
        tmp_path: Owned project.

    Returns:
        None; no missing result is reported as a zero-percent risk claim.
    """
    session, selected = setup_project(tmp_path)
    assert preview(selected["document"], selected["source"])["result"] is None
    selected = persist_source(
        session.working,
        selected,
        replace(selected["source"], tasks=(LifftTask("a", 0, 0, 0),)),
    )
    assert selected["result"].damage == 0
    assert selected["result"].probability_percent is None


def test_editing_name_preserves_unedited_numeric_precision() -> None:
    """Changing a descriptive name cannot round original metric or imperial numbers.

    Args:
        None.

    Returns:
        None; the bound task name changes, but source numeric bytes retain precision.
    """
    task = LifftTask("a", 30 / 2.54, 49 / 4.45, 100.12345678901234, task_name="Old")
    original = task_form_values(task)
    values = {**original, "task_name": "New"}
    updated = task_from_form(task, values, original)
    assert (updated.lever_arm, updated.load, updated.repetitions) == (
        task.lever_arm,
        task.load,
        task.repetitions,
    )
    assert updated.task_name == "New"


def test_recalculate_unchanged_source_is_not_an_undo_or_dirty_change(
    tmp_path: Path,
) -> None:
    """Repeated explicit Calculate does not create history from SQLite-only rewrites.

    Args:
        tmp_path: Owned native project.

    Returns:
        None; exact source/results and saved status remain unchanged.
    """
    session, selected = setup_project(tmp_path)
    selected = session.change(
        "Edit",
        lambda: persist_source(
            session.working,
            selected,
            replace(selected["source"], tasks=(LifftTask("a", 30, 49, 100),)),
        ),
    )
    session.save()
    before = session.working.read_bytes()
    revision = session.history.revision
    selected = session.change(
        "Calculate LiFFT",
        lambda: persist_source(session.working, selected, selected["source"]),
    )
    assert session.working.read_bytes() == before
    assert session.history.revision == revision and not session.active["dirty"]

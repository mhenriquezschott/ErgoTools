"""M04 scientific/storage/history boundaries for shared DUET/ST mobile operations.

Known literal vectors, imported ST conventions, physical units, selectors and
compound actions are verified with actual native project files and unchanged core.
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

from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    task_has_data,
)
from ergotools.domain.assessments.tst import TstDirection
from ergotools.domain.assessments.tst_draft import TstDirectionConvention
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.work_catalog import WorkerEntry
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile


def project_with_tool(tmp_path: Path, kind: AssessmentKind) -> tuple:
    """Create an owned native source independently for a chosen mobile tool.

    Args:
        tmp_path: Disposable native storage directory.
        kind: DUET or ST model identity.

    Returns:
        Private session and selected exact source projection.
    """
    session = ProjectSession(tmp_path)
    session.create("Tools", "metric")
    session.change(
        "Add worker", lambda: put_worker(session.working, WorkerEntry("W01"))
    )
    session.change("Create", lambda: create_standalone(session.working, "W01", kind))
    return session, assessment(session.working, "W01", kind=kind)


def filled(selected: dict, selector: str = "0") -> AssessmentDraft:
    """Build a known task preserving its stable source row ID.

    Args:
        selected: Typed selected source and worker owner.
        selector: OMNI rating or source direction code.

    Returns:
        Draft with one task, 30 cm, 49 N and 100 repetitions where applicable.
    """
    row = task_from_form(
        selected["source"].tasks[0],
        {
            "task_name": "Packing",
            "lever_arm": "30",
            "load": "49",
            "repetitions": "100",
            "omni_res_scale": selector,
            "direction": selector,
        },
        {},
    )
    return replace(selected["source"], tasks=(row,))


@pytest.mark.parametrize(
    "kind,selector,damage,probability",
    [
        (AssessmentKind.DUET, "3", 0.00041, 12.376491915752084),
        (AssessmentKind.DUET, "6", 0.01162, 29.477781162652782),
        (AssessmentKind.DUET, "10", 0.97087, 63.72410253989626),
        (AssessmentKind.TST, "0", 0.00088, 12.222570893163052),
        (AssessmentKind.TST, "1", 0.0001, 5.47847918813796),
        (AssessmentKind.TST, "2", 0.00029, 8.174318545491246),
    ],
)
def test_known_vectors_and_exact_native_reopen(
    tmp_path: Path,
    kind: AssessmentKind,
    selector: str,
    damage: float,
    probability: float,
) -> None:
    """Save characterized calculator vectors without additional mobile rounding.

    Args:
        tmp_path: Private storage.
        kind: Selected tool.
        selector: Discrete input code.
        damage: Literal characterized core damage.
        probability: Literal characterized probability percentage.

    Returns:
        None; native desktop reopening retains exact values and source convention.
    """
    session, selected = project_with_tool(tmp_path, kind)
    assert preview(selected["document"], selected["source"])["result"] is None
    selected = session.change(
        "Input",
        lambda: persist_source(session.working, selected, filled(selected, selector)),
    )
    assert selected["result"].damage == damage
    assert selected["result"].probability_percent == probability
    assert selected["result"].calculation_status.value == "complete"
    session.save()
    assert assessment(session.working, "W01", kind=kind)["result"] == selected["result"]
    if kind is AssessmentKind.TST:
        assert (
            selected["source"].direction_convention
            is TstDirectionConvention.REFERENCE_UI
        )


@pytest.mark.parametrize("kind", [AssessmentKind.DUET, AssessmentKind.TST])
def test_tool_independence_partial_invalid_noop_and_history(
    tmp_path: Path, kind: AssessmentKind
) -> None:
    """Other tool ownership survives source edits, history and empty/partial rows.

    Args:
        tmp_path: Disposable project.
        kind: Selected source model.

    Returns:
        None; no-op Calculate has no history or dirty effect; invalid clears results.
    """
    session, selected = project_with_tool(tmp_path, kind)
    session.change(
        "Other", lambda: create_standalone(session.working, "W01", AssessmentKind.LIFFT)
    )
    other = assessment(session.working, "W01")
    selected = session.change(
        "Input", lambda: persist_source(session.working, selected, filled(selected))
    )
    before = selected
    partial = replace(blank_task(kind), repetitions=100)
    if kind is AssessmentKind.DUET:
        partial = replace(partial, omni_res_scale=None)
    else:
        partial = replace(partial, lever_arm=30)
    source = replace(
        selected["source"], tasks=(*selected["source"].tasks, blank_task(kind), partial)
    )
    selected = session.change(
        "Paste tasks", lambda: persist_source(session.working, selected, source)
    )
    assert selected["result"].calculation_status.value == "partial"
    assert "Task 3:" in selected["readiness"]["message"]
    session.replay()
    selected = assessment(session.working, "W01", kind=kind)
    assert selected["source"] == before["source"]
    assert selected["result"] == before["result"]
    assert assessment(session.working, "W01")["source"] == other["source"]
    session.save()
    native_bytes = session.working.read_bytes()
    label = session.history.undo_label_key
    selected = session.change(
        "Calculate",
        lambda: persist_source(session.working, selected, selected["source"]),
    )
    assert native_bytes == session.working.read_bytes()
    assert session.history.undo_label_key == label
    assert not session.active["dirty"]
    invalid = replace(selected["source"].tasks[0], repetitions=-1)
    selected = session.change(
        "Invalid",
        lambda: persist_source(
            session.working, selected, replace(selected["source"], tasks=(invalid,))
        ),
    )
    assert selected["result"] is None
    assert selected["readiness"]["status"] == "invalid_input"
    with pytest.raises(ValueError):
        persist_source(session.working, before, before["source"])


@pytest.mark.parametrize(
    "kind,text",
    [
        (AssessmentKind.DUET, "Box packing\t6\t100\nSort\t3\t200"),
        (AssessmentKind.TST, "Box packing\t1\t30\t49\t100\nSort\t2\t40\t98\t200"),
    ],
)
def test_clipboard_catalog_batch_remove_and_atomic_replay(
    tmp_path: Path, kind: AssessmentKind, text: str
) -> None:
    """Paste names/typed inputs, select a subset and restore full exact source/result.

    Args:
        tmp_path: Owned files.
        kind: Selected model.
        text: Tool-specific input-only TSV.

    Returns:
        None; source/catalog/results are one operation and invalid selectors reject.
    """
    session, selected = project_with_tool(tmp_path, kind)
    rows = tasks_from_tsv(text, kind)
    assert tasks_from_tsv(tasks_to_tsv(rows, kind), kind)[0].task_name == "Box packing"
    selected = session.change(
        "Paste tasks",
        lambda: persist_source(
            session.working, selected, replace(selected["source"], tasks=rows)
        ),
    )
    with AssessmentProjectFile.open(session.working) as project:
        assert {d.name for d in project.load_task_definitions()} == {
            "Box packing",
            "Sort",
        }
    session.replay()
    with AssessmentProjectFile.open(session.working) as project:
        assert not project.load_task_definitions()
    session.replay(redo=True)
    selected = assessment(session.working, "W01", kind=kind)
    exact = selected
    selected = session.change(
        "Remove tasks",
        lambda: persist_source(
            session.working,
            selected,
            remove_tasks(selected["source"], {rows[0].task_id}),
        ),
    )
    assert len(selected["source"].tasks) == 1
    session.replay()
    selected = assessment(session.working, "W01", kind=kind)
    assert (
        selected["source"] == exact["source"] and selected["result"] == exact["result"]
    )
    cleared = remove_tasks(selected["source"], {r.task_id for r in rows})
    assert len(cleared.tasks) == 1 and not task_has_data(cleared.tasks[0])
    for bad in (
        ("11\t100", "3.5\t100")
        if kind is AssessmentKind.DUET
        else ("3\t30\t49\t100", "down\t30\t49\t100")
    ):
        with pytest.raises(ValueError):
            tasks_from_tsv(bad, kind)


def test_st_convention_and_imperial_sources_are_not_reinterpreted(
    tmp_path: Path,
) -> None:
    """Imported model codes and reference indices stay distinct across mobile editing.

    Args:
        tmp_path: Private native file.

    Returns:
        None; metric/imperial physical inputs agree and naming never rounds them.
    """
    session, selected = project_with_tool(tmp_path, AssessmentKind.TST)
    reference = filled(selected, "1")
    model = replace(reference, direction_convention=TstDirectionConvention.MODEL_CODES)
    key = DocumentKey("test", "st")
    assert preview(key, reference)["result"].damage == 0.0001
    assert preview(key, model)["result"].damage == 0.00029
    imperial = replace(
        reference,
        system=MeasurementSystem.IMPERIAL,
        tasks=(replace(reference.tasks[0], lever_arm=30 / 2.54, load=49 / 4.45),),
    )
    assert (
        preview(key, imperial)["result"].probability_percent
        == preview(key, reference)["result"].probability_percent
    )
    values = task_form_values(imperial.tasks[0])
    original = dict(values)
    values["task_name"] = "Changed"
    task = task_from_form(imperial.tasks[0], values, original)
    assert task.lever_arm == 30 / 2.54 and task.load == 49 / 4.45
    selected = session.change(
        "Import model codes", lambda: persist_source(session.working, selected, model)
    )
    assert selected["source"].direction_convention is TstDirectionConvention.MODEL_CODES
    assert selected["source"].tasks[0].direction is TstDirection.DOWNWARD


def test_all_tools_save_independently_with_imperial_result_labels(
    tmp_path: Path,
) -> None:
    """One worker holds each tool once; saved native bytes retain each exact source.

    Args:
        tmp_path: Disposable tablet workspace.

    Returns:
        None; DUET labels use project defaults, while ST keeps its physical units.
    """
    session = ProjectSession(tmp_path)
    session.create("Imperial tools", "imperial")
    session.change("Worker", lambda: put_worker(session.working, WorkerEntry("W01")))
    expected = {}
    for kind in AssessmentKind:
        create_standalone(session.working, "W01", kind)
        selected = assessment(session.working, "W01", kind=kind)
        values = {
            "task_name": kind.value,
            "omni_res_scale": "6",
            "direction": "2",
            "lever_arm": "12",
            "load": "10",
            "repetitions": "100",
        }
        row = task_from_form(selected["source"].tasks[0], values, {})
        selected = persist_source(
            session.working, selected, replace(selected["source"], tasks=(row,))
        )
        assert selected["result"].unit_label == "Imperial"
        expected[kind] = selected
        with pytest.raises(ValueError):
            create_standalone(session.working, "W01", kind)
    session.save()
    session.open_recent(session.active["id"])
    for kind, original in expected.items():
        reopened = assessment(session.working, "W01", kind=kind)
        assert reopened["source"] == original["source"]
        assert reopened["result"] == original["result"]

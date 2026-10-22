"""Original dropdown labels and executed model codes survive source history/I/O.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from ergotools.application.assessments.tst_commands import ReplaceTstInputs
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.domain.assessments.tst import TstDirection, calculate_tst_task
from ergotools.domain.assessments.tst_draft import (
    TstDirectionConvention,
    TstDraft,
    TstTask,
)
from ergotools.domain.assessments.validation import DraftError
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.tst_serialization import decode_tst, encode_tst
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.tst_task_panel import TstTaskPanel
from tests.test_tst_task_panel import panel as panel


def test_original_ui_mapping_matches_all_frozen_model_vectors() -> None:
    """Check all 1,650 old model outputs through the actual inverse UI mapping.

    Args:
        None.

    Returns:
        None.
    """
    records = json.loads(
        (Path(__file__).parent / "fixtures/tst_calculation_reference.json").read_text()
    )["records"]
    inverse = {
        "0": TstDirection.HANDLING_LOADS,
        "1": TstDirection.HORIZONTAL,
        "2": TstDirection.DOWNWARD,
    }
    for record in records:
        task = TstTask(
            "original",
            inverse[record["direction"]],
            record["lever_arm"],
            record["load"],
            record["repetitions"],
        )
        draft = TstDraft(
            MeasurementSystem(record["system"]),
            (task,),
            TstDirectionConvention.REFERENCE_UI,
        )
        projected = draft.model_task("original")
        result = calculate_tst_task(projected, draft.system)
        assert projected.direction.value == record["direction"]
        assert result.model_moment_ft_lbf == record["model_moment"]
        assert result.displayed_moment == record["display_moment"]
        assert result.cumulative_damage == record["damage"]
        assert draft.tasks[0] is task


def test_version_one_stays_identical_and_reference_convention_roundtrips() -> None:
    """Old new-format sources do not acquire swapped semantics on open or save.

    Args:
        None.

    Returns:
        None.
    """
    original = TstDraft(
        MeasurementSystem.IMPERIAL, (TstTask("a", TstDirection.DOWNWARD, 12, 20, 100),)
    )
    payload = encode_tst(original)
    assert json.loads(payload)["version"] == 1
    assert "direction_convention" not in json.loads(payload)
    assert decode_tst(payload) == original
    assert original.model_task("a").direction is TstDirection.DOWNWARD
    imported = replace(
        original, direction_convention=TstDirectionConvention.REFERENCE_UI
    )
    assert json.loads(encode_tst(imported))["version"] == 2
    assert decode_tst(encode_tst(imported)) == imported
    assert imported.tasks[0].direction is TstDirection.DOWNWARD
    assert imported.model_task("a").direction is TstDirection.HORIZONTAL
    absent = replace(imported, tasks=(replace(imported.tasks[0], direction=None),))
    assert absent.model_task("a").direction is None


@pytest.mark.parametrize("mutation", ["missing", "unknown", "old-version-extra"])
def test_ambiguous_convention_is_rejected(mutation: str) -> None:
    """Never infer a convention from an unsupported or incomplete payload.

    Args:
        mutation: Named malformed snapshot/catalog mutation selected by the parametrized
            scenario.

    Returns:
        None.
    """
    draft = TstDraft(MeasurementSystem.METRIC, (), TstDirectionConvention.REFERENCE_UI)
    data = json.loads(encode_tst(draft))
    if mutation == "missing":
        del data["direction_convention"]
    elif mutation == "unknown":
        data["direction_convention"] = "guess"
    else:
        data["version"] = 1
    with pytest.raises(ValueError):
        decode_tst(json.dumps(data))


def test_reference_panel_edits_clear_history_and_save_preserve_convention(
    panel: TstTaskPanel, tmp_path: Path
) -> None:
    """Use the existing original controls; ordinary edits must not drop provenance.

    Args:
        panel: Live tool task panel supplied by the fixture; edits use its actual
            controls.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    active = panel.presenter.workspace.active
    imported = replace(
        active.state, direction_convention=TstDirectionConvention.REFERENCE_UI
    )
    document = active.document
    workspace = panel.presenter.workspace
    workspace.close(choice=CloseChoice.DISCARD)
    with AssessmentProjectFile.open(tmp_path / "st.ergprj") as project:
        project.save(document, imported)
    workspace.switch(str(tmp_path / "st.ergprj"), document.document_id)
    active = workspace.active
    panel.load_source(panel.presenter.bind())
    assert panel.inputs[1][0].currentText() == "Push or Pull Downward"
    panel.inputs[1][0].setCurrentIndex(2)
    assert active.state != imported and not panel.pending
    assert not panel.commit_inputs()
    changed = active.state
    assert changed.direction_convention is TstDirectionConvention.REFERENCE_UI
    assert changed.tasks[1].direction is TstDirection.HORIZONTAL
    assert changed.model_task("b").direction is TstDirection.DOWNWARD
    with patch.object(LifftWindow, "confirm_clear_assessment", return_value=True):
        panel.clear_button.click()
    assert active.state.direction_convention is TstDirectionConvention.REFERENCE_UI
    active.undo()
    assert active.state == changed
    panel.presenter.workspace.save()
    with AssessmentProjectFile.open(tmp_path / "st.ergprj") as project:
        assert project.load(active.document) == changed
    with pytest.raises(DraftError):
        ReplaceTstInputs(
            active.document,
            changed,
            replace(changed, direction_convention=TstDirectionConvention.MODEL_CODES),
        ).apply(changed)


def test_compact_numeric_display_preserves_exact_source(
    panel: TstTaskPanel,
    tmp_path: Path,
) -> None:
    """A narrow load field retains full precision and no-edit source identity.

    Args:
        panel: Live tool task panel supplied by the fixture; edits use its actual
            controls.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = panel.presenter.workspace
    active = workspace.active
    source = replace(
        active.state,
        tasks=(
            replace(active.state.tasks[0], load=8.900000000000005),
            *active.state.tasks[1:],
        ),
    )
    document = active.document
    workspace.close(choice=CloseChoice.DISCARD)
    with AssessmentProjectFile.open(tmp_path / "st.ergprj") as project:
        project.save(document, source)
    workspace.switch(str(tmp_path / "st.ergprj"), document.document_id)
    panel.load_source(panel.presenter.bind())
    editor = panel.inputs[0][2]
    assert editor.text() == "8.9"
    assert editor.source_text() == repr(source.tasks[0].load)
    assert editor.cursorPosition() == 0
    assert not panel.commit_inputs()
    assert workspace.active.state == source and not workspace.active.is_dirty


def test_application_evaluates_both_conventions_against_frozen_reference() -> None:
    """Match 1650 frozen vectors through both application source conventions.

    Args:
        None.

    Returns:
        None.
    """
    from dataclasses import replace

    from ergotools.application.assessments.evaluation import (
        AssessmentEvaluator,
        EvaluationStatus,
    )
    from ergotools.application.session import DocumentKey, DocumentSession
    from ergotools.domain.assessments.document import AssessmentDraft

    fixture = json.loads(
        (Path(__file__).parent / "fixtures/tst_calculation_reference.json").read_text()
    )
    for record in fixture["records"]:
        direction = TstDirection(record["direction"])
        task = TstTask(
            "t", direction, record["lever_arm"], record["load"], record["repetitions"]
        )
        for convention in TstDirectionConvention:
            source_direction = direction
            if (
                convention is TstDirectionConvention.REFERENCE_UI
                and direction is not TstDirection.HANDLING_LOADS
            ):
                source_direction = (
                    TstDirection.HORIZONTAL
                    if direction is TstDirection.DOWNWARD
                    else TstDirection.DOWNWARD
                )
            source = TstDraft(
                MeasurementSystem(record["system"]),
                (replace(task, direction=source_direction),),
                convention,
            )
            session: DocumentSession[AssessmentDraft] = DocumentSession(
                DocumentKey("p", "st"), source, persisted=True
            )
            outcome = AssessmentEvaluator().evaluate(session)
            assert outcome.status is EvaluationStatus.COMPLETE
            result = outcome.task_results[0]
            assert result.displayed_moment == record["display_moment"]
            assert result.cumulative_damage == record["damage"]
            assert session.state is source and not session.is_dirty


def test_st_grid_keeps_partial_inputs_and_zero_total_unavailable() -> None:
    """Partial ST moment previews do not invent saved zero inputs or probability.

    Args:
        None.

    Returns:
        None.
    """
    from ergotools.application.assessments.evaluation import (
        AssessmentEvaluator,
        EvaluationStatus,
    )
    from ergotools.application.session import DocumentKey, DocumentSession
    from ergotools.domain.assessments.document import AssessmentDraft

    source = TstDraft(
        MeasurementSystem.IMPERIAL,
        (TstTask("moment", TstDirection.HANDLING_LOADS, 12, 20), TstTask("blank")),
    )
    session: DocumentSession[AssessmentDraft] = DocumentSession(
        DocumentKey("p", "st"), source
    )
    evaluator = AssessmentEvaluator()
    assert evaluator.evaluate(session).status is EvaluationStatus.INVALID_INPUT
    result = evaluator.evaluate_tst_grid(session)
    assert result.status is EvaluationStatus.PARTIAL
    assert result.summary.total_damage == 0 and result.summary.probability is None
    assert result.task_results[0].displayed_moment > 0
    assert result.task_results[1].displayed_moment == 0
    assert session.state is source and source.tasks[0].repetitions is None
    with pytest.raises(ValueError):
        evaluator.evaluate_lifft_grid(session)

"""Grid completeness, unused slots and lossless task-count modal regressions.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from ergotools.application.assessments.evaluation import (
    AssessmentEvaluator,
    EvaluationStatus,
)
from ergotools.application.assessments.lifft_commands import SetLifftTaskCount
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.application.settings import Language
from ergotools.bootstrap import create_window
from ergotools.domain.assessments.lifft import calculate_lifft_task
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.validation import DraftError
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.preferences_dialog import PreferencesDialog

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])
# Exact synthetic integrated-grid project/document identity.
_KEY = DocumentKey("grid", "lifft")


def test_grid_preview_preserves_source_and_strict_evaluation() -> None:
    """Only complete rows contribute; rep-less rows show moment without fake input.

    Args:
        None.

    Returns:
        None.
    """
    source = LifftDraft(
        MeasurementSystem.IMPERIAL,
        (
            LifftTask("complete", 12, 20, 100),
            LifftTask("moment", 24, 10),
            LifftTask("blank"),
            LifftTask("no_arm", None, 20, 100),
            LifftTask("no_load", 12, None, 100),
        ),
    )
    session = DocumentSession(_KEY, source, persisted=True)
    evaluator = AssessmentEvaluator()
    assert evaluator.evaluate(session).status is EvaluationStatus.INVALID_INPUT
    result = evaluator.evaluate_lifft_grid(session)
    assert result.status is EvaluationStatus.PARTIAL
    assert (
        result.summary.total_damage
        == calculate_lifft_task(source.tasks[0], source.system).cumulative_damage
    )
    assert [row.displayed_moment for row in result.task_results] == [20, 20, 0, 0, 0]
    assert all(row.cumulative_damage == 0 for row in result.task_results[1:])
    assert result.issues and all(i.code == "validation.required" for i in result.issues)
    assert session.state is source and not session.is_dirty
    assert source.tasks[1].repetitions is None
    assert evaluator.current(session) is result


def test_grid_blank_and_invalid_rows_do_not_claim_complete_risk() -> None:
    """Blank previews have no modeled probability; invalid numeric source blocks all.

    Args:
        None.

    Returns:
        None.
    """
    evaluator = AssessmentEvaluator()
    blank = DocumentSession(
        _KEY, LifftDraft(MeasurementSystem.IMPERIAL, (LifftTask("b"),))
    )
    result = evaluator.evaluate_lifft_grid(blank)
    assert result.status is EvaluationStatus.PARTIAL
    assert result.summary.total_damage == 0 and result.summary.probability is None
    bad = DocumentSession(
        _KEY,
        LifftDraft(MeasurementSystem.IMPERIAL, (LifftTask("bad", 12, -1),)),
    )
    result = evaluator.evaluate_lifft_grid(bad)
    assert result.status is EvaluationStatus.INVALID_INPUT
    assert result.summary is None and not result.task_results
    empty = DocumentSession(_KEY, LifftDraft(MeasurementSystem.IMPERIAL))
    assert evaluator.evaluate_lifft_grid(empty).status is EvaluationStatus.INVALID_INPUT


def test_grid_metric_preserves_reference_preview_and_missing_source() -> None:
    """Metric preview calculates complete rows without replacing missing inputs.

    Args:
        None.

    Returns:
        None.
    """
    session = DocumentSession(
        _KEY,
        LifftDraft(
            MeasurementSystem.METRIC, (LifftTask("a", 10, 20, 30), LifftTask("b"))
        ),
    )
    result = AssessmentEvaluator().evaluate_lifft_grid(session)
    assert result.status is EvaluationStatus.COMPLETE
    assert not result.issues
    assert result.summary is not None and len(result.task_results) == 2
    assert session.state.tasks[1].lever_arm is None


@pytest.fixture
def window(tmp_path: Path) -> Iterator[LifftWindow]:
    """Own a synthetic integrated grid with three unused reference task slots.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Yields:
        Live synthetic integrated window; fixture cleanup closes the window and releases
        its temporary project after the test.
    """
    view = create_window(tmp_path / "settings.json", original_navigation=True)
    view.presenter.workspace.create(
        str(tmp_path / "grid.ergprj"),
        ProjectMetadata("grid", "Grid", MeasurementSystem.IMPERIAL),
        "lifft",
        LifftDraft(
            MeasurementSystem.IMPERIAL, tuple(LifftTask(str(i)) for i in range(3))
        ),
    )
    view.refresh()
    view.show()
    _APP.processEvents()
    yield view
    view.presenter.workspace.close(choice=CloseChoice.DISCARD)
    view.close()
    _APP.processEvents()


def test_grid_calculate_save_reopen_keeps_unused_values_missing(
    window: LifftWindow, tmp_path: Path
) -> None:
    """One populated row is complete beside unused slots, which remain absent on Save.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    panel = window.task_panel
    for cell, value in zip(panel.inputs[0], ("12", "20", "100"), strict=True):
        cell.setText(value)
        cell.textEdited.emit(value)
    panel.calculate_button.click()
    assert panel.outputs[0][0].text() == "20.0"
    assert panel.outputs[1][1].text() == "0.0000"
    assert "Incomplete" not in window.message.text()
    window.main_navigation.toolbar_actions["save"].trigger()
    with AssessmentProjectFile.open(tmp_path / "grid.ergprj") as project:
        source = project.load(project.list_assessments()[0].document)
        assert source.tasks[0].load == 20
        assert source.tasks[1].repetitions is None and source.tasks[2].load is None
    window.language = Language.SPANISH
    window.translate()
    window.task_panel.calculate_button.click()
    assert "Entrada incompleta" not in window.message.text()
    for row in window.task_panel.inputs:
        for cell, value in zip(row, ("12", "20", "100"), strict=True):
            cell.setText(value)
            cell.textEdited.emit(value)
    window.task_panel.calculate_button.click()
    result = window.presenter.evaluator.current(window.presenter.workspace.active)
    assert result.status is EvaluationStatus.COMPLETE
    assert not window.message.text()


def test_owned_task_count_cancel_reset_and_undo(window: LifftWindow) -> None:
    """Modal Cancel retains text; growth preserves rows and Undo restores capacity.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    source = window.presenter.source()
    active = window.presenter.workspace.active
    pending_field = window.task_panel.inputs[0][0]
    pending_field.setText("invalid")
    pending_field.textEdited.emit("invalid")

    def cancel() -> None:
        """Check the unified modal's active count and Cancel without changing inputs.

        The count starts at the current row count with the original 1-100 bounds.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, PreferencesDialog) and dialog.parent() is window
        assert dialog.count.minimum() == 1 and dialog.count.maximum() == 100
        assert dialog.count.value() == len(source.tasks)
        dialog.count.setValue(5)
        dialog.cancel_button.click()

    QTimer.singleShot(0, cancel)
    window.main_navigation.toolbar_actions["settings"].trigger()
    assert active.state is source
    assert window.task_panel.inputs[0][0] is pending_field
    assert pending_field.text() == "invalid" and window.task_panel.pending

    def accept() -> None:
        """Set the actual owned task-count modal to 5.

        Set the actual owned task-count modal to 5 and accept one reversible
        grid resize.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, PreferencesDialog)
        dialog.count.setValue(5)
        dialog.reset_tasks.setChecked(True)
        dialog.apply_button.click()

    pending_field.setText("14")
    pending_field.textEdited.emit("14")
    with patch.object(
        window,
        "confirm_task_reset",
        return_value=True,
    ) as confirm:
        QTimer.singleShot(0, accept)
        window.main_navigation.toolbar_actions["settings"].trigger()
    assert len(active.state.tasks) == 5 and len(window.task_panel.inputs) == 5
    confirm.assert_not_called()
    assert active.state.tasks[0].lever_arm == 14
    assert active.state.tasks[1:3] == source.tasks[1:]
    assert all(t.lever_arm is None for t in active.state.tasks[3:])
    active.undo()
    window.refresh()
    assert len(window.task_panel.inputs) == 3
    assert active.state.tasks[0].lever_arm == 14
    assert active.state.tasks[1:] == source.tasks[1:]


def test_task_count_rejects_invalid_replacement_and_stale_source() -> None:
    """Bad counts, changed prefixes and stale resize requests preserve the source.

    Args:
        None.

    Returns:
        None.
    """
    source = LifftDraft(MeasurementSystem.IMPERIAL, (LifftTask("a", 12, 20, 100),))
    for tasks in (
        (),
        tuple(LifftTask(str(i)) for i in range(101)),
        (LifftTask("other"),),
    ):
        with pytest.raises(DraftError):
            SetLifftTaskCount(_KEY, source, tasks).apply(source)
    with pytest.raises(DraftError):
        SetLifftTaskCount(
            _KEY, LifftDraft(MeasurementSystem.IMPERIAL), (LifftTask("b"),)
        ).apply(source)


def test_metric_calculate_save_reopen_and_unit_projection(
    window: LifftWindow, tmp_path: Path
) -> None:
    """Metric save retains precision; unit toggles remain read-only.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    from ergotools.domain.assessments.lifft import calculate_lifft_task

    workspace = window.presenter.workspace
    workspace.close(choice=CloseChoice.DISCARD)
    source = LifftDraft(
        MeasurementSystem.METRIC, (LifftTask("a", 30.48, 44.5, 100), LifftTask("b"))
    )
    path = tmp_path / "metric.ergprj"
    workspace.create(
        str(path),
        ProjectMetadata("metric", "Metric", MeasurementSystem.METRIC),
        "lifft",
        source,
    )
    window.refresh()
    window.task_panel.calculate_button.click()
    result = window.presenter.evaluator.current(workspace.active)
    expected = calculate_lifft_task(source.tasks[0], source.system)
    assert result.status is EvaluationStatus.COMPLETE
    assert result.task_results[0] == expected
    assert window.task_panel.outputs[0][0].text() == f"{expected.displayed_moment:.1f}"
    assert window.results_sidebar.assessment_status_label.text() != "Review required"
    assert workspace.active.state == source
    for units in MeasurementSystem:
        window.units.setCurrentIndex(list(MeasurementSystem).index(units))
        assert workspace.active.state == source
    window.save_project()
    identity = workspace.active.document.document_id
    workspace.close(choice=CloseChoice.DISCARD)
    workspace.switch(str(path), identity)
    window.refresh()
    window.task_panel.calculate_button.click()
    assert workspace.active.state == source and not workspace.active.is_dirty
    assert (
        window.presenter.evaluator.current(workspace.active).task_results[0] == expected
    )

"""Original DUET controls: atomic editing, calculation, persistence and layout.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from PyQt5.QtWidgets import QApplication

from ergotools.application.assessments.evaluation import EvaluationStatus
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.bootstrap import create_window, load_icons
from ergotools.domain.assessments.duet import DuetTask
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.validation import DraftError
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.duet_presenter import DuetPresenter
from ergotools.presentation.desktop.duet_task_panel import DuetTaskPanel
from ergotools.presentation.numeric_input import DecimalConvention

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.fixture
def panel(tmp_path: Path) -> Iterator[DuetTaskPanel]:
    """Use the existing workspace and a synthetic DUET document only.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Yields:
        Live synthetic tool task panel with its real presenter/workspace; fixture
        cleanup closes owned controls and the temporary project.
    """
    workspace = create_window(tmp_path / "settings.json").presenter.workspace
    workspace.create(
        str(tmp_path / "duet.ergprj"),
        ProjectMetadata("p", "DUET", MeasurementSystem.IMPERIAL),
        "d",
        DuetDraft((DuetTask("a", 5, 100), DuetTask("b", 8, 50))),
    )
    presenter = DuetPresenter(workspace)
    view = DuetTaskPanel(
        presenter, load_icons(), report_issue=lambda issue: None, changed=lambda: None
    )
    view.resize(980, 650)
    view.load_source(presenter.bind())
    view.show()
    _APP.processEvents()
    yield view
    workspace.close(choice=CloseChoice.DISCARD)
    view.close()
    _APP.processEvents()


def enter(panel: DuetTaskPanel, row: int, text: str) -> None:
    """Emit a user edit, rather than using silent programmatic loading.

    Args:
        panel: Live tool task panel supplied by the fixture; edits use its actual
            controls.
        row: Zero-based task/risk table row selected for actual user editing.
        text: Literal typed/control input, including invalid/incomplete cases where
            specified.

    Returns:
        None.
    """
    field = panel.inputs[row][1]
    field.setText(text)
    field.textEdited.emit(text)


def test_calculate_atomic_save_and_reopen(panel: DuetTaskPanel, tmp_path: Path) -> None:
    """Both edited rows commit together and independently round-trip through disk.

    Args:
        panel: Live tool task panel supplied by the fixture; edits use its actual
            controls.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    active = panel.presenter.workspace.active
    assert active is not None
    before = active.state
    panel.inputs[0][0].setCurrentIndex(6)
    selected = active.state
    assert selected is not before and not panel.pending
    enter(panel, 1, "75")
    assert active.state is selected
    panel.calculate_button.click()
    assert not panel.pending
    assert panel.outputs[0][0].text() != "0.0"
    changed = active.state
    active.undo()
    assert active.state is selected
    active.undo()
    assert active.state is before
    active.redo()
    assert active.state is selected
    active.redo()
    assert active.state is changed
    panel.presenter.workspace.save()
    with AssessmentProjectFile.open(tmp_path / "duet.ergprj") as project:
        assert project.load(active.document) == changed


def test_invalid_text_retained_then_clear_and_undo(panel: DuetTaskPanel) -> None:
    """Rejected parsing retains edits; clearing is one reversible source change.

    Args:
        panel: Live tool task panel supplied by the fixture; edits use its actual
            controls.

    Returns:
        None.
    """
    before = panel.presenter.source()
    enter(panel, 0, "200")
    enter(panel, 1, "bad")
    with pytest.raises(DraftError):
        panel.commit_inputs()
    assert panel.presenter.source() is before and panel.pending
    assert panel.inputs[0][1].text() == "200" and panel.inputs[1][1].text() == "bad"
    panel.calculate_button.click()
    assert (
        panel.pending
        and panel.presenter.evaluator.current(panel.presenter.workspace.active) is None
    )
    panel.clear_button.click()
    assert all(c.currentIndex() == 0 and not e.text() for c, e in panel.inputs)
    panel.presenter.workspace.active.undo()
    assert panel.presenter.source() == before


def test_partial_rows_and_strict_evaluation(panel: DuetTaskPanel) -> None:
    """Blank slots stay missing; grid partial totals never become complete results.

    Args:
        panel: Live tool task panel supplied by the fixture; edits use its actual
            controls.

    Returns:
        None.
    """
    enter(panel, 1, "")
    panel.calculate_button.click()
    active = panel.presenter.workspace.active
    result = panel.presenter.evaluator.current(active)
    assert result.status is EvaluationStatus.PARTIAL
    assert result.task_results[0].cumulative_damage > 0
    assert result.task_results[1].cumulative_damage == 0
    assert panel.presenter.source().tasks[1].repetitions is None
    assert panel.outputs[1][0].text() == "0.0000"
    assert (
        panel.presenter.evaluator.evaluate(active).status
        is EvaluationStatus.INVALID_INPUT
    )


def test_language_decimal_and_units_preserve_inputs(panel: DuetTaskPanel) -> None:
    """Translation preserves pending text; unit toggles do not convert DUET counts.

    Args:
        panel: Live tool task panel supplied by the fixture; edits use its actual
            controls.

    Returns:
        None.
    """
    enter(panel, 0, "12,5")
    panel.language = Language.SPANISH
    panel.translate()
    assert panel.pending and panel.inputs[0][1].text() == "12,5"
    assert panel.inputs[0][0].itemText(10) == "10: Extremadamente difícil"
    panel.presenter.convention = DecimalConvention.COMMA
    panel.context = panel.presenter.bind()
    panel.calculate_button.click()
    before = panel.presenter.source()
    assert before.tasks[0].repetitions == 12.5
    panel.presenter.system = MeasurementSystem.METRIC
    panel.load_source(panel.presenter.bind())
    assert panel.presenter.source() is before
    assert panel.inputs[0][1].text() == "12"
    assert panel.headers[1].text() == "Escala OMNI-Res"


def test_clear_colors_invalid_values_and_stale_context(panel: DuetTaskPanel) -> None:
    """Input changes clear obsolete colors; invalid values suppress all calculation.

    Args:
        panel: Live tool task panel supplied by the fixture; edits use its actual
            controls.

    Returns:
        None.
    """
    panel.calculate_button.click()
    assert panel.outputs[0][0].styleSheet()
    enter(panel, 0, "-1")
    assert all(not o[0].styleSheet() for o in panel.outputs)
    panel.calculate_button.click()
    result = panel.presenter.evaluator.current(panel.presenter.workspace.active)
    assert result.status is EvaluationStatus.INVALID_INPUT and result.summary is None
    old = panel.context
    panel.presenter.bind()
    with pytest.raises(DraftError):
        panel.presenter.commit_grid(old, (("a", 0, "1"), ("b", 0, "1")))
    with pytest.raises(DraftError):
        panel.presenter.commit_grid(
            panel.presenter.context,
            (("b", 0, "1"), ("a", 0, "1")),
        )


def test_zero_scale_missing_scale_and_grid_geometry(panel: DuetTaskPanel) -> None:
    """Scale zero is data; unselected scale remains None and all columns align.

    Args:
        panel: Live tool task panel supplied by the fixture; edits use its actual
            controls.

    Returns:
        None.
    """
    panel.inputs[0][0].setCurrentIndex(0)
    panel.inputs[1][0].setCurrentIndex(-1)
    panel.calculate_button.click()
    assert panel.presenter.source().tasks[0].omni_res_scale == 0
    assert panel.presenter.source().tasks[1].omni_res_scale is None
    assert (
        panel.presenter.evaluator.current(panel.presenter.workspace.active).status
        is EvaluationStatus.PARTIAL
    )
    _APP.processEvents()
    assert panel.grid.columnMinimumWidth(1) == 250
    assert panel.grid.columnMinimumWidth(2) == 220
    assert all(
        b.height() == 40
        for b in (
            panel.clear_button,
            panel.context_button,
            panel.calculate_button,
        )
    )
    assert not panel.context_button.isEnabled()
    for column, header in enumerate(panel.headers):
        assert header.width() == panel.grid.itemAtPosition(1, column).widget().width()

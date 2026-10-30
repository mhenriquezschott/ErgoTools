"""ST controls exercise original geometry, units, atomic history and review gates.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from ergotools.application.assessments.evaluation import EvaluationStatus
from ergotools.application.assessments.tst_commands import ReplaceTstInputs
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.bootstrap import create_window, load_icons
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.assessments.validation import DraftError
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.tst_presenter import TstPresenter
from ergotools.presentation.desktop.tst_task_panel import TstTaskPanel
from ergotools.presentation.numeric_input import DecimalConvention

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.fixture
def panel(tmp_path: Path) -> Iterator[TstTaskPanel]:
    """Use a new synthetic project; never touch the reference or operational data.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Yields:
        Live synthetic tool task panel with its real presenter/workspace; fixture
        cleanup closes owned controls and the temporary project.
    """
    workspace = create_window(tmp_path / "settings.json").presenter.workspace
    workspace.create(
        str(tmp_path / "st.ergprj"),
        ProjectMetadata("p", "ST", MeasurementSystem.IMPERIAL),
        "st",
        TstDraft(
            MeasurementSystem.IMPERIAL,
            (
                TstTask("a", TstDirection.HANDLING_LOADS, 12, 20, 100),
                TstTask("b", TstDirection.DOWNWARD, 8, 10, 50),
            ),
        ),
    )
    presenter = TstPresenter(workspace)
    view = TstTaskPanel(
        presenter, load_icons(), report_issue=lambda issue: None, changed=lambda: None
    )
    view.resize(980, 650)
    view.load_source(presenter.bind())
    view.show()
    QTest.qWait(30)
    yield view
    workspace.close(choice=CloseChoice.DISCARD)
    view.close()
    _APP.processEvents()


def enter(panel: TstTaskPanel, row: int, column: int, text: str) -> None:
    """Simulate edited text rather than the silent programmatic load path.

    Args:
        panel: Live tool task panel supplied by the fixture; edits use its actual
            controls.
        row: Zero-based task/risk table row selected for actual user editing.
        column: Zero-based visible column or explicit SQL column identity selected by
            the regression.
        text: Literal typed/control input, including invalid/incomplete cases where
            specified.

    Returns:
        None.
    """
    field = panel.inputs[row][column]
    field.setText(text)
    field.textEdited.emit(text)


def test_atomic_edit_review_save_reopen(panel: TstTaskPanel, tmp_path: Path) -> None:
    """Selector and explicit numeric-grid acceptance replay separately and reopen.

    Args:
        panel: Live tool task panel supplied by the fixture; edits use its actual
            controls.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    active = panel.presenter.workspace.active
    before = active.state
    enter(panel, 0, 1, "15")
    enter(panel, 1, 3, "75")
    panel.inputs[0][0].setCurrentIndex(2)
    selected = active.state
    assert selected.tasks[0].direction is TstDirection.HORIZONTAL
    assert selected.tasks[0].lever_arm == before.tasks[0].lever_arm
    assert selected.tasks[1].repetitions == before.tasks[1].repetitions
    assert panel.pending  # Programmatic numeric setup is not a completed field edit.
    panel.calculate_button.click()
    result = panel.presenter.evaluator.current(active)
    assert result.status is EvaluationStatus.COMPLETE
    assert result.issues == ()
    assert result.summary is not None and len(result.task_results) == 2
    assert (
        panel.outputs[0][0].text() == f"{result.task_results[0].displayed_moment:.1f}"
    )
    changed = active.state
    assert changed.tasks[0].direction is TstDirection.HORIZONTAL
    assert changed.tasks[0].lever_arm == 15 and changed.tasks[1].repetitions == 75
    active.undo()
    assert active.state is selected
    active.undo()
    assert active.state is before
    active.redo()
    assert active.state is selected
    active.redo()
    assert active.state is changed
    panel.presenter.workspace.save()
    with AssessmentProjectFile.open(tmp_path / "st.ergprj") as project:
        assert project.load(active.document) == changed


def test_invalid_text_clear_missing_and_undo(panel: TstTaskPanel) -> None:
    """Invalid input preserves text/source; clearing is one reversible step.

    Args:
        panel: Live tool task panel supplied by the fixture; edits use its actual
            controls.

    Returns:
        None.
    """
    before = panel.presenter.source()
    enter(panel, 0, 1, "99")
    enter(panel, 1, 2, "bad")
    with pytest.raises(DraftError):
        panel.commit_inputs()
    panel.calculate_button.click()
    assert panel.pending and panel.inputs[1][2].text() == "bad"
    assert panel.presenter.source() is before
    panel.clear_button.click()
    assert not panel.pending
    assert all(
        combo.currentIndex() == 0 and all(not e.text() for e in editors)
        for combo, *editors in panel.inputs
    )
    assert all(
        t.direction is TstDirection.HANDLING_LOADS and t.load is None
        for t in panel.presenter.source().tasks
    )
    panel.presenter.workspace.active.undo()
    assert panel.presenter.source() is before
    panel.load_source(panel.presenter.bind())
    panel.inputs[1][0].setCurrentIndex(-1)
    enter(panel, 0, 3, "-1")
    panel.calculate_button.click()
    result = panel.presenter.evaluator.current(panel.presenter.workspace.active)
    assert result.status is EvaluationStatus.INVALID_INPUT and result.summary is None
    assert panel.presenter.source().tasks[1].direction is None


def test_unit_projection_language_and_comma_edit(panel: TstTaskPanel) -> None:
    """Display conversion preserves source; edits convert back without toggle drift.

    Args:
        panel: Live tool task panel supplied by the fixture; edits use its actual
            controls.

    Returns:
        None.
    """
    before = panel.presenter.source()
    panel.presenter.system = MeasurementSystem.METRIC
    panel.presenter.convention = DecimalConvention.COMMA
    panel.load_source(panel.presenter.bind())
    assert panel.presenter.source() is before
    assert panel.inputs[0][1].text() == "30,5"
    assert panel.headers[2].text() == "Lever Arm (cm)"
    enter(panel, 0, 1, "25,4")
    panel.language = Language.SPANISH
    panel.translate()
    assert panel.pending and panel.inputs[0][1].text() == "25,4"
    assert panel.inputs[1][0].currentData() == TstDirection.DOWNWARD.value
    assert panel.headers[3].text() == "Carga (N)"
    assert panel.commit_inputs()
    after = panel.presenter.source()
    assert after.system is MeasurementSystem.IMPERIAL
    assert (
        after.tasks[0].lever_arm == 10 and after.tasks[0].load == before.tasks[0].load
    )
    for system in (MeasurementSystem.IMPERIAL, MeasurementSystem.METRIC) * 3:
        panel.presenter.system = system
        panel.load_source(panel.presenter.bind())
        assert panel.presenter.source() is after
        assert not panel.commit_inputs()


def test_metric_gates_and_wrong_context(panel: TstTaskPanel) -> None:
    """Metric source exposes both gates; source/context/identity errors stay atomic.

    Args:
        panel: Live tool task panel supplied by the fixture; edits use its actual
            controls.

    Returns:
        None.
    """
    presenter = panel.presenter
    active = presenter.workspace.active
    old = panel.context
    context = presenter.bind()
    rows = (
        ("a", TstDirection.HANDLING_LOADS, "12", "20", "100"),
        ("b", TstDirection.DOWNWARD, "8", "10", "50"),
    )
    with pytest.raises(DraftError):
        presenter.commit_grid(old, rows)
    with pytest.raises(DraftError):
        presenter.commit_grid(context, rows[::-1])
    before = active.state
    with pytest.raises(DraftError):
        ReplaceTstInputs(
            active.document, before, TstDraft(MeasurementSystem.METRIC, before.tasks)
        ).apply(before)
    with pytest.raises(DraftError):
        ReplaceTstInputs(active.document, TstDraft(before.system), before).apply(before)
    presenter.workspace.create_assessment(
        "metric",
        TstDraft(
            MeasurementSystem.METRIC,
            (TstTask("m", TstDirection.HORIZONTAL, 30, 40, 50),),
        ),
    )
    result = presenter.calculate()
    assert result.status is EvaluationStatus.COMPLETE
    assert result.issues == ()
    presenter.workspace.close()
    assert presenter.bind() is None and presenter.calculate() is None
    assert not presenter.reset_grid()


def test_header_rebuild_resize_and_programmatic_signals(panel: TstTaskPanel) -> None:
    """Original column minima remain; translated rebuilds align at both sizes.

    Args:
        panel: Live tool task panel supplied by the fixture; edits use its actual
            controls.

    Returns:
        None.
    """
    before = panel.presenter.source()
    changes = []
    panel._changed = lambda: changes.append(True)
    panel.language = Language.SPANISH
    panel.translate()
    panel.load_source(panel.presenter.bind())
    assert not changes and not panel.pending and panel.presenter.source() is before
    assert tuple(panel.grid.columnMinimumWidth(c) for c in range(8)) == (
        55,
        190,
        95,
        58,
        80,
        145,
        115,
        85,
    )
    for width in (980, 1500, 980):
        panel.resize(width, 650)
        QTest.qWait(30)
        for column, header in enumerate(panel.headers):
            assert (
                header.width() == panel.grid.itemAtPosition(1, column).widget().width()
            )
    assert all(
        button.height() == 40
        for button in (
            panel.clear_button,
            panel.add_task_button,
            panel.calculate_button,
        )
    )
    assert panel.add_task_button.isEnabled()

    panel.load_source(None)
    QTest.qWait(30)
    assert not panel.isEnabled()
    for column, header in enumerate(panel.headers):
        assert header.width() == panel.grid.itemAtPosition(0, column).widget().width()


@pytest.mark.parametrize("reload_source", [False, True])
def test_original_direction_first_keyboard_order(
    panel: TstTaskPanel, reload_source: bool
) -> None:
    """Tab and Backtab follow original selectors-first order, including rebuilds.

    Args:
        panel: Live tool task panel supplied by the fixture; edits use its actual
            controls.
        reload_source: True replaces the active source/session before asserting
            old-result freshness behavior.

    Returns:
        None.
    """
    source = panel.presenter.source()
    if reload_source:
        panel.load_source(panel.presenter.bind())
    expected = [row[0] for row in panel.inputs]
    expected.extend(editor for row in panel.inputs for editor in row[1:])
    panel.activateWindow()
    QTest.qWait(30)  # Let Qt show rebuilt children before assigning keyboard focus.
    expected[0].setFocus()
    QTest.qWait(30)
    assert QApplication.focusWidget() is expected[0]
    for widget in expected[1:]:
        QTest.keyClick(QApplication.focusWidget(), Qt.Key_Tab)
        assert QApplication.focusWidget() is widget
    for widget in reversed(expected[:-1]):
        QTest.keyClick(QApplication.focusWidget(), Qt.Key_Backtab)
        assert QApplication.focusWidget() is widget
    assert panel.presenter.source() is source and not panel.pending

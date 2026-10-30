"""Original-grid calculation/save, atomic failures, units, clearing and geometry.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.bootstrap import create_window
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.numeric_input import DecimalConvention

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.fixture
def window(tmp_path: Path) -> Iterator[LifftWindow]:
    """Open a small synthetic original-grid project, never a reference database.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Yields:
        Live synthetic integrated window; fixture cleanup closes the window and releases
        its temporary project after the test.
    """
    view = create_window(tmp_path / "settings.json", original_controls=True)
    view.presenter.workspace.create(
        str(tmp_path / "grid.ergprj"),
        ProjectMetadata("grid", "Grid", MeasurementSystem.IMPERIAL),
        "lifft",
        LifftDraft(
            MeasurementSystem.IMPERIAL,
            (
                LifftTask("a", 12, 20, 100),
                LifftTask("b", 10, 15, 50),
            ),
        ),
    )
    view.refresh()
    view.show()
    _APP.processEvents()
    yield view
    view.presenter.workspace.close(choice=CloseChoice.DISCARD)
    view.close()
    _APP.processEvents()


def enter(view: LifftWindow, row: int, column: int, text: str) -> None:
    """Use actual key events so programmatic loading never substitutes for editing.

    Args:
        view: Live synthetic integrated window; this helper borrows it and does not
            acquire storage ownership.
        row: Zero-based task/risk table row selected for actual user editing.
        column: Zero-based visible column or explicit SQL column identity selected by
            the regression.
        text: Literal typed/control input, including invalid/incomplete cases where
            specified.

    Returns:
        None.
    """
    panel = view.task_panel
    assert panel is not None
    editor = panel.inputs[row][column]
    _APP.setActiveWindow(view)
    editor.setFocus()
    _APP.processEvents()
    assert editor.hasFocus()
    editor.selectAll()
    QTest.keyClicks(editor, text)
    _APP.processEvents()


def test_calculate_save_and_reopen(window: LifftWindow, tmp_path: Path) -> None:
    """Completed fields stay separate through calculation and durable reopen.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    panel = window.task_panel
    assert panel is not None
    active = window.presenter.workspace.active
    assert active is not None
    initial = active.state
    enter(window, 0, 0, "14")
    enter(window, 1, 1, "25")
    after_first = active.state
    assert after_first.tasks[0].lever_arm == 14
    assert after_first.tasks[1] == initial.tasks[1]
    panel.calculate_button.click()
    panel = window.task_panel
    assert panel is not None
    assert window.presenter.source().tasks[0].lever_arm == 14
    assert panel.outputs[0][0].text() != "0.0"
    assert panel.outputs[1][1].text() != "0.0"
    changed = active.state
    active.undo()
    assert active.state == after_first
    active.undo()
    assert active.state == initial
    active.redo()
    assert active.state == after_first
    active.redo()
    assert active.state == changed
    window.refresh()
    window.buttons["save"].click()
    with AssessmentProjectFile.open(tmp_path / "grid.ergprj") as project:
        saved = project.load(active.document)
        assert saved == changed
    enter(window, 0, 1, "21")
    assert window.damage_value.text() == "—"
    assert panel.outputs[0][1].text() == "0.0"


def test_invalid_grid_is_atomic_and_clear_clears_it(window: LifftWindow) -> None:
    """Invalid cells retain all text; confirmed clearing removes bad input.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    panel = window.task_panel
    assert panel is not None
    active = window.presenter.workspace.active
    assert active is not None
    original = active.state
    enter(window, 0, 0, "16")
    enter(window, 1, 2, "bad")
    after_first = active.state
    assert after_first.tasks[0].lever_arm == 16
    assert after_first.tasks[1] == original.tasks[1]
    panel.calculate_button.click()
    assert active.state == after_first
    assert panel.inputs[0][0].text() == "16"
    assert panel.inputs[1][2].text() == "bad"
    assert panel.pending
    with patch.object(LifftWindow, "confirm_clear_assessment", return_value=True):
        panel.clear_button.click()
    assert all(
        t.lever_arm is None and t.load is None and t.repetitions is None
        for t in window.presenter.source().tasks
    )
    window.buttons["undo"].click()
    assert active.state == after_first
    window.buttons["undo"].click()
    assert active.state == original


def test_units_decimal_and_pending_rejection(window: LifftWindow) -> None:
    """Edited metric values convert once; unchanged toggles retain source exactly.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    original = window.presenter.source()
    window.units.setCurrentIndex(
        list(MeasurementSystem).index(MeasurementSystem.METRIC)
    )
    panel = window.task_panel
    assert panel is not None
    assert panel.inputs[0][0].text() == "30.5"
    assert "ft.lb" in panel.headers[3].text()
    assert window.presenter.source() == original
    window.decimal.setCurrentIndex(
        list(DecimalConvention).index(DecimalConvention.COMMA)
    )
    enter(window, 0, 0, "35,56")
    window.buttons["save"].click()
    assert window.presenter.source().tasks[0].lever_arm == pytest.approx(14)
    assert window.presenter.source().system is MeasurementSystem.IMPERIAL
    enter(window, 1, 1, "bad")
    window.units.setCurrentIndex(
        list(MeasurementSystem).index(MeasurementSystem.IMPERIAL)
    )
    assert window.presenter.system is MeasurementSystem.METRIC
    assert panel.inputs[1][1].text() == "bad"


def test_header_scroll_and_minimum_bottom_controls(window: LifftWindow) -> None:
    """Sticky columns track original editable cells after resize and scrolling.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    panel = window.task_panel
    assert panel is not None
    for size in ((1200, 780), (960, 680)):
        window.resize(*size)
        # Allow native layout and deferred header events to finish.
        QTest.qWait(30)
        for column, header in enumerate(panel.headers):
            item = panel.grid.itemAtPosition(1, column)
            assert item is not None and item.widget() is not None
            assert header.width() == item.widget().width()
        for button in (
            panel.clear_button,
            panel.add_task_button,
            panel.calculate_button,
        ):
            assert panel.rect().contains(
                button.mapTo(panel, button.rect().bottomRight())
            )
    body_bar = panel.body_scroll.horizontalScrollBar()
    header_bar = panel.header.horizontalScrollBar()
    assert body_bar is not None and header_bar is not None
    body_bar.setValue(body_bar.maximum())
    assert header_bar.value() == body_bar.value()
    assert panel.add_task_button.text() == "+ Task"
    QTest.keyClick(panel.inputs[0][0], Qt.Key.Key_Tab)


def test_close_invalid_and_cancelled_dirty_retry(window: LifftWindow) -> None:
    """Close rejects invalid text; cancelled dirty close retains a usable editor.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    from unittest.mock import patch

    active = window.presenter.workspace.active
    assert active is not None
    enter(window, 0, 1, "bad")
    assert not window.close()
    assert window.task_panel.inputs[0][1].text() == "bad"
    enter(window, 0, 1, "30")
    with patch.object(window, "dirty_choice", return_value=CloseChoice.CANCEL):
        assert not window.close()
    assert window.presenter.workspace.active is active
    assert window.presenter.source().tasks[0].load == 30
    enter(window, 0, 1, "40")
    window.task_panel.calculate_button.click()
    assert window.presenter.source().tasks[0].load == 40
    assert window.task_panel.outputs[0][1].text() != "0.0"


def test_remove_uses_focused_task_and_undo_restores_it(window: LifftWindow) -> None:
    """Harness removal acts on the edited grid row, not a hidden default selection.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    enter(window, 1, 1, "25")
    window.buttons["remove"].click()
    assert tuple(t.task_id for t in window.presenter.source().tasks) == ("a",)
    window.buttons["undo"].click()
    assert window.presenter.source().tasks[1].load == 25


def test_close_clears_old_grid_before_deferred_widget_deletion(
    window: LifftWindow,
) -> None:
    """A cleared project must not paint the previous project's rows or colors.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    panel = window.task_panel
    assert panel is not None
    old_field = panel.inputs[0][0]
    window.presenter.workspace.close(choice=CloseChoice.DISCARD)
    window.refresh()
    assert not old_field.isVisible()
    assert panel.inputs == []
    assert panel.outputs == []
    assert not panel.isEnabled()

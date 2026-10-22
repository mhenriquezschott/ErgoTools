"""Analysis setup history, mixed chronology and main-window keyboard ownership.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QDialog

from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.plot_filters import PlotRiskView
from ergotools.domain.plot_scope import PlotScope
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.rotation_dialog import RotationDialog
from tests.test_plot_results import project as project
from tests.test_plot_window import host
from tests.test_rotation_dialog import seed
from tests.test_saved_tool_data import window as window

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("language", tuple(Language))
@pytest.mark.parametrize("system", tuple(MeasurementSystem))
def test_plot_analysis_controls_multistep_and_exact_disabled_bounds(
    project: AssessmentProjectFile,
    tmp_path: Path,
    language: Language,
    system: MeasurementSystem,
) -> None:
    """Apply/tool/mode undo restores disabled/unpaired bounds without any write.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.
        system: Explicit metric/imperial display or source system exercised by this
            scenario.

    Returns:
        None.
    """
    view = host(project, tmp_path, language=language, system=system)
    filters = view.filters
    history = view.layer.shared_history
    assert history is not None
    initial = history.session.state
    saved = project.load_plot_positions(), project.load_jobs(), project.load_history()
    filters.demographics.setChecked(True)
    filters.sex.setCurrentIndex(1)
    filters.ranges["weight"][0].setValue(55.5)
    filters.ranges["weight"][1].setValue(90.3)
    filters.ranges["height"][0].setValue(65.2)
    filters.apply_button.click()
    first = history.session.state
    assert first.filters.enabled and first.filters.bounds[-1] is None
    filters.demographics.setChecked(False)
    filters.ranges["weight"][0].setValue(60.7)
    filters.apply_button.click()
    disabled = history.session.state
    assert not disabled.filters.enabled and disabled.filters.sex == "Female"
    filters.tools.buttons[AssessmentKind.DUET].click()
    selected_tool = history.session.state
    assert selected_tool.filters.tool is AssessmentKind.DUET
    assert selected_tool.applied.tool is AssessmentKind.LIFFT
    filters.apply_button.click()
    applied_tool = history.session.state
    filters.risk_buttons[PlotRiskView.JOB].click()
    assert view.layer.results.selection.risk_view is PlotRiskView.JOB
    for expected in (applied_tool, selected_tool, disabled, first, initial):
        assert view.layer.undo()
        assert history.session.state == expected
        assert filters.snapshot() == expected.filters
        assert view.layer.results.selection == expected.applied
    assert not view.layer.undo()
    for expected in (first, disabled, selected_tool, applied_tool):
        assert view.layer.redo() and history.session.state == expected
    # A no-op Apply retains Redo; a new tool choice creates a genuine branch.
    filters.apply_button.click()
    assert history.session.redo_label_key is not None
    filters.tools.buttons[AssessmentKind.TST].click()
    assert history.session.redo_label_key is None
    assert (
        project.load_plot_positions(),
        project.load_jobs(),
        project.load_history(),
    ) == saved
    view.close()
    view.deleteLater()


def test_plot_scope_clear_replay_rejection_and_geometry_share_one_history(
    project: AssessmentProjectFile,
    tmp_path: Path,
) -> None:
    """Scope/Clear and saved marker moves replay chronologically without Save.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    view = host(project, tmp_path)
    layer = view.layer
    history = layer.shared_history
    assert history is not None
    initial = history.session.state
    item = layer.items["worker", 1]
    item.setPos(item.pos().x() + 30, item.pos().y() + 20)
    layer.moved(item)
    assert layer.save(("worker", 1))
    moved = history.session.state
    saved = project.load_plot_positions()
    assert view.filters.workplace.set_scope(PlotScope((("P", "T"),), "Day"))
    scoped = history.session.state
    assert scoped.applied is None and layer.results is None
    with patch.object(view.map_panel, "set_scope", return_value=False):
        assert not layer.undo() and history.session.state == scoped
    assert layer.undo() and history.session.state == moved
    assert layer.undo() and history.session.state == initial and layer.pending
    assert project.load_plot_positions() == saved
    assert layer.redo() and not layer.pending
    view.filters.tools.buttons[AssessmentKind.DUET].click()
    before_clear = history.session.state
    with patch.object(LifftWindow, "confirm_clear_assessment", return_value=True):
        view.filters.clear_button.click()
    assert layer.undo() and history.session.state == before_clear
    assert view.filters.tools.selected is AssessmentKind.DUET
    assert project.load_plot_positions() == saved
    view.close()
    view.deleteLater()


@pytest.mark.parametrize("language", tuple(Language))
def test_jrot_tool_pending_scope_and_applied_grid_are_independent_revisions(
    tmp_path: Path,
    language: Language,
) -> None:
    """Undo restores pending choices separately from Apply, with frozen pools.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    with seed(tmp_path / "scope.ergprj") as repository:
        view = RotationDialog(repository, load_icons(), language=language)
        view.show()
        initial = view.history.state
        saved = repository.load_rotation_schemes()
        view.tool_buttons[AssessmentKind.DUET].click()
        selected_tool = view.history.state
        assert selected_tool.display_kind is AssessmentKind.DUET
        scope = (repository.load_hierarchy().work.available_workplaces()[0],)
        with patch(
            "ergotools.presentation.desktop.rotation_dialog.RotationScopeDialog"
        ) as factory:
            factory.return_value.exec.return_value = QDialog.Accepted
            factory.return_value.selected_contexts.return_value = scope
            view.workplace_scope_button.click()
        pending = view.history.state
        assert pending.pending_scope == scope and pending.scope == ()
        assert pending.workplace_scope and pending.pool == initial.pool
        view.apply_scope_button.click()
        applied = view.history.state
        assert applied.scope == scope
        for expected in (pending, selected_tool, initial):
            view.replay_history(redo=False)
            assert view.history.state == expected
            assert view.kind == expected.display_kind
            assert view.pending_scope == expected.pending_scope
            assert view.workplace_scope_button.isChecked() == expected.workplace_scope
        for expected in (selected_tool, pending, applied):
            view.replay_history(redo=True)
            assert view.history.state == expected
        view.all_scope_button.click()
        all_pending = view.history.state
        assert not all_pending.workplace_scope and all_pending.scope == scope
        view.replay_history(redo=False)
        assert view.history.state == applied
        revision = view.history.revision
        with patch(
            "ergotools.presentation.desktop.rotation_dialog.RotationScopeDialog"
        ) as factory:
            factory.return_value.exec.return_value = QDialog.Rejected
            view.choose_scope_button.click()
        assert view.history.revision == revision and view.history.state == applied
        assert view.history.redo_label_key is not None
        assert repository.load_rotation_schemes() == saved
        view.close()


@pytest.mark.parametrize("index", [0, 1, 2])
def test_main_document_shortcuts_and_native_typing_remain_separate(
    window: LifftWindow,
    index: int,
) -> None:
    """Ctrl+Z/Redo reverses document edits; focused typing cannot fall through.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        index: Zero-based selected input/row/case index used by the parametrized
            regression.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(index)
    active = window.presenter.workspace.active
    source = active.state
    panel = window.task_panel if index == 0 else window.secondary_panel()
    with patch.object(LifftWindow, "confirm_clear_assessment", return_value=True):
        panel.clear_button.click()
    cleared = active.state
    assert source != cleared
    window.activateWindow()
    window.assessment_tabs.setFocus()
    _APP.processEvents()
    QTest.keyClick(window, Qt.Key_Z, Qt.ControlModifier)
    assert active.state == source
    QTest.keyClick(window, Qt.Key_Z, Qt.ControlModifier | Qt.ShiftModifier)
    assert active.state == cleared
    _APP.processEvents()
    panel = window.task_panel if index == 0 else window.secondary_panel()
    field = panel.inputs[0][2 if index == 0 else -1]
    assert field.isVisible()
    field.setFocus()
    _APP.processEvents()
    assert window.history_actions.focused_field() is field
    QTest.keyClicks(field, "123")
    revision = active.revision
    QTest.keyClick(field, Qt.Key_Z, Qt.ControlModifier)
    assert field.text() == "" and active.revision == revision
    QTest.keyClick(field, Qt.Key_Z, Qt.ControlModifier)
    assert active.revision == revision
    QTest.keyClick(field, Qt.Key_Z, Qt.ControlModifier | Qt.ShiftModifier)
    assert field.text() == "123" and active.revision == revision
    window._assessment_menu.edit.aboutToShow.emit()
    assert field.isUndoAvailable()
    assert window._assessment_menu.actions_by_key["undo"].isEnabled()
    window._assessment_menu.actions_by_key["undo"].trigger()
    assert field.text() == "" and active.revision == revision
    # Moving from an empty editor history to the grid must reactivate document
    # shortcuts without opening the menu or manually refreshing its actions.
    window.assessment_tabs.setFocus()
    _APP.processEvents()
    QTest.keyClick(window, Qt.Key_Z, Qt.ControlModifier)
    assert active.state == source

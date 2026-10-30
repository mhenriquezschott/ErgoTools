"""PLOT scoped hierarchy selection, literal values, colors and cancel boundaries.

Tests use detached results and disposable databases. Picker browsing never places
markers, accepts invalid field drafts or writes source/result data.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QTreeWidgetItemIterator

from ergotools.application.plot_results import saved_plot_results
from ergotools.bootstrap import load_icons
from ergotools.domain.language import Language
from ergotools.domain.plot_filters import PlotFilterSelection
from ergotools.domain.plot_scope import PlotScope
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.plot_marker_layer import PlotMarkerLayer
from ergotools.presentation.desktop.plot_result_picker import PlotResultPicker
from ergotools.presentation.desktop.plot_worker_overview import PlotWorkerOverview
from tests.test_plot_markers import canvas_with_map, positions_for
from tests.test_plot_results import project as project

# Retain one Qt application for real dialog selection and deferred-delete ownership.
_APP = QApplication.instance() or QApplication([])


def leaf_ids(dialog: PlotResultPicker) -> tuple[int, ...]:
    """Read selectable leaf identities without interpreting names or hierarchy depth.

    Args:
        dialog: Live read-only hierarchy picker.

    Returns:
        Assignment IDs in native tree order; branches are deliberately excluded.
    """
    result = []
    iterator = QTreeWidgetItemIterator(dialog.tree)
    while iterator.value() is not None:
        item = iterator.value()
        identity = item.data(0, Qt.ItemDataRole.UserRole)
        if type(identity) is int:
            result.append(identity)
        iterator += 1
    return tuple(result)


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("job_view", [False, True])
def test_hierarchy_picker_search_identity_and_literal_names(
    project: AssessmentProjectFile, language: Language, job_view: bool
) -> None:
    """Repeated workers/Jobs/stations retain exact ancestry and current model colors.

    Args:
        project: Disposable source, assignments and risk catalog.
        language: English/Spanish interface without translating saved identities.
        job_view: Both Job-occurrence and individual-assignment picker contexts.

    Returns:
        None; Cancel is read-only, branches cannot accept and literal HTML is escaped.
    """
    rows = saved_plot_results(
        project, PlotFilterSelection(PlotScope((("P",),))), current_year=2026
    ).workers
    before = project.load_plot_positions()
    dialog = PlotResultPicker(rows, load_icons(), job_view=job_view, language=language)
    assert set(leaf_ids(dialog)) == {1, 3, 5}
    plant = dialog.tree.topLevelItem(0)
    assert plant.text(0) == "P" and plant.childCount() == 2
    dialog.tree.setCurrentItem(plant)
    dialog.accept_selection()
    assert (
        dialog.selected_assignment_id is None and not dialog.select_button.isEnabled()
    )
    dialog.search_input.setText("  DAY  ")
    assert leaf_ids(dialog) == (5,)
    assert dialog.tree.currentItem().data(0, Qt.ItemDataRole.UserRole) == 5
    dialog.search_input.setText("does not exist")
    assert not leaf_ids(dialog) and not dialog.select_button.isEnabled()
    dialog.accept_selection()
    assert dialog.selected_assignment_id is None
    dialog.search_input.setText("  ALPHA ")
    assert leaf_ids(dialog) == (3,)
    dialog.search_input.clear()
    assert set(leaf_ids(dialog)) == {1, 3, 5}
    dialog.reject()
    assert dialog.selected_assignment_id is None
    dialog.deleteLater()
    row = replace(rows[0], worker=replace(rows[0].worker, last_name="<b>A & B</b>"))
    literal = PlotResultPicker(
        (row,), load_icons(), job_view=job_view, language=language
    )
    literal.search_input.setText("<b>A & B</b>")
    item = literal.tree.currentItem()
    assert "<b>A & B</b>" in item.text(0)
    assert "&lt;b&gt;A &amp; B&lt;/b&gt;" in item.toolTip(0)
    if job_view:
        assert item.text(2) == "0.0"  # A real zero Job risk is not missing evidence.
    literal.tree.itemDoubleClicked.emit(item, 0)
    assert literal.selected_assignment_id == row.assessment.assignment_id
    assert project.load_plot_positions() == before
    literal.close()
    literal.deleteLater()


def test_overview_picker_cancel_and_selection_outside_alphabet(
    project: AssessmentProjectFile, tmp_path: Path
) -> None:
    """Searching uses the applied scope; selecting outside a local letter reveals All.

    Args:
        project: Disposable real worker/Job catalogs and positions.
        tmp_path: Temporary synthetic map directory.

    Returns:
        None; Cancel retains partial input, acceptance browses without source writes.
    """
    positions_for(project)
    canvas = canvas_with_map(tmp_path)
    writer = Mock(wraps=project.save_plot_positions)
    layer = PlotMarkerLayer(
        canvas, project.load_jobs(), writer, Mock(), current_year=2026
    )
    panel = PlotWorkerOverview(layer, load_icons(), show_success=Mock())
    assert not panel.selector.isEnabled()
    panel.search()
    layer.set_results(
        saved_plot_results(
            project, PlotFilterSelection(PlotScope((("P",),))), current_year=2026
        )
    )
    panel.set_letter("A")
    assert panel.selected_id == 3
    panel.controls.x_input.setText("-")
    panel.controls.field_edited("-")
    before = project.load_plot_positions()
    errors: list[Exception] = []

    def answer(accept: bool) -> None:
        """Inspect the actual modal and answer its explicit acceptance boundary.

        Args:
            accept: True accepts the exact Day-shift assignment; False cancels.

        Returns:
            None; capture assertions for the enclosing test rather than Qt callbacks.
        """
        dialog = _APP.activeModalWidget()
        try:
            assert isinstance(dialog, PlotResultPicker)
            dialog.search_input.setText("Day")
            assert leaf_ids(dialog) == (5,)
            dialog.accept_selection() if accept else dialog.reject()
        except Exception as error:
            errors.append(error)
            if dialog is not None:
                dialog.close()

    QTimer.singleShot(0, lambda: answer(False))
    panel.search()
    assert not errors and panel.selected_id == 3 and panel.letter == "A"
    assert panel.controls.x_input.text() == "-"
    QTimer.singleShot(0, lambda: answer(True))
    panel.search()
    assert not errors and panel.selected_id == 5 and panel.letter == "All"
    assert panel.controls.field_drafts[3][0] == "-"
    assert project.load_plot_positions() == before and writer.call_count == 0
    panel.close()
    canvas.close()

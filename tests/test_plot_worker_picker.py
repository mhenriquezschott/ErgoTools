"""Original PLOT search semantics and stable modal selection handoff.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication

from ergotools.application.plot_results import saved_plot_results
from ergotools.bootstrap import load_icons
from ergotools.domain.language import Language
from ergotools.domain.plot_filters import PlotFilterSelection
from ergotools.domain.plot_scope import PlotScope
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.plot_marker_layer import PlotMarkerLayer
from ergotools.presentation.desktop.plot_worker_overview import PlotWorkerOverview
from ergotools.presentation.desktop.plot_worker_picker import PlotWorkerPicker
from tests.test_plot_markers import canvas_with_map, positions_for
from tests.test_plot_results import project as project

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("language", [Language.ENGLISH, Language.SPANISH])
def test_picker_live_scope_literal_search_and_identity(
    project: AssessmentProjectFile,
    language: Language,
) -> None:
    """Repeated workers/station labels resolve by ancestry and stable assignment.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    rows = saved_plot_results(
        project, PlotFilterSelection(PlotScope((("P",),))), current_year=2026
    ).workers
    before = project.load_plot_positions()
    dialog = PlotWorkerPicker(rows, load_icons(), language=language)
    assert dialog.results.topLevelItemCount() == 3
    assert dialog.scope_path == ()
    plant = dialog.workplace_tree.topLevelItem(0)
    assert plant is not None
    section = plant.child(1)
    assert section is not None
    dialog.workplace_tree.setCurrentItem(section)
    assert dialog.scope_path == ("P", "T")
    assert dialog.results.topLevelItemCount() == 1
    dialog.search_input.setText("  DAY  ")
    assert dialog.results.topLevelItemCount() == 1
    assert dialog.results.currentItem().data(0, Qt.ItemDataRole.UserRole) == 5
    dialog.search_input.setText("All")
    assert dialog.results.topLevelItemCount() == 0
    assert not dialog.select_button.isEnabled()
    dialog.accept_selection()
    assert dialog.selected_assignment_id is None
    dialog.change_scope(None)
    assert dialog.results.topLevelItemCount() == 2
    dialog.search_input.setText("  ALPHA ")
    assert dialog.results.topLevelItemCount() == 1
    dialog.search_input.clear()
    assert dialog.results.topLevelItemCount() == 3
    dialog.reject()
    assert dialog.selected_assignment_id is None
    row = rows[0]
    literal = replace(row, worker=replace(row.worker, last_name="<b>A & B</b>"))
    dialog = PlotWorkerPicker((literal,), load_icons(), language=language)
    dialog.search_input.setText("<b>A & B</b>")
    item = dialog.results.currentItem()
    assert item is not None
    assert item.text(1).startswith("<b>A & B</b>")
    assert "&lt;b&gt;A &amp; B&lt;/b&gt;" in item.toolTip(1)
    dialog.results.itemDoubleClicked.emit(item, 0)
    assert dialog.selected_assignment_id == row.assessment.assignment_id
    assert project.load_plot_positions() == before
    dialog.close()


def test_overview_modal_cancel_and_hidden_assignment_selection(
    project: AssessmentProjectFile,
    tmp_path: Path,
) -> None:
    """Cancel retains partial edits; accepted search reveals the correct hidden row.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    positions_for(project)
    canvas = canvas_with_map(tmp_path)
    writer = Mock(wraps=project.save_plot_positions)
    layer = PlotMarkerLayer(
        canvas, project.load_jobs(), writer, Mock(), current_year=2026
    )
    panel = PlotWorkerOverview(layer, load_icons(), show_success=Mock())
    assert not panel.search_button.isEnabled()
    panel.search()
    layer.set_results(
        saved_plot_results(
            project, PlotFilterSelection(PlotScope((("P",),))), current_year=2026
        )
    )
    assert panel.search_button.isEnabled()
    panel.set_letter("A")
    assert panel.selected_id == 3
    panel.controls.x_input.setText("-")
    panel.controls.field_edited("-")
    before = project.load_plot_positions()
    errors: list[Exception] = []

    def answer(accept: bool) -> None:
        """Filter the actual worker picker to Day, verify one exact result.

        Filter the actual worker picker to Day, verify one exact result and accept or
        reject according to the supplied intent.

        Args:
            accept: True accepts the exact selected row; False rejects the modal without
                changing the owner.

        Returns:
            None.
        """
        dialog = _APP.activeModalWidget()
        try:
            assert isinstance(dialog, PlotWorkerPicker)
            dialog.search_input.setText("Day")
            assert dialog.results.topLevelItemCount() == 1
            if accept:
                dialog.accept_selection()
            else:
                dialog.reject()
        except Exception as error:
            errors.append(error)
            if dialog is not None:
                dialog.close()

    QTimer.singleShot(0, lambda: answer(False))
    panel.search()
    assert not errors
    assert panel.letter == "A" and panel.selected_id == 3
    assert panel.controls.x_input.text() == "-"
    QTimer.singleShot(0, lambda: answer(True))
    panel.search()
    assert not errors
    assert panel.selected_id == 5 and panel.controls.identity == 5
    assert panel.letter == "All"
    assert ("worker", 5) not in layer.items
    panel.marker_selected(("worker", 3))
    assert panel.controls.x_input.text() == "-"
    assert writer.call_count == 0 and project.load_plot_positions() == before
    panel.close()
    canvas.close()

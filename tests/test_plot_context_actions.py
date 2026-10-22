"""Original worker menu and assessment handoff through the integrated editor.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QMenu

from ergotools.application.assessment_export import saved_summary_rows
from ergotools.application.plot_results import saved_plot_results
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.plot_filters import PlotFilterSelection
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.plot_marker_layer import PlotMarkerLayer
from tests.test_plot_markers import canvas_with_map, positions_for
from tests.test_plot_results import SCOPE
from tests.test_plot_results import project as project
from tests.test_saved_tool_data import window as window

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("language", [Language.ENGLISH, Language.SPANISH])
def test_worker_menu_lock_save_failure_and_exact_load(
    project: AssessmentProjectFile,
    tmp_path: Path,
    language: Language,
) -> None:
    """Menu actions preserve identity, failed intent and explicit write boundaries.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    positions_for(project)
    canvas = canvas_with_map(tmp_path)
    error, writer, load = (
        Mock(),
        Mock(wraps=project.save_plot_positions),
        Mock(return_value=True),
    )
    layer = PlotMarkerLayer(
        canvas,
        project.load_jobs(),
        writer,
        error,
        current_year=2026,
        language=language,
        load_assessment=load,
    )
    layer.set_results(
        saved_plot_results(project, PlotFilterSelection(SCOPE), current_year=2026)
    )
    menu = layer.worker_menu(3)
    lock, save, handoff = menu.actions()
    assert [action.text() for action in menu.actions()] == (
        ["Lock", "Save", "Load into Tool Window"]
        if language is Language.ENGLISH
        else ["Bloquear", "Guardar", "Cargar en la ventana de evaluación"]
    )
    assert all(action.icon().isNull() for action in menu.actions())
    assert writer.call_count == 0
    lock.trigger()
    assert layer.items["worker", 3].locked and layer.pending
    assert (
        not layer.items["worker", 3].flags()
        & layer.items["worker", 3].GraphicsItemFlag.ItemIsMovable
    )
    handoff.trigger()
    assert not load.called and error.call_count == 1
    writer.side_effect = OSError("disk")
    save.trigger()
    assert layer.pending and error.call_count == 2
    writer.side_effect = None
    save.trigger()
    assert not layer.pending and project.load_plot_positions().marker(3).locked
    handoff.trigger()
    row = load.call_args.args[0]
    assert row.assignment_id == 3 and row.owner.worker_id == "x"
    assert row.kind is AssessmentKind.LIFFT
    load.return_value = False
    assert not layer.load_worker(3)
    load.side_effect = OSError("load")
    assert not layer.load_worker(3) and error.call_count == 3
    layer.load_assessment = None
    disabled = layer.worker_menu(1)
    assert not disabled.actions()[-1].isEnabled() and not layer.load_worker(1)
    # Real right-click runs the menu for the clicked item and releases it on exit.
    layer.load_assessment = load
    canvas.show()
    _APP.processEvents()
    item = layer.items["worker", 1]
    point = canvas.mapFromScene(item.mapToScene(item.marker_rect().center()))
    seen: list[str] = []

    def close_menu() -> None:
        """Record the actual worker popup actions and close the native menu.

        Record the actual worker popup actions and close the native menu without
        triggering persistence.

        Args:
            None.

        Returns:
            None.
        """
        popup = _APP.activePopupWidget()
        if isinstance(popup, QMenu):
            seen.extend(action.text() for action in popup.actions())
            popup.close()

    QTimer.singleShot(50, close_menu)
    QTest.mouseClick(canvas.viewport(), Qt.MouseButton.RightButton, pos=point)
    assert seen and item.isSelected()
    menu.close()
    disabled.close()
    canvas.close()


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_plot_handoff_retains_edits_and_saved_units_until_main_save(
    window: LifftWindow,
    kind: AssessmentKind,
) -> None:
    """PLOT handoff retains accepted edits and loads the exact owner/tool source.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
            captions are not keys.

    Returns:
        None.
    """
    workspace = window.presenter.workspace
    with AssessmentProjectFile.open(Path(workspace.location)) as repository:
        row = next(
            row
            for row in saved_summary_rows(repository, kind)
            if row.assignment_id == 3 and row.kind is kind
        )
        same = next(
            row
            for row in saved_summary_rows(repository, AssessmentKind.LIFFT)
            if row.assignment_id == 1 and row.kind is AssessmentKind.LIFFT
        )
        expected = repository.load(row.document)
    field = window.task_panel.inputs[0][2]
    field.setText("999")
    field.textEdited.emit("999")
    original = workspace.active
    assert window.load_plot_assessment(same)
    assert workspace.active is original and field.text() == "999"
    foreign = replace(row, document=replace(row.document, project_id="foreign"))
    with pytest.raises(ValueError, match="another project"):
        window.load_plot_assessment(foreign)
    assert field.text() == "999"
    with pytest.raises(ValueError, match="saved ownership"):
        window.load_plot_assessment(
            replace(row, document=replace(row.document, document_id="old"))
        )
    with patch.object(window, "dirty_choice") as departure:
        assert window.load_plot_assessment(row)
    departure.assert_not_called()
    assert workspace.active.document == row.document
    assert window.active_kind() is kind
    assert workspace.active.state == expected

    with AssessmentProjectFile.open(Path(workspace.location)) as repository:
        assert repository.load(original.document).tasks[0].repetitions != 999
        assert (
            workspace.editing.repository.load(original.document).tasks[0].repetitions
            == 999
        )
        positions = repository.load_plot_positions()
    panel = window.secondary_panel() or window.task_panel
    field = panel.inputs[0][2 if kind is AssessmentKind.LIFFT else -1]
    field.setText("888")
    field.textEdited.emit("888")
    with patch.object(window, "dirty_choice") as departure:
        assert window.load_plot_assessment(same)
    departure.assert_not_called()
    assert workspace.editing.repository.load(row.document).tasks[0].repetitions == 888
    with AssessmentProjectFile.open(Path(workspace.location)) as repository:
        assert repository.load(row.document) == expected
        assert repository.load_plot_positions() == positions

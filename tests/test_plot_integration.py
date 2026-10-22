"""PLOT CSV fidelity and actual main-navigation modal/saved-assessment integration.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import csv
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.plot_results import saved_plot_results
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.plot_filters import PlotFilterSelection
from ergotools.domain.plot_positions import WorkerAssignmentMarker
from ergotools.domain.plot_scope import PlotScope
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.plot_csv_file import write_plot_csv
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.plot_window import PlotWindow
from ergotools.presentation.plot_csv import PLOT_HEADERS, plot_csv_table
from tests.test_plot_results import project as project
from tests.test_plot_window import host
from tests.test_saved_tool_data import window as window


def test_csv_saved_identity_precision_units_absence_zero_and_quoting(
    project: AssessmentProjectFile, tmp_path: Path
) -> None:
    """Retain original columns, missing versus zero, and source provenance.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    result = saved_plot_results(
        project, PlotFilterSelection(PlotScope((("P",),))), current_year=2026
    )
    table = plot_csv_table(result, MeasurementSystem.IMPERIAL)
    assert table[0] == PLOT_HEADERS and all(
        len(row) == len(PLOT_HEADERS) for row in table
    )
    rows = [dict(zip(PLOT_HEADERS, row, strict=True)) for row in table[1:]]
    first = next(row for row in rows if row["worker_assignment_id"] == "1")
    assert first["worker_id"] == "w" and "assessment_version" not in first
    assert (
        first["job_probability_outcome"] == "0"
        or first["job_probability_outcome"] == "0.0"
    )
    assert float(first["worker_weight"]) == pytest.approx(70 * 2.2046226218487757)
    assert first["worker_body_unit"] == "Imperial" and first["worker_height"] == ""
    absent = next(row for row in rows if row["worker_id"] == "x")
    assert absent["gender"] == "" and absent["worker_weight"] == ""
    shoulder = saved_plot_results(
        project,
        PlotFilterSelection(PlotScope((("P",),)), AssessmentKind.TST),
        current_year=2026,
    )
    assert all(
        float(row[PLOT_HEADERS.index("probability_outcome")]) > 0
        for row in plot_csv_table(shoulder, MeasurementSystem.METRIC)[1:]
    )
    literal = replace(
        result,
        workers=(
            replace(
                result.workers[0],
                worker=replace(result.workers[0].worker, first_name='A,"B"\nC'),
            ),
        ),
    )
    destination = tmp_path / "export.csv"
    destination.write_text("old file")
    write_plot_csv(str(destination), plot_csv_table(literal, MeasurementSystem.METRIC))
    with destination.open(newline="", encoding="utf-8") as stream:
        exported = list(csv.reader(stream))
    assert exported[1][PLOT_HEADERS.index("first_name")] == 'A,"B"\nC'
    assert not list(tmp_path.glob(".ergotools-plot-*"))
    before = destination.read_bytes()
    with (
        patch(
            "ergotools.infrastructure.plot_csv_file.os.replace",
            side_effect=OSError("publication failure"),
        ),
        pytest.raises(OSError),
    ):
        write_plot_csv(str(destination), table)
    assert destination.read_bytes() == before and not list(
        tmp_path.glob(".ergotools-plot-*")
    )


def test_csv_dialog_cancel_success_error_empty_and_pending_preservation(
    project: AssessmentProjectFile, tmp_path: Path
) -> None:
    """Export saved snapshots without saving editor or map intent.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    writer = Mock()
    view = host(project, tmp_path, csv_writer=writer)
    panel = view.map_panel
    panel.message = Mock()
    before = project.load_plot_positions(), project.read("P")
    view.layer.preview_worker(WorkerAssignmentMarker(1, visible=False))
    drafts = dict(view.layer.worker_drafts)
    view.choose_csv = Mock(return_value="")
    panel.buttons["export"].click()
    writer.assert_not_called()
    view.choose_csv.return_value = str(tmp_path / "out.csv")
    panel.buttons["export"].click()
    assert writer.call_count == 1
    writer.side_effect = OSError("fixture export failure")
    panel.show_error = Mock()
    panel.buttons["export"].click()
    panel.show_error.assert_called_once()
    with patch.object(QFileDialog, "getSaveFileName", return_value=("", "")) as choose:
        assert type(view).choose_csv(view) == ""
    assert choose.call_args.args[2].startswith("WorkerStationShiftData_")
    assert view.layer.worker_drafts == drafts
    view.layer.cancel(("worker", 1))
    view.filters.workplace.set_scope(PlotScope((("Empty",),)))
    view.filters.apply_filters()
    panel.buttons["export"].click()
    assert writer.call_count == 2
    assert (project.load_plot_positions(), project.read("P")) == before
    view.close()
    view.deleteLater()


@pytest.mark.parametrize("language", tuple(Language))
def test_actual_navigation_borrowed_project_map_upgrade_and_duet_handoff(
    window: LifftWindow, language: Language
) -> None:
    """The PLOT action opens its modal and loads another exact worker/model.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    window.language = language
    window.translate()
    window.refresh()
    workspace = window.presenter.workspace
    repository = workspace.plot_repository()
    assert repository is workspace.plot_repository()
    history = workspace.read_history().history
    visited = []
    failures = []
    timer = QTimer(window)
    timer.setSingleShot(True)

    def interact() -> None:
        """Check borrowed PLOT repository/language.

        Check borrowed PLOT repository/language, Apply DUET, request exact saved worker
        x handoff and return callback failures to pytest.

        Args:
            None.

        Returns:
            None.
        """
        view = QApplication.activeModalWidget()
        try:
            assert isinstance(view, PlotWindow)
            visited.append(view)
            assert view.repository is repository and view.language is language
            assert (
                view.csv_writer is not None
                and view.map_panel.buttons["export"].isEnabled()
            )
            view.filters.tools.select_tool(AssessmentKind.DUET)
            view.filters.apply_filters()
            selected = next(
                row for row in view.layer.results.workers if row.worker.worker_id == "x"
            )
            menu = view.layer.worker_menu(selected.assessment.assignment_id)
            menu.actions()[2].trigger()
            assert not view.isVisible()
        except BaseException as error:
            failures.append(error)
            if isinstance(view, PlotWindow):
                view.reject()

    timer.timeout.connect(interact)
    timer.start(0)
    action = window.main_navigation.toolbar_actions["plot"]
    assert action.isEnabled()
    action.trigger()
    timer.stop()
    assert visited and not failures, failures
    assert window.duet_active and workspace.active.document.document_id == "duet-3"
    assert workspace.read_history().history == history
    assert workspace.plot_repository() is repository
    # The same handle remains usable after explicit PLOT saves/format upgrades.
    from io import BytesIO

    from PIL import Image

    from ergotools.domain.plant_layout_image import PlantLayoutImage

    data = BytesIO()
    Image.new("RGB", (20, 20), "white").save(data, format="PNG")
    repository.save_plant_image(
        workspace.read_hierarchy().hierarchy.plants[0],
        PlantLayoutImage(data.getvalue()),
    )
    assert (
        repository.read(workspace.read_hierarchy().hierarchy.plants[0])
        == data.getvalue()
    )
    workspace.save()
    assert workspace.read_history().history == history


def test_plot_navigation_clean_close_and_missing_project(window: LifftWindow) -> None:
    """Cancel keeps the assessment; no-project navigation disables PLOT.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    current = window.presenter.workspace.active
    timer = QTimer(window)
    timer.setSingleShot(True)
    visited = []

    def cancel() -> None:
        """Record and close the actual PLOT modal.

        Record and close the actual PLOT modal without modifying assessment or map data.

        Args:
            None.

        Returns:
            None.
        """
        view = QApplication.activeModalWidget()
        assert isinstance(view, PlotWindow)
        visited.append(view)
        view.close()

    timer.timeout.connect(cancel)
    timer.start(0)
    window.main_navigation.toolbar_actions["plot"].trigger()
    timer.stop()
    assert visited and window.presenter.workspace.active is current
    window.presenter.workspace.close(choice=CloseChoice.DISCARD)
    window.refresh()
    assert not window.main_navigation.toolbar_actions["plot"].isEnabled()
    window.open_plot()
    with pytest.raises(ValueError):
        window.presenter.workspace.plot_repository()


def test_modal_escape_uses_unsaved_edit_consent(
    project: AssessmentProjectFile, tmp_path: Path
) -> None:
    """Escape Cancel preserves pending map intent; confirmed discard rejects once.

    Args:
        project: Isolated native project fixture owned by this test; never the reference
            checkout.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    view = host(project, tmp_path)
    view.layer.preview_worker(WorkerAssignmentMarker(1, visible=False))
    timer = QTimer(view)
    timer.setSingleShot(True)
    visited = []
    answer = QMessageBox.No

    def respond() -> None:
        """Record the native unsaved-map consent message.

        Record the native unsaved-map consent message and supply the parametrized Qt
        response.

        Args:
            None.

        Returns:
            None.
        """
        box = QApplication.activeModalWidget()
        assert isinstance(box, QMessageBox)
        visited.append(box.text())
        box.done(answer)

    timer.timeout.connect(respond)
    timer.start(0)
    QTest.keyClick(view, Qt.Key_Escape)
    timer.stop()
    assert len(visited) == 1 and view.isVisible() and view.layer.pending
    answer = QMessageBox.Yes
    timer.start(0)
    QTest.keyClick(view, Qt.Key_Escape)
    timer.stop()
    assert len(visited) == 2 and not view.isVisible()
    view.deleteLater()

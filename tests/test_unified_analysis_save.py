"""PLOT/JROT accepted edits share project Save and survive modal closure.

Real native projects, marker/source controls and frozen rotation pools verify private
versus durable data. No operational/reference files or maintained fixtures are mutated.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image
from PyQt5.QtWidgets import QApplication

from ergotools.application.project_editing import ProjectEditingSession
from ergotools.bootstrap import load_icons
from ergotools.domain.language import Language
from ergotools.domain.plot_filters import PlotRiskView
from ergotools.domain.plot_positions import PlotPoint
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.plant_image_import import import_plant_image
from ergotools.presentation.desktop.plot_window import PlotWindow
from ergotools.presentation.desktop.rotation_dialog import RotationDialog
from tests.test_plot_markers import positions_for
from tests.test_plot_results import project as project
from tests.test_rotation_dialog import fill
from tests.test_rotation_persistence import seed

# Retain the shared QApplication for actual marker and table controls.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("language", list(Language))
def test_plot_move_close_reopen_shared_undo_and_main_commit(
    project: AssessmentProjectFile, tmp_path: Path, language: Language
) -> None:
    """Accepted marker changes survive closing and publish only with project Save.

    Args:
        project: Existing isolated PLOT project fixture with real associated sources.
        tmp_path: Disposable image/project directory owned by pytest.
        language: English/Spanish controls exercise the same accepted data contract.

    Returns:
        None; Undo restores the preceding coordinates without a disk write.
    """
    image_path = tmp_path / "map.png"
    Image.new("RGB", (640, 400), "white").save(image_path)
    project.save_plant_image("P", import_plant_image(image_path))
    project.save_plot_positions(positions_for(project))
    editing = ProjectEditingSession(project.metadata.project_id, project)
    original = project.load_plot_positions()
    dialog = PlotWindow(
        project,
        project,
        project,
        lambda path: import_plant_image(Path(path)),
        load_icons(),
        current_year=2026,
        language=language,
        editing=editing,
    )
    try:
        assert dialog.map_panel.buttons["save"].isHidden()
        assert dialog.workers.controls.save_button.isHidden()
        marker = dialog.layer.worker_settings(1)
        dialog.layer.preview_worker(replace(marker, point=PlotPoint(123, 234)))
        assert project.load_plot_positions().marker(1).point == PlotPoint(123, 234)
        assert editing.is_dirty
        assert dialog.confirm_close()
        assert editing.replay(redo=False)
        assert project.load_plot_positions() == original
        assert editing.replay(redo=True)
        dialog.close()
        reopened = PlotWindow(
            project,
            project,
            project,
            lambda path: import_plant_image(Path(path)),
            load_icons(),
            current_year=2026,
            language=language,
            editing=editing,
        )
        try:
            assert reopened.layer.worker_settings(1).point == PlotPoint(123, 234)
        finally:
            reopened.close()
        editing.commit()
        assert not editing.is_dirty
    finally:
        dialog.close()


@pytest.mark.parametrize("language", list(Language))
def test_rotation_partial_reopen_complete_commit_and_shared_replay(
    tmp_path: Path, language: Language
) -> None:
    """Partial JROT drafts survive close and block Save until complete or cancelled.

    Args:
        tmp_path: Disposable native project directory.
        language: English/Spanish modal controls.

    Returns:
        None; complete frozen schemes publish only through the shared project commit.
    """
    path = tmp_path / "rotation.ergprj"
    with seed(path, version=19) as repository, patch.object(RotationDialog, "_message"):
        before = path.read_bytes()
        editing = ProjectEditingSession(repository.metadata.project_id, repository)
        dialog = RotationDialog(
            repository, load_icons(), language=language, editing=editing
        )
        try:
            assert dialog.save_button.isHidden()
            dialog.new_scheme()
            dialog.scheme_combo.setEditText("workflow")
            dialog.grid.set_choice(0, 0, "w")
            dialog.close()
            assert editing.is_dirty
            with pytest.raises(ValueError, match=r"project\.rotation_draft_incomplete"):
                editing.commit()
            assert path.read_bytes() == before
            reopened = RotationDialog(
                repository, load_icons(), language=language, editing=editing
            )
            try:
                assert reopened.scheme_combo.currentText() == "workflow"
                assert reopened.grid.choice_key(0, 0) == "w"
                fill(reopened, "workflow")
                reopened.close()
                assert path.read_bytes() == before
                assert repository.load_rotation_schemes()[0].scheme_id == "workflow"
                editing.commit()
                assert not editing.is_dirty
                assert editing.replay(redo=False)
                assert editing.is_dirty
                assert editing.replay(redo=True)
            finally:
                reopened.close()
        finally:
            dialog.close()
    with AssessmentProjectFile.open(path) as saved:
        assert saved.load_rotation_schemes()[0].scheme_id == "workflow"


def test_rotation_viewing_saved_and_cancelling_partial_remain_clean(
    tmp_path: Path,
) -> None:
    """Viewing a saved scheme or cancelling a new partial draft never requires Save.

    Args:
        tmp_path: Disposable native project directory owned by pytest.

    Returns:
        None; native data and the persistent draft marker remain at their baseline.
    """
    from tests.test_rotation_persistence import scheme

    path = tmp_path / "rotation.ergprj"
    with seed(path, version=19) as repository:
        repository.save_rotation_scheme(scheme())
        editing = ProjectEditingSession(repository.metadata.project_id, repository)
        dialog = RotationDialog(repository, load_icons(), editing=editing)
        try:
            dialog.close()
            assert not editing.is_dirty
            dialog.new_scheme()
            dialog.scheme_combo.setEditText("Partial")
            dialog.grid.set_choice(0, 0, "w")
            assert editing.is_dirty
            dialog.cancel_scheme()
            assert not editing.is_dirty
            editing.commit()
        finally:
            dialog.close()


@pytest.mark.parametrize("mode", [PlotRiskView.JOB, PlotRiskView.COMPARISON])
def test_plot_mode_and_drag_have_separate_shared_history(
    project: AssessmentProjectFile, tmp_path: Path, mode: PlotRiskView
) -> None:
    """Undo a map move independently of the immediately preceding mode change.

    Args:
        project: Isolated native project containing worker and Job assessments.
        tmp_path: Disposable image directory owned by pytest.
        mode: Applied assignment representation whose geometry must remain shared.

    Returns:
        None; move Undo/Redo retains the selected mode and exact assignment point.
    """
    image_path = tmp_path / "map.png"
    Image.new("RGB", (640, 400), "white").save(image_path)
    project.save_plant_image("P", import_plant_image(image_path))
    project.save_plot_positions(positions_for(project))
    editing = ProjectEditingSession(project.metadata.project_id, project)
    dialog = PlotWindow(
        project,
        project,
        project,
        lambda path: import_plant_image(Path(path)),
        load_icons(),
        current_year=2026,
        editing=editing,
    )
    try:
        dialog.filters.risk_buttons[mode].click()
        key = ("job" if mode is PlotRiskView.JOB else "worker", 1)
        item = dialog.layer.items[key]
        original = item.anchor_point()
        item.setPos(123.125, 234.25)
        dialog.layer.moved(item)
        assert project.load_plot_positions().marker(1).point == PlotPoint(
            123.125, 234.25
        )
        dialog.history_actions.replay(redo=False)
        assert dialog.filters.risk_view is mode
        assert dialog.layer.items[key].anchor_point() == original
        dialog.history_actions.replay(redo=True)
        assert dialog.filters.risk_view is mode
        assert dialog.layer.items[key].anchor_point() == PlotPoint(123.125, 234.25)
    finally:
        dialog.close()

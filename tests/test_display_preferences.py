"""Regression coverage for exact inputs, project decimals and all-region overlays.

Test layer: use disposable classified projects and real Qt fields/dialogs. Exercise
ordinary user editing, project reopen/snapshots and the replaceable renderer contract;
never write reference applications or permanent test projects.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QMessageBox

from ergotools.application.contracts.body_renderer import BodyRegion, BodyViewState
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.display_precision import DisplayPrecision
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.precision_editor import PrecisionLineEdit
from ergotools.presentation.desktop.preferences_dialog import PreferencesDialog
from tests.test_saved_tool_data import window as window


@pytest.mark.parametrize("index", [0, 2])
def test_rounded_inputs_preserve_other_fields_and_unit_roundtrips(
    window: LifftWindow, index: int
) -> None:
    """Editing repetitions must not quantize unchanged converted arm/load values.

    Args:
        window: Fixture-owned integrated window with all three classified tools.
        index: LiFFT or ST tab index, whose continuous inputs convert between units.

    Returns:
        None; assert exact source equality for unchanged fields through repeated
        toggles.
    """
    window.select_tool(index)
    workspace = window.presenter.workspace
    before = workspace.active.state
    window.presenter.system = MeasurementSystem.METRIC
    window.refresh()
    panel = window.secondary_panel() or window.task_panel
    arm = panel.inputs[0][0 if index == 0 else 1]
    assert arm.text() == "30.5"
    assert arm.source_text() == "30.48"
    repetitions = panel.inputs[0][-1]
    repetitions.setText("123")
    repetitions.textEdited.emit("123")
    panel.commit_inputs()
    after = workspace.active.state
    assert after.tasks[0].lever_arm == before.tasks[0].lever_arm
    assert after.tasks[0].load == before.tasks[0].load
    assert after.tasks[0].repetitions == 123
    for system in (MeasurementSystem.IMPERIAL, MeasurementSystem.METRIC) * 3:
        window.presenter.system = system
        window.refresh()
        assert workspace.active.state is after
        assert not (window.secondary_panel() or window.task_panel).commit_inputs()


def test_unified_settings_persist_precision_in_project_and_snapshots(
    window: LifftWindow, tmp_path: Path
) -> None:
    """Toolbar/menu use one modal; Apply saves project policy without rounding inputs.

    Args:
        window: Fixture-owned integrated main window with a disposable native project.
        tmp_path: Pytest-owned destinations for complete project copies.

    Returns:
        None; verify reopen, Save As and Backup retain identical preferences and
        sources.
    """
    workspace = window.presenter.workspace
    before = workspace.active.state
    requested = DisplayPrecision(2, 3, 2, 6, 2)

    def apply() -> None:
        """Drive actual settings controls and accept once.

        Args:
            None.

        Returns:
            None; modal acceptance returns control to the owning host.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, PreferencesDialog)
        for key, field in dialog.decimal_fields.items():
            field.setValue(getattr(requested, key))
        dialog.units.setCurrentIndex(
            list(MeasurementSystem).index(MeasurementSystem.METRIC)
        )
        dialog.animated_focus.setChecked(False)
        assert not dialog.reset_tasks.isChecked()
        dialog.apply_button.click()

    QTimer.singleShot(0, apply)
    window.main_navigation.toolbar_actions["settings"].trigger()
    assert not window._settings_store.load().animated_body_region_focus
    assert not window._assessment_menu.camera_animation.isChecked()
    assert workspace.project_metadata.precision == requested
    assert workspace.active.state is before
    assert window.task_panel.inputs[0][0].text() == "30.48"
    window.task_panel.calculate_button.click()
    calculation = window.presenter.evaluator.current(workspace.active)
    assert (
        window.results_sidebar.risk_gauge.target_value
        == calculation.summary.probability * 100
    )
    original = workspace.location
    with AssessmentProjectFile.open(Path(original)) as project:
        assert project.metadata.precision != requested
    window.save_project()
    with AssessmentProjectFile.open(Path(original)) as project:
        assert project.metadata.precision == requested
        assert project.metadata.default_units is MeasurementSystem.METRIC
        assert project.load(workspace.active.document) == before
    for command, name in (
        (window.backup_project, "backup"),
        (window.save_project_as, "copy"),
    ):
        destination = tmp_path / (name + ".ergprj")
        with (
            patch.object(window, "choose_file", return_value=str(destination)),
            patch.object(window, "choose_project_details", return_value=("Copy", "")),
        ):
            command()
        with AssessmentProjectFile.open(destination) as project:
            assert project.metadata.precision == requested
            assert project.load(workspace.active.document) == before
    workspace.close(choice=CloseChoice.DISCARD)
    window.open_project_location(original)
    assert window.presenter.system is MeasurementSystem.METRIC
    assert not window._settings_store.load().animated_body_region_focus
    assert not window._assessment_menu.camera_animation.isChecked()
    assert workspace.project_metadata.precision == requested


def test_task_reset_requires_confirmation_and_remains_undoable(
    window: LifftWindow,
) -> None:
    """Cancel preserves data; confirmed tail removal retains the prefix and can undo.

    Args:
        window: Fixture-owned main window with populated LiFFT inputs.

    Returns:
        None; exercise both modal confirmation paths and existing document history.
    """
    window.presenter.set_task_count(12)
    window.refresh()
    field = window.task_panel.inputs[11][2]
    field.setText("100")
    field.textEdited.emit("100")
    window.task_panel.commit_inputs()
    window.refresh()
    before = window.active_source()

    def request_reset() -> None:
        """Request removal of a populated trailing row in the unified settings modal.

        Args:
            None.

        Returns:
            None; host must still request separate destructive-action confirmation.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, PreferencesDialog)
        dialog.reset_tasks.setChecked(True)
        dialog.count.setValue(11)
        dialog.apply_button.click()

    for answer in (QMessageBox.Cancel, QMessageBox.Yes):
        QTimer.singleShot(0, request_reset)
        with patch.object(
            window, "confirm_task_reset", return_value=answer == QMessageBox.Yes
        ):
            window.open_preferences()
        if answer == QMessageBox.Cancel:
            assert window.active_source() is before
    assert len(window.active_source().tasks) == 11
    assert window.active_source().tasks == before.tasks[:11]
    window.undo()
    assert window.active_source() == before


class RecordingRenderer:
    """Record immutable display requests without owning a renderer backend."""

    def set_state(self, state: BodyViewState) -> None:
        """Capture the typed host projection without interpreting scientific inputs.

        Args:
            state: Immutable complete anatomical display request.

        Returns:
            None; retain the latest snapshot for assertions.
        """
        self.state = state


def test_avatar_projects_all_tools_without_switching_owner(window: LifftWindow) -> None:
    """Keep all three overlays tied to one assignment and active focus separate.

    Args:
        window: Fixture-owned all-tool project with two same-workplace Job owners.

    Returns:
        None; verify missing regions clear and previewing never switches/saves sources.
    """
    renderer = RecordingRenderer()
    with patch.object(window, "_body_renderer", renderer):
        for index, region in enumerate(
            (
                BodyRegion.LOW_BACK,
                BodyRegion.DISTAL_UPPER_EXTREMITIES,
                BodyRegion.SHOULDERS,
            )
        ):
            window.select_tool(index)
            panel = window.secondary_panel() or window.task_panel
            panel.calculate_button.click()
            active = window.presenter.workspace.active
            before = active.state
            window.show_result()
            assert renderer.state.region is region
            assert {r for r, _ in renderer.state.region_colors} == {
                BodyRegion.LOW_BACK,
                BodyRegion.DISTAL_UPPER_EXTREMITIES,
                BodyRegion.SHOULDERS,
            }
            assert (
                window.presenter.workspace.active is active and active.state is before
            )
        sources = window.assessment_navigation.overlay_sources()
        assert all(s.tasks[0].repetitions == 100 for s in sources)
        with patch.object(window, "dirty_choice", return_value=CloseChoice.DISCARD):
            window.close_project()
        assert renderer.state.region_colors == ()
        assert renderer.state.overlay_color is None


def test_native_typing_undo_restores_exact_hidden_value() -> None:
    """Undoing all text edits restores exact input instead of committing its rounding.

    Args:
        None.

    Returns:
        None; real key events also distinguish intentionally replacing a rounded value.
    """
    editor = PrecisionLineEdit(3.937007874015748, DecimalConvention.POINT, 1)
    editor.show()
    editor.setFocus()
    editor.selectAll()
    QTest.keyClicks(editor, "3.9")
    assert editor.source_text() == "3.9"
    while editor.isUndoAvailable():
        editor.undo()
    assert editor.text() == "3.9"
    assert editor.source_text() == "3.937007874015748"
    editor.close()


@pytest.mark.parametrize("value", [-1, 9, True, 1.5])
def test_precision_rejects_invalid_project_counts(value: object) -> None:
    """Invalid decimal counts cannot reach project storage or numeric rendering.

    Args:
        value: Invalid negative, excessive, boolean or fractional precision.

    Returns:
        None; validate constructor rejection through the public immutable contract.
    """
    with pytest.raises(ValueError, match="integers"):
        DisplayPrecision(inputs=value)


@pytest.mark.parametrize("accept", [False, True])
def test_branded_reset_confirmation(window: LifftWindow, accept: bool) -> None:
    """Use processed assets and explicit consent in the actual row-removal modal.

    Args:
        window: Fixture-owned integrated assessment window.
        accept: Whether the user clicks Remove rows instead of default Cancel.

    Returns:
        None; assert the modal returns exactly the chosen consent value.
    """
    from ergotools.application.settings import Language

    def choose() -> None:
        """Inspect the owned modal and click its requested response.

        Args:
            None.

        Returns:
            None; assertions propagate through the Qt test exception handler.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, QMessageBox)
        assert dialog.defaultButton() is dialog.button(QMessageBox.Cancel)
        assert not dialog.button(QMessageBox.Yes).icon().isNull()
        assert not dialog.button(QMessageBox.Cancel).icon().isNull()
        assert dialog.button(QMessageBox.Yes).text() == "Eliminar filas"
        dialog.button(QMessageBox.Yes if accept else QMessageBox.Cancel).click()

    QTimer.singleShot(0, choose)
    assert window.confirm_task_reset(Language.SPANISH) is accept

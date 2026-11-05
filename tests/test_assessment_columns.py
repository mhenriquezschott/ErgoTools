"""Optional columns preserve data, calculation and personal preference scope."""

import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QCoreApplication, QEvent
from PyQt5.QtWidgets import QApplication, QDialog

from ergotools.application.assessment_columns import (
    AssessmentColumns,
    assessment_column_keys,
    optional_assessment_columns,
)
from ergotools.application.settings import UserSettings
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.settings_store import (
    JsonSettingsStore,
    SettingsFormatError,
)
from ergotools.presentation.desktop.assessment_column_settings import (
    AssessmentColumnSettings,
)
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.preferences_dialog import PreferencesDialog
from tests.test_saved_tool_data import window as window

# Keep native sample controls alive until their owned deferred deletion completes.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_required_inputs_cannot_be_hidden(kind: AssessmentKind) -> None:
    """Preferences permit only optional descriptive/index/calculated columns.

    Args:
        kind: Every supported tool schema.

    Returns:
        None; invalid or duplicated optional fields fail before any UI change.
    """
    optional = optional_assessment_columns(kind)
    assert AssessmentColumns(kind, optional).hidden == optional
    for key in set(assessment_column_keys(kind)) - set(optional):
        with pytest.raises(ValueError):
            AssessmentColumns(kind, (key,))
    with pytest.raises(ValueError):
        AssessmentColumns(kind, ("task_name", "task_name"))


@pytest.mark.parametrize("language", list(Language))
def test_preview_reuses_real_grid_and_keeps_all_task_and_result_values(
    language: Language,
) -> None:
    """Live previews hide optional columns without manufacturing another row renderer.

    Args:
        language: English/Spanish controls and tool captions.

    Returns:
        None; hidden values, required controls and exact source/results survive replay.
    """
    view = AssessmentColumnSettings(
        (), language, MeasurementSystem.METRIC, DecimalConvention.POINT
    )
    try:
        view.resize(1000, 550)
        view.show()
        for index, kind in enumerate(AssessmentKind):
            view.tools.setCurrentIndex(index)
            grid = view._grids[kind]
            source, results = grid.source, grid.result_rows
            _APP.processEvents()
            for key in optional_assessment_columns(kind):
                view.checks[key].setChecked(False)
            _APP.processEvents()
            for column, key in enumerate(assessment_column_keys(kind)):
                assert grid.headers[column].isHidden() is (
                    key in optional_assessment_columns(kind)
                )
                if key not in optional_assessment_columns(kind):
                    assert (
                        view.checks[key].isChecked()
                        and not view.checks[key].isEnabled()
                    )
            assert grid.source is source and grid.result_rows == results
            grid.load_source(source, results)
            assert grid.task_names[0].isHidden()
            view.all_button.click()
            assert not view._grids[kind].task_names[0].isHidden()
            assert grid.source is source and grid.result_rows == results
            view.checks["damage"].setChecked(False)
            view.familiar_button.click()
            assert not view.checks["damage"].isChecked()
            assert not view.checks["task_name"].isChecked()
            view.all_button.click()
    finally:
        view.close()
        view.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_version_eight_defaults_and_current_strict_roundtrip(
    tmp_path: Path,
) -> None:
    """Previous personal preferences load unchanged and only explicit Save upgrades.

    Args:
        tmp_path: Private personal settings directory.

    Returns:
        None; visibility rejects required inputs and never writes a project.
    """
    path = tmp_path / "settings.json"
    store = JsonSettingsStore(path)
    store.save(UserSettings())
    payload = json.loads(path.read_text())
    payload["version"] = 8
    payload.pop("assessment_columns")
    payload.pop("highs_single_tool", None)
    path.write_text(json.dumps(payload))
    before = path.read_bytes()
    loaded = store.load()
    assert loaded.assessment_columns == () and path.read_bytes() == before
    profile = AssessmentColumns(AssessmentKind.LIFFT, ("task_name", "moment", "damage"))
    store.save(replace(loaded, assessment_columns=(profile,)))
    assert store.load().assessment_columns == (profile,)
    payload = json.loads(path.read_text())
    assert payload["version"] == 11
    payload["assessment_columns"][0]["hidden"] = ["load"]
    path.write_text(json.dumps(payload))
    with pytest.raises(SettingsFormatError):
        store.load()


def test_real_settings_apply_changes_only_visibility_and_cancel_keeps_it(
    window: LifftWindow,
) -> None:
    """A personal-only column Apply preserves unfinished task text and project history.

    Args:
        window: Private integrated worker/project fixture.

    Returns:
        None; existing source identities/results and durable project bytes remain exact.
    """
    workspace = window.presenter.workspace
    source, revision = workspace.active.state, workspace.editing.history.revision
    path = Path(workspace.location)
    before = path.read_bytes()
    field = window.task_panel.inputs[0][0]
    field.setText("unfinished")
    field.textEdited.emit(field.text())

    def apply_columns(dialog: PreferencesDialog) -> int:
        """Edit the real personal page without resolving its host's pending source.

        Args:
            dialog: Production preferences modal.

        Returns:
            Accepted result after choosing optional column visibility.
        """
        dialog.column_settings.familiar_button.click()
        dialog.accept()
        return QDialog.Accepted

    with patch.object(PreferencesDialog, "exec", apply_columns):
        window._assessment_menu.preferences.trigger()
    assert field.text() == "unfinished"
    assert workspace.active.state is source
    assert workspace.editing.history.revision == revision
    assert path.read_bytes() == before
    assert window.task_panel.task_grid.task_names[0].isHidden()
    assert window._settings_store.load().assessment_columns[0].hidden == ("task_name",)

    accepted = window._settings_store.load()

    def cancel_columns(dialog: PreferencesDialog) -> int:
        """Discard a visible draft preset without publishing it.

        Args:
            dialog: Actual owned personal Settings.

        Returns:
            Rejected result; stored preferences and pending project text stay exact.
        """
        dialog.column_settings.all_button.click()
        dialog.reject()
        return QDialog.Rejected

    with patch.object(PreferencesDialog, "exec", cancel_columns):
        window._assessment_menu.preferences.trigger()
    assert window._settings_store.load() == accepted
    assert field.text() == "unfinished" and workspace.active.state is source

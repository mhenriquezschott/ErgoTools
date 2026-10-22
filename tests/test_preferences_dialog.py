"""Native Settings acceptance/cancellation and independent source/preferences state.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.bootstrap import create_window
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.settings_store import JsonSettingsStore
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.preferences_dialog import PreferencesDialog
from tests.test_saved_tool_data import window as window


@pytest.mark.parametrize("index", [0, 1, 2])
def test_preferences_cancel_invalid_apply_source_and_restart(
    window: LifftWindow, index: int
) -> None:
    """Cancel/invalid Apply preserve state; accepted preferences retain source units.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        index: Zero-based selected input/row/case index used by the parametrized
            regression.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(index)
    workspace = window.presenter.workspace
    active = workspace.active
    before = active.state
    panel = window.task_panel if index == 0 else window.secondary_panel()
    field = panel.inputs[0][2 if index == 0 else -1]
    field.setText("bad")
    field.textEdited.emit("bad")
    store = window._settings_store
    settings = store.load()

    def cancel() -> None:
        """Select Metric in the actual preferences modal and click Cancel.

        Select Metric in the actual preferences modal and click Cancel without changing
        source or settings.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, PreferencesDialog)
        dialog.units.setCurrentIndex(
            list(MeasurementSystem).index(MeasurementSystem.METRIC)
        )
        dialog.cancel_button.click()

    QTimer.singleShot(0, cancel)
    window._assessment_menu.preferences.trigger()
    assert active.state is before and field.text() == "bad" and panel.pending
    assert store.load() == settings

    def apply() -> None:
        """Apply Metric and Spanish in the real modal.

        Select Metric and Spanish in the actual preferences modal and click Apply once.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, PreferencesDialog)
        dialog.units.setCurrentIndex(
            list(MeasurementSystem).index(MeasurementSystem.METRIC)
        )
        dialog.language.setCurrentIndex(list(Language).index(Language.SPANISH))
        dialog.apply_button.click()

    QTimer.singleShot(0, apply)
    window._assessment_menu.preferences.trigger()
    assert active.state is before and field.text() == "bad" and store.load() == settings
    field.setText("350")
    field.textEdited.emit("350")
    with patch.object(
        JsonSettingsStore, "save", side_effect=OSError("injected settings failure")
    ):
        QTimer.singleShot(0, apply)
        window._assessment_menu.preferences.trigger()
    assert window.language is Language.ENGLISH and store.load() == settings
    assert active.state.tasks[0].repetitions == 350
    # Rebind after accepted input even when saving preferences fails.
    panel = window.task_panel if index == 0 else window.secondary_panel()
    assert not panel.pending
    QTimer.singleShot(0, apply)
    window._assessment_menu.preferences.trigger()
    assert "Métrico" in window.main_navigation.unit_label.text()
    changed = active.state
    assert (
        window.language is Language.SPANISH
        and window.presenter.system is MeasurementSystem.METRIC
    )
    assert changed.tasks[0].repetitions == 350
    if index != 1:
        assert changed.system is before.system
    assert store.load().recent_documents == settings.recent_documents
    assert (
        store.load().language is Language.SPANISH
        and store.load().default_units is MeasurementSystem.METRIC
    )
    # A fresh window reloads saved policy without requiring any open project.
    fresh = create_window(Path(store._path), original_navigation=True)
    assert (
        fresh.language is Language.SPANISH
        and fresh.presenter.system is MeasurementSystem.METRIC
    )
    fresh.presenter.workspace.close(choice=CloseChoice.DISCARD)
    fresh.close()

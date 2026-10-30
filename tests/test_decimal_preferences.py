"""Persist decimal input policy without reinterpreting existing assessment values.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from ergotools.application.settings import Language, UserSettings
from ergotools.bootstrap import create_window
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.infrastructure.settings_store import (
    JsonSettingsStore,
    SettingsFormatError,
)
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.preferences_dialog import PreferencesDialog
from tests.test_saved_tool_data import window as window


@pytest.mark.parametrize("index", [0, 1, 2])
def test_decimal_apply_cancel_failure_and_restart(
    window: LifftWindow, index: int
) -> None:
    """Old-mark input is validated before Apply; saved comma survives restart.

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
    panel = window.task_panel if index == 0 else window.secondary_panel()
    field = panel.inputs[0][0 if index == 0 else 1]
    before = active.state
    settings = window._settings_store.load()

    def choose(cancel: bool = False) -> None:
        """Change the actual decimal preference to comma.

        Change the actual decimal preference to comma and use explicit Cancel/Apply
        intent.

        Args:
            cancel: True clicks Cancel; False accepts the proposed preference/selection
                change.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, PreferencesDialog)
        dialog.decimal.setCurrentIndex(1)
        (dialog.cancel_button if cancel else dialog.apply_button).click()

    field.setText("bad")
    field.textEdited.emit("bad")
    QTimer.singleShot(0, lambda: choose(True))
    window._assessment_menu.preferences.trigger()
    assert field.text() == "bad" and active.state is before
    QTimer.singleShot(0, choose)
    window._assessment_menu.preferences.trigger()
    assert window._settings_store.load() == settings
    assert window.presenter.convention is DecimalConvention.POINT
    # Use the currently active point convention before applying comma.
    field.setText("12.5" if index != 1 else "6.5")
    field.textEdited.emit(field.text())
    with patch.object(JsonSettingsStore, "save", side_effect=OSError("save failed")):
        QTimer.singleShot(0, choose)
        window._assessment_menu.preferences.trigger()
    assert window.presenter.convention is DecimalConvention.POINT
    assert window._settings_store.load() == settings
    accepted = active.state
    QTimer.singleShot(0, choose)
    window._assessment_menu.preferences.trigger()
    assert active.state is accepted
    assert window.presenter.convention is DecimalConvention.COMMA
    panel = window.task_panel if index == 0 else window.secondary_panel()
    field = panel.inputs[0][0 if index == 0 else 1]
    assert field.text() == "6" if index == 1 else "," in field.text()
    saved = window._settings_store.load()
    assert saved.decimal_convention is DecimalConvention.COMMA
    assert (
        saved.language is settings.language
        and saved.default_units is settings.default_units
    )
    assert saved.recent_documents == settings.recent_documents
    restored = create_window(window._settings_store._path, original_navigation=True)
    try:
        assert restored.presenter.convention is DecimalConvention.COMMA
        assert restored.decimal.currentIndex() == 1
        assert restored._settings_store.load() == saved
    finally:
        restored.close()
    # New convention accepts decimal comma and rejects point, without guessing.
    field.setText("13,5" if index != 1 else "7,5")
    field.textEdited.emit(field.text())
    assert panel.commit_inputs()


def test_version_one_is_read_without_write_and_upgrades_explicitly(
    tmp_path: Path,
) -> None:
    """Existing preferences retain units/language/history and default to point.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "settings.json"
    old = dict(
        format="ergotools.user-settings",
        version=1,
        language="es",
        default_units="imperial",
        recent_documents=["old"],
    )
    path.write_text(json.dumps(old))
    original = path.read_bytes()
    store = JsonSettingsStore(path)
    saved = store.load()
    assert saved.language is Language.SPANISH
    assert saved.decimal_convention is DecimalConvention.POINT
    assert path.read_bytes() == original
    store.save(saved.remember("new"))
    assert json.loads(path.read_text())["version"] == 7
    assert store.load().recent_documents == ("new", "old")
    payload = json.loads(path.read_text())
    payload["decimal_convention"] = "auto"
    path.write_text(json.dumps(payload))
    with pytest.raises(SettingsFormatError):
        store.load()
    with pytest.raises(ValueError):
        UserSettings(decimal_convention=",")

"""Personal result animations, legacy preferences and main/modal composition.

Use private settings/projects and real Qt controls; no operational preferences change.
Disabling display animation must never alter calculated targets or source history.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QAbstractAnimation
from PyQt5.QtWidgets import QApplication, QDialog, QGroupBox, QVBoxLayout, QWidget

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import UserSettings
from ergotools.bootstrap import create_window, load_icons
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.settings_store import (
    JsonSettingsStore,
    SettingsFormatError,
)
from ergotools.presentation.desktop.job_management_dialog import JobManagementDialog
from ergotools.presentation.desktop.preferences_dialog import PreferencesDialog
from ergotools.presentation.desktop.result_animation_preferences import (
    apply_result_animations,
)
from ergotools.presentation.desktop.result_scales import DamageScale, RiskGauge
from tests.test_unified_project_save import editing_workspace

# Keep one QApplication alive throughout widget ownership and signal tests.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize(
    "gauge,damage", [(True, True), (True, False), (False, True), (False, False)]
)
def test_personal_flags_roundtrip_and_settle_independently(
    tmp_path: Path, gauge: bool, damage: bool
) -> None:
    """Animation choices roundtrip independently and settle without changing targets.

    Args:
        tmp_path: Disposable personal-settings directory.
        gauge: Desired risk-display animation choice.
        damage: Desired damage-bar animation choice.

    Returns:
        None; unchanged targets do not restart animations after applying preferences.
    """
    store = JsonSettingsStore(tmp_path / "settings.json")
    settings = UserSettings(
        animated_risk_gauge=gauge, animated_cumulative_damage=damage
    )
    store.save(settings)
    assert store.load() == settings
    root = QWidget()
    layout = QVBoxLayout(root)
    risk, bar = RiskGauge(), DamageScale()
    layout.addWidget(risk)
    layout.addWidget(bar)
    risk.set_probability(70)
    bar.set_value(1.5, "#FF0000")
    apply_result_animations(root, gauge, damage)
    for widget, enabled, target in ((risk, gauge, 70), (bar, damage, 1.5)):
        assert widget.target_value == target
        if not enabled:
            assert widget.display_value == target
            assert widget.animation.state() == QAbstractAnimation.Stopped
        widget.set_value(target + 0.1, "#FFFF00")
        if not enabled:
            assert widget.display_value == widget.target_value
        else:
            assert widget.animation.state() == QAbstractAnimation.Running
    root.close()


def test_version_six_defaults_and_strict_new_boolean_validation(tmp_path: Path) -> None:
    """Existing personal files load unchanged and malformed flags cannot overwrite them.

    Args:
        tmp_path: Disposable settings directory.

    Returns:
        None; no project format or database is involved.
    """
    path = tmp_path / "settings.json"
    store = JsonSettingsStore(path)
    store.save(
        UserSettings(animated_risk_gauge=False, animated_cumulative_damage=False)
    )
    payload = json.loads(path.read_text())
    payload["version"] = 6
    payload.pop("animated_risk_gauge")
    payload.pop("animated_cumulative_damage")
    path.write_text(json.dumps(payload))
    previous = path.read_bytes()
    loaded = store.load()
    assert loaded.animated_risk_gauge and loaded.animated_cumulative_damage
    assert path.read_bytes() == previous
    store.save(loaded)
    payload = json.loads(path.read_text())
    for key in ("animated_risk_gauge", "animated_cumulative_damage"):
        for invalid in (0, "true", None):
            broken = {**payload, key: invalid}
            path.write_text(json.dumps(broken))
            with pytest.raises(SettingsFormatError):
                store.load()
            with pytest.raises(SettingsFormatError):
                store.save(UserSettings())
            assert json.loads(path.read_text()) == broken


@pytest.mark.parametrize("language", list(Language))
def test_preferences_group_and_main_job_composition(
    tmp_path: Path, language: Language
) -> None:
    """One group exposes all animations; main and newly opened Jobs use saved choices.

    Args:
        tmp_path: Disposable native project and preference files.
        language: English/Spanish settings wording.

    Returns:
        None; opening preferences/Jobs creates no data or history action.
    """
    preferences = PreferencesDialog(
        language,
        MeasurementSystem.METRIC,
        load_icons(),
        parent=None,
        animated_focus=False,
        animated_risk_gauge=False,
        animated_cumulative_damage=False,
    )
    assert isinstance(preferences.animated_focus.parentWidget(), QGroupBox)
    assert (
        preferences.animated_focus.parentWidget()
        is preferences.animated_gauge.parentWidget()
    )
    assert (
        preferences.animated_focus.parentWidget()
        is preferences.animated_damage.parentWidget()
    )
    preferences.close()
    workspace = editing_workspace(tmp_path)
    location = workspace.location
    workspace.close(choice=CloseChoice.DISCARD)
    store = JsonSettingsStore(tmp_path / "main-settings.json")
    store.save(
        UserSettings(
            language=language,
            animated_risk_gauge=False,
            animated_cumulative_damage=False,
        )
    )
    host = create_window(
        tmp_path / "main-settings.json",
        original_controls=True,
        original_navigation=True,
    )
    host.open_project_location(location)
    assert not host.results_sidebar.risk_gauge.animation_enabled
    assert not host.results_sidebar.damage_progress.animation_enabled
    viewed: list[bool] = []

    def inspect(dialog: JobManagementDialog) -> int:
        """Inspect composed Job scales before modal work begins.

        Args:
            dialog: Real main-owned Job editor constructed by its normal launcher.

        Returns:
            Rejected modal result without any Job edit or project mutation.
        """
        assert not dialog.result_panel.risk_gauge.animation_enabled
        assert not dialog.result_panel.damage_progress.animation_enabled
        viewed.append(True)
        return QDialog.Rejected

    with patch.object(JobManagementDialog, "exec", inspect):
        host.open_job_management()
    assert viewed == [True]
    host.presenter.workspace.close(choice=CloseChoice.DISCARD)
    host.close()

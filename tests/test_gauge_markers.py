"""Gauge marker contracts, persistence and actual main-window preference actions.

Test layer. Use synthetic/disposable settings and the established temporary desktop
fixture. Verify exact category boundaries, independent visibility, old preference
compatibility, cancellation/failure ownership and unchanged scientific/animation state.
Native captures separately establish label/layout fit; these tests do not certify it.
"""

import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QPoint, QRect
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import QApplication, QDialog, QInputDialog, QMenu

from ergotools.application.gauge_preferences import GaugeMarkerSettings
from ergotools.application.settings import Language, UserSettings
from ergotools.infrastructure.settings_store import (
    JsonSettingsStore,
    SettingsFormatError,
)
from ergotools.presentation.desktop.gauge_markers import marker_values
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.preferences_dialog import PreferencesDialog
from ergotools.presentation.desktop.result_scales import RiskGauge
from tests.test_saved_tool_data import window as window

# Actual existing probability category boundaries; 37.5 must not snap to regular ticks.
BOUNDARIES = (0.0, 25.0, 37.5, 50.0, 100.0)
# Retain one Qt application while temporary widgets and menus are alive.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize(
    "values",
    [
        (1, True, 5),
        (True, 0, 5),
        (True, True, True),
        (True, True, 0),
        (True, True, 101),
        (True, True, 2.5),
    ],
)
def test_invalid_marker_preferences(values: tuple[object, ...]) -> None:
    """Reject ambiguous booleans and unbounded/noninteger drawing intervals.

    Args:
        values: Invalid visibility flags or percentage-point interval.

    Returns:
        None; malformed preferences cannot reach rendering or persistence.
    """
    with pytest.raises(ValueError, match="gauge marker"):
        GaugeMarkerSettings(*values)


def test_regular_ticks_preserve_exact_category_limits_and_independent_labels() -> None:
    """A ten-point grid retains off-grid limits exactly once, including both endpoints.

    Args:
        None.

    Returns:
        None; interval changes cannot round or omit a category limit.
    """
    settings = GaugeMarkerSettings(interval=10)
    ticks = marker_values(settings, BOUNDARIES)
    assert tuple(value for value, major in ticks if major) == BOUNDARIES
    assert tuple(value for value, major in ticks if not major) == (
        10,
        20,
        30,
        40,
        60,
        70,
        80,
        90,
    )
    assert len(ticks) == len({value for value, _major in ticks})
    assert (100.0, True) in marker_values(replace(settings, interval=3), BOUNDARIES)
    assert not marker_values(replace(settings, show_ticks=False), BOUNDARIES)
    assert marker_values(replace(settings, show_labels=False), BOUNDARIES) == ticks


@pytest.mark.parametrize("version", [1, 2, 3, 4])
def test_old_settings_default_markers_without_losing_saved_preferences(
    tmp_path: Path, version: int
) -> None:
    """Load each accepted older personal format and upgrade only on explicit save.

    Args:
        tmp_path: Disposable per-user settings directory.
        version: Existing supported settings version before gauge options.

    Returns:
        None; load preserves old bytes and preferences, then v7 roundtrips options.
    """
    path = tmp_path / "settings.json"
    store = JsonSettingsStore(path)
    store.save(UserSettings(language=Language.SPANISH).remember("test-location"))
    data = json.loads(path.read_text())
    data["version"] = version
    del data["gauge_markers"]
    for minimum, name in (
        (7, "animated_risk_gauge"),
        (7, "animated_cumulative_damage"),
        (6, "undo_limit"),
        (4, "assessment_contexts"),
        (3, "animated_body_region_focus"),
        (2, "decimal_convention"),
    ):
        if version < minimum:
            del data[name]
    path.write_text(json.dumps(data))
    before = path.read_bytes()
    settings = store.load()
    assert path.read_bytes() == before
    assert settings.gauge_markers == GaugeMarkerSettings()
    assert settings.language is Language.SPANISH
    assert settings.recent_documents == ("test-location",)
    changed = replace(settings, gauge_markers=GaugeMarkerSettings(False, True, 10))
    store.save(changed)
    assert store.load() == changed
    assert json.loads(path.read_text())["version"] == 7


@pytest.mark.parametrize(
    "markers",
    [
        None,
        {},
        {"show_ticks": True},
        {"show_ticks": True, "show_labels": True, "interval": 0},
        {"show_ticks": True, "show_labels": True, "interval": 5, "extra": 1},
    ],
)
def test_malformed_marker_settings_are_preserved_and_rejected(
    tmp_path: Path, markers: object
) -> None:
    """Refuse broken marker objects instead of overwriting personal settings.

    Args:
        tmp_path: Disposable preference file directory.
        markers: Invalid nested marker payload in current personal preferences.

    Returns:
        None; both load and save fail while exact malformed bytes remain.
    """
    path = tmp_path / "settings.json"
    store = JsonSettingsStore(path)
    store.save(UserSettings())
    data = json.loads(path.read_text())
    data["gauge_markers"] = markers
    path.write_text(json.dumps(data))
    before = path.read_bytes()
    with pytest.raises(SettingsFormatError):
        store.load()
    with pytest.raises(SettingsFormatError):
        store.save(UserSettings())
    assert path.read_bytes() == before


@pytest.mark.parametrize("language", list(Language))
def test_right_click_and_settings_share_saved_options_without_source_edits(
    window: LifftWindow, language: Language
) -> None:
    """Use real menu actions and Settings Apply/Cancel on an owned desktop gauge.

    Args:
        window: Integrated fixture with a disposable classified project/settings store.
        language: English/Spanish menu and Settings controls.

    Returns:
        None; options roundtrip without changing source identity, state or gauge motion.
    """
    window.language = language
    window.refresh()
    gauge = window.results_sidebar.risk_gauge
    store = window._settings_store
    active = window.presenter.workspace.active
    before = active.state
    gauge.set_value(70.0, "#FF3B30")
    gauge.animation.setCurrentTime(200)
    animation_time = gauge.animation.currentTime()
    value = gauge.display_value
    menu = gauge.marker_menu()
    intervals = next(action.menu() for action in menu.actions() if action.menu())
    next(a for a in intervals.actions() if a.objectName() == "interval_10").trigger()
    assert store.load().gauge_markers.interval == 10
    assert gauge.marker_settings == store.load().gauge_markers
    assert gauge.target_value == 70 and gauge.display_value == value
    assert gauge.animation.currentTime() == animation_time
    assert active.state is before
    menu.deleteLater()
    saved = store.load()

    def cancel(dialog: PreferencesDialog) -> int:
        """Change draft controls and cancel the actual preferences form.

        Args:
            dialog: Owned modal settings form; changes remain tentative.

        Returns:
            Rejected disposition, leaving saved/rendered preferences intact.
        """
        assert dialog.gauge_interval.value() == 10
        dialog.gauge_interval.setValue(20)
        dialog.gauge_ticks.setChecked(False)
        return QDialog.Rejected

    with patch.object(PreferencesDialog, "exec", cancel):
        window.open_preferences()
    assert store.load() == saved and gauge.marker_settings == saved.gauge_markers

    def apply(dialog: PreferencesDialog) -> int:
        """Accept the hidden-markers option through normal Settings Apply.

        Args:
            dialog: Owned preferences form initialized from right-click changes.

        Returns:
            Accepted disposition; the host retains its existing input-resolution policy.
        """
        dialog.gauge_ticks.setChecked(False)
        dialog.gauge_labels.setChecked(False)
        dialog.gauge_interval.setValue(5)
        return QDialog.Accepted

    with patch.object(PreferencesDialog, "exec", apply):
        window.open_preferences()
    assert gauge.marker_settings == GaugeMarkerSettings(False, False, 5)
    assert store.load().gauge_markers == gauge.marker_settings
    assert active.state is before
    with (
        patch.object(JsonSettingsStore, "save", side_effect=OSError("injected")),
        pytest.raises(OSError),
    ):
        window.change_gauge_markers(GaugeMarkerSettings())
    assert gauge.marker_settings == GaugeMarkerSettings(False, False, 5)
    assert store.load().gauge_markers == gauge.marker_settings


def test_local_controls_custom_cancel_and_context_menu_lifetime() -> None:
    """A standalone gauge can preview options without a store or hidden side effects.

    Args:
        None.

    Returns:
        None; presets/visibility/custom input work locally and cancelled menus are safe.
    """
    gauge = RiskGauge()
    menu = gauge.marker_menu()
    next(a for a in menu.actions() if a.objectName() == "show_ticks").trigger()
    next(a for a in menu.actions() if a.objectName() == "show_labels").trigger()
    assert gauge.marker_settings == GaugeMarkerSettings(False, False, 10)

    def accept_interval(dialog: QInputDialog) -> int:
        """Choose a custom interval through its real owned integer input.

        Args:
            dialog: Transient input initialized with the current marker spacing.

        Returns:
            Accepted result after selecting fifteen percentage points.
        """
        assert dialog.intMinimum() == 1 and dialog.intMaximum() == 100
        dialog.setIntValue(15)
        return QDialog.Accepted

    with patch.object(QInputDialog, "exec", return_value=QDialog.Rejected):
        gauge._custom_marker_interval()
    assert gauge.marker_settings.interval == 10
    with patch.object(QInputDialog, "exec", accept_interval):
        gauge._custom_marker_interval()
    assert gauge.marker_settings.interval == 15
    gauge.contextMenuEvent(None)
    with patch.object(QMenu, "exec", return_value=None) as execute:
        gauge.contextMenuEvent(
            QContextMenuEvent(QContextMenuEvent.Mouse, QPoint(10, 10))
        )
    execute.assert_called_once()
    menu.deleteLater()
    gauge.close()
    gauge.deleteLater()


@pytest.mark.parametrize("language", list(Language))
def test_annotations_leave_original_arc_interior_value_and_animation_unchanged(
    language: Language,
) -> None:
    """Render all visibility combinations and compare the original interior pixels.

    Args:
        language: English point or Spanish comma in the off-grid boundary label.

    Returns:
        None; visible annotations change outer pixels only, never the needle/value
        interior or original fixed size. This is not a substitute for native visual QA.
    """
    gauge = RiskGauge(GaugeMarkerSettings(False, False))
    gauge.setStyleSheet("background: white;")
    gauge.resize(190, 167)
    gauge.marker_language = language
    gauge.set_value(70.0, "#FF3B30")
    gauge.animation.setCurrentTime(750)
    original = gauge.grab().toImage()
    interior = QRect(40, 45, 110, 60)
    for settings in (
        GaugeMarkerSettings(),
        GaugeMarkerSettings(False, True),
        GaugeMarkerSettings(True, False, 10),
    ):
        gauge.set_marker_settings(settings)
        rendered = gauge.grab().toImage()
        assert rendered != original
        assert rendered.copy(interior) == original.copy(interior)
        assert gauge.target_value == 70 and gauge.display_value == 70
        assert gauge.height() == 167
    with pytest.raises(ValueError, match="gauge marker"):
        replace(UserSettings(), gauge_markers=None)
    gauge.close()
    gauge.deleteLater()

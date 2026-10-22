"""Section navigation, shared gauge persistence and application-wide dialog theming.

Test layer. Use owned Qt widgets and disposable native projects/settings. Verify
that page switches preserve drafts, the production PLOT opener shares preferences,
failures retain previous appearances, and owned forms/prompts use the shared theme
without deleting specific styles. System choosers keep platform defaults. Native
screenshots separately establish fit.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QInputDialog,
    QMessageBox,
)

from ergotools.application.gauge_preferences import GaugeMarkerSettings
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.settings_store import JsonSettingsStore
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.plot_window import PlotWindow
from ergotools.presentation.desktop.preferences_dialog import PreferencesDialog
from ergotools.presentation.desktop.result_scales import RiskGauge
from ergotools.presentation.desktop.theme.dialogs import (
    APPLICATION_DIALOG_STYLE,
    DIALOG_STYLE,
    apply_dialog_theme,
    install_dialog_theme,
)
from tests.test_saved_tool_data import window as window

# Retain a QApplication while independent family probes/widgets are alive.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("project_open", [True, False])
def test_settings_pages_retain_all_drafts_and_footer_actions(
    window: LifftWindow,
    language: Language,
    project_open: bool,
) -> None:
    """Switch every real tree leaf without applying or discarding hidden-page drafts.

    Args:
        window: Fixture-owned main desktop supplying packaged icons and Qt lifetime.
        language: English/Spanish section labels.
        project_open: Enable or disable project/task pages without hiding their context.

    Returns:
        None; the dialog remains compact, all draft controls persist and Cancel writes
        nothing to personal settings or the current assessment.
    """
    source = window.presenter.workspace.active.state
    saved = window._settings_store.load()
    dialog = PreferencesDialog(
        language,
        MeasurementSystem.METRIC,
        window.icons,
        parent=window,
        project_open=project_open,
        task_count=100 if project_open else None,
        tool_name="LiFFT",
    )
    try:
        dialog.show()
        _APP.processEvents()
        assert dialog.pages.count() == 5
        dialog.gauge_interval.setValue(10)
        dialog.decimal_fields["probability"].setValue(3)
        for item in dialog.section_items.values():
            dialog.sections.setCurrentItem(item)
            _APP.processEvents()
            assert dialog.pages.currentIndex() == item.data(0, Qt.ItemDataRole.UserRole)
            assert dialog.apply_button.isVisible() and dialog.cancel_button.isVisible()
            assert dialog.rect().contains(dialog.apply_button.geometry())
        assert dialog.gauge_interval.value() == 10
        assert dialog.decimal_fields["probability"].value() == 3
        assert dialog.decimal_fields["inputs"].isEnabled() is project_open
        dialog._select_section(None, None)
        dialog.reject()
        assert window._settings_store.load() == saved
        assert window.presenter.workspace.active.state is source
    finally:
        dialog.close()
        dialog.deleteLater()


@pytest.mark.parametrize("language", list(Language))
def test_production_plot_opener_synchronizes_every_gauge_and_main_on_close(
    window: LifftWindow,
    language: Language,
) -> None:
    """Exercise production composition, not a separately configured PLOT test control.

    Args:
        window: Integrated fixture with borrowed repository and personal store.
        language: UI language for every compact gauge menu and input prompt.

    Returns:
        None; PLOT/main use one rendering class and retain the same saved options.
        Native project snapshot bytes are unchanged by every preference action.
    """
    window.language = language
    window.change_gauge_markers(GaugeMarkerSettings(interval=10))
    before = Path(window.presenter.workspace.location).read_bytes()
    active = window.presenter.workspace.active.state
    visited = []

    def inspect(dialog: PlotWindow) -> int:
        """Trigger a comparison gauge menu and verify shared application preferences.

        Args:
            dialog: Production PLOT modal built by the main opener with injected ports.

        Returns:
            Rejected modal result after explicit preference changes and failure probes.
        """
        gauges = (
            dialog.outcome.gauge,
            dialog.outcome.individual_gauge,
            dialog.outcome.job_gauge,
        )
        assert all(isinstance(gauge, RiskGauge) for gauge in gauges)
        assert all(gauge.marker_settings.interval == 10 for gauge in gauges)
        assert all(gauge.marker_language is language for gauge in gauges)
        menu = gauges[1].marker_menu()
        next(
            action for action in menu.actions() if action.objectName() == "show_labels"
        ).trigger()
        expected = GaugeMarkerSettings(True, False, 10)
        assert all(gauge.marker_settings == expected for gauge in gauges)
        assert window._settings_store.load().gauge_markers == expected
        with (
            patch.object(JsonSettingsStore, "save", side_effect=OSError("injected")),
            patch.object(QMessageBox, "critical") as error,
        ):
            dialog.change_gauge_markers(GaugeMarkerSettings())
        error.assert_called_once()
        assert all(gauge.marker_settings == expected for gauge in gauges)
        visited.append(True)
        menu.deleteLater()
        return QDialog.Rejected

    with patch.object(PlotWindow, "exec", inspect):
        window.open_plot()
    assert visited == [True]
    assert window.results_sidebar.risk_gauge.marker_settings == GaugeMarkerSettings(
        True, False, 10
    )
    assert window.presenter.workspace.active.state is active
    assert Path(window.presenter.workspace.location).read_bytes() == before


@pytest.mark.parametrize(
    "dialog_type",
    [QDialog, QInputDialog, QMessageBox],
)
def test_owned_dialog_families_accept_shared_theme_and_preserve_local_styles(
    dialog_type: type[QDialog],
) -> None:
    """Owned forms/prompts share an idempotent theme beyond main-window children.

    Args:
        dialog_type: Qt family for app-owned forms, prompts or confirmations.

    Returns:
        None; installation is idempotent, styling survives later local changes, and
        existing specific selectors retain their local Qt priority.
    """
    install_dialog_theme(_APP)
    install_dialog_theme(_APP)
    assert not _APP.testAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs)
    assert _APP.styleSheet().count(APPLICATION_DIALOG_STYLE) == 1
    dialog = dialog_type()
    try:
        specific = "QLabel#specific { color: #087E91; }"
        dialog.setStyleSheet(specific)
        dialog.ensurePolished()
        apply_dialog_theme(dialog)
        assert dialog.styleSheet() == DIALOG_STYLE + specific
        apply_dialog_theme(dialog)
        assert dialog.styleSheet() == DIALOG_STYLE + specific
        changed = "QLabel#specific { color: #0B326C; }"
        dialog.setStyleSheet(changed)
        apply_dialog_theme(dialog)
        assert dialog.styleSheet() == DIALOG_STYLE + changed
    finally:
        dialog.close()
        dialog.deleteLater()


def test_system_choosers_are_not_forced_to_use_the_app_dialog_theme() -> None:
    """Retain platform defaults without opening a real system file/color/font chooser.

    Args:
        None.

    Returns:
        None; the shared policy excludes system chooser subclasses and never sets
        DontUseNativeDialog. Actual native UI remains an owner verification step.
    """
    install_dialog_theme(_APP)
    assert not _APP.testAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs)
    assert "QFileDialog" not in APPLICATION_DIALOG_STYLE
    assert "QColorDialog" not in APPLICATION_DIALOG_STYLE
    assert "QFontDialog" not in APPLICATION_DIALOG_STYLE
    assert ".QDialog" in APPLICATION_DIALOG_STYLE


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("enabled", [True, False])
def test_unchecked_task_count_indicator_has_visible_outline(
    window: LifftWindow, language: Language, enabled: bool
) -> None:
    """The actual unchecked checkbox paints a visible outline in both languages.

    Args:
        window: Existing integrated parent supplying inherited production styles.
        language: English/Spanish dialog labels.
        enabled: Normal or disabled assessment controls; both need a visible box.

    Returns:
        None; indicator pixels are inspected without asserting stylesheet text or
        an exact platform checkmark bitmap.
    """
    from PyQt5.QtTest import QTest
    from PyQt5.QtWidgets import QStyle, QStyleOptionButton

    dialog = PreferencesDialog(
        language,
        MeasurementSystem.METRIC,
        window.icons,
        parent=window,
        task_count=15 if enabled else None,
        tool_name="LiFFT",
        project_open=True,
        assessment_context="W01 — Ana Ruiz",
    )
    try:
        dialog.show()
        dialog.sections.setCurrentItem(dialog.section_items["assessment"])
        QTest.qWait(30)
        box = dialog.reset_tasks
        assert not box.isChecked() and box.isEnabled() is enabled
        option = QStyleOptionButton()
        box.initStyleOption(option)
        rectangle = box.style().subElementRect(QStyle.SE_CheckBoxIndicator, option, box)
        picture = box.grab().toImage()
        pixels = [
            picture.pixelColor(x, y)
            for x in range(rectangle.left(), rectangle.right() + 1)
            for y in range(rectangle.top(), rectangle.bottom() + 1)
        ]
        assert (
            sum(
                765 - color.red() - color.green() - color.blue() > 50
                for color in pixels
            )
            >= 12
        )
    finally:
        dialog.reject()
        dialog.deleteLater()

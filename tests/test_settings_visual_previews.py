"""Real movie/shared-scale Settings previews with isolated draft and timer ownership."""

from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QAbstractAnimation
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget

from ergotools.application.gauge_preferences import GaugeMarkerSettings
from ergotools.bootstrap import load_icons
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.resources import read_asset
from ergotools.presentation.desktop.preferences_dialog import PreferencesDialog
from ergotools.presentation.desktop.settings_previews import DiagnosticReportInfo

# A retained application owns native preview/movie objects throughout these tests.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("language", list(Language))
def test_preview_drafts_and_movie_never_apply_or_keep_running_hidden(
    language: Language,
) -> None:
    """Exercise marker switches, actual GIF decoding and independent animations.

    Args:
        language: Both supported UI languages.

    Returns:
        None; ordinary draft values stay unchanged during playback and cancel closes it.
    """
    parent = QWidget()
    view = PreferencesDialog(
        language,
        MeasurementSystem.METRIC,
        load_icons(),
        parent=parent,
        avatar_preview=read_asset("images/avatar_focus_preview.gif"),
    )
    view.show()
    initial = view._ordinary_values()
    view.decimal_fields["damage"].setValue(6)
    assert view.decimal_examples["damage"].text() == "0.012346"
    view.decimal.setCurrentIndex(1)
    assert view.decimal_examples["damage"].text() == "0,012346"
    view.decimal_fields["damage"].setValue(4)
    view.decimal.setCurrentIndex(0)
    preview = view.animation_previews
    assert preview.movie.isValid() and preview.movie.frameCount() > 20
    view.sections.setCurrentItem(view.section_items["gauges"])
    view.gauge_ticks.setChecked(False)
    view.gauge_labels.setChecked(False)
    view.gauge_interval.setValue(20)
    assert view.gauge_preview.gauge.marker_settings == GaugeMarkerSettings(
        False, False, 20
    )
    assert preview.gauge.marker_settings == GaugeMarkerSettings(False, False, 20)
    view.gauge_preview.slider.setValue(77)
    assert view.gauge_preview.gauge.target_value == 77
    view.sections.setCurrentItem(view.section_items["animations"])
    QTest.qWait(50)
    assert preview.timer.isActive()
    preview.advance()
    assert preview.gauge.animation.state() == QAbstractAnimation.State.Running
    view.animated_gauge.setChecked(False)
    view.animated_damage.setChecked(False)
    view.animated_focus.setChecked(False)
    preview.advance()
    assert preview.gauge.display_value == preview.gauge.target_value
    assert preview.damage.display_value == preview.damage.target_value
    assert preview.movie.currentFrameNumber() == 0
    assert preview.gauge.animation.state() == QAbstractAnimation.State.Stopped
    view.animated_focus.setChecked(True)
    view.animated_gauge.setChecked(True)
    view.animated_damage.setChecked(True)
    assert not view.gauge_ticks.isChecked()
    view.gauge_ticks.setChecked(True)
    view.gauge_labels.setChecked(True)
    view.gauge_interval.setValue(10)
    assert view._ordinary_values() == initial
    view.sections.setCurrentItem(view.section_items["general"])
    assert not preview.timer.isActive()
    assert preview.gauge.animation.state() == QAbstractAnimation.State.Stopped
    view.reject()
    assert not preview.timer.isActive()
    view.deleteLater()
    parent.close()


def test_report_location_uses_independent_os_browser_and_copy(tmp_path: Path) -> None:
    """Report controls expose the exact current file without loading its contents.

    Args:
        tmp_path: Disposable report path, including spaces.

    Returns:
        None; only the parent folder is handed to the OS, with no application ownership.
    """
    path = tmp_path / "report folder" / "trial.jsonl"
    view = DiagnosticReportInfo(str(path), Language.ENGLISH)
    buttons = {b.text(): b for b in view.findChildren(QPushButton)}
    buttons["Copy report path"].click()
    assert QApplication.clipboard().text() == str(path)
    with patch(
        "ergotools.presentation.desktop.settings_previews.QDesktopServices.openUrl",
        return_value=True,
    ) as browser:
        buttons["Open report folder"].click()
    assert browser.call_args.args[0].toLocalFile() == str(path.parent)
    assert not path.exists()
    view.close()

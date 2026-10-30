"""Saved-only location browsing, exact historical identity and copy-target UI tests."""

from dataclasses import replace

from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from ergotools.application.assessment_navigation import context_values
from ergotools.application.settings import Language
from ergotools.bootstrap import load_icons
from ergotools.presentation.desktop.assessment_location_browser import (
    AssessmentLocation,
    AssessmentLocationBrowser,
)
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_assessment_navigation import add_night_context
from tests.test_main_navigation import window as window

# Own one application for standalone widget tests as well as the integrated fixture.
_APP = QApplication.instance() or QApplication([])


def test_current_tool_saved_only_navigation_and_disabled_browser(
    window: LifftWindow,
) -> None:
    """Only saved sources for the selected worker/tool appear; toggle changes no data.

    Args:
        window: Integrated project with workplace LiFFT sources and no DUET source.

    Returns:
        None; Night opens exactly, missing tools disable browsing, drafts survive.
    """
    add_night_context(window)
    window.refresh_navigation()
    nav = window.main_navigation
    browser = nav.location_browser
    combo = browser.combos[0]
    assert combo.count() == 2  # Placeholder plus the sole plant owning saved sources.
    assert combo.itemText(1) == "P"
    assert browser.headings[0].text() == "Plant (1)"
    browser.combos[-1].setCurrentIndex(2)
    assert window.assessment_navigation.view.workplace.shift_id == "Night"
    document = window.presenter.workspace.active.document
    nav.context_disclosure.setChecked(True)
    QTest.qWait(230)
    nav.context_disclosure.click()
    QTest.qWait(230)
    assert not nav.context_frame.isVisible()
    assert window.presenter.workspace.active.document == document
    nav.context_disclosure.click()
    assert window.presenter.workspace.active.document == document
    window.assessment_tabs.setCurrentIndex(1)
    assert not browser.has_assessments
    assert all(not combo.isEnabled() for combo in browser.combos)
    assert browser.add_button.isEnabled()
    assert all(c.count() == 1 for c in browser.combos)
    assert "DUET" in browser.summary.text()
    window.assessment_tabs.setCurrentIndex(0)
    assert browser.has_assessments
    assert window.presenter.workspace.active.document == document


def test_duplicate_paths_keep_exact_historical_identity_and_missing_results() -> None:
    """Historical assessments sharing a complete path remain independently selectable.

    Args:
        None.

    Returns:
        None; cascades emit exact source IDs; missing outputs never become zero risk.
    """
    from tests.test_history_persistence import STATION

    location = STATION.at_shift("Day")
    rows = (
        AssessmentLocation("old", 1, location, "Historical 2020-2021", None),
        AssessmentLocation("current", 2, location, "J01 · Packing", 55.1),
        AssessmentLocation("other", 3, replace(location, plant_name="South"), "", 30),
    )
    widget = AssessmentLocationBrowser(load_icons())
    seen: list[str] = []
    widget.selected.connect(seen.append)
    try:
        for language in Language:
            widget.update_rows(rows, "current", language, "LiFFT")
            assert not seen
            assert (
                tuple(c.currentData() for c in widget.combos[:4])
                == context_values(location)[:4]
            )
            assert widget.job_combo.currentData() == "current"
            assert "55.1%" in widget.combos[3].currentText()
            assert "%" not in widget.combos[-1].itemText(1)
            assert widget.headings[4].text().endswith("(1)")
            assert widget.combos[-1].itemData(1, Qt.ItemDataRole.BackgroundRole) is None
            assert (
                widget.combos[3].itemData(1, Qt.ItemDataRole.BackgroundRole) is not None
            )
        widget.job_combo.setCurrentIndex(widget.job_combo.findData("old"))
        assert seen == ["old"]
        widget.combos[0].setCurrentIndex(widget.combos[0].findData("South"))
        assert seen[-1] == "other"
        widget.combos[0].setCurrentIndex(0)
        assert seen[-1] == "other"  # Placeholders do not navigate.
        assert widget.combos[0].currentData() == location.plant_name
        assert widget.job_combo.currentData() == "current"
    finally:
        widget.close()
        widget.deleteLater()


def test_rejected_pending_input_restores_browser_path(window: LifftWindow) -> None:
    """An unfinished invalid field cannot leave the browser at an unopened assessment.

    Args:
        window: Disposable integrated project with a second saved LiFFT location.

    Returns:
        None; source identity, pending text and all five accepted choices remain intact.
    """
    add_night_context(window)
    window.refresh_navigation()
    nav = window.main_navigation
    document = window.presenter.workspace.active.document
    before = tuple(c.currentData() for c in nav.location_browser.combos)
    field = window.task_panel.inputs[0][0]
    field.setText("bad")
    field.textEdited.emit("bad")
    nav.location_browser.combos[-1].setCurrentIndex(2)
    assert window.presenter.workspace.active.document == document
    assert tuple(c.currentData() for c in nav.location_browser.combos) == before
    assert field.text() == "bad"


def test_heading_counts_entries_and_station_results_follow_shift() -> None:
    """Counts belong to headings; selecting a shift updates its station's exact result.

    Args:
        None.

    Returns:
        None; raw location identities stay undecorated and mixed risks are not averaged.
    """
    from tests.test_history_persistence import STATION

    place = STATION.at_shift("Day")
    rows = (
        AssessmentLocation("day", 1, place, "", 13.2),
        AssessmentLocation("night", 2, replace(place, shift_id="Night"), "", 60.0),
        AssessmentLocation("second", 3, replace(place, station_id="ST02"), "", None),
    )
    widget = AssessmentLocationBrowser(load_icons())
    try:
        widget.update_rows(rows, "day", Language.ENGLISH, "LiFFT")
        assert [h.text() for h in widget.headings] == [
            "Plant (1)",
            "Section (1)",
            "Line (1)",
            "Station (2)",
            "Shift (2)",
        ]
        assert widget.combos[2].currentText() == place.line_name
        assert widget.combos[3].currentText() == f"{place.station_id} · 13.2%"
        widget.update_rows(rows, "night", Language.ENGLISH, "LiFFT")
        assert widget.combos[3].currentText() == f"{place.station_id} · 60.0%"
        assert widget.combos[4].currentText() == "Night"
        caption, risk = widget._station_caption(place.station_id, rows[:2], None)
        assert "13.2" in caption and "60.0" in caption and risk is None
    finally:
        widget.close()
        widget.deleteLater()


def test_job_information_is_separate_from_shift_and_selects_exact_saved_owner() -> None:
    """Single Jobs are read-only information; ambiguous owners get their own selector.

    Args:
        None.

    Returns:
        None; Shift stays literal and Job selection opens the exact saved source.
    """
    from tests.test_history_persistence import STATION

    first = AssessmentLocation(
        "packing", 1, STATION.at_shift("Day"), "", 20, ("J01", "Packing")
    )
    second = AssessmentLocation(
        "loading", 2, first.workplace, "Historical", 50, ("J02", "Loading")
    )
    widget = AssessmentLocationBrowser(load_icons())
    seen: list[str] = []
    widget.selected.connect(seen.append)
    try:
        widget.update_rows(
            (first,),
            first.document_id,
            Language.ENGLISH,
            "LiFFT",
            standalone_open=False,
        )
        assert widget.job_stack.currentIndex() == 0
        assert widget.job_value.text() == "J01 · Packing"
        widget.update_rows(
            (first, second),
            second.document_id,
            Language.ENGLISH,
            "LiFFT",
            standalone_open=False,
        )
        assert widget.job_stack.currentIndex() == 1
        assert widget.combos[4].currentText() == "Day"
        assert widget.combos[4].count() == 2
        assert widget.job_combo.currentData() == "loading"
        assert not seen
        widget.job_combo.setCurrentIndex(widget.job_combo.findData("packing"))
        assert seen == ["packing"]
    finally:
        widget.close()
        widget.deleteLater()

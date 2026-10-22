"""Original main panels: result coherence, animation lifecycle and layout limits.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QAbstractAnimation
from PyQt5.QtWidgets import QApplication

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.bootstrap import create_window
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.result_scales import DamageScale, RiskGauge

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.fixture
def window(tmp_path: Path) -> Iterator[LifftWindow]:
    """Own a complete synthetic assessment in the real three-panel main preview.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Yields:
        Live synthetic integrated window; fixture cleanup closes the window and releases
        its temporary project after the test.
    """
    view = create_window(tmp_path / "settings.json", original_navigation=True)
    view.presenter.workspace.create(
        str(tmp_path / "panels.ergprj"),
        ProjectMetadata("p", "Panels", MeasurementSystem.IMPERIAL),
        "lifft",
        LifftDraft(
            MeasurementSystem.IMPERIAL,
            (
                LifftTask("a", 12, 20, 100),
                LifftTask("b", 24, 10, 50),
            ),
        ),
    )
    view.refresh()
    view.show()
    _APP.processEvents()
    yield view
    view.presenter.workspace.close(choice=CloseChoice.DISCARD)
    view.close()
    _APP.processEvents()


def test_calculation_cards_metrics_and_pending_edit_clear(window: LifftWindow) -> None:
    """Cards match grid outputs, then clear immediately when inputs change.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    panel = window.task_panel
    sidebar = window.results_sidebar
    panel.calculate_button.click()
    result = window.presenter.evaluator.current(window.presenter.workspace.active)
    assert sidebar.damage_value_label.text() == f"{result.summary.total_damage:.4f}"
    assert sidebar.risk_gauge.target_value == result.summary.probability * 100
    assert sidebar.assessment_status_label.text() == "Ready"
    assert {k: v.text() for k, v in sidebar.metric_labels.items()} == {
        "tasks": "2",
        "repetitions": "150",
        "average_load": "15.0",
        "max_moment": "20.0",
    }
    sidebar.risk_gauge.animation.setCurrentTime(300)
    before = sidebar.risk_gauge.animation.currentTime()
    window.show_result()
    assert sidebar.risk_gauge.animation.currentTime() == before
    cell = panel.inputs[0][1]
    cell.setText("invalid")
    cell.textEdited.emit("invalid")
    assert sidebar.damage_value_label.text() == "—"
    assert not sidebar.risk_gauge.has_value
    assert sidebar.risk_gauge.animation.state() == QAbstractAnimation.State.Stopped
    assert sidebar.metric_labels["max_moment"].text() == "-"
    assert sidebar.assessment_status_label.text() == "Incomplete"


def test_partial_and_clear_cannot_leave_complete_status(window: LifftWindow) -> None:
    """Moment-only output is incomplete; clearing removes old risk.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    cell = window.task_panel.inputs[1][2]
    cell.clear()
    cell.textEdited.emit("")
    window.task_panel.calculate_button.click()
    sidebar = window.results_sidebar
    assert sidebar.assessment_status_label.text() == "Incomplete"
    assert (
        sidebar.assessment_status_detail.text()
        == "Results include completed rows only."
    )
    assert sidebar.risk_gauge.has_value
    with patch.object(LifftWindow, "confirm_clear_assessment", return_value=True):
        window.task_panel.clear_button.click()
    assert not sidebar.risk_gauge.has_value
    assert sidebar.damage_value_label.text() == "—"
    assert sidebar.metric_labels["tasks"].text() == "0"


def test_empty_clears_and_metric_calculation_populates_result_cards(
    tmp_path: Path,
) -> None:
    """Absent outputs clear cards; valid metric calculations populate them.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    view = create_window(tmp_path / "settings.json", original_navigation=True)
    assert view.results_sidebar.risk_severity_label.text() == "● Not available"
    view.presenter.workspace.create(
        str(tmp_path / "metric.ergprj"),
        ProjectMetadata("m", "Metric", MeasurementSystem.METRIC),
        "lifft",
        LifftDraft(MeasurementSystem.METRIC, (LifftTask("a", 10, 20, 30),)),
    )
    view.refresh()
    view.run(view.calculate)
    assert view.results_sidebar.risk_gauge.has_value
    assert (
        view.results_sidebar.assessment_status_detail.text()
        == "Assessment data is available."
    )
    assert view.results_sidebar.damage_value_label.text() != "—"
    view.presenter.workspace.close(choice=CloseChoice.DISCARD)
    view.close()


def test_panel_localization_assets_and_native_width_bounds(window: LifftWindow) -> None:
    """Original side regions remain within the main window at the target size.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    window.language = Language.SPANISH
    window.translate()
    window.refresh()
    _APP.processEvents()
    body = window.body_panel
    sidebar = window.results_sidebar
    assert all(
        not button.isEnabled() and not button.icon().isNull()
        for button in body.view_buttons
    )
    assert [button.text() for button in body.view_buttons] == [
        "Girar",
        "Ampliar",
        "Restablecer vista",
    ]
    assert sidebar.individual_risk_title.text() == "LiFFT individual"
    assert sidebar.damage_progress.toolTip().startswith("Escala de daño")
    assert 240 <= body.width() <= 285 and 230 <= sidebar.width() <= 260
    assert body.viewport.height() >= 315
    for widget in (
        body,
        sidebar,
        window.task_panel,
        window.main_navigation.context_frame,
    ):
        position = widget.mapTo(window, widget.rect().bottomRight())
        assert position.x() < window.width() and position.y() < window.height()
    assert not body.grab().isNull() and not sidebar.grab().isNull()


def test_scale_clamping_color_change_and_clear() -> None:
    """Same-value color changes repaint without restarting; clear stops animation.

    Args:
        None.

    Returns:
        None.
    """
    gauge = RiskGauge()
    scale = DamageScale()
    for widget, value, expected in ((gauge, 200, 100), (scale, 3, 2)):
        widget.set_value(value, "#19B83F")
        widget.animation.setCurrentTime(200)
        before = widget.animation.currentTime()
        widget.set_value(value, "#FF3B30")
        assert widget.animation.currentTime() == before
        assert widget.target_value == expected and widget.fill_color.name() == "#ff3b30"
        with pytest.raises(ValueError):
            widget.set_value(float("nan"), "#19B83F")
        with pytest.raises(ValueError):
            widget.set_value(1, "not-a-color")
        widget.show()
        _APP.processEvents()
        assert not widget.grab().isNull()
        widget.clear()
        assert widget.display_value == 0 and not widget.has_value
        assert widget.animation.state() == QAbstractAnimation.State.Stopped
        widget.close()

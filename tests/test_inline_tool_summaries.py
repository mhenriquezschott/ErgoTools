"""Populated inline totals retain reference styling across projection and Save.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import pytest
from PyQt5.QtCore import QPoint
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_saved_tool_data import window as window


@pytest.mark.parametrize("index", [0, 1, 2])
@pytest.mark.parametrize("units", list(MeasurementSystem))
@pytest.mark.parametrize("language", list(Language))
def test_inline_totals_survive_save_projection_and_pending_input(
    window: LifftWindow,
    index: int,
    units: MeasurementSystem,
    language: Language,
) -> None:
    """All populated tools show summaries, without relabeling source moments.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        index: Zero-based selected input/row/case index used by the parametrized
            regression.
        units: Explicit source/display system used to verify preserved numeric meaning.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(index)
    window.language = language
    window.translate()
    panel = window.task_panel if index == 0 else window.secondary_panel()
    workspace = window.presenter.workspace
    source = workspace.active.state
    window.units.setCurrentIndex(list(MeasurementSystem).index(units))
    window.run(window.calculate)
    result = window.current_result_snapshot()
    assert result is not None
    summary = panel.summary
    assert summary.total_value.isVisible() and summary.probability_value.isVisible()
    assert float(summary.total_value.text()) == pytest.approx(
        result.damage, abs=0.00005
    )
    assert "font-size: 15px" in summary.total_value.styleSheet()
    assert "background: transparent" not in summary.total_value.styleSheet()
    for width, height in ((1550, 1015), (1800, 1200)):
        window.resize(width, height)
        QApplication.processEvents()
        QTest.qWait(30)
        damage = panel.outputs[0][1 if index in (0, 2) else 0]
        assert (
            abs(
                summary.total_value.mapTo(panel, QPoint()).x()
                - damage.mapTo(panel, QPoint()).x()
            )
            <= 1
        )
        assert summary.total_value.width() == damage.width()
        for title, value in summary.rows:
            assert panel.rect().contains(title.geometry())
            assert panel.rect().contains(value.geometry())
    if index in (0, 2):
        assert "ft.lb" in panel.headers[3 if index == 0 else 4].text()
    if index in (0, 2):
        header = panel.headers[1 if index == 0 else 2].text()
        assert f"({'in' if units is MeasurementSystem.IMPERIAL else 'cm'})" in header
    assert workspace.active.state == source
    fresh_style = summary.total_value.styleSheet()
    fresh_total_text = summary.total_value.text()
    window.save_project()
    document = workspace.active.document.document_id
    location = workspace.location
    workspace.close(choice=CloseChoice.DISCARD)
    workspace.switch(location, document)
    window.refresh()
    assert summary.total_value.styleSheet() == fresh_style
    assert summary.total_value.text() == fresh_total_text
    assert float(summary.total_value.text()) == pytest.approx(
        result.damage, abs=0.00005
    )
    assert workspace.historical_result().damage == result.damage
    assert "background: transparent" not in summary.total_value.styleSheet()
    field = panel.inputs[0][2 if index == 0 else -1]
    field.setText("invalid")
    field.textEdited.emit("invalid")
    assert summary.total_value.text() == "0.0"
    assert summary.probability_value.text() == "0.0"
    assert "background: transparent" in summary.total_value.styleSheet()
    assert workspace.active.state == source


@pytest.mark.parametrize(
    "color,foreground", [("#ff2e00", "#FFFFFF"), ("#f2ff00", "#10212B")]
)
def test_reference_summary_contrast(color: str, foreground: str) -> None:
    """The original luminance threshold keeps values readable on risk colors.

    Args:
        color: Expected source palette color or test image fill color; not recomputed
            from screenshots.
        foreground: Expected reference text contrast color for the tested damage
            background.

    Returns:
        None.
    """
    from ergotools.presentation.desktop.tool_result_summary import ToolResultSummary

    summary = ToolResultSummary()
    summary.show_values("1.0", "80.0", color)
    assert f"color: {foreground}" in summary.total_value.styleSheet()
    summary.show_values("0.0", "0.0", None)
    assert "background: transparent" in summary.total_value.styleSheet()

"""PLOT Apply/Clear, original demographics, unit fidelity and composed disclosure.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest
from PyQt5.QtWidgets import QApplication

from ergotools.application.settings import Language
from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.plot_filters import (
    PlotDemographics,
    PlotFilterSelection,
    PlotRiskView,
    paired_range,
)
from ergotools.domain.plot_scope import PlotScope
from ergotools.domain.worker_details import WorkerDetails
from ergotools.infrastructure.plant_image_import import import_plant_image
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.plot_filters_panel import PlotFiltersPanel
from ergotools.presentation.desktop.plot_map_panel import PlotMapPanel
from ergotools.presentation.desktop.plot_window import PlotWindow
from tests.test_plant_layout_persistence import create_project, image_file
from tests.test_saved_tool_data import window as window

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


def test_reference_demographic_predicates_and_invalid_bounds() -> None:
    """Paired/year predicates retain missing and disabled behavior.

    Args:
        None.

    Returns:
        None.
    """
    details = WorkerDetails(
        birth_date="2000-12-31", sex="Female", height_cm=170, weight_kg=70
    )
    filters = PlotDemographics(True, "Female", (26, 26), (70, 70), (170, 170))
    assert filters.matches(details, current_year=2026)
    assert not filters.matches(None, current_year=2026)
    assert not filters.matches(WorkerDetails(sex="Male"), current_year=2026)
    assert PlotDemographics().matches(None, current_year=2026)
    assert PlotDemographics(True).matches(None, current_year=2026)
    assert paired_range(None, 100) is None and paired_range(100, 1) is None
    assert paired_range(0, 0) == (0, 0)
    for value in (True, -1, float("nan"), "wrong"):
        with pytest.raises(ValueError):
            paired_range(value, 100)
    for bounds in ((100, 1), (None, 100), [1, 2], (1,), (1, 2, 3)):
        with pytest.raises(ValueError):
            PlotDemographics(age=bounds)
    with pytest.raises(ValueError):
        PlotDemographics(enabled=1)
    with pytest.raises(ValueError):
        PlotDemographics(sex="Both")
    with pytest.raises(ValueError):
        filters.matches(details, current_year=True)
    with pytest.raises(ValueError):
        PlotFilterSelection("P")


@pytest.mark.parametrize("language", [Language.ENGLISH, Language.SPANISH])
def test_apply_clear_filter_results_and_failure_retention(
    tmp_path: Path, language: Language
) -> None:
    """Actual Apply evaluates predicates; edits/Clear do not replace applied results.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    with create_project(tmp_path / "project.ergprj", 8) as project:
        hierarchy = project.load_hierarchy()
        map_panel = PlotMapPanel(
            hierarchy,
            project,
            project,
            lambda filename: import_plant_image(Path(filename)),
            load_icons(),
        )
        results = []
        workers = (
            WorkerDetails(
                birth_date="2000-12-31", sex="Female", height_cm=170, weight_kg=70
            ),
            WorkerDetails(
                birth_date="1990-01-01", sex="Male", height_cm=180, weight_kg=80
            ),
            None,
        )

        def apply(selection: PlotFilterSelection) -> bool:
            """Record membership from the supplied predicates.

            Evaluate the exact supplied demographic predicates against synthetic worker
            details and record the accepted membership.

            Args:
                selection: Immutable exact PLOT scope/tool/risk/demographic intent
                    supplied to the test publication callback.

            Returns:
                True after recording the applied selection and its matching result
                projection.
            """
            results.append(
                tuple(
                    i
                    for i, details in enumerate(workers)
                    if selection.demographics.matches(details, current_year=2026)
                )
            )
            return True

        filters = PlotFiltersPanel(
            hierarchy, map_panel, load_icons(), apply, language=language
        )
        map_panel.show_error = Mock()
        filters.apply_button.click()
        assert filters.applied is None and not results
        assert filters.workplace.set_scope(PlotScope((("P",),)))
        with pytest.raises(ValueError):
            filters.select_risk("job")
        filters.demographics.setChecked(True)
        assert filters.height() == 229 and filters.risk_group.height() == 96
        filters.sex.setCurrentIndex(filters.sex.findData("Female"))
        filters.ranges["age"][0].setValue(26)
        filters.ranges["age"][1].setValue(26)
        filters.ranges["weight"][0].setValue(70)
        filters.ranges["weight"][1].setValue(70)
        filters.apply_button.click()
        applied = filters.applied
        assert results == [(0,)] and applied.demographics.sex == "Female"
        filters.tools.buttons[AssessmentKind.DUET].click()
        filters.risk_buttons[PlotRiskView.COMPARISON].click()
        assert (
            filters.applied is applied
            and filters.selection().tool is AssessmentKind.DUET
        )
        filters.apply_selection = Mock(return_value=False)
        filters.apply_button.click()
        assert filters.applied is applied and results == [(0,)]
        filters.apply_selection = Mock(side_effect=OSError("query failed"))
        filters.apply_button.click()
        assert filters.applied is applied and map_panel.show_error.called
        map_panel.choose_image = Mock(
            return_value=str(image_file(tmp_path / "map.png"))
        )
        map_panel.buttons["open"].click()
        map_panel.confirm_discard = Mock(return_value=False)
        filters.workplace.scope = PlotScope((("Empty",),))
        map_panel.scope = filters.workplace.scope
        filters.clear_button.click()
        assert (
            filters.tools.selected is AssessmentKind.DUET
            and filters.demographics.isChecked()
        )
        map_panel.confirm_discard.return_value = True
        filters.clear_button.click()
        assert (
            filters.tools.selected is AssessmentKind.LIFFT
            and filters.risk_view is PlotRiskView.INDIVIDUAL
        )
        assert not filters.demographics.isChecked() and filters.height() == 201
        assert all(
            field.value() == -1
            for fields in filters.ranges.values()
            for field in fields
        )
        assert filters.workplace.scope.shift == hierarchy.work.shifts[0]
        assert filters.applied is applied and results == [(0,)]
        filters.close()
        filters.deleteLater()
        map_panel.close()
        map_panel.deleteLater()


def test_units_preserve_exact_bounds_across_repeated_toggles(tmp_path: Path) -> None:
    """Decimal display and large projections retain canonical filters.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    with create_project(tmp_path / "project.ergprj", 8) as project:
        hierarchy = project.load_hierarchy()
        panel = PlotMapPanel(
            hierarchy,
            project,
            project,
            lambda filename: import_plant_image(Path(filename)),
            load_icons(),
        )
        filters = PlotFiltersPanel(
            hierarchy, panel, load_icons(), Mock(return_value=True)
        )
        assert filters.workplace.set_scope(PlotScope((("P",),)))
        filters.demographics.setChecked(True)
        filters.ranges["weight"][0].setValue(100)
        filters.ranges["weight"][1].setValue(1000)
        filters.ranges["height"][0].setValue(170.3)
        filters.ranges["height"][1].setValue(200.1)
        filters.apply_button.click()
        original = filters.applied
        for _ in range(3):
            filters.set_system(MeasurementSystem.IMPERIAL)
            assert filters.ranges["weight"][1].value() > 2000
            assert filters.range_titles["weight"].text().endswith("(lb)")
            assert filters.ranges["weight"][1].suffix() == ""
            assert filters.selection() == original and filters.applied is original
            filters.set_system(MeasurementSystem.METRIC)
            assert filters.selection() == original
        filters.set_system(MeasurementSystem.IMPERIAL)
        filters.ranges["weight"][0].setValue(220.4)
        assert filters.selection().demographics.weight_kg[0] == pytest.approx(
            220.4 * 0.45359237
        )
        filters.set_system(MeasurementSystem.IMPERIAL)
        with pytest.raises(ValueError):
            filters.set_system("imperial")
        filters.ranges["age"][0].setValue(30)
        assert filters.selection().demographics.age is None
        filters.ranges["age"][1].setValue(20)
        assert filters.selection().demographics.age is None
        filters.close()
        filters.deleteLater()
        panel.close()
        panel.deleteLater()


@pytest.mark.parametrize("tab", [0, 1, 2])
def test_filter_apply_preserves_pending_assessments(
    window: LifftWindow, tmp_path: Path, tab: int
) -> None:
    """Apply/Clear operate only PLOT inputs and preserve every assessment edit.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        tab: Zero-based integrated tool-tab position used by the actual Qt interaction.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(tab)
    task = window.task_panel if tab == 0 else window.secondary_panel()
    field = task.inputs[0][2 if tab == 0 else -1]
    field.setText("bad")
    field.textEdited.emit("bad")
    active = window.presenter.workspace.active
    state = active.state
    settings = window._settings_store.load()
    with create_project(tmp_path / "plot.ergprj", 8) as project:
        hierarchy = project.load_hierarchy()
        panel = PlotMapPanel(
            hierarchy,
            project,
            project,
            lambda filename: import_plant_image(Path(filename)),
            load_icons(),
        )
        callback = Mock(return_value=True)
        filters = PlotFiltersPanel(hierarchy, panel, load_icons(), callback)
        filters.clear_button.click()
        filters.apply_button.click()
        assert callback.call_count == 1 and field.text() == "bad" and task.pending
        assert window.presenter.workspace.active is active and active.state is state
        assert window._settings_store.load() == settings
        assert window.main_navigation.toolbar_actions["plot"].isEnabled()
        filters.close()
        filters.deleteLater()
        panel.close()
        panel.deleteLater()


@pytest.mark.parametrize(
    "convention", [DecimalConvention.POINT, DecimalConvention.COMMA]
)
def test_explicit_decimal_input_keeps_bounds(
    tmp_path: Path, convention: DecimalConvention
) -> None:
    """Native decimal settings are independent of UI language.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        convention: Explicit point/comma input policy independent of language and units.

    Returns:
        None.
    """
    with create_project(tmp_path / "project.ergprj", 8) as project:
        hierarchy = project.load_hierarchy()
        panel = PlotMapPanel(
            hierarchy,
            project,
            project,
            lambda filename: import_plant_image(Path(filename)),
            load_icons(),
        )
        filters = PlotFiltersPanel(
            hierarchy,
            panel,
            load_icons(),
            Mock(return_value=True),
            decimal_convention=convention,
        )
        assert filters.workplace.set_scope(PlotScope((("P",),)))
        field = filters.ranges["height"][0]
        field.setValue(170.3)
        assert "170" + convention.value + "3" in field.text()
        before = dict(filters._canonical_bounds)
        filters.set_decimal_convention(DecimalConvention.COMMA)
        filters.set_decimal_convention(DecimalConvention.POINT)
        assert filters._canonical_bounds == before
        with pytest.raises(ValueError):
            filters.set_decimal_convention("comma")
        filters.close()
        filters.deleteLater()
        panel.close()
        panel.deleteLater()


def test_apply_button_paints_reference_teal(tmp_path: Path) -> None:
    """The composed PLOT window paints Apply teal while Clear remains white.

    Args:
        tmp_path: Disposable native project and synthetic map directory.

    Returns:
        None; inspect actual pixels and close the borrowed-repository window.
    """
    with create_project(tmp_path / "styled.ergprj", 8) as project:
        window = PlotWindow(
            project,
            project,
            project,
            lambda name: import_plant_image(Path(name)),
            load_icons(),
            current_year=2026,
        )
        window.show()
        try:
            _APP.processEvents()
            apply_image = window.filters.apply_button.grab().toImage()
            clear_image = window.filters.clear_button.grab().toImage()
            assert (
                apply_image.pixelColor(8, apply_image.height() // 2).name() == "#087e91"
            )
            assert (
                clear_image.pixelColor(8, clear_image.height() // 2).name() == "#ffffff"
            )
        finally:
            window.close()

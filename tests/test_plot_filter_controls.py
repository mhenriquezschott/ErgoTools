"""Original workplace/tool controls: actual modal acceptance and map consistency.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from html import unescape
from pathlib import Path
from unittest.mock import Mock

import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QDialog, QHBoxLayout, QVBoxLayout

from ergotools.application.settings import Language
from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.plot_scope import PlotScope
from ergotools.domain.work_catalog import WorkCatalog
from ergotools.domain.work_hierarchy import WorkHierarchy
from ergotools.infrastructure.plant_image_import import import_plant_image
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.plot_filter_controls import (
    PlotToolControls,
    PlotWorkplaceControls,
)
from ergotools.presentation.desktop.plot_map_panel import PlotMapPanel
from ergotools.presentation.desktop.plot_workplace_dialog import PlotWorkplaceDialog
from tests.test_plant_layout_persistence import create_project, image_file
from tests.test_plot_layout import HIERARCHY_FULL
from tests.test_saved_tool_data import window as window

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("language", [Language.ENGLISH, Language.SPANISH])
def test_real_picker_accept_cancel_and_map_failure(language: Language) -> None:
    """Only accepted map intent updates the original summary.

    Args:
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    apply = Mock(return_value=True)
    controls = PlotWorkplaceControls(
        HIERARCHY_FULL, load_icons(), apply, language=language
    )
    assert controls.scope is None and apply.call_count == 0

    def choose() -> None:
        """Select two exact same-plant stations.

        Select two exact same-plant stations and the literal Todos shift in the actual
        scope picker, then accept.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, PlotWorkplaceDialog)
        dialog.items[("P", "S", "L", "1")].setCheckState(0, Qt.Checked)
        dialog.items[("P", "S", "L", "2")].setCheckState(0, Qt.Checked)
        dialog.shift_combo.setCurrentIndex(dialog.shift_combo.findData("Todos"))
        dialog.use_button.click()

    QTimer.singleShot(0, choose)
    controls.choose_button.click()
    scope = PlotScope((("P", "S", "L", "1"), ("P", "S", "L", "2")), "Todos")
    assert controls.scope == scope and apply.call_args.args == (scope,)
    assert controls.values["Plant"].value == "P"
    assert controls.values["Station"].value == (
        "2 seleccionados" if language is Language.SPANISH else "2 selected"
    )
    assert controls.values["Shift"].value == "Todos"
    assert "P \u203a S \u203a L \u203a 2" in controls.values["Station"].toolTip()
    assert controls.set_scope(scope) and apply.call_count == 1

    def cancel() -> None:
        """Check that the literal Todos shift survived.

        Check that the literal Todos shift survived and reject the actual scope picker
        without changing the map.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, PlotWorkplaceDialog)
        assert dialog.shift_combo.currentData() == "Todos"
        dialog.reject()

    QTimer.singleShot(0, cancel)
    controls.choose_button.click()
    assert controls.scope == scope and apply.call_count == 1
    apply.return_value = False
    assert not controls.set_scope(PlotScope((("Empty",),))) and controls.scope == scope
    assert controls.values["Plant"].value == "P"
    with pytest.raises(ValueError):
        controls.set_scope(PlotScope((("Missing",),)))
    controls.close()
    controls.deleteLater()


def test_empty_and_long_literal_summary_resize() -> None:
    """Long literal identities fit and remain accessible.

    Args:
        None.

    Returns:
        None.
    """
    empty = PlotWorkplaceControls(WorkHierarchy(WorkCatalog("p")), load_icons(), Mock())
    assert not empty.choose_button.isEnabled()
    empty.close()
    empty.deleteLater()
    literal = "<b>All & Plant</b> " + "Long name " * 30
    hierarchy = WorkHierarchy(WorkCatalog("p", shifts=("All",)), (literal,))
    controls = PlotWorkplaceControls(hierarchy, load_icons(), Mock(return_value=True))
    scope = PlotScope(((literal,),), "All")
    assert controls.set_scope(scope)
    controls.resize(1000, 88)
    controls.show()
    _APP.processEvents()
    value = controls.values["Plant"]
    assert value.value == literal and value.textFormat() == Qt.PlainText
    assert value.accessibleDescription() == literal and literal in unescape(
        value.toolTip()
    )
    assert len(value.text()) < len(literal)
    controls.resize(1600, 88)
    _APP.processEvents()
    assert value.fontMetrics().horizontalAdvance(value.text()) <= value.width()
    assert controls.values["Shift"].value == "All" and controls.scope.shift == "All"
    controls.close()
    controls.deleteLater()


@pytest.mark.parametrize("language", [Language.ENGLISH, Language.SPANISH])
def test_tool_exclusivity_and_single_typed_notification(language: Language) -> None:
    """Same-tool clicks do not repeat queries.

    Args:
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    callback = Mock()
    controls = PlotToolControls(load_icons(), callback, language=language)
    assert controls.selected is AssessmentKind.LIFFT and callback.call_count == 0
    controls.buttons[AssessmentKind.LIFFT].click()
    assert callback.call_count == 0
    for kind in (AssessmentKind.DUET, AssessmentKind.TST, AssessmentKind.LIFFT):
        controls.buttons[kind].click()
        assert controls.selected is kind and callback.call_args.args == (kind,)
        assert sum(button.isChecked() for button in controls.buttons.values()) == 1
        controls.buttons[kind].click()
    assert callback.call_count == 3
    with pytest.raises(ValueError):
        controls.select_tool("duet")
    assert controls.selected is AssessmentKind.LIFFT
    controls.close()
    controls.deleteLater()


@pytest.mark.parametrize("tab", [0, 1, 2])
def test_composed_filters_map_preview_and_pending_assessment(
    window: LifftWindow,
    tmp_path: Path,
    tab: int,
) -> None:
    """Composed controls preserve scope consent and independent tool intent.

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
    task_panel = window.task_panel if tab == 0 else window.secondary_panel()
    field = task_panel.inputs[0][2 if tab == 0 else -1]
    field.setText("bad")
    field.textEdited.emit("bad")
    active = window.presenter.workspace.active
    state = active.state
    settings = window._settings_store.load()
    with create_project(tmp_path / "plot.ergprj", 8) as project:
        hierarchy = project.load_hierarchy()
        host = QDialog(window)
        map_panel = PlotMapPanel(
            hierarchy,
            project,
            project,
            lambda filename: import_plant_image(Path(filename)),
            load_icons(),
            parent=host,
        )
        workplace = PlotWorkplaceControls(
            hierarchy, load_icons(), map_panel.set_scope, parent=host
        )
        selected = []
        tools = PlotToolControls(load_icons(), selected.append, parent=host)
        layout = QVBoxLayout(host)
        row = QHBoxLayout()
        row.addWidget(tools, 2)
        row.addWidget(workplace, 3)
        layout.addLayout(row)
        layout.addWidget(map_panel)
        assert workplace.set_scope(PlotScope((("P",),)))
        map_panel.choose_image = Mock(
            return_value=str(image_file(tmp_path / "map.png"))
        )
        map_panel.buttons["open"].click()
        preview = map_panel.pending_image
        map_panel.confirm_discard = Mock(return_value=False)
        assert not workplace.set_scope(PlotScope((("Empty",),)))
        assert workplace.scope == map_panel.scope == PlotScope((("P",),))
        tools.buttons[AssessmentKind.DUET].click()
        assert selected == [AssessmentKind.DUET] and map_panel.pending_image is preview
        assert field.text() == "bad" and task_panel.pending
        assert window.presenter.workspace.active is active and active.state is state
        assert window._settings_store.load() == settings
        assert window.main_navigation.toolbar_actions["plot"].isEnabled()
        host.close()
        host.deleteLater()

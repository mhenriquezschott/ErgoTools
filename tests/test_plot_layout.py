"""PLOT source-derived workplace selection and read-only image-space loading.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest
from PyQt5.QtCore import QRectF, Qt, QTimer
from PyQt5.QtGui import QColor, QImage
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QDialog

from ergotools.application.plot_layout import LoadedPlantLayout, load_plant_layout
from ergotools.application.settings import Language
from ergotools.bootstrap import load_icons
from ergotools.domain.plot_scope import PlotScope, hierarchy_paths
from ergotools.domain.work_catalog import StationKey
from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy
from ergotools.infrastructure.plot_layout_files import FilePlantLayouts
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.plot_layout_canvas import PlotLayoutCanvas
from ergotools.presentation.desktop.plot_workplace_dialog import PlotWorkplaceDialog
from tests.test_history_persistence import HIERARCHY
from tests.test_saved_tool_data import window as window

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])
# Expanded synthetic hierarchy with repeated branch labels and an empty plant for scope
# identity/fit tests.
HIERARCHY_FULL = replace(
    HIERARCHY,
    plants=("P", "Q", "Empty"),
    sections=(SectionKey("P", "S"), SectionKey("P", "T"), SectionKey("Q", "S")),
    lines=(LineKey("P", "S", "L"), LineKey("P", "T", "L"), LineKey("Q", "S", "L")),
    work=replace(
        HIERARCHY.work,
        stations=(
            StationKey("P", "S", "L", "1"),
            StationKey("P", "S", "L", "2"),
            StationKey("P", "T", "L", "1"),
            StationKey("Q", "S", "L", "1"),
        ),
        shifts=("All", "Day", "Todos"),
    ),
)


@pytest.mark.parametrize(
    "paths,shift",
    [
        ((), None),
        ((("P",), ("Q",)), None),
        ((("",),), None),
        ((("P", "S", "L", "1", "extra"),), None),
        (("P",), None),
        ((("P",),), " "),
    ],
)
def test_scope_rejects_invalid_identity_shapes(paths: object, shift: object) -> None:
    """Scope rejects ambiguous identity paths, multiple plants and blank shifts.

    Args:
        paths: Deliberately untyped/invalid PLOT hierarchy paths used to verify strict
            scope boundaries.
        shift: Deliberately untyped/invalid shift value used to verify strict scope
            identity.

    Returns:
        None.
    """
    with pytest.raises(ValueError):
        PlotScope(paths, shift)


def test_scope_normalizes_and_validates_before_any_image_io() -> None:
    """Parents cover descendants; unavailable records fail without accessing storage.

    Args:
        None.

    Returns:
        None.
    """
    scope = PlotScope((("P", "S", "L", "1"), ("P", "S"), ("P", "T"), ("P", "S")), "Day")
    assert scope.paths == (("P", "S"), ("P", "T")) and scope.plant == "P"
    scope.validate(HIERARCHY_FULL)
    assert ("Empty",) in hierarchy_paths(HIERARCHY_FULL)
    reader = Mock()
    for invalid in (PlotScope((("Missing",),)), PlotScope((("P",),), "Missing shift")):
        with pytest.raises(ValueError):
            load_plant_layout(HIERARCHY_FULL, invalid, reader)
    reader.read.assert_not_called()
    with pytest.raises(ValueError):
        LoadedPlantLayout(scope, b"")
    with pytest.raises(ValueError):
        LoadedPlantLayout(scope, "not bytes")
    with pytest.raises(ValueError):
        LoadedPlantLayout("not scope", None)


def test_original_picker_one_plant_prefix_rules_and_literal_shift_identity() -> None:
    """Checkbox ancestry, other-plant clearing and All shift text retain exact IDs.

    Args:
        None.

    Returns:
        None.
    """
    dialog = PlotWorkplaceDialog(
        HIERARCHY_FULL, load_icons(), initial=PlotScope((("P",),), "Day")
    )
    dialog.show()
    _APP.processEvents()
    assert dialog.use_button.isEnabled()
    assert len(dialog.items) == len(hierarchy_paths(HIERARCHY_FULL))
    assert dialog.items[("Empty",)].childCount() == 0
    dialog.items[("P", "S", "L", "1")].setCheckState(0, Qt.Checked)
    assert dialog.items[("P",)].checkState(0) == Qt.Unchecked
    dialog.items[("P", "S", "L", "2")].setCheckState(0, Qt.Checked)
    assert dialog._paths == (("P", "S", "L", "1"), ("P", "S", "L", "2"))
    dialog.items[("P", "S")].setCheckState(0, Qt.Checked)
    assert dialog._paths == (("P", "S"),)
    dialog.items[("Q", "S", "L", "1")].setCheckState(0, Qt.Checked)
    assert dialog._paths == (("Q", "S", "L", "1"),)
    dialog.shift_combo.setCurrentIndex(dialog.shift_combo.findData("All"))
    dialog.use_button.click()
    assert dialog.result() == QDialog.Accepted
    assert dialog.selection == PlotScope((("Q", "S", "L", "1"),), "All")
    dialog.deleteLater()


def test_empty_picker_and_spanish_literal_records() -> None:
    """Empty states stay disabled; language changes never reinterpret saved names.

    Args:
        None.

    Returns:
        None.
    """
    empty = PlotWorkplaceDialog(
        WorkHierarchy(replace(HIERARCHY.work, stations=(), shifts=())),
        load_icons(),
        language=Language.SPANISH,
    )
    empty.show()
    assert not empty.use_button.isEnabled()
    empty.accept_selection()
    assert empty.selection is None
    empty.reject()
    empty.deleteLater()
    spanish = PlotWorkplaceDialog(
        HIERARCHY_FULL, load_icons(), language=Language.SPANISH
    )
    spanish.show()
    spanish.tree.expandAll()
    spanish.toggle_check(spanish.items[("Empty",)], 0)
    assert spanish.tree.headerItem().text(0) == "Incluir"
    assert spanish.items[("Empty",)].text(1) == "Empty"
    assert "Empty" in spanish.path_label.text()
    assert (
        spanish.shift_combo.itemData(spanish.shift_combo.findData("Todos")) == "Todos"
    )
    spanish.use_button.click()
    assert spanish.selection == PlotScope((("Empty",),))
    spanish.deleteLater()


@pytest.mark.parametrize("encoding", ["PNG", "JPG"])
def test_read_only_image_loading_pixel_space_resize_missing_and_invalid(
    tmp_path: Path, encoding: str
) -> None:
    """Native image fitting keeps pixel coordinates and clears missing-plant images.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        encoding: Encoded image format selected for the synthetic import fixture.

    Returns:
        None.
    """
    path = tmp_path / f"layout.{encoding.lower()}"
    image = QImage(640, 360, QImage.Format_RGB32)
    image.fill(QColor("#087E91"))
    assert image.save(str(path), encoding)
    original = path.read_bytes()
    catalog = {"P": path}
    reader = FilePlantLayouts(catalog)
    catalog.clear()
    scope = PlotScope((("P",),))
    loaded = load_plant_layout(HIERARCHY_FULL, scope, reader)
    canvas = PlotLayoutCanvas()
    canvas.resize(970, 580)
    canvas.set_layout(loaded)
    canvas.show()
    QTest.qWait(20)
    assert canvas.loaded_layout == loaded
    assert canvas.sceneRect() == QRectF(0, 0, 640, 360)
    for width, height in ((900, 580), (1280, 800), (1600, 1000)):
        canvas.resize(width, height)
        QTest.qWait(20)
        bounds = canvas.mapFromScene(canvas.sceneRect()).boundingRect()
        assert canvas.viewport().rect().contains(bounds)
        assert canvas.transform().m11() == canvas.transform().m22()
        assert canvas.sceneRect() == QRectF(0, 0, 640, 360)
    with pytest.raises(ValueError, match="decoded"):
        canvas.set_layout(LoadedPlantLayout(PlotScope((("Q",),)), b"invalid image"))
    assert canvas.loaded_layout is loaded
    canvas.set_layout(load_plant_layout(HIERARCHY_FULL, PlotScope((("Q",),)), reader))
    assert not canvas.scene().items() and canvas.sceneRect().isEmpty()
    assert reader.read("Missing") is None
    missing_reader = FilePlantLayouts({"P": tmp_path / "missing.png"})
    assert missing_reader.read("P") is None
    with pytest.raises(IsADirectoryError):
        FilePlantLayouts({"P": tmp_path}).read("P")
    assert path.read_bytes() == original
    canvas.close()
    assert not canvas._fit_timer.isActive()
    canvas.deleteLater()


@pytest.mark.parametrize("index", [0, 1, 2])
def test_scope_then_layout_harness_preserves_pending_assessments(
    window: LifftWindow, tmp_path: Path, index: int
) -> None:
    """Targeted component integration loads a saved image without touching source/UI.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        index: Zero-based selected input/row/case index used by the parametrized
            regression.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(index)
    active = window.presenter.workspace.active
    state = active.state
    settings = window._settings_store.load()
    panel = window.task_panel if index == 0 else window.secondary_panel()
    field = panel.inputs[0][2 if index == 0 else -1]
    field.setText("bad")
    field.textEdited.emit("bad")
    path = tmp_path / "image.png"
    image = QImage(300, 200, QImage.Format_RGB32)
    image.fill(QColor("white"))
    assert image.save(str(path))
    picker = PlotWorkplaceDialog(HIERARCHY_FULL, load_icons(), parent=window)

    def choose() -> None:
        """Check the exact P/S scope and activate Use in the composed original picker.

        Args:
            None.

        Returns:
            None.
        """
        picker.items[("P", "S")].setCheckState(0, Qt.Checked)
        picker.use_button.click()

    QTimer.singleShot(0, choose)
    assert picker.exec_() == QDialog.Accepted
    loaded = load_plant_layout(
        HIERARCHY_FULL, picker.selection, FilePlantLayouts({"P": path})
    )
    canvas = PlotLayoutCanvas()
    canvas.set_layout(loaded)
    assert loaded.scope == PlotScope((("P", "S"),))
    assert window.presenter.workspace.active is active and active.state is state
    assert field.text() == "bad" and panel.pending
    assert window._settings_store.load() == settings
    assert window.main_navigation.toolbar_actions["plot"].isEnabled()
    picker.deleteLater()
    canvas.close()
    canvas.deleteLater()

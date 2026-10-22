"""Characterize the active original PLOT loader without importing legacy UI.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from pathlib import Path
from types import SimpleNamespace

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from ergotools.application.plot_layout import LoadedPlantLayout
from ergotools.domain.plot_scope import PlotScope
from ergotools.presentation.desktop.plot_layout_canvas import PlotLayoutCanvas

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("dimensions", [(1600, 600), (600, 1600), (900, 900)])
def test_active_reference_loader_matches_image_space_and_resize_fit(
    tmp_path: Path,
    dimensions: tuple[int, int],
) -> None:
    """Compare exact scene pixels, fit transform/alignment and complete bounds.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        dimensions: Original image width and height in pixels.

    Returns:
        None.
    """
    namespace = {"QPixmap": QPixmap, "Qt": Qt}
    frozen = Path(__file__).parent / "fixtures/reference_plot_load.py.txt"
    exec(compile(frozen.read_text(), str(frozen), "exec"), namespace)
    path = tmp_path / "map.png"
    pixmap = QPixmap(*dimensions)
    pixmap.fill(Qt.GlobalColor.white)
    assert pixmap.save(str(path))
    new, original = PlotLayoutCanvas(), PlotLayoutCanvas()
    try:
        for view in (new, original):
            view.show()
            view.resize(1200, 750)
        QTest.qWait(30)
        new.set_layout(
            LoadedPlantLayout(PlotScope((("P",),), "Day"), path.read_bytes())
        )
        QTest.qWait(30)
        namespace["loadImageNew"](
            SimpleNamespace(), str(path), original.scene(), original
        )
        assert new.sceneRect() == original.sceneRect()
        assert new.sceneRect().width() == dimensions[0]
        assert new.sceneRect().height() == dimensions[1]
        assert new.transform() == original.transform()
        assert new.alignment() == original.alignment()
        assert new.horizontalScrollBarPolicy() == original.horizontalScrollBarPolicy()
        new.resize(1500, 950)
        original.resize(1500, 950)
        QTest.qWait(30)
        namespace["loadImageNew"](
            SimpleNamespace(), str(path), original.scene(), original
        )
        assert new.transform() == original.transform()
        assert new.background.rotation() == 0 and new.background.scale() == 1
    finally:
        new.close()
        original.close()
        _APP.processEvents()

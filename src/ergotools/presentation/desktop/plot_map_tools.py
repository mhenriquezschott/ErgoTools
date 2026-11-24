"""Compact map layout tools over the existing PLOT marker/history owner.

Presentation layer. Selection, snap/grid and coordinates are local view settings;
only completed align/drag operations reach the injected marker layer's history.
"""

from collections.abc import Mapping

from PyQt5 import sip
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QLabel,
    QMenu,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from ergotools.presentation.desktop.plot_marker_layer import PlotMarkerLayer


class PlotMapTools(QWidget):
    """Keep compact layout tools in the map rail; spacing lives in a context menu."""

    def __init__(self, layer: PlotMarkerLayer, icons: Mapping[str, QIcon]) -> None:
        """Connect transient tools to an existing canvas and chronological history.

        Args:
            layer: Borrowed marker owner; it validates all layout operations.
            icons: Packaged designer artwork supplied by composition; no local
                designer files or generated fallback glyphs are loaded at runtime.

        Returns:
            None; construction changes neither project geometry nor preferences.
        """
        super().__init__()
        self.layer = layer
        canvas = layer.canvas
        row = QVBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        self.horizontal = QToolButton()
        self.horizontal.setText(
            layer.text("Align horizontally", "Alinear horizontalmente")
        )
        self.vertical = QToolButton()
        self.vertical.setText(layer.text("Align vertically", "Alinear verticalmente"))
        for button, horizontal in ((self.horizontal, True), (self.vertical, False)):
            button.setIcon(
                icons["horizontal_alignment" if horizontal else "vertical_alignment"]
            )
            button.setIconSize(QSize(24, 24))
            button.setToolTip(
                button.text()
                + "\n"
                + layer.text(
                    (
                        "Align selected unlocked worker centers. Drag an empty map area"
                        " to select several; Shift-click adds/removes a worker."
                    ),
                    (
                        "Alinear centros de trabajadores seleccionados sin bloqueo. "
                        "Arrastre un área vacía para seleccionar varios; Mayús-clic "
                        "agrega o quita."
                    ),
                )
            )
            button.clicked.connect(
                lambda _checked, h=horizontal: layer.align_selected(h)
            )
            row.addWidget(button, 0, Qt.AlignmentFlag.AlignHCenter)
        self.snap = QToolButton()
        self.snap.setText(layer.text("Snap", "Ajustar"))
        self.snap.setCheckable(True)
        self.snap.setIcon(icons["snap_to_grid"])
        self.snap.setToolTip(
            layer.text(
                "Snap dragged anchors to the grid. Show the grid during dragging.",
                "Ajustar anclas a la cuadrícula al arrastrar.",
            )
        )
        self.snap.toggled.connect(self.set_snap)
        row.addWidget(self.snap, 0, Qt.AlignmentFlag.AlignHCenter)
        self.spacing = QSpinBox()
        self.spacing.setRange(5, 500)
        self.spacing.setValue(40)
        self.spacing.setSuffix(" px")
        self.spacing.setMaximumWidth(90)
        self.spacing.setToolTip(
            layer.text(
                (
                    "Grid cell size in original image pixels. Starts at the "
                    "selected icon size; change it for finer placement."
                ),
                (
                    "Tamaño de celda en píxeles de imagen. Inicia con el tamaño del"
                    " símbolo; cambie para mayor precisión."
                ),
            )
        )
        self.spacing.valueChanged.connect(self.set_spacing)
        self.grid_menu = QMenu(self)
        spacing_panel = QWidget()
        spacing_layout = QVBoxLayout(spacing_panel)
        spacing_layout.addWidget(
            QLabel(
                layer.text(
                    "Grid spacing (image pixels)", "Espaciado (píxeles de imagen)"
                )
            )
        )
        spacing_layout.addWidget(self.spacing)
        spacing_action = QWidgetAction(self.grid_menu)
        spacing_action.setDefaultWidget(spacing_panel)
        self.grid_menu.addAction(spacing_action)
        self.grid = QToolButton()
        self.grid.setText(layer.text("Grid", "Cuadrícula"))
        self.grid.setCheckable(True)
        self.grid.setIcon(icons["show_grid"])
        self.grid.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.grid.customContextMenuRequested.connect(self.open_grid_menu)
        self.grid.setToolTip(
            layer.text(
                "Show the placement grid. Right-click to set grid spacing.",
                "Mostrar cuadrícula. Clic derecho para ajustar el espaciado.",
            )
        )
        self.grid.toggled.connect(self.set_grid)
        row.addWidget(self.grid, 0, Qt.AlignmentFlag.AlignHCenter)
        self.setStyleSheet(
            "QToolButton {padding:0;border:0;border-bottom:1px solid #d5dee5;"
            "border-radius:0;background:white;} QToolButton:hover {background:#eaf7f8;}"
            "QToolButton:checked {background:#ddf3f5;border-left:3px solid #08a9b5;}"
        )
        canvas.drag_changed.connect(self.drag_state)
        scene = canvas.scene()
        assert scene is not None
        scene.selectionChanged.connect(self.refresh)
        canvas.fitted.connect(self.refresh)
        self._spacing_chosen = False
        self.spacing.editingFinished.connect(self.mark_spacing)
        self.set_compact(False)
        self.refresh()

    def mark_spacing(self) -> None:
        """Retain deliberate user spacing instead of replacing it on selection.

        Args:
            None.

        Returns:
            None; local view state only.
        """
        self._spacing_chosen = True

    def refresh(self) -> None:
        """Enable alignment only for two editable unlocked selected markers.

        Args:
            None.

        Returns:
            None; selection alone never records a project edit.
        """
        if sip.isdeleted(self.horizontal) or sip.isdeleted(self.layer.canvas):
            return
        selected = [
            i
            for i in self.layer.items.values()
            if not sip.isdeleted(i)
            and i.isSelected()
            and not i.locked
            and i.isVisible()
        ]
        editable = not self.layer.canvas.read_only
        self.horizontal.setEnabled(editable and len(selected) > 1)
        self.vertical.setEnabled(editable and len(selected) > 1)
        self.snap.setEnabled(editable)
        self.spacing.setEnabled(editable)
        if selected and not self._spacing_chosen:
            self.spacing.setValue(max(5, round(selected[0].marker_rect().width())))
        self.layer.canvas._viewport.update()

    def set_snap(self, enabled: bool) -> None:
        """Toggle local drag snapping without moving any existing icon.

        Args:
            enabled: User-selected snap state.

        Returns:
            None.
        """
        self.layer.canvas.snap_enabled = enabled
        self.layer.canvas._viewport.update()

    def set_grid(self, enabled: bool) -> None:
        """Toggle the nonpersistent map grid overlay.

        Args:
            enabled: True retains the grid outside drags too.

        Returns:
            None.
        """
        self.layer.canvas.grid_visible = enabled
        self.layer.canvas._viewport.update()

    def set_spacing(self, pixels: int) -> None:
        """Set positive original-image grid spacing.

        Args:
            pixels: Validated spin-box cell side in source pixels.

        Returns:
            None.
        """
        self.layer.canvas.grid_step = float(pixels)
        self.layer.canvas._viewport.update()

    def open_grid_menu(self, point: object) -> None:
        """Open the spacing editor next to Grid without consuming map area.

        Args:
            point: Qt context-menu position; the button corner anchors the menu.

        Returns:
            None; changes remain transient map view settings.
        """
        self.grid_menu.popup(self.grid.mapToGlobal(self.grid.rect().bottomRight()))

    def set_compact(self, compact: bool) -> None:
        """Size all four rail tools consistently with the adjacent navigation tools.

        Args:
            compact: Use 34-pixel rather than 40-pixel button squares.

        Returns:
            None; icons stay large enough to distinguish alignment and grid tools.
        """
        side = 34 if compact else 40
        for button in (self.horizontal, self.vertical, self.snap, self.grid):
            button.setFixedSize(side, side)
            button.setIconSize(QSize(24 if compact else 28, 24 if compact else 28))

    def drag_state(self, active: bool) -> None:
        """Refresh the transient grid at both ends of a marker gesture.

        Args:
            active: Whether the canvas currently owns an editable marker drag.

        Returns:
            None; the always-visible grid preference is left unchanged.
        """
        self.layer.canvas._viewport.update()

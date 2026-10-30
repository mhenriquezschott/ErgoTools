"""Source-derived PLOT map/action rail with explicit preview and save intent.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

import logging
import re
from collections.abc import Callable, Mapping
from datetime import datetime

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.plot_layout import (
    LoadedPlantLayout,
    PlantLayoutReader,
    PlantLayoutWriter,
    load_plant_layout,
    save_plant_layout,
)
from ergotools.application.settings import Language
from ergotools.domain.plant_layout_image import PlantLayoutImage
from ergotools.domain.plot_scope import PlotScope
from ergotools.domain.work_hierarchy import WorkHierarchy
from ergotools.presentation.desktop.plot_layout_canvas import PlotLayoutCanvas
from ergotools.presentation.desktop.plot_navigation_icons import navigation_icon
from ergotools.presentation.desktop.theme.plot import PLOT_STYLE

# Original PLOT action-rail order with packaged icons and English/Spanish tooltips.
_ACTIONS = (
    (
        "select",
        "",
        "Select and move markers (normal cursor).",
        "Seleccionar y mover marcadores (cursor normal).",
    ),
    ("open", "open", "Open a plant layout image.", "Abrir una imagen de la planta."),
    (
        "save",
        "save",
        "Save the current plant layout.",
        "Guardar el plano actual de la planta.",
    ),
    (
        "zoom_in",
        "zoom_in",
        "Click an image point to zoom in; Esc cancels.",
        "Haga clic en un punto para acercar; Esc cancela.",
    ),
    (
        "zoom_out",
        "zoom_out",
        "Click an image point to zoom out; Esc cancels.",
        "Haga clic en un punto para alejar; Esc cancela.",
    ),
    (
        "pan",
        "",
        "Drag to pan without moving markers; Esc cancels. Middle-drag also pans.",
        (
            "Arrastre para desplazar sin mover marcadores; Esc cancela. "
            "También puede usar el botón central."
        ),
    ),
    (
        "fit",
        "",
        "Fit the entire plant image in the view.",
        "Ajustar toda la imagen de la planta a la vista.",
    ),
    (
        "opacity",
        "opacity_transparency",
        "Cycle the opacity of layout markers.",
        "Cambiar la opacidad de los marcadores.",
    ),
    (
        "capture",
        "capture_image",
        "Capture an image of the current layout.",
        "Capturar una imagen del plano actual.",
    ),
    ("export", "export", "Export layout data.", "Exportar los datos del plano."),
)


class PlotMapPanel(QWidget):
    """Own original map controls; injected adapters own all files/project mutations.

    The rail reserves the full height of its fixed-size controls, so demographic
    disclosure cannot clip the bottom export action. Canvas navigation has no image
    scrollbars; source availability controls action enablement.
    """

    def __init__(
        self,
        hierarchy: WorkHierarchy,
        reader: PlantLayoutReader,
        writer: PlantLayoutWriter,
        import_image: Callable[[str], PlantLayoutImage],
        icons: Mapping[str, QIcon],
        *,
        language: Language = Language.ENGLISH,
        parent: QWidget | None = None,
    ) -> None:
        """Build original map/rail geometry without reading or modifying a project.

        Args:
            hierarchy: Immutable saved workplace/shift catalog used to build the local
                selection tree.
            reader: Injected reader of embedded plant-layout image data.
            writer: Injected explicit plant-layout writer; preview/open actions do not
                call it.
            import_image: Injected validator returning decoded source image bytes and
                metadata for a chosen file.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        self.hierarchy = hierarchy
        self.reader = reader
        self.writer = writer
        self.import_image = import_image
        self.language = language
        self.scope: PlotScope | None = None
        self.pending_image: PlantLayoutImage | None = None
        self.setObjectName("plotCanvasPanel")
        self.setStyleSheet(PLOT_STYLE)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 0, 0)
        layout.setSpacing(8)
        self.rail = QGroupBox()
        self.rail.setObjectName("plotToolRail")
        self.rail.setFixedWidth(81)
        tools = QVBoxLayout(self.rail)
        tools.setContentsMargins(0, 0, 0, 10)
        tools.setSpacing(0)
        title = QLabel(self.text("Plant\nView", "Vista de\nplanta"))
        title.setObjectName("toolRailTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFixedHeight(42)
        title.setToolTip(
            self.text(
                "Plant layout viewing and export tools.",
                "Herramientas de vista y exportación del plano.",
            )
        )
        tools.addWidget(title)
        self.buttons: dict[str, QPushButton] = {}
        for key, asset, english, spanish in _ACTIONS:
            button = QPushButton()
            button.setObjectName("plotToolButton")
            button.setFixedSize(63, 63)
            button.setIconSize(QSize(48, 48))
            button.setIcon(
                navigation_icon(
                    "select" if key == "select" else "pan" if key == "pan" else "fit"
                )
                if key in ("select", "pan", "fit")
                else icons[asset]
            )
            button.setToolTip(self.text(english, spanish))
            button.setEnabled(False)
            if key in ("select", "zoom_in", "zoom_out", "pan"):
                button.setCheckable(True)
            self.buttons[key] = button
        # Share one rail row between magnifiers to add Pan without a taller rail.
        for key, *_rest in _ACTIONS:
            if key == "zoom_in":
                zoom_row = QWidget()
                zoom_layout = QHBoxLayout(zoom_row)
                zoom_layout.setContentsMargins(0, 0, 0, 0)
                zoom_layout.setSpacing(0)
                for zoom_key in ("zoom_in", "zoom_out"):
                    zoom_button = self.buttons[zoom_key]
                    zoom_button.setProperty("compactZoom", True)
                    zoom_button.setProperty("zoomOut", zoom_key == "zoom_out")
                    zoom_button.setFixedSize(32 if zoom_key == "zoom_out" else 31, 63)
                    zoom_button.setIconSize(QSize(29, 29))
                    zoom_layout.addWidget(zoom_button)
                tools.addWidget(zoom_row, 0, Qt.AlignmentFlag.AlignHCenter)
            elif key != "zoom_out":
                tools.addWidget(self.buttons[key], 0, Qt.AlignmentFlag.AlignHCenter)
        tools.addStretch(1)
        self.rail.setMinimumHeight(tools.minimumSize().height())
        layout.addWidget(self.rail)
        self.canvas = PlotLayoutCanvas()
        self.canvas.language = language
        self.canvas.setToolTip(
            self.text(
                "Plant layout canvas. Select workers and use the tool rail "
                "to navigate or export the view.",
                "Plano de la planta. Seleccione trabajadores y use las herramientas "
                "para navegar o exportar la vista.",
            )
        )
        column = QVBoxLayout()
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(6)
        column.addWidget(self.canvas, 1)
        layout.addLayout(column, 1)
        self.buttons["open"].clicked.connect(self.open_image)
        self.buttons["save"].clicked.connect(self.save_image)
        self.buttons["select"].clicked.connect(self.canvas.cancel_navigation)
        self.buttons["zoom_in"].clicked.connect(self.canvas.begin_zoom)
        self.buttons["zoom_out"].clicked.connect(self.canvas.zoom_out)
        self.buttons["fit"].clicked.connect(self.canvas.reset_view)
        self.buttons["pan"].clicked.connect(self.canvas.begin_pan)
        self.canvas.navigation_changed.connect(self.sync_navigation)
        self.canvas.fitted.connect(self.sync_navigation)
        # Qt toggles checkable buttons before clicked; active tools remain checked
        # even when pressing the already-selected tool leaves its mode unchanged.
        for key in ("select", "zoom_in", "zoom_out", "pan"):
            self.buttons[key].clicked.connect(self.sync_navigation)
        self.buttons["opacity"].clicked.connect(self.canvas.cycle_opacity)
        self.buttons["capture"].clicked.connect(self.capture_image)

    def sync_navigation(self) -> None:
        """Reflect armed tools and fitted zoom limits without recording data/history.

        Args:
            None; both navigation and transform signals are projection-only.

        Returns:
            None; signal blocking avoids toggling a mode during button projection.
        """
        mode = self.canvas.navigation_mode
        available = self.canvas.background is not None
        for key in ("select", "zoom_in", "zoom_out", "pan"):
            button = self.buttons[key]
            previous = button.blockSignals(True)
            button.setChecked(mode == key)
            button.blockSignals(previous)
            button.setEnabled(
                available
                and (key not in ("zoom_out", "pan") or self.canvas.can_zoom_out)
            )
        state = self.canvas.navigation_snapshot()
        percentage = f"{state.zoom * 100 if state else 100:.1f}".rstrip("0").rstrip(".")
        for key, _asset, english, spanish in _ACTIONS:
            if key in ("zoom_in", "zoom_out"):
                self.buttons[key].setToolTip(
                    self.text(english, spanish)
                    + "\n"
                    + self.text(
                        f"Current zoom: {percentage}% (maximum 400%).",
                        f"Zoom actual: {percentage}% (máximo 400%).",
                    )
                )

    def text(self, english: str, spanish: str) -> str:
        """Translate owned captions without interpreting stored plant identities.

        Args:
            english: English UI text; saved user values are never translated by this
                helper.
            spanish: Spanish UI text corresponding to the English caption.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return spanish if self.language is Language.SPANISH else english

    def set_scope(self, scope: PlotScope) -> bool:
        """Load a saved scope before committing selection; retain preview on failure.

        A different scope requires explicit discard of a pending image. Selecting the
        same scope preserves that preview without reading or refreshing again.

        Args:
            scope: Exact typed workplace filter; no selection is reconstructed from
                displayed labels.

        Returns:
            True when scope/map acceptance succeeds (including an unchanged scope);
            False after rejection or handled failure.
        """
        if scope == self.scope:
            return True
        if self.pending_image is not None and not self.confirm_discard():
            return False
        try:
            loaded = load_plant_layout(self.hierarchy, scope, self.reader)
            self.canvas.set_layout(loaded)
        except Exception:
            # Keep technical details in diagnostics and preserve the current map.
            logging.getLogger(__name__).exception("Unable to load PLOT layout")
            self.show_error(
                self.text(
                    "The workplace layout could not be loaded. The "
                    "current map has been kept.",
                    "No se pudo cargar el plano del lugar de "
                    "trabajo. Se conservó el plano actual.",
                )
            )
            return False
        self.update_view_actions()
        self.scope = scope
        self.pending_image = None
        self.buttons["open"].setEnabled(True)
        self.buttons["save"].setEnabled(False)
        return True

    def choose_image(self) -> str:
        """Use the reference PNG/JPG chooser; cancellation has no side effects.

        Args:
            None.

        Returns:
            Selected PNG/JPEG image path, or an empty string after cancellation.
        """
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.text("Select Plant Image", "Seleccionar imagen de la planta"),
            "",
            self.text("Images (*.png *.jpg)", "Imágenes (*.png *.jpg)"),
        )
        return path

    def open_image(self) -> None:
        """Preview validated original pixels without saving project or source data.

        Args:
            None.

        Returns:
            None.
        """
        if self.scope is None:
            return
        path = self.choose_image()
        if not path:
            return
        try:
            image = self.import_image(path)
            self.canvas.set_layout(LoadedPlantLayout(self.scope, image.data))
        except Exception:
            logging.getLogger(__name__).exception("Unable to import PLOT image")
            self.show_error(
                self.text(
                    "The image could not be opened. Select a readable PNG or JPG file.",
                    "No se pudo abrir la imagen. Seleccione un "
                    "archivo PNG o JPG legible.",
                )
            )
            return
        self.update_view_actions()
        self.pending_image = image
        self.buttons["save"].setEnabled(True)

    def update_view_actions(self) -> None:
        """Enable map-only actions for actual pixels, including an unsaved preview.

        Args:
            None.

        Returns:
            None.
        """
        available = self.canvas.background is not None
        for key in ("zoom_in", "zoom_out", "pan", "fit", "opacity", "capture"):
            self.buttons[key].setEnabled(available)
        self.sync_navigation()

    def choose_capture(self) -> str:
        """Use the original PNG chooser with a portable plant/timestamp filename.

        Args:
            None.

        Returns:
            Selected PNG capture destination, or an empty string after cancellation.
        """
        assert self.scope is not None
        plant = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", self.scope.plant)
        suggested = f"{plant}_{datetime.now():%Y%m%d_%H%M%S}.png"
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.text(
                "Save Plant Layout Image", "Guardar imagen del plano de la planta"
            ),
            suggested,
            self.text(
                "PNG Files (*.png);;All Files (*)", "Archivos PNG (*.png);;Todos (*)"
            ),
        )
        return path

    def capture_image(self) -> None:
        """Save exactly the current scaled view as PNG; cancellation never writes.

        Qt's encoder returns False for failures instead of raising. Both failures and
        exceptions are reported; project image/marker data remain untouched.

        Args:
            None.

        Returns:
            None.
        """
        if self.scope is None or self.canvas.background is None:
            return
        path = self.choose_capture()
        if not path:
            return
        try:
            if not self.canvas.grab().save(path, "PNG"):
                raise OSError("Qt could not encode the PLOT view as PNG.")
        except Exception:
            logging.getLogger(__name__).exception("Unable to capture PLOT view")
            self.show_error(
                self.text(
                    "The layout image could not be saved. Choose a writable location.",
                    "No se pudo guardar la imagen del plano. Elija una ubicación "
                    "con permiso de escritura.",
                )
            )

    def save_image(self) -> None:
        """Commit the preview for its exact scope; a failure keeps it retryable.

        Args:
            None.

        Returns:
            None.
        """
        if self.scope is None or self.pending_image is None:
            return
        try:
            save_plant_layout(
                self.hierarchy, self.scope, self.pending_image, self.writer
            )
        except Exception:
            # The writer owns rollback; this view retains the accepted preview.
            logging.getLogger(__name__).exception("Unable to save PLOT image")
            self.show_error(
                self.text(
                    "The image could not be saved. The preview has "
                    "been kept; you can retry.",
                    "No se pudo guardar la imagen. Se conservó la "
                    "vista previa; puede reintentar.",
                )
            )
            return
        self.pending_image = None
        self.buttons["save"].setEnabled(False)
        self.message(
            self.text("Success", "Éxito"),
            self.text(
                "Plant image has been saved successfully.",
                "La imagen de la planta se ha guardado correctamente.",
            ),
            QMessageBox.Icon.Information,
        )

    def confirm_discard(self) -> bool:
        """Require consent before changing the scope of an unsaved image preview.

        Args:
            None.

        Returns:
            True only for explicit Yes to discarding the pending plant-image preview.
        """
        return (
            self.message(
                self.text("Unsaved plant image", "Imagen de planta sin guardar"),
                self.text(
                    "Discard the unsaved image and change workplace?",
                    "¿Descartar la imagen sin guardar y cambiar de lugar de trabajo?",
                ),
                QMessageBox.Icon.Question,
                question=True,
            )
            == QMessageBox.StandardButton.Yes
        )

    def show_error(self, body: str) -> None:
        """Display an adapter failure using the owned PLOT style and literal text.

        Args:
            body: Literal message content shown by the owned styled dialog.

        Returns:
            None.
        """
        self.message(self.text("Error", "Error"), body, QMessageBox.Icon.Critical)

    def message(
        self, title: str, body: str, icon: QMessageBox.Icon, *, question: bool = False
    ) -> int:
        """Own localized native message buttons; default discard confirmation to No.

        Args:
            title: Localized message/window title; never used as a stored identifier.
            body: Literal message content shown by the owned styled dialog.
            icon: Qt message severity icon.
            question: True presents Yes/No consent; False presents an informational
                acknowledgement.

        Returns:
            Qt standard-button/result integer selected by the user; the owned temporary
            dialog is released.
        """
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setTextFormat(Qt.TextFormat.PlainText)
        box.setText(body)
        box.setIcon(icon)
        labels: tuple[tuple[QMessageBox.StandardButton, str], ...]
        if question:
            box.setStandardButtons(
                QMessageBox.StandardButtons(QMessageBox.StandardButton.Yes)
                | QMessageBox.StandardButton.No
            )
            box.setDefaultButton(QMessageBox.StandardButton.No)
            labels = (
                (QMessageBox.StandardButton.Yes, self.text("Yes", "Sí")),
                (QMessageBox.StandardButton.No, self.text("No", "No")),
            )
        else:
            box.setStandardButtons(QMessageBox.StandardButton.Ok)
            labels = ((QMessageBox.StandardButton.Ok, "OK"),)
        for standard, label in labels:
            button = box.button(standard)
            assert button is not None
            button.setText(label)
        try:
            return box.exec()
        finally:
            box.deleteLater()

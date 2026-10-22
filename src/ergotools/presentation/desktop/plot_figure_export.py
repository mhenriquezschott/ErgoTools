"""Explicit PLOT chart export using the original chooser and error boundary.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

import logging
import re
from pathlib import Path

from matplotlib.figure import Figure
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget

from ergotools.domain.language import Language


def export_plot(
    figure: Figure,
    parent: QWidget,
    language: Language,
    name: str,
    *,
    expanded: bool = False,
) -> bool:
    """Save an explicitly chosen chart at source 300 DPI; Cancel has no side effect.

    A suffix follows the selected graph-settings filter when absent. The expanded viewer
    retains its original PNG/JPEG/all-files chooser and no success popup. Failures are
    logged and shown locally; they never close the owning dialog.

    Args:
        figure: Owned Matplotlib figure; no pyplot global state or scientific values are
            modified.
        parent: Required Qt owner of the new control; ownership follows the parent
            widget lifetime.
        language: UI language only; does not reinterpret saved names, numeric inputs or
            units.
        name: Literal project/scheme name or export-name stem; None preserves the
            operation's stated default.
        expanded: True reveals optional detail controls; False collapses them without
            clearing values.

    Returns:
        True after successful file export; False on cancellation or a locally reported
        export failure.
    """
    spanish = language is Language.SPANISH
    title = (
        ("Guardar gráfico" if spanish else "Save Plot")
        if expanded
        else ("Guardar gráfico de resumen" if spanish else "Save Summary Plot")
    )
    slug = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower() or "plot-summary"
    if expanded:
        filters = (
            "Archivos PNG (*.png);;Archivos JPEG (*.jpg);;Todos los archivos (*)"
            if spanish
            else "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
        )
    else:
        filters = (
            "Imagen PNG (*.png);;Imagen JPEG (*.jpg *.jpeg);;"
            "Imagen SVG (*.svg);;Documento PDF (*.pdf)"
            if spanish
            else "PNG image (*.png);;JPEG image (*.jpg *.jpeg);;"
            "SVG image (*.svg);;PDF document (*.pdf)"
        )
    path, selected_filter = QFileDialog.getSaveFileName(
        parent, title, "" if expanded else slug + ".png", filters
    )
    if not path:
        return False
    if not expanded and not Path(path).suffix:
        path += next(
            (
                suffix
                for label, suffix in (
                    ("JPEG", ".jpg"),
                    ("SVG", ".svg"),
                    ("PDF", ".pdf"),
                )
                if label in selected_filter
            ),
            ".png",
        )
    try:
        figure.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    except Exception:
        logging.getLogger(__name__).exception("Unable to export PLOT chart")
        QMessageBox.critical(
            parent,
            title,
            "No se pudo guardar el gráfico."
            if spanish
            else "The graph could not be saved.",
        )
        return False
    if not expanded:
        QMessageBox.information(
            parent,
            "Guardar gráfico" if spanish else "Save plot",
            ("Gráfico guardado en:\n" if spanish else "Graph saved to:\n") + path,
        )
    return True

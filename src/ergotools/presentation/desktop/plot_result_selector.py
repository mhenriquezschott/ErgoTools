"""Compact PLOT selection control opening a shared searchable workplace tree.

Presentation layer. Store immutable filtered rows and an assignment identity; never
use display captions as keys or retain a hidden flat combo for compatibility.
"""

from collections.abc import Mapping
from html import escape

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QSizePolicy, QToolButton, QWidget

from ergotools.application.plot_results import PlotWorkerResult
from ergotools.domain.language import Language
from ergotools.presentation.desktop.plot_result_picker import PlotResultPicker


class PlotResultSelector(QToolButton):
    """Browse applied results with stable IDs and local keyboard/button navigation."""

    selection_changed = pyqtSignal(int)

    def __init__(
        self,
        icons: Mapping[str, QIcon],
        *,
        job_view: bool = False,
        language: Language = Language.ENGLISH,
        parent: QWidget | None = None,
    ) -> None:
        """Create a native button rather than an unbounded dropdown list.

        Args:
            icons: Packaged search, workplace and record glyphs used by the picker.
            job_view: Select Job-risk occurrences rather than individual results.
            language: Interface language only.
            parent: Owning overview widget.

        Returns:
            None; browsing/cancelling never changes the project.
        """
        super().__init__(parent)
        self.icons, self.job_view, self.language = icons, job_view, language
        self.rows: tuple[PlotWorkerResult, ...] = ()
        self.catalog: tuple[PlotWorkerResult, ...] = ()
        self.selected_id: int | None = None
        self.setObjectName("plotSelectionButton")
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setIcon(icons["search"])
        self.setIconSize(QSize(20, 20))
        self.setFixedHeight(36)
        self.setMinimumWidth(80)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.clicked.connect(self.open_picker)
        self.set_rows(())

    @property
    def current_index(self) -> int:
        """Locate the selected assignment in the caller-provided result ordering.

        Args:
            None.

        Returns:
            Zero-based row index, or -1 when no result is selected.
        """
        return next(
            (
                index
                for index, row in enumerate(self.rows)
                if row.assessment.assignment_id == self.selected_id
            ),
            -1,
        )

    def set_rows(
        self,
        rows: tuple[PlotWorkerResult, ...],
        preferred: int | None = None,
        *,
        catalog: tuple[PlotWorkerResult, ...] | None = None,
    ) -> None:
        """Project rows and a valid preferred ID without emitting user intent.

        Args:
            rows: Already filtered/ordered assignments; no additional database reads.
            preferred: Host-selected assignment, falling back to prior selection/first.
            catalog: Applied-scope search rows before a local alphabet filter, or None
                when the visible rows are already the full search scope.

        Returns:
            None; the full literal caption stays in the tooltip when width is narrow.
        """
        self.rows = rows
        self.catalog = rows if catalog is None else catalog
        identities = {row.assessment.assignment_id for row in rows}
        identity = preferred if preferred in identities else self.selected_id
        self.selected_id = (
            identity
            if identity in identities
            else rows[0].assessment.assignment_id
            if rows
            else None
        )
        row = self.row_for_id(self.selected_id)
        if row is None:
            caption = (
                "Elegir trabajo…"
                if self.job_view and self.language is Language.SPANISH
                else "Choose Job…"
                if self.job_view
                else "Elegir trabajador…"
                if self.language is Language.SPANISH
                else "Choose worker…"
            )
        elif self.job_view:
            caption = f"{row.job.job_id if row.job else '—'} · {row.worker.worker_id}"
        else:
            name = ", ".join(
                value
                for value in (row.worker.last_name, row.worker.first_name)
                if value
            )
            caption = (
                f"{row.worker.worker_id} · {name}" if name else row.worker.worker_id
            )
        self.setText(caption)
        action = (
            "Buscar y elegir en el árbol de lugares de trabajo"
            if self.language is Language.SPANISH
            else "Search and choose from the workplace tree"
        )
        self.setToolTip("<qt>" + escape(caption) + "<br>" + escape(action) + "</qt>")
        self.setEnabled(bool(rows))

    def row_for_id(self, identity: int | None) -> PlotWorkerResult | None:
        """Resolve an exact assignment ID without parsing any displayed name.

        Args:
            identity: Stable assignment identity, or None for an empty selection.

        Returns:
            The immutable row, or None when it is outside the current result set.
        """
        return next(
            (row for row in self.rows if row.assessment.assignment_id == identity), None
        )

    def select_id(self, identity: int) -> None:
        """Accept a valid user selection and notify its host once.

        Args:
            identity: Assignment ID chosen from this selector's filtered rows.

        Returns:
            None; invalid IDs and reselecting the current row emit no operation.
        """
        candidate = next(
            (row for row in self.catalog if row.assessment.assignment_id == identity),
            None,
        )
        if candidate is not None and identity != self.selected_id:
            rows = self.rows if self.row_for_id(identity) is not None else self.catalog
            self.set_rows(rows, identity, catalog=self.catalog)
            self.selection_changed.emit(identity)

    def navigate(self, index: int) -> None:
        """Clamp first/previous/next/last browsing to the current filtered ordering.

        Args:
            index: Desired zero-based row index.

        Returns:
            None; navigation changes selection only, never source data.
        """
        if self.rows:
            self.select_id(
                self.rows[
                    max(0, min(index, len(self.rows) - 1))
                ].assessment.assignment_id
            )

    def open_picker(self) -> None:
        """Open the hierarchy picker; Cancel retains the current map selection.

        Args:
            None.

        Returns:
            None; only explicit acceptance of a valid row emits selection_changed.
        """
        if not self.rows:
            return
        dialog = PlotResultPicker(
            self.catalog,
            self.icons,
            job_view=self.job_view,
            selected_id=self.selected_id,
            language=self.language,
            parent=self,
        )
        try:
            if (
                dialog.exec() == QDialog.DialogCode.Accepted
                and dialog.selected_assignment_id is not None
            ):
                self.select_id(dialog.selected_assignment_id)
        finally:
            dialog.deleteLater()

"""Owned modal host for the reusable assessment import/paste panel.

The same panel is embedded in Settings. This host adds no parsing, project writer or
independent history; callers accept its immutable replacement through existing services.
"""

from collections.abc import Mapping

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QWidget

from ergotools.application.assessment_import import ImportProfile, TabularFileReader
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.assessment_import_panel import (
    AssessmentImportPanel,
)
from ergotools.presentation.desktop.assessment_import_panel import (
    clipboard_field as clipboard_field,
)
from ergotools.presentation.desktop.assessment_import_panel import (
    clipboard_header_system as clipboard_header_system,
)
from ergotools.presentation.desktop.theme.dialogs import apply_dialog_theme


class AssessmentPasteDialog(QDialog):
    """Stage task values in one shared panel before explicit host acceptance."""

    def __init__(
        self,
        source: AssessmentDraft,
        text: str,
        language: Language,
        convention: DecimalConvention,
        system: MeasurementSystem,
        start_row: int,
        parent: QWidget | None = None,
        *,
        icons: Mapping[str, QIcon] | None = None,
        start_field: str = "task_name",
        profile: ImportProfile | None = None,
        file_reader: TabularFileReader | None = None,
    ) -> None:
        """Own a reusable import editor without accepting source or preference edits.

        Args:
            icons: Injected packaged action glyphs; no asset lookup or source writes.
            source: Exact immutable destination captured after pending text resolves.
            text: Optional initial clipboard data; empty permits loading a file.
            language: Static interface language.
            convention: Initial numeric decimal convention.
            system: Initial source units.
            start_row: Focused zero-based destination row.
            parent: Native modal owner.
            start_field: Focused input column for headerless data.
            profile: Optional remembered per-tool interpretation/mapping.
            file_reader: Explicit read-only file capability; None disables file loading.

        Returns:
            None; source data is staged until prepare succeeds and the owner accepts it.
        """
        super().__init__(parent)
        self.icons = icons or {}
        self.panel = AssessmentImportPanel(
            source,
            text,
            language,
            convention,
            system,
            start_row,
            self,
            start_field=start_field,
            profile=profile,
            icons=self.icons,
            file_reader=file_reader,
        )
        self.setWindowTitle(self.panel.windowTitle())
        self.setWindowIcon(self.icons.get("worksheet", QIcon()))
        self.resize(1180, 860)
        apply_dialog_theme(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.panel)
        self.panel.prepared.connect(self.accept)
        self.panel.cancelled.connect(self.reject)
        self.finished.connect(self.panel.stop_validation)
        # Preserve the typed controls used by hosts and native acceptance probes.
        self.header_option = self.panel.header_option
        self.units = self.panel.units
        self.decimal = self.panel.decimal
        self.error = self.panel.error
        self.table = self.panel.table
        self.start = self.panel.start

    @property
    def replacement(self) -> AssessmentDraft | None:
        """Read the validated replacement, absent after invalid/cancelled input.

        Args:
            None.

        Returns:
            Staged replacement; only the caller owns project acceptance.
        """
        return self.panel.replacement

    def prepare(self) -> None:
        """Validate the shared panel and accept the modal only on success.

        Args:
            None.

        Returns:
            None; validation errors remain visible without source mutation.
        """
        self.panel.prepare()

"""Embed the shared import panel in Settings, storing only per-tool preferences.

No assessment target is exposed here. File/clipboard previews are temporary, and host
Apply/Cancel owns acceptance; switching tools retains explicit mapping drafts.
"""

from collections.abc import Mapping

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ergotools.application.assessment_import import ImportProfile, TabularFileReader
from ergotools.domain.assessments.document import AssessmentDraft, AssessmentKind
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.assessment_import_panel import AssessmentImportPanel


def import_preview_source(
    kind: AssessmentKind, units: MeasurementSystem
) -> AssessmentDraft:
    """Create a transient blank preview source, never a project assessment.

    Args:
        kind: Tool whose allowed input columns are configured.
        units: Initial source units.

    Returns:
        Empty typed source used solely for personal-settings previews.
    """
    if kind is AssessmentKind.LIFFT:
        return LifftDraft(units)
    if kind is AssessmentKind.DUET:
        return DuetDraft()
    return TstDraft(units)


class AssessmentImportSettings(QWidget):
    """Hold independent tool drafts around the same reusable modal import panel."""

    def __init__(
        self,
        language: Language,
        units: MeasurementSystem,
        decimal: DecimalConvention,
        profiles: tuple[ImportProfile, ...],
        reader: TabularFileReader | None,
        parent: QWidget | None = None,
        *,
        icons: Mapping[str, QIcon] | None = None,
    ) -> None:
        """Build tool selection with temporary data previews and no target Apply action.

        Args:
            icons: Injected packaged action glyphs; no asset lookup or source writes.
            language: English/Spanish labels.
            units: Initial source units when no tool profile exists.
            decimal: Initial numeric convention.
            profiles: Existing immutable personal profiles, copied into local drafts.
            reader: Explicit optional read-only file capability.
            parent: Settings page owner.

        Returns:
            None; no personal preference/project write occurs before host Apply.
        """
        super().__init__(parent)
        self.icons = icons or {}
        self.language, self.units, self.decimal, self.reader = (
            language,
            units,
            decimal,
            reader,
        )
        self._profiles = {p.kind: p for p in profiles}
        self._kind = AssessmentKind.LIFFT
        self._panel_defaults: dict[AssessmentKind, ImportProfile] = {}
        self._panels: dict[AssessmentKind, AssessmentImportPanel] = {}
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        bar.addWidget(QLabel("Herramienta" if language is Language.SPANISH else "Tool"))
        self.tools = QComboBox()
        for caption, kind in [
            ("LiFFT", AssessmentKind.LIFFT),
            ("DUET", AssessmentKind.DUET),
            ("ST", AssessmentKind.TST),
        ]:
            self.tools.addItem(caption, kind)
        self.tools.setToolTip(
            "Preferencias independientes para cada herramienta."
            if language is Language.SPANISH
            else "Independent import defaults for each tool."
        )
        bar.addWidget(self.tools)
        bar.addStretch(1)
        self.root.addLayout(bar)
        self.tools.currentIndexChanged.connect(self.show_tool)
        self.show_tool()

    def show_tool(self) -> None:
        """Switch independent panel drafts without copying source data into preferences.

        Args:
            None.

        Returns:
            None; staged file/clipboard contents remain window-local only.
        """
        for panel in self._panels.values():
            panel.hide()
        kind = self.tools.currentData()
        self._kind = kind
        if kind not in self._panels:
            profile = self._profiles.get(
                kind, ImportProfile(kind, units=self.units, decimal=self.decimal)
            )
            panel = AssessmentImportPanel(
                import_preview_source(kind, profile.units),
                "",
                self.language,
                profile.decimal,
                profile.units,
                0,
                self,
                profile=profile,
                icons=self.icons,
                file_reader=self.reader,
                embedded=True,
            )
            panel.start.setEnabled(False)
            self._panels[kind] = panel
            self._panel_defaults[kind] = panel.profile()
            self.root.addWidget(panel)
        self._panels[kind].show()

    def profiles(self) -> tuple[ImportProfile, ...]:
        """Read validated profile drafts without serializing staged preview values.

        Args:
            None.

        Returns:
            All existing profiles plus explicitly changed tool configurations.

        Raises:
            ValueError: A mapping or numeric interpretation is invalid.
        """
        result = dict(self._profiles)
        for kind, panel in self._panels.items():
            try:
                current = panel.profile()
            except ValueError:
                self.tools.setCurrentIndex(self.tools.findData(kind))
                raise
            if current != self._panel_defaults[kind]:
                result[kind] = current
        return tuple(sorted(result.values(), key=lambda p: p.kind.value))

    def show_error(self, error: ValueError) -> None:
        """Present a correctable preference failure on the active tool panel.

        Args:
            error: Invalid personal mapping or numeric interpretation.

        Returns:
            None; no host/private widget lookup or preference publication occurs.
        """
        from ergotools.presentation.desktop.assessment_import_text import (
            assessment_import_error,
        )

        self._panels[self._kind].error.setText(
            assessment_import_error(error, self.language)
        )

    def stop_validation(self) -> None:
        """Release every owned staging timer when the surrounding Settings closes.

        Args:
            None.

        Returns:
            None; preference drafts remain readable for the host's explicit Apply.
        """
        for panel in self._panels.values():
            panel.stop_validation()

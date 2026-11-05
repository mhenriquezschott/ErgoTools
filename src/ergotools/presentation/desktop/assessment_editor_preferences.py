"""Injected shared editor preferences and value-only file capability.

Presentation service. Owned hosts explicitly bind their grids; column changes use
owned Qt signals. No global window lookup,
project mutation, calculator, file writer or independent Undo stack exists here.
"""

from dataclasses import replace

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget

from ergotools.application.assessment_import import ImportProfile, TabularFileReader
from ergotools.application.settings import SettingsStore
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.assessment_task_grid import AssessmentTaskGrid


class AssessmentEditorPreferences(QObject):
    """Borrow explicit settings/reader ports, independently of project ownership.

    Attributes:
        columns_changed: Accepted personal visibility published to explicitly bound
            editable grids; the Qt receivers own connection lifetime.
    """

    columns_changed = pyqtSignal(object)

    def __init__(self, store: SettingsStore, reader: TabularFileReader) -> None:
        """Retain injected application preferences and read-only file reader.

        Args:
            store: Personal settings port, never a project repository.
            reader: Bounded detached CSV/TSV/XLSX values reader.

        Returns:
            None; no I/O is performed at construction.
        """
        super().__init__()
        self.store, self.reader = store, reader

    def bind(self, owner: QWidget) -> None:
        """Bind only grids owned by an explicitly supplied window/component.

        Args:
            owner: Host whose editable grids receive shared editor preferences.

        Returns:
            None; read-only copy grids do not gain editing capabilities.
        """
        profiles = self.store.load().assessment_columns
        grids = owner.findChildren(AssessmentTaskGrid)
        if isinstance(owner, AssessmentTaskGrid):
            grids.insert(0, owner)
        for grid in grids:
            if not grid.read_only and grid.editor_preferences is not self:
                grid.editor_preferences = self
                grid.set_column_preferences(profiles)
                self.columns_changed.connect(grid.set_column_preferences)

    def profile(
        self, kind: AssessmentKind, units: MeasurementSystem, decimal: DecimalConvention
    ) -> ImportProfile:
        """Read this tool's defaults without interpreting any assessment data.

        Args:
            kind: Exact current tool.
            units: Current input units used only if no profile exists.
            decimal: Current decimal convention used only for initial defaults.

        Returns:
            Existing immutable preferences or an unconfigured first-use profile.
        """
        return next(
            (p for p in self.store.load().import_profiles if p.kind is kind),
            ImportProfile(kind, units=units, decimal=decimal),
        )

    def save(self, profile: ImportProfile) -> None:
        """Replace one tool's interpretation without persisting imported source values.

        Args:
            profile: Validated explicit personal choices.

        Returns:
            None; preserves unrelated preferences and all other tool mappings.

        Raises:
            OSError: Atomic preference publication fails.
            ValueError: Existing preferences or this profile are invalid.
        """
        settings = self.store.load()
        profiles = (
            *(p for p in settings.import_profiles if p.kind is not profile.kind),
            profile,
        )
        self.store.save(
            replace(
                settings,
                import_profiles=tuple(sorted(profiles, key=lambda p: p.kind.value)),
            )
        )

    def refresh_columns(self) -> None:
        """Publish accepted personal visibility to bound editors without rebinding data.

        Args:
            None.

        Returns:
            None; Qt retires connections with their owned grid receivers.
        """
        self.columns_changed.emit(self.store.load().assessment_columns)

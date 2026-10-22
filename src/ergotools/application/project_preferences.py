"""Optional project preference port, independent of storage and desktop controls.

Application layer: let the owned workspace change display metadata without exposing
SQL or rewriting assessment inputs/results. Diagnostic repositories may omit this port.
"""

from typing import Protocol, runtime_checkable

from ergotools.domain.project import ProjectMetadata


@runtime_checkable
class ProjectPreferencesRepository(Protocol):
    """Native adapter capability for atomic project display-preference writes."""

    def update_display_settings(self, metadata: ProjectMetadata) -> None:
        """Persist validated display defaults on the owned repository.

        Args:
            metadata: Same project identity/details with changed units/precision only.

        Returns:
            None after successful persistence; failure must retain previous metadata.
        """
        ...

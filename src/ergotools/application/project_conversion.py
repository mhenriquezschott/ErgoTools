"""Application port for optional, external project upgrades.

Defines discovery, literal command guidance and publication responsibilities.
Implementations own process execution; desktop policy owns user consent, temporary
destinations and first Save. Native projects never require the tool.

Application layer. Define immutable capability/operation contracts independently of Qt
and storage implementations. Callers own modal consent and borrowed project lifetime;
concrete adapters own I/O and transaction enforcement.
"""

from typing import Protocol


class ProjectConversion(Protocol):
    """Recognize earlier files and publish a separate self-contained native copy."""

    def requires_conversion(self, location: str) -> bool:
        """Recognize an earlier container or obsolete native result envelope.

        Args:
            location: Existing selected project path.

        Returns:
            Whether opening requires the optional external upgrade utility.

        Raises:
            OSError: The selected file cannot be read.
            ValueError: Header metadata cannot be interpreted.
        """
        ...

    def command_line(self, source: str, destination: str) -> str:
        """Describe an equivalent external command without executing it.

        Args:
            source: Original project path, preserved by conversion.
            destination: Separate nonexistent native output path.

        Returns:
            Platform-quoted command text suitable for copying to a terminal.
        """
        ...

    def convert(self, source: str, destination: str) -> None:
        """Publish a complete native project without changing the active workspace.

        The caller owns temporary-file cleanup, activation and first Save. No
        recent-project setting or active assessment is changed by this operation.

        Args:
            source: Earlier project and, when applicable, its original sidecars.
            destination: Absent output path owned by the caller.

        Returns:
            None after successful publication and closure of owned handles.

        Raises:
            OSError: Process launch or source/output access fails.
            ValueError: Conversion or native validation fails.
        """
        ...

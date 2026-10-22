"""Project-owned JROT scheme persistence port for the original form workflow.

Application layer. Define immutable capability/operation contracts independently of Qt
and storage implementations. Callers own modal consent and borrowed project lifetime;
concrete adapters own I/O and transaction enforcement.
"""

from typing import Protocol

from ergotools.domain.rotation_scheme import RotationScheme


class RotationSchemeRepository(Protocol):
    """Read without migration; persist only explicit save/delete commands."""

    def load_rotation_schemes(self) -> tuple[RotationScheme, ...]:
        """Load stable ordered schemes with original Job/assignment links.

        Args:
            None.

        Returns:
            Stable ordered saved schemes with their original frozen Job/assignment
            links, without solving.
        """
        ...

    def save_rotation_scheme(self, scheme: RotationScheme) -> None:
        """Atomically save a complete current scheme, excluding optimizer previews.

        Args:
            scheme: Complete saved rotation with exact historical
                worker/placement/profile links; optimizer previews alone are not saved.

        Returns:
            None after atomic save of the complete validated current scheme, preserving
            frozen historical links.
        """
        ...

    def delete_rotation_scheme(self, scheme_id: str) -> None:
        """Delete an existing selected scheme after the desktop obtains consent.

        Args:
            scheme_id: Exact existing saved scheme identity; caller owns delete
                confirmation.

        Returns:
            None after removing the explicitly selected saved scheme; no other scheme is
            selected or optimized.
        """
        ...

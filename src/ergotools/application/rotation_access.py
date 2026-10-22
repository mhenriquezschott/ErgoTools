"""Borrowed full-project capability for the original modal JROT workflow.

Application layer. Define immutable capability/operation contracts independently of Qt
and storage implementations. Callers own modal consent and borrowed project lifetime;
concrete adapters own I/O and transaction enforcement.
"""

from typing import Protocol, runtime_checkable

from ergotools.application.rotation_pool import RotationPoolReader
from ergotools.application.rotation_repository import RotationSchemeRepository


@runtime_checkable
class RotationRepository(RotationPoolReader, RotationSchemeRepository, Protocol):
    """Supply saved catalogs and explicit scheme commands without handle ownership."""

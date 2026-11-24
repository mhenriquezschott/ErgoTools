"""Bounded mobile project history using the shared immutable DocumentSession engine.

Snapshots are complete native bytes, owned only by the isolated tablet workspace.
No SQL schema or core history implementation changes. The timeline is in memory;
accepted working bytes remain recoverable across Android process restart.
"""

from dataclasses import dataclass
from pathlib import Path

from ergotools.application.session import DocumentKey


@dataclass(frozen=True)
class ProjectChange:
    """Pure immutable replacement consumed by the existing history engine.

    Attributes:
        document: Private mobile project owner.
        label_key: Human-readable prototype action label for Undo/Redo.
        before: Expected complete native snapshot.
        after: Successful replacement snapshot.
    """

    document: DocumentKey
    label_key: str
    before: bytes
    after: bytes

    def apply(self, state: bytes) -> bytes:
        """Reject stale history ownership before accepting a complete native state.

        Args:
            state: Current engine snapshot.

        Returns:
            Exact next bytes; no storage operation occurs here.
        """
        if state != self.before:
            raise ValueError("Project history no longer matches the working file.")
        return self.after


@dataclass(frozen=True)
class SavedMarker:
    """Verify the already published native file before marking a revision clean.

    Attributes:
        path: Explicitly saved private tablet file.
    """

    path: Path

    def save(self, document: DocumentKey, state: bytes) -> None:
        """Confirm durable publication through DocumentSession's save contract.

        Args:
            document: Project timeline owner; identity does not become a file path.
            state: Current complete native state expected in the saved file.

        Returns:
            None; mismatching storage raises and retains the dirty marker.
        """
        if self.path.read_bytes() != state:
            raise ValueError("Saved project does not match the active revision.")

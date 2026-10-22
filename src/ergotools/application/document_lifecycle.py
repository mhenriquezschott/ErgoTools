"""Single-document lifecycle coordination with explicit dirty-state decisions.

Application layer. Coordinate immutable domain sources and the explicit ports shown
below; GUI controls, SQL and filesystem policy belong to adapters. These operations run
synchronously on their owning session thread; no background or multi-user coordination
is introduced.
"""

from enum import StrEnum
from typing import Protocol

from ergotools.application.session import DocumentKey, DocumentSession, DocumentStore


class DocumentRepository[State](DocumentStore[State], Protocol):
    """Read/write port returning fully validated immutable document snapshots."""

    def load(self, document: DocumentKey) -> State:
        """Return the complete source snapshot or raise without changing storage.

        Args:
            document: Exact project/document owner; commands and persistence cannot
                redirect it to another assessment.

        Returns:
            Fully validated deeply immutable saved source; loading must not mutate the
            stored document.
        """
        ...


class CloseChoice(StrEnum):
    """User intent for leaving a draft, independent of dialog text or language."""

    # Explicitly save a dirty source before leaving; failures preserve the active draft.
    SAVE = "save"
    # Leave without writing the dirty draft; this does not delete its saved document.
    DISCARD = "discard"
    # Retain the current source and history without loading or saving.
    CANCEL = "cancel"


class DocumentLifecycle[State]:
    """Own an active document reference without owning storage connections.

    Single-owner-thread synchronous operations only. Callers route edits through the
    active session. No project paths, dialogs, Save As or multi-document workspace
    semantics are inferred by this coordinator.
    """

    def __init__(
        self,
        repository: DocumentRepository[State],
        initial: DocumentSession[State] | None = None,
    ) -> None:
        """Adopt an optional new/loaded session without performing storage I/O.

        Args:
            repository: Borrowed document repository port; this coordinator does not own
                its connections.
            initial: Optional already-created/loaded active session; None starts with no
                open document.

        Returns:
            None. Retain the borrowed repository and optional active session without
            loading or saving.
        """
        self._repository = repository
        self._active = initial
        self._busy = False

    @property
    def active(self) -> DocumentSession[State] | None:
        """Return the active document, or None when no document is open.

        Args:
            None.

        Returns:
            Current session, or None when no document is open; the repository remains
            separately owned.
        """
        return self._active

    def _check(self, choice: CloseChoice | None) -> None:
        """Validate close intent and reject reentrant lifecycle operations.

        Args:
            choice: Explicit Save/Discard/Cancel intent for a dirty draft, or None when
                no decision has been supplied.

        Returns:
            None when the coordinator is idle and any supplied close choice has the
            correct enum type.

        Raises:
            RuntimeError: Another lifecycle operation is active.
            ValueError: The supplied close choice is not a supported enum.
        """
        if self._busy:
            raise RuntimeError("A document lifecycle operation is already active.")
        if choice is not None and not isinstance(choice, CloseChoice):
            raise ValueError("Unsupported close choice.")

    def _permitted(self, choice: CloseChoice | None) -> bool:
        """Decide whether leaving the active draft has explicit sufficient consent.

        Args:
            choice: Explicit Save/Discard/Cancel intent for a dirty draft, or None when
                no decision has been supplied.

        Returns:
            False for Cancel or an undecided dirty draft; True for clean/no active
            source or explicit Save/Discard consent.
        """
        if choice is CloseChoice.CANCEL:
            return False
        return self._active is None or not self._active.is_dirty or choice is not None

    def _save_if_requested(self, choice: CloseChoice | None) -> None:
        """Save the dirty active draft only when the caller explicitly chose Save.

        Args:
            choice: Explicit Save/Discard/Cancel intent for a dirty draft, or None when
                no decision has been supplied.

        Returns:
            None. Call the storage port only for an active dirty source and explicit
            Save; propagate failures.
        """
        if (
            self._active is not None
            and self._active.is_dirty
            and choice is CloseChoice.SAVE
        ):
            self._active.save(self._repository)

    def open(self, document: DocumentKey, *, choice: CloseChoice | None = None) -> bool:
        """Switch only after a valid load and any requested save both succeed.

        Return False on cancellation or a dirty draft without an explicit choice.
        Reopening the active identity preserves its draft/history without I/O. Load the
        target before saving/discarding the current draft, so a failed load cannot cause
        an unnecessary write or discard. Exceptions propagate.

        Args:
            document: Exact project/document owner; commands and persistence cannot
                redirect it to another assessment.
            choice: Explicit Save/Discard/Cancel intent for a dirty draft, or None when
                no decision has been supplied.

        Returns:
            True after adopting a valid loaded target, or for the already active
            identity; False on Cancel or missing dirty-state consent.

        Raises:
            RuntimeError: The coordinator is busy or the active source changed during a
                load.
            ValueError: The supplied close choice is unsupported; repository load/save
                failures propagate before adopting the target.
        """
        self._check(choice)
        if choice is CloseChoice.CANCEL:
            return False
        current = self._active
        if current is not None and current.document == document:
            return True
        if not self._permitted(choice):
            return False
        token = (current.revision, current.is_dirty) if current is not None else None
        self._busy = True
        try:
            loaded = self._repository.load(document)
            if current is not None and token != (current.revision, current.is_dirty):
                raise RuntimeError("The active draft changed while loading a document.")
            candidate = DocumentSession(document, loaded, persisted=True)
            self._save_if_requested(choice)
            self._active = candidate
            return True
        finally:
            self._busy = False

    def close(self, *, choice: CloseChoice | None = None) -> bool:
        """Release the active reference only after consent and successful save.

        Discard never writes/deletes stored records. Cancel or absent dirty-state
        consent retains the same session and history. The repository stays open.

        Args:
            choice: Explicit Save/Discard/Cancel intent for a dirty draft, or None when
                no decision has been supplied.

        Returns:
            True after optional successful Save and releasing the active reference;
            False retains the same draft/history.

        Raises:
            RuntimeError: Another lifecycle operation is active.
            ValueError: The supplied close choice is unsupported; requested-save
                failures preserve the active source.
        """
        self._check(choice)
        if not self._permitted(choice):
            return False
        self._busy = True
        try:
            self._save_if_requested(choice)
            self._active = None
            return True
        finally:
            self._busy = False

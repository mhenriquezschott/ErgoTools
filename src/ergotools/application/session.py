"""Document-owned immutable draft history and synchronous save coordination.

Snapshots must be deeply immutable values. Commands are pure transformations: no I/O,
mutation of the input, or irreversible side effects. This is a single owner-thread
contract, not a concurrency or transaction implementation.

Application layer. Coordinate immutable domain sources and the explicit ports shown
below; GUI controls, SQL and filesystem policy belong to adapters. These operations run
synchronously on their owning session thread; no background or multi-user coordination
is introduced.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class DocumentKey:
    """Stable project/document identity; display names and paths are not identity.

    Attributes:
        project_id: Exact stable project identity, independent of path or display name.
        document_id: Exact stable source-document identity within the project.
    """

    project_id: str
    document_id: str

    def __post_init__(self) -> None:
        """Reject empty identifiers before history or storage can be addressed.

        Args:
            None.

        Returns:
            None. Validate nonblank owner identifiers before history or storage is
            addressed.

        Raises:
            ValueError: Project or document identity is blank.
        """
        if not self.project_id.strip() or not self.document_id.strip():
            raise ValueError("Project and document identifiers must not be blank.")


class EditCommand[State](Protocol):
    """Pure validated edit returning a new immutable document snapshot."""

    @property
    def document(self) -> DocumentKey:
        """Identify the only document this command is allowed to change.

        Args:
            None.

        Returns:
            The sole project/document identity that the implementation may edit.
        """
        ...

    @property
    def label_key(self) -> str:
        """Provide a stable localization key for the Undo/Redo action label.

        Args:
            None.

        Returns:
            Stable localization key for Undo/Redo text, never a pretranslated display
            label.
        """
        ...

    def apply(self, state: State) -> State:
        """Return the edited value, or raise without changing the original.

        Args:
            state: Current immutable source snapshot; successful edits return a
                replacement rather than mutating it.

        Returns:
            New deeply immutable source snapshot, or an equal unchanged value for a
            no-op. Validation failures propagate without source mutation.

        Raises:
            DraftError: The task/grid edit violates the command's identity, position,
                blank-slot or expected-source preconditions.
        """
        ...


class DocumentStore[State](Protocol):
    """Storage port confirming atomic acceptance by the owning repository.

    Direct file adapters persist durably; integrated project editing stages privately
    until the main project Save. Concrete adapters preserve the preceding accepted
    document on failure. This protocol prescribes neither an on-disk format nor the
    enclosing project's durable publication policy.
    """

    def save(self, document: DocumentKey, state: State) -> None:
        """Persist the snapshot atomically; raise if the operation did not commit.

        Args:
            document: Exact project/document owner; commands and persistence cannot
                redirect it to another assessment.
            state: Current immutable source snapshot; successful edits return a
                replacement rather than mutating it.

        Returns:
            None only after atomic repository acceptance; failure leaves the previous
            accepted document intact. The project owner decides durable publication.
        """
        ...


@dataclass(frozen=True, slots=True)
class _Revision[State]:
    """One immutable history revision with its stable identity and edit label.

    Attributes:
        number: Monotonic session-local revision identity; undo restores an earlier
            identity.
        state: Deeply immutable source snapshot retained by this history entry.
        label_key: Stable localization key describing the edit; None for the initial
            revision.
    """

    number: int
    state: State
    label_key: str | None


class DocumentSession[State]:
    """Own one document's history; independent of widgets, locale and storage.

    A loaded snapshot uses persisted=True; a new unsaved document uses False. Revision
    numbers are monotonic within this session, not persisted IDs. Undo/redo restores
    immutable source snapshots without rerunning commands. AssessmentEvaluator owns
    derived calculation and freshness separately from this source history. The
    generic timeline is unlimited until its application owner configures a positive
    command budget through set_history_limit; eviction never changes current data.
    """

    def __init__(
        self, document: DocumentKey, initial: State, *, persisted: bool = False
    ) -> None:
        """Create an isolated session with no I/O or shared application globals.

        Args:
            document: Exact project/document owner; commands and persistence cannot
                redirect it to another assessment.
            initial: Deeply immutable initial source snapshot; no loading or calculation
                occurs during adoption.
            persisted: True marks the initial revision clean; False creates an unsaved
                source with no clean revision.

        Returns:
            None. Own an independent initial history, cursor, revision counter and clean
            marker without I/O.
        """
        self._document = document
        self._history = [_Revision(0, initial, None)]
        self._cursor = 0
        self._next_revision = 1
        self._saved_revision: int | None = 0 if persisted else None
        self._busy = False
        self._history_limit: int | None = None

    @property
    def document(self) -> DocumentKey:
        """Return the immutable owner of this history.

        Args:
            None.

        Returns:
            Immutable identity owning this entire source-history timeline.
        """
        return self._document

    @property
    def state(self) -> State:
        """Return the current immutable draft snapshot.

        Args:
            None.

        Returns:
            Current deeply immutable source snapshot; consumers must not mutate
            referenced values.
        """
        return self._history[self._cursor].state

    @property
    def revision(self) -> int:
        """Return a session-local identity for the current historical state.

        Args:
            None.

        Returns:
            Session-local monotonic revision identity of the current state; undo
            restores the prior identity.
        """
        return self._history[self._cursor].number

    @property
    def is_dirty(self) -> bool:
        """Report whether the current revision differs from the last saved one.

        Args:
            None.

        Returns:
            True when the current revision differs from the last successful save,
            including an initially unsaved document.
        """
        return self.revision != self._saved_revision

    @property
    def undo_label_key(self) -> str | None:
        """Return the undo action key, or None when undo is unavailable.

        Args:
            None.

        Returns:
            Stable action key for the current edit, or None at the initial history
            state.
        """
        return self._history[self._cursor].label_key if self._cursor else None

    @property
    def redo_label_key(self) -> str | None:
        """Return the redo action key, or None when redo is unavailable.

        Args:
            None.

        Returns:
            Stable action key for the next retained edit, or None when the redo branch
            is exhausted.
        """
        if self._cursor + 1 == len(self._history):
            return None
        return self._history[self._cursor + 1].label_key

    def _require_idle(self) -> None:
        """Reject edits or saves reentering an active document operation.

        Args:
            None.

        Returns:
            None when no synchronous edit/save is in progress.

        Raises:
            RuntimeError: An edit or synchronous save is already in progress on this
                session.
        """
        if self._busy:
            raise RuntimeError("A document edit or save is already in progress.")

    def execute(self, command: EditCommand[State]) -> bool:
        """Apply a valid edit; return False for an equal-state no-op.

        No-ops and failed commands preserve the redo branch and clean marker. A
        successful new edit discards redo and receives a fresh revision ID.
        Configured capacity releases the oldest excess snapshots after acceptance.
        Wrong-document commands, blank labels and reentrant operations fail.

        Args:
            command: Pure validated edit with matching document identity and a nonblank
                localization label key.

        Returns:
            True for a committed new history revision; False for an equal-state no-op
            that retains redo and the clean marker.

        Raises:
            RuntimeError: An edit or save is already in progress.
            ValueError: The command targets another document or has a blank history
                label.
        """
        self._require_idle()
        if command.document != self.document:
            raise ValueError("Command belongs to another document.")
        label_key = command.label_key
        if not label_key.strip():
            raise ValueError("Command label key must not be blank.")
        self._busy = True
        try:
            after = command.apply(self.state)
            if after == self.state:
                return False
            revision = _Revision(self._next_revision, after, label_key)
            history = [*self._history[: self._cursor + 1], revision]
            self._history = history
            self._cursor += 1
            self._next_revision += 1
            self._trim_history()
            return True
        finally:
            self._busy = False

    def set_history_limit(self, limit: int | None) -> None:
        """Bound retained commands without changing current data or revision identity.

        The current state and nearest preceding Undo steps take priority. Redo fills
        remaining capacity; shrinking while undone may discard excess Redo. Increasing
        capacity cannot recover discarded steps. The saved revision marker is retained
        independently, even when its snapshot leaves the timeline.

        Args:
            limit: Positive command budget, or None for the diagnostic unlimited policy.

        Returns:
            None; current source and monotonic revision allocation remain unchanged.

        Raises:
            ValueError: A non-None budget is not a positive integer; bool is rejected.
            RuntimeError: An edit or synchronous save is in progress.
        """
        self._require_idle()
        if limit is not None and (type(limit) is not int or limit < 1):
            raise ValueError("History limit must be a positive integer or None.")
        self._history_limit = limit
        self._trim_history()

    def _trim_history(self) -> None:
        """Release excess snapshots while preserving the active source and cursor.

        Args:
            None.

        Returns:
            None; at most limit plus one states remain when a budget is configured.
        """
        limit = self._history_limit
        if limit is None:
            return
        first = max(0, self._cursor - limit)
        self._history = self._history[first : first + limit + 1]
        self._cursor -= first

    def undo(self) -> bool:
        """Restore the preceding snapshot, or return False at the initial state.

        Args:
            None.

        Returns:
            True after restoring the preceding snapshot; False at the initial state. No
            command is rerun or saved.

        Raises:
            RuntimeError: An edit or synchronous save is already in progress.
        """
        self._require_idle()
        if self._cursor == 0:
            return False
        self._cursor -= 1
        return True

    def redo(self) -> bool:
        """Restore the next snapshot, or return False when no redo branch exists.

        Args:
            None.

        Returns:
            True after restoring the next snapshot; False when no redo remains. No
            command is rerun or saved.

        Raises:
            RuntimeError: An edit or synchronous save is already in progress.
        """
        self._require_idle()
        if self._cursor + 1 == len(self._history):
            return False
        self._cursor += 1
        return True

    def mark_unsaved(self) -> None:
        """Retain source/history identities after the owner rolls back staging.

        Args:
            None.

        Returns:
            None; clear only the accepted-storage marker. Immutable inputs, revision,
            calculation provenance and Undo/Redo remain available for an exact retry.

        Raises:
            RuntimeError: A source edit/save currently owns this session.
        """
        self._require_idle()
        self._saved_revision = None

    def amend_current(self, state: State) -> None:
        """Synchronize derived checkpoint data without inventing a user action.

        Args:
            state: Exact same-action state with refreshed derived/persistence data.
                User edits must use execute instead.

        Returns:
            None; retain the revision identity, action label, cursor and Redo branch.
            Project persistence separately compares data against its saved baseline.

        Raises:
            RuntimeError: A source edit or save is in progress.
        """
        self._require_idle()
        current = self._history[self._cursor]
        self._history[self._cursor] = _Revision(
            current.number, state, current.label_key
        )

    def replace_from_owner(self, state: State, *, persisted: bool = True) -> None:
        """Rebind a live document projection after its project owner replays history.

        Args:
            state: Exact immutable source from the restored project checkpoint.
            persisted: True marks the source clean relative to the owning repository;
                the project session separately tracks durable file changes.

        Returns:
            None; retain this session object's identity, invalidate old edit contexts
            with a fresh revision and discard its superseded local history. The shared
            project history owns reversal across this boundary.

        Raises:
            RuntimeError: A document operation is currently active.
        """
        self._require_idle()
        number = self._next_revision
        self._next_revision += 1
        self._history = [_Revision(number, state, None)]
        self._cursor = 0
        self._saved_revision = number if persisted else None

    def save(self, store: DocumentStore[State]) -> None:
        """Mark clean only after storage succeeds; saving is not an undo entry.

        Failure propagates and leaves history/dirty state unchanged. Mutating operations
        cannot reenter during this synchronous save. The caller may retry after failure.
        Opening, Save As and dirty-close choices are outside this document-level port
        and are not implicitly performed here.

        Args:
            store: Borrowed atomic document storage port; successful return confirms the
                commit before marking clean.

        Returns:
            None after the storage port succeeds and the current revision becomes clean.
            Saving adds no undo entry.

        Raises:
            RuntimeError: An edit or synchronous save is already in progress;
                storage-port failures also propagate without marking clean.
        """
        self._require_idle()
        self._busy = True
        try:
            store.save(self.document, self.state)
            self._saved_revision = self.revision
        finally:
            self._busy = False

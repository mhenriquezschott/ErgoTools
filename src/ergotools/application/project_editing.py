"""Project-session persistence and chronological cross-editor history.

Application layer. Opaque repository checkpoints and deeply immutable editor values
share the existing DocumentSession engine. No SQL, widgets, files or calculators
belong here. Accepted edits change private session state; commit is the only durable
write. Editor callbacks are borrowed for their live GUI lifetime and removable on close.
"""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from types import MethodType
from typing import Protocol, runtime_checkable
from weakref import WeakMethod

from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.application.settings import DEFAULT_UNDO_LIMIT, validate_undo_limit


@runtime_checkable
class EditingRepository(Protocol):
    """Optional repository capability for private editing and atomic publication."""

    def begin_editing(self, changed: Callable[[str], None]) -> None:
        """Detach writes from the durable project and report accepted mutations.

        Args:
            changed: Owner-thread callback after an outermost successful mutation.

        Returns:
            None; ordinary repository ports now operate on private session data.
        """
        ...

    def editing_checkpoint(self) -> bytes:
        """Return an immutable opaque snapshot of all native project data.

        Args:
            None.

        Returns:
            Adapter-owned checkpoint bytes, including embedded assets and results.
        """
        ...

    def restore_editing_checkpoint(self, checkpoint: bytes) -> None:
        """Validate and restore private data atomically without publishing it.

        Args:
            checkpoint: Exact checkpoint produced by this adapter for this project.

        Returns:
            None; invalid checkpoints leave the current session unchanged.
        """
        ...

    def editing_records(self) -> frozenset[tuple[str, str]]:
        """Identify business records for removal confirmations.

        Args:
            None.

        Returns:
            Immutable kind/identity pairs; configuration and scientific values are
            excluded because editing a value is not deleting a record.
        """
        ...

    def commit_editing(self) -> None:
        """Atomically write all private project data to its durable destination.

        Args:
            None.

        Returns:
            None on success; failures preserve the previous file and editable session.
        """
        ...


@dataclass(frozen=True, slots=True)
class ProjectEditState:
    """Complete reversible project session without GUI ownership.

    Attributes:
        data: Opaque repository checkpoint; scientific inputs/results stay exact.
        records: Record identities used to explain removals before replay.
        editors: Named deeply immutable view/draft values, never Qt objects.
    """

    data: bytes
    records: frozenset[tuple[str, str]]
    editors: tuple[tuple[str, object], ...] = ()


@dataclass(frozen=True, slots=True)
class ReplaceProjectEdit:
    """Existing DocumentSession command for one accepted project action.

    Attributes:
        document: Stable project-session owner.
        after: Complete proposed private state.
        label_key: Stable action identity, translated by the presentation adapter.
    """

    document: DocumentKey
    after: ProjectEditState
    label_key: str

    def apply(self, state: ProjectEditState) -> ProjectEditState:
        """Return an already validated immutable checkpoint.

        Args:
            state: Previous complete private state; never mutated.

        Returns:
            Proposed state, including equal-state no-ops handled by DocumentSession.
        """
        return self.after


class ProjectEditingSession:
    """Own private accepted data and one chronological project history.

    All editor values must be deeply immutable. Repository checkpoints remain opaque
    to this layer. Weak listeners cannot retain Qt windows or workspace owners, and
    removal confirmation remains with presentation. Dirty detection compares native
    data and persistent draft tokens; view-only changes never require Save.

    Attributes:
        repository: Borrowed private editing capability; the workspace owns closing it.
        history: Existing DocumentSession engine containing complete project revisions.
        replaying: True only during validated project restoration and live rebinding.
        replay_revision: Replayed action identity for presentation-only caches, or None
            outside replay. No widget or viewport state enters this module.
    """

    def __init__(
        self,
        project_id: str,
        repository: EditingRepository,
        *,
        undo_limit: int = DEFAULT_UNDO_LIMIT,
    ) -> None:
        """Begin private editing without writing the project file.

        Args:
            project_id: Stable project identity, independent of path or caption.
            repository: Borrowed owned-project capability; workspace closes it.
            undo_limit: Personal shared command budget, 1-50; defaults to 25.

        Returns:
            None; initial private state is clean and has no Undo entry.

        Raises:
            ValueError: The Undo limit is not an integer from 1 through 50.
        """
        validate_undo_limit(undo_limit)
        self.replaying = False
        self.replay_revision: int | None = None
        self.repository = repository
        self._suspended = 0
        self._editors: dict[str, object] = {}
        self._listeners: list[Callable[[], None]] = []
        self._validators: dict[str, Callable[[object | None], None]] = {}
        self._persistent_keys: set[str] = set()
        self._saved_editors: dict[str, object] = {}
        repository.begin_editing(self.record)
        self._saved_data = repository.editing_checkpoint()
        self.history = DocumentSession(
            DocumentKey(project_id, "project-session"), self._snapshot(), persisted=True
        )
        self.history.set_history_limit(undo_limit)

    def set_undo_limit(self, limit: int) -> None:
        """Apply a personal command budget and update every borrowing editor.

        Args:
            limit: Validated application preference, integer from 1 through 50.

        Returns:
            None; trimming changes neither project data nor the durable Save baseline.

        Raises:
            ValueError: The budget is outside the application range or is not integer.
            RuntimeError: The history is executing an edit or synchronous save.
        """
        validate_undo_limit(limit)
        self.history.set_history_limit(limit)
        self.notify()

    @property
    def is_dirty(self) -> bool:
        """Distinguish project data edits from reversible view-only changes.

        Args:
            None.

        Returns:
            True when native data or entered persistent draft intent differs from
            the last durable Save; view-only changes remain clean.
        """
        return self.history.state.data != self._saved_data or any(
            self._editors.get(key) != self._saved_editors.get(key)
            for key in self._persistent_keys
        )

    def _snapshot(self) -> ProjectEditState:
        """Capture exact repository data and retained immutable editor values.

        Args:
            None.

        Returns:
            Complete state, sharing unchanged immutable values between revisions.
        """
        return ProjectEditState(
            self.repository.editing_checkpoint(),
            self.repository.editing_records(),
            tuple(sorted(self._editors.items())),
        )

    @contextmanager
    def suspend(self) -> Iterator[None]:
        """Group nested repository writes into a single caller-recorded operation.

        Args:
            None.

        Yields:
            None; the caller records the final successful accepted state explicitly.
        """
        self._suspended += 1
        try:
            yield
        finally:
            self._suspended -= 1

    @contextmanager
    def stage(self) -> Iterator[None]:
        """Rollback a failed multi-port acceptance without writing the project file.

        Args:
            None.

        Yields:
            None; nested repository notifications are grouped. The caller records a
            successful complete action and restores its source dirty markers on failure.
        """
        before = self._snapshot()
        with self.suspend():
            try:
                yield
            except Exception:
                self.repository.restore_editing_checkpoint(before.data)
                self._editors = dict(before.editors)
                raise

    def record(self, label: str) -> None:
        """Record an accepted outer operation, ignoring suspended calls and no-ops.

        Args:
            label: Stable action identity; display translation belongs to the UI.

        Returns:
            None; a new action truncates Redo and notifies live action adapters.
        """
        if self._suspended:
            return
        after = self._snapshot()
        if label == "assessment.edit" and after.data == self.history.state.data:
            return
        added = after.records - self.history.state.records
        removed = self.history.state.records - after.records
        worker_added = [identity for kind, identity in added if kind == "worker"]
        worker_removed = [identity for kind, identity in removed if kind == "worker"]
        if len(worker_added) == 1:
            label = "worker.add:" + worker_added[0]
        elif len(worker_removed) == 1:
            label = "worker.delete:" + worker_removed[0]
        if self.history.execute(
            ReplaceProjectEdit(self.history.document, after, label)
        ):
            self.notify()

    def set_editor(
        self, key: str, value: object, label: str, *, persistent: bool = False
    ) -> None:
        """Retain an accepted immutable editor state and record it chronologically.

        Args:
            key: Project-local editor identity, stable across window reopening.
            value: Deeply immutable source/view state; widgets and mutable values
                violate this contract.
            label: Stable action identity for Undo/Redo text.
            persistent: Mark this data-only value as unsaved intent, including drafts
                that cannot yet be represented by the native complete-record schema.

        Returns:
            None; identical values add no history step.
        """
        if value is None and key not in self._editors:
            return
        self._editors[key] = value
        if persistent:
            self._persistent_keys.add(key)
        self.record(label)

    def validate_on_save(
        self, key: str, validator: Callable[[object | None], None]
    ) -> None:
        """Retain a widget-free validator for an editor's accepted project draft.

        Args:
            key: Retained editor identity to validate before durable publication.
            validator: Widget-free validation/staging callback through private ports;
                it must retain no Qt/window owner or publish a durable file.

        Returns:
            None; replacing a validator does not add a history entry.
        """
        self._validators[key] = validator

    def seed_editor(self, key: str, value: object) -> None:
        """Retain a window's initial projection without adding a user action.

        Args:
            key: Stable editor identity absent/None before its first usable projection.
            value: Deeply immutable initial view/draft state.

        Returns:
            None; later accepted actions capture this projection in their checkpoints.
        """
        if self._editors.get(key) is None:
            self._editors[key] = value
        self.synchronize()

    def project_editor(self, key: str, value: object) -> None:
        """Fold automatic view rebinding into its accepted data operation.

        Args:
            key: Stable immutable editor projection identity.
            value: View resulting from creation/deletion or initial window display.

        Returns:
            None; automatic selection cleanup and window closure add no Undo step.
        """
        self._editors[key] = value
        self.synchronize()

    def editor(self, key: str) -> object | None:
        """Read a retained editor value without creating an edit.

        Args:
            key: Project-local editor identity.

        Returns:
            Immutable accepted state, or None when this editor has not been used.
        """
        return self._editors.get(key)

    def subscribe(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register one live UI refresh callback and return its detach operation.

        Args:
            listener: Owner-thread callback; must not create edits while replaying.

        Returns:
            Idempotent cleanup callback for the subscriber's lifetime.
        """
        if isinstance(listener, MethodType):
            receiver = WeakMethod(listener)

            def callback() -> None:
                """Refresh a still-live subscriber without retaining its window.

                Args:
                    None.

                Returns:
                    None; dead workspace/editor owners are ignored.
                """
                method = receiver()
                if method is not None:
                    method()
        else:
            callback = listener
        listeners = self._listeners
        listeners.append(callback)

        def detach() -> None:
            """Release the borrowed callback without affecting retained project data.

            Args:
                None.

            Returns:
                None; repeated detachment is harmless.
            """
            if callback in listeners:
                listeners.remove(callback)

        return detach

    def notify(self) -> None:
        """Refresh live adapters after accepted edits, saves or replay.

        Args:
            None.

        Returns:
            None; listener iteration tolerates subscription changes during refresh.
        """
        for listener in tuple(self._listeners):
            listener()

    def removals(self, *, redo: bool) -> frozenset[tuple[str, str]]:
        """Preview exactly which records the next replay would remove.

        Args:
            redo: True examines Redo; False examines Undo.

        Returns:
            Kind/identity pairs absent from the target, or an empty set when the
            operation only restores records, edits values or changes navigation.
        """
        current = self.history.state
        with self.suspend():
            moved = self.history.redo() if redo else self.history.undo()
            if not moved:
                return frozenset()
            target = self.history.state
            self.history.undo() if redo else self.history.redo()
        return current.records - target.records

    def replay(self, *, redo: bool) -> bool:
        """Restore one complete action after the caller's removal confirmation.

        Args:
            redo: True restores the next action; False restores the preceding one.

        Returns:
            True after successful replay; False at the history boundary. Invalid
            repository restoration preserves the original cursor and state.
        """
        previous = self.history.state
        operation_revision = self.history.revision
        moved = self.history.redo() if redo else self.history.undo()
        if not moved:
            return False
        self.replaying = True
        self.replay_revision = self.history.revision if redo else operation_revision
        try:
            with self.suspend():
                state = self.history.state
                self.repository.restore_editing_checkpoint(state.data)
                self._editors = dict(state.editors)
                self.notify()
        except Exception:
            self.history.undo() if redo else self.history.redo()
            with self.suspend():
                self.repository.restore_editing_checkpoint(previous.data)
                self._editors = dict(previous.editors)
            raise
        finally:
            self.replaying = False
            self.replay_revision = None
        return True

    def save(self, document: DocumentKey, state: ProjectEditState) -> None:
        """Implement DocumentStore by committing the complete private repository.

        Args:
            document: Exact shared-history owner; foreign projects are rejected.
            state: Current complete history state, validated against the owner.

        Returns:
            None after atomic durable commit; storage failures remain retryable.

        Raises:
            ValueError: Caller supplies a different project or obsolete checkpoint.
        """
        if document != self.history.document or state != self.history.state:
            raise ValueError("Project Save belongs to another revision.")
        self.repository.commit_editing()

    def synchronize(self) -> None:
        """Fold same-source calculated output into the current accepted action.

        Args:
            None.

        Returns:
            None; Save adds no Undo step and cannot truncate an existing Redo branch.
        """
        self.history.amend_current(self._snapshot())

    def validate(self) -> None:
        """Validate all retained data drafts before Save or Save As publication.

        Args:
            None.

        Returns:
            None when every entered draft can be represented by the native schema;
            invalid drafts raise their specific error without changing data or history.
        """
        with self.stage():
            for key, validator in self._validators.items():
                validator(self._editors.get(key))
        self.synchronize()

    def commit(self) -> None:
        """Save once and mark clean only after the complete commit succeeds.

        Args:
            None.

        Returns:
            None; Save adds no history entry and retains Undo/Redo across saves.
        """
        self.validate()
        self.history.save(self)
        self._saved_editors = dict(self._editors)
        self._saved_data = self.history.state.data
        self.notify()

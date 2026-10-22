"""Session-local chronological assessment navigation and source replay.

Application layer: combine reversible worker/tool/context viewing with existing
DocumentSession commands. No Qt, SQL, calculations, persistence or global Undo lives
here. Worker/context Save/Discard decisions remain with ProjectWorkspace; crossing
that boundary drops source replay entries, preserving view navigation alone.
"""

from collections.abc import Callable
from dataclasses import dataclass

from ergotools.application.assessment_navigation import AssessmentView
from ergotools.application.session import DocumentSession
from ergotools.domain.assessments.document import AssessmentDraft


@dataclass(frozen=True, slots=True)
class InteractionStep:
    """One accepted view change or source revision interval.

    Attributes:
        before: Exact view before the operation, or None for unclassified harnesses.
        after: Exact view after the operation.
        session: Source owner for an edit; None denotes navigation only.
        start: Source revision before an edit; unused for navigation.
        end: Source revision after an edit; unused for navigation.
    """

    before: AssessmentView | None
    after: AssessmentView | None
    session: DocumentSession[AssessmentDraft] | None = None
    start: int = 0
    end: int = 0


def same_position(left: AssessmentView | None, right: AssessmentView | None) -> bool:
    """Compare selection identities without treating saved labels as navigation.

    Args:
        left: Earlier view, including context-free or preview selections.
        right: Current view; saved status and Job captions may change on Save/rename.

    Returns:
        True for the same worker/tool/workplace/assignment/document selection.
    """
    if left is None or right is None:
        return left is right
    return (
        left.worker_id,
        left.kind,
        left.workplace,
        left.assignment_id,
        left.document_id,
    ) == (
        right.worker_id,
        right.kind,
        right.workplace,
        right.assignment_id,
        right.document_id,
    )


class AssessmentInteractions:
    """Order accepted UI navigation and source changes within one open project.

    Attributes:
        undo_steps: Chronological accepted operations awaiting reversal.
        redo_steps: Reversed operations awaiting reapplication, most recent at the end.
        replaying: Suppress new entries while the host restores a selection/source;
            refresh observations still synchronize the accepted baseline.
    """

    def __init__(self) -> None:
        """Start empty without opening a project or capturing widget state.

        Args:
            None.

        Returns:
            None; history is in-memory and lasts only for this project session.
        """
        self.undo_steps: list[InteractionStep] = []
        self.redo_steps: list[InteractionStep] = []
        self._scope: str | None = None
        self._view: AssessmentView | None = None
        self._session: DocumentSession[AssessmentDraft] | None = None
        self._revision = 0
        self.replaying = False

    def observe(
        self,
        scope: str | None,
        view: AssessmentView | None,
        session: DocumentSession[AssessmentDraft] | None,
    ) -> None:
        """Capture accepted operations; duplicate refreshes add no history entries.

        Args:
            scope: Open project location, or None after closing; changes clear history.
            view: Exact accepted navigation view; pending or cancelled intent is absent.
            session: Active source/history owner, or None with no project.

        Returns:
            None; Save and label updates alone add no entry. Worker/workplace/assignment
            departure drops source commands whose Save/Discard lifecycle has ended.
            During replay only synchronize the baseline, preventing recursive entries.
        """
        if scope != self._scope:
            self.undo_steps.clear()
            self.redo_steps.clear()
            self._view = None
            self._session = None
        elif not self.replaying:
            if (
                not same_position(self._view, view)
                and self._view is not None
                and view is not None
            ):
                if (
                    self._view.worker_id,
                    self._view.workplace,
                    self._view.assignment_id,
                ) != (view.worker_id, view.workplace, view.assignment_id):
                    self.undo_steps[:] = [
                        s for s in self.undo_steps if s.session is None
                    ]
                self._record(InteractionStep(self._view, view))
            elif (
                session is self._session
                and session is not None
                and session.revision != self._revision
            ):
                self._record(
                    InteractionStep(
                        view, view, session, self._revision, session.revision
                    )
                )
        self._scope, self._view, self._session = scope, view, session
        self._revision = session.revision if session is not None else 0

    def _record(self, step: InteractionStep) -> None:
        """Append an accepted operation and discard its superseded redo branch.

        Args:
            step: Immutable source interval or exact selection transition.

        Returns:
            None; no database, source or navigation change is performed.
        """
        self.undo_steps.append(step)
        self.redo_steps.clear()

    def replay(
        self,
        redo: bool,
        restore: Callable[[AssessmentView], bool],
        session: DocumentSession[AssessmentDraft] | None,
    ) -> bool:
        """Replay one accepted operation without inventing another source command.

        Args:
            redo: True reapplies the next operation; False restores the previous one.
            restore: Host callback restoring an exact view with ordinary dirty consent;
                False denotes cancellation and keeps the history cursor unchanged.
            session: Current live source owner; detached/discarded sources are
                not replayed.

        Returns:
            True after a successful replay; False for an empty stack, cancellation or
            a source owner/revision mismatch. Failures retain the history entry.
        """
        source = self.redo_steps if redo else self.undo_steps
        target = self.undo_steps if redo else self.redo_steps
        if not source:
            return False
        step = source[-1]
        self.replaying = True
        try:
            if step.session is None:
                view = step.after if redo else step.before
                if view is None or not restore(view):
                    return False
            else:
                expected, revision = (
                    (step.start, step.end) if redo else (step.end, step.start)
                )
                if session is not step.session or session.revision != expected:
                    return False
                forward = revision > expected
                while session.revision != revision:
                    changed = session.redo() if forward else session.undo()
                    if not changed:
                        return False
            source.pop()
            target.append(step)
            return True
        finally:
            self.replaying = False

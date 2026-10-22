"""Input preparation and freshness contracts, without assessment-model integration.

Application layer. Coordinate immutable domain sources and the explicit ports shown
below; GUI controls, SQL and filesystem policy belong to adapters. These operations run
synchronously on their owning session thread; no background or multi-user coordination
is introduced.
"""

from dataclasses import dataclass, field

from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.lifft_draft import InputIssue, LifftDraft
from ergotools.domain.assessments.lifft_validation import lifft_draft_issues


@dataclass(frozen=True, slots=True)
class LifftPreparation:
    """Immutable source snapshot/issues plus its originating session identity.

    The private session reference is retained only for identity checks; consumers should
    discard old preparations on close/switch. It is not a persisted ID or
    background-work synchronization mechanism. Construct via prepare_lifft.

    Attributes:
        document: Exact project/document owner of this command or captured preparation.
        revision: Captured session-local revision identity, not a persisted assessment
            version number.
        source: Exact immutable source object captured from the originating session.
        issues: Ordered structured input or calculation issues; absence is not silently
            converted to numeric zero.
        _session: Originating owner-thread session retained only for identity checks;
            release preparations on close.
    """

    document: DocumentKey
    revision: int
    source: LifftDraft
    issues: tuple[InputIssue, ...]
    _session: DocumentSession[LifftDraft] = field(repr=False, compare=False)

    @property
    def has_valid_inputs(self) -> bool:
        """Report input validity only, not scientific approval or arithmetic success.

        Args:
            None.

        Returns:
            True when the ordered input-issue tuple is empty; this is not scientific
            approval or arithmetic validation.
        """
        return not self.issues

    def is_current(self, active: DocumentSession[LifftDraft] | None) -> bool:
        """Check active session, revision and source identity before using a result.

        Edits invalidate this preparation; undo to this exact revision restores it. Save
        alone preserves freshness. Reload/switch/close invalidates it, even when another
        session has equal document, revision and source values. The caller must pass the
        actual active session, not a retained old one.

        Args:
            active: Actual currently active session, or None after closing; equal values
                in another session do not match.

        Returns:
            True only for the exact originating active session, captured revision and
            original source object.
        """
        return (
            active is self._session
            and active.revision == self.revision
            and active.state is self.source
        )


def prepare_lifft(session: DocumentSession[LifftDraft]) -> LifftPreparation:
    """Capture and validate the current source on the session's owner thread.

    Gather all issues without changing history, dirty state or persistence. Never
    substitute zero for missing inputs or calculate partial totals. Calculation belongs
    to the evaluator; this boundary stops after input validation.

    Args:
        session: Caller-owned assessment session inspected synchronously on its owner
            thread.

    Returns:
        Immutable source/revision/session-bound LiFFT preparation and all ordered input
        issues; no calculator runs.
    """
    source = session.state
    return LifftPreparation(
        session.document, session.revision, source, lifft_draft_issues(source), session
    )

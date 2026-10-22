"""Open coordination that treats recent-history failure as a separate outcome.

Application layer. Define immutable capability/operation contracts independently of Qt
and storage implementations. Callers own modal consent and borrowed project lifetime;
concrete adapters own I/O and transaction enforcement.
"""

from dataclasses import dataclass

from ergotools.application.document_lifecycle import CloseChoice, DocumentLifecycle
from ergotools.application.session import DocumentKey
from ergotools.application.settings import SettingsStore


@dataclass(frozen=True, slots=True)
class OpenOutcome:
    """Document success/cancellation plus a separate optional settings warning.

    Attributes:
        opened: True when the document is open; False for cancellation or absent
            dirty-state consent.
        warning_key: Optional stable recency-settings warning after successful open;
            never report it as document-open failure.
    """

    opened: bool
    warning_key: str | None = None


def open_document[State](
    lifecycle: DocumentLifecycle[State],
    document: DocumentKey,
    location: str,
    settings: SettingsStore,
    *,
    choice: CloseChoice | None = None,
) -> OpenOutcome:
    """Record recency only after open succeeds, without undoing a successful open.

    The caller supplies a normalized location associated with the repository. Load/save
    errors for the document propagate; settings I/O/format errors are reported as a
    stable warning key. Do not interpret this warning as open failure.

    Args:
        lifecycle: Caller-owned single-document lifecycle whose consent/load/save policy
            governs selection.
        document: Exact project/document version identity, independent of path or
            visible label.
        location: Caller-normalized project location; treat it as opaque recency data,
            not a path to resolve/open here.
        settings: Borrowed per-user preference store; its errors must not undo an
            otherwise successful document open.
        choice: Explicit Save/Discard/Cancel intent for leaving a dirty draft, or None
            for no supplied decision.

    Returns:
        OpenOutcome distinguishing document success/cancellation from an optional
        independent recent-history warning.

    Raises:
        ValueError: The supplied recent location is not nonblank text, or the lifecycle
            rejects its explicit close choice.
        RuntimeError: The delegated lifecycle rejects reentrancy or a source change
            during loading.
    """
    if not isinstance(location, str) or not location.strip():
        raise ValueError("A recent-document location is required.")
    if not lifecycle.open(document, choice=choice):
        return OpenOutcome(False)
    return OpenOutcome(True, remember_open_location(location, settings))


def remember_open_location(location: str, settings: SettingsStore) -> str | None:
    """Record a completed open; return a warning for settings I/O/format failure.

    Args:
        location: Caller-normalized project location; treat it as opaque recency data,
            not a path to resolve/open here.
        settings: Borrowed per-user preference store; its errors must not undo an
            otherwise successful document open.

    Returns:
        None after preference persistence, or settings.recent_update_failed for an
        OSError/ValueError; a successful document open stays successful.
    """
    try:
        updated = settings.load().remember(location)
        settings.save(updated)
    except (OSError, ValueError):
        return "settings.recent_update_failed"
    return None

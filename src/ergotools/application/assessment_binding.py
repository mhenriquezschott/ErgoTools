"""Explicit persisted ownership, independent of document edit history.

Application layer. Define immutable capability/operation contracts independently of Qt
and storage implementations. Callers own modal consent and borrowed project lifetime;
concrete adapters own I/O and transaction enforcement.
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.context import AssessmentContext


@dataclass(frozen=True, slots=True)
class AssessmentBinding:
    """One document's immutable ownership within the same project.

    Attributes:
        document: Exact project-scoped saved assessment identity.
        context: Exact project/worker/workplace/model ownership; project identity must
            agree with document.
    """

    document: DocumentKey
    context: AssessmentContext

    def __post_init__(self) -> None:
        """Reject cross-project associations before storage is addressed.

        Args:
            None.

        Returns:
            None after enforcing same-project ownership; no repository is read or
            changed.

        Raises:
            ValueError: Document and ownership context belong to different projects.
        """
        if self.document.project_id != self.context.worker.project_id:
            raise ValueError("Assessment binding cannot cross projects.")


@runtime_checkable
class AssessmentBindings(Protocol):
    """Optional repository capability; binding does not save an unsaved draft."""

    def bind_assessment(self, binding: AssessmentBinding) -> None:
        """Bind an existing saved model once; exact repeats are idempotent.

        Args:
            binding: Exact saved document/model/worker/workplace ownership; never saves
                an unsaved draft implicitly.

        Returns:
            None after atomically binding an existing saved source; exact repeated
            binding is idempotent, conflicting ownership fails.
        """
        ...

    def assessment_binding(self, document: DocumentKey) -> AssessmentBinding | None:
        """Read ownership of an existing document; None means unbound.

        Args:
            document: Exact project/document identity, independent of path or
                visible label.

        Returns:
            Saved ownership of the named document, or None when it is unbound; no
            selection changes.
        """
        ...

    def find_assessment(self, context: AssessmentContext) -> DocumentKey | None:
        """Find a saved document by exact ownership, without changing selection.

        Args:
            context: Exact project/worker/workplace/model ownership including shift; no
                workplace-only fallback.

        Returns:
            Exact saved document key for this owner/model, or None when absent; do not
            select or create a source.
        """
        ...

"""Immutable persisted-assessment catalog entries independent of widgets/storage.

Application layer. Define immutable capability/operation contracts independently of Qt
and storage implementations. Callers own modal consent and borrowed project lifetime;
concrete adapters own I/O and transaction enforcement.
"""

from dataclasses import dataclass

from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.document import AssessmentKind


@dataclass(frozen=True, slots=True)
class AssessmentEntry:
    """Persisted identity, model and source task count; no unsaved-preview claims.

    Attributes:
        document: Persisted project/document identity, excluding unsaved preview-only
            drafts.
        kind: Stable supported assessment model identity.
        task_count: Saved source row count, including unfinished slots; not the count of
            scientifically valid/calculated tasks.
    """

    document: DocumentKey
    kind: AssessmentKind
    task_count: int

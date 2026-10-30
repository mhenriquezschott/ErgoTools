"""Optional atomic saved-assessment transfer capability.

Application layer. Define immutable capability/operation contracts independently of Qt
and storage implementations. Callers own modal consent and borrowed project lifetime;
concrete adapters own I/O and transaction enforcement.
"""

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from ergotools.domain.assessment_history import AssessmentHistory
from ergotools.domain.assessment_transfer import TransferRequest
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_catalog import JobCatalog


@runtime_checkable
class TransferRepository(Protocol):
    """Copy/move assessments without changing project lifetime or Job risks."""

    def transfer_assessments(
        self,
        expected_jobs: JobCatalog,
        expected_history: AssessmentHistory,
        request: TransferRequest,
        document_ids: Mapping[AssessmentKind, str],
    ) -> AssessmentHistory:
        """Commit copies, approved replacements and optional source removal atomically.

        Args:
            expected_jobs: Previously read job/placement/assignment catalog; must still
                match saved data before writing.
            expected_history: Previously read assigned/standalone ownership
                history used to reject stale transfer intent.
            request: Exact assigned/standalone source, destination owner, tools and
                explicit copy/move mode and selected-target replacement consent.
            document_ids: Caller-allocated distinct new destination document ID for each
                selected model.

        Returns:
            Committed history after all selected copies and optional source removals
            succeed together. Unapproved conflicts or failures change nothing.
        """
        ...

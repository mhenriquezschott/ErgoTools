"""Optional project risk operations and workspace-issued view authority.

Application layer. Define immutable capability/operation contracts independently of Qt
and storage implementations. Callers own modal consent and borrowed project lifetime;
concrete adapters own I/O and transaction enforcement.
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from ergotools.domain.job_catalog import Job, JobCatalog
from ergotools.domain.job_risk import JobRiskCatalog, JobRiskValues


@dataclass(frozen=True, slots=True)
class JobRiskSnapshot:
    """Saved risk catalog whose exact identity scopes management callbacks.

    Attributes:
        risk: Immutable workspace-issued saved job-risk catalog; exact object identity
            scopes current-value operations.
    """

    risk: JobRiskCatalog


@runtime_checkable
class JobRiskRepository(Protocol):
    """Explicit current Job risk operations; no unrestricted catalog replacement."""

    @property
    def supports_job_risk(self) -> bool:
        """Report format support without I/O.

        Args:
            None.

        Returns:
            True when the native format supports current Job values; no I/O is
            required.
        """
        ...

    def load_job_risk(self) -> JobRiskCatalog:
        """Read validated saved risk data.

        Args:
            None.

        Returns:
            Validated saved current Job values and model-specific evidence, without
            recalculation or profile lifecycle.
        """
        ...

    def delete_job(
        self,
        expected_jobs: JobCatalog,
        expected_risk: JobRiskCatalog,
        job_id: str,
    ) -> tuple[JobCatalog, JobRiskCatalog]:
        """Delete job-owned records atomically or retain all data on failure.

        Args:
            expected_jobs: Previously read job/placement/assignment catalog; must still
                match saved data before writing.
            expected_risk: Previously read current Job risk catalog; must still match
                saved evidence before writing.
            job_id: Exact saved job identity; never infer membership from display names.

        Returns:
            Committed job/risk catalog pair after atomic job-owned removal and
            retained-assignment unclassification.
        """
        ...

    def save_job_details(
        self,
        expected_jobs: JobCatalog,
        expected_risk: JobRiskCatalog,
        job: Job,
        values: JobRiskValues | None,
    ) -> tuple[JobCatalog, JobRiskCatalog]:
        """Commit the Job Management form as one transaction.

        Args:
            expected_jobs: Previously read job/placement/assignment catalog; must still
                match saved data before writing.
            expected_risk: Previously read current Job risk catalog; must still match
                saved evidence before writing.
            job: Proposed job form fields for the same stable job identity.
            values: Replacement current values; None preserves the existing set.
                An empty set removes only risks, not the Job.

        Returns:
            Committed job/risk catalog pair for one validated form Save; neither catalog
            may partially commit.
        """
        ...

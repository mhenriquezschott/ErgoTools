"""Optional catalog access and immutable workspace-issued edit snapshots.

Application layer. Define immutable capability/operation contracts independently of Qt
and storage implementations. Callers own modal consent and borrowed project lifetime;
concrete adapters own I/O and transaction enforcement.
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from ergotools.domain.job_catalog import JobCatalog


@dataclass(frozen=True, slots=True)
class JobSnapshot:
    """Saved jobs presented by a workspace; object identity guards callbacks.

    Only the latest snapshot issued by that workspace is eligible for replacement. Equal
    copies, snapshots from other workspaces and previous project handles do not confer
    write authority. This is not a persistent assignment edit history.

    Attributes:
        jobs: Immutable workspace-issued saved job/placement/assignment catalog; equal
            copies carry no replacement authority.
    """

    jobs: JobCatalog


@runtime_checkable
class JobRepository(Protocol):
    """Optional project capability with atomic expected-source replacement."""

    def load_jobs(self) -> JobCatalog:
        """Return the complete validated saved snapshot without mutation.

        Args:
            None.

        Returns:
            Complete immutable saved job/placement/assignment catalog, including
            inactive history.
        """
        ...

    def replace_jobs(self, expected: JobCatalog, replacement: JobCatalog) -> None:
        """Commit only if saved data equals expected; retain old data on failure.

        Args:
            expected: Exact previously read saved catalog used as the atomic
                replacement/transition precondition.
            replacement: Proposed immutable replacement with the ownership and lifecycle
                constraints described above.

        Returns:
            None after atomic expected-source replacement; preserve saved catalog and
            protected historical references on failure.
        """
        ...

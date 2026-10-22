"""Optional catalog access and immutable workspace-issued edit snapshots.

Application layer. Define immutable capability/operation contracts independently of Qt
and storage implementations. Callers own modal consent and borrowed project lifetime;
concrete adapters own I/O and transaction enforcement.
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from ergotools.domain.job_catalog import JobCatalog
from ergotools.domain.work_hierarchy import WorkHierarchy


@dataclass(frozen=True, slots=True)
class HierarchySnapshot:
    """Saved hierarchy presented by a workspace; object identity guards callbacks.

    Only the latest snapshot issued by that workspace is eligible for replacement. Equal
    copies, snapshots from other workspaces and previous project handles do not confer
    write authority. This is not a persistent catalog edit history.

    Attributes:
        hierarchy: Immutable saved hierarchy issued by this workspace; only the latest
            issued object carries replacement authority.
    """

    hierarchy: WorkHierarchy


@runtime_checkable
class HierarchyRepository(Protocol):
    """Optional project capability with atomic expected-source replacement."""

    def load_hierarchy(self) -> WorkHierarchy:
        """Return the complete validated saved snapshot without mutation.

        Args:
            None.

        Returns:
            Complete validated saved hierarchy, including empty parents and independent
            shifts.
        """
        ...

    def replace_hierarchy(
        self, expected: WorkHierarchy, replacement: WorkHierarchy
    ) -> None:
        """Commit only if saved data equals expected; retain old data on failure.

        Args:
            expected: Exact previously read saved catalog used as the atomic
                replacement/transition precondition.
            replacement: Proposed immutable replacement with the ownership and lifecycle
                constraints described above.

        Returns:
            None only after atomic expected-source replacement; retain prior saved data
            if validation or writing fails.
        """
        ...


@runtime_checkable
class WorkerRepository(Protocol):
    """Commit the worker form and its classification edits in one transaction."""

    def replace_worker_catalogs(
        self,
        expected_hierarchy: WorkHierarchy,
        replacement_hierarchy: WorkHierarchy,
        expected_jobs: JobCatalog,
        replacement_jobs: JobCatalog,
    ) -> None:
        """Keep both saved catalogs unchanged if either validation/write fails.

        Args:
            expected_hierarchy: Previously read complete worker/organization hierarchy
                to compare inside the write transaction.
            replacement_hierarchy: Validated proposed worker/organization snapshot
                committed together with assignment edits.
            expected_jobs: Previously read job/placement/assignment catalog; must still
                match saved data before writing.
            replacement_jobs: Validated proposed classification/assignment snapshot for
                the same project.

        Returns:
            None after committing both worker and assignment catalogs together; either
            failure leaves both prior catalogs intact.
        """
        ...

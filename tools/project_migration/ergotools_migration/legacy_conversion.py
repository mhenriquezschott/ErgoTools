"""Compose original-format readers into one explicitly published native project.

Optional external tools layer: read a consistent source snapshot, reconcile exact
ownership, normalize approved body units, recalculate outputs and embed images. This
module never runs in the application process. Native storage contains typed data, not an
old-schema database; original input files are retained untouched.

Developer tooling layer; no normal application module imports this file. External
conversion code remains separately removable. This file owns only the operations
described above; it never changes original project files.
"""

from pathlib import Path

from ergotools.application.saved_results import calculate_saved_result
from ergotools.application.session import DocumentKey
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.project_snapshot import (
    ProjectSnapshot,
    SnapshotAssessment,
)

from .legacy_assessments import (
    LegacyAssessment,
    LegacyShoulderSource,
    read_legacy_assessments,
)
from .legacy_catalogs import read_legacy_catalogs
from .legacy_plot import read_legacy_plot
from .legacy_project import (
    LegacyProject,
    read_legacy_descriptor,
)
from .legacy_reconciliation import (
    LegacyConflict,
    LegacyRecoveredAssessment,
    reconcile_legacy_assessments,
)
from .legacy_rotations import read_legacy_rotations
from .shoulder_source import convert_shoulder_source


class LegacyConversionReviewError(ValueError):
    """Concrete source conflicts block publication without silently repairing data."""

    def __init__(self, conflicts: tuple[LegacyConflict, ...]) -> None:
        """Retain concrete conflicts without publishing an incomplete destination.

        Args:
            conflicts: Original records whose ownership/source cannot be reconciled.

        Returns:
            None. The exception exposes immutable conflicts to the external caller.
        """
        self.conflicts = conflicts
        super().__init__(
            f"Legacy conversion needs review: {len(conflicts)} source conflicts."
        )


def convert_legacy_project(
    source: Path, destination: Path, project_id: str
) -> AssessmentProjectFile:
    """Convert a reviewed version-eight project without modifying original files.

    Assessment formulas, source units and version/current ownership are unchanged.
    Rounded/obsolete saved outputs are discarded; the existing calculator produces the
    sole new result per version. Failed inputs have no fabricated result. Worker body
    measurements normalize to cm/kg according to the declared project units (owner
    CR003); original input files remain untouched. All sources are read on one snapshot
    and closed before publication. Destination creation retains its documented
    failure/publication guarantees. The separate command-line utility owns invocation;
    desktop code never imports it.

    Args:
        source: Original XML descriptor; use an isolated copy for validation.
        destination: Separate new-format file, which must not already exist.
        project_id: Explicit stable destination identity, absent from the old XML.

    Returns:
        Owned native repository with typed data, embedded images and recalculated
        full-precision results.

    Raises:
        LegacyConversionReviewError: Conflicting old/history data needs review. No
            assessments are silently skipped.
        ValueError: Unsupported/malformed source data or cross-feature references.
        OSError: Source assets cannot be read or exclusive publication fails.
        FileExistsError: The separate destination already exists; never overwrite it.
    """
    if destination.exists():
        raise FileExistsError(destination)
    descriptor = read_legacy_descriptor(source, project_id)
    with LegacyProject(descriptor) as project:
        catalogs = read_legacy_catalogs(project)
        assessments = read_legacy_assessments(project, catalogs)
        recovery = reconcile_legacy_assessments(project, catalogs, assessments)
        records: tuple[LegacyAssessment | LegacyRecoveredAssessment, ...] = (
            *assessments,
            *recovery.recovered,
        )
        if recovery.conflicts:
            raise LegacyConversionReviewError(recovery.conflicts)
        converted = tuple(
            SnapshotAssessment(
                item.ownership,
                convert_shoulder_source(item.source)
                if isinstance(item.source, LegacyShoulderSource)
                else item.source,
            )
            for item in records
        )
        plot = read_legacy_plot(project, catalogs)
        rotations = read_legacy_rotations(project, catalogs)
        snapshot = ProjectSnapshot(
            descriptor.metadata,
            catalogs.hierarchy,
            catalogs.jobs,
            catalogs.risks,
            tuple(converted),
            tuple((image.plant, image.image) for image in plot.images),
            plot.positions,
            rotations.schemes,
            tuple(
                (item.ownership.document_id, result)
                for item in converted
                if (
                    result := calculate_saved_result(
                        DocumentKey(project_id, item.ownership.document_id),
                        item.source,
                        descriptor.metadata.default_units,
                    )
                )
                is not None
            ),
        )
    return AssessmentProjectFile.create_from_snapshot(destination, snapshot)

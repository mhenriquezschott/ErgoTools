"""Describe complete native project creation input at the storage boundary.

Infrastructure value contracts collect domain catalogs, source ownership, images, PLOT
positions, JROT schemes and source-bound outputs for atomic publication. They validate
relationships without SQL, file access, conversion or calculation. Each assessment
has at most one result bound to its exact input source. No original-format
database is carried.

Infrastructure layer. Keep these representations and concrete I/O outside the
domain/application core. Ownership, validation and transaction effects are documented at
each boundary below; no GUI or scientific formula is implemented here.
"""

from dataclasses import dataclass

from ergotools.application.historical_results import HistoricalAssessmentResult
from ergotools.domain.assessment_history import AssessmentHistory, AssignmentAssessment
from ergotools.domain.assessments.document import AssessmentDraft, assessment_kind
from ergotools.domain.job_catalog import JobCatalog
from ergotools.domain.job_risk import JobRiskCatalog
from ergotools.domain.plant_layout_image import PlantLayoutImage
from ergotools.domain.plot_positions import PlotPositions
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.rotation_scheme import RotationScheme
from ergotools.domain.work_hierarchy import WorkHierarchy


@dataclass(frozen=True, slots=True)
class SnapshotAssessment:
    """An original source paired with its exact historical owner and lifecycle.

    Attributes:
        ownership: Exact project-assignment/tool ownership, unique in the project.
        source: Immutable original task inputs and units; its model must match
            ownership.
    """

    ownership: AssignmentAssessment
    source: AssessmentDraft


@dataclass(frozen=True, slots=True)
class ProjectSnapshot:
    """Complete creation input retaining recorded units and assignment relationships.

    This storage-boundary contract is not an editing command. It neither infers missing
    assessments nor authorizes scientific reinterpretation of old inputs. Image
    coordinates remain pixels, worker dimensions remain cm/kg, and each assessment
    retains its own measurement system independently of defaults.

    Attributes:
        metadata: Typed project identity, defaults and saved description/date/language.
        hierarchy: Complete worker/organization hierarchy including empty parents.
        jobs: Job/placement/assignment catalog retaining closed historical owners.
        risks: Exact current Job risk sets and model-specific recorded evidence.
        assessments: Every source paired with its exact historical owner; no inferred
            missing sources.
        images: Exact owning-plant/image pairs; all encoded map bytes are embedded
            during native publication.
        positions: Unscaled original-image station and assignment-marker geometry.
        rotations: Saved schemes with frozen historical assignment/Job/placement
            links.
        saved_results: At most one source-bound calculation per document ID; no original
            archive or second result collection.
    """

    metadata: ProjectMetadata
    hierarchy: WorkHierarchy
    jobs: JobCatalog
    risks: JobRiskCatalog
    assessments: tuple[SnapshotAssessment, ...]
    images: tuple[tuple[str, PlantLayoutImage], ...]
    positions: PlotPositions
    rotations: tuple[RotationScheme, ...]
    # One source-bound calculation per assessment; no imported-result collection.
    saved_results: tuple[tuple[str, HistoricalAssessmentResult], ...] = ()

    def __post_init__(self) -> None:
        """Freeze caller collections and validate the complete creation contract.

        No persistence or scientific calculation occurs during construction.

        Args:
            None.

        Returns:
            None. The frozen instance owns immutable collection snapshots.

        Raises:
            ValueError: Cross-feature identities or source models disagree.

        KeyError: A cross-feature catalog lacks a referenced worker, assignment or
        Job.
        """
        object.__setattr__(self, "assessments", tuple(self.assessments))
        object.__setattr__(self, "images", tuple(tuple(item) for item in self.images))
        object.__setattr__(self, "rotations", tuple(self.rotations))
        object.__setattr__(
            self, "saved_results", tuple(tuple(item) for item in self.saved_results)
        )
        self.validate()

    def validate(self) -> None:
        """Validate exact cross-feature references without writing or calculating.

        Args:
            None.

        Returns:
            None when every reference is valid. Sources retain their declared units;
            saved results must describe the exact persisted assessment source.

        Raises:
            ValueError: Catalog identities, sources, images or frozen links disagree.
            KeyError: A catalog lacks a referenced worker, assignment or Job.
        """
        project_id = self.metadata.project_id
        if self.hierarchy.work.project_id != project_id:
            raise ValueError("Snapshot hierarchy belongs to another project.")
        self.jobs.validate_hierarchy(self.hierarchy)
        self.risks.validate_jobs(self.jobs)
        if self.risks.project_id != project_id:
            raise ValueError("Snapshot risk catalog belongs to another project.")
        history = AssessmentHistory(
            project_id, tuple(item.ownership for item in self.assessments)
        )
        history.validate_jobs(self.jobs)
        for item in self.assessments:
            if assessment_kind(item.source) != item.ownership.kind:
                raise ValueError("Snapshot source model does not match its owner.")
        plants = [plant for plant, _ in self.images]
        if len(set(plants)) != len(plants) or any(
            plant not in self.hierarchy.plants for plant in plants
        ):
            raise ValueError("Snapshot images have duplicate or missing plants.")
        self.positions.validate(self.hierarchy, self.jobs)
        identities = [scheme.scheme_id for scheme in self.rotations]
        if len(set(identities)) != len(identities):
            raise ValueError("Snapshot contains duplicate rotation schemes.")
        for scheme in self.rotations:
            scheme.validate_references(self.hierarchy, self.jobs, self.risks)

        owners = {
            item.ownership.document_id: item.ownership.kind for item in self.assessments
        }
        saved_ids = [identity for identity, _ in self.saved_results]
        if len(set(saved_ids)) != len(saved_ids):
            raise ValueError("Snapshot has duplicate saved result identities.")
        sources = {item.ownership.document_id: item.source for item in self.assessments}
        for identity, result in self.saved_results:
            if (
                identity not in owners
                or result.source != sources[identity]
                or result.calculation_status is None
            ):
                raise ValueError("Snapshot saved result has no matching owner/model.")

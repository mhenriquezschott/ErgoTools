"""Exact assessment ownership independent of widgets and database row locations.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from dataclasses import dataclass

from ergotools.domain.assessments.document import AssessmentKind


def _require_identity(*values: str) -> None:
    """Reject absent identifiers without changing their stored spelling.

    Args:
        values: Stored identifiers; each must be a nonblank string, retaining case and
            whitespace.

    Returns:
        None. Return normally only when the stated validation succeeds; invalid data
        raises instead.

    Raises:
        ValueError: Context identifiers must be nonblank strings.
    """
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError("Context identifiers must be nonblank strings.")


@dataclass(frozen=True, slots=True)
class WorkplaceContext:
    """Reference five-part workplace identity; shift is part of ownership.

    Identifiers are case-sensitive and retain whitespace. Display labels, combo indices
    and database surrogate IDs must be resolved before this boundary.

    Attributes:
        plant_name: Literal plant identity; case and nonblank whitespace are preserved.
        section_name: Literal section identity scoped by its owning plant.
        line_name: Literal line identity scoped by its plant and section.
        station_id: Literal station identity scoped by complete plant/section/line
            ancestry.
        shift_id: Literal project-wide shift identity; independent of station ancestry.
    """

    plant_name: str
    section_name: str
    line_name: str
    station_id: str
    shift_id: str

    def __post_init__(self) -> None:
        """Require all five identifiers without trimming or coercing them.

        Args:
            None. Dataclass construction supplies the fields documented on
            WorkplaceContext.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: The typed record or one of its referenced identities violates
                the invariants described above.
        """
        _require_identity(
            self.plant_name,
            self.section_name,
            self.line_name,
            self.station_id,
            self.shift_id,
        )


@dataclass(frozen=True, slots=True)
class WorkerContext:
    """A worker's exact workplace within one explicitly identified project.

    Attributes:
        project_id: Nonblank saved project identity, never derived from a file name.
        worker_id: Literal saved worker identity; names never establish ownership.
        workplace: Typed plant/section/line/station/shift ownership.
    """

    project_id: str
    worker_id: str
    workplace: WorkplaceContext

    def __post_init__(self) -> None:
        """Reject incomplete ownership before it can be used for matching.

        Args:
            None. Dataclass construction supplies the fields documented on
            WorkerContext.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: Worker context requires a typed workplace.
        """
        _require_identity(self.project_id, self.worker_id)
        if not isinstance(self.workplace, WorkplaceContext):
            raise ValueError("Worker context requires a typed workplace.")


@dataclass(frozen=True, slots=True)
class AssessmentContext:
    """Tool-specific ownership, separate from draft/session document identity.

    No job ID participates: job assignment is optional reference metadata and must not
    silently relocate an assessment when the assignment changes.

    Attributes:
        worker: Typed project/worker/workplace owner.
        kind: Stable assessment model identity; displayed tool names are localized
            separately.
    """

    worker: WorkerContext
    kind: AssessmentKind

    def __post_init__(self) -> None:
        """Require explicit worker ownership and a supported model identity.

        Args:
            None. Dataclass construction supplies the fields documented on
            AssessmentContext.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: Assessment context requires a typed worker context. Assessment
                context requires a supported model.
        """
        if not isinstance(self.worker, WorkerContext):
            raise ValueError("Assessment context requires a typed worker context.")
        if not isinstance(self.kind, AssessmentKind):
            raise ValueError("Assessment context requires a supported model.")

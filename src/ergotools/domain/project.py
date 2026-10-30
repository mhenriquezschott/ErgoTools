"""Immutable metadata for a new-format project, separate from user settings.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from dataclasses import dataclass, field
from datetime import datetime

from ergotools.domain.display_precision import DisplayPrecision
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem


@dataclass(frozen=True, slots=True)
class ProjectMetadata:
    """Stable identity/defaults plus optional original project details.

    Missing legacy details remain None. Creation time is local wall-clock time at second
    precision, matching the original date/time fields; its timezone is not inferred.
    Stored language is independent of the current user preference.

    Attributes:
        precision: Project-saved display decimals; never round source/result storage.
        assessment_context_expanded: Saved disclosure choice; None retains automatic
            defaults for older/new projects until the user explicitly chooses a state.
        project_id: Nonblank saved project identity, never derived from a file name.
        title: Nonblank saved project title, independent of its current file path.
        default_units: Explicit project display/input default; individual sources
            preserve their own original units.
        description: Optional saved description; None is distinct from an empty string.
        created_at: Optional local wall-clock datetime at whole-second precision with no
            inferred timezone.
        language: Optional saved language identity, independent of the current per-user
            UI preference.
    """

    project_id: str
    title: str
    default_units: MeasurementSystem
    description: str | None = None
    created_at: datetime | None = None
    language: Language | None = None
    precision: DisplayPrecision = field(default_factory=DisplayPrecision)
    assessment_context_expanded: bool | None = None

    def __post_init__(self) -> None:
        """Require explicit metadata without deriving identity from file paths.

        Args:
            None. Dataclass construction supplies the fields documented on
            ProjectMetadata.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: Project identity and title must be nonblank strings. Unsupported
                project unit default or display precision. Project description must
                be text or absent.
                Project creation time must be local, at second precision. Unsupported
                project language or non-boolean disclosure choice.
        """
        if self.assessment_context_expanded is not None and not isinstance(
            self.assessment_context_expanded, bool
        ):
            raise ValueError("Invalid assessment context disclosure setting.")
        if not isinstance(self.precision, DisplayPrecision):
            raise ValueError("Unsupported project display precision.")
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (self.project_id, self.title)
        ):
            raise ValueError("Project identity and title must be nonblank strings.")
        if not isinstance(self.default_units, MeasurementSystem):
            raise ValueError("Unsupported project unit default.")
        if self.description is not None and not isinstance(self.description, str):
            raise ValueError("Project description must be text or absent.")
        if self.created_at is not None and (
            not isinstance(self.created_at, datetime)
            or self.created_at.tzinfo is not None
            or self.created_at.microsecond != 0
        ):
            raise ValueError(
                "Project creation time must be local, at second precision."
            )
        if self.language is not None and not isinstance(self.language, Language):
            raise ValueError("Unsupported project language.")

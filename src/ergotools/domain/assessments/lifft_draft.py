"""LiFFT source drafts, with explicit missing values and original unit metadata.

No calculation, derived result, text parsing or unit switching occurs here.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

import math
from dataclasses import dataclass

from ergotools.domain.assessments.validation import DraftError as DraftError
from ergotools.domain.assessments.validation import InputIssue as InputIssue
from ergotools.domain.model_units import MeasurementSystem


@dataclass(frozen=True, slots=True)
class LifftTask:
    """One stable task identity and original inputs, including unfinished fields.

    Lever arm is inches or centimeters and load is lbf or N according to the owning
    draft. Repetitions are per work day. Finite signed/fractional values are retained
    for review; physical/model validity is a separate boundary.

    Attributes:
        task_id: Stable source-row identity used to associate edits, issues and
            calculated results.
        lever_arm: Original arm length in cm or inches according to the owning source
            system; None is unfinished.
        load: Original force in N or lbf according to the source system; never body
            mass. None is unfinished.
        repetitions: Repetitions per work day; None means unfinished input and
            fractional values remain supported.
    """

    task_id: str
    lever_arm: float | None = None
    load: float | None = None
    repetitions: float | None = None

    def __post_init__(self) -> None:
        """Reject blank identity and nonfinite values; preserve missing fields.

        Args:
            None. Dataclass construction supplies the fields documented on LifftTask.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            DraftError: Source structure, completeness, numeric validity or task
                identity violates the constraints described above; issue retains
                field/task context.
        """
        if not self.task_id.strip():
            raise DraftError(InputIssue("validation.required", "task_id"))
        for field in ("lever_arm", "load", "repetitions"):
            value = getattr(self, field)
            if value is not None and not math.isfinite(value):
                raise DraftError(
                    InputIssue("validation.nonfinite", field, self.task_id)
                )

    def missing_inputs(self) -> tuple[InputIssue, ...]:
        """Return missing fields in form order; zero is explicitly present.

        An empty tuple means structurally complete, not scientifically valid or approved
        for calculation. Range and integer policies need model review.

        Args:
            None.

        Returns:
            Missing arm/load/repetition issues in form order; zero and signed present
            values are not missing.
        """
        return tuple(
            InputIssue("validation.required", field, self.task_id)
            for field in ("lever_arm", "load", "repetitions")
            if getattr(self, field) is None
        )


@dataclass(frozen=True, slots=True)
class LifftDraft:
    """Ordered immutable task snapshots sharing an explicit original unit system.

    Attributes:
        system: Explicit original arm/force system: cm/N or inches/lbf; independent of
            interface language.
        tasks: Ordered immutable source tasks; absence remains None in individual
            fields.
    """

    system: MeasurementSystem
    tasks: tuple[LifftTask, ...] = ()

    def __post_init__(self) -> None:
        """Validate units, retain a tuple snapshot, and reject duplicate task IDs.

        Args:
            None. Dataclass construction supplies the fields documented on LifftDraft.

        Returns:
            None. Construction validates this record before publishing it. Snapshot
            tasks as immutable tuples on the new frozen instance.

        Raises:
            DraftError: Source structure, completeness, numeric validity or task
                identity violates the constraints described above; issue retains
                field/task context.
        """
        if not isinstance(self.system, MeasurementSystem):
            raise DraftError(InputIssue("validation.unit", "system"))
        object.__setattr__(self, "tasks", tuple(self.tasks))
        seen: set[str] = set()
        for task in self.tasks:
            if task.task_id in seen:
                raise DraftError(
                    InputIssue("validation.duplicate", "task_id", task.task_id)
                )
            seen.add(task.task_id)

    def task_index(self, task_id: str) -> int:
        """Find a stable task ID; reject references to an absent task.

        Args:
            task_id: Stable task identity used for lookup or field-specific validation
                diagnostics.

        Returns:
            Zero-based position of the exact task ID in the saved source order.

        Raises:
            DraftError: Source structure, completeness, numeric validity or task
                identity violates the constraints described above; issue retains
                field/task context.
        """
        for index, task in enumerate(self.tasks):
            if task.task_id == task_id:
                return index
        raise DraftError(InputIssue("validation.missing_task", "task_id", task_id))

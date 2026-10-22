"""Source-bound unit projections; display switching never rewrites assessment data.

Application layer. Coordinate immutable domain sources and the explicit ports shown
below; GUI controls, SQL and filesystem policy belong to adapters. These operations run
synchronously on their owning session thread; no background or multi-user coordination
is introduced.
"""

from dataclasses import dataclass

from ergotools.application.assessments.evaluation import (
    AssessmentPreparation,
    prepare_assessment,
)
from ergotools.application.session import DocumentSession
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.model_units import MeasurementSystem, project_model_input


@dataclass(frozen=True, slots=True)
class UnitViewTask:
    """Unrounded display inputs; force is N/lbf, arm is cm/in, repetitions unchanged.

    Direction retains its source code and recorded convention; no remapping occurs. No
    calculated moment, damage or probability is converted by this projection.

    Attributes:
        task_id: Stable source-row identity, independent of current grid position.
        lever_arm: Unrounded projected arm length in the view's cm/in display system, or
            None.
        load: Unrounded projected force in the view's N/lbf display system, or None;
            never body mass.
        repetitions: Unchanged source repetitions per day, or None when unfinished.
        direction: Source/model direction identity retained without unit conversion;
            absent for LiFFT or unfinished ST.
    """

    task_id: str
    lever_arm: float | None
    load: float | None
    repetitions: float | None
    direction: TstDirection | None


@dataclass(frozen=True, slots=True)
class AssessmentUnitView:
    """Immutable display snapshot retaining source units and freshness provenance.

    Release views on close. Units are a view choice, not a document edit or project
    default change. A later edit must explicitly translate its units at the input
    boundary; never save these rows as if they were original source values.

    Attributes:
        preparation: Exact source/session/revision provenance used to reject foreign or
            obsolete display/results.
        system: Explicit chosen arm/force display units; source quantities are never
            rewritten by preparing a view.
        tasks: Fresh blank source rows for a 1-100 row reset; default direction/OMNI
            selectors follow the original form.
    """

    preparation: AssessmentPreparation
    system: MeasurementSystem
    tasks: tuple[UnitViewTask, ...]

    def is_current(self, active: DocumentSession[AssessmentDraft] | None) -> bool:
        """Reject projections belonging to another session or edited revision.

        Args:
            active: Actual currently active session, or None after closing; equal values
                in another session do not match.

        Returns:
            True only for the exact originating active session, captured revision and
            original source object.
        """
        return self.preparation.is_current(active)


def prepare_unit_view(
    session: DocumentSession[AssessmentDraft], system: MeasurementSystem
) -> AssessmentUnitView:
    """Project LiFFT/TST input quantities without calculation, mutation or rounding.

    Always derive from the original source, never from an earlier projection. Missing
    and signed values remain editable. Invalid numeric values or overflow raise
    DraftError atomically; invalid target units or unitless DUET raise ValueError.
    Preparation issues remain available for incomplete source fields. Scientific
    evaluation gates continue to depend on source units, not view units.

    Args:
        session: Caller-owned assessment session inspected synchronously on its owner
            thread.
        system: Requested display system for arm/force: cm/N or inches/lbf; source units
            remain unchanged.

    Returns:
        Immutable unrounded display rows bound to the exact original source/revision;
        absent/signed source quantities remain unchanged.

    Raises:
        DraftError: Projection input is malformed/nonfinite or cannot be represented
            without overflow/underflow.
        ValueError: The requested system is unsupported or the source is
            unit-independent DUET.
    """
    if not isinstance(system, MeasurementSystem):
        raise ValueError("Unsupported display measurement system.")
    prepared = prepare_assessment(session)
    source = prepared.source
    if isinstance(source, DuetDraft):
        raise ValueError("DUET source has no dimensional inputs to convert.")
    tasks = tuple(
        UnitViewTask(
            task.task_id,
            project_model_input(
                task.lever_arm, "lever_arm", task.task_id, source.system, system
            ),
            project_model_input(task.load, "load", task.task_id, source.system, system),
            task.repetitions,
            task.direction if isinstance(task, TstTask) else None,
        )
        for task in source.tasks
    )
    return AssessmentUnitView(prepared, system, tasks)

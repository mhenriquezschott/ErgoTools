"""Immutable source-bound outputs for one saved assessment.

Application value contracts carry a detached calculation and its exact input snapshot.
Historical refers to a recorded worker assessment, not alternate versions or imported
outputs. Native projects have one replaceable result per document identity. SQL,
conversion and UI formatting belong to their respective adapters.

Application layer. Coordinate immutable domain sources and the explicit ports shown
below; GUI controls, SQL and filesystem policy belong to adapters. These operations run
synchronously on their owning session thread; no background or multi-user coordination
is introduced.
"""

from dataclasses import dataclass

from ergotools.application.assessments.evaluation import EvaluationStatus
from ergotools.domain.assessments.document import AssessmentDraft


@dataclass(frozen=True, slots=True)
class HistoricalTaskResult:
    """One calculator row: moment uses source result units; shares use percent.

    None means unavailable. Values retain the existing calculator's precision;
    additional presentation rounding is not applied by this value contract.

    Attributes:
        moment: Optional calculator display moment in the calculation's source result
            units; absent for DUET.
        damage: Optional dimensionless calculator damage, retaining intrinsic precision
            without save-time rounding.
        share_percent: Optional task percentage-of-total damage, retaining the
            calculator's one-decimal share policy.
    """

    moment: float | None
    damage: float | None
    share_percent: float | None


@dataclass(frozen=True, slots=True)
class HistoricalAssessmentResult:
    """One detached result bound to the assessment's exact current saved inputs.

    Damage is dimensionless; probability_percent is on the 0-100 scale before display
    clipping. Task moments retain calculator result units. Status/issues distinguish
    complete and partial outcomes. unit_label identifies calculation units, independent
    of current display preferences. Current saves require a successful calculation
    status; the codec rejects absent/obsolete status values. No second imported result
    is persisted.

    Attributes:
        source: Exact immutable source object captured from the originating session.
        damage: Optional dimensionless calculator damage, retaining intrinsic precision
            without save-time rounding.
        probability_percent: Optional outcome on the 0-100 scale before display
            clipping, without extra save-time rounding.
        tasks: Exact per-task output rows in source order, including unavailable values
            for blank rows; no input tasks are created by this result contract.
        unit_label: Original calculation unit label, independent of the current display
            preference.
        calculation_status: Complete/partial result status required by current
            persistence; None is rejected before writing.
        issue_keys: Ordered stable issue message keys retained with a partial
            calculation, localized only by presentation.
    """

    source: AssessmentDraft
    damage: float | None
    probability_percent: float | None
    tasks: tuple[HistoricalTaskResult, ...]
    # Persistence requires COMPLETE/PARTIAL; None is rejected before any write.
    unit_label: str | None = None
    calculation_status: EvaluationStatus | None = None
    issue_keys: tuple[str, ...] = ()

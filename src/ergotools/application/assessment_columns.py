"""Personal tool-column visibility independent of task data and calculations.

Application layer. Required numeric/choice inputs cannot be hidden; descriptive and
calculated columns may be hidden without removing their values or changing results.
"""

from dataclasses import dataclass

from ergotools.domain.assessments.document import AssessmentKind


def assessment_column_keys(kind: AssessmentKind) -> tuple[str, ...]:
    """Describe the shared grid's stable semantic order independently of UI captions.

    Args:
        kind: LiFFT, DUET or ST column schema.

    Returns:
        All display columns, including required inputs and optional outputs.
    """
    return (
        ("task_number", "task_name", "omni_res_scale", "repetitions", "damage", "share")
        if kind is AssessmentKind.DUET
        else (
            "task_number",
            "task_name",
            *(("direction",) if kind is AssessmentKind.TST else ()),
            "lever_arm",
            "load",
            "moment",
            "repetitions",
            "damage",
            "share",
        )
    )


def optional_assessment_columns(kind: AssessmentKind) -> tuple[str, ...]:
    """List only columns whose presentation may be customized.

    Args:
        kind: Exact shared tool.

    Returns:
        Semantic keys; required inputs are deliberately absent.
    """
    return tuple(
        key
        for key in assessment_column_keys(kind)
        if key in ("task_number", "task_name", "moment", "damage", "share")
    )


@dataclass(frozen=True, slots=True)
class AssessmentColumns:
    """One tool's hidden optional columns; omitted preferences show every column.

    Attributes:
        kind: Tool whose editable assessment grids use this preference.
        hidden: Unique optional semantic keys; never required numeric/choice fields.
    """

    kind: AssessmentKind
    hidden: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Reject foreign, repeated or required fields instead of hiding inputs.

        Args:
            None.

        Returns:
            None after immutable typed validation, without inspecting any assessment.

        Raises:
            ValueError: Tool, tuple or column choices are invalid.
        """
        if (
            not isinstance(self.kind, AssessmentKind)
            or not isinstance(self.hidden, tuple)
            or any(
                not isinstance(key, str)
                or key not in optional_assessment_columns(self.kind)
                for key in self.hidden
            )
            or len(set(self.hidden)) != len(self.hidden)
        ):
            raise ValueError("Only optional assessment columns may be hidden once.")

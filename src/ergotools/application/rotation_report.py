"""Read-only report snapshots over frozen guided JROT result evidence.

Application layer. Report creation reuses the domain comparison contract, never
loads current Job values, solves, accepts a preview or writes project data. The
presentation adapter owns language, pagination, preview and PDF file publication.
"""

from dataclasses import dataclass

from ergotools.domain.rotation_comparison import ToolComparison, compare_rotation_run
from ergotools.domain.rotation_scenario import RotationRun


@dataclass(frozen=True, slots=True)
class RotationReport:
    """One immutable report context shared by preview and file export.

    Attributes:
        project_title: Literal current project title, not a filesystem location.
        rotation_name: Literal selected rotation label; not a second run identity.
        run: Recorded inputs, timing, names, coefficients and arrangements.
        comparisons: Unrounded distributions from this exact run only.
        preview: True marks an optimization that has not been explicitly kept.
        current: False visibly identifies stale recorded evidence.
    """

    project_title: str
    rotation_name: str
    run: RotationRun
    comparisons: tuple[ToolComparison, ...]
    preview: bool
    current: bool


def build_rotation_report(
    project_title: str,
    rotation_name: str,
    run: RotationRun,
    *,
    preview: bool,
    current: bool,
) -> RotationReport:
    """Validate and freeze the displayed run without reading live measurements.

    Args:
        project_title: Owning project caption, retained literally.
        rotation_name: Current named plan caption, retained literally.
        run: Supported complete preview or retained evidence.
        preview: Whether this result has not been explicitly kept.
        current: Freshness already checked by the owning project presenter.

    Returns:
        Same-context report snapshot with no persistence or acceptance side effects.

    Raises:
        ValueError: A caption is blank or the run cannot be compared safely.
    """
    if not project_title.strip() or not rotation_name.strip():
        raise ValueError("Report requires project and rotation names.")
    return RotationReport(
        project_title,
        rotation_name,
        run,
        compare_rotation_run(run),
        preview,
        current,
    )


def relative_index_change(before: float, after: float) -> float | None:
    """Express an index change relative to a nonzero starting value.

    Args:
        before: Starting worker-index statistic in percentage points.
        after: Corresponding result statistic using the same frozen context.

    Returns:
        Signed relative percent, or None when the starting value is zero. This is
        distinct from after-minus-before in percentage points and from injury risk.
    """
    return (after - before) / before * 100 if before != 0 else None

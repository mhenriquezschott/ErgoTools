"""Owned project reads for saved PLOT datasets; never accept active editor input.

Infrastructure layer. Adapt validated application/domain values to explicit storage or
interchange formats. Use parameterized SQLite or caller-selected file paths; no Qt UI,
scientific formula changes or automatic old-project conversion. Connection ownership and
transaction boundaries are specified by each operation; I/O failures propagate unless
wrapped as a format error.
"""

from pathlib import Path

from ergotools.application.plot_results import (
    PlotResults,
    PlotWorkerOrder,
    saved_plot_results,
)
from ergotools.domain.plot_filters import PlotFilterSelection
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile


def load_plot_results(
    location: str,
    selection: PlotFilterSelection,
    *,
    current_year: int,
    order: PlotWorkerOrder = PlotWorkerOrder.WORKER_ID,
) -> PlotResults:
    """Read saved results through an owned connection; close on success or failure.

    Args:
        location: Existing native project path; a separate read/write handle is owned
            only for this read scope.
        selection: Validated scope/tool/mode/demographic selection.
        current_year: Positive calendar year for original age filtering.
        order: Original binary worker-ID or last-name order.

    Returns:
        Complete immutable saved PLOT dataset after validation, with the temporary
        repository closed.

    Raises:
        ValueError: Selection/year/order, native format or saved ownership/evidence is
            invalid.
        sqlite3.DatabaseError: Project open/read/close fails.
    """
    with AssessmentProjectFile.open(Path(location)) as project:
        return saved_plot_results(
            project, selection, current_year=current_year, order=order
        )

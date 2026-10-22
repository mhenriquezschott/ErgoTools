"""Borrowed PLOT capability over the workspace-owned project connection.

Application layer. Define immutable capability/operation contracts independently of Qt
and storage implementations. Callers own modal consent and borrowed project lifetime;
concrete adapters own I/O and transaction enforcement.
"""

from typing import Protocol, runtime_checkable

from ergotools.application.plot_layout import PlantLayoutReader, PlantLayoutWriter
from ergotools.application.plot_results import PlotResultRepository
from ergotools.domain.plot_positions import PlotPositions


@runtime_checkable
class PlotRepository(
    PlotResultRepository, PlantLayoutReader, PlantLayoutWriter, Protocol
):
    """Borrow saved PLOT data and explicit edits without owning project lifetime."""

    def save_plot_positions(self, positions: PlotPositions) -> None:
        """Commit explicit position intent atomically or raise.

        Args:
            positions: Complete typed original-image pixel geometry for this project and
                its historical assignment owners.

        Returns:
            None after atomic validated geometry persistence; pixel coordinates are
            never converted as metric/imperial measurements.
        """
        ...

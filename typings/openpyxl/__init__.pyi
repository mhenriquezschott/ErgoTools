"""Minimal reviewed openpyxl 3.1.5 read-only API used by cell import.

Typing boundary only, not a workbook implementation. Describes the exercised read-only
constructor, worksheet dimensions/iteration and deterministic closure. No formulas are
calculated and no writes are exposed through this declaration.
"""

from collections.abc import Iterator
from pathlib import Path

class Cell:
    """Read-only cell whose upstream value can be any scalar Excel cell type."""

    value: object

class Worksheet:
    """Selected worksheet dimensions and bounded value-cell iteration."""

    max_row: int | None
    max_column: int | None
    def iter_rows(
        self, *, min_row: int, max_row: int, min_col: int, max_col: int
    ) -> Iterator[tuple[Cell, ...]]:
        """Iterate an explicit rectangular cell range without evaluating formulas.

        Args:
            min_row: One-based first worksheet row.
            max_row: Inclusive last row.
            min_col: One-based first worksheet column.
            max_col: Inclusive last column.

        Returns:
            Iterator of row tuples within the requested rectangle.

        Yields:
            Row tuples of upstream read-only cells, including explicit empty cells.
        """
        ...

class Workbook:
    """Read-only workbook with exact worksheet names and owned source handle."""

    sheetnames: list[str]
    def __getitem__(self, name: str) -> Worksheet:
        """Select one exact worksheet without modifying it.

        Args:
            name: Literal workbook tab name.

        Returns:
            Read-only worksheet.

        Raises:
            KeyError: No worksheet has this exact name.
        """
        ...
    def close(self) -> None:
        """Release the read-only source archive and underlying handles.

        Args:
            None.

        Returns:
            None; worksheet access must finish before closure.
        """
        ...

def load_workbook(
    filename: Path, *, read_only: bool, data_only: bool, keep_links: bool
) -> Workbook:
    """Open the approved read-only workbook API without executing Excel formulas.

    Args:
        filename: Caller-selected local workbook path.
        read_only: True selects streamed source access.
        data_only: False exposes formula text for input rejection.
        keep_links: False avoids retaining external linked-workbook structures.

    Returns:
        Workbook whose close operation belongs to the caller.

    Raises:
        OSError: Source access fails.
        ValueError: Workbook content is unsupported or malformed.
    """
    ...

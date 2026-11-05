"""Reviewed openpyxl 3.1.5 A1 coordinate utility signatures; no runtime I/O."""

def get_column_letter(col_idx: int) -> str:
    """Format one column index in A1 notation.

    Args:
        col_idx: Positive one-based worksheet column.

    Returns:
        Alphabetic uppercase column label.

    Raises:
        ValueError: Index is outside upstream supported limits.
    """
    ...

def range_boundaries(
    range_string: str,
) -> tuple[int | None, int | None, int | None, int | None]:
    """Parse A1 rectangle bounds without reading worksheet contents.

    Args:
        range_string: Caller-supplied A1 rectangle/column/row notation.

    Returns:
        Left/top/right/bottom one-based bounds; unbounded axes are None.

    Raises:
        ValueError: Source is not valid A1 notation.
    """
    ...

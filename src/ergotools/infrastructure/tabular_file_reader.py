"""Read bounded CSV/TSV/XLSX/XLSM cell values without modifying source files.

Infrastructure adapter. Unicode/text decoding and the approved openpyxl dependency
stay outside the portable core. Workbooks are read-only, formulas are exposed as text
for normal input rejection, and all handles close before returning detached values.
"""

from pathlib import Path
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

from openpyxl import load_workbook
from openpyxl.utils.cell import get_column_letter, range_boundaries

from ergotools.application.assessment_import import (
    MAX_IMPORT_CHARACTERS,
    MAX_IMPORT_COLUMNS,
    MAX_IMPORT_ROWS,
    ImportProfile,
    ImportTable,
    parse_import_text,
)


def decode_import_text(data: bytes, encoding: str) -> str:
    """Decode common text encodings strictly, reporting uncertain legacy detection.

    Args:
        data: Bounded file bytes, never clipboard Unicode.
        encoding: Auto or a validated profile codec.

    Returns:
        Unicode text; auto accepts only UTF BOM or valid UTF-8.

    Raises:
        ValueError: Decoding needs an explicit legacy encoding or chosen codec fails.
    """
    if encoding == "auto":
        encoding = (
            "utf-16" if data.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
        )
    try:
        return data.decode(encoding)
    except UnicodeError as error:
        raise ValueError(
            "Choose the text encoding; the file is not valid in this encoding."
        ) from error


class SpreadsheetValueReader:
    """Read finite source values for an explicit worksheet/range."""

    def read(
        self,
        location: str,
        profile: ImportProfile,
        sheet: str = "",
        cell_range: str = "",
    ) -> ImportTable:
        """Read selected data, never execute formulas or save a workbook.

        Args:
            location: Native-selector CSV/TSV/XLSX/XLSM path.
            profile: Validated text decoding and delimiter choices.
            sheet: Exact workbook tab; empty selects the first.
            cell_range: A1 rectangle; empty previews at most 101 rows/20 columns.

        Returns:
            Detached strings, worksheet names and exact loaded range.

        Raises:
            OSError: File access fails.
            ValueError: Unsupported/oversized file, sheet/range, archive or encoding.
        """
        path = Path(location)
        if path.stat().st_size > 32_000_000:
            raise ValueError("Source files must be smaller than 32 MB.")
        if path.suffix.casefold() in (".csv", ".tsv", ".txt"):
            data = path.read_bytes()
            if len(data) > MAX_IMPORT_CHARACTERS * 4:
                raise ValueError("Text file exceeds the preview limit.")
            text = decode_import_text(data, profile.encoding)
            delimiter = (
                "\t"
                if path.suffix.casefold() == ".tsv" and profile.delimiter == "auto"
                else profile.delimiter
            )
            bounds = None
            if cell_range:
                left, top, right, bottom = range_boundaries(cell_range)
                if any(v is None for v in (left, top, right, bottom)):
                    raise ValueError("Use a rectangle such as B4:F25.")
                assert (
                    left is not None
                    and top is not None
                    and right is not None
                    and bottom is not None
                )
                bounds = (left, top, right, bottom)
            rows = parse_import_text(text, delimiter, bounds=bounds, preview=True)
            if not any(any(cell.strip() for cell in row) for row in rows):
                raise ValueError("The selected range contains no values.")
            selected = cell_range or f"A1:{get_column_letter(len(rows[0]))}{len(rows)}"
            return ImportTable(rows, cell_range=selected, notice="text_range")
        if path.suffix.casefold() not in (".xlsx", ".xlsm"):
            raise ValueError("Choose CSV, TSV, XLSX or XLSM cell data.")
        try:
            workbook = load_workbook(
                path, read_only=True, data_only=False, keep_links=False
            )
            try:
                sheets = tuple(workbook.sheetnames)
                first = next(
                    (name for name in sheets if hasattr(workbook[name], "iter_rows")),
                    None,
                )
                if first is None:
                    raise ValueError(
                        "The workbook is unreadable or has no usable worksheets."
                    )
                selected = sheet or first
                if selected not in sheets:
                    raise ValueError("The selected worksheet is unavailable.")
                page = workbook[selected]
                if not hasattr(page, "iter_rows"):
                    raise ValueError(
                        "Choose a data worksheet; this sheet has no tabular cells."
                    )
                last_column = get_column_letter(min(page.max_column or 1, 20))
                last_row = min(page.max_row or 1, 101)
                rectangle = cell_range or f"A1:{last_column}{last_row}"
                left, top, right, bottom = range_boundaries(rectangle)
                if any(v is None for v in (left, top, right, bottom)):
                    raise ValueError("Use a rectangle such as B4:F25.")
                assert (
                    left is not None
                    and top is not None
                    and right is not None
                    and bottom is not None
                )
                if (
                    min(left, top) < 1
                    or right < left
                    or bottom < top
                    or right - left + 1 > MAX_IMPORT_COLUMNS
                    or bottom - top + 1 > MAX_IMPORT_ROWS
                    or right > 16384
                    or bottom > 1048576
                ):
                    raise ValueError(
                        "Select at most 2000 rows and 100 columns inside the worksheet."
                    )
                rows = tuple(
                    tuple("" if c.value is None else str(c.value) for c in row)
                    for row in page.iter_rows(
                        min_row=top, max_row=bottom, min_col=left, max_col=right
                    )
                )
                if not any(any(cell.strip() for cell in row) for row in rows):
                    raise ValueError("The selected range contains no values.")
                return ImportTable(rows, sheets, selected, rectangle, "worksheet_range")
            finally:
                workbook.close()
        except (BadZipFile, KeyError, IndexError, ParseError) as error:
            raise ValueError(
                "The workbook is unreadable or has no usable worksheets."
            ) from error

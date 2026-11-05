"""Portable tabular import choices and atomic assessment input preparation.

Application layer. No files, Qt, workbook engine, calculators or project writes occur
here. Profiles contain interpretation/mapping preferences and header metadata, never
body cells or paths. All task validation and unit conversion delegate to the shared
clipboard service.
"""

import csv
import re
from dataclasses import dataclass
from io import StringIO
from typing import Protocol

from ergotools.application.assessment_clipboard import (
    assessment_input_fields,
    prepare_assessment_paste,
)
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    assessment_kind,
)
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.model_units import MeasurementSystem

# Finite preview bounds, separate from the existing 100 destination task limit.
MAX_IMPORT_ROWS = 2000
# Source columns may include unrelated columns which users explicitly ignore.
MAX_IMPORT_COLUMNS = 100
# Text file/clipboard bounds avoid allocating an unbounded preview.
MAX_IMPORT_CHARACTERS = 4_000_000
# Common Spanish/European Unicode and legacy text encodings; UTF-8 accepts a BOM.
IMPORT_ENCODINGS = ("auto", "utf-8-sig", "utf-16", "cp1252", "iso8859-1", "iso8859-15")


@dataclass(frozen=True, slots=True)
class ImportProfile:
    """One tool's personal import interpretation, independent of project data.

    Attributes:
        kind: Destination tool; identities/results are never eligible columns.
        delimiter: Auto or one explicit separator character.
        encoding: Auto or one approved text-file codec; irrelevant for clipboard/XLSX.
        decimal: Explicit numeric decimal mark, never guessed from interface language.
        thousands: Optional explicit grouping mark; must differ from decimal.
        units: Source measurement units, not destination/source-record metadata.
        header: First selected row contains headers.
        fields: Source-column destinations; None explicitly ignores a column.
        headers: Optional source labels used to detect incompatible quick-paste headers.
        configured: True only after the user explicitly saves this mapping.
    """

    kind: AssessmentKind
    delimiter: str = "auto"
    encoding: str = "auto"
    decimal: DecimalConvention = DecimalConvention.POINT
    thousands: str = ""
    units: MeasurementSystem = MeasurementSystem.METRIC
    header: bool = True
    fields: tuple[str | None, ...] = ()
    configured: bool = False
    headers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate typed finite preferences without reading or transforming inputs.

        Args:
            None.

        Returns:
            None after rejecting invalid separators, duplicate fields or foreign tools.

        Raises:
            ValueError: Profile types, mapping or parsing choices are invalid.
        """
        allowed = {
            AssessmentKind.LIFFT: {"task_name", "lever_arm", "load", "repetitions"},
            AssessmentKind.DUET: {"task_name", "omni_res_scale", "repetitions"},
            AssessmentKind.TST: {
                "task_name",
                "direction",
                "lever_arm",
                "load",
                "repetitions",
            },
        }
        if (
            not isinstance(self.kind, AssessmentKind)
            or not isinstance(self.decimal, DecimalConvention)
            or not isinstance(self.units, MeasurementSystem)
            or type(self.header) is not bool
            or type(self.configured) is not bool
            or self.encoding not in IMPORT_ENCODINGS
            or not isinstance(self.delimiter, str)
            or (
                self.delimiter != "auto"
                and (len(self.delimiter) != 1 or self.delimiter in '\r\n"')
            )
            or self.thousands not in ("", ".", ",", " ")
            or self.thousands == self.decimal.value
            or not isinstance(self.fields, tuple)
            or len(self.fields) > MAX_IMPORT_COLUMNS
            or not isinstance(self.headers, tuple)
            or any(not isinstance(h, str) for h in self.headers)
            or len(self.headers) not in (0, len(self.fields))
        ):
            raise ValueError("Invalid import profile choices.")
        mapped = [f for f in self.fields if f is not None]
        if any(
            not isinstance(f, str) or f not in allowed[self.kind] for f in mapped
        ) or len(set(mapped)) != len(mapped):
            raise ValueError("Map each allowed input column only once.")


@dataclass(frozen=True, slots=True)
class ImportTable:
    """Detached source values and truthful file-preview metadata.

    Attributes:
        rows: Rectangular string cells; blanks remain blanks, never fabricated zeros.
        sheets: All workbook sheet names, empty for delimited text.
        sheet: Selected sheet, or empty for text.
        cell_range: Exact loaded workbook coordinates, or empty for text.
        notice: Adapter-owned stable message key, not a scientific result.
    """

    rows: tuple[tuple[str, ...], ...]
    sheets: tuple[str, ...] = ()
    sheet: str = ""
    cell_range: str = ""
    notice: str = ""


class TabularFileReader(Protocol):
    """Borrowed value-only file adapter; never writes the source workbook."""

    def read(
        self,
        location: str,
        profile: ImportProfile,
        sheet: str = "",
        cell_range: str = "",
    ) -> ImportTable:
        """Load bounded values for an explicit source/worksheet/range.

        Args:
            location: Caller-selected CSV/TSV/XLSX path.
            profile: Text-file decoding and delimiter choices.
            sheet: Exact worksheet name, empty selects the first sheet.
            cell_range: Optional A1 rectangle, enabling bounded reads far into a sheet.

        Returns:
            Detached rectangular source values; no file handle escapes.

        Raises:
            OSError: File access fails.
            ValueError: Type, encoding, dimensions or selected rectangle is unsupported.
        """
        ...


def parse_import_text(
    text: str,
    delimiter: str = "auto",
    *,
    bounds: tuple[int, int, int, int] | None = None,
    preview: bool = False,
) -> tuple[tuple[str, ...], ...]:
    """Parse quoted delimited Unicode text while retaining blank cells.

    Args:
        text: Already decoded clipboard/file contents.
        delimiter: Auto, or one explicit separator including tab/comma/semicolon/pipe.
        bounds: Optional one-based left/top/right/bottom source rectangle.
        preview: True bounds initial file previews to the first permitted rows/columns.

    Returns:
        Rectangular padded source rows inside finite preview bounds.

    Raises:
        ValueError: Source is empty, too large, malformed or separator is invalid.
    """
    if not text.strip() or len(text) > MAX_IMPORT_CHARACTERS:
        raise ValueError("Empty or oversized source data.")
    if delimiter == "auto":
        try:
            delimiter = csv.Sniffer().sniff(text[:8192], delimiters="\t,;|").delimiter
        except csv.Error:
            delimiter = "\t"
    if len(delimiter) != 1 or delimiter in '\r\n"':
        raise ValueError("Choose one valid separator character.")
    if bounds is not None:
        left, top, right, bottom = bounds
        if not (
            1 <= left <= right
            and 1 <= top <= bottom
            and right - left + 1 <= MAX_IMPORT_COLUMNS
            and bottom - top + 1 <= MAX_IMPORT_ROWS
        ):
            raise ValueError("Select at most 2000 rows and 100 source columns.")
    else:
        left, top, right, bottom = (
            1,
            1,
            0,
            MAX_IMPORT_ROWS if preview else MAX_IMPORT_ROWS + 1,
        )
    rows = []
    try:
        for index, values in enumerate(
            csv.reader(StringIO(text), delimiter=delimiter, strict=True), 1
        ):
            if index > bottom:
                break
            if index < top:
                continue
            row = tuple(values)
            if bounds is not None:
                row = (row + ("",) * max(0, right - len(row)))[left - 1 : right]
            elif preview:
                row = row[:MAX_IMPORT_COLUMNS]
            rows.append(row)
    except csv.Error as error:
        raise ValueError(
            "Invalid source quoting; review separator and quotes."
        ) from error
    if bounds is not None and len(rows) != bottom - top + 1:
        raise ValueError("Range is outside the source data.")
    width = max((len(row) for row in rows), default=0)
    if not rows or len(rows) > MAX_IMPORT_ROWS or not 0 < width <= MAX_IMPORT_COLUMNS:
        raise ValueError("Preview supports up to 2000 rows and 100 source columns.")
    return tuple(row + ("",) * (width - len(row)) for row in rows)


def normalize_import_number(text: str, profile: ImportProfile) -> str:
    """Remove only explicitly selected, correctly grouped thousands separators.

    Args:
        text: Original numeric/choice token; no rounding or unit conversion occurs.
        profile: Explicit decimal/grouping choice.

    Returns:
        Token retaining its exact decimal digits, with valid grouping removed.

    Raises:
        ValueError: Grouping is malformed, rather than silently changing magnitude.
    """
    token = text.strip()
    mark = profile.thousands
    if not mark or mark not in token:
        return token
    group = re.escape(mark)
    decimal = re.escape(profile.decimal.value)
    if not re.fullmatch(rf"[+-]?\d{{1,3}}(?:{group}\d{{3}})+(?:{decimal}\d+)?", token):
        raise ValueError("Invalid thousands grouping; review number format.")
    return token.replace(mark, "")


def prepare_import(
    source: AssessmentDraft,
    rows: tuple[tuple[str, ...], ...],
    profile: ImportProfile,
    start_row: int = 0,
) -> AssessmentDraft:
    """Validate/prepare the mapped source as one existing atomic paste operation.

    Args:
        source: Exact canonical destination retained on every failure.
        rows: Selected rectangle including optional first header row.
        profile: Tool-specific explicit field, number and source-unit interpretation.
        start_row: Zero-based destination task position, never saved in preferences.

    Returns:
        Validated source replacement; no calculation/history/database operation occurs.

    Raises:
        ValueError: Mapping, units, grouping, dimensions or task input is invalid.
    """
    if (
        assessment_kind(source) is not profile.kind
        or not rows
        or len(rows[0]) != len(profile.fields)
    ):
        raise ValueError("Source columns do not match this tool's saved mapping.")
    if any(
        f not in assessment_input_fields(source)
        for f in profile.fields
        if f is not None
    ):
        raise ValueError("Unsupported destination input.")
    if profile.header:
        for caption, field in zip(rows[0], profile.fields, strict=True):
            if field in ("lever_arm", "load"):
                units = re.findall(r"\(([^)]+)\)", caption.casefold())
                if units:
                    token = units[-1].strip()
                    accepted = (
                        (
                            ("cm",)
                            if field == "lever_arm"
                            else ("n", "newton", "newtons")
                        )
                        if profile.units is MeasurementSystem.METRIC
                        else (
                            ("in", "inch", "inches")
                            if field == "lever_arm"
                            else ("lb", "lbs", "lbf")
                        )
                    )
                    if token not in accepted:
                        raise ValueError(
                            "Header units disagree: use cm/N or in/lbf; kg is mass."
                        )
            if field == "load" and "kg" in caption.casefold():
                raise ValueError("Load is force (N/lbf), not mass (kg).")
    values = rows[1:] if profile.header else rows
    values = tuple(
        tuple(
            normalize_import_number(cell, profile)
            if field in ("lever_arm", "load", "repetitions")
            else cell
            for cell, field in zip(row, profile.fields, strict=True)
        )
        for row in values
    )
    return prepare_assessment_paste(
        source,
        values,
        profile.fields,
        start_row=start_row,
        convention=profile.decimal,
        input_system=profile.units,
    )

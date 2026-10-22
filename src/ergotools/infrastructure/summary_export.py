"""Owned project reading and exclusive, complete UTF-8 CSV publication.

Infrastructure layer. Adapt validated application/domain values to explicit storage or
interchange formats. Use parameterized SQLite or caller-selected file paths; no Qt UI,
scientific formula changes or automatic old-project conversion. Connection ownership and
transaction boundaries are specified by each operation; I/O failures propagate unless
wrapped as a format error.
"""

import csv
import os
import tempfile
from pathlib import Path

from ergotools.application.assessment_export import SummaryExportRow, saved_summary_rows
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile


def load_summary_rows(
    location: str, kind: AssessmentKind
) -> tuple[SummaryExportRow, ...]:
    """Read saved data through a separately owned connection; close on any outcome.

    Args:
        location: Existing native project path opened through a separately owned scoped
            connection.
        kind: Scientific model whose saved current versions are read.

    Returns:
        Immutable saved current-version summary rows; temporary project handle closes on
        every outcome.

    Raises:
        ValueError: Native source/format/ownership validation fails.
        KeyError: Saved ownership references an absent assignment.
        sqlite3.DatabaseError: Project open/read/close fails.
    """
    with AssessmentProjectFile.open(Path(location)) as project:
        return saved_summary_rows(project, kind)


def write_summary_csv(location: str, table: tuple[tuple[str, ...], ...]) -> None:
    """Publish complete Excel-compatible CSV, never overwriting an existing file.

    UTF-8 BOM, standard comma quoting and CRLF preserve reference interchange. Temporary
    output is written/closed before exclusive same-directory hard-link publication.
    Failures retain an existing target and remove ordinary temporary files. Filesystem
    hard-link support is required; crash durability is uncertified.

    Args:
        location: Nonexistent CSV destination with an existing parent directory.
        table: Complete presentation-formatted Unicode cell table including the header;
            formulas are not evaluated here.

    Returns:
        None after exclusive publication of a complete BOM UTF-8 comma/CRLF file.

    Raises:
        FileExistsError: Destination exists before publication or another writer creates
            it.
        OSError: Temporary creation/write, hard-link publication or cleanup fails.
        UnicodeError: A supplied cell cannot be encoded as UTF-8.
        csv.Error: A supplied row cannot be serialized as CSV.
    """
    destination = Path(location)
    if destination.exists():
        raise FileExistsError(destination)
    descriptor, name = tempfile.mkstemp(
        prefix=".ergotools-export-", suffix=".csv", dir=destination.parent
    )
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", newline="", encoding="utf-8-sig") as output:
            csv.writer(output).writerows(table)
        os.link(temporary, destination)
    finally:
        temporary.unlink()

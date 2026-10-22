"""Complete UTF-8 PLOT CSV publication after the user's save-path selection.

Infrastructure layer. Keep these representations and concrete I/O outside the
domain/application core. Ownership, validation and transaction effects are documented at
each boundary below; no GUI or scientific formula is implemented here.
"""

import csv
import os
import tempfile
from pathlib import Path


def write_plot_csv(location: str, table: tuple[tuple[str, ...], ...]) -> None:
    """Publish a complete source-compatible CSV with atomic target replacement.

    The native chooser owns overwrite consent. Same-directory temporary encoding
    completes before replacement; errors retain any existing target and remove the
    temporary file. UTF-8, comma quoting and CRLF match the original PLOT exporter.

    Args:
        location: Caller-approved export destination; overwrite consent belongs to the
            native chooser.
        table: Complete preformatted rows, including any header; this adapter neither
            calculates nor localizes cells.

    Returns:
        None after complete UTF-8/CRLF CSV publication with atomic same-directory
        replacement; cleanup removes staging on failure.

    Raises:
        OSError: Staging, encoding/closing or atomic target replacement fails; no
            incomplete temporary content is published.
    """
    destination = Path(location)
    descriptor, name = tempfile.mkstemp(
        prefix=".ergotools-plot-", dir=destination.parent
    )
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", newline="", encoding="utf-8") as output:
            csv.writer(output).writerows(table)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)

"""Persist optional native project display settings without changing scientific data.

Infrastructure layer. Older native files have no settings table and use validated
defaults. Reads never create tables; writes join the caller's explicit transaction.
Snapshots carry this optional table with all other project contents.
"""

import sqlite3

from ergotools.domain.display_precision import DisplayPrecision
from ergotools.infrastructure.lifft_store import StoreFormatError


def read_precision(connection: sqlite3.Connection) -> DisplayPrecision:
    """Read one validated record, defaulting only when the optional table is absent.

    Args:
        connection: Borrowed native project connection on its owning thread.

    Returns:
        Immutable project decimals, with defaults for existing files without a table.

    Raises:
        StoreFormatError: The table has an invalid record count or invalid decimals.
        sqlite3.Error: The table cannot be queried.
    """
    if not connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' "
        "AND name='project_display_settings'"
    ).fetchone():
        return DisplayPrecision()
    rows = connection.execute(
        "SELECT inputs, moment, probability, damage, contribution "
        "FROM project_display_settings"
    ).fetchall()
    if len(rows) != 1:
        raise StoreFormatError("Project display settings require one record.")
    try:
        return DisplayPrecision(*rows[0])
    except ValueError as error:
        raise StoreFormatError("Invalid project display decimals.") from error


def write_precision(connection: sqlite3.Connection, value: DisplayPrecision) -> None:
    """Replace display preferences within the caller's transaction.

    Args:
        connection: Borrowed connection with a caller-owned write transaction.
        value: Validated immutable decimals; no assessment quantities are written.

    Returns:
        None; write one record without committing the caller's transaction.

    Raises:
        sqlite3.Error: Schema creation or parameterized writing fails.
    """
    connection.execute(
        "CREATE TABLE IF NOT EXISTS project_display_settings "
        "(inputs INTEGER NOT NULL, moment INTEGER NOT NULL, "
        "probability INTEGER NOT NULL, damage INTEGER NOT NULL, "
        "contribution INTEGER NOT NULL)"
    )
    connection.execute("DELETE FROM project_display_settings")
    connection.execute(
        "INSERT INTO project_display_settings VALUES (?, ?, ?, ?, ?)",
        (
            value.inputs,
            value.moment,
            value.probability,
            value.damage,
            value.contribution,
        ),
    )

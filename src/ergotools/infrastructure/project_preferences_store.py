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


def write_display_settings(
    connection: sqlite3.Connection,
    value: DisplayPrecision,
    context_expanded: bool | None = None,
) -> None:
    """Replace display preferences within the caller's transaction.

    Args:
        connection: Borrowed connection with a caller-owned write transaction.
        value: Validated immutable decimals; no assessment quantities are written.
        context_expanded: Explicit disclosure choice, or None for automatic defaults.

    Returns:
        None; write one record without committing the caller's transaction. Add the
        optional disclosure column only when an explicit choice first needs storage.

    Raises:
        ValueError: Disclosure intent is neither a bool nor None; no write occurs.
        sqlite3.Error: Schema creation or parameterized writing fails.
    """
    if context_expanded is not None and not isinstance(context_expanded, bool):
        raise ValueError("Invalid assessment context disclosure setting.")
    connection.execute(
        "CREATE TABLE IF NOT EXISTS project_display_settings "
        "(inputs INTEGER NOT NULL, moment INTEGER NOT NULL, "
        "probability INTEGER NOT NULL, damage INTEGER NOT NULL, "
        "contribution INTEGER NOT NULL)"
    )
    connection.execute("DELETE FROM project_display_settings")
    connection.execute(
        "INSERT INTO project_display_settings "
        "(inputs, moment, probability, damage, contribution) VALUES (?, ?, ?, ?, ?)",
        (
            value.inputs,
            value.moment,
            value.probability,
            value.damage,
            value.contribution,
        ),
    )
    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(project_display_settings)")
    }
    if context_expanded is not None and "context_expanded" not in columns:
        connection.execute(
            "ALTER TABLE project_display_settings ADD COLUMN context_expanded INTEGER "
            "CHECK(context_expanded IS NULL OR context_expanded IN (0, 1))"
        )
        columns.add("context_expanded")
    if "context_expanded" in columns:
        connection.execute(
            "UPDATE project_display_settings SET context_expanded = ?",
            (None if context_expanded is None else int(context_expanded),),
        )


def read_context_expanded(connection: sqlite3.Connection) -> bool | None:
    """Read optional disclosure intent without modifying older project schemas.

    Args:
        connection: Borrowed native project connection on its owning thread.

    Returns:
        Explicit bool, or None when the optional field is absent/unset.

    Raises:
        StoreFormatError: An existing disclosure record has invalid count/value.
        sqlite3.Error: Native schema/settings queries fail.
    """
    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(project_display_settings)")
    }
    if "context_expanded" not in columns:
        return None
    rows = connection.execute(
        "SELECT context_expanded FROM project_display_settings"
    ).fetchall()
    if len(rows) != 1 or (
        rows[0][0] is not None
        and (type(rows[0][0]) is not int or rows[0][0] not in (0, 1))
    ):
        raise StoreFormatError("Invalid project context disclosure setting.")
    return None if rows[0][0] is None else bool(rows[0][0])

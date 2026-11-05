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
    last_rotation = read_last_rotation(connection)
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
    if "last_rotation_id" in columns:
        connection.execute(
            "UPDATE project_display_settings SET last_rotation_id=?", (last_rotation,)
        )
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


def read_last_rotation(connection: sqlite3.Connection) -> str | None:
    """Read optional last-viewed rotation identity without repairing stale selection.

    Args:
        connection: Borrowed current project connection.

    Returns:
        Exact ID or None when absent/unset; membership is a caller selection policy.

    Raises:
        StoreFormatError: Existing view state has invalid row count/type.
        sqlite3.Error: Reading optional settings fails.
    """
    columns = {
        r[1] for r in connection.execute("PRAGMA table_info(project_display_settings)")
    }
    if "last_rotation_id" not in columns:
        return None
    rows = connection.execute(
        "SELECT last_rotation_id FROM project_display_settings"
    ).fetchall()
    if len(rows) != 1 or (
        rows[0][0] is not None
        and (not isinstance(rows[0][0], str) or not rows[0][0].strip())
    ):
        raise StoreFormatError("Invalid last-viewed rotation identity.")
    return rows[0][0]


def write_last_rotation(connection: sqlite3.Connection, identity: str | None) -> None:
    """Write independent view state inside the caller's existing project transaction.

    Args:
        connection: Borrowed owner-thread connection with an active transaction.
        identity: Explicit saved ID or None; caller validates current membership.

    Returns:
        None; decimals/context disclosure remain unchanged and no scenario is created.

    Raises:
        RuntimeError: Caller has no project transaction.
        ValueError: Identity is not nonblank text or None.
        sqlite3.Error: Optional settings creation/write fails; caller must roll back.
    """
    if not connection.in_transaction:
        raise RuntimeError("Rotation selection requires a project transaction.")
    if identity is not None and (not isinstance(identity, str) or not identity.strip()):
        raise ValueError("Invalid rotation selection identity.")
    columns = {
        r[1] for r in connection.execute("PRAGMA table_info(project_display_settings)")
    }
    if not columns:
        write_display_settings(connection, DisplayPrecision())
    if "last_rotation_id" not in columns:
        connection.execute(
            "ALTER TABLE project_display_settings ADD COLUMN last_rotation_id TEXT"
        )
    connection.execute(
        "UPDATE project_display_settings SET last_rotation_id=?", (identity,)
    )

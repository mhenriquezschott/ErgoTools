"""Read-only database inventory used before and after schema migrations."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from database import database_session


def resolve_project_database(input_path) -> tuple[Path | None, Path]:
    path = Path(input_path).expanduser().resolve()
    if path.suffix.lower() != ".ergprj":
        return None, path

    root = ET.parse(path).getroot()
    data_path = root.findtext("DataPath")
    database_name = root.findtext("DatabaseName")
    if not data_path or not database_name:
        raise ValueError(f"Project file does not identify its database: {path}")
    return path, (path.parent / data_path / database_name).resolve()


def _object_rows(connection, object_type: str) -> list[dict]:
    internal_filter = "AND name NOT LIKE 'sqlite_%'" if object_type != "index" else ""
    rows = connection.execute(
        f"""
        SELECT name, tbl_name, sql
        FROM sqlite_master
        WHERE type = ? {internal_filter}
        ORDER BY name
        """,
        (object_type,),
    ).fetchall()
    return [
        {"name": row[0], "table": row[1], "sql": row[2]}
        for row in rows
    ]


def inventory_database(input_path) -> dict:
    project_path, database_path = resolve_project_database(input_path)
    with database_session(database_path, read_only=True) as connection:
        tables = _object_rows(connection, "table")
        row_counts = {}
        for table in tables:
            escaped = table["name"].replace('"', '""')
            row_counts[table["name"]] = connection.execute(
                f'SELECT COUNT(*) FROM "{escaped}"'
            ).fetchone()[0]

        quick_check = [row[0] for row in connection.execute("PRAGMA quick_check")]
        foreign_key_violations = [
            {
                "table": row[0],
                "rowid": row[1],
                "parent": row[2],
                "foreign_key_index": row[3],
            }
            for row in connection.execute("PRAGMA foreign_key_check")
        ]
        schema_version = connection.execute("PRAGMA user_version").fetchone()[0]

    return {
        "project_path": str(project_path) if project_path else None,
        "database_path": str(database_path),
        "schema_version": schema_version,
        "tables": tables,
        "indexes": _inventory_objects(database_path, "index"),
        "triggers": _inventory_objects(database_path, "trigger"),
        "row_counts": row_counts,
        "quick_check": quick_check,
        "foreign_key_violations": foreign_key_violations,
    }


def _inventory_objects(database_path: Path, object_type: str) -> list[dict]:
    with database_session(database_path, read_only=True) as connection:
        return _object_rows(connection, object_type)


def inventory_json(input_path) -> str:
    return json.dumps(inventory_database(input_path), indent=2, sort_keys=True)

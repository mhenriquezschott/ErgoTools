"""Shared SQLite connection, validation, and backup utilities."""

from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional


class DatabaseSafetyError(RuntimeError):
    """Raised when a database cannot be modified without risking project data."""


@dataclass(frozen=True)
class DatabaseBackup:
    path: Path
    checksum: str
    source_checksum: str


def _database_path(database_path) -> Path:
    path = Path(database_path).expanduser().resolve()
    if not path.name:
        raise ValueError("A project database path is required.")
    return path


def file_sha256(path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def connect_database(
    database_path,
    *,
    read_only: bool = False,
    row_factory=None,
    timeout: float = 10.0,
) -> sqlite3.Connection:
    """Open an ErgoTools database with consistent safety settings."""
    path = _database_path(database_path)
    if read_only:
        connection = sqlite3.connect(
            f"file:{path.as_posix()}?mode=ro",
            uri=True,
            timeout=timeout,
        )
    else:
        connection = sqlite3.connect(str(path), timeout=timeout)

    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(f"PRAGMA busy_timeout = {int(timeout * 1000)}")
    if row_factory is not None:
        connection.row_factory = row_factory
    if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        connection.close()
        raise DatabaseSafetyError("SQLite foreign-key enforcement could not be enabled.")
    return connection


@contextmanager
def database_session(
    database_path,
    *,
    read_only: bool = False,
    row_factory=None,
    timeout: float = 10.0,
) -> Iterator[sqlite3.Connection]:
    """Yield a connection and commit or roll back writable work consistently."""
    connection = connect_database(
        database_path,
        read_only=read_only,
        row_factory=row_factory,
        timeout=timeout,
    )
    try:
        yield connection
        if not read_only:
            connection.commit()
    except Exception:
        if not read_only:
            connection.rollback()
        raise
    finally:
        connection.close()


def validate_database(database_path) -> None:
    """Run read-only integrity and foreign-key preflight checks."""
    path = _database_path(database_path)
    if not path.is_file():
        raise DatabaseSafetyError(f"Project database does not exist: {path}")
    with database_session(path, read_only=True) as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise DatabaseSafetyError(f"Database integrity check failed: {integrity}")
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise DatabaseSafetyError(
                f"Database has {len(violations)} foreign-key violation(s); migration stopped."
            )


def create_verified_backup(database_path, *, target_version: int) -> DatabaseBackup:
    """Create an exact, timestamped copy before migration and verify its checksum."""
    path = _database_path(database_path)
    validate_database(path)

    wal_path = Path(f"{path}-wal")
    if wal_path.exists() and wal_path.stat().st_size:
        raise DatabaseSafetyError(
            "The project database has an active SQLite WAL file. Close other project "
            "windows and retry the migration."
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_path = path.with_name(
        f"{path.name}.pre-schema-v{target_version}.{timestamp}.bak"
    )
    temporary_path = backup_path.with_suffix(f"{backup_path.suffix}.tmp")
    source_checksum = file_sha256(path)

    try:
        shutil.copy2(path, temporary_path)
        backup_checksum = file_sha256(temporary_path)
        if backup_checksum != source_checksum:
            raise DatabaseSafetyError("Database backup checksum verification failed.")
        os.replace(temporary_path, backup_path)
    except Exception:
        if temporary_path.exists():
            temporary_path.unlink()
        raise

    return DatabaseBackup(
        path=backup_path,
        checksum=backup_checksum,
        source_checksum=source_checksum,
    )


def restore_verified_backup(backup: DatabaseBackup, database_path) -> None:
    """Restore a verified backup atomically."""
    destination = _database_path(database_path)
    if file_sha256(backup.path) != backup.checksum:
        raise DatabaseSafetyError("Refusing to restore a backup with a changed checksum.")
    temporary_path = destination.with_suffix(f"{destination.suffix}.restore.tmp")
    shutil.copy2(backup.path, temporary_path)
    if file_sha256(temporary_path) != backup.checksum:
        temporary_path.unlink(missing_ok=True)
        raise DatabaseSafetyError("Restored database checksum verification failed.")
    os.replace(temporary_path, destination)


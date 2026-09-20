"""Schema migration support for normalized JROT rotation records."""

from __future__ import annotations

import sqlite3

from database import DatabaseSafetyError


def normalize_rotation_model_v8(connection: sqlite3.Connection) -> None:
    """Make rotation scope and risk provenance explicit and reproducible."""
    connection.execute("PRAGMA defer_foreign_keys = ON")

    missing_profiles = connection.execute(
        """
        SELECT COUNT(*)
        FROM RotationAssignment AS assignment
        WHERE NOT EXISTS (
            SELECT 1
            FROM JobRiskProfile AS profile
            WHERE profile.job_id = assignment.job_id
        )
        """
    ).fetchone()[0]
    if missing_profiles:
        raise DatabaseSafetyError(
            "Legacy rotations reference Jobs without a risk profile; migration stopped."
        )

    connection.execute("ALTER TABLE RotationScheme RENAME TO RotationScheme_legacy_v8")
    connection.execute("ALTER TABLE RotationAssignment RENAME TO RotationAssignment_legacy_v8")
    _create_rotation_tables(connection)

    connection.execute(
        """
        INSERT INTO RotationScheme (
            id, name, description, num_workers, num_timeblocks,
            optimization_mode, primary_tool_id
        )
        SELECT id, name,
               'Migrated as organization-wide because the legacy workplace fields did not '
               || 'identify assignment-backed rotation scope.',
               num_workers, num_timeblocks, 'manual', NULL
        FROM RotationScheme_legacy_v8
        """
    )
    connection.execute(
        """
        INSERT INTO RotationTarget (
            scheme_id, job_id, job_placement_id, job_risk_profile_id
        )
        SELECT legacy.scheme_id, legacy.job_id, NULL,
               COALESCE(
                   (
                       SELECT profile.id
                       FROM JobRiskProfile AS profile
                       WHERE profile.job_id = legacy.job_id
                         AND profile.status = 'approved'
                         AND profile.is_current = 1
                       ORDER BY profile.version DESC
                       LIMIT 1
                   ),
                   (
                       SELECT profile.id
                       FROM JobRiskProfile AS profile
                       WHERE profile.job_id = legacy.job_id
                       ORDER BY (profile.status = 'approved') DESC, profile.version DESC
                       LIMIT 1
                   )
               )
        FROM (
            SELECT DISTINCT scheme_id, job_id
            FROM RotationAssignment_legacy_v8
        ) AS legacy
        """
    )
    connection.execute(
        """
        INSERT INTO RotationAssignment (
            scheme_id, block_index, worker_id,
            worker_assignment_id, rotation_target_id
        )
        SELECT legacy.scheme_id, legacy.block_index, legacy.worker_id, NULL, target.id
        FROM RotationAssignment_legacy_v8 AS legacy
        JOIN RotationTarget AS target
          ON target.scheme_id = legacy.scheme_id
         AND target.job_id = legacy.job_id
         AND target.job_placement_id IS NULL
        """
    )
    connection.execute("DROP TABLE RotationAssignment_legacy_v8")
    connection.execute("DROP TABLE RotationScheme_legacy_v8")
    _create_rotation_integrity_triggers(connection)


def _create_rotation_tables(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE RotationScheme (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            num_workers INTEGER NOT NULL CHECK (num_workers > 0),
            num_timeblocks INTEGER NOT NULL CHECK (num_timeblocks > 0),
            optimization_mode TEXT NOT NULL DEFAULT 'manual' CHECK (
                optimization_mode IN ('manual', 'single_tool', 'all_tools')
            ),
            primary_tool_id TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (primary_tool_id) REFERENCES ErgoTool (id) ON DELETE SET NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE RotationSchemeScope (
            scheme_id TEXT NOT NULL,
            workplace_context_id INTEGER NOT NULL,
            PRIMARY KEY (scheme_id, workplace_context_id),
            FOREIGN KEY (scheme_id) REFERENCES RotationScheme (id) ON DELETE CASCADE,
            FOREIGN KEY (workplace_context_id) REFERENCES WorkplaceContext (id)
                ON DELETE RESTRICT
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE RotationTarget (
            id INTEGER PRIMARY KEY,
            scheme_id TEXT NOT NULL,
            job_id TEXT NOT NULL,
            job_placement_id INTEGER,
            job_risk_profile_id INTEGER NOT NULL,
            FOREIGN KEY (scheme_id) REFERENCES RotationScheme (id) ON DELETE CASCADE,
            FOREIGN KEY (job_id) REFERENCES Job (id) ON DELETE RESTRICT,
            FOREIGN KEY (job_placement_id) REFERENCES JobPlacement (id) ON DELETE RESTRICT,
            FOREIGN KEY (job_risk_profile_id) REFERENCES JobRiskProfile (id)
                ON DELETE RESTRICT
        )
        """
    )
    connection.execute(
        """
        CREATE UNIQUE INDEX uq_rotation_target_identity
        ON RotationTarget (scheme_id, job_id, COALESCE(job_placement_id, -1))
        """
    )
    connection.execute(
        """
        CREATE TABLE RotationAssignment (
            scheme_id TEXT NOT NULL,
            block_index INTEGER NOT NULL CHECK (block_index >= 0),
            worker_id TEXT NOT NULL,
            worker_assignment_id INTEGER,
            rotation_target_id INTEGER NOT NULL,
            PRIMARY KEY (scheme_id, block_index, worker_id),
            FOREIGN KEY (scheme_id) REFERENCES RotationScheme (id) ON DELETE CASCADE,
            FOREIGN KEY (worker_id) REFERENCES Worker (id) ON DELETE RESTRICT,
            FOREIGN KEY (worker_assignment_id) REFERENCES WorkerAssignment (id)
                ON DELETE RESTRICT,
            FOREIGN KEY (rotation_target_id) REFERENCES RotationTarget (id)
                ON DELETE RESTRICT
        )
        """
    )
    connection.execute(
        "CREATE INDEX ix_rotation_assignment_target "
        "ON RotationAssignment (rotation_target_id)"
    )


def _create_rotation_integrity_triggers(connection: sqlite3.Connection) -> None:
    for operation in ("INSERT", "UPDATE"):
        suffix = operation.lower()
        connection.execute(
            f"""
            CREATE TRIGGER trg_rotation_target_integrity_{suffix}
            BEFORE {operation} ON RotationTarget
            WHEN NOT EXISTS (
                    SELECT 1 FROM JobRiskProfile AS profile
                    WHERE profile.id = NEW.job_risk_profile_id
                      AND profile.job_id = NEW.job_id
                 )
              OR (
                    NEW.job_placement_id IS NOT NULL
                    AND NOT EXISTS (
                        SELECT 1 FROM JobPlacement AS placement
                        WHERE placement.id = NEW.job_placement_id
                          AND placement.job_id = NEW.job_id
                    )
                 )
              OR (
                    EXISTS (
                        SELECT 1 FROM RotationSchemeScope AS scope
                        WHERE scope.scheme_id = NEW.scheme_id
                    )
                    AND (
                        NEW.job_placement_id IS NULL
                        OR NOT EXISTS (
                            SELECT 1
                            FROM JobPlacement AS placement
                            JOIN RotationSchemeScope AS scope
                              ON scope.workplace_context_id = placement.workplace_context_id
                             AND scope.scheme_id = NEW.scheme_id
                            WHERE placement.id = NEW.job_placement_id
                        )
                    )
                 )
            BEGIN
                SELECT RAISE(ABORT, 'invalid Rotation Target provenance or scope');
            END
            """
        )
        connection.execute(
            f"""
            CREATE TRIGGER trg_rotation_assignment_integrity_{suffix}
            BEFORE {operation} ON RotationAssignment
            WHEN NOT EXISTS (
                    SELECT 1 FROM RotationTarget AS target
                    WHERE target.id = NEW.rotation_target_id
                      AND target.scheme_id = NEW.scheme_id
                 )
              OR (
                    NEW.worker_assignment_id IS NOT NULL
                    AND NOT EXISTS (
                        SELECT 1 FROM WorkerAssignment AS assignment
                        WHERE assignment.id = NEW.worker_assignment_id
                          AND assignment.worker_id = NEW.worker_id
                    )
                 )
              OR (
                    EXISTS (
                        SELECT 1 FROM RotationSchemeScope AS scope
                        WHERE scope.scheme_id = NEW.scheme_id
                    )
                    AND (
                        NEW.worker_assignment_id IS NULL
                        OR NOT EXISTS (
                            SELECT 1
                            FROM WorkerAssignment AS assignment
                            JOIN RotationSchemeScope AS scope
                              ON scope.workplace_context_id = assignment.workplace_context_id
                             AND scope.scheme_id = NEW.scheme_id
                            WHERE assignment.id = NEW.worker_assignment_id
                        )
                    )
                 )
            BEGIN
                SELECT RAISE(ABORT, 'invalid Rotation Assignment provenance or scope');
            END
            """
        )

    connection.execute(
        """
        CREATE TRIGGER trg_rotation_scope_requires_rebuild
        BEFORE INSERT ON RotationSchemeScope
        WHEN NOT EXISTS (
                SELECT 1 FROM RotationSchemeScope
                WHERE scheme_id = NEW.scheme_id
             )
         AND EXISTS (
                SELECT 1 FROM RotationTarget
                WHERE scheme_id = NEW.scheme_id
             )
        BEGIN
            SELECT RAISE(ABORT, 'clear Rotation Targets before changing scope mode');
        END
        """
    )
    connection.execute(
        """
        CREATE TRIGGER trg_rotation_scope_delete_requires_rebuild
        BEFORE DELETE ON RotationSchemeScope
        WHEN EXISTS (
            SELECT 1 FROM RotationTarget
            WHERE scheme_id = OLD.scheme_id
        )
        BEGIN
            SELECT RAISE(ABORT, 'clear Rotation Targets before changing scope');
        END
        """
    )

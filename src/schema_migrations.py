"""Ordered, transactional schema migrations for ErgoTools projects."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional, Sequence

from database import (
    DatabaseBackup,
    DatabaseSafetyError,
    connect_database,
    create_verified_backup,
)
from rotation_schema import normalize_rotation_model_v8


MigrationAction = Callable[[sqlite3.Connection], None]


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    definition: str
    apply: MigrationAction
    requires_foreign_keys_off: bool = False

    @property
    def checksum(self) -> str:
        content = f"{self.version}\n{self.name}\n{self.definition}".encode("utf-8")
        return hashlib.sha256(content).hexdigest()


@dataclass(frozen=True)
class MigrationResult:
    initial_version: int
    final_version: int
    applied_versions: tuple[int, ...]
    backup: Optional[DatabaseBackup]


SCHEMA_MIGRATION_COLUMNS = {
    "version",
    "name",
    "checksum",
    "applied_at",
    "application_version",
}

JROT_REQUIRED_COLUMNS = {
    "Job": {"id", "name", "description"},
    "JobMeasurement": {
        "job_id",
        "tool_id",
        "total_cumulative_damage",
        "probability_outcome",
        "color",
    },
    "RotationScheme": {
        "id",
        "name",
        "num_workers",
        "num_timeblocks",
    },
    "RotationSchemeScope": {"scheme_id", "workplace_context_id"},
    "RotationTarget": {
        "id",
        "scheme_id",
        "job_id",
        "job_placement_id",
        "job_risk_profile_id",
    },
    # These columns exist in both the legacy and normalized forms. Version 8
    # tests its additional provenance columns after the migration is applied.
    "RotationAssignment": {"scheme_id", "block_index", "worker_id"},
    "JobRiskProfile": {
        "id",
        "job_id",
        "name",
        "version",
        "status",
        "is_current",
        "source_type",
        "source_reference",
        "methodology",
        "sample_size",
        "assessed_on",
        "notes",
        "created_at",
        "updated_at",
    },
    "JobRiskMeasurement": {
        "profile_id",
        "tool_id",
        "total_cumulative_damage",
        "probability_outcome",
        "unit",
        "notes",
    },
    "WorkplaceContext": {
        "id",
        "plant_name",
        "section_name",
        "line_name",
        "station_id",
        "shift_id",
    },
    "JobPlacement": {
        "id",
        "job_id",
        "workplace_context_id",
        "active",
        "notes",
    },
    "WorkerAssignment": {
        "id",
        "worker_id",
        "workplace_context_id",
        "job_placement_id",
        "started_at",
        "ended_at",
        "active",
        "notes",
    },
    "IndividualAssessment": {
        "id",
        "worker_assignment_id",
        "tool_id",
        "version",
        "status",
        "is_current",
        "assessed_at",
        "unit",
        "total_cumulative_damage",
        "probability_outcome",
        "notes",
    },
    "LiFFTAssessmentTask": {
        "individual_assessment_id",
        "task_index",
        "lever_arm",
        "load",
        "moment",
        "repetitions",
        "cumulative_damage",
        "percentage_total",
    },
    "DUETAssessmentTask": {
        "individual_assessment_id",
        "task_index",
        "omni_res_scale",
        "repetitions",
        "cumulative_damage",
        "percentage_total",
    },
    "ShoulderAssessmentTask": {
        "individual_assessment_id",
        "task_index",
        "type_of_task",
        "lever_arm",
        "load",
        "moment",
        "repetitions",
        "cumulative_damage",
        "percentage_total",
    },
    "PlotAssessmentMarker": {
        "individual_assessment_id",
        "x",
        "y",
        "width",
        "height",
        "line_thickness",
        "scale_x",
        "scale_y",
        "crop_x",
        "crop_y",
        "crop_width",
        "crop_height",
        "zoom",
        "rotation",
        "mirror_h",
        "mirror_v",
        "orientation",
        "r",
        "g",
        "b",
        "brightness",
        "contrast",
        "saturation",
        "lock",
        "visible",
        "transparency",
        "enable",
    },
    "PlotStationPosition": {
        "plant_name",
        "section_name",
        "line_name",
        "station_id",
        "x",
        "y",
        "position_source",
        "updated_at",
    },
    "PlotWorkerAssignmentMarker": {
        "worker_assignment_id",
        "x",
        "y",
        "size",
        "scale",
        "line_thickness",
        "locked",
        "visible",
        "enabled",
        "position_source",
        "updated_at",
    },
}


def _create_jrot_schema_v1(connection: sqlite3.Connection) -> None:
    statements = (
        """
        CREATE TABLE IF NOT EXISTS SchemaMigration (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            checksum TEXT NOT NULL,
            applied_at TEXT NOT NULL,
            application_version TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS Job (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS JobMeasurement (
            job_id TEXT NOT NULL,
            tool_id TEXT NOT NULL,
            total_cumulative_damage REAL,
            probability_outcome REAL,
            color TEXT,
            PRIMARY KEY (job_id, tool_id),
            FOREIGN KEY (job_id) REFERENCES Job (id) ON DELETE CASCADE,
            FOREIGN KEY (tool_id) REFERENCES ErgoTool (id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS RotationScheme (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            plant_name TEXT NOT NULL,
            shift_id TEXT NOT NULL,
            num_workers INTEGER NOT NULL,
            num_timeblocks INTEGER NOT NULL,
            num_jobs INTEGER NOT NULL,
            FOREIGN KEY (plant_name) REFERENCES Plant (name) ON DELETE CASCADE,
            FOREIGN KEY (shift_id) REFERENCES Shift (id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS RotationAssignment (
            scheme_id TEXT NOT NULL,
            block_index INTEGER NOT NULL,
            worker_id TEXT NOT NULL,
            job_id TEXT NOT NULL,
            PRIMARY KEY (scheme_id, block_index, worker_id),
            FOREIGN KEY (scheme_id) REFERENCES RotationScheme (id) ON DELETE CASCADE,
            FOREIGN KEY (worker_id) REFERENCES Worker (id) ON DELETE CASCADE,
            FOREIGN KEY (job_id) REFERENCES Job (id) ON DELETE CASCADE
        )
        """,
    )
    for statement in statements:
        connection.execute(statement)


PLANT_COLUMNS_V2 = (
    "name",
    "description",
    "location",
    "type",
    "area",
    "number_of_shifts",
    "start_time",
    "end_time",
    "operational_hours",
    "production_capacity",
    "opening_date",
    "years_of_operation",
    "image_name",
    "image_path",
    "x",
    "y",
    "width",
    "height",
    "scale_x",
    "scale_y",
    "crop_x",
    "crop_y",
    "crop_width",
    "crop_height",
    "zoom",
    "rotation",
    "mirror_h",
    "mirror_v",
    "orientation",
    "color",
    "brightness",
    "contrast",
    "saturation",
    "lock",
    "visible",
    "transparency",
    "enable",
)


def _repair_plant_schema_v2(connection: sqlite3.Connection) -> None:
    info = connection.execute("PRAGMA table_info(Plant)").fetchall()
    columns = {row[1].lower(): row for row in info}
    mirror_column = columns.get("mirror_v")
    is_malformed_legacy_table = (
        mirror_column is not None
        and "orientation" not in columns
        and "orientation text" in (mirror_column[2] or "").lower()
    )
    if not is_malformed_legacy_table:
        return

    connection.execute("PRAGMA defer_foreign_keys = ON")
    connection.execute(
        """
        CREATE TABLE Plant_schema_v2 (
            name TEXT PRIMARY KEY,
            description TEXT,
            location TEXT,
            type TEXT,
            area REAL,
            number_of_shifts INTEGER,
            start_time TEXT,
            end_time TEXT,
            operational_hours REAL,
            production_capacity REAL,
            opening_date TEXT,
            years_of_operation INTEGER,
            image_name TEXT,
            image_path TEXT,
            x REAL,
            y REAL,
            width REAL,
            height REAL,
            scale_x REAL,
            scale_y REAL,
            crop_x REAL,
            crop_y REAL,
            crop_width REAL,
            crop_height REAL,
            zoom REAL,
            rotation REAL,
            mirror_h INTEGER,
            mirror_v INTEGER,
            orientation TEXT,
            color TEXT,
            brightness REAL,
            contrast REAL,
            saturation REAL,
            lock INTEGER,
            visible INTEGER,
            transparency REAL,
            enable INTEGER
        )
        """
    )
    legacy_columns = [column for column in PLANT_COLUMNS_V2 if column != "orientation"]
    quoted_legacy = ", ".join(f'"{column}"' for column in legacy_columns)
    connection.execute(
        f"INSERT INTO Plant_schema_v2 ({quoted_legacy}) SELECT {quoted_legacy} FROM Plant"
    )
    connection.execute("DROP TABLE Plant")
    connection.execute("ALTER TABLE Plant_schema_v2 RENAME TO Plant")


def _create_job_risk_profiles_v3(connection: sqlite3.Connection) -> None:
    job_columns = _table_columns(connection, "Job")
    if not {"active", "created_at", "updated_at"}.issubset(job_columns):
        connection.execute("PRAGMA defer_foreign_keys = ON")
        connection.execute(
            """
            CREATE TABLE Job_schema_v3 (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            INSERT INTO Job_schema_v3 (id, name, description)
            SELECT id, name, description FROM Job
            """
        )
        connection.execute("DROP TABLE Job")
        connection.execute("ALTER TABLE Job_schema_v3 RENAME TO Job")

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS JobRiskProfile (
            id INTEGER PRIMARY KEY,
            job_id TEXT NOT NULL,
            name TEXT NOT NULL,
            version INTEGER NOT NULL CHECK (version > 0),
            status TEXT NOT NULL CHECK (status IN ('draft', 'approved', 'retired')),
            is_current INTEGER NOT NULL DEFAULT 0 CHECK (is_current IN (0, 1)),
            source_type TEXT NOT NULL CHECK (
                source_type IN ('expert', 'external', 'study', 'aggregate', 'imported')
            ),
            source_reference TEXT,
            methodology TEXT,
            sample_size INTEGER CHECK (sample_size IS NULL OR sample_size >= 0),
            assessed_on TEXT,
            valid_from TEXT,
            valid_to TEXT,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (job_id, version),
            CHECK (valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to),
            FOREIGN KEY (job_id) REFERENCES Job (id) ON DELETE CASCADE
        )
        """
    )
    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_job_risk_profile_current_approved
        ON JobRiskProfile (job_id)
        WHERE is_current = 1 AND status = 'approved'
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_job_risk_profile_job_status
        ON JobRiskProfile (job_id, status, version)
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS JobRiskMeasurement (
            profile_id INTEGER NOT NULL,
            tool_id TEXT NOT NULL,
            total_cumulative_damage REAL CHECK (
                total_cumulative_damage IS NULL OR total_cumulative_damage >= 0
            ),
            probability_outcome REAL CHECK (
                probability_outcome IS NULL OR probability_outcome BETWEEN 0 AND 100
            ),
            unit TEXT,
            notes TEXT,
            PRIMARY KEY (profile_id, tool_id),
            FOREIGN KEY (profile_id) REFERENCES JobRiskProfile (id) ON DELETE CASCADE,
            FOREIGN KEY (tool_id) REFERENCES ErgoTool (id) ON DELETE CASCADE
        )
        """
    )
    connection.execute(
        """
        INSERT INTO JobRiskProfile (
            job_id, name, version, status, is_current, source_type,
            methodology, notes
        )
        SELECT id, 'Imported baseline', 1, 'approved', 1, 'imported',
               'Migrated from the legacy JobMeasurement record.',
               'Automatically created during the integrated risk schema migration.'
        FROM Job
        WHERE NOT EXISTS (
            SELECT 1 FROM JobRiskProfile profile WHERE profile.job_id = Job.id
        )
        """
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO JobRiskMeasurement (
            profile_id, tool_id, total_cumulative_damage, probability_outcome
        )
        SELECT profile.id, measurement.tool_id,
               measurement.total_cumulative_damage, measurement.probability_outcome
        FROM JobMeasurement AS measurement
        JOIN JobRiskProfile AS profile
          ON profile.job_id = measurement.job_id
         AND profile.version = 1
         AND profile.source_type = 'imported'
        """
    )
    connection.execute(
        """
        CREATE VIEW IF NOT EXISTS CurrentJobRiskMeasurement AS
        SELECT job.id AS job_id,
               job.name AS job_name,
               job.description AS job_description,
               profile.id AS profile_id,
               profile.name AS profile_name,
               profile.version AS profile_version,
               profile.source_type,
               profile.source_reference,
               measurement.tool_id,
               measurement.total_cumulative_damage,
               measurement.probability_outcome,
               measurement.unit,
               measurement.notes
        FROM Job AS job
        JOIN JobRiskProfile AS profile ON profile.job_id = job.id
        JOIN JobRiskMeasurement AS measurement ON measurement.profile_id = profile.id
        WHERE job.active = 1
          AND profile.status = 'approved'
          AND profile.is_current = 1
        """
    )


def _create_workplace_assignments_v4(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS WorkplaceContext (
            id INTEGER PRIMARY KEY,
            plant_name TEXT NOT NULL,
            section_name TEXT NOT NULL,
            line_name TEXT NOT NULL,
            station_id TEXT NOT NULL,
            shift_id TEXT NOT NULL,
            UNIQUE (plant_name, section_name, line_name, station_id, shift_id),
            FOREIGN KEY (plant_name, section_name, line_name, station_id)
                REFERENCES Station (plant_name, section_name, line_name, id)
                ON DELETE CASCADE,
            FOREIGN KEY (shift_id) REFERENCES Shift (id) ON DELETE CASCADE
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_workplace_context_hierarchy
        ON WorkplaceContext (
            plant_name, section_name, line_name, station_id, shift_id
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS JobPlacement (
            id INTEGER PRIMARY KEY,
            job_id TEXT NOT NULL,
            workplace_context_id INTEGER NOT NULL,
            active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
            valid_from TEXT,
            valid_to TEXT,
            notes TEXT,
            CHECK (valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to),
            FOREIGN KEY (job_id) REFERENCES Job (id) ON DELETE CASCADE,
            FOREIGN KEY (workplace_context_id) REFERENCES WorkplaceContext (id)
                ON DELETE CASCADE
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_job_placement_job
        ON JobPlacement (job_id, active, valid_from, valid_to)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_job_placement_context
        ON JobPlacement (workplace_context_id, active, valid_from, valid_to)
        """
    )
    for operation in ("INSERT", "UPDATE"):
        connection.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS trg_job_placement_no_overlap_{operation.lower()}
            BEFORE {operation} ON JobPlacement
            WHEN NEW.active = 1 AND EXISTS (
                SELECT 1
                FROM JobPlacement existing
                WHERE existing.job_id = NEW.job_id
                  AND existing.workplace_context_id = NEW.workplace_context_id
                  AND existing.active = 1
                  AND existing.id != COALESCE(NEW.id, -1)
                  AND COALESCE(existing.valid_from, '0001-01-01')
                      <= COALESCE(NEW.valid_to, '9999-12-31')
                  AND COALESCE(NEW.valid_from, '0001-01-01')
                      <= COALESCE(existing.valid_to, '9999-12-31')
            )
            BEGIN
                SELECT RAISE(ABORT, 'active Job Placements may not overlap');
            END
            """
        )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS WorkerAssignment (
            id INTEGER PRIMARY KEY,
            worker_id TEXT NOT NULL,
            workplace_context_id INTEGER NOT NULL,
            job_placement_id INTEGER,
            started_at TEXT,
            ended_at TEXT,
            active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
            notes TEXT,
            CHECK (started_at IS NULL OR ended_at IS NULL OR started_at <= ended_at),
            FOREIGN KEY (worker_id) REFERENCES Worker (id) ON DELETE CASCADE,
            FOREIGN KEY (workplace_context_id) REFERENCES WorkplaceContext (id)
                ON DELETE CASCADE,
            FOREIGN KEY (job_placement_id) REFERENCES JobPlacement (id)
                ON DELETE SET NULL
        )
        """
    )
    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_worker_assignment_active_context
        ON WorkerAssignment (worker_id, workplace_context_id)
        WHERE active = 1
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_worker_assignment_context
        ON WorkerAssignment (workplace_context_id, active)
        """
    )
    for operation in ("INSERT", "UPDATE"):
        connection.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS trg_worker_assignment_placement_context_{operation.lower()}
            BEFORE {operation} ON WorkerAssignment
            WHEN NEW.job_placement_id IS NOT NULL
             AND NOT EXISTS (
                 SELECT 1 FROM JobPlacement placement
                 WHERE placement.id = NEW.job_placement_id
                   AND placement.workplace_context_id = NEW.workplace_context_id
             )
            BEGIN
                SELECT RAISE(ABORT, 'Worker Assignment and Job Placement contexts must match');
            END
            """
        )

    legacy_table = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='WorkerStationShiftErgoTool'"
    ).fetchone()
    if legacy_table:
        connection.execute(
            """
            INSERT OR IGNORE INTO WorkplaceContext (
                plant_name, section_name, line_name, station_id, shift_id
            )
            SELECT DISTINCT plant_name, section_name, line_name, station_id, shift_id
            FROM WorkerStationShiftErgoTool
            """
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO WorkerAssignment (
                worker_id, workplace_context_id, job_placement_id, active, notes
            )
            SELECT DISTINCT legacy.worker_id, context.id, NULL, 1,
                   'Migrated from WorkerStationShiftErgoTool; Job not yet classified.'
            FROM WorkerStationShiftErgoTool AS legacy
            JOIN WorkplaceContext AS context
              ON context.plant_name = legacy.plant_name
             AND context.section_name = legacy.section_name
             AND context.line_name = legacy.line_name
             AND context.station_id = legacy.station_id
             AND context.shift_id = legacy.shift_id
            """
        )


def _create_individual_assessments_v5(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS IndividualAssessment (
            id INTEGER PRIMARY KEY,
            worker_assignment_id INTEGER NOT NULL,
            tool_id TEXT NOT NULL,
            version INTEGER NOT NULL CHECK (version > 0),
            status TEXT NOT NULL CHECK (status IN ('draft', 'complete', 'superseded')),
            is_current INTEGER NOT NULL DEFAULT 0 CHECK (is_current IN (0, 1)),
            assessed_at TEXT,
            unit TEXT,
            total_cumulative_damage REAL CHECK (
                total_cumulative_damage IS NULL OR total_cumulative_damage >= 0
            ),
            probability_outcome REAL CHECK (
                probability_outcome IS NULL OR probability_outcome BETWEEN 0 AND 100
            ),
            notes TEXT,
            UNIQUE (worker_assignment_id, tool_id, version),
            FOREIGN KEY (worker_assignment_id) REFERENCES WorkerAssignment (id)
                ON DELETE CASCADE,
            FOREIGN KEY (tool_id) REFERENCES ErgoTool (id) ON DELETE CASCADE
        )
        """
    )
    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_individual_assessment_current
        ON IndividualAssessment (worker_assignment_id, tool_id)
        WHERE is_current = 1
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_individual_assessment_tool_status
        ON IndividualAssessment (tool_id, status, is_current)
        """
    )

    task_definitions = {
        "LiFFTAssessmentTask": """
            lever_arm REAL CHECK (lever_arm IS NULL OR lever_arm >= 0),
            load REAL CHECK (load IS NULL OR load >= 0),
            moment REAL CHECK (moment IS NULL OR moment >= 0),
            repetitions INTEGER CHECK (repetitions IS NULL OR repetitions >= 0),
            cumulative_damage REAL CHECK (cumulative_damage IS NULL OR cumulative_damage >= 0),
            percentage_total REAL CHECK (percentage_total IS NULL OR percentage_total >= 0)
        """,
        "DUETAssessmentTask": """
            omni_res_scale INTEGER CHECK (omni_res_scale IS NULL OR omni_res_scale BETWEEN 0 AND 10),
            repetitions INTEGER CHECK (repetitions IS NULL OR repetitions >= 0),
            cumulative_damage REAL CHECK (cumulative_damage IS NULL OR cumulative_damage >= 0),
            percentage_total REAL CHECK (percentage_total IS NULL OR percentage_total >= 0)
        """,
        "ShoulderAssessmentTask": """
            type_of_task INTEGER,
            lever_arm REAL CHECK (lever_arm IS NULL OR lever_arm >= 0),
            load REAL CHECK (load IS NULL OR load >= 0),
            moment REAL CHECK (moment IS NULL OR moment >= 0),
            repetitions INTEGER CHECK (repetitions IS NULL OR repetitions >= 0),
            cumulative_damage REAL CHECK (cumulative_damage IS NULL OR cumulative_damage >= 0),
            percentage_total REAL CHECK (percentage_total IS NULL OR percentage_total >= 0)
        """,
    }
    expected_tools = {
        "LiFFTAssessmentTask": "LiFFT",
        "DUETAssessmentTask": "DUET",
        "ShoulderAssessmentTask": "ST",
    }
    for table_name, fields in task_definitions.items():
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                individual_assessment_id INTEGER NOT NULL,
                task_index INTEGER NOT NULL CHECK (task_index >= 0),
                {fields},
                PRIMARY KEY (individual_assessment_id, task_index),
                FOREIGN KEY (individual_assessment_id) REFERENCES IndividualAssessment (id)
                    ON DELETE CASCADE
            )
            """
        )
        for operation in ("INSERT", "UPDATE"):
            connection.execute(
                f"""
                CREATE TRIGGER IF NOT EXISTS trg_{table_name.lower()}_tool_{operation.lower()}
                BEFORE {operation} ON {table_name}
                WHEN NOT EXISTS (
                    SELECT 1 FROM IndividualAssessment assessment
                    WHERE assessment.id = NEW.individual_assessment_id
                      AND assessment.tool_id = '{expected_tools[table_name]}'
                )
                BEGIN
                    SELECT RAISE(ABORT, 'assessment task belongs to the wrong ergonomic tool');
                END
                """
            )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS PlotAssessmentMarker (
            individual_assessment_id INTEGER PRIMARY KEY,
            x REAL,
            y REAL,
            width REAL,
            height REAL,
            line_thickness REAL,
            scale_x REAL,
            scale_y REAL,
            crop_x REAL,
            crop_y REAL,
            crop_width REAL,
            crop_height REAL,
            zoom REAL,
            rotation REAL,
            mirror_h INTEGER CHECK (mirror_h IS NULL OR mirror_h IN (0, 1)),
            mirror_v INTEGER CHECK (mirror_v IS NULL OR mirror_v IN (0, 1)),
            orientation TEXT,
            r INTEGER CHECK (r IS NULL OR r BETWEEN 0 AND 255),
            g INTEGER CHECK (g IS NULL OR g BETWEEN 0 AND 255),
            b INTEGER CHECK (b IS NULL OR b BETWEEN 0 AND 255),
            brightness REAL,
            contrast REAL,
            saturation REAL,
            lock INTEGER CHECK (lock IS NULL OR lock IN (0, 1)),
            visible INTEGER CHECK (visible IS NULL OR visible IN (0, 1)),
            transparency REAL CHECK (
                transparency IS NULL OR transparency BETWEEN 0 AND 1
            ),
            enable INTEGER CHECK (enable IS NULL OR enable IN (0, 1)),
            FOREIGN KEY (individual_assessment_id) REFERENCES IndividualAssessment (id)
                ON DELETE CASCADE
        )
        """
    )

    legacy_table = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='WorkerStationShiftErgoTool'"
    ).fetchone()
    if not legacy_table:
        return

    completion_expression = """
        CASE legacy.tool_id
            WHEN 'LiFFT' THEN EXISTS (
                SELECT 1 FROM LifftResults task
                WHERE task.worker_id = legacy.worker_id
                  AND task.plant_name = legacy.plant_name
                  AND task.section_name = legacy.section_name
                  AND task.line_name = legacy.line_name
                  AND task.station_id = legacy.station_id
                  AND task.shift_id = legacy.shift_id
                  AND task.tool_id = legacy.tool_id
                  AND COALESCE(task.repetitions, 0) > 0
            )
            WHEN 'DUET' THEN EXISTS (
                SELECT 1 FROM DuetResults task
                WHERE task.worker_id = legacy.worker_id
                  AND task.plant_name = legacy.plant_name
                  AND task.section_name = legacy.section_name
                  AND task.line_name = legacy.line_name
                  AND task.station_id = legacy.station_id
                  AND task.shift_id = legacy.shift_id
                  AND task.tool_id = legacy.tool_id
                  AND COALESCE(task.repetitions, 0) > 0
            )
            WHEN 'ST' THEN EXISTS (
                SELECT 1 FROM TstResults task
                WHERE task.worker_id = legacy.worker_id
                  AND task.plant_name = legacy.plant_name
                  AND task.section_name = legacy.section_name
                  AND task.line_name = legacy.line_name
                  AND task.station_id = legacy.station_id
                  AND task.shift_id = legacy.shift_id
                  AND task.tool_id = legacy.tool_id
                  AND COALESCE(task.repetitions, 0) > 0
            )
            ELSE 0
        END
    """
    connection.execute(
        f"""
        INSERT OR IGNORE INTO IndividualAssessment (
            worker_assignment_id, tool_id, version, status, is_current,
            unit, total_cumulative_damage, probability_outcome, notes
        )
        SELECT assignment.id, legacy.tool_id, 1,
               CASE WHEN ({completion_expression}) THEN 'complete' ELSE 'draft' END,
               1,
               legacy.unit,
               CASE WHEN ({completion_expression}) THEN legacy.total_cumulative_damage END,
               CASE WHEN ({completion_expression}) THEN legacy.probability_outcome END,
               'Migrated from WorkerStationShiftErgoTool.'
        FROM WorkerStationShiftErgoTool AS legacy
        JOIN WorkplaceContext AS context
          ON context.plant_name = legacy.plant_name
         AND context.section_name = legacy.section_name
         AND context.line_name = legacy.line_name
         AND context.station_id = legacy.station_id
         AND context.shift_id = legacy.shift_id
        JOIN WorkerAssignment AS assignment
          ON assignment.worker_id = legacy.worker_id
         AND assignment.workplace_context_id = context.id
         AND assignment.active = 1
        """
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO PlotAssessmentMarker (
            individual_assessment_id, x, y, width, height, line_thickness,
            scale_x, scale_y, crop_x, crop_y, crop_width, crop_height, zoom,
            rotation, mirror_h, mirror_v, orientation, r, g, b, brightness,
            contrast, saturation, lock, visible, transparency, enable
        )
        SELECT assessment.id, legacy.x, legacy.y, legacy.width, legacy.height,
               legacy.line_thickness, legacy.scale_x, legacy.scale_y,
               legacy.crop_x, legacy.crop_y, legacy.crop_width, legacy.crop_height,
               legacy.zoom, legacy.rotation, legacy.mirror_h, legacy.mirror_v,
               legacy.orientation, legacy.r, legacy.g, legacy.b, legacy.brightness,
               legacy.contrast, legacy.saturation, legacy.lock, legacy.visible,
               legacy.transparency, legacy.enable
        FROM WorkerStationShiftErgoTool AS legacy
        JOIN WorkplaceContext AS context
          ON context.plant_name = legacy.plant_name
         AND context.section_name = legacy.section_name
         AND context.line_name = legacy.line_name
         AND context.station_id = legacy.station_id
         AND context.shift_id = legacy.shift_id
        JOIN WorkerAssignment AS assignment
          ON assignment.worker_id = legacy.worker_id
         AND assignment.workplace_context_id = context.id
         AND assignment.active = 1
        JOIN IndividualAssessment AS assessment
          ON assessment.worker_assignment_id = assignment.id
         AND assessment.tool_id = legacy.tool_id
         AND assessment.version = 1
        """
    )

    task_migrations = (
        (
            "LifftResults",
            "LiFFTAssessmentTask",
            "lever_arm, load, moment, repetitions, cumulative_damage, percentage_total",
        ),
        (
            "DuetResults",
            "DUETAssessmentTask",
            "omni_res_scale, repetitions, cumulative_damage, percentage_total",
        ),
        (
            "TstResults",
            "ShoulderAssessmentTask",
            "type_of_task, lever_arm, load, moment, repetitions, cumulative_damage, percentage_total",
        ),
    )
    for legacy_name, target_name, task_columns in task_migrations:
        qualified_columns = ", ".join(
            f"task.{column.strip()}" for column in task_columns.split(",")
        )
        connection.execute(
            f"""
            INSERT OR IGNORE INTO {target_name} (
                individual_assessment_id, task_index, {task_columns}
            )
            SELECT assessment.id, task.task_id, {qualified_columns}
            FROM {legacy_name} AS task
            JOIN WorkplaceContext AS context
              ON context.plant_name = task.plant_name
             AND context.section_name = task.section_name
             AND context.line_name = task.line_name
             AND context.station_id = task.station_id
             AND context.shift_id = task.shift_id
            JOIN WorkerAssignment AS assignment
              ON assignment.worker_id = task.worker_id
             AND assignment.workplace_context_id = context.id
             AND assignment.active = 1
            JOIN IndividualAssessment AS assessment
              ON assessment.worker_assignment_id = assignment.id
             AND assessment.tool_id = task.tool_id
             AND assessment.version = 1
            """
        )


def _remove_unused_validity_periods_v6(connection: sqlite3.Connection) -> None:
    """Remove validity periods; lifecycle state is explicit and user-controlled."""
    connection.execute("DROP VIEW IF EXISTS CurrentJobRiskMeasurement")
    connection.execute(
        """
        CREATE TABLE JobRiskProfile_schema_v6 (
            id INTEGER PRIMARY KEY,
            job_id TEXT NOT NULL,
            name TEXT NOT NULL,
            version INTEGER NOT NULL CHECK (version > 0),
            status TEXT NOT NULL CHECK (status IN ('draft', 'approved', 'retired')),
            is_current INTEGER NOT NULL DEFAULT 0 CHECK (is_current IN (0, 1)),
            source_type TEXT NOT NULL CHECK (
                source_type IN ('expert', 'external', 'study', 'aggregate', 'imported')
            ),
            source_reference TEXT,
            methodology TEXT,
            sample_size INTEGER CHECK (sample_size IS NULL OR sample_size >= 0),
            assessed_on TEXT,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (job_id, version),
            FOREIGN KEY (job_id) REFERENCES Job (id) ON DELETE CASCADE
        )
        """
    )
    connection.execute(
        """
        INSERT INTO JobRiskProfile_schema_v6 (
            id, job_id, name, version, status, is_current, source_type,
            source_reference, methodology, sample_size, assessed_on, notes,
            created_at, updated_at
        )
        SELECT id, job_id, name, version, status, is_current, source_type,
               source_reference, methodology, sample_size, assessed_on, notes,
               created_at, updated_at
        FROM JobRiskProfile
        """
    )
    connection.execute("DROP TABLE JobRiskProfile")
    connection.execute("ALTER TABLE JobRiskProfile_schema_v6 RENAME TO JobRiskProfile")
    connection.execute(
        """
        CREATE UNIQUE INDEX uq_job_risk_profile_current_approved
        ON JobRiskProfile (job_id)
        WHERE is_current = 1 AND status = 'approved'
        """
    )
    connection.execute(
        "CREATE INDEX ix_job_risk_profile_job_status "
        "ON JobRiskProfile (job_id, status, version)"
    )
    connection.execute(
        """
        CREATE VIEW CurrentJobRiskMeasurement AS
        SELECT job.id AS job_id,
               job.name AS job_name,
               job.description AS job_description,
               profile.id AS profile_id,
               profile.name AS profile_name,
               profile.version AS profile_version,
               profile.source_type,
               profile.source_reference,
               measurement.tool_id,
               measurement.total_cumulative_damage,
               measurement.probability_outcome,
               measurement.unit,
               measurement.notes
        FROM Job AS job
        JOIN JobRiskProfile AS profile ON profile.job_id = job.id
        JOIN JobRiskMeasurement AS measurement ON measurement.profile_id = profile.id
        WHERE job.active = 1
          AND profile.status = 'approved'
          AND profile.is_current = 1
        """
    )

    connection.execute("DROP TRIGGER IF EXISTS trg_worker_assignment_placement_context_insert")
    connection.execute("DROP TRIGGER IF EXISTS trg_worker_assignment_placement_context_update")
    connection.execute(
        """
        CREATE TABLE JobPlacement_schema_v6 (
            id INTEGER PRIMARY KEY,
            job_id TEXT NOT NULL,
            workplace_context_id INTEGER NOT NULL,
            active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
            notes TEXT,
            FOREIGN KEY (job_id) REFERENCES Job (id) ON DELETE CASCADE,
            FOREIGN KEY (workplace_context_id) REFERENCES WorkplaceContext (id)
                ON DELETE CASCADE
        )
        """
    )
    connection.execute(
        """
        INSERT INTO JobPlacement_schema_v6 (
            id, job_id, workplace_context_id, active, notes
        )
        SELECT id, job_id, workplace_context_id, active, notes
        FROM JobPlacement
        """
    )
    connection.execute("DROP TABLE JobPlacement")
    connection.execute("ALTER TABLE JobPlacement_schema_v6 RENAME TO JobPlacement")
    connection.execute(
        """
        CREATE UNIQUE INDEX uq_job_placement_active_context
        ON JobPlacement (job_id, workplace_context_id)
        WHERE active = 1
        """
    )
    connection.execute(
        "CREATE INDEX ix_job_placement_job ON JobPlacement (job_id, active)"
    )
    connection.execute(
        "CREATE INDEX ix_job_placement_context ON JobPlacement (workplace_context_id, active)"
    )
    for operation in ("INSERT", "UPDATE"):
        connection.execute(
            f"""
            CREATE TRIGGER trg_worker_assignment_placement_context_{operation.lower()}
            BEFORE {operation} ON WorkerAssignment
            WHEN NEW.job_placement_id IS NOT NULL
             AND NOT EXISTS (
                 SELECT 1 FROM JobPlacement placement
                 WHERE placement.id = NEW.job_placement_id
                   AND placement.workplace_context_id = NEW.workplace_context_id
             )
            BEGIN
                SELECT RAISE(ABORT, 'Worker Assignment and Job Placement contexts must match');
            END
            """
        )


def _create_assignment_map_positions_v7(connection: sqlite3.Connection) -> None:
    """Normalize PLOT positions around Stations and Worker Assignments."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS PlotStationPosition (
            plant_name TEXT NOT NULL,
            section_name TEXT NOT NULL,
            line_name TEXT NOT NULL,
            station_id TEXT NOT NULL,
            x REAL NOT NULL,
            y REAL NOT NULL,
            position_source TEXT NOT NULL CHECK (
                position_source IN ('manual', 'worker', 'job', 'migration')
            ),
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (plant_name, section_name, line_name, station_id),
            FOREIGN KEY (plant_name, section_name, line_name, station_id)
                REFERENCES Station (plant_name, section_name, line_name, id)
                ON DELETE CASCADE
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS PlotWorkerAssignmentMarker (
            worker_assignment_id INTEGER PRIMARY KEY,
            x REAL,
            y REAL,
            size REAL NOT NULL DEFAULT 50 CHECK (size > 0),
            scale REAL NOT NULL DEFAULT 1 CHECK (scale > 0),
            line_thickness REAL NOT NULL DEFAULT 1 CHECK (line_thickness >= 0),
            locked INTEGER NOT NULL DEFAULT 0 CHECK (locked IN (0, 1)),
            visible INTEGER NOT NULL DEFAULT 0 CHECK (visible IN (0, 1)),
            enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
            position_source TEXT NOT NULL DEFAULT 'unplaced' CHECK (
                position_source IN ('unplaced', 'station_anchor', 'manual', 'migration')
            ),
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK ((x IS NULL) = (y IS NULL)),
            CHECK (
                (position_source = 'unplaced' AND x IS NULL AND y IS NULL)
                OR
                (position_source != 'unplaced' AND x IS NOT NULL AND y IS NOT NULL)
            ),
            FOREIGN KEY (worker_assignment_id) REFERENCES WorkerAssignment (id)
                ON DELETE CASCADE
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_plot_worker_marker_visibility
        ON PlotWorkerAssignmentMarker (visible, enabled)
        """
    )

    # A Worker Assignment has one physical position. Prefer a visible, enabled
    # current assessment marker and use tool order only as a deterministic tie-break.
    connection.execute(
        """
        WITH ranked_markers AS (
            SELECT assessment.worker_assignment_id,
                   marker.x, marker.y,
                   MAX(COALESCE(marker.width, 50), COALESCE(marker.height, 50)) AS size,
                   COALESCE(marker.scale_x, marker.scale_y, 1) AS scale,
                   COALESCE(marker.line_thickness, 1) AS line_thickness,
                   COALESCE(marker.lock, 0) AS locked,
                   COALESCE(marker.visible, 0) AS visible,
                   COALESCE(marker.enable, 1) AS enabled,
                   ROW_NUMBER() OVER (
                       PARTITION BY assessment.worker_assignment_id
                       ORDER BY COALESCE(marker.visible, 0) DESC,
                                COALESCE(marker.enable, 1) DESC,
                                CASE assessment.tool_id
                                    WHEN 'LiFFT' THEN 0
                                    WHEN 'DUET' THEN 1
                                    WHEN 'ST' THEN 2
                                    ELSE 3
                                END,
                                assessment.id
                   ) AS marker_rank
            FROM IndividualAssessment AS assessment
            JOIN PlotAssessmentMarker AS marker
              ON marker.individual_assessment_id = assessment.id
            WHERE assessment.is_current = 1
        )
        INSERT OR IGNORE INTO PlotWorkerAssignmentMarker (
            worker_assignment_id, x, y, size, scale, line_thickness,
            locked, visible, enabled, position_source
        )
        SELECT worker_assignment_id, x, y, size, scale, line_thickness,
               locked, visible, enabled,
               CASE WHEN x IS NULL OR y IS NULL THEN 'unplaced' ELSE 'migration' END
        FROM ranked_markers
        WHERE marker_rank = 1
        """
    )

    station_table_exists = connection.execute(
        """
        SELECT EXISTS (
            SELECT 1 FROM sqlite_master
            WHERE type = 'table' AND name = 'Station'
        )
        """
    ).fetchone()[0]
    if station_table_exists:
        # Existing Station coordinates are authoritative when present.
        connection.execute(
            """
            INSERT OR IGNORE INTO PlotStationPosition (
                plant_name, section_name, line_name, station_id,
                x, y, position_source
            )
            SELECT plant_name, section_name, line_name, id,
                   x, y, 'migration'
            FROM Station
            WHERE x IS NOT NULL AND y IS NOT NULL
            """
        )

    # Older projects normally positioned Workers rather than Stations. The best
    # available active Worker marker initializes an otherwise unknown Station anchor.
    connection.execute(
        """
        WITH ranked_station_markers AS (
            SELECT context.plant_name, context.section_name, context.line_name,
                   context.station_id, marker.x, marker.y,
                   ROW_NUMBER() OVER (
                       PARTITION BY context.plant_name, context.section_name,
                                    context.line_name, context.station_id
                       ORDER BY assignment.active DESC,
                                marker.visible DESC,
                                marker.enabled DESC,
                                assignment.id
                   ) AS marker_rank
            FROM PlotWorkerAssignmentMarker AS marker
            JOIN WorkerAssignment AS assignment
              ON assignment.id = marker.worker_assignment_id
            JOIN WorkplaceContext AS context
              ON context.id = assignment.workplace_context_id
            WHERE marker.x IS NOT NULL AND marker.y IS NOT NULL
        )
        INSERT OR IGNORE INTO PlotStationPosition (
            plant_name, section_name, line_name, station_id,
            x, y, position_source
        )
        SELECT plant_name, section_name, line_name, station_id,
               x, y, 'worker'
        FROM ranked_station_markers
        WHERE marker_rank = 1
        """
    )


MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        version=1,
        name="versioned JROT baseline",
        definition="SchemaMigration plus the integrated JROT schema as of 2026-09-12",
        apply=_create_jrot_schema_v1,
    ),
    Migration(
        version=2,
        name="repair legacy Plant columns",
        definition=(
            "Rebuild the malformed legacy Plant table so mirror_v INTEGER and "
            "orientation TEXT are distinct columns"
        ),
        apply=_repair_plant_schema_v2,
        requires_foreign_keys_off=True,
    ),
    Migration(
        version=3,
        name="versioned job risk profiles",
        definition=(
            "Add Job lifecycle fields, JobRiskProfile, JobRiskMeasurement, the current "
            "risk read model, and migrate legacy JobMeasurement rows"
        ),
        apply=_create_job_risk_profiles_v3,
        requires_foreign_keys_off=True,
    ),
    Migration(
        version=4,
        name="workplace contexts and assignments",
        definition=(
            "Add WorkplaceContext, JobPlacement, and WorkerAssignment with hierarchy, "
            "validity, overlap, and matching-context rules; migrate known worker locations"
        ),
        apply=_create_workplace_assignments_v4,
    ),
    Migration(
        version=5,
        name="individual assessments and PLOT markers",
        definition=(
            "Add IndividualAssessment, tool task tables, and PlotAssessmentMarker; "
            "migrate legacy worker-tool results while retaining per-tool marker state"
        ),
        apply=_create_individual_assessments_v5,
    ),
    Migration(
        version=6,
        name="remove unused validity periods",
        definition=(
            "Remove JobRiskProfile and JobPlacement validity ranges; profile lifecycle "
            "and placement activation are explicit user-controlled states"
        ),
        apply=_remove_unused_validity_periods_v6,
        requires_foreign_keys_off=True,
    ),
    Migration(
        version=7,
        name="station and worker assignment map positions",
        definition=(
            "Add normalized PLOT Station anchors and one physical marker per Worker "
            "Assignment; deterministically migrate existing tool-assessment marker positions"
        ),
        apply=_create_assignment_map_positions_v7,
    ),
    Migration(
        version=8,
        name="normalized rotation scope and risk provenance",
        definition=(
            "Replace legacy plant, shift, and Job-only rotation references with optional "
            "WorkplaceContext scope, frozen Job risk-profile targets, and Worker-assignment "
            "provenance; migrate legacy rotations as organization-wide schemes"
        ),
        apply=normalize_rotation_model_v8,
        requires_foreign_keys_off=True,
    ),
)

LATEST_SCHEMA_VERSION = MIGRATIONS[-1].version


def _table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    escaped = table_name.replace('"', '""')
    return {row[1] for row in connection.execute(f'PRAGMA table_info("{escaped}")')}


def _validate_partial_tables(connection: sqlite3.Connection) -> None:
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    requirements = dict(JROT_REQUIRED_COLUMNS)
    if int(connection.execute("PRAGMA user_version").fetchone()[0]) >= 8:
        requirements["RotationAssignment"] = requirements["RotationAssignment"] | {
            "worker_assignment_id",
            "rotation_target_id",
        }
    requirements["SchemaMigration"] = SCHEMA_MIGRATION_COLUMNS
    for table_name, required_columns in requirements.items():
        if table_name not in tables:
            continue
        missing = required_columns - _table_columns(connection, table_name)
        if missing:
            missing_text = ", ".join(sorted(missing))
            raise DatabaseSafetyError(
                f"Table {table_name} is partially defined; missing column(s): {missing_text}."
            )


def _migration_history(connection: sqlite3.Connection) -> dict[int, tuple[str, str]]:
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'SchemaMigration'"
        )
    }
    if not tables:
        return {}
    return {
        int(version): (name, checksum)
        for version, name, checksum in connection.execute(
            "SELECT version, name, checksum FROM SchemaMigration ORDER BY version"
        )
    }


def _validate_version_state(
    connection: sqlite3.Connection,
    migrations: Sequence[Migration],
) -> int:
    user_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
    latest = migrations[-1].version if migrations else 0
    if user_version > latest:
        raise DatabaseSafetyError(
            f"Project schema version {user_version} is newer than this application supports "
            f"({latest})."
        )

    history = _migration_history(connection)
    known = {migration.version: migration for migration in migrations}
    unknown_history = sorted(set(history) - set(known))
    if unknown_history:
        raise DatabaseSafetyError(
            f"Project contains unknown migration version(s): {unknown_history}."
        )
    for version, (name, checksum) in history.items():
        migration = known[version]
        if name != migration.name or checksum != migration.checksum:
            raise DatabaseSafetyError(
                f"Migration history checksum mismatch at schema version {version}."
            )
    if history and max(history) != user_version:
        raise DatabaseSafetyError(
            "SchemaMigration history and PRAGMA user_version are inconsistent."
        )
    if user_version and user_version not in history:
        raise DatabaseSafetyError(
            "PRAGMA user_version is set but its migration history is missing."
        )
    return user_version


def migrate_database(
    database_path,
    *,
    application_version: Optional[str] = None,
    create_backup: bool = True,
    migrations: Sequence[Migration] = MIGRATIONS,
) -> MigrationResult:
    """Apply pending migrations atomically after a verified pre-migration backup."""
    path = Path(database_path).expanduser().resolve()
    if not path.is_file():
        raise DatabaseSafetyError(f"Project database does not exist: {path}")

    probe = connect_database(path, read_only=True)
    try:
        _validate_partial_tables(probe)
        initial_version = _validate_version_state(probe, migrations)
    finally:
        probe.close()

    pending = [migration for migration in migrations if migration.version > initial_version]
    if not pending:
        return MigrationResult(initial_version, initial_version, (), None)

    backup = (
        create_verified_backup(path, target_version=pending[-1].version)
        if create_backup
        else None
    )
    connection = connect_database(path)
    applied_versions: list[int] = []
    try:
        if any(migration.requires_foreign_keys_off for migration in pending):
            connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("BEGIN IMMEDIATE")
        _validate_partial_tables(connection)
        current_version = _validate_version_state(connection, migrations)
        if current_version != initial_version:
            raise DatabaseSafetyError("Project schema changed while migration was starting.")

        for migration in pending:
            migration.apply(connection)
            connection.execute(
                """
                INSERT INTO SchemaMigration (
                    version, name, checksum, applied_at, application_version
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    migration.version,
                    migration.name,
                    migration.checksum,
                    datetime.now(timezone.utc).isoformat(),
                    application_version,
                ),
            )
            connection.execute(f"PRAGMA user_version = {migration.version}")
            applied_versions.append(migration.version)

        _validate_partial_tables(connection)
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise DatabaseSafetyError(
                f"Migration produced {len(violations)} foreign-key violation(s)."
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return MigrationResult(
        initial_version=initial_version,
        final_version=applied_versions[-1],
        applied_versions=tuple(applied_versions),
        backup=backup,
    )

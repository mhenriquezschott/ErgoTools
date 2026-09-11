import sqlite3
from contextlib import closing


JROT_TABLES = ("Job", "JobMeasurement", "RotationScheme", "RotationAssignment")


def ensure_jrot_schema(database_path):
    """Add the JROT schema to an existing ErgoTools project without altering its data."""
    if not database_path:
        raise ValueError("A project database path is required.")

    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS Job (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT
            );

            CREATE TABLE IF NOT EXISTS JobMeasurement (
                job_id TEXT NOT NULL,
                tool_id TEXT NOT NULL,
                total_cumulative_damage REAL,
                probability_outcome REAL,
                color TEXT,
                PRIMARY KEY (job_id, tool_id),
                FOREIGN KEY (job_id) REFERENCES Job (id) ON DELETE CASCADE,
                FOREIGN KEY (tool_id) REFERENCES ErgoTool (id) ON DELETE CASCADE
            );

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
            );

            CREATE TABLE IF NOT EXISTS RotationAssignment (
                scheme_id TEXT NOT NULL,
                block_index INTEGER NOT NULL,
                worker_id TEXT NOT NULL,
                job_id TEXT NOT NULL,
                PRIMARY KEY (scheme_id, block_index, worker_id),
                FOREIGN KEY (scheme_id) REFERENCES RotationScheme (id) ON DELETE CASCADE,
                FOREIGN KEY (worker_id) REFERENCES Worker (id) ON DELETE CASCADE,
                FOREIGN KEY (job_id) REFERENCES Job (id) ON DELETE CASCADE
            );
            """
        )
        connection.commit()

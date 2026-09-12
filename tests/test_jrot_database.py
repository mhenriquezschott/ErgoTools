import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from database import DatabaseSafetyError, connect_database, file_sha256, restore_verified_backup
from jrot_database import JROT_TABLES, ensure_jrot_schema
from schema_migrations import LATEST_SCHEMA_VERSION, Migration, migrate_database


def _create_existing_project(database_path):
    with closing(sqlite3.connect(database_path)) as connection:
        connection.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE Worker (id TEXT PRIMARY KEY);
            CREATE TABLE Plant (name TEXT PRIMARY KEY);
            CREATE TABLE Shift (id TEXT PRIMARY KEY);
            CREATE TABLE ErgoTool (id TEXT PRIMARY KEY);
            INSERT INTO Worker VALUES ('W-1');
            INSERT INTO Plant VALUES ('Plant-1');
            INSERT INTO Shift VALUES ('1');
            INSERT INTO ErgoTool VALUES ('LiFFT');
            """
        )
        connection.commit()


class JrotDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "project.db"
        _create_existing_project(self.database_path)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_migration_preserves_existing_data_and_is_idempotent(self):
        original_checksum = file_sha256(self.database_path)
        first_result = ensure_jrot_schema(self.database_path)
        second_result = ensure_jrot_schema(self.database_path)

        with closing(sqlite3.connect(self.database_path)) as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            self.assertTrue(set(JROT_TABLES).issubset(tables))
            self.assertEqual(connection.execute("SELECT id FROM Worker").fetchall(), [("W-1",)])
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], LATEST_SCHEMA_VERSION)
            history = connection.execute(
                "SELECT version, name, checksum FROM SchemaMigration"
            ).fetchall()
            self.assertEqual(len(history), LATEST_SCHEMA_VERSION)

        self.assertEqual(
            first_result.applied_versions,
            tuple(range(1, LATEST_SCHEMA_VERSION + 1)),
        )
        self.assertIsNotNone(first_result.backup)
        self.assertEqual(first_result.backup.source_checksum, original_checksum)
        self.assertEqual(file_sha256(first_result.backup.path), original_checksum)
        self.assertEqual(second_result.applied_versions, ())
        self.assertIsNone(second_result.backup)

    def test_jrot_foreign_keys_and_cascades(self):
        ensure_jrot_schema(self.database_path)

        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                "INSERT INTO Job (id, name, description) VALUES ('J-1', 'Job 1', '')"
            )
            connection.execute(
                "INSERT INTO JobMeasurement VALUES ('J-1', 'LiFFT', 0.1, 25.0, '#00ff00')"
            )
            connection.execute("DELETE FROM Job WHERE id = 'J-1'")
            self.assertEqual(connection.execute("SELECT * FROM JobMeasurement").fetchall(), [])
            connection.commit()

    def test_connection_helper_always_enables_foreign_keys(self):
        connection = connect_database(self.database_path)
        try:
            self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        finally:
            connection.close()

    def test_rejects_unknown_newer_schema_without_changing_database(self):
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.execute("PRAGMA user_version = 999")
            connection.commit()
        checksum_before = file_sha256(self.database_path)

        with self.assertRaisesRegex(DatabaseSafetyError, "newer"):
            ensure_jrot_schema(self.database_path)

        self.assertEqual(file_sha256(self.database_path), checksum_before)
        self.assertEqual(list(self.database_path.parent.glob("*.bak")), [])

    def test_rejects_partial_existing_table_without_changing_database(self):
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.execute("CREATE TABLE Job (id TEXT PRIMARY KEY)")
            connection.commit()
        checksum_before = file_sha256(self.database_path)

        with self.assertRaisesRegex(DatabaseSafetyError, "partially defined"):
            ensure_jrot_schema(self.database_path)

        self.assertEqual(file_sha256(self.database_path), checksum_before)
        self.assertEqual(list(self.database_path.parent.glob("*.bak")), [])

    def test_failed_migration_rolls_back_and_backup_restores_exact_source(self):
        def fail_after_writing(connection):
            connection.execute("CREATE TABLE MustRollBack (id INTEGER)")
            raise RuntimeError("simulated migration interruption")

        failing_migration = Migration(1, "interrupted test", "test only", fail_after_writing)
        original_checksum = file_sha256(self.database_path)

        with self.assertRaisesRegex(RuntimeError, "simulated"):
            migrate_database(self.database_path, migrations=(failing_migration,))

        with closing(sqlite3.connect(self.database_path)) as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            self.assertNotIn("MustRollBack", tables)
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 0)

        backups = list(self.database_path.parent.glob("*.bak"))
        self.assertEqual(len(backups), 1)
        from database import DatabaseBackup

        backup = DatabaseBackup(backups[0], file_sha256(backups[0]), original_checksum)
        restore_verified_backup(backup, self.database_path)
        self.assertEqual(file_sha256(self.database_path), original_checksum)

    def test_repairs_malformed_plant_definition_and_preserves_children(self):
        malformed_path = Path(self.temporary_directory.name) / "malformed-plant.db"
        with closing(sqlite3.connect(malformed_path)) as connection:
            connection.executescript(
                """
                PRAGMA foreign_keys = ON;
                CREATE TABLE Worker (id TEXT PRIMARY KEY);
                CREATE TABLE Shift (id TEXT PRIMARY KEY);
                CREATE TABLE ErgoTool (id TEXT PRIMARY KEY);
                CREATE TABLE Plant (
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
                    mirror_V INTEGER
                    orientation TEXT,
                    color TEXT,
                    brightness REAL,
                    contrast REAL,
                    saturation REAL,
                    lock INTEGER,
                    visible INTEGER,
                    transparency REAL,
                    enable INTEGER
                );
                CREATE TABLE Section (
                    plant_name TEXT NOT NULL,
                    name TEXT NOT NULL,
                    PRIMARY KEY (plant_name, name),
                    FOREIGN KEY (plant_name) REFERENCES Plant (name) ON DELETE CASCADE
                );
                INSERT INTO Plant (name, description, mirror_V, color)
                VALUES ('P-1', 'Preserve me', 1, '#123456');
                INSERT INTO Section VALUES ('P-1', 'S-1');
                """
            )
            connection.commit()

        ensure_jrot_schema(malformed_path)

        with closing(sqlite3.connect(malformed_path)) as connection:
            info = {row[1]: row[2] for row in connection.execute("PRAGMA table_info(Plant)")}
            self.assertEqual(info["mirror_v"], "INTEGER")
            self.assertEqual(info["orientation"], "TEXT")
            self.assertEqual(
                connection.execute(
                    "SELECT name, description, mirror_v, orientation, color FROM Plant"
                ).fetchone(),
                ("P-1", "Preserve me", 1, None, "#123456"),
            )
            self.assertEqual(connection.execute("SELECT * FROM Section").fetchone(), ("P-1", "S-1"))
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])


if __name__ == "__main__":
    unittest.main()

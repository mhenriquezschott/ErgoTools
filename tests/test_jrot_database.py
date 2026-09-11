import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from jrot_database import JROT_TABLES, ensure_jrot_schema


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
        ensure_jrot_schema(self.database_path)
        ensure_jrot_schema(self.database_path)

        with closing(sqlite3.connect(self.database_path)) as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            self.assertTrue(set(JROT_TABLES).issubset(tables))
            self.assertEqual(connection.execute("SELECT id FROM Worker").fetchall(), [("W-1",)])

    def test_jrot_foreign_keys_and_cascades(self):
        ensure_jrot_schema(self.database_path)

        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("INSERT INTO Job VALUES ('J-1', 'Job 1', '')")
            connection.execute(
                "INSERT INTO JobMeasurement VALUES ('J-1', 'LiFFT', 0.1, 25.0, '#00ff00')"
            )
            connection.execute("DELETE FROM Job WHERE id = 'J-1'")
            self.assertEqual(connection.execute("SELECT * FROM JobMeasurement").fetchall(), [])
            connection.commit()


if __name__ == "__main__":
    unittest.main()

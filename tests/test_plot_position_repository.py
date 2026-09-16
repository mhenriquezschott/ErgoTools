import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC))

from database import connect_database
from plot_position_repository import (
    PlotPositionError,
    StationKey,
    ensure_worker_assignment_marker,
    initialize_station_position,
    save_worker_assignment_marker,
    set_station_position,
    station_position,
)
from schema_migrations import migrate_database


class PlotPositionRepositoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = (
            REPOSITORY_ROOT
            / "tests"
            / "ErgoTools_IntegratedTest_data"
            / "ErgoTools_IntegratedTest_data.db"
        )

    def setUp(self):
        if not self.fixture.is_file():
            self.skipTest("The integrated development fixture is not available.")
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "positions.db"
        shutil.copy2(self.fixture, self.database_path)
        migrate_database(self.database_path, create_backup=False)
        self.connection = connect_database(self.database_path)

        plant, section, line = self.connection.execute(
            """
            SELECT plant_name, section_name, name
            FROM Line
            ORDER BY plant_name, section_name, name
            LIMIT 1
            """
        ).fetchone()
        self.key = StationKey(plant, section, line, "POSITION-TEST")
        self.connection.execute(
            """
            INSERT INTO Station (plant_name, section_name, line_name, id)
            VALUES (?, ?, ?, ?)
            """,
            (plant, section, line, self.key.station_id),
        )
        shift_id = self.connection.execute(
            "SELECT id FROM Shift ORDER BY id LIMIT 1"
        ).fetchone()[0]
        context_id = self.connection.execute(
            """
            INSERT INTO WorkplaceContext (
                plant_name, section_name, line_name, station_id, shift_id
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (plant, section, line, self.key.station_id, shift_id),
        ).lastrowid
        self.assignment_ids = []
        for worker_id in ("POSITION-WORKER-1", "POSITION-WORKER-2"):
            self.connection.execute("INSERT INTO Worker (id) VALUES (?)", (worker_id,))
            self.assignment_ids.append(
                self.connection.execute(
                    """
                    INSERT INTO WorkerAssignment (
                        worker_id, workplace_context_id, active
                    ) VALUES (?, ?, 1)
                    """,
                    (worker_id, context_id),
                ).lastrowid
            )
        self.connection.commit()

    def tearDown(self):
        if hasattr(self, "connection"):
            self.connection.close()
        self.temporary_directory.cleanup()

    def test_first_worker_position_initializes_station_anchor_once(self):
        first_marker = ensure_worker_assignment_marker(
            self.connection, self.assignment_ids[0]
        )
        self.assertIsNone(first_marker.x)
        self.assertEqual(first_marker.position_source, "unplaced")
        self.assertFalse(first_marker.visible)

        saved = save_worker_assignment_marker(
            self.connection,
            self.assignment_ids[0],
            x=125,
            y=240,
            size=54,
            scale=0.8,
            visible=True,
        )
        self.assertEqual((saved.x, saved.y), (125.0, 240.0))
        self.assertEqual(saved.position_source, "manual")
        self.assertTrue(saved.visible)
        anchor = station_position(self.connection, self.key)
        self.assertEqual((anchor.x, anchor.y), (125.0, 240.0))
        self.assertEqual(anchor.position_source, "worker")

        second_marker = ensure_worker_assignment_marker(
            self.connection, self.assignment_ids[1]
        )
        self.assertEqual((second_marker.x, second_marker.y), (125.0, 240.0))
        self.assertEqual(second_marker.position_source, "station_anchor")
        self.assertFalse(second_marker.visible)

        save_worker_assignment_marker(
            self.connection,
            self.assignment_ids[1],
            x=400,
            y=500,
        )
        unchanged_anchor = station_position(self.connection, self.key)
        self.assertEqual((unchanged_anchor.x, unchanged_anchor.y), (125.0, 240.0))

    def test_station_position_requires_explicit_move_after_initialization(self):
        self.assertTrue(
            initialize_station_position(
                self.connection,
                self.key,
                10,
                20,
                position_source="job",
            )
        )
        self.assertFalse(
            initialize_station_position(
                self.connection,
                self.key,
                30,
                40,
                position_source="worker",
            )
        )
        self.assertEqual(
            (station_position(self.connection, self.key).x,
             station_position(self.connection, self.key).y),
            (10.0, 20.0),
        )

        set_station_position(self.connection, self.key, 30, 40)
        moved = station_position(self.connection, self.key)
        self.assertEqual((moved.x, moved.y), (30.0, 40.0))
        self.assertEqual(moved.position_source, "manual")

    def test_invalid_marker_values_and_unknown_assignments_are_rejected(self):
        with self.assertRaises(PlotPositionError):
            ensure_worker_assignment_marker(self.connection, 999999)
        with self.assertRaises(PlotPositionError):
            save_worker_assignment_marker(
                self.connection,
                self.assignment_ids[0],
                x=10,
                y=20,
                scale=0,
            )
        with self.assertRaises(PlotPositionError):
            initialize_station_position(
                self.connection,
                self.key,
                10,
                20,
                position_source="guess",
            )


if __name__ == "__main__":
    unittest.main()

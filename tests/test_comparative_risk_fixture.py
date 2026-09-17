import sqlite3
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PROJECT = REPOSITORY_ROOT / "tests" / "ErgoTools_ComparativeRiskTest.ergprj"


class ComparativeRiskFixtureTests(unittest.TestCase):
    def setUp(self):
        if not PROJECT.is_file():
            self.skipTest("The comparative-risk fixture has not been generated.")
        root = ET.parse(PROJECT).getroot()
        self.database = PROJECT.parent / root.findtext("DataPath") / root.findtext("DatabaseName")
        self.images = PROJECT.parent / root.findtext("ImagesPath")

    def test_fixture_is_complete_and_consistent(self):
        self.assertTrue(self.database.is_file())
        self.assertTrue(self.images.is_dir())
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 7)
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM Plant").fetchone()[0], 4)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM Shift").fetchone()[0], 2)
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM JobPlacement WHERE active = 1"
                ).fetchone()[0],
                17,
            )
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM IndividualAssessment WHERE is_current = 1"
                ).fetchone()[0],
                191,
            )
            self.assertEqual(
                connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM IndividualAssessment AS assessment
                    JOIN WorkerAssignment AS assignment
                      ON assignment.id = assessment.worker_assignment_id
                    WHERE assessment.is_current = 1 AND assignment.active = 1
                      AND assignment.job_placement_id IS NULL
                    """
                ).fetchone()[0],
                0,
            )
            self.assertEqual(
                connection.execute(
                    """
                    SELECT COUNT(*) FROM Job AS job
                    WHERE job.active = 1 AND NOT EXISTS (
                        SELECT 1 FROM JobPlacement AS placement
                        WHERE placement.job_id = job.id AND placement.active = 1
                    )
                    """
                ).fetchone()[0],
                2,
            )
            self.assertEqual(
                connection.execute(
                    """
                    SELECT COUNT(*) FROM CurrentJobRiskMeasurement
                    WHERE job_id = 'Job-S010' AND tool_id = 'ST'
                    """
                ).fetchone()[0],
                0,
            )
            self.assertGreater(
                connection.execute("SELECT COUNT(*) FROM Worker WHERE gender IS NULL").fetchone()[0],
                0,
            )
            self.assertEqual(
                connection.execute(
                    """
                    SELECT COUNT(*) FROM (
                        SELECT DISTINCT context.plant_name, context.section_name,
                               context.line_name, context.station_id
                        FROM JobPlacement AS placement
                        JOIN WorkplaceContext AS context
                          ON context.id = placement.workplace_context_id
                        LEFT JOIN PlotStationPosition AS position
                          ON position.plant_name = context.plant_name
                         AND position.section_name = context.section_name
                         AND position.line_name = context.line_name
                         AND position.station_id = context.station_id
                        WHERE placement.active = 1 AND position.station_id IS NULL
                    )
                    """
                ).fetchone()[0],
                1,
            )


if __name__ == "__main__":
    unittest.main()

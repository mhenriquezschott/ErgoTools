import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC))

from database import file_sha256
from schema_migrations import LATEST_SCHEMA_VERSION, migrate_database
from risk_colors import job_risk_color


class IntegratedProjectMigrationTests(unittest.TestCase):
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
        self.database_path = Path(self.temporary_directory.name) / "integrated-copy.db"
        shutil.copy2(self.fixture, self.database_path)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_full_fixture_migrates_without_data_loss_and_repeats_cleanly(self):
        tracked_tables = (
            "Plant",
            "Section",
            "Line",
            "Station",
            "Shift",
            "Worker",
            "WorkerStationShiftErgoTool",
            "LifftResults",
            "DuetResults",
            "TstResults",
            "Job",
            "JobMeasurement",
            "RotationScheme",
            "RotationAssignment",
            "JobRiskProfile",
            "JobRiskMeasurement",
            "JobPlacement",
            "WorkerAssignment",
        )
        with sqlite3.connect(self.database_path) as connection:
            initial_version = connection.execute("PRAGMA user_version").fetchone()[0]
            counts_before = {
                table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                for table in tracked_tables
            }
        checksum_before = file_sha256(self.database_path)

        first = migrate_database(self.database_path)
        second = migrate_database(self.database_path)

        self.assertEqual(first.final_version, LATEST_SCHEMA_VERSION)
        self.assertEqual(second.applied_versions, ())
        if initial_version < LATEST_SCHEMA_VERSION:
            self.assertIsNotNone(first.backup)
            self.assertEqual(first.backup.source_checksum, checksum_before)
            self.assertEqual(file_sha256(first.backup.path), checksum_before)
        else:
            self.assertIsNone(first.backup)
        with sqlite3.connect(self.database_path) as connection:
            counts_after = {
                table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                for table in tracked_tables
            }
            self.assertEqual(counts_after, counts_before)
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], LATEST_SCHEMA_VERSION)
            for table in ("JobRiskProfile", "JobPlacement"):
                columns = {
                    row[1] for row in connection.execute(f"PRAGMA table_info({table})")
                }
                self.assertNotIn("valid_from", columns)
                self.assertNotIn("valid_to", columns)
            plant_columns = {
                row[1]: row[2] for row in connection.execute("PRAGMA table_info(Plant)")
            }
            self.assertEqual(plant_columns["mirror_v"], "INTEGER")
            self.assertEqual(plant_columns["orientation"], "TEXT")
            self.assertEqual(
                connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM Job
                    WHERE NOT EXISTS (
                        SELECT 1 FROM JobRiskProfile profile
                        WHERE profile.job_id = Job.id
                    )
                    """
                ).fetchone()[0],
                0,
            )
            self.assertEqual(
                connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM JobMeasurement legacy
                    JOIN CurrentJobRiskMeasurement current
                      ON current.job_id = legacy.job_id
                     AND current.tool_id = legacy.tool_id
                    WHERE current.total_cumulative_damage = legacy.total_cumulative_damage
                      AND current.probability_outcome = legacy.probability_outcome
                    """
                ).fetchone()[0],
                connection.execute("SELECT COUNT(*) FROM JobMeasurement").fetchone()[0],
            )
            self.assertGreaterEqual(
                connection.execute("SELECT COUNT(*) FROM WorkplaceContext").fetchone()[0],
                17,
            )
            self.assertGreaterEqual(
                connection.execute("SELECT COUNT(*) FROM WorkerAssignment").fetchone()[0],
                100,
            )
            self.assertEqual(
                connection.execute(
                    """
                    SELECT COUNT(*) FROM WorkerAssignment
                    WHERE job_placement_id IS NULL
                      AND notes LIKE 'Migrated from WorkerStationShiftErgoTool%'
                    """
                ).fetchone()[0],
                100,
            )
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM IndividualAssessment").fetchone()[0], 191)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM PlotAssessmentMarker").fetchone()[0], 191)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM LiFFTAssessmentTask").fetchone()[0], 2010)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM DUETAssessmentTask").fetchone()[0], 735)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM ShoulderAssessmentTask").fetchone()[0], 787)
            self.assertEqual(
                connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM WorkerStationShiftErgoTool legacy
                    JOIN WorkplaceContext context
                      ON context.plant_name = legacy.plant_name
                     AND context.section_name = legacy.section_name
                     AND context.line_name = legacy.line_name
                     AND context.station_id = legacy.station_id
                     AND context.shift_id = legacy.shift_id
                    JOIN WorkerAssignment assignment
                      ON assignment.worker_id = legacy.worker_id
                     AND assignment.workplace_context_id = context.id
                    JOIN IndividualAssessment assessment
                      ON assessment.worker_assignment_id = assignment.id
                     AND assessment.tool_id = legacy.tool_id
                    JOIN PlotAssessmentMarker marker
                      ON marker.individual_assessment_id = assessment.id
                    WHERE marker.x IS legacy.x AND marker.y IS legacy.y
                    """
                ).fetchone()[0],
                191,
            )
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM CurrentJobRiskMeasurement").fetchone()[0],
                connection.execute("SELECT COUNT(*) FROM JobMeasurement").fetchone()[0],
            )
            expected_worker_markers = connection.execute(
                """
                SELECT COUNT(DISTINCT assessment.worker_assignment_id)
                FROM IndividualAssessment AS assessment
                JOIN PlotAssessmentMarker AS marker
                  ON marker.individual_assessment_id = assessment.id
                WHERE assessment.is_current = 1
                """
            ).fetchone()[0]
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM PlotWorkerAssignmentMarker"
                ).fetchone()[0],
                expected_worker_markers,
            )
            self.assertEqual(
                connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM PlotWorkerAssignmentMarker AS worker_marker
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM IndividualAssessment AS assessment
                        JOIN PlotAssessmentMarker AS assessment_marker
                          ON assessment_marker.individual_assessment_id = assessment.id
                        WHERE assessment.worker_assignment_id = worker_marker.worker_assignment_id
                          AND assessment_marker.x IS worker_marker.x
                          AND assessment_marker.y IS worker_marker.y
                    )
                    """
                ).fetchone()[0],
                0,
            )
            self.assertGreater(
                connection.execute("SELECT COUNT(*) FROM PlotStationPosition").fetchone()[0],
                0,
            )
            self.assertEqual(
                connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM PlotStationPosition AS position
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM Station AS station
                        WHERE station.plant_name = position.plant_name
                          AND station.section_name = position.section_name
                          AND station.line_name = position.line_name
                          AND station.id = position.station_id
                    )
                    """
                ).fetchone()[0],
                0,
            )
            marker_id = connection.execute(
                "SELECT worker_assignment_id FROM PlotWorkerAssignmentMarker LIMIT 1"
            ).fetchone()[0]
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    """
                    UPDATE PlotWorkerAssignmentMarker
                    SET position_source = 'unplaced'
                    WHERE worker_assignment_id = ?
                    """,
                    (marker_id,),
                )
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    """
                    UPDATE PlotWorkerAssignmentMarker
                    SET size = 0
                    WHERE worker_assignment_id = ?
                    """,
                    (marker_id,),
                )
            migrated_job_colors = connection.execute(
                """
                SELECT legacy.tool_id, legacy.total_cumulative_damage, legacy.color,
                       current.unit
                FROM JobMeasurement legacy
                JOIN CurrentJobRiskMeasurement current
                  ON current.job_id = legacy.job_id AND current.tool_id = legacy.tool_id
                """
            ).fetchall()
            self.assertTrue(migrated_job_colors)
            for tool_id, damage, legacy_color, unit in migrated_job_colors:
                self.assertEqual(
                    job_risk_color(tool_id, damage, unit or "Metric").lower(),
                    legacy_color.lower(),
                )
            with self.assertRaises(sqlite3.IntegrityError):
                existing_job_id = connection.execute(
                    "SELECT job_id FROM JobRiskProfile ORDER BY id LIMIT 1"
                ).fetchone()[0]
                connection.execute(
                    """
                    INSERT INTO JobRiskProfile (
                        job_id, name, version, status, is_current, source_type
                    ) VALUES (?, 'Invalid duplicate current', 2, 'approved', 1, 'expert')
                    """,
                    (existing_job_id,),
                )
            self.assertEqual(
                connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM JobMeasurement legacy
                    JOIN CurrentJobRiskMeasurement current
                      ON current.job_id = legacy.job_id AND current.tool_id = legacy.tool_id
                    WHERE current.total_cumulative_damage IS legacy.total_cumulative_damage
                      AND current.probability_outcome IS legacy.probability_outcome
                    """
                ).fetchone()[0],
                connection.execute("SELECT COUNT(*) FROM JobMeasurement").fetchone()[0],
            )


class NewProjectTemplateTests(unittest.TestCase):
    def test_template_is_born_at_the_current_schema(self):
        template = REPOSITORY_ROOT / "data" / "ergotools_data.db"
        self.assertTrue(template.is_file())
        with sqlite3.connect(template) as connection:
            self.assertEqual(
                connection.execute("PRAGMA user_version").fetchone()[0],
                LATEST_SCHEMA_VERSION,
            )
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
            history = connection.execute(
                "SELECT version FROM SchemaMigration ORDER BY version"
            ).fetchall()
            self.assertEqual(
                [version for (version,) in history],
                list(range(1, LATEST_SCHEMA_VERSION + 1)),
            )

        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        project_database = Path(temporary_directory.name) / "new-project.db"
        shutil.copy2(template, project_database)
        result = migrate_database(project_database)
        self.assertEqual(result.applied_versions, ())
        self.assertIsNone(result.backup)


if __name__ == "__main__":
    unittest.main()

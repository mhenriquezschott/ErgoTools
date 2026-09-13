import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from database import connect_database
from job_risk_repository import (
    JobRiskProfileError,
    approve_profile,
    create_draft_profile,
    current_measurements,
    format_job_risk_issues,
    job_risk_issues,
    job_profiles,
    jobs_for_tool,
    make_profile_current,
    profile_measurements,
    retire_profile,
    save_draft_profile,
    save_job_with_measurements,
)
from risk_colors import job_risk_color
from schema_migrations import migrate_database


class JobRiskRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "jobs.db"
        with sqlite3.connect(self.database_path) as connection:
            connection.executescript(
                """
                CREATE TABLE Worker (id TEXT PRIMARY KEY);
                CREATE TABLE Plant (name TEXT PRIMARY KEY);
                CREATE TABLE Shift (id TEXT PRIMARY KEY);
                CREATE TABLE ErgoTool (id TEXT PRIMARY KEY);
                INSERT INTO ErgoTool VALUES ('LiFFT');
                INSERT INTO ErgoTool VALUES ('DUET');
                INSERT INTO ErgoTool VALUES ('ST');
                """
            )
        migrate_database(self.database_path)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_save_creates_current_profile_and_legacy_compatibility_rows(self):
        connection = connect_database(self.database_path)
        try:
            profile_id = save_job_with_measurements(
                connection,
                job_id="J-1",
                name="Case packing",
                description="Packing finished units",
                measurements=(
                    {
                        "tool_id": "LiFFT",
                        "total_cumulative_damage": 0.25,
                        "probability_outcome": 30.0,
                        "unit": "Metric",
                    },
                    {
                        "tool_id": "DUET",
                        "total_cumulative_damage": 0.5,
                        "probability_outcome": 50.0,
                        "unit": "Metric",
                    },
                ),
            )
            connection.commit()

            profile = connection.execute(
                """
                SELECT id, version, status, is_current, source_type
                FROM JobRiskProfile WHERE job_id = 'J-1'
                """
            ).fetchone()
            self.assertEqual(profile, (profile_id, 1, "approved", 1, "expert"))
            self.assertEqual(current_measurements(connection, "J-1")["LiFFT"]["unit"], "Metric")
            jobs = jobs_for_tool(connection, "LiFFT")
            self.assertEqual(jobs[0]["id"], "J-1")
            self.assertEqual(jobs[0]["color"], job_risk_color("LiFFT", 0.25, "Metric"))
            self.assertEqual(
                connection.execute(
                    "SELECT probability_outcome FROM JobMeasurement WHERE job_id='J-1' AND tool_id='LiFFT'"
                ).fetchone()[0],
                30.0,
            )
        finally:
            connection.close()

    def test_editing_imported_profile_preserves_it_as_retired_history(self):
        connection = connect_database(self.database_path)
        try:
            connection.execute(
                "INSERT INTO Job (id, name, description) VALUES ('J-2', 'Legacy', '')"
            )
            connection.execute(
                """
                INSERT INTO JobRiskProfile (
                    job_id, name, version, status, is_current, source_type
                ) VALUES ('J-2', 'Imported baseline', 1, 'approved', 1, 'imported')
                """
            )
            connection.commit()

            save_job_with_measurements(
                connection,
                job_id="J-2",
                name="Edited legacy job",
                description="",
                measurements=(
                    {
                        "tool_id": "ST",
                        "total_cumulative_damage": 0.1,
                        "probability_outcome": 12.0,
                        "unit": "Metric",
                    },
                ),
            )
            connection.commit()

            profiles = connection.execute(
                """
                SELECT version, status, is_current, source_type
                FROM JobRiskProfile WHERE job_id='J-2' ORDER BY version
                """
            ).fetchall()
            self.assertEqual(
                profiles,
                [(1, "retired", 0, "imported"), (2, "approved", 1, "expert")],
            )
        finally:
            connection.close()

    def test_placement_overlap_and_assignment_context_are_enforced(self):
        connection = connect_database(self.database_path)
        try:
            connection.executescript(
                """
                INSERT INTO Worker VALUES ('W-1');
                INSERT INTO Plant VALUES ('P-1');
                INSERT INTO Shift VALUES ('1');
                CREATE TABLE Section (
                    plant_name TEXT NOT NULL,
                    name TEXT NOT NULL,
                    PRIMARY KEY (plant_name, name),
                    FOREIGN KEY (plant_name) REFERENCES Plant(name)
                );
                CREATE TABLE Line (
                    plant_name TEXT NOT NULL,
                    section_name TEXT NOT NULL,
                    name TEXT NOT NULL,
                    PRIMARY KEY (plant_name, section_name, name)
                );
                CREATE TABLE Station (
                    plant_name TEXT NOT NULL,
                    section_name TEXT NOT NULL,
                    line_name TEXT NOT NULL,
                    id TEXT NOT NULL,
                    PRIMARY KEY (plant_name, section_name, line_name, id)
                );
                INSERT INTO Section VALUES ('P-1', 'S-1');
                INSERT INTO Line VALUES ('P-1', 'S-1', 'L-1');
                INSERT INTO Station VALUES ('P-1', 'S-1', 'L-1', 'ST-1');
                INSERT INTO Station VALUES ('P-1', 'S-1', 'L-1', 'ST-2');
                INSERT INTO WorkplaceContext (
                    plant_name, section_name, line_name, station_id, shift_id
                ) VALUES ('P-1', 'S-1', 'L-1', 'ST-1', '1');
                INSERT INTO WorkplaceContext (
                    plant_name, section_name, line_name, station_id, shift_id
                ) VALUES ('P-1', 'S-1', 'L-1', 'ST-2', '1');
                INSERT INTO Job (id, name) VALUES ('J-3', 'Placed job');
                """
            )
            contexts = [
                row[0] for row in connection.execute("SELECT id FROM WorkplaceContext ORDER BY id")
            ]
            first_context, second_context = contexts
            placement_id = connection.execute(
                """
                INSERT INTO JobPlacement (
                    job_id, workplace_context_id, valid_from, valid_to
                ) VALUES ('J-3', ?, '2026-01-01', '2026-12-31')
                """,
                (first_context,),
            ).lastrowid
            with self.assertRaisesRegex(sqlite3.IntegrityError, "may not overlap"):
                connection.execute(
                    """
                    INSERT INTO JobPlacement (
                        job_id, workplace_context_id, valid_from, valid_to
                    ) VALUES ('J-3', ?, '2026-06-01', NULL)
                    """,
                    (first_context,),
                )
            with self.assertRaisesRegex(sqlite3.IntegrityError, "contexts must match"):
                connection.execute(
                    """
                    INSERT INTO WorkerAssignment (
                        worker_id, workplace_context_id, job_placement_id
                    ) VALUES ('W-1', ?, ?)
                    """,
                    (second_context, placement_id),
                )
            connection.execute(
                """
                INSERT INTO WorkerAssignment (
                    worker_id, workplace_context_id, job_placement_id
                ) VALUES ('W-1', ?, ?)
                """,
                (first_context, placement_id),
            )
            connection.commit()
        finally:
            connection.close()

    def test_optimizer_validation_reports_exact_missing_job_tool_pairs(self):
        connection = connect_database(self.database_path)
        try:
            save_job_with_measurements(
                connection,
                job_id="Complete",
                name="Complete",
                description="",
                measurements=(
                    {
                        "tool_id": "LiFFT",
                        "total_cumulative_damage": 0.1,
                        "probability_outcome": 20.0,
                        "unit": "Metric",
                    },
                ),
            )
            connection.execute(
                "INSERT INTO Job (id, name) VALUES ('DraftOnly', 'Draft only')"
            )
            connection.execute(
                """
                INSERT INTO JobRiskProfile (
                    job_id, name, version, status, is_current, source_type
                ) VALUES ('DraftOnly', 'Draft', 1, 'draft', 0, 'expert')
                """
            )
            connection.commit()

            issues = job_risk_issues(
                connection,
                ("Complete", "DraftOnly", "MissingJob"),
                ("LiFFT", "DUET"),
            )
            issue_tuples = {
                (issue.job_id, issue.tool_id, issue.reason) for issue in issues
            }
            self.assertEqual(
                issue_tuples,
                {
                    ("Complete", "DUET", "measurement is not available"),
                    ("DraftOnly", "LiFFT", "no current approved risk profile"),
                    ("DraftOnly", "DUET", "no current approved risk profile"),
                    ("MissingJob", "LiFFT", "job does not exist"),
                    ("MissingJob", "DUET", "job does not exist"),
                },
            )
            message = format_job_risk_issues(issues)
            self.assertIn("Complete - DUET", message)
            self.assertIn("DraftOnly - LiFFT", message)
            self.assertNotIn("Complete - LiFFT", message)
        finally:
            connection.close()

    def test_profile_lifecycle_preserves_approved_history(self):
        connection = connect_database(self.database_path)
        try:
            save_job_with_measurements(
                connection,
                job_id="Lifecycle",
                name="Lifecycle",
                description="",
                measurements=(
                    {
                        "tool_id": "LiFFT",
                        "total_cumulative_damage": 0.01,
                        "probability_outcome": 25.0,
                        "unit": "Metric",
                    },
                ),
            )
            current = job_profiles(connection, "Lifecycle")[0]
            draft_id = create_draft_profile(
                connection,
                "Lifecycle",
                copy_from_profile_id=current["id"],
            )
            copied = profile_measurements(connection, draft_id)
            self.assertEqual(copied["LiFFT"]["probability_outcome"], 25.0)
            save_draft_profile(
                connection,
                draft_id,
                name="Observed 2026 sample",
                source_type="study",
                source_reference="Study-2026",
                methodology="Observed sample mean",
                sample_size=12,
                assessed_on="2026-09-01",
                valid_from="2026-09-01",
                valid_to=None,
                notes="Reviewed",
                measurements=(
                    {
                        "tool_id": "LiFFT",
                        "total_cumulative_damage": 0.02,
                        "probability_outcome": 30.0,
                        "unit": "Metric",
                    },
                ),
            )
            approve_profile(connection, draft_id)
            profiles = job_profiles(connection, "Lifecycle")
            self.assertEqual(
                [(item["version"], item["status"], item["is_current"]) for item in profiles],
                [(2, "approved", 1), (1, "approved", 0)],
            )
            make_profile_current(connection, current["id"])
            self.assertEqual(job_profiles(connection, "Lifecycle")[1]["is_current"], 1)
            retire_profile(connection, current["id"])
            self.assertEqual(job_profiles(connection, "Lifecycle")[1]["status"], "retired")
            self.assertEqual(
                job_risk_issues(connection, ("Lifecycle",), ("LiFFT",))[0].reason,
                "no current approved risk profile",
            )
            with self.assertRaisesRegex(JobRiskProfileError, "Only a draft"):
                approve_profile(connection, draft_id)
        finally:
            connection.close()

    def test_empty_draft_cannot_be_approved(self):
        connection = connect_database(self.database_path)
        try:
            connection.execute("INSERT INTO Job (id, name) VALUES ('Empty', 'Empty')")
            draft_id = create_draft_profile(connection, "Empty")
            with self.assertRaisesRegex(JobRiskProfileError, "At least one complete"):
                approve_profile(connection, draft_id)
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()

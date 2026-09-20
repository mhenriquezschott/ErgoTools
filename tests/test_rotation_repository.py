import shutil
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC))

from database import connect_database
from rotation_repository import (
    available_scope_contexts,
    load_rotation_scheme,
    missing_target_measurements,
    rotation_targets,
    rotation_workers,
    save_rotation_scheme,
    target_measurements,
)
from schema_migrations import migrate_database


class RotationRepositoryTests(unittest.TestCase):
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
        self.database_path = Path(self.temporary_directory.name) / "rotation-copy.db"
        shutil.copy2(self.fixture, self.database_path)
        migrate_database(self.database_path, create_backup=False)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_legacy_rotations_are_unscoped_and_keep_exact_assignments(self):
        with closing(connect_database(self.database_path, row_factory=sqlite3.Row)) as connection:
            scheme = load_rotation_scheme(connection, "Large01_10x8")
            self.assertIsNotNone(scheme)
            self.assertEqual(scheme["context_ids"], [])
            self.assertEqual(len(scheme["assignments"]), 80)
            self.assertTrue(all(row["profile_id"] for row in scheme["assignments"]))
            self.assertTrue(all(row["job_placement_id"] is None for row in scheme["assignments"]))
            self.assertTrue(all(row["worker_assignment_id"] is None for row in scheme["assignments"]))

    def test_scoped_pool_uses_active_job_and_worker_assignments(self):
        with closing(connect_database(self.database_path, row_factory=sqlite3.Row)) as connection:
            contexts = available_scope_contexts(connection)
            self.assertTrue(contexts)
            context_id = next(
                context["id"]
                for context in contexts
                if rotation_workers(connection, [context["id"]])
            )
            workers = rotation_workers(connection, [context_id])
            targets = rotation_targets(connection, [context_id])
            self.assertTrue(workers)
            self.assertTrue(targets)
            self.assertTrue(all(worker.worker_assignment_id is not None for worker in workers))
            self.assertTrue(all(target.job_placement_id is not None for target in targets))
            self.assertTrue(all(target.context_id == context_id for target in targets))

    def test_scoped_scheme_freezes_profile_and_assignment_provenance(self):
        with closing(connect_database(self.database_path, row_factory=sqlite3.Row)) as connection:
            contexts = available_scope_contexts(connection)
            selected = None
            for context in contexts:
                workers = rotation_workers(connection, [context["id"]])
                targets = rotation_targets(connection, [context["id"]])
                if workers and targets:
                    selected = context["id"], workers[0], targets[0]
                    break
            self.assertIsNotNone(selected)
            context_id, worker, target = selected
            save_rotation_scheme(
                connection,
                scheme_id="Scoped-Test",
                name="Scoped Test",
                description="Repository test",
                num_workers=1,
                num_timeblocks=1,
                optimization_mode="single_tool",
                primary_tool_id="LiFFT",
                context_ids=[context_id],
                assignments=[
                    {
                        "block_index": 0,
                        "worker_id": worker.worker_id,
                        "worker_assignment_id": worker.worker_assignment_id,
                        "job_id": target.job_id,
                        "job_placement_id": target.job_placement_id,
                        "profile_id": target.profile_id,
                    }
                ],
            )
            connection.commit()

            loaded = load_rotation_scheme(connection, "Scoped-Test")
            self.assertEqual(loaded["context_ids"], [context_id])
            assignment = loaded["assignments"][0]
            self.assertEqual(assignment["worker_assignment_id"], worker.worker_assignment_id)
            self.assertEqual(assignment["job_placement_id"], target.job_placement_id)
            self.assertEqual(assignment["profile_id"], target.profile_id)

            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    """
                    UPDATE RotationTarget
                    SET job_risk_profile_id = (
                        SELECT id FROM JobRiskProfile
                        WHERE job_id != ? LIMIT 1
                    )
                    WHERE id = ?
                    """,
                    (target.job_id, assignment["rotation_target_id"]),
                )

    def test_measurement_preflight_reports_missing_tools_instead_of_zero(self):
        with closing(connect_database(self.database_path)) as connection:
            targets = rotation_targets(connection)
            self.assertTrue(targets)
            measurements = target_measurements(connection, targets)
            self.assertIn("LiFFT", measurements[targets[0].key])
            missing = missing_target_measurements(
                connection,
                targets,
                ("LiFFT", "DUET", "ST", "UnknownTool"),
            )
            self.assertEqual(len(missing), len(targets))
            self.assertTrue(all(tool_id == "UnknownTool" for _, tool_id in missing))


if __name__ == "__main__":
    unittest.main()

import importlib.util
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "fuse_test_projects", ROOT / "scripts" / "fuse_test_projects.py"
)
FUSION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FUSION)


class FuseTestProjectsTests(unittest.TestCase):
    def test_fuses_plot_and_jrot_projects_without_broken_references(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "Integrated.ergprj"
            FUSION.fuse_projects(
                ROOT / "tests" / "test3.ergprj",
                ROOT / "tests" / "JROT_EpiSalmonTestStudy01.ergprj",
                output,
                "Integrated Test",
            )

            database = output.parent / "Integrated_data" / "Integrated_data.db"
            with closing(sqlite3.connect(database)) as connection:
                expected_counts = {
                    "Worker": 27,
                    "WorkerStationShiftErgoTool": 191,
                    "Job": 11,
                    "JobMeasurement": 33,
                    "RotationScheme": 5,
                    "RotationAssignment": 182,
                }
                actual_counts = {
                    table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                    for table in expected_counts
                }
                self.assertEqual(actual_counts, expected_counts)
                self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
                image_paths = [
                    row[0]
                    for row in connection.execute(
                        "SELECT image_path FROM Plant WHERE image_path IS NOT NULL"
                    )
                ]
                self.assertTrue(image_paths)
                self.assertTrue(
                    all(path.startswith("Integrated_images/") for path in image_paths)
                )

            self.assertEqual(len(list((output.parent / "Integrated_images").iterdir())), 4)


if __name__ == "__main__":
    unittest.main()

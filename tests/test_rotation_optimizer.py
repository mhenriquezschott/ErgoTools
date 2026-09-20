import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rotation_optimizer import (
    RotationOptimizationError,
    optimize_all_tools,
    optimize_single_tool,
)


class RotationOptimizerTests(unittest.TestCase):
    def setUp(self):
        self.workers = ["W1", "W2"]
        self.current = {
            "W1": ["J-high", "J-low"],
            "W2": ["J-low", "J-high"],
        }

    def test_single_tool_keeps_job_totals_and_returns_complete_schedule(self):
        result = optimize_single_tool(
            self.workers,
            self.current,
            {"J-high": 80.0, "J-low": 10.0},
            2,
            10,
        )
        assigned = [job for jobs, _, _ in result.values() for job in jobs]
        self.assertEqual(sorted(assigned), ["J-high", "J-high", "J-low", "J-low"])
        self.assertTrue(all(len(jobs) == 2 for jobs, _, _ in result.values()))

    def test_all_tools_keeps_job_totals_and_uses_only_plain_data(self):
        result = optimize_all_tools(
            self.workers,
            self.current,
            {
                "LiFFT": {"J-high": 80.0, "J-low": 10.0},
                "DUET": {"J-high": 20.0, "J-low": 60.0},
                "ST": {"J-high": 45.0, "J-low": 25.0},
            },
            2,
            10,
        )
        assigned = [job for jobs in result.values() for job in jobs]
        self.assertEqual(sorted(assigned), ["J-high", "J-high", "J-low", "J-low"])

    def test_incomplete_schedule_is_rejected_before_solver(self):
        with self.assertRaises(RotationOptimizationError):
            optimize_single_tool(
                self.workers,
                {"W1": ["J1"], "W2": ["J1", "J1"]},
                {"J1": 10.0},
                2,
                10,
            )


if __name__ == "__main__":
    unittest.main()

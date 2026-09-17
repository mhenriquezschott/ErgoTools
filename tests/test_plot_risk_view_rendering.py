import os
import shutil
import sys
import tempfile
import types
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
sys.path.insert(0, os.path.abspath("src"))

from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QWidget

webengine = types.ModuleType("PyQt5.QtWebEngineWidgets")
webengine.QWebEngineView = QWidget
sys.modules.setdefault("PyQt5.QtWebEngineWidgets", webengine)

from plant_layout import PlantLayoutWindow


class ProjectHost(QWidget):
    def __init__(self, root):
        super().__init__()
        self.projectFileCreated = True
        self.projectdatabasePath = os.path.join(
            root,
            "ErgoTools_ComparativeRiskTest_data",
            "ErgoTools_ComparativeRiskTest_data.db",
        )
        self.projectFolderPath = root
        self.imagesFolder = "ErgoTools_ComparativeRiskTest_images"


class PlotRiskViewRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.project_root = tempfile.TemporaryDirectory()
        shutil.copytree(
            "tests/ErgoTools_ComparativeRiskTest_data",
            os.path.join(cls.project_root.name, "ErgoTools_ComparativeRiskTest_data"),
        )
        shutil.copytree(
            "tests/ErgoTools_ComparativeRiskTest_images",
            os.path.join(cls.project_root.name, "ErgoTools_ComparativeRiskTest_images"),
        )
        cls.host = ProjectHost(cls.project_root.name)
        cls.window = PlantLayoutWindow(cls.host)
        cls.window.resize(1456, 1053)
        cls.window.show()
        cls._settle(350)

    @classmethod
    def tearDownClass(cls):
        cls.window.close()
        cls.host.close()
        cls.project_root.cleanup()

    @classmethod
    def _settle(cls, delay=80):
        for _ in range(10):
            cls.app.processEvents()
        QTest.qWait(delay)
        cls.app.processEvents()

    def test_job_view_uses_readable_per_job_chart_and_safe_marker_bounds(self):
        self.window.selectRiskViewMode("job")
        self._settle()

        records = self.window.job_risk_marker_dataset
        self.assertEqual(len(self.window.visual_job_markers), len(records))
        available_jobs = {
            record["job_id"]
            for record in records
            if record.get("probability_outcome") is not None
        }
        axis = self.window.current_plot_figure.axes[0]
        self.assertEqual(axis.get_title(), "Job Risk by Placed Job")
        self.assertEqual(axis._ergotools_value_axis, "x")
        self.assertEqual(len(axis.patches), len(available_jobs))
        self.assertEqual(len(axis.get_yticklabels()), len(available_jobs))
        self.assertTrue(all(label.get_rotation() == 0 for label in axis.get_yticklabels()))
        self.assertTrue(all("(" in label.get_text() for label in axis.get_yticklabels()))

        marker = self.window.visual_job_markers[0]
        marker_rect = marker._markerRect()
        selection_gap = max(3.0, 3.0 * marker.internal_scale)
        selection_rect = marker_rect.adjusted(
            -selection_gap, -selection_gap, selection_gap, selection_gap
        )
        self.assertTrue(marker.boundingRect().contains(selection_rect))
        self.assertIn(marker.job_id.removeprefix("Job-"), marker.job_id)

    def test_comparison_view_nests_worker_inside_job_square(self):
        self.window.selectRiskViewMode("comparison")
        self._settle()

        self.assertEqual(self.window.outcome_result_stack.currentIndex(), 1)
        self.assertEqual(self.window.outcome_ranges_panel.width(), 250)
        self.assertEqual(self.window.outcome_result_stack.width(), 410)
        self.assertEqual(self.window.outcome_range_labels[0].property("compact"), True)
        enabled_workers = [
            worker
            for worker in self.window.workerstationshifttool_dataset
            if worker.get("enable", 0) == 1
        ]
        expected_individual = sum(
            float(worker["probability_outcome"]) for worker in enabled_workers
        ) / len(enabled_workers)
        applicable_job_risks = [
            float(worker["job_probability_outcome"])
            for worker in enabled_workers
            if worker.get("job_probability_outcome") is not None
        ]
        expected_job = sum(applicable_job_risks) / len(applicable_job_risks)
        self.assertTrue(self.window.comparison_individual_gauge.has_value)
        self.assertTrue(self.window.comparison_job_gauge.has_value)
        self.assertAlmostEqual(
            self.window.comparison_individual_gauge.target_value,
            expected_individual,
        )
        self.assertAlmostEqual(
            self.window.comparison_job_gauge.target_value,
            expected_job,
        )

        worker = self.window.visual_worker_tools[0]
        base_rect = worker._baseMarkerRect(worker.x, worker.y)
        individual_rect = worker._workerMarkerRect(worker.x, worker.y)
        self.assertLess(individual_rect.width(), base_rect.width())
        self.assertLess(individual_rect.height(), base_rect.height())
        self.assertAlmostEqual(individual_rect.center().x(), base_rect.center().x())
        self.assertAlmostEqual(individual_rect.center().y(), base_rect.center().y())
        self.assertNotEqual(worker.item.pen().style(), Qt.NoPen)

        selection_gap = max(2.0, 2.0 * float(worker.sfi))
        selection_rect = base_rect.adjusted(
            -selection_gap, -selection_gap, selection_gap, selection_gap
        )
        self.assertTrue(worker.boundingRect().contains(selection_rect))

        self.window.selectRiskViewMode("individual")
        self._settle()
        self.assertEqual(self.window.outcome_result_stack.currentIndex(), 0)
        self.assertEqual(self.window.outcome_ranges_panel.width(), 300)
        self.assertEqual(self.window.outcome_result_stack.width(), 360)
        self.assertEqual(self.window.outcome_range_labels[0].property("compact"), False)
        self.assertGreaterEqual(self.window.plot_risk_gauge.width(), 250)


if __name__ == "__main__":
    unittest.main()

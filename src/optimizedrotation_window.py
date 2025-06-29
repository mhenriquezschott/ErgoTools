from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt

class OptimizedRotationWindow(QtWidgets.QDialog):
    """
    Displays the optimized rotation in a table format.
    """

    def __init__(self, optimized_result, job_info, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Optimized Rotation Table")
        self.resize(1000, 600)

        self.optimized_result = optimized_result  # Dict[worker_id] = (job_list, risk_list, avg)
        self.job_info = job_info  # Dict[job_id] = {prob, color, name, tool, damage}
        self.initUI()

    def initUI(self):
        layout = QtWidgets.QVBoxLayout(self)
        table = QtWidgets.QTableWidget(self)
        layout.addWidget(table)

        n_workers = len(self.optimized_result)
        n_blocks = len(next(iter(self.optimized_result.values()))[0])  # From job list
        headers = ["Worker"] + [f"Time-Block {i + 1}" for i in range(n_blocks)] + ["Avg."]

        table.setColumnCount(len(headers))
        table.setRowCount(n_workers)
        table.setHorizontalHeaderLabels(headers)

        bold_font = QFont()
        bold_font.setBold(True)
        for c in range(table.columnCount()):
            table.horizontalHeaderItem(c).setFont(bold_font)

        for row_idx, (worker_id, (jobs, risks, avg)) in enumerate(self.optimized_result.items()):
            table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(worker_id))
            total_rgb = []

            for col_idx, (job_id, risk_val) in enumerate(zip(jobs, risks), start=1):
                job_data = self.job_info.get(job_id, {})
                item = QtWidgets.QTableWidgetItem(f"{job_id}\n{risk_val:.1f}%")
                item.setTextAlignment(Qt.AlignCenter)
                tooltip = f"{job_data.get('tool', '')} – {job_data.get('name', '')} ({job_data.get('damage', '')})"
                item.setToolTip(tooltip)

                color = QColor(job_data.get("color", "#ffffff"))
                item.setBackground(color)
                total_rgb.append((color.red(), color.green(), color.blue()))
                table.setItem(row_idx, col_idx, item)

            avg_item = QtWidgets.QTableWidgetItem(f"{avg:.1f}%")
            avg_item.setTextAlignment(Qt.AlignCenter)

            if total_rgb:
                r_avg = sum(c[0] for c in total_rgb) // len(total_rgb)
                g_avg = sum(c[1] for c in total_rgb) // len(total_rgb)
                b_avg = sum(c[2] for c in total_rgb) // len(total_rgb)
                avg_item.setBackground(QColor(r_avg, g_avg, b_avg))

            table.setItem(row_idx, table.columnCount() - 1, avg_item)

        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        table.horizontalHeader().setStretchLastSection(True)
        self.table = table


from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt

class CompareRotationWindow(QtWidgets.QDialog):
    def __init__(self, current_assignments, optimized_assignments, worker_ids,
                 timeblocks, get_jobs_func, tool_selected, tools_to_compare, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rotation Comparison (Non-Optimized Tools)")
        self.resize(1300, 900)
        #self.setModal(True)
        self.setWindowFlags(Qt.Window)  # Allow normal window behavior

        self.current_assignments = current_assignments
        self.optimized_assignments = optimized_assignments
        self.worker_ids = worker_ids
        self.num_blocks = int(timeblocks)
        self.get_jobs_func = get_jobs_func
        self.tool_selected = tool_selected
        self.tools_to_compare = tools_to_compare

        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.renderComparisonGrids()
        #self.renderSummaryStats()  # Optional summary

    def renderComparisonGrids(self):
        for tool in self.tools_to_compare:
            job_info = {
                j["id"]: {
                    "prob": j["probability_outcome"],
                    "color": j["color"],
                    "name": j.get("name", ""),
                    "tool": j.get("tool_id", ""),
                    "damage": j.get("total_cumulative_damage", "")
                } for j in self.get_jobs_func(tool)
            }

            section = QtWidgets.QWidget()
            section_layout = QtWidgets.QHBoxLayout(section)

            #current_table = self.buildTable(tool, self.current_assignments, job_info, is_optimized=False)
            #optimized_table = self.buildTable(tool, self.optimized_assignments, job_info, is_optimized=True)
            current_table = self.buildTable(tool, self.current_assignments, job_info, is_optimized=False)
            optimized_table = self.buildTable(tool, self.optimized_assignments, job_info, is_optimized=True, main_tool=self.tool_selected)


            section_layout.addWidget(current_table)
            section_layout.addWidget(optimized_table)
            self.main_layout.addWidget(section)

    #def buildTable(self, tool, assignment_dict, job_info, is_optimized):
    def buildTable(self, tool, assignment_dict, job_info, is_optimized, main_tool=None):

        #label = QtWidgets.QLabel(f"{'Optimized Rotation Applied to' if is_optimized else 'Current Rotation for'} {tool}")
        if is_optimized and main_tool:
            label_text = f"{main_tool} Optimized Rotation Applied to {tool}"
        else:
            label_text = f"Current Rotation for {tool}"
        label = QtWidgets.QLabel(label_text)

        label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        label.setFont(font)

        table = QtWidgets.QTableWidget()
        table.setRowCount(len(self.worker_ids))
        table.setColumnCount(self.num_blocks + 2)
        headers = ["Worker"] + [f"Time-Block\n{i+1}" for i in range(self.num_blocks)] + ["Avg."]
        table.setHorizontalHeaderLabels(headers)

        header = table.horizontalHeader()
        bold_font = QFont()
        bold_font.setBold(True)
        for c in range(table.columnCount()):
            table.horizontalHeaderItem(c).setFont(bold_font)
        table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)

        table.setColumnWidth(0, 80)
        for c in range(1, self.num_blocks + 1):
            table.setColumnWidth(c, 100)
        table.setColumnWidth(self.num_blocks + 1, 100)
        table.verticalHeader().setDefaultSectionSize(50)

        for row, wid in enumerate(self.worker_ids):
            table.setItem(row, 0, QtWidgets.QTableWidgetItem(wid))
            total_probs = []
            total_colors = []

            for b in range(self.num_blocks):
                job_id = assignment_dict[wid][b] if wid in assignment_dict and b < len(assignment_dict[wid]) else ""
                job = job_info.get(job_id, {})
                prob = job.get("prob", 0.0)
                color = job.get("color", "#ffffff")

                item = QtWidgets.QTableWidgetItem(f"{job_id}\n{prob:.1f}%")
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(QColor(color))
                item.setToolTip(f"{job.get('tool', '')} – {job.get('name', '')} ({job.get('damage', '')})")
                table.setItem(row, b + 1, item)

                total_probs.append(prob)
                c = QColor(color)
                total_colors.append((c.red(), c.green(), c.blue()))

            # Average column
            avg_val = round(sum(total_probs) / len(total_probs), 1) if total_probs else 0.0
            avg_item = QtWidgets.QTableWidgetItem(f"{avg_val:.1f}%")
            avg_item.setTextAlignment(Qt.AlignCenter)

            if total_colors:
                r = sum(c[0] for c in total_colors) // len(total_colors)
                g = sum(c[1] for c in total_colors) // len(total_colors)
                b = sum(c[2] for c in total_colors) // len(total_colors)
                avg_item.setBackground(QColor(r, g, b))

            table.setItem(row, self.num_blocks + 1, avg_item)

        wrapper = QtWidgets.QVBoxLayout()
        container = QtWidgets.QWidget()
        wrapper.addWidget(label)
        wrapper.addWidget(table)
        container.setLayout(wrapper)
        return container

    # Optional feature
    #def renderSummaryStats(self):
    #    stats = QLabel("← Add average risk deltas here for each tool →")
    #    stats.setAlignment(Qt.AlignCenter)
    #    stats.setStyleSheet("font-weight: bold; padding: 10px;")
    #    self.main_layout.addWidget(stats)


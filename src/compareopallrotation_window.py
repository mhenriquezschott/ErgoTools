from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt

class CompareOpAllRotationWindow(QtWidgets.QDialog):
    def __init__(self, current_assignments, optimized_assignments, worker_ids,
                 timeblocks, get_jobs_func, tools, parent=None):
        super().__init__(parent)
        self.setWindowTitle("All Tools - Optimized vs Current Rotation")
        self.resize(1400, 1000)
        self.setWindowFlags(Qt.Window)

        self.current_assignments = current_assignments
        self.optimized_assignments = optimized_assignments
        self.worker_ids = worker_ids
        self.num_blocks = int(timeblocks)
        self.get_jobs_func = get_jobs_func
        self.tools = tools

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.renderGrids()
        
        # After rendering all tables
        self.transfer_button = QtWidgets.QPushButton("Apply This Optimized Rotation to Current Tool")
        self.transfer_button.setFixedHeight(40)
        self.transfer_button.setStyleSheet("font-weight: bold;")
        self.transfer_button.clicked.connect(self.transferToMainWindow)

        self.main_layout.addWidget(self.transfer_button)
        
        
        

    def renderGrids(self):
        for tool in self.tools:
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

            label_current = QtWidgets.QLabel(f"Current Rotation for {tool}")
            label_optimized = QtWidgets.QLabel(f"Optimized Rotation for {tool}")
            for lbl in (label_current, label_optimized):
                lbl.setAlignment(Qt.AlignCenter)
                fnt = QFont()
                fnt.setBold(True)
                lbl.setFont(fnt)

            current_table = self.buildTable(tool, self.current_assignments, job_info)
            optimized_table = self.buildTable(tool, self.optimized_assignments, job_info)

            layout_current = QtWidgets.QVBoxLayout()
            layout_current.addWidget(label_current)
            layout_current.addWidget(current_table)

            layout_optimized = QtWidgets.QVBoxLayout()
            layout_optimized.addWidget(label_optimized)
            layout_optimized.addWidget(optimized_table)

            section_layout.addLayout(layout_current)
            section_layout.addLayout(layout_optimized)
            self.main_layout.addWidget(section)
            
            
            
            

    def buildTable(self, tool, assignment_dict, job_info):
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

        return table


    def transferToMainWindow(self):
        """
        Finds the optimized rotation for the current tool and copies it
        into the main window's `optimized_table`, then triggers the transfer logic.
        """
        parent = self.parent()
        if parent is None:
            print("[ERROR] No parent found.")
            return
    
        # Step 1: Get current tool from the main rotation window
        current_tool = parent.tool_combo.currentText().strip()
        #print(f"[DEBUG] Current selected tool in main window: '{current_tool}'")
    
        if current_tool not in ["LiFFT", "DUET", "ST"]:
            print("[ERROR] Invalid tool selected.")
            return
    
        # Step 2: Get job info for that tool
        job_data = self.get_jobs_func(current_tool)
        job_info = {
            j["id"]: {
                "prob": j["probability_outcome"],
                "color": j["color"],
                "name": j.get("name", ""),
                "tool": j.get("tool_id", ""),
                "damage": j.get("total_cumulative_damage", "")
            } for j in job_data
        }
    
        # Step 3: Extract optimized jobs for current tool
        if not self.optimized_assignments:
            print("[ERROR] No optimized assignments found.")
            return

        # Build the structure that displayOptimizedTable expects
        optimized_result = {}
        for worker_id, job_list in self.optimized_assignments.items():
            risks = [job_info.get(j, {}).get("prob", 0.0) for j in job_list]
            avg = round(sum(risks) / len(risks), 1) if risks else 0.0
            optimized_result[worker_id] = (job_list, risks, avg)
    
        # Step 4: Display the optimized result in the main window’s optimized_table
        parent.displayOptimizedTable(
            optimized_result=optimized_result,
            job_info=job_info,
            table=parent.optimized_table
        )
    
        # Step 5: Transfer to the main rotation table
        parent.transferOptimizedToCurrent()
        #print(f"[INFO] Transferred optimized rotation for {current_tool}.")
        self.close()


import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

class ZCPWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zoomable Circle Packing View")
        self.resize(1000, 800)
        
        layout = QVBoxLayout(self)
        self.web_view = QWebEngineView(self)
        layout.addWidget(self.web_view)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_file = os.path.join(current_dir, "index.html")
        self.web_view.load(QUrl.fromLocalFile(html_file))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ZCPWindow()
    window.show()
    sys.exit(app.exec_())

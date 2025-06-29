import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("D3 Zoomable Circle Packing")
        self.resize(1000, 800)

        self.web_view = QWebEngineView()
        self.setCentralWidget(self.web_view)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_file = os.path.join(current_dir, "index.html")
        self.web_view.load(QUrl.fromLocalFile(html_file))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


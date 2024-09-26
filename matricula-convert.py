import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from modules.gui.main_window import MainWindow
from modules.logger import Logger

log = Logger()

QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    log.info("Application started.")
    sys.exit(app.exec())

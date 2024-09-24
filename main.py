import sys

from PySide6.QtWidgets import QApplication

from modules.gui.main_window import MainWindow
from modules.logger import Logger

log = Logger()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    log.info("Application started.")
    sys.exit(app.exec())

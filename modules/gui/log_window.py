from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QTextEdit,
    QVBoxLayout,
)

from modules.gui.ui_helper import UIHelper


class LogWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui_helper = UIHelper(self)
        self.setWindowTitle("Conversion Log")

        icon_path = self.ui_helper.get_resource_path("icon.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)
        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        close_button = self.ui_helper.create_button("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

    def append_log(self, message: str):
        self.log_text.append(message)

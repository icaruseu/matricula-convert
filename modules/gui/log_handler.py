import logging
from typing import override

from PySide6.QtWidgets import QTextEdit


class QTextEditLogHandler(logging.Handler):
    def __init__(self, text_edit: QTextEdit):
        super().__init__()
        self.text_edit = text_edit

    @override
    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)
        self.text_edit.append(message)

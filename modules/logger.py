# logger.py
import logging
from datetime import datetime
from typing import override

from PySide6.QtCore import QObject, Signal


class Logger:
    _logger = logging.getLogger("Matricula-Convert Logger")

    def __init__(self):
        if not self._logger.handlers:
            self._logger.setLevel(logging.DEBUG)
            file_handler = logging.FileHandler(
                f"log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
            )
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)

    def add_handler(self, handler: logging.Handler):
        self._logger.addHandler(handler)

    def debug(self, message: str):
        self._logger.debug(message)

    def info(self, message: str):
        self._logger.info(message)

    def warn(self, message: str):
        self._logger.warning(message)

    def error(self, message: str):
        self._logger.error(message)


class LogEmitter(QObject):
    log_signal = Signal(str)


class SignalLogHandler(logging.Handler):
    def __init__(self, emitter: LogEmitter):
        super().__init__()
        self.emitter = emitter

    @override
    def emit(self, record: logging.LogRecord):
        message = self.format(record)
        self.emitter.log_signal.emit(message)

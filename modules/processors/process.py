from PySide6.QtCore import QObject, Signal, Slot

from modules.logger import Logger
from modules.models.matricula_data import MatriculaData
from modules.processors.augias_9_2_processor import Augias92Processor
from modules.processors.augias_x_processor import AugiasXProcessor
from modules.processors.base_processor import BaseProcessor

processors: list[type[BaseProcessor]] = [Augias92Processor, AugiasXProcessor]

log = Logger()


class ProcessorWorker(QObject):
    log_signal = Signal(str)  # Log messages
    initialized = Signal(str)  # Processor name
    progress = Signal(float)  # Processing progress
    finished = Signal(MatriculaData)  # Processing result
    error = Signal(str)  # Error messages
    start_extraction = Signal(str)

    def __init__(self, input_file: str):
        super().__init__()
        self.input_file = input_file
        self.processor: None | BaseProcessor = None
        self.start_extraction.connect(self.extract)

    @Slot()
    def init(self) -> None:
        for processor_class in processors:
            try:
                processor = processor_class(
                    self.input_file, lambda p: self.progress.emit(p)
                )
                log.debug(f"Trying processor: {processor.name}")
                if processor.can_process():
                    log.debug(
                        f"Processor {processor.name} can process {self.input_file}"
                    )
                    self.processor = processor
                    break
                else:
                    log.debug(
                        f"Processor {processor.name} cannot process {self.input_file}"
                    )
            except Exception as e:
                log.error(
                    f"Error processing data using {processor_class.__name__}: {e}"
                )
        if self.processor is None:
            self.error.emit(
                "Unsupported file format or unable to create a valid processor"
            )
        else:
            self.initialized.emit(self.processor.name)

    @Slot(str)
    def extract(self, diocese_id: str) -> None:
        if self.processor is None:
            error_msg = "Processor is not initialized"
            log.error(error_msg)
            self.error.emit(error_msg)
        else:
            try:
                data = self.processor.try_process(diocese_id)
                self.finished.emit(data)
            except Exception as e:
                log.error(f"Error during extraction: {e}")
                self.error.emit(str(e))

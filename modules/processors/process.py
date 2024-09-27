from modules.logger import Logger
from modules.models.matricula_data import MatriculaData
from modules.processors.augias_9_2_processor import Augias92Processor
from modules.processors.augias_x_processor import AugiasXProcessor
from modules.processors.base_processor import BaseProcessor

processors: list[type[BaseProcessor]] = [Augias92Processor, AugiasXProcessor]

log = Logger()


class Processor:
    def __init__(self, input_file: str):
        self.input_file = input_file
        self.processor: None | BaseProcessor = None
        for processor_class in processors:
            # Try to instantiate the processor
            try:
                # Instantiate the processor
                self.processor = processor_class(input_file)
                log.debug(f"Trying processor: {self.processor.name}")
                # Check if the processor can process the input file
                if self.processor.can_process():
                    log.debug(
                        f"Processor {self.processor.name} can process {input_file}"
                    )
                    # Found a valid processor, break the loop
                    break
                else:
                    log.debug(
                        f"Processor {self.processor.name} cannot process {input_file}"
                    )
            # Log any errors
            except Exception as e:
                log.debug(
                    f"Error processing data using {processor_class.__name__}. Error: {e}"
                )
        if self.processor is None:
            raise ValueError(
                "Unsupported file format or unable to create a valid processor"
            )

    def name(self) -> str:
        if self.processor is None:
            raise RuntimeError("Processor is not initialized")
        return self.processor.name

    def extract(self, diocese_id: str) -> None | MatriculaData:
        if self.processor is None:
            raise RuntimeError("Processor is not initialized")
        return self.processor.try_process(diocese_id)

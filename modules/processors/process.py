from modules.logger import Logger
from modules.models.matricula_data import MatriculaData
from modules.processors.augias_9_2_processor import Augias92Processor
from modules.processors.augias_x_processor import AugiasXProcessor
from modules.processors.base_processor import BaseProcessor

processors: list[type[BaseProcessor]] = [Augias92Processor, AugiasXProcessor]

log = Logger()


def process_data(input_file: str, diocese_id: str) -> MatriculaData:
    for processor in processors:
        try:
            processor_instance = processor(input_file, diocese_id)
            data = processor_instance.extract()
            if data:
                return data
        except Exception as e:
            log.debug(f"Error processing data using {processor.__name__}. Error: {e})")

    raise ValueError("Unsupported file format")

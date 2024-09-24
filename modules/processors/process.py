from modules.models.matricula_data import MatriculaData
from modules.processors.augias_9_2_processor import Augias92Processor
from modules.processors.augias_x_processor import AugiasXProcessor


def process_data(input_file: str, diocese_id: str) -> MatriculaData:
    data = None
    augias92 = Augias92Processor(input_file, diocese_id)
    if augias92.success:
        data = augias92.data
    augiasX = AugiasXProcessor(input_file, diocese_id)
    if augiasX.success:
        data = augiasX.data

    if not data:
        raise ValueError("Unsupported file format")

    return data

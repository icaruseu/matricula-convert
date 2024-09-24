from enum import Enum

from modules.models.matricula_data import MatriculaData
from modules.writers.csv_writer import CSVWriter


class OutputVariant(Enum):
    CSV = 1


def write(output_variant: OutputVariant, data: MatriculaData, output_dir: str):
    writer = None
    if output_variant == OutputVariant.CSV:
        writer = CSVWriter
    # Add more writers if needed

    writer(output_dir).write(data)

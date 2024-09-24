from abc import abstractmethod

from modules.models.matricula_data import MatriculaData


class BaseWriter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    @abstractmethod
    def write(self, data: MatriculaData) -> None:
        """Write data to the output file"""
        raise NotImplementedError("Subclasses must implement this method")

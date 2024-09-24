import re
from abc import ABC, abstractmethod

from unidecode import unidecode

from modules.models.matricula_data import MatriculaData


class BaseProcessor(ABC):
    def __init__(self, input_file: str, diocese_id: str):
        self.input_file = input_file
        self.diocese_id = diocese_id
        self.data = self._extract_data()
        self.success = True if self.data else False

    @abstractmethod
    def _extract_data(self) -> None | MatriculaData:
        """Extract data from the input file"""
        raise NotImplementedError("Subclasses must implement this method")

    def _to_ascii(self, text: str) -> str:
        # Convert to ASCII (remove accents, diacritics)
        ascii_text = unidecode(text.lower())
        # Replace non-alphanumeric characters with a hyphen
        ascii_text = re.sub(r"[^\w\s]", "-", ascii_text)
        # Replace whitespace with a hyphen
        ascii_text = re.sub(r"\s+", "-", ascii_text)
        # Collapse multiple hyphens into a single hyphen
        ascii_text = re.sub(r"-+", "-", ascii_text)
        # Remove any leading/trailing hyphens
        ascii_text = ascii_text.strip("-")
        return ascii_text

    def _remove_newlines(self, text: str) -> str:
        return text.replace("\r\n", "").replace("\n", "")

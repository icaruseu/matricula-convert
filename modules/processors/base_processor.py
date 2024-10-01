import os
import re
from abc import ABC, abstractmethod
from typing import Callable

from unidecode import unidecode

from modules.models.matricula_data import MatriculaData
from modules.models.percent import Percent, PercentChangeHandler

type ProgressCallback = Callable[[Percent], None]


class BaseProcessor(ABC):
    name: str
    increment: float

    def __init__(self, input_file: str, on_progress: PercentChangeHandler):
        self.__on_progress = on_progress
        self._percent = Percent(on_change=on_progress)
        self.input_file = input_file
        if not os.path.exists(input_file):
            raise ValueError("Input file does not exist")

    @abstractmethod
    def can_process(self) -> bool:
        """Whether or not to proceed with the processing using this processor"""
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def try_process(self, diocese_id: str) -> None | MatriculaData:
        """Extract data from the input file"""
        raise NotImplementedError("Subclasses must implement this method")

    def _to_simple_ascii(self, text: str) -> str:
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

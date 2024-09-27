from abc import ABC
from typing import override

import pandas as pd
import pypyodbc

from modules.logger import Logger
from modules.processors.base_processor import BaseProcessor

pypyodbc.lowercase = False
log = Logger()

drivers = [
    "Microsoft Access Driver (*.mdb, *.accdb)",
    "Microsoft Access Driver (*.mdb)",
]


class MDBProcessor(BaseProcessor, ABC):
    @override
    def __init__(self, input_file: str):
        super().__init__(input_file)
        if not input_file.endswith(".mdb") and not input_file.endswith(".accdb"):
            raise ValueError("Input file must be an MS Access file (*.mdb, *.accdb)")
        self.connection = None
        for driver in drivers:
            try:
                log.debug(f"Trying driver: {driver}")
                connection_str = f"Driver={{{driver}}};DBQ={self.input_file};"
                connection = pypyodbc.connect(connection_str)
                log.debug(f"Connected successfully using driver: {driver}")
                self.connection = connection
                break
            except pypyodbc.Error as e:
                log.debug(f"Failed to connect with driver: {driver}. Error: {e}")
        if self.connection is None:
            raise ValueError(
                "No suitable driver found or unable to establish a connection."
            )

    def _get_table(self, table: str) -> pd.DataFrame | None:
        if self.connection is None:
            return None
        try:
            cursor = self.connection.cursor()
            log.debug(f"Reading table: {table}")
            query = f"SELECT * FROM [{table}]"
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            # Convert the result to a DataFrame
            return pd.DataFrame.from_records(rows, columns=columns)
        except Exception as e:
            log.debug(f"Error reading table: {table}. Error: {e}")
            return None

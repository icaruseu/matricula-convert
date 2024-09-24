from abc import ABC, abstractmethod
from typing import override

import pandas as pd
import pypyodbc

from modules.logger import Logger
from modules.models.matricula_data import MatriculaData
from modules.processors.base_processor import BaseProcessor

pypyodbc.lowercase = False
log = Logger()

drivers = [
    "Microsoft Access Driver (*.mdb, *.accdb)",
    "Microsoft Access Driver (*.mdb)",
]

type Tables = dict[str, pd.DataFrame]


class MDBProcessor(BaseProcessor, ABC):
    @override
    def __init__(self, input_file: str, diocese_id: str):
        super().__init__(input_file, diocese_id)

    @abstractmethod
    def _extract_from_tables(self, tables: Tables) -> None | MatriculaData:
        raise NotImplementedError("Subclasses must implement this method")

    @override
    def _extract_data(self) -> None | MatriculaData:
        tables = self._read_db()
        if tables:
            return self._extract_from_tables(tables)
        return None

    def _read_db(self) -> Tables | None:
        """
        Connect to an Access database, read all tables, and return a dictionary of DataFrames.
        Logs errors and returns None in case of failure.

        :return: A dictionary where the keys are table names and the values are DataFrames, or None if an error occurs.
        """
        connection = None

        # Try to connect using the available drivers
        for driver in drivers:
            try:
                log.info(f"Trying driver: {driver}")
                connection_str = f"Driver={{{driver}}};DBQ={self.input_file};"
                connection = pypyodbc.connect(connection_str)
                log.info(f"Connected successfully using driver: {driver}")
                break
            except pypyodbc.Error as e:
                log.error(f"Failed to connect with driver: {driver}. Error: {e}")

        if connection is None:
            log.error("No suitable driver found or unable to establish a connection.")
            return None

        # Dictionary to store the DataFrames
        db_dict = {}

        try:
            cursor = connection.cursor()

            # Get a list of all table names in the database
            cursor.tables()
            tables = [row[2] for row in cursor.fetchall() if row[3] == "TABLE"]

            # Iterate over the tables and convert each one to a DataFrame
            for table in tables:
                try:
                    log.info(f"Reading table: {table}")
                    query = f"SELECT * FROM [{table}]"
                    cursor.execute(query)
                    columns = [column[0] for column in cursor.description]
                    rows = cursor.fetchall()

                    # Convert the result to a DataFrame
                    df = pd.DataFrame.from_records(rows, columns=columns)
                    db_dict[table] = df
                except Exception as e:
                    log.error(f"Error reading table: {table}. Error: {e}")
                    return None

        except Exception as e:
            log.error(f"Error fetching table list or reading data. Error: {e}")
            return None

        finally:
            # Clean up the connection
            if connection:
                connection.close()

        return db_dict

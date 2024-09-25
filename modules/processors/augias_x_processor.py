from typing import final, override

from modules.logger import Logger
from modules.models.matricula_data import MatriculaData
from modules.processors.mdb_processor import MDBProcessor

log = Logger()
version_table_name = "DB_VERSION"
version_col_name = "VERSION"


@final
class AugiasXProcessor(MDBProcessor):
    @override
    def _proceed(self) -> bool:
        table = self._get_table(version_table_name)
        if table is None or table.empty:
            return False
        version_column = table[version_col_name]
        if version_column.empty:
            return False
        if version_column.isin([10004]).any():
            version = version_column.iloc[-1].item()
            log.info("Augias X file detected")
            log.debug(f"Augias database version: {version}")
            return True
        return False

    @override
    def _extract_data(self) -> None | MatriculaData:
        pass

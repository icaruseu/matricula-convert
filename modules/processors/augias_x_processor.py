from typing import final, override

import pandas as pd

from modules.models.matricula_data import MatriculaData
from modules.processors.mdb_processor import MDBProcessor


@final
class AugiasXProcessor(MDBProcessor):
    @override
    def _extract_from_tables(
        self, tables: dict[str, pd.DataFrame]
    ) -> None | MatriculaData:
        return None

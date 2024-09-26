from typing import final, override

from modules.logger import Logger
from modules.processors.augias_processor import (
    AugiasProcessor,
    ImageColumns,
    KeyMap,
    ParishColumns,
    RegisterColumns,
)

log = Logger()


@final
class Augias92Processor(AugiasProcessor):
    @override
    def _proceed(self) -> bool:
        table = self._get_table(self.key_map.version_table_name)
        if table is None or table.empty:
            return False
        version_column = table[self.key_map.version_col_name]
        if version_column.empty:
            return False
        if version_column.isin([920]).any():
            version = version_column.iloc[-1].item()
            log.info("Augias 9.2 file detected")
            log.debug(f"Augias file version: {version}")
            return True
        return False

    @override
    def _get_key_map(self) -> KeyMap:
        return KeyMap(
            version_table_name="Version",
            version_col_name="Version",
            parish_table_name="M_Bestaende",
            register_table_name="M_Objekte1",
            imgs_table_name="M_Bilder",
            register_parent_col="B_ID",
            img_parent_col="Ob_Id",
            parish_cols=ParishColumns(
                augias_id="B_ID",
                title="B_Name",
                matricula_identifier="B_intAbk",
                location="B_Umfang",
                parish_church_link="B_IAvorgaenger",
                image_url="B_Nachfolger",
                date_range="B_Vorwort",
                description="B_Bemerkungen",
            ),
            register_cols=RegisterColumns(
                identifier="Ob_ID",
                title="Ob_f20",
                description="Ob_f21",
                comment="Ob_f24",
                archival_identifier="Ob_f2",
                storage_location="Ob_f23",
                microfilm_identifier="Ob_f16",
                date_range="Ob_f3",
                date_start="Ob_f30",
                date_end="Ob_f31",
            ),
            image_cols=ImageColumns(
                augias_id="IM_Id",
                file_path="IM_Pfad",
                label="IM_Name",
                file_name="IM_Dateiname",
            ),
        )

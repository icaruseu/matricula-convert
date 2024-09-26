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
class AugiasXProcessor(AugiasProcessor):
    @override
    def _proceed(self) -> bool:
        table = self._get_table(self.key_map.version_table_name)
        if table is None or table.empty:
            return False
        version_column = table[self.key_map.version_col_name]
        if version_column.empty:
            return False
        if version_column.isin([10004]).any():
            version = version_column.iloc[-1].item()
            log.info("Augias X file detected")
            log.debug(f"Augias database version: {version}")
            return True
        return False

    @override
    def _get_key_map(self) -> KeyMap:
        return KeyMap(
            version_table_name="DB_VERSION",
            version_col_name="VERSION",
            parish_table_name="M_BESTAENDE",
            register_table_name="M_OBJEKTE1",
            imgs_table_name="M_BILDER",
            register_parent_col="B_ID",
            img_parent_col="CHILD_ID",
            parish_cols=ParishColumns(
                augias_id="B_ID",
                title="B_NAME",
                matricula_identifier="B_INTABK",
                location="B_UMFANG",
                parish_church_link="B_IAVORGAENGER",
                image_url="B_NACHFOLGER",
                date_range="B_VORWORT",
                description="B_BEMERKUNGEN",
            ),
            register_cols=RegisterColumns(
                identifier="OB_ID",
                title="OB_F20",
                description="OB_F21",
                comment="OB_F24",
                archival_identifier="OB_F2",
                storage_location="OB_F23",
                microfilm_identifier="OB_F16",
                date_range="OB_F3",
                date_start="OB_F30",
                date_end="OB_F31",
            ),
            image_cols=ImageColumns(
                augias_id="IM_ID",
                file_path="IM_PFAD",
                label="IM_NAME",
                file_name="IM_DATEINAME",
            ),
        )

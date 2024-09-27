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
    name = "Augias 9.2"

    @override
    def _get_key_map(self) -> KeyMap:
        return KeyMap(
            valid_versions=[920],
            correct_version_message="Augias 9.2 file detected",
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

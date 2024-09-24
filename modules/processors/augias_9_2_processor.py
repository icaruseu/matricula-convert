import os
from typing import final, override

import pandas as pd

from modules.logger import Logger
from modules.models.image import Image
from modules.models.matricula_data import MatriculaData
from modules.models.parish import Parish
from modules.models.register import Register
from modules.processors.mdb_processor import MDBProcessor, Tables

log = Logger()

version_table_name = "Version"
version_col_name = "Version"
parish_table_name = "M_Bestaende"
register_table_name = "M_Objekte1"
register_table_imgs = "M_Bilder"


@final
class Augias92Processor(MDBProcessor):
    @override
    def _extract_from_tables(self, tables: Tables) -> None | MatriculaData:
        version = self._extract_version(tables)
        if version is not None:
            log.info("Augias 9.2 file detected")
            log.debug(f"Augias file version: {version}")
        dfs = self._get_relevant_tables(tables)
        if dfs is None:
            log.error("Could not extract relevant tables from MDB file")
            return None
        parishes_df, registers_df, imgs_df = dfs
        parishes = self._extract_parishes(parishes_df, self.diocese_id)
        registers: list[Register] = []
        images: list[Image] = []
        for parish in parishes:
            parish_registers_df = registers_df[registers_df["B_ID"] == parish.augias_id]
            parish_registers = self._extract_registers(
                parish_registers_df, self.diocese_id, parish.identifier
            )
            registers.extend(parish_registers)
            for register in parish_registers:
                register_imgs_df = imgs_df[imgs_df["Ob_Id"] == register.augias_id]
                register_images = self._extract_images(
                    register_imgs_df,
                    self.diocese_id,
                    parish.identifier,
                    register.archival_identifier,
                )
                images.extend(register_images)
                if len(register_images) > 0:
                    first_img = register_images[0]
                    image_dir_path = first_img.file_path.replace(
                        first_img.file_name, ""
                    )
                    register.image_dir_path = image_dir_path
        return MatriculaData(parishes=parishes, registers=registers, images=images)

    def _get_relevant_tables(
        self, tables: Tables
    ) -> None | tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        parishes = tables.get(parish_table_name)
        if parishes is None:
            log.error(f"Table {parish_table_name} not found in MDB file")
        registers = tables.get(register_table_name)
        if registers is None:
            log.error(f"Table {register_table_name} not found in MDB file")
        images = tables.get(register_table_imgs)
        if images is None:
            log.error(f"Table {register_table_imgs} not found in MDB file")
        if parishes is None or registers is None or images is None:
            return None
        else:
            return parishes, registers, images

    def _extract_version(self, tables: Tables) -> int | None:
        table = tables.get(version_table_name)
        if table is None or table.empty:
            return None
        version_column = table[version_col_name]
        if version_column.empty:
            return None
        if version_column.isin([920]).any():
            return version_column.iloc[-1].item()
        return None

    def _extract_parishes(self, df: pd.DataFrame, diocese_key: str) -> list[Parish]:
        columns_to_keep = {
            "B_ID": "augias_id",
            "B_Name": "title",
            "B_intAbk": "matricula_identifier",
            "B_Umfang": "location",
            "B_IAvorgaenger": "parish_church_link",
            "B_Nachfolger": "image_url",
            "B_Vorwort": "date_range",
            "B_Bemerkungen": "description",
            "B_DatVon": "date_start",
            "B_DatBis": "date_end",
        }
        df = df[columns_to_keep.keys()].rename(columns=columns_to_keep)
        df = df.sort_values(by="augias_id")
        df["identifier"] = df["title"].apply(self._to_ascii)
        df["parish_church"] = df["title"]
        df["date_range"] = df["date_range"].apply(self._wrap_in_p)
        df["description"] = df["description"].apply(lambda d: d if d else None)
        df["location"] = df["location"].apply(self._coord_to_point)
        self._b_ids = dict(zip(df["augias_id"], df["identifier"]))
        parishes = []
        for _, row in df.iterrows():
            parish = Parish(
                augias_id=row["augias_id"],
                identifier=row["identifier"],
                title=row["title"],
                matricula_identifier=row["matricula_identifier"],
                location=row["location"],
                parish_church_link=row["parish_church_link"],
                image_url=row["image_url"],
                date_range=row["date_range"],
                description=row["description"],
                date_start=row["date_start"],
                date_end=row["date_end"],
                diocese=f'["{diocese_key}"]',
                parish_church=row["parish_church"],
            )
            parishes.append(parish)
        return parishes

    def _extract_registers(
        self, df: pd.DataFrame, diocese_key: str, parish_key: str
    ) -> list[Register]:
        columns_to_keep = {
            "Ob_ID": "identifier",
            "Ob_f20": "title",
            "Ob_f21": "description",
            "Ob_f24": "comment",
            "Ob_f2": "archival_identifier",
            "Ob_f23": "storage_location",
            "Ob_f16": "microfilm_identifier",
            "Ob_f3": "date_range",
            "Ob_f30": "date_start",
            "Ob_f31": "date_end",
        }
        df = df[columns_to_keep.keys()].rename(columns=columns_to_keep)
        df = df.sort_values(by="identifier")
        df["title"] = df["title"].apply(self._remove_newlines)
        df["type"] = df["title"].apply(self._extract_types)
        df["description"] = df["description"].apply(self._wrap_in_p)
        df["comment"] = df["comment"].apply(self._wrap_in_p)
        df["date_start"] = df["date_start"].apply(self.format_date)
        df["date_end"] = df["date_end"].apply(self.format_date)
        df["ordering"] = range(1, len(df) + 1)
        registers = []
        for _, row in df.iterrows():
            register = Register(
                augias_id=row["identifier"],
                identifier=row["identifier"],
                title=row["title"],
                register_type=row["type"],
                description=row["description"],
                comment=row["comment"],
                archival_identifier=row["archival_identifier"],
                storage_location=row["storage_location"],
                microfilm_identifier=row["microfilm_identifier"],
                date_range=row["date_range"],
                date_start=row["date_start"],
                date_end=row["date_end"],
                parish=f'["{diocese_key}", "{parish_key}", true]',
                image_dir_path=None,
                ordering=row["ordering"],
            )
            registers.append(register)
        return registers

    def _extract_types(self, title: str) -> str:
        types: list[str] = []
        if "index" in title.lower():
            types.append("Index")
        if "sterb" in title.lower():
            types.append("Sterben")
        if "tauf" in title.lower():
            types.append("Taufen")
        if "trauu" in title.lower():
            types.append("Trauungen")
        return " - ".join(types) if types else title

    def _extract_images(
        self, df: pd.DataFrame, diocese_key: str, parish_key: str, register_key: str
    ) -> list[Image]:
        columns_to_keep = {
            "IM_Id": "augias_id",
            "IM_Pfad": "file_path",
            "IM_Name": "label",
            "IM_Dateiname": "file_name",
        }
        df = df[columns_to_keep.keys()].rename(columns=columns_to_keep)
        df = df.sort_values(by="augias_id")
        df["order"] = range(1, len(df) + 1)
        images = []
        for _, row in df.iterrows():
            image = Image(
                augias_id=row["augias_id"],
                parish=f'["{diocese_key}", "{parish_key}", true]',
                register=f'["{diocese_key}", "{parish_key}", true, "{register_key}"]',
                file_path=row["file_path"],
                label=row["label"],
                file_name=row["file_name"],
                order=None,  # Is empty in the example file even though it would be easy (see col order in df)
            )
            images.append(image)
        return images

    def _coord_to_point(self, coord: str) -> str:
        lat, lon = coord.split(", ")
        return f"SRID=4326;POINT ({lon} {lat})"

    def _wrap_in_p(self, text: None | str) -> None | str:
        if not text or text.strip() == "":
            return None
        return f"<p>{text}</p>"

    def format_date(self, x: float) -> None | str:
        date = (
            str(int(x))
            if isinstance(x, float) and not pd.isnull(x)
            else str(x)
            if not pd.isnull(x)
            else ""
        )
        if not date:
            return
        return f"{date[:4]}-{date[4:6]}-{date[6:]}"

    def _common_path_prefix(self, paths: pd.Series) -> str:
        return os.path.commonpath(paths.tolist())  # Convert Series to list

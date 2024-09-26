from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import final, override

import pandas as pd

from modules.logger import Logger
from modules.models.image import Image
from modules.models.matricula_data import MatriculaData
from modules.models.parish import Parish
from modules.models.register import Register
from modules.processors.mdb_processor import MDBProcessor

log = Logger()
version_table_name = "DB_VERSION"
version_col_name = "VERSION"
parish_table_name = "M_BESTAENDE"
register_table_name = "M_OBJEKTE1"
register_table_imgs = "M_BILDER"


@dataclass
class ParishColumns:
    augias_id: str
    title: str
    matricula_identifier: str
    location: str
    parish_church_link: str
    image_url: str
    date_range: str
    description: str

    def dict(self) -> dict[str, str]:
        return {v: k for k, v in asdict(self).items()}


@dataclass
class RegisterColumns:
    identifier: str
    title: str
    description: str
    comment: str
    archival_identifier: str
    storage_location: str
    microfilm_identifier: str
    date_range: str
    date_start: str
    date_end: str

    def dict(self) -> dict[str, str]:
        return {v: k for k, v in asdict(self).items()}


@dataclass
class ImageColumns:
    augias_id: str
    file_path: str
    label: str
    file_name: str

    def dict(self) -> dict[str, str]:
        return {v: k for k, v in asdict(self).items()}


@dataclass
class KeyMap:
    version_table_name: str
    version_col_name: str
    parish_table_name: str
    register_table_name: str
    imgs_table_name: str
    register_parent_col: str
    img_parent_col: str
    parish_cols: ParishColumns
    register_cols: RegisterColumns
    image_cols: ImageColumns


class AugiasProcessor(MDBProcessor, ABC):
    @override
    def __init__(self, input_file: str, diocese_id: str):
        super().__init__(input_file, diocese_id)
        self.key_map = self._get_key_map()

    @abstractmethod
    def _get_key_map(self) -> KeyMap:
        raise NotImplementedError("Subclasses must implement this method")

    @final
    @override
    def _extract_data(self) -> None | MatriculaData:
        parishes_df = self._get_table(parish_table_name)
        registers_df = self._get_table(register_table_name)
        imgs_df = self._get_table(register_table_imgs)
        if parishes_df is None or registers_df is None or imgs_df is None:
            log.error("Could not extract relevant tables from MDB file")
            return None

        parishes = self.__extract_parishes(parishes_df, self.diocese_id)
        registers: list[Register] = []
        images: list[Image] = []

        for parish in parishes:
            parish_registers_df = registers_df[
                registers_df[self.key_map.register_parent_col] == parish.augias_id
            ]
            parish_registers = self.__extract_registers(
                parish_registers_df, self.diocese_id, parish.identifier
            )
            registers.extend(parish_registers)
            for register in parish_registers:
                register_imgs_df = imgs_df[
                    imgs_df[self.key_map.img_parent_col] == register.augias_id
                ]
                register_images = self.__extract_images(
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

    def __extract_parishes(self, df: pd.DataFrame, diocese_key: str) -> list[Parish]:
        columns_to_keep = self.key_map.parish_cols.dict()
        df = df[columns_to_keep.keys()].rename(columns=columns_to_keep)
        df = df.sort_values(by="augias_id")
        df["identifier"] = df["title"].apply(self._to_simple_ascii)
        df["parish_church"] = df["title"]
        df["date_range"] = df["date_range"].apply(self.__wrap_in_p)
        df["description"] = df["description"].apply(lambda d: d if d else None)
        df["location"] = df["location"].apply(self.__coord_to_point)
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
                diocese=f'["{diocese_key}"]',
                parish_church=row["parish_church"],
            )
            parishes.append(parish)
        return parishes

    def __extract_registers(
        self, df: pd.DataFrame, diocese_key: str, parish_key: str
    ) -> list[Register]:
        columns_to_keep = self.key_map.register_cols.dict()
        df = df[columns_to_keep.keys()].rename(columns=columns_to_keep)
        df = df.sort_values(by="identifier")
        df["title"] = df["title"].apply(self._remove_newlines)
        df["type"] = df["title"].apply(self.__extract_types)
        df["description"] = df["description"].apply(self.__wrap_in_p)
        df["comment"] = df["comment"].apply(self.__wrap_in_p)
        df["date_start"] = df["date_start"].apply(self.__format_date)
        df["date_end"] = df["date_end"].apply(self.__format_date)
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

    def __extract_images(
        self, df: pd.DataFrame, diocese_key: str, parish_key: str, register_key: str
    ) -> list[Image]:
        columns_to_keep = self.key_map.image_cols.dict()
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

    def __coord_to_point(self, coord: None | str) -> None | str:
        if not coord:
            return None
        lat, lon = coord.split(", ")
        return f"SRID=4326;POINT ({lon} {lat})"

    def __wrap_in_p(self, text: None | str) -> None | str:
        if not text or text.strip() == "":
            return None
        return f"<p>{text}</p>"

    def __format_date(self, x: float) -> None | str:
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

    def __any_in_text(self, text: str, fragments: list[str]) -> bool:
        return any(fragment in text.lower() for fragment in fragments)

    def __extract_types(self, title: str) -> str:
        types: list[str] = []
        if self.__any_in_text(title, ["index", "register"]):
            types.append("Index")
        if self.__any_in_text(title, ["sterb", "tod"]):
            types.append("Sterben")
        if self.__any_in_text(title, ["tauf"]):
            types.append("Taufen")
        if self.__any_in_text(title, ["trauu", "hochzeit", "heirat"]):
            types.append("Trauungen")
        return " - ".join(types) if types else title

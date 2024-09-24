import csv
from os import path
from typing import override

from modules.models.image import Image
from modules.models.matricula_data import MatriculaData
from modules.models.parish import Parish
from modules.models.register import Register
from modules.writers.base_writer import BaseWriter


class CSVWriter(BaseWriter):
    @override
    def write(self, data: MatriculaData) -> None:
        self._write_parishes(data.parishes, self.output_dir)
        self._write_registers(data.registers, self.output_dir)
        self._write_images(data.images, self.output_dir)

    def _write_parishes(self, parishes: list[Parish], output_dir: str) -> None:
        parishes_path = path.join(output_dir, "parishes.csv")
        with open(parishes_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "model",
                    "pk",
                    "is_test",
                    "identifier",
                    "title",
                    "diocese",
                    "matricula_identifier",
                    "location",
                    "parish_church_link",
                    "parish_church",
                    "image_url",
                    "date_range",
                    "description",
                    "date_start",
                    "date_end",
                ]
            )
            for parish in parishes:
                writer.writerow(
                    [
                        parish.model,
                        parish.pk,
                        parish.is_test,
                        parish.identifier,
                        parish.title,
                        parish.diocese,
                        parish.matricula_identifier,
                        parish.location,
                        parish.parish_church_link,
                        parish.parish_church,
                        parish.image_url,
                        parish.date_range,
                        parish.description,
                        parish.date_start,
                        parish.date_end,
                    ]
                )

    def _write_registers(self, registers: list[Register], output_dir: str):
        registers_path = path.join(output_dir, "registers.csv")
        with open(registers_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "model",
                    "pk",
                    "identifier",
                    "title",
                    "type",
                    "description",
                    "comment",
                    "archival_identifier",
                    "storage_location",
                    "microfilm_identifier",
                    "date_range",
                    "date_start",
                    "date_end",
                    "parish",
                    "image_dir_path",
                    "ordering",
                ]
            )
            for register in registers:
                writer.writerow(
                    [
                        register.model,
                        register.pk,
                        register.identifier,
                        register.title,
                        register.register_type,
                        register.description,
                        register.comment,
                        register.archival_identifier,
                        register.storage_location,
                        register.microfilm_identifier,
                        register.date_range,
                        register.date_start,
                        register.date_end,
                        register.parish,
                        register.image_dir_path,
                        register.ordering,
                    ]
                )

    def _write_images(self, images: list[Image], output_dir: str):
        images_path = path.join(output_dir, "images.csv")
        with open(images_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["model", "pk", "parish", "register", "file_path", "label", "order"]
            )
            for image in images:
                writer.writerow(
                    [
                        image.model,
                        image.pk,
                        image.parish,
                        image.register,
                        image.file_path,
                        image.label,
                        image.order,
                    ]
                )

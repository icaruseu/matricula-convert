from typing import override


class Register:
    def __init__(
        self,
        augias_id: int,
        identifier: str,
        title: str,
        register_type: str,
        description: str | None,
        comment: str | None,
        archival_identifier: str,
        storage_location: str,
        microfilm_identifier: str | None,
        date_range: str,
        date_start: str | None,
        date_end: str | None,
        parish: str,
        image_dir_path: None | str,
        ordering: int,
    ):
        self.augias_id = augias_id
        self.model = "parish.register"
        self.pk = None
        self.identifier = identifier
        self.title = title
        self.register_type = register_type  # type
        self.description = description
        self.comment = comment
        self.archival_identifier = archival_identifier
        self.storage_location = storage_location
        self.microfilm_identifier = microfilm_identifier
        self.date_range = date_range
        self.date_start = date_start
        self.date_end = date_end
        self.parish = parish
        self.image_dir_path = image_dir_path
        self.ordering = ordering

    @override
    def __repr__(self) -> str:
        fields = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({fields})"

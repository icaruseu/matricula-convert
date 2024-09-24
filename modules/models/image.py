from typing import override


class Image:
    def __init__(
        self,
        augias_id: int,
        parish: str,
        register: str,
        file_path: str,
        label: str,
        file_name: str,
        order: int | None,
    ):
        self.augias_id = augias_id
        self.model = "parish.image"
        self.pk = None
        self.parish = parish
        self.register = register
        self.file_path = file_path
        self.label = label
        self.file_name = file_name
        self.order = order

    @override
    def __repr__(self) -> str:
        fields = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({fields})"

from typing import override


class Parish:
    def __init__(
        self,
        augias_id: int,
        identifier: str,
        title: str,
        diocese: str,
        matricula_identifier: str,
        location: str,
        parish_church_link: str | None,
        parish_church: str | None,
        image_url: str | None,
        date_range: str,
        description: str | None,
        date_start: str | None,
        date_end: str | None,
    ):
        self.augias_id = augias_id
        self.model = "parish.parish"
        self.pk = None
        self.is_test = True
        self.identifier = identifier
        self.title = title
        self.diocese = diocese
        self.matricula_identifier = matricula_identifier
        self.location = location
        self.parish_church_link = parish_church_link
        self.parish_church = parish_church
        self.image_url = image_url
        self.date_range = date_range
        self.description = description
        self.date_start = date_start
        self.date_end = date_end

    @override
    def __repr__(self) -> str:
        fields = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({fields})"

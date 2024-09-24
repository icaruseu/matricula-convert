from modules.models.image import Image
from modules.models.parish import Parish
from modules.models.register import Register


class MatriculaData:
    def __init__(
        self, parishes: list[Parish], registers: list[Register], images: list[Image]
    ):
        self.images: list[Image] = images
        self.parishes: list[Parish] = parishes
        self.registers: list[Register] = registers

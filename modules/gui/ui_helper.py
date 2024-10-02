import os
import sys

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QWidget,
)


def get_root_dir() -> str:
    root_dir = os.path.dirname(os.path.abspath(sys.modules["__main__"].__file__))
    if not isinstance(root_dir, str):
        log.error("Executable directory not found.")
        exit(1)
    return root_dir


class UIHelper:
    def __init__(self, parent: QWidget):
        self.parent = parent
        self.button_width = 150
        self.color_mod = 105
        self.color_mod_hover = 115
        self.ele_height = 25
        self.spacing = 10
        self.radius = 5

        palette = self.parent.palette()
        self.rounded_style = f"border-radius: {self.radius}px;"
        self.section_bg_color = (
            palette.color(QPalette.Window).lighter(self.color_mod).name()
        )
        self.input_bg_color = palette.color(QPalette.Base).darker(self.color_mod).name()
        self.bold_font_style = "font-weight: bold;"
        self.step_label_style = f"{self.bold_font_style} font-size: 14px;"

        self.input_style = f"""
            background-color: {self.input_bg_color};
            padding: 0 {self.spacing}px;
            {self.rounded_style}
            border: none;
            line-height: {self.ele_height}px;
        """

        self.button_style = f"""
            QPushButton {{
                background-color: {palette.color(QPalette.Highlight).name()};
                color: {palette.color(QPalette.HighlightedText).name()};
                padding: 5px 10px;
                {self.rounded_style}
                border: none;
            }}
            QPushButton:hover {{
                background-color: {palette.color(QPalette.Highlight).lighter(self.color_mod_hover).name()};
            }}
        """

        self.title_style = f"{self.bold_font_style} font-size: 18px;"

        self.progress_bar_style = f"""
            QProgressBar {{
                {self.rounded_style}
                background-color: {self.input_bg_color};
                color: {self.input_bg_color};
                text-align: left;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {palette.color(QPalette.Highlight).name()};
                {self.rounded_style}
            }}
        """

        self.intro_widget_style = (
            f"background-color: {self.section_bg_color}; {self.rounded_style}"
        )
        self.step_widget_style = (
            f"background-color: {self.section_bg_color}; {self.rounded_style}"
        )

    def get_main_dir(self) -> str:
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        return get_root_dir()

    def get_resource_path(self, name: str) -> str:
        if getattr(sys, "frozen", False):
            icon_dir = str(sys._MEIPASS)
        else:
            icon_dir = self.get_main_dir()
        return os.path.join(icon_dir, "resources", name)

    def create_button(self, text: str) -> QPushButton:
        button = QPushButton(text, self.parent)
        button.setStyleSheet(self.button_style)
        button.setFixedHeight(self.ele_height)
        button.setFixedWidth(self.button_width)
        return button

    def create_input(self) -> QLineEdit:
        input_field = QLineEdit(self.parent)
        input_field.setStyleSheet(self.input_style)
        input_field.setFixedHeight(self.ele_height)
        return input_field

    def create_progress_bar(self) -> QProgressBar:
        progress_bar = QProgressBar(self.parent)
        progress_bar.setStyleSheet(self.progress_bar_style)
        progress_bar.setFixedHeight(self.ele_height)
        progress_bar.setFormat(" %p%")
        return progress_bar

    def create_title_label(self, text: str) -> QLabel:
        label = QLabel(text, self.parent)
        label.setStyleSheet(self.title_style)
        return label

    def create_step_label(self, text: str) -> QLabel:
        label = QLabel(text, self.parent)
        label.setStyleSheet(self.step_label_style)
        return label

    def create_description(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        return label

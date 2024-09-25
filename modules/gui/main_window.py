# pyright: reportUnusedCallResult=false
import logging
import os
import sys
import webbrowser

from PySide6.QtCore import QSettings
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from modules.gui.log_handler import QTextEditLogHandler
from modules.logger import Logger
from modules.processors.process import process_data
from modules.writers.csv_writer import CSVWriter
from modules.writers.write import OutputVariant

import_site_url = "https://data.matricula-online.eu/en/admin/serialized/importrequest/"


log = Logger()


def get_root_dir() -> str:
    root_dir = os.path.dirname(os.path.abspath(sys.modules["__main__"].__file__))
    if not isinstance(root_dir, str):
        log.error("Executable directory not found.")
        exit(1)
    return root_dir


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        if getattr(
            sys, "frozen", False
        ):  # If the application is bundled using PyInstaller or similar
            main_dir = os.path.dirname(sys.executable)
            icon_dir = str(sys._MEIPASS)
        else:
            main_dir = get_root_dir()
            icon_dir = main_dir

        settings_path = os.path.join(main_dir, "matricula-convert.ini")
        icon_path = os.path.join(icon_dir, "resources", "icon.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.settings = QSettings(settings_path, QSettings.Format.IniFormat)

        self.selected_file_path = str(self.settings.value("last_file_path", ""))
        self.output_dir = str(self.settings.value("last_output_dir", ""))
        self.data = None
        self.output_variant = OutputVariant.CSV  # Default output variant
        main_layout = QVBoxLayout()

        # Step 1 - Selecting Input File
        step1_label = QLabel("Step 1 - Select Input File")
        file_layout = QHBoxLayout()
        self.file_input = QLineEdit(self.selected_file_path)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_file)  # Connect button to file browsing
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(browse_btn)

        # Step 2 - Enter Diocese ID
        step2_label = QLabel("Step 2 - Enter Diocese ID")
        diocese_layout = QHBoxLayout()
        self.diocese_id_input = QLineEdit(
            str(self.settings.value("last_diocese_id", ""))
        )
        diocese_layout.addWidget(QLabel("Diocese ID:"))
        diocese_layout.addWidget(self.diocese_id_input)

        # Step 3 - Selecting Output Directory
        step3_label = QLabel("Step 3 - Select Output Directory")
        output_dir_layout = QHBoxLayout()
        self.output_dir_input = QLineEdit(self.output_dir)
        output_dir_btn = QPushButton("Browse Output...")
        output_dir_btn.clicked.connect(
            self.browse_output_directory
        )  # Button to select output directory
        output_dir_layout.addWidget(self.output_dir_input)
        output_dir_layout.addWidget(output_dir_btn)

        # Step 4 - Start Conversion Button
        start_btn = QPushButton("Start Conversion")
        start_btn.clicked.connect(self.start_conversion)

        # Step 5 - Open Website Button
        open_website_btn = QPushButton("Open Website")
        open_website_btn.clicked.connect(
            self.open_website
        )  # Button to open the website

        # Process Log and Progress Bar
        self.progress_bar = QProgressBar()
        self.process_log = QTextEdit(self)
        self.process_log.setReadOnly(True)

        # Create and add the custom QTextEdit log handler
        log_handler = QTextEditLogHandler(self.process_log)
        log_handler.setLevel(logging.INFO)  # Set the appropriate log level
        log_handler.setFormatter(logging.Formatter("%(message)s"))
        log.add_handler(log_handler)

        # Add widgets to layout
        main_layout.addWidget(step1_label)
        main_layout.addLayout(file_layout)
        main_layout.addWidget(step2_label)
        main_layout.addLayout(diocese_layout)
        main_layout.addWidget(step3_label)
        main_layout.addLayout(output_dir_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.process_log)
        main_layout.addWidget(start_btn)
        main_layout.addWidget(open_website_btn)  # Add website button to the layout

        self.setLayout(main_layout)
        self.setWindowTitle("Data Converter")

    def browse_file(self):
        # This method is only triggered by the 'Browse' button, not during start_conversion
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Input File", "", "All Files (*)"
        )
        if file_name:
            self.selected_file_path = file_name  # Store selected file path in variable
            self.file_input.setText(
                file_name
            )  # Update the QLineEdit with the selected file
            self.settings.setValue("last_file_path", file_name)

    def browse_output_directory(self):
        # Open a dialog to select an output directory
        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if output_dir:
            self.output_dir = output_dir  # Store selected output directory in variable
            self.output_dir_input.setText(
                output_dir
            )  # Update the QLineEdit with the output directory
            self.settings.setValue("last_output_dir", output_dir)

    def start_conversion(self):
        # Ensure the input file and output directory have been selected
        if not self.selected_file_path:
            QMessageBox.warning(self, "Error", "Please select an input file.")
            return
        if not self.output_dir:
            QMessageBox.warning(self, "Error", "Please select an output directory.")
            return
        diocese_id = self.diocese_id_input.text()
        if not diocese_id:
            QMessageBox.warning(self, "Error", "Please enter the Diocese ID.")
            return
        self.settings.setValue("last_diocese_id", diocese_id)
        input_file = self.selected_file_path

        # Add conversion logic here
        log.info(f"Starting conversion for file: {input_file}")
        self.progress_bar.setValue(50)  # Example of progress update

        # Extract data from the input file
        self.data = process_data(input_file, diocese_id)

        # After processing, write the output files
        self.write_output_files()

        self.progress_bar.setValue(100)
        log.info("Conversion complete!")

    def write_output_files(self):
        if not self.output_dir:
            QMessageBox.warning(self, "Error", "No output directory selected.")
            return

        # Log and GUI update
        if not self.data:
            return
        else:
            if self.output_variant == OutputVariant.CSV:
                log.info(f"Writing output files to {self.output_dir}")
                writer = CSVWriter(self.output_dir)
                writer.write(self.data)
                QMessageBox.information(
                    self, "Success", "Conversion completed successfully."
                )

    def open_website(self):
        # Open a specific website in the default web browser
        webbrowser.open(import_site_url)  # Replace with your desired URL

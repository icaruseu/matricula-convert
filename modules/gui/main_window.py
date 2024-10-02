# pyright: reportUnusedCallResult=false
import logging
import os
import webbrowser
from typing import Callable, override

from PySide6.QtCore import QSettings, QThread
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from modules.gui.log_window import LogWindow
from modules.gui.ui_helper import UIHelper
from modules.logger import LogEmitter, Logger, SignalLogHandler
from modules.models.matricula_data import MatriculaData
from modules.processors.process import ProcessorWorker
from modules.writers.csv_writer import CSVWriter
from modules.writers.write import OutputVariant

import_site_url = "https://data.matricula-online.eu/en/admin/serialized/importrequest/"

log = Logger()

# Global variable for steps (title and description tuples)
STEPS = [
    (
        "Enter Diocese ID",
        "Enter the diocese ID exactly as it is already configured in the Matricula backend.",
    ),
    ("Select Input File", "Select an input file from your local file system."),
    (
        "Select Output Directory",
        "Select the local directory in which the output files will be written.",
    ),
    (
        "Convert Data",
        "Start the conversion by clicking on the 'Start Conversion' button. After a short while, the files will be written to the output file.",
    ),
    (
        "Upload to Matricula",
        "Visit the Matricula administration and import the files one by one. Start with the parishes, then the registers, and finally the images.",
    ),
]

INTRO_TEXT = "This tool converts parish register book data from various sources into a form that can be used to import the data into matricula. To use it successfully, you have to have a Matricula content manager account, access to the Matricala administration and data exported from your archival management software. To convert this data, please follow the steps below. If you need help, please include the log file created next to the program executable."

banner = """
                               ##############                   
                           ########       ########              
                         #####                 ######           
                        ####                      #####         
                       ####                         #####       
                       ###                            #####     
                      ####                             ######   
                      ###                               ######  
            ######    ###                                ###### 
            ########   ##                                ###### 
    #####   ####  #### ###                               #######
    ############    ### ##                               #######
    ############     ######                              #######
     ####   #####      ####                              #######
      ####   #####      ####                            ####### 
       ####    ####      ####                          ######## 
        ####    ####       ###    ####              ##########  
         ####     ###       ###    #########################    
           ###     ####       ###      ##################       
 #          ####    ####       ####                             
   ##         ###    ####        ####            ######         
     ###       ####   #####        #####        #########       
        ####     ###    #####         ####################      
           ##########    #####           #################      
               ######                         ##########        
"""


class MainWindow(QWidget):
    STEP_INFO = [
        (
            "Enter Diocese ID",
            "Enter the diocese ID exactly as it is already configured in the Matricula backend.",
            "_create_diocese_layout",
        ),
        (
            "Select Input File",
            "Select an input file from your local file system.",
            "_create_file_layout",
        ),
        (
            "Select Output Directory",
            "Select the local directory in which the output files will be written.",
            "_create_output_dir_layout",
        ),
        (
            "Start Conversion",
            "Start the conversion by clicking on the 'Start Conversion' button. After a short while, the files will be written to the output file.",
            "_create_conversion_layout",
        ),
        (
            "Upload to Matricula",
            "Visit the Matricula administration and import the files one by one. Start with the parishes, then the registers, and finally the images.",
            "_create_upload_layout",
        ),
    ]

    def __init__(self):
        super().__init__()

        self.ui_helper = UIHelper(self)
        self.log_window = LogWindow()
        self.settings: QSettings
        self.progress_bar: QProgressBar
        self.open_log_button: QPushButton
        self.log_emitter: LogEmitter
        self.log_handler: SignalLogHandler
        self.file_input: QLineEdit
        self.diocese_id_input: QLineEdit
        self.output_dir_input: QLineEdit
        self.selected_file_path: str = ""
        self.output_dir: str = ""
        self.data: MatriculaData | None = None
        self.worker: ProcessorWorker | None = None
        self.worker_thread: QThread | None = None
        self.output_variant: OutputVariant = OutputVariant.CSV

        self._initialize_ui()
        self._setup_logging()
        self._load_settings()
        self._assemble_layout()

        if self.selected_file_path:
            self._update_processor()

    @override
    def closeEvent(self, event: QCloseEvent):
        if self.log_window.isVisible():
            self.log_window.close()
        super().closeEvent(event)

    def _assemble_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(self.ui_helper.spacing)

        # Intro section
        main_layout.addWidget(self._create_intro_layout())

        # Step sections
        for step, (title, description, layout_func_name) in enumerate(
            self.STEP_INFO, 1
        ):
            step_layout = QVBoxLayout()
            step_label = self.ui_helper.create_step_label(f"Step {step} - {title}")
            step_layout.addWidget(step_label)

            desc_label = self.ui_helper.create_description(description)
            step_layout.addWidget(desc_label)

            layout_func: Callable[[], QLayout | QWidget] = getattr(
                self, layout_func_name
            )
            step_content = layout_func()
            if isinstance(step_content, QWidget):
                step_layout.addWidget(step_content)
            else:
                step_layout.addLayout(step_content)

            step_widget = QWidget()
            step_widget.setLayout(step_layout)
            step_widget.setAutoFillBackground(True)
            step_widget.setStyleSheet(self.ui_helper.step_widget_style)

            main_layout.addWidget(step_widget)

        self.setLayout(main_layout)

    def _browse_input_file(self):
        start_dir = (
            os.path.dirname(self.selected_file_path) if self.selected_file_path else ""
        )
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Input File", start_dir, "All Files (*)"
        )
        if isinstance(file_name, str) and len(file_name) > 0:
            self.selected_file_path = str(file_name)
            self.file_input.setText(file_name)
            self.settings.setValue("last_file_path", file_name)
            self._update_processor()

    def _browse_output_directory(self):
        start_dir = self.output_dir if self.output_dir else ""
        output_dir = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", start_dir
        )
        if output_dir:
            self.output_dir = output_dir
            self.output_dir_input.setText(output_dir)
            self.settings.setValue("last_output_dir", output_dir)

    def _create_button(self, text: str, slot: Callable[[], None]) -> QPushButton:
        button = self.ui_helper.create_button(text)
        button.clicked.connect(slot)
        return button

    def _create_conversion_layout(self):
        conversion_layout = QVBoxLayout()
        start_button = self._create_button("Start Conversion", self._start_conversion)
        button_layout = QHBoxLayout()
        button_layout.addWidget(start_button)
        button_layout.addStretch()
        conversion_layout.addLayout(button_layout)
        self.progress_bar.setStyleSheet(self.ui_helper.progress_bar_style)
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.progress_bar)
        self.open_log_button = self._create_button("Open Log", self._open_log_window)
        progress_layout.addWidget(self.open_log_button)
        conversion_layout.addLayout(progress_layout)

        return conversion_layout

    def _create_diocese_layout(self):
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Diocese ID:"))
        layout.addWidget(self.diocese_id_input)
        return layout

    def _create_file_layout(self):
        layout = QHBoxLayout()
        layout.addWidget(self.file_input)
        layout.addWidget(self._create_button("Browse", self._browse_input_file))
        return layout

    def _create_intro_layout(self):
        # Introductory section with title and icon
        intro_widget = QWidget()
        intro_layout = QVBoxLayout(intro_widget)

        # Title and logo layout
        title_layout = QHBoxLayout()

        # App title
        title_label = self.ui_helper.create_title_label("Matricula-Convert")
        title_layout.addWidget(title_label)

        # Separator between title and logo
        title_layout.addStretch()

        # App icon
        logo_label = QLabel()
        logo_path = self.ui_helper.get_resource_path("logo.png")
        logo_label.setPixmap(QIcon(logo_path).pixmap(32, 32))
        title_layout.addWidget(logo_label)

        intro_layout.addLayout(title_layout)

        intro_text = self.ui_helper.create_description(INTRO_TEXT)
        intro_layout.addWidget(intro_text)

        intro_widget.setAutoFillBackground(True)
        intro_widget.setStyleSheet(self.ui_helper.intro_widget_style)
        return intro_widget

    def _create_output_dir_layout(self):
        layout = QHBoxLayout()
        layout.addWidget(self.output_dir_input)
        layout.addWidget(self._create_button("Browse", self._browse_output_directory))
        return layout

    def _create_upload_layout(self):
        # Create and style the "Open Website" button as a hyperlink
        layout = QHBoxLayout()
        open_website_button = self._create_button("Open Website", self._open_website)
        layout.addWidget(open_website_button)
        layout.addStretch()
        return layout

    def _handle_result(self, data: MatriculaData):
        log.info("Conversion completed successfully")
        self.data = data
        self._write_output_files()

    def _initialize_ui(self):
        icon_path = self.ui_helper.get_resource_path("icon.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("Matricula-Convert")

        self.progress_bar = self.ui_helper.create_progress_bar()
        self.file_input = self.ui_helper.create_input()
        self.diocese_id_input = self.ui_helper.create_input()
        self.output_dir_input = self.ui_helper.create_input()

    def _load_settings(self):
        settings_path = os.path.join(
            self.ui_helper.get_main_dir(), "matricula-convert.ini"
        )
        self.settings = QSettings(settings_path, QSettings.Format.IniFormat)
        self.selected_file_path = str(self.settings.value("last_file_path", ""))
        self.output_dir = str(self.settings.value("last_output_dir", ""))
        self.file_input.setText(self.selected_file_path)
        self.output_dir_input.setText(self.output_dir)
        self.diocese_id_input.setText(str(self.settings.value("last_diocese_id", "")))

    def _on_log_signal(self, message: str):
        if hasattr(self, "log_window"):
            self.log_window.append_log(message)

    def _open_log_window(self):
        if not hasattr(self, "log_window"):
            self.log_window = LogWindow(self)
        self.log_window.show()
        self.log_window.raise_()
        self.log_window.activateWindow()

    def _open_website(self):
        webbrowser.open(import_site_url)

    def _processor_initialized(self, processor_name: str):
        log.info(f"Processor '{processor_name}' initialized successfully")

    def _setup_logging(self):
        self.log_emitter = LogEmitter()
        self.log_handler = SignalLogHandler(self.log_emitter)
        self.log_handler.setLevel(logging.INFO)
        self.log_handler.setFormatter(logging.Formatter("%(message)s"))
        log.add_handler(self.log_handler)
        self.log_emitter.log_signal.connect(self._on_log_signal)
        log.debug(banner)
        log.info("Matricula-Convert started")

    def _show_error(self, error_message: str):
        QMessageBox.warning(self, "Error", error_message)

    def _start_conversion(self):
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

        # Recreate worker and thread if not running
        if self.worker_thread is None or not self.worker_thread.isRunning():
            self._update_processor()

        if self.worker:
            self.worker.start_extraction.emit(diocese_id)

    def _update_processor(self):
        # Clean up existing worker and thread if they exist
        if self.worker_thread is not None:
            self.worker_thread.quit()
            self.worker_thread.wait()
            self.worker_thread = None
            self.worker = None

        if self.selected_file_path:
            log.info(f"Initializing processor for '{self.selected_file_path}'")
            # Create a new ProcessorWorker and thread
            self.worker = ProcessorWorker(self.selected_file_path)
            self.worker_thread = QThread()
            self.worker.moveToThread(self.worker_thread)

            # Connect signals and slots
            self.worker_thread.started.connect(self.worker.init)
            self.worker.initialized.connect(self._processor_initialized)
            self.worker.progress.connect(self._update_progress)
            self.worker.finished.connect(self._handle_result)
            self.worker.error.connect(self._show_error)
            self.worker.log_signal.connect(self._on_log_signal)
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)
            self.worker_thread.start()
        else:
            self.worker = None
            self.worker_thread = None

    def _update_progress(self, percent: float):
        percent = round(percent)
        self.progress_bar.setValue(percent)

    def _write_output_files(self):
        if not self.output_dir:
            QMessageBox.warning(self, "Error", "No output directory selected.")
            return
        if not self.data:
            return
        if self.output_variant == OutputVariant.CSV:
            log.info(f"Writing output files to {self.output_dir}")
            writer = CSVWriter(self.output_dir)
            writer.write(self.data)
            log.info("Output files written successfully")
            log.info("Conversion completed successfully")
            QMessageBox.information(
                self, "Success", "Conversion completed successfully."
            )

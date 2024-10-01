# pyright: reportUnusedCallResult=false
import logging
import os
import sys
import webbrowser

from PySide6.QtCore import QSettings, QThread, Slot
from PySide6.QtGui import QFont, QIcon
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

from modules.logger import LogEmitter, Logger, SignalLogHandler
from modules.models.matricula_data import MatriculaData
from modules.models.percent import Percent
from modules.processors.process import ProcessorWorker
from modules.writers.csv_writer import CSVWriter
from modules.writers.write import OutputVariant

import_site_url = "https://data.matricula-online.eu/en/admin/serialized/importrequest/"

log = Logger()

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


def get_root_dir() -> str:
    root_dir = os.path.dirname(os.path.abspath(sys.modules["__main__"].__file__))
    if not isinstance(root_dir, str):
        log.error("Executable directory not found.")
        exit(1)
    return root_dir


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        if getattr(sys, "frozen", False):
            main_dir = os.path.dirname(sys.executable)
            icon_dir = str(sys._MEIPASS)
        else:
            main_dir = get_root_dir()
            icon_dir = main_dir

        settings_path = os.path.join(main_dir, "matricula-convert.ini")
        icon_path = os.path.join(icon_dir, "resources", "icon.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.settings = QSettings(settings_path, QSettings.Format.IniFormat)

        # Process Log and Progress Bar
        self.progress_bar = QProgressBar()
        self.process_log = QTextEdit(self)
        monospace_font = QFont("Courier New")
        self.process_log.setFont(monospace_font)
        self.process_log.setReadOnly(True)

        # Set up the log emitter and handler
        self.log_emitter = LogEmitter()
        self.log_handler = SignalLogHandler(self.log_emitter)
        self.log_handler.setLevel(logging.INFO)
        self.log_handler.setFormatter(logging.Formatter("%(message)s"))
        log.add_handler(self.log_handler)
        self.log_emitter.log_signal.connect(self.on_log_signal)
        log.debug(banner)
        log.info("Matricula-Convert started")

        self.selected_file_path = str(self.settings.value("last_file_path", ""))
        self.output_dir = str(self.settings.value("last_output_dir", ""))
        self.data = None
        self.worker = None
        self.worker_thread = None
        self.output_variant = OutputVariant.CSV  # Default output variant

        main_layout = QVBoxLayout()

        # Step 1 - Selecting Input File
        step1_label = QLabel("Step 1 - Select Input File")
        file_layout = QHBoxLayout()
        self.file_input = QLineEdit(self.selected_file_path)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)
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
        output_dir_btn = QPushButton("Browse")
        output_dir_btn.clicked.connect(self.browse_output_directory)
        output_dir_layout.addWidget(self.output_dir_input)
        output_dir_layout.addWidget(output_dir_btn)

        # Step 4 - Start Conversion Button
        start_btn = QPushButton("Start Conversion")
        start_btn.clicked.connect(self.start_conversion)

        # Step 5 - Open Website Button
        open_website_btn = QPushButton("Open Website")
        open_website_btn.clicked.connect(self.open_website)

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
        main_layout.addWidget(open_website_btn)

        self.setLayout(main_layout)
        self.setWindowTitle("Matricula-Convert")

        if self.selected_file_path:
            self._update_processor()

    def browse_file(self):
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

    def browse_output_directory(self):
        start_dir = self.output_dir if self.output_dir else ""
        output_dir = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", start_dir
        )
        if output_dir:
            self.output_dir = output_dir
            self.output_dir_input.setText(output_dir)
            self.settings.setValue("last_output_dir", output_dir)

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
            self.worker.initialized.connect(self.processor_initialized)
            self.worker.progress.connect(self.update_progress)
            self.worker.finished.connect(self.handle_result)
            self.worker.error.connect(self.show_error)
            self.worker.log_signal.connect(self.on_log_signal)
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)
            self.worker_thread.start()
        else:
            self.worker = None
            self.worker_thread = None

    def start_conversion(self):
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

    @Slot(str)
    def processor_initialized(self, processor_name: str):
        log.info(f"Processor '{processor_name}' initialized successfully")

    @Slot(MatriculaData)
    def handle_result(self, data: MatriculaData):
        log.info("Conversion completed successfully")
        self.data = data
        self.write_output_files()

    def write_output_files(self):
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

    def open_website(self):
        webbrowser.open(import_site_url)

    @Slot(Percent)
    def update_progress(self, percent: int):
        self.progress_bar.setValue(round(percent))

    @Slot(str)
    def show_error(self, error_message: str):
        QMessageBox.warning(self, "Error", error_message)

    @Slot(str)
    def on_log_signal(self, message: str):
        self.process_log.append(message)

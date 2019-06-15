import os
from threading import Lock
import logging
from datetime import datetime

from .main_menu_widget import MainMenuWidget
from .plot_widget import PlotWidget
from demo_src.demo_tasks_runner import DemoTasksRunner
from demo_src.read_from_hdf5 import  HDF5FileReader


from PySide2.QtWidgets import QMainWindow, QMessageBox
from PySide2.QtCore import Slot, Signal, QCoreApplication
from PySide2 import QtCore, QtGui, QtWidgets



logger = logging.getLogger("Status bar logger")


class MainWindow(QMainWindow):
    log_message_active = Signal(str)

    def __init__(self):
        super().__init__()
        self._ui = self._load_ui()
        self._menu_widget = None
        self._plot_widget = None

        self.demo_tasks_runner = DemoTasksRunner()

        self._setup_menu()
        self._create_connections()

    def _load_ui(self):
        from .moc_mainwindow import Ui_MainWindow
        ui = Ui_MainWindow()
        ui.setupUi(self)
        return ui

    def _setup_menu(self):
        self._menu_widget = MainMenuWidget()
        self.status_bar = self.statusBar()

        log_handler = logging.getLogger("Status bar logger").handlers[0]
        log_handler.set_write_function(self._logger_triggered)
        log_handler.setLevel(logging.DEBUG)

        self._ui.verticalLayout_main_widget.addWidget(self._menu_widget)
        self._menu_widget.show()

    def _create_connections(self):
        self._menu_widget.start_clicked.connect(self._process_start_demo)
        self._menu_widget.open_clicked.connect(self._process_open_file)
        self.log_message_active.connect(self._log_to_status_bar)

    def _process_start_demo(self):
        bit_file_path = self._menu_widget.get_bitfile_path()
        if not os.path.isfile(bit_file_path):
            logger.error("Error! Wrong bitfile path")
            return

        results_dir = self._menu_widget.get_h5_output_dir()
        if not os.path.isdir(results_dir):
            logger.error("Error! Output h5 directory does not exist.")
            return

        sampling_rate = self._menu_widget.get_sampling_rate_in_kHz()
        sampling_rate_Hz = sampling_rate * 1000
        number_of_channels = self._menu_widget.get_number_of_channels()
        package_length_in_bytes = self._menu_widget.get_packet_length_in_bytes()
        output_h5_file_path = os.path.join(results_dir, 'received_data{:%Y_%m_%d_%H:%M}.h5'.format(datetime.now()))

        self.demo_tasks_runner.services_started.connect(self._process_services_started)
        self.demo_tasks_runner.start(bit_file_path, output_h5_file_path, number_of_channels, package_length_in_bytes, sampling_rate_Hz)

    def _process_open_file(self):
        file_to_open_path = self._menu_widget.get_hdf5_file_path()
        if not os.path.isfile(file_to_open_path):
            logger.error("Error! Wrong hdf5 file path")
            return
        self._file_reader = HDF5FileReader(file_to_open_path)
        self._file_reader.load_plot_data()
        self._menu_widget.hide()
        self._setup_plot_widget(offline=True)
        self._plot_widget.plot_data()

    def _setup_plot_widget(self, offline=False):
        self._plot_widget = PlotWidget(offline=offline)
        self._ui.verticalLayout_main_widget.addWidget(self._plot_widget)
        if not offline:
            self._plot_widget.stop_clicked.connect(self._process_stop_demo)
            self._plot_widget.pause_clicked.connect(self._process_pause_demo)
            self._plot_widget.change_slope_max.connect(self._send_change_slope_max)
            # connect plot data source to plot widget
            self._plot_widget.add_data_source_handle(self.demo_tasks_runner.get_data_source_handle())
        else:
            self._plot_widget.add_data_source_handle(self._file_reader)

        self._plot_widget.show()

    def _process_services_started(self):
        logger.info("Start DEMO")
        self._menu_widget.hide()
        self._setup_plot_widget()

    def _process_pause_demo(self):
        if self._plot_widget.paused:
            self._plot_widget.resume()
        else:
            self._plot_widget.pause()

    def _process_stop_demo(self, close=False):
        if close:
            self.demo_tasks_runner.services_stopped.connect(self.close)
        else:
            self.demo_tasks_runner.services_stopped.connect(self.after_services_stopped)
        self.demo_tasks_runner.stop()

    def after_services_stopped(self):
        self._plot_widget.hide()
        self._menu_widget.show()

    def _logger_triggered(self, msg):
        self.log_message_active.emit(msg)

    @Slot()
    def _log_to_status_bar(self, msg):
        message_time = 5000
        self.status_bar.showMessage(msg, message_time)

    @Slot(int)
    def _send_change_slope_max(self, value):
        self.demo_tasks_runner.send_change_slope_max(value)

    def closeEvent(self, event):
        self._process_stop_demo(close=True)


if __name__ == '__main__':
    from PySide2.QtWidgets import QApplication
    import sys
    import os

    app = QApplication(sys.argv)
    mm = MainWindow()
    mm.show()
    sys.exit(app.exec_())

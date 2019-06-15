import os
from PySide2 import QtWidgets
from PySide2.QtWidgets import QTableWidgetItem, QHeaderView, QFileDialog
import PySide2.QtCore

from PySide2.QtCore import Signal


class MainMenuWidget(QtWidgets.QWidget):
    start_clicked = Signal()
    open_clicked = Signal()

    def __init__(self):
        super().__init__()
        self._ui = self._load_ui()
        self._create_connections()

    def _create_connections(self):
        self._ui.pushButton_start.clicked.connect(self._start_clicked)
        self._ui.pushButton_search_bitfile.clicked.connect(self._search_bitfile_path)
        self._ui.pushButton_search_output_dir.clicked.connect(self._get_hdf5_output_dir)
        self._ui.pushButton_open_hdf5.clicked.connect(self._open_clicked)
        self._ui.pushButton_search_hdf5.clicked.connect(self._search_hdf5_file_to_open)

    def _load_ui(self):
        from .moc_menu import Ui_main_menu
        ui = Ui_main_menu()
        ui.setupUi(self)
        return ui

    ############# online data acqisition part #######################

    def _start_clicked(self):
        self._ui.pushButton_start.setEnabled(False)
        self.start_clicked.emit()

    def _get_bitfile_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Select bit file', '/home', ("Bitfiles (*.bit)"))
        return file_name

    def _get_hdf5_output_dir(self):
        dir_name= QFileDialog.getExistingDirectory(self, 'Select output dir', '/home')
        self._ui.lineEdit_output_dir.setText(dir_name)

    def _search_bitfile_path(self):
        bitfile_path = self._get_bitfile_file_dialog()
        self._ui.lineEdit_bitffile.setText(bitfile_path)
        self._get_parameters_from_bitfile_name(os.path.basename(bitfile_path))

    def _get_parameters_from_bitfile_name(self, bitfile_name):
        bitfile_name, _ = bitfile_name.split('.')
        if len(bitfile_name.split('_')) == 3:
            try:
                [number_of_sources, sampling_rate, packet_length] = bitfile_name.split('_')
                number_of_sources = int(number_of_sources)
                packet_length = int(packet_length.rstrip('B'))
                if sampling_rate[-1]=='M':
                    factor = 1e6
                elif sampling_rate[-1]=='k':
                    factor = 1e3
                else:
                    factor = 1
                sampling_rate_in_Hz = int(sampling_rate[:-1]) * factor
            except TypeError:
                return
            else:
                self._ui.spinBox_number_of_sources.setValue(number_of_sources)
                self._ui.spinBox_sampling_rate.setValue(sampling_rate_in_Hz//1000)
                self._ui.spinBox_packet_length.setValue(packet_length)

    def get_bitfile_path(self):
        return self._ui.lineEdit_bitffile.text()

    def get_h5_output_dir(self):
        return self._ui.lineEdit_output_dir.text()

    def get_number_of_channels(self):
        return self._ui.spinBox_number_of_sources.value()

    def get_packet_length_in_bytes(self):
        return self._ui.spinBox_packet_length.value()

    def get_sampling_rate_in_kHz(self):
        return self._ui.spinBox_sampling_rate.value()

    ############## offline viewer part ###############################

    def _open_clicked(self):
        self.open_clicked.emit()

    def _get_hdf5_file_dialog(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select hdf5 file', '/home', ("Hdf5 files (*.h5)"))
        return file_path

    def _search_hdf5_file_to_open(self):
        hdf5_file_path = self._get_hdf5_file_dialog()
        self._ui.lineEdit_hdf5_file_path.setText(hdf5_file_path)

    def get_hdf5_file_path(self):
        return self._ui.lineEdit_hdf5_file_path.text()


if __name__ == "__main__":
    from PySide2.QtWidgets import QApplication, QMainWindow

    app = QApplication()

    widget = MainMenuWidget()
    widget.show()
    app.exec_()

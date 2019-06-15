import os
from PySide2 import QtWidgets
from PySide2.QtWidgets import QTableWidgetItem, QHeaderView
from PySide2.QtCore import Slot, Signal, QTimer

import pyqtgraph as pg

from .curves_plot_widget import GraphicWidget

os.environ["PYQTGRAPH_QT_LIB"] = "PySide2" # added for now, pyqtgraph not working without it


TIMER_INTERVAL_MS = 700

class PlotWidget(QtWidgets.QWidget):
    stop_clicked = Signal()
    pause_clicked = Signal()
    change_slope_max = Signal(int)

    def __init__(self, offline=False):
        super().__init__()
        self._ui = self._load_ui()
        self._create_connections()

        self.data_source_handle = None
        self.offline = offline
        self.time_span = 1
        self.paused = False

        self._graphic_widget = GraphicWidget(parent=self)
        self._ui.verticalLayout_plot.addWidget(self._graphic_widget)
        self._ui.spinBox_time_span.setValue(self.time_span)

        if offline:
            self._set_offline_layout()
            self._graphic_widget.setDownsampling(ds=100, auto=True, mode='subsample')
        else:
            self.replot_timer = self.create_replot_timer()


    def _set_offline_layout(self):
        self._ui.pushButton_stop.setVisible(False)
        self._ui.pushButton_pause.setVisible(False)
        self._ui.spinBox_time_span.setVisible(False)
        self._ui.label.setVisible(False)
        self._ui.label_2.setVisible(False)

    def _create_connections(self):
        self._ui.pushButton_stop.clicked.connect(self._stop_clicked)
        self._ui.pushButton_pause.clicked.connect(self._pause_clicked)
        self._ui.spinBox_time_span.valueChanged.connect(self.change_time_span)

    def create_replot_timer(self):
        replot_timer = QTimer()
        replot_timer.setSingleShot(True)
        replot_timer.timeout.connect(self._replot_timer_timeout)
        replot_timer.start(TIMER_INTERVAL_MS)
        return replot_timer

    def add_data_source_handle(self, data_source_handle):
        self.data_source_handle = data_source_handle
        self.update_channels_list(self.data_source_handle.get_available_channels())
        self._ui.comboBox_channels.currentIndexChanged.connect(self._channel_changed)

    def update_channels_list(self, available_channles):
        for channel in available_channles:
            self._ui.comboBox_channels.addItem(f"{channel}")

    @Slot(str)
    def _channel_changed(self, selected_channel: str):
        channel_number = int(selected_channel)
        self.plot_data()

    @Slot(int)
    def change_time_span(self, new_time_span: int):
        self.time_span = new_time_span

    def _load_ui(self):
        from .moc_plot_widget import Ui_plot_widget
        ui = Ui_plot_widget()
        ui.setupUi(self)
        return ui

    @Slot()
    def _replot_timer_timeout(self):
        if not self.paused:
            if self.data_source_handle is not None:
                if self.data_source_handle.get_available_time_span()>self.time_span:
                    self.plot_data()
            self.replot_timer.start(TIMER_INTERVAL_MS)

    @Slot()
    def plot_data(self):
        selected_channel = self._get_selected_channel()
        plot_data = self.data_source_handle.get_data(selected_channel, self.time_span)
        max_time = plot_data['time'][-1]
        min_time = max(0, max_time - self.time_span)
        self._graphic_widget.plot_data(plot_data, min_time)

    def _get_selected_channel(self):
        return int(self._ui.comboBox_channels.currentText())

    def _stop_clicked(self):
        self.stop_clicked.emit()

    def _pause_clicked(self):
        self.pause_clicked.emit()

    def pause(self):
        self.paused = True
        self._ui.pushButton_pause.setText('Resume')

    def resume(self):
        self.paused = False
        self._replot_timer_timeout()
        self._ui.pushButton_pause.setText('Pause')


if __name__ == "__main__":
    from PySide2.QtWidgets import QApplication, QMainWindow
    from .moc_plot_widget import Ui_plot_widget

    app = QApplication()

    widget = Ui_plot_widget()
    widget.show()
    app.exec_()

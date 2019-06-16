import threading
import logging
import time

import PySide2
from PySide2.QtCore import QObject, Signal

from demo_src.fpga_device import FPGADevice
from demo_src.data_unpacker import DataUnpacker
from demo_src.file_writer import FileWriter
from demo_src.data_manager import DataManager
from demo_src.plot_data_source import PlotDataSource, PlotData

BLOCK_LENGTH = 1024
TRANSFER_LENGTH = BLOCK_LENGTH  #

MIN_TIME_SPAN = 1024

logger = logging.getLogger("Status bar logger")


class DemoTasksRunner(QObject):
    services_stopped = Signal()
    services_started = Signal()

    def __init__(self):
        super().__init__()
        self.device = None
        self.data_unpacker = None
        self.data_manager = None
        self.file_writer = None
        self.plot_data_source = None

        self.start_services_requested = False

        self.should_stop = False
        self.thread = threading.Thread(target=self._run, name="TaskRunner")

    def start(self, bit_file_path, hdf5_file_path, number_of_channels, package_length_in_bytes, sampling_rate_Hz):

        self.bit_file_path = bit_file_path
        self.hdf5_file_path = hdf5_file_path
        self.number_of_channels = number_of_channels
        self.package_length_in_bytes = package_length_in_bytes
        self.sampling_rate_Hz = sampling_rate_Hz
        self.sampling_interval = 1/sampling_rate_Hz

        #### start :
        self.start_services_requested = True
        self.thread.start()

    def _start_services(self):
        self.device = FPGADevice()
        self.device.load_bit_file(self.bit_file_path)

        self.data_unpacker = DataUnpacker(packet_length_in_bytes=self.package_length_in_bytes, number_of_channels=self.number_of_channels)
        self.file_writer = FileWriter(self.sampling_interval)
        self.file_writer.open_file(self.hdf5_file_path, self.number_of_channels)
        self.plot_data_source = PlotDataSource(self.number_of_channels, self.sampling_rate_Hz)
        self.data_manager = DataManager()
        self.data_manager.add_data_sink(self.file_writer)
        self.data_manager.add_data_sink(self.plot_data_source)
        self.data_unpacker.add_data_handler(self.data_manager)

        self.device.reset_design()
        self.device.start_data_generation()  # enable data generation

        self.file_writer.start()
        self.plot_data_source.start()
        self.data_manager.start()
        self.data_unpacker.start()

        self.services_started.emit()


    def _run(self):
        counter = 0
        start = time.time()
        counter_max=16
        while True:
            if self.start_services_requested:
                self.start_services_requested = False
                self._start_services()
            elif self.should_stop:
                self.device.stop_data_generation()  # disable data generation
                self.plot_data_source.stop()
                self.data_manager.remove_data_sink(self.plot_data_source)
                logger.debug("Waiting for data unpacker to finish its job....")
                self.data_unpacker.stop()
                self.data_unpacker.print_summary()
                logger.debug("Waiting for data manager to finish its job....")
                self.data_manager.stop()
                logger.debug("Waiting for file writer to finish its job....")
                self.file_writer.stop()
                logger.debug("")

                self.services_stopped.emit()
                break
            else:
                # receive buffer from FPGA and add it to further processing
                received_buffer = self.device.receive_data(BLOCK_LENGTH, TRANSFER_LENGTH)
                if received_buffer is not None:
                    self.data_unpacker.add_buffer_to_queue(received_buffer)
                    counter += 1
                    if counter%counter_max == 0:
                        print('Speed {:2f} MB/s'.format(counter_max*TRANSFER_LENGTH/(1024*1024*(time.time()-start))))
                        start = time.time()

    def get_data_source_handle(self):
        return self.plot_data_source

    def send_change_slope_max(self, value):
        self.device.set_slope_max(value)

    def stop(self):
        self.should_stop = True

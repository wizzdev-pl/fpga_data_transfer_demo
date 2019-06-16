import sys
import os
import time
from datetime import datetime
import struct
import logging

from FrontPanelAPI import ok
from .common import ok_error_message


logger = logging.getLogger("Status bar logger")


class FPGADevice:

    FILL_LEVEL_WIRE_OUT_ADDRESS = 0x21
    DATA_GENERATION_TRIGGER_IN_ADDRESS = 0x40
    CONTROL_WIRE_IN_ADDRESS = 0x00
    SLOPE_MAX_WIRE_ADDRESS = 0x01
    DATA_PIPE_OUT_ADDRESS = 0xa0

    def __init__(self):
        self.xem = ok.okCFrontPanel()
        logger.info("Opening device...")
        error_code = self.xem.OpenBySerial("")
        if error_code != ok.okCFrontPanel.NoError:
            logger.error("Device could not be opened, errorCode: {}, error message: {}".format(error_code, ok_error_message[error_code]))
            sys.exit()
        else:
            logger.info("Device open: {}".format(self.xem.IsOpen()))

        self.timeout_reported = False

    def load_bit_file(self, bit_file_path):
        logger.info("Loading bitfile to FPGA...")
        error_code = self.xem.ConfigureFPGA(bit_file_path)
        if error_code != ok.okCFrontPanel.NoError:
            raise Exception("Error while writing bit file! errorCode: {}, error message: {}".format(error_code, ok_error_message[error_code]))
        else:
            logger.info('Bitfile loaded succesfuly!')

    def reset_design(self, f_rate=0, sig_type=1):
        # Hold reset state for 0.1s :
        wire_value = (sig_type << 3) | (f_rate << 1) | 1
        logger.info("Performing reset")
        error_code = self.xem.SetWireInValue(self.CONTROL_WIRE_IN_ADDRESS, wire_value)
        self.check_errors(error_code)

        error_code = self.xem.UpdateWireIns()
        self.check_errors(error_code)

        time.sleep(0.01)
        wire_value = (sig_type << 3) | (f_rate << 1) | 0
        error_code = self.xem.SetWireInValue(self.CONTROL_WIRE_IN_ADDRESS, wire_value)
        self.check_errors(error_code)

        error_code = self.xem.UpdateWireIns()
        self.check_errors(error_code)

    def start_data_generation(self):
        error_code = self.xem.ActivateTriggerIn(self.DATA_GENERATION_TRIGGER_IN_ADDRESS, 0)  # Enable/disable data generation
        self.check_errors(error_code)

    def stop_data_generation(self):
        error_code = self.xem.ActivateTriggerIn(self.DATA_GENERATION_TRIGGER_IN_ADDRESS, 1)  # Enable/disable data generation
        self.check_errors(error_code)

    def set_slope_max(self, value):
        error_code = self.xem.SetWireInValue(self.SLOPE_MAX_WIRE_ADDRESS, value)
        self.check_errors(error_code)
        error_code = self.xem.UpdateWireIns()
        self.check_errors(error_code)

    def receive_data(self, block_length, buffer_length):

        buff = bytearray(buffer_length)
        bytes_count_or_error = self.xem.ReadFromBlockPipeOut(self.DATA_PIPE_OUT_ADDRESS, block_length, buff)
        if bytes_count_or_error <= 0:
            logger.error("Error while reading from pipe: {}".format(bytes_count_or_error))
            if self.timeout_reported:
                raise Exception('Error while reading: {}'.format(ok_error_message[bytes_count_or_error]))
            else:
                self.timeout_reported = True
                return
        else:
            self.timeout_reported = False
            return buff

    def get_DDR_fill_level(self):
        self.xem.UpdateWireOuts()
        fill_level = self.xem.GetWireOutValue(self.FILL_LEVEL_WIRE_OUT_ADDRESS)
        return fill_level

    def check_errors(self, error_code):
        if error_code != ok.okCFrontPanel.NoError:
            raise Exception("errorCode: {}, error message: {}".format(error_code, ok_error_message[error_code]))

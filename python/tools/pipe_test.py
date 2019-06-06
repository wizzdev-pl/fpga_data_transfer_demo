"""
This is a simplified Python version of PipeTest.cpp application from Opal Kelly Front Panel examples
            (which can be found in Samples folder in your FrontPanel installation directory)

an Opal Kelly FPGA board device and a corresponding PipeTest.bit file are needed
"""
import os
import sys
import time

# add parent directory to PYTHONPATH
file_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(file_dir)
sys.path.append(parent_dir)

from FrontPanelAPI import ok

OK_PATTERN_COUNT         = 0
OK_PATTERN_LFSR          = 1
OK_PATTERN_WALKING1      = 2
OK_PATTERN_WALKING0      = 3
OK_PATTERN_HAMMER        = 4
OK_PATTERN_NEIGHBOR      = 5
OK_PATTERN_FIXED         = 6


dev_info = ok.okTDeviceInfo()

selected_pattern = OK_PATTERN_LFSR
fixed_pattern = 0x01010101
throttle_in = 0xffffffff
throttle_out = 0xffffffff

class TransferSettings:
    def __init__(self, settings):
        self.block_size = settings[0]
        self.segment_size = settings[1]
        self.count = settings[2]


def createSettingsList():
    settings_matrix = [
        #BlockSize, SegmentSize, Count
        (0, 4 * 1024 * 1024, 10),
        (0, 1 * 1024 * 1024, 10),
        (0, 256 * 1024, 10),
        (0, 64 * 1024, 10),
        (0, 16 * 1024,  10),
        (0, 4 * 1024, 10),
        (0, 1 * 1024, 10),
        (16 * 1024, 16 * 1024, 10),
        (16 * 1024, 1024 * 1024,  10),
        (1024, 1 * 1024,  10),
        (1024, 1 * 1024 * 1024, 100),
        (512, 1 * 1024 * 1024, 100),
        (256, 1 * 1024 * 1024, 100),
        (128, 1 * 1024 * 1024, 100)]

    settings_list = []
    for settings in settings_matrix:
        settings_list.append(TransferSettings(settings))

    return settings_list

class TestbenchType:
    triggers = 0
    wires = 1
    pipes = 2


def initialize_FPGA(dev: ok.okCFrontPanel, bit_file_path):

    dev.GetDeviceInfo(dev_info)
    print("Found device: {}".format(dev_info.productName))

    dev.LoadDefaultPLLConfiguration()

    print('Device firmware version: {}.{}'.format(dev_info.deviceMajorVersion, dev_info.deviceMinorVersion))
    print('Device serial number: {}'.format(dev_info.serialNumber))
    print('Device ID: {}'.format(dev_info.productID))

    # Download the configuration file:
    if (dev.ConfigureFPGA(bit_file_path) != ok.okCFrontPanel.NoError):
        print("Fpga configuration failed.")
        return False

    # Check for FrontPanel support in the FPGA configuration
    if dev.IsFrontPanelEnabled():
        print('Front Panel support enabled.')
    else:
        print('Front Panel support not enabled.')

    if dev_info.deviceInterface == ok.OK_INTERFACE_USB3:
        print('Using USB3.0 interface.')
    else:
        print('Using USB2.0 interface')

    if dev_info.usbSpeed == ok.OK_USBSPEED_FULL:
        print('USB speed : FULL')
    elif dev_info.usbSpeed == ok.OK_USBSPEED_HIGH:
        print('USB speed : HIGH')
    elif dev_info.usbSpeed == ok.OK_USBSPEED_SUPER:
        print('USB speed: SUPER')
    else:
        print('USB speed type unrecognized')

    return True


def BenchmarkWires(dev: ok.okCFrontPanel):
    # WireIns:
    start_time = time.time()
    for i in range(1000):
        dev.UpdateWireIns()
    duration = time.time() - start_time
    print('UpdateWireIns (1000 calls) Duration: {:3f} seconds -- {:2f} calls/s'.format(duration, 1000/duration))
    # WireOuts:
    start_time = time.time()
    for i in range(1000):
        dev.UpdateWireOuts()
    duration = time.time() - start_time
    print('UpdateWireOuts (1000 calls) Duration: {:3f} seconds -- {:2f} calls/s'.format(duration, 1000/duration))


def BenchmarkTriggers(dev: ok.okCFrontPanel):
    #TriggerIns:
    start_time = time.time()
    for i in range(1000):
        dev.ActivateTriggerIn(0x40, 0x01)
    duration = time.time() - start_time
    print('ActivateTriggerIns (1000 calls) Duration: {:3f} seconds -- {:2f} calls/s'.format(duration, 1000/duration))
    #TriggerOuts:
    start_time = time.time()
    for i in range(1000):
        dev.UpdateTriggerOuts()
    duration = time.time() - start_time
    print('UpdateTriggerOuts (1000 calls) Duration: {:3f} seconds -- {:2f} calls/s'.format(duration, 1000/duration))


def BenchmarkPipes(dev: ok.okCFrontPanel, custom_settings = None):
    if custom_settings is not None:
        settings_list = [custom_settings]
    else:
        settings_list = createSettingsList()
    for read_write in ('READ', 'WRITE'):
        for entry in settings_list:
            if (entry.block_size != 0):
                entry.segment_size -= (entry.segment_size % entry.block_size)     # must be a multiple of block length
            Transfer(dev, entry, read_write)


def Transfer(dev: ok.okCFrontPanel, transfer_settings: TransferSettings, read_write: str):

    # Apparently this is required to setup FPGA:

    # Check capability bits for newer pattern
    selected_pattern = OK_PATTERN_LFSR

    # Bit 0 - added Fixed pattern
    dev.UpdateWireOuts()
    if ((dev.GetWireOutValue(0x3e) & 0x1) != 0x1) and (selected_pattern == OK_PATTERN_FIXED):
        print("Fixed pattern is not supported by this bitstream. Switchin to LFSR.")
        selected_pattern = OK_PATTERN_LFSR

    # only COUNT and LFSR are supported on non-USB3 devicecs
    if dev_info.deviceInterface != ok.OK_INTERFACE_USB3:
        if selected_pattern in (OK_PATTERN_WALKING0, OK_PATTERN_WALKING1, OK_PATTERN_HAMMER, OK_PATTERN_NEIGHBOR):
            print("Unsupported pattern for not USB3 device. Switching do LFSR.")
            selected_pattern = OK_PATTERN_LFSR

    if dev_info.deviceInterface == ok.OK_INTERFACE_USB3:
        dev.SetWireInValue(0x03, fixed_pattern) # Apply fixed pattern
        dev.SetWireInValue(0x02, throttle_in) # Pipe in throttle
        dev.SetWireInValue(0x01, throttle_out)  # Pipe out throttle
        dev.SetWireInValue(0x00, (selected_pattern << 2) | 1 << 1 | 1) # PATTERN | SET_THROTTLE = 1 | RESET = 1
        dev.UpdateWireIns()
        dev.SetWireInValue(0x00, (selected_pattern << 2) | 0 << 1 | 0) # PATTERN | SET_THROTTLE = 0 | RESET = 0
        dev.UpdateWireIns()
    else:
        dev.SetWireInValue(0x02, throttle_in) #PipeIn throttle
        dev.SetWireInValue(0x01, throttle_out)  # pipe out throttle
        dev.SetWireInValue(0x00, 1 << 5 | (
                    (1 if (selected_pattern == OK_PATTERN_LFSR) else 0) << 4) | 1 << 2) # SET_THROTTLE = 1 | MODE = LFSR | RESET = 1
        dev.UpdateWireIns()
        dev.SetWireInValue(0x00, 0 << 5 | (
                    (1 if (selected_pattern == OK_PATTERN_LFSR) else 0) << 4) | 0 << 2) # SET_THROTTLE = 0 | MODE = LFSR | RESET = 0
        dev.UpdateWireIns()

    start_time = time.time()
    for i in range(transfer_settings.count):

        # create sample data array
        input_buffer = bytearray(transfer_settings.segment_size)

        if read_write == 'WRITE':
            if transfer_settings.block_size == 0:
                ret = dev.WriteToPipeIn(0x80, input_buffer)
            else:
                ret = dev.WriteToBlockPipeIn(0x80, transfer_settings.block_size, input_buffer)
        else:
            buff = bytearray(transfer_settings.segment_size)
            if transfer_settings.block_size == 0:
                ret = dev.ReadFromPipeOut(0xA0, buff)
            else:
                ret = dev.ReadFromBlockPipeOut(0xA0, transfer_settings.block_size, buff)

        if ret < 0:
            # error reported
            if ret == ok.okCFrontPanel.InvalidBlockSize:
                reportUnsupported(read_write, transfer_settings, "Block Size not Supported!")
                break
            elif ret == ok.okCFrontPanel.UnsupportedFeature:
                reportUnsupported(read_write, transfer_settings, "Unsupported feature!")
                break
            else:
                print("Transfer Failed with error {}".format(ret))
            if not dev.IsOpen():
                print("Device disconnected")
                sys.exit(-1)
    else:
        # if the loop ended normally (no breaks => no errors)
        duration = time.time() - start_time
        transfer_speed_MiBs = transfer_settings.segment_size*transfer_settings.count / (1024*1024*duration)
        reportBandwidthResults(read_write, transfer_settings, duration, transfer_speed_MiBs)


def reportBandwidthResults(read_write, transfer_settings, duration, transfer_speed_MiBs):
    print("{:5} Block Size: {:8.2f}B \tSS:{:10.2f}kB \tTS:{:8.2f}kB \tDuration: {:.3f}sec -- {:6.2f} MiB/s ".format(
                                                                 read_write,
                                                                transfer_settings.block_size,
                                                                transfer_settings.segment_size/1024,
                                                                 transfer_settings.segment_size * transfer_settings.count/1024,
                                                                 duration,
                                                                 transfer_speed_MiBs))

def reportUnsupported(read_write, transfer_settings, error_info):
    print("{:5} Block Size: {:8.2f}B \tSS:{:10.2f}kB \tTS:{:8.2f}kB \t{}".format(read_write,
                                                                                transfer_settings.block_size,
                                                                                transfer_settings.segment_size/1024,
                                                                                transfer_settings.segment_size * transfer_settings.count/1024,
                                                                                error_info))


def parse_args():

    test_type = TestbenchType.pipes
    custom_transfer = None

    if len(sys.argv) < 2:
        print("Path to bitfile not provided!")
        print_help()
        sys.exit(1)

    if len(sys.argv) >= 3:
        if sys.argv[2] == 'wires':
            test_type = TestbenchType.wires
        elif sys.argv[2] == 'triggers':
            test_type = TestbenchType.triggers
        elif len(sys.argv) > 3:
            custom_transfer = TransferSettings([int(sys.argv[3]), int(sys.argv[4]), 10])

    return test_type, custom_transfer



def print_help():
    print("PipeTest.py syntax:\npython PipeTest.py path_to_bitfile [params]")
    print("params:")
    print("\twires: \texecutes wires testbench\n"
          "\ttriggers: \texecutes triggers testbench\n"
          "\tpipes [BLOCK_SIZE TRANSFER_SIZE]:\texecutes pipes testbench, if no BLOCK_SIZE and TRANSFER_SIZE provided (in bytes)"
          "performs default testbench, otherwise performs test only for a given setting")


def main(type=TestbenchType.pipes, custom_transfer=None):

    print("------ PipeTest Application fot Python API ----------")
    print("Front Panel API version: {}".format(ok.okCFrontPanel_GetAPIVersionString()))

    dev = ok.okCFrontPanel()
    error_code = dev.OpenBySerial("")
    if error_code != 0:
        print('Could not open the device.')
        print(error_code)
        sys.exit(1)

    if not initialize_FPGA(dev, sys.argv[1]):
        print("FPGA could not be initialized.")
        sys.exit(1)

    if type == TestbenchType.triggers:
        print('Starting benchmark: triggers...')
        BenchmarkTriggers(dev)
    elif type == TestbenchType.wires:
        print('Starting benchmark: wires...')
        BenchmarkWires(dev)
    else:
        print('Starting benchmark: pipes...')
        BenchmarkPipes(dev, custom_transfer)


if __name__ == '__main__':
    test_type, custom = parse_args()
    main(test_type, custom)


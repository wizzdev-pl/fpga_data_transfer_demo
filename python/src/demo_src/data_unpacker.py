import sys
import os
import time
import numpy as np
import struct

import queue
import threading


class DataUnpacker:
    def __init__(self, packet_length_in_bytes, number_of_channels):
        self.last_id = -1
        self.packet_length = packet_length_in_bytes
        self.number_of_channels = number_of_channels

        self.should_stop = False
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._run, name="Data unpacker")

        self.all_received = 0
        self.with_incorrect_id = 0
        self.with_incorrect_checksum = 0
        self.unpacked_data_handler = None

    def add_buffer_to_queue(self, buffer):
        self.queue.put(buffer)

    def add_data_handler(self, data_handler):
        self.unpacked_data_handler = data_handler

    def _run(self):
        while True:
            should_stop =  self.should_stop and self.queue.empty()
            if should_stop:
                break
            if self.queue.empty():
                time.sleep(0.01)
            else:
                buffer = self.queue.get()
                self.process_buffer(buffer)
                self.queue.task_done()

    def process_buffer(self, buffer):
        data = self.unpack_from_buffer(buffer)
        data = data.transpose()
        if self.unpacked_data_handler is not None:
            self.unpacked_data_handler.add_buffer(data)

    def stop(self):
        self.should_stop = True
        self.thread.join()

    def start(self):
        self.thread.start()

    def validate_checksum(self, packet):
        buff_int = struct.unpack('<{}H'.format(len(packet) // 2), packet)
        temp_checksum = 0
        for i in range((len(buff_int) // 2) - 1):
            temp_checksum += (buff_int[2 * i] << 16) + buff_int[2 * i + 1]
            temp_checksum = temp_checksum % (2 ** 32)

        return temp_checksum == ((buff_int[-2] << 16) + buff_int[-1])

    def unpack_package(self, packet) -> np.array:
        self.all_received += 1

        wrong_checksum = False
        wrong_id = False

        packet_id = struct.unpack('<2H', packet[:4])
        packet_id = (packet_id[0]<<16) + packet_id[1]

        if (packet_id != self.last_id+1) and (packet_id !=0):
            self.with_incorrect_id += 1
            wrong_id = True
        else:
            self.last_id = packet_id

        if not self.validate_checksum(packet):
            self.with_incorrect_checksum += 1
            wrong_checksum = True

        #buff_int = struct.unpack('<{}H'.format(self.number_of_channels), packet[4:-4])
        dt = np.dtype(np.uint16)
        dt.newbyteorder('<')
        buff_array = np.frombuffer(packet[4:-4], dtype=dt)
        buff_array = buff_array.reshape((len(buff_array)//self.number_of_channels), self.number_of_channels)
        buff_array = buff_array.transpose()
        return buff_array

    def unpack_from_buffer(self, buff):
        unpacked_array = None
        while len(buff) >= self.packet_length:
            packet = buff[:self.packet_length]
            del buff[:self.packet_length]
            if unpacked_array is None:
                unpacked_array = self.unpack_package(packet)
            else:
                unpacked_array = np.concatenate((unpacked_array, self.unpack_package(packet)), axis=1)
        return unpacked_array

    def read_from_file_and_unpack(self, file_path):
        with open(file_path, 'rb') as file:
            buff = file.read()
            buff = bytearray(buff)
            unpacked_data = self.unpack_from_buffer(buff)
        return unpacked_data

    def print_summary(self):
        print('Packets read: {}, with wrong checksums: {}, with wrong ids: {}'.format(
            self.all_received,
            self.with_incorrect_checksum,
            self.with_incorrect_id))
        print('Unpacked {} bytes of data total.'.format(self.all_received*self.packet_length))


if __name__ == '__main__':

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        print('File to read not provided')
        sys.exit(1)

    du = DataUnpacker()
    start = time.time()
    du.read_from_file_and_unpack(file_path)
    print("Execution time: {} seconds".format(time.time()-start))




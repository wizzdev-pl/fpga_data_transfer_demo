import threading
import queue
import time
import numpy as np

from .write_to_hdf5 import Hdf5Writer


class FileWriter:
    BUFFERS_TO_WRITE = 100

    def __init__(self, sampling_interval):
        self.hdf5_wirter = Hdf5Writer()
        self.should_stop = False
        self.first_buffer = True
        self.sampling_interval=sampling_interval
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._run, name="File writer")

        self._buffer_to_write = None
        self._buffers_list_to_write = []
        self._buffers_counter = 0

    def open_file(self, file_path, number_of_columns):
        self.hdf5_wirter.open_file(file_path, number_of_columns)

    def add_buffer_to_queue(self, buffer):
        self.queue.put(buffer)

    def _run(self):
        while True:
            should_stop =  self.should_stop and self.queue.empty()
            if should_stop:
                break
            if self.queue.empty():
                time.sleep(0.01)
            else:
                buffer = self.queue.get()
                if self.first_buffer:
                    self.add_file_attributes()
                self.process_buffer(buffer)
                self.queue.task_done()
        self.hdf5_wirter.close_file()

    def process_buffer_concatenating(self, buffer):
        # concatenating
        if self._buffer_to_write is None:
            self._buffer_to_write = buffer
        else:
            self._buffer_to_write = np.concatenate((self._buffer_to_write, buffer))
        self._buffers_counter += 1
        if self._buffers_counter % self.BUFFERS_TO_WRITE == 0:
            self.hdf5_wirter.append_data(self._buffer_to_write)
            self._buffer_to_write = None

    def process_buffer(self, buffer):
        # list and append
        self._buffers_list_to_write.append(buffer)
        self._buffers_counter += 1
        if self._buffers_counter % self.BUFFERS_TO_WRITE == 0:
            self.hdf5_wirter.append_data(np.concatenate(self._buffers_list_to_write))
            self._buffers_list_to_write = []

    def add_file_attributes(self):
        self.hdf5_wirter.add_attribute('start_time', time.time())
        self.hdf5_wirter.add_attribute('sampling_interval', self.sampling_interval)
        self.first_buffer = False

    def stop(self):
        self.should_stop = True
        self.thread.join()

    def start(self):
        self.thread.start()


if __name__ == '__main__':
    import numpy as np
    PACKETS_IN_BUFFER = 16 * 1024 // 64

    num_of_channels = 28
    file_writer = FileWriter()
    file_writer.open_file('test.h5', num_of_channels)
    file_writer.start()
    data = np.arange(PACKETS_IN_BUFFER* num_of_channels, dtype=np.uint16)
    data = data.reshape((PACKETS_IN_BUFFER, num_of_channels))
    data = data.astype('uint16')
    start = time.time()
    for i in range(10000):
        file_writer.add_buffer_to_queue(data)

    file_writer.stop()
    print(time.time()-start)



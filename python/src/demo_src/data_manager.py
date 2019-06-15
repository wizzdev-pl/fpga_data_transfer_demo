import queue
import time
import threading

class DataManager:
    def __init__(self):
        self.should_stop = False
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._run, name="Data manager")
        self._list_with_all_data_sinks = []

    def add_buffer(self, buffer):
        self.queue.put(buffer)

    def add_data_sink(self, data_sink):
        self._list_with_all_data_sinks.append(data_sink)

    def remove_data_sink(self, data_sink):
        self._list_with_all_data_sinks.remove(data_sink)

    def _run(self):
        while True:
            should_stop =  self.should_stop and self.queue.empty()
            if should_stop:
                break
            if self.queue.empty():
                time.sleep(0.01)
            else:
                buffer = self.queue.get()
                for sink in self._list_with_all_data_sinks:
                    sink.add_buffer_to_queue(buffer)
                self.queue.task_done()

    def stop(self):
        self.should_stop = True
        self.thread.join()

    def start(self):
        self.thread.start()


if __name__ == '__main__':
    import numpy as np
    from file_writer import FileWriter
    file_writer = FileWriter()
    file_writer.open_file('test.h5', 2)
    file_writer.start()
    data_manager = DataManager()
    data_manager.add_data_sink(file_writer)
    data_manager.start()
    data = np.arange(500* 2, dtype=np.uint16)
    data = data.reshape((500, 2))
    data = data.astype('uint16')
    data_manager.add_buffer(data)
    data_manager.add_buffer(data)
    data_manager.add_buffer(data)
    data_manager.add_buffer(data)
    data_manager.add_buffer(data)
    data_manager.add_buffer(data)
    data_manager.add_buffer(data)
    data_manager.add_buffer(data)
    data_manager.add_buffer(data)
    data_manager.add_buffer(data)
    data_manager.add_buffer(data)
    data_manager.add_buffer(data)
    data_manager.stop()
    file_writer.stop()
    file_writer.stop()

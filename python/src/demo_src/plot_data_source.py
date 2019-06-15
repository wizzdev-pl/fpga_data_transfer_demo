import threading
import queue
import time
import numpy as np
import copy


class PlotData:
    def __init__(self, number_of_channels, sampling_rate_Hz):
        self.number_of_channels = number_of_channels
        self._data = []
        self.min_time = 0
        self.max_time = 0
        self.sampling_rate = sampling_rate_Hz

        for i in range(number_of_channels):
            # create empty dicts for every channel:
            self._data.append({'values': None, 'time': None})

    def append_data(self, buffer):
        buffer = buffer.transpose()
        for i in range(self.number_of_channels):
            if self._data[i]['values'] is None:
                self._data[i]['values'] = buffer[i][:]
                self._data[i]['time'] = self.max_time+(np.arange(buffer.shape[1])+1)/self.sampling_rate
            else:
                self._data[i]['time'] = np.concatenate((self._data[i]['time'], self.max_time+(np.arange(buffer.shape[1]))/self.sampling_rate))
                self._data[i]['values'] = np.concatenate((self._data[i]['values'], buffer[i]))

            assert self._data[i]['values'].shape == self._data[i]['time'].shape

        self.max_time = self._data[-1]['time'][-1]

    def get_data_channel(self, channel, time_span):
        time_span = int(time_span*self.sampling_rate)
        data_to_copy = {}
        data_to_copy['values'] = self._data[channel]['values'][-time_span:]
        data_to_copy['time'] = self._data[channel]['time'][-time_span:]
        return copy.deepcopy(data_to_copy)


    def get_data(self):
        return copy.deepcopy(self._data)

    def get_available_time_span(self):
        return self.max_time-self.min_time


class PlotDataSource:
    def __init__(self, number_of_channels, sampling_rate_Hz):
        self.plot_data = PlotData(number_of_channels, sampling_rate_Hz)
        self.should_stop = False
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._run, name="Plot data source")
        self._lock = threading.Lock()


    def add_buffer_to_queue(self, buffer):
        with self._lock:
            self.queue.put(buffer)

    def _run(self):
        while True:
            # should_stop = self.should_stop and self.queue.empty()
            # dont wait to empty the queue
            if self.should_stop:
                break
            if self.queue.empty():
                time.sleep(0.01)
            else:
                buffer = self.queue.get()
                with self._lock:
                    self.process_buffer(buffer)
                self.queue.task_done()

    def get_available_time_span(self):
        with self._lock:
            time_span = self.plot_data.get_available_time_span()
            return time_span

    def get_available_channels(self):
        return list(range(self.plot_data.number_of_channels))

    def get_data(self, channel=None, time_span=None):
        with self._lock:
            if channel is None:
                return self.plot_data.get_data()
            elif type(channel) == int:
                return self.plot_data.get_data_channel(channel, time_span)
            elif type(channel) == list:
                return [self.plot_data.get_data_channel(i, time_span) for i in channel]

    def process_buffer(self, buffer):
        self.plot_data.append_data(buffer)

    def stop(self):
        self.should_stop = True
        self.thread.join()

    def start(self):
        self.thread.start()
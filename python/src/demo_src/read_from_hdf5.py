import h5py
import numpy as np
import copy


from demo_src.plot_data_source import PlotData


class HDF5FileReader:
    def __init__(self, file_path):
        self.file = h5py.File(file_path, 'r')

        group_name = list(self.file.keys())[0]
        self.group = self.file[group_name]
        data_set_name = list(self.group.keys())[0]
        self.data_set = self.group[data_set_name]

        self.number_of_sources = self.data_set.shape[1]
        self.time_span = self.data_set.shape[0]

        self.start_time = self.data_set.attrs['start_time']
        self.sampling_interval = self.data_set.attrs['sampling_interval']
        self.sampling_rate = int(1/self.sampling_interval)

        self.plot_data = PlotData(self.number_of_sources, self.sampling_rate)

    def load_plot_data(self):
        self.plot_data.append_data(self.data_set[:])

    def get_data(self, channel, time_span):
        if type(channel) == list:
            return [self.plot_data.get_data_channel(i, self.time_span) for i in channel]
        elif type(channel) == int:
            return self.plot_data.get_data_channel(channel, self.time_span)

    def get_available_channels(self):
        return list(range(self.plot_data.number_of_channels))

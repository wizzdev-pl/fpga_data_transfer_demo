import h5py
import numpy as np


class Hdf5Writer:
    MAX_CHUNK_LENGTH = 1024

    def __init__(self):
        self.file = None
        self._group = None
        self._data_set = None

    def __del__(self):
        self.close_file()

    def open_file(self, file_path:str, number_of_columns):
        self.file = h5py.File(file_path, 'w')
        self._group = self.file.create_group("data")
        self._data_set = self._group.create_dataset("data_set",
                                                    shape=(0, number_of_columns),
                                                    maxshape=(None, number_of_columns),
                                                    dtype='u2',
                                                    chunks=(self.MAX_CHUNK_LENGTH, number_of_columns))
    def add_attribute(self, name, value):
        # it is recommended to access attributes that way, but how to specify data types then?
        self._data_set.attrs[name] = value

    def close_file(self):
        if self.file:
            self.file.close()
            self.file = None

    def append_data(self, data:np.array):
        shape = self._data_set.shape
        self._data_set.resize((shape[0]+data.shape[0], data.shape[1]))
        self._data_set[shape[0]:,:] = data


if __name__ == '__main__':
    write = Hdf5Writer()
    write.open_file("test.h5", 100)
    for i in range(10):
        data = i* np.arange(100, dtype=np.uint16)
        data = data.reshape((1, 100))
        data = data.astype('uint16')
        write.append_data(data)



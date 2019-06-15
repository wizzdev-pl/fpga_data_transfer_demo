FPGA Data Transfer is a simple & exemplary project designed for high speed data acquisition.

Main two parts of this project are:
* FPGA program (written in VHDL) responsible for data generation and transmission,
* Python GUI application handling communication with the board, visualizing received data, and writing them to hdf5 file.


## Requirements:

(tested with)

	system: Ubuntu 18.04
	tools: 	Xilinx Vivado WebPack (2018.3 or newer)
		Opal Kelly FrontPanel (Python3 API & HDL sources)
		Python3.6

### Python3 required packages

All required packages are listed in requirements.txt file in the python sources directory. All but one can be installed by calling :

		pip install -r requirements.txt

while pyqtgraph must be installed from devel branch from its git repository as its latest release does not support Pyside2:

		pip install git+https://github.com/pyqtgraph/pyqtgraph
 

FPGA Data Transfer is a simple & exemplary project designed for high speed data acquisition.

Main two parts of this project are:
* FPGA program (written in VHDL) responsible for data generation and transmission,
* Python GUI application handling communication with the board, visualizing received data, and writing them to hdf5 file.


##Requirements:
(tested with)
	system: Ubuntu 18.04
	tools: 	Xilinx Vivado WebPack (2018.3 or newer)
		Opal Kelly FrontPanel (Python3 API & HDL sources)
		Python3.6 

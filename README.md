
# FPGA Data Transfer demo
is a simple & exemplary project designed for high speed data acquisition.

Main two parts of this project are:
* FPGA program (written in VHDL) responsible for data generation and transmission,
* Python GUI application handling communication with the board, visualizing received data, and writing them to hdf5 file.


## Requirements:

#### Hardware:
- Opal Kelly XEM7310   FPGA integration module
- PC with USB3.0 interface

#### Software
- system: Ubuntu 18.04
- tools: 	
	- Xilinx Vivado WebPack (2018.3 or newer)
	- Opal Kelly FrontPanel (Python3 API & HDL sources)
	- Python3.6 

 
## Before first run
Opal Kelly **FrontPanel HDL** files for a correct board must be added to your Vivado project, as well as **FrontPanel API** files for Python3 must be located in the `fpga_data_transfer_demo/python/FrontPanelAPI`  directory

## Generating bitstream for FPGA
Project in Vivado must be set up, and all files from `fpga_data_transfer_demo/vhdl_src` folder (and its subfolders) added to it. 
If you are not familiar with Vivado,  you can look into our [blog post](https://wizzdev.pl/blog/fpga-data-transfer-demo-2/) in which the whole process is described step by step.

Generated bitstream  is then needed by the GUI application, which will use it to program the FPGA. Remember the values of :  
- number of sources, 
- sampling frequency and 
- packet size, 

as they will be needed to guarantee correct data reception.
You can change the name of a bitfile to follow this scheme:
	
		4_1k_512B.bit
where: 4 is the number of sources, 1k is 1kHz sampling rate and 512B means 512 byte packet length. This way the Python application will automatically load these values, otherwise you can just type them by hand.

## Running Python GUI application

We recommend creating a separate virtual environment for the python project.
		
	python3 -m venv venv
 Activate the environment:
 
	source venv/bin/activate

All required packages are listed in requirements.txt file in the /python  directory. All but one can be installed by calling :

	pip install -r requirements.txt

while *pyqtgraph* must be installed from devel branch from its git repository as its latest release does not support Pyside2:

	pip install git+https://github.com/pyqtgraph/pyqtgraph

Now GUI application can be started by calling:
	
	python start_gui.py
assuming you are currently in `fpga_data_transfer_demo/python/src` directory, else just provide the full, or relative path to the *start_gui.py* script.


## ...
More info about the project can be found on our website:
https://wizzdev.pl/blog/category/fpga-projects/

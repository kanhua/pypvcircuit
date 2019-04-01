import pypvcircuit.config_tool as config
import sys

ngspice_path=sys.argv[1]
output_path = sys.argv[2]
spice_output_path = sys.argv[3]

#ngspice_path=r'C:\Users\kanhu\OneDrive\Documents\solcore5_install_lab\ngspice-28_64\Spice64\bin\ngspice.exe'
config.set_location_of_spice(ngspice_path)
config.set_location_of_output(output_path)
config.set_location_of_spice_output(spice_output_path)

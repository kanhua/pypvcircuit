import spice.config_tools as config
import sys

ngspice_path=sys.argv[1]

#ngspice_path=r'C:\Users\kanhu\OneDrive\Documents\solcore5_install_lab\ngspice-28_64\Spice64\bin\ngspice.exe'
config.set_location_of_spice(ngspice_path)

import numpy as np
import matplotlib.pyplot as plt
from skimage.io import imread

from solcore.structure import Junction

from solcore.solar_cell import SolarCell
from solcore.light_source import LightSource
from spice.dynamic_pixel import solve_quasi_3D

illuminationMask = imread(
    '/Users/kanhua/Dropbox/Programming/solar-cell-circuit/private_data/Illumination_profile_20181016.png')
contactsMask = imread('/Users/kanhua/Dropbox/Programming/solar-cell-circuit/private_data/Mask_profile_20181016.png')

illuminationMask = illuminationMask[:, :, 0]
contactsMask = contactsMask[:, :, 0]

assert illuminationMask.shape == contactsMask.shape

print(np.max(illuminationMask))
print(np.max(contactsMask))

nx, ny = illuminationMask.shape

# For symmetry arguments (not completely true for the illumination), we can mode just 1/4 of the device and then
# multiply the current by 4
center_x = int(nx / 2)
center_y = int(ny / 2)

dx = 200
dy = 200
illuminationMask = illuminationMask[center_x:center_x + dx, center_y:center_y + dy]
contactsMask = contactsMask[center_x:center_x + dx, center_y:center_y + dy]

# Size of the pixels (m)
Lx = 10e-3
Ly = 10e-3

# Height of the metal fingers (m)
h = 2.2e-6

# Contact resistance (Ohm m2)
Rcontact = 3e-10

# Resistivity metal fingers (Ohm m)
Rline = 2e-8

# Bias (V)
vini = 0
vfin = 2.0
step = 0.01

T = 298

# For a single junction, this will have >28800 nodes and for the full 3J it will be >86400, so it is worth to
# exploit symmetries whenever possible. A smaller number of nodes also makes the solver more robust.

wl = np.linspace(350, 2000, 301) * 1e-9
light_source = LightSource(source_type='standard', version='AM1.5g', x=wl, output_units='photon_flux_per_m',
                           concentration=100)

options = {'light_iv': True, 'wavelength': wl, 'light_source': light_source}

test_pixel_width = [5]

for pw in test_pixel_width:
    db_junction3 = Junction(kind='2D', T=T, reff=0.5, jref=300, Eg=1.8, A=1, R_sheet_top=100,
                            R_sheet_bot=100,
                            R_shunt=1e16, n=3.5)
    my_solar_cell = SolarCell([db_junction3], T=T)
    V, I = solve_quasi_3D(my_solar_cell, illuminationMask, contactsMask, options=options, Lx=Lx,
                                      Ly=Ly,
                                      h=h,
                                      R_back=1e-16, R_contact=Rcontact, R_line=Rline, bias_start=vini,
                                      bias_end=vfin,
                                      bias_step=step, sub_cw=pw, sub_rw=pw)

    plt.plot(V, I, label="pw: {}".format(pw))

plt.ylim([np.min(I) * 1.1, 0])
plt.show()

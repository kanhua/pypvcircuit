import unittest
import timeit
import os
import numpy as np
import matplotlib.pyplot as plt
import typing
from skimage.io import imread, imsave

from pypvcell.solarcell import SQCell, MJCell
from pypvcell.illumination import load_astm
from pypvcell.fom import isc, ff

from .helper import draw_contact_and_voltage_map, draw_merged_contact_images, \
    get_quater_image, contact_ratio, draw_illumination_3d

from pypvcircuit.parse_spice_input import NodeReducer
from pypvcircuit.spice_solver import SPICESolver, SPICESolver3D
from pypvcircuit.util import make_3d_illumination, gen_profile, HighResGrid, MetalGrid
from pypvcircuit.import_tool import RayData

import yaml


class MyTestCase(unittest.TestCase):
    def test_series_r(self):
        # Size of the pixels (m)
        l_r = 1e-6
        l_c = 1e-6

        h = 2.2e-6

        # Start voltage
        vini = -0.1
        # End voltage
        vfin = 3.5
        # Voltage step
        step = 0.01

        # cell temperature in Kelvins
        T = 298

        r_range = np.array([1e-7, 1e-6, 3e-6, 5e-6])
        mask_filepath = './private_data/Mask_profile_20181016.png'

        contactsMask = imread(mask_filepath)
        contactsMask = contactsMask[:, :, 0]
        nx, ny = contactsMask.shape
        concentration = 1
        illuminationMask = np.ones((nx, ny)) * concentration

        nd = NodeReducer()

        top_cell_eg = 1.87
        middle_cell_eg = 1.42
        bottom_cell_eg = 0.93

        top_cell_rad_eta = 5e-3
        middle_cell_rad_eta = 1e-2
        bottom_cell_rad_eta = 1e-4

        gaas_cell = SQCell(middle_cell_eg, T, middle_cell_rad_eta)
        ingap_cell = SQCell(top_cell_eg, T, top_cell_rad_eta)
        ge_cell = SQCell(bottom_cell_eg, T, bottom_cell_rad_eta)

        solar_cell_1 = MJCell([ingap_cell, gaas_cell, ge_cell])

        fill_factor_array = np.empty(len(r_range))
        for idx, res in enumerate(r_range):
            sps = SPICESolver(solarcell=solar_cell_1, illumination=illuminationMask,
                              metal_contact=contactsMask, rw=25, cw=25,
                              v_start=vini, v_end=vfin,
                              v_steps=step, l_r=l_r, l_c=l_c, h=h,
                              spice_preprocessor=nd, lump_series_r=res)
            # plt.plot(sps.V, sps.I)
            ff_value = ff(sps.V, sps.I)

            fill_factor_array[idx] = ff_value

            print("FF:{}".format(ff_value))

        plt.plot(r_range, fill_factor_array)
        plt.xlabel("resistance")
        plt.ylabel("fill factors")

        plt.show()

    def test_concentration(self):
        # Size of the pixels (m)
        l_r = 1e-6
        l_c = 1e-6

        h = 2.2e-6

        # Start voltage
        vini = -0.1
        # End voltage
        vfin = 3.5
        # Voltage step
        step = 0.01

        # cell temperature in Kelvins
        T = 298

        mask_filepath = './private_data/Mask_profile_20181016.png'

        contactsMask = imread(mask_filepath)
        contactsMask = contactsMask[:, :, 0]
        nx, ny = contactsMask.shape
        contactsMask = contactsMask[:, int(ny / 2):]
        nx, ny = contactsMask.shape

        conc_range = np.array([1, 10, 100, 500, 800])
        lump_r = 1e-6

        nd = NodeReducer()

        top_cell_eg = 1.87
        middle_cell_eg = 1.42
        bottom_cell_eg = 0.93

        top_cell_rad_eta = 5e-3
        middle_cell_rad_eta = 1e-2
        bottom_cell_rad_eta = 1e-4

        gaas_cell = SQCell(middle_cell_eg, T, middle_cell_rad_eta)
        ingap_cell = SQCell(top_cell_eg, T, top_cell_rad_eta)
        ge_cell = SQCell(bottom_cell_eg, T, bottom_cell_rad_eta)

        solar_cell_1 = MJCell([ingap_cell, gaas_cell, ge_cell])

        ff_value_arr = np.empty(conc_range.shape)

        result_vi = None
        for idx, conc in enumerate(conc_range):
            illumination_mask = np.ones((nx, ny)) * conc
            sps = SPICESolver(solarcell=solar_cell_1, illumination=illumination_mask,
                              metal_contact=contactsMask, rw=10, cw=10, v_start=vini, v_end=vfin,
                              v_steps=step, l_r=l_r, l_c=l_c, h=h, spice_preprocessor=nd, lump_series_r=lump_r)
            ff_value = ff(sps.V, sps.I)
            print("FF:{}".format(ff_value))
            ff_value_arr[idx] = ff_value
            if result_vi is None:
                result_vi = np.stack((sps.V, sps.I))
            else:
                result_vi = np.vstack((result_vi, sps.V, sps.I))

        np.savetxt("concentrated_3j_iv_pw10.csv", result_vi.T, delimiter=',')

        plt.semilogx(conc_range, ff_value_arr)
        plt.xlabel("concentration")
        plt.ylabel("FF")
        plt.show()


if __name__ == '__main__':
    unittest.main()

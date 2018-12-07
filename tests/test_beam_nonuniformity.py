"""
This set tests the full solar cell equivalent circuit simulation, using the dynamically changing pixels.


"""

import unittest
import os
import copy
import numpy as np
import matplotlib.pyplot as plt
import typing
from skimage.io import imread, imsave

from pypvcell.solarcell import SQCell, MJCell
from spice.spice_solver import SPICESolver
from pypvcell.illumination import load_astm
from pypvcell.fom import isc, ff

from .helper import draw_contact_and_voltage_map, draw_merged_contact_images, get_quater_image

from spice.parse_spice_input import NodeReducer
from spice.util import default_mask, gen_profile


class BeamUniformityTest(unittest.TestCase):

    def setUp(self):
        file_path = os.path.abspath(os.path.dirname(__file__))

        self.output_data_path = os.path.join(file_path, 'test_output_data')

        self.T = 298

        # TODO simplify the illumination mask to np.ones
        # self.default_illuminationMask = imread(os.path.join(file_path, 'masks_illumination.png'))

        self.default_contactsMask = imread(os.path.join(file_path, 'masks_sq_no_shades.png'))

        self.default_illuminationMask = np.ones_like(self.default_contactsMask)

        # Size of the pixels (m)
        self.Lx = 10e-5
        self.Ly = 10e-5

        # Height of the metal fingers (m)
        self.h = 2.2e-6

        # Contact resistance (Ohm m2)
        self.Rcontact = 3e-10

        # Resistivity metal fingers (Ohm m)
        self.Rline = 2e-8

        # Bias (V)
        self.vini = 0
        self.vfin = 3.0
        self.step = 0.05

        self.gaas_1j = SQCell(1.42, 300, 1)
        self.ingap_1j = SQCell(1.87, 300, 1)


    def test_bunch_nonuniformity(self):

        self.test_nonuniformity(0.1)
        self.test_nonuniformity(0.8)
        self.test_nonuniformity(1.0)

    def test_nonuniformity(self, bound_ratio):
        """
        Test the solar cell results with different number of fingers

        :param grid_n: number of fingers
        :param pw: merged pixel width
        :return:
        """

        grid_n = 5
        pw = 5

        original_mask_image = default_mask(self.default_contactsMask.shape, finger_n=grid_n)

        metal_mask = get_quater_image(original_mask_image)

        # concentration should be ramped up to see the fill factor difference. Typically > 100
        illumination_mask = gen_profile(metal_mask.shape[0],
                                        metal_mask.shape[1], bound_ratio=bound_ratio,conc=100)

        nd = NodeReducer()

        self.gaas_1j.set_input_spectrum(load_astm("AM1.5g"))

        sps = SPICESolver(solarcell=self.gaas_1j, illumination=illumination_mask,
                          metal_contact=metal_mask, rw=pw, cw=pw, v_start=self.vini, v_end=self.vfin,
                          v_steps=self.step,
                          l_r=self.Lx, l_c=self.Ly, h=self.h, spice_preprocessor=nd)

        solver_isc = isc(sps.V, sps.I)

        # calculate the isc by detailed balance model
        is_metal = np.where(metal_mask > 0, 1, 0)

        # This line is critical: we have to reset the input spectrum of the test 1J gaas cell
        self.gaas_1j.set_input_spectrum(load_astm("AM1.5g"))
        estimated_isc = self.gaas_1j.jsc * self.Ly * self.Lx * np.sum(illumination_mask * is_metal)

        print("estimated isc:{}".format(estimated_isc))
        print("solver isc:{}".format(solver_isc))
        print("diff: {}".format(estimated_isc - solver_isc))
        print("fill factor: {}".format(ff(sps.V, -sps.I)))
        self.assertTrue(np.isclose(float(solver_isc), estimated_isc))


if __name__ == '__main__':
    unittest.main()

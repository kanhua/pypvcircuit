import unittest
from pypvcell.solarcell import SQCell
from pypvcircuit.pixel_processor import PixelProcessor
from pypvcircuit.spice_solver import SPICESolver, SinglePixelSolver
from pypvcircuit.parse_spice_input import reprocess_spice_input, NodeReducer
import os
from skimage.io import imread, imsave
import matplotlib.pyplot as plt
import numpy as np


class PixelProcessorTestCase(unittest.TestCase):
    def setUp(self):
        file_path = os.path.abspath(os.path.dirname(__file__))

        self.output_data_path = os.path.join(file_path, 'test_output_data')

        self.T = 298

        self.default_illuminationMask = imread(os.path.join(file_path, 'masks_illumination.png'))

        self.default_contactsMask = imread(os.path.join(file_path, 'masks_sq_no_shades.png'))

        # Size of the pixels (m)
        self.Lx = 10e-6
        self.Ly = 10e-6

        # Height of the metal fingers (m)
        self.h = 2.2e-6

        # Contact resistance (Ohm m2)
        self.Rcontact = 3e-10

        # Resistivity metal fingers (Ohm m)
        self.Rline = 2e-8

        # Bias (V)
        self.vini = 0
        self.vfin = 1.1
        self.step = 0.01

    def test_1(self):
        sq = SQCell(1.42, 300, 1)
        from pypvcell.illumination import load_astm

        ill = load_astm("AM1.5g")
        sq.set_input_spectrum(ill)
        px = PixelProcessor(sq, lr=1e-6, lc=1e-6)

    def test_2(self):
        sq = SQCell(1.42, 300, 1)

        sps = SPICESolver(solarcell=sq, illumination=self.default_illuminationMask,
                          metal_contact=self.default_contactsMask, rw=2, cw=2, v_start=self.vini, v_end=self.vfin,
                          v_steps=self.step,
                          l_r=self.Lx, l_c=self.Ly, h=self.h)

        plt.plot(sps.V, -sps.I)
        print(sps.I)
        plt.show()

        plt.figure()
        plt.imshow(sps.v_junc[:, :, -1])
        plt.show()

    def test_single_pixel(self):
        """
        Compare the values between pypvcell (SQCell) and
        single-pixel network simulation

        :return:
        """

        sq = SQCell(1.42, 300, 1)

        nd = NodeReducer()

        sps = SinglePixelSolver(solarcell=sq, illumination=1, v_start=0,
                                v_end=1.1, v_steps=0.01, l_r=1, l_c=1,
                                h=self.h, spice_preprocessor=nd)

        print(sq.j01)

        v, i = sq.get_iv(volt=np.linspace(0, 1.1, 250))

        print(v, i)
        plt.plot(v, i, label="pypvcell", alpha=0.5)
        plt.plot(sps.V, -sps.I, label="networksim", alpha=0.5)
        plt.xlabel("voltage (V)")
        plt.ylabel("current (A)")
        plt.legend()

        plt.show()


if __name__ == '__main__':
    unittest.main()

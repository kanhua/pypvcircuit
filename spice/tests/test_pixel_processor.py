import unittest
from pypvcell.solarcell import SQCell
from spice.pixel_processor import PixelProcessor
from spice.spice_solver import SPICESolver
import os
from skimage.io import imread, imsave
import matplotlib.pyplot as plt


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
        self.vfin = 3.0
        self.step = 0.01

    def test_1(self):
        sq = SQCell(1.42, 300, 1)
        from pypvcell.illumination import load_astm

        ill = load_astm("AM1.5g")
        sq.set_input_spectrum(ill)
        px = PixelProcessor(sq, lx=1e-6, ly=1e-6)
        print(px.node_string())

    def test_2(self):
        sq = SQCell(1.42, 300, 1)

        sps = SPICESolver(solarcell=sq, illumination=self.default_illuminationMask,
                          metal_contact=self.default_contactsMask, rw=2, cw=2, v_start=self.vini, v_end=self.vfin,
                          v_steps=self.step,
                          Lx=self.Lx, Ly=self.Ly, h=self.h)

        plt.plot(sps.V, -sps.I)
        print(sps.I)
        plt.show()

        plt.figure()
        plt.imshow(sps.v_junc[:, :, -1])
        plt.show()


if __name__ == '__main__':
    unittest.main()

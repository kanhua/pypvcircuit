import matplotlib.pyplot as plt
import pandas as pd
import unittest

from pypvcircuit.import_tool import to_ill_mtx, RayData
from pypvcircuit.spice_solver import SPICESolver3D

class ImportToolTestCase(unittest.TestCase):
    def test_to_ill_mtx(self):
        df = pd.read_csv("example_ray.csv")

        mtx, _ = to_ill_mtx(df, r_pixel=10, c_pixel=10, r_max=5,
                            r_min=-5, c_max=5, c_min=-5)

        self.assertEqual(mtx.shape[2], 2)
        self.assertEqual(mtx[0, -1, 0], 2)

    def test_read_rays_data(self):
        file = r"C:\Users\kanhu\OneDrive\Documents\LightTools-tutorial\exporty_rays_binary_1mm.1.ray"

        rd = RayData(file)

        ill_mtx, wavelength = rd.get_ill_mtx(r_pixel=100, c_pixel=100, r_max=0.5, r_min=-0.5,
                                             c_max=6.5, c_min=5.5)

        # plot a slice
        plt.plot(wavelength, ill_mtx[50, 50, :])
        plt.show()








if __name__ == '__main__':
    unittest.main()

"""
This module tests the 3d illumination I(x,y,z), where lambda(z) is the wavelength of the spectrum

"""

import unittest

import numpy as np
from pypvcell.illumination import load_astm
from pypvcell.spectrum import Spectrum
import matplotlib.pyplot as plt
from scipy.stats import multivariate_normal

from pypvcircuit.util import LinearAberration, make_3d_illumination


class IlluminationTestCase(unittest.TestCase):
    def test_initial_illumination(self):
        default_illumination = load_astm("AM1.5g")

        spec = default_illumination.get_spectrum(to_x_unit='nm')

        print(spec[0, :])

        plt.plot(*spec)
        plt.show()

    def test_2d_normal_random(self):
        """
        try 2d normal distribution random generator

        :return:
        """
        mean = [0, 0]
        cov = [[1, 0], [0, 100]]  # diagonal covariance

        x, y = np.random.multivariate_normal(mean, cov, 5000).T
        plt.plot(x, y, 'x')
        plt.axis('equal')

    def test_2d_scipy_normal(self):
        x, y = np.mgrid[-1:1:.01, -1:1:.01]
        pos = np.empty(x.shape + (2,))
        pos[:, :, 0] = x
        pos[:, :, 1] = y
        rv = multivariate_normal([0.5, -0.2], [[2.0, 0.3], [0.3, 0.5]])
        plt.contourf(x, y, rv.pdf(pos))

    def test_2d_scipy_normal_on_grids(self):
        x, y = np.mgrid[0:120:1, 0:120:1]
        pos = np.empty(x.shape + (2,))
        pos[:, :, 0] = x
        pos[:, :, 1] = y
        rv = multivariate_normal([60, 60], [[3000, 0], [0, 3000]])

        plt.contourf(x, y, rv.pdf(pos))

        plt.figure()
        plt.plot(np.arange(0, 120, 1), rv.pdf(pos)[60, :])

    def test_square_random(self):
        lb = LinearAberration(4000, 285, 0.6, 0.9)

        x = np.linspace(285, 4000, num=100)
        y = lb.get_abb(x)

        plt.plot(1 / x, y)
        plt.show()

    def test_make_3d_illumination(self):
        ill_mtx, wl = make_3d_illumination(60, 60)

        fig, ax = plt.subplots(nrows=1, ncols=2)
        ax[0].set_title("{:.1f} nm".format(wl[0]))
        ax[0].imshow(ill_mtx[:, :, 0])
        ax[1].set_title("{:.1f} nm".format(wl[-1]))
        ax[1].imshow(ill_mtx[:, :, -1])

        plt.show()

    def test_illumination_class(self):
        default_illumination = load_astm("AM1.5g")

        spec = default_illumination.get_spectrum(to_x_unit='nm')

        new_factor = np.ones_like(spec[1, :])

        plt.plot(*spec)

        new_illumination = default_illumination * new_factor
        spec2 = new_illumination.get_spectrum(to_x_unit='nm')

        plt.plot(*spec2)

        factor_sp = Spectrum(spec[0, :], new_factor, x_unit='nm')

        new_illumination = default_illumination * factor_sp

        spec3 = new_illumination.get_spectrum(to_x_unit='nm')

        plt.plot(*spec3)
        plt.show()


if __name__ == '__main__':
    unittest.main()

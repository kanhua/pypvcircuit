import unittest
import numpy as np
import matplotlib.pyplot as plt
from skimage.io import imread, imsave

from solcore.structure import Junction

from solcore.solar_cell import SolarCell
from solcore.light_source import LightSource
from ..dynamic_pixel import solve_quasi_3D


class MyTestCase(unittest.TestCase):

    def setUp(self):
        self.T = 298

        self.db_junction = Junction(kind='2D', T=self.T, reff=1, jref=300, Eg=0.66, A=1, R_sheet_top=100,
                                    R_sheet_bot=1e-16,
                                    R_shunt=1e16, n=3.5)
        self.db_junction2 = Junction(kind='2D', T=self.T, reff=1, jref=300, Eg=1.4, A=1, R_sheet_top=100,
                                     R_sheet_bot=1e-16,
                                     R_shunt=1e16, n=3.5)
        self.db_junction3 = Junction(kind='2D', T=self.T, reff=0.5, jref=300, Eg=1.8, A=1, R_sheet_top=100,
                                     R_sheet_bot=100,
                                     R_shunt=1e16, n=3.5)

        self.default_illuminationMask = imread(
            '/Users/kanhua/Dropbox/Programming/solcore5/examples/masks_illumination.png')
        self.default_contactsMask = imread('/Users/kanhua/Dropbox/Programming/solcore5/examples/masks_sq.png')

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

    def test_mj_circuit(self):
        """
        Compare isc of different pixel values

        :return:
        """
        illumination_mask = self.default_illuminationMask
        contacts_mask = self.default_contactsMask

        print(np.max(illumination_mask))
        print(np.max(contacts_mask))

        nx, ny = illumination_mask.shape

        # For symmetry arguments (not completely true for the illumination), we can mode just 1/4 of the device and then
        # multiply the current by 4
        center_x = int(nx / 2)
        center_y = int(ny / 2)
        illumination_mask = illumination_mask[center_x:center_x + 50, center_y:center_y + 50]
        contacts_mask = contacts_mask[center_x:center_x + 50, center_y:center_y + 50]

        imsave("ill1.png", illumination_mask)
        imsave("contact1.png", contacts_mask)

        # For a single junction, this will have >28800 nodes and for the full 3J it will be >86400, so it is worth to
        # exploit symmetries whenever possible. A smaller number of nodes also makes the solver more robust.

        wl = np.linspace(350, 2000, 301) * 1e-9
        light_source = LightSource(source_type='standard', version='AM1.5g', x=wl, output_units='photon_flux_per_m',
                                   concentration=100)

        options = {'light_iv': True, 'wavelength': wl, 'light_source': light_source}

        test_pixel_width = [1, 2, 3, 4]

        result_vi = None

        for pw in test_pixel_width:
            db_junction3 = Junction(kind='2D', T=self.T, reff=0.5, jref=300, Eg=1.8, A=1, R_sheet_top=100,
                                    R_sheet_bot=100,
                                    R_shunt=1e16, n=3.5)
            my_solar_cell = SolarCell([db_junction3], T=self.T)
            V, I, Vall, Vmet = solve_quasi_3D(my_solar_cell, illumination_mask, contacts_mask, options=options,
                                              Lx=self.Lx,
                                              Ly=self.Ly,
                                              h=self.h,
                                              R_back=1e-16, R_contact=self.Rcontact, R_line=self.Rline,
                                              bias_start=self.vini,
                                              bias_end=self.vfin,
                                              bias_step=self.step, sub_cw=pw, sub_rw=pw)

            if result_vi is None:
                result_vi = np.stack((V, I))
            else:
                result_vi = np.vstack((result_vi, V, I))
            plt.plot(V, I, label="pw: {}".format(pw))

        # plt.ylim([-0.03, 0])
        np.savetxt("ingap_iv.csv", result_vi.T, delimiter=',')
        plt.show()


    def test_larger_1j_circuit(self):

        illumination_mask = self.default_illuminationMask
        contacts_mask = self.default_contactsMask

        print(np.max(illumination_mask))
        print(np.max(contacts_mask))

        nx, ny = illumination_mask.shape

        # For symmetry arguments (not completely true for the illumination), we can mode just 1/4 of the device and then
        # multiply the current by 4
        center_x = int(nx / 2)
        center_y = int(ny / 2)
        illumination_mask = illumination_mask[center_x:, center_y:]
        contacts_mask = contacts_mask[center_x:, center_y:]

        imsave("ill1.png", illumination_mask)
        imsave("contact1.png", contacts_mask)

        # For a single junction, this will have >28800 nodes and for the full 3J it will be >86400, so it is worth to
        # exploit symmetries whenever possible. A smaller number of nodes also makes the solver more robust.

        wl = np.linspace(350, 2000, 301) * 1e-9
        light_source = LightSource(source_type='standard', version='AM1.5g', x=wl, output_units='photon_flux_per_m',
                                   concentration=100)

        options = {'light_iv': True, 'wavelength': wl, 'light_source': light_source}

        test_pixel_width = [1, 2, 3, 4]

        result_vi = None

        for pw in test_pixel_width:
            db_junction3 = Junction(kind='2D', T=self.T, reff=0.5, jref=300, Eg=1.8, A=1, R_sheet_top=100,
                                    R_sheet_bot=100,
                                    R_shunt=1e16, n=3.5)
            my_solar_cell = SolarCell([db_junction3], T=self.T)
            V, I, Vall, Vmet = solve_quasi_3D(my_solar_cell, illumination_mask, contacts_mask, options=options,
                                              Lx=self.Lx,
                                              Ly=self.Ly,
                                              h=self.h,
                                              R_back=1e-16, R_contact=self.Rcontact, R_line=self.Rline,
                                              bias_start=self.vini,
                                              bias_end=self.vfin,
                                              bias_step=self.step, sub_cw=pw, sub_rw=pw)

            if result_vi is None:
                result_vi = np.stack((V, I))
            else:
                result_vi = np.vstack((result_vi, V, I))
            plt.plot(V, I, label="pw: {}".format(pw))

        # plt.ylim([-0.03, 0])
        np.savetxt("ingap_iv.csv", result_vi.T, delimiter=',')
        plt.show()


if __name__ == '__main__':
    unittest.main()

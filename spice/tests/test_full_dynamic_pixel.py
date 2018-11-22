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

from solcore.structure import Junction
from solcore.solar_cell import SolarCell
from solcore.light_source import LightSource
from ..dynamic_pixel import solve_quasi_3D, get_merged_r_image


class FullSimulationWithDynamicPixel(unittest.TestCase):

    def setUp(self):

        file_path = os.path.abspath(os.path.dirname(__file__))

        self.output_data_path = os.path.join(file_path, 'test_output_data')

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

        wl = np.linspace(350, 2000, 301) * 1e-9
        light_source = LightSource(source_type='standard', version='AM1.5g', x=wl, output_units='photon_flux_per_m',
                                   concentration=100)

        self.baseline_options = {'light_iv': True, 'wavelength': wl, 'light_source': light_source}

    def test_small_1j(self):
        """
        Test the simulation of 1J diode with 50x50 pixels.

        :return:
        """


        illumination_mask = self.default_illuminationMask
        contacts_mask = self.default_contactsMask

        nx, ny = illumination_mask.shape

        # For symmetry arguments (not completely true for the illumination), we can mode just 1/4 of the device and then
        # multiply the current by 4
        center_x = int(nx / 2)
        center_y = int(ny / 2)
        illumination_mask = illumination_mask[center_x:center_x + 50, center_y:center_y + 50]
        contacts_mask = contacts_mask[center_x:center_x + 50, center_y:center_y + 50]

        # imsave("ill1.png", illumination_mask)
        # imsave("contact1.png", contacts_mask)

        # For a single junction, this will have >28800 nodes and for the full 3J it will be >86400, so it is worth to
        # exploit symmetries whenever possible. A smaller number of nodes also makes the solver more robust.

        test_pixel_width = [1, 2, 3, 4]

        result_vi = None

        for pw in test_pixel_width:
            db_junction3 = copy.copy(self.db_junction3)
            my_solar_cell = SolarCell([db_junction3], T=self.T)
            V, I, Vall, Vmet = solve_quasi_3D(my_solar_cell, illumination_mask, contacts_mask,
                                              options=self.baseline_options,
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
            # plt.plot(V, I, label="pw: {}".format(pw))

        # np.savetxt(os.path.join(self.output_data_path, "ingap_iv.csv"), result_vi.T, delimiter=',')
        # plt.show()

    def test_larger_1j_circuit(self):
        """
        Test 1J cell

        :return:
        """

        db_junction3 = copy.copy(self.db_junction3)

        self.run_larger_1j_circuit([db_junction3], "1j")

    def test_larger_3j_circuit(self):
        """
        Test 3J cell

        :return:
        """

        tj_cell = copy.deepcopy([self.db_junction3, self.db_junction2, self.db_junction])

        self.run_larger_1j_circuit(tj_cell, "3j")

    def draw_merged_contact_images(self, test_pws, file_prefix:str, contact_mask:np.ndarray):
        """
        Output an image "{}equiv_r_images.png".format(file_prefix)) to compare the contact images
        and their merged versions.

        :param test_pws: a list of different pixel widths
        :param file_prefix: prefix of the file.
        :param contact_mask: The profile of the metal contact
        :return:
        """

        fig, ax = plt.subplots(ncols=len(test_pws) + 1, figsize=(8, 6), dpi=300)
        for i, pw in enumerate(test_pws):
            r_image = get_merged_r_image(contact_mask, pw, pw)
            ax[i].imshow(r_image)
            ax[i].set_title("{} pixels".format(pw))
        r_image = get_merged_r_image(contact_mask, 1, 1)
        ax[-1].imshow(r_image)
        ax[-1].set_title("original")
        fig.savefig(os.path.join(self.output_data_path, "{}equiv_r_images.png".format(file_prefix)))

    def run_larger_1j_circuit(self, input_solar_cells: typing.List,
                              file_prefix: str, illumination_mask=None, contacts_mask=None):

        if illumination_mask is None:
            illumination_mask = self.default_illuminationMask

        if contacts_mask is None:
            contacts_mask = self.default_contactsMask

        nx, ny = illumination_mask.shape

        # For symmetry arguments (not completely true for the illumination), we can mode just 1/4 of the device and then
        # multiply the current by 4
        center_x = int(nx / 2)
        center_y = int(ny / 2)
        illumination_mask = illumination_mask[center_x:, center_y:]
        contacts_mask = contacts_mask[center_x:, center_y:]

        imsave(os.path.join(self.output_data_path, "{}_ill1.png".format(file_prefix)), illumination_mask)
        imsave(os.path.join(self.output_data_path, "{}_contact1.png".format(file_prefix)), contacts_mask)

        test_pixel_width = [2,3, 5, 10]

        self.draw_merged_contact_images(test_pixel_width, file_prefix, contacts_mask)

        result_vi = None

        for pw in test_pixel_width:
            my_solar_cell = SolarCell(copy.deepcopy(input_solar_cells), T=self.T)

            V, I, Vall, Vmet = solve_quasi_3D(my_solar_cell, illumination_mask, contacts_mask,
                                              options=self.baseline_options,
                                              Lx=self.Lx,
                                              Ly=self.Ly,
                                              h=self.h,
                                              R_back=1e-16, R_contact=self.Rcontact, R_line=self.Rline,
                                              bias_start=self.vini,
                                              bias_end=self.vfin,
                                              bias_step=self.step, sub_cw=pw, sub_rw=pw)

            np.save(os.path.join(self.output_data_path, "{}_vmap_{}.npy").format(file_prefix, pw), Vmet[:, :, -1])

            if result_vi is None:
                result_vi = np.stack((V, I))
            else:
                result_vi = np.vstack((result_vi, V, I))
            plt.plot(V, I, label="pw: {}".format(pw))

        # plt.ylim([-0.03, 0])
        np.savetxt(os.path.join(self.output_data_path, "{}_ingap_iv.csv".format(file_prefix)), result_vi.T,
                   delimiter=',')

        plt.savefig(os.path.join(self.output_data_path, "{}_1jfig.png".format(file_prefix)))


if __name__ == '__main__':
    unittest.main()

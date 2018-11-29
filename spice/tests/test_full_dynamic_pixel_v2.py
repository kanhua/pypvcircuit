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

from pypvcell.solarcell import SQCell
from spice.spice_solver import SPICESolver
from pypvcell.illumination import load_astm
from ..dynamic_pixel import solve_quasi_3D, get_merged_r_image

from spice.parse_spice_input import reprocess_spice_input, NodeReducer


class FullSimulationWithDynamicPixel(unittest.TestCase):

    def setUp(self):

        file_path = os.path.abspath(os.path.dirname(__file__))

        self.output_data_path = os.path.join(file_path, 'test_output_data')

        self.T = 298

        # TODO simplify the illumination mask to np.ones
        # self.default_illuminationMask = imread(os.path.join(file_path, 'masks_illumination.png'))

        self.default_contactsMask = imread(os.path.join(file_path, 'masks_sq_no_shades.png'))

        self.default_illuminationMask = np.ones_like(self.default_contactsMask)

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
        self.vfin = 1.3
        self.step = 0.05

        self.pvcell_1j = SQCell(1.42, 300, 1)

    def test_larger_1j_circuit(self):
        """
        Test 1J cell

        :return:
        """

        ill = load_astm("AM1.5g")

        self.pvcell_1j.set_input_spectrum(ill)

        self.run_larger_1j_circuit(self.pvcell_1j, file_prefix="1j")

    def test_larger_3j_circuit(self):
        """
        Test 3J cell

        :return:
        """

        tj_cell = copy.deepcopy([self.db_junction3, self.db_junction2, self.db_junction])

        self.run_larger_1j_circuit(tj_cell, "3j")

    def draw_merged_contact_images(self, test_pws, file_prefix: str, contact_mask: np.ndarray):
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
        plt.close(fig)

    def draw_contact_and_voltage_map(self, test_pws, file_prefix: str, contact_mask: np.ndarray):

        fig, ax = plt.subplots(nrows=2, ncols=len(test_pws) + 1, figsize=(8, 6), dpi=300)
        for i, pw in enumerate(test_pws):
            r_image = get_merged_r_image(contact_mask, pw, pw)
            ax[0, i].imshow(r_image)
            ax[0, i].set_title("{} pixels".format(pw))

            voltage_map = np.load(os.path.join(self.output_data_path, "{}_vmap_{}.npy").format(file_prefix, pw))

            ax[1, i].imshow(voltage_map)

        r_image = get_merged_r_image(contact_mask, 1, 1)
        ax[0, -1].imshow(r_image)
        ax[0, -1].set_title("original")
        fig.savefig(os.path.join(self.output_data_path, "{}_equiv_r_map_images.png".format(file_prefix)))
        plt.close(fig)

    def run_larger_1j_circuit(self, input_solar_cells: SQCell,
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

        test_pixel_width = [1, 2, 5, 10]

        self.draw_merged_contact_images(test_pixel_width, file_prefix, contacts_mask)

        result_vi = None

        print("original image shape:{},{}".format(*contacts_mask.shape))
        print("Jsc: {:2f} A/m^2".format(self.pvcell_1j.jsc))
        print("illumination total {}:".format(illumination_mask.sum()))

        plt.figure()

        for pw in test_pixel_width:

            nd = NodeReducer()

            sps = SPICESolver(solarcell=self.pvcell_1j, illumination=illumination_mask,
                              metal_contact=contacts_mask, rw=pw, cw=pw, v_start=self.vini, v_end=self.vfin,
                              v_steps=self.step,
                              Lx=self.Lx, Ly=self.Ly, h=self.h, spice_preprocessor=nd)

            np.save(os.path.join(self.output_data_path, "{}_vmap_{}.npy").format(file_prefix, pw),
                    sps.get_end_voltage_map())

            if result_vi is None:
                result_vi = np.stack((sps.V, sps.I))
            else:
                result_vi = np.vstack((result_vi, sps.V, sps.I))

            plt.plot(sps.V, sps.I, label="pw: {}".format(pw))

        self.draw_contact_and_voltage_map(test_pixel_width, file_prefix, contacts_mask)

        np.savetxt(os.path.join(self.output_data_path, "{}_ingap_iv.csv".format(file_prefix)), result_vi.T,
                   delimiter=',')

        plt.savefig(os.path.join(self.output_data_path, "{}_1jfig.png".format(file_prefix)))


if __name__ == '__main__':
    unittest.main()

"""
This set tests the full solar cell equivalent circuit simulation, using the dynamically changing pixels.


"""

import unittest
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

from spice.parse_spice_input import NodeReducer
from spice.spice_solver import SPICESolver, SPICESolver3D
from spice.util import make_3d_illumination, gen_profile


class SpiceSolverTest(unittest.TestCase):

    def setUp(self):

        file_path = os.path.abspath(os.path.dirname(__file__))

        self.output_data_path = os.path.join(file_path, 'test_output_data')

        self.T = 298

        # TODO simplify the illumination mask to np.ones
        # self.default_illuminationMask = imread(os.path.join(file_path, 'masks_illumination.png'))

        self.default_contactsMask = imread(os.path.join(file_path, 'masks_sq_no_shades.png'))

        self.default_illuminationMask = np.ones_like(self.default_contactsMask) * 100

        # Size of the pixels (m)
        self.lr = 10e-5
        self.lc = 10e-5

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
        self.ge_1j = SQCell(0.7, 300, 1)

    def test_jsc(self):

        self.test_jsc_consistency(pw=5)
        self.test_jsc_consistency(pw=10)

    def test_jsc_consistency(self, pw=5):
        """
        Test if jsc calculated by the SPICE solver is equal to the analytical result.

        :param pw: merged pixel width
        :return:
        """

        metal_mask = get_quater_image(self.default_contactsMask)
        illumination_mask = np.ones_like(metal_mask)

        nd = NodeReducer()

        self.gaas_1j.set_input_spectrum(load_astm("AM1.5g"))

        sps = SPICESolver(solarcell=self.gaas_1j, illumination=illumination_mask,
                          metal_contact=metal_mask, rw=pw, cw=pw, v_start=self.vini, v_end=self.vfin,
                          v_steps=self.step,
                          l_r=self.lr, l_c=self.lc, h=self.h, spice_preprocessor=nd)

        solver_isc = isc(sps.V, sps.I)

        # calculate the isc by detailed balance model
        not_metal = np.where(metal_mask > 0, 0, 1)

        # This line is critical: we have to reset the input spectrum of the test 1J gaas cell
        self.gaas_1j.set_input_spectrum(load_astm("AM1.5g"))
        estimated_isc = self.gaas_1j.jsc * self.lc * self.lr * np.sum(illumination_mask * not_metal)

        print("estimated isc:{}".format(estimated_isc))
        print("solver isc:{}".format(solver_isc))
        print("diff: {}".format(estimated_isc - solver_isc))
        self.assertTrue(np.isclose(float(solver_isc), estimated_isc))

    def test_3d_illumination_naive(self):

        """
        This test checks if SPICESolver3D and SPICESolver gives the same result if the illumination matrix is identity

        :return:
        """

        pw = 5

        metal_mask = get_quater_image(self.default_contactsMask)

        illumination_mask_3d, _ = make_3d_illumination(5, 5)

        illumination_mask_3d = np.ones(metal_mask.shape + (illumination_mask_3d.shape[2],))

        illumination_mask_2d = np.ones_like(metal_mask)

        nd = NodeReducer()

        self.gaas_1j.set_input_spectrum(load_astm("AM1.5g"))

        sps = SPICESolver3D(solarcell=self.gaas_1j, illumination=illumination_mask_3d,
                            metal_contact=metal_mask, rw=pw, cw=pw, v_start=self.vini, v_end=self.vfin,
                            v_steps=self.step,
                            l_r=self.lr, l_c=self.lc, h=self.h, spice_preprocessor=nd)

        sps_2d = SPICESolver(solarcell=self.gaas_1j, illumination=illumination_mask_2d,
                             metal_contact=metal_mask, rw=pw, cw=pw, v_start=self.vini, v_end=self.vfin,
                             v_steps=self.step,
                             l_r=self.lr, l_c=self.lc, h=self.h, spice_preprocessor=nd)

        self.assertTrue(np.allclose(sps.I, sps_2d.I))

    def test_3d_illumination(self):
        """
        Test if 3D illumination can run successfully on 1J cell

        :return:
        """

        pw = 5

        vfin = 1.1
        step = 0.02

        metal_mask = get_quater_image(self.default_contactsMask)
        plt.figure()

        plt.imshow(metal_mask)
        plt.show()

        print(contact_ratio(metal_mask, threshold=0))

        illumination_mask_3d, wl = make_3d_illumination(*metal_mask.shape)

        fig, ax = draw_illumination_3d(illumination_mask_3d, wl, [0, -1])

        fig.savefig(os.path.join(self.output_data_path, 'abberated_profile.png'), dpi=300)

        fig.show()

        illumination_mask_2d = gen_profile(metal_mask.shape[0], metal_mask.shape[1], bound_ratio=0.6)

        nd = NodeReducer()

        self.gaas_1j.set_input_spectrum(load_astm("AM1.5g"))

        sps = SPICESolver3D(solarcell=self.gaas_1j, illumination=illumination_mask_3d,
                            metal_contact=metal_mask, rw=pw, cw=pw, v_start=self.vini, v_end=vfin,
                            v_steps=step,
                            l_r=self.lr, l_c=self.lc, h=self.h, spice_preprocessor=nd)

        sps_2d = SPICESolver(solarcell=self.gaas_1j, illumination=illumination_mask_2d,
                             metal_contact=metal_mask, rw=pw, cw=pw, v_start=self.vini, v_end=vfin,
                             v_steps=step,
                             l_r=self.lr, l_c=self.lc, h=self.h, spice_preprocessor=nd)

        device_area = (metal_mask.size * self.lc * self.lr)

        plt.figure()
        plt.plot(sps.V, sps.I / device_area, label="with abberration")
        plt.plot(sps_2d.V, sps_2d.I / device_area, label="uniform")
        plt.xlabel("voltage (V)")
        plt.ylabel("current density (A/m^2)")
        plt.legend()

        plt.ylim(ymax=0, ymin=np.min(sps_2d.I / device_area) * 2)

        plt.savefig(os.path.join(self.output_data_path, "chromatic_abberated_iv.png"), dpi=300)

        plt.show()

        not_metal = np.logical_not(np.where(metal_mask > 0, 1, 0))

        self.gaas_1j.set_input_spectrum(load_astm("AM1.5g"))
        estimated_isc = self.gaas_1j.jsc * self.lc * self.lr * np.sum(illumination_mask_2d * not_metal)
        # device_photo_active_area=self.lc*self.lr*np.sum()
        print(estimated_isc)
        print("2D illumination solver isc:{}".format(sps_2d.I[0]))
        print("3D illumination solver isc:{}".format(sps.I[0]))
        print(self.gaas_1j.jsc)

    def test_3d_illumination_3J(self):
        """
        Test if 3D illumination can run successfully on 3J cell
        #TODO lots of duplicated code from 1J version

        :return:
        """

        mj_cell = MJCell([self.ingap_1j, self.gaas_1j, self.ge_1j])

        pw = 5

        vfin = 3.0
        step = 0.02

        metal_mask = get_quater_image(self.default_contactsMask)
        plt.figure()

        plt.imshow(metal_mask)
        plt.show()

        print(contact_ratio(metal_mask, threshold=0))

        illumination_mask_3d, wl = make_3d_illumination(*metal_mask.shape)

        fig, ax = draw_illumination_3d(illumination_mask_3d, wl, [0, 500, 800, -1])

        fig.savefig(os.path.join(self.output_data_path, 'aberrated_profile.png'), dpi=300)

        fig.show()

        illumination_mask_2d = gen_profile(metal_mask.shape[0], metal_mask.shape[1], bound_ratio=0.7)
        plt.figure()
        plt.imshow(illumination_mask_2d)

        plt.title("no aberration")
        plt.savefig(os.path.join(self.output_data_path, "no_aberration_profile.png"))
        plt.show()

        nd = NodeReducer()

        mj_cell.set_input_spectrum(load_astm("AM1.5g"))

        sps = SPICESolver3D(solarcell=mj_cell, illumination=illumination_mask_3d,
                            metal_contact=metal_mask, rw=pw, cw=pw, v_start=self.vini, v_end=vfin,
                            v_steps=step,
                            l_r=self.lr, l_c=self.lc, h=self.h, spice_preprocessor=nd)

        sps_2d = SPICESolver(solarcell=mj_cell, illumination=illumination_mask_2d,
                             metal_contact=metal_mask, rw=pw, cw=pw, v_start=self.vini, v_end=vfin,
                             v_steps=step,
                             l_r=self.lr, l_c=self.lc, h=self.h, spice_preprocessor=nd)

        device_area = (metal_mask.size * self.lc * self.lr)

        plt.figure()
        plt.plot(sps.V, sps.I / device_area, label="with aberration")
        plt.plot(sps_2d.V, sps_2d.I / device_area, label="no aberration")
        plt.xlabel("voltage (V)")
        plt.ylabel("current density (A/m^2)")
        plt.grid()
        plt.legend()

        plt.ylim(ymax=0, ymin=np.min(sps_2d.I / device_area) * 1.2)

        plt.savefig(os.path.join(self.output_data_path, "chromatic_aberrated_iv.png"), dpi=300)

        plt.show()

        not_metal = np.logical_not(np.where(metal_mask > 0, 1, 0))

        mj_cell.set_input_spectrum(load_astm("AM1.5g"))
        # estimated_isc = self.gaas_1j.jsc * self.lc * self.lr * np.sum(illumination_mask_2d * not_metal)
        # device_photo_active_area=self.lc*self.lr*np.sum()
        # print(estimated_isc)
        print("2D illumination solver isc:{}".format(sps_2d.I[0]))
        print("3D illumination solver isc:{}".format(sps.I[0]))
        # print(self.gaas_1j.jsc)

    def test_larger_1j_circuit(self):
        """
        Test 1J cell

        :return:
        """

        ill = load_astm("AM1.5g")

        self.gaas_1j.set_input_spectrum(ill)

        self.run_larger_1j_circuit(self.gaas_1j, file_prefix="1j")

    def test_larger_3j_circuit(self):
        """
        Test 3J cell

        :return:
        """

        ill = load_astm("AM1.5g")

        mj_cell = MJCell([self.ingap_1j, self.gaas_1j])
        mj_cell.set_input_spectrum(ill)

        self.run_larger_1j_circuit(mj_cell, file_prefix="3j")

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

        draw_merged_contact_images(self.output_data_path, test_pixel_width, file_prefix, contacts_mask)

        result_vi = None

        print("original image shape:{},{}".format(*contacts_mask.shape))
        print("illumination total {}:".format(illumination_mask.sum()))

        plt.figure()

        for pw in test_pixel_width:

            nd = NodeReducer()

            sps = SPICESolver(solarcell=input_solar_cells, illumination=illumination_mask,
                              metal_contact=contacts_mask, rw=pw, cw=pw, v_start=self.vini, v_end=self.vfin,
                              v_steps=self.step,
                              l_r=self.lr, l_c=self.lc, h=self.h, spice_preprocessor=nd)

            np.save(os.path.join(self.output_data_path, "{}_vmap_{}.npy").format(file_prefix, pw),
                    sps.get_end_voltage_map())

            if result_vi is None:
                result_vi = np.stack((sps.V, sps.I))
            else:
                result_vi = np.vstack((result_vi, sps.V, sps.I))

            plt.plot(sps.V, sps.I, label="pw: {}".format(pw))
            fill_factor = ff(sps.V, sps.I)
            calculated_isc = isc(sps.V, sps.I)

            print("Jsc: {:2f} A/m^2".format(calculated_isc))
            print("fill factor of of pw {}: {}".format(pw, fill_factor))

        draw_contact_and_voltage_map(self.output_data_path, test_pixel_width, file_prefix, contacts_mask)

        np.savetxt(os.path.join(self.output_data_path, "{}_ingap_iv.csv".format(file_prefix)), result_vi.T,
                   delimiter=',')

        plt.savefig(os.path.join(self.output_data_path, "{}_1jfig.png".format(file_prefix)))


if __name__ == '__main__':
    unittest.main()
